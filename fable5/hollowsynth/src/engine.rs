//! The render engine: walks the event list in 64-sample blocks, spawns and
//! mixes voices per channel, applies each channel's strip (program-aware
//! distortion insert, CC74 brightness filter, CC7 volume, CC11 expression,
//! CC1 mod-wheel vibrato / Leslie ramp, CC64 sustain pedal, CC10 pan with a
//! Haas micro-delay for real width, CC91 reverb send) and three global
//! buses: a hall reverb, a stereo chorus (ensembles breathe), and a
//! tempo-derived ping-pong echo (the classic delayed-lead sound).

use crate::dsp::{Biquad, DelayLine, OnePole, Rng};
use crate::midi::{EvKind, Song};
use crate::reverb::Reverb;
use crate::{drums, voices};
use std::f32::consts::{FRAC_PI_2, TAU};

const BLOCK: usize = 64;

// CC1 mod wheel. Melodic sustained voices (plucks, bowed, winds) get an
// engine-level vibrato LFO per channel, multiplied on top of the channel's
// pitch-bend; organs morph their tremulant toward Leslie-fast instead.
const VIB_RATE_HZ: f32 = 5.3; // vibrato LFO rate
const VIB_DEPTH_CENTS: f32 = 35.0; // pitch depth at mod = 1
const LESLIE_FAST_HZ: f32 = 6.8; // tremulant rate the rotor spins up to
const LESLIE_INERTIA_S: f32 = 1.5; // rotor time constant (spin-up/down)
const LESLIE_DEPTH_ADD: f32 = 0.10; // extra tremulant depth at mod = 1

// CC74 brightness: a resonant 2-pole lowpass on the channel's dry path,
// ahead of the bus sends, so the wah colours the reverb and echo too.
// 0..127 maps exponentially WAH_MIN_HZ..WAH_MAX_HZ; 127 is a true bypass.
const WAH_MIN_HZ: f32 = 300.0;
const WAH_MAX_HZ: f32 = 12000.0;
const WAH_Q: f32 = 1.4;
const WAH_SLEW_S: f32 = 0.02; // cutoff smoothing so a CC74 LFO doesn't zipper

/// Melodic sustained families that take the engine-level CC1 vibrato:
/// plucks (except palm-mute 28), bowed strings, winds. Drums, organs and
/// modal instruments (piano, bells) are left alone.
fn vibrato_family(program: u8) -> bool {
    // guitars (no palm-mute 28), basses, bowed strings, harp, winds, banjo
    matches!(program, 24..=27 | 29..=46 | 72..=79 | 104..=107)
}

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
    volume: f32,   // CC7 as amplitude (squared curve)
    pan: f32,      // 0..1
    bend: f32,     // pitch-bend as a frequency multiplier
    legato: bool,  // CC68: new notes slur into the ringing voice
    sustain: bool, // CC64: NoteOffs are held until the pedal lifts
    expr_target: f32,
    expr: f32,
    mod_target: f32, // CC1, smoothed into mod_cur like expression
    mod_cur: f32,
    mod_engaged: bool, // mod machinery active (stays on through spin-down)
    vib_phase: f32,
    leslie_rate: f32, // current tremulant rate/depth, slewed with inertia
    leslie_depth: f32,
    reverb_send: f32,
    chorus_send: f32,
    delay_send: f32,
    drive: Option<Drive>,
    wah: Option<Biquad>, // CC74 brightness filter; None = true bypass
    cutoff: f32,         // current wah cutoff Hz, slewed toward cutoff_target
    cutoff_target: f32,
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
            sustain: false,
            expr_target: 1.0,
            expr: 1.0,
            mod_target: 0.0,
            mod_cur: 0.0,
            mod_engaged: false,
            vib_phase: 0.0,
            leslie_rate: 0.0,
            leslie_depth: 0.0,
            reverb_send: 0.3,
            chorus_send: 0.0,
            delay_send: 0.0,
            drive: None,
            wah: None,
            cutoff: WAH_MAX_HZ,
            cutoff_target: WAH_MAX_HZ,
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
    pub solo: u16,     // channel bitmask; note events elsewhere are dropped
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
    held: bool, // NoteOff arrived while the sustain pedal was down
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
    let leslie_k = 1.0 - (-(BLOCK as f32) / (LESLIE_INERTIA_S * sr)).exp();
    let wah_smooth = 1.0 - (-(BLOCK as f32) / (WAH_SLEW_S * sr)).exp();
    let mut next_report = total / 10;

    let mut block_start = 0usize;
    while block_start < total {
        let n = BLOCK.min(total - block_start);

        // apply events that fall inside this block (quantised to block start)
        while ev_i < events.len() && events[ev_i].0 < block_start + n {
            let (_, kind) = events[ev_i];
            ev_i += 1;
            match kind {
                // --solo: muted channels keep their CCs but lose their notes
                EvKind::NoteOn { ch, .. } | EvKind::NoteOff { ch, .. }
                    if opt.solo & (1u16 << ch) == 0 => {}
                EvKind::NoteOn { ch, key, vel } => {
                    // CC68 legato: slur into the channel's one ringing voice
                    // (pedal-held voices are past their NoteOff — not slurred)
                    if ch != 9 && strips[ch as usize].legato {
                        let mut ringing = active
                            .iter_mut()
                            .filter(|a| a.ch == ch && !a.held && !a.voice.released());
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
                        active.push(Active {
                            ch,
                            key,
                            held: false,
                            voice,
                        });
                        stats.voices_spawned += 1;
                    }
                }
                EvKind::NoteOff { ch, key } => {
                    if let Some(a) = active
                        .iter_mut()
                        .find(|a| a.ch == ch && a.key == key && !a.held && !a.voice.released())
                    {
                        if ch != 9 && strips[ch as usize].sustain {
                            a.held = true; // CC64: the pedal keeps it ringing
                        } else {
                            a.voice.note_off();
                        }
                    }
                }
                EvKind::Cc { ch, num, val } => {
                    let s = &mut strips[ch as usize];
                    let v = val as f32 / 127.0;
                    match num {
                        1 => s.mod_target = v,
                        7 => s.volume = v * v,
                        10 => {
                            s.pan = v;
                            // far ear hears a panned source a moment later
                            s.haas_delay = 0.005 * sr * (v - 0.5).abs() * 2.0;
                        }
                        11 => s.expr_target = v * v,
                        64 => {
                            s.sustain = val >= 64;
                            if !s.sustain {
                                // pedal up: everything it was holding lets go
                                for a in active.iter_mut().filter(|a| a.ch == ch && a.held) {
                                    a.held = false;
                                    a.voice.note_off();
                                }
                            }
                        }
                        68 => s.legato = val >= 64,
                        74 => {
                            s.cutoff_target = WAH_MIN_HZ * (WAH_MAX_HZ / WAH_MIN_HZ).powf(v);
                            if val < 127 && s.wah.is_none() {
                                // the filter enters the path transparently:
                                // wide open, then slews down to the target
                                s.wah = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                            }
                        }
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

        // CC1 mod wheel: per-block pitch/tremulant updates, before the
        // voices render. Nothing here runs for channels that never move
        // the wheel, so mod-free renders are bit-identical to v0.5.
        for (ci, strip) in strips.iter_mut().enumerate() {
            strip.mod_cur += expr_smooth * (strip.mod_target - strip.mod_cur);
            let on = strip.mod_cur > 1e-3;
            if ci == 9 || (!on && !strip.mod_engaged) {
                continue;
            }
            let m = if on { strip.mod_cur } else { 0.0 };
            let ch = ci as u8;
            if matches!(strip.program, 16..=23) {
                // organs: the wheel is a Leslie speed control — the channel's
                // one rotor slews toward fast with real inertia, and every
                // organ voice on the channel follows it
                let (base_rate, base_depth) = voices::organ_trem_base(strip.program);
                if !strip.mod_engaged {
                    strip.leslie_rate = base_rate;
                    strip.leslie_depth = base_depth;
                }
                let target_rate = base_rate + (LESLIE_FAST_HZ - base_rate) * m;
                let target_depth = base_depth + LESLIE_DEPTH_ADD * m;
                strip.leslie_rate += leslie_k * (target_rate - strip.leslie_rate);
                strip.leslie_depth += leslie_k * (target_depth - strip.leslie_depth);
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_trem(strip.leslie_rate, strip.leslie_depth);
                }
                // stay engaged until the rotor has coasted back to base speed
                strip.mod_engaged = on || (strip.leslie_rate - base_rate).abs() > 0.01;
            } else if vibrato_family(strip.program) {
                strip.vib_phase += TAU * VIB_RATE_HZ * n as f32 / sr;
                if strip.vib_phase > TAU {
                    strip.vib_phase -= TAU;
                }
                // vibrato multiplies on top of the channel's bend multiplier;
                // the final pass (m = 0) snaps pitch back to the bare bend
                let mult =
                    strip.bend * 2f32.powf(m * VIB_DEPTH_CENTS / 1200.0 * strip.vib_phase.sin());
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_pitch(mult);
                }
                strip.mod_engaged = on;
            } else {
                strip.mod_engaged = false;
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
            if let Some(wah) = &mut strip.wah {
                // CC74 brightness: on the dry path before the sends tap it,
                // so the wah colours the reverb and echo too; the cutoff
                // slews per block so a riding CC74 LFO doesn't zipper
                strip.cutoff += wah_smooth * (strip.cutoff_target - strip.cutoff);
                wah.retune_lowpass(strip.cutoff, WAH_Q, sr);
                for x in buf[..n].iter_mut() {
                    *x = wah.process(*x);
                }
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
    use crate::midi::Ev;

    fn test_song(events: Vec<(f64, EvKind)>, seconds: f64) -> Song {
        Song {
            events: events
                .into_iter()
                .map(|(sec, kind)| Ev { sec, kind })
                .collect(),
            seconds,
            markers: Vec::new(),
            title: String::new(),
            initial_bpm: 120.0,
        }
    }

    /// Dry options: no reverb, no echo, no LA samples — the tests below
    /// measure the voices themselves, not the room.
    fn test_opts(sr: f32) -> Options {
        Options {
            sr,
            wet: 0.0,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            verbose: false,
        }
    }

    fn left(stereo: &[f32]) -> Vec<f32> {
        stereo.iter().step_by(2).copied().collect()
    }

    fn rms(seg: &[f32]) -> f32 {
        (seg.iter().map(|&x| (x * x) as f64).sum::<f64>() / seg.len() as f64).sqrt() as f32
    }

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

    /// Isolate the fundamental, find interpolated rising zero-crossings,
    /// smooth the per-cycle frequency over 8 cycles, and report max − min:
    /// how far the pitch wanders inside the segment.
    fn cycle_freq_spread(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(700.0, sr);
        let mut lp2 = OnePole::lowpass(700.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut times = Vec::new();
        for i in 1..f.len() {
            if f[i - 1] <= 0.0 && f[i] > 0.0 {
                times.push((i - 1) as f32 - f[i - 1] / (f[i] - f[i - 1]));
            }
        }
        let freqs: Vec<f32> = times.windows(2).map(|w| sr / (w[1] - w[0])).collect();
        let smooth: Vec<f32> = freqs
            .windows(8)
            .map(|w| w.iter().sum::<f32>() / 8.0)
            .collect();
        let hi = smooth.iter().fold(f32::MIN, |m, &x| m.max(x));
        let lo = smooth.iter().fold(f32::MAX, |m, &x| m.min(x));
        hi - lo
    }

    fn render_bowed_with_mod(mod_val: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 40 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: mod_val,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 100,
                    },
                ),
                (2.4, EvKind::NoteOff { ch: 0, key: 69 }),
            ],
            2.5,
        );
        left(&render(&song, &test_opts(44100.0)).0)
    }

    /// CC1 = 127 on a bowed note must produce a periodic pitch deviation
    /// far beyond the voice's own gentle vibrato; CC1 = 0 must not.
    #[test]
    fn cc1_mod_wheel_adds_vibrato() {
        let sr = 44100.0;
        let plain = render_bowed_with_mod(0);
        let modded = render_bowed_with_mod(127);
        let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let spread_plain = cycle_freq_spread(&plain[a..b], sr);
        let spread_mod = cycle_freq_spread(&modded[a..b], sr);
        // 35 cents of vibrato on A4 swings ~18 Hz peak-to-peak
        assert!(
            spread_mod > 10.0,
            "mod vibrato too shallow: {spread_mod} Hz"
        );
        assert!(
            spread_mod > 2.0 * spread_plain,
            "plain {spread_plain} Hz vs mod {spread_mod} Hz"
        );
    }

    /// CC1 = 127 on an organ spins the tremulant up like a Leslie: the
    /// amplitude-modulation rate must climb over ~2 s, not jump.
    #[test]
    fn cc1_leslie_spins_up_with_inertia() {
        let sr = 44100.0;
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 19 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: 127,
                    },
                ),
                (
                    0.02,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 57,
                        vel: 100,
                    },
                ),
                (3.95, EvKind::NoteOff { ch: 0, key: 57 }),
            ],
            4.0,
        );
        let mono = left(&render(&song, &test_opts(sr)).0);
        // envelope-follow the whole take, detrend, then count tremulant
        // cycles (rising crossings) per window — the AM rate
        let mut lp1 = OnePole::lowpass(15.0, sr);
        let mut lp2 = OnePole::lowpass(15.0, sr);
        let env: Vec<f32> = mono
            .iter()
            .map(|&x| lp2.process(lp1.process(x.abs())))
            .collect();
        let mut trend = OnePole::lowpass(1.5, sr);
        let det: Vec<f32> = env.iter().map(|&x| x - trend.process(x)).collect();
        let am_rate = |t0: f32, t1: f32| {
            let seg = &det[(t0 * sr) as usize..(t1 * sr) as usize];
            let mut c = 0;
            for w in seg.windows(2) {
                if w[0] <= 0.0 && w[1] > 0.0 {
                    c += 1;
                }
            }
            c as f32 / (t1 - t0)
        };
        // base 4.2 Hz slewing toward 6.8 Hz with a 1.5 s time constant
        let early = am_rate(0.15, 1.15);
        let late = am_rate(2.9, 3.9);
        assert!(
            late > early + 0.7,
            "no spin-up: early {early} Hz, late {late} Hz"
        );
        assert!(early < 5.9, "rotor started too fast: {early} Hz");
        assert!(late > 5.5, "rotor never got fast: {late} Hz");
    }

    fn render_pluck_with_cc74(cc74: Option<u8>) -> Vec<f32> {
        let mut events = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 25 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 94,
                    val: 0,
                },
            ),
        ];
        if let Some(val) = cc74 {
            events.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 74,
                    val,
                },
            ));
        }
        events.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 64,
                vel: 110,
            },
        ));
        events.push((1.5, EvKind::NoteOff { ch: 0, key: 64 }));
        render(&test_song(events, 1.6), &test_opts(44100.0)).0
    }

    /// CC74 = 20 must strip the top off a bright pluck; CC74 = 127 must be
    /// a true bypass — bit-identical to a render with no filter in the path.
    #[test]
    fn cc74_brightness_filter() {
        let sr = 44100.0;
        let dark = left(&render_pluck_with_cc74(Some(20)));
        let open = render_pluck_with_cc74(Some(127));
        let none = render_pluck_with_cc74(None);
        assert!(open == none, "CC74=127 is not a true bypass");
        // fraction of energy above 3 kHz — collapses with the cutoff ~535 Hz
        let hf_frac = |sig: &[f32]| {
            let mut hp = Biquad::highpass(3000.0, 0.7, sr);
            let (mut hf, mut total) = (0.0f64, 0.0f64);
            for &x in sig {
                let y = hp.process(x);
                hf += (y * y) as f64;
                total += (x * x) as f64;
            }
            hf / total.max(1e-12)
        };
        let f_dark = hf_frac(&dark);
        let f_open = hf_frac(&left(&open));
        assert!(
            f_dark < 0.25 * f_open,
            "no darkening: dark {f_dark} vs open {f_open}"
        );
    }

    /// A NoteOff under the sustain pedal keeps ringing until CC64 lifts,
    /// then releases and dies away.
    #[test]
    fn cc64_sustain_pedal_holds_notes() {
        let sr = 44100.0;
        let events = |pedal: bool| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog: 19 })];
            if pedal {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 64,
                        val: 127,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((0.5, EvKind::NoteOff { ch: 0, key: 60 }));
            if pedal {
                ev.push((
                    2.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 64,
                        val: 0,
                    },
                ));
            }
            ev
        };
        let held = left(&render(&test_song(events(true), 3.2), &test_opts(sr)).0);
        let plain = left(&render(&test_song(events(false), 3.2), &test_opts(sr)).0);
        let w = |sig: &[f32], t0: f32, t1: f32| rms(&sig[(t0 * sr) as usize..(t1 * sr) as usize]);
        // a second past the NoteOff the pedalled organ still sounds
        let held_mid = w(&held, 1.4, 1.9);
        let plain_mid = w(&plain, 1.4, 1.9);
        assert!(
            held_mid > 10.0 * plain_mid.max(1e-9),
            "pedal didn't hold: {held_mid} vs {plain_mid}"
        );
        // pedal up at 2.0 s: released, and decayed away a second later
        let after = w(&held, 3.0, 3.4);
        assert!(
            after < 0.05 * held_mid,
            "pedal-up didn't release: {after} vs {held_mid}"
        );
    }

    /// --solo of a channel with no notes renders true silence, even when
    /// other channels are full of notes.
    #[test]
    fn solo_mutes_other_channels() {
        let sr = 44100.0;
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 25 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 60,
                        vel: 100,
                    },
                ),
                (
                    0.06,
                    EvKind::NoteOn {
                        ch: 2,
                        key: 67,
                        vel: 100,
                    },
                ),
                (0.5, EvKind::NoteOff { ch: 0, key: 60 }),
                (0.5, EvKind::NoteOff { ch: 2, key: 67 }),
            ],
            1.0,
        );
        let mut opt = test_opts(sr);
        opt.solo = 1 << 5; // channel 5 never plays a note
        let (out, stats) = render(&song, &opt);
        assert_eq!(stats.voices_spawned, 0);
        assert!(
            out.iter().all(|&x| x == 0.0),
            "solo of an empty channel must be silent"
        );
        // soloing channel 0 keeps exactly its own notes
        opt.solo = 1 << 0;
        let (out2, stats2) = render(&song, &opt);
        assert_eq!(stats2.voices_spawned, 1);
        assert!(out2.iter().any(|&x| x != 0.0));
    }
}
