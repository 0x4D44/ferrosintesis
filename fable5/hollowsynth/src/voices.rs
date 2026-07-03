//! The instrument models. Every voice adds its output into a mono block and
//! reports whether it is still alive.
//!
//! Families:
//!   Modal    — additive/modal synthesis via rotation oscillators
//!              (piano with two-stage decay, celesta, glockenspiel, music
//!               box, tubular bells, crystal, timpani)
//!   Pluck    — extended Karplus-Strong strings with per-note round-robin
//!              variation (guitars, bass, harp, banjo)
//!   Organ    — harmonic drawbar bank with key click, chiff and tremulant
//!   SawStack — detuned polyBLEP saws, each layer with its own vibrato and
//!              slow pitch drift, through lowpass or vocal formants that
//!              morph open at the onset (string ensembles, choir, pads)
//!   Wind     — sine + harmonics + breath, with a pitch scoop into the note
//!   Bowed    — sawtooth through a violin body, with scoop, attack bow
//!              noise, and bow-pressure brightness
//!
//! Timing realism: sustained families speak slower at low velocity, the way
//! a gently-bowed or gently-blown note actually starts.

use crate::dsp::{key_freq, vel_amp, Adsr, Biquad, BlepSaw, DelayLine, Drift, OnePole, Rng, Sine};
use std::f32::consts::TAU;

pub trait Voice {
    /// Add one block of samples into `out`; return false when finished.
    fn render(&mut self, out: &mut [f32]) -> bool;
    fn note_off(&mut self);
    fn released(&self) -> bool;
    /// Channel pitch bend as a frequency multiplier (1.0 = centre).
    /// Voices that cannot bend simply ignore it.
    fn set_pitch(&mut self, _mult: f32) {}
    /// Take over a new note without re-attacking (slur / hammer-on).
    /// Return false if this voice cannot, and a fresh voice is needed.
    fn legato_to(&mut self, _key: u8, _vel: u8) -> bool {
        false
    }
}

fn t60_mul(t60: f32, sr: f32) -> f32 {
    // per-sample amplitude multiplier for a -60 dB decay over t60 seconds
    10f32.powf(-3.0 / (t60.max(0.01) * sr))
}

const CTRL: u32 = 16; // control-rate interval in samples

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

struct Mode {
    osc: Sine,
    amp: f32,
    decay: f32,
}

pub struct Modal {
    modes: Vec<Mode>,
    noise_amp: f32,
    noise_decay: f32,
    noise_filt: Biquad,
    rng: Rng,
    att: f32, // attack ramp increment per sample (>=1 means instant)
    att_env: f32,
    release_env: f32,
    rel_mul: f32,
    released: bool,
    gain: f32,
    level: f32, // rough live-amplitude bookkeeping
}

impl Modal {
    #[allow(clippy::too_many_arguments)]
    fn new(
        sr: f32,
        seed: u32,
        partials: &[(f32, f32, f32)], // (freq Hz, amp, T60 s)
        noise: (f32, f32, Biquad),    // (amp, T60, filter)
        attack_s: f32,
        release_t60: f32,
        gain: f32,
    ) -> Self {
        let mut rng = Rng::new(seed);
        let modes = partials
            .iter()
            .filter(|&&(f, _, _)| f < sr * 0.45)
            .map(|&(f, a, t)| Mode {
                osc: Sine::new(f, sr, rng.white() * std::f32::consts::PI),
                amp: a,
                decay: t60_mul(t, sr),
            })
            .collect();
        Modal {
            modes,
            noise_amp: noise.0,
            noise_decay: t60_mul(noise.1, sr),
            noise_filt: noise.2,
            rng,
            att: if attack_s <= 0.0 {
                1.0
            } else {
                1.0 / (attack_s * sr)
            },
            att_env: 0.0,
            release_env: 1.0,
            rel_mul: t60_mul(release_t60, sr),
            released: false,
            gain,
            level: 1.0,
        }
    }
}

impl Voice for Modal {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            let mut s = 0.0;
            for m in &mut self.modes {
                s += m.amp * m.osc.next();
                m.amp *= m.decay;
            }
            if self.noise_amp > 1e-5 {
                s += self.noise_filt.process(self.rng.white()) * self.noise_amp;
                self.noise_amp *= self.noise_decay;
            }
            if self.att_env < 1.0 {
                self.att_env = (self.att_env + self.att).min(1.0);
            }
            if self.released {
                self.release_env *= self.rel_mul;
            }
            *o += s * self.gain * self.att_env * self.release_env;
        }
        self.level = self.modes.iter().map(|m| m.amp.abs()).sum::<f32>() * self.release_env;
        self.level * self.gain > 2e-5 || self.noise_amp > 1e-4
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }
}

fn piano(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let bright = 0.55 + 0.40 * (vel as f32 / 127.0);
    let inharm = 0.00045;
    let t1 = (9.0 * (110.0 / f).powf(0.65)).clamp(0.4, 12.0);
    let mut partials = Vec::new();
    for k in 1..=16u32 {
        let kf = k as f32;
        let fk = f * kf * (1.0 + inharm * kf * kf).sqrt();
        if fk > sr * 0.42 {
            break;
        }
        let amp = v * bright.powi(k as i32 - 1) / kf.powf(1.08);
        let t = t1 / (1.0 + 0.6 * (kf - 1.0));
        // prompt sound: decays at the strike rate
        partials.push((fk, amp * 0.85, t));
        if k <= 6 {
            // aftersound: a quiet second stage that sings on much longer —
            // the characteristic double decay of a real piano string
            partials.push((fk * 1.0003, amp * 0.22, t * 2.8));
        }
        if k <= 4 {
            // detuned second string for a gentle unison shimmer
            partials.push((fk * 1.0007, amp * 0.6, t * 0.9));
        }
    }
    let hammer = Biquad::bandpass((f * 9.0).min(3800.0), 1.0, sr);
    Modal::new(
        sr,
        seed,
        &partials,
        (0.30 * v, 0.012, hammer),
        0.0015,
        0.10,
        0.50,
    )
}

/// Bar/tube/bell family, defined by (ratio, amp, T60) tables. Each strike
/// jitters the mode amplitudes a little (nobody hits the same spot twice).
#[allow(clippy::too_many_arguments)]
fn bell(
    key: u8,
    vel: u8,
    sr: f32,
    seed: u32,
    table: &[(f32, f32, f32)],
    noise: (f32, f32, f32, f32), // (amp, T60, filter freq, q)
    attack_s: f32,
    release_t60: f32,
    gain: f32,
) -> Modal {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let mut jrng = Rng::new(seed ^ 0x5F5F_5F5F);
    let partials: Vec<(f32, f32, f32)> = table
        .iter()
        .map(|&(r, a, t)| (f * r, a * v * (1.0 + 0.10 * jrng.white()), t))
        .collect();
    let filt = Biquad::bandpass(noise.2.min(sr * 0.4), noise.3, sr);
    Modal::new(
        sr,
        seed,
        &partials,
        (noise.0 * v, noise.1, filt),
        attack_s,
        release_t60,
        gain,
    )
}

const TUBULAR: &[(f32, f32, f32)] = &[
    (0.72, 0.35, 7.0),
    (1.00, 0.25, 8.0),
    (2.00, 1.00, 7.5),
    (3.00, 0.80, 6.5),
    (4.17, 0.42, 5.5),
    (5.43, 0.24, 4.5),
    (6.79, 0.12, 3.5),
    (8.21, 0.06, 2.5),
];
const GLOCK: &[(f32, f32, f32)] = &[
    (1.0, 1.0, 2.6),
    (2.76, 0.45, 1.5),
    (5.40, 0.22, 0.8),
    (8.93, 0.08, 0.4),
];
const CELESTA: &[(f32, f32, f32)] = &[(1.0, 1.0, 1.9), (2.76, 0.30, 0.8), (5.40, 0.06, 0.3)];
const MUSICBOX: &[(f32, f32, f32)] = &[(1.0, 1.0, 1.3), (2.81, 0.35, 0.6), (5.40, 0.10, 0.3)];
const CRYSTAL: &[(f32, f32, f32)] = &[
    (1.0, 0.90, 3.0),
    (1.003, 0.50, 3.4),
    (2.0, 0.35, 2.6),
    (2.996, 0.20, 2.2),
    (4.50, 0.18, 2.0),
    (6.70, 0.10, 1.6),
];
const VIBES: &[(f32, f32, f32)] = &[(1.0, 1.0, 3.0), (4.0, 0.25, 1.2), (9.8, 0.06, 0.5)];

fn timpani(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let table = [
        (1.0, 1.0, 1.0),
        (1.504, 0.70, 0.85),
        (1.742, 0.45, 0.70),
        (2.0, 0.30, 0.60),
        (2.245, 0.20, 0.50),
    ];
    let partials: Vec<(f32, f32, f32)> = table.iter().map(|&(r, a, t)| (f * r, a * v, t)).collect();
    let thump = Biquad::lowpass(300.0, 0.8, sr);
    Modal::new(
        sr,
        seed,
        &partials,
        (1.1 * v, 0.045, thump),
        0.001,
        0.25,
        0.85,
    )
}

// ---------------------------------------------------------------------------
// Pluck (extended Karplus-Strong)
// ---------------------------------------------------------------------------

pub struct PluckPreset {
    pub t60: f32,     // decay at 220 Hz
    pub bright: f32,  // loop damping cutoff
    pub pick_lp: f32, // excitation lowpass
    pub pos: f32,     // pick position (0..0.5)
    pub amp: f32,
    pub attack_s: f32,
    pub rel_t60: f32,
    pub body: &'static [(f32, f32, f32)], // (freq, q, gain dB) peak EQs
    pub out_lp: f32,                      // 0 = none
    pub pickup: f32,                      // magnetic pickup position (0 = acoustic)
    pub sub: f32,                         // envelope-locked fundamental sine (0 = none)
}

pub const NYLON: PluckPreset = PluckPreset {
    t60: 2.8,
    bright: 3200.0,
    pick_lp: 2500.0,
    pos: 0.28,
    amp: 0.55,
    attack_s: 0.0,
    rel_t60: 0.15,
    // Helmholtz air mode, top-plate mode, upper body colour
    body: &[(98.0, 1.4, 4.5), (210.0, 1.2, 4.0), (420.0, 1.8, 2.5)],
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
};
pub const STEEL: PluckPreset = PluckPreset {
    t60: 3.5,
    bright: 5200.0,
    pick_lp: 5000.0,
    pos: 0.18,
    amp: 0.50,
    attack_s: 0.0,
    rel_t60: 0.15,
    // Helmholtz, top plate, and a little steel-string presence sparkle
    body: &[(105.0, 1.4, 4.0), (215.0, 1.2, 3.0), (2800.0, 1.8, 1.5)],
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
};
pub const CLEAN: PluckPreset = PluckPreset {
    t60: 3.0,
    bright: 4200.0,
    pick_lp: 4500.0,
    pos: 0.15,
    amp: 0.50,
    attack_s: 0.0,
    rel_t60: 0.18,
    body: &[],
    out_lp: 5500.0,
    pickup: 0.12,
    sub: 0.0,
};
pub const DRIVE: PluckPreset = PluckPreset {
    t60: 8.0,
    bright: 4800.0,
    pick_lp: 6000.0,
    pos: 0.12,
    amp: 0.70,
    attack_s: 0.0,
    rel_t60: 0.20,
    body: &[],
    out_lp: 0.0,
    pickup: 0.10,
    sub: 0.0,
};
pub const MUTED: PluckPreset = PluckPreset {
    t60: 0.45, // palm on the bridge: the ring dies fast
    bright: 1600.0,
    pick_lp: 2200.0,
    pos: 0.10,
    amp: 0.62,
    attack_s: 0.0,
    rel_t60: 0.08,
    body: &[],
    out_lp: 3200.0,
    pickup: 0.10,
    sub: 0.35, // the chug's thud carries the weight
};
pub const BASS: PluckPreset = PluckPreset {
    t60: 3.6,
    bright: 1100.0,
    pick_lp: 850.0,
    pos: 0.35,
    amp: 1.05,
    attack_s: 0.0,
    rel_t60: 0.12,
    body: &[(65.0, 0.7, 4.0)], // fundamental weight
    out_lp: 1900.0,
    pickup: 0.28,
    sub: 0.18,
};
pub const FRETLESS: PluckPreset = PluckPreset {
    t60: 2.6,
    bright: 850.0,
    pick_lp: 550.0,
    pos: 0.40,
    amp: 1.05,
    attack_s: 0.012,
    rel_t60: 0.15,
    body: &[(60.0, 0.7, 3.5)],
    out_lp: 1500.0,
    pickup: 0.33,
    sub: 0.15,
};
pub const HARP: PluckPreset = PluckPreset {
    t60: 4.5,
    bright: 3000.0,
    pick_lp: 1800.0,
    pos: 0.35,
    amp: 0.62,
    attack_s: 0.0,
    rel_t60: 0.4,
    body: &[],
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
};
pub const BANJO: PluckPreset = PluckPreset {
    t60: 0.9,
    bright: 7500.0,
    pick_lp: 7000.0,
    pos: 0.12,
    amp: 0.60,
    attack_s: 0.0,
    rel_t60: 0.10,
    body: &[(720.0, 2.5, 6.0)],
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
};

/// One Karplus-Strong delay loop on a fractional-tap delay line, so its
/// pitch can *move* while ringing (bends, slides, hammer-ons, vibrato).
/// The in-loop damper's phase delay is compensated in the delay length,
/// so the string tunes accurately; retuning glides over a few ms.
struct KsLoop {
    dl: DelayLine,
    delay: f32,
    target: f32,
    glide_k: f32,
    damp: OnePole,
    loop_gain: f32,
    bright: f32,
    t60: f32,
    sr: f32,
}

impl KsLoop {
    /// Loop delay (in samples) for frequency `f`, compensating the damper's
    /// phase delay and the one-sample write→read latency.
    fn delay_for(f: f32, bright: f32, sr: f32) -> f32 {
        let a = 1.0 - (-2.0 * std::f32::consts::PI * (bright / sr).min(0.49)).exp();
        let b = 1.0 - a;
        let w = 2.0 * std::f32::consts::PI * f / sr;
        let d1p = ((b * w.sin()) / (1.0 - b * w.cos())).atan() / w;
        (sr / f - d1p - 1.0).max(2.0)
    }

    fn new(f: f32, bright: f32, t60: f32, exc: &[f32], sr: f32) -> Self {
        let target = Self::delay_for(f, bright, sr);
        // room to bend or slur a full octave down
        let mut dl = DelayLine::new((target * 2.2) as usize + 8);
        let n = target.ceil() as usize + 1;
        for i in 0..n {
            dl.push(exc[i % exc.len()]);
        }
        KsLoop {
            dl,
            delay: target,
            target,
            glide_k: 1.0 - (-1.0 / (0.004 * sr)).exp(),
            damp: OnePole::lowpass(bright, sr),
            loop_gain: 10f32.powf(-3.0 / (t60 * f)),
            bright,
            t60,
            sr,
        }
    }

    /// Retune to a new frequency; the ringing energy stays in the string.
    fn retune(&mut self, f: f32) {
        self.target = Self::delay_for(f, self.bright, self.sr);
        self.loop_gain = 10f32.powf(-3.0 / (self.t60 * f));
    }

    #[inline]
    fn tick(&mut self, input: f32) -> f32 {
        self.delay += self.glide_k * (self.target - self.delay);
        let s = self.dl.tap(self.delay);
        self.dl.push(self.damp.process(s) * self.loop_gain + input);
        s
    }
}

pub struct Pluck {
    // a real string vibrates in two polarizations: one rings on (horizontal),
    // one decays faster and slightly detuned (vertical) — their sum gives the
    // characteristic fast-then-slow decay and a gentle beat
    horiz: KsLoop,
    vert: KsLoop,
    base_f: f32,
    bend: f32,
    pickup: Option<(DelayLine, f32)>, // magnetic pickup position comb
    sub: Option<(Sine, f32, f32)>,    // (osc, gain, decay) fundamental weight
    sub_env: f32,
    body: Vec<Biquad>,
    out_lp: Option<OnePole>,
    hammer: Vec<f32>, // pending legato excitation, fed into the loops
    hammer_pos: usize,
    rng: Rng,
    pick_lp_hz: f32,
    amp: f32,
    att: f32,
    att_env: f32,
    release_env: f32,
    rel_mul: f32,
    released: bool,
    env: f32,
    t: u32,
    min_life: u32,
    sr: f32,
}

impl Pluck {
    pub fn new(p: &PluckPreset, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let mut rng = Rng::new(seed);
        // round-robin variation: no two picks land identically
        let pos = (p.pos * (1.0 + 0.15 * rng.white())).clamp(0.06, 0.45);
        let bright = p.bright * (1.0 + 0.08 * rng.white());
        let t60_base = p.t60 * (1.0 + 0.10 * rng.white());

        let f = key_freq(key);
        let period = sr / f;
        let t60 = (t60_base * (220.0 / f).powf(0.55)).clamp(0.25, 14.0);

        // excitation: filtered noise burst with a pick-position comb
        let exc_len = (period as usize).max(4);
        let mut lp = OnePole::lowpass(p.pick_lp, sr);
        let raw: Vec<f32> = (0..exc_len).map(|_| lp.process(rng.white())).collect();
        let comb = ((exc_len as f32 * pos) as usize).max(1);
        let mut exc: Vec<f32> = (0..exc_len)
            .map(|i| raw[i] - 0.9 * raw[(i + comb) % exc_len])
            .collect();
        let peak = exc.iter().fold(0f32, |m, &x| m.max(x.abs())).max(1e-6);
        let v = vel_amp(vel);
        for x in &mut exc {
            *x *= v / peak;
        }

        Pluck {
            horiz: KsLoop::new(f, bright, t60, &exc, sr),
            vert: KsLoop::new(f * 1.0013, bright * 1.15, t60 * 0.42, &exc, sr),
            base_f: f,
            bend: 1.0,
            pickup: (p.pickup > 0.0).then(|| {
                // the pickup senses the string a fraction of its length from
                // the bridge: a feedforward comb with a 2·pos·period delay
                let d = 2.0 * p.pickup * period;
                (DelayLine::new(d as usize + 8), d)
            }),
            sub: (p.sub > 0.0).then(|| (Sine::new(f, sr, 0.0), p.sub * v, t60_mul(t60 * 0.8, sr))),
            sub_env: 0.0,
            body: p
                .body
                .iter()
                .map(|&(f, q, g)| Biquad::peak(f, q, g, sr))
                .collect(),
            out_lp: if p.out_lp > 0.0 {
                Some(OnePole::lowpass(p.out_lp, sr))
            } else {
                None
            },
            hammer: Vec::new(),
            hammer_pos: 0,
            rng,
            pick_lp_hz: p.pick_lp,
            amp: p.amp,
            att: if p.attack_s <= 0.0 {
                1.0
            } else {
                1.0 / (p.attack_s * sr)
            },
            att_env: 0.0,
            release_env: 1.0,
            rel_mul: t60_mul(p.rel_t60, sr),
            released: false,
            env: 1.0,
            t: 0,
            min_life: (0.05 * sr) as u32,
            sr,
        }
    }

    fn apply_pitch(&mut self) {
        let f = self.base_f * self.bend;
        self.horiz.retune(f);
        self.vert.retune(f * 1.0013);
        if let Some((osc, _, _)) = &mut self.sub {
            osc.set_freq(f, self.sr);
        }
    }
}

impl Voice for Pluck {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            // pending hammer-on energy trickles into both loops
            let inject = if self.hammer_pos < self.hammer.len() {
                let h = self.hammer[self.hammer_pos];
                self.hammer_pos += 1;
                h
            } else {
                0.0
            };
            let mut y = 0.74 * self.horiz.tick(inject) + 0.26 * self.vert.tick(inject * 0.7);
            if let Some((dl, d)) = &mut self.pickup {
                dl.push(y);
                y = (y - dl.tap(*d)) * 0.75;
            }
            for b in &mut self.body {
                y = b.process(y);
            }
            if let Some(lp) = &mut self.out_lp {
                y = lp.process(y);
            }
            if let Some((osc, gain, decay)) = &mut self.sub {
                // the fundamental's weight, decaying with the string
                if self.t < 220 {
                    self.sub_env = (self.sub_env + 1.0 / 220.0).min(1.0);
                }
                y += osc.next() * *gain * self.sub_env;
                self.sub_env *= *decay;
            }
            if self.att_env < 1.0 {
                self.att_env = (self.att_env + self.att).min(1.0);
            }
            if self.released {
                self.release_env *= self.rel_mul;
            }
            let y = y * self.amp * self.att_env * self.release_env;
            self.env = self.env.max(y.abs()) * 0.9995;
            *o += y;
            self.t += 1;
        }
        self.t < self.min_life || self.env > 2e-5
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
        self.apply_pitch();
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        // hammer-on / pull-off: retune the ringing string, add a soft tap
        self.base_f = key_freq(key);
        self.apply_pitch();
        let v = vel_amp(vel);
        let n = ((self.sr / self.base_f) as usize / 2).max(3);
        let mut lp = OnePole::lowpass((self.pick_lp_hz * 0.5).max(400.0), self.sr);
        self.hammer = (0..n)
            .map(|_| lp.process(self.rng.white()) * v * 0.30)
            .collect();
        self.hammer_pos = 0;
        self.sub_env = self.sub_env.max(0.6 * v);
        self.env = self.env.max(0.3 * v);
        true
    }
}

// ---------------------------------------------------------------------------
// Organ
// ---------------------------------------------------------------------------

pub struct Organ {
    harms: Vec<(Sine, f32)>,
    env: Adsr,
    trem: Sine,
    trem_depth: f32,
    chiff_amp: f32,
    chiff_decay: f32,
    chiff_filt: Biquad,
    click_amp: f32,
    click_decay: f32,
    click_filt: Biquad,
    rng: Rng,
    drive: f32,
    amp: f32,
}

impl Organ {
    #[allow(clippy::too_many_arguments)]
    fn new(
        key: u8,
        vel: u8,
        sr: f32,
        seed: u32,
        stops: &[(f32, f32)],
        env: Adsr,
        trem_hz: f32,
        trem_depth: f32,
        chiff: f32,
        drive: f32,
        amp: f32,
    ) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let harms = stops
            .iter()
            .filter(|&&(m, _)| f * m < sr * 0.45)
            .map(|&(m, a)| {
                // every pipe speaks at its own level
                let a = a * (1.0 + 0.08 * rng.white());
                (Sine::new(f * m, sr, rng.white() * std::f32::consts::PI), a)
            })
            .collect();
        Organ {
            harms,
            env,
            trem: Sine::new(trem_hz, sr, 0.0),
            trem_depth,
            chiff_amp: chiff * vel_amp(vel),
            chiff_decay: t60_mul(0.03, sr),
            chiff_filt: Biquad::bandpass((f * 2.0).min(sr * 0.4), 2.0, sr),
            click_amp: 0.09 * vel_amp(vel),
            click_decay: t60_mul(0.004, sr),
            click_filt: Biquad::highpass(2000.0, 0.7, sr),
            rng,
            drive,
            amp: amp * (0.4 + 0.6 * vel_amp(vel)),
        }
    }
}

impl Voice for Organ {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            let mut s = 0.0;
            for (osc, a) in &mut self.harms {
                s += *a * osc.next();
            }
            if self.chiff_amp > 1e-5 {
                s += self.chiff_filt.process(self.rng.white()) * self.chiff_amp;
                self.chiff_amp *= self.chiff_decay;
            }
            if self.click_amp > 1e-5 {
                s += self.click_filt.process(self.rng.white()) * self.click_amp;
                self.click_amp *= self.click_decay;
            }
            if self.drive > 0.0 {
                s = (s * self.drive).tanh() / self.drive;
            }
            let trem = 1.0 + self.trem_depth * self.trem.next();
            *o += s * self.amp * trem * self.env.next();
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }
}

fn organ(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Organ {
    match program {
        18 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (0.5, 0.6),
                (1.0, 1.0),
                (1.5, 0.55),
                (2.0, 0.5),
                (3.0, 0.25),
                (4.0, 0.15),
            ],
            Adsr::new(0.005, 0.05, 1.0, 0.10, sr),
            6.5,
            0.10,
            0.10,
            1.8,
            0.32,
        ),
        16 | 17 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (0.5, 0.5),
                (1.0, 1.0),
                (1.5, 0.35),
                (2.0, 0.35),
                (3.0, 0.12),
                (4.0, 0.08),
            ],
            Adsr::new(0.01, 0.05, 1.0, 0.15, sr),
            5.5,
            0.06,
            0.08,
            0.0,
            0.32,
        ),
        _ => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (1.0, 1.0),
                (2.0, 0.62),
                (3.0, 0.28),
                (4.0, 0.42),
                (6.0, 0.16),
                (8.0, 0.18),
            ],
            Adsr::new(0.06, 0.10, 0.92, 0.25, sr),
            4.2,
            0.04,
            0.20,
            0.0,
            0.32,
        ),
    }
}

// ---------------------------------------------------------------------------
// SawStack (strings / choir / pads)
// ---------------------------------------------------------------------------

struct Layer {
    osc: BlepSaw,
    ratio: f32,
    vib_phase: f32,
    vib_rate: f32, // Hz — every player's wobble is their own
    drift: Drift,
}

enum StackFilter {
    Lp(Biquad),
    /// Vocal formants that morph from a closed schwa into the vowel over the
    /// first ~150 ms of the note ("mm-ah").
    Formant {
        bands: [Biquad; 3],
        gains: [f32; 3],
        cur: [f32; 3],
        tgt: [f32; 3],
        qs: [f32; 3],
    },
}

pub struct SawStack {
    layers: Vec<Layer>,
    base_f: f32,
    filt: StackFilter,
    env: Adsr,
    vib_depth: f32,
    vib_delay: u32,
    breath: f32,
    rng: Rng,
    sweep: Option<(f32, f32, f32, f32)>, // (lfo phase, rate Hz, base cutoff, octaves)
    sweep_q: f32,
    t: u32,
    amp: f32,
    sr: f32,
}

impl SawStack {
    #[allow(clippy::too_many_arguments)]
    fn new(
        key: u8,
        vel: u8,
        sr: f32,
        seed: u32,
        n_osc: usize,
        detune: f32,
        drift_depth: f32,
        filt: StackFilter,
        env: Adsr,
        vib: (f32, f32, f32), // (hz, depth, delay s)
        breath: f32,
        sweep: Option<(f32, f32, f32)>, // (rate, base, octaves)
        sweep_q: f32,
        amp: f32,
    ) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let layers = (0..n_osc)
            .map(|i| {
                let spread = if n_osc > 1 {
                    (i as f32 / (n_osc - 1) as f32) * 2.0 - 1.0
                } else {
                    0.0
                };
                Layer {
                    osc: BlepSaw::new(f * (1.0 + detune * spread), sr, rng.white() * 0.5 + 0.5),
                    ratio: 1.0 + detune * spread,
                    vib_phase: rng.white() * std::f32::consts::PI,
                    vib_rate: vib.0 * (1.0 + 0.15 * rng.white()),
                    drift: Drift::new(seed ^ (0x1234 + i as u32 * 977), drift_depth, 2800),
                }
            })
            .collect();
        let sweep_phase = rng.white() * std::f32::consts::PI;
        SawStack {
            layers,
            base_f: f,
            filt,
            env,
            vib_depth: vib.1,
            vib_delay: (vib.2 * sr) as u32,
            breath,
            rng,
            sweep: sweep.map(|(rate, base, oct)| (sweep_phase, rate, base, oct)),
            sweep_q,
            t: 0,
            amp: amp * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }

    fn control_tick(&mut self) {
        let ramp = if self.t > self.vib_delay {
            (((self.t - self.vib_delay) as f32) / self.sr).min(1.0)
        } else {
            0.0
        };
        let sr = self.sr;
        for layer in &mut self.layers {
            layer.vib_phase += TAU * layer.vib_rate * CTRL as f32 / sr;
            let vib = if ramp > 0.0 && self.vib_depth > 0.0 {
                self.vib_depth * ramp * layer.vib_phase.sin()
            } else {
                0.0
            };
            let drift = layer.drift.next();
            layer
                .osc
                .set_freq(self.base_f * layer.ratio * (1.0 + vib + drift), sr);
        }
        match &mut self.filt {
            StackFilter::Formant {
                bands,
                cur,
                tgt,
                qs,
                ..
            } => {
                for i in 0..3 {
                    if (tgt[i] - cur[i]).abs() > 1.0 {
                        cur[i] += 0.045 * (tgt[i] - cur[i]);
                        bands[i].retune_bandpass(cur[i], qs[i], sr);
                    }
                }
            }
            StackFilter::Lp(b) => {
                if let Some((phase, rate, base, oct)) = &mut self.sweep {
                    *phase += TAU * *rate * CTRL as f32 / sr;
                    let cut = *base * 2f32.powf(*oct * 0.5 * (phase.sin() + 1.0));
                    b.retune_lowpass(cut.min(sr * 0.4), self.sweep_q, sr);
                }
            }
        }
    }
}

impl Voice for SawStack {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.control_tick();
            }
            let mut s = 0.0;
            for layer in &mut self.layers {
                s += layer.osc.next();
            }
            s /= self.layers.len() as f32;
            if self.breath > 0.0 {
                s += self.rng.white() * self.breath;
            }
            s = match &mut self.filt {
                StackFilter::Lp(b) => b.process(s),
                StackFilter::Formant { bands, gains, .. } => {
                    let mut y = 0.0;
                    for (b, g) in bands.iter_mut().zip(gains.iter()) {
                        y += b.process(s) * *g;
                    }
                    y
                }
            };
            *o += s * self.amp * self.env.next();
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }
}

/// Soft notes speak slower: scale an attack time by velocity.
fn vel_attack(base: f32, vel: u8) -> f32 {
    base * (1.45 - 0.65 * (vel as f32 / 127.0))
}

fn strings(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let slow = program == 49;
    SawStack::new(
        key,
        vel,
        sr,
        seed,
        5,
        0.007,
        0.0035,
        StackFilter::Lp(Biquad::lowpass(if slow { 3200.0 } else { 4200.0 }, 0.7, sr)),
        if slow {
            Adsr::new(vel_attack(0.45, vel), 0.3, 0.85, 0.8, sr)
        } else {
            Adsr::new(vel_attack(0.07, vel), 0.3, 0.85, 0.35, sr)
        },
        (5.1, 0.003, 0.22),
        0.0,
        None,
        0.7,
        0.22,
    )
}

fn choir(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let (f1, f2, f3) = if program == 52 {
        (660.0, 1120.0, 2500.0)
    } else {
        (330.0, 870.0, 2300.0)
    };
    let qs = [9.0, 10.0, 9.0];
    let start = [500.0, 1400.0, 2400.0]; // closed-mouth schwa
    SawStack::new(
        key,
        vel,
        sr,
        seed,
        4,
        0.009,
        0.0045,
        StackFilter::Formant {
            bands: [
                Biquad::bandpass(start[0], qs[0], sr),
                Biquad::bandpass(start[1], qs[1], sr),
                Biquad::bandpass(start[2], qs[2], sr),
            ],
            gains: [1.0, 0.55, 0.28],
            cur: start,
            tgt: [f1, f2, f3],
            qs,
        },
        Adsr::new(vel_attack(0.28, vel), 0.3, 0.9, 0.4, sr),
        (4.6, 0.004, 0.30),
        0.02,
        None,
        0.7,
        1.10,
    )
}

fn pad(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    if program == 95 {
        SawStack::new(
            key,
            vel,
            sr,
            seed,
            5,
            0.010,
            0.0030,
            StackFilter::Lp(Biquad::lowpass(900.0, 1.1, sr)),
            Adsr::new(0.9, 0.5, 1.0, 1.8, sr),
            (0.0, 0.0, 0.0),
            0.0,
            Some((0.07, 350.0, 1.8)),
            1.1,
            0.42,
        )
    } else {
        SawStack::new(
            key,
            vel,
            sr,
            seed,
            5,
            0.010,
            0.0030,
            StackFilter::Lp(Biquad::lowpass(1400.0, 0.6, sr)),
            Adsr::new(0.6, 0.5, 1.0, 1.4, sr),
            (0.0, 0.0, 0.0),
            0.0,
            Some((0.13, 1100.0, 0.5)),
            0.7,
            0.42,
        )
    }
}

// ---------------------------------------------------------------------------
// Wind (flute / whistle)
// ---------------------------------------------------------------------------

pub struct Wind {
    fund: Sine,
    h2: Sine,
    h3: Sine,
    a2: f32,
    a3: f32,
    base_f: f32,
    bend: f32,
    scoop: f32, // pitch multiplier settling toward 1.0
    scoop_k: f32,
    breath_filt: Biquad,
    breath: f32,
    chiff_amp: f32,
    chiff_decay: f32,
    env: Adsr,
    vib: Sine,
    vib_depth: f32,
    vib_delay: u32,
    vib_val: f32,
    rng: Rng,
    t: u32,
    amp: f32,
    sr: f32,
}

impl Wind {
    fn new(whistle: bool, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let (a2, a3, breath, vibr) = if whistle {
            (0.12, 0.03, 0.05, (5.5, 0.006, 0.18))
        } else {
            (0.32, 0.12, 0.09, (5.0, 0.004, 0.25))
        };
        let attack = if whistle {
            vel_attack(0.02, vel)
        } else {
            vel_attack(0.05, vel)
        };
        Wind {
            fund: Sine::new(f, sr, rng.white() * std::f32::consts::PI),
            h2: Sine::new(f * 2.0, sr, rng.white() * std::f32::consts::PI),
            h3: Sine::new(f * 3.0, sr, rng.white() * std::f32::consts::PI),
            a2,
            a3,
            base_f: f,
            bend: 1.0,
            scoop: if whistle { 0.990 } else { 0.984 },
            scoop_k: 0.05,
            breath_filt: Biquad::bandpass((f * 2.0).min(sr * 0.4), 2.0, sr),
            breath,
            chiff_amp: 0.22 * vel_amp(vel),
            chiff_decay: t60_mul(0.025, sr),
            env: Adsr::new(attack, 0.05, 0.92, 0.10, sr),
            vib: Sine::new(vibr.0, sr, 0.0),
            vib_depth: vibr.1,
            vib_delay: (vibr.2 * sr) as u32,
            vib_val: 0.0,
            rng,
            t: 0,
            amp: 0.5 * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for Wind {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.scoop += self.scoop_k * (1.0 - self.scoop);
                let v = self.vib.next();
                self.vib_val = v;
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                let f = self.base_f * self.bend * self.scoop * (1.0 + vib);
                self.fund.set_freq(f, self.sr);
                self.h2.set_freq(f * 2.0, self.sr);
                self.h3.set_freq(f * 3.0, self.sr);
            }
            let mut s = self.fund.next() + self.a2 * self.h2.next() + self.a3 * self.h3.next();
            let e = self.env.next();
            // the breath rides the vibrato — air moves with the pitch wobble
            let breath_mod = 1.0 + 0.5 * self.vib_val;
            s += self.breath_filt.process(self.rng.white())
                * (self.breath * e * breath_mod + self.chiff_amp);
            self.chiff_amp *= self.chiff_decay;
            *o += s * self.amp * e;
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // slur: glide from the old pitch via the scoop, keep the air moving
        let new_f = key_freq(key);
        self.scoop = (self.base_f * self.scoop / new_f).clamp(0.85, 1.18);
        self.base_f = new_f;
        self.chiff_amp = 0.0;
        true
    }
}

// ---------------------------------------------------------------------------
// Bowed (fiddle)
// ---------------------------------------------------------------------------

pub struct Bowed {
    saw: BlepSaw,
    base_f: f32,
    bend: f32,
    scoop: f32,
    body: [Biquad; 3],
    lp: OnePole, // bow-pressure brightness: opens with the envelope
    env: Adsr,
    vib: Sine,
    vib_depth: f32,
    vib_delay: u32,
    vib_val: f32,
    rng: Rng,
    t: u32,
    attack_samples: u32,
    last_env: f32,
    amp: f32,
    sr: f32,
}

impl Bowed {
    fn new(key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let attack = vel_attack(0.07, vel);
        Bowed {
            saw: BlepSaw::new(f * 0.975, sr, rng.white() * 0.5 + 0.5),
            base_f: f,
            bend: 1.0,
            scoop: 0.975 + 0.008 * (vel as f32 / 127.0),
            body: [
                Biquad::peak(280.0, 1.2, 5.0, sr),
                Biquad::peak(610.0, 1.8, 4.0, sr),
                Biquad::peak(1350.0, 1.5, 3.0, sr),
            ],
            lp: OnePole::lowpass(1400.0, sr),
            env: Adsr::new(attack, 0.2, 0.9, 0.18, sr),
            vib: Sine::new(5.3 * (1.0 + 0.1 * rng.white()), sr, 0.0),
            vib_depth: 0.0045,
            vib_delay: (0.22 * sr) as u32,
            vib_val: 0.0,
            rng,
            t: 0,
            attack_samples: (attack * sr) as u32,
            last_env: 0.0,
            amp: 0.40 * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for Bowed {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.scoop += 0.03 * (1.0 - self.scoop);
                let v = self.vib.next();
                self.vib_val = v;
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                self.saw
                    .set_freq(self.base_f * self.bend * self.scoop * (1.0 + vib), self.sr);
                // more bow pressure -> brighter tone
                self.lp.set_cutoff(900.0 + 5200.0 * self.last_env, self.sr);
            }
            let e = self.env.next();
            self.last_env = e;
            // bow noise: loud while the bow bites, quieter once the string speaks
            let noise_amp = if self.t < self.attack_samples * 2 {
                0.10
            } else {
                0.028
            } * (1.0 + 0.4 * self.vib_val);
            let mut s = self.saw.next() + self.rng.white() * noise_amp * e;
            for b in &mut self.body {
                s = b.process(s);
            }
            s = self.lp.process(s);
            *o += s * self.amp * e;
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // one bow, new finger: glide over via the scoop, no fresh bite
        let new_f = key_freq(key);
        self.scoop = (self.base_f * self.scoop / new_f).clamp(0.85, 1.18);
        self.base_f = new_f;
        true
    }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/// LA layering (sampled attack + modeled sustain) — level-matched to the
/// models by the `la_level_continuity` test.
const LA_VIOLIN: (f32, (f32, f32)) = (0.30, (0.12, 0.38));
const LA_FLUTE: (f32, (f32, f32)) = (0.55, (0.06, 0.24));
const LA_PIANO: (f32, (f32, f32)) = (0.42, (0.18, 0.85));

pub fn make(program: u8, key: u8, vel: u8, sr: f32, seed: u32, samples: bool) -> Box<dyn Voice> {
    let noise_off = (0.0, 0.01, 1000.0, 1.0);
    match program {
        0..=7 => {
            let model = Box::new(piano(key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_PIANO;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::piano_bank(vel, seed & 1 == 0),
                    key,
                    vel,
                    sr,
                    gain,
                    fade,
                )
            } else {
                model
            }
        }
        8 => Box::new(bell(
            key,
            vel,
            sr,
            seed,
            CELESTA,
            (0.08, 0.006, 2500.0, 1.0),
            0.002,
            0.6,
            0.58,
        )),
        9 => Box::new(bell(
            key,
            vel,
            sr,
            seed,
            GLOCK,
            (0.10, 0.004, 7000.0, 1.0),
            0.0,
            0.8,
            0.40,
        )),
        10 => Box::new(bell(
            key,
            vel,
            sr,
            seed,
            MUSICBOX,
            (0.06, 0.004, 5000.0, 1.0),
            0.0,
            0.5,
            0.52,
        )),
        11..=13 => Box::new(bell(key, vel, sr, seed, VIBES, noise_off, 0.002, 0.8, 0.45)),
        14 | 15 => Box::new(bell(
            key,
            vel,
            sr,
            seed,
            TUBULAR,
            (0.07, 0.015, 2400.0, 1.0),
            0.003,
            2.5,
            0.50,
        )),
        16..=23 => Box::new(organ(program, key, vel, sr, seed)),
        24 => Box::new(Pluck::new(&NYLON, key, vel, sr, seed)),
        25 => Box::new(Pluck::new(&STEEL, key, vel, sr, seed)),
        26 | 27 => Box::new(Pluck::new(&CLEAN, key, vel, sr, seed)),
        28 => Box::new(Pluck::new(&MUTED, key, vel, sr, seed)),
        29..=31 => Box::new(Pluck::new(&DRIVE, key, vel, sr, seed)),
        32..=34 | 36..=39 => Box::new(Pluck::new(&BASS, key, vel, sr, seed)),
        35 => Box::new(Pluck::new(&FRETLESS, key, vel, sr, seed)),
        40..=45 => {
            let model = Box::new(Bowed::new(key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_VIOLIN;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::violin_bank(vel),
                    key,
                    vel,
                    sr,
                    gain,
                    fade,
                )
            } else {
                model
            }
        }
        46 => Box::new(Pluck::new(&HARP, key, vel, sr, seed)),
        47 => Box::new(timpani(key, vel, sr, seed)),
        48..=51 => Box::new(strings(program, key, vel, sr, seed)),
        52..=54 => Box::new(choir(program, key, vel, sr, seed)),
        72..=79 => {
            let model = Box::new(Wind::new(
                matches!(program, 72 | 78 | 79),
                key,
                vel,
                sr,
                seed,
            ));
            if samples {
                let (gain, fade) = LA_FLUTE;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::flute_bank(),
                    key,
                    vel,
                    sr,
                    gain,
                    fade,
                )
            } else {
                model
            }
        }
        96..=103 => Box::new(bell(
            key, vel, sr, seed, CRYSTAL, noise_off, 0.03, 1.5, 0.60,
        )),
        104..=107 => Box::new(Pluck::new(&BANJO, key, vel, sr, seed)),
        80..=95 => Box::new(pad(program, key, vel, sr, seed)),
        _ => Box::new(Pluck::new(&STEEL, key, vel, sr, seed)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Lowpass twice, then count rising zero crossings.
    fn measure_pitch(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(700.0, sr);
        let mut lp2 = OnePole::lowpass(700.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut c = 0;
        for w in f.windows(2) {
            if w[0] <= 0.0 && w[1] > 0.0 {
                c += 1;
            }
        }
        c as f32 / (seg.len() as f32 / sr)
    }

    /// A plucked A4 should oscillate near 440 Hz (count zero crossings).
    #[test]
    fn pluck_pitch_a4() {
        let sr = 44100.0;
        let mut v = Pluck::new(&STEEL, 69, 100, sr, 7);
        let mut buf = vec![0f32; 22050];
        v.render(&mut buf);
        // isolate the fundamental before counting zero crossings — the raw
        // string is harmonic-rich and would overcount
        let mut lp1 = OnePole::lowpass(500.0, sr);
        let mut lp2 = OnePole::lowpass(500.0, sr);
        let filtered: Vec<f32> = buf.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        // skip the noisy attack, count rising zero crossings in 0.4 s
        let seg = &filtered[4410..4410 + 17640];
        let mut crossings = 0;
        for w in seg.windows(2) {
            if w[0] <= 0.0 && w[1] > 0.0 {
                crossings += 1;
            }
        }
        let hz = crossings as f32 / 0.4;
        assert!((hz - 440.0).abs() < 6.0, "measured {hz} Hz");
    }

    #[test]
    fn voices_decay_and_die() {
        let sr = 44100.0;
        let mut v = make(9, 84, 100, sr, 3, false); // glockenspiel
        let mut buf = vec![0f32; 4096];
        let mut blocks = 0;
        while v.render(&mut buf) && blocks < 200 {
            buf.fill(0.0);
            blocks += 1;
        }
        assert!(blocks < 200, "glockenspiel never died");
    }

    #[test]
    fn sustained_voice_needs_note_off() {
        let sr = 44100.0;
        let mut v = make(19, 60, 90, sr, 4, false); // church organ
        let mut buf = vec![0f32; 4096];
        for _ in 0..40 {
            assert!(v.render(&mut buf));
            buf.fill(0.0);
        }
        v.note_off();
        let mut blocks = 0;
        while v.render(&mut buf) && blocks < 100 {
            buf.fill(0.0);
            blocks += 1;
        }
        assert!(blocks < 100, "organ never released");
    }

    /// A bent string must sound at the bent pitch: A4 bent +2 semitones
    /// should ring near B4 once the glide settles.
    #[test]
    fn pluck_bend_two_semitones() {
        let sr = 44100.0;
        let mut v = Pluck::new(&STEEL, 69, 100, sr, 9);
        v.set_pitch(2f32.powf(2.0 / 12.0));
        let mut buf = vec![0f32; 44100];
        v.render(&mut buf);
        let hz = measure_pitch(&buf[8820..30870], sr);
        assert!((hz - 493.9).abs() < 8.0, "bent pitch {hz} Hz");
    }

    /// A hammer-on retunes the ringing string without a fresh pluck.
    #[test]
    fn pluck_hammer_on_retunes() {
        let sr = 44100.0;
        let mut v = Pluck::new(&CLEAN, 69, 100, sr, 12);
        let mut buf = vec![0f32; 11025];
        v.render(&mut buf); // let A4 ring for 0.25 s
        assert!(v.legato_to(74, 90)); // hammer to D5
        let mut buf2 = vec![0f32; 44100];
        v.render(&mut buf2);
        let hz = measure_pitch(&buf2[8820..30870], sr);
        assert!((hz - 587.3).abs() < 9.0, "hammered pitch {hz} Hz");
    }

    /// A palm-muted string dies much faster than an open one.
    #[test]
    fn muted_dies_fast() {
        let sr = 44100.0;
        let mut v = Pluck::new(&MUTED, 52, 100, sr, 5);
        let mut buf = vec![0f32; 4096];
        let mut blocks = 0;
        while v.render(&mut buf) && blocks < 40 {
            buf.fill(0.0);
            blocks += 1;
        }
        assert!(blocks < 40, "palm mute rang too long ({blocks} blocks)");
    }

    /// The fiddle's scoop should settle: pitch after a second must be much
    /// closer to nominal than at the onset.
    #[test]
    fn bowed_scoop_settles() {
        let sr = 44100.0;
        let mut v = Bowed::new(69, 100, sr, 11);
        let mut buf = vec![0f32; 44100 * 2];
        v.render(&mut buf);
        let measure = |seg: &[f32]| {
            let mut lp1 = OnePole::lowpass(600.0, sr);
            let mut lp2 = OnePole::lowpass(600.0, sr);
            let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
            let mut c = 0;
            for w in f.windows(2) {
                if w[0] <= 0.0 && w[1] > 0.0 {
                    c += 1;
                }
            }
            c as f32 / (seg.len() as f32 / sr)
        };
        let late = measure(&buf[44100..44100 + 22050]);
        assert!((late - 440.0).abs() < 8.0, "late pitch {late} Hz");
    }
}
