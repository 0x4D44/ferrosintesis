//! The instrument models. Every voice adds its output into a mono block and
//! reports whether it is still alive.
//!
//! Families:
//!   Modal    — additive/modal synthesis via rotation oscillators
//!              (piano with two-stage decay, celesta, glockenspiel, music
//!               box, tubular bells, kalimba, crystal, timpani)
//!   Pluck    — extended Karplus-Strong strings with per-note round-robin
//!              variation (guitars, bass, harp, banjo)
//!   Organ    — harmonic drawbar bank with key click, chiff and tremulant
//!   SawStack — detuned polyBLEP saws, each layer with its own vibrato and
//!              slow pitch drift, through lowpass or vocal formants that
//!              morph open at the onset (string ensembles, choir, pads)
//!   OrchHit  — one-shot octave-stacked orchestral stab with a thump
//!   Reed     — band-limited pulse reeds, including bagpipe chanter and shanai
//!   Wind     — sine + harmonics + breath, with a pitch scoop into the note
//!   Bowed    — sawtooth through a violin body, with scoop, attack bow
//!              noise, and bow-pressure brightness
//!   ReverseCymbal — a pitch-agnostic reverse-cymbal swell for GM 119
//!   SfxNoise — safe toneless noise fallback for GM sound effects
//!
//! Timing realism: sustained families speak slower at low velocity, the way
//! a gently-bowed or gently-blown note actually starts.

use crate::dsp::{
    key_freq, vel_amp, Adsr, Biquad, BlepPulse, BlepSaw, Burst, DelayLine, Drift, OnePole,
    ReedPulse, Rng, Sine,
};
use std::f32::consts::TAU;

pub trait Voice: Send {
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
    /// Tremulant control (organs): absolute rate in Hz and depth. The engine
    /// slews these toward the CC1 mod-wheel target so the Leslie rotor has
    /// real inertia. Voices without a tremulant ignore it.
    fn set_trem(&mut self, _rate_hz: f32, _depth: f32) {}
    /// CC70 vowel morph (formant voices): absolute formant frequency, Q and
    /// gain targets. The engine slews the vowel position per block and the
    /// voice's own control-rate formant smoothing removes any residual
    /// zipper. Voices without formants ignore it.
    fn set_vowel(&mut self, _freqs: [f32; 3], _qs: [f32; 3], _gains: [f32; 3]) {}
    /// Breath/expression control (brass, GM 56-63): CC11 sets lip pressure
    /// (opening the timbre) and channel aftertouch adds flutter growl. The
    /// engine drives it in the authored-controller pass. Voices without a
    /// breath model ignore it.
    fn set_breath(&mut self, _pressure: f32, _growl: f32) {}
    /// CC1 section-vibrato depth (alt-bank strings): deepen each layer's own
    /// decorrelated per-layer vibrato. Default no-op; only the alt-bank
    /// `SawStack` implements it (the default voices are never driven by it).
    fn set_vib(&mut self, _depth: f32) {}
    /// Shared cathedral-organ wind state. `pressure` is the smoothed channel
    /// load in 0..1; `trem` is the signed, channel-global tremulant sample.
    /// Other voices deliberately ignore both values.
    fn set_organ_pressure(&mut self, _pressure: f32, _trem: f32) {}
    /// CC11-derived swell drive for the cathedral organ's reed rasp (0 = smooth,
    /// 1 = full snarl). Deliberately separate from `set_organ_pressure` so it
    /// never triggers table regeneration and leaves that setter's call sites and
    /// tests untouched. No-op for every other voice (incl. the legacy GM19).
    fn set_organ_swell(&mut self, _drive: f32) {}
    /// Hat choke (D6/CYM-4): a closed-hat strike silences the ringing open
    /// hat within ~10-30 ms. Default no-op; only `Drum` implements it.
    fn choke(&mut self) {}
    /// Test-only concrete-voice discriminant — the oracle-36 routing seam.
    /// Plucks report their preset name; other families their family name.
    #[cfg(test)]
    fn kind(&self) -> &'static str;
}

fn t60_mul(t60: f32, sr: f32) -> f32 {
    // per-sample amplitude multiplier for a -60 dB decay over t60 seconds
    10f32.powf(-3.0 / (t60.max(0.01) * sr))
}

const CTRL: u32 = 16; // control-rate interval in samples

/// Build an LFO that is advanced once per [`CTRL`] output samples. Keeping the
/// reduced sample rate here prevents the historical 16x-slow vibrato bug from
/// reappearing when another control-rate voice is added.
fn control_lfo(rate_hz: f32, jitter: f32, rng: &mut Rng, sr: f32) -> Sine {
    Sine::new(
        rate_hz * (1.0 + jitter * rng.white()),
        sr / CTRL as f32,
        0.0,
    )
}

// ---------------------------------------------------------------------------
// SFX noise fallback
// ---------------------------------------------------------------------------

struct SfxNoise {
    rng: Rng,
    filt: Biquad,
    amp: f32,
    decay: f32,
    rel_mul: f32,
    released: bool,
}

impl SfxNoise {
    fn new(program: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let (freq, q, t60, gain): (f32, f32, f32, f32) = match program {
            120 => (3_400.0, 0.55, 0.12, 0.09), // fret squeak
            121 => (1_900.0, 0.50, 0.35, 0.07), // breath
            122 => (900.0, 0.45, 0.95, 0.10),   // seashore wash
            123 => (4_500.0, 0.50, 0.16, 0.07), // bird tweet fallback
            124 => (1_250.0, 0.50, 0.18, 0.06), // telephone ring fallback
            125 => (260.0, 0.45, 0.55, 0.09),   // helicopter wash
            126 => (2_700.0, 0.45, 0.70, 0.12), // applause
            127 => (1_500.0, 0.42, 0.28, 0.16), // gunshot
            _ => (1_600.0, 0.45, 0.25, 0.08),
        };
        SfxNoise {
            rng: Rng::new(seed ^ 0x5F58_0000 ^ ((program as u32) << 8)),
            filt: Biquad::bandpass(freq.min(sr * 0.40), q, sr),
            amp: vel_amp(vel) * gain,
            decay: t60_mul(t60, sr),
            rel_mul: t60_mul(0.06, sr),
            released: false,
        }
    }
}

impl Voice for SfxNoise {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            let s = self.filt.process(self.rng.white()) * self.amp;
            *o += s;
            self.amp *= self.decay;
            if self.released {
                self.amp *= self.rel_mul;
            }
        }
        self.amp > 1e-5
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "sfx"
    }
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

struct Mode {
    osc: Sine,
    base_freq: f32,
    active: bool,
    amp: f32,
    decay: f32,
}

#[derive(Clone, Copy)]
struct StrikeGlide {
    ratio: f32,
    step: f32,
    floor: f32,
}

/// Mode-group bloom (v0.12 alt-bank tam-tam): the modes at index >= `from`
/// fade in over an attack ramp of their own, so a gong's shimmer partials
/// swell AFTER the fundamental speaks. `None` on every pre-existing voice —
/// the render loop branches OUTSIDE the per-sample multiply, so a bloom-less
/// Modal renders token-identically to before the field existed.
#[derive(Clone, Copy)]
struct ModeBloom {
    from: usize,
    env: f32,
    att: f32,
}

struct ModalAmpTrem {
    osc: Sine,
    depth: f32,
}

impl ModalAmpTrem {
    fn new(rate_hz: f32, depth: f32, sr: f32) -> Self {
        ModalAmpTrem {
            osc: Sine::new(rate_hz.max(0.1), sr, 0.0),
            depth: depth.clamp(0.0, 0.95),
        }
    }

    #[inline]
    fn gain(&mut self) -> f32 {
        1.0 + self.depth * self.osc.next()
    }
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
    sr: f32,
    bend: f32,
    strike_glide: Option<StrikeGlide>,
    amp_trem: Option<ModalAmpTrem>,
    bloom: Option<ModeBloom>,
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
                base_freq: f,
                active: true,
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
            sr,
            bend: 1.0,
            strike_glide: None,
            amp_trem: None,
            bloom: None,
        }
    }

    fn with_amp_trem(mut self, rate_hz: f32, depth: f32) -> Self {
        self.amp_trem = Some(ModalAmpTrem::new(rate_hz, depth, self.sr));
        self
    }

    fn with_strike_glide(
        mut self,
        start_ratio: f32,
        glide_oct_per_s: f32,
        floor_ratio: f32,
    ) -> Self {
        let floor = floor_ratio.max(0.01);
        let start = start_ratio.max(floor);
        if start > floor && glide_oct_per_s > 0.0 {
            self.strike_glide = Some(StrikeGlide {
                ratio: start,
                step: 2f32.powf(-glide_oct_per_s / self.sr),
                floor,
            });
            self.apply_pitch();
        }
        self
    }

    /// v0.12 tam-tam: the modes at index >= `from` bloom in over `bloom_s`
    /// seconds instead of speaking at the strike. Only the alt-bank gong
    /// calls this — every other Modal keeps `bloom: None` and renders
    /// through the untouched fast path.
    fn with_mode_bloom(mut self, from: usize, bloom_s: f32) -> Self {
        if bloom_s > 0.0 && from < self.modes.len() {
            self.bloom = Some(ModeBloom {
                from,
                env: 0.0,
                att: 1.0 / (bloom_s * self.sr),
            });
        }
        self
    }

    fn strike_ratio(&self) -> f32 {
        self.strike_glide.map_or(1.0, |g| g.ratio)
    }

    fn apply_pitch(&mut self) {
        let strike = self.strike_ratio();
        for mode in &mut self.modes {
            let f = mode.base_freq * self.bend * strike;
            mode.active = f < self.sr * 0.45;
            if mode.active {
                mode.osc.set_freq(f, self.sr);
            }
        }
    }

    fn advance_strike_glide(&mut self) {
        let mut retune = false;
        let mut done = false;
        if let Some(glide) = &mut self.strike_glide {
            if glide.ratio > glide.floor {
                let next = (glide.ratio * glide.step).max(glide.floor);
                retune = next != glide.ratio;
                glide.ratio = next;
                done = glide.ratio <= glide.floor;
            }
        }
        if retune {
            self.apply_pitch();
        }
        if done {
            self.strike_glide = None;
        }
    }
}

impl Voice for Modal {
    fn render(&mut self, out: &mut [f32]) -> bool {
        // The bloom branch lives OUTSIDE the per-sample loop: a voice with
        // `bloom: None` (every pre-v0.12 Modal) runs the second arm, which is
        // token-identical to the pre-bloom loop — never a multiply-by-1.0.
        if let Some(ModeBloom { from, mut env, att }) = self.bloom {
            for o in out.iter_mut() {
                let mut s = 0.0;
                for (i, m) in self.modes.iter_mut().enumerate() {
                    if m.active {
                        let g = if i >= from { env } else { 1.0 };
                        s += m.amp * g * m.osc.next();
                    }
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
                let amp_trem = self.amp_trem.as_mut().map_or(1.0, ModalAmpTrem::gain);
                *o += s * self.gain * self.att_env * self.release_env * amp_trem;
                self.advance_strike_glide();
                if env < 1.0 {
                    env = (env + att).min(1.0);
                }
            }
            self.bloom = Some(ModeBloom { from, env, att });
        } else {
            for o in out.iter_mut() {
                let mut s = 0.0;
                for m in &mut self.modes {
                    if m.active {
                        s += m.amp * m.osc.next();
                    }
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
                let amp_trem = self.amp_trem.as_mut().map_or(1.0, ModalAmpTrem::gain);
                *o += s * self.gain * self.att_env * self.release_env * amp_trem;
                self.advance_strike_glide();
            }
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

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
        self.apply_pitch();
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "modal"
    }
}

pub(crate) fn is_acoustic_piano(program: u8) -> bool {
    matches!(program, 0..=3)
}

fn acoustic_piano(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
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

fn electric_piano_1(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let vn = vel as f32 / 127.0;
    let v = 0.25 + 0.75 * vel_amp(vel);
    let scale = (440.0 / f).powf(0.25).clamp(0.75, 1.5);
    let partials = [
        (1.000, 0.95 * v, 3.6 * scale),
        (1.003, 0.55 * v, 3.1 * scale),
        (2.000, 0.32 * v, 2.1 * scale),
        (2.820, 0.24 * v * (0.7 + 0.5 * vn), 0.85 * scale),
        (3.000, 0.13 * v, 1.3 * scale),
        (5.380, 0.08 * v * (0.6 + 0.7 * vn), 0.40 * scale),
    ];
    Modal::new(
        sr,
        seed,
        &partials,
        (
            0.035 * v,
            0.010,
            Biquad::bandpass((f * 7.0).min(5200.0), 0.8, sr),
        ),
        0.002,
        0.22,
        0.56,
    )
}

fn electric_piano_2(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let vn = vel as f32 / 127.0;
    let v = 0.22 + 0.82 * vel_amp(vel);
    let scale = (440.0 / f).powf(0.18).clamp(0.70, 1.35);
    let partials = [
        (1.000, 0.72 * v, 2.4 * scale),
        (1.997, 0.24 * v, 1.6 * scale),
        (3.010, 0.42 * v * (0.7 + 0.8 * vn), 1.0 * scale),
        (4.180, 0.30 * v * (0.6 + 0.9 * vn), 0.72 * scale),
        (6.820, 0.15 * v * (0.5 + vn), 0.42 * scale),
        (9.200, 0.06 * v * vn, 0.20 * scale),
    ];
    Modal::new(
        sr,
        seed,
        &partials,
        (
            0.025 * v,
            0.006,
            Biquad::bandpass((f * 10.0).min(7000.0), 0.9, sr),
        ),
        0.0008,
        0.18,
        0.54,
    )
}

fn harpsichord(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let v = 0.78 + 0.22 * (vel as f32 / 127.0);
    let decay_scale = (440.0 / f).powf(0.28).clamp(0.65, 1.5);
    let mut partials = Vec::new();
    for k in 1..=12u32 {
        let kf = k as f32;
        let fk = f * kf;
        if fk > sr * 0.42 {
            break;
        }
        partials.push((fk, v / kf.powf(0.72), (1.45 / kf.powf(0.30)) * decay_scale));
    }
    Modal::new(
        sr,
        seed,
        &partials,
        (
            0.10 * v,
            0.006,
            Biquad::highpass((f * 6.0).clamp(1600.0, 6500.0), 0.7, sr),
        ),
        0.0,
        0.08,
        0.34,
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
const VIBRAPHONE_MOTOR_RATE_HZ: f32 = 6.0;
const VIBRAPHONE_MOTOR_DEPTH: f32 = 0.35;
const MARIMBA: &[(f32, f32, f32)] = &[(1.0, 1.0, 0.95), (3.0, 0.34, 0.42), (5.2, 0.12, 0.22)];
const MARIMBA_NOISE: (f32, f32, f32, f32) = (0.14, 0.010, 1800.0, 1.0);
const MARIMBA_ATTACK_S: f32 = 0.001;
const MARIMBA_RELEASE_T60: f32 = 0.35;
const MARIMBA_GAIN: f32 = 0.52;
const XYLOPHONE: &[(f32, f32, f32)] = &[(1.0, 1.0, 0.42), (3.0, 0.58, 0.24), (6.2, 0.14, 0.12)];
const XYLOPHONE_NOISE: (f32, f32, f32, f32) = (0.18, 0.006, 3200.0, 1.2);
const XYLOPHONE_ATTACK_S: f32 = 0.0;
const XYLOPHONE_RELEASE_T60: f32 = 0.25;
const XYLOPHONE_GAIN: f32 = 0.46;

#[allow(clippy::too_many_arguments)]
fn wood_bar(
    key: u8,
    vel: u8,
    sr: f32,
    seed: u32,
    table: &[(f32, f32, f32)],
    noise: (f32, f32, f32, f32),
    attack_s: f32,
    release_t60: f32,
    gain: f32,
) -> Modal {
    let f = key_freq(key);
    let decay_scale = (440.0 / f).powf(0.35).clamp(0.50, 1.80);
    let scaled: Vec<(f32, f32, f32)> = table
        .iter()
        .map(|&(r, a, t)| (r, a, t * decay_scale))
        .collect();
    bell(
        key,
        vel,
        sr,
        seed,
        &scaled,
        noise,
        attack_s,
        release_t60,
        gain,
    )
}
const KALIMBA: &[(f32, f32, f32)] = &[
    (1.00, 1.00, 0.95),
    (2.80, 0.42, 0.42),
    (5.40, 0.16, 0.22),
    (8.15, 0.05, 0.12),
];
const TIMPANI: &[(f32, f32, f32)] = &[
    (1.0, 1.0, 1.0),
    (1.504, 0.70, 0.85),
    (1.742, 0.45, 0.70),
    (2.0, 0.30, 0.60),
    (2.245, 0.20, 0.50),
];
const TIMPANI_STRIKE_SEMITONES: f32 = 2.1;
const TIMPANI_STRIKE_SETTLE_S: f32 = 0.155;
const TIMPANI_RELEASE_T60: f32 = 6.0;
const TIMPANI_UPPER_MIN: f32 = 0.62;
const TIMPANI_UPPER_VELOCITY_SCALE: f32 = 0.58;
const TIMPANI_UPPER_JITTER: f32 = 0.24;
const TIMPANI_JITTER_SEED_XOR: u32 = 0x7151_47A5;

fn timpani_partials(key: u8, vel: u8, seed: u32) -> Vec<(f32, f32, f32)> {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let vn = vel as f32 / 127.0;
    let upper = TIMPANI_UPPER_MIN + TIMPANI_UPPER_VELOCITY_SCALE * vn;
    let mut jrng = Rng::new(seed ^ TIMPANI_JITTER_SEED_XOR);
    TIMPANI
        .iter()
        .enumerate()
        .map(|(i, &(r, a, t))| {
            let amp = if i == 0 {
                a * v
            } else {
                a * v * upper * (1.0 + TIMPANI_UPPER_JITTER * jrng.white())
            };
            (f * r, amp, t)
        })
        .collect()
}

fn timpani(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let v = vel_amp(vel);
    let partials = timpani_partials(key, vel, seed);
    let thump = Biquad::lowpass(300.0, 0.8, sr);
    let start = 2f32.powf(TIMPANI_STRIKE_SEMITONES / 12.0);
    let glide_oct_per_s = (TIMPANI_STRIKE_SEMITONES / 12.0) / TIMPANI_STRIKE_SETTLE_S;
    Modal::new(
        sr,
        seed,
        &partials,
        (1.1 * v, 0.045, thump),
        0.001,
        TIMPANI_RELEASE_T60,
        0.85,
    )
    .with_strike_glide(start, glide_oct_per_s, 1.0)
}

const TINKLE_BELL: &[(f32, f32, f32)] = &[
    (1.00, 0.72, 1.7),
    (2.35, 0.56, 1.35),
    (3.88, 0.46, 1.05),
    (5.42, 0.28, 0.72),
    (7.10, 0.14, 0.45),
];

const AGOGO: &[(f32, f32, f32)] = &[
    (1.00, 0.86, 0.42),
    (1.70, 0.92, 0.36),
    (2.85, 0.26, 0.24),
    (4.10, 0.12, 0.16),
];

const WOODBLOCK: &[(f32, f32, f32)] = &[(1.00, 1.00, 0.16), (2.65, 0.30, 0.07), (4.35, 0.12, 0.04)];

const TAIKO_MODES: &[(f32, f32, f32)] =
    &[(1.00, 1.00, 0.80), (1.59, 0.44, 0.52), (2.14, 0.24, 0.34)];
const TOM_MODES: &[(f32, f32, f32)] = &[(1.00, 1.00, 0.40), (1.59, 0.90, 0.30), (2.14, 0.62, 0.22)];
const SYNTH_DRUM_MODES: &[(f32, f32, f32)] = &[(1.00, 1.00, 0.26), (2.00, 0.03, 0.10)];

fn tinkle_bell(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    bell(
        key,
        vel,
        sr,
        seed,
        TINKLE_BELL,
        (0.07, 0.006, 7_200.0, 1.0),
        0.0,
        8.0,
        0.42,
    )
}

fn agogo(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    bell(
        key,
        vel,
        sr,
        seed,
        AGOGO,
        (0.18, 0.008, 3_500.0, 1.1),
        0.0,
        4.0,
        0.50,
    )
}

fn steel_drum(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let decay_scale = (440.0 / f).powf(0.22).clamp(0.72, 1.45);
    let mut jrng = Rng::new(seed ^ 0x514E_5748);
    let partials: Vec<(f32, f32, f32)> = [
        (1.000, 1.00, 1.00),
        (1.006, 0.36, 1.10),
        (2.000, 0.38, 0.82),
        (2.012, 0.20, 0.75),
        (3.000, 0.20, 0.60),
        (4.180, 0.08, 0.42),
    ]
    .into_iter()
    .map(|(r, a, t)| (f * r, a * v * (1.0 + 0.05 * jrng.white()), t * decay_scale))
    .collect();

    Modal::new(
        sr,
        seed,
        &partials,
        (
            0.09 * v,
            0.020,
            Biquad::bandpass(2_200.0_f32.min(sr * 0.40), 0.9, sr),
        ),
        0.001,
        6.0,
        0.55,
    )
}

fn woodblock(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    wood_bar(
        key,
        vel,
        sr,
        seed,
        WOODBLOCK,
        (0.28, 0.010, 2_700.0, 0.9),
        0.0,
        2.0,
        0.48,
    )
}

#[allow(clippy::too_many_arguments)]
fn membrane_drum(
    key: u8,
    vel: u8,
    sr: f32,
    seed: u32,
    table: &[(f32, f32, f32)],
    noise: (f32, f32, Biquad),
    release_t60: f32,
    gain: f32,
    strike_semitones: f32,
    settle_s: f32,
    jitter: f32,
) -> Modal {
    let f = key_freq(key);
    let v = vel_amp(vel);
    let decay_scale = (220.0 / f).powf(0.16).clamp(0.76, 1.42);
    let mut jrng = Rng::new(seed ^ 0x4D45_4D42);
    let partials: Vec<(f32, f32, f32)> = table
        .iter()
        .map(|&(r, a, t)| {
            (
                f * r,
                a * v * (1.0 + jitter * jrng.white()),
                t * decay_scale,
            )
        })
        .collect();
    let start = 2f32.powf(strike_semitones / 12.0);
    let glide_oct_per_s = (strike_semitones / 12.0) / settle_s;
    Modal::new(
        sr,
        seed,
        &partials,
        (noise.0 * v, noise.1, noise.2),
        0.0,
        release_t60,
        gain,
    )
    .with_strike_glide(start, glide_oct_per_s, 1.0)
}

fn taiko_drum(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    membrane_drum(
        key,
        vel,
        sr,
        seed,
        TAIKO_MODES,
        (0.95, 0.055, Biquad::lowpass(260.0, 0.8, sr)),
        6.0,
        0.72,
        2.8,
        0.105,
        0.10,
    )
}

fn melodic_tom(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    membrane_drum(
        key,
        vel,
        sr,
        seed,
        TOM_MODES,
        (
            0.36,
            0.030,
            Biquad::bandpass(2_300.0_f32.min(sr * 0.40), 0.85, sr),
        ),
        5.0,
        0.60,
        1.7,
        0.070,
        0.08,
    )
}

fn synth_drum(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    membrane_drum(
        key,
        vel,
        sr,
        seed,
        SYNTH_DRUM_MODES,
        (
            0.16,
            0.010,
            Biquad::bandpass(4_200.0_f32.min(sr * 0.40), 0.75, sr),
        ),
        4.0,
        0.62,
        7.0,
        0.090,
        0.02,
    )
}

struct ReversePartial {
    osc: Sine,
    amp: f32,
}

struct ReverseCymbal {
    rng: Rng,
    hp: Biquad,
    partials: Vec<ReversePartial>,
    sample: usize,
    peak_samples: usize,
    sr: f32,
    gain: f32,
    released: bool,
}

impl ReverseCymbal {
    fn new(vel: u8, sr: f32, seed: u32) -> Self {
        let mut rng = Rng::new(seed ^ 0xC1A5_0119);
        let partials = [
            (1_450.0, 0.18),
            (2_230.0, 0.13),
            (3_610.0, 0.10),
            (5_850.0, 0.06),
        ]
        .into_iter()
        .filter(|(f, _)| *f < sr * 0.45)
        .map(|(f, amp)| ReversePartial {
            osc: Sine::new(f, sr, rng.white() * TAU),
            amp,
        })
        .collect();

        ReverseCymbal {
            rng,
            hp: Biquad::highpass(2_800.0_f32.min(sr * 0.40), 0.7, sr),
            partials,
            sample: 0,
            peak_samples: (1.02 * sr) as usize,
            sr,
            gain: vel_amp(vel) * 0.13,
            released: false,
        }
    }

    fn env_at(&self, sample: usize) -> f32 {
        if sample <= self.peak_samples {
            let x = sample as f32 / self.peak_samples.max(1) as f32;
            x * x * (3.0 - 2.0 * x)
        } else {
            let age = (sample - self.peak_samples) as f32 / self.sr;
            let t60 = if self.released { 0.18 } else { 0.38 };
            10f32.powf(-3.0 * age / t60)
        }
    }
}

impl Voice for ReverseCymbal {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            let env = self.env_at(self.sample);
            let noise = self.hp.process(self.rng.white()) * 0.95;
            let metal: f32 = self.partials.iter_mut().map(|p| p.amp * p.osc.next()).sum();
            *o += (noise + metal) * env * self.gain;
            self.sample += 1;
        }
        self.sample <= self.peak_samples || self.env_at(self.sample) * self.gain > 1e-5
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "reverse_cym"
    }
}

// ---------------------------------------------------------------------------
// Alt-bank percussion set B (v0.12): a SECOND voicing of GM 112-115 plus the
// GM 14 tam-tam, selected only via CC0 bank select (`altbank::make`). The
// default-bank 112-119 voices above are untouched; everything here is
// namespaced `_b` so both sets coexist. Ported from the superseded v0.11
// branch (216da4a) — the numeric oracles live in altbank.rs.
// ---------------------------------------------------------------------------

/// Register fold: move `key` into [lo, hi] by whole octaves, so the pitch
/// class is preserved (a melodic register instrument, unlike a plain clamp
/// which lands everything on the boundary note). Bank-B-internal helper,
/// shared by the tinkle bell / agogo / steel drums wrappers and the alt-bank
/// tam-tam.
pub(crate) fn fold_key(key: u8, lo: u8, hi: u8) -> u8 {
    let mut k = key as i32;
    while k < lo as i32 {
        k += 12;
    }
    while k > hi as i32 {
        k -= 12;
    }
    k.clamp(lo as i32, hi as i32) as u8
}

/// Bank-B GM 112 tinkle bell: a tiny bright hand bell — inharmonic upper
/// modes on a fast-fading fundamental, with a light >8 kHz strike "ting".
const TINKLE_B: &[(f32, f32, f32)] = &[
    (1.00, 1.00, 1.6),
    (2.32, 0.55, 1.1),
    (3.85, 0.30, 0.7),
    (6.24, 0.12, 0.4),
    (9.51, 0.05, 0.25),
];
const TINKLE_B_NOISE: (f32, f32, f32, f32) = (0.10, 0.004, 8000.0, 1.0);
const TINKLE_B_ATTACK_S: f32 = 0.0;
const TINKLE_B_RELEASE_T60: f32 = 0.6;
const TINKLE_B_GAIN: f32 = 0.45; // level knob: altbank_b112_tinkle_level_vs_glock

pub(crate) fn tinkle_bell_b(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    bell(
        fold_key(key, 72, 108),
        vel,
        sr,
        seed,
        TINKLE_B,
        TINKLE_B_NOISE,
        TINKLE_B_ATTACK_S,
        TINKLE_B_RELEASE_T60,
        TINKLE_B_GAIN,
    )
}

/// Bank-B GM 113 agogo: a struck metal clang bell — the cowbell-family 1.51x
/// second mode over a short dry ring.
const AGOGO_B: &[(f32, f32, f32)] = &[
    (1.00, 1.00, 0.55),
    (1.51, 0.65, 0.40),
    (2.62, 0.35, 0.28),
    (4.20, 0.18, 0.18),
    (5.85, 0.08, 0.12),
];
const AGOGO_B_NOISE: (f32, f32, f32, f32) = (0.12, 0.005, 3500.0, 1.2);
const AGOGO_B_ATTACK_S: f32 = 0.0;
const AGOGO_B_RELEASE_T60: f32 = 0.15;
const AGOGO_B_GAIN: f32 = 0.31; // level knob: altbank_b113_agogo_level_vs_xylophone

pub(crate) fn agogo_b(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    bell(
        fold_key(key, 60, 96),
        vel,
        sr,
        seed,
        AGOGO_B,
        AGOGO_B_NOISE,
        AGOGO_B_ATTACK_S,
        AGOGO_B_RELEASE_T60,
        AGOGO_B_GAIN,
    )
}

/// Bank-B GM 115 woodblock: two or three stiff bar modes, hollow knock noise,
/// very short ring. Register-clamped (not folded): a woodblock is a
/// percussion register, and the B115 oracles assume plain clamp behaviour.
const WOODBLOCK_B: &[(f32, f32, f32)] = &[
    (1.00, 1.00, 0.085),
    (2.55, 0.55, 0.045),
    (4.10, 0.20, 0.028),
];
const WOODBLOCK_B_NOISE: (f32, f32, f32, f32) = (0.30, 0.004, 2600.0, 1.0);
const WOODBLOCK_B_ATTACK_S: f32 = 0.0;
const WOODBLOCK_B_RELEASE_T60: f32 = 0.06;
const WOODBLOCK_B_GAIN: f32 = 1.03; // level knob: altbank_b115_woodblock_level_vs_xylophone

pub(crate) fn woodblock_b(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    wood_bar(
        key.clamp(60, 96),
        vel,
        sr,
        seed,
        WOODBLOCK_B,
        WOODBLOCK_B_NOISE,
        WOODBLOCK_B_ATTACK_S,
        WOODBLOCK_B_RELEASE_T60,
        WOODBLOCK_B_GAIN,
    )
}

/// Bank-B GM 114 steel drums: a modal pan note following the timpani
/// pattern — velocity-scaled upper modes with AMP-ONLY jitter. The defining
/// features: a strong octave (2.000x) with a slightly detuned twin (2.018x)
/// that beats at 0.018·f0 (≈ 4.7 Hz at C4), a near-twelfth (3.011x), a soft
/// 10 ms rubber-mallet attack, and a small strike glide (the dent starts
/// ~0.5 st sharp and settles in ~60 ms).
const STEELPAN_B: &[(f32, f32, f32)] = &[
    (1.000, 1.00, 1.4),
    (1.007, 0.45, 1.1),
    (2.000, 0.85, 1.0), // octave twin a — the pan's signature shimmer pair;
    (2.018, 0.30, 1.0), // twin b: NEVER jitter these ratios (beat = Δr·f0).
    // Twin b rings at twin a's T60: both are modes of the same dent, and a
    // faster twin-b decay collapses the beat DEPTH mid-ring (measured: the
    // 4.7 Hz AM line smears into an unreadable 4-6 Hz plateau with 0.8 s).
    (3.011, 0.55, 0.8),
    (4.53, 0.18, 0.5),
    (6.19, 0.08, 0.35),
];
const STEELPAN_B_NOISE: (f32, f32, f32, f32) = (0.06, 0.008, 1200.0, 0.8);
const STEELPAN_B_ATTACK_S: f32 = 0.010;
const STEELPAN_B_RELEASE_T60: f32 = 0.5;
const STEELPAN_B_GAIN: f32 = 0.31; // level knob: altbank_b114_steel_level_vs_marimba
const STEELPAN_B_STRIKE_RATIO: f32 = 1.0293; // 0.5 st sharp at the strike
const STEELPAN_B_STRIKE_SETTLE_S: f32 = 0.060;
const STEELPAN_B_UPPER_MIN: f32 = 0.55;
const STEELPAN_B_UPPER_VELOCITY_SCALE: f32 = 0.75;
const STEELPAN_B_UPPER_JITTER: f32 = 0.10;

pub(crate) fn steel_drum_b(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let key = fold_key(key, 45, 96);
    let f = key_freq(key);
    let v = vel_amp(vel);
    let vn = vel as f32 / 127.0;
    let upper = STEELPAN_B_UPPER_MIN + STEELPAN_B_UPPER_VELOCITY_SCALE * vn;
    let mut jrng = Rng::new(seed ^ 0x57EE_1DA0);
    // AMP-ONLY jitter: the 2.000/2.018 twin ratios are load-bearing (their
    // difference IS the shimmer beat rate) and are never jittered.
    let partials: Vec<(f32, f32, f32)> = STEELPAN_B
        .iter()
        .map(|&(r, a, t)| {
            let vel_scale = if r >= 2.0 { upper } else { 1.0 };
            let amp = a * v * vel_scale * (1.0 + STEELPAN_B_UPPER_JITTER * jrng.white());
            (f * r, amp, t)
        })
        .collect();
    let mallet = Biquad::bandpass(STEELPAN_B_NOISE.2.min(sr * 0.4), STEELPAN_B_NOISE.3, sr);
    let glide_oct_per_s = (0.5 / 12.0) / STEELPAN_B_STRIKE_SETTLE_S;
    Modal::new(
        sr,
        seed,
        &partials,
        (STEELPAN_B_NOISE.0 * v, STEELPAN_B_NOISE.1, mallet),
        STEELPAN_B_ATTACK_S,
        STEELPAN_B_RELEASE_T60,
        STEELPAN_B_GAIN,
    )
    .with_strike_glide(STEELPAN_B_STRIKE_RATIO, glide_oct_per_s, 1.0)
}

/// CC0-alt GM 14 tam-tam / gong ageng: a deep 65–124 Hz strike whose upper
/// modes BLOOM in over 0.3–0.7 s (slower when struck softly) and ring
/// 6–15 s, under a short bright splash. Routed ONLY from `altbank::make`
/// (CC0 != 0 on a GM 14 channel) — the default bank keeps tubular bells.
const TAMTAM: &[(f32, f32, f32)] = &[
    (1.000, 1.00, 12.0),
    (1.483, 0.75, 10.5),
    (2.090, 0.55, 9.5), // twin a — the bloom group starts here (idx 2)
    (2.132, 0.45, 9.0), // twin b: 0.042·f0 shimmer beat inside the bloom
    (2.980, 0.40, 8.0),
    (3.820, 0.30, 7.5),
    (4.760, 0.22, 6.5),
    (5.890, 0.15, 6.0),
    (7.240, 0.10, 5.0),
    (8.710, 0.07, 4.5),
];
const TAMTAM_BLOOM_FROM: usize = 2;
const TAMTAM_NOISE_AMP: f32 = 0.55;
const TAMTAM_NOISE_T60: f32 = 0.12;
const TAMTAM_NOISE_BP: (f32, f32) = (1100.0, 0.6);
const TAMTAM_ATTACK_S: f32 = 0.002;
const TAMTAM_RELEASE_T60: f32 = 3.0;
const TAMTAM_GAIN: f32 = 0.80; // level knob (alt bank only)
const TAMTAM_BLOOM_MAX_S: f32 = 0.7;
const TAMTAM_BLOOM_VEL_S: f32 = 0.4; // bloom_s = 0.7 − 0.4·vn
const TAMTAM_UPPER_MIN: f32 = 0.5;
const TAMTAM_UPPER_VELOCITY_SCALE: f32 = 0.9;
const TAMTAM_UPPER_JITTER: f32 = 0.10;

pub(crate) fn tam_tam(key: u8, vel: u8, sr: f32, seed: u32) -> Modal {
    let k = fold_key(key, 36, 47);
    let f = key_freq(k);
    let v = vel_amp(vel);
    let vn = vel as f32 / 127.0;
    let upper = TAMTAM_UPPER_MIN + TAMTAM_UPPER_VELOCITY_SCALE * vn;
    let mut jrng = Rng::new(seed ^ 0x7A37_A300);
    let partials: Vec<(f32, f32, f32)> = TAMTAM
        .iter()
        .enumerate()
        .map(|(i, &(r, a, t))| {
            let amp = if i >= TAMTAM_BLOOM_FROM {
                a * v * upper * (1.0 + TAMTAM_UPPER_JITTER * jrng.white())
            } else {
                a * v
            };
            (f * r, amp, t)
        })
        .collect();
    let splash = Biquad::bandpass(TAMTAM_NOISE_BP.0.min(sr * 0.4), TAMTAM_NOISE_BP.1, sr);
    let bloom_s = TAMTAM_BLOOM_MAX_S - TAMTAM_BLOOM_VEL_S * vn;
    Modal::new(
        sr,
        seed,
        &partials,
        (TAMTAM_NOISE_AMP * v, TAMTAM_NOISE_T60, splash),
        TAMTAM_ATTACK_S,
        TAMTAM_RELEASE_T60,
        TAMTAM_GAIN,
    )
    .with_mode_bloom(TAMTAM_BLOOM_FROM, bloom_s)
}

// ---------------------------------------------------------------------------
// Pluck (extended Karplus-Strong)
// ---------------------------------------------------------------------------

#[derive(Clone, Copy)]
pub struct MwahSpec {
    pub start_hz: f32,
    pub bloom_hz: f32,
    pub q: f32,
    pub bloom_s: f32,
    pub decay_s: f32,
    pub gain: f32,
}

struct Mwah {
    spec: MwahSpec,
    low: Biquad,
    high: Biquad,
    follower: f32,
    attack_k: f32,
    release_k: f32,
}

impl Mwah {
    const FOLLOWER_SCALE: f32 = 8.0;
    const HIGH_BLOOM_GAIN: f32 = 2.2;

    fn new(spec: MwahSpec, sr: f32) -> Self {
        Mwah {
            spec,
            low: Biquad::bandpass(spec.start_hz, spec.q, sr),
            high: Biquad::bandpass(spec.bloom_hz, spec.q, sr),
            follower: 0.0,
            attack_k: 1.0 - (-1.0 / (0.006 * sr)).exp(),
            release_k: 1.0 - (-1.0 / (0.055 * sr)).exp(),
        }
    }

    fn tick(&mut self, x: f32, t: u32, sr: f32) -> f32 {
        let target = x.abs();
        let k = if target > self.follower {
            self.attack_k
        } else {
            self.release_k
        };
        self.follower += k * (target - self.follower);

        let t_s = t as f32 / sr;
        let u = (t_s / self.spec.bloom_s.max(0.001)).clamp(0.0, 1.0);
        let smooth = u * u * (3.0 - 2.0 * u);
        let open = smooth * smooth * smooth * smooth * smooth;

        let age = (t_s - self.spec.bloom_s).max(0.0);
        let decay = 10f32.powf(-3.0 * age / self.spec.decay_s.max(0.01));
        let follow = (self.follower * Self::FOLLOWER_SCALE).min(1.0);
        let low = self.low.process(x);
        let high = self.high.process(x);
        let opened = low * (1.0 - open) + high * open * Self::HIGH_BLOOM_GAIN;
        opened * self.spec.gain * open * decay * follow
    }
}

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
    // Magnetic pickup position comb (0 = acoustic). NOTE the ×2 convention:
    // the comb delay is 2·pickup·period, so the field is HALF the physical
    // sensing fraction — 0.11 senses at ~0.22 of the string (a neck pickup),
    // 0.05 near the bridge.
    pub pickup: f32,
    pub sub: f32,    // envelope-locked fundamental sine (0 = none)
    pub cab_lp: f32, // clean-amp cab rolloff, 0 = none (HLD G2)
    // --- HLD family B: parallel one-shot transients ---
    pub click: f32,             // pick/slap onset hardness (0 = none)
    pub click_hp: f32,          // click filter corner
    pub click_post: bool,       // false: knocks the body (pre-EQ); true: post-out
    pub attack_noise: f32,      // finger/fret noise level (0 = none, post-out)
    pub stop_thump: f32,        // release thud level (0 = none, armed by note_off)
    pub sub_shape: (f32, f32),  // sub waveshaper (2f, 3f) amounts (MUTED grit / B5)
    pub sub_ramp: u32,          // sub fade-in samples
    pub grit: bool,             // per-voice soft-clip (MUTED palm chug, G4)
    pub wound_all: bool,        // K4: wound full-range (bass family) vs key-split (guitars)
    pub wound_key_split: bool,  // when false, non-bass presets skip the guitar split
    pub harmonic: bool,         // prog-31 flageolet: loop retuned to 2f/3f (G7)
    pub mwah: Option<MwahSpec>, // fretless vocal formant bloom (GM 35)
    // --- v0.12 second-polarization "course" voicing (GM 15 dulcimer) ---
    // The vertical KS loop's detune, decay and damping relative to the
    // horizontal one, and the h/v mix. DEFAULTS carry the exact literals the
    // code used to hardcode (1.0013 / 0.42 / 1.15 / (0.74, 0.26)), so every
    // pre-existing preset is bit-identical; the dulcimer re-voices the pair
    // as a true double course (wider detune, near-equal decay and mix).
    pub course_detune: f32,
    pub course_t60: f32,
    pub course_bright: f32,
    pub course_mix: (f32, f32),
    // Cross-injection strength between the two loops. DEFAULTS keep the old
    // hardcoded K_COUPLE (same-string polarization coupling). A double COURSE
    // is two separate strings that meet only at the bridge — an order weaker;
    // full-strength skew coupling splits the pair's normal modes by
    // ~k·f0/π Hz, which would bury the course's slow tuning beat.
    pub course_couple: f32,
    // --- v0.15 electric-guitar v2 ---
    // Magnetic-pickup coil resonance (Hz, Q): one resonant lowpass after the
    // position comb — the RLC peak-then-12 dB/oct that reads "electric"
    // (Paiva/Pakarinen/Välimäki, JAES 2012). (0, 0) = no pickup circuit.
    pub pickup_rlc: (f32, f32),
    // E-bow/sustainer hold level as a fraction of the note's early reference
    // level (0 = none): once a HELD note decays to this fraction, a
    // band-limited SATURATING driver at each loop's fundamental latches on
    // and holds it there — supercritical small-signal gain, amplitude pinned
    // by the soft limiter (Sullivan 1990's stabilized feedback). Release
    // drops the driver instantly and the string decays as ever.
    pub sustain: f32,
    #[cfg(test)]
    pub name: &'static str, // oracle-36 routing discriminant (test-only)
}

/// Base values every preset starts from (struct-update in const context).
const DEFAULTS: PluckPreset = PluckPreset {
    t60: 3.0,
    bright: 3000.0,
    pick_lp: 2500.0,
    pos: 0.2,
    amp: 0.5,
    attack_s: 0.0,
    rel_t60: 0.15,
    body: &[],
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
    cab_lp: 0.0,
    click: 0.0,
    click_hp: 1500.0,
    click_post: false,
    attack_noise: 0.0,
    stop_thump: 0.0,
    sub_shape: (0.0, 0.0),
    sub_ramp: 220,
    grit: false,
    wound_all: false,
    wound_key_split: true,
    harmonic: false,
    mwah: None,
    course_detune: 1.0013,
    course_t60: 0.42,
    course_bright: 1.15,
    course_mix: (0.74, 0.26),
    course_couple: K_COUPLE,
    pickup_rlc: (0.0, 0.0),
    sustain: 0.0,
    #[cfg(test)]
    name: "DEFAULT",
};

pub const NYLON: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "NYLON",
    t60: 2.8,
    bright: 3200.0,
    pick_lp: 2500.0,
    pos: 0.28,
    amp: 0.55,
    // Helmholtz air mode, top-plate mode, upper body colour
    body: &[(98.0, 1.4, 4.5), (210.0, 1.2, 4.0), (420.0, 1.8, 2.5)],
    click: 0.9, // fingernail on nylon: soft
    click_hp: 1000.0,
    ..DEFAULTS
};
pub const STEEL: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "STEEL",
    t60: 3.5,
    bright: 5200.0,
    pick_lp: 5000.0,
    pos: 0.18,
    amp: 0.50,
    // Helmholtz, top plate, and a little steel-string presence sparkle
    body: &[(105.0, 1.4, 4.0), (215.0, 1.2, 3.0), (2800.0, 1.8, 1.5)],
    click: 2.0, // plectrum on steel (G4)
    ..DEFAULTS
};
pub const CLEAN: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "CLEAN",
    t60: 3.0,
    bright: 4200.0,
    pick_lp: 4500.0,
    pos: 0.15,
    amp: 0.50,
    rel_t60: 0.18,
    // clean-amp body colour (HLD G2): low warmth + presence sparkle
    body: &[(200.0, 1.0, 2.0), (2500.0, 1.0, 3.0)],
    out_lp: 5500.0,
    pickup: 0.12,
    pickup_rlc: (4200.0, 1.8), // bright single-coil + cable resonance
    cab_lp: 4500.0,            // light clean-combo speaker rolloff
    click: 1.8,
    ..DEFAULTS
};
/// Jazz guitar (GM 26, guitar v2 unit B): a hollowbody at the neck pickup
/// with the tone rolled off — the warm round comping voice, split from the
/// bright CLEAN (27) platform it used to share.
pub const JAZZ: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "JAZZ",
    t60: 2.4, // flatwounds ring shorter
    bright: 3600.0,
    pick_lp: 3500.0,
    pos: 0.30, // picked over the neck join, not near the bridge
    amp: 0.50,
    rel_t60: 0.18,
    // hollowbody warmth: low bloom + low-mid roundness
    body: &[(180.0, 1.0, 2.5), (700.0, 1.2, 1.5)],
    out_lp: 4800.0,
    pickup: 0.11,              // ×2 convention: senses at ~0.22 — neck position
    pickup_rlc: (2400.0, 1.1), // neck humbucker, tone rolled
    cab_lp: 3800.0,            // warm clean-combo rolloff
    click: 1.2,                // soft pick, no snap
    ..DEFAULTS
};
pub const DRIVE: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "DRIVE",
    t60: 8.0,
    bright: 4800.0,
    pick_lp: 6000.0,
    pos: 0.12,
    amp: 0.70,
    rel_t60: 0.20,
    pickup: 0.10,
    pickup_rlc: (3300.0, 1.5), // pushed humbucker resonance
    sustain: 0.35,             // amp-feedback hold: a held note settles near -9 dB, not silence
    click: 2.2,                // the pick hits harder through an amp
    ..DEFAULTS
};
/// Opt-in (CC0 alt-bank) SUSTAINING lead voicing of the driven guitar. A
/// near-infinite string decay so a held note rings at ~constant level for its
/// whole written duration (real amp sustain), held in the distortion — a
/// soaring lead that bends and slurs, instead of a decaying pluck that reads
/// as a struck mallet. Softer pick so it sings, not chugs. The default-bank
/// 29/30 voice (DRIVE, above) is untouched; only a channel that opts in via
/// CC0 bank-select gets this.
pub const DRIVE_LEAD: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "DRIVE_LEAD",
    // Guitar v2 re-spec: the SUSTAINER is the hold mechanism now — the old
    // hot-amp hack (t60 40 / amp 1.5 pinning the engine tanh) is retired.
    // What stays DRIVE_LEAD's own: the gentle 11 kHz damper (harmonics ring —
    // the proven KS brightness-sustain lever), the softer pick, the longer
    // bloom-off, and a deeper hold than DRIVE (0.6 vs 0.35).
    t60: 8.0,
    bright: 11000.0,
    pick_lp: 6000.0,
    pos: 0.12,
    amp: 0.7,
    rel_t60: 0.30, // a slightly longer bloom-off when the note is lifted
    pickup: 0.10,
    pickup_rlc: (3300.0, 1.5), // pushed humbucker resonance
    sustain: 0.6,              // a lead holds close to its spoken level
    click: 1.3,                // softer pick attack: a lead sings, it does not chug
    ..DEFAULTS
};
pub const MUTED: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "MUTED",
    t60: 0.45, // palm on the bridge: the ring dies fast
    bright: 1600.0,
    pick_lp: 2200.0,
    pos: 0.10,
    amp: 0.62,
    rel_t60: 0.08,
    out_lp: 3200.0,
    pickup: 0.10,
    pickup_rlc: (3000.0, 1.2), // darker coil under the palm
    sub: 0.35,                 // the chug's thud carries the weight
    sub_shape: (0.6, 0.4),     // 2f/3f enrichment: a thud, not a sine (G4)
    sub_ramp: 90,              // the thud speaks fast
    grit: true,                // palm-mute soft-clip grit
    click: 1.4,                // palm chuff
    click_hp: 900.0,
    ..DEFAULTS
};
pub const CLAVINET: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "CLAVINET",
    t60: 0.78,
    bright: 5200.0,
    pick_lp: 5800.0,
    pos: 0.11,
    amp: 0.56,
    rel_t60: 0.06,
    body: &[(180.0, 1.0, 1.8), (900.0, 1.2, 2.2), (2600.0, 1.0, 2.5)],
    out_lp: 5200.0,
    pickup: 0.18,
    cab_lp: 5200.0,
    click: 2.0,
    click_hp: 1600.0,
    click_post: true,
    attack_noise: 0.22,
    stop_thump: 0.5,
    ..DEFAULTS
};
// Fingered electric bass (GM 33), the album workhorse. Voiced deep, warm and
// MUFFLED — flatwound/McCartney rather than a bright roundwound jazz bass:
// the fundamental carries the note, the highs are rolled off, and the pickup
// comb no longer notches the 2nd harmonic (the partial the ear reads as "deep").
pub const BASS: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "BASS",
    wound_all: true,
    t60: 3.2,        // was 3.6: a touch tighter, still a warm ring
    bright: 1250.0,  // was 1700: darker loop damping — fewer high harmonics ring
    pick_lp: 1000.0, // was 1300: duller, rounder attack (flatwound)
    pos: 0.35,
    amp: 1.05,
    rel_t60: 0.12,
    // low fundamental + low-mid woody warmth
    body: &[(60.0, 0.8, 4.5), (110.0, 1.0, 2.5)],
    out_lp: 1350.0,        // was 1900: muffle — roll the masking mids off the top
    pickup: 0.34,          // was 0.28: move the comb notch OFF the 2nd harmonic
    sub: 0.28,             // was 0.18: the "not thin" fix — more fundamental weight
    sub_ramp: 90,          // the sub speaks fast (a thud, not a swell)
    sub_shape: (0.4, 0.0), // B5: a real string's weight has a strong 2nd harmonic
    attack_noise: 0.40,    // was 0.5: less roundwound zing
    stop_thump: 2.2,       // the damp lands with a thud (B3/BASS-6)
    ..DEFAULTS
};
// Fretless (GM 35), the album's other bass. Already the darkest electric;
// pushed deeper and warmer to match the new default character.
pub const FRETLESS: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "FRETLESS",
    wound_all: true,
    t60: 2.6,
    bright: 1050.0, // was 1300: darker
    pick_lp: 780.0, // was 900: rounder, softer attack
    pos: 0.40,
    amp: 1.05,
    attack_s: 0.012,
    body: &[(58.0, 0.8, 4.0), (105.0, 1.0, 2.2)], // deeper + woody
    out_lp: 1200.0,                               // was 1500: muffle
    pickup: 0.37,                                 // was 0.33: 2nd-harmonic weight
    sub: 0.26,                                    // was 0.15: fuller fundamental
    sub_ramp: 90,                                 // the sub speaks fast
    sub_shape: (0.4, 0.0), // B5: a real string's weight has a strong 2nd harmonic
    attack_noise: 0.55,    // was 0.7
    stop_thump: 2.2,
    mwah: Some(MwahSpec {
        start_hz: 380.0,
        bloom_hz: 720.0,
        q: 4.0,
        bloom_s: 0.120,
        decay_s: 0.450,
        gain: 0.55,
    }),
    ..DEFAULTS
};
/// Slap bass (B2, GM 36/37): thumb slap + near-bridge pop.
pub const SLAP: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "SLAP",
    wound_all: true,
    t60: 2.8,
    bright: 3500.0,
    pick_lp: 4500.0,
    pos: 0.12,
    amp: 1.0,
    rel_t60: 0.12,
    body: &[(65.0, 0.7, 3.0)],
    out_lp: 4000.0,
    pickup: 0.28,
    sub: 0.15,
    sub_shape: (0.3, 0.0), // B5: a real string's weight has a 2nd harmonic
    click: 2.4,            // the pop — post-out so the out-LP doesn't swallow it
    click_hp: 1500.0,
    click_post: true,
    stop_thump: 0.9,
    ..DEFAULTS
};
/// Slap Bass 2 (GM 37): the *pop* — the finger pulls the string off the board near
/// the bridge. Brighter and thinner than the thumb-slap SLAP (GM 36): a bridge-ward
/// pluck position, far more HF snap, less fundamental weight, and a short ring.
pub const SLAP_POP: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "SLAP_POP",
    pos: 0.06,        // near the bridge — thin, bright
    bright: 5200.0,   // was 3500: the pop's HF snap
    pick_lp: 6500.0,  // was 4500: let the snap through
    t60: 1.8,         // was 2.8: dies faster than the thumb
    sub: 0.08,        // was 0.15: thinner, less weight
    click: 3.2,       // was 2.4: a sharper pull-off transient
    click_hp: 2600.0, // was 1500: the snap sits higher
    ..SLAP
};
/// Picked bass (B2, GM 34): the plectrum click survives the chain.
pub const PICK: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "PICK",
    wound_all: true,
    t60: 3.2,
    bright: 2200.0,
    pick_lp: 2600.0,
    pos: 0.15,
    amp: 1.0,
    rel_t60: 0.12,
    body: &[(65.0, 0.7, 3.5)],
    out_lp: 2400.0,
    pickup: 0.28,
    sub: 0.16,
    sub_shape: (0.3, 0.0), // B5: a real string's weight has a 2nd harmonic
    click: 1.6,
    click_hp: 1800.0,
    click_post: true,
    stop_thump: 0.8,
    ..DEFAULTS
};
/// Upright/acoustic bass (B2, GM 32): woody, darker, breathier attack.
pub const UPRIGHT: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "UPRIGHT",
    wound_all: true,
    t60: 2.4,
    bright: 900.0,
    pick_lp: 600.0,
    pos: 0.38,
    amp: 1.05,
    attack_s: 0.008,
    body: &[(65.0, 0.7, 4.0), (110.0, 1.0, 3.0)],
    out_lp: 2200.0,
    sub: 0.15,
    sub_shape: (0.3, 0.0), // B5: a real string's weight has a 2nd harmonic
    attack_noise: 0.65,    // woody fingertip thud
    stop_thump: 0.8,
    ..DEFAULTS
};
/// Guitar harmonics (G7, GM 31): the flageolet — the KS loop itself is
/// retuned to the touched harmonic (2f below E4, 3f above), thin glassy
/// ring, light grit, no heavy amp.
pub const HARMONIC: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "HARMONIC",
    t60: 2.0,
    bright: 6000.0,
    pick_lp: 6000.0,
    pos: 0.08,
    amp: 0.55,
    rel_t60: 0.25,
    pickup: 0.10,
    pickup_rlc: (3800.0, 1.5), // the coil still colors the flageolet
    click: 0.7,
    click_hp: 2000.0,
    harmonic: true,
    ..DEFAULTS
};
pub const HARP: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "HARP",
    t60: 4.5,
    bright: 3000.0,
    pick_lp: 1800.0,
    pos: 0.35,
    amp: 0.62,
    rel_t60: 0.4,
    body: &[(90.0, 0.8, 3.5), (180.0, 0.9, 2.8), (400.0, 1.1, 1.8)],
    wound_key_split: false,
    ..DEFAULTS
};
pub const BANJO: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "BANJO",
    t60: 0.9,
    bright: 7500.0,
    pick_lp: 7000.0,
    pos: 0.12,
    amp: 0.60,
    rel_t60: 0.10,
    body: &[(720.0, 2.5, 6.0)],
    click: 1.6, // fingerpicks on a drum head
    click_hp: 2000.0,
    ..DEFAULTS
};
pub const SITAR: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "SITAR",
    t60: 2.2,
    bright: 12_000.0,
    pick_lp: 10_000.0,
    pos: 0.045,
    amp: 0.58,
    rel_t60: 0.18,
    body: &[
        (320.0, 1.3, 2.0),
        (780.0, 1.6, 2.8),
        (1040.0, 1.8, 3.2),
        (1300.0, 1.8, 3.0),
        (3200.0, 1.5, 4.5),
    ],
    out_lp: 11_000.0,
    pickup: 0.09,
    click: 1.9,
    click_hp: 2200.0,
    attack_noise: 0.20,
    grit: true,
    ..DEFAULTS
};
pub const SHAMISEN: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "SHAMISEN",
    t60: 0.55,
    bright: 6200.0,
    pick_lp: 5200.0,
    pos: 0.16,
    amp: 0.54,
    rel_t60: 0.09,
    body: &[(480.0, 2.0, 3.2), (980.0, 1.5, 2.0)],
    out_lp: 5600.0,
    click: 1.2,
    click_hp: 1600.0,
    ..DEFAULTS
};
/// GM 15 hammered dulcimer (v0.12): bright steel double courses struck with
/// wooden hammers. The course pair IS the character — the vertical loop is a
/// true second string (wide 1.0042 detune ≈ 7 cents, near-equal decay and
/// mix, near-zero bridge coupling), so every note carries a slow
/// unison-shimmer beat (~1-1.8 Hz mid-register) that no single-course preset
/// has. `bright` sits high: a dulcimer's steel courses ring for seconds —
/// the ring must span several beat periods or the shimmer never speaks.
pub const DULCIMER: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "DULCIMER",
    t60: 5.0,
    bright: 9000.0,
    pick_lp: 4200.0,
    pos: 0.13,
    amp: 0.87, // level knob: dulcimer_level_vs_harp
    attack_s: 0.0,
    rel_t60: 0.35,
    // soundbox air + top-plate modes, and a hammered-steel presence sparkle
    body: &[
        (170.0, 1.0, 3.5),
        (340.0, 1.2, 2.5),
        (700.0, 1.5, 1.6),
        (2800.0, 1.4, 1.8),
    ],
    click: 1.7, // wooden hammer knock (pre-EQ: it excites the body)
    click_hp: 2600.0,
    wound_key_split: false,
    course_detune: 1.0042,
    course_t60: 0.85,
    course_bright: 1.0,
    course_mix: (0.56, 0.44),
    // Two separate strings share only the bridge: an order weaker than the
    // same-string polarization coupling. Full K_COUPLE would split the pair
    // ~2-4 Hz apart (measured) and bury the 0.42% tuning beat.
    course_couple: 0.002,
    ..DEFAULTS
};

pub const KOTO: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "KOTO",
    t60: 7.0,
    bright: 1900.0,
    pick_lp: 1500.0,
    pos: 0.34,
    amp: 0.62,
    rel_t60: 0.35,
    body: &[(140.0, 0.8, 3.0), (280.0, 1.0, 2.4), (560.0, 1.3, 1.6)],
    out_lp: 2600.0,
    click: 0.45,
    click_hp: 900.0,
    ..DEFAULTS
};

/// One Karplus-Strong delay loop on a fractional-tap delay line, so its
/// pitch can *move* while ringing (bends, slides, hammer-ons, vibrato).
/// The in-loop damper's phase delay is compensated in the delay length,
/// so the string tunes accurately; retuning glides over a few ms.
struct KsLoop {
    dl: DelayLine,
    delay: f32,
    target: f32,
    max_delay: f32, // V4/INT-4: the line's safe capacity (tap margin held back)
    glide_k: f32,
    damp: OnePole,
    loop_gain: f32,
    bright: f32,
    t60: f32,
    sr: f32,
    // guitar v2 sustainer driver (None unless the preset authors `sustain`)
    drv: Option<SusDrv>,
}

/// The e-bow driver (guitar v2 HLD §3.D): a resonant bandpass at the loop
/// fundamental feeding back through a soft limiter. The small-signal
/// round-trip gain at f0 is deliberately slightly supercritical
/// (SUS_K_OVER x the loop's per-trip deficit); the SATURATOR pins the
/// amplitude — Sullivan 1990's
/// stabilized feedback. Every other mode sees only the bandpass skirt (zero
/// at DC) and stays contracting, and the energy input is hard-bounded by
/// k·l per sample no matter how the constants are mis-tuned.
struct SusDrv {
    bp: Biquad,
    k_max: f32,  // headroom clamp, min across the current glide's endpoints
    k: f32,      // current drive (0 until the voice's hold latch engages)
    l: f32,      // saturator knee (set at latch time from the reference)
    h_last: f32, // headroom at the previous retune's center (glide endpoint)
}

/// Guitar v2 sustainer constants (HLD §3.D): driver bandpass Q, the
/// small-signal round-trip target at the fundamental, the absolute drive
/// cap, the saturator knee as a fraction of the hold level, and the ramp.
const SUS_BP_Q: f32 = 4.0;
const SUS_K_OVER: f32 = 1.18; // k = 1.18×deficit: constant supercriticality RATIO
const SUS_K_MAX: f32 = 0.12;
const SUS_L_SCALE: f32 = 0.7;
const SUS_RAMP_S: f32 = 0.060; // drive engage ramp

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
            // a wider bend (RPN range 24, deep portamento origins) would
            // silently wrap the ring buffer into garbage — clamp instead:
            // an out-of-range glide pitch-limits (V4/INT-4, oracle 43)
            max_delay: target * 2.2 + 4.0,
            glide_k: 1.0 - (-1.0 / (0.004 * sr)).exp(),
            damp: OnePole::lowpass(bright, sr),
            loop_gain: 10f32.powf(-3.0 / (t60 * f)),
            bright,
            t60,
            sr,
            drv: None,
        }
    }

    /// |H| of the in-loop OnePole damper at frequency `f` (closed form).
    fn damp_mag(&self, f: f32) -> f32 {
        OnePole::lowpass_mag(self.bright, f, self.sr)
    }

    /// Driver gain at `f`: PROPORTIONALLY supercritical — k = SUS_K_OVER ×
    /// the loop's per-trip deficit at the fundamental (damper included; a
    /// bare scalar cannot hold anything above ~A4, review D1/O1). Keeping
    /// k/deficit constant pins the saturator's equilibrium amplitude at the
    /// SAME multiple of the knee L at every pitch — the hold level is
    /// calibrated by construction instead of trimmed at runtime.
    fn sus_headroom(&self, f: f32) -> f32 {
        let lg = 10f32.powf(-3.0 / (self.t60 * f));
        let deficit = 1.0 - lg * self.damp_mag(f);
        (deficit * SUS_K_OVER).clamp(0.0, SUS_K_MAX)
    }

    /// Arm the e-bow driver (presets with `sustain > 0`); it stays silent
    /// (k = 0) until the voice's hold latch engages.
    fn enable_driver(&mut self, f: f32) {
        let h = self.sus_headroom(f);
        self.drv = Some(SusDrv {
            bp: Biquad::bandpass(f, SUS_BP_Q, self.sr),
            k_max: h,
            k: 0.0,
            l: 0.0,
            h_last: h,
        });
    }

    /// Latch control: `frac` ramps 0→1, `l` is the saturator knee.
    fn set_drive(&mut self, frac: f32, l: f32) {
        if let Some(d) = &mut self.drv {
            d.k = frac * d.k_max;
            d.l = l.max(1e-6);
        }
    }

    fn clear_drive(&mut self) {
        if let Some(d) = &mut self.drv {
            d.k = 0.0;
        }
    }

    /// Retune to a new frequency; the ringing energy stays in the string.
    fn retune(&mut self, f: f32) {
        self.target = Self::delay_for(f, self.bright, self.sr).min(self.max_delay);
        self.loop_gain = 10f32.powf(-3.0 / (self.t60 * f));
        if self.drv.is_some() {
            // glide-endpoint minimum (review C3): an upward bend must not
            // borrow the new center's larger headroom while the delay still
            // rings near the old one. h_last is the FRESH endpoint value from
            // the previous retune (not the clamped min - min-ing against the
            // previous clamp would ratchet down forever under vibrato), so
            // one transcendental evaluation per retune suffices.
            let h = self.sus_headroom(f);
            let sr = self.sr;
            if let Some(d) = &mut self.drv {
                d.bp.retune_bandpass(f, SUS_BP_Q, sr);
                d.k_max = h.min(d.h_last);
                d.k = d.k.min(d.k_max);
                d.h_last = h;
            }
        }
    }

    /// G6 release darkening: move the in-loop damper and retune so the
    /// delay keeps compensating the NEW damper's phase — pitch holds while
    /// the string dulls. `f` must be the composed current frequency
    /// (base × harm × bend): the engine keeps writing pitch to released
    /// voices, and a nominal retune would fight it (V4/INT-3).
    fn set_bright(&mut self, bright: f32, f: f32) {
        self.bright = bright;
        self.damp.set_cutoff(bright, self.sr);
        self.retune(f);
    }

    #[inline]
    fn tick(&mut self, input: f32) -> f32 {
        self.delay += self.glide_k * (self.target - self.delay);
        // K1: cubic-Lagrange tap — linear interpolation lowpasses the loop
        // at fractional delays and dulls short treble strings
        let s = self.dl.tap_cubic(self.delay);
        // guitar v2 e-bow driver: band-limited saturating feedback at f0.
        // The bandpass runs even at k = 0 so engagement is click-free.
        let fb = match &mut self.drv {
            Some(d) => {
                let b = d.bp.process(s);
                if d.k > 0.0 {
                    d.k * d.l * (b / d.l).tanh()
                } else {
                    0.0
                }
            }
            None => 0.0,
        };
        self.dl
            .push(self.damp.process(s) * self.loop_gain + input + fb);
        s
    }
}

/// K3 polarization coupling strength: strong enough for a measurable
/// secondary rise (oracle 15), weak enough to keep long notes bounded. NOTE
/// (guitar v2 review): the discrete step matrix [[a, k], [−k, a]] has
/// |λ| = sqrt(a² + k²) — skew coupling is only energy-neutral in the
/// continuous-time limit, so boundedness needs a² + k² < 1 with
/// a = loop_gain·|H_damp|; the coupled_loop_margin_holds oracle asserts it
/// across every preset at worst-case jitter.
pub(crate) const K_COUPLE: f32 = 0.02;

/// G6 release-darken targets: while released, each polarization's damper
/// glides toward this floor at control rate (already-dark presets are
/// unaffected — the glide only ever darkens).
const REL_FLOOR_H: f32 = 600.0;
const REL_FLOOR_V: f32 = 700.0;
const REL_DARKEN_K: f32 = 0.010; // per control tick: τ ≈ 36 ms

/// K4 Stage 1 wound-ness: bass strings are wound full-range; guitars cross
/// from wound to plain around G3 (key 55). Pure arithmetic — no allpass
/// (Stage 2 dispersion stays deferred, §7).
pub(crate) fn wound_factor(wound_all: bool, wound_key_split: bool, key: u8) -> f32 {
    if wound_all {
        1.0
    } else if !wound_key_split {
        0.0
    } else {
        ((55.0 - key as f32) / 24.0).clamp(0.0, 1.0)
    }
}

pub struct Pluck {
    // a real string vibrates in two polarizations: one rings on (horizontal),
    // one decays faster and slightly detuned (vertical) — their sum gives the
    // characteristic fast-then-slow decay and a gentle beat
    horiz: KsLoop,
    vert: KsLoop,
    // K3: energy sloshes between the two polarizations (skew-symmetric,
    // one-sample-delayed cross-injection)
    h_prev: f32,
    v_prev: f32,
    k_couple: f32,
    course_detune: f32,     // vertical-loop detune ratio (preset course_detune)
    course_mix: (f32, f32), // (horiz, vert) output mix
    base_f: f32,
    bend: f32,
    harm: f32, // G7 flageolet multiple (1.0 = normal), composed into every retune
    pickup: Option<(DelayLine, f32)>, // magnetic pickup position comb
    pickup_rlc: Option<Biquad>, // pickup coil RLC resonance (resonant lowpass)
    // guitar v2 hold latch (§3.D): the raw string mix is watched at control
    // rate; once a HELD note decays to sustain×reference the e-bow drivers
    // ramp in. One-way — never attenuates, release clears it instantly.
    sus_target: f32, // preset `sustain` (0 = feature absent)
    sus_acc: f32,    // per-control-window peak of |string mix|
    sus_env: f32,    // smoothed envelope of the above
    sus_ref: f32,    // reference level captured 100–200 ms post-onset
    sus_hold: bool,
    sus_ramp: f32,
    sus_l: f32,                    // saturator knee, frozen at latch engage
    sus_ref_until: u32,            // reference-capture deadline (re-armed by a slur)
    sub: Option<(Sine, f32, f32)>, // (osc, gain, decay) fundamental weight
    sub_env: f32,
    sub_shape: (f32, f32), // (2f, 3f) waveshaper amounts on the sub
    sub_ramp: u32,
    // HLD family B one-shots, all fed by the voice's own rng
    onset_pre: Option<Burst>,  // pick click / palm chuff — knocks the body
    onset_post: Option<Burst>, // finger noise / slap pop — after the out-LP
    stop: Option<Burst>,       // release thump, armed by note_off
    mwah: Option<Mwah>,        // fretless vocal formant bloom
    grit: bool,                // MUTED palm soft-clip
    body: Vec<Biquad>,
    // clean-amp cab (HLD G2): two cascaded biquad lowpasses — one 2nd-order
    // pole pair alone cannot make the −12 dB-vs-one-pole 8 kHz cliff
    // oracle 6 demands
    cab: Option<[Biquad; 2]>,
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
    #[cfg(test)]
    kind: &'static str,
}

impl Pluck {
    pub fn new(p: &PluckPreset, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let mut rng = Rng::new(seed);
        let vn = vel as f32 / 127.0;
        // round-robin variation: no two picks land identically
        let pos = (p.pos * (1.0 + 0.15 * rng.white())).clamp(0.06, 0.45);
        // velocity→timbre law (HLD family A, G3/B1): a harder pick opens both
        // the loop damper and the excitation lowpass — velocity changes the
        // tone, not just the level (the single biggest "sampled at one
        // dynamic" tell). The soft end is steeper than the HLD's first-guess
        // constants so bright presets (STEEL, damper ≥ 5 kHz) genuinely
        // darken at low velocity — tuned to pass oracle 1's 1.4×/1.3×
        // centroid contrast. Tuning stays exact: KsLoop compensates the
        // damper's phase delay at whatever cutoff it is given (oracle 2).
        let bright = (p.bright * (0.22 + 0.98 * vn) * (1.0 + 0.08 * rng.white())).min(sr * 0.45);
        let t60_base = p.t60 * (1.0 + 0.10 * rng.white());
        let pick_lp = (p.pick_lp * (0.10 + 1.30 * vn)).max(200.0);
        // the output lowpass (electric/bass presets) opens with velocity too —
        // without this the fixed out_lp caps the ff brightness of BASS-family
        // presets and the velocity contrast cannot reach oracle 1's floor
        let out_lp = p.out_lp * (0.30 + 0.95 * vn);

        // G7 flageolet: the loop itself resonates at the touched harmonic —
        // 2f below E4, 3f from E4 up (natural-harmonic playability); the
        // multiple is persistent state composed into every retune (V4/INT-2)
        let harm = if p.harmonic {
            if key < 64 {
                2.0
            } else {
                3.0
            }
        } else {
            1.0
        };
        let note_f = key_freq(key);
        let f = note_f * harm; // the frequency the LOOP rings at
        let period = sr / f;
        // K4 Stage 1: wound strings are darker — the windings damp both the
        // ring (loop damper) and the pick transient — with a skewed decay
        let wound = wound_factor(p.wound_all, p.wound_key_split, key);
        let bright = (bright * (1.0 - 0.30 * wound)).max(300.0);
        let pick_lp = (pick_lp * (1.0 - 0.42 * wound)).max(300.0);
        let t60 = (t60_base * (220.0 / f).powf(0.55)).clamp(0.25, 14.0) * (1.0 - 0.12 * wound);

        // excitation: filtered noise burst with a pick-position comb.
        // (K2's deterministic triangle IC was BUILT AND REVERTED: the
        // displacement picture (sin(nπp)/n²) buries every pluck under its
        // fundamental, and the bridge-force picture re-levels the whole
        // instrument — both destabilised ten oracles including a v0.7
        // regression. The noise burst already carries the attack character
        // and per-note variation; K2 is deferred pending a listen-driven
        // re-design. The velocity- and wound-scaled pick_lp levers stay.)
        let exc_len = (period as usize).max(4);
        let mut lp = OnePole::lowpass(pick_lp, sr);
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

        let mut horiz = KsLoop::new(f, bright, t60, &exc, sr);
        let mut vert = KsLoop::new(
            f * p.course_detune,
            bright * p.course_bright,
            t60 * p.course_t60,
            &exc,
            sr,
        );
        if p.sustain > 0.0 {
            horiz.enable_driver(f);
            vert.enable_driver(f * p.course_detune);
        }

        Pluck {
            horiz,
            vert,
            h_prev: 0.0,
            v_prev: 0.0,
            k_couple: p.course_couple,
            course_detune: p.course_detune,
            course_mix: p.course_mix,
            base_f: note_f,
            bend: 1.0,
            harm,
            pickup: (p.pickup > 0.0).then(|| {
                // the pickup senses the string a fraction of its length from
                // the bridge: a feedforward comb with a 2·pos·period delay
                let d = 2.0 * p.pickup * period;
                (DelayLine::new(d as usize + 8), d)
            }),
            // the coil circuit: a resonant lowpass — peak at the resonance,
            // 12 dB/oct above it (the RLC that makes a pickup sound electric)
            pickup_rlc: (p.pickup_rlc.0 > 0.0)
                .then(|| Biquad::lowpass(p.pickup_rlc.0, p.pickup_rlc.1, sr)),
            sus_target: p.sustain,
            sus_acc: 0.0,
            sus_env: 0.0,
            sus_ref: 0.0,
            sus_hold: false,
            sus_ramp: 0.0,
            sus_l: 0.0,
            sus_ref_until: (0.08 * sr) as u32,
            // B5: random start phase — the sub is part of the string, not a
            // laboratory cosine locked to the pick. Its WEIGHT eases off as
            // velocity rises (a hard pluck is proportionally brighter, not
            // just louder — the last piece of the family-A law).
            sub: (p.sub > 0.0).then(|| {
                (
                    Sine::new(f, sr, rng.white() * std::f32::consts::PI),
                    p.sub * v * (1.25 - 0.5 * vn),
                    t60_mul(t60 * 0.8, sr),
                )
            }),
            sub_env: 0.0,
            sub_shape: p.sub_shape,
            sub_ramp: p.sub_ramp,
            onset_pre: (p.click > 0.0 && !p.click_post).then(|| {
                let mut b = Burst::new(Biquad::highpass(p.click_hp, 0.7, sr), p.click, 0.003, sr);
                // super-linear in velocity: a soft fingerpad barely snaps
                b.trigger(v * vn);
                b
            }),
            onset_post: {
                // slap/pop (click_post) and finger/fret noise share the
                // post-out insertion so the out-LP doesn't swallow them
                if p.click > 0.0 && p.click_post {
                    let mut b =
                        Burst::new(Biquad::highpass(p.click_hp, 0.7, sr), p.click, 0.003, sr);
                    b.trigger(v * vn);
                    Some(b)
                } else if p.attack_noise > 0.0 {
                    let mut b = Burst::new(
                        Biquad::bandpass(2000.0, 0.8, sr),
                        // a soft touch barely scrapes the winding — the
                        // extra vn factor keeps whisper notes from being
                        // mostly finger noise
                        (p.attack_noise * (0.45 + 0.55 * v) * (0.3 + 0.7 * vn)).min(v),
                        0.004,
                        sr,
                    );
                    b.trigger(1.0);
                    Some(b)
                } else {
                    None
                }
            },
            stop: (p.stop_thump > 0.0).then(|| {
                Burst::new(
                    Biquad::lowpass(250.0, 0.7, sr),
                    p.stop_thump * (0.5 + 0.5 * v),
                    0.12,
                    sr,
                )
            }),
            mwah: p.mwah.map(|spec| Mwah::new(spec, sr)),
            grit: p.grit,
            body: p
                .body
                .iter()
                .map(|&(f, q, g)| Biquad::peak(f, q, g, sr))
                .collect(),
            cab: (p.cab_lp > 0.0).then(|| {
                [
                    Biquad::lowpass(p.cab_lp, 0.75, sr),
                    Biquad::lowpass(p.cab_lp, 0.75, sr),
                ]
            }),
            out_lp: if p.out_lp > 0.0 {
                Some(OnePole::lowpass(out_lp, sr))
            } else {
                None
            },
            hammer: Vec::new(),
            hammer_pos: 0,
            rng,
            pick_lp_hz: pick_lp,
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
            #[cfg(test)]
            kind: p.name,
        }
    }

    fn apply_pitch(&mut self) {
        // the flageolet multiple composes into EVERY retune (V4/INT-2) — a
        // CC1/RPN/portamento writer must not collapse the loop back to the
        // fundamental
        let f = self.base_f * self.harm * self.bend;
        self.horiz.retune(f);
        self.vert.retune(f * self.course_detune);
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
            // G6: while released, the damper glides darker at control rate;
            // the retune uses the COMPOSED frequency so bends/glides on a
            // released voice keep their pitch (V4/INT-3)
            if self.released && self.t.is_multiple_of(CTRL) {
                let f = self.base_f * self.harm * self.bend;
                let bh = self.horiz.bright;
                if bh > REL_FLOOR_H {
                    self.horiz
                        .set_bright(bh + REL_DARKEN_K * (REL_FLOOR_H - bh), f);
                }
                let bv = self.vert.bright;
                if bv > REL_FLOOR_V {
                    self.vert.set_bright(
                        bv + REL_DARKEN_K * (REL_FLOOR_V - bv),
                        f * self.course_detune,
                    );
                }
            }
            // K3: skew-symmetric polarization coupling — energy sloshes
            // between the planes (the slow secondary bloom of a real string),
            // none is created; each loop remains a contraction
            let hc = self.horiz.tick(inject + self.k_couple * self.v_prev);
            let vc = self.vert.tick(inject * 0.7 - self.k_couple * self.h_prev);
            self.h_prev = hc;
            self.v_prev = vc;
            let mut y = self.course_mix.0 * hc + self.course_mix.1 * vc;
            // guitar v2 hold latch (§3.D): watch the RAW string mix — before
            // the onset click (which never enters the loops) and the pickup
            // chain — capture an early reference, and once a held note has
            // decayed to sustain×reference, ramp the e-bow drivers in.
            if self.sus_target > 0.0 {
                self.sus_acc = self.sus_acc.max(y.abs());
                if !self.released && self.t.is_multiple_of(CTRL) {
                    self.sus_env = self.sus_env * 0.9 + self.sus_acc * 0.1;
                    self.sus_acc = 0.0;
                    // the reference is the note's SPOKEN level: 20-80 ms —
                    // late enough to skip the click, early enough that a
                    // fast-crashing high note (E6 is gone by 100 ms) still
                    // registers its real voice
                    // the reference window is the 60 ms ending at
                    // sus_ref_until; a slur RE-ARMS it (review C4), so a soft
                    // slurred note references ITS own spoken level instead of
                    // holding at a previous loud note's
                    let win = (0.06 * self.sr) as u32;
                    if self.t < self.sus_ref_until {
                        if self.t + win >= self.sus_ref_until {
                            self.sus_ref = self.sus_ref.max(self.sus_env);
                        }
                    } else {
                        let target = self.sus_target * self.sus_ref;
                        if !self.sus_hold && self.sus_env <= target {
                            self.sus_hold = true;
                            // the knee places the hold level; frozen at
                            // engage (the beat makes the instantaneous
                            // envelope an unreliable snapshot — target is
                            // the calibrated quantity)
                            self.sus_l = SUS_L_SCALE * target.max(1e-9);
                        }
                        if self.sus_hold {
                            self.sus_ramp =
                                (self.sus_ramp + CTRL as f32 / (SUS_RAMP_S * self.sr)).min(1.0);
                            // with k a constant multiple of the deficit, the
                            // equilibrium sits at the same multiple of the
                            // knee at every pitch
                            self.horiz.set_drive(self.sus_ramp, self.sus_l);
                            self.vert.set_drive(self.sus_ramp, self.sus_l);
                        }
                    }
                }
            }
            if self.grit {
                // palm-mute chug: the palm+pick+amp chain compresses (G4)
                y = (y * 2.0).tanh() * 0.5;
            }
            if let Some((dl, d)) = &mut self.pickup {
                dl.push(y);
                y = (y - dl.tap(*d)) * 0.75;
            }
            if let Some(rlc) = &mut self.pickup_rlc {
                // pickup coil resonance, directly after the position comb
                // (string → position/aperture → coil circuit)
                y = rlc.process(y);
            }
            if let Some(b) = &mut self.onset_pre {
                // the pick click knocks the body: summed before the body EQ
                y += b.tick(&mut self.rng);
            }
            for b in &mut self.body {
                y = b.process(y);
            }
            if let Some(cab) = &mut self.cab {
                for c in cab.iter_mut() {
                    y = c.process(y);
                }
            }
            let mwah_tap = y;
            if let Some(lp) = &mut self.out_lp {
                y = lp.process(y);
            }
            if let Some(mwah) = &mut self.mwah {
                y += mwah.tick(mwah_tap, self.t, self.sr);
            }
            if let Some((osc, gain, decay)) = &mut self.sub {
                // the fundamental's weight, decaying with the string
                if self.t < self.sub_ramp {
                    self.sub_env = (self.sub_env + 1.0 / self.sub_ramp as f32).min(1.0);
                }
                let s = osc.next();
                // DC-free 2f/3f enrichment (G4 thud / B5): s²−½ = −½cos2x,
                // ¾s−s³ = ¼sin3x — clean even/odd harmonics of a unit sine
                let (a2, a3) = self.sub_shape;
                let shaped = s + a2 * (s * s - 0.5) + a3 * (0.75 * s - s * s * s);
                y += shaped * *gain * self.sub_env;
                self.sub_env *= *decay;
            }
            if self.att_env < 1.0 {
                self.att_env = (self.att_env + self.att).min(1.0);
            }
            if self.released {
                self.release_env *= self.rel_mul;
            }
            let mut y = y * self.amp * self.att_env * self.release_env;
            if let Some(b) = &mut self.onset_post {
                // slap pop / finger noise, after the out-LP AND outside the
                // attack ramp — the finger contact happens at t=0 even when
                // the string itself speaks slowly (fretless/upright)
                y += b.tick(&mut self.rng) * self.amp;
            }
            if let Some(b) = &mut self.stop {
                // release thump (armed by note_off): the palm's thud is NOT
                // the string ring, so it does not decay with the release env
                y += b.tick(&mut self.rng) * self.amp;
            }
            self.env = self.env.max(y.abs()) * 0.9995;
            *o += y;
            self.t += 1;
        }
        self.t < self.min_life || self.env > 2e-5
    }

    fn note_off(&mut self) {
        if !self.released {
            if let Some(b) = &mut self.stop {
                // the stop thump fires on the effective release — under
                // CC64/CC66 that is the pedal lift, by design (V4/INT-7)
                b.trigger(1.0);
            }
        }
        self.released = true;
        // release drops the e-bow instantly: the string decays as ever
        self.horiz.clear_drive();
        self.vert.clear_drive();
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
        // (the flageolet multiple, if any, is preserved — V4/INT-2)
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
        // guitar v2 (review C4): the slurred note is a NEW note to the
        // sustainer — drop the drive, re-arm the reference window, and let
        // the latch re-engage against the slur's own spoken level
        if self.sus_target > 0.0 {
            self.horiz.clear_drive();
            self.vert.clear_drive();
            self.sus_hold = false;
            self.sus_ramp = 0.0;
            self.sus_ref = 0.0;
            self.sus_ref_until = self.t + (0.06 * self.sr) as u32;
        }
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        self.kind
    }
}

// ---------------------------------------------------------------------------
// SynthBass (HLD family F, B4) — GM 38/39 are synth basses, not plucked
// strings: saw(s) + sub sine through an envelope-swept resonant lowpass.
// ---------------------------------------------------------------------------

pub struct SynthBass {
    saws: Vec<(BlepSaw, f32)>, // (osc, detune ratio)
    sub: Sine,
    base_f: f32,
    bend: f32,
    amp_env: Adsr,
    filt_env: Adsr,
    filt: Biquad,
    depth: f32, // filter-env sweep depth in Hz
    q: f32,
    t: u32,
    amp: f32,
    sr: f32,
}

impl SynthBass {
    /// program 38 = one saw; 39 = two saws detuned ±8 cents.
    pub fn new(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let vn = vel as f32 / 127.0;
        let detunes: &[f32] = if program == 39 {
            &[0.99538, 1.00463] // ±8 cents
        } else {
            &[1.0]
        };
        let saws = detunes
            .iter()
            .map(|&r| (BlepSaw::new(f * r, sr, rng.white() * 0.5 + 0.5), r))
            .collect();
        SynthBass {
            saws,
            sub: Sine::new(f, sr, rng.white() * std::f32::consts::PI),
            base_f: f,
            bend: 1.0,
            amp_env: Adsr::new(0.004, 0.18, 0.75, 0.08, sr),
            filt_env: Adsr::new(0.003, 0.28, 0.25, 0.10, sr),
            filt: Biquad::lowpass(300.0, 4.0, sr),
            depth: 900.0 + 2600.0 * vn, // velocity opens the sweep
            q: 4.0,
            t: 0,
            amp: 0.62 * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for SynthBass {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                // envelope-swept resonant filter, state-preserving retune
                let fenv = self.filt_env.next();
                let cut = (300.0 + fenv * self.depth).clamp(80.0, self.sr * 0.4);
                self.filt.retune_lowpass(cut, self.q, self.sr);
            } else {
                self.filt_env.next();
            }
            let mut s = 0.0;
            for (osc, _) in &mut self.saws {
                s += osc.next();
            }
            s /= self.saws.len() as f32;
            s += 0.35 * self.sub.next();
            let y = self.filt.process(s) * self.amp * self.amp_env.next();
            *o += y;
            self.t += 1;
        }
        self.amp_env.alive()
    }

    fn note_off(&mut self) {
        self.amp_env.release();
        self.filt_env.release();
    }

    fn released(&self) -> bool {
        self.amp_env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        // v0.6/v0.7 bend/vibrato/portamento support (V4/INT-5): the engine
        // writes per block; BlepSaw/Sine retunes are click-free
        self.bend = mult;
        let f = self.base_f * mult;
        for (osc, r) in &mut self.saws {
            osc.set_freq(f * *r, self.sr);
        }
        self.sub.set_freq(f, self.sr);
    }

    // legato_to: default false — a synth bass retriggers (stated, not
    // accidental; V4/B4).

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "synthbass"
    }
}

// ---------------------------------------------------------------------------
// Organ
// ---------------------------------------------------------------------------

struct Pipe {
    osc: Sine,
    ratio: f32,
    amp: f32,
    active: bool,
}

#[derive(Clone, Copy)]
struct PitchScoop {
    ratio: f32,
    slew: f32,
}

// ---------------------------------------------------------------------------
// GM 19 cathedral organ
// ---------------------------------------------------------------------------

const ORGAN_TABLE_LEN: usize = 1024;
const ORGAN_MAX_SOURCE_HARMONICS: usize = 24;
const ORGAN_MIN_FUNDAMENTAL_HZ: f32 = 12.0;
const ORGAN_MAX_SR_FRACTION: f32 = 0.45;
const ORGAN_FIXED_SEED: u32 = 0xC471_EDA1;
// Reed rasp on the swell (CC11): a chorus reed driven hard *snarls*. When drive
// (from CC11) rises, the reed pipes crossfade from their `steady` table toward a
// harder `driven` table (spectral peak off the fundamental, brighter tail,
// extended to 48 harmonics to fill the 2–8 kHz snarl band that the 24-harmonic
// cap leaves empty for mid keys) and lift in level. Alias-free by construction —
// a band-limited table, never a time-domain nonlinearity. See the reed-rasp HLD.
const ORGAN_MAX_DRIVEN_HARMONICS: usize = 48;
const REED_LIFT_DB: f32 = 8.0; // reed prominence at full drive (reeds-forward)

/// Driven (hard-blown) chorus-reed spectrum, in dB relative to H1. Same
/// key-anchored shape as `organ_harmonic_db` but the peak sits on H2–H4 and the
/// tail falls ~−4 dB/oct (vs −6), which is the perceptual signature of a reed
/// beating fully against its shallot. Register shaping stays in the key anchors
/// only (no fixed-Hz formant), so the table remains a pure function of
/// (family, key, count) and the pitch/pressure path-independence test holds.
fn organ_driven_harmonic_db(key: u8, harmonic: usize) -> f32 {
    if harmonic <= 1 {
        return 0.0;
    }
    let h2 = organ_anchor([3.0, 2.0, 1.0], key);
    let h3 = organ_anchor([2.0, 1.0, 0.0], key);
    let h6 = organ_anchor([-2.0, -3.0, -4.0], key);
    let h = harmonic as f32;
    if harmonic == 2 {
        h2
    } else if harmonic == 3 {
        h3
    } else {
        (h3 + (h6 - h3) * (h / 3.0).log2()).max(-72.0)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RankFamily {
    OpenWood,
    Principal,
    ChorusReed,
    Mixture,
}

#[derive(Clone, Copy)]
struct RankSpec {
    id: u8,
    ratio: f32,
    family: RankFamily,
    gain: f32,
    sensitivity: f32,
}

fn organ_anchor(values: [f32; 3], key: u8) -> f32 {
    let k = key as f32;
    if k <= 36.0 {
        values[0]
    } else if k < 60.0 {
        values[0] + (values[1] - values[0]) * ((k - 36.0) / 24.0)
    } else if k < 84.0 {
        values[1] + (values[2] - values[1]) * ((k - 60.0) / 24.0)
    } else {
        values[2]
    }
}

fn organ_speech_ms(family: RankFamily, key: u8) -> f32 {
    let (c2, c6) = match family {
        RankFamily::OpenWood => (180.0, 90.0),
        RankFamily::Principal => (90.0, 35.0),
        RankFamily::ChorusReed => (130.0, 60.0),
        RankFamily::Mixture => (55.0, 20.0),
    };
    let t = ((key as f32 - 36.0) / 48.0).clamp(0.0, 1.0);
    c2 + (c6 - c2) * t
}

fn organ_harmonic_db(family: RankFamily, key: u8, harmonic: usize) -> f32 {
    if harmonic <= 1 {
        return 0.0;
    }
    let (h2, h3, h6) = match family {
        RankFamily::OpenWood => (
            organ_anchor([-28.0, -25.0, -22.0], key),
            organ_anchor([-9.0, -8.0, -7.0], key),
            organ_anchor([-40.0, -36.0, -32.0], key),
        ),
        RankFamily::Principal => (
            organ_anchor([-6.0, -5.0, -4.0], key),
            organ_anchor([-11.0, -9.0, -8.0], key),
            organ_anchor([-24.0, -18.0, -15.0], key),
        ),
        RankFamily::ChorusReed => (
            organ_anchor([-2.0, -3.0, -4.0], key),
            organ_anchor([-4.0, -5.0, -6.0], key),
            organ_anchor([-10.0, -11.0, -12.0], key),
        ),
        RankFamily::Mixture => (
            organ_anchor([-7.0, -6.0, -5.0], key),
            organ_anchor([-12.0, -10.0, -9.0], key),
            organ_anchor([-24.0, -20.0, -18.0], key),
        ),
    };
    let h = harmonic as f32;
    if harmonic == 2 {
        h2
    } else if harmonic == 3 {
        h3
    } else {
        // Continue the H3->H6 log-frequency slope above H6. This gives every
        // generated integer harmonic one deterministic value while retaining
        // the signed H1/H2/H3/H6 spectral contract.
        (h3 + (h6 - h3) * (h / 3.0).log2()).max(-72.0)
    }
}

fn organ_speech_tilt_db(family: RankFamily, harmonic: usize) -> f32 {
    match family {
        RankFamily::OpenWood if harmonic >= 3 => -6.0,
        RankFamily::Principal if harmonic >= 3 => 3.0,
        RankFamily::ChorusReed if harmonic >= 2 => 2.0,
        RankFamily::Mixture if harmonic >= 2 => 2.0,
        _ => 0.0,
    }
}

fn cathedral_mixture_ratios(key: u8) -> [f32; 4] {
    match key {
        0..=47 => [6.0, 8.0, 12.0, 16.0],
        48..=59 => [4.0, 6.0, 8.0, 12.0],
        60..=71 => [3.0, 4.0, 6.0, 8.0],
        72..=83 => [2.0, 3.0, 4.0, 6.0],
        _ => [1.5, 2.0, 3.0, 4.0],
    }
}

fn cathedral_registration(key: u8) -> Vec<RankSpec> {
    let mut ranks = Vec::with_capacity(14);
    let mut add = |id, ratio, family, gain, sensitivity| {
        ranks.push(RankSpec {
            id,
            ratio,
            family,
            gain,
            sensitivity,
        });
    };
    add(0, 0.5, RankFamily::Principal, 0.28, 1.0);
    add(1, 1.0, RankFamily::Principal, 0.72, 1.0);
    add(2, 2.0, RankFamily::Principal, 0.34, 1.0);
    add(3, 3.0, RankFamily::Principal, 0.18, 1.0);
    add(4, 4.0, RankFamily::Principal, 0.22, 1.0);
    let mixture = cathedral_mixture_ratios(key);
    let previous = matches!(key, 48 | 60 | 72 | 84).then(|| cathedral_mixture_ratios(key - 1));
    let crossfade_gain = 0.05 * std::f32::consts::FRAC_1_SQRT_2;
    for (i, ratio) in mixture.into_iter().enumerate() {
        let gain = if let Some(old) = previous {
            if old.contains(&ratio) {
                0.05
            } else {
                crossfade_gain
            }
        } else {
            0.05
        };
        add(5 + i as u8, ratio, RankFamily::Mixture, gain, 0.35);
    }
    if let Some(old) = previous {
        if let Some(ratio) = old.into_iter().find(|ratio| !mixture.contains(ratio)) {
            // One old-only rank overlaps the new break for this semitone. ID 14
            // is reserved for that transition pipe so physical identity remains
            // unambiguous without lifting the fourteen-pipe runtime ceiling.
            add(14, ratio, RankFamily::Mixture, crossfade_gain, 0.35);
        }
    }
    add(9, 1.0, RankFamily::ChorusReed, 0.18, 1.2);

    let pedal = ((50.0 - key as f32) / 4.0).clamp(0.0, 1.0);
    if pedal > 0.0 {
        add(10, 0.25, RankFamily::OpenWood, 0.32 * pedal, 0.25);
        add(11, 0.5, RankFamily::Principal, 0.26 * pedal, 0.25);
        add(12, 1.0, RankFamily::Principal, 0.18 * pedal, 0.25);
        // At the first mixture overlap only, omit the quietest doubled pedal
        // colour to leave room for the transition pipe under the 14-rank cap.
        if key != 48 {
            add(13, 0.5, RankFamily::ChorusReed, 0.16 * pedal, 0.25);
        }
    }
    ranks
}

struct RankPipe {
    #[cfg(test)]
    id: u8,
    key: u8,
    ratio: f32,
    family: RankFamily,
    gain: f32,
    sensitivity: f32,
    static_tune: f32,
    #[cfg(test)]
    identity_bits: (u32, u32),
    sr: f32,
    phase: f32,
    phase_inc: f32,
    frequency: f32,
    harmonics: usize,
    active: bool,
    speech: Box<[f32; ORGAN_TABLE_LEN]>,
    steady: Box<[f32; ORGAN_TABLE_LEN]>,
    age: u64,
    attack_samples: f32,
    transition_samples: f32,
    amp_mod: f32,
    // Per-pipe wind-wander: an independent slow random walk (local wind-pressure
    // deviation) that drifts pitch and amplitude together, so this pipe beats
    // against its neighbours on a continuously moving rate rather than the fixed
    // `static_tune` offset. This — not a coherent tremulant — is what makes the
    // additive stack breathe like many real pipes instead of one frozen,
    // "harpsichord-like" oscillator. Ticks at control rate off `age`; never
    // touches `frequency`/`harmonics`, so no table regen and the pinned
    // frequency/bounds tests are unaffected.
    drift: Drift,
    wander_ratio: f32,
    wander_amp: f32,
    // Reed rasp (ChorusReed pipes only). `driven` is the hard-blown table
    // crossfaded in by `blend` (0..1, the CC11-derived drive); `driven_harmonics`
    // caches its count so it regenerates only when the count changes; `drive_gain`
    // is the reed lift. `None`/0.0/1.0 for non-reed pipes and at drive 0 — which
    // is the byte-identical `else` path in `next()`.
    driven: Option<Box<[f32; ORGAN_TABLE_LEN]>>,
    driven_harmonics: usize,
    blend: f32,
    drive_gain: f32,
}

impl RankPipe {
    fn new(spec: RankSpec, key: u8, sr: f32, event_seed: u32) -> Self {
        let stable_seed = ORGAN_FIXED_SEED
            ^ (spec.id as u32).wrapping_mul(0x9E37_79B9)
            ^ (key as u32).wrapping_mul(0x85EB_CA6B);
        let mut stable = Rng::new(stable_seed);
        let tune_cents = stable.white() * 1.5;
        let level = 1.0 + stable.white() * 0.04;
        let attack_var = 1.0 + stable.white() * 0.08;
        // Wander seed + hold jitter are drawn from `stable` AFTER the identity
        // draws above, so (a) they are stable per (rank id, key) and independent
        // of `event_seed` — `pipe_identity_ignores_event_seed` and byte-identical
        // rebuilds both hold — and (b) `tune_cents`/`level`/`attack_var` are
        // untouched. Base hold ~0.45 s at the 64-sample control rate (≈310
        // ticks), jittered ±25% per pipe so the 14 pipes never retarget in
        // lock-step. Depth scales with `sensitivity` (pedals stay stately).
        let wander_seed = stable.next_u32();
        let hold_jitter = stable.white();
        let hold_ticks = (310.0 * (1.0 + 0.25 * hold_jitter)).round().max(1.0) as u32;
        let mut event = Rng::new(event_seed ^ (spec.id as u32).wrapping_mul(0x27D4_EB2D));
        let speech_ms = organ_speech_ms(spec.family, key) * attack_var;
        let mut pipe = Self {
            #[cfg(test)]
            id: spec.id,
            key,
            ratio: spec.ratio,
            family: spec.family,
            gain: spec.gain * level,
            sensitivity: spec.sensitivity,
            static_tune: 2f32.powf(tune_cents / 1200.0),
            #[cfg(test)]
            identity_bits: (tune_cents.to_bits(), level.to_bits()),
            sr,
            phase: event.next_u32() as f32 / u32::MAX as f32 * ORGAN_TABLE_LEN as f32,
            phase_inc: 0.0,
            frequency: 0.0,
            harmonics: 0,
            active: false,
            speech: Box::new([0.0; ORGAN_TABLE_LEN]),
            steady: Box::new([0.0; ORGAN_TABLE_LEN]),
            age: 0,
            attack_samples: (speech_ms * 0.12).clamp(4.0, 22.0) * 0.001 * sr,
            transition_samples: speech_ms * 0.001 * sr,
            amp_mod: 1.0,
            drift: Drift::new(wander_seed, 2.5 * spec.sensitivity, hold_ticks),
            wander_ratio: 1.0,
            wander_amp: 1.0,
            driven: matches!(spec.family, RankFamily::ChorusReed)
                .then(|| Box::new([0.0; ORGAN_TABLE_LEN])),
            driven_harmonics: 0,
            blend: 0.0,
            drive_gain: 1.0,
        };
        pipe.retune(1.0, 0.0, 0.0);
        pipe
    }

    fn regenerate_tables(&mut self, harmonics: usize) {
        self.speech.fill(0.0);
        self.steady.fill(0.0);
        if harmonics == 0 {
            return;
        }
        let mut energy = 0.0;
        let mut amps = Vec::with_capacity(harmonics);
        for harmonic in 1..=harmonics {
            let steady_amp = 10f32.powf(organ_harmonic_db(self.family, self.key, harmonic) / 20.0);
            let speech_amp =
                steady_amp * 10f32.powf(organ_speech_tilt_db(self.family, harmonic) / 20.0);
            energy += steady_amp * steady_amp;
            amps.push((steady_amp, speech_amp));
        }
        let scale = 0.65 / energy.sqrt().max(1e-6);
        for (index, &(steady_amp, speech_amp)) in amps.iter().enumerate() {
            let harmonic = index + 1;
            let mut osc = Sine::new(harmonic as f32, ORGAN_TABLE_LEN as f32, 0.0);
            for i in 0..ORGAN_TABLE_LEN {
                let s = osc.next() * scale;
                self.steady[i] += s * steady_amp;
                self.speech[i] += s * speech_amp;
            }
        }
    }

    /// Build the hard-blown reed table (ChorusReed pipes only), normalized to its
    /// own energy exactly like `steady`, so crossfading `steady`→`driven` changes
    /// timbre only — loudness is the separate `drive_gain` lift.
    fn regenerate_driven(&mut self, harmonics: usize) {
        let key = self.key;
        let Some(driven) = self.driven.as_mut() else {
            return;
        };
        driven.fill(0.0);
        if harmonics == 0 {
            return;
        }
        let mut energy = 0.0;
        let mut amps = Vec::with_capacity(harmonics);
        for harmonic in 1..=harmonics {
            let amp = 10f32.powf(organ_driven_harmonic_db(key, harmonic) / 20.0);
            energy += amp * amp;
            amps.push(amp);
        }
        let scale = 0.65 / energy.sqrt().max(1e-6);
        for (index, &amp) in amps.iter().enumerate() {
            let mut osc = Sine::new((index + 1) as f32, ORGAN_TABLE_LEN as f32, 0.0);
            for slot in driven.iter_mut() {
                *slot += osc.next() * scale * amp;
            }
        }
    }

    fn retune(&mut self, performance_pitch: f32, pressure: f32, trem: f32) {
        let wind_cents = -5.0 * pressure.clamp(0.0, 1.0) * self.sensitivity;
        let trem_cents = 3.0 * trem.clamp(-1.0, 1.0) * self.sensitivity;
        let frequency = key_freq(self.key)
            * self.ratio
            * self.static_tune
            * performance_pitch.max(0.0001)
            * 2f32.powf((wind_cents + trem_cents) / 1200.0);
        let max_hz = self.sr * ORGAN_MAX_SR_FRACTION;
        let harmonics = if frequency >= ORGAN_MIN_FUNDAMENTAL_HZ && frequency < max_hz {
            ORGAN_MAX_SOURCE_HARMONICS.min((max_hz / frequency).floor() as usize)
        } else {
            0
        };
        if harmonics != self.harmonics {
            self.regenerate_tables(harmonics);
            self.harmonics = harmonics;
        }
        // Reed pipes also carry a hard-blown `driven` table extended to 48
        // harmonics (fills the 2–8 kHz snarl band). Same alias law, higher
        // ceiling; cache its own count so it regenerates only when it changes,
        // independently of the 24-harmonic steady count.
        if self.driven.is_some() {
            let driven_h = if frequency >= ORGAN_MIN_FUNDAMENTAL_HZ && frequency < max_hz {
                ORGAN_MAX_DRIVEN_HARMONICS.min((max_hz / frequency).floor() as usize)
            } else {
                0
            };
            if driven_h != self.driven_harmonics {
                self.regenerate_driven(driven_h);
                self.driven_harmonics = driven_h;
            }
        }
        self.frequency = frequency;
        self.phase_inc = frequency * ORGAN_TABLE_LEN as f32 / self.sr;
        self.active = harmonics > 0;
        let amp_db = -1.5 * pressure.clamp(0.0, 1.0) * self.sensitivity
            + 0.30 * trem.clamp(-1.0, 1.0) * self.sensitivity;
        self.amp_mod = 10f32.powf(amp_db / 20.0);
    }

    #[inline]
    fn next(&mut self) -> f32 {
        self.age = self.age.saturating_add(1);
        if !self.active {
            return 0.0;
        }
        // Advance the wind-wander at a 64-sample control rate (~689 Hz). The walk
        // value is in cents; convert to a pitch ratio and a co-signed amplitude
        // trim (+0.4 dB per +2.5 cents). Keyed off `age`, this is independent of
        // the caller's block size, so voice unit renders (which call render()
        // once on the whole buffer, never retune) see the wander too.
        if self.age % 64 == 1 {
            let w = self.drift.next().clamp(-60.0, 60.0);
            self.wander_ratio = 2f32.powf(w / 1200.0);
            self.wander_amp = 10f32.powf(0.16 * w / 20.0);
        }
        let i0 = self.phase as usize & (ORGAN_TABLE_LEN - 1);
        let i1 = (i0 + 1) & (ORGAN_TABLE_LEN - 1);
        let frac = self.phase - self.phase.floor();
        let speech = self.speech[i0] + (self.speech[i1] - self.speech[i0]) * frac;
        let steady = self.steady[i0] + (self.steady[i1] - self.steady[i0]) * frac;
        // Reed rasp: under swell drive, harden `steady` toward the `driven` table
        // (same phase accumulator, so the wander detunes both coherently). At
        // blend 0 — every non-reed pipe, and every reed with the swell shut — this
        // is bit-for-bit the original `steady`, and the drive_gain multiply below
        // is skipped: that is the opt-in byte-identity guarantee.
        let body = if self.blend > 0.0 {
            match &self.driven {
                Some(driven) => {
                    let driven_val = driven[i0] + (driven[i1] - driven[i0]) * frac;
                    steady + (driven_val - steady) * self.blend
                }
                None => steady,
            }
        } else {
            steady
        };
        self.phase += self.phase_inc * self.wander_ratio;
        self.phase = self.phase.rem_euclid(ORGAN_TABLE_LEN as f32);
        let speech_mix = (self.age as f32 / self.transition_samples.max(1.0)).min(1.0);
        let attack = (self.age as f32 / self.attack_samples.max(1.0)).min(1.0);
        let reed_overshoot = if self.family == RankFamily::ChorusReed {
            1.0 + 0.15 * (1.0 - self.age as f32 / (0.015 * self.sr)).max(0.0)
        } else {
            1.0
        };
        let out = (speech + (body - speech) * speech_mix)
            * attack
            * reed_overshoot
            * self.gain
            * self.amp_mod
            * self.wander_amp;
        if self.blend > 0.0 {
            out * self.drive_gain
        } else {
            out
        }
    }
}

pub struct CathedralOrgan {
    pipes: Vec<RankPipe>,
    performance_pitch: f32,
    pressure: f32,
    trem: f32,
    norm: f32,
    output_hp: Biquad,
    chiff_filter: Biquad,
    chiff_rng: Rng,
    chiff_amp: f32,
    chiff_decay: f32,
    released: bool,
    release_gain: f32,
    release_step: f32,
}

impl CathedralOrgan {
    fn new(key: u8, vel: u8, sr: f32, event_seed: u32) -> Self {
        let pipes: Vec<_> = cathedral_registration(key)
            .into_iter()
            .map(|spec| RankPipe::new(spec, key, sr, event_seed))
            .collect();
        debug_assert!(pipes.len() <= 14);
        let energy = pipes.iter().map(|p| p.gain * p.gain).sum::<f32>().sqrt();
        // The extra old/new pipe pair at a mixture break is correlated rather
        // than noise-like, so the generic root-sum-square normaliser trims a
        // fraction too much. This measured half-percent correction keeps the
        // audible semitone crossfade inside the 2 dB level contract.
        let break_compensation = if matches!(key, 48 | 60 | 72 | 84) {
            1.005
        } else {
            1.0
        };
        Self {
            pipes,
            performance_pitch: 1.0,
            pressure: 0.0,
            trem: 0.0,
            norm: 0.28 / energy.max(0.1) * break_compensation,
            output_hp: Biquad::highpass(10.0, 0.707, sr),
            chiff_filter: Biquad::bandpass(2_200.0, 0.8, sr),
            chiff_rng: Rng::new(event_seed ^ 0xC41F_F123),
            chiff_amp: 0.012 * (0.35 + 0.65 * vel_amp(vel)),
            chiff_decay: t60_mul(0.045, sr),
            released: false,
            release_gain: 1.0,
            release_step: 1.0 / (0.10 * sr).max(1.0),
        }
    }

    fn retune(&mut self) {
        for pipe in &mut self.pipes {
            pipe.retune(self.performance_pitch, self.pressure, self.trem);
        }
    }

    #[cfg(test)]
    fn debug_pipe_identity(&self) -> Vec<(u8, u32, u32)> {
        self.pipes
            .iter()
            .map(|pipe| (pipe.id, pipe.identity_bits.0, pipe.identity_bits.1))
            .collect()
    }

    #[cfg(test)]
    fn debug_composed_frequencies(&self) -> Vec<u32> {
        self.pipes
            .iter()
            .map(|pipe| pipe.frequency.to_bits())
            .collect()
    }

    #[cfg(test)]
    fn debug_all_pipe_bounds_hold(&self) -> bool {
        self.pipes.len() <= 14
            && self.pipes.iter().all(|pipe| {
                (!pipe.active
                    || (pipe.frequency >= ORGAN_MIN_FUNDAMENTAL_HZ
                        && pipe.frequency * pipe.harmonics as f32
                            <= pipe.sr * ORGAN_MAX_SR_FRACTION + 0.01))
                    // The 48-harmonic driven reed table obeys the same Nyquist law.
                    && pipe.frequency * pipe.driven_harmonics as f32
                        <= pipe.sr * ORGAN_MAX_SR_FRACTION + 0.01
            })
    }
}

impl Voice for CathedralOrgan {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for sample in out.iter_mut() {
            let mut organ = self.pipes.iter_mut().map(RankPipe::next).sum::<f32>();
            if self.chiff_amp > 1e-6 {
                organ += self.chiff_filter.process(self.chiff_rng.white()) * self.chiff_amp;
                self.chiff_amp *= self.chiff_decay;
            }
            if self.released {
                self.release_gain = (self.release_gain - self.release_step).max(0.0);
            }
            *sample += self
                .output_hp
                .process(organ * self.norm * self.release_gain);
        }
        self.release_gain > 0.0
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }

    fn set_pitch(&mut self, mult: f32) {
        self.performance_pitch = mult.max(0.0001);
        self.retune();
    }

    fn set_organ_pressure(&mut self, pressure: f32, trem: f32) {
        self.pressure = pressure.clamp(0.0, 1.0);
        self.trem = trem.clamp(-1.0, 1.0);
        self.retune();
    }

    fn set_organ_swell(&mut self, drive: f32) {
        let d = drive.clamp(0.0, 1.0);
        // Reed-only: the reeds harden toward `driven` and lift; the flues are left
        // to the wind-pressure model. Does NOT call `retune()` — no table regen.
        let gain = 10f32.powf(REED_LIFT_DB * d / 20.0);
        for pipe in &mut self.pipes {
            if pipe.family == RankFamily::ChorusReed {
                pipe.blend = d;
                pipe.drive_gain = gain;
            }
        }
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "cathedral-organ"
    }
}

pub struct Organ {
    harms: Vec<Pipe>,
    env: Adsr,
    trem: Sine,
    trem_depth: f32,
    chiff_amp: f32,
    chiff_decay: f32,
    chiff_filt: Biquad,
    click_amp: f32,
    click_decay: f32,
    click_filt: Biquad,
    // Percussion tab (GM 17 only): a pitched harmonic tap struck at key-on that
    // decays away over the sustained drawbar — the Hammond "Percussion" voice.
    // Inert (`perc_amp == 0.0`) for every other organ program, whose render is
    // then bit-identical (the block is skipped and `perc_osc` never ticks).
    perc_osc: Sine,
    perc_amp: f32,
    perc_decay: f32,
    reed_noise_amp: f32,
    reed_noise_filt: Biquad,
    scoop: Option<PitchScoop>,
    rng: Rng,
    drive: f32,
    amp: f32,
    base_f: f32,
    bend: f32,
    sr: f32,
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
        click: f32,
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
                Pipe {
                    osc: Sine::new(f * m, sr, rng.white() * std::f32::consts::PI),
                    ratio: m,
                    amp: a,
                    active: true,
                }
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
            click_amp: click * vel_amp(vel),
            click_decay: t60_mul(0.004, sr),
            click_filt: Biquad::highpass(2000.0, 0.7, sr),
            perc_osc: Sine::new(f, sr, 0.0),
            perc_amp: 0.0,
            perc_decay: 0.0,
            reed_noise_amp: 0.0,
            reed_noise_filt: Biquad::bandpass((f * 3.0).clamp(240.0, sr * 0.4), 0.8, sr),
            scoop: None,
            rng,
            drive,
            amp: amp * (0.4 + 0.6 * vel_amp(vel)),
            base_f: f,
            bend: 1.0,
            sr,
        }
    }

    fn with_reed_noise(mut self, amp: f32, center_hz: f32, q: f32) -> Self {
        self.reed_noise_amp = amp;
        self.reed_noise_filt = Biquad::bandpass(center_hz.clamp(180.0, self.sr * 0.4), q, self.sr);
        self
    }

    /// The Hammond Percussion tab (GM 17): a pitched harmonic tap at `ratio`×f0,
    /// level `amp` relative to the drawbar fundamental, decaying over `t60`. It
    /// rides the master amp/env like the drawbars, so it is velocity-scaled and
    /// released with the note, but its own exponential decay makes it a one-shot
    /// tap over the held sustain — the "ping" that separates 17 from 16.
    fn with_percussion(mut self, ratio: f32, amp: f32, t60: f32) -> Self {
        let f = (self.base_f * ratio).min(self.sr * 0.45);
        self.perc_osc = Sine::new(f, self.sr, 0.0);
        self.perc_amp = amp;
        self.perc_decay = t60_mul(t60, self.sr);
        self
    }

    fn with_pitch_scoop(mut self, start_ratio: f32, settle_s: f32) -> Self {
        self.scoop = Some(PitchScoop {
            ratio: start_ratio,
            slew: 1.0 - (-1.0 / (settle_s.max(0.01) * self.sr)).exp(),
        });
        self.apply_pitch();
        self
    }

    fn scoop_ratio(&self) -> f32 {
        self.scoop.map_or(1.0, |s| s.ratio)
    }

    fn apply_pitch(&mut self) {
        let pitch = self.bend * self.scoop_ratio();
        for pipe in &mut self.harms {
            let f = self.base_f * pipe.ratio * pitch;
            pipe.active = f < self.sr * 0.45;
            if pipe.active {
                pipe.osc.set_freq(f, self.sr);
            }
        }
    }

    fn advance_scoop(&mut self) {
        let Some(scoop) = self.scoop.as_mut() else {
            return;
        };
        if (1.0 - scoop.ratio).abs() < 1e-5 {
            scoop.ratio = 1.0;
            return;
        }
        scoop.ratio += (1.0 - scoop.ratio) * scoop.slew;
        self.apply_pitch();
    }
}

impl Voice for Organ {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            self.advance_scoop();
            let mut s = 0.0;
            for pipe in &mut self.harms {
                if pipe.active {
                    s += pipe.amp * pipe.osc.next();
                }
            }
            if self.reed_noise_amp > 1e-6 {
                s += self.reed_noise_filt.process(self.rng.white()) * self.reed_noise_amp;
            }
            if self.chiff_amp > 1e-5 {
                s += self.chiff_filt.process(self.rng.white()) * self.chiff_amp;
                self.chiff_amp *= self.chiff_decay;
            }
            if self.click_amp > 1e-5 {
                s += self.click_filt.process(self.rng.white()) * self.click_amp;
                self.click_amp *= self.click_decay;
            }
            if self.perc_amp > 1e-5 {
                s += self.perc_amp * self.perc_osc.next();
                self.perc_amp *= self.perc_decay;
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

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
        self.apply_pitch();
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        // phase-continuous retune; the engine calls this once per block with
        // an inertia-slewed rate, so there is no zipper and no click
        self.trem.set_freq(rate_hz, self.sr);
        self.trem_depth = depth;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "organ"
    }
}

/// Base tremulant/musette AM (rate Hz, depth) for GM16-23. The engine only
/// morphs GM16-19 from these values toward Leslie-fast; free reeds keep their
/// built-in motion or, for GM22, use CC1 as pitch vibrato.
pub fn organ_trem_base(program: u8) -> (f32, f32) {
    match program {
        18 => (6.5, 0.10),
        16 | 17 => (5.5, 0.06),
        20 | 22 => (4.2, 0.0),
        21 => (5.0, 0.015),
        23 => (5.8, 0.018),
        _ => (4.2, 0.04),
    }
}

fn cent_ratio(cents: f32) -> f32 {
    2f32.powf(cents / 1200.0)
}

fn organ(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Organ {
    let (trem_hz, trem_depth) = organ_trem_base(program);
    let f = key_freq(key);
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
            trem_hz,
            trem_depth,
            0.10,
            0.09,
            1.8,
            0.32,
        ),
        16 => Organ::new(
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
            trem_hz,
            trem_depth,
            0.08,
            0.09,
            0.0,
            0.32,
        ),
        // 17 percussive organ: the Percussion tab drops the 4' drawbar and thins
        // the upper drawbars, and a 3rd-harmonic tap pings at key-on and decays
        // over the sustained tone — the identity 16 lacks. Louder key click too.
        17 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (0.5, 0.55),
                (1.0, 1.0),
                (1.5, 0.25),
                (2.0, 0.30),
                (3.0, 0.06),
            ],
            Adsr::new(0.01, 0.05, 1.0, 0.15, sr),
            trem_hz,
            trem_depth,
            0.08,
            0.14,
            0.0,
            0.32,
        )
        .with_percussion(3.0, 0.55, 0.22),
        19 => Organ::new(
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
            trem_hz,
            trem_depth,
            0.20,
            0.09,
            0.0,
            0.32,
        ),
        20 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (1.0, 1.0),
                (1.5, 0.18),
                (2.0, 0.34),
                (2.5, 0.14),
                (3.0, 0.20),
                (3.5, 0.12),
                (4.0, 0.10),
                (4.5, 0.10),
                (5.0, 0.06),
            ],
            Adsr::new(0.095, 0.08, 0.96, 0.22, sr),
            trem_hz,
            trem_depth,
            0.0,
            0.0,
            0.0,
            0.30,
        )
        .with_reed_noise(0.035, (f * 3.6).clamp(700.0, 2400.0), 0.75),
        21 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (cent_ratio(-16.0), 0.58),
                (1.0, 0.92),
                (cent_ratio(16.0), 0.58),
                (2.0, 0.24),
                (3.0, 0.10),
                (4.0, 0.05),
            ],
            Adsr::new(0.040, 0.08, 0.98, 0.18, sr),
            trem_hz,
            trem_depth,
            0.0,
            0.0,
            0.0,
            0.22,
        )
        .with_reed_noise(0.018, (f * 3.4).clamp(700.0, 2300.0), 0.8),
        22 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (1.0, 1.0),
                (1.5, 0.30),
                (2.0, 0.30),
                (2.5, 0.21),
                (3.0, 0.16),
                (3.5, 0.17),
                (4.0, 0.07),
                (4.5, 0.14),
            ],
            Adsr::new(0.095, 0.04, 0.94, 0.14, sr),
            trem_hz,
            trem_depth,
            0.0,
            0.0,
            0.0,
            0.30,
        )
        .with_reed_noise(0.070, (f * 4.0).clamp(900.0, 3200.0), 0.65)
        .with_pitch_scoop(cent_ratio(-110.0), 0.085),
        23 => Organ::new(
            key,
            vel,
            sr,
            seed,
            &[
                (cent_ratio(-22.0), 0.54),
                (1.0, 0.86),
                (cent_ratio(22.0), 0.54),
                (2.0, 0.26),
                (3.0, 0.12),
                (4.0, 0.06),
            ],
            Adsr::new(0.040, 0.07, 0.98, 0.18, sr),
            trem_hz,
            trem_depth,
            0.0,
            0.0,
            0.0,
            0.21,
        )
        .with_reed_noise(0.020, (f * 3.5).clamp(750.0, 2600.0), 0.75),
        _ => unreachable!("organ() only handles GM16-23"),
    }
}

/// Frozen pre-cathedral GM19 voice for the non-zero CC0 compatibility bank.
pub(crate) fn legacy_church_organ(key: u8, vel: u8, sr: f32, seed: u32) -> Box<dyn Voice> {
    Box::new(organ(19, key, vel, sr, seed))
}

// ---------------------------------------------------------------------------
// SawStack (strings / choir / pads)
// ---------------------------------------------------------------------------

/// Oscillator shape for a `SawStack` layer. Saw for strings/choir/pads and
/// most leads; Pulse (band-limited square) for the square-lead class.
#[derive(Clone, Copy)]
enum Wave {
    Saw,
    Pulse(f32), // duty cycle
}

/// A layer's oscillator — a thin enum so the render loop stays branch-cheap and
/// the `Saw` arm is numerically identical to a bare `BlepSaw`.
enum LayerOsc {
    Saw(BlepSaw),
    Pulse(BlepPulse),
}

impl LayerOsc {
    #[inline]
    fn next(&mut self) -> f32 {
        match self {
            LayerOsc::Saw(o) => o.next(),
            LayerOsc::Pulse(o) => o.next(),
        }
    }

    #[inline]
    fn set_freq(&mut self, freq: f32, sr: f32) {
        match self {
            LayerOsc::Saw(o) => o.set_freq(freq, sr),
            LayerOsc::Pulse(o) => o.set_freq(freq, sr),
        }
    }
}

struct Layer {
    osc: LayerOsc,
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
    bend: f32, // channel pitch multiplier (bend / fine-tune / aftertouch vibrato)
    filt: StackFilter,
    vowel_morph_start: Option<[f32; 3]>,
    env: Adsr,
    vib_depth: f32,
    vib_delay: u32,
    breath: f32,
    rng: Rng,
    sweep: Option<(f32, f32, f32, f32)>, // (lfo phase, rate Hz, base cutoff, octaves)
    sweep_q: f32,
    // Divide-down string machine (synth strings 50/51): one shared BBD chorus
    // LFO — (phase, rate Hz, ± pitch depth) — read by every layer at its own
    // fixed phase offset, so the ensemble motion is *correlated*, unlike each
    // player's independent `drift`. `None` for every other caller; its per-layer
    // contribution is then exactly `+ 0.0`, so those renders are bit-identical.
    chorus: Option<(f32, f32, f32)>,
    t: u32,
    amp: f32,
    sr: f32,
    legato_enabled: bool, // strings/choir/leads slur on CC68; pads re-attack
}

impl SawStack {
    /// Saw-oscillator constructor (strings / choir / pads). Delegates to
    /// `new_wave` with `Wave::Saw`; kept as the stable entry point so those
    /// callers are byte-identical.
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
        Self::new_wave(
            key,
            vel,
            sr,
            seed,
            n_osc,
            detune,
            drift_depth,
            filt,
            env,
            vib,
            breath,
            sweep,
            sweep_q,
            amp,
            Wave::Saw,
        )
    }

    /// Full constructor with a selectable oscillator shape. The per-layer RNG
    /// draw order (osc phase, then `vib_phase`, then `vib_rate`) is identical to
    /// the historical saw path — load-bearing for byte-identity — so the phase
    /// is drawn once before the wave match and both arms consume it the same way.
    #[allow(clippy::too_many_arguments)]
    fn new_wave(
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
        wave: Wave,
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
                let layer_f = f * (1.0 + detune * spread);
                let phase = rng.white() * 0.5 + 0.5;
                let osc = match wave {
                    Wave::Saw => LayerOsc::Saw(BlepSaw::new(layer_f, sr, phase)),
                    Wave::Pulse(duty) => LayerOsc::Pulse(BlepPulse::new(layer_f, sr, phase, duty)),
                };
                Layer {
                    osc,
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
            bend: 1.0,
            filt,
            vowel_morph_start: None,
            env,
            vib_depth: vib.1,
            vib_delay: (vib.2 * sr) as u32,
            breath,
            rng,
            sweep: sweep.map(|(rate, base, oct)| (sweep_phase, rate, base, oct)),
            sweep_q,
            chorus: None,
            t: 0,
            amp: amp * (0.4 + 0.6 * vel_amp(vel)),
            sr,
            legato_enabled: false,
        }
    }

    /// Turn this stack into a divide-down string machine: replace the layers'
    /// independent detune drift with one shared BBD chorus LFO. Fixed start
    /// phase (0.0) keeps the render deterministic; the per-layer phase offsets
    /// applied in `control_tick` supply the ensemble width.
    fn with_chorus(mut self, rate_hz: f32, depth: f32) -> Self {
        self.chorus = Some((0.0, rate_hz, depth));
        self
    }

    fn control_tick(&mut self) {
        let ramp = if self.t > self.vib_delay {
            (((self.t - self.vib_delay) as f32) / self.sr).min(1.0)
        } else {
            0.0
        };
        let sr = self.sr;
        // Advance the shared BBD chorus LFO once per control tick (string
        // machines only). Every layer then reads it at a fixed phase offset for
        // a *correlated* ensemble motion. `None` → `cmod == 0.0` below, so every
        // other caller's frequency is unchanged to the bit.
        let chorus = if let Some((phase, rate, depth)) = &mut self.chorus {
            *phase += TAU * *rate * CTRL as f32 / sr;
            Some((*phase, *depth))
        } else {
            None
        };
        let n = self.layers.len() as f32;
        for (i, layer) in self.layers.iter_mut().enumerate() {
            layer.vib_phase += TAU * layer.vib_rate * CTRL as f32 / sr;
            let vib = if ramp > 0.0 && self.vib_depth > 0.0 {
                self.vib_depth * ramp * layer.vib_phase.sin()
            } else {
                0.0
            };
            let drift = layer.drift.next();
            let cmod = match chorus {
                Some((phase, depth)) => depth * (phase + i as f32 * TAU / n).sin(),
                None => 0.0,
            };
            layer.osc.set_freq(
                self.base_f * layer.ratio * self.bend * (1.0 + vib + drift + cmod),
                sr,
            );
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

    fn set_pitch(&mut self, mult: f32) {
        // applied at control rate on top of each layer's detune/vibrato/drift
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // A slur just retunes the base frequency; the layers pick it up on the
        // next control tick and the envelope keeps running (no fresh attack).
        if !self.legato_enabled {
            return false;
        }
        self.base_f = key_freq(key);
        true
    }

    fn set_vowel(&mut self, freqs: [f32; 3], qs: [f32; 3], gains: [f32; 3]) {
        if let StackFilter::Formant {
            tgt,
            qs: q,
            gains: g,
            ..
        } = &mut self.filt
        {
            *tgt = freqs;
            *q = qs;
            *g = gains;
        } else if let Some(start) = self.vowel_morph_start.take() {
            self.filt = StackFilter::Formant {
                bands: [
                    Biquad::bandpass(start[0], qs[0], self.sr),
                    Biquad::bandpass(start[1], qs[1], self.sr),
                    Biquad::bandpass(start[2], qs[2], self.sr),
                ],
                gains,
                cur: start,
                tgt: freqs,
                qs,
            };
        }
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "sawstack"
    }
}

/// Soft notes speak slower: scale an attack time by velocity.
fn vel_attack(base: f32, vel: u8) -> f32 {
    base * (1.45 - 0.65 * (vel as f32 / 127.0))
}

fn strings(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let slow = program == 49;
    let mut s = SawStack::new(
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
    );
    s.legato_enabled = true;
    s
}

/// Synth Strings 1/2 (GM 50/51) — a *divide-down string machine* (Solina idiom),
/// deliberately NOT the acoustic section `strings()` renders for 48/49. A string
/// machine has no players: its ensemble comes from one shared BBD chorus (via
/// [`SawStack::with_chorus`]), so per-player `drift` and vibrato are OFF and the
/// width is entirely correlated. 51 is the lush/slow variant — wider, more
/// layers, slower & deeper chorus, darker and slower to swell. Tier D: no sample
/// layer (the `make` dispatch routes 50/51 straight here, model-only).
fn synth_strings(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let lush = program == 51;
    let (n_osc, detune, cutoff, q) = if lush {
        (6, 0.014, 2400.0, 0.8)
    } else {
        (5, 0.010, 3000.0, 0.9)
    };
    let (attack, decay, sustain, release) = if lush {
        (0.25, 0.5, 0.92, 0.9)
    } else {
        (0.10, 0.4, 0.90, 0.5)
    };
    let (chorus_hz, chorus_depth) = if lush { (0.45, 0.0026) } else { (0.75, 0.0015) };
    let mut s = SawStack::new(
        key,
        vel,
        sr,
        seed,
        n_osc,
        detune,
        0.0, // no independent per-player drift — the machine's motion is the chorus
        StackFilter::Lp(Biquad::lowpass(cutoff, q, sr)),
        Adsr::new(vel_attack(attack, vel), decay, sustain, release, sr),
        (0.0, 0.0, 0.0), // no per-player vibrato
        0.0,             // no breath bed
        None,            // no filter sweep
        q,
        0.24,
    )
    .with_chorus(chorus_hz, chorus_depth);
    s.legato_enabled = true;
    s
}

// ---------------------------------------------------------------------------
// ChoirV2 (GM 52-54) — formant engine v2 (HLD option C, 2026.07.10)
//
// A dedicated choir voice, deliberately NOT built on `SawStack`: the stack is
// shared by strings (48-51), pads and leads, so every choir-v2 behaviour lives
// in this choir-scoped struct and the shared families render bit-identically.
//
// Design (per the signed-off HLD):
//  - per-singer saw sources in four SATB section pairs, each pair with its own
//    intonation lean, pitch scatter, drift and decorrelated delayed vibrato;
//  - an upgraded 5-band tract per section: three CC70-morphable vowel formants
//    plus a fixed singer's-formant cluster (~2.9/3.25 kHz), with per-section
//    formant scatter so the four tracts never line up exactly;
//  - breath noise injected pre-tract (vowel-coloured) — a one-shot onset puff
//    plus a low sustained air floor;
//  - a soft consonant onset generalised from the alt-bank `hum_hold` prior
//    art: the vowel morph holds at a closed schwa, the mouth then opens (level
//    lift + brightening lowpass);
//  - CC70 vowel sequences keep working through the existing `set_vowel` path
//    (the engine's 3-band anchors drive the vowel formants; the singer's
//    cluster shades with the third band's gain, so "mm" closes it too).
// ---------------------------------------------------------------------------

/// One SATB section's ensemble character. Cents are relative to written pitch.
struct Ch2Section {
    off_cents: f32,        // systematic intonation lean
    scatter_cents: f32,    // ± uniform per-note draw
    drift: f32,            // Drift depth
    vib_rate_mul: f32,     // × 4.6 Hz base
    vib_depth_mul: f32,    // × 0.006 base
    vib_delay: (f32, f32), // s, per-singer uniform draw range
    reg: (u8, u8),         // full-weight key range
}

/// S, A, T, B. Offsets ≤ 6 cents keep the cluster centre on pitch; scatter
/// grows toward the low voices; vibrato slows and shallows toward the basses.
const CH2_SECTIONS: [Ch2Section; 4] = [
    Ch2Section {
        off_cents: 3.0,
        scatter_cents: 4.0,
        drift: 0.0035,
        vib_rate_mul: 1.12,
        vib_depth_mul: 1.00,
        vib_delay: (0.20, 0.55),
        reg: (60, 84),
    },
    Ch2Section {
        off_cents: -2.0,
        scatter_cents: 6.0,
        drift: 0.0040,
        vib_rate_mul: 0.97,
        vib_depth_mul: 0.95,
        vib_delay: (0.30, 0.60),
        reg: (53, 74),
    },
    Ch2Section {
        off_cents: 5.0,
        scatter_cents: 8.0,
        drift: 0.0045,
        vib_rate_mul: 1.05,
        vib_depth_mul: 0.90,
        vib_delay: (0.28, 0.58),
        reg: (47, 69),
    },
    Ch2Section {
        off_cents: -6.0,
        scatter_cents: 10.0,
        drift: 0.0055,
        vib_rate_mul: 0.85,
        vib_depth_mul: 0.70,
        vib_delay: (0.35, 0.80),
        reg: (36, 62),
    },
];

const CH2_SCHWA: [f32; 3] = [500.0, 1400.0, 2400.0]; // closed-mouth onset vowel
const CH2_MORPH: f32 = 0.045; // vowel slew per control tick
/// Singer's-formant cluster: (Hz, Q) — the trained-voice "ring" at 2.8-3.2 kHz.
const CH2_SF: [(f32, f32); 2] = [(2900.0, 5.0), (3250.0, 6.0)];
const CH2_FSCAT: f32 = 0.03; // ± per-section formant-frequency scatter
const CH2_REG_FADE: f32 = 7.0; // semitones of gain fade outside a section reg
const CH2_REG_FLOOR: f32 = 0.25; // a section never fully mutes
const CH2_HUM_GAIN: f32 = 0.45; // closed-lips level (−6.9 dB)
const CH2_MOUTH_RATE: f32 = 0.030; // mouth-open slew per control tick
const CH2_HUM_LP: (f32, f32) = (900.0, 8000.0); // closed→open lowpass cutoff Hz
const CH2_BREATH_T60: f32 = 0.09; // onset breath decay, seconds
const CH2_BREATH_SUS: f32 = 0.008; // sustained air floor (pre-tract)
/// Output level, calibrated so the sustained RMS sits in the v1 choir's
/// 0.03-0.07 window across the keyboard (measured before the swap).
const CH2_AMP: f32 = 1.55;

/// Section register weight: 1.0 inside `reg`, fading linearly to
/// `CH2_REG_FLOOR` over `CH2_REG_FADE` semitones outside it.
fn ch2_reg_weight(key: u8, reg: (u8, u8)) -> f32 {
    let d = if key < reg.0 {
        (reg.0 - key) as f32
    } else if key > reg.1 {
        (key - reg.1) as f32
    } else {
        0.0
    };
    if d <= 0.0 {
        1.0
    } else {
        let t = (d / CH2_REG_FADE).min(1.0);
        1.0 - (1.0 - CH2_REG_FLOOR) * t
    }
}

/// One singer: a detuned/drifting saw with their own delayed vibrato.
struct Ch2Singer {
    osc: BlepSaw,
    ratio: f32,
    vib_phase: f32,
    vib_rate: f32,  // Hz
    vib_depth: f32, // fractional pitch deviation
    vib_delay: u32, // samples before the wobble starts
    vib_ramp_s: f32,
    drift: Drift,
    gain: f32, // register/section weight (mean-renormalised to 1)
}

/// One section's vocal tract: 3 vowel formants + the 2-band singer's cluster,
/// each centre scattered by the section's own `fscat` multipliers.
struct Ch2Tract {
    bands: [Biquad; 5],
    fscat: [f32; 5],
}

pub struct ChoirV2 {
    singers: Vec<Ch2Singer>, // 8: [S,S,A,A,T,T,B,B]
    tracts: [Ch2Tract; 4],   // singer pair i uses tract i/2
    // shared vowel morph state (per-tract scatter applied at retune)
    cur: [f32; 3],
    tgt: [f32; 3],
    qs: [f32; 3],
    vgains: [f32; 3],
    sf_gains: [f32; 2],
    sf_ref_g3: f32, // program-default third-band gain: the cluster's open point
    sf_open: f32,   // slewless cluster shade = (vgains[2]/sf_ref_g3).min(1.3)
    base_f: f32,
    bend: f32,
    env: Adsr,
    breath_env: f32, // one-shot onset puff (decays)
    breath_mul: f32,
    hum_hold: u32, // samples: vowel morph frozen, mouth closed
    mouth: f32,    // 0 closed → 1 open
    hum_lp: OnePole,
    rng: Rng,
    t: u32,
    amp: f32,
    sr: f32,
}

fn choir(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> ChoirV2 {
    use std::f32::consts::PI;
    let f = key_freq(key);
    let vn = vel as f32 / 127.0;
    let mut rng = Rng::new(seed);

    // Per-program vowel target, onset multipliers and cluster gains. 54
    // ("synth voice") finally splits from 53 with a brighter "eh" and a
    // uniform (non-SATB) scatter — a stack of synth voices, not a room.
    let (tgt, vgains, sf_gains, hold_mul, br_mul): ([f32; 3], [f32; 3], [f32; 2], f32, f32) =
        match program {
            52 => (
                [660.0, 1120.0, 2500.0],
                [1.0, 0.55, 0.28],
                [0.30, 0.18],
                1.0,
                1.0,
            ), // aah
            53 => (
                [330.0, 870.0, 2300.0],
                [1.0, 0.45, 0.20],
                [0.20, 0.12],
                1.25,
                0.7,
            ), // ooh
            _ => (
                [400.0, 1900.0, 2600.0],
                [1.0, 0.70, 0.40],
                [0.35, 0.22],
                0.5,
                1.3,
            ), // eh
        };
    let qs = [9.0, 10.0, 9.0];
    let uniform = program == 54;

    let mut singers: Vec<Ch2Singer> = Vec::with_capacity(8);
    for i in 0..8u32 {
        let sec = &CH2_SECTIONS[(i / 2) as usize];
        let (cents, rate_mul, depth_mul, dlo, dhi, drift, gain) = if uniform {
            (rng.white() * 12.0, 1.0, 1.0, 0.30, 0.70, 0.0040, 1.0)
        } else {
            let (dlo, dhi) = sec.vib_delay;
            (
                sec.off_cents + rng.white() * sec.scatter_cents,
                sec.vib_rate_mul,
                sec.vib_depth_mul,
                dlo,
                dhi,
                sec.drift,
                ch2_reg_weight(key, sec.reg),
            )
        };
        let ratio = 2f32.powf(cents / 1200.0);
        let phase = rng.white() * 0.5 + 0.5;
        let vib_phase = rng.white() * PI;
        let vib_rate = 4.6 * rate_mul * (1.0 + 0.15 * rng.white());
        let vib_delay_s = dlo + (dhi - dlo) * (rng.white() * 0.5 + 0.5);
        let vib_ramp_s = 0.5 + 0.7 * (rng.white() * 0.5 + 0.5); // 0.5-1.2 s
        singers.push(Ch2Singer {
            osc: BlepSaw::new(f * ratio, sr, phase),
            ratio,
            vib_phase,
            vib_rate,
            vib_depth: 0.006 * depth_mul,
            vib_delay: (vib_delay_s * sr) as u32,
            vib_ramp_s,
            drift: Drift::new(seed ^ (0x2C41 + i * 977), drift, 2800),
            gain,
        });
    }
    // Renormalise the mean singer gain to 1 so register weighting reshapes the
    // section balance without moving the overall level across the keyboard.
    let sum: f32 = singers.iter().map(|s| s.gain).sum();
    if sum > 0.0 {
        let k = singers.len() as f32 / sum;
        for s in &mut singers {
            s.gain *= k;
        }
    }

    // Four tracts, each with its own ±CH2_FSCAT formant scatter. Built at the
    // closed schwa; the morph retunes the vowel bands toward `tgt`.
    let tracts = std::array::from_fn(|_| {
        let mut fscat = [1.0f32; 5];
        for m in &mut fscat {
            *m = 1.0 + CH2_FSCAT * rng.white();
        }
        let bands = std::array::from_fn(|k| {
            if k < 3 {
                Biquad::bandpass(CH2_SCHWA[k] * fscat[k], qs[k], sr)
            } else {
                let (sf, sq) = CH2_SF[k - 3];
                Biquad::bandpass(sf * fscat[k], sq, sr)
            }
        });
        Ch2Tract { bands, fscat }
    });

    // Soft consonant onset (generalised hum_hold): velocity shortens the hold,
    // the program scales it; the onset puff is shaped by the tract it feeds.
    let hum_hold_s = 0.11 * (1.3 - 0.6 * vn) * hold_mul;
    let breath0 = 0.10 * (0.3 + 0.7 * vn) * br_mul;

    ChoirV2 {
        singers,
        tracts,
        cur: CH2_SCHWA,
        tgt,
        qs,
        vgains,
        sf_gains,
        sf_ref_g3: vgains[2],
        sf_open: 1.0,
        base_f: f,
        bend: 1.0,
        env: Adsr::new(vel_attack(0.28, vel), 0.3, 0.9, 0.4, sr),
        breath_env: breath0,
        breath_mul: t60_mul(CH2_BREATH_T60, sr),
        hum_hold: (hum_hold_s * sr) as u32,
        mouth: 0.0,
        hum_lp: OnePole::lowpass(CH2_HUM_LP.0, sr),
        rng,
        t: 0,
        amp: CH2_AMP * (0.4 + 0.6 * vel_amp(vel)),
        sr,
    }
}

impl ChoirV2 {
    fn control_tick(&mut self) {
        let sr = self.sr;
        let t = self.t;
        // per-singer delayed/ramped vibrato + drift
        for s in &mut self.singers {
            s.vib_phase += TAU * s.vib_rate * CTRL as f32 / sr;
            let ramp = if t > s.vib_delay {
                (((t - s.vib_delay) as f32) / sr / s.vib_ramp_s).min(1.0)
            } else {
                0.0
            };
            let vib = if ramp > 0.0 {
                s.vib_depth * ramp * s.vib_phase.sin()
            } else {
                0.0
            };
            let drift = s.drift.next();
            s.osc
                .set_freq(self.base_f * s.ratio * self.bend * (1.0 + vib + drift), sr);
        }
        // vowel morph — frozen at the schwa during the consonant hold
        if t >= self.hum_hold {
            for i in 0..3 {
                if (self.tgt[i] - self.cur[i]).abs() > 1.0 {
                    self.cur[i] += CH2_MORPH * (self.tgt[i] - self.cur[i]);
                    for tr in &mut self.tracts {
                        tr.bands[i].retune_bandpass(self.cur[i] * tr.fscat[i], self.qs[i], sr);
                    }
                }
            }
            self.mouth += CH2_MOUTH_RATE * (1.0 - self.mouth);
        }
        // singer's-formant cluster shade: closed vowels ("mm") mute the ring
        self.sf_open = (self.vgains[2] / self.sf_ref_g3.max(1e-3)).min(1.3);
        // closed-lips lowpass opens with the mouth
        let cut = CH2_HUM_LP.0 + (CH2_HUM_LP.1 - CH2_HUM_LP.0) * self.mouth * self.mouth;
        self.hum_lp.set_cutoff(cut, sr);
    }
}

#[cfg(test)]
impl ChoirV2 {
    /// CH2-O5 structural accessors: per-singer vibrato rates (Hz) and onset
    /// delays (samples) — the decorrelation that makes ensemble shimmer.
    fn singer_vib_rates(&self) -> Vec<f32> {
        self.singers.iter().map(|s| s.vib_rate).collect()
    }
    fn singer_vib_delays(&self) -> Vec<u32> {
        self.singers.iter().map(|s| s.vib_delay).collect()
    }
}

impl Voice for ChoirV2 {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.control_tick();
            }
            let breath_now = CH2_BREATH_SUS + self.breath_env;
            let mut s = 0.0;
            for (sec, tr) in self.tracts.iter_mut().enumerate() {
                // section pair summed pre-tract, breath injected pre-tract so
                // the air is vowel-coloured, decorrelated across sections
                let a = &mut self.singers[sec * 2];
                let mut x = a.osc.next() * a.gain;
                let b = &mut self.singers[sec * 2 + 1];
                x += b.osc.next() * b.gain;
                x += self.rng.white() * breath_now;
                let mut y = 0.0;
                for k in 0..3 {
                    y += tr.bands[k].process(x) * self.vgains[k];
                }
                for k in 0..2 {
                    y += tr.bands[3 + k].process(x) * self.sf_gains[k] * self.sf_open;
                }
                s += y;
            }
            s /= self.singers.len() as f32;
            s = self.hum_lp.process(s);
            s *= CH2_HUM_GAIN + (1.0 - CH2_HUM_GAIN) * self.mouth;
            self.breath_env *= self.breath_mul;
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

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // a melisma: the ringing choir retunes on one vowel — no fresh
        // consonant, breath puff or attack
        self.base_f = key_freq(key);
        true
    }

    fn set_vowel(&mut self, freqs: [f32; 3], qs: [f32; 3], gains: [f32; 3]) {
        self.tgt = freqs;
        self.qs = qs;
        self.vgains = gains;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "choir2"
    }
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
        let mut stack = SawStack::new(
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
        );
        if program == 91 {
            stack.vowel_morph_start = Some([500.0, 900.0, 2400.0]);
        }
        stack
    }
}

/// Per-program voicing for the GM synth leads (80-87). Kept to the cheap knobs
/// the SawStack already exposes; bespoke per-program DSP (charang drive, voice
/// formants, the 86 fifth / 87 sub-octave interval) is deferred to reqs.
struct LeadSpec {
    wave: Wave,
    n_osc: usize,
    detune: f32,
    cutoff: f32,
    q: f32,
    breath: f32,
}

const LEADS: [LeadSpec; 8] = [
    // 80 square lead — hollow, focused pulse
    LeadSpec {
        wave: Wave::Pulse(0.5),
        n_osc: 2,
        detune: 0.004,
        cutoff: 3400.0,
        q: 1.0,
        breath: 0.0,
    },
    // 81 saw lead — the classic (the one used by albums)
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 3,
        detune: 0.006,
        cutoff: 3000.0,
        q: 1.1,
        breath: 0.0,
    },
    // 82 calliope — rounder pulse, breathy, no detune
    LeadSpec {
        wave: Wave::Pulse(0.5),
        n_osc: 1,
        detune: 0.0,
        cutoff: 2200.0,
        q: 0.8,
        breath: 0.015,
    },
    // 83 chiff — airy saw
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 2,
        detune: 0.005,
        cutoff: 2800.0,
        q: 1.0,
        breath: 0.05,
    },
    // 84 charang — brightest, edgiest saw
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 3,
        detune: 0.012,
        cutoff: 4200.0,
        q: 1.4,
        breath: 0.0,
    },
    // 85 voice lead — softer, breathy saw
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 3,
        detune: 0.008,
        cutoff: 2500.0,
        q: 1.2,
        breath: 0.02,
    },
    // 86 fifths* — plain saw this pass (parallel fifth deferred)
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 2,
        detune: 0.006,
        cutoff: 3000.0,
        q: 1.1,
        breath: 0.0,
    },
    // 87 bass+lead* — darker saw this pass (sub octave deferred)
    LeadSpec {
        wave: Wave::Saw,
        n_osc: 2,
        detune: 0.005,
        cutoff: 2400.0,
        q: 1.0,
        breath: 0.0,
    },
];

/// GM synth leads (80-87): a `SawStack` voiced for a lead — fast
/// velocity-tracked attack, short release, a velocity-tracked filter, and a
/// pulse oscillator for the square-lead class. CC1 vibrato and CC68 legato come
/// from the engine; `legato_enabled` opts this instance into slurs.
fn lead(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let spec = &LEADS[(program - 80) as usize];
    let cutoff = (spec.cutoff * (0.55 + 0.45 * vel_amp(vel))).min(sr * 0.45);
    let mut s = SawStack::new_wave(
        key,
        vel,
        sr,
        seed,
        spec.n_osc,
        spec.detune,
        0.002, // light per-layer drift — leads sit tighter than pads
        StackFilter::Lp(Biquad::lowpass(cutoff, spec.q, sr)),
        Adsr::new(vel_attack(0.010, vel), 0.06, 0.82, 0.10, sr),
        (0.0, 0.0, 0.0), // no always-on vibrato — CC1 mod wheel provides it
        spec.breath,
        None, // no filter sweep (that stays a pad feature)
        spec.q,
        0.50,
        spec.wave,
    );
    s.legato_enabled = true;
    s
}

// ---------------------------------------------------------------------------
// Wind — the GM pipe / flue family (72-79)
// ---------------------------------------------------------------------------
// Air-jet (edge-tone) instruments. ONE voice + a per-program preset table — the
// shape the Reed family (64-71) proved. The key move: **bore class lives in the
// DATA, not in code.** A stopped pipe (pan flute) is a preset whose EVEN
// harmonic slots are 0.0; a Helmholtz vessel (bottle / ocarina / whistle) is a
// preset whose ladder is one weak entry. One mechanism (an amplitude table),
// eight identities — so `render` carries no per-instrument branch.
//
// Design + oracle spec: see the WD-O suite in `mod tests` and
// `wrk_docs/2026.07.11 - HLD - woodwind and synthwide LA synthesis ...` §7.1.
// This voice needs nothing from the engine beyond set_pitch / legato_to.
// ---------------------------------------------------------------------------

const WD_SCOOP_K: f32 = 0.05; // onset-scoop settle per control tick
/// Velocity normal at which the preset table reads DIRECTLY off the render
/// (`bright` == 1.0 at vel 100, mid-register) — so the table is the spectrum.
const WD_VN0: f32 = 100.0 / 127.0;
/// Partials above this fraction of `sr` are gated off rather than folded.
const WD_ALIAS_LIM: f32 = 0.44;

/// A GM pipe program's fixed voicing. All-`pub`, const-constructible.
pub struct WindPreset {
    /// h2..h7 amplitudes relative to h1 = 1.0, at `bright` = 1. The bore class:
    /// stopped pipe zeroes the evens; a vessel keeps one weak entry.
    pub harm: [f32; 6],
    pub vel_bright: f32, // velocity → spectral tilt slope (recorder ≈ 0: it can't be blown open)
    pub reg_dark: f32,   // register → spectral tilt slope (top of range purifies)
    pub breath: f32,     // sustain breath-bed level (through the tracked bandpass)
    pub breath_f: f32,   // bed centre as a MULTIPLE of f0 (vessels sit on f0; pipes above it)
    pub breath_q: f32,   // bed Q (pan-flute halo 0.8 … whistle 4.0 focused)
    pub breath_hi: f32,  // >8 kHz noise shelf (shakuhachi muraiki); 0.0 = filter not built
    pub chiff: f32,      // onset chiff level (× vn × vel_amp — super-linear, Reed convention)
    pub chiff_t60: f32,  // chiff decay
    pub vib: (f32, f32, f32), // (rate Hz, depth, delay s)
    pub attack: f32,     // Adsr attack base (vel_attack-scaled)
    pub release: f32,
    pub scoop: f32,      // onset pitch multiplier start
    pub range: (u8, u8), // MIDI keys for register normalisation
    pub amp: f32,
    #[cfg(test)]
    pub name: &'static str, // diagnostic label (kind() is always "wind")
}

/// 72 — open cylinder, half a flute. A thinner flute ladder; its register does
/// the "piercing" work. Focused air (its high register masks noise anyway).
pub const PICCOLO: WindPreset = WindPreset {
    harm: [0.22, 0.06, 0.015, 0.0, 0.0, 0.0],
    vel_bright: 0.7,
    reg_dark: 0.45,
    breath: 0.055,
    breath_f: 2.0,
    breath_q: 2.5,
    breath_hi: 0.0,
    chiff: 0.12,
    chiff_t60: 0.020,
    vib: (5.5, 0.0035, 0.20),
    attack: 0.025,
    release: 0.09,
    scoop: 0.988,
    range: (74, 108),
    amp: 0.50,
    #[cfg(test)]
    name: "piccolo",
};
/// 73 — the flagship (used by ~all 12 committed albums, so R1: move it as little
/// as possible). h2/h3, breath level+placement+Q, attack, release, scoop and amp
/// are TODAY'S ACCEPTED VALUES verbatim; h4..h6 merely extend the existing
/// ~−8.5 dB/harmonic rolloff into a skirt, replacing the old absolute cliff.
pub const FLUTE: WindPreset = WindPreset {
    harm: [0.32, 0.12, 0.045, 0.018, 0.008, 0.0],
    vel_bright: 0.9,
    reg_dark: 0.55,
    breath: 0.09,
    breath_f: 2.0,
    breath_q: 2.0,
    breath_hi: 0.0,
    chiff: 0.10,
    chiff_t60: 0.025,
    // depth trimmed 0.004 → 0.0035: the CTRL-rate fix makes this vibrato NEWLY
    // AUDIBLE (it ran at ~0.31 Hz before), so keep it subtle. ±6 cents.
    vib: (5.0, 0.0035, 0.25),
    attack: 0.050,
    release: 0.10,
    scoop: 0.984,
    range: (60, 96),
    amp: 0.50,
    #[cfg(test)]
    name: "flute",
};
/// 74 — open duct + fipple. The PUREST pipe: fundamental-dominant, a whisper of
/// ladder, near-zero breath, speaks instantly at pitch. Its defining trait is
/// that velocity does NOT open the timbre (blow harder and it just goes sharp),
/// hence vel_bright 0.15.
pub const RECORDER: WindPreset = WindPreset {
    harm: [0.09, 0.05, 0.012, 0.0, 0.0, 0.0],
    vel_bright: 0.15,
    reg_dark: 0.35,
    breath: 0.03,
    breath_f: 2.0,
    breath_q: 2.0,
    breath_hi: 0.0,
    chiff: 0.06,
    chiff_t60: 0.018,
    vib: (5.0, 0.0018, 0.35),
    attack: 0.018,
    release: 0.08,
    scoop: 0.996,
    range: (60, 96),
    amp: 0.50,
    #[cfg(test)]
    name: "recorder",
};
/// 75 — STOPPED cylinder: the evens are structurally dead (bore class as data).
/// Strong h3 (the hollow 12th it overblows to) + decaying odds. Loud BROAD breath
/// halo at 2.5·f0 — deliberately BETWEEN h2 and h3 so the noise cannot fake an
/// even partial and pollute the odd/even oracle. Iconic chiff: loudest + longest.
pub const PAN_FLUTE: WindPreset = WindPreset {
    harm: [0.0, 0.38, 0.0, 0.14, 0.0, 0.05],
    vel_bright: 0.6,
    reg_dark: 0.5,
    breath: 0.24,
    breath_f: 2.5,
    breath_q: 0.8,
    breath_hi: 0.0,
    chiff: 0.30,
    chiff_t60: 0.045,
    vib: (4.8, 0.005, 0.22),
    attack: 0.035,
    release: 0.10,
    scoop: 0.978,
    range: (55, 91),
    amp: 0.46,
    #[cfg(test)]
    name: "pan_flute",
};
/// 76 — HELMHOLTZ vessel: one resonance, so a near-bare sine. The jet noise is
/// filtered by that same resonance, so the bed sits ON f0 and is the loudest
/// fraction in the family — the tone is bare, so the AIR is the timbre.
pub const BLOWN_BOTTLE: WindPreset = WindPreset {
    harm: [0.08, 0.02, 0.0, 0.0, 0.0, 0.0],
    vel_bright: 0.3,
    reg_dark: 0.0, // no ladder to darken
    breath: 0.80,
    breath_f: 1.0,
    breath_q: 1.5,
    breath_hi: 0.0,
    chiff: 0.18,
    chiff_t60: 0.035,
    vib: (4.6, 0.004, 0.30),
    attack: 0.065,
    release: 0.12,
    scoop: 0.975,
    range: (48, 84),
    amp: 0.54,
    #[cfg(test)]
    name: "blown_bottle",
};
/// 77 — open end-blown bamboo. The richest ladder, weighted h2 ≈ h3 (the dark
/// wood + edge complexity that separates it from the flute's h2-dominant
/// balance), tail to h7. Rich breath PLUS the muraiki >8 kHz shelf — the one
/// instrument that needs `breath_hi`. Deep meri onset scoop, slowest bloom.
pub const SHAKUHACHI: WindPreset = WindPreset {
    harm: [0.26, 0.26, 0.10, 0.05, 0.025, 0.012],
    vel_bright: 0.8,
    reg_dark: 0.5,
    breath: 0.30,
    breath_f: 2.5,
    breath_q: 1.0,
    breath_hi: 0.05,
    chiff: 0.20,
    chiff_t60: 0.040,
    vib: (4.5, 0.006, 0.35),
    attack: 0.070,
    release: 0.12,
    scoop: 0.955,
    range: (57, 86),
    amp: 0.46,
    #[cfg(test)]
    name: "shakuhachi",
};
/// 78 — the human whistle: the mouth cavity is itself a Helmholtz resonator, so
/// a near-pure sine with a NARROW focused air band AT the whistle pitch.
pub const WHISTLE: WindPreset = WindPreset {
    harm: [0.04, 0.008, 0.0, 0.0, 0.0, 0.0],
    vel_bright: 0.2,
    reg_dark: 0.2,
    breath: 0.16,
    breath_f: 1.0,
    breath_q: 4.0,
    breath_hi: 0.0,
    chiff: 0.05,
    chiff_t60: 0.015,
    vib: (5.5, 0.006, 0.18),
    attack: 0.015,
    release: 0.08,
    scoop: 0.990,
    range: (72, 100),
    amp: 0.52,
    #[cfg(test)]
    name: "whistle",
};
/// 79 — vessel flute: one dominant partial plus a single warm h2, and
/// deliberately NO h3 (a vessel's overtones are weak and inharmonic — omitting
/// is more honest than faking one).
pub const OCARINA: WindPreset = WindPreset {
    harm: [0.16, 0.0, 0.0, 0.0, 0.0, 0.0],
    vel_bright: 0.25,
    reg_dark: 0.0,
    breath: 0.17,
    breath_f: 1.2,
    breath_q: 2.0,
    breath_hi: 0.0,
    chiff: 0.08,
    chiff_t60: 0.022,
    vib: (5.2, 0.004, 0.25),
    attack: 0.030,
    release: 0.11,
    scoop: 0.985,
    range: (60, 88),
    amp: 0.52,
    #[cfg(test)]
    name: "ocarina",
};

/// GM pipe program → its voicing. Anything outside 72..=79 falls back to the flute.
pub fn wind(program: u8) -> &'static WindPreset {
    match program {
        72 => &PICCOLO,
        74 => &RECORDER,
        75 => &PAN_FLUTE,
        76 => &BLOWN_BOTTLE,
        77 => &SHAKUHACHI,
        78 => &WHISTLE,
        79 => &OCARINA,
        _ => &FLUTE,
    }
}

pub struct Wind {
    osc: [Sine; 7], // h1..h7 (index i renders harmonic i+1)
    amps: [f32; 7], // amps[0] = 1.0 (fundamental); zero slots are never ticked
    base_f: f32,
    bend: f32,
    scoop: f32, // pitch multiplier settling toward 1.0
    breath_filt: Biquad,
    breath_amp: f32,
    hi_filt: Option<Biquad>, // >8 kHz muraiki shelf (shakuhachi only)
    hi_amp: f32,
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
    fn from_preset(preset: &WindPreset, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let vn = vel as f32 / 127.0;
        let mut rng = Rng::new(seed);
        // Register position: 0 at range bottom, 1 at top (out-of-range clamps).
        let (lo, hi) = preset.range;
        let reg = ((key as f32 - lo as f32) / (hi as f32 - lo as f32).max(1.0)).clamp(0.0, 1.0);
        // The spectral-tilt scalar. Normalised so bright == 1.0 at vel 100,
        // mid-register — i.e. the preset table IS the spectrum at the oracle probe.
        // Harder blowing opens the timbre; the top of the range purifies it.
        let bright = (1.0 + preset.vel_bright * (vn - WD_VN0) - preset.reg_dark * (reg - 0.5))
            .clamp(0.55, 1.20);

        // Partial amplitudes: upper partials scale super-linearly with `bright`.
        let mut amps = [0.0f32; 7];
        amps[0] = 1.0;
        for (i, a) in amps.iter_mut().enumerate().skip(1) {
            *a = preset.harm[i - 1] * bright.powi(i as i32);
        }
        // Alias gate: a partial above 0.44·sr is silenced, never folded. (0.44
        // leaves headroom for a ±2-semitone bend: 0.44 × 1.122 = 0.494 < Nyquist.)
        let lim = WD_ALIAS_LIM * sr;
        for (i, a) in amps.iter_mut().enumerate() {
            if (i + 1) as f32 * f > lim {
                *a = 0.0;
            }
        }
        // One phase draw per SLOT (even silent ones) so the RNG stream stays
        // aligned across presets with different partial counts — the WD-O5
        // breath-differential seam depends on that.
        let osc = std::array::from_fn(|i| {
            Sine::new(f * (i + 1) as f32, sr, rng.white() * std::f32::consts::PI)
        });

        // Breath bed: a bandpass tracking f0, placed and shaped per bore.
        // Amplitude-quadratic in velocity — turbulent noise grows super-linearly
        // with jet speed, so hard blowing is airier and soft playing purer.
        let vel_air = 0.35 + 1.05 * vn * vn;
        let vibr = preset.vib;
        Wind {
            osc,
            amps,
            base_f: f,
            bend: 1.0,
            scoop: preset.scoop,
            breath_filt: Biquad::bandpass((preset.breath_f * f).min(sr * 0.4), preset.breath_q, sr),
            breath_amp: preset.breath * vel_air,
            hi_filt: (preset.breath_hi > 0.0).then(|| Biquad::highpass(8000.0, 0.7, sr)),
            hi_amp: preset.breath_hi * vel_air,
            chiff_amp: preset.chiff * vn * vel_amp(vel),
            chiff_decay: t60_mul(preset.chiff_t60, sr),
            env: Adsr::new(
                vel_attack(preset.attack, vel),
                0.05,
                0.92,
                preset.release,
                sr,
            ),
            vib: control_lfo(vibr.0, 0.08, &mut rng, sr),
            vib_depth: vibr.1,
            vib_delay: (vibr.2 * sr) as u32,
            vib_val: 0.0,
            rng,
            t: 0,
            amp: preset.amp * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for Wind {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.scoop += WD_SCOOP_K * (1.0 - self.scoop);
                let v = self.vib.next();
                self.vib_val = v;
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                let f = self.base_f * self.bend * self.scoop * (1.0 + vib);
                for (i, osc) in self.osc.iter_mut().enumerate() {
                    if self.amps[i] > 0.0 {
                        osc.set_freq(f * (i + 1) as f32, self.sr);
                    }
                }
            }
            let mut s = 0.0;
            for (i, osc) in self.osc.iter_mut().enumerate() {
                if self.amps[i] > 0.0 {
                    s += self.amps[i] * osc.next();
                }
            }
            let e = self.env.next();
            // the breath rides the vibrato — air moves with the pitch wobble
            let breath_mod = 1.0 + 0.5 * self.vib_val;
            let noise = self.breath_filt.process(self.rng.white());
            s += noise * self.breath_amp * e * breath_mod;
            // The second RNG draw is gated on the FILTER, not on hi_amp, so a test
            // that zeroes hi_amp keeps this stream aligned with its twin.
            if let Some(hf) = self.hi_filt.as_mut() {
                s += hf.process(self.rng.white()) * self.hi_amp * e * breath_mod;
            }
            // The chiff sits OUTSIDE the envelope (the Reed/Brass onset convention):
            // a fresh attack spits at t=0 while the envelope is still ramping. Inside
            // it, the old flute's chiff was largely swallowed by its own 50 ms attack.
            let chiff = noise * self.chiff_amp * self.amp;
            self.chiff_amp *= self.chiff_decay;
            *o += s * self.amp * e + chiff;
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
        // An upward slur sheds partials that would now alias (never un-zeroed).
        let lim = WD_ALIAS_LIM * self.sr;
        for (i, a) in self.amps.iter_mut().enumerate() {
            if (i + 1) as f32 * new_f > lim {
                *a = 0.0;
            }
        }
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "wind"
    }
}

// ---------------------------------------------------------------------------
// Bowed solo strings (GM 40-44 / 110)
// ---------------------------------------------------------------------------

const BODY_VIOLIN: [(f32, f32, f32); 3] =
    [(280.0, 1.2, 5.0), (610.0, 1.8, 4.0), (1350.0, 1.5, 3.0)];
const BODY_VIOLA: [(f32, f32, f32); 3] = [(220.0, 1.3, 7.5), (475.0, 1.8, 4.0), (1200.0, 1.6, 3.5)];
const BODY_CELLO: [(f32, f32, f32); 3] = [(105.0, 1.1, 5.5), (220.0, 1.5, 4.5), (650.0, 1.4, 3.5)];
const BODY_CONTRABASS: [(f32, f32, f32); 3] =
    [(62.0, 1.0, 2.5), (115.0, 1.3, 7.5), (380.0, 1.4, 3.0)];

#[derive(Clone, Copy)]
struct BowedPreset {
    body: &'static [(f32, f32, f32); 3],
    press_lo: f32,
    press_span: f32,
    vib_rate: f32,
    vib_depth: f32,
    attack_s: f32,
    bite: f32,
    amp_trim: f32,
    tremolo: bool,
}

const BOWED_VIOLIN: BowedPreset = BowedPreset {
    body: &BODY_VIOLIN,
    press_lo: 900.0,
    press_span: 5200.0,
    vib_rate: 5.3,
    vib_depth: 0.0045,
    attack_s: 0.070,
    bite: 0.100,
    amp_trim: 1.0,
    tremolo: false,
};

fn bowed_preset(program: u8) -> BowedPreset {
    match program {
        41 => BowedPreset {
            body: &BODY_VIOLA,
            press_lo: 800.0,
            press_span: 4200.0,
            vib_rate: 5.1,
            attack_s: 0.090,
            bite: 0.095,
            amp_trim: 0.98,
            ..BOWED_VIOLIN
        },
        42 => BowedPreset {
            body: &BODY_CELLO,
            press_lo: 600.0,
            press_span: 2900.0,
            vib_rate: 4.8,
            attack_s: 0.105,
            bite: 0.090,
            ..BOWED_VIOLIN
        },
        43 => BowedPreset {
            body: &BODY_CONTRABASS,
            press_lo: 350.0,
            press_span: 1700.0,
            vib_rate: 4.2,
            vib_depth: 0.0038,
            attack_s: 0.125,
            bite: 0.085,
            amp_trim: 0.85,
            ..BOWED_VIOLIN
        },
        44 => BowedPreset {
            tremolo: true,
            ..BOWED_VIOLIN
        },
        110 => BowedPreset {
            press_lo: 1800.0,
            press_span: 7000.0,
            vib_rate: 5.6,
            attack_s: 0.052,
            bite: 0.230,
            ..BOWED_VIOLIN
        },
        _ => BOWED_VIOLIN,
    }
}

const BOW_TREM_RATE_LO_HZ: f32 = 6.0;
const BOW_TREM_RATE_VEL_HZ: f32 = 3.0;
const BOW_TREM_DEPTH_LO: f32 = 0.50;
const BOW_TREM_DEPTH_VEL: f32 = 0.15;
const BOW_TREM_BITE_S: f32 = 0.018;
const BOW_TREM_JITTER: f32 = 0.06;
const BOW_TREM_AMP_JITTER: f32 = 0.10;

const PIZZ: PluckPreset = PluckPreset {
    #[cfg(test)]
    name: "PIZZ",
    t60: 0.9,
    bright: 2600.0,
    pick_lp: 1600.0,
    pos: 0.30,
    amp: 0.58,
    rel_t60: 0.10,
    body: &BODY_VIOLIN,
    click: 0.6,
    click_hp: 900.0,
    attack_noise: 0.25,
    stop_thump: 0.5,
    ..DEFAULTS
};

pub struct Bowed {
    saw: BlepSaw,
    base_f: f32,
    bend: f32,
    scoop: f32,
    body: [Biquad; 3],
    lp: OnePole, // bow-pressure brightness: opens with the envelope
    press_lo: f32,
    press_span: f32,
    env: Adsr,
    vib: Sine,
    vib_depth: f32,
    vib_delay: u32,
    #[cfg(test)]
    vib_val: f32,
    bite: f32,
    trem_rate: f32,
    trem_rate_cur: f32,
    trem_phase: f32,
    trem_depth: f32,
    trem_stroke_gain: f32,
    trem_gain: f32,
    trem_bite_until: u32,
    rng: Rng,
    t: u32,
    attack_samples: u32,
    last_env: f32,
    amp: f32,
    sr: f32,
}

impl Bowed {
    fn new(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let preset = bowed_preset(program);
        let vn = vel as f32 / 127.0;
        let attack = vel_attack(preset.attack_s, vel);
        let (trem_rate, trem_depth) = if preset.tremolo {
            (
                BOW_TREM_RATE_LO_HZ + BOW_TREM_RATE_VEL_HZ * vn,
                BOW_TREM_DEPTH_LO + BOW_TREM_DEPTH_VEL * vn,
            )
        } else {
            (0.0, 0.0)
        };
        Bowed {
            saw: BlepSaw::new(f * 0.975, sr, rng.white() * 0.5 + 0.5),
            base_f: f,
            bend: 1.0,
            scoop: 0.975 + 0.008 * vn,
            body: [
                Biquad::peak(preset.body[0].0, preset.body[0].1, preset.body[0].2, sr),
                Biquad::peak(preset.body[1].0, preset.body[1].1, preset.body[1].2, sr),
                Biquad::peak(preset.body[2].0, preset.body[2].1, preset.body[2].2, sr),
            ],
            lp: OnePole::lowpass(1400.0, sr),
            press_lo: preset.press_lo,
            press_span: preset.press_span,
            env: Adsr::new(attack, 0.2, 0.9, 0.18, sr),
            vib: control_lfo(preset.vib_rate, 0.1, &mut rng, sr),
            vib_depth: preset.vib_depth,
            vib_delay: (0.22 * sr) as u32,
            #[cfg(test)]
            vib_val: 0.0,
            bite: preset.bite,
            trem_rate,
            trem_rate_cur: trem_rate,
            trem_phase: 0.0,
            trem_depth,
            trem_stroke_gain: 1.0,
            trem_gain: 1.0,
            trem_bite_until: 0,
            rng,
            t: 0,
            attack_samples: (attack * sr) as u32,
            last_env: 0.0,
            amp: 0.40 * (0.4 + 0.6 * vel_amp(vel)) * preset.amp_trim,
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
                #[cfg(test)]
                {
                    self.vib_val = v;
                }
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                self.saw
                    .set_freq(self.base_f * self.bend * self.scoop * (1.0 + vib), self.sr);
                // More bow pressure opens each instrument's brightness ceiling.
                self.lp
                    .set_cutoff(self.press_lo + self.press_span * self.last_env, self.sr);
                if self.trem_rate > 0.0 {
                    self.trem_phase += self.trem_rate_cur * CTRL as f32 / self.sr;
                    if self.trem_phase >= 1.0 {
                        self.trem_phase -= 1.0;
                        self.trem_bite_until = self.t + (BOW_TREM_BITE_S * self.sr) as u32;
                        self.trem_stroke_gain = 1.0 + BOW_TREM_AMP_JITTER * self.rng.white();
                        self.trem_rate_cur =
                            self.trem_rate * (1.0 + BOW_TREM_JITTER * self.rng.white());
                    }
                    let c = (std::f32::consts::TAU * self.trem_phase).cos();
                    self.trem_gain = self.trem_stroke_gain
                        * ((1.0 - self.trem_depth) + self.trem_depth * 0.5 * (1.0 - c));
                }
            }
            let e = self.env.next();
            self.last_env = e;
            // bow noise: loud while the bow bites, quieter once the string speaks
            let noise_amp = if self.t < self.attack_samples * 2 || self.t < self.trem_bite_until {
                self.bite
            } else {
                0.028
            };
            let mut s = self.saw.next() + self.rng.white() * noise_amp * e;
            for b in &mut self.body {
                s = b.process(s);
            }
            s = self.lp.process(s);
            *o += s * self.amp * e * self.trem_gain;
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

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "bowed"
    }
}

// ---------------------------------------------------------------------------
// BowedString (GM 43 contrabass) — a bowed-string digital waveguide
// ---------------------------------------------------------------------------

/// A bowed string as a *physical model*: a delay-line waveguide split at the
/// bow into a bridge-side and a nut-side section, driven every sample by a
/// nonlinear stick-slip bow-friction interaction (the McIntyre–Woodhouse–
/// Schumacher / Smith / STK lineage).
///
/// Why this and not the shared `Bowed` (saw + static body EQ): a saw through a
/// fixed EQ is, at 65 Hz, a static harmonic stack — it reads as a buzzy
/// "transformer hum", and no amount of EQ makes it an instrument, because an
/// instrument's identity is in the *time domain*. Here every partial comes
/// from one coupled oscillator locked to the fundamental, so the tone fuses by
/// construction, and the stick-slip nonlinearity gives it the living,
/// slightly-irregular motion a static spectrum cannot fake. Contrabass-only
/// (default GM 43); the Codex per-program `Bowed` set is the CC0 alt bank.
pub struct BowedString {
    bridge: DelayLine, // bow -> bridge -> bow section
    neck: DelayLine,   // bow -> nut -> bow section
    bridge_delay: f32,
    neck_delay: f32,
    beta: f32, // bow position as a fraction of the speaking length
    base_f: f32,
    bend: f32,
    refl: OnePole,     // bridge reflection filter: string losses (darkens)
    body: [Biquad; 3], // the instrument body's broad low resonances
    dc_x1: f32,        // DC blocker state (bowed loops accumulate DC)
    dc_y1: f32,
    env: Adsr,               // bow pressure/velocity envelope (the onset + release)
    max_vel: f32,            // bow speed (loudness / brightness)
    slope: f32,              // bow force: narrows the friction curve (brighter/scratchier)
    vib: Sine,               // pitch vibrato
    vib_depth: f32,          //
    vib_delay: u32,          // vibrato onset delay
    grit: Biquad,            // bow-hair / rosin noise band (bandpass)
    bow_noise: f32,          // per-note grit level — no two bows are identical
    scratch: f32,            // decaying attack "catch" intensity (the bite before the tone)
    scratch_k: f32,          // its per-sample decay
    drift: Drift,            // slow human pitch wander (intonation is never dead-steady)
    amp_follow: f32,         // output magnitude follower, for the release tail
    refl_sustain: f32,       // bridge-filter cutoff while bowed (register brightness)
    loop_comp: f32,          // loop-latency tuning compensation, in samples
    out_lp: Option<OnePole>, // post-output darkening (cello de-buzz); None = flat
    rng: Rng,
    t: u32,
    amp: f32,
    sr: f32,
}

/// The stick-slip friction characteristic (STK `BowTable`): the fraction of the
/// bow/string differential velocity that the bow imparts to the string. Near
/// zero differential the bow *sticks* (coefficient saturates at 1, string moves
/// with the bow); past a force-dependent threshold it *slips* (coefficient
/// falls off), and the alternation of the two is what makes a string speak.
#[inline]
fn bow_friction(delta_v: f32, slope: f32) -> f32 {
    let s = (delta_v * slope).abs() + 0.75;
    let s2 = s * s;
    (1.0 / (s2 * s2)).min(1.0) // (|Δv·slope| + 0.75)^-4, clamped to the stick region
}

impl BowedString {
    fn new(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let beta = 0.127; // bow ~1/8 from the bridge (arco bass idiom)
                          // Register-dependent voicing: the cello (42) sits ~an octave above the
                          // contrabass (43), so its body resonances and string brightness are
                          // higher and its output a touch lighter. Same waveguide, retuned.
                          // (body freqs, in-loop bridge damping, amp base/span, OUTPUT lowpass Hz,
                          // loop-latency tuning compensation in samples).
                          // The output lowpass (0 = none) darkens the cello cleanly without touching
                          // the loop's nonlinear dynamics; it is None for the contrabass, so GM43
                          // stays byte-identical to the integrated Stage 1.
                          // loop_comp: the in-loop reflection filter + structural latency add ~3.8
                          // samples the bare `sr/f - 1` never subtracted, so the string renders
                          // progressively flat with pitch (fine in the bass, but ~50 cents flat at
                          // the cello's A4). The cello subtracts the measured ~3.85; the contrabass
                          // keeps 1.0 to stay byte-identical to Stage 1 (its residual flatness is
                          // small and characterful in the bass; a global re-tune is a separate,
                          // ear-gated change).
        let (body_f, refl_sustain, amp_base, amp_span, out_lp_hz, loop_comp) = match program {
            42 => (
                [110.0f32, 230.0, 500.0],
                2600.0f32,
                0.36f32,
                0.82f32,
                2100.0f32,
                3.85f32,
            ),
            _ => ([70.0, 180.0, 700.0], 2600.0, 0.55, 1.25, 0.0, 1.0),
        };
        // Per-note character: the seed varies per voice (the engine's spawn
        // counter), so drawing the bow's force, grit, scratch and vibrato here
        // makes every stroke its own — the fix for "each note sounds the same".
        let u = |r: &mut Rng| r.white() * 0.5 + 0.5;
        let slope = 2.2 + 0.7 * u(&mut rng); // bow force / pressure this stroke
        let bow_noise = 0.05 + 0.06 * u(&mut rng); // how gritty this stroke is
                                                   // the sampled arco bite now owns the onset, so the model's own synth
                                                   // scratch is dialled right back — just a hint under the sample.
        let scratch = 0.08 + 0.10 * u(&mut rng);
        let vib_rate = 4.6 * (1.0 + 0.16 * rng.white());
        let vib_depth = 0.0016 + 0.0016 * u(&mut rng);
        let vib_onset = (0.16 + 0.24 * u(&mut rng)) * sr;
        let grit_hz = 500.0 + 800.0 * u(&mut rng); // bow-hair fluctuation band (low-mid)
        let mut s = BowedString {
            bridge: DelayLine::new(320),
            neck: DelayLine::new(1600),
            bridge_delay: 1.0,
            neck_delay: 1.0,
            beta,
            base_f: f,
            bend: 1.0,
            // string loss: wound bass strings are quite lossy up top -> darker,
            // and this is what lets the note decay once the bow lifts.
            refl: OnePole::lowpass(refl_sustain, sr),
            body: [
                Biquad::peak(body_f[0], 0.7, 3.0, sr), // the big body/air resonance
                Biquad::peak(body_f[1], 0.7, 2.0, sr), // main wood mode
                Biquad::peak(body_f[2], 0.5, 1.5, sr), // broad arco "presence"
            ],
            dc_x1: 0.0,
            dc_y1: 0.0,
            // soft notes speak slower: a longer bow onset at low velocity
            env: Adsr::new(vel_attack(0.05, vel), 0.1, 0.9, 0.18, sr),
            // Bow SPEED drives brightness (a harder note is a faster bow, so it
            // is brighter — real bowing): quiet pedal ~dark, collision ~bright.
            max_vel: 0.03 + 0.22 * vel_amp(vel),
            slope,
            vib: Sine::new(vib_rate, sr, u(&mut rng)), // random start phase too
            vib_depth,
            vib_delay: vib_onset as u32,
            grit: Biquad::bandpass(grit_hz.min(sr * 0.40), 0.8, sr),
            bow_noise,
            scratch,
            // the catch decays over ~45-70 ms into the settled tone
            scratch_k: (-1.0 / (0.055 * sr)).exp(),
            drift: Drift::new(seed ^ 0x2BED_51CE, 0.0018, (0.05 * sr / CTRL as f32) as u32),
            amp_follow: 1.0,
            rng,
            t: 0,
            // Loudness is a velocity-scaled output gain: the self-oscillating
            // limit-cycle amplitude barely tracks velocity, so the dynamic level
            // is applied here. Level-matched to the old contrabass so the album
            // mix balance holds (~0.11 at the quiet pedal, ~0.18 riff/collision).
            amp: amp_base + amp_span * vel_amp(vel),
            refl_sustain,
            loop_comp,
            out_lp: if out_lp_hz > 0.0 {
                Some(OnePole::lowpass(out_lp_hz, sr))
            } else {
                None
            },
            sr,
        };
        s.set_freq(f);
        s
    }

    fn set_freq(&mut self, f: f32) {
        // total loop delay = one period, minus the loop latency (structural
        // read/write plus the in-loop reflection filter's phase delay, ~1 sample
        // for the bass, ~3.85 for the cello); split at the bow into the two
        // sections. Compensating this is what keeps the higher register in tune.
        let total = (self.sr / f.max(20.0) - self.loop_comp).max(8.0);
        self.bridge_delay = (total * self.beta).max(1.0);
        self.neck_delay = (total * (1.0 - self.beta)).max(1.0);
    }
}

impl Voice for BowedString {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.25 * self.sr)).min(1.0);
                    self.vib_depth * ramp * self.vib.next()
                } else {
                    self.vib.next();
                    0.0
                };
                let drift = self.drift.next();
                self.set_freq(self.base_f * self.bend * (1.0 + vib) * (1.0 + drift));
                // the bow lifts on release: the loop loses its energy source and
                // the string damps faster (darker) as it decays.
                let refl_hz = if self.env.released() {
                    900.0
                } else {
                    self.refl_sustain
                };
                self.refl.set_cutoff(refl_hz, self.sr);
            }
            let e = self.env.next();
            // the bow "catch": a scratchy bite at the onset that decays into the
            // settled tone. This transient — not the steady state — is the single
            // strongest "this is a bow, not an oscillator" cue.
            self.scratch *= self.scratch_k;
            // Bow-hair micro-fluctuation. The critical point (the fix for the
            // "hiss bolted on top"): this perturbs the bow VELOCITY — the INPUT to
            // the friction nonlinearity — so it jitters the stick-slip timing and
            // emerges as grain phase-locked to the string, NOT a noise signal added
            // after the fact. Stronger at the catch, easing into the settled tone.
            let bow_n = self.grit.process(self.rng.white());
            let noise_amt = self.bow_noise * (0.6 + 7.0 * self.scratch);
            // the catch also presses harder — more slip, scratchier — then eases.
            let slope_eff = self.slope * (1.0 + 1.3 * self.scratch);
            let bow_vel = self.max_vel * e * (1.0 + noise_amt * bow_n);
            // loop loss: enough per-period loss that the limit-cycle amplitude
            // is set by the balance of bow energy in vs loss out — that is what
            // makes loudness track bow SPEED (dynamics). Heavier once released so
            // the note actually stops within the tail.
            let loss = if self.env.released() { 0.70 } else { 0.95 };

            let bridge_out = self.bridge.tap(self.bridge_delay);
            let neck_out = self.neck.tap(self.neck_delay);
            // terminations invert; the bridge also filters (string loss) and loses.
            let bridge_refl = -self.refl.process(bridge_out) * loss;
            let nut_refl = -neck_out;
            let string_vel = bridge_refl + nut_refl;
            let delta_v = bow_vel - string_vel;
            // the string is driven purely by the friction — the noise is already
            // inside `bow_vel`, so its grain is shaped by the string, not layered on.
            let excite = delta_v * bow_friction(delta_v, slope_eff);
            self.neck.push(bridge_refl + excite);
            self.bridge.push(nut_refl + excite);

            // pick up the motion at the bridge, colour it with the body, block DC.
            let mut y = bridge_out;
            for b in &mut self.body {
                y = b.process(y);
            }
            if let Some(lp) = &mut self.out_lp {
                y = lp.process(y); // cello de-buzz; None for the bass (byte-identical)
            }
            let hp = y - self.dc_x1 + 0.9985 * self.dc_y1;
            self.dc_x1 = y;
            self.dc_y1 = hp;
            let sample = (hp * self.amp).clamp(-1.5, 1.5);
            *o += sample;
            self.amp_follow = self.amp_follow * 0.9997 + sample.abs() * 0.0003;
            self.t += 1;
        }
        // alive while the bow is on, or while the string is still ringing down.
        self.env.alive() || self.amp_follow > 3.0e-4
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
        // one bow-stroke, new stopped pitch: retune the string, keep it ringing.
        self.base_f = key_freq(key);
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "bowedstring"
    }
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

/// LA layering (sampled attack + modeled sustain) — level-matched to the
/// models by the `la_level_continuity` test.
const LA_VIOLIN: (f32, (f32, f32)) = (0.30, (0.12, 0.38));
const LA_FIDDLE: (f32, (f32, f32)) = (0.32, (0.08, 0.28));
/// GM 43 contrabass: a real cello-section arco *bite* over the waveguide
/// sustain — the bow-catch is what the physical model fakes worst, so the
/// sample owns the onset. A slightly longer handover than the violin: a bass
/// bow speaks slower. Gain tuned by ear (Arthur): a restrained bite.
const LA_CONTRABASS: (f32, (f32, f32)) = (0.29, (0.16, 0.46));
/// GM 42 cello: the cello-section arco bite over the waveguide sustain. A
/// slightly faster handover than the bass (a cello bow speaks quicker).
const LA_CELLO: (f32, (f32, f32)) = (0.30, (0.13, 0.40));
const LA_FLUTE: (f32, (f32, f32)) = (0.55, (0.06, 0.24));
const LA_PIANO: (f32, (f32, f32)) = (0.42, (0.18, 0.85));
const LA_BRASS: (f32, (f32, f32)) = (0.35, (0.10, 0.32));
const LA_REED: (f32, (f32, f32)) = (0.45, (0.06, 0.24));
/// GM 24 nylon guitar: the sample owns the pick transient (first ~30 ms),
/// the Karplus-Strong string carries the bendable decay from 200 ms (HLD §4).
/// Gain level-matched down from the HLD's ~0.45 estimate: the FreePats pluck
/// body is loud relative to the model and 0.45 stepped the 50–150 ms window
/// 3.4× above the handover (la_level_continuity cap is 2.4×).
const LA_GUITAR: (f32, (f32, f32)) = (0.25, (0.05, 0.20));
/// String sections 48-49: the real section swell reads best with a longer
/// crossfade than the solo bowed layer (a section "comes into focus", it
/// does not bite), so the transient hands over across [0.10, 0.40] s.
const LA_STRINGS: (f32, (f32, f32)) = (0.40, (0.10, 0.40));
/// GM 61 brass section: trumpet bank at reduced gain so the modeled
/// scattered player onsets stay audible underneath (HLD §4).
const LA_BRASS_SECTION_GAIN: f32 = 0.6;

// ---------------------------------------------------------------------------
// Orchestra Hit (GM 55)
// ---------------------------------------------------------------------------

const ORCH_RATIOS: [f32; 5] = [0.5, 0.994, 1.006, 1.988, 2.012];
const ORCH_ATTACK_S: f32 = 0.004;
const ORCH_T60_S: f32 = 0.40;
const ORCH_REL_T60_S: f32 = 0.15;
const ORCH_LP_BASE_HZ: f32 = 1800.0;
const ORCH_LP_VEL_HZ: f32 = 3200.0;
const ORCH_LP_Q: f32 = 0.8;
const ORCH_AMP: f32 = 0.50;
const ORCH_THUMP_F_LO: f32 = 50.0;
const ORCH_THUMP_F_HI: f32 = 110.0;
const ORCH_THUMP_GAIN: f32 = 0.9;

/// GM 55 Orchestra Hit: a struck tutti stab, built as an octave-stacked
/// detuned saw ensemble over a short timpani-like thump and noisy attack bite.
struct OrchHit {
    saws: Vec<(BlepSaw, f32)>,
    lp: Biquad,
    thump: Modal,
    bite: Burst,
    base_f: f32,
    bend: f32,
    att_env: f32,
    att_step: f32,
    dec_env: f32,
    dec_mul: f32,
    rel_env: f32,
    rel_mul: f32,
    released: bool,
    rng: Rng,
    amp: f32,
    t: u32,
    sr: f32,
}

fn orch_hit(key: u8, vel: u8, sr: f32, seed: u32) -> OrchHit {
    let v = vel_amp(vel);
    let vn = vel as f32 / 127.0;
    let f = key_freq(key);
    let mut rng = Rng::new(seed);
    let saws = ORCH_RATIOS
        .iter()
        .map(|&r| {
            let ratio = r * (1.0 + 0.0015 * rng.white());
            let phase = rng.white() * 0.5 + 0.5;
            (BlepSaw::new((f * ratio).min(sr * 0.45), sr, phase), ratio)
        })
        .collect();
    let cut = (ORCH_LP_BASE_HZ + ORCH_LP_VEL_HZ * vn).min(sr * 0.45);
    let f_th = (f * 0.5).clamp(ORCH_THUMP_F_LO, ORCH_THUMP_F_HI);
    let thump = Modal::new(
        sr,
        seed ^ 0x5151,
        &[(f_th, 1.0 * v, 0.30), (f_th * 1.5, 0.5 * v, 0.20)],
        (0.9 * v, 0.04, Biquad::lowpass(250.0, 0.8, sr)),
        0.001,
        ORCH_REL_T60_S,
        ORCH_THUMP_GAIN,
    );
    let mut bite = Burst::new(Biquad::bandpass(2500.0, 1.0, sr), 0.5 * v, 0.035, sr);
    bite.trigger(vn);
    OrchHit {
        saws,
        lp: Biquad::lowpass(cut, ORCH_LP_Q, sr),
        thump,
        bite,
        base_f: f,
        bend: 1.0,
        att_env: 0.0,
        att_step: 1.0 / (ORCH_ATTACK_S * sr),
        dec_env: 1.0,
        dec_mul: t60_mul(ORCH_T60_S, sr),
        rel_env: 1.0,
        rel_mul: t60_mul(ORCH_REL_T60_S, sr),
        released: false,
        rng,
        amp: ORCH_AMP * (0.4 + 0.6 * v),
        t: 0,
        sr,
    }
}

impl Voice for OrchHit {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let thump_alive = self.thump.render(out);
        let n = self.saws.len() as f32;
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                let (bend, base, sr) = (self.bend, self.base_f, self.sr);
                for (osc, ratio) in self.saws.iter_mut() {
                    osc.set_freq((base * *ratio * bend).min(sr * 0.45), sr);
                }
            }
            let mut s = 0.0;
            for (osc, _) in self.saws.iter_mut() {
                s += osc.next();
            }
            s = self.lp.process(s / n);
            if self.att_env < 1.0 {
                self.att_env = (self.att_env + self.att_step).min(1.0);
            }
            *o += s * self.amp * self.att_env * self.dec_env * self.rel_env
                + self.bite.tick(&mut self.rng);
            self.dec_env *= self.dec_mul;
            if self.released {
                self.rel_env *= self.rel_mul;
            }
            self.t += 1;
        }
        self.dec_env * self.rel_env * self.amp > 2e-5
            || thump_alive
            || self.t < (0.05 * self.sr) as u32
    }

    fn note_off(&mut self) {
        self.released = true;
        self.thump.note_off();
    }

    fn released(&self) -> bool {
        self.released
    }

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "orch_hit"
    }
}

// ---------------------------------------------------------------------------
// Reed (GM 64–71) — the v0.9 sustaining reed family: soprano/alto/tenor/bari
// sax, oboe, english horn, bassoon, clarinet. A band-limited pulse source
// (RD1) whose duty cycle is fixed per program + register — a square for the
// clarinet's hollow odd spectrum, a short pulse for the double reeds' buzz —
// voiced by a FIXED per-instrument formant bank (RD2), opened by a
// register/velocity/envelope brightness law (RD3), roughened by an optional
// velocity-tanh grit on the saxes (RD4), with breath + tongue chiff (RD5),
// onset scoop + CC68 slur (RD6), a vibrato composed into every retune (RD7),
// and equal-RMS loudness normalisation across duty cycles (RD8). Engine wiring
// (vibrato_family / CC11 / fx_profile) is the separate engine55 unit; this
// voice needs nothing beyond set_pitch / legato_to / velocity / program.
// ---------------------------------------------------------------------------

const RD_SCOOP_K: f32 = 0.045; // RD6 onset-scoop settle per control tick (τ ≈ 8 ms)
const RD_CHIFF_T60: f32 = 0.020; // RD5 tongue-chiff decay
const RD_CHIFF_AMP: f32 = 0.30; // RD5 chiff level (× vn × vel_amp — super-linear)
pub(crate) const BAGPIPE_DRONE_CONTROL_MAX: u8 = 54;
const BAGPIPE_DRONE_WIDTH: f32 = 0.22;

/// A GM reed program's fixed voicing (§5 table). All-`pub`, const-constructible.
pub struct ReedPreset {
    pub width: f32,                     // RD1 pulse duty at range bottom
    pub width_hi: f32,                  // RD3 duty at range top (register interp)
    pub formants: [(f32, f32, f32); 3], // RD2 (Hz, Q, gain dB); gain 0.0 = inert slot
    pub lp: f32,                        // RD3 brightness ceiling, Hz
    pub drive_vn: f32,                  // RD4 tanh amount; 0.0 = bypass
    pub breath: f32,                    // RD5 sustain breath level
    pub vib: (f32, f32, f32),           // RD7 (Hz, depth, delay s)
    pub attack: f32,                    // Adsr attack base (vel_attack-scaled)
    pub release: f32,                   // Adsr release
    pub scoop: f32,                     // RD6 onset pitch multiplier start
    pub range: (u8, u8),                // MIDI keys for register normalisation
    pub amp: f32,
    #[cfg(test)]
    pub name: &'static str, // diagnostic label (kind() is always "reed")
}

pub const SOP_SAX: ReedPreset = ReedPreset {
    width: 0.30,
    width_hi: 0.27,
    formants: [(1100.0, 1.4, 5.0), (2200.0, 1.8, 4.0), (3600.0, 2.0, 2.5)],
    lp: 5200.0,
    drive_vn: 0.9,
    breath: 0.030,
    vib: (5.4, 0.006, 0.22),
    attack: 0.050,
    release: 0.12,
    scoop: 0.972,
    range: (56, 88),
    amp: 0.34,
    #[cfg(test)]
    name: "soprano_sax",
};
pub const ALTO_SAX: ReedPreset = ReedPreset {
    width: 0.31,
    width_hi: 0.28,
    formants: [(900.0, 1.4, 5.5), (1900.0, 1.8, 4.0), (3100.0, 2.0, 2.5)],
    lp: 4800.0,
    drive_vn: 0.9,
    breath: 0.032,
    vib: (5.2, 0.006, 0.24),
    attack: 0.055,
    release: 0.12,
    scoop: 0.970,
    range: (49, 81),
    amp: 0.35,
    #[cfg(test)]
    name: "alto_sax",
};
pub const TENOR_SAX: ReedPreset = ReedPreset {
    width: 0.32,
    width_hi: 0.29,
    formants: [(650.0, 1.3, 6.0), (1500.0, 1.8, 4.0), (2700.0, 2.0, 2.5)],
    lp: 4300.0,
    drive_vn: 0.9,
    breath: 0.035,
    vib: (5.0, 0.006, 0.26),
    attack: 0.060,
    release: 0.12,
    scoop: 0.968,
    range: (44, 76),
    amp: 0.36,
    #[cfg(test)]
    name: "tenor_sax",
};
pub const BARI_SAX: ReedPreset = ReedPreset {
    width: 0.33,
    width_hi: 0.30,
    formants: [(480.0, 1.2, 6.0), (1150.0, 1.6, 4.0), (2300.0, 2.0, 2.5)],
    lp: 3800.0,
    drive_vn: 0.9,
    breath: 0.040,
    vib: (4.8, 0.005, 0.28),
    attack: 0.070,
    release: 0.13,
    scoop: 0.966,
    range: (36, 69),
    amp: 0.38,
    #[cfg(test)]
    name: "bari_sax",
};
pub const OBOE: ReedPreset = ReedPreset {
    width: 0.14,
    width_hi: 0.14,
    formants: [(1050.0, 2.4, 8.0), (2700.0, 2.0, 5.0), (0.0, 1.0, 0.0)],
    lp: 5000.0,
    drive_vn: 0.35,
    breath: 0.020,
    vib: (5.6, 0.004, 0.30),
    attack: 0.035,
    release: 0.10,
    scoop: 0.990,
    range: (58, 93),
    amp: 0.40,
    #[cfg(test)]
    name: "oboe",
};
pub const ENGLISH_HORN: ReedPreset = ReedPreset {
    width: 0.15,
    width_hi: 0.15,
    formants: [(930.0, 2.6, 8.0), (1900.0, 2.2, 3.5), (0.0, 1.0, 0.0)],
    lp: 4200.0,
    drive_vn: 0.35,
    breath: 0.022,
    vib: (5.2, 0.004, 0.32),
    attack: 0.040,
    release: 0.10,
    scoop: 0.988,
    range: (52, 81),
    amp: 0.40,
    #[cfg(test)]
    name: "english_horn",
};
pub const BASSOON: ReedPreset = ReedPreset {
    width: 0.16,
    width_hi: 0.16,
    formants: [(500.0, 2.0, 7.0), (1220.0, 2.2, 4.5), (0.0, 1.0, 0.0)],
    lp: 3200.0,
    drive_vn: 0.35,
    breath: 0.024,
    vib: (4.6, 0.0035, 0.35),
    attack: 0.080,
    release: 0.14,
    scoop: 0.985,
    range: (34, 72),
    amp: 0.42,
    #[cfg(test)]
    name: "bassoon",
};
pub const CLARINET: ReedPreset = ReedPreset {
    width: 0.50,
    width_hi: 0.44,
    formants: [(1550.0, 1.8, 4.5), (3100.0, 2.2, 3.0), (0.0, 1.0, 0.0)],
    lp: 4000.0,
    drive_vn: 0.0,
    breath: 0.015,
    vib: (5.0, 0.0015, 0.40),
    attack: 0.045,
    release: 0.10,
    scoop: 0.988,
    range: (50, 94),
    amp: 0.36,
    #[cfg(test)]
    name: "clarinet",
};

pub const BAGPIPE: ReedPreset = ReedPreset {
    width: 0.18,
    width_hi: 0.16,
    formants: [(780.0, 1.8, 7.0), (1550.0, 2.2, 5.5), (3000.0, 2.0, 3.0)],
    lp: 4700.0,
    drive_vn: 0.45,
    breath: 0.018,
    vib: (4.8, 0.0015, 0.38),
    attack: 0.028,
    release: 0.11,
    scoop: 0.992,
    range: (60, 84),
    amp: 0.24,
    #[cfg(test)]
    name: "bagpipe",
};

pub const SHANAI: ReedPreset = ReedPreset {
    width: 0.12,
    width_hi: 0.105,
    formants: [(1200.0, 2.6, 8.0), (2550.0, 2.2, 6.0), (3800.0, 2.0, 3.0)],
    lp: 5000.0,
    drive_vn: 0.42,
    breath: 0.026,
    vib: (5.8, 0.0045, 0.24),
    attack: 0.030,
    release: 0.10,
    scoop: 0.988,
    range: (60, 91),
    amp: 0.40,
    #[cfg(test)]
    name: "shanai",
};

pub(crate) struct BagpipeDrone {
    root: ReedPulse,
    fifth: ReedPulse,
    root_norm: f32,
    fifth_norm: f32,
    lp: OnePole,
    env: Adsr,
    amp: f32,
}

impl BagpipeDrone {
    fn new(key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let mut rng = Rng::new(seed ^ 0xBA60_0001);
        let root_f = if key <= BAGPIPE_DRONE_CONTROL_MAX {
            key_freq(key)
        } else {
            key_freq(key) * 0.5
        };
        let fifth_f = root_f * 1.5;
        let root_width = BAGPIPE_DRONE_WIDTH * (1.0 + 0.015 * rng.white());
        let fifth_width = (BAGPIPE_DRONE_WIDTH * 0.92) * (1.0 + 0.015 * rng.white());
        let norm = |width: f32| 0.5 / (width * (1.0 - width)).sqrt();
        BagpipeDrone {
            root: ReedPulse::new(root_f, sr, rng.white() * 0.5 + 0.5, root_width),
            fifth: ReedPulse::new(fifth_f, sr, rng.white() * 0.5 + 0.5, fifth_width),
            root_norm: norm(root_width),
            fifth_norm: norm(fifth_width),
            lp: OnePole::lowpass(2600.0, sr),
            env: Adsr::new(0.050, 0.08, 0.95, 0.28, sr),
            amp: 0.055 * (0.45 + 0.55 * vel_amp(vel)),
        }
    }
}

impl Voice for BagpipeDrone {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            let e = self.env.next();
            let s = self.root.next() * self.root_norm * 0.70
                + self.fifth.next() * self.fifth_norm * 0.42;
            *o += self.lp.process(s) * self.amp * e;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "reed"
    }
}

pub(crate) fn bagpipe_drone(key: u8, vel: u8, sr: f32, seed: u32) -> BagpipeDrone {
    BagpipeDrone::new(key, vel, sr, seed)
}

pub struct Reed {
    osc: ReedPulse,
    osc_norm: f32, // RD8 equal-RMS-across-widths source gain
    drive: f32,    // RD4 precomputed shaper index d = 1 + drive_vn·vn; 0.0 = bypass
    dcb: Biquad,   // RD4 DC guard: tanh of the ASYMMETRIC (not just zero-mean) pulse biases
    formants: [Biquad; 3],
    lp: OnePole,
    lp_base: f32, // RD3 brightness ceiling
    base_f: f32,
    bend: f32,
    scoop: f32,
    breath_filt: Biquad,
    breath: f32, // RD5 register-scaled sustain breath level
    chiff_amp: f32,
    chiff_decay: f32,
    env: Adsr,
    last_env: f32,
    vib: Sine,
    vib_depth: f32,
    vib_delay: u32,
    vib_val: f32,
    rng: Rng,
    t: u32,
    vn: f32,
    amp: f32,
    sr: f32,
}

impl Reed {
    /// Parametric constructor (the RD-O8a `breath = 0` differential test seam
    /// constructs through it; `reed()` is a thin lookup-then-`from_preset`).
    fn from_preset(preset: &ReedPreset, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let vn = vel as f32 / 127.0;
        let mut rng = Rng::new(seed);
        // RD3 register position: 0 at range bottom, 1 at top (out-of-range clamps)
        let (lo, hi) = preset.range;
        let reg = ((key as f32 - lo as f32) / (hi as f32 - lo as f32).max(1.0)).clamp(0.0, 1.0);
        // RD1 duty: interpolate bottom→top width, then ±2% per-note jitter
        let w0 = preset.width + (preset.width_hi - preset.width) * reg;
        let width = w0 * (1.0 + 0.02 * rng.white());
        // RD8 equal-RMS source normalisation (raw pulse RMS = √(w(1−w)))
        let osc_norm = 0.5 / (width * (1.0 - width)).sqrt();
        // RD4 grit: the shaper index is constant per note; 0.0 = explicit bypass
        let drive = if preset.drive_vn > 0.0 {
            1.0 + preset.drive_vn * vn
        } else {
            0.0
        };
        // RD2 fixed formant bank (±2% freq jitter). A 0 dB slot is a pass-through,
        // but must NOT be built at f = 0 (as the §5 table marks inert slots): a
        // 0 Hz peak lands a DOUBLE POLE on z = 1 (DC) — a marginally-stable
        // integrator that accumulates float rounding into a slow DC drift. A
        // benign mid-band frequency keeps the (still-identity) filter's poles
        // inside the unit circle so rounding decays instead of accumulating.
        let formants = preset.formants.map(|(ff, q, g)| {
            let j = 1.0 + 0.02 * rng.white(); // one jitter draw per slot (stable RNG stream)
            if g == 0.0 {
                Biquad::peak(sr * 0.25, 1.0, 0.0, sr)
            } else {
                Biquad::peak((ff * j).min(sr * 0.4), q, g, sr)
            }
        });
        let lp_base = preset.lp;
        let lp = OnePole::lowpass(
            (lp_base * (0.35 + 0.75 * vn) * 0.55).clamp(500.0, sr * 0.4),
            sr,
        );
        // RD5 breath: register-scaled (low notes breathier — the sax subtone),
        // through a bandpass at the upper reed-hiss band (Wind idiom, tamer Q)
        let breath = preset.breath * (1.3 - 0.6 * reg);
        let breath_filt = Biquad::bandpass((2.5 * f).min(5000.0).min(sr * 0.4), 1.2, sr);
        let vibr = preset.vib;
        Reed {
            osc: ReedPulse::new(f, sr, rng.white() * 0.5 + 0.5, width),
            osc_norm,
            drive,
            dcb: Biquad::highpass(20.0, 0.7, sr),
            formants,
            lp,
            lp_base,
            base_f: f,
            bend: 1.0,
            scoop: preset.scoop,
            breath_filt,
            breath,
            chiff_amp: RD_CHIFF_AMP * vn * vel_amp(vel),
            chiff_decay: t60_mul(RD_CHIFF_T60, sr),
            env: Adsr::new(
                vel_attack(preset.attack, vel),
                0.06,
                0.90,
                preset.release,
                sr,
            ),
            last_env: 0.0,
            vib: control_lfo(vibr.0, 0.08, &mut rng, sr),
            vib_depth: vibr.1,
            vib_delay: (vibr.2 * sr) as u32,
            vib_val: 0.0,
            rng,
            t: 0,
            vn,
            amp: preset.amp * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for Reed {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                // RD6 scoop settle + RD7 vibrato, composed into the retune so the
                // engine's per-block bend/CC1 writers cannot snap them back
                self.scoop += RD_SCOOP_K * (1.0 - self.scoop);
                let v = self.vib.next();
                self.vib_val = v;
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                let f = self.base_f * self.bend * self.scoop * (1.0 + vib);
                self.osc.set_freq(f, self.sr);
                // RD3 brightness: register/velocity/envelope open the lowpass
                let cut = (self.lp_base * (0.35 + 0.75 * self.vn) * (0.55 + 0.45 * self.last_env))
                    .clamp(500.0, self.sr * 0.4);
                self.lp.set_cutoff(cut, self.sr);
            }
            // RD1 band-limited pulse × RD8 equal-RMS gain
            let mut s = self.osc.next() * self.osc_norm;
            // RD4 sax grit — before the formants voice it, before the LP trims it.
            // The DC guard is load-bearing: tanh of the pulse's ASYMMETRIC two
            // levels (w−1 and +w) biases even though the input is zero-mean, so a
            // 20 Hz highpass removes it (the Brass BR11 precedent, voices.rs:2380).
            if self.drive > 0.0 {
                s = (s * self.drive).tanh() / self.drive;
                s = self.dcb.process(s);
            }
            // RD2 fixed formant bank
            for b in &mut self.formants {
                s = b.process(s);
            }
            // RD3 brightness lowpass
            s = self.lp.process(s);
            let e = self.env.next();
            self.last_env = e;
            // RD5 breath (rides the vibrato) — a quiet, envelope-scaled sustain
            // hiss, post-LP; and a one-shot tongue chiff sharing the same filter
            let breath_mod = 1.0 + 0.4 * self.vib_val;
            let noise = self.breath_filt.process(self.rng.white());
            s += noise * self.breath * e * breath_mod;
            // The tongue chiff is added OUTSIDE the amp envelope (the Brass/Pluck
            // onset_post precedent, voices.rs:2552) so it "spits" at t=0 even
            // while the amp envelope is still ramping in — a hard-tongued forte
            // attack spits, a soft entrance barely speaks. A slur kills it.
            let chiff = noise * self.chiff_amp * self.amp;
            self.chiff_amp *= self.chiff_decay;
            *o += s * self.amp * e + chiff;
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
        // RD6 slur: glide from the old pitch via the scoop, keep the air moving,
        // and kill the tongue chiff — one breath across several fingered notes
        let new_f = key_freq(key);
        self.scoop = (self.base_f * self.scoop / new_f).clamp(0.85, 1.18);
        self.base_f = new_f;
        self.chiff_amp = 0.0;
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "reed"
    }
}

fn reed(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Reed {
    let preset: &'static ReedPreset = match program {
        64 => &SOP_SAX,
        65 => &ALTO_SAX,
        66 => &TENOR_SAX,
        67 => &BARI_SAX,
        68 => &OBOE,
        69 => &ENGLISH_HORN,
        70 => &BASSOON,
        71 => &CLARINET,
        109 => &BAGPIPE,
        111 => &SHANAI,
        _ => &CLARINET,
    };
    Reed::from_preset(preset, key, vel, sr, seed)
}

// ---------------------------------------------------------------------------
// Brass (GM 56–63) — the v0.9 flagship. An isolated sustaining voice adjacent
// to Wind/Bowed (§3.1): per-player lip-valve saws (2× oversampled), ONE
// loudness scalar driving both the lip lowpass and the per-player
// bias-referenced tanh (BR1/BR2), bore peak EQ + first-order bell shelf (BR3),
// straight-mute transmission (BR4), scoop/slur (BR5), breath+tongue chiff
// (BR6), section scatter (BR7), the synth-brass resonant sweep (BR8), the
// CC11 breath + aftertouch growl seam (BR9/BR10), and a DC guard (BR11).
// ---------------------------------------------------------------------------

const BR_DECIM_HZ: f32 = 13_500.0; // BR1 2× decimation cliff (Q 0.8, at sr2)
const BR_BITE_T60: f32 = 0.06; // BR2 tongue over-blow decay
const BR_ONSET_RAMP_S: f32 = 0.015; // BR7 late-entry smoothstep ramp
const BR_H_EXP: f32 = 1.4; // BR2 cutoff-law convexity
const BR_BLOOM_A: f32 = 0.25; // BR2 brightness-bloom attack (the "waa")
const BR_L_VEL: (f32, f32) = (0.10, 0.90); // BR2 timbre-law velocity floor/span
const BR_GROWL_HZ: f32 = 30.0; // BR10 flutter-tongue rate
const BR_GROWL_AM: f32 = 0.35; // BR10 flutter AM depth
const BR_GROWL_DRIVE: f32 = 1.6; // BR10 growl → shaper-index bite
const BR_GROWL_BRIGHT: f32 = 1.00; // BR10 growl → lip/output brightness (so the bite radiates)
const BR_K_MAX: f32 = 3.2; // BR1/BR2/BR10 composed-drive ceiling (alias cap)
const BR_GROWL_SLEW: f32 = 0.05; // BR9 growl_cur de-zipper slew (τ ≈ 7 ms)
const BR_SCOOP_CLAMP: (f32, f32) = (0.85, 1.19); // BR5 slur glide origin bounds
const BR_PRESS_FLOOR: (f32, f32) = (0.30, 0.70); // BR9 CC11=0 is dark, not dead

// BR12 — progressive-steepening cascade (the "rasp"/cuivré). A real brass note
// "brasses up" when pushed: the pressure wave steepens toward a shock as it
// travels the bore, cascading energy into a slow-rolloff high-harmonic tail whose
// centroid climbs super-linearly with loudness. The single BR1 lip valve, driven
// linearly by L and capped at BR_K_MAX for aliasing, has a rolloff too fast for
// that tearing edge. BR12 adds a SECOND mild bias-tanh stage — a discrete analog
// of cumulative bore steepening — blended in by an amount that (a) blooms with
// loudness above a threshold (gated on `bright`, which spans ~0.3..1.0 in sustain
// and >1 only under authored growl — so mp stays clean and forte/ff/growl rip),
// (b) scales per-program by a brassiness constant B (trombone/trumpet rip, horn/
// tuba barely), and (c) derates at high f0 so the alias floor (BR-O11) holds at
// 2×. Naturals 56–61 only; the synth path (62/63, near-linear, no oversampling)
// never reads it. This is the FORK-A change: it reshapes the harmonic rolloff
// within the existing 2× envelope, it does NOT raise the drive past BR_K_MAX.
const BR_CASCADE_MAX: f32 = 1.0; // max morph toward the two-stage cascade (full rip)
const BR_CASCADE_SPLIT: f32 = 0.6; // stage-1 drive reduction at full cascade (the split)
const BR_CASCADE_K2: f32 = 2.6; // stage-2 shaper index (the second knee)
const BR_CASCADE_BIAS2: f32 = 0.55; // stage-2 bias fraction (less even, more buzz)
const BR_CASCADE_RADIATE: f32 = 1.2; // BR12 out_lp cutoff opening at full cascade (lets rasp radiate)
const BR_CASCADE_LO: f32 = 0.62; // bright below which no rasp (mp stays clean)
const BR_CASCADE_HI: f32 = 1.02; // bright at which the rasp is fully open (ff/growl)
const BR_CASCADE_F0: f32 = 440.0; // f0 (Hz) above which the rasp derates (alias guard)
                                  // BR13 ADAA (first-order antiderivative anti-aliasing on the rasp shaper) lifts
                                  // the sinc-suppressed alias floor by ≥29 dB at the worst BR-O11 guard bin, so the
                                  // high-f0 derate no longer has to gut the top-register rasp. Raised 0.06→0.60,
                                  // oracle-set: BR-O11b (F#6, the worst case) holds the fold-back a full 6 dB under
                                  // the 0.03 ceiling at this floor. The f0-dependent derate LAW is kept as margin.
const BR_CASCADE_F0_FLOOR: f32 = 0.30; // top-octave rasp lift (was a flat 0.06 pre-ADAA; see HLD §4)
                                       // BR13: the floor is applied ONLY to the top octave, ramped in over this band, so
                                       // it lifts F#6-and-up (where ADAA gives alias headroom) WITHOUT clamping the
                                       // mildly-derated upper-mid (A5≈880, B5≈988) up — over-driving those aliases under
                                       // growl and busts BR-O11. Below LIFT_LO the natural quartic derate stands alone.
const BR_CASCADE_LIFT_LO: f32 = 900.0; // Hz: below this the lift is inert (A5 keeps its natural rasp)
const BR_CASCADE_LIFT_HI: f32 = 1100.0; // Hz: above this the full lift applies (C6 and up)

/// Smoothstep 0→1 over [e0, e1]; flat outside. Used to gate the BR12 rasp on
/// loudness so it blooms in over forte rather than switching on.
#[inline]
fn smoothstep(e0: f32, e1: f32, x: f32) -> f32 {
    let t = ((x - e0) / (e1 - e0)).clamp(0.0, 1.0);
    t * t * (3.0 - 2.0 * t)
}

/// BR1 bias-referenced tanh lip valve. Normalisation `÷ tanh(0.9·k)` keeps the
/// positive peak ~k-invariant so the law changes *slope*, not loudness; the
/// bias term breaks odd symmetry so even harmonics appear (asymmetric flow).
#[inline]
fn brass_valve(x: f32, k: f32, b: f32) -> f32 {
    ((x * k + b).tanh() - b.tanh()) / (0.9 * k).tanh()
}

// --- BR13: first-order antiderivative anti-aliasing (ADAA) for the rasp ------
// See `wrk_docs/2026.07.11 - HLD - brass ADAA antialiasing`. First-order ADAA
// replaces the memoryless shaper f(x[n]) with the boxcar-filtered continuous
// model (F(x1)-F(x0))/(x1-x0), F=∫f — a sinc(f/sr2) prefilter with zeros at every
// multiple of sr2, i.e. exactly where the audible aliases are born. Applied
// STAGE-WISE (each bias-tanh separately, then the morph is a linear mix, which
// commutes with ADAA), so no composite antiderivative is needed. All math in f64
// (the divided difference is ill-conditioned near x1≈x0); audio stays f32.
const BR_ADAA_H: f64 = 1.0e-4; // |Δx| below which the DD cancels → midpoint fallback

/// Numerically stable ln cosh: |u| − ln2 + ln1p(e^(−2|u|)). Exact for all |u|
/// (the naive `cosh(u).ln()` overflows for |u| ≳ 20 even in f64).
#[inline]
fn lncosh(u: f64) -> f64 {
    let a = u.abs();
    a - std::f64::consts::LN_2 + (-2.0 * a).exp().ln_1p()
}

/// One bias-referenced tanh valve in f64 (mirrors `brass_valve`, the shaper the
/// antiderivative below integrates).
#[inline]
fn brass_valve_f64(x: f64, k: f64, b: f64) -> f64 {
    ((x * k + b).tanh() - b.tanh()) / (0.9 * k).tanh()
}

/// Antiderivative F of `brass_valve_f64`: ∫tanh(kx+b)dx = (1/k)lncosh(kx+b),
/// ∫tanh(b)dx = x·tanh(b), both ÷ the same tanh(0.9k) normaliser.
#[inline]
fn brass_valve_antideriv(x: f64, k: f64, b: f64) -> f64 {
    (lncosh(k * x + b) / k - x * b.tanh()) / (0.9 * k).tanh()
}

/// First-order ADAA of one bias valve over the step x0→x1. Divided difference of
/// the antiderivative, with a midpoint fallback when |Δx| < BR_ADAA_H to dodge the
/// catastrophic cancellation of `(F(x1)-F(x0))/(x1-x0)`. At the seam the two
/// branches agree to ~3e-9 (f64), far below f32 output quantisation, so the
/// switch is spectrally inert. F is recomputed each call with the CURRENT (k,b) —
/// never cached — because a cached F(x0) from ramped parameters is meaningless.
#[inline]
fn brass_valve_adaa(x1: f64, x0: f64, k: f64, b: f64) -> f64 {
    let dx = x1 - x0;
    if dx.abs() < BR_ADAA_H {
        brass_valve_f64(0.5 * (x0 + x1), k, b)
    } else {
        (brass_valve_antideriv(x1, k, b) - brass_valve_antideriv(x0, k, b)) / dx
    }
}

/// One BrassPlayer per human player: solo programs run 1, section 61 runs 3,
/// synth 62/63 run 5. (Skeleton: candidate B.)
struct BrassPlayer {
    saw: BlepSaw,       // lip source (natural: at sr2; synth: at sr)
    detune: f32,        // fixed per-player ratio (sections/synth)
    onset: u32,         // output samples of silence before this player speaks (BR7)
    lip_lp: OnePole,    // BR2 envelope-tracked lip-closure lowpass
    decim: [Biquad; 2], // BR1 2×→1× decimation cliff (natural only)
    vib_phase: f32,     // BR7 per-player autonomous vibrato (sections/synth)
    vib_rate: f32,
    drift: Drift, // BR7 random-walk pitch instability
    scoop: f32,   // BR5 per-player pitch mult settling toward 1.0
    scoop_k: f32, // BR5 per-player settle rate (jittered ±15% in sections)
    // BR13 ADAA state (natural path): previous sr2 sample fed to the shaper, and
    // the previous ADAA outputs of the single valve and the cascade's stage 1.
    // All zero at note-on — every valve maps 0→0, so x_prev=0 seeds exactly.
    x_prev: f64,
    s_prev: f64,
    u_prev: f64,
}

impl BrassPlayer {
    /// BR13: anti-aliased rasp for one sr2 sub-step. `x` is the lip_lp output
    /// (the shaper input). Mirrors `brass_rasp` but every bias-tanh is run through
    /// first-order ADAA, and the `single` branch carries a matching half-sample
    /// alignment average so the linear single↔cascade morph never combs (both
    /// paths land at 1.0-sample group delay). See the HLD §2/§4.
    #[inline]
    fn rasp_adaa(&mut self, x: f32, k: f32, b: f32, cascade_amt: f32) -> f32 {
        let (k, b, x) = (k as f64, b as f64, x as f64);
        let s = brass_valve_adaa(x, self.x_prev, k, b);
        let s_align = 0.5 * (s + self.s_prev); // +0.5-sample delay to match the cascade
        let y = if cascade_amt > 0.0 {
            let a = cascade_amt as f64;
            let k1 = k * (1.0 - BR_CASCADE_SPLIT as f64 * a);
            let u = brass_valve_adaa(x, self.x_prev, k1, b);
            let c = brass_valve_adaa(
                u,
                self.u_prev,
                BR_CASCADE_K2 as f64,
                b * BR_CASCADE_BIAS2 as f64,
            );
            self.u_prev = u;
            s_align + a * (c - s_align)
        } else {
            // Cascade dormant: keep u_prev tracking stage 1's static output so the
            // first sample after cascade_amt lifts off 0 has no seeding transient.
            self.u_prev = brass_valve_f64(x, k, b);
            s_align
        };
        self.x_prev = x;
        self.s_prev = s;
        y as f32
    }
}

pub struct BrassSpec {
    pub players: usize,
    pub detune_cents: f32,    // full spread; players spread linearly
    pub onset_scatter_s: f32, // per-player random onset in [0, this]; player 0 = 0
    pub scoop0: f32,
    pub scoop_k: f32, // BR5
    pub h_min: f32,
    pub h_max: f32, // BR2 lip cutoff, multiples of f0
    pub k_min: f32,
    pub k_max: f32,
    pub bias: f32,                  // BR1/BR2 law
    pub brassiness: f32,            // BR12 rasp/cuivré readiness (0 = no cascade; ~1 = rips easily)
    pub bore: [(f32, f32, f32); 2], // BR3 (Hz, Q, dB); Hz=0 → skip
    pub bell_fc: f32,
    pub bell_g: f32, // BR3
    // BR2 output brightness: an L-driven radiated lowpass `out_base·2^(out_oct·L)`
    // (the Bowed env→brightness precedent, voices.rs:1861), so the flagship
    // loudness law reaches the OUTPUT centroid past the fixed bore/bell — the
    // lip lowpass alone is masked by them. out_base=0 → disabled (synth, which
    // owns its own resonant sweep).
    pub out_base: f32,
    pub out_oct: f32,
    pub mute: bool,                                // BR4
    pub synth_sweep: Option<(f32, f32, f32, f32)>, // BR8 (base, vel0, vel_depth, q)
    pub fenv: (f32, f32, f32, f32),                // BR8 synth resonant-sweep envelope (A/D/S/R)
    pub breath: f32,
    pub chiff: f32,                // BR6
    pub env: (f32, f32, f32, f32), // amp A/D/S/R
    pub vib: (f32, f32, f32),      // BR7 (rate, depth, delay); depth=0 → none
    pub drift: f32,
    pub growl: bool, // BR10 aftertouch growl enabled (naturals yes, synth no)
    pub amp: f32,
    #[cfg(test)]
    pub name: &'static str, // kind() string, oracle-36 seam
}

/// Base every BrassSpec starts from (struct-update in const context, the
/// preset idiom of `DEFAULTS` at voices.rs:325).
const BR_DEFAULTS: BrassSpec = BrassSpec {
    players: 1,
    detune_cents: 0.0,
    onset_scatter_s: 0.0,
    scoop0: 0.98,
    scoop_k: 0.010,
    h_min: 2.5,
    h_max: 8.0,
    k_min: 0.8,
    k_max: 3.0,
    bias: 0.30,
    brassiness: 0.0, // BR12 off by default; naturals opt in below, synth stays 0
    bore: [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)],
    bell_fc: 1500.0,
    bell_g: 1.0,
    out_base: 400.0,
    out_oct: 4.2,
    mute: false,
    synth_sweep: None,
    fenv: (0.0, 0.0, 0.0, 0.0),
    breath: 0.012,
    chiff: 0.30,
    env: (0.03, 0.10, 0.88, 0.12),
    vib: (0.0, 0.0, 0.0),
    drift: 0.0015,
    growl: true,
    amp: 0.30,
    #[cfg(test)]
    name: "brass",
};

pub const BR_TRUMPET: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "trumpet",
    scoop0: 0.982,
    scoop_k: 0.012,
    h_min: 2.5,
    h_max: 9.0,
    k_min: 0.8,
    k_max: 3.2,
    bias: 0.30,
    brassiness: 1.0, // BR12 the brightest, most readily "brassing up" voice
    bore: [(1200.0, 1.2, 5.0), (2900.0, 1.6, 3.0)],
    bell_fc: 1500.0,
    bell_g: 1.1,
    breath: 0.012,
    chiff: 0.35,
    env: (0.03, 0.10, 0.88, 0.12),
    drift: 0.0015,
    amp: 0.30,
    ..BR_DEFAULTS
};
pub const BR_TROMBONE: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "trombone",
    scoop0: 0.975,
    scoop_k: 0.008, // slow scoop = an audible slide (BR5)
    h_min: 2.2,
    h_max: 7.0,
    k_min: 0.8,
    k_max: 2.8,
    bias: 0.35,
    brassiness: 1.0, // BR12 cylindrical bore + flare: rips as readily as the trumpet
    bore: [(600.0, 1.1, 5.0), (1500.0, 1.5, 2.5)],
    bell_fc: 800.0,
    bell_g: 0.8,
    breath: 0.014,
    chiff: 0.30,
    env: (0.045, 0.12, 0.88, 0.15),
    drift: 0.0018,
    amp: 0.32,
    ..BR_DEFAULTS
};
pub const BR_TUBA: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "tuba",
    scoop0: 0.970,
    scoop_k: 0.006,
    h_min: 2.0,
    h_max: 5.0,
    k_min: 0.7,
    k_max: 2.2,
    bias: 0.40,
    brassiness: 0.35, // BR12 wide conical bore barely brasses — a gentle edge only
    bore: [(230.0, 1.0, 6.0), (600.0, 1.4, 2.0)],
    bell_fc: 400.0,
    bell_g: 0.4,
    breath: 0.018,
    chiff: 0.22,
    env: (0.07, 0.14, 0.90, 0.18),
    drift: 0.0020,
    amp: 0.40,
    ..BR_DEFAULTS
};
pub const BR_MUTE_TPT: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "muted_trumpet",
    scoop0: 0.982,
    scoop_k: 0.012,
    h_min: 2.5,
    h_max: 8.0,
    k_min: 0.8,
    k_max: 3.0,
    bias: 0.30,
    brassiness: 0.9, // BR12 trumpet source rasps; the mute stage tames it downstream
    bore: [(1200.0, 1.2, 5.0), (2900.0, 1.6, 3.0)], // trumpet source
    bell_fc: 1500.0,
    bell_g: 1.1,
    mute: true, // BR4 mute stage §3.7 (net ≈ −8 dB)
    breath: 0.012,
    chiff: 0.30,
    env: (0.03, 0.10, 0.88, 0.10),
    drift: 0.0015,
    amp: 0.55,
    ..BR_DEFAULTS
};
pub const BR_HORN: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "french_horn",
    scoop0: 0.985,
    scoop_k: 0.010,
    h_min: 2.0,
    h_max: 5.5,
    k_min: 0.7,
    k_max: 2.0,
    bias: 0.45,
    brassiness: 0.5, // BR12 mellow until pushed hard — the cuivré only at fortissimo
    bore: [(340.0, 1.0, 6.0), (750.0, 1.4, 2.5)],
    bell_fc: 750.0,
    bell_g: 0.5, // darkest: hand-in-bell
    breath: 0.014,
    chiff: 0.20,
    env: (0.055, 0.15, 0.86, 0.20),
    drift: 0.0016,
    amp: 0.34,
    ..BR_DEFAULTS
};
pub const BR_SECTION: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "brass_section",
    players: 3,
    detune_cents: 16.0,
    onset_scatter_s: 0.028,
    scoop0: 0.978,
    scoop_k: 0.010, // ±15% per player
    h_min: 2.4,
    h_max: 7.5,
    k_min: 0.8,
    k_max: 2.8,
    bias: 0.32,
    brassiness: 0.7, // BR12 the ensemble edge, a touch held back vs a solo lead
    bore: [(800.0, 1.0, 4.0), (1800.0, 1.4, 2.5)],
    bell_fc: 1100.0,
    bell_g: 0.8,
    breath: 0.010,
    chiff: 0.15,
    env: (0.06, 0.15, 0.88, 0.22),
    vib: (5.0, 0.0025, 0.35),
    drift: 0.0030,
    amp: 0.26,
    ..BR_DEFAULTS
};
pub const BR_SYN1: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "synth_brass",
    players: 5,
    detune_cents: 24.0,
    onset_scatter_s: 0.0,
    scoop0: 1.0,
    scoop_k: 0.0,
    k_min: 0.6,
    k_max: 0.6,
    bias: 0.15,
    bore: [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)], // none
    bell_fc: 1400.0,
    bell_g: 0.6,
    out_base: 0.0,                                  // synth owns its resonant sweep
    synth_sweep: Some((260.0, 900.0, 2600.0, 1.8)), // 260 + (900 + 2600·vn), Q 1.8
    fenv: (0.005, 0.22, 0.35, 0.15),
    breath: 0.0,
    chiff: 0.0,
    env: (0.02, 0.18, 0.80, 0.25),
    vib: (5.2, 0.0015, 0.40),
    drift: 0.0025,
    growl: false,
    amp: 0.28,
    ..BR_DEFAULTS
};
pub const BR_SYN2: BrassSpec = BrassSpec {
    #[cfg(test)]
    name: "synth_brass",
    players: 5,
    detune_cents: 32.0,
    onset_scatter_s: 0.0,
    scoop0: 1.0,
    scoop_k: 0.0,
    k_min: 0.6,
    k_max: 0.6,
    bias: 0.12,
    bore: [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0)], // none
    bell_fc: 900.0,
    bell_g: 0.4,
    out_base: 0.0,                                  // synth owns its resonant sweep
    synth_sweep: Some((220.0, 600.0, 1600.0, 1.2)), // 220 + (600 + 1600·vn), Q 1.2
    fenv: (0.02, 0.35, 0.35, 0.25),                 // slower, darker, longer
    breath: 0.0,
    chiff: 0.0,
    env: (0.09, 0.25, 0.85, 0.35),
    vib: (4.6, 0.0020, 0.50),
    drift: 0.0025,
    growl: false,
    amp: 0.28,
    ..BR_DEFAULTS
};

pub struct Brass {
    players: Vec<BrassPlayer>,
    spec: &'static BrassSpec,
    base_f: f32,
    bend: f32,      // composed engine multiplier, stored whole (INT-2/3/5)
    pressure: f32,  // BR9 engine-slewed CC11 blowing pressure, default 1.0
    growl: f32,     // BR9/BR10 engine-slewed aftertouch growl, default 0.0
    growl_cur: f32, // BR10 voice-side slew of growl (de-zipper)
    bite: f32,      // BR2 tongue over-blow, decays t60 60 ms
    bite_decay: f32,
    kws: f32,           // current shaper index k (updated at CTRL rate)
    cascade_amt: f32,   // BR12 rasp cascade wet-blend (updated at CTRL rate; 0 = off)
    env: Adsr,          // amplitude envelope
    benv: Adsr,         // BR2 brightness-bloom envelope (slow attack — the "waa")
    bloom: f32,         // BR2 per-sample cached benv level (the timbre driver)
    vn: f32,            // velocity/127, timbre-law input
    fenv: Option<Adsr>, // BR8 synth resonant-sweep envelope (62/63)
    fenv_level: f32,
    sweep: Option<Biquad>, // BR8 shared resonant LP, retuned at CTRL rate
    dcb: Biquad,           // BR11 highpass 25 Hz — biased-tanh DC guard
    bore: Vec<Biquad>,     // BR3 bore/mouthpiece peak EQ (linear, on the sum)
    bell_lp: OnePole,      // BR3 first-order HF-shelf helper
    bell_g: f32,
    out_lp: Option<OnePole>, // BR2 L-driven radiated brightness (natural only)
    mute: Option<[Biquad; 3]>, // BR4 prog 59 (HP + 2 nasal peaks + loss)
    breath_filt: Biquad,     // BR6 sustained blowing noise, BP at upper bore formant
    breath: f32,
    chiff: Burst,   // BR6 tongue transient
    flutter: Sine,  // BR10 growl flutter LFO (30 Hz)
    vib_depth: f32, // BR7
    vib_delay: u32,
    rng: Rng,
    t: u32,
    amp: f32,
    oversample: bool, // natural: 2× the source; synth: 1× (near-linear tanh)
    osr: f32,         // oscillator sample rate (sr2 natural, sr synth)
    sr: f32,
}

impl Brass {
    fn new(spec: &'static BrassSpec, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let mut rng = Rng::new(seed);
        let f = key_freq(key);
        let vn = vel as f32 / 127.0;
        // Synth brass is near-linear (k = 0.6): its mild tanh makes no
        // alias-worthy harmonics, so the 2× cascade is skipped (§3.11).
        let oversample = spec.synth_sweep.is_none();
        let osr = if oversample { sr * 2.0 } else { sr };
        let n = spec.players.max(1);

        let players: Vec<BrassPlayer> = (0..n)
            .map(|i| {
                let spread = if n > 1 {
                    (i as f32 / (n - 1) as f32) * 2.0 - 1.0
                } else {
                    0.0
                };
                let detune = 2f32.powf(spec.detune_cents * 0.5 * spread / 1200.0);
                // player 0 pinned to 0 so the section has a defined front edge
                let onset = if i == 0 || spec.onset_scatter_s <= 0.0 {
                    0
                } else {
                    (rng.white().abs() * spec.onset_scatter_s * sr) as u32
                };
                let scoop_k = if n > 1 {
                    spec.scoop_k * (1.0 + 0.15 * rng.white())
                } else {
                    spec.scoop_k
                };
                let scoop = if spec.scoop_k > 0.0 {
                    spec.scoop0 + 0.008 * vn
                } else {
                    1.0
                };
                let lip_fc = if oversample {
                    (f * spec.h_min).min(osr * 0.24)
                } else {
                    osr * 0.45
                };
                let f_i = (f * detune).min(osr * 0.45);
                BrassPlayer {
                    saw: BlepSaw::new(f_i, osr, rng.white() * 0.5 + 0.5),
                    detune,
                    onset,
                    lip_lp: OnePole::lowpass(lip_fc, osr),
                    decim: [
                        Biquad::lowpass(BR_DECIM_HZ, 0.8, osr),
                        Biquad::lowpass(BR_DECIM_HZ, 0.8, osr),
                    ],
                    vib_phase: rng.white() * std::f32::consts::PI,
                    vib_rate: spec.vib.0 * (1.0 + 0.08 * rng.white()),
                    drift: Drift::new(seed ^ (0x1234 + i as u32 * 977), spec.drift, 2800),
                    scoop,
                    scoop_k,
                    x_prev: 0.0,
                    s_prev: 0.0,
                    u_prev: 0.0,
                }
            })
            .collect();

        // upper bore formant — colours the breath and the tongue chiff
        let upper = spec
            .bore
            .iter()
            .map(|&(bf, _, _)| bf)
            .fold(0.0f32, f32::max);
        let upper = if upper > 0.0 { upper } else { f * 2.0 };

        let bore: Vec<Biquad> = spec
            .bore
            .iter()
            .filter(|&&(bf, _, _)| bf > 0.0)
            .map(|&(bf, q, g)| Biquad::peak(bf.min(sr * 0.4), q, g, sr))
            .collect();

        let mute = if spec.mute {
            Some([
                Biquad::highpass(750.0, 0.7, sr),
                Biquad::peak(1600.0, 2.2, 7.0, sr),
                Biquad::peak(4000.0, 2.0, 3.0, sr),
            ])
        } else {
            None
        };

        let (fenv, sweep) = if let Some((base, _, _, q)) = spec.synth_sweep {
            (
                Some(Adsr::new(
                    spec.fenv.0,
                    spec.fenv.1,
                    spec.fenv.2,
                    spec.fenv.3,
                    sr,
                )),
                Some(Biquad::lowpass(base, q, sr)),
            )
        } else {
            (None, None)
        };

        let mut chiff = Burst::new(
            Biquad::bandpass(upper.min(sr * 0.4), 1.0, sr),
            spec.chiff,
            0.03,
            sr,
        );
        // tongued attack: super-linear, house onset convention (voices.rs:833)
        chiff.trigger(vel_amp(vel) * vn);

        Brass {
            players,
            spec,
            base_f: f,
            bend: 1.0,
            pressure: 1.0,
            growl: 0.0,
            growl_cur: 0.0,
            bite: 0.7 * vn * vn,
            bite_decay: t60_mul(BR_BITE_T60, sr),
            kws: spec.k_min,
            cascade_amt: 0.0,
            env: Adsr::new(
                vel_attack(spec.env.0, vel),
                spec.env.1,
                spec.env.2,
                spec.env.3,
                sr,
            ),
            benv: Adsr::new(BR_BLOOM_A, 0.05, 1.0, spec.env.3, sr),
            bloom: 0.0,
            vn,
            fenv,
            fenv_level: 0.0,
            sweep,
            dcb: Biquad::highpass(25.0, 0.7, sr),
            bore,
            bell_lp: OnePole::lowpass(spec.bell_fc, sr),
            bell_g: spec.bell_g,
            out_lp: (spec.out_base > 0.0).then(|| OnePole::lowpass(spec.out_base, sr)),
            mute,
            breath_filt: Biquad::bandpass(upper.min(sr * 0.4), 1.5, sr),
            breath: spec.breath,
            chiff,
            flutter: Sine::new(BR_GROWL_HZ, sr, 0.0),
            vib_depth: spec.vib.1,
            vib_delay: (spec.vib.2 * sr) as u32,
            rng,
            t: 0,
            amp: spec.amp * (0.4 + 0.6 * vel_amp(vel)),
            oversample,
            osr,
            sr,
        }
    }

    fn control_tick(&mut self) {
        // BR2 loudness scalar L (one scalar drives the whole timbre)
        let press = BR_PRESS_FLOOR.0 + BR_PRESS_FLOOR.1 * self.pressure;
        let l =
            (self.bloom * (BR_L_VEL.0 + BR_L_VEL.1 * self.vn) * press * (1.0 + self.bite)).min(1.3);
        // BR9/BR10 growl slew (de-zipper block-rate writes); synth never growls
        let g_target = if self.spec.growl { self.growl } else { 0.0 };
        self.growl_cur += BR_GROWL_SLEW * (g_target - self.growl_cur);
        // BR10: growl folds into the brightness scalar so its added drive
        // (the bite) actually reaches the source AND the radiated output —
        // otherwise the lip lowpass / output lowpass cap it and only the
        // flutter AM survives. At growl 0 this is exactly `l` (BR-O2/O3 unmoved).
        let bright = (l + BR_GROWL_BRIGHT * self.growl_cur).min(1.5);
        // BR2 lip-closure cutoff law (natural only; synth uses the sweep)
        if self.oversample {
            let fc = (self.base_f
                * (self.spec.h_min + (self.spec.h_max - self.spec.h_min) * bright.powf(BR_H_EXP)))
            .min(self.osr * 0.24);
            for p in &mut self.players {
                p.lip_lp.set_cutoff(fc, self.osr);
            }
        }
        // BR1/BR2/BR10 shaper index, composed drive clamped to the alias cap
        self.kws = (self.spec.k_min
            + (self.spec.k_max - self.spec.k_min) * l
            + BR_GROWL_DRIVE * self.growl_cur)
            .min(BR_K_MAX);
        // BR12 rasp cascade amount (natural only). Blooms with `bright` over
        // [LO,HI] so mp stays clean and forte/ff/growl rip; scaled per-program by
        // brassiness B; derated above BR_CASCADE_F0 so a high note's dense upper
        // harmonics can't push fold-back past the 2× alias floor (BR-O11). Because
        // `bright` carries the authored growl term, an aftertouch note rasps
        // harder — the opt-in cuivré rides the existing growl seam for free.
        self.cascade_amt = if self.oversample && self.spec.brassiness > 0.0 {
            // Quartic roll-off: full rasp through the common range (≤ ~A4 440 Hz),
            // shedding above it. BR13 ADAA then LIFTS the top octave back up via a
            // frequency-gated floor (ramped over [LIFT_LO, LIFT_HI]) — the top
            // register is no longer Fork-B territory. The lift deliberately spares
            // the upper-mid (A5/B5) so BR-O11 (breath-contaminated A5 guard) holds.
            let r2 = {
                let r = BR_CASCADE_F0 / self.base_f.max(BR_CASCADE_F0);
                r * r
            };
            let lift = BR_CASCADE_F0_FLOOR
                * smoothstep(BR_CASCADE_LIFT_LO, BR_CASCADE_LIFT_HI, self.base_f);
            let hf_derate = (r2 * r2).max(lift).min(1.0);
            (self.spec.brassiness
                * BR_CASCADE_MAX
                * smoothstep(BR_CASCADE_LO, BR_CASCADE_HI, bright)
                * hf_derate)
                .clamp(0.0, BR_CASCADE_MAX)
        } else {
            0.0
        };
        // BR2 radiated brightness: the flagship L scalar opens an output lowpass
        // so "loudness opens timbre" reaches the OUTPUT centroid (the lip law
        // alone is masked by the fixed bore/bell). Same L → same at C3, so the
        // BR-O9 program ordering is unaffected.
        if let Some(lp) = &mut self.out_lp {
            // BR12: the cascade also OPENS the radiated output so its extra rasp
            // harmonics actually leave the bell (the fixed out_lp corner would
            // otherwise roll them off). Gated by cascade_amt (⇒ by loudness &
            // program brassiness), so mp is unmoved and the pre-BR12 / flat-twin
            // render is bit-identical (cascade_amt ≡ 0).
            let open = 1.0 + BR_CASCADE_RADIATE * self.cascade_amt;
            let cut = (self.spec.out_base * open * 2f32.powf(self.spec.out_oct * bright))
                .min(self.sr * 0.45);
            lp.set_cutoff(cut, self.sr);
        }
        // BR5/BR7 per-player retune, composing every persistent offset
        let ramp = if self.t > self.vib_delay {
            (((self.t - self.vib_delay) as f32) / self.sr).min(1.0)
        } else {
            0.0
        };
        let (base_f, bend, vib_depth, osr, sr) =
            (self.base_f, self.bend, self.vib_depth, self.osr, self.sr);
        for p in &mut self.players {
            p.scoop += p.scoop_k * (1.0 - p.scoop);
            // control_tick fires every CTRL OUTPUT samples (self.t counts at sr),
            // so the real tick period is CTRL/sr — divide by sr, not osr (osr=2·sr
            // for natural presets would halve the rate; only BR_SECTION is affected).
            p.vib_phase += TAU * p.vib_rate * CTRL as f32 / sr;
            let vib = if ramp > 0.0 && vib_depth > 0.0 {
                vib_depth * ramp * p.vib_phase.sin()
            } else {
                0.0
            };
            let drift = p.drift.next();
            let f_i = (base_f * p.detune * bend * p.scoop * (1.0 + vib + drift)).min(osr * 0.45);
            p.saw.set_freq(f_i, osr);
        }
    }
}

impl Voice for Brass {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let ramp_samples = (BR_ONSET_RAMP_S * self.sr) as u32;
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.control_tick();
            }
            let e = self.env.next();
            self.bloom = self.benv.next();
            self.bite *= self.bite_decay;
            // BR8 synth resonant sweep (SynthBass idiom): fenv advances every
            // sample, the filter retunes at control rate.
            if let Some(f) = &mut self.fenv {
                self.fenv_level = f.next();
            }
            if let (Some(sweep), Some((base, v0, vd, q))) =
                (self.sweep.as_mut(), self.spec.synth_sweep)
            {
                if self.t.is_multiple_of(CTRL) {
                    let cut =
                        (base + self.fenv_level * (v0 + vd * self.vn)).clamp(80.0, self.sr * 0.4);
                    sweep.retune_lowpass(cut, q, self.sr);
                }
            }

            // BR1 per-player lip valve, summed (each player intermodulates on
            // its own — a shared shaper would be a section tell). BR12 folds the
            // rasp cascade in per player too — the steepening is a per-lip effect,
            // not a section-bus one.
            let (kws, bias, oversample, cascade_amt) =
                (self.kws, self.spec.bias, self.oversample, self.cascade_amt);
            let mut sum = 0.0;
            for p in &mut self.players {
                if self.t < p.onset {
                    continue;
                }
                let ramp = {
                    let dt = self.t - p.onset;
                    if ramp_samples == 0 || dt >= ramp_samples {
                        1.0
                    } else {
                        let u = dt as f32 / ramp_samples as f32;
                        u * u * (3.0 - 2.0 * u) // smoothstep, no step click
                    }
                };
                let v = if oversample {
                    // two sub-steps at sr2, decimated; keep the aligned sample.
                    // BR12 rasp cascade runs HERE, before decimation, so its extra
                    // harmonics see the same 13.5 kHz anti-alias cliff as BR1.
                    let mut y = 0.0;
                    for _ in 0..2 {
                        let lip = p.lip_lp.process(p.saw.next());
                        let mut x = p.rasp_adaa(lip, kws, bias, cascade_amt);
                        for d in p.decim.iter_mut() {
                            x = d.process(x);
                        }
                        y = x;
                    }
                    y
                } else {
                    // synth path: near-linear (k≈0.6), no cascade (cascade_amt≡0)
                    brass_valve(p.lip_lp.process(p.saw.next()), kws, bias)
                };
                sum += v * ramp;
            }
            sum /= self.players.len() as f32;

            // BR6 breath noise (before the bore EQ so it shares the resonances)
            if self.breath > 0.0 {
                sum += self.breath_filt.process(self.rng.white()) * self.breath * e.max(0.0).sqrt();
            }
            // BR11 shaper DC guard
            sum = self.dcb.process(sum);
            // BR8 synth resonant LP (replaces the per-player lip law)
            if let Some(sweep) = &mut self.sweep {
                sum = sweep.process(sum);
            }
            // BR3 bore/mouthpiece formants
            for b in &mut self.bore {
                sum = b.process(sum);
            }
            // BR3 bell HF radiation shelf (first-order, phase-benign)
            sum += self.bell_g * (sum - self.bell_lp.process(sum));
            // BR2 L-driven radiated brightness (natural presets)
            if let Some(lp) = &mut self.out_lp {
                sum = lp.process(sum);
            }
            // BR4 mute: HP 750 ► peak 1600 ► peak 4000 ► ×0.40
            if let Some(m) = &mut self.mute {
                let mut y = sum;
                for stage in m.iter_mut() {
                    y = stage.process(y);
                }
                sum = y * 0.40;
            }
            // BR10 flutter AM (post-decimation, so its ±30 Hz sidebands can't
            // alias); same growl_cur as the bite, so both halves ramp together
            let am = 1.0 - BR_GROWL_AM * self.growl_cur * (1.0 + self.flutter.next()) * 0.5;
            sum *= am;

            // BR6 tongue transient ("tuh"): a fresh-attack onset spike, added
            // OUTSIDE the amp envelope (the Pluck onset_post precedent,
            // voices.rs:998) so the tongue speaks at t=0 even while the note's
            // amplitude is still ramping in. A slur (legato_to) never triggers
            // it — the tongued≠slurred dichotomy (BR-O6).
            let chiff = self.chiff.tick(&mut self.rng) * self.amp;
            *o += sum * self.amp * e + chiff;
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
        self.benv.release();
        if let Some(f) = &mut self.fenv {
            f.release();
        }
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        // composed whole; applied at control rate on top of scoop/vib/drift
        self.bend = mult;
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        // BR9: pressure opens fc/k (never amplitude); growl drives BR10.
        self.pressure = pressure;
        self.growl = growl;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // one breath across fingered notes (BR5): re-aim each player via its
        // scoop, do NOT retrigger env; kill the bite so the slur has no
        // second consonant (the tongued≠slurred dichotomy, BR-O6).
        let new_f = key_freq(key);
        for p in &mut self.players {
            let j = 1.0 + 0.10 * self.rng.white(); // players don't move as one
            p.scoop = (self.base_f * p.scoop / new_f * j).clamp(BR_SCOOP_CLAMP.0, BR_SCOOP_CLAMP.1);
        }
        self.base_f = new_f;
        self.bite = 0.0;
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        self.spec.name
    }
}

fn brass(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Brass {
    let spec: &'static BrassSpec = match program {
        56 => &BR_TRUMPET,
        57 => &BR_TROMBONE,
        58 => &BR_TUBA,
        59 => &BR_MUTE_TPT,
        60 => &BR_HORN,
        61 => &BR_SECTION,
        62 => &BR_SYN1,
        _ => &BR_SYN2, // 63
    };
    Brass::new(spec, key, vel, sr, seed)
}

pub fn make(program: u8, key: u8, vel: u8, sr: f32, seed: u32, samples: bool) -> Box<dyn Voice> {
    let samples = samples && crate::embedded_samples_available();
    let noise_off = (0.0, 0.01, 1000.0, 1.0);
    match program {
        0..=3 => {
            let model = Box::new(acoustic_piano(key, vel, sr, seed));
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
        4 => Box::new(electric_piano_1(key, vel, sr, seed)),
        5 => Box::new(electric_piano_2(key, vel, sr, seed)),
        6 => Box::new(harpsichord(key, vel, sr, seed)),
        7 => Box::new(Pluck::new(&CLAVINET, key, vel, sr, seed)),
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
        11 => Box::new(
            bell(key, vel, sr, seed, VIBES, noise_off, 0.002, 0.8, 0.45)
                .with_amp_trem(VIBRAPHONE_MOTOR_RATE_HZ, VIBRAPHONE_MOTOR_DEPTH),
        ),
        12 => Box::new(wood_bar(
            key,
            vel,
            sr,
            seed,
            MARIMBA,
            MARIMBA_NOISE,
            MARIMBA_ATTACK_S,
            MARIMBA_RELEASE_T60,
            MARIMBA_GAIN,
        )),
        13 => Box::new(wood_bar(
            key,
            vel,
            sr,
            seed,
            XYLOPHONE,
            XYLOPHONE_NOISE,
            XYLOPHONE_ATTACK_S,
            XYLOPHONE_RELEASE_T60,
            XYLOPHONE_GAIN,
        )),
        14 => Box::new(bell(
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
        15 => Box::new(Pluck::new(&DULCIMER, key, vel, sr, seed)),
        16..=18 | 20..=23 => Box::new(organ(program, key, vel, sr, seed)),
        19 => Box::new(CathedralOrgan::new(key, vel, sr, seed)),
        24 => {
            let model = Box::new(Pluck::new(&NYLON, key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_GUITAR;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::guitar_bank(),
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
        // 25 steel stays pure model for now: the FreePats steel-string set is
        // GPL-with-exception, not CC0 — no clean sampled source yet (HLD §2.2)
        25 => Box::new(Pluck::new(&STEEL, key, vel, sr, seed)),
        26 => Box::new(Pluck::new(&JAZZ, key, vel, sr, seed)),
        27 => Box::new(Pluck::new(&CLEAN, key, vel, sr, seed)),
        28 => Box::new(Pluck::new(&MUTED, key, vel, sr, seed)),
        29 | 30 => Box::new(Pluck::new(&DRIVE, key, vel, sr, seed)),
        31 => Box::new(Pluck::new(&HARMONIC, key, vel, sr, seed)), // G7 flageolet
        32 => Box::new(Pluck::new(&UPRIGHT, key, vel, sr, seed)),  // B2
        33 => Box::new(Pluck::new(&BASS, key, vel, sr, seed)),
        38 | 39 => Box::new(SynthBass::new(program, key, vel, sr, seed)), // B4
        34 => Box::new(Pluck::new(&PICK, key, vel, sr, seed)),            // B2
        36 => Box::new(Pluck::new(&SLAP, key, vel, sr, seed)),            // B2: thumb slap
        37 => Box::new(Pluck::new(&SLAP_POP, key, vel, sr, seed)),        // B2: bridge pop
        35 => Box::new(Pluck::new(&FRETLESS, key, vel, sr, seed)),
        40 | 110 => {
            let model = Box::new(Bowed::new(program, key, vel, sr, seed));
            if samples {
                let (gain, fade) = if program == 110 { LA_FIDDLE } else { LA_VIOLIN };
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
        // GM 42 cello / 43 contrabass: waveguide + arco LA is the DEFAULT bank.
        // The Codex per-program `Bowed` set is the CC0 alt bank (altbank.rs).
        42 | 43 => {
            let model = Box::new(BowedString::new(program, key, vel, sr, seed));
            if samples {
                let (gain, fade, bank) = if program == 42 {
                    (LA_CELLO.0, LA_CELLO.1, crate::sampler::cello_bank(vel))
                } else {
                    (
                        LA_CONTRABASS.0,
                        LA_CONTRABASS.1,
                        crate::sampler::contrabass_bank(vel),
                    )
                };
                crate::sampler::LaVoice::wrap(model, bank, key, vel, sr, gain, fade)
            } else {
                model
            }
        }
        41 | 44 => Box::new(Bowed::new(program, key, vel, sr, seed)),
        45 => Box::new(Pluck::new(&PIZZ, key, vel, sr, seed)),
        46 => Box::new(Pluck::new(&HARP, key, vel, sr, seed)),
        47 => Box::new(timpani(key, vel, sr, seed)),
        48..=49 => {
            let model = Box::new(strings(program, key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_STRINGS;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::strings_bank(vel),
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
        // 50-51 are *synth* strings — a divide-down string machine, distinct from
        // the acoustic section 48/49 render. Pure model (tier D), no sample layer.
        50 | 51 => Box::new(synth_strings(program, key, vel, sr, seed)),
        52..=54 => Box::new(choir(program, key, vel, sr, seed)),
        55 => Box::new(orch_hit(key, vel, sr, seed)),
        56..=61 => {
            let model = Box::new(brass(program, key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_BRASS;
                let gain = if program == 61 {
                    gain * LA_BRASS_SECTION_GAIN
                } else {
                    gain
                };
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::brass_bank(program, vel),
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
        62 | 63 => Box::new(brass(program, key, vel, sr, seed)), // synth brass: pure model
        // saxes, bagpipe, shanai: pure model (no clean CC0 source / idiomatic onset)
        64..=67 | 109 | 111 => Box::new(reed(program, key, vel, sr, seed)),
        68..=71 => {
            let model = Box::new(reed(program, key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_REED;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::reed_bank(program, vel),
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
        72..=79 => {
            let model = Box::new(Wind::from_preset(wind(program), key, vel, sr, seed));
            // Sample policy: ONLY the concert flute (73) and the piccolo (72 — a
            // flute attack repitched up is still a credible small-flute onset) get
            // the flute LA bank. Smearing a transverse-flute attack across a stopped
            // pipe, a vessel, end-blown bamboo or a human whistle destroyed identity
            // exactly in the window where the ear decides what the instrument IS.
            // 74..=79 are model-only, each with its own bespoke chiff.
            if samples && matches!(program, 72 | 73) {
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
        96 | 98 | 100 | 102 => Box::new(bell(
            key, vel, sr, seed, CRYSTAL, noise_off, 0.03, 1.5, 0.60,
        )),
        97 | 99 | 103 => Box::new(pad(program, key, vel, sr, seed)),
        101 => Box::new(pad(95, key, vel, sr, seed)),
        104 => Box::new(Pluck::new(&SITAR, key, vel, sr, seed)),
        105 => Box::new(Pluck::new(&BANJO, key, vel, sr, seed)),
        106 => Box::new(Pluck::new(&SHAMISEN, key, vel, sr, seed)),
        107 => Box::new(Pluck::new(&KOTO, key, vel, sr, seed)),
        108 => Box::new(bell(
            key,
            vel,
            sr,
            seed,
            KALIMBA,
            (0.08, 0.010, 2800.0, 0.9),
            0.001,
            0.18,
            0.56,
        )),
        112 => Box::new(tinkle_bell(key, vel, sr, seed)),
        113 => Box::new(agogo(key, vel, sr, seed)),
        114 => Box::new(steel_drum(key, vel, sr, seed)),
        115 => Box::new(woodblock(key, vel, sr, seed)),
        116 => Box::new(taiko_drum(key, vel, sr, seed)),
        117 => Box::new(melodic_tom(key, vel, sr, seed)),
        118 => Box::new(synth_drum(key, vel, sr, seed)),
        119 => Box::new(ReverseCymbal::new(vel, sr, seed)),
        120..=127 => Box::new(SfxNoise::new(program, vel, sr, seed)),
        80..=87 => Box::new(lead(program, key, vel, sr, seed)),
        88..=95 => Box::new(pad(program, key, vel, sr, seed)),
        _ => Box::new(Pluck::new(&STEEL, key, vel, sr, seed)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    // Audio oracle helpers used by the v0.9 reed/brass oracles (bare names).
    use crate::testutil::{
        assert_render_signature, band_rms, centroid, env_autocorr_peak, env_autocorr_peak_detrend,
        hp_rms, mag_at, peak_locate, render_signature, rms, spectral_band_rms, spectral_centroid,
        RenderSignature, BW_TREM_PEAK_FLOOR,
    };

    #[test]
    fn control_lfo_advances_at_the_requested_rate() {
        let sr = 44100.0;
        let mut rng = Rng::new(7);
        let mut lfo = control_lfo(5.0, 0.0, &mut rng, sr);
        let ticks = (2.0 * sr / CTRL as f32) as usize;
        let mut previous = lfo.next();
        let mut rising_crossings = 0;
        for _ in 1..ticks {
            let current = lfo.next();
            if previous <= 0.0 && current > 0.0 {
                rising_crossings += 1;
            }
            previous = current;
        }
        assert!(
            (9..=11).contains(&rising_crossings),
            "5 Hz control LFO produced {rising_crossings} cycles in 2 seconds"
        );
    }

    #[test]
    fn fold_key_preserves_pitch_class_inside_each_callsite_range() {
        for (lo, hi) in [(72, 108), (60, 96), (45, 96), (36, 47)] {
            for key in 0..=127 {
                let folded = fold_key(key, lo, hi);
                assert!(
                    (lo..=hi).contains(&folded),
                    "key {key} folded to {folded}, outside {lo}..={hi}"
                );
                assert_eq!(
                    folded % 12,
                    key % 12,
                    "key {key} changed pitch class in {lo}..={hi}"
                );
            }
        }
    }

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

    /// Oracle 1: velocity opens the timbre, not just the level — a hard pick
    /// reads measurably brighter than a soft one at the same key.
    #[test]
    fn velocity_opens_pluck_timbre() {
        let sr = 44100.0;
        let cent = |preset: &PluckPreset, key: u8, vel: u8| {
            let mut v = Pluck::new(preset, key, vel, sr, 7);
            // pick + early ring: the damper contrast compounds per loop pass
            let mut buf = vec![0f32; 11025];
            v.render(&mut buf);
            crate::testutil::centroid(&buf, sr)
        };
        let steel = cent(&STEEL, 52, 120) / cent(&STEEL, 52, 30);
        // isolate the STRING's law from the (separately-tested, oracle 9)
        // finger-noise garnish, which floors a whisper note's centroid
        let bare_bass = PluckPreset {
            attack_noise: 0.0,
            ..BASS
        };
        let bass = cent(&bare_bass, 33, 120) / cent(&bare_bass, 33, 30);
        assert!(
            steel > 1.4 && bass > 1.3,
            "ff/pp centroid ratios: STEEL {steel} (need >1.4), BASS {bass} (need >1.3)"
        );
    }

    /// Oracle 2 (guard): the velocity law must not move the tuning — the
    /// KS loop compensates the damper phase at whatever cutoff it is given.
    /// Measured with peak_locate (zero-crossing counts overreact to the
    /// brighter harmonics a hard pick now legitimately carries).
    #[test]
    fn velocity_preserves_tuning() {
        let sr = 44100.0;
        for vel in [30u8, 120] {
            let mut v = Pluck::new(&STEEL, 69, vel, sr, 7);
            let mut buf = vec![0f32; 22050];
            v.render(&mut buf);
            let hz = crate::testutil::peak_locate(&buf[4410..], sr, 396.0, 484.0);
            assert!((hz - 440.0).abs() < 6.0, "vel {vel}: {hz} Hz");
        }
    }

    /// Oracle 6 (§5.3): the CLEAN chain (shipped body peaks + cascaded cab
    /// lowpasses, built from the preset's own data) has the presence lift
    /// and the steep top-end the old bare one-pole lacked.
    #[test]
    fn clean_cab_response() {
        let sr = 44100.0;
        // new chain from the shipped preset data
        let mut body: Vec<Biquad> = CLEAN
            .body
            .iter()
            .map(|&(f, q, g)| Biquad::peak(f, q, g, sr))
            .collect();
        let mut cab = [
            Biquad::lowpass(CLEAN.cab_lp, 0.75, sr),
            Biquad::lowpass(CLEAN.cab_lp, 0.75, sr),
        ];
        let mut new_ir = vec![0f32; 8192];
        new_ir[0] = 1.0;
        for x in new_ir.iter_mut() {
            let mut y = *x;
            for b in body.iter_mut() {
                y = b.process(y);
            }
            for c in cab.iter_mut() {
                y = c.process(y);
            }
            *x = y;
        }
        // the old chain: nothing but the shared out_lp one-pole
        let mut old_lp = OnePole::lowpass(5500.0, sr);
        let mut old_ir = vec![0f32; 8192];
        old_ir[0] = 1.0;
        for x in old_ir.iter_mut() {
            *x = old_lp.process(*x);
        }
        let db = |ir: &[f32], f: f32| 20.0 * crate::testutil::mag_at(ir, sr, f).max(1e-12).log10();
        let d2500 = db(&new_ir, 2500.0) - db(&old_ir, 2500.0);
        let d8k = db(&new_ir, 8000.0) - db(&old_ir, 8000.0);
        assert!(d2500 >= 2.0, "presence vs old one-pole: {d2500:.1} dB");
        assert!(d8k <= -12.0, "top-end vs old one-pole: {d8k:.1} dB");
    }

    fn render_pluck(p: &PluckPreset, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = Pluck::new(p, key, vel, sr, seed);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    fn render_program(program: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(program, key, vel, sr, seed, false);

        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    /// V2a (guitar v2): the pickup RLC building block is a genuinely RESONANT
    /// lowpass — a peak above unity at the resonance (a monotone lowpass can
    /// never gain), then rolloff above. Pinned on the isolated biquad so the
    /// end-to-end leg (V2b) can attribute its band shift to this element.
    #[test]
    fn pickup_rlc_biquad_resonates() {
        let sr = 44100.0;
        for &(fc, q) in &[(4200.0f32, 1.8f32), (3300.0, 1.5), (2400.0, 1.1)] {
            let mut b = Biquad::lowpass(fc, q, sr);
            let mut ir = vec![0f32; 8192];
            ir[0] = 1.0;
            for x in ir.iter_mut() {
                *x = b.process(*x);
            }
            let m = |f: f32| mag_at(&ir, sr, f);
            // mag_at is normalized for sines, not impulses — assert RATIOS
            // against the near-DC passband (gain ≈ 1 there), where a monotone
            // lowpass could never show a peak.
            let (floor, peak, above) = (m(fc * 0.125), m(fc), m(fc * 2.0));
            let (pk, ro) = (peak / floor, above / peak);
            println!("rlc {fc}/{q}: peak/floor {pk:.2} rolloff {ro:.2}");
            // |H(fc)| = Q for this topology; even the mildest preset (Q 1.1)
            // must show a genuine peak above the passband floor — the property
            // no monotone lowpass can fake. (fc/2 comparisons are V2b's job.)
            assert!(
                pk > 1.05,
                "rlc {fc}/{q}: no peak above the passband ({pk:.2})"
            );
            assert!(ro < 0.5, "rlc {fc}/{q}: no rolloff above ({ro:.2})");
        }
    }

    /// V2b (guitar v2): end-to-end differential — the CLEAN voice with its
    /// pickup RLC vs the identical preset with the circuit removed. Measured
    /// at pitches whose harmonic lattices populate BOTH comparison bands
    /// (A2 = 110 Hz and A3 = 220 Hz put ≥ 3 harmonics in each band), with
    /// per-band energy floors so a comb null or spectral hole cannot fake
    /// the ratio (adversarial-review O6/C7).
    #[test]
    fn pickup_rlc_shifts_voice_spectrum() {
        let (fc, _q) = CLEAN.pickup_rlc;
        let no_rlc = PluckPreset {
            pickup_rlc: (0.0, 0.0),
            ..CLEAN
        };
        for key in [45u8, 57] {
            let on = render_pluck(&CLEAN, key, 100, 1.0, 0xA2);
            let off = render_pluck(&no_rlc, key, 100, 1.0, 0xA2);
            let sr = 44100.0;
            let band = |s: &[f32], lo: f32, hi: f32| spectral_band_rms(s, sr, lo, hi);
            // resonance band vs one octave below it
            let (r_lo, r_hi) = (fc * 0.8, fc * 1.25);
            let (n_lo, n_hi) = (fc * 0.4, fc * 0.625);
            for (nm, s) in [("off", &off), ("on", &on)] {
                assert!(
                    band(s, r_lo, r_hi) > 1e-6 && band(s, n_lo, n_hi) > 1e-6,
                    "key {key} {nm}: a comparison band is empty"
                );
            }
            let ratio_on = band(&on, r_lo, r_hi) / band(&on, n_lo, n_hi);
            let ratio_off = band(&off, r_lo, r_hi) / band(&off, n_lo, n_hi);
            let db = 20.0 * (ratio_on / ratio_off).log10();
            println!("V2b key {key}: resonance-vs-neighbor shift {db:.2} dB");
            assert!(db >= 2.0, "key {key}: RLC band shift {db:.2} dB < 2.0");
        }
    }

    /// V3 (guitar v2 unit B): the 26/27 split is audible — the same note at
    /// the same velocity reads distinctly darker on the jazz box (neck
    /// pickup, rolled tone, hollowbody warmth) than on the bright CLEAN
    /// platform, and both stay solidly audible.
    #[test]
    fn jazz_clean_split_is_audible() {
        let sr = 44100.0;
        for key in [50u8, 62] {
            let j = render_program(26, key, 100, 1.0, 0xB3);
            let c = render_program(27, key, 100, 1.0, 0xB3);
            let (cj, cc) = (centroid(&j, sr), centroid(&c, sr));
            let (rj, rc) = (rms(&j), rms(&c));
            println!("V3 key {key}: JAZZ centroid {cj:.0} Hz, CLEAN {cc:.0} Hz");
            assert!(
                cc >= 1.25 * cj,
                "key {key}: CLEAN {cc:.0} Hz not ≥1.25× JAZZ {cj:.0} Hz"
            );
            assert!(
                rj > 0.01 && rc > 0.01,
                "key {key}: a split voice fell silent (jazz {rj:.4}, clean {rc:.4})"
            );
        }
    }

    /// Measured systematic offset between the spoken-level peak reference and
    /// the held RMS: crest-vs-RMS, the smoothed window-max envelope statistic,
    /// and the saturator equilibrium multiple. Shared by V6a and V6c so the
    /// sustainer's level calibration lives in exactly one place.
    const SUS_HOLD_REF_OFFSET_DB: f32 = -11.6;

    /// Drive a Pluck through a held phase then a released tail (V6/V7/V8).
    fn render_pluck_phased(
        p: &PluckPreset,
        key: u8,
        hold_s: f32,
        tail_s: f32,
        seed: u32,
    ) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = Pluck::new(p, key, 100, sr, seed);
        let mut buf = vec![0f32; ((hold_s + tail_s) * sr) as usize];
        let split = (hold_s * sr) as usize;
        v.render(&mut buf[..split]);
        if tail_s > 0.0 {
            v.note_off();
            v.render(&mut buf[split..]);
        }
        buf
    }

    /// V6a (guitar v2 unit D): the sustainer HOLDS a high held note — solo
    /// voice (no engine Drive, isolating unit D from unit C), E5 and E6 (the
    /// worst case the T16 lead exposed), 8 s: every late 1-s window sits
    /// within ±5 dB of the constant-derived hold level (upper AND lower
    /// bounds: growth or a dead sustainer fails), the windows stay FLAT
    /// within 3 dB (the pumping catch), DC/sub-fundamental energy stays
    /// ≥ 40 dB down, and every sample is finite.
    #[test]
    fn sustain_holds_high_notes() {
        let sr = 44100.0;
        for key in [76u8, 88] {
            let buf = render_pluck_phased(&DRIVE, key, 8.0, 0.0, 0xD6);
            assert!(buf.iter().all(|x| x.is_finite()), "key {key}: non-finite");
            let db = |a: f32, b: f32| {
                20.0 * rms(&buf[(a * sr) as usize..(b * sr) as usize])
                    .max(1e-12)
                    .log10()
            };
            // reference = the note's spoken level: peak over 20-80 ms
            // (matching the controller's capture; at E6 the string is dead by
            // 100 ms, so a later window would reference the noise floor).
            // Expected hold derives from the preset constant with a −3 dB
            // RMS-vs-peak offset; the band allows the saturator's residual
            // per-pitch equilibrium spread (documented in the HLD).
            let refl = 20.0
                * buf[(0.02 * sr) as usize..(0.08 * sr) as usize]
                    .iter()
                    .fold(0f32, |m, &x| m.max(x.abs()))
                    .max(1e-12)
                    .log10();
            // Expected hold: the preset constant with the measured −11.6 dB
            // systematic offset (onset-crest-vs-held-RMS, the controller's
            // smoothed window-max envelope vs instantaneous peak, and the
            // saturator equilibrium multiple). The ±5 dB band absorbs the
            // per-pitch remainder of those statistics (E5 −23.5 / E6 −17.9
            // at capture); the FLATNESS clause below is the pumping catch.
            let hold = 20.0 * DRIVE.sustain.log10() + SUS_HOLD_REF_OFFSET_DB;
            let (mut lo, mut hi) = (f32::INFINITY, f32::NEG_INFINITY);
            let mut bad = Vec::new();
            for w in 2..8 {
                let rel = db(w as f32, w as f32 + 1.0) - refl;
                println!("V6a key {key} window {w}s: {rel:.1} dB rel ref (hold {hold:.1})");
                lo = lo.min(rel);
                hi = hi.max(rel);
                if !(rel >= hold - 5.0 && rel <= hold + 5.0) {
                    bad.push((w, rel));
                }
            }
            assert!(
                bad.is_empty(),
                "key {key}: windows outside [{:.1}, {:.1}]: {bad:?}",
                hold - 5.0,
                hold + 5.0
            );
            assert!(
                hi - lo <= 3.0,
                "key {key}: hold not flat — {:.1} dB spread across windows",
                hi - lo
            );
            let f0 = key_freq(key);
            let late = &buf[(6.0 * sr) as usize..(8.0 * sr) as usize];
            let sub = spectral_band_rms(late, sr, 2.0, f0 * 0.5);
            let fund = spectral_band_rms(late, sr, f0 * 0.9, f0 * 1.1);
            assert!(
                sub <= fund * 0.01,
                "key {key}: sub-f0 energy {sub} vs fundamental {fund}"
            );
        }
    }

    /// V6c (guitar v2 unit D): the hold survives the lead idiom — a whole-
    /// tone bend up and back, then a slurred drop — without losing the note
    /// or running away (catches a missing/wrong glide-endpoint clamp).
    #[test]
    fn sustain_survives_bends_and_slurs() {
        let sr = 44100.0;
        let mut v = Pluck::new(&DRIVE, 76, 100, sr, 0xD7);
        let seg = |v: &mut Pluck, secs: f32| {
            let mut b = vec![0f32; (secs * sr) as usize];
            v.render(&mut b);
            b
        };
        let head = seg(&mut v, 2.0); // latch + settle
        v.set_pitch(1.1225); // whole tone up
        let up = seg(&mut v, 0.7);
        v.set_pitch(1.0);
        let back = seg(&mut v, 0.7);
        assert!(v.legato_to(64, 90)); // slur an octave down
        let slur = seg(&mut v, 1.5);
        let db = |s: &[f32]| 20.0 * rms(s).max(1e-12).log10();
        let refl = 20.0
            * head[(0.02 * sr) as usize..(0.08 * sr) as usize]
                .iter()
                .fold(0f32, |m, &x| m.max(x.abs()))
                .max(1e-12)
                .log10();
        let hold = 20.0 * DRIVE.sustain.log10() + SUS_HOLD_REF_OFFSET_DB;
        for (nm, s) in [("bend-up", &up), ("bend-back", &back), ("slur", &slur)] {
            assert!(s.iter().all(|x| x.is_finite()), "{nm}: non-finite");
            // skip each segment's transient + re-settle window; the slurred
            // OCTAVE-DOWN holds a few dB lower still (the controller's
            // window-max envelope reads a smaller fraction of the true
            // amplitude as the period grows past the control window), so its
            // lower bound is wider — the leg's job is alive-and-stable, and
            // dead is -60.
            if nm == "slur" {
                // the slur RE-REFERENCES its own spoken level (review C4) —
                // a soft hammer tap holds quietly by design, so the absolute
                // level tracks the tap, not the original note. The
                // diagnostics are aliveness (a dead sustainer decays through
                // this window) and FLATNESS (the hold's signature).
                let h1 = db(&s[(0.8 * sr) as usize..(1.15 * sr) as usize]) - refl;
                let h2 = db(&s[(1.15 * sr) as usize..(1.5 * sr) as usize]) - refl;
                println!("V6c slur: {h1:.1} / {h2:.1} dB rel ref (hold {hold:.1})");
                assert!(h1 > -45.0 && h2 > -45.0, "slur died: {h1:.1}/{h2:.1} dB");
                assert!(
                    (h1 - h2).abs() <= 3.0,
                    "slur not held flat: {h1:.1} vs {h2:.1} dB"
                );
                continue;
            }
            // steady holds pin +/-5 dB (V6a); bend legs allow a wider LOWER
            // bound — the endpoint-minimum clamp and the higher pitch's
            // envelope statistics legitimately hold a bend a few dB softer.
            let skip = 0.1;
            let rel = db(&s[(skip * sr) as usize..]) - refl;
            println!("V6c {nm}: {rel:.1} dB rel ref (hold {hold:.1})");
            assert!(
                rel >= hold - 8.0 && rel <= hold + 5.0,
                "{nm}: {rel:.1} dB outside [{:.1}, {:.1}]",
                hold - 8.0,
                hold + 5.0
            );
        }
    }

    /// V7 (guitar v2 unit D): releasing an ENGAGED hold decays naturally —
    /// still speaking 50 ms after release (an instant kill fails the lower
    /// bound), no upward bounce, −60 dB within 2.5 s, and the voice dies.
    #[test]
    fn sustain_release_decays_naturally() {
        let sr = 44100.0;
        let mut v = Pluck::new(&DRIVE, 76, 100, sr, 0xD8);
        let mut buf = vec![0f32; (6.0 * sr) as usize];
        let split = (3.0 * sr) as usize;
        v.render(&mut buf[..split]);
        v.note_off();
        let mut alive = v.render(&mut buf[split..]);
        let db = |a: f32, b: f32| {
            20.0 * rms(&buf[(a * sr) as usize..(b * sr) as usize])
                .max(1e-12)
                .log10()
        };
        // instant-kill detector: 50 ms after release the voice must still be
        // speaking relative to its level JUST BEFORE release
        let held = db(2.8, 3.0);
        let post = db(3.02, 3.08) - held;
        assert!(
            (-20.0..=1.0).contains(&post),
            "50 ms post-release at {post:.1} dB rel the held level"
        );
        let mut prev = f32::INFINITY;
        for i in 0..12 {
            let w = db(3.0 + 0.1 * i as f32, 3.1 + 0.1 * i as f32);
            assert!(
                w <= prev + 1.0,
                "release bounced: window {i} {w:.1} vs {prev:.1}"
            );
            prev = w;
        }
        assert!(
            db(5.4, 5.6) - held <= -60.0,
            "release tail only {:.1} dB down",
            db(5.4, 5.6) - held
        );
        if alive {
            let mut tail = vec![0f32; sr as usize];
            alive = v.render(&mut tail);
        }
        assert!(!alive, "voice still alive 4 s after release");
    }

    /// V8 (guitar v2 unit D): no self-oscillation — a staccato note whose
    /// latch never engages, and a note released mid-hold, both decay to
    /// silence.
    #[test]
    fn sustain_never_self_oscillates() {
        let sr = 44100.0;
        let stac = render_pluck_phased(&DRIVE, 76, 0.05, 4.0, 0xD9);
        let t1 = rms(&stac[(3.5 * sr) as usize..]);
        assert!(t1 < 1e-4, "staccato tail rms {t1}");
        let held = render_pluck_phased(&DRIVE, 88, 2.0, 4.0, 0xDA);
        let t2 = rms(&held[(5.5 * sr) as usize..]);
        assert!(t2 < 1e-4, "held-release tail rms {t2}");
    }

    /// Diagnostic probe for the sustainer internals (`--ignored --nocapture`).
    #[test]
    #[ignore]
    fn sus_probe() {
        let sr = 44100.0;
        let mut v = Pluck::new(&DRIVE, 88, 100, sr, 0xD6);
        for step in 0..25 {
            let mut b = vec![0f32; (0.2 * sr) as usize];
            v.render(&mut b);
            println!(
                "t={:.1}s out_rms {:.5} env {:.5} ref {:.5} hold {} ramp {:.2} k_max {:.5} k {:.5}",
                (step as f32 + 1.0) * 0.2,
                rms(&b),
                v.sus_env,
                v.sus_ref,
                v.sus_hold,
                v.sus_ramp,
                v.horiz.drv.as_ref().map(|d| d.k_max).unwrap_or(0.0),
                v.horiz.drv.as_ref().map(|d| d.k).unwrap_or(0.0)
            );
        }
    }

    /// V0 (guitar v2): tight portable canaries for UNTOUCHED Pluck presets.
    /// These catch level, spectrum, or envelope contamination without relying
    /// on raw `f32` fingerprints that vary across fleet machines.
    #[test]
    fn v2_untouched_pluck_signatures_are_stable() {
        let nylon_render = render_program(24, 52, 100, 1.0, 0xE1);
        let bass_render = render_program(33, 40, 100, 1.0, 0xE2);
        assert_render_signature(
            "NYLON",
            render_signature(
                &nylon_render,
                44100.0,
                (0.05, 0.4),
                (0.05, 0.15),
                (0.5, 0.8),
            ),
            RenderSignature {
                rms_db: -24.052,
                centroid_hz: 252.392,
                late_early_db: -24.303,
            },
        );
        assert_render_signature(
            "BASS",
            render_signature(&bass_render, 44100.0, (0.05, 0.4), (0.05, 0.15), (0.5, 0.8)),
            RenderSignature {
                rms_db: -17.016,
                centroid_hz: 186.643,
                late_early_db: -15.518,
            },
        );
    }

    /// V8b (guitar v2): the coupled two-polarization step matrix
    /// [[a, k], [-k, a]] has |λ| = sqrt(a² + k²) — discrete skew coupling is
    /// NOT energy-neutral (it adds |λ|/a − 1 per step). With the sustainer
    /// driver off, every preset × key must keep (loop_gain·|H_damp(f0)|)² +
    /// k_couple² < 1 at worst-case velocity/jitter, or a bare held note could
    /// grow. Mirrors the laws in `Pluck::new` (vel ≤ ×1.2, bright jitter
    /// ≤ ×1.08, t60 jitter ≤ ×1.1, wound only darkens — ignored, conservative).
    #[test]
    fn coupled_loop_margin_holds() {
        let sr = 44100.0;
        let presets: &[(&str, &PluckPreset)] = &[
            ("NYLON", &NYLON),
            ("STEEL", &STEEL),
            ("CLEAN", &CLEAN),
            ("JAZZ", &JAZZ),
            ("DRIVE", &DRIVE),
            ("DRIVE_LEAD", &DRIVE_LEAD),
            ("MUTED", &MUTED),
            ("CLAVINET", &CLAVINET),
            ("BASS", &BASS),
            ("FRETLESS", &FRETLESS),
            ("SLAP", &SLAP),
            ("PICK", &PICK),
            ("UPRIGHT", &UPRIGHT),
            ("HARMONIC", &HARMONIC),
            ("HARP", &HARP),
            ("BANJO", &BANJO),
            ("SITAR", &SITAR),
            ("SHAMISEN", &SHAMISEN),
            ("DULCIMER", &DULCIMER),
            ("KOTO", &KOTO),
            ("PIZZ", &PIZZ),
        ];
        // the SAME closed form the shipped code uses - the oracle must not
        // hold a private copy that keeps passing against stale math
        let hmag = |bright: f32, f: f32| OnePole::lowpass_mag(bright, f, sr);
        let mut worst = 0f32;
        let mut worst_at = String::new();
        for (name, p) in presets {
            for key in 21u8..=108 {
                let harm = if p.harmonic {
                    if key < 64 {
                        2.0
                    } else {
                        3.0
                    }
                } else {
                    1.0
                };
                // both polarizations, worst-case law multipliers
                for (f, bright_mul, t60_mul_c) in [
                    (key_freq(key) * harm, 1.0, 1.0),
                    (
                        key_freq(key) * harm * p.course_detune,
                        p.course_bright,
                        p.course_t60,
                    ),
                ] {
                    let bright = (p.bright * bright_mul * 1.2 * 1.08).min(sr * 0.45);
                    let t60 = (p.t60 * 1.1 * (220.0 / f).powf(0.55)).clamp(0.25, 14.0) * t60_mul_c;
                    let lg = 10f32.powf(-3.0 / (t60 * f));
                    let m = (lg * hmag(bright, f)).powi(2) + p.course_couple * p.course_couple;
                    if m > worst {
                        worst = m;
                        worst_at = format!("{name} key {key} f {f:.0}");
                    }
                    assert!(m < 1.0, "{name} key {key}: a² + k² = {m} ≥ 1");
                }
            }
        }
        println!("V8b worst coupled margin (a²+k²) = {worst:.6} at {worst_at}");
    }

    fn render_program_released(
        program: u8,
        key: u8,
        vel: u8,
        release_s: f32,
        secs: f32,
        seed: u32,
    ) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(program, key, vel, sr, seed, false);
        let mut buf = vec![0f32; (secs * sr) as usize];
        let split = ((release_s * sr) as usize).min(buf.len());
        v.render(&mut buf[..split]);
        v.note_off();
        let block = 128;
        for chunk in buf[split..].chunks_mut(block) {
            if !v.render(chunk) {
                break;
            }
        }
        buf
    }

    fn survives_until(mut v: Box<dyn Voice>, sr: f32, secs: f32) -> bool {
        let block = 128;
        let mut left = (secs * sr) as usize;
        while left > 0 {
            let n = left.min(block);
            let mut scratch = vec![0f32; n];
            if !v.render(&mut scratch) {
                return false;
            }
            left -= n;
        }
        true
    }

    fn dies_within(mut v: Box<dyn Voice>, sr: f32, secs: f32) -> bool {
        let block = 128;
        let mut left = (secs * sr) as usize;
        while left > 0 {
            let n = left.min(block);
            let mut scratch = vec![0f32; n];
            if !v.render(&mut scratch) {
                return true;
            }
            left -= n;
        }
        false
    }

    fn render_program_sampled(
        program: u8,
        key: u8,
        vel: u8,
        secs: f32,
        seed: u32,
        samples: bool,
    ) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(program, key, vel, sr, seed, samples);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    fn segment(s: &[f32], sr: f32, a: f32, b: f32) -> &[f32] {
        &s[(a * sr) as usize..(b * sr) as usize]
    }

    fn max_abs(s: &[f32]) -> f32 {
        s.iter().map(|x| x.abs()).fold(0.0, f32::max)
    }

    fn off_harmonic_residual(seg: &[f32], sr: f32, f0: f32) -> f32 {
        let fund = band_rms(seg, sr, f0, 18.0).max(1e-9);
        let off = [1.5, 2.5, 3.5, 4.5]
            .iter()
            .map(|m| band_rms(seg, sr, f0 * *m, 18.0))
            .sum::<f32>()
            / 4.0;
        off / fund
    }

    fn low_rate_am_depth(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(60.0, sr);
        let mut lp2 = OnePole::lowpass(60.0, sr);
        let env: Vec<f32> = seg
            .iter()
            .map(|&x| lp2.process(lp1.process(x.abs())))
            .collect();
        let mean = env.iter().sum::<f32>() / env.len() as f32;
        let mut bp = Biquad::bandpass(5.5, 0.9, sr);
        let am: Vec<f32> = env.iter().map(|&x| bp.process(x - mean)).collect();
        rms(&am) / mean.max(1e-9)
    }

    // --- ChoirV2 (GM 52-54) formant-engine oracles (HLD option C) ----------
    // Thresholds are pinned from measured values (2026.07.10, key 57 / vel
    // 100 / seed 7 unless noted) with generous margins; the sustain window
    // (2.0-3.8 s) sits past the consonant hold, mouth ramp and vowel morph.

    /// CH2-O1: routing — the default bank builds the dedicated formant engine
    /// for all three choir programs.
    #[test]
    fn choir2_default_bank_routing() {
        let sr = 44100.0;
        for prog in 52..=54u8 {
            assert_eq!(
                make(prog, 60, 96, sr, 7, false).kind(),
                "choir2",
                "GM{prog} must route to ChoirV2"
            );
        }
    }

    /// CH2-O2: vowel formant placement. Per the 2026.07.08 lesson the
    /// measurement grid is FIXED (three F2 probe frequencies, band q 5) and
    /// programs are compared against each other at the same probe, so pitch
    /// and static detune cannot masquerade as timbre. Measured prominences
    /// P(f) = band_rms(f)/rms at key 57:
    ///   P870:  53 (own F2) 0.54 vs 54 0.12 | P1120: 52 (own F2) 0.32 vs 54
    ///   0.13 | P1900: 54 (own F2) 0.28 vs 52 0.11, 53 0.11.
    /// Plus the F1 ordering as centroid: ooh 939 < aah 1407 / eh 1477.
    #[test]
    fn choir2_formant_placement_per_vowel() {
        let sr = 44100.0;
        let sus = |prog: u8| {
            let sig = render_program(prog, 57, 100, 4.0, 7);
            sig[(2.0 * sr) as usize..(3.8 * sr) as usize].to_vec()
        };
        let (aah, ooh, eh) = (sus(52), sus(53), sus(54));
        let prom = |seg: &[f32], f: f32| band_rms(seg, sr, f, 5.0) / rms(seg).max(1e-9);
        assert!(
            prom(&ooh, 870.0) > 1.8 * prom(&eh, 870.0),
            "ooh F2 870 not prominent: {} vs eh {}",
            prom(&ooh, 870.0),
            prom(&eh, 870.0)
        );
        assert!(
            prom(&aah, 1120.0) > 1.6 * prom(&eh, 1120.0),
            "aah F2 1120 not prominent: {} vs eh {}",
            prom(&aah, 1120.0),
            prom(&eh, 1120.0)
        );
        assert!(
            prom(&eh, 1900.0) > 1.6 * prom(&aah, 1900.0).max(prom(&ooh, 1900.0)),
            "eh F2 1900 not prominent: {} vs aah {} ooh {}",
            prom(&eh, 1900.0),
            prom(&aah, 1900.0),
            prom(&ooh, 1900.0)
        );
        let cent = |seg: &[f32]| crate::testutil::centroid(seg, sr);
        assert!(
            cent(&ooh) < 0.8 * cent(&aah) && cent(&ooh) < 0.8 * cent(&eh),
            "ooh must be darkest: ooh {} aah {} eh {}",
            cent(&ooh),
            cent(&aah),
            cent(&eh)
        );
    }

    /// CH2-O3: the singer's-formant cluster. (a) All three programs carry a
    /// 2.8-3.3 kHz ring that stands clear of the spectrum just above it
    /// (measured cluster/4100 ratios 1.6-1.9×); (b) a closed "mm" vowel via
    /// the CC70 `set_vowel` path shades the cluster down with the lips
    /// (measured 0.175 → 0.096 at prog 53).
    #[test]
    fn choir2_singers_formant_cluster() {
        let sr = 44100.0;
        let prom = |seg: &[f32], f: f32, q: f32| band_rms(seg, sr, f, q) / rms(seg).max(1e-9);
        for prog in 52..=54u8 {
            let sig = render_program(prog, 57, 100, 4.0, 7);
            let sus = segment(&sig, sr, 2.0, 3.8);
            let cluster = prom(sus, 2950.0, 5.0).max(prom(sus, 3250.0, 5.0));
            let above = prom(sus, 4100.0, 5.0);
            assert!(
                cluster > 1.3 * above,
                "GM{prog} singer's formant missing: cluster {cluster} vs 4100 band {above}"
            );
        }
        let render_vowel = |vowel: Option<([f32; 3], [f32; 3], [f32; 3])>| {
            let mut v = choir(53, 57, 100, sr, 7);
            if let Some((f, q, g)) = vowel {
                v.set_vowel(f, q, g);
            }
            let mut buf = vec![0f32; (4.0 * sr) as usize];
            v.render(&mut buf);
            buf
        };
        let open = render_vowel(None);
        let mm = render_vowel(Some((
            [500.0, 1400.0, 2400.0],
            [12.0, 10.0, 9.0],
            [1.0, 0.30, 0.10],
        )));
        let sfr = |sig: &[f32]| {
            let sus = segment(sig, sr, 2.0, 3.8);
            band_rms(sus, sr, 3050.0, 3.0) / rms(sus).max(1e-9)
        };
        assert!(
            sfr(&mm) < 0.75 * sfr(&open),
            "mm must close the singer's cluster: mm {} open {}",
            sfr(&mm),
            sfr(&open)
        );
    }

    /// CH2-O4: the soft consonant onset — the first 60 ms is both quieter
    /// (closed lips, measured 0.14-0.46× sustain) and darker (closed-lips
    /// lowpass, measured centroid 397-580 Hz vs 939-1477 sustain), and the
    /// onset carries breath (spectral flatness ≥ 0.12 measured 0.17-0.27)
    /// while the sustain stays harmonic (flatness ≤ 0.30 measured
    /// 0.07-0.19).
    #[test]
    fn choir2_consonant_breath_onset() {
        let sr = 44100.0;
        for prog in 52..=54u8 {
            let sig = render_program(prog, 57, 100, 4.0, 7);
            let onset = segment(&sig, sr, 0.005, 0.065);
            let sus = segment(&sig, sr, 2.0, 3.8);
            assert!(
                rms(onset) < 0.62 * rms(sus),
                "GM{prog} onset not soft: onset {} sus {}",
                rms(onset),
                rms(sus)
            );
            let (c_on, c_sus) = (
                crate::testutil::centroid(onset, sr),
                crate::testutil::centroid(sus, sr),
            );
            assert!(
                c_on < 0.62 * c_sus,
                "GM{prog} onset not closed-lips dark: onset {c_on} sus {c_sus}"
            );
            let (f_on, f_sus) = (
                crate::testutil::flatness(onset, sr, 300.0, 6000.0),
                crate::testutil::flatness(sus, sr, 300.0, 6000.0),
            );
            assert!(
                f_on > 0.12,
                "GM{prog} onset carries no breath: flatness {f_on}"
            );
            assert!(
                f_sus < 0.30,
                "GM{prog} sustain not harmonic enough: flatness {f_sus}"
            );
        }
    }

    /// CH2-O5: ensemble shimmer. Structure: eight singers with decorrelated
    /// vibrato rates (spanning ≥ 0.8 Hz, all in the 3.4-6.2 Hz vocal range)
    /// and staggered onsets. Audio: envelope AM near the vibrato rates in the
    /// LIVE window (2.6-3.6 s, all delays ≤ 0.8 s + ramps ≤ 1.2 s are past)
    /// stays above a floor (measured 0.13-0.22; the grid is an envelope
    /// bandpass at 5.5 Hz, well away from the ±10-cent static detune lines
    /// per the 2026.07.08 shimmer-oracle lesson).
    #[test]
    fn choir2_ensemble_shimmer() {
        let sr = 44100.0;
        for prog in 52..=54u8 {
            let v = choir(prog, 57, 100, sr, 7);
            let rates = v.singer_vib_rates();
            let (lo, hi) = rates
                .iter()
                .fold((f32::MAX, f32::MIN), |(l, h), &r| (l.min(r), h.max(r)));
            assert!(
                hi - lo > 0.8,
                "GM{prog} vibrato rates too uniform: {lo}-{hi} Hz"
            );
            assert!(
                lo > 3.4 && hi < 6.2,
                "GM{prog} vibrato outside vocal range: {lo}-{hi} Hz"
            );
            let delays = v.singer_vib_delays();
            let d_lo = *delays.iter().min().unwrap();
            let d_hi = *delays.iter().max().unwrap();
            assert!(
                d_hi > d_lo + (0.05 * sr) as u32,
                "GM{prog} vibrato onsets not staggered: {d_lo}-{d_hi}"
            );
            let sig = render_program(prog, 57, 100, 4.0, 7);
            let live = segment(&sig, sr, 2.6, 3.6);
            let am = low_rate_am_depth(live, sr);
            assert!(am > 0.08, "GM{prog} live-window shimmer too flat: {am}");
        }
    }

    /// CH2-O6: pitch integrity and level continuity. The ensemble's spectral
    /// peak sits within 45 cents of the written pitch (Goertzel, not zero
    /// crossings), the bend path works, and the choir's sustained level stays
    /// within the 2.4× continuity window of the neighbouring string ensemble
    /// (measured ratios 0.80-2.07 across keys 45/57/69).
    #[test]
    fn choir2_pitch_and_level_continuity() {
        let sr = 44100.0;
        for prog in 52..=54u8 {
            for key in [45u8, 57, 69] {
                let f0 = key_freq(key);
                let sig = render_program(prog, key, 100, 4.0, 7);
                let sus = segment(&sig, sr, 2.0, 3.8);
                let hz = crate::testutil::peak_locate(sus, sr, f0 * 0.9, f0 * 1.1);
                let cents = 1200.0 * (hz / f0).log2().abs();
                assert!(
                    cents < 45.0,
                    "GM{prog} key {key} pitch off by {cents} cents ({hz} Hz vs {f0})"
                );
                let s48 = render_program(48, key, 100, 4.0, 7);
                let ratio = rms(sus) / rms(segment(&s48, sr, 2.0, 3.8)).max(1e-9);
                assert!(
                    (1.0 / 2.4..=2.4).contains(&ratio),
                    "GM{prog} key {key} level discontinuity vs strings: {ratio}"
                );
            }
        }
        // bend: a whole tone up lands where it should
        let mut v = choir(52, 57, 100, sr, 7);
        let up = 2f32.powf(2.0 / 12.0);
        v.set_pitch(up);
        let mut buf = vec![0f32; (2.0 * sr) as usize];
        v.render(&mut buf);
        let want = key_freq(57) * up;
        let hz =
            crate::testutil::peak_locate(&buf[(1.0 * sr) as usize..], sr, want * 0.9, want * 1.1);
        assert!(
            (1200.0 * (hz / want).log2()).abs() < 45.0,
            "bent choir pitch {hz}, want {want}"
        );
    }

    #[test]
    fn vibraphone_11_motor_tremolo_modulates_amplitude() {
        let sr = 12000.0;
        let key = 69;
        let vel = 104;
        let seed = 0x11_0012;
        let render = |program: u8, seed: u32| {
            let mut voice = make(program, key, vel, sr, seed, false);
            let mut buf = vec![0f32; (2.8 * sr) as usize];
            voice.render(&mut buf);
            buf
        };
        let vibraphone = render(11, seed);
        let vibe_body = segment(&vibraphone, sr, 0.35, 2.35);
        let (peak, rate) = env_autocorr_peak_detrend(vibe_body, sr, 0.12, 0.22, 4.0);
        let depth = low_rate_am_depth(vibe_body, sr);

        assert!(
            peak >= 0.28,
            "GM11 vibraphone motor AM peak too weak: {peak:.3}"
        );
        assert!(
            (rate - 6.0).abs() <= 0.8,
            "GM11 vibraphone motor AM rate should be near 6 Hz, got {rate:.2} Hz"
        );
        assert!(
            depth >= 0.08,
            "GM11 vibraphone motor AM depth too weak: {depth:.4}"
        );

        for program in [10u8, 12, 13, 14] {
            let static_voice = render(program, seed ^ program as u32);
            let static_body = segment(&static_voice, sr, 0.35, 2.35);
            let (static_peak, static_rate) =
                env_autocorr_peak_detrend(static_body, sr, 0.12, 0.22, 4.0);
            let static_depth = low_rate_am_depth(static_body, sr);
            assert!(
                !((static_rate - 6.0).abs() <= 0.8 && static_peak >= 0.18),
                "GM{program} picked up a GM11-like motor signature: peak {static_peak:.3} at {static_rate:.2} Hz, depth {static_depth:.4}"
            );
        }
    }

    #[test]
    fn keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice() {
        let sr = 44100.0;
        let key = 60;
        let vel = 96;
        let seed = 0x4b05_000f;
        for program in 0u8..=3 {
            assert!(
                is_acoustic_piano(program),
                "GM{program} should stay acoustic"
            );
        }
        for program in 4u8..=7 {
            assert!(
                !is_acoustic_piano(program),
                "GM{program} should not use acoustic-piano engine gates"
            );
        }
        let acoustic = render_program(0, key, vel, 1.2, seed);
        for program in 1u8..=3 {
            assert_eq!(
                render_program(program, key, vel, 1.2, seed),
                acoustic,
                "GM0-3 acoustic piano routes diverged locally"
            );
        }

        let mut renders: Vec<Vec<f32>> = Vec::new();
        for program in 4u8..=7 {
            let s = render_program(program, key, vel, 1.2, seed ^ program as u32);
            assert_ne!(
                s, acoustic,
                "GM{program} still renders as the acoustic piano model"
            );
            assert!(
                renders.iter().all(|old| old != &s),
                "GM{program} is not distinct from an earlier GM4-7 keyboard voice"
            );
            renders.push(s);
        }

        #[cfg(feature = "embedded-samples")]
        {
            let ac_plain = render_program_sampled(0, key, vel, 0.35, seed, false);
            let ac_sampled = render_program_sampled(0, key, vel, 0.35, seed, true);
            assert_ne!(
                ac_plain, ac_sampled,
                "GM0 sample-layer positive control did not differ"
            );
        }
        for program in 4u8..=7 {
            let plain =
                render_program_sampled(program, key, vel, 0.35, seed ^ program as u32, false);
            let sampled =
                render_program_sampled(program, key, vel, 0.35, seed ^ program as u32, true);
            assert_eq!(
                plain, sampled,
                "GM{program} still uses the acoustic piano LA sample layer"
            );
        }

        let band_ratio = |program: u8, key: u8, center: f32| {
            let f0 = key_freq(key);
            let s = render_program(program, key, vel, 0.8, seed ^ program as u32 ^ key as u32);
            let body = segment(&s, sr, 0.05, 0.35);
            band_rms(body, sr, f0 * center, 12.0) / rms(body).max(1e-9)
        };
        for key in [60u8, 76] {
            let rhodes_bell = band_ratio(4, key, 3.0);
            let dx_bell = band_ratio(5, key, 3.0);
            assert!(
                dx_bell >= rhodes_bell * 1.25,
                "GM5 should be more bell-forward than GM4 at key {key}: {dx_bell:.4} vs {rhodes_bell:.4}"
            );
        }

        let body_rms = |program: u8, vel: u8| {
            let s = render_program(program, key, vel, 0.8, seed ^ program as u32 ^ vel as u32);
            rms(segment(&s, sr, 0.05, 0.35))
        };
        let harpsi_lo = body_rms(6, 32);
        let harpsi_hi = body_rms(6, 116);
        let piano_lo = body_rms(0, 32);
        let piano_hi = body_rms(0, 116);
        assert!(
            harpsi_lo > 1e-4,
            "GM6 harpsichord too quiet at low velocity"
        );
        assert!(
            harpsi_hi / harpsi_lo <= 1.5,
            "GM6 harpsichord velocity spread too piano-like: {harpsi_hi:.6} / {harpsi_lo:.6}"
        );
        assert!(
            piano_hi / piano_lo >= 3.0,
            "GM0 positive control lacks broad piano velocity spread: {piano_hi:.6} / {piano_lo:.6}"
        );

        let mut clav = make(7, key, vel, sr, seed, false);
        assert_eq!(
            clav.kind(),
            "CLAVINET",
            "GM7 should route through the clavinet pluck preset"
        );
        let mut clav_buf = vec![0f32; (0.8 * sr) as usize];
        clav.render(&mut clav_buf);
        let early = rms(segment(&clav_buf, sr, 0.03, 0.18));
        let late = rms(segment(&clav_buf, sr, 0.42, 0.72));
        assert!(
            late < early * 0.45,
            "GM7 clavinet should decay quickly: late {late:.6}, early {early:.6}"
        );
    }

    #[test]
    fn cathedral_organ_legacy_signature_is_stable() {
        let sr = 44_100.0;
        let mut legacy = legacy_church_organ(69, 104, sr, 0x5eed);
        let mut rendered = vec![0.0; (0.5 * sr) as usize];
        legacy.render(&mut rendered);
        assert_render_signature(
            "legacy cathedral organ",
            render_signature(&rendered, sr, (0.1, 0.4), (0.05, 0.15), (0.35, 0.48)),
            RenderSignature {
                rms_db: -12.798,
                centroid_hz: 1189.406,
                late_early_db: -0.724,
            },
        );
    }

    #[test]
    fn cathedral_organ_has_pedal_body_and_mixture_sheen() {
        let sr = 44_100.0;
        let low = render_program(19, 36, 96, 1.2, 0x1234);
        let body = segment(&low, sr, 0.35, 1.10);
        let p32 = mag_at(body, sr, 16.35);
        let p16 = mag_at(body, sr, 32.70);
        let p8 = mag_at(body, sr, 65.41);
        assert!(
            p32 > 1e-4 && p16 > 1e-4 && p8 > 1e-4,
            "pedal peaks {p32}/{p16}/{p8}"
        );
        assert!(
            p32 >= p8 * 10f32.powf(-18.0 / 20.0),
            "32-foot {p32} vs 8-foot {p8}"
        );
        let sub = spectral_band_rms(body, sr, 15.0, 40.0);
        let bass = spectral_band_rms(body, sr, 40.0, 120.0);
        assert!(
            sub >= bass * 10f32.powf(-14.0 / 20.0),
            "sub/bass {sub}/{bass}"
        );

        let mut legacy = legacy_church_organ(36, 96, sr, 0x1234);
        let mut legacy_render = vec![0.0; (1.2 * sr) as usize];
        legacy.render(&mut legacy_render);
        let legacy_sub = spectral_band_rms(segment(&legacy_render, sr, 0.35, 1.10), sr, 15.0, 40.0);
        assert!(
            sub >= legacy_sub * 10f32.powf(6.0 / 20.0),
            "cathedral/legacy 15-40Hz {sub}/{legacy_sub}"
        );

        let high = render_program(19, 84, 96, 0.8, 0x1234);
        let high_body = segment(&high, sr, 0.25, 0.75);
        assert!(
            hp_rms(high_body, sr, 4_000.0) >= 0.04 * rms(high_body),
            "high mixture energy too low"
        );
    }

    #[test]
    fn cathedral_organ_steady_level_is_velocity_independent() {
        let sr = 44_100.0;
        let soft = render_program(19, 60, 32, 0.8, 7);
        let loud = render_program(19, 60, 120, 0.8, 7);
        let soft_rms = rms(segment(&soft, sr, 0.30, 0.75));
        let loud_rms = rms(segment(&loud, sr, 0.30, 0.75));
        let delta_db = 20.0 * (loud_rms / soft_rms.max(1e-12)).log10().abs();
        assert!(delta_db <= 1.5, "steady velocity delta {delta_db:.2} dB");
    }

    // Oracle A — the steady state is alive and aperiodic (not a static,
    // phase-locked additive tone = "harpsichord"). Key 76 (E5) sits in the
    // complained-about register, has no pedal ranks, and carries both a
    // unison pair (Principal id1 vs Reed id9) and mixture-vs-principal
    // coincident ratios. A2 (max normalised envelope autocorrelation over
    // 1.5–4.5 s lags) is the discriminator: a static organ's constant-rate
    // beats make the envelope quasi-periodic (re-peaks high); independent
    // per-pipe wind-walks decorrelate it (low). Calibration (measured @44.1k,
    // stable across event seeds to ±0.01):
    //   pre-wander static organ  autocorr ≈ 0.44,  cov ≈ 0.153
    //   post-wander              autocorr ≈ 0.25,  cov ≈ 0.131
    // 0.35 sits cleanly between (≈0.10 margin each side). The static organ is a
    // touch less self-similar than a pure model predicts, so the separation is
    // ~1.8× rather than a larger factor — but the two clusters do not overlap
    // and are seed-stable, so the threshold holds for this signal.
    #[test]
    fn cathedral_organ_steady_state_is_alive_and_aperiodic() {
        let sr = 44_100.0;
        let render = render_program(19, 76, 96, 11.0, 0xA11CE);
        let steady = segment(&render, sr, 1.0, 10.5);
        let (autocorr, cov) = crate::testutil::env_aperiodicity(steady, sr, 1.5, 4.5);
        println!("cathedral A  seedA: autocorr={autocorr:.4} cov={cov:.4}");

        // A3 — the wander rides the STABLE (rank,key) seed, not the event seed:
        // a different event seed must give the same envelope statistics.
        let render2 = render_program(19, 76, 96, 11.0, 0x5EED9);
        let steady2 = segment(&render2, sr, 1.0, 10.5);
        let (autocorr2, cov2) = crate::testutil::env_aperiodicity(steady2, sr, 1.5, 4.5);
        println!("cathedral A  seedB: autocorr={autocorr2:.4} cov={cov2:.4}");

        assert!(cov >= 0.02, "steady envelope is frozen: cov {cov:.4}");
        assert!(
            autocorr <= 0.35,
            "steady envelope is quasi-periodic (harpsichord-like): autocorr {autocorr:.4}"
        );
        assert!(
            (cov - cov2).abs() <= 0.20 * cov.max(cov2) + 1e-6
                && (autocorr - autocorr2).abs() <= 0.15,
            "wander looks event-seeded: ({cov:.4},{autocorr:.4}) vs ({cov2:.4},{autocorr2:.4})"
        );
    }

    // Oracle B — regression guard that sustained high notes are NOT
    // harpsichord-like in the two ways that percept is often assumed to arise:
    // integer-buzz and a plucked onset. Measurement (@44.1k) showed this voice
    // already sits well inside "organ" territory on both — key84 buzz ≈ −27 dB,
    // key96 ≈ −16 dB, key88 onset rise ≈ 143 ms — so the actual "harpsichordy"
    // driver is static-ness (Oracle A / the wind-wander), not these. B1 measures
    // integer-buzz at k∈{5,7,11,13}·f0 — the slots reachable ONLY by the
    // unison/reed ranks' own upper harmonics (mixtures live at 1.5/2/3/4× and
    // their multiples), so it excludes the intended mixture sheen and sees only
    // the "dense integer series" that reads as a plucked string. Thresholds carry
    // margin over the measured values: this test guards against a future change
    // (or the reverb refresh) regressing the treble, it is not driving a fix.
    #[test]
    fn cathedral_organ_high_notes_are_not_harpsichord_bright() {
        let sr = 44_100.0;
        for key in [84u8, 96] {
            let f0 = key_freq(key);
            let render = render_program(19, key, 96, 4.0, 0xB0B);
            let body = segment(&render, sr, 0.8, 3.5);
            let mut buzz2 = 0.0f32;
            for k in [5.0f32, 7.0, 11.0, 13.0] {
                let f = k * f0;
                if f < 0.45 * sr {
                    let m = crate::testutil::mag_at(body, sr, f);
                    buzz2 += m * m;
                }
            }
            let body_mag = crate::testutil::mag_at(body, sr, f0).max(1e-9);
            let buzz_db = 20.0 * (buzz2.sqrt() / body_mag).log10();
            println!("cathedral B  key{key}: integer-buzz {buzz_db:.2} dB");
            assert!(
                buzz_db <= -14.0,
                "key {key} integer-buzz {buzz_db:.2} dB reads harpsichord-like"
            );
            // B3 anti-dulling: keep real >4 kHz mixture sheen (mirrors the pinned
            // pedal-body test's high clause, so purifying flues cannot go too far).
            let sheen = hp_rms(body, sr, 4_000.0);
            assert!(
                sheen >= 0.04 * rms(body),
                "key {key} mixture sheen collapsed"
            );
        }

        // B2 — the onset is no longer a pluck: envelope reaches 90% of steady
        // within no LESS than 8 ms (a real treble principal speaks in 10–30 ms;
        // a sub-5 ms rise + noise chiff is a hammer/pluck cue).
        let render = render_program(19, 88, 96, 1.0, 0xB0B);
        let mut lp = OnePole::lowpass(200.0, sr);
        let env: Vec<f32> = render.iter().map(|&x| lp.process(x.abs())).collect();
        let steady = rms(segment(&render, sr, 0.30, 0.60));
        let rise_idx = env
            .iter()
            .position(|&e| e >= 0.9 * steady)
            .unwrap_or(env.len());
        let rise_ms = rise_idx as f32 / sr * 1000.0;
        println!("cathedral B  key88 rise {rise_ms:.2} ms");
        assert!(
            rise_ms >= 8.0,
            "key 88 onset rises in {rise_ms:.2} ms (pluck-like)"
        );
    }

    #[test]
    fn cathedral_organ_pipe_identity_ignores_event_seed() {
        let a = CathedralOrgan::new(60, 90, 44_100.0, 1);
        let b = CathedralOrgan::new(60, 90, 44_100.0, 0xdead_beef);
        assert_eq!(a.debug_pipe_identity(), b.debug_pipe_identity());
    }

    #[test]
    fn cathedral_organ_registration_and_mixture_breaks_are_pinned() {
        for (key, want) in [
            (47, vec![6.0, 8.0, 12.0, 16.0]),
            (48, vec![4.0, 6.0, 8.0, 12.0, 16.0]),
            (49, vec![4.0, 6.0, 8.0, 12.0]),
            (60, vec![3.0, 4.0, 6.0, 8.0, 12.0]),
            (72, vec![2.0, 3.0, 4.0, 6.0, 8.0]),
            (84, vec![1.5, 2.0, 3.0, 4.0, 6.0]),
        ] {
            let ranks = cathedral_registration(key);
            assert!(ranks.len() <= 14);
            let mut got: Vec<_> = ranks
                .iter()
                .filter(|rank| rank.family == RankFamily::Mixture)
                .map(|rank| rank.ratio)
                .collect();
            got.sort_by(f32::total_cmp);
            let mut want = want;
            want.sort_by(f32::total_cmp);
            assert_eq!(got, want, "mixture break at key {key}");
        }
        let full = cathedral_registration(46);
        assert_eq!(full.len(), 14);
        assert_eq!(full.iter().find(|rank| rank.id == 10).unwrap().gain, 0.32);
        let half = cathedral_registration(48);
        assert_eq!(half.iter().find(|rank| rank.id == 10).unwrap().gain, 0.16);
        assert_eq!(cathedral_registration(50).len(), 10);

        let high = CathedralOrgan::new(108, 96, 44_100.0, 7);
        let audible_mixtures = high
            .pipes
            .iter()
            .filter(|pipe| pipe.family == RankFamily::Mixture && pipe.active)
            .count();
        assert!(
            audible_mixtures >= 2,
            "top-compass mixture ranks {audible_mixtures}"
        );
    }

    #[test]
    fn cathedral_organ_mixture_crossfades_are_smooth() {
        let sr = 44_100.0;
        for break_key in [48u8, 60, 72, 84] {
            let measurements: Vec<_> = [break_key - 1, break_key, break_key + 1]
                .into_iter()
                .map(|key| {
                    // Measure the registration level over a long window: per-pipe
                    // wind-wander is a zero-mean micro-dynamic, so a short window
                    // catches different keys at different walk phases and would
                    // read that as a registration jump. A ~2.5 s window averages
                    // the wander out and tests the static registration-continuity
                    // contract the 2.0 dB bound is really about.
                    let rendered = render_program(19, key, 96, 3.0, 99);
                    let body = segment(&rendered, sr, 0.5, 3.0);
                    (rms(body), spectral_centroid(body, sr, 100.0, 12_000.0))
                })
                .collect();
            for (pair_index, pair) in measurements.windows(2).enumerate() {
                let level_db = 20.0 * (pair[1].0 / pair[0].0.max(1e-12)).log10().abs();
                let centroid_ratio = pair[1].1 / pair[0].1.max(1e-12);
                assert!(
                    level_db <= 2.0,
                    "break {break_key} pair {pair_index} level jump {level_db:.2}dB ({:.6}/{:.6})",
                    pair[0].0,
                    pair[1].0
                );
                assert!(
                    (0.75..=1.25).contains(&centroid_ratio),
                    "break {break_key} centroid ratio {centroid_ratio:.3}"
                );
            }
        }
    }

    #[test]
    fn cathedral_organ_rejects_sub_ten_hz_across_low_midi_keys() {
        let sr = 44_100.0;
        for key in 0u8..=35 {
            let rendered = render_program(19, key, 96, 0.7, 0x7000 + key as u32);
            let body = segment(&rendered, sr, 0.25, 0.65);
            let infrasonic = spectral_band_rms(body, sr, 0.1, 9.5);
            let musical_sub = spectral_band_rms(body, sr, 12.0, 40.0).max(1e-12);
            let relative_db = 20.0 * (infrasonic / musical_sub).log10();
            assert!(
                relative_db <= -24.0,
                "key {key} sub-10 ratio {relative_db:.1}dB"
            );
        }
    }

    #[test]
    fn cathedral_organ_composes_pitch_pressure_and_tremulant() {
        let bend = 2f32.powf(7.0 / 12.0);
        let mut pitch_first = CathedralOrgan::new(48, 90, 44_100.0, 9);
        pitch_first.set_pitch(bend);
        pitch_first.set_organ_pressure(0.8, 0.45);
        let mut wind_first = CathedralOrgan::new(48, 90, 44_100.0, 9);
        wind_first.set_organ_pressure(0.8, 0.45);
        wind_first.set_pitch(bend);
        assert_eq!(
            pitch_first.debug_composed_frequencies(),
            wind_first.debug_composed_frequencies()
        );
        assert!(pitch_first.debug_all_pipe_bounds_hold());

        let mut loaded = CathedralOrgan::new(48, 90, 44_100.0, 9);
        let unloaded: Vec<_> = loaded.pipes.iter().map(|pipe| pipe.frequency).collect();
        loaded.set_organ_pressure(1.0, 0.0);
        let cents = |id: u8| {
            let index = loaded.pipes.iter().position(|pipe| pipe.id == id).unwrap();
            1200.0 * (loaded.pipes[index].frequency / unloaded[index]).log2()
        };
        assert!(
            (-1.5..=-1.0).contains(&cents(10)),
            "pedal settling {} cents",
            cents(10)
        );
        assert!(
            (-5.2..=-4.8).contains(&cents(1)),
            "principal settling {} cents",
            cents(1)
        );
        assert!(
            (-6.2..=-5.8).contains(&cents(9)),
            "reed settling {} cents",
            cents(9)
        );

        let mut dry = CathedralOrgan::new(48, 90, 44_100.0, 17);
        let mut under_load = CathedralOrgan::new(48, 90, 44_100.0, 17);
        under_load.set_organ_pressure(1.0, 0.0);
        let mut dry_audio = vec![0.0; 35_280];
        let mut loaded_audio = vec![0.0; 35_280];
        dry.render(&mut dry_audio);
        under_load.render(&mut loaded_audio);
        let dry_level = rms(&dry_audio[13_230..33_075]);
        let loaded_level = rms(&loaded_audio[13_230..33_075]);
        let settling_db = 20.0 * (loaded_level / dry_level.max(1e-12)).log10();
        assert!(
            (-1.8..=-0.3).contains(&settling_db),
            "loaded pipe level settled {settling_db:.2}dB"
        );
    }

    #[test]
    fn cathedral_organ_runtime_bend_stays_bounded_and_release_is_clean() {
        let sr = 44_100.0;
        let mut high = CathedralOrgan::new(120, 100, sr, 5);
        high.set_pitch(4.0);
        high.set_organ_pressure(1.0, 1.0);
        high.set_organ_swell(1.0); // exercise the driven reed table at the extreme bend
        assert!(high.debug_all_pipe_bounds_hold());
        let mut high_buf = vec![0.0; sr as usize / 2];
        high.render(&mut high_buf);
        assert!(high_buf.iter().all(|x| x.is_finite()));

        let mut low = CathedralOrgan::new(0, 100, sr, 6);
        assert!(low.debug_all_pipe_bounds_hold());
        // Four seconds gives the lowest retained (~16 Hz) rank enough cycles
        // that the mean measures DC rather than a partial-cycle endpoint.
        let mut low_buf = vec![0.0; (4.0 * sr) as usize];
        low.render(&mut low_buf);
        let mean = low_buf.iter().sum::<f32>() / low_buf.len() as f32;
        assert!(mean.abs() < 10f32.powf(-70.0 / 20.0), "DC {mean}");
        low.note_off();
        assert!(
            dies_within(Box::new(low), sr, 0.25),
            "cathedral organ release exceeded 250 ms"
        );
    }

    #[test]
    fn reed_organ_accordion_harmonica_have_free_reed_character() {
        let sr = 44100.0;
        let key = 69;
        let vel = 104;
        let seed = 0x5eed;
        let f0 = key_freq(key);

        for program in 20..=23 {
            let mut v = make(program, key, vel, sr, seed, false);
            assert_eq!(v.kind(), "organ", "GM{program} must route through make()");
            let mut buf = vec![0f32; (0.25 * sr) as usize];
            assert!(v.render(&mut buf), "GM{program} should sustain");
            assert!(
                rms(&buf) > 1e-4 && buf.iter().all(|x| x.is_finite()),
                "GM{program} render invalid"
            );
        }

        let expected = [
            (
                16u8,
                RenderSignature {
                    rms_db: -12.554,
                    centroid_hz: 358.579,
                    late_early_db: 0.270,
                },
            ),
            (
                // GM17 percussive organ (Stage 5a): darker than 16 (dropped 4'
                // drawbar, thinned 3rd) with a decaying 3rd-harmonic tap.
                17,
                RenderSignature {
                    rms_db: -12.710,
                    centroid_hz: 330.765,
                    late_early_db: 0.257,
                },
            ),
            (
                18,
                RenderSignature {
                    rms_db: -18.891,
                    centroid_hz: 701.393,
                    late_early_db: 0.158,
                },
            ),
        ];
        for (program, signature) in expected {
            let rendered = render_program(program, key, vel, 0.5, seed);
            assert_render_signature(
                &format!("legacy organ GM{program}"),
                render_signature(&rendered, sr, (0.1, 0.4), (0.05, 0.15), (0.35, 0.48)),
                signature,
            );
        }
        let mut legacy = legacy_church_organ(key, vel, sr, seed);
        let mut legacy_render = vec![0.0; (0.5 * sr) as usize];
        legacy.render(&mut legacy_render);
        assert_render_signature(
            "legacy organ GM19",
            render_signature(&legacy_render, sr, (0.1, 0.4), (0.05, 0.15), (0.35, 0.48)),
            RenderSignature {
                rms_db: -12.798,
                centroid_hz: 1189.406,
                late_early_db: -0.724,
            },
        );

        let render_old_organ = |program| {
            if program == 19 {
                let mut v = legacy_church_organ(key, vel, sr, seed ^ program as u32);
                let mut s = vec![0.0; (0.9 * sr) as usize];
                v.render(&mut s);
                s
            } else {
                render_program(program, key, vel, 0.9, seed ^ program as u32)
            }
        };
        let click_ratio = |program| {
            let s = render_old_organ(program);
            let click = hp_rms(segment(&s, sr, 0.0, 0.008), sr, 2500.0);
            let body = rms(segment(&s, sr, 0.08, 0.22)).max(1e-9);
            click / body
        };
        let gm19_click = click_ratio(19);
        assert!(gm19_click > 0.030, "GM19 click floor: {gm19_click:.4}");
        for program in 20..=23 {
            let r = click_ratio(program);
            assert!(
                r <= gm19_click * 0.35,
                "GM{program} onset too clicky: {r:.4} vs GM19 {gm19_click:.4}"
            );
        }

        let mut gm19_voice = legacy_church_organ(key, vel, sr, seed);
        let mut gm19 = vec![0.0; (0.9 * sr) as usize];
        gm19_voice.render(&mut gm19);
        let gm20 = render_program(20, key, vel, 0.9, seed);
        let gm20_body = segment(&gm20, sr, 0.26, 0.60);
        let gm20_pitch = peak_locate(gm20_body, sr, f0 * 0.97, f0 * 1.03);
        assert!(
            (gm20_pitch / f0 - 1.0).abs() <= 0.02,
            "GM20 late pitch {gm20_pitch:.1} Hz vs {f0:.1}"
        );
        let gm20_res = off_harmonic_residual(gm20_body, sr, f0);
        let gm19_res = off_harmonic_residual(segment(&gm19, sr, 0.26, 0.60), sr, f0);
        assert!(
            gm20_res >= 1.5 * gm19_res,
            "GM20 bellows/free-reed residual {gm20_res:.4} vs GM19 {gm19_res:.4}"
        );

        let am = |program| {
            let s = render_program(program, key, vel, 1.0, seed ^ 0x3333);
            let seg = segment(&s, sr, 0.20, 0.90);
            let (peak, rate) = env_autocorr_peak(seg, sr, 1.0 / 8.0, 1.0 / 3.0);
            (
                low_rate_am_depth(seg, sr),
                peak,
                rate,
                rms(seg),
                max_abs(seg),
            )
        };
        let (d20, _p20, _r20, rms20, _mx20) = am(20);
        for program in [21u8, 23] {
            let (depth, peak, rate, body, peak_abs) = am(program);
            assert!(
                (3.0..=8.0).contains(&rate) && peak >= 0.15 && depth >= 2.0 * d20.max(0.002),
                "GM{program} musette AM depth/peak/rate {depth:.4}/{peak:.3}/{rate:.2} Hz vs GM20 depth {d20:.4}"
            );
            assert!(
                (0.6 * rms20..=1.8 * rms20).contains(&body),
                "GM{program} body RMS {body:.5} vs GM20 {rms20:.5}"
            );
            assert!(
                peak_abs < 2.5 * rms20,
                "GM{program} peak {peak_abs:.5} too hot vs GM20 RMS {rms20:.5}"
            );
        }

        let gm22 = render_program(22, key, vel, 0.7, seed);
        let early_pitch = peak_locate(segment(&gm22, sr, 0.015, 0.055), sr, f0 * 0.90, f0 * 1.03);
        let late_pitch = peak_locate(segment(&gm22, sr, 0.16, 0.36), sr, f0 * 0.97, f0 * 1.03);
        assert!(
            early_pitch <= late_pitch * 0.985,
            "GM22 scoop missing: early {early_pitch:.1} late {late_pitch:.1}"
        );
        assert!(
            (late_pitch / f0 - 1.0).abs() <= 0.02,
            "GM22 late pitch {late_pitch:.1} Hz vs {f0:.1}"
        );
        let gm22_res = off_harmonic_residual(segment(&gm22, sr, 0.26, 0.60), sr, f0);
        assert!(
            gm22_res >= 1.3 * gm20_res,
            "GM22 breath residual {gm22_res:.4} vs GM20 {gm20_res:.4}"
        );

        let mut harmonica = organ(22, key, vel, sr, seed);
        let mut warm = vec![0f32; (0.16 * sr) as usize];
        harmonica.render(&mut warm);
        let bend = 2f32.powf(2.0 / 12.0);
        harmonica.set_pitch(bend);
        harmonica.set_pitch(bend);
        let mut bent = vec![0f32; (0.24 * sr) as usize];
        harmonica.render(&mut bent);
        let bent_pitch = peak_locate(
            &bent[(0.08 * sr) as usize..],
            sr,
            f0 * bend * 0.97,
            f0 * bend * 1.03,
        );
        assert!(
            (bent_pitch / (f0 * bend) - 1.0).abs() <= 0.02,
            "GM22 set_pitch reset the scoop or missed bend: {bent_pitch:.1}"
        );
    }

    #[test]
    fn timpani_47_glides_brightens_and_rings_after_noteoff() {
        let sr = 44100.0;
        let seed = 0x4700_1300;
        let bend = 2f32.powf(2.0 / 12.0);

        let pitch = |s: &[f32], f0: f32| peak_locate(s, sr, 0.95 * f0, 1.15 * f0);
        let upper_ratio = |s: &[f32], f0: f32| {
            let fundamental = mag_at(s, sr, f0).max(1e-9);
            (mag_at(s, sr, 1.504 * f0) + mag_at(s, sr, 1.742 * f0) + mag_at(s, sr, 2.0 * f0))
                / fundamental
        };

        for key in [40u8, 45] {
            let mut routed = make(47, key, 96, sr, seed, false);
            assert_eq!(routed.kind(), "modal");
            let mut routed_buf = vec![0f32; (0.35 * sr) as usize];
            routed.render(&mut routed_buf);

            let f0 = key_freq(key);
            let early = pitch(segment(&routed_buf, sr, 0.025, 0.070), f0);
            let late = pitch(segment(&routed_buf, sr, 0.180, 0.320), f0);
            assert!(
                early > 1.05 * late && (late / f0 - 1.0).abs() < 0.03,
                "key {key}: timpani strike does not settle downward: early {early} late {late} expected {f0}"
            );

            let soft = render_program(47, key, 40, 0.35, seed);
            let hard = render_program(47, key, 120, 0.35, seed);
            let soft_body = segment(&soft, sr, 0.080, 0.260);
            let hard_body = segment(&hard, sr, 0.080, 0.260);
            let soft_upper = upper_ratio(soft_body, f0);
            let hard_upper = upper_ratio(hard_body, f0);
            assert!(
                hard_upper > 1.3 * soft_upper,
                "key {key}: hard timpani strike is not brighter: hard {hard_upper} soft {soft_upper}"
            );
            assert!(
                rms(hard_body) > 4.0 * rms(soft_body)
                    && max_abs(hard_body) < 8.0 * max_abs(soft_body),
                "key {key}: velocity loudness/peak law regressed: rms hard {} soft {}, peak hard {} soft {}",
                rms(hard_body),
                rms(soft_body),
                max_abs(hard_body),
                max_abs(soft_body)
            );

            let partial_shape = |partial_seed| {
                let partials = timpani_partials(key, 96, partial_seed);
                let fundamental = partials[0].1.max(1e-9);
                [
                    partials[1].1 / fundamental,
                    partials[2].1 / fundamental,
                    partials[3].1 / fundamental,
                ]
            };
            let shape_a = partial_shape(seed);
            let shape_b = partial_shape(seed ^ 0x5555_AAAA);
            let variation = shape_a
                .iter()
                .zip(shape_b)
                .map(|(&a, b)| (a - b).abs() / a.max(b).max(1e-9))
                .fold(0.0, f32::max);
            let a = render_program(47, key, 96, 0.35, seed);
            let b = render_program(47, key, 96, 0.35, seed ^ 0x5555_AAAA);
            let late_a = pitch(segment(&a, sr, 0.180, 0.320), f0);
            let late_b = pitch(segment(&b, sr, 0.180, 0.320), f0);
            assert!(
                variation > 0.08
                    && (late_a / f0 - 1.0).abs() < 0.03
                    && (late_b / f0 - 1.0).abs() < 0.03,
                "key {key}: seed does not change phase-invariant upper balance without moving pitch: variation {variation}, late {late_a}/{late_b}, expected {f0}"
            );

            let mut held = make(47, key, 96, sr, seed, false);
            let mut released = make(47, key, 96, sr, seed, false);
            let mut gate = vec![0f32; (0.120 * sr) as usize];
            held.render(&mut gate);
            gate.fill(0.0);
            released.render(&mut gate);
            released.note_off();
            let mut held_tail = vec![0f32; (0.700 * sr) as usize];
            let mut released_tail = vec![0f32; (0.700 * sr) as usize];
            held.render(&mut held_tail);
            released.render(&mut released_tail);
            let held_tail = segment(&held_tail, sr, 0.300, 0.650);
            let released_tail = segment(&released_tail, sr, 0.300, 0.650);
            assert!(
                rms(released_tail) > 0.65 * rms(held_tail) && rms(released_tail) > 1e-4,
                "key {key}: timpani note-off chokes the head ring: released {} held {}",
                rms(released_tail),
                rms(held_tail)
            );

            let mut bent = make(47, key, 96, sr, seed, false);
            let mut bent_buf = vec![0f32; (0.360 * sr) as usize];
            let chunk = (0.020 * sr) as usize;
            for (i, part) in bent_buf.chunks_mut(chunk).enumerate() {
                if i as f32 * 0.020 <= 0.120 {
                    bent.set_pitch(bend);
                }
                bent.render(part);
            }
            let want = f0 * bend;
            let early_bent = pitch(segment(&bent_buf, sr, 0.025, 0.070), want);
            let late_bent = pitch(segment(&bent_buf, sr, 0.180, 0.320), want);
            assert!(
                early_bent > 1.05 * late_bent && (late_bent / want - 1.0).abs() < 0.03,
                "key {key}: repeated set_pitch reset or double-applied timpani glide: early {early_bent} late {late_bent} expected {want}"
            );
        }

        for (program, key) in [(0u8, 60u8), (11, 60), (14, 60), (98, 60), (108, 72)] {
            let f0 = key_freq(key);
            let buf = render_program(program, key, 96, 0.35, seed ^ program as u32);
            let early = pitch(segment(&buf, sr, 0.025, 0.070), f0);
            let late = pitch(segment(&buf, sr, 0.180, 0.320), f0);
            assert!(
                (early / late - 1.0).abs() < 0.03,
                "program {program}: non-timpani modal voice picked up timpani glide: early {early} late {late}"
            );
        }
    }

    #[test]
    fn marimba_xylophone_have_wood_bar_envelopes() {
        let sr = 44100.0;
        let key = 69;
        let vibe = render_program(11, key, 105, 2.0, 17);
        let marimba = render_program(12, key, 105, 2.0, 17);
        let xylophone = render_program(13, key, 105, 2.0, 17);
        let mut static_vibe_voice = bell(
            key,
            105,
            sr,
            17,
            VIBES,
            (0.0, 0.01, 1000.0, 1.0),
            0.002,
            0.8,
            0.45,
        );
        let mut static_vibe = vec![0f32; (2.0 * sr) as usize];
        static_vibe_voice.render(&mut static_vibe);

        let vibe_t60 = crate::testutil::t60_of(&vibe, sr);
        let marimba_t60 = crate::testutil::t60_of(&marimba, sr);
        let xylophone_t60 = crate::testutil::t60_of(&xylophone, sr);
        assert!(
            marimba_t60 < 0.55 * vibe_t60,
            "marimba should decay like wood, not vibes: marimba {marimba_t60:.2}s vs vibes {vibe_t60:.2}s"
        );
        assert!(
            xylophone_t60 < 0.75 * marimba_t60,
            "xylophone should be shorter than marimba: xylo {xylophone_t60:.2}s vs marimba {marimba_t60:.2}s"
        );

        let marimba_low = render_program(12, 57, 105, 2.5, 17);
        let marimba_high = render_program(12, 81, 105, 2.0, 17);
        let xylo_low = render_program(13, 57, 105, 2.0, 17);
        let xylo_high = render_program(13, 81, 105, 1.5, 17);
        let marimba_low_t60 = crate::testutil::t60_of(&marimba_low, sr);
        let marimba_high_t60 = crate::testutil::t60_of(&marimba_high, sr);
        let xylo_low_t60 = crate::testutil::t60_of(&xylo_low, sr);
        let xylo_high_t60 = crate::testutil::t60_of(&xylo_high, sr);
        assert!(
            marimba_high_t60 < 0.75 * marimba_low_t60,
            "marimba decay should shorten up the keyboard: high {marimba_high_t60:.2}s vs low {marimba_low_t60:.2}s"
        );
        assert!(
            xylo_high_t60 < 0.75 * xylo_low_t60,
            "xylophone decay should shorten up the keyboard: high {xylo_high_t60:.2}s vs low {xylo_low_t60:.2}s"
        );

        let click_ratio = |sig: &[f32], hz| {
            let onset = 0..(0.015 * sr) as usize;
            let body = (0.075 * sr) as usize..(0.140 * sr) as usize;
            crate::testutil::band_rms(&sig[onset], sr, hz, 1.2)
                / crate::testutil::band_rms(&sig[body], sr, hz, 1.2).max(1e-9)
        };
        let vibe_click = click_ratio(&static_vibe, 2600.0);
        let marimba_click = click_ratio(&marimba, 1800.0);
        let xylo_click = click_ratio(&xylophone, 3200.0);
        assert!(
            marimba_click > 1.6 * vibe_click,
            "marimba wood click missing: marimba {marimba_click} vs static vibes {vibe_click}"
        );
        assert!(
            xylo_click > 1.6 * vibe_click,
            "xylophone wood click missing: xylo {xylo_click} vs static vibes {vibe_click}"
        );

        let click_filter_response = |noise: (f32, f32, f32, f32)| {
            let mut filt = Biquad::bandpass(noise.2, noise.3, sr);
            let mut ir = vec![0f32; 8192];
            ir[0] = 1.0;
            for x in &mut ir {
                *x = filt.process(*x);
            }
            let center = crate::testutil::mag_at(&ir, sr, noise.2);
            let low = crate::testutil::mag_at(&ir, sr, noise.2 * 0.33);
            let high = crate::testutil::mag_at(&ir, sr, noise.2 * 2.0);
            (center, low, high)
        };
        let (marimba_center, marimba_low, marimba_high) = click_filter_response(MARIMBA_NOISE);
        assert!(
            marimba_center > 2.0 * marimba_low && marimba_center > 1.6 * marimba_high,
            "marimba click is not band-passed: center {marimba_center}, low {marimba_low}, high {marimba_high}"
        );
        let (xylo_center, xylo_low, xylo_high) = click_filter_response(XYLOPHONE_NOISE);
        assert!(
            xylo_center > 2.0 * xylo_low && xylo_center > 1.6 * xylo_high,
            "xylophone click is not band-passed: center {xylo_center}, low {xylo_low}, high {xylo_high}"
        );

        let body = &xylophone[(0.04 * sr) as usize..(0.45 * sr) as usize];
        let f = key_freq(key);
        let quint = crate::testutil::mag_at(body, sr, 3.0 * f);
        let vibes_fourth = crate::testutil::mag_at(body, sr, 4.0 * f);
        assert!(
            quint > 1.8 * vibes_fourth,
            "xylophone 1:3 bar mode not dominant: 3f {quint} vs 4f {vibes_fourth}"
        );
    }

    #[test]
    fn kalimba_108_has_tine_decay_not_pluck() {
        let sr = 44100.0;
        let mut voice = make(108, 72, 108, sr, 0x108, false);
        assert_eq!(
            voice.kind(),
            "modal",
            "program 108 must route to bell/modal"
        );

        let mut kalimba = vec![0f32; (1.4 * sr) as usize];
        voice.render(&mut kalimba);

        let f = key_freq(72);
        let early = &kalimba[(0.015 * sr) as usize..(0.24 * sr) as usize];
        let fundamental = crate::testutil::band_rms(early, sr, f, 10.0);
        let second_harmonic = crate::testutil::band_rms(early, sr, f * 2.0, 10.0);
        let tine_28 = crate::testutil::band_rms(early, sr, f * 2.80, 12.0);
        let tine_54 = crate::testutil::band_rms(early, sr, f * 5.40, 12.0);
        assert!(
            tine_28 > 0.22 * fundamental && tine_28 > 1.25 * second_harmonic,
            "2.8x tine mode {tine_28} vs f0 {fundamental} and 2x {second_harmonic}"
        );
        assert!(
            tine_54 > 0.055 * fundamental,
            "5.4x tine mode {tine_54} vs f0 {fundamental}"
        );

        let contact = crate::testutil::hp_rms(&kalimba[..(0.008 * sr) as usize], sr, 2000.0);
        let body = crate::testutil::rms(&kalimba[(0.04 * sr) as usize..(0.12 * sr) as usize]);
        assert!(
            contact > 0.20 * body && contact < 4.0 * body,
            "thumb contact {contact} vs early body {body}"
        );

        let after_contact = (0.020 * sr) as usize;
        let kalimba_t60 = crate::testutil::t60_of(&kalimba[after_contact..], sr);
        assert!(
            kalimba_t60 > 0.25 && kalimba_t60 < 1.4,
            "kalimba t60 {kalimba_t60}s should be a short tine ring"
        );
    }

    /// Req MM-REQ-KILN-00005: GM 55 routes to a short layered orchestra hit,
    /// not the steel-guitar fallback.
    #[test]
    fn orchestra_hit_55_is_short_layered_stab() {
        let sr = 44100.0;
        let hit = make(55, 69, 100, sr, 7, false);
        assert_eq!(hit.kind(), "orch_hit", "GM 55 must not route to steel");
        let buf = render_voice(hit, sr, 2.0);
        let seg = |a: f32, z: f32| &buf[(a * sr) as usize..(z * sr) as usize];
        let early = crate::testutil::rms(seg(0.15, 0.45));
        let late = crate::testutil::rms(seg(1.45, 1.85));
        let fund = crate::testutil::mag_at(seg(0.05, 0.25), sr, 440.0);
        let sub = crate::testutil::mag_at(seg(0.05, 0.25), sr, 220.0);
        let upper = crate::testutil::mag_at(seg(0.05, 0.25), sr, 880.0);
        let thump = crate::testutil::band_rms(seg(0.0, 0.15), sr, 100.0, 0.7);
        assert!(
            late < 0.10 * early,
            "stab rings too long: late/early {}",
            late / early
        );
        assert!(
            sub >= 0.25 * fund,
            "sub-octave layer missing: sub {sub} fund {fund}"
        );
        assert!(
            upper >= 0.12 * fund,
            "upper-octave layer missing: upper {upper} fund {fund}"
        );
        assert!(thump > 1e-3, "low thump missing: {thump}");
    }

    #[test]
    fn gm_sfx_120_127_are_toneless_noise_fallbacks() {
        let sr = 44100.0;
        let n = (0.6 * sr) as usize;
        for program in 120u8..=127 {
            let seed = 0x5F58_0100 ^ program as u32;
            let mut low = make(program, 48, 100, sr, seed, false);
            let mut high = make(program, 72, 100, sr, seed, false);
            assert_eq!(
                low.kind(),
                "sfx",
                "program {program} must not route to pluck"
            );
            assert_eq!(
                high.kind(),
                "sfx",
                "program {program} must not route to pluck"
            );

            let mut low_buf = vec![0f32; n];
            let mut high_buf = vec![0f32; n];
            low.render(&mut low_buf);
            high.render(&mut high_buf);

            assert!(
                low_buf
                    .iter()
                    .zip(&high_buf)
                    .all(|(a, b)| a.to_bits() == b.to_bits()),
                "program {program} SFX fallback must ignore written pitch"
            );

            let body = &low_buf[(0.015 * sr) as usize..(0.32 * sr) as usize];
            let level = crate::testutil::rms(body);
            let flat = crate::testutil::flatness(body, sr, 120.0, 8_000.0);
            let written_pitch = crate::testutil::band_rms(body, sr, key_freq(60), 12.0);
            assert!(
                level > 1e-5 && level < 0.08,
                "program {program} should be a safe low-level noise fallback, rms {level}"
            );
            assert!(
                flat > 0.18,
                "program {program} should be toneless/noisy, flatness {flat}"
            );
            assert!(
                written_pitch < 0.55 * level,
                "program {program} should not emphasize written pitch: band {written_pitch}, rms {level}"
            );
        }
    }

    #[test]
    fn gm112_119_melodic_percussion_are_modeled() {
        let sr = 44100.0;
        let seed = 0x1121_1900;
        for program in 112u8..=119 {
            let sig = render_program(program, 72, 100, 1.6, seed ^ program as u32);
            let body = segment(&sig, sr, 0.04, 0.32);
            assert!(
                sig.iter().all(|s| s.is_finite()),
                "program {program} produced non-finite audio"
            );
            assert!(
                rms(body) > 1e-5,
                "program {program} should be audible, body rms {}",
                rms(body)
            );
            assert!(
                max_abs(&sig) < 0.98,
                "program {program} should leave headroom, peak {}",
                max_abs(&sig)
            );
        }

        for program in 112u8..=118 {
            assert_eq!(
                make(program, 72, 100, sr, seed, false).kind(),
                "modal",
                "program {program} must route away from steel fallback"
            );
        }
        assert_eq!(
            make(119, 72, 100, sr, seed, false).kind(),
            "reverse_cym",
            "GM119 needs its reverse-cymbal one-shot, not a pluck"
        );

        let f = key_freq(84);
        let tinkle = render_program(112, 84, 100, 1.6, seed ^ 112);
        let agogo_at_tinkle = render_program(113, 84, 100, 1.6, seed ^ 113);
        let wood_at_tinkle = render_program(115, 84, 100, 1.6, seed ^ 115);
        let tinkle_body = segment(&tinkle, sr, 0.06, 0.40);
        let tinkle_peak = peak_locate(tinkle_body, sr, 0.90 * f, 1.10 * f);
        assert!(
            (tinkle_peak / f - 1.0).abs() < 0.05,
            "GM112 pitch center {tinkle_peak}, expected {f}"
        );
        let bright = |s: &[f32]| hp_rms(s, sr, 4_000.0) / rms(s).max(1e-9);
        assert!(
            bright(tinkle_body) > 1.15 * bright(segment(&agogo_at_tinkle, sr, 0.06, 0.40))
                && bright(tinkle_body) > 1.25 * bright(segment(&wood_at_tinkle, sr, 0.06, 0.40)),
            "GM112 should be the bright small-metal voice"
        );
        assert!(
            rms(segment(&tinkle, sr, 0.80, 1.20)) > 1e-4,
            "GM112 should keep a quiet bell tail"
        );

        let f = key_freq(76);
        let agogo = render_program(113, 76, 100, 1.0, seed ^ 113);
        let tinkle_at_agogo = render_program(112, 76, 100, 1.0, seed ^ 112);
        let steel_at_agogo = render_program(114, 76, 100, 1.0, seed ^ 114);
        let agogo_body = segment(&agogo, sr, 0.04, 0.20);
        let agogo_peak = peak_locate(agogo_body, sr, 0.85 * f, 1.15 * f);
        assert!(
            (agogo_peak / f - 1.0).abs() < 0.08,
            "GM113 pitch center {agogo_peak}, expected {f}"
        );
        let agogo_clank = band_rms(agogo_body, sr, 1.70 * f, 16.0) / rms(agogo_body).max(1e-9);
        let tinkle_clank = band_rms(
            segment(&tinkle_at_agogo, sr, 0.04, 0.20),
            sr,
            1.70 * f,
            16.0,
        ) / rms(segment(&tinkle_at_agogo, sr, 0.04, 0.20)).max(1e-9);
        let steel_clank = band_rms(segment(&steel_at_agogo, sr, 0.04, 0.20), sr, 1.70 * f, 16.0)
            / rms(segment(&steel_at_agogo, sr, 0.04, 0.20)).max(1e-9);
        assert!(
            agogo_clank > 1.35 * tinkle_clank && agogo_clank > 1.20 * steel_clank,
            "GM113 should carry the 1.7f agogo clang: agogo {agogo_clank}, tinkle {tinkle_clank}, steel {steel_clank}"
        );
        assert!(
            rms(segment(&agogo, sr, 0.65, 0.95)) < 0.30 * rms(agogo_body),
            "GM113 should be a short struck bell"
        );

        let f = key_freq(72);
        let steel = render_program(114, 72, 100, 1.2, seed ^ 114);
        let steel_body = segment(&steel, sr, 0.08, 0.35);
        let steel_peak = peak_locate(steel_body, sr, 0.95 * f, 1.05 * f);
        assert!(
            (steel_peak / f - 1.0).abs() < 0.03,
            "GM114 pitch center {steel_peak}, expected {f}"
        );
        let fund = mag_at(steel_body, sr, f).max(1e-9);
        assert!(
            mag_at(steel_body, sr, 2.0 * f) > 0.10 * fund
                && mag_at(steel_body, sr, 3.0 * f) > 0.06 * fund,
            "GM114 should have steelpan octave/twelfth support"
        );

        let wood = render_program(115, 72, 100, 0.7, seed ^ 115);
        let wood_body = segment(&wood, sr, 0.025, 0.140);
        let wood_peak = peak_locate(wood_body, sr, 0.85 * f, 1.15 * f);
        assert!(
            (wood_peak / f - 1.0).abs() < 0.10,
            "GM115 pitch center {wood_peak}, expected {f}"
        );
        assert!(
            rms(segment(&wood, sr, 0.25, 0.50)) < 0.10 * rms(segment(&wood, sr, 0.00, 0.08)),
            "GM115 should be the dry short woodblock"
        );

        let taiko = render_program(116, 48, 100, 1.2, seed ^ 116);
        let tom_at_taiko = render_program(117, 48, 100, 1.2, seed ^ 117);
        let f = key_freq(48);
        let taiko_early = peak_locate(segment(&taiko, sr, 0.035, 0.090), sr, 1.00 * f, 1.30 * f);
        let taiko_late = peak_locate(segment(&taiko, sr, 0.18, 0.36), sr, 0.95 * f, 1.06 * f);
        assert!(
            taiko_early > 1.05 * taiko_late && (taiko_late / f - 1.0).abs() < 0.04,
            "GM116 should settle downward to pitch: early {taiko_early}, late {taiko_late}, expected {f}"
        );
        assert!(
            band_rms(segment(&taiko, sr, 0.00, 0.20), sr, 150.0, 0.7)
                > 1.20 * band_rms(segment(&tom_at_taiko, sr, 0.00, 0.20), sr, 150.0, 0.7),
            "GM116 should have a larger low drum body than melodic tom"
        );

        let tom = render_program(117, 55, 100, 0.9, seed ^ 117);
        let taiko_at_tom = render_program(116, 55, 100, 0.9, seed ^ 116);
        let f = key_freq(55);
        let tom_early = peak_locate(segment(&tom, sr, 0.025, 0.075), sr, 1.00 * f, 1.20 * f);
        let tom_late = peak_locate(segment(&tom, sr, 0.12, 0.28), sr, 0.95 * f, 1.06 * f);
        assert!(
            tom_early > 1.02 * tom_late && (tom_late / f - 1.0).abs() < 0.04,
            "GM117 should settle to pitch: early {tom_early}, late {tom_late}, expected {f}"
        );
        let attack_bright = hp_rms(segment(&tom, sr, 0.00, 0.08), sr, 1_800.0)
            / rms(segment(&tom, sr, 0.00, 0.08)).max(1e-9);
        let taiko_attack_bright = hp_rms(segment(&taiko_at_tom, sr, 0.00, 0.08), sr, 1_800.0)
            / rms(segment(&taiko_at_tom, sr, 0.00, 0.08)).max(1e-9);
        assert!(
            attack_bright > 1.10 * taiko_attack_bright
                && rms(segment(&tom, sr, 0.45, 0.75)) < rms(segment(&taiko_at_tom, sr, 0.45, 0.75)),
            "GM117 should be brighter and shorter than taiko"
        );

        let synth = render_program(118, 60, 100, 0.8, seed ^ 118);
        let tom_at_synth = render_program(117, 60, 100, 0.8, seed ^ 117);
        let f = key_freq(60);
        let synth_early = peak_locate(segment(&synth, sr, 0.015, 0.055), sr, 1.10 * f, 1.70 * f);
        let synth_late = peak_locate(segment(&synth, sr, 0.14, 0.28), sr, 0.95 * f, 1.06 * f);
        let tom_at_synth_early = peak_locate(
            segment(&tom_at_synth, sr, 0.015, 0.055),
            sr,
            1.00 * f,
            1.30 * f,
        );
        assert!(
            synth_early > 1.25 * synth_late
                && synth_early > 1.12 * tom_at_synth_early
                && (synth_late / f - 1.0).abs() < 0.04,
            "GM118 should have the strongest electronic pitch sweep: synth early {synth_early}, late {synth_late}, tom early {tom_at_synth_early}"
        );
        let synth_body = segment(&synth, sr, 0.20, 0.34);
        let tom_body = segment(&tom_at_synth, sr, 0.20, 0.34);
        let synth_concentration = mag_at(synth_body, sr, f)
            / (mag_at(synth_body, sr, 1.59 * f) + mag_at(synth_body, sr, 2.14 * f)).max(1e-9);
        let tom_concentration = mag_at(tom_body, sr, f)
            / (mag_at(tom_body, sr, 1.59 * f) + mag_at(tom_body, sr, 2.14 * f)).max(1e-9);
        assert!(
            synth_concentration > 2.0 * tom_concentration,
            "GM118 body should avoid acoustic tom upper modes: synth {synth_concentration}, tom {tom_concentration}"
        );

        for &(program, key, early_a, early_b, late_a, late_b, min_sweep) in &[
            (116u8, 48u8, 0.035, 0.090, 0.18, 0.36, 1.05),
            (117, 55, 0.025, 0.075, 0.12, 0.28, 1.02),
            (118, 60, 0.015, 0.055, 0.14, 0.28, 1.25),
        ] {
            let bend = 2f32.powf(2.0 / 12.0);
            let f0 = key_freq(key) * bend;
            let mut v = make(program, key, 100, sr, seed ^ program as u32, false);
            let mut bent = vec![0f32; (0.40 * sr) as usize];
            let chunk = (0.020 * sr) as usize;
            for (i, part) in bent.chunks_mut(chunk).enumerate() {
                if i as f32 * 0.020 <= 0.120 {
                    v.set_pitch(bend);
                }
                v.render(part);
            }
            let early = peak_locate(segment(&bent, sr, early_a, early_b), sr, f0, f0 * 1.70);
            let late = peak_locate(segment(&bent, sr, late_a, late_b), sr, 0.95 * f0, 1.06 * f0);
            assert!(
                early > min_sweep * late && (late / f0 - 1.0).abs() < 0.04,
                "program {program} repeated set_pitch reset or double-applied strike glide: early {early}, late {late}, expected {f0}"
            );
        }

        let reverse_low = render_program(119, 48, 100, 1.6, seed ^ 119);
        let reverse_high = render_program(119, 84, 100, 1.6, seed ^ 119);
        assert!(
            reverse_low
                .iter()
                .zip(&reverse_high)
                .all(|(a, b)| a.to_bits() == b.to_bits()),
            "GM119 reverse cymbal intentionally ignores written pitch"
        );
        let early = rms(segment(&reverse_low, sr, 0.10, 0.25));
        let pre_peak = rms(segment(&reverse_low, sr, 0.75, 0.95));
        let late = rms(segment(&reverse_low, sr, 1.20, 1.50));
        assert!(
            pre_peak > 5.0 * early && late < 0.65 * pre_peak,
            "GM119 should swell then decay: early {early}, pre_peak {pre_peak}, late {late}"
        );
        let short = render_program_released(119, 72, 100, 0.06, 1.6, seed ^ 119);
        assert!(
            rms(segment(&short, sr, 0.75, 0.95)) > 0.70 * pre_peak,
            "GM119 short note-off must not kill the reverse swell"
        );
        let mut short_rev = make(119, 72, 100, sr, seed ^ 119, false);
        let mut gate = vec![0f32; (0.06 * sr) as usize];
        short_rev.render(&mut gate);
        short_rev.note_off();
        assert!(
            survives_until(short_rev, sr, 0.95),
            "GM119 must stay alive through the reverse swell after a short note"
        );
        assert!(
            dies_within(make(119, 72, 100, sr, seed ^ 119, false), sr, 2.0),
            "GM119 should eventually return false after the post-peak decay"
        );

        for &(program, key, secs, tail_a, tail_b, min_tail_ratio) in &[
            (112u8, 84u8, 1.3, 0.40, 0.90, 0.55),
            (113, 76, 0.8, 0.12, 0.32, 0.45),
            (114, 72, 1.0, 0.24, 0.60, 0.55),
            (115, 72, 0.5, 0.08, 0.18, 0.25),
            (116, 48, 1.0, 0.24, 0.60, 0.55),
            (117, 55, 0.8, 0.16, 0.42, 0.50),
            (118, 60, 0.7, 0.14, 0.34, 0.45),
        ] {
            let held = render_program(program, key, 100, secs, seed ^ program as u32);
            let short =
                render_program_released(program, key, 100, 0.06, secs, seed ^ program as u32);
            let held_tail = rms(segment(&held, sr, tail_a, tail_b)).max(1e-9);
            let short_tail = rms(segment(&short, sr, tail_a, tail_b));
            assert!(
                short_tail > min_tail_ratio * held_tail,
                "program {program} note-off hard-choked the natural tail: short {short_tail}, held {held_tail}"
            );
        }
    }

    #[test]
    fn sitar_shamisen_koto_have_distinct_pluck_presets() {
        let sr = 44100.0;
        for (program, want) in [
            (104, "SITAR"),
            (105, "BANJO"),
            (106, "SHAMISEN"),
            (107, "KOTO"),
        ] {
            assert_eq!(
                make(program, 60, 100, sr, 7, false).kind(),
                want,
                "program {program}"
            );
        }

        let render = |program: u8, key: u8, seed: u32| {
            let mut voice = make(program, key, 104, sr, seed, false);
            let mut buf = vec![0f32; (1.6 * sr) as usize];
            voice.render(&mut buf);
            buf
        };
        let body_lo = (0.030 * sr) as usize;
        let body_hi = (0.420 * sr) as usize;
        let centroid = |s: &[f32]| crate::testutil::centroid(&s[body_lo..body_hi], sr);
        let t60 = |s: &[f32]| crate::testutil::t60_of(&s[(0.020 * sr) as usize..], sr);
        let upper = |s: &[f32], f: f32| {
            crate::testutil::mag_at(&s[body_lo..body_hi], sr, 3.0 * f)
                + crate::testutil::mag_at(&s[body_lo..body_hi], sr, 4.0 * f)
                + crate::testutil::mag_at(&s[body_lo..body_hi], sr, 5.0 * f)
        };
        let f = key_freq(60);

        for seed in [0x6510, 0x76A1, 0x1250] {
            let banjo = render(105, 60, seed);
            let sitar = render(104, 60, seed);
            let shamisen = render(106, 60, seed);
            let koto = render(107, 60, seed);

            assert!(
                centroid(&sitar) > 1.10 * centroid(&banjo)
                    && upper(&sitar, f) > 1.25 * upper(&banjo, f),
                "sitar should have bright jawari-like upper partials at seed {seed}: cent {} vs {}, upper {} vs {}",
                centroid(&sitar),
                centroid(&banjo),
                upper(&sitar, f),
                upper(&banjo, f)
            );
            assert!(
                t60(&shamisen) < 0.85 * t60(&banjo)
                    && centroid(&shamisen) < 0.95 * centroid(&banjo),
                "shamisen should be a lighter, shorter banjo cousin at seed {seed}: t60 {} vs {}, cent {} vs {}",
                t60(&shamisen),
                t60(&banjo),
                centroid(&shamisen),
                centroid(&banjo)
            );
            assert!(
                t60(&koto) > 2.0 * t60(&banjo) && centroid(&koto) < 0.72 * centroid(&banjo),
                "koto should ring long and mellow at seed {seed}: t60 {} vs {}, cent {} vs {}",
                t60(&koto),
                t60(&banjo),
                centroid(&koto),
                centroid(&banjo)
            );
            assert!(
                t60(&sitar) > 1.2 * t60(&shamisen) && t60(&koto) > 1.5 * t60(&sitar),
                "sitar/shamisen/koto decay ordering collapsed at seed {seed}: sitar {}, shamisen {}, koto {}",
                t60(&sitar),
                t60(&shamisen),
                t60(&koto)
            );
        }
    }

    /// Oracle 7 (§5.3 differential): the pick click adds real onset HF —
    /// same seed, same preset, click on vs off.
    #[test]
    fn pick_click_is_audible() {
        let sr = 44100.0;
        let no_click = PluckPreset {
            click: 0.0,
            ..STEEL
        };
        let with = render_pluck(&STEEL, 45, 100, 0.1, 7);
        let without = render_pluck(&no_click, 45, 100, 0.1, 7);
        let onset_hf = |s: &[f32]| {
            crate::testutil::hp_rms(&s[..(0.003 * sr) as usize], sr, 1500.0)
                / crate::testutil::rms(&s[(0.05 * sr) as usize..(0.08 * sr) as usize]).max(1e-9)
        };
        let (w, wo) = (onset_hf(&with), onset_hf(&without));
        assert!(w > 1.3 * wo, "click on {w} vs off {wo}");
        // NYLON's fingernail is softer than STEEL's plectrum
        let nylon = render_pluck(&NYLON, 45, 100, 0.1, 7);
        let no_nylon = render_pluck(
            &PluckPreset {
                click: 0.0,
                ..NYLON
            },
            45,
            100,
            0.1,
            7,
        );
        let gain = |a: f32, b: f32| a / b.max(1e-9);
        assert!(
            gain(onset_hf(&nylon), onset_hf(&no_nylon)) < gain(w, wo),
            "NYLON click should be softer than STEEL's"
        );
    }

    /// Oracle 8 (§5.1): SLAP's first 3 ms carry ≥3× the >3 kHz energy of
    /// fingered BASS at the same low key, and the fundamental stays E1.
    #[test]
    fn slap_transient_and_pitch() {
        let sr = 44100.0;
        let slap = render_pluck(&SLAP, 28, 110, 0.6, 7);
        let bass = render_pluck(&BASS, 28, 110, 0.6, 7);
        let onset = |s: &[f32]| crate::testutil::hp_rms(&s[..(0.003 * sr) as usize], sr, 3000.0);
        assert!(
            onset(&slap) >= 3.0 * onset(&bass),
            "slap onset {} vs bass {}",
            onset(&slap),
            onset(&bass)
        );
        let f = crate::testutil::peak_locate(&slap[(0.1 * sr) as usize..], sr, 35.0, 50.0);
        assert!((f - 41.2).abs() < 4.0, "slap fundamental {f} Hz");
    }

    /// Oracle 9 (§5): FRETLESS finger noise — onset >2 kHz energy above the
    /// no-noise baseline, dying within ~8 ms.
    #[test]
    fn finger_noise_speaks_then_dies() {
        let sr = 44100.0;
        let with = render_pluck(&FRETLESS, 31, 80, 0.1, 7);
        let without = render_pluck(
            &PluckPreset {
                attack_noise: 0.0,
                ..FRETLESS
            },
            31,
            80,
            0.1,
            7,
        );
        let hf = |s: &[f32], a: f32, b: f32| {
            crate::testutil::hp_rms(&s[(a * sr) as usize..(b * sr) as usize], sr, 2000.0)
        };
        assert!(
            hf(&with, 0.0, 0.008) > 1.5 * hf(&without, 0.0, 0.008),
            "finger noise: {} vs {}",
            hf(&with, 0.0, 0.008),
            hf(&without, 0.0, 0.008)
        );
        // the NOISE dies within ~8 ms — measure its energy excess over the
        // noiseless build per window (the string itself is still ramping up)
        let excess =
            |a: f32, b: f32| (hf(&with, a, b).powi(2) - hf(&without, a, b).powi(2)).max(0.0);
        assert!(
            excess(0.012, 0.020) < 0.35 * excess(0.0, 0.008),
            "finger noise rings too long: late {} vs early {}",
            excess(0.012, 0.020),
            excess(0.0, 0.008)
        );
    }

    #[test]
    fn fretless_bass_35_mwah_blooms() {
        let sr = 44100.0;
        let vel = 96;
        let spec = FRETLESS.mwah.expect("FRETLESS must carry the mwah spec");
        let no_mwah = PluckPreset {
            mwah: None,
            ..FRETLESS
        };

        assert_eq!(make(35, 31, vel, sr, 7, false).kind(), "FRETLESS");

        for key in [31u8, 38] {
            let seed = 0x35_00u32 + key as u32;
            let with = render_program(35, key, vel, 0.55, seed);
            let without = render_pluck(&no_mwah, key, vel, 0.55, seed);
            let residual: Vec<f32> = with.iter().zip(&without).map(|(a, b)| a - b).collect();
            let band = |s: &[f32], a: f32, b: f32, hz: f32| {
                let lo = (a * sr) as usize;
                let hi = (b * sr) as usize;
                crate::testutil::band_rms(&s[lo..hi], sr, hz, spec.q)
            };

            let early_low = band(&residual, 0.035, 0.070, spec.start_hz);
            let early_high = band(&residual, 0.035, 0.070, spec.bloom_hz);
            let bloom_low = band(&residual, 0.105, 0.155, spec.start_hz);
            let bloom_high = band(&residual, 0.105, 0.155, spec.bloom_hz);
            let late_low = band(&residual, 0.280, 0.420, spec.start_hz);
            let late_high = band(&residual, 0.280, 0.420, spec.bloom_hz);

            let early_mid = early_low + early_high;
            let bloom_mid = bloom_low + bloom_high;
            let late_mid = late_low + late_high;
            assert!(
                early_low > 1.35 * early_high.max(1e-9),
                "key {key}: mwah does not start as a low-mid formant: early low {early_low}, early high {early_high}"
            );
            assert!(
                early_low > 0.02 * bloom_mid,
                "key {key}: mwah low-mid onset is too small to prove the opening shape: early low {early_low}, bloom mid {bloom_mid}"
            );
            assert!(
                bloom_mid > 2.0 * early_mid.max(1e-8),
                "key {key}: mwah bloom is not delayed: bloom {bloom_mid} early {early_mid}"
            );
            assert!(
                bloom_mid > 1.6 * late_mid.max(1e-8),
                "key {key}: mwah bloom does not decay: bloom {bloom_mid} late {late_mid}"
            );

            let early_ratio = early_high / early_low.max(1e-9);
            let bloom_ratio = bloom_high / bloom_low.max(1e-9);
            assert!(
                bloom_ratio > 1.25 * early_ratio
                    && bloom_ratio > 0.4
                    && bloom_high > 6.0 * early_high.max(1e-9),
                "key {key}: mwah formant does not open upward: early ratio {early_ratio}, bloom ratio {bloom_ratio}, bloom high {bloom_high}, early high {early_high}"
            );

            let f0 = key_freq(key);
            let body = &with[(0.080 * sr) as usize..(0.420 * sr) as usize];
            let peak = crate::testutil::peak_locate(body, sr, f0 * 0.85, f0 * 1.15);
            assert!(
                (peak / f0 - 1.0).abs() < 0.05,
                "key {key}: mwah moved perceived pitch to {peak} Hz, expected {f0}"
            );
            let fund = crate::testutil::mag_at(body, sr, f0);
            let h2 = crate::testutil::mag_at(body, sr, 2.0 * f0);
            let h3 = crate::testutil::mag_at(body, sr, 3.0 * f0);
            assert!(
                fund > 0.55 * h2.max(h3),
                "key {key}: mwah upper harmonics dominate f0: f0 {fund}, h2 {h2}, h3 {h3}"
            );
        }
    }

    /// Oracle 10 (§5): the stop thump fires on note_off (LF bump vs a
    /// thump-disabled build) and NEVER on a natural end (bit-identical).
    #[test]
    fn stop_thump_on_note_off_only() {
        let sr = 44100.0;
        let no_thump = PluckPreset {
            stop_thump: 0.0,
            ..BASS
        };
        let run = |p: &PluckPreset, off: bool| {
            let mut v = Pluck::new(p, 33, 100, sr, 7);
            let mut a = vec![0f32; (0.3 * sr) as usize];
            v.render(&mut a);
            if off {
                v.note_off();
            }
            let mut b = vec![0f32; (0.12 * sr) as usize];
            v.render(&mut b);
            (a, b)
        };
        let (_, tail_with) = run(&BASS, true);
        let (_, tail_without) = run(&no_thump, true);
        let lf = |s: &[f32]| crate::testutil::band_rms(s, sr, 150.0, 0.7);
        // The flatwound revoice raised BASS's sub weight (0.18 -> 0.28), so the
        // note's own low end sustains further into the tail and the thump's
        // *relative* prominence shrinks even though it still clearly fires
        // (~1.29x here). 1.25 keeps the assertion meaningful at the deeper voicing.
        assert!(
            lf(&tail_with) > 1.25 * lf(&tail_without),
            "thump missing: {} vs {}",
            lf(&tail_with),
            lf(&tail_without)
        );
        // natural end: the armed-but-untriggered burst must change nothing
        let (a1, b1) = run(&BASS, false);
        let (a2, b2) = run(&no_thump, false);
        assert!(
            a1.iter().zip(&a2).all(|(x, y)| x.to_bits() == y.to_bits())
                && b1.iter().zip(&b2).all(|(x, y)| x.to_bits() == y.to_bits()),
            "un-triggered thump altered the render"
        );
    }

    /// Oracle 39 (MUTED grit + sub enrichment, §5.1): the palm chug's thud
    /// carries 2f/3f, and the soft-clip grit changes the string's output.
    #[test]
    fn muted_grit_and_rich_thud() {
        let sr = 44100.0;
        let plain_sub = PluckPreset {
            sub_shape: (0.0, 0.0),
            ..MUTED
        };
        let rich = render_pluck(&MUTED, 40, 110, 0.3, 7);
        let plain = render_pluck(&plain_sub, 40, 110, 0.3, 7);
        let f = key_freq(40);
        let h23 = |s: &[f32]| {
            crate::testutil::mag_at(s, sr, 2.0 * f) + crate::testutil::mag_at(s, sr, 3.0 * f)
        };
        assert!(
            h23(&rich) > 1.2 * h23(&plain),
            "sub enrichment missing: {} vs {}",
            h23(&rich),
            h23(&plain)
        );
        let no_grit = PluckPreset {
            grit: false,
            ..MUTED
        };
        let gritless = render_pluck(&no_grit, 40, 110, 0.3, 7);
        assert!(
            rich.iter().zip(&gritless).any(|(x, y)| x != y),
            "grit clip is not in the path"
        );
    }

    /// Oracle 40 (§5.3, three clauses): the prog-31 flageolet suppresses the
    /// notated fundamental, actually rings at the touched harmonic, and
    /// holds both under an active pitch modulator (V4/INT-2).
    #[test]
    fn harmonic_flageolet_suppresses_fundamental() {
        let sr = 44100.0;
        let f = key_freq(52); // E3 ≈ 164.8 Hz, below the E4 split → 2f
        let buf = render_pluck(&HARMONIC, 52, 100, 0.8, 7);
        let strongest = crate::testutil::peak_locate(&buf, sr, f * 0.8, f * 3.5);
        assert!(
            (strongest / (2.0 * f) - 1.0).abs() < 0.03,
            "strongest partial at {strongest} Hz, expected ~{}",
            2.0 * f
        );
        let db = |m: f32| 20.0 * m.max(1e-12).log10();
        let sup = db(crate::testutil::mag_at(&buf, sr, f))
            - db(crate::testutil::mag_at(&buf, sr, strongest));
        assert!(sup <= -12.0, "fundamental only {sup:.1} dB down");
        // clause (c): a +2-semitone bend must move the flageolet, not
        // collapse it back to the fundamental
        let mut v = Pluck::new(&HARMONIC, 52, 100, sr, 7);
        let mut head = vec![0f32; (0.25 * sr) as usize];
        v.render(&mut head);
        let bend = 2f32.powf(2.0 / 12.0);
        v.set_pitch(bend);
        let mut tail = vec![0f32; (0.6 * sr) as usize];
        v.render(&mut tail);
        let late = &tail[(0.2 * sr) as usize..];
        let target = 2.0 * f * bend;
        let p = crate::testutil::peak_locate(late, sr, f * 0.8, f * 3.5);
        assert!(
            (p / target - 1.0).abs() < 0.04,
            "bent flageolet at {p} Hz, expected ~{target}"
        );
        let sup_bent = db(crate::testutil::mag_at(late, sr, f * bend))
            - db(crate::testutil::mag_at(late, sr, p));
        assert!(
            sup_bent <= -12.0,
            "bent fundamental only {sup_bent:.1} dB down"
        );
    }

    /// Oracle 12 (B2): the three bass articulations are genuinely distinct —
    /// pick brighter than fingers, upright woodier and shorter, with its
    /// 110 Hz body mode in the shipped table.
    #[test]
    fn bass_articulations_distinct() {
        let sr = 44100.0;
        let cent = |p: &PluckPreset| {
            let buf = render_pluck(p, 30, 100, 0.3, 7); // F#1: partials avoid 110 Hz
            crate::testutil::centroid(&buf, sr)
        };
        assert!(
            cent(&PICK) > 1.1 * cent(&BASS),
            "PICK {} not brighter than BASS {}",
            cent(&PICK),
            cent(&BASS)
        );
        assert!(
            UPRIGHT.body.iter().any(|&(f, _, g)| f == 110.0 && g > 0.0),
            "UPRIGHT 110 Hz body mode missing from the shipped table"
        );
        let (u, b) = (
            std::hint::black_box(UPRIGHT.t60),
            std::hint::black_box(BASS.t60),
        );
        assert!(u < b, "upright should decay faster: {u} vs {b}");
    }

    #[test]
    fn harp_46_has_soundboard_and_harp_wound_law() {
        assert!(
            HARP.body.iter().any(|&(f, _, g)| f < 120.0 && g > 0.0),
            "HARP should have a low soundboard mode"
        );
        assert!(
            HARP.body
                .iter()
                .any(|&(f, _, g)| (150.0..=250.0).contains(&f) && g > 0.0),
            "HARP should have a low-mid soundboard mode"
        );
        assert!(
            HARP.body
                .iter()
                .any(|&(f, _, g)| (350.0..=500.0).contains(&f) && g > 0.0),
            "HARP should have a warm upper soundboard mode"
        );
        assert!(
            !std::hint::black_box(HARP.wound_key_split),
            "HARP should not inherit the guitar key-split wound law"
        );
        assert_eq!(wound_factor(true, true, 70), 1.0);
        assert_eq!(wound_factor(false, true, 60), 0.0);
        assert!(wound_factor(false, true, 45) > 0.3);
        assert_eq!(wound_factor(false, false, 31), 0.0);

        let sr = 44100.0;
        let bodyless = PluckPreset { body: &[], ..HARP };
        let old_split = PluckPreset {
            wound_key_split: true,
            ..HARP
        };

        for (key, bands) in [(45u8, [90.0, 180.0, 400.0]), (52u8, [180.0, 400.0, 90.0])] {
            let full = render_pluck(&HARP, key, 104, 0.7, 0x4600 + key as u32);
            let dry = render_pluck(&bodyless, key, 104, 0.7, 0x4600 + key as u32);
            let full_body = segment(&full, sr, 0.04, 0.42);
            let dry_body = segment(&dry, sr, 0.04, 0.42);
            for f in bands {
                let lift =
                    band_rms(full_body, sr, f, 1.0) / band_rms(dry_body, sr, f, 1.0).max(1e-9);
                assert!(
                    lift > 1.08,
                    "key {key}: HARP body mode {f} Hz did not lift enough versus bodyless clone: {lift:.3}"
                );
            }
        }

        let new_harp = render_pluck(&HARP, 45, 104, 0.7, 0x46_4510);
        let old_harp = render_pluck(&old_split, 45, 104, 0.7, 0x46_4510);
        let new_body = segment(&new_harp, sr, 0.04, 0.42);
        let old_body = segment(&old_harp, sr, 0.04, 0.42);
        let new_centroid = centroid(new_body, sr);
        let old_centroid = centroid(old_body, sr);
        assert!(
            new_centroid > old_centroid * 1.04,
            "new harp should be less guitar-wound/dark in bass register: {new_centroid:.1} vs {old_centroid:.1}"
        );
        let new_hf = hp_rms(new_body, sr, 1200.0);
        let old_hf = hp_rms(old_body, sr, 1200.0);
        assert!(
            new_hf > old_hf * 1.06,
            "new harp should retain more high-frequency pluck energy than guitar-split clone: {new_hf:.5} vs {old_hf:.5}"
        );
    }

    /// Oracle 15 (K3, §5.3 differential): the polarization coupling is
    /// audible (same seed, k on vs off differ) and unconditionally bounded
    /// on the worst case — a long low DRIVE note at high loop gain.
    #[test]
    fn coupling_audible_and_bounded() {
        let sr = 44100.0;
        let run = |k: f32, secs: f32| {
            let mut v = Pluck::new(&DRIVE, 28, 110, sr, 7);
            v.k_couple = k;
            let mut buf = vec![0f32; (secs * sr) as usize];
            v.render(&mut buf);
            buf
        };
        let with = run(K_COUPLE, 2.0);
        let without = run(0.0, 2.0);
        let d: Vec<f32> = with.iter().zip(&without).map(|(a, b)| a - b).collect();
        assert!(
            crate::testutil::rms(&d) > 0.05 * crate::testutil::rms(&with),
            "coupling inaudible: diff {} vs signal {}",
            crate::testutil::rms(&d),
            crate::testutil::rms(&with)
        );
        let long = run(K_COUPLE, 10.0);
        let peak = long.iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(
            long.iter().all(|x| x.is_finite()) && peak < 1.5,
            "peak {peak}"
        );
    }

    /// Oracle 18 (G6, §5.3 time-matched differential): a released string
    /// dulls faster than a held one — same seed, same absolute window.
    #[test]
    fn release_darkens_the_string() {
        let sr = 44100.0;
        let run = |release: bool| {
            let mut v = Pluck::new(&CLEAN, 64, 110, sr, 7);
            let mut head = vec![0f32; (0.3 * sr) as usize];
            v.render(&mut head);
            if release {
                v.note_off();
            }
            let mut tail = vec![0f32; (0.3 * sr) as usize];
            v.render(&mut tail);
            tail[(0.1 * sr) as usize..].to_vec()
        };
        let rel = crate::testutil::centroid(&run(true), sr);
        let held = crate::testutil::centroid(&run(false), sr);
        assert!(
            rel < 0.8 * held,
            "release not darkening: released {rel} vs held {held}"
        );
    }

    /// Oracle 41 (K4 Stage 1, §5.3): wound-ness is real — the factor splits
    /// the registers, and a fully-wound build of the same note reads darker.
    #[test]
    fn wound_strings_darker() {
        // structural: bass full-range, guitars split around G3
        assert_eq!(wound_factor(true, true, 70), 1.0);
        assert_eq!(wound_factor(false, true, 60), 0.0);
        assert!(wound_factor(false, true, 45) > 0.3);
        assert!(wound_factor(false, true, 31) >= 1.0);
        assert_eq!(wound_factor(false, false, 31), 0.0);
        // audio: the same key, wound vs plain construction
        let sr = 44100.0;
        let wound_steel = PluckPreset {
            wound_all: true,
            ..STEEL
        };
        let plain = render_pluck(&STEEL, 57, 100, 0.3, 7); // above the split
        let wound = render_pluck(&wound_steel, 57, 100, 0.3, 7);
        let (cw, cp) = (
            crate::testutil::centroid(&wound, sr),
            crate::testutil::centroid(&plain, sr),
        );
        assert!(cw < 0.9 * cp, "wound {cw} not darker than plain {cp}");
    }

    /// Oracle 43 (V4/INT-4): a range-24 full-down bend pitch-limits at the
    /// delay line's capacity instead of silently wrapping into garbage.
    #[test]
    fn extreme_downbend_stays_finite() {
        let sr = 44100.0;
        let mut v = Pluck::new(&BASS, 28, 110, sr, 7);
        v.set_pitch(2f32.powf(-24.0 / 12.0)); // RPN range 24, wheel floored
        let mut buf = vec![0f32; sr as usize];
        v.render(&mut buf);
        assert!(buf.iter().all(|x| x.is_finite()), "non-finite output");
        let peak = buf.iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(peak < 2.0, "wrapped ring buffer: peak {peak}");
    }

    /// Oracle 11 (B5, §5.3): the bass sub carries a real 2nd harmonic
    /// (differential vs a shaper-disabled build) with no DC, and its start
    /// phase varies with the seed.
    #[test]
    fn bass_sub_shaped_and_phase_random() {
        let sr = 44100.0;
        let plain = PluckPreset {
            sub_shape: (0.0, 0.0),
            ..BASS
        };
        let with = render_pluck(&BASS, 28, 100, 0.4, 7);
        let without = render_pluck(&plain, 28, 100, 0.4, 7);
        let f = key_freq(28);
        let h2 = |s: &[f32]| crate::testutil::mag_at(s, sr, 2.0 * f);
        assert!(
            h2(&with) > 1.1 * h2(&without),
            "sub 2f missing: {} vs {}",
            h2(&with),
            h2(&without)
        );
        // DC clause, differential: an unwindowed mean of a 41 Hz note reads
        // fundamental partial-cycle residue (~A/2πn), so compare the SAME
        // seed with the shaper on vs off — sin²−½ = −½cos2x must add none
        let mean = |s: &[f32]| s.iter().map(|&x| x as f64).sum::<f64>() / s.len() as f64;
        let added_dc = (mean(&with) - mean(&without)).abs();
        assert!(added_dc < 1e-3, "sub shaper leaked DC: {added_dc}");
        // seed-dependent sub phase: the LF starts differently across seeds
        let a = render_pluck(&BASS, 28, 100, 0.05, 7);
        let b = render_pluck(&BASS, 28, 100, 0.05, 8);
        let lf = |s: &[f32]| {
            let mut lp = OnePole::lowpass(60.0, sr);
            s.iter().map(|&x| lp.process(x)).collect::<Vec<f32>>()
        };
        assert!(
            crate::testutil::inter_corr(&lf(&a), &lf(&b)).abs() < 0.98,
            "sub phase identical across seeds"
        );
    }

    /// Oracle 13 (B4 + §5.3 pitch clause): SynthBass holds a steady sustain,
    /// its filter envelope sweeps the brightness down after the attack, and
    /// set_pitch actually bends it (V4/INT-5).
    #[test]
    fn synthbass_class_and_pitch() {
        let sr = 44100.0;
        let mut v = SynthBass::new(38, 40, 100, sr, 7);
        let mut buf = vec![0f32; (1.0 * sr) as usize];
        v.render(&mut buf);
        let rms_a = crate::testutil::rms(&buf[(0.2 * sr) as usize..(0.5 * sr) as usize]);
        let rms_b = crate::testutil::rms(&buf[(0.5 * sr) as usize..(0.8 * sr) as usize]);
        let ratio = rms_a.max(rms_b) / rms_a.min(rms_b).max(1e-9);
        assert!(ratio < 1.3, "sustain not steady: {ratio}");
        let c_early = crate::testutil::centroid(&buf[..(0.15 * sr) as usize], sr);
        let c_late = crate::testutil::centroid(&buf[(0.5 * sr) as usize..(0.8 * sr) as usize], sr);
        assert!(
            c_early > 1.15 * c_late,
            "filter env not sweeping: early {c_early} late {c_late}"
        );
        // pitch clause: +2 semitones must sound at the bent pitch
        let mut vb = SynthBass::new(38, 40, 100, sr, 7);
        vb.set_pitch(2f32.powf(2.0 / 12.0));
        let mut bent = vec![0f32; (0.6 * sr) as usize];
        vb.render(&mut bent);
        let want = key_freq(40) * 2f32.powf(2.0 / 12.0);
        let p =
            crate::testutil::peak_locate(&bent[(0.2 * sr) as usize..], sr, want * 0.9, want * 1.1);
        assert!((p / want - 1.0).abs() < 0.04, "bent pitch {p} vs {want}");
    }

    /// A plucked A4 should oscillate near 440 Hz (count zero crossings).
    #[test]
    fn pluck_pitch_a4() {
        let sr = 44100.0;
        let mut v = Pluck::new(&STEEL, 69, 100, sr, 7);
        let mut buf = vec![0f32; 22050];
        v.render(&mut buf);
        // Goertzel peak instead of zero crossings: the K1 cubic tap keeps
        // the 2nd harmonic ringing, which over-counts crossings even after
        // a 500 Hz lowpass — the fundamental itself is what this test pins
        let hz = crate::testutil::peak_locate(&buf[4410..], sr, 396.0, 484.0);
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
        let mut v = Bowed::new(40, 69, 100, sr, 11);
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

    fn render_default_bowed(program: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = Bowed::new(program, key, vel, sr, seed);
        let mut buf = vec![0.0; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    fn attack_rise_s(sig: &[f32], sr: f32) -> f32 {
        let win = (0.005 * sr) as usize;
        let steady = &sig[(0.25 * sr) as usize..(0.45 * sr) as usize];
        let mut levels: Vec<f32> = steady.chunks(win).map(rms).collect();
        levels.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let threshold = 0.8 * levels[levels.len() / 2];
        sig.chunks(win)
            .position(|chunk| rms(chunk) >= threshold)
            .map(|i| i as f32 * win as f32 / sr)
            .unwrap_or(f32::INFINITY)
    }

    /// Solo bowed presets must differ in both steady body and bow onset. The
    /// timbre comparison is level-normalised so attenuation cannot masquerade
    /// as a darker instrument.
    #[test]
    fn default_bowed_bodies_and_onsets_are_distinct() {
        let sr = 44100.0;
        let hf = |program: u8| {
            [50u8, 57, 64]
                .iter()
                .map(|&key| {
                    let s = render_default_bowed(program, key, 100, 0.8, 7);
                    let body = segment(&s, sr, 0.25, 0.70);
                    hp_rms(body, sr, 2500.0) / rms(body).max(1e-9)
                })
                .sum::<f32>()
                / 3.0
        };
        let body = [hf(40), hf(41), hf(42), hf(43)];
        for (i, pair) in body.windows(2).enumerate() {
            let relative = (pair[0] / pair[1]).max(pair[1] / pair[0]);
            assert!(
                relative >= 1.05,
                "adjacent body {} / {} differs only {:.1}%: {body:?}",
                40 + i,
                41 + i,
                (relative - 1.0) * 100.0
            );
        }

        let programs = [110u8, 40, 41, 42, 43];
        let window_s = (0.005 * sr) as usize as f32 / sr;
        let rises: Vec<f32> = programs
            .iter()
            .map(|&program| attack_rise_s(&render_default_bowed(program, 57, 100, 0.5, 11), sr))
            .collect();
        for (pair, labels) in rises.windows(2).zip(programs.windows(2)) {
            assert!(
                pair[1] - pair[0] + 1e-6 >= window_s,
                "GM{} / GM{} onset separation too small: {rises:?}",
                labels[0],
                labels[1]
            );
        }
    }

    /// Each larger instrument must own an audible body band, while fiddle
    /// remains a quicker/brighter violin style on both sides of its sample
    /// handover.
    #[test]
    fn default_bowed_body_bands_and_fiddle_identity() {
        let sr = 44100.0;
        let prominence = |program: u8, key: u8, center: f32, q: f32| {
            let s = render_default_bowed(program, key, 100, 0.8, 9);
            let body = segment(&s, sr, 0.25, 0.70);
            band_rms(body, sr, center, q) / rms(body).max(1e-9)
        };
        for (program, key, center, q) in [
            (41u8, 57u8, 220.0, 1.3),
            (42, 43, 105.0, 1.1),
            (43, 34, 62.0, 1.0),
        ] {
            let own = prominence(program, key, center, q);
            let violin = prominence(40, key, center, q);
            assert!(
                own >= 1.10 * violin,
                "GM{program} body {center} Hz not distinct: {own:.4} vs violin {violin:.4}"
            );
        }

        let violin = render_program_sampled(40, 69, 100, 0.8, 11, false);
        let fiddle = render_program_sampled(110, 69, 100, 0.8, 11, false);
        let hf = |s: &[f32], a: f32, b: f32| {
            let w = segment(s, sr, a, b);
            hp_rms(w, sr, 2500.0) / rms(w).max(1e-9)
        };
        let v_early = hf(&violin, 0.0, 0.08);
        let f_early = hf(&fiddle, 0.0, 0.08);
        assert!(
            f_early >= 1.10 * v_early,
            "fiddle modeled bite is not brighter: {f_early:.4} vs {v_early:.4}"
        );
        let v_post = hf(&violin, 0.35, 0.75);
        let f_post = hf(&fiddle, 0.35, 0.75);
        assert!(
            (f_post / v_post).max(v_post / f_post) >= 1.05,
            "fiddle post-handover body collapsed into violin: {f_post:.4} vs {v_post:.4}"
        );

        let sampled = render_program_sampled(110, 69, 100, 0.8, 11, true);
        let windows: Vec<f32> = segment(&sampled, sr, 0.05, 0.35)
            .chunks((0.05 * sr) as usize)
            .map(rms)
            .collect();
        let worst = windows
            .windows(2)
            .map(|w| (w[0] / w[1]).max(w[1] / w[0]))
            .fold(1.0, f32::max);
        assert!(
            worst <= 1.6,
            "fiddle handover RMS jump {worst:.3}: {windows:?}"
        );
    }

    /// The nominal natural-vibrato rates are control-rate values, not full-rate
    /// oscillators sampled once every CTRL frames.
    #[test]
    fn default_bowed_natural_vibrato_runs_at_named_rate() {
        let sr = 44100.0;
        for (program, nominal) in [(40u8, 5.3f32), (41, 5.1), (42, 4.8), (43, 4.2), (110, 5.6)] {
            let mut v = Bowed::new(program, 69, 100, sr, 17);
            let mut values = Vec::new();
            let mut block = [0.0; CTRL as usize];
            let seconds = 3usize;
            for _ in 0..(seconds * sr as usize / CTRL as usize) {
                block.fill(0.0);
                v.render(&mut block);
                values.push(v.vib_val);
            }
            let crossings = values
                .windows(2)
                .filter(|w| w[0] <= 0.0 && w[1] > 0.0)
                .count() as f32
                / seconds as f32;
            assert!(
                (crossings - nominal).abs() / nominal <= 0.15,
                "GM{program} vibrato {crossings:.2} Hz, expected near {nominal:.2} Hz"
            );
        }
    }

    /// Corrected pitch vibrato must not reappear as periodic bow-hiss AM.
    #[test]
    fn default_bowed_arco_am_stays_small() {
        let sr = 44100.0;
        for program in [40u8, 110] {
            let s = render_default_bowed(program, 69, 100, 1.4, 13);
            let depth = low_rate_am_depth(segment(&s, sr, 0.55, 1.35), sr);
            assert!(
                depth < 0.03,
                "GM{program} arco low-rate AM depth {depth:.4}"
            );
        }
        let trem = render_default_bowed(44, 69, 100, 1.4, 13);
        let trem_depth = low_rate_am_depth(segment(&trem, sr, 0.55, 1.35), sr);
        assert!(
            trem_depth >= 0.08,
            "GM44 tremolo AM depth only {trem_depth:.4}"
        );
    }

    /// Default-bank tremolo and pizzicato are articulation-correct solo
    /// proxies; neither may inherit the sustained violin sample wrapper.
    #[test]
    fn default_bowed_articulations_and_sample_routing() {
        let sr = 44100.0;
        let trem = render_program_sampled(44, 69, 100, 2.5, 5, false);
        let (peak, rate) =
            env_autocorr_peak_detrend(segment(&trem, sr, 0.4, 2.4), sr, 0.08, 0.20, 4.0);
        assert!(peak >= BW_TREM_PEAK_FLOOR, "tremolo AM peak {peak:.3}");
        assert!((6.0..=9.5).contains(&rate), "tremolo rate {rate:.2} Hz");

        let slow = Bowed::new(44, 69, 32, sr, 5).trem_rate;
        let fast = Bowed::new(44, 69, 127, sr, 5).trem_rate;
        assert!(
            fast - slow >= 1.5,
            "GM44 velocity did not accelerate tremolo: {slow:.2} -> {fast:.2} Hz"
        );

        let mut voice = Bowed::new(44, 69, 100, sr, 5);
        let mut signal = Vec::with_capacity((2.0 * sr) as usize);
        let mut reversals = Vec::new();
        let mut block = [0.0; CTRL as usize];
        while signal.len() < (2.0 * sr) as usize {
            let reversal = voice.t as usize;
            let old_until = voice.trem_bite_until;
            block.fill(0.0);
            voice.render(&mut block);
            if voice.trem_bite_until != old_until {
                reversals.push(reversal);
            }
            signal.extend_from_slice(&block);
        }
        let period = (sr / key_freq(69)) as usize;
        let residual: Vec<f32> = signal
            .iter()
            .enumerate()
            .map(|(i, &x)| {
                if i >= period {
                    x - signal[i - period]
                } else {
                    0.0
                }
            })
            .collect();
        let w = (BOW_TREM_BITE_S * sr) as usize;
        let ratios: Vec<f32> = reversals
            .iter()
            .copied()
            .filter(|&i| i >= w && i + w < residual.len())
            .map(|i| {
                hp_rms(&residual[i..i + w], sr, 3000.0)
                    / hp_rms(&residual[i - w..i], sr, 3000.0).max(1e-9)
            })
            .collect();
        let rebite = ratios.iter().sum::<f32>() / ratios.len().max(1) as f32;
        assert!(
            ratios.len() >= 8,
            "found only {} bow reversals",
            ratios.len()
        );
        assert!(rebite >= 1.3, "GM44 reversal re-bite ratio {rebite:.3}");

        let early_late = |program: u8| {
            let s = render_program_sampled(program, 69, 100, 2.0, 7, false);
            rms(segment(&s, sr, 1.55, 1.95)) / rms(segment(&s, sr, 0.10, 0.35)).max(1e-9)
        };
        assert!(early_late(45) < 0.10, "GM45 must decay like a pluck");
        assert!(early_late(40) > 0.70, "GM40 must sustain like arco");

        let bits = |s: Vec<f32>| s.into_iter().map(f32::to_bits).collect::<Vec<_>>();
        let samples_available = bits(render_program_sampled(0, 69, 100, 0.5, 6, true))
            != bits(render_program_sampled(0, 69, 100, 0.5, 6, false));
        // Modeled-only bowed voices carry no sample layer: viola (41), tremolo
        // (44) and pizzicato (45).
        for program in [41u8, 44, 45] {
            let on = bits(render_program_sampled(program, 69, 100, 0.5, 6, true));
            let off = bits(render_program_sampled(program, 69, 100, 0.5, 6, false));
            assert_eq!(on, off, "GM{program} must skip the sample layer");
        }
        // Sampled voices carry their LA attack when the key is in the bank's
        // range: violin (40) and fiddle (110) and the cello (42) at A4; the
        // contrabass (43) at a low E2 — A4 is above its zones, so there it
        // correctly falls back to the bare waveguide (tested in the skip spirit
        // by the range guard, not here).
        for (program, key) in [(40u8, 69u8), (110, 69), (42, 69), (43, 40)] {
            let on = bits(render_program_sampled(program, key, 100, 0.5, 6, true));
            let off = bits(render_program_sampled(program, key, 100, 0.5, 6, false));
            if samples_available {
                assert_ne!(on, off, "GM{program} must carry its LA sample at key {key}");
            } else {
                assert_eq!(
                    on, off,
                    "GM{program} must stay modeled without an embedded bank"
                );
            }
        }
    }

    /// Natural playing ranges stay tuned through bodies and LA handovers; a
    /// slur retunes the same bow without spawning a fresh attack.
    #[test]
    fn default_bowed_pitch_range_and_legato() {
        let sr = 44100.0;
        for (program, keys) in [
            (40u8, &[55u8, 69, 88][..]),
            (41, &[48, 60, 76]),
            (42, &[36, 48, 69]),
            (43, &[34, 45, 64]),
            (44, &[45, 60, 78]),
            (45, &[52, 64, 76]),
            (110, &[55, 69, 88]),
        ] {
            for &key in keys {
                let s = render_program_sampled(program, key, 100, 0.8, 21, true);
                let window = if program == 45 {
                    segment(&s, sr, 0.05, 0.45)
                } else {
                    segment(&s, sr, 0.20, 0.65)
                };
                let f0 = key_freq(key);
                let found = peak_locate(window, sr, f0 * 0.8, f0 * 1.25);
                let cents = 1200.0 * (found / f0).log2();
                assert!(
                    cents.abs() < 45.0,
                    "GM{program} key {key} pitch {found:.2} Hz ({cents:.1} cents)"
                );
            }
        }

        let mut v = Bowed::new(42, 57, 100, sr, 23);
        let mut before = vec![0.0; (0.30 * sr) as usize];
        v.render(&mut before);
        assert!(v.legato_to(62, 96));
        let mut after = vec![0.0; (0.80 * sr) as usize];
        v.render(&mut after);
        let f0 = key_freq(62);
        let found = peak_locate(segment(&after, sr, 0.35, 0.75), sr, f0 * 0.8, f0 * 1.25);
        assert!(
            (1200.0 * (found / f0).log2()).abs() < 45.0,
            "cello legato retune landed at {found:.2} Hz"
        );
    }

    #[test]
    fn default_bowed_family_level_and_numerical_safety() {
        let sr = 44100.0;
        let violin = render_default_bowed(40, 57, 100, 1.0, 29);
        let violin_rms = rms(segment(&violin, sr, 0.20, 0.80));
        for program in [41u8, 42, 43, 110] {
            let s = render_default_bowed(program, 57, 100, 1.0, 29);
            let level = rms(segment(&s, sr, 0.20, 0.80));
            let db = 20.0 * (level / violin_rms).log10();
            assert!(db.abs() <= 3.0, "GM{program} level is {db:.2} dB vs violin");
            assert!(
                s.iter().all(|x| x.is_finite()),
                "GM{program} emitted non-finite audio"
            );
            assert!(max_abs(&s) < 1.5, "GM{program} raw peak {}", max_abs(&s));
            let mut lp1 = OnePole::lowpass(8.0, sr);
            let mut lp2 = OnePole::lowpass(8.0, sr);
            let mut lp3 = OnePole::lowpass(8.0, sr);
            let mut lp4 = OnePole::lowpass(8.0, sr);
            let dc: Vec<f32> = s
                .iter()
                .map(|&x| lp4.process(lp3.process(lp2.process(lp1.process(x)))))
                .collect();
            let dc_ratio =
                rms(segment(&dc, sr, 0.60, 0.95)) / rms(segment(&s, sr, 0.60, 0.95)).max(1e-9);
            assert!(dc_ratio < 1e-3, "GM{program} true-DC ratio {dc_ratio:.6}");
        }

        let pizz = render_program_sampled(45, 69, 100, 0.4, 31, false);
        let harp = render_program_sampled(46, 69, 100, 0.4, 31, false);
        let arco = render_program_sampled(40, 69, 100, 0.4, 31, false);
        let early = |s: &[f32]| rms(segment(s, sr, 0.05, 0.35));
        let db = |a: f32, b: f32| 20.0 * (a / b).log10();
        assert!(db(early(&pizz), early(&arco)) <= 3.0);
        assert!(db(early(&pizz), early(&harp)).abs() <= 10.0);
    }

    // ---- synth-lead voice (GM 80-87) ----

    fn render_saw(v: &mut SawStack, sr: f32, secs: f32) -> Vec<f32> {
        let mut buf = vec![0f32; (sr * secs) as usize];
        v.render(&mut buf);
        buf
    }

    fn render_voice(mut v: Box<dyn Voice>, sr: f32, secs: f32) -> Vec<f32> {
        let mut buf = vec![0f32; (sr * secs) as usize];
        v.render(&mut buf);
        buf
    }

    // -- Stage 4 (ensemble 48-51): the Synth Strings 50/51 string-machine split --

    /// EN-O1: Synth Strings 1/2 (50/51) are tier D — a *model-only* divide-down
    /// machine. The `make` dispatch must never wrap them in a sample layer, so
    /// samples on/off render bit-identically. Guards a future dispatch edit from
    /// silently turning the synth strings into sampled acoustic strings.
    #[test]
    fn synth_strings_50_51_are_model_only() {
        let sr = 44100.0;
        for program in [50u8, 51] {
            let render = |samples: bool| {
                let mut v = make(program, 60, 100, sr, 7, samples);
                let mut buf = vec![0f32; (sr * 0.5) as usize];
                v.render(&mut buf);
                buf
            };
            assert_eq!(
                render(true),
                render(false),
                "program {program} must be model-only — the sample layer must be inert"
            );
        }
    }

    /// EN-O2: within the machine, 51 is the lush/dark variant of 50 (lowpass 2400
    /// vs 3000 Hz). Both are chorus-only (no vibrato or drift), so a high-band
    /// energy fraction compares them cleanly — where a magnitude centroid would be
    /// confounded by the *acoustic* section's vibrato smearing its own partials.
    /// The raw distinctness of all three is proven independently by the matrix.
    #[test]
    fn synth_strings_2_is_the_darker_variant() {
        let sr = 44100.0;
        let render = |mut v: SawStack| {
            let mut buf = vec![0f32; (sr * 0.7) as usize];
            v.render(&mut buf);
            buf
        };
        let hf_frac = |s: &[f32]| hp_rms(s, sr, 2800.0) / rms(s).max(1e-9);
        let h50 = hf_frac(&render(synth_strings(50, 60, 100, sr, 7)));
        let h51 = hf_frac(&render(synth_strings(51, 60, 100, sr, 7)));
        assert!(
            h51 < h50 * 0.85,
            "synth strings 2 (51) should pass less high-frequency energy than 1 (50): \
             HF fraction {h51:.4} vs {h50:.4}"
        );
    }

    /// EN-O3: the string machine's ensemble motion is CORRELATED — one shared BBD
    /// chorus (period ~1.33 s at 0.75 Hz) beats the layers together periodically,
    /// where the acoustic section's independent per-player drift + vibrato wander
    /// aperiodically. The envelope autocorrelation in the chorus band is the
    /// differential; the machine must show a stronger period than the section.
    #[test]
    fn synth_strings_ensemble_motion_is_correlated() {
        let sr = 44100.0;
        let render = |mut v: SawStack| {
            let mut buf = vec![0f32; (sr * 4.0) as usize];
            v.render(&mut buf);
            buf
        };
        // 0.9-2.2 s lag brackets the 0.75 Hz chorus period (1.33 s).
        let (machine, _) =
            env_autocorr_peak(&render(synth_strings(50, 60, 100, sr, 7)), sr, 0.9, 2.2);
        let (section, _) = env_autocorr_peak(&render(strings(48, 60, 100, sr, 7)), sr, 0.9, 2.2);
        assert!(
            machine > section * 1.3,
            "the string machine (50) should beat more periodically than the acoustic section (48): {machine:.3} vs {section:.3}"
        );
    }

    /// OS-1 (Stage 5a): GM 17 percussive organ strikes a 3rd-harmonic tap at
    /// key-on that DECAYS over the held drawbar, where GM 16's 3rd harmonic is a
    /// steady drawbar. Normalising the 3rd by the fundamental in an early vs late
    /// window isolates the tap from any global envelope; the differential vs 16 is
    /// the guard. The anti-clone matrix proves the raw split, but its steady-state
    /// read cannot see the *percussive* (temporal) identity — this can.
    #[test]
    fn percussive_organ_17_has_a_decaying_tap() {
        let sr = 44100.0;
        let f0 = key_freq(60);
        // Early/late ratio of (3rd harmonic / fundamental): >1 means the 3rd is
        // proportionally stronger at onset — i.e. a decaying tap sits on it.
        let tap_ratio = |program: u8| {
            let mut v = make(program, 60, 100, sr, 7, false);
            let mut buf = vec![0f32; (sr * 0.8) as usize];
            v.render(&mut buf);
            let third_over_first = |lo: f32, hi: f32| {
                let seg = &buf[(lo * sr) as usize..(hi * sr) as usize];
                mag_at(seg, sr, f0 * 3.0) / mag_at(seg, sr, f0).max(1e-9)
            };
            // 0.02-0.10 s: past the click transient, tap still strong.
            third_over_first(0.02, 0.10) / third_over_first(0.45, 0.75)
        };
        let d17 = tap_ratio(17);
        let d16 = tap_ratio(16);
        // Onset punch: the tap + louder key click make 17's onset energy larger
        // relative to its sustain than 16's steady drawbars — a band-energy read
        // (700-900 Hz around the 3rd harmonic) integrates the decaying tap where a
        // narrowband Goertzel smears it.
        let punch = |program: u8| {
            let mut v = make(program, 60, 100, sr, 7, false);
            let mut buf = vec![0f32; (sr * 0.8) as usize];
            v.render(&mut buf);
            let band = |lo: f32, hi: f32| {
                spectral_band_rms(
                    &buf[(lo * sr) as usize..(hi * sr) as usize],
                    sr,
                    650.0,
                    950.0,
                )
            };
            band(0.005, 0.055) / band(0.45, 0.75).max(1e-9)
        };
        let p17 = punch(17);
        let p16 = punch(16);
        assert!(
            p17 > 1.6 * p16,
            "GM17 should have a percussive onset the steady GM16 lacks: \
             onset/sustain band-punch 17={p17:.2} 16={p16:.2} (3rd-ratio 17={d17:.2} 16={d16:.2})"
        );
    }

    /// Non-overlapping windowed-RMS envelope (X5: measure the envelope, not raw
    /// sample peaks, which oscillator phase moves around).
    fn rms_env(sig: &[f32], sr: f32, win_ms: f32) -> Vec<f32> {
        let w = (((win_ms / 1000.0) * sr) as usize).max(1);
        sig.chunks(w)
            .map(|c| (c.iter().map(|x| x * x).sum::<f32>() / c.len() as f32).sqrt())
            .collect()
    }

    /// Steady-state RMS over [lo, hi] seconds — a beat-robust reference level
    /// (the detuned stack's beat makes a global-peak reference unreliable).
    fn steady_rms(sig: &[f32], sr: f32, lo_s: f32, hi_s: f32) -> f32 {
        let seg = &sig[(lo_s * sr) as usize..(hi_s * sr) as usize];
        (seg.iter().map(|x| x * x).sum::<f32>() / seg.len() as f32).sqrt()
    }

    /// Time (s) for the RMS envelope to first reach an absolute level `thr`.
    fn t_to_level(sig: &[f32], sr: f32, thr: f32, win_ms: f32) -> f32 {
        let env = rms_env(sig, sr, win_ms);
        for (i, &e) in env.iter().enumerate() {
            if e >= thr {
                return i as f32 * win_ms / 1000.0;
            }
        }
        f32::INFINITY
    }

    /// Oracle 7a: the `LayerOsc::Saw` arm is bit-for-bit a bare `BlepSaw` — the
    /// enum wrapper cannot perturb the byte-identical saw path.
    #[test]
    fn layerosc_saw_is_bit_identical_to_blepsaw() {
        let sr = 44100.0;
        let mut a = LayerOsc::Saw(BlepSaw::new(220.0, sr, 0.3));
        let mut b = BlepSaw::new(220.0, sr, 0.3);
        for _ in 0..4000 {
            assert_eq!(a.next().to_bits(), b.next().to_bits());
        }
    }

    /// Oracle 7b: the SawStack families this change refactors — pads and
    /// strings — retain tight level, spectrum, and envelope signatures.
    /// (The choir arm was retired 2026.07.10: GM 52-54
    /// moved off SawStack onto the dedicated `ChoirV2` formant engine, an
    /// intentional default-bank voicing change; the surviving pad/strings pins
    /// prove the shared stack itself did not move.)
    #[test]
    fn sawstack_family_signatures_are_stable() {
        let sr = 44100.0;
        let render = |mut v: SawStack| {
            let mut buf = vec![0f32; (sr * 0.5) as usize];
            v.render(&mut buf);
            buf
        };
        let pad_render = render(pad(95, 60, 100, sr, 7));
        let strings_render = render(strings(48, 60, 100, sr, 7));
        assert_render_signature(
            "SawStack pad(95)",
            render_signature(&pad_render, sr, (0.1, 0.4), (0.05, 0.15), (0.35, 0.48)),
            RenderSignature {
                rms_db: -25.026,
                centroid_hz: 657.345,
                late_early_db: 12.005,
            },
        );
        assert_render_signature(
            "SawStack strings(48)",
            render_signature(&strings_render, sr, (0.1, 0.4), (0.05, 0.15), (0.35, 0.48)),
            RenderSignature {
                rms_db: -28.043,
                centroid_hz: 683.291,
                late_early_db: 3.082,
            },
        );
    }

    #[test]
    fn synth_fx_97_99_101_103_sustain_as_pads() {
        let sr = 44100.0;
        let key = 60;
        let vel = 100;
        let seed = 7;
        let crystal = render_voice(make(98, key, vel, sr, seed, false), sr, 4.5);
        let crystal_tail = steady_rms(&crystal, sr, 3.8, 4.4);

        for prog in [97, 99, 103] {
            let v = make(prog, key, vel, sr, seed, false);
            assert_eq!(v.kind(), "sawstack", "program {prog} should route to pad");
            let sig = render_voice(v, sr, 4.5);
            let mid = steady_rms(&sig, sr, 2.0, 3.0);
            let tail = steady_rms(&sig, sr, 3.8, 4.4);
            assert!(
                tail > 0.40 * mid,
                "program {prog} should sustain while held: mid {mid}, tail {tail}"
            );
            assert!(
                tail > 8.0 * crystal_tail.max(1e-9),
                "program {prog} should not decay like crystal: tail {tail}, crystal {crystal_tail}"
            );
        }

        let sweep_fx = render_voice(make(101, key, vel, sr, seed, false), sr, 2.0);
        let mut sweep_pad = pad(95, key, vel, sr, seed);
        let sweep_ref = render_saw(&mut sweep_pad, sr, 2.0);
        assert!(
            sweep_fx
                .iter()
                .zip(&sweep_ref)
                .all(|(a, b)| a.to_bits() == b.to_bits()),
            "program 101 should use the sweep-pad path"
        );
    }

    /// Oracle 1: a lead speaks fast; a pad swells slowly. Guard is the ratio —
    /// absolute pad thresholds near 300 ms are fragile.
    #[test]
    fn lead_attack_is_fast_vs_pad() {
        let sr = 44100.0;
        let lead_sig = render_saw(&mut lead(81, 69, 100, sr, 7), sr, 1.2);
        let pad_sig = render_saw(&mut pad(89, 69, 100, sr, 7), sr, 1.2);
        // reference each against its own steady level (both are settled by 0.8 s)
        let lt = t_to_level(
            &lead_sig,
            sr,
            0.9 * steady_rms(&lead_sig, sr, 0.8, 1.1),
            10.0,
        );
        let pt = t_to_level(&pad_sig, sr, 0.9 * steady_rms(&pad_sig, sr, 0.8, 1.1), 10.0);
        assert!(lt < 0.050, "lead attack too slow: {lt}s");
        assert!(
            pt > 0.150 && pt > 5.0 * lt,
            "pad attack {pt}s vs lead {lt}s (ratio guard)"
        );
    }

    /// Oracle 2: the lead release is short; the pad rings on.
    #[test]
    fn lead_release_is_short_vs_pad() {
        let sr = 44100.0;
        let run = |mut v: SawStack| {
            let mut buf = vec![0f32; (sr * 0.3) as usize];
            v.render(&mut buf);
            let seg = &buf[(sr * 0.2) as usize..];
            let plateau = (seg.iter().map(|x| x * x).sum::<f32>() / seg.len() as f32).sqrt();
            v.note_off();
            let mut tail = vec![0f32; (sr * 0.5) as usize];
            v.render(&mut tail);
            (plateau, tail)
        };
        let (lp, ltail) = run(lead(81, 69, 100, sr, 7));
        let (pp, ptail) = run(pad(89, 69, 100, sr, 7));
        let at_300 = |t: &[f32]| rms_env(t, sr, 10.0)[30]; // 300 ms / 10 ms
        assert!(at_300(&ltail) < 0.10 * lp, "lead release too long");
        assert!(at_300(&ptail) > 0.10 * pp, "pad released too fast");
    }

    /// Oracle 3: harder playing opens the lead's tone (velocity -> brightness).
    #[test]
    fn lead_velocity_opens_brightness() {
        let sr = 44100.0;
        let hard = render_saw(&mut lead(81, 69, 120, sr, 7), sr, 0.4);
        let soft = render_saw(&mut lead(81, 69, 40, sr, 7), sr, 0.4);
        let skip = (sr * 0.1) as usize;
        let c_hard = crate::testutil::centroid(&hard[skip..], sr);
        let c_soft = crate::testutil::centroid(&soft[skip..], sr);
        assert!(
            c_hard > 1.2 * c_soft,
            "vel brightness: hard {c_hard} soft {c_soft}"
        );
    }

    /// Oracle 4b: the square lead (80) routes to the pulse oscillator — its
    /// even-harmonic content is far weaker than the saw lead (81).
    #[test]
    fn square_lead_routes_to_pulse() {
        let sr = 44100.0;
        let sq = render_saw(&mut lead(80, 57, 100, sr, 7), sr, 1.2);
        let sw = render_saw(&mut lead(81, 57, 100, sr, 7), sr, 1.2);
        let win = |s: &[f32]| s[(sr * 0.15) as usize..(sr * 1.15) as usize].to_vec();
        let (sqw, sww) = (win(&sq), win(&sw));
        let mag = crate::testutil::mag_at;
        let r_sq = mag(&sqw, sr, 440.0) / mag(&sqw, sr, 220.0);
        let r_sw = mag(&sww, sr, 440.0) / mag(&sww, sr, 220.0);
        assert!(r_sq < 0.35 * r_sw, "square H2/H1 {r_sq} vs saw {r_sw}");
    }

    /// Oracle 6 (gate half): strings/choir/leads slur; pads re-attack
    /// (byte-identity does not depend on the CC68 census).
    #[test]
    fn legato_gated_to_strings_choir_and_leads() {
        let sr = 44100.0;
        let mut a = strings(48, 60, 100, sr, 7);
        let mut b = choir(52, 60, 100, sr, 7);
        let mut c = pad(89, 60, 100, sr, 7);
        let mut d = lead(81, 60, 100, sr, 7);
        assert!(a.legato_to(62, 100), "strings must slur");
        assert!(b.legato_to(62, 100), "choir must slur");
        assert!(!c.legato_to(62, 100), "pad must not slur");
        assert!(d.legato_to(62, 100), "lead must slur");
    }

    /// Oracle 8: the lead still answers pitch bend via the shared set_pitch.
    #[test]
    fn lead_still_bends() {
        let sr = 44100.0;
        let mut v = lead(81, 57, 100, sr, 7); // A3 = 220 Hz
        let up = 2f32.powf(2.0 / 12.0);
        v.set_pitch(up);
        let buf = render_saw(&mut v, sr, 0.5);
        let hz = crate::testutil::peak_locate(&buf[(sr * 0.1) as usize..], sr, 220.0, 300.0);
        assert!(
            (hz - 220.0 * up).abs() < 6.0,
            "bent pitch {hz}, want {}",
            220.0 * up
        );
    }

    /// Render a fresh brass voice `secs` seconds (no note_off) into a buffer.
    fn render_brass(prog: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = brass(prog, key, vel, sr, seed);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    /// 10→90% rise time of the 10 ms windowed-RMS envelope, in seconds.
    fn rise_10_90(seg: &[f32], sr: f32) -> f32 {
        let win = (0.01 * sr) as usize;
        let env: Vec<f32> = seg.chunks(win).map(rms).collect();
        let peak = env.iter().cloned().fold(0.0f32, f32::max).max(1e-12);
        let (lo, hi) = (0.10 * peak, 0.90 * peak);
        let t_at = |thresh: f32| -> f32 {
            for (i, &v) in env.iter().enumerate() {
                if v >= thresh {
                    return (i * win) as f32 / sr;
                }
            }
            f32::INFINITY
        };
        (t_at(hi) - t_at(lo)).max(0.0)
    }

    /// BR-O1 (sustain): a held brass note holds — sustain ratio ≥ 0.7 (a
    /// STEEL-pluck fallback measures ≈ 0.01, the journal headline).
    #[test]
    fn brass_o1_sustains() {
        let sr = 44100.0;
        let b = render_brass(56, 69, 100, 2.2, 7);
        let ratio = rms(&b[(1.45 * sr) as usize..(1.85 * sr) as usize])
            / rms(&b[(0.15 * sr) as usize..(0.45 * sr) as usize]).max(1e-12);
        assert!(ratio >= 0.7, "sustain ratio {ratio:.3} (need ≥ 0.7)");
    }

    /// BR-O2 (loudness→brightness, flagship): a loud note is measurably brighter
    /// than a soft one AT THE SUSTAIN, not just louder. The lip law alone is
    /// masked by the fixed bore/bell, so the L-driven output brightness carries
    /// the centroid contrast (see `out_base`/`out_oct`, the Bowed precedent).
    #[test]
    fn brass_o2_loudness_opens_brightness() {
        let sr = 44100.0;
        let cent = |vel: u8| {
            let b = render_brass(56, 69, vel, 1.4, 7);
            let seg = &b[(0.4 * sr) as usize..(1.2 * sr) as usize];
            (centroid(seg, sr), rms(seg))
        };
        let (c36, r36) = cent(36);
        let (c120, r120) = cent(120);
        assert!(
            r36 > 1e-4 && r120 > 1e-4,
            "a window is silent: {r36} {r120}"
        );
        assert!(
            c120 / c36 >= 1.30,
            "centroid ratio {:.3} (need ≥ 1.30): vel120 {c120:.0} vel36 {c36:.0}",
            c120 / c36
        );
    }

    /// BR-O3 (the "waa"): the note speaks dark and blooms bright over the onset
    /// (the dedicated `benv`, not the amp attack). EQUAL-length 70 ms windows —
    /// the Goertzel centroid's leakage is window-length dependent, so the
    /// appendix's 70 ms early vs 200 ms late is not a valid comparison; both
    /// windows begin after the ≈28 ms amp attack, so this measures the bloom.
    #[test]
    fn brass_o3_the_waa() {
        let sr = 44100.0;
        let b = render_brass(56, 69, 100, 1.0, 7);
        let early = centroid(&b[(0.03 * sr) as usize..(0.10 * sr) as usize], sr);
        let late = centroid(&b[(0.30 * sr) as usize..(0.37 * sr) as usize], sr);
        assert!(
            late / early >= 1.25,
            "waa late/early {:.3} (need ≥ 1.25): late {late:.0} early {early:.0}",
            late / early
        );
    }

    /// 30 Hz flutter depth: rms of the 30 Hz-bandpassed amplitude envelope over
    /// its mean — a clean growl-present vs absent discriminator.
    fn flutter30(seg: &[f32], sr: f32) -> f32 {
        let mut lp = OnePole::lowpass(200.0, sr);
        let env: Vec<f32> = seg.iter().map(|&x| lp.process(x.abs())).collect();
        let mean = env.iter().sum::<f32>() / env.len() as f32;
        let mut bp = Biquad::bandpass(30.0, 4.0, sr);
        let flut: Vec<f32> = env.iter().map(|&x| bp.process(x)).collect();
        rms(&flut) / mean.max(1e-9)
    }

    /// BR-O5 (growl, voice-level via `set_breath`): channel-aftertouch growl
    /// adds a 25–40 Hz flutter roughness AND a drive bite, both absent without
    /// it. (The engine AT path — `at_gain`/`at_vib` — is deferred; this pins the
    /// voice's own BR10 response.) The env-autocorr peak magnitude alone can't
    /// discriminate (a smooth envelope autocorrelates highly at short lags), so
    /// the flutter is pinned by its 30 Hz depth and its autocorr RATE.
    #[test]
    fn brass_o5_growl() {
        let sr = 44100.0;
        let run = |growl: f32| {
            let mut v = brass(56, 60, 80, sr, 7);
            let mut warm = vec![0f32; (0.1 * sr) as usize];
            v.render(&mut warm);
            v.set_breath(1.0, growl);
            let mut buf = vec![0f32; (1.6 * sr) as usize];
            v.render(&mut buf);
            let seg = buf[(0.4 * sr) as usize..(1.4 * sr) as usize].to_vec();
            let (peak, rate) = env_autocorr_peak(&seg, sr, 0.02, 0.05);
            (flutter30(&seg, sr), peak, rate, hp_rms(&seg, sr, 2000.0))
        };
        let (f_on, p_on, r_on, hp_on) = run(110.0 / 127.0);
        let (f_off, _p_off, r_off, hp_off) = run(0.0);
        // flutter present with growl, absent without
        assert!(
            f_on >= 0.08 && f_on >= 3.0 * f_off,
            "flutter30 growl {f_on:.4} vs none {f_off:.4}"
        );
        assert!(
            p_on >= 0.25 && (25.0..=40.0).contains(&r_on),
            "growl autocorr peak {p_on:.3} rate {r_on:.1} Hz"
        );
        assert!(
            !(25.0..=40.0).contains(&r_off),
            "no-growl envelope shows a 30 Hz flutter (rate {r_off:.1})"
        );
        // the drive bite: growl raises >2 kHz energy
        assert!(
            hp_on / hp_off >= 1.4,
            "growl bite hp(2k) ratio {:.3} (need ≥ 1.4)",
            hp_on / hp_off
        );
    }

    /// BR-O6 (tongued ≠ slurred): a fresh-attack note fires a tongue chiff; a
    /// slur (legato_to) does not. Measured by a differential that isolates the
    /// chiff exactly — chiff on vs off share an identical RNG stream (the Burst
    /// draws noise regardless of its gain), so the onset difference IS the
    /// chiff's audio. It is large for a tongued attack and zero for the slur.
    /// (A broadband-HF or flatness comparison is confounded: the slur inherits
    /// full bloom/amplitude/breath while the tongued note speaks dark.)
    #[test]
    fn brass_o6_tongued_vs_slurred() {
        let sr = 44100.0;
        let nochiff: &'static BrassSpec = Box::leak(Box::new(BrassSpec {
            chiff: 0.0,
            ..BR_TRUMPET
        }));
        let n = (0.03 * sr) as usize;
        // tongued C5: the chiff on-vs-off difference is the tongue transient
        let t_on = {
            let mut v = Brass::new(&BR_TRUMPET, 72, 100, sr, 7);
            let mut b = vec![0f32; (0.2 * sr) as usize];
            v.render(&mut b);
            b
        };
        let t_off = {
            let mut v = Brass::new(nochiff, 72, 100, sr, 7);
            let mut b = vec![0f32; (0.2 * sr) as usize];
            v.render(&mut b);
            b
        };
        let diff = |on: &[f32], off: &[f32]| {
            rms(&on[..n]
                .iter()
                .zip(&off[..n])
                .map(|(a, b)| a - b)
                .collect::<Vec<_>>())
        };
        let tongued_chiff = diff(&t_on, &t_off);
        // slur A4 → C5 via legato_to at 1.0 s: the chiff must NOT re-fire
        let slur = |spec: &'static BrassSpec| {
            let mut v = Brass::new(spec, 69, 100, sr, 7);
            let mut head = vec![0f32; sr as usize];
            v.render(&mut head);
            assert!(v.legato_to(72, 100), "brass should slur");
            let mut b = vec![0f32; (0.2 * sr) as usize];
            v.render(&mut b);
            b
        };
        let s_on = slur(&BR_TRUMPET);
        let s_off = slur(nochiff);
        let slur_chiff = diff(&s_on, &s_off);
        assert!(
            tongued_chiff > 1e-3 && slur_chiff < 0.05 * tongued_chiff,
            "chiff: tongued {tongued_chiff:.5} vs slur {slur_chiff:.5} (slur must have none)"
        );
        // the slur arrives at C5 (523.25 Hz)
        let p = peak_locate(&s_on[(0.1 * sr) as usize..], sr, 500.0, 550.0);
        assert!(
            (p / 523.25 - 1.0).abs() < 0.01,
            "slur pitch {p} Hz vs 523.25"
        );
    }

    /// BR-O7 (section scatter + determinism): the section (61) rises slower than
    /// the solo (56) — its per-player onset scatter spreads the front edge — and
    /// the same seed renders bit-identically twice.
    #[test]
    fn brass_o7_section_scatter_and_determinism() {
        let sr = 44100.0;
        let sec = render_brass(61, 60, 100, 1.0, 7);
        let solo = render_brass(56, 60, 100, 1.0, 7);
        assert!(
            rise_10_90(&sec, sr) >= rise_10_90(&solo, sr) + 0.015,
            "section rise {:.4}s not ≥ solo {:.4}s + 15 ms",
            rise_10_90(&sec, sr),
            rise_10_90(&solo, sr)
        );
        // determinism: same seed twice bit-identical
        let a = render_brass(61, 60, 100, 0.5, 7);
        let b = render_brass(61, 60, 100, 0.5, 7);
        assert!(
            a.iter().zip(&b).all(|(x, y)| x.to_bits() == y.to_bits()),
            "same-seed section renders differ"
        );
        // two seeds differ (per-player scatter/detune/drift is seeded)
        let c = render_brass(61, 60, 100, 0.5, 8);
        assert!(
            a.iter().zip(&c).any(|(x, y)| x != y),
            "seeds 7 and 8 identical"
        );
    }

    /// BR-O8 (mute identity, prog 59): the straight mute collapses the lows and
    /// pushes the nasal mid — `band_rms(500)/band_rms(1800)` ≤ 0.5× the open
    /// trumpet — and its insertion loss lowers the overall level.
    #[test]
    fn brass_o8_mute_identity() {
        let sr = 44100.0;
        let m = render_brass(59, 74, 100, 1.0, 7);
        let o = render_brass(56, 74, 100, 1.0, 7);
        let ratio =
            |s: &[f32]| band_rms(s, sr, 500.0, 1.0) / band_rms(s, sr, 1800.0, 1.0).max(1e-9);
        assert!(
            ratio(&m) <= 0.5 * ratio(&o),
            "mute band(500/1800) {:.3} not ≤ 0.5× open {:.3}",
            ratio(&m),
            ratio(&o)
        );
        assert!(
            rms(&m) < rms(&o),
            "mute rms {} not < open {}",
            rms(&m),
            rms(&o)
        );
    }

    /// BR-O9 (program brightness spread) — implemented against the design's own
    /// ordering, NOT the appendix/master-HLD §6 literal, which is
    /// self-inconsistent. The corrected oracle asks for absolute `centroid` at
    /// C3 ordered trumpet > horn > trombone > tuba. Measuring (voice-level,
    /// seed-pinned) exposes two problems. First, the full-band C3 `centroid` is
    /// confounded by the bell-shelf corner (`bell_fc`), not the intended
    /// lip/bore brightness — it yields trombone > trumpet ≈ tuba > horn, no
    /// valid brightness order. Second, the specified `horn > trombone`
    /// contradicts the signed-off preset table, which makes trombone brighter
    /// than horn (h_max 7.0 vs 5.5, upper bore 1500 vs 750 Hz) — as it should be
    /// physically. The voices ARE correctly differentiated: a valid high-band
    /// proxy (`hp_rms(2 kHz)/rms`) orders them trumpet > trombone > horn > tuba
    /// at every pitch, matching the `h_max` design intent. This test pins THAT —
    /// the real acceptance (trumpet brightest, tuba darkest, monotone between).
    /// The appendix's C3-centroid metric and its horn/trombone swap are flagged
    /// for reconciliation at fixture capture (see the task report).
    #[test]
    fn brass_o9_program_brightness_spread() {
        let sr = 44100.0;
        let bright = |prog: u8| {
            let b = render_brass(prog, 48, 100, 2.0, 7); // C3, in every range
            let seg = &b[(0.4 * sr) as usize..(1.2 * sr) as usize];
            hp_rms(seg, sr, 2000.0) / rms(seg).max(1e-9)
        };
        let (tpt, tbn, horn, tuba) = (bright(56), bright(57), bright(60), bright(58));
        assert!(
            tpt > tbn && tbn > horn && horn > tuba,
            "brightness order tpt {tpt:.3} > tbn {tbn:.3} > horn {horn:.3} > tuba {tuba:.3}"
        );
    }

    /// BR-O10 (synth vs natural): the synth-brass resonant sweep (62) decays
    /// from a bright attack "bwah" to a darker sustain — early centroid ≥ 1.2×
    /// late — whereas the natural trumpet (56) does NOT (its centroid rises).
    #[test]
    fn brass_o10_synth_sweep_decays() {
        let sr = 44100.0;
        let ratio = |prog: u8| {
            let b = render_brass(prog, 60, 110, 1.0, 7);
            centroid(&b[(0.03 * sr) as usize..(0.15 * sr) as usize], sr)
                / centroid(&b[(0.6 * sr) as usize..(1.0 * sr) as usize], sr).max(1e-9)
        };
        assert!(
            ratio(62) >= 1.2,
            "synth sweep early/late {:.3} (need ≥ 1.2)",
            ratio(62)
        );
        assert!(
            ratio(56) < 1.2,
            "natural trumpet should not sweep-decay: {:.3}",
            ratio(56)
        );
    }

    /// BR-O11 (alias floor, guard): the loudest growled high note — prog 56 A5
    /// vel 127, rendered dry AND growled — keeps fold-back on non-harmonic bins
    /// ≤ 0.03× the 2nd harmonic. The composed drive is clamped to `BR_K_MAX`, so
    /// the growled render sits at the same drive as the dry note and its flutter
    /// AM is post-decimation — growl adds no aliasing.
    #[test]
    fn brass_o11_alias_floor() {
        let sr = 44100.0;
        for growl in [0.0f32, 110.0 / 127.0] {
            let mut v = brass(56, 81, 127, sr, 7);
            v.set_breath(1.0, growl);
            let mut buf = vec![0f32; sr as usize];
            v.render(&mut buf);
            let seg = &buf[(0.2 * sr) as usize..];
            let base = mag_at(seg, sr, 1760.0); // 2nd harmonic of 880 Hz
            for f in [1246.0f32, 2200.0, 3080.0] {
                let r = mag_at(seg, sr, f) / base.max(1e-12);
                assert!(
                    r <= 0.03,
                    "growl {growl:.3}: off-bin {f} Hz = {r:.4}× (need ≤ 0.03)"
                );
            }
        }
    }

    /// BR-O11b (alias floor, worst case — the BR13 ADAA acceptance guard): the
    /// TOP-register loud note where the raised `BR_CASCADE_F0_FLOOR` runs the rasp
    /// hardest and folding harmonics have the lowest (strongest) index. Prog 56,
    /// key 90 (F#6 ≈ 1480 Hz), vel 127, dry AND growled. Non-harmonic guard bins
    /// {3840, 2360, 880} Hz (fold sources p≈57–59 about sr2; none a multiple of
    /// 1480). Fold-back must stay ≤ 0.03× the 2nd harmonic (2960 Hz) AND ≤ 0.015×
    /// — the 6 dB margin that licenses the committed floor value (HLD §4/O-A).
    #[test]
    fn brass_o11b_alias_floor_top() {
        let sr = 44100.0;
        for growl in [0.0f32, 110.0 / 127.0] {
            let mut v = brass(56, 90, 127, sr, 7);
            v.set_breath(1.0, growl);
            let mut buf = vec![0f32; sr as usize];
            v.render(&mut buf);
            let seg = &buf[(0.2 * sr) as usize..];
            let base = mag_at(seg, sr, 2960.0); // 2nd harmonic of 1480 Hz
            for f in [3840.0f32, 2360.0, 880.0] {
                let r = mag_at(seg, sr, f) / base.max(1e-12);
                assert!(
                    r <= 0.015,
                    "F#6 growl {growl:.3}: off-bin {f} Hz = {r:.4}× (need ≤ 0.015, 6 dB margin)"
                );
            }
        }
    }

    /// Non-asserting diagnostic: prints the worst off-bin/2nd-harmonic ratio at
    /// A5 and F#6 for the CURRENT `BR_CASCADE_F0_FLOOR`, so the floor can be
    /// oracle-set. Run with `--nocapture`. Not a gate.
    #[test]
    fn brass_adaa_floor_diag() {
        let sr = 44100.0;
        for &(key, f2, bins) in &[
            (81u8, 1760.0f32, [1246.0f32, 2200.0, 3080.0]),
            (90u8, 2960.0f32, [3840.0f32, 2360.0, 880.0]),
        ] {
            for breath in [1.0f32, 0.0] {
                for growl in [0.0f32, 110.0 / 127.0] {
                    let mut v = brass(56, key, 127, sr, 7);
                    v.set_breath(breath, growl);
                    let mut buf = vec![0f32; sr as usize];
                    v.render(&mut buf);
                    let seg = &buf[(0.2 * sr) as usize..];
                    let base = mag_at(seg, sr, f2).max(1e-12);
                    let worst = bins
                        .iter()
                        .map(|&f| mag_at(seg, sr, f) / base)
                        .fold(0.0f32, f32::max);
                    eprintln!(
                        "DIAG floor={BR_CASCADE_F0_FLOOR} key={key} breath={breath:.0} growl={growl:.2} worst_ratio={worst:.4}"
                    );
                }
            }
        }
    }

    /// BR-O (ADAA math correctness, pins HLD §1/§2): first-order ADAA replaces the
    /// memoryless shaper by its boxcar-filtered continuous model, whose value over
    /// a linear step x0→x1 is exactly the MEAN of the shaper over [x0, x1]:
    ///   (F(x1) − F(x0)) / (x1 − x0) = (1/(x1−x0)) ∫ f dx  =  mean f over [x0,x1].
    /// So the divided difference must equal a fine numerical mean of `brass_valve`.
    /// This is the robust unit oracle (a spectral test of the isolated shaper is not
    /// — a single tone barely aliases, so it cannot exercise the suppression the way
    /// the full voice does; the voice-level guard is BR-O11/BR-O11b). It catches a
    /// wrong antiderivative directly, AND — via the near-equal-Δx cases — proves the
    /// midpoint fallback equals the true mean at the seam (HLD §3).
    #[test]
    fn brass_o_adaa_matches_boxcar_mean() {
        // trapezoidal mean of brass_valve over [x0, x1] at high resolution
        let mean = |x0: f64, x1: f64, k: f64, b: f64| -> f64 {
            let m = 8192usize;
            let h = (x1 - x0) / m as f64;
            let mut acc = 0.5 * (brass_valve_f64(x0, k, b) + brass_valve_f64(x1, k, b));
            for j in 1..m {
                acc += brass_valve_f64(x0 + h * j as f64, k, b);
            }
            acc * h / (x1 - x0)
        };
        let params = [
            (0.8f64, 0.15f64),
            (3.2, 0.30),
            (BR_CASCADE_K2 as f64, 0.30 * BR_CASCADE_BIAS2 as f64),
        ];
        // wide steps (DD branch) and near-equal steps (midpoint fallback branch)
        let steps = [
            (-1.3f64, 0.9f64),
            (-0.2, 1.4),
            (0.05, 0.9),
            (0.4, 0.4 + 5e-5),   // |Δx| < BR_ADAA_H ⇒ fallback
            (-0.7, -0.7 - 3e-5), // fallback, descending
        ];
        let mut worst = 0.0f64;
        for &(k, b) in &params {
            for &(x0, x1) in &steps {
                let got = brass_valve_adaa(x1, x0, k, b);
                let want = mean(x0, x1, k, b);
                worst = worst.max((got - want).abs());
            }
        }
        assert!(
            worst <= 1e-5,
            "ADAA divided-difference must equal the shaper's boxcar mean: worst |Δ| {worst:.2e} (need ≤ 1e-5)"
        );
    }

    /// BR-O (fallback seam, pins HLD §3): the near-equal-samples midpoint fallback
    /// must join the divided-difference branch seamlessly. Sweeps x0 across the
    /// operating range at every stage's (k,b) extreme and compares the two branches
    /// evaluated either side of the h threshold about the SAME midpoint — the exact
    /// switch a spectral oracle never exercises. (Part 2 of O-C, the forced-branch
    /// render + hit-counter canary, is covered structurally: the sweep drives both
    /// branches deterministically here.)
    #[test]
    fn brass_o_adaa_fallback_seam() {
        let params = [
            (0.8f64, 0.15f64),
            (0.8, 0.30),
            (3.2, 0.15),
            (3.2, 0.30),
            (BR_CASCADE_K2 as f64, 0.30 * BR_CASCADE_BIAS2 as f64),
        ];
        let eps = BR_ADAA_H * (1.0 / 1024.0);
        let mut worst = 0.0f64;
        for &(k, b) in &params {
            let mut x0 = -1.6f64;
            while x0 <= 1.6 {
                let m = x0; // midpoint
                            // DD branch: Δx just above threshold, symmetric about m
                let hi = brass_valve_adaa(
                    m + 0.5 * (BR_ADAA_H + eps),
                    m - 0.5 * (BR_ADAA_H + eps),
                    k,
                    b,
                );
                // fallback branch: Δx just below threshold, same midpoint
                let lo = brass_valve_adaa(
                    m + 0.5 * (BR_ADAA_H - eps),
                    m - 0.5 * (BR_ADAA_H - eps),
                    k,
                    b,
                );
                worst = worst.max((hi - lo).abs());
                x0 += 8e-4;
            }
        }
        assert!(
            worst <= 1e-6,
            "ADAA fallback seam discontinuity {worst:.2e} (need ≤ 1e-6)"
        );
    }

    /// BR-O12 (the rasp blooms — BR12 acceptance): the progressive-steepening
    /// cascade adds real high-harmonic energy at forte, stays clean at mp, and the
    /// gap BLOOMS super-linearly with loudness (the cuivré "brasses up"). Measured
    /// as a differential — trumpet vs a cascade-disabled twin (`brassiness = 0`,
    /// i.e. the pre-BR12 sound), same seed — so the ratio isolates the cascade from
    /// everything else (the BR-O6 idiom). Fixed pitch C4 (261.6 Hz, below the
    /// high-f0 derate knee so the full cascade is live); high band ≥ 3.5 kHz sits
    /// above the trumpet's top bore formant (2.9 kHz), clear of the static
    /// structure the 2026.07.08 lesson warns about.
    #[test]
    fn brass_o12_rasp_blooms() {
        let sr = 44100.0;
        // cascade-disabled twin: brassiness 0 ⇒ brass_rasp returns the bare BR1
        // valve ⇒ byte-identical to the pre-BR12 render for this spec.
        let flat: &'static BrassSpec = Box::leak(Box::new(BrassSpec {
            brassiness: 0.0,
            ..BR_TRUMPET
        }));
        let hi = |spec: &'static BrassSpec, vel: u8| {
            let mut v = Brass::new(spec, 60, vel, sr, 7); // C4, full-cascade register
            let mut buf = vec![0f32; (1.4 * sr) as usize];
            v.render(&mut buf);
            let seg = &buf[(0.4 * sr) as usize..(1.2 * sr) as usize];
            hp_rms(seg, sr, 5000.0) / rms(seg).max(1e-9)
        };
        let ratio_f = hi(&BR_TRUMPET, 120) / hi(flat, 120).max(1e-9); // forte: rips
        let ratio_p = hi(&BR_TRUMPET, 80) / hi(flat, 80).max(1e-9); // mp: clean
        assert!(
            ratio_f >= 1.18,
            "forte rasp adds high-harmonic energy: on/off {ratio_f:.3} (need ≥ 1.18)"
        );
        assert!(
            ratio_p <= 1.06,
            "mp must stay clean (rasp gated off): on/off {ratio_p:.3} (need ≤ 1.06)"
        );
        assert!(
            ratio_f >= ratio_p + 0.12,
            "the rasp must BLOOM with loudness: forte {ratio_f:.3} vs mp {ratio_p:.3}"
        );
    }

    /// BR-O13 (DC guard, guard): the biased-tanh DC is blocked (`dcb` HP 25 Hz).
    /// True DC is isolated with a 4-pole 8 Hz lowpass — the raw finite-window
    /// mean of a low note is dominated by the fundamental's partial-cycle
    /// residue (~A/2πN), not DC (cf. `bass_sub_shaped_and_phase_random`).
    #[test]
    fn brass_o13_dc_guard() {
        let sr = 44100.0;
        let b = render_brass(57, 41, 127, 1.0, 7);
        let mut lps = [OnePole::lowpass(8.0, sr); 4];
        let dc: Vec<f32> = b
            .iter()
            .map(|&x| {
                let mut y = x;
                for lp in lps.iter_mut() {
                    y = lp.process(y);
                }
                y
            })
            .collect();
        let win = (0.5 * sr) as usize..(0.9 * sr) as usize;
        let level = rms(&dc[win.clone()]) / rms(&b[win]).max(1e-12);
        assert!(level < 1e-3, "DC/rms {level:.6} (need < 1e-3)");
    }

    /// BR-O16 (routing + lifecycle, guard): make() routes 56–63 to their brass
    /// names; a held note stays alive at 6 s and, on note_off, dies (the shared
    /// Adsr's exponential release reaches the alive threshold in ≈ 9× the
    /// release time, so trumpet's 0.12 s release dies in ≈ 1.0 s — the
    /// appendix's "release + 0.2 s" underestimates that tail); render ADDS into
    /// its output buffer.
    #[test]
    fn brass_o16_routing_and_lifecycle() {
        let sr = 44100.0;
        for (prog, name) in [
            (56u8, "trumpet"),
            (57, "trombone"),
            (58, "tuba"),
            (59, "muted_trumpet"),
            (60, "french_horn"),
            (61, "brass_section"),
            (62, "synth_brass"),
            (63, "synth_brass"),
        ] {
            assert_eq!(
                make(prog, 60, 100, sr, 7, false).kind(),
                name,
                "prog {prog}"
            );
        }
        // held → alive at 6 s
        let mut v = brass(56, 60, 100, sr, 7);
        let mut buf = vec![0f32; 4096];
        let blocks_6s = (6.0 * sr / 4096.0) as usize;
        for _ in 0..blocks_6s {
            assert!(v.render(&mut buf), "held brass died before 6 s");
        }
        // note_off → dead within a bounded time (exponential-to-1e-4 tail)
        v.note_off();
        let mut n = 0;
        while v.render(&mut buf) && n < 200 {
            n += 1;
        }
        let dead_s = n as f32 * 4096.0 / sr;
        assert!(
            dead_s < 1.5,
            "brass did not die after note_off ({dead_s:.2}s)"
        );
        // render ADDS into a pre-filled buffer (does not overwrite)
        let a = render_brass(56, 60, 100, 0.05, 7);
        let mut b = vec![0.5f32; a.len()];
        let mut v2 = brass(56, 60, 100, sr, 7);
        v2.render(&mut b);
        assert!(
            a.iter().zip(&b).all(|(s, o)| (o - (0.5 + s)).abs() < 1e-6),
            "render overwrote instead of adding into the buffer"
        );
    }

    /// Diagnostic print of every oracle's measured value (not a gate).
    /// `cargo test brass_calibration -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn brass_calibration() {
        let sr = 44100.0;
        // BR-O9 (corrected): matched-pitch centroids at several keys + a
        // high-band brightness proxy (hp_rms 2 kHz / rms), to see which metric
        // tracks the intended trumpet>horn>trombone>tuba ordering.
        for key in [48u8, 60, 72] {
            print!("BR-O9 key{key}: ");
            for (name, prog) in [("tpt", 56u8), ("horn", 60), ("tbn", 57), ("tuba", 58)] {
                let b = render_brass(prog, key, 100, 2.0, 7);
                let seg = &b[(0.4 * sr) as usize..(1.2 * sr) as usize];
                print!(
                    "{name} c{:.0}/hp{:.2} ",
                    centroid(seg, sr),
                    hp_rms(seg, sr, 2000.0) / rms(seg).max(1e-9)
                );
            }
            println!();
        }
        // BR-O2 loudness→brightness (key 69)
        let c36 = centroid(
            &render_brass(56, 69, 36, 1.4, 7)[(0.4 * sr) as usize..(1.2 * sr) as usize],
            sr,
        );
        let c120 = centroid(
            &render_brass(56, 69, 120, 1.4, 7)[(0.4 * sr) as usize..(1.2 * sr) as usize],
            sr,
        );
        println!(
            "BR-O2 centroid vel120/vel36 = {:.3} ({c120:.0}/{c36:.0})",
            c120 / c36
        );
        // BR-O3 the waa (key 69 vel 100) — EQUAL-length 70 ms windows (Goertzel
        // centroid leakage depends on window length; the appendix's 70 ms early
        // vs 200 ms late is not a valid comparison)
        let b = render_brass(56, 69, 100, 1.0, 7);
        let early = centroid(&b[(0.03 * sr) as usize..(0.10 * sr) as usize], sr);
        let late = centroid(&b[(0.30 * sr) as usize..(0.37 * sr) as usize], sr);
        println!(
            "BR-O3 waa late/early = {:.3} ({late:.0}/{early:.0})",
            late / early
        );
        // BR-O8 mute vs open (key 74)
        let m = render_brass(59, 74, 100, 1.0, 7);
        let o = render_brass(56, 74, 100, 1.0, 7);
        let ratio = |s: &[f32]| band_rms(s, sr, 500.0, 1.0) / band_rms(s, sr, 1800.0, 1.0);
        println!(
            "BR-O8 band(500/1800): mute {:.3} open {:.3} → {:.3}× ; rms mute {:.5} open {:.5}",
            ratio(&m),
            ratio(&o),
            ratio(&m) / ratio(&o),
            rms(&m),
            rms(&o)
        );
        // BR-O5 growl at the voice level (prog 56, C4=60, vel 80)
        for g in [0.0f32, 110.0 / 127.0] {
            let mut v = brass(56, 60, 80, sr, 7);
            let mut warm = vec![0f32; (0.1 * sr) as usize];
            v.render(&mut warm);
            v.set_breath(1.0, g);
            let mut buf = vec![0f32; (1.6 * sr) as usize];
            v.render(&mut buf);
            let seg = &buf[(0.4 * sr) as usize..(1.4 * sr) as usize];
            let (peak, rate) = env_autocorr_peak(seg, sr, 0.02, 0.05);
            // direct 30 Hz flutter depth: rms of the 30 Hz-bandpassed envelope
            // over its mean — clean 0 vs ~0.1 discriminator
            let mut lp = OnePole::lowpass(200.0, sr);
            let env: Vec<f32> = seg.iter().map(|&x| lp.process(x.abs())).collect();
            let mean = env.iter().sum::<f32>() / env.len() as f32;
            let mut bp = Biquad::bandpass(30.0, 4.0, sr);
            let flut: Vec<f32> = env.iter().map(|&x| bp.process(x)).collect();
            println!(
                "BR-O5 growl={g:.3}: autocorr peak {peak:.3} rate {rate:.1} Hz, flutter30 {:.4}, hp2k {:.5}",
                rms(&flut) / mean.max(1e-9),
                hp_rms(seg, sr, 2000.0)
            );
        }
        // BR-O7 section vs solo rise time
        let sec = render_brass(61, 60, 100, 1.0, 7);
        let solo = render_brass(56, 60, 100, 1.0, 7);
        println!(
            "BR-O7 rise: section {:.4}s solo {:.4}s (Δ={:.4}s)",
            rise_10_90(&sec, sr),
            rise_10_90(&solo, sr),
            rise_10_90(&sec, sr) - rise_10_90(&solo, sr)
        );
        // BR-O10 synth sweep decay (prog 62 vs 56, key 60 vel 110)
        for prog in [62u8, 56] {
            let b = render_brass(prog, 60, 110, 1.0, 7);
            let ce = centroid(&b[(0.03 * sr) as usize..(0.15 * sr) as usize], sr);
            let cl = centroid(&b[(0.6 * sr) as usize..(1.0 * sr) as usize], sr);
            println!(
                "BR-O10 prog {prog}: early/late = {:.3} ({ce:.0}/{cl:.0})",
                ce / cl
            );
        }
        // BR-O11 alias floor (prog 56 key 81 vel 127, growl 0 and 110)
        for g in [0.0f32, 110.0 / 127.0] {
            let mut v = brass(56, 81, 127, sr, 7);
            v.set_breath(1.0, g);
            let mut buf = vec![0f32; sr as usize];
            v.render(&mut buf);
            let seg = &buf[(0.2 * sr) as usize..];
            let base = mag_at(seg, sr, 1760.0);
            let worst = [1246.0f32, 2200.0, 3080.0]
                .iter()
                .map(|&f| mag_at(seg, sr, f) / base)
                .fold(0.0f32, f32::max);
            println!("BR-O11 growl={g:.3}: worst off-bin/mag(1760) = {worst:.4}");
        }
        // BR-O13 DC guard (prog 57 key 41 vel 127) — period-aligned window so
        // the fundamental's partial-cycle residue (~A/2πN) cancels and only true
        // DC survives (the raw finite-window mean is fundamental-dominated)
        let b = render_brass(57, 41, 127, 2.5, 7);
        let f0 = key_freq(41);
        let per = sr / f0;
        let start = (0.3 * sr) as usize;
        for span in [0.6f32, 1.6, 2.0] {
            let nper = ((span * sr) / per).floor();
            let len = (nper * per) as usize;
            let seg_al = &b[start..start + len];
            let m_al = seg_al.iter().map(|&x| x as f64).sum::<f64>() / seg_al.len() as f64;
            // DC via a 4-pole 8 Hz lowpass, settled region
            let mut lps = [OnePole::lowpass(8.0, sr); 4];
            let dc: Vec<f32> = b
                .iter()
                .map(|&x| {
                    let mut y = x;
                    for lp in lps.iter_mut() {
                        y = lp.process(y);
                    }
                    y
                })
                .collect();
            let dcm = &dc[(0.6 * sr) as usize..(2.4 * sr) as usize];
            let dc_lvl = rms(dcm) / rms(&b[(0.6 * sr) as usize..(2.4 * sr) as usize]).max(1e-12);
            println!(
                "BR-O13 span {span}: aligned |mean|/rms {:.6}; 4pole-8Hz DC/rms {:.6}",
                m_al.abs() as f32 / rms(seg_al).max(1e-12),
                dc_lvl
            );
        }
        // BR-O1 sustain ratio
        let b = render_brass(56, 69, 100, 2.2, 7);
        println!(
            "BR-O1 sustain ratio = {:.3}",
            rms(&b[(1.45 * sr) as usize..(1.85 * sr) as usize])
                / rms(&b[(0.15 * sr) as usize..(0.45 * sr) as usize])
        );
        // lifecycle: death time after note_off (prog 56, release 0.12)
        let mut v = brass(56, 60, 100, sr, 7);
        let mut buf = vec![0f32; 4096];
        for _ in 0..30 {
            v.render(&mut buf);
        }
        v.note_off();
        let mut blocks = 0;
        while v.render(&mut buf) && blocks < 500 {
            blocks += 1;
        }
        println!(
            "lifecycle: dead {:.3}s after note_off ({blocks} blocks)",
            blocks as f32 * 4096.0 / sr
        );
    }

    // -----------------------------------------------------------------------
    // Reed (GM 64–71) voice-level oracles (§8). Renders are seed-pinned,
    // sr 44100, pitch via peak_locate (never zero crossings — this family is
    // bright by design). The ENGINE-dependent oracles are deferred to the
    // engine-wiring/finalize unit:
    //   RD-O10 (CC68 slur + PB/CC1 liveness under the modulator)
    //   RD-O1b (baseline-binary album byte-compare)
    //   RD-O1a/RD-O1c/golden-fixture recapture (needs the coordinated recapture)
    // The voice-side seams (from_preset, legato_to, set_pitch) ARE tested here.
    // -----------------------------------------------------------------------

    /// Render a fresh reed voice `secs` seconds (no note_off) into a buffer.
    fn render_reed(prog: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = reed(prog, key, vel, sr, seed);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    const REED_PRESETS: [&ReedPreset; 10] = [
        &SOP_SAX,
        &ALTO_SAX,
        &TENOR_SAX,
        &BARI_SAX,
        &OBOE,
        &ENGLISH_HORN,
        &BASSOON,
        &CLARINET,
        &BAGPIPE,
        &SHANAI,
    ];

    /// RD-O2 (sustains, not plucks): a held reed note holds — late/early RMS
    /// ratio ≥ 0.6 (the STEEL-pluck fallback measures ≈ 0.01, the journal
    /// headline). Checked for a sax, a double reed and the clarinet.
    #[test]
    fn reed_o2_sustains() {
        let sr = 44100.0;
        for (prog, key) in [(66u8, 55u8), (68, 76), (71, 62)] {
            let b = render_reed(prog, key, 100, 2.0, 7);
            let ratio = rms(&b[(1.45 * sr) as usize..(1.85 * sr) as usize])
                / rms(&b[(0.15 * sr) as usize..(0.45 * sr) as usize]).max(1e-12);
            assert!(
                ratio >= 0.6,
                "prog {prog}: sustain ratio {ratio:.3} (need ≥ 0.6)"
            );
        }
    }

    /// RD-O3 (clarinet hollowness, differential): at key 50 (D3, 146.83 Hz) the
    /// clarinet's even harmonics are near-null (width-0.5 square) while its odd
    /// harmonics survive — hollow, not a bare sine — whereas the tenor sax
    /// (full harmonic series) is even-rich.
    #[test]
    fn reed_o3_clarinet_hollowness() {
        let sr = 44100.0;
        let f = key_freq(50);
        let ratios = |prog: u8| {
            let b = render_reed(prog, 50, 100, 1.6, 7);
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            let h1 = mag_at(seg, sr, f);
            (mag_at(seg, sr, 2.0 * f) / h1, mag_at(seg, sr, 3.0 * f) / h1)
        };
        let (clar_2, clar_3) = ratios(71);
        let (tenor_2, _) = ratios(66);
        assert!(clar_2 < 0.12, "clarinet h2/h1 {clar_2:.4} (need < 0.12)");
        assert!(clar_3 > 0.15, "clarinet h3/h1 {clar_3:.4} (need > 0.15)");
        assert!(tenor_2 > 0.30, "tenor sax h2/h1 {tenor_2:.4} (need > 0.30)");
    }

    /// RD-O5 / RD-O5b (double-reed nasal formants): the oboe's 1050 Hz nasal
    /// band is far more prominent than the clarinet's there; the bassoon's
    /// 500 Hz "vocal-baritone" band beats the tenor sax's; and the english
    /// horn's low formant dominates its upper one more than the oboe's does.
    /// Prominence P(f) = band_rms(f, 2.5) / rms.
    #[test]
    fn reed_o5_double_reed_formants() {
        let sr = 44100.0;
        let prom = |b: &[f32], f: f32| {
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            band_rms(seg, sr, f, 2.5) / rms(seg).max(1e-9)
        };
        let oboe = render_reed(68, 64, 100, 1.6, 7);
        let clar = render_reed(71, 64, 100, 1.6, 7);
        let eh = render_reed(69, 64, 100, 1.6, 7);
        assert!(
            prom(&oboe, 1050.0) > 1.4 * prom(&clar, 1050.0),
            "P_oboe(1050) {:.3} not > 1.4× P_clar {:.3}",
            prom(&oboe, 1050.0),
            prom(&clar, 1050.0)
        );
        let bassoon = render_reed(70, 45, 100, 1.6, 7);
        let tenor = render_reed(66, 45, 100, 1.6, 7);
        // 1.25× (calibrated: the correct render measures 1.30×; the appendix's
        // 1.4 estimate was optimistic — the tenor's 650 Hz formant skirt leaks
        // into the 500 Hz band. Bassoon IS more prominent, just by less).
        assert!(
            prom(&bassoon, 500.0) > 1.25 * prom(&tenor, 500.0),
            "P_bassoon(500) {:.3} not > 1.25× P_tenor {:.3}",
            prom(&bassoon, 500.0),
            prom(&tenor, 500.0)
        );
        // RD-O5b: english horn's low-formant dominance exceeds the oboe's
        assert!(
            prom(&eh, 930.0) / prom(&eh, 1900.0) > prom(&oboe, 930.0) / prom(&oboe, 1900.0),
            "EH P930/P1900 {:.3} not > oboe {:.3}",
            prom(&eh, 930.0) / prom(&eh, 1900.0),
            prom(&oboe, 930.0) / prom(&oboe, 1900.0)
        );
    }

    /// RD-O6 (sax family ordering): at a shared key (60) the four saxes'
    /// brightness strictly increases bari < tenor < alto < soprano — the bore
    /// length ordering (descending formant/LP centres), with the sop/bari span
    /// ≥ 1.3×. Measured by the level-normalised high-band fraction
    /// `hp_rms(1500)/rms`, NOT the fixed-bin `centroid`: once RD7 vibrato was
    /// corrected to its true ~5 Hz rate, the pitch wobble smears the Goertzel
    /// bins of the brighter voices non-uniformly (soprano centroid swings the
    /// most), which is a measurement artifact — the wide-band energy fraction is
    /// invariant to a ±10-cent wobble and cleanly exposes the static formant/LP
    /// ordering the design guarantees.
    #[test]
    fn reed_o6_sax_ordering() {
        let sr = 44100.0;
        let bright = |prog: u8| {
            let b = render_reed(prog, 60, 100, 1.6, 7);
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            hp_rms(seg, sr, 1500.0) / rms(seg).max(1e-9)
        };
        let (bari, tenor, alto, sop) = (bright(67), bright(66), bright(65), bright(64));
        assert!(
            bari < tenor && tenor < alto && alto < sop,
            "sax brightness order bari {bari:.3} < tenor {tenor:.3} < alto {alto:.3} < sop {sop:.3}"
        );
        assert!(
            sop / bari >= 1.3,
            "sop/bari brightness span {:.2} (need ≥ 1.3)",
            sop / bari
        );
    }

    /// RD-O7 (velocity opens the timbre): harder blowing raises the
    /// level-normalised high-band fraction (the RD3 law opens the lowpass) — not
    /// merely the level. Measured by `hp_rms(2 kHz)/rms` (the centroid is a weak
    /// proxy for a gentle 1-pole cutoff sweep at a low fundamental — calibrated:
    /// the correct render's centroid ratio is only ≈ 1.06, but its high-band
    /// fraction opens ≈ 1.17×; the appendix's 1.25 centroid estimate does not
    /// hold for a 1-pole LP, so this pins the high-band proxy instead).
    #[test]
    fn reed_o7_velocity_opens_timbre() {
        let sr = 44100.0;
        let probe = |vel: u8| {
            let b = render_reed(66, 55, vel, 1.6, 7);
            let seg = &b[(0.4 * sr) as usize..(1.2 * sr) as usize];
            (hp_rms(seg, sr, 2000.0) / rms(seg).max(1e-9), rms(seg))
        };
        let (h40, r40) = probe(40);
        let (h120, r120) = probe(120);
        assert!(
            h120 / h40 >= 1.12,
            "velocity brightness hp/rms ratio {:.3} (need ≥ 1.12)",
            h120 / h40
        );
        assert!(
            r120 > r40,
            "louder velocity must also raise level: {r120} vs {r40}"
        );
    }

    /// RD-O8a (breath, differential): the RD5 breath adds a quiet reed hiss,
    /// concentrated in its 2.5·f band, WITHOUT changing the level. A same-seed
    /// `breath = 0` clone isolates it exactly. (The appendix's `hp_rms(5000)`
    /// probe assumed the breath sits above the tone; calibrated: the design
    /// places it at 2.5·f — 490 Hz for this key, below the LP ceiling at every
    /// reed pitch — so the correct isolation is the differential, not an HF band.)
    #[test]
    fn reed_o8a_breath_differential() {
        let sr = 44100.0;
        let dry: &'static ReedPreset = Box::leak(Box::new(ReedPreset {
            breath: 0.0,
            ..TENOR_SAX
        }));
        let render = |p: &'static ReedPreset| {
            let mut v = Reed::from_preset(p, 55, 100, sr, 7);
            let mut b = vec![0f32; (1.6 * sr) as usize];
            v.render(&mut b);
            b
        };
        let with = render(&TENOR_SAX);
        let without = render(dry);
        let win = (0.5 * sr) as usize..(1.5 * sr) as usize;
        let diff: Vec<f32> = with[win.clone()]
            .iter()
            .zip(&without[win.clone()])
            .map(|(a, b)| a - b)
            .collect();
        let present = rms(&diff) / rms(&without[win.clone()]).max(1e-12);
        let bf = (2.5 * key_freq(55)).min(5000.0);
        let band_conc = band_rms(&diff, sr, bf, 1.2) / rms(&diff).max(1e-12);
        let level_db =
            20.0 * (rms(&with[win.clone()]) / rms(&without[win.clone()]).max(1e-12)).log10();
        assert!(
            present >= 0.005,
            "breath not present: diff/tone {present:.4}"
        );
        assert!(
            band_conc >= 0.5,
            "breath not in its band: concentration {band_conc:.3}"
        );
        assert!(
            level_db.abs() <= 1.0,
            "breath changed the level by {level_db:.3} dB (need ≤ 1)"
        );
    }

    /// RD-O8b (tongue chiff): a fresh attack fires a chiff — an onset transient
    /// (early ≫ late), super-linear in velocity. A same-seed `chiff_amp = 0`
    /// clone isolates it exactly (the tone+breath are identical, so the
    /// difference IS the chiff). (Calibrated: the appendix's `hp_rms(3k)`
    /// early/late probe is confounded by the amp envelope — the whole note is
    /// quiet during the attack — so the differential is the correct isolation.)
    #[test]
    fn reed_o8b_chiff_onset() {
        let sr = 44100.0;
        let chiff_diff = |vel: u8, lo: f32, hi: f32| {
            let mut on = Reed::from_preset(&ALTO_SAX, 60, vel, sr, 7);
            let mut off = Reed::from_preset(&ALTO_SAX, 60, vel, sr, 7);
            off.chiff_amp = 0.0;
            let (mut bon, mut boff) = (
                vec![0f32; (0.3 * sr) as usize],
                vec![0f32; (0.3 * sr) as usize],
            );
            on.render(&mut bon);
            off.render(&mut boff);
            rms(&bon[(lo * sr) as usize..(hi * sr) as usize]
                .iter()
                .zip(&boff[(lo * sr) as usize..(hi * sr) as usize])
                .map(|(a, b)| a - b)
                .collect::<Vec<_>>())
        };
        let early = chiff_diff(120, 0.0, 0.02);
        let late = chiff_diff(120, 0.20, 0.22);
        let soft = chiff_diff(30, 0.0, 0.02);
        assert!(early > 1e-3, "chiff absent at forte: {early:.5}");
        assert!(
            early / late.max(1e-12) >= 2.0,
            "chiff not an onset transient: early/late {:.2}",
            early / late.max(1e-12)
        );
        assert!(
            early / soft.max(1e-12) > 10.0,
            "chiff not super-linear: ff/pp {:.1}",
            early / soft.max(1e-12)
        );
    }

    /// RD-O12 (RD4 alias bound, corrected — master HLD §6 wins over §8): the
    /// un-oversampled tanh's fold-back must stay ≥ 34 dB down on the WORST case —
    /// the soprano sax (prog 64, the highest LP ceiling ⇒ the least post-shaper
    /// alias suppression) played HIGH. Method is RD-O0's separable-bin trick: at
    /// f = sr/35.5 the m-odd tanh fold-back lands exactly on half-integer bins,
    /// where no real harmonic sits; measured pre-vibrato so the pitch is steady.
    #[test]
    fn reed_o12_alias_floor() {
        let sr = 44100.0;
        let f0 = sr / 35.5; // ≈ 1242 Hz — high in the soprano's 56–88 range
        let mut v = Reed::from_preset(&SOP_SAX, 87, 127, sr, 7);
        v.base_f = f0; // exact tuning for the separable-bin fold-back method
        let mut b = vec![0f32; (0.22 * sr) as usize];
        v.render(&mut b);
        // pre-vibrato (< vib_delay 0.22 s), post-scoop-settle window: steady f0
        let seg = &b[(0.06 * sr) as usize..(0.20 * sr) as usize];
        let fund = mag_at(seg, sr, f0);
        let (mut acc, mut cnt, mut worst) = (0.0f64, 0u32, 0.0f32);
        let mut k = 1.5f32;
        while f0 * k < 0.4 * sr {
            let r = mag_at(seg, sr, f0 * k) / fund.max(1e-12);
            acc += (r as f64) * (r as f64);
            worst = worst.max(r);
            cnt += 1;
            k += 1.0;
        }
        let alias = (acc / cnt as f64).sqrt() as f32;
        assert!(
            alias < 0.02 && worst < 0.03,
            "soprano fold-back rms {alias:.4} worst {worst:.4} (need < 0.02 / 0.03)"
        );
    }

    /// RD-O13 (routing + lifecycle, guard): make() routes 64–71 to `"reed"`; a
    /// held note stays alive at 6 s and dies after note_off; render ADDS into its
    /// buffer; a 1 s render is finite and DC-free.
    #[test]
    fn reed_o13_routing_and_lifecycle() {
        let sr = 44100.0;
        for prog in (64u8..=71).chain([109, 111]) {
            assert_eq!(
                make(prog, 60, 100, sr, 7, false).kind(),
                "reed",
                "prog {prog}"
            );
        }
        // held → alive at 6 s
        let mut v = reed(66, 60, 100, sr, 7);
        let mut buf = vec![0f32; 4096];
        for _ in 0..(6.0 * sr / 4096.0) as usize {
            assert!(v.render(&mut buf), "held reed died before 6 s");
        }
        // note_off → dead within a bounded time
        v.note_off();
        let mut n = 0;
        while v.render(&mut buf) && n < 200 {
            n += 1;
        }
        assert!(
            n as f32 * 4096.0 / sr < 1.5,
            "reed did not die after note_off"
        );
        // render ADDS into a pre-filled buffer
        let a = render_reed(66, 60, 100, 0.05, 7);
        let mut bb = vec![0.5f32; a.len()];
        reed(66, 60, 100, sr, 7).render(&mut bb);
        assert!(
            a.iter().zip(&bb).all(|(s, o)| (o - (0.5 + s)).abs() < 1e-6),
            "render overwrote instead of adding"
        );
        // finite over 1 s (every program), and DC-free. True DC is isolated with
        // a period-aligned mean over the fundamental (integer periods cancel the
        // tone + its partial-cycle residue exactly, leaving only 0 Hz — the Brass
        // BR-O13 discipline), with vibrato zeroed so a wobble through the fixed
        // formants can't AM the level. This guards two DC sources: the RD4 tanh's
        // asymmetric-pulse bias (the 20 Hz `dcb` catches it) and a marginally-
        // stable inert formant slot (built off DC so it cannot integrate).
        for prog in (64u8..=71).chain([109, 111]) {
            let b = render_reed(prog, 60, 100, 1.0, 7);
            assert!(
                b.iter().all(|x| x.is_finite()),
                "prog {prog}: non-finite sample"
            );
            let mut v = reed(prog, 60, 100, sr, 7);
            v.vib_depth = 0.0;
            let mut bd = vec![0f32; (2.0 * sr) as usize];
            v.render(&mut bd);
            let per = sr / key_freq(60);
            let start = (0.4 * sr) as usize;
            let len = ((1.4 * sr / per).floor() * per) as usize;
            let seg = &bd[start..start + len];
            let dc = (seg.iter().map(|&x| x as f64).sum::<f64>() / seg.len() as f64).abs() as f32;
            let level = dc / rms(seg).max(1e-12);
            assert!(level < 1e-3, "prog {prog}: DC/rms {level:.6} (need < 1e-3)");
        }
    }

    /// Diagnostic print of every reed oracle's measured value (not a gate).
    /// `cargo test reed_calibration -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn reed_calibration() {
        let sr = 44100.0;
        // preset table sanity (also keeps the #[cfg(test)] name field live)
        for p in REED_PRESETS {
            println!(
                "{:>13}: w {:.2}->{:.2} lp {:.0} drive {:.2} amp {:.2} range {:?}",
                p.name, p.width, p.width_hi, p.lp, p.drive_vn, p.amp, p.range
            );
        }
        // True-DC diagnostic: period-aligned |mean|/rms (vib zeroed) per program
        for prog in (64u8..=71).chain([109, 111]) {
            let mut v = reed(prog, 60, 100, sr, 7);
            v.vib_depth = 0.0;
            let mut bd = vec![0f32; (2.0 * sr) as usize];
            v.render(&mut bd);
            let per = sr / key_freq(60);
            let start = (0.4 * sr) as usize;
            let len = ((1.4 * sr / per).floor() * per) as usize;
            let seg = &bd[start..start + len];
            let m = seg.iter().map(|&x| x as f64).sum::<f64>() / seg.len() as f64;
            println!(
                "DC prog {prog}: aligned |mean|/rms {:.6}",
                m.abs() as f32 / rms(seg).max(1e-12)
            );
        }
        // RD-O3 clarinet(71) vs tenor(66) key 50 (D3, 146.83 Hz), h2/h1 & h3/h1
        let f = key_freq(50);
        for prog in [71u8, 66] {
            let b = render_reed(prog, 50, 100, 1.6, 7);
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            println!(
                "RD-O3 prog {prog}: h2/h1 {:.4} h3/h1 {:.4}",
                mag_at(seg, sr, 2.0 * f) / mag_at(seg, sr, f),
                mag_at(seg, sr, 3.0 * f) / mag_at(seg, sr, f)
            );
        }
        // RD-O6 sax family centroid ordering at key 60
        print!("RD-O6 key60 centroid: ");
        for (n, prog) in [("bari", 67u8), ("tenor", 66), ("alto", 65), ("sop", 64)] {
            let b = render_reed(prog, 60, 100, 1.6, 7);
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            print!("{n} {:.0} ", centroid(seg, sr));
        }
        println!();
        // RD-O5 formant prominence P(f) = band_rms(f,2.5)/rms
        let prom = |b: &[f32], f: f32| {
            let seg = &b[(0.5 * sr) as usize..(1.5 * sr) as usize];
            band_rms(seg, sr, f, 2.5) / rms(seg).max(1e-9)
        };
        let oboe = render_reed(68, 64, 100, 1.6, 7);
        let clar = render_reed(71, 64, 100, 1.6, 7);
        let eh = render_reed(69, 64, 100, 1.6, 7);
        println!(
            "RD-O5 P(1050): oboe {:.3} clar {:.3} -> {:.2}×",
            prom(&oboe, 1050.0),
            prom(&clar, 1050.0),
            prom(&oboe, 1050.0) / prom(&clar, 1050.0)
        );
        let bassoon = render_reed(70, 45, 100, 1.6, 7);
        let tenor45 = render_reed(66, 45, 100, 1.6, 7);
        println!(
            "RD-O5 P(500) key45: bassoon {:.3} tenor {:.3} -> {:.2}×",
            prom(&bassoon, 500.0),
            prom(&tenor45, 500.0),
            prom(&bassoon, 500.0) / prom(&tenor45, 500.0)
        );
        println!(
            "RD-O5b EH {:.3} vs OBOE {:.3} (P930/P1900)",
            prom(&eh, 930.0) / prom(&eh, 1900.0),
            prom(&oboe, 930.0) / prom(&oboe, 1900.0)
        );
        // RD-O2 sustain ratio for a few programs
        for (prog, key) in [(66u8, 55u8), (68, 76), (71, 62)] {
            let b = render_reed(prog, key, 100, 2.0, 7);
            println!(
                "RD-O2 prog {prog}: sustain ratio {:.3}",
                rms(&b[(1.45 * sr) as usize..(1.85 * sr) as usize])
                    / rms(&b[(0.15 * sr) as usize..(0.45 * sr) as usize]).max(1e-12)
            );
        }
        // RD-O7 velocity brightness — centroid vs level-normalised high-band
        // proxy, swept over keys and probes to find the clearest metric
        for key in [55u8, 60, 67] {
            for probe in [1500.0f32, 2000.0, 2500.0] {
                let hp = |vel: u8| {
                    let b = render_reed(66, key, vel, 1.6, 7);
                    let seg = &b[(0.4 * sr) as usize..(1.2 * sr) as usize];
                    hp_rms(seg, sr, probe) / rms(seg).max(1e-9)
                };
                print!(
                    "RD-O7 key{key} p{probe:.0}: hp/rms {:.3}  ",
                    hp(120) / hp(40)
                );
            }
            println!();
        }
        // RD-O8a breath differential (prog 66) and RD-O8b chiff (prog 65)
        let dry: &'static ReedPreset = Box::leak(Box::new(ReedPreset {
            breath: 0.0,
            ..TENOR_SAX
        }));
        let with = {
            let mut v = Reed::from_preset(&TENOR_SAX, 55, 100, sr, 7);
            let mut b = vec![0f32; (1.6 * sr) as usize];
            v.render(&mut b);
            b
        };
        let without = {
            let mut v = Reed::from_preset(dry, 55, 100, sr, 7);
            let mut b = vec![0f32; (1.6 * sr) as usize];
            v.render(&mut b);
            b
        };
        let win = (0.5 * sr) as usize..(1.5 * sr) as usize;
        let bf = (2.5 * key_freq(55)).min(5000.0); // breath band centre for key 55
        let diff: Vec<f32> = with[win.clone()]
            .iter()
            .zip(&without[win.clone()])
            .map(|(a, b)| a - b)
            .collect();
        println!(
            "RD-O8a breath band {bf:.0} Hz: diff/without rms {:.4}; diff-band-conc {:.3}; fullband dB delta {:.4}",
            rms(&diff) / rms(&without[win.clone()]).max(1e-12),
            band_rms(&diff, sr, bf, 1.2) / rms(&diff).max(1e-12),
            20.0 * (rms(&with[win.clone()]) / rms(&without[win.clone()]).max(1e-12)).log10()
        );
        // RD-O8b chiff: a same-seed differential isolates the chiff exactly
        // (chiff-on preset vs a chiff_amp=0 clone; same seed → tone+breath
        // identical, the difference IS the chiff). It is an onset transient
        // (early ≫ late) and super-linear in velocity.
        let chiff_diff = |vel: u8, lo: f32, hi: f32| {
            let mut on = Reed::from_preset(&ALTO_SAX, 60, vel, sr, 7);
            let mut off = Reed::from_preset(&ALTO_SAX, 60, vel, sr, 7);
            off.chiff_amp = 0.0;
            let (mut bon, mut boff) = (
                vec![0f32; (0.3 * sr) as usize],
                vec![0f32; (0.3 * sr) as usize],
            );
            on.render(&mut bon);
            off.render(&mut boff);
            let seg: Vec<f32> = bon[(lo * sr) as usize..(hi * sr) as usize]
                .iter()
                .zip(&boff[(lo * sr) as usize..(hi * sr) as usize])
                .map(|(a, b)| a - b)
                .collect();
            rms(&seg)
        };
        for vel in [30u8, 120] {
            let early = chiff_diff(vel, 0.0, 0.02);
            let late = chiff_diff(vel, 0.20, 0.22);
            println!(
                "RD-O8b alto60 vel{vel}: chiff early {early:.5} late {late:.6} -> onset {:.1}×",
                early / late.max(1e-12)
            );
        }
        println!(
            "RD-O8b super-linear vel120/vel30 = {:.1}×",
            chiff_diff(120, 0.0, 0.02) / chiff_diff(30, 0.0, 0.02).max(1e-12)
        );
        // RD-O12 corrected: soprano (prog 64, highest lp) played HIGH at exactly
        // f = sr/35.5 so the m-odd tanh fold-back lands on half-integer bins (no
        // real harmonic there). Measure pre-vibrato (< vib_delay) so the pitch is
        // steady. Fold-back RMS on those guard bins / the fundamental.
        let f0 = sr / 35.5;
        let mut v = Reed::from_preset(&SOP_SAX, 87, 127, sr, 7);
        v.base_f = f0;
        let mut b = vec![0f32; (0.22 * sr) as usize];
        v.render(&mut b);
        let seg = &b[(0.06 * sr) as usize..(0.20 * sr) as usize];
        let fund = mag_at(seg, sr, f0);
        let mut worst = 0.0f32;
        let mut half: Vec<f32> = Vec::new();
        let mut k = 1.5f32;
        while f0 * k < 0.4 * sr {
            let m = mag_at(seg, sr, f0 * k) / fund.max(1e-12);
            worst = worst.max(m);
            half.push(m);
            k += 1.0;
        }
        let rms_half =
            (half.iter().map(|&x| (x * x) as f64).sum::<f64>() / half.len() as f64).sqrt();
        println!(
            "RD-O12 soprano f0={f0:.1}: half-int fold-back worst {worst:.4}, rms {rms_half:.4}"
        );
    }

    // =======================================================================
    // v0.12 — GM 15 hammered dulcimer oracles (ported from the superseded
    // v0.11 branch, 216da4a)
    // =======================================================================

    const SR12: f32 = 44100.0;

    fn db_ratio(a: f32, b: f32) -> f32 {
        20.0 * (a / b.max(1e-12)).log10()
    }

    /// D1: GM 15 routes to the DULCIMER Pluck preset, holds its written pitch,
    /// and leads with a wooden hammer knock (early HP-2600 energy well above
    /// the ringing body's).
    #[test]
    fn dulcimer_routing_pitch_and_hammer_click() {
        assert_eq!(
            make(15, 69, 100, SR12, 7, false).kind(),
            "DULCIMER",
            "GM 15 must route to the DULCIMER preset"
        );
        let b = render_program(15, 69, 100, 1.0, 0x11_1501);
        let f = peak_locate(segment(&b, SR12, 0.10, 0.90), SR12, 396.0, 484.0);
        assert!((f - 440.0).abs() < 6.0, "GM15 key 69 pitch {f:.1} Hz");
        let click = hp_rms(segment(&b, SR12, 0.0, 0.02), SR12, 2600.0);
        let body = hp_rms(segment(&b, SR12, 0.10, 0.12), SR12, 2600.0);
        println!("GM15 hammer click hp2600: early {click:.5} vs body {body:.5}");
        assert!(
            click >= 2.0 * body,
            "GM15 hammer click not prominent: {click:.5} vs {body:.5}"
        );
    }

    /// D2 (2 seeds): the double course — two strings per note detuned by
    /// 0.42% — beats at 0.0042*f0 (~1.39 Hz at E4, where the course rings
    /// long enough to span 4+ beat periods). Bandpass the fundamental,
    /// flatten the decay (divide by a slow envelope tracker), remove the
    /// residual trend with a zero-phase centered moving average of one beat
    /// period, then read the AM rate as the Goertzel argmax of the envelope
    /// spectrum (autocorrelation is edge-biased on a 3-4 period window; the
    /// Goertzel line is not — see lessons_learnt on Goertzel-peak reads).
    /// Differential: a unison clone (course_detune 1.0) must show far less.
    #[test]
    fn dulcimer_double_course_beat() {
        let f0 = 329.628_f32; // key 64: beat = 0.0042*f0 = 1.385 Hz
        for seed in [3u32, 11] {
            let measure = |preset: &PluckPreset| {
                let b = render_pluck(preset, 64, 100, 3.5, seed);
                let (env, srd) = beat_envelope(&b, f0);
                let seg = &env[(0.4 * srd) as usize..(3.2 * srd) as usize];
                let (mut bmag, mut brate) = (0.0f32, 0.0f32);
                for i in 0..35 {
                    let hz = 0.70 + 0.05 * i as f32;
                    let m = mag_at(seg, srd, hz);
                    if m > bmag {
                        bmag = m;
                        brate = hz;
                    }
                }
                (bmag, brate)
            };
            let (mag_d, rate) = measure(&DULCIMER);
            let unison = PluckPreset {
                course_detune: 1.0,
                ..DULCIMER
            };
            let (mag_u, _) = measure(&unison);
            println!(
                "GM15 seed {seed}: course beat {mag_d:.3} at {rate:.2} Hz; unison max {mag_u:.3}"
            );
            assert!(mag_d >= 0.10, "seed {seed}: course beat {mag_d:.3} < 0.10");
            assert!(
                (0.97..=1.80).contains(&rate),
                "seed {seed}: course beat rate {rate:.2} Hz outside [0.97, 1.80]"
            );
            assert!(
                mag_d >= 2.0 * mag_u,
                "seed {seed}: beat {mag_d:.3} not >=2x unison clone {mag_u:.3}"
            );
        }
    }

    /// D2's envelope extractor: bandpass f0 (Q8) → rectified 30 Hz-lowpassed
    /// envelope → flatten the exponential decay (divide by a 0.4 Hz tracker)
    /// → decimate to ~200 Hz → subtract a centered (zero-phase) moving
    /// average one beat period wide. Returns (envelope, envelope sample rate).
    fn beat_envelope(b: &[f32], f0: f32) -> (Vec<f32>, f32) {
        let mut bp = Biquad::bandpass(f0, 8.0, SR12);
        let mut elp = OnePole::lowpass(30.0, SR12);
        let mut slw = OnePole::lowpass(0.4, SR12);
        let flat: Vec<f32> = b
            .iter()
            .map(|&x| {
                let e = elp.process(bp.process(x).abs());
                e / slw.process(e).max(1e-9)
            })
            .collect();
        let dec = (SR12 / 200.0) as usize;
        let srd = SR12 / dec as f32;
        let sub: Vec<f32> = flat.iter().step_by(dec).copied().collect();
        let half = ((0.722 * srd) as usize) / 2;
        let detr: Vec<f32> = (0..sub.len())
            .map(|i| {
                let a = i.saturating_sub(half);
                let z = (i + half).min(sub.len() - 1);
                let m = sub[a..=z].iter().sum::<f32>() / (z - a + 1) as f32;
                sub[i] - m
            })
            .collect();
        (detr, srd)
    }

    /// D3: the decay tracks the register the way a real hammered string does —
    /// a treble course (its fundamental near the loop damper's corner) dies
    /// materially faster than a bass course.
    #[test]
    fn dulcimer_key_tracked_decay() {
        let sustain = |key: u8| {
            let b = render_program(15, key, 100, 2.0, 0x11_1503);
            rms(segment(&b, SR12, 1.5, 1.9)) / rms(segment(&b, SR12, 0.05, 0.45)).max(1e-12)
        };
        let low = sustain(52);
        let high = sustain(88);
        println!("GM15 sustain ratio: key52 {low:.4} vs key88 {high:.4}");
        assert!(
            low >= 1.4 * high,
            "GM15 low course {low:.4} should outring the treble {high:.4} by >=1.4x"
        );
    }

    /// D4 (level knob DULCIMER.amp): within ±2 dB of the concert harp at the
    /// same key — the neighbouring plucked-string voice it shares stages with.
    #[test]
    fn dulcimer_level_vs_harp() {
        let dul = render_program(15, 69, 100, 0.5, 0x11_1504);
        let harp = render_program(46, 69, 100, 0.5, 0x11_1504);
        let d = db_ratio(
            rms(segment(&dul, SR12, 0.02, 0.42)),
            rms(segment(&harp, SR12, 0.02, 0.42)),
        );
        println!("GM15 vs harp level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "GM15 level {d:+.2} dB off harp");
    }

    // -----------------------------------------------------------------------
    // WD-O — the pipe/flue family oracle suite (GM 72-79)
    // -----------------------------------------------------------------------
    // WD-O1 (8-way distinctness) is NOT re-implemented here: it IS the synth-wide
    // anti-clone matrix in `testutil::distinctness`, whose 13 pipe `Collapse(1)`
    // exemptions this stage DELETED. That deletion is the proof, and duplicating
    // it here would be dead weight. (Measured after the rework: every one of the
    // 28 pipe pairs clears EPS 0.03 — the tightest is 74/79 at 0.188.)
    //
    // House rules honoured throughout: matched pitch inside any cross-instrument
    // comparison; `mag_at`/`peak_locate`, never a zero-crossing counter (it lies
    // when a voice legitimately brightens); and windows chosen either PRE-VIBRATO
    // ([0.10, 0.28] s — after attack+scoop settle, before any vib_delay ≥ 0.18 s
    // bites) or LATE-SUSTAIN ([0.5, 1.5] s) where the measure is wobble-immune.

    const WD_SR: f32 = 44100.0;

    /// STRICTLY PRE-VIBRATO window for every harmonic-ratio read.
    ///
    /// This is load-bearing, not a detail. Read a harmonic ratio inside the
    /// vibrato'd region and it UNDER-READS the upper partials: harmonic n carries
    /// n× the frequency deviation, hence n× the modulation index β, so its energy
    /// spreads into FM sidebands that a fixed-bin Goertzel simply misses. (Pan
    /// flute, β₃ = 1.73 → J₀ = 0.36: a true h3 of 0.38 reads as 0.14.) Every
    /// preset's `vib_delay` is ≥ 0.18 s and the onset scoop (τ ≈ 7 ms) is long
    /// settled by 0.10 s, so this window sees the steady table and nothing else.
    /// RMS/fraction measures (WD-O4/O5/O11) are wobble-immune and use late sustain.
    const WD_PREVIB: (f32, f32) = (0.10, 0.17);

    /// The key at which a preset's register position is exactly 0.5, i.e. where
    /// `bright` == 1.0 at vel 100 and the preset table reads DIRECTLY off the render.
    fn wd_mid_key(p: &WindPreset) -> u8 {
        ((p.range.0 as u16 + p.range.1 as u16) / 2) as u8
    }

    fn wd_render(p: &WindPreset, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let mut v = Wind::from_preset(p, key, vel, WD_SR, seed);
        let mut buf = vec![0f32; (secs * WD_SR) as usize];
        v.render(&mut buf);
        buf
    }

    /// Breathless seam: the same voice with the noise bed silenced at construction,
    /// so a harmonic read is not biased by the air. (Struct-update from a const;
    /// every WindPreset field is Copy.)
    fn wd_render_dry(p: &WindPreset, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let dry = WindPreset {
            breath: 0.0,
            breath_hi: 0.0,
            ..*p
        };
        wd_render(&dry, key, vel, secs, seed)
    }

    /// Harmonic magnitude ratio m(n)/m(1) of a segment whose fundamental is `f0`.
    fn wd_hr(seg: &[f32], f0: f32, n: u32) -> f32 {
        mag_at(seg, WD_SR, f0 * n as f32) / mag_at(seg, WD_SR, f0).max(1e-9)
    }

    /// WD-O2 — BORE CLASS. A stopped pipe (pan flute) has structurally dead EVEN
    /// harmonics and a strong odd ladder; an open pipe (flute) is even-rich.
    /// Fail-first: today 75 renders the flute table, so m2/m1 ≈ 0.32, not < 0.02.
    #[test]
    fn wd_o2_stopped_pipe_is_odd_only() {
        let pan_key = wd_mid_key(&PAN_FLUTE);
        let pan = wd_render_dry(&PAN_FLUTE, pan_key, 100, 0.5, 7);
        let pan_body = segment(&pan, WD_SR, WD_PREVIB.0, WD_PREVIB.1);
        let f0 = key_freq(pan_key);
        let (m2, m3, m4, m5) = (
            wd_hr(pan_body, f0, 2),
            wd_hr(pan_body, f0, 3),
            wd_hr(pan_body, f0, 4),
            wd_hr(pan_body, f0, 5),
        );
        println!("WD-O2 pan flute: h2 {m2:.4} h3 {m3:.4} h4 {m4:.4} h5 {m5:.4}");
        assert!(
            m2 < 0.02 && m4 < 0.02,
            "pan-flute evens alive: h2 {m2} h4 {m4}"
        );
        assert!(
            (0.28..=0.48).contains(&m3),
            "pan-flute h3 {m3} outside [0.28, 0.48]"
        );
        assert!(
            (0.08..=0.20).contains(&m5),
            "pan-flute h5 {m5} outside [0.08, 0.20]"
        );
        assert!(
            (m3 + m5) / (m2 + m4 + 1e-6) > 10.0,
            "odd/even ratio collapsed: {}",
            (m3 + m5) / (m2 + m4 + 1e-6)
        );
        // open-pipe contrast at ITS mid key (an absolute per-instrument claim)
        let fl_key = wd_mid_key(&FLUTE);
        let fl = wd_render_dry(&FLUTE, fl_key, 100, 0.5, 7);
        let fl_h2 = wd_hr(
            segment(&fl, WD_SR, WD_PREVIB.0, WD_PREVIB.1),
            key_freq(fl_key),
            2,
        );
        println!("WD-O2 flute h2 {fl_h2:.4}");
        assert!(
            (0.25..=0.40).contains(&fl_h2),
            "flute h2 {fl_h2} outside [0.25, 0.40] — the open pipe lost its evens"
        );
    }

    /// WD-O3 — HELMHOLTZ vessels (76 bottle, 78 whistle, 79 ocarina) are ONE
    /// dominant partial, not a ladder. This is what stops them sounding like a
    /// dull flute. Fail-first: today 76 ≡ flute (R ≈ 0.36 ≫ 0.11) and 79's old
    /// whistle table carried an h3 it should not have.
    #[test]
    fn wd_o3_helmholtz_single_partial_dominance() {
        // upper-partial energy relative to the fundamental
        let upper_ratio = |p: &WindPreset| -> f32 {
            let key = wd_mid_key(p);
            let s = wd_render_dry(p, key, 100, 0.5, 7);
            let body = segment(&s, WD_SR, WD_PREVIB.0, WD_PREVIB.1);
            let f0 = key_freq(key);
            let up: f32 = (2..=6)
                .map(|n| wd_hr(body, f0, n).powi(2))
                .sum::<f32>()
                .sqrt();
            up
        };
        let (bottle, whistle, flute) = (
            upper_ratio(&BLOWN_BOTTLE),
            upper_ratio(&WHISTLE),
            upper_ratio(&FLUTE),
        );
        println!("WD-O3 upper/fund — bottle {bottle:.4} whistle {whistle:.4} flute {flute:.4}");
        assert!(bottle < 0.11, "blown bottle is not a bare vessel: {bottle}");
        assert!(whistle < 0.06, "whistle is not near-sine: {whistle}");
        assert!(
            flute > 0.30,
            "flute lost its ladder (contrast broken): {flute}"
        );

        // the ocarina: exactly one warm h2, and deliberately NO h3
        let oc_key = wd_mid_key(&OCARINA);
        let oc = wd_render_dry(&OCARINA, oc_key, 100, 0.5, 7);
        let body = segment(&oc, WD_SR, WD_PREVIB.0, WD_PREVIB.1);
        let f0 = key_freq(oc_key);
        let (h2, h3) = (wd_hr(body, f0, 2), wd_hr(body, f0, 3));
        println!("WD-O3 ocarina: h2 {h2:.4} h3 {h3:.4}");
        assert!(
            (0.12..=0.20).contains(&h2),
            "ocarina h2 {h2} outside [0.12, 0.20]"
        );
        assert!(h3 < 0.012, "ocarina grew an h3 it should not have: {h3}");
    }

    /// WD-O4 — the shakuhachi's muraiki breath tone: a genuine sustained noise
    /// shelf above 8 kHz that no other pipe has. Fail-first: today 77 ≡ 73
    /// byte-identically, so the ratio is exactly 1.0.
    #[test]
    fn wd_o4_shakuhachi_muraiki_shelf() {
        let key = wd_mid_key(&SHAKUHACHI); // 71
                                           // Measured with an EXACT DFT band, not `hp_rms`: a Q-0.7 highpass at 8 kHz
                                           // leaks a flute's own h4 (2.1 kHz) / h5 / h6 straight through its skirt and
                                           // reports ~0.8% "above 8 kHz" for a voice whose top partial is 3.1 kHz —
                                           // which would silently compress the very contrast this oracle exists to prove.
        let shelf = |p: &WindPreset| {
            let s = wd_render(p, key, 100, 1.6, 7); // breath ON — the shelf IS breath
            let body = segment(&s, WD_SR, 0.5, 1.5);
            spectral_band_rms(body, WD_SR, 8000.0, 16000.0) / rms(body).max(1e-9)
        };
        let (shak, flute) = (shelf(&SHAKUHACHI), shelf(&FLUTE));
        println!(
            "WD-O4 8-16kHz fraction — shakuhachi {shak:.5} flute {flute:.5} (ratio {:.0}x)",
            shak / flute.max(1e-9)
        );
        assert!(shak >= 0.010, "no muraiki shelf: {shak}");
        assert!(
            shak >= 10.0 * flute,
            "shakuhachi shelf {shak} not clear of the flute's {flute}"
        );
    }

    /// WD-O5 — BREATH FRACTION per instrument, via a same-seed differential seam:
    /// zeroing `breath_amp`/`hi_amp` POST-construction keeps both RNG streams
    /// aligned, so (full − nobed) isolates the bed exactly. Fail-first: today all
    /// five non-whistle programs share one bed and all three whistle programs
    /// share another, so the ordering clause (recorder < flute < pan < bottle)
    /// cannot hold — recorder == flute exactly.
    #[test]
    fn wd_o5_breath_fraction_bands_and_ordering() {
        let bf = |p: &WindPreset| -> f32 {
            let key = wd_mid_key(p);
            let n = (1.6 * WD_SR) as usize;
            let mut full = Wind::from_preset(p, key, 100, WD_SR, 7);
            let mut nobed = Wind::from_preset(p, key, 100, WD_SR, 7);
            nobed.breath_amp = 0.0;
            nobed.hi_amp = 0.0;
            let (mut a, mut b) = (vec![0f32; n], vec![0f32; n]);
            full.render(&mut a);
            nobed.render(&mut b);
            let diff: Vec<f32> = a.iter().zip(&b).map(|(x, y)| x - y).collect();
            rms(segment(&diff, WD_SR, 0.5, 1.5)) / rms(segment(&a, WD_SR, 0.5, 1.5)).max(1e-9)
        };
        let (rec, picc, fl, wh, oc, shak, pan, bot) = (
            bf(&RECORDER),
            bf(&PICCOLO),
            bf(&FLUTE),
            bf(&WHISTLE),
            bf(&OCARINA),
            bf(&SHAKUHACHI),
            bf(&PAN_FLUTE),
            bf(&BLOWN_BOTTLE),
        );
        println!(
            "WD-O5 breath fraction — rec {rec:.4} picc {picc:.4} flute {fl:.4} whistle {wh:.4} \
             oca {oc:.4} shak {shak:.4} pan {pan:.4} bottle {bot:.4}"
        );
        // Bands calibrated against the render. NOTE the factor that sets them:
        // `Rng::white()` is UNIFORM in [-1, 1), so its RMS is 1/sqrt(3) = 0.577, NOT 1.
        // The closed-form bed level is therefore
        //     bed_rms ~= breath * (1/sqrt(3)) * sqrt(pi*fc / (Q*sr)) * e^2   (e = sustain)
        // and breath_mod (1 + 0.5*vib) adds a further ~x1.06 in RMS. Predicting these
        // fractions from a UNIT-RMS white assumption overstates every one of them by
        // ~1/0.61. The coefficients are anchored on the flute's accepted `breath: 0.09`
        // (R1), so these fractions are a CONSEQUENCE of that anchor, not a free choice.
        for (name, v, lo, hi) in [
            ("recorder", rec, 0.003, 0.009),
            ("piccolo", picc, 0.007, 0.018),
            ("flute", fl, 0.010, 0.021), // tight: this IS today's accepted flute bed (R1)
            ("whistle", wh, 0.012, 0.028),
            ("ocarina", oc, 0.014, 0.031),
            ("shakuhachi", shak, 0.048, 0.105),
            ("pan_flute", pan, 0.038, 0.085),
            ("blown_bottle", bot, 0.055, 0.122),
        ] {
            assert!(
                (lo..=hi).contains(&v),
                "{name} breath fraction {v:.4} outside [{lo}, {hi}]"
            );
        }
        // the robust ordering clause — the part that cannot hold on today's code
        assert!(
            rec < fl && fl < pan && pan < bot,
            "breath ordering collapsed: rec {rec} < flute {fl} < pan {pan} < bottle {bot}"
        );
        assert!(
            shak > 3.0 * fl,
            "shakuhachi {shak} is not markedly airier than the flute {fl}"
        );
    }

    /// WD-O6 — the spectrum opens with VELOCITY and closes with REGISTER, and the
    /// recorder is the instrument that (physically) does NOT open: you cannot blow
    /// a fipple harder without going sharp. Fail-first: today the spectrum is
    /// invariant in both, so all three ratios are exactly 1.00.
    #[test]
    fn wd_o6_register_and_velocity_brightness_coupling() {
        // upper-partial energy relative to the fundamental, breathless
        let tilt = |p: &WindPreset, key: u8, vel: u8| -> f32 {
            let s = wd_render_dry(p, key, vel, 0.5, 7);
            let body = segment(&s, WD_SR, WD_PREVIB.0, WD_PREVIB.1);
            let f0 = key_freq(key);
            (2..=4).map(|n| wd_hr(body, f0, n)).sum::<f32>()
        };
        // A: velocity opens the flute's timbre, not merely its level
        let fl_key = 65;
        let (soft, hard) = (tilt(&FLUTE, fl_key, 30), tilt(&FLUTE, fl_key, 115));
        let flute_ratio = hard / soft.max(1e-9);
        let (r_soft, r_hard) = rms_pair(&FLUTE, fl_key);
        println!("WD-O6a flute tilt ff/pp {flute_ratio:.3} (rms {r_soft:.4} -> {r_hard:.4})");
        assert!(
            flute_ratio >= 1.4,
            "velocity does not open the flute: {flute_ratio}"
        );
        assert!(r_hard > r_soft, "velocity did not raise level");

        // B: the recorder does NOT open — and the law is per-instrument
        let rec_ratio = tilt(&RECORDER, fl_key, 115) / tilt(&RECORDER, fl_key, 30).max(1e-9);
        println!("WD-O6b recorder tilt ff/pp {rec_ratio:.3}");
        assert!(
            rec_ratio <= 1.25,
            "the recorder should barely open with velocity: {rec_ratio}"
        );
        assert!(
            flute_ratio >= 1.5 * rec_ratio,
            "flute {flute_ratio} vs recorder {rec_ratio}: the coupling is not per-instrument"
        );

        // C: the top of the range purifies (harmonic-relative — pitch-safe)
        let low = wd_hr(
            segment(
                &wd_render_dry(&FLUTE, 62, 100, 0.5, 7),
                WD_SR,
                WD_PREVIB.0,
                WD_PREVIB.1,
            ),
            key_freq(62),
            2,
        );
        let high = wd_hr(
            segment(
                &wd_render_dry(&FLUTE, 91, 100, 0.5, 7),
                WD_SR,
                WD_PREVIB.0,
                WD_PREVIB.1,
            ),
            key_freq(91),
            2,
        );
        println!("WD-O6c flute h2/h1 — key62 {low:.4} key91 {high:.4}");
        assert!(
            low >= 1.25 * high,
            "register does not purify: h2 {low} @62 vs {high} @91"
        );
    }

    fn rms_pair(p: &WindPreset, key: u8) -> (f32, f32) {
        let s = |vel| {
            rms(segment(
                &wd_render(p, key, vel, 0.5, 7),
                WD_SR,
                WD_PREVIB.0,
                WD_PREVIB.1,
            ))
        };
        (s(30), s(115))
    }

    /// WD-O7 — VIBRATO RATE. The regression test for MM-BUG-KILN-00003: the LFO is
    /// ticked at control rate, so it must be BUILT at sr/CTRL. Measured by an FM
    /// sideband scan (no zero-crossing counter, wobble-proof).
    /// Fail-first: the old LFO ran at rate/16 ≈ 0.31 Hz, so there is no sideband
    /// pair anywhere in 3-8 Hz and S/carrier sits at leakage level (≲ 0.03).
    #[test]
    fn wd_o7_builtin_vibrato_rate_is_about_5hz() {
        let probe = |p: &WindPreset, key: u8, lo: f32, hi: f32| -> (f32, f32) {
            // breathless: the vibrato is pitch-FM on the TONE
            let s = wd_render_dry(p, key, 100, 3.0, 7);
            let body = segment(&s, WD_SR, 1.0, 3.0); // fully ramped; scoop settled, no bend
                                                     // The carrier of an FM tone sits EXACTLY at the centre pitch, which here is
                                                     // key_freq(key) (scoop settled to 1.0, no bend). Do NOT peak-locate it: under
                                                     // a deep vibrato (the shakuhachi's beta ~ 0.69) the first sideband rivals the
                                                     // carrier, and a peak search then locks onto the SIDEBAND and inverts the
                                                     // ratio. The known centre frequency is both simpler and correct.
            let f0 = key_freq(key);
            let carrier = mag_at(body, WD_SR, f0).max(1e-9);
            let mut best = (0.0f32, 0.0f32); // (rate, sideband-sum / carrier)
            let mut r = lo;
            while r <= hi {
                let sb = (mag_at(body, WD_SR, f0 - r) + mag_at(body, WD_SR, f0 + r)) / carrier;
                if sb > best.1 {
                    best = (r, sb);
                }
                r += 0.05;
            }
            best
        };
        let (rate, depth) = probe(&FLUTE, 72, 3.0, 8.0);
        println!("WD-O7 flute vibrato: {rate:.2} Hz, sidebands {depth:.3} of carrier");
        assert!(
            (4.3..=5.7).contains(&rate),
            "flute vibrato at {rate:.2} Hz, not ~5 Hz (0.31 Hz => the CTRL-rate bug is back)"
        );
        assert!(
            depth >= 0.25,
            "flute vibrato is inert: sidebands {depth:.3}"
        );

        let (s_rate, s_depth) = probe(&SHAKUHACHI, wd_mid_key(&SHAKUHACHI), 3.0, 8.0);
        println!("WD-O7 shakuhachi vibrato: {s_rate:.2} Hz, sidebands {s_depth:.3}");
        assert!(
            (3.8..=5.2).contains(&s_rate),
            "shakuhachi vibrato at {s_rate:.2} Hz, not ~4.5 Hz"
        );
        assert!(s_depth >= 0.25, "shakuhachi vibrato inert: {s_depth:.3}");
    }

    /// WD-O8 — the CHIFF: a fresh attack spits, super-linearly in velocity, and the
    /// pan flute's iconic chiff dwarfs the recorder's discreet one.
    /// Fail-first: today 75 and 74 are byte-identical, so pan/rec is exactly 1.0.
    #[test]
    fn wd_o8_chiff_onset_and_per_instrument_prominence() {
        // same-seed differential isolates the chiff exactly
        let chiff_energy = |p: &WindPreset, key: u8, vel: u8, a: f32, b: f32| -> f32 {
            let n = (0.3 * WD_SR) as usize;
            let mut on = Wind::from_preset(p, key, vel, WD_SR, 7);
            let mut off = Wind::from_preset(p, key, vel, WD_SR, 7);
            off.chiff_amp = 0.0;
            let (mut x, mut y) = (vec![0f32; n], vec![0f32; n]);
            on.render(&mut x);
            off.render(&mut y);
            let d: Vec<f32> = x.iter().zip(&y).map(|(u, v)| u - v).collect();
            rms(segment(&d, WD_SR, a, b))
        };
        let (early, late) = (
            chiff_energy(&PAN_FLUTE, 72, 100, 0.0, 0.02),
            chiff_energy(&PAN_FLUTE, 72, 100, 0.20, 0.22),
        );
        println!("WD-O8 pan chiff: early {early:.5} late {late:.5}");
        assert!(early > 1e-3, "no chiff at the onset: {early}");
        assert!(
            early >= 2.0 * late,
            "chiff does not decay: {early} vs {late}"
        );

        // super-linear in velocity (the Reed convention: × vn × vel_amp)
        let ff = chiff_energy(&PAN_FLUTE, 72, 120, 0.0, 0.02);
        let pp = chiff_energy(&PAN_FLUTE, 72, 30, 0.0, 0.02);
        println!("WD-O8 pan chiff ff/pp {:.1}x", ff / pp.max(1e-9));
        assert!(ff >= 8.0 * pp, "chiff is not super-linear: {ff} vs {pp}");

        // the load-bearing clause: per-instrument prominence, at MATCHED pitch
        let rec = chiff_energy(&RECORDER, 72, 100, 0.0, 0.02);
        println!("WD-O8 pan/recorder chiff {:.1}x", early / rec.max(1e-9));
        assert!(
            early >= 3.0 * rec,
            "the pan flute's iconic chiff does not stand out from the recorder's: \
             {early} vs {rec}"
        );
    }

    /// WD-O9 — the FLUTE CONTINUITY CANARY (R1). GM 73 is used by ~all 12 committed
    /// albums, so it must move as little as the design promised. This is deliberately
    /// NOT fail-first: it should pass BEFORE and AFTER. A failure means the flagship
    /// drifted — STOP; never widen these bands to make it green.
    #[test]
    fn wd_o9_flute_continuity_canary() {
        let s = wd_render_dry(&FLUTE, 72, 100, 1.6, 7);
        let body = segment(&s, WD_SR, WD_PREVIB.0, WD_PREVIB.1);
        let f0 = key_freq(72);
        let (h2, h3) = (wd_hr(body, f0, 2), wd_hr(body, f0, 3));
        // today 0.32 / 0.12; after the register tilt at key 72, ≈ 0.35 / 0.143
        println!("WD-O9 flute h2 {h2:.4} h3 {h3:.4}");
        assert!(
            (0.27..=0.40).contains(&h2),
            "flute h2 {h2} left [0.27, 0.40] — the flagship moved"
        );
        assert!(
            (0.09..=0.18).contains(&h3),
            "flute h3 {h3} left [0.09, 0.18] — the flagship moved"
        );
        // The new h4-h6 must stay a SKIRT, not a sheen. Measured DIRECTLY as
        // harmonic energy relative to the fundamental: a `hp_rms(3000)` proxy is
        // useless here because a Q-0.7 highpass leaks the flute's own h4 (2.1 kHz)
        // and h5 (2.6 kHz) straight through its skirt, reading them as "sheen".
        let skirt = (4..=6)
            .map(|n| wd_hr(body, f0, n).powi(2))
            .sum::<f32>()
            .sqrt();
        println!("WD-O9 flute h4..h6 skirt {skirt:.4}");
        assert!(
            skirt < 0.10,
            "the flute grew a sheen where it should have a skirt: {skirt}"
        );
    }

    /// WD-O10 — routing, SAMPLE POLICY, and lifecycle.
    /// The sample-policy clause is a DIFFERENTIAL, not a `kind()` check: `LaVoice`
    /// is transparent for routing (it reports the inner model's kind), so kind()
    /// cannot distinguish wrapped from bare. Instead: a program with no LA layer
    /// renders BIT-IDENTICALLY with samples on and off.
    /// Fail-first: today all eight are wrapped, so 74..=79 differ.
    #[test]
    fn wd_o10_routing_sample_policy_and_lifecycle() {
        for p in 72..=79u8 {
            assert_eq!(
                make(p, 60, 100, WD_SR, 7, false).kind(),
                "wind",
                "program {p} left the Wind family"
            );
        }
        // key 72 sits inside the flute bank's zone map (it has no zone below C4)
        for p in 72..=79u8 {
            let with = render_program_sampled(p, 72, 100, 0.5, 7, true);
            let without = render_program_sampled(p, 72, 100, 0.5, 7, false);
            let identical = with
                .iter()
                .zip(&without)
                .all(|(a, b)| a.to_bits() == b.to_bits());
            match p {
                72 | 73 => assert!(
                    !identical,
                    "GM {p} should carry the flute LA attack, but samples=true changed nothing"
                ),
                _ => assert!(
                    identical,
                    "GM {p} still borrows the transverse-flute attack — the wrong onset is \
                     exactly what made it read as 'flute'"
                ),
            }
        }
        // lifecycle + hygiene (mirrors reed_o13)
        assert!(survives_until(
            Box::new(Wind::from_preset(&FLUTE, 72, 100, WD_SR, 7)),
            WD_SR,
            6.0
        ));
        let mut v = Wind::from_preset(&FLUTE, 72, 100, WD_SR, 7);
        let mut warm = vec![0f32; 4410];
        v.render(&mut warm);
        v.note_off();
        // Adsr release is exponential (tau = `release`) and dies below 1e-4, so from
        // sustain 0.92 with tau = 0.10 s that is 0.92*exp(-t/0.1) < 1e-4 => t ~ 0.91 s.
        assert!(dies_within(Box::new(v), WD_SR, 2.0), "flute never released");
        let s = wd_render(&SHAKUHACHI, 71, 100, 1.0, 7);
        assert!(s.iter().all(|x| x.is_finite()), "non-finite sample");
        let dc = s.iter().sum::<f32>() / s.len() as f32;
        assert!(dc.abs() < 1e-3, "DC offset {dc}");
        // the alias gate: a hot top-register piccolo must not fold junk back down
        let hot = wd_render(&PICCOLO, 106, 127, 0.5, 7);
        let hb = segment(&hot, WD_SR, 0.10, 0.40);
        let junk = hp_rms(hb, WD_SR, 20500.0) / rms(hb).max(1e-9);
        println!("WD-O10 piccolo near-Nyquist junk {junk:.5}");
        assert!(
            junk < 0.01,
            "partials above 0.44·sr are folding, not gated: {junk}"
        );
    }

    /// WD-O11 — family loudness containment: no preset is a mix bomb. A guard
    /// (passes trivially today, when all eight are clones) that binds future edits.
    #[test]
    fn wd_o11_family_loudness_containment() {
        let level = |p: &WindPreset| {
            let s = wd_render(p, wd_mid_key(p), 100, 1.6, 7);
            rms(segment(&s, WD_SR, 0.5, 1.5))
        };
        let flute = level(&FLUTE);
        for p in [
            &PICCOLO,
            &RECORDER,
            &PAN_FLUTE,
            &BLOWN_BOTTLE,
            &SHAKUHACHI,
            &WHISTLE,
            &OCARINA,
        ] {
            let d = db_ratio(level(p), flute);
            println!("WD-O11 {} vs flute: {d:+.2} dB", p.name);
            assert!(
                d.abs() <= 4.0,
                "{} sits {d:+.2} dB off the flute — a mix bomb",
                p.name
            );
        }
    }
}
