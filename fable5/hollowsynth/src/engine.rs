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
}

impl Drive {
    fn new(program: u8, sr: f32) -> Self {
        let (gain, post) = if program == 30 {
            (7.0, 0.30)
        } else {
            (3.5, 0.42)
        };
        Drive {
            pre: Biquad::highpass(90.0, 0.7, sr),
            tone: Biquad::lowpass(3400.0, 0.8, sr),
            gain,
            post,
        }
    }

    fn process(&mut self, buf: &mut [f32]) {
        for x in buf.iter_mut() {
            let y = (self.pre.process(*x) * self.gain).tanh();
            *x = self.tone.process(y) * self.post;
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

struct Strip {
    program: u8,
    volume: f32, // CC7 as amplitude (squared curve)
    pan: f32,    // 0..1
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
    let mut chorus = Chorus::new(sr);
    let mut echo = (opt.delay_s > 0.0).then(|| PingPong::new(sr, opt.delay_s));
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
                    if let Some(voice) = voice {
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
                        91 => s.reverb_send = v,
                        _ => {}
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
            }
        }
        chorus.process(&send_cho[..n], &mut mix_l[..n], &mut mix_r[..n]);
        if let Some(echo) = &mut echo {
            echo.process(&send_del[..n], &mut mix_l[..n], &mut mix_r[..n]);
        }
        reverb.process(&send_rev[..n], &mut mix_l[..n], &mut mix_r[..n]);

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
