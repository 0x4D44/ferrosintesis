//! The render engine: walks the event list in 64-sample blocks, spawns and
//! mixes voices per channel, applies each channel's strip (program-aware
//! distortion insert, CC7 volume, CC11 expression, CC10 pan with a Haas
//! micro-delay for real width, CC91 reverb send) and three global buses:
//! a hall reverb, a stereo chorus (ensembles breathe), and a tempo-derived
//! ping-pong echo (the classic delayed-lead sound).

use crate::dsp::{Biquad, DelayLine, OnePole, Rng};
use crate::midi::{EvKind, Song};
use crate::reverb::Reverb;
use crate::{drums, voices};
use std::f32::consts::{FRAC_PI_2, TAU};

const BLOCK: usize = 64;

/// Overdrive/distortion channel insert for GM programs 29/30.
struct Drive {
    pre: Biquad,
    tone: Biquad,
    gain: f32,
    post: f32,
    prev: f32,
}

impl Drive {
    fn new(program: u8, sr: f32) -> Self {
        let (gain, post) = if program == 30 {
            (7.0, 0.30)
        } else {
            (3.5, 0.42)
        };
        // the nonlinearity runs at 2x rate to halve tanh aliasing
        Drive {
            pre: Biquad::highpass(90.0, 0.7, sr * 2.0),
            tone: Biquad::lowpass(3400.0, 0.8, sr * 2.0),
            gain,
            post,
            prev: 0.0,
        }
    }

    fn process(&mut self, buf: &mut [f32]) {
        for x in buf.iter_mut() {
            let mid = 0.5 * (self.prev + *x);
            self.prev = *x;
            let y0 = self
                .tone
                .process((self.pre.process(mid) * self.gain).tanh());
            let y1 = self.tone.process((self.pre.process(*x) * self.gain).tanh());
            *x = 0.5 * (y0 + y1) * self.post;
        }
    }
}

/// Per-program bus sends (chorus, echo). Reverb stays CC91-authored.
fn fx_profile(program: u8) -> (f32, f32) {
    match program {
        16..=23 => (0.20, 0.0),   // organs: gentle ensemble
        24 | 25 => (0.12, 0.08),  // acoustic guitars: a touch of both
        26..=31 => (0.10, 0.30),  // electric guitars: the delayed-lead sound
        40..=45 => (0.10, 0.10),  // fiddle
        46 => (0.15, 0.0),        // harp
        48..=51 => (0.35, 0.0),   // string ensembles
        52..=54 => (0.30, 0.0),   // choir
        72..=79 => (0.0, 0.22),   // flute / whistle
        80..=95 => (0.45, 0.0),   // pads
        96..=103 => (0.30, 0.35), // crystal: shimmer and echo
        8..=10 => (0.0, 0.15),    // celesta / glockenspiel / music box
        14 | 15 => (0.0, 0.08),   // tubular bells
        _ => (0.0, 0.0),
    }
}

/// Stereo chorus bus: one modulated delay line, quadrature taps L/R.
struct Chorus {
    dl: DelayLine,
    phase: f32,
    rate: f32,
    base: f32,
    depth: f32,
    sr: f32,
}

impl Chorus {
    fn new(sr: f32) -> Self {
        Chorus {
            dl: DelayLine::new((0.040 * sr) as usize),
            phase: 0.0,
            rate: 0.35,
            base: 0.018 * sr,
            depth: 0.005 * sr,
            sr,
        }
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        for i in 0..send.len() {
            self.dl.push(send[i]);
            self.phase += TAU * self.rate / self.sr;
            if self.phase > TAU {
                self.phase -= TAU;
            }
            let tl = self.dl.tap(self.base + self.depth * self.phase.sin());
            let tr = self
                .dl
                .tap(self.base + self.depth * (self.phase + FRAC_PI_2).sin());
            l[i] += tl * 0.55;
            r[i] += tr * 0.55;
        }
    }
}

/// Ping-pong echo bus: repeats alternate sides, darkening as they fade.
struct PingPong {
    left: DelayLine,
    right: DelayLine,
    time: f32,
    feedback: f32,
    lp_l: OnePole,
    lp_r: OnePole,
}

impl PingPong {
    fn new(sr: f32, time_s: f32) -> Self {
        let samples = (time_s * sr).max(64.0);
        PingPong {
            left: DelayLine::new(samples as usize + 4),
            right: DelayLine::new(samples as usize + 4),
            time: samples,
            feedback: 0.34,
            lp_l: OnePole::lowpass(3200.0, sr),
            lp_r: OnePole::lowpass(3200.0, sr),
        }
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        for i in 0..send.len() {
            let out_l = self.left.tap(self.time);
            let out_r = self.right.tap(self.time);
            self.left
                .push(send[i] + self.lp_r.process(out_r) * self.feedback);
            self.right.push(self.lp_l.process(out_l) * self.feedback);
            l[i] += out_l * 0.8;
            r[i] += out_r * 0.8;
        }
    }
}

/// Sympathetic resonance: the piano's undamped strings ring along with
/// whatever it plays. Twelve lightly-damped comb resonators (one per pitch
/// class, C3..B3) are fed by the piano channels and returned quietly.
struct Sympathetic {
    combs: Vec<(DelayLine, f32, OnePole)>,
    hp: Biquad,
}

impl Sympathetic {
    fn new(sr: f32) -> Self {
        let combs = (0..12)
            .map(|k| {
                let f = 130.81 * 2f32.powf(k as f32 / 12.0);
                let d = sr / f;
                (
                    DelayLine::new(d as usize + 4),
                    d,
                    OnePole::lowpass(2600.0, sr),
                )
            })
            .collect();
        Sympathetic {
            combs,
            hp: Biquad::highpass(170.0, 0.7, sr),
        }
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        for i in 0..send.len() {
            let x = self.hp.process(send[i]) * 0.05;
            let mut sum = 0.0;
            for (dl, d, damp) in &mut self.combs {
                let y = dl.tap(*d);
                dl.push(x + damp.process(y) * 0.85);
                sum += y;
            }
            let w = sum * 0.55;
            l[i] += w;
            r[i] += w;
        }
    }
}

/// Master-bus glue: a slow 2:1 compressor (a dB or two of gentle movement)
/// and a whisper of saturation, so the mix couples like a record instead of
/// arithmetic.
struct BusGlue {
    env: f32,
    gain: f32,
    atk: f32,
    rel: f32,
    thr: f32,
    shelf_l: Biquad,
    shelf_r: Biquad,
}

impl BusGlue {
    fn new(sr: f32) -> Self {
        BusGlue {
            env: 0.0,
            gain: 1.0,
            atk: 1.0 - (-1.0 / (0.015 * sr)).exp(),
            rel: 1.0 - (-1.0 / (0.250 * sr)).exp(),
            thr: 0.32,
            shelf_l: Biquad::peak(95.0, 0.7, 1.5, sr),
            shelf_r: Biquad::peak(95.0, 0.7, 1.5, sr),
        }
    }

    fn process(&mut self, l: &mut [f32], r: &mut [f32]) {
        for i in 0..l.len() {
            let xl = self.shelf_l.process(l[i]);
            let xr = self.shelf_r.process(r[i]);
            let level = xl.abs().max(xr.abs());
            let k = if level > self.env { self.atk } else { self.rel };
            self.env += k * (level - self.env);
            let target = if self.env > self.thr {
                (self.thr / self.env).sqrt() // 2:1 above threshold
            } else {
                1.0
            };
            let kg = if target < self.gain {
                self.atk
            } else {
                self.rel
            };
            self.gain += kg * (target - self.gain);
            // gentle tape-ish saturation on the glued signal
            let gl = xl * self.gain;
            let gr = xr * self.gain;
            l[i] = gl + 0.12 * ((gl * 1.4).tanh() / 1.4 - gl);
            r[i] = gr + 0.12 * ((gr * 1.4).tanh() / 1.4 - gr);
        }
    }
}

struct Strip {
    program: u8,
    volume: f32,  // CC7 as amplitude (squared curve)
    pan: f32,     // 0..1
    bend: f32,    // pitch-bend as a frequency multiplier
    legato: bool, // CC68: new notes slur into the ringing voice
    expr_target: f32,
    expr: f32,
    reverb_send: f32,
    chorus_send: f32,
    delay_send: f32,
    drive: Option<Drive>,
    haas: DelayLine,
    haas_delay: f32, // samples of far-side delay; 0 disables
}

impl Strip {
    fn new(sr: f32) -> Self {
        Strip {
            program: 0,
            volume: (100.0f32 / 127.0).powi(2),
            pan: 0.5,
            bend: 1.0,
            legato: false,
            expr_target: 1.0,
            expr: 1.0,
            reverb_send: 0.3,
            chorus_send: 0.0,
            delay_send: 0.0,
            drive: None,
            haas: DelayLine::new((0.006 * sr) as usize + 4),
            haas_delay: 0.0,
        }
    }
}

pub struct Options {
    pub sr: f32,
    pub wet: f32,
    pub tail: f32,
    pub delay_s: f32,  // echo time; 0 disables the echo bus
    pub samples: bool, // LA attack-sample layer on the solo voices
    pub verbose: bool,
}

pub struct Stats {
    pub voices_spawned: u64,
    pub peak: f32,
    pub max_polyphony: usize,
}

struct Active {
    ch: u8,
    key: u8,
    voice: Box<dyn voices::Voice>,
}

pub fn render(song: &Song, opt: &Options) -> (Vec<f32>, Stats) {
    let sr = opt.sr;
    let total = ((song.seconds + opt.tail as f64) * sr as f64) as usize;
    let mut out = vec![0f32; total * 2]; // interleaved stereo

    let mut strips: Vec<Strip> = (0..16).map(|_| Strip::new(sr)).collect();
    let mut active: Vec<Active> = Vec::new();
    let mut reverb = Reverb::new(sr, 0.86, 0.35, opt.wet);
    let mut rev_hp = Biquad::highpass(150.0, 0.7, sr); // keep the lows dry and tight
    let mut chorus = Chorus::new(sr);
    let mut echo = (opt.delay_s > 0.0).then(|| PingPong::new(sr, opt.delay_s));
    let mut symp = Sympathetic::new(sr);
    let mut glue = BusGlue::new(sr);
    let mut stats = Stats {
        voices_spawned: 0,
        peak: 0.0,
        max_polyphony: 0,
    };

    let events: Vec<(usize, EvKind)> = song
        .events
        .iter()
        .map(|e| ((e.sec * sr as f64) as usize, e.kind))
        .collect();
    let mut ev_i = 0;

    let mut ch_buf = vec![[0f32; BLOCK]; 16];
    let mut scratch = [0f32; BLOCK];
    let mut send_rev = [0f32; BLOCK];
    let mut send_cho = [0f32; BLOCK];
    let mut send_del = [0f32; BLOCK];
    let mut send_sym = [0f32; BLOCK];
    let mut mix_l = [0f32; BLOCK];
    let mut mix_r = [0f32; BLOCK];
    let expr_smooth = 1.0 - (-(BLOCK as f32) / (0.03 * sr)).exp();
    let mut next_report = total / 10;

    let mut block_start = 0usize;
    while block_start < total {
        let n = BLOCK.min(total - block_start);

        // apply events that fall inside this block (quantised to block start)
        while ev_i < events.len() && events[ev_i].0 < block_start + n {
            let (_, kind) = events[ev_i];
            ev_i += 1;
            match kind {
                EvKind::NoteOn { ch, key, vel } => {
                    // CC68 legato: slur into the channel's one ringing voice
                    if ch != 9 && strips[ch as usize].legato {
                        let mut ringing = active
                            .iter_mut()
                            .filter(|a| a.ch == ch && !a.voice.released());
                        if let (Some(a), None) = (ringing.next(), ringing.next()) {
                            if a.voice.legato_to(key, vel) {
                                a.key = key;
                                continue;
                            }
                        }
                    }
                    let seed = 0x9E37 ^ (stats.voices_spawned as u32).wrapping_mul(2654435761);
                    let voice = if ch == 9 {
                        drums::make(key, vel, sr, seed)
                    } else {
                        Some(voices::make(
                            strips[ch as usize].program,
                            key,
                            vel,
                            sr,
                            seed,
                            opt.samples,
                        ))
                    };
                    if let Some(mut voice) = voice {
                        let bend = strips[ch as usize].bend;
                        if bend != 1.0 {
                            voice.set_pitch(bend);
                        }
                        active.push(Active { ch, key, voice });
                        stats.voices_spawned += 1;
                    }
                }
                EvKind::NoteOff { ch, key } => {
                    if let Some(a) = active
                        .iter_mut()
                        .find(|a| a.ch == ch && a.key == key && !a.voice.released())
                    {
                        a.voice.note_off();
                    }
                }
                EvKind::Cc { ch, num, val } => {
                    let s = &mut strips[ch as usize];
                    let v = val as f32 / 127.0;
                    match num {
                        7 => s.volume = v * v,
                        10 => {
                            s.pan = v;
                            // far ear hears a panned source a moment later
                            s.haas_delay = 0.005 * sr * (v - 0.5).abs() * 2.0;
                        }
                        11 => s.expr_target = v * v,
                        68 => s.legato = val >= 64,
                        91 => s.reverb_send = v,
                        93 => s.chorus_send = v,
                        94 => s.delay_send = v,
                        _ => {}
                    }
                }
                EvKind::Bend { ch, semis } => {
                    let mult = 2f32.powf(semis / 12.0);
                    strips[ch as usize].bend = mult;
                    for a in active.iter_mut().filter(|a| a.ch == ch) {
                        a.voice.set_pitch(mult);
                    }
                }
                EvKind::Prog { ch, prog } => {
                    let s = &mut strips[ch as usize];
                    s.program = prog;
                    let (cho, del) = if ch == 9 {
                        (0.0, 0.0)
                    } else {
                        fx_profile(prog)
                    };
                    s.chorus_send = cho;
                    s.delay_send = del;
                    if matches!(prog, 29 | 30) {
                        if s.drive.is_none() {
                            s.drive = Some(Drive::new(prog, sr));
                        }
                    } else {
                        s.drive = None;
                    }
                }
            }
        }

        // voices -> channel buffers
        for buf in ch_buf.iter_mut() {
            buf[..n].fill(0.0);
        }
        stats.max_polyphony = stats.max_polyphony.max(active.len());
        active.retain_mut(|a| {
            scratch[..n].fill(0.0);
            let alive = a.voice.render(&mut scratch[..n]);
            let buf = &mut ch_buf[a.ch as usize];
            for i in 0..n {
                buf[i] += scratch[i];
            }
            alive
        });

        // channel strips -> stereo mix + bus sends
        mix_l[..n].fill(0.0);
        mix_r[..n].fill(0.0);
        send_rev[..n].fill(0.0);
        send_cho[..n].fill(0.0);
        send_del[..n].fill(0.0);
        send_sym[..n].fill(0.0);
        for (ci, strip) in strips.iter_mut().enumerate() {
            let buf = &mut ch_buf[ci];
            if let Some(drive) = &mut strip.drive {
                drive.process(&mut buf[..n]);
            }
            strip.expr += expr_smooth * (strip.expr_target - strip.expr);
            let g = strip.volume * strip.expr;
            if g < 1e-6 {
                continue;
            }
            let theta = strip.pan * FRAC_PI_2;
            let (gl, gr) = (g * theta.cos(), g * theta.sin());
            let rs = strip.reverb_send * 0.9;
            let is_piano = ci != 9 && strip.program <= 7;
            let haas = strip.haas_delay;
            for i in 0..n {
                let x = buf[i];
                strip.haas.push(x);
                // the far channel is delayed a few milliseconds — Haas
                // localisation instead of a bare level difference
                let (xl, xr) = if haas < 1.0 {
                    (x, x)
                } else if strip.pan < 0.5 {
                    (x, strip.haas.tap(haas))
                } else {
                    (strip.haas.tap(haas), x)
                };
                mix_l[i] += xl * gl;
                mix_r[i] += xr * gr;
                let xs = x * g;
                send_rev[i] += xs * rs;
                send_cho[i] += xs * strip.chorus_send;
                send_del[i] += xs * strip.delay_send;
                if is_piano {
                    send_sym[i] += xs;
                }
            }
        }
        symp.process(&send_sym[..n], &mut mix_l[..n], &mut mix_r[..n]);
        chorus.process(&send_cho[..n], &mut mix_l[..n], &mut mix_r[..n]);
        if let Some(echo) = &mut echo {
            echo.process(&send_del[..n], &mut mix_l[..n], &mut mix_r[..n]);
        }
        for x in send_rev[..n].iter_mut() {
            *x = rev_hp.process(*x);
        }
        reverb.process(&send_rev[..n], &mut mix_l[..n], &mut mix_r[..n]);
        glue.process(&mut mix_l[..n], &mut mix_r[..n]);

        for i in 0..n {
            out[(block_start + i) * 2] = mix_l[i];
            out[(block_start + i) * 2 + 1] = mix_r[i];
            let m = mix_l[i].abs().max(mix_r[i].abs());
            if m > stats.peak {
                stats.peak = m;
            }
        }

        block_start += n;
        if opt.verbose && block_start >= next_report {
            eprintln!(
                "  rendered {:>3.0}%  ({:.1} s, {} live voices)",
                block_start as f64 / total as f64 * 100.0,
                block_start as f64 / sr as f64,
                active.len()
            );
            next_report += total / 10;
        }
    }
    (out, stats)
}

/// Peak-normalise to `target` and convert to interleaved i16 with TPDF dither.
pub fn normalize_to_i16(samples: &[f32], peak: f32, target: f32) -> Vec<i16> {
    let scale = if peak > 1e-9 { target / peak } else { 1.0 };
    let mut rng = Rng::new(0xD17E);
    samples
        .iter()
        .map(|&x| {
            let dither = (rng.white() + rng.white()) * 0.5; // triangular, ±1 LSB
            ((x * scale).clamp(-1.0, 1.0) * 32767.0 + dither)
                .round()
                .clamp(-32768.0, 32767.0) as i16
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The bus glue must tame loud material, pass quiet material nearly
    /// unchanged, and never blow up.
    #[test]
    fn glue_compresses_and_stays_sane() {
        let sr = 44100.0;
        let mut glue = BusGlue::new(sr);
        let mut l: Vec<f32> = (0..44100)
            .map(|i| (i as f32 * 220.0 / sr * std::f32::consts::TAU).sin() * 0.8)
            .collect();
        let mut r = l.clone();
        glue.process(&mut l, &mut r);
        let out_peak = l[22050..].iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(out_peak < 0.8, "no gain reduction: {out_peak}");
        assert!(out_peak > 0.3, "over-compressed: {out_peak}");
        assert!(l.iter().all(|x| x.is_finite()));

        let mut glue2 = BusGlue::new(sr);
        let mut ql: Vec<f32> = (0..44100)
            .map(|i| (i as f32 * 220.0 / sr * std::f32::consts::TAU).sin() * 0.05)
            .collect();
        let mut qr = ql.clone();
        glue2.process(&mut ql, &mut qr);
        let q_peak = ql[22050..].iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(
            (q_peak - 0.05).abs() < 0.012,
            "quiet signal changed: {q_peak}"
        );
    }
}
