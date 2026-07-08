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
//!   Wind     — sine + harmonics + breath, with a pitch scoop into the note
//!   Bowed    — sawtooth through a violin body, with scoop, attack bow
//!              noise, and bow-pressure brightness
//!
//! Timing realism: sustained families speak slower at low velocity, the way
//! a gently-bowed or gently-blown note actually starts.

use crate::dsp::{
    key_freq, vel_amp, Adsr, Biquad, BlepPulse, BlepSaw, Burst, DelayLine, Drift, OnePole, Rng,
    Sine,
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

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "modal"
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
    pub cab_lp: f32,                      // clean-amp cab rolloff, 0 = none (HLD G2)
    // --- HLD family B: parallel one-shot transients ---
    pub click: f32,            // pick/slap onset hardness (0 = none)
    pub click_hp: f32,         // click filter corner
    pub click_post: bool,      // false: knocks the body (pre-EQ); true: post-out
    pub attack_noise: f32,     // finger/fret noise level (0 = none, post-out)
    pub stop_thump: f32,       // release thud level (0 = none, armed by note_off)
    pub sub_shape: (f32, f32), // sub waveshaper (2f, 3f) amounts (MUTED grit / B5)
    pub sub_ramp: u32,         // sub fade-in samples
    pub grit: bool,            // per-voice soft-clip (MUTED palm chug, G4)
    pub wound_all: bool,       // K4: wound full-range (bass family) vs key-split (guitars)
    pub harmonic: bool,        // prog-31 flageolet: loop retuned to 2f/3f (G7)
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
    harmonic: false,
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
    cab_lp: 4500.0, // light clean-combo speaker rolloff
    click: 1.8,
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
    click: 2.2, // the pick hits harder through an amp
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
    sub: 0.35,             // the chug's thud carries the weight
    sub_shape: (0.6, 0.4), // 2f/3f enrichment: a thud, not a sine (G4)
    sub_ramp: 90,          // the thud speaks fast
    grit: true,            // palm-mute soft-clip grit
    click: 1.4,            // palm chuff
    click_hp: 900.0,
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
        }
    }

    /// Retune to a new frequency; the ringing energy stays in the string.
    fn retune(&mut self, f: f32) {
        self.target = Self::delay_for(f, self.bright, self.sr).min(self.max_delay);
        self.loop_gain = 10f32.powf(-3.0 / (self.t60 * f));
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
        self.dl.push(self.damp.process(s) * self.loop_gain + input);
        s
    }
}

/// K3 polarization coupling strength: strong enough for a measurable
/// secondary rise (oracle 15), weak enough to keep long notes bounded —
/// each loop stays a contraction (loop_gain < 1) and the skew-symmetric
/// cross-injection adds no energy (V4/DSP-5).
const K_COUPLE: f32 = 0.02;

/// G6 release-darken targets: while released, each polarization's damper
/// glides toward this floor at control rate (already-dark presets are
/// unaffected — the glide only ever darkens).
const REL_FLOOR_H: f32 = 600.0;
const REL_FLOOR_V: f32 = 700.0;
const REL_DARKEN_K: f32 = 0.010; // per control tick: τ ≈ 36 ms

/// K4 Stage 1 wound-ness: bass strings are wound full-range; guitars cross
/// from wound to plain around G3 (key 55). Pure arithmetic — no allpass
/// (Stage 2 dispersion stays deferred, §7).
pub(crate) fn wound_factor(wound_all: bool, key: u8) -> f32 {
    if wound_all {
        1.0
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
    base_f: f32,
    bend: f32,
    harm: f32, // G7 flageolet multiple (1.0 = normal), composed into every retune
    pickup: Option<(DelayLine, f32)>, // magnetic pickup position comb
    sub: Option<(Sine, f32, f32)>, // (osc, gain, decay) fundamental weight
    sub_env: f32,
    sub_shape: (f32, f32), // (2f, 3f) waveshaper amounts on the sub
    sub_ramp: u32,
    // HLD family B one-shots, all fed by the voice's own rng
    onset_pre: Option<Burst>,  // pick click / palm chuff — knocks the body
    onset_post: Option<Burst>, // finger noise / slap pop — after the out-LP
    stop: Option<Burst>,       // release thump, armed by note_off
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
        let wound = wound_factor(p.wound_all, key);
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

        Pluck {
            horiz: KsLoop::new(f, bright, t60, &exc, sr),
            vert: KsLoop::new(f * 1.0013, bright * 1.15, t60 * 0.42, &exc, sr),
            h_prev: 0.0,
            v_prev: 0.0,
            k_couple: K_COUPLE,
            base_f: note_f,
            bend: 1.0,
            harm,
            pickup: (p.pickup > 0.0).then(|| {
                // the pickup senses the string a fraction of its length from
                // the bridge: a feedforward comb with a 2·pos·period delay
                let d = 2.0 * p.pickup * period;
                (DelayLine::new(d as usize + 8), d)
            }),
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
                    self.vert
                        .set_bright(bv + REL_DARKEN_K * (REL_FLOOR_V - bv), f * 1.0013);
                }
            }
            // K3: skew-symmetric polarization coupling — energy sloshes
            // between the planes (the slow secondary bloom of a real string),
            // none is created; each loop remains a contraction
            let hc = self.horiz.tick(inject + self.k_couple * self.v_prev);
            let vc = self.vert.tick(inject * 0.7 - self.k_couple * self.h_prev);
            self.h_prev = hc;
            self.v_prev = vc;
            let mut y = 0.74 * hc + 0.26 * vc;
            if self.grit {
                // palm-mute chug: the palm+pick+amp chain compresses (G4)
                y = (y * 2.0).tanh() * 0.5;
            }
            if let Some((dl, d)) = &mut self.pickup {
                dl.push(y);
                y = (y - dl.tap(*d)) * 0.75;
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
            if let Some(lp) = &mut self.out_lp {
                y = lp.process(y);
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
            sr,
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

/// Tremulant (rate Hz, depth) each organ program idles at. The CC1 mod
/// wheel morphs the rate from here toward the Leslie's fast speed — the
/// slewing lives in the engine, per channel, so all of a channel's organ
/// voices share one rotor.
pub fn organ_trem_base(program: u8) -> (f32, f32) {
    match program {
        18 => (6.5, 0.10),
        16 | 17 => (5.5, 0.06),
        _ => (4.2, 0.04),
    }
}

fn organ(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Organ {
    let (trem_hz, trem_depth) = organ_trem_base(program);
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
            trem_hz,
            trem_depth,
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
            trem_hz,
            trem_depth,
            0.20,
            0.0,
            0.32,
        ),
    }
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
            legato_enabled: false,
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
            layer.osc.set_freq(
                self.base_f * layer.ratio * self.bend * (1.0 + vib + drift),
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

fn choir(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    let (f1, f2, f3) = if program == 52 {
        (660.0, 1120.0, 2500.0)
    } else {
        (330.0, 870.0, 2300.0)
    };
    let qs = [9.0, 10.0, 9.0];
    let start = [500.0, 1400.0, 2400.0]; // closed-mouth schwa
    let mut s = SawStack::new(
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
    );
    s.legato_enabled = true;
    s
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

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "wind"
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

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "bowed"
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
        11 => Box::new(bell(key, vel, sr, seed, VIBES, noise_off, 0.002, 0.8, 0.45)),
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
        29 | 30 => Box::new(Pluck::new(&DRIVE, key, vel, sr, seed)),
        31 => Box::new(Pluck::new(&HARMONIC, key, vel, sr, seed)), // G7 flageolet
        32 => Box::new(Pluck::new(&UPRIGHT, key, vel, sr, seed)),  // B2
        33 => Box::new(Pluck::new(&BASS, key, vel, sr, seed)),
        38 | 39 => Box::new(SynthBass::new(program, key, vel, sr, seed)), // B4
        34 => Box::new(Pluck::new(&PICK, key, vel, sr, seed)),            // B2
        36 | 37 => Box::new(Pluck::new(&SLAP, key, vel, sr, seed)),       // B2
        35 => Box::new(Pluck::new(&FRETLESS, key, vel, sr, seed)),
        40..=45 | 110 => {
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
        80..=87 => Box::new(lead(program, key, vel, sr, seed)),
        88..=95 => Box::new(pad(program, key, vel, sr, seed)),
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

    #[test]
    fn marimba_xylophone_have_wood_bar_envelopes() {
        let sr = 44100.0;
        let key = 69;
        let vibe = render_program(11, key, 105, 2.0, 17);
        let marimba = render_program(12, key, 105, 2.0, 17);
        let xylophone = render_program(13, key, 105, 2.0, 17);

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
        let vibe_click = click_ratio(&vibe, 2600.0);
        let marimba_click = click_ratio(&marimba, 1800.0);
        let xylo_click = click_ratio(&xylophone, 3200.0);
        assert!(
            marimba_click > 1.6 * vibe_click,
            "marimba wood click missing: marimba {marimba_click} vs vibes {vibe_click}"
        );
        assert!(
            xylo_click > 1.6 * vibe_click,
            "xylophone wood click missing: xylo {xylo_click} vs vibes {vibe_click}"
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
        assert_eq!(wound_factor(true, 70), 1.0);
        assert_eq!(wound_factor(false, 60), 0.0);
        assert!(wound_factor(false, 45) > 0.3);
        assert!(wound_factor(false, 31) >= 1.0);
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

    // ---- synth-lead voice (GM 80-87) ----

    fn render_saw(v: &mut SawStack, sr: f32, secs: f32) -> Vec<f32> {
        let mut buf = vec![0f32; (sr * secs) as usize];
        v.render(&mut buf);
        buf
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

    /// Oracle 7b: the SawStack families this change refactors — pads, choir,
    /// strings — render bit-for-bit as the baseline (origin/main) binary.
    /// Hashes pinned from the baseline; a future SawStack/LayerOsc refactor that
    /// drifts them trips here.
    #[test]
    fn sawstack_families_byte_identical() {
        let sr = 44100.0;
        let hash = |mut v: SawStack| {
            let mut buf = vec![0f32; (sr * 0.5) as usize];
            v.render(&mut buf);
            buf.iter().fold(0xcbf29ce484222325u64, |acc, &s| {
                (acc ^ s.to_bits() as u64).wrapping_mul(0x100000001b3)
            })
        };
        assert_eq!(
            hash(pad(95, 60, 100, sr, 7)),
            0xb0bdc70da0091298,
            "pad(95) drifted"
        );
        assert_eq!(
            hash(choir(52, 60, 100, sr, 7)),
            0xb6bf7e8fefbc82f1,
            "choir(52) drifted"
        );
        assert_eq!(
            hash(strings(48, 60, 100, sr, 7)),
            0x65817f27e894bcac,
            "strings(48) drifted"
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
}
