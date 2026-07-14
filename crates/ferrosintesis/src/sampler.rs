//! LA-style sample layer — the Roland D-50 trick: a short PCM attack
//! transient supplies the first ~200 ms (the bow bite, the breath chiff —
//! exactly what synthesis fakes worst), then crossfades into the modeled
//! sustain, which keeps all its expressive vibrato, scoop and dynamics.
//!
//! The transients are trimmed from VSCO 2 Community Edition (CC0 / public
//! domain) sustains and embedded from two compile-time asset crates, so the tool
//! remains a single self-contained executable. Each zone's root frequency was
//! measured by autocorrelation, so repitching is cent-accurate.

use crate::dsp::{key_freq, vel_amp, Rng};
use crate::voices::Voice;
use std::sync::OnceLock;

pub struct Zone {
    root: f32,
    data: Vec<f32>,
}

pub struct HitSample {
    data: Vec<f32>,
}

/// Minimal RIFF walker for the bank's own files (16-bit mono 44.1 kHz).
fn parse_wav(bytes: &[u8]) -> Vec<f32> {
    assert!(&bytes[0..4] == b"RIFF" && &bytes[8..12] == b"WAVE");
    let mut pos = 12;
    let mut data = Vec::new();
    while pos + 8 <= bytes.len() {
        let id = &bytes[pos..pos + 4];
        let len = u32::from_le_bytes(bytes[pos + 4..pos + 8].try_into().unwrap()) as usize;
        let body = &bytes[pos + 8..(pos + 8 + len).min(bytes.len())];
        if id == b"fmt " {
            let channels = u16::from_le_bytes(body[2..4].try_into().unwrap());
            let sr = u32::from_le_bytes(body[4..8].try_into().unwrap());
            let bits = u16::from_le_bytes(body[14..16].try_into().unwrap());
            assert!(
                channels == 1 && sr == 44100 && bits == 16,
                "sample bank must be 16-bit mono 44.1 kHz"
            );
        } else if id == b"data" {
            data = body
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes([c[0], c[1]]) as f32 / 32768.0)
                .collect();
        }
        pos += 8 + len + (len & 1);
    }
    assert!(!data.is_empty(), "sample bank file has no data chunk");
    data
}

#[cfg(feature = "embedded-samples")]
fn embedded_wav(name: &str) -> &'static [u8] {
    ferrosintesis_samples_core::get(name)
        .or_else(|| ferrosintesis_samples_orchestral::get(name))
        .unwrap_or_else(|| panic!("embedded sample inventory is missing {name}"))
}

#[cfg(not(feature = "embedded-samples"))]
fn embedded_wav(name: &str) -> &'static [u8] {
    panic!("sample {name} requested from a modeled-only ferrosintesis build")
}

macro_rules! bank {
    ($($file:literal => $root:expr),+ $(,)?) => {
        vec![$(Zone {
            root: $root,
            data: parse_wav(embedded_wav($file)),
        }),+]
    };
}

macro_rules! hit_bank {
    ($($file:literal),+ $(,)?) => {
        vec![$(HitSample {
            data: parse_wav(embedded_wav($file)),
        }),+]
    };
}

// Roots measured by autocorrelation in the prep script
// (see ../../tools/ferrosintesis-samples/README.md).
fn violin_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "violin_G3_f.wav" => 196.00,
            "violin_E4_f.wav" => 329.33,
            "violin_C5_f.wav" => 519.94,
            "violin_G5_f.wav" => 786.90,
            "violin_C6_f.wav" => 1040.45,
            "violin_E6_f.wav" => 1329.58,
        )
    })
}

fn violin_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "violin_G3_p.wav" => 195.11,
            "violin_E4_p.wav" => 329.51,
            "violin_C5_p.wav" => 521.61,
            "violin_G5_p.wav" => 787.21,
            "violin_C6_p.wav" => 1045.77,
            "violin_E6_p.wav" => 1320.88,
        )
    })
}

fn flute() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "flute_C4.wav" => 523.23,
            "flute_A4.wav" => 879.92,
            "flute_E5.wav" => 1320.47,
            "flute_A5.wav" => 1757.81,
            "flute_C6.wav" => 2091.31,
        )
    })
}

fn piano_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_pp.wav" => 65.05,
            "piano_G2_pp.wav" => 97.77,
            "piano_C3_pp.wav" => 130.68,
            "piano_G3_pp.wav" => 195.31,
            "piano_C4_pp.wav" => 261.04,
            "piano_G4_pp.wav" => 393.15,
            "piano_C5_pp.wav" => 523.65,
            "piano_G5_pp.wav" => 784.41,
            "piano_C6_pp.wav" => 1051.84,
        )
    })
}

fn piano_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_mf.wav" => 65.17,
            "piano_G2_mf.wav" => 98.10,
            "piano_C3_mf.wav" => 130.94,
            "piano_G3_mf.wav" => 196.23,
            "piano_C4_mf.wav" => 261.25,
            "piano_G4_mf.wav" => 393.58,
            "piano_C5_mf.wav" => 524.52,
            "piano_G5_mf.wav" => 785.35,
            "piano_C6_mf.wav" => 1050.22,
        )
    })
}

fn piano_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_f.wav" => 65.52,
            "piano_G2_f.wav" => 98.33,
            "piano_C3_f.wav" => 131.19,
            "piano_G3_f.wav" => 195.73,
            "piano_C4_f.wav" => 261.74,
            "piano_G4_f.wav" => 393.96,
            "piano_C5_f.wav" => 525.21,
            "piano_G5_f.wav" => 786.26,
            "piano_C6_f.wav" => 1050.00,
        )
    })
}

fn piano_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_pp_rr2.wav" => 65.05,
            "piano_G2_pp_rr2.wav" => 97.77,
            "piano_C3_pp_rr2.wav" => 130.60,
            "piano_G3_pp_rr2.wav" => 194.91,
            "piano_C4_pp_rr2.wav" => 261.00,
            "piano_G4_pp_rr2.wav" => 392.77,
            "piano_C5_pp_rr2.wav" => 523.95,
            "piano_G5_pp_rr2.wav" => 784.04,
            "piano_C6_pp_rr2.wav" => 1049.08,
        )
    })
}

fn piano_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_mf_rr2.wav" => 65.51,
            "piano_G2_mf_rr2.wav" => 98.28,
            "piano_C3_mf_rr2.wav" => 131.12,
            "piano_G3_mf_rr2.wav" => 196.23,
            "piano_C4_mf_rr2.wav" => 261.29,
            "piano_G4_mf_rr2.wav" => 393.76,
            "piano_C5_mf_rr2.wav" => 524.92,
            "piano_G5_mf_rr2.wav" => 785.18,
            "piano_C6_mf_rr2.wav" => 1049.43,
        )
    })
}

fn piano_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "piano_C2_f_rr2.wav" => 65.58,
            "piano_G2_f_rr2.wav" => 98.43,
            "piano_C3_f_rr2.wav" => 131.20,
            "piano_G3_f_rr2.wav" => 196.39,
            "piano_C4_f_rr2.wav" => 261.73,
            "piano_G4_f_rr2.wav" => 393.77,
            "piano_C5_f_rr2.wav" => 525.19,
            "piano_G5_f_rr2.wav" => 786.16,
            "piano_C6_f_rr2.wav" => 1050.12,
        )
    })
}

fn trumpet_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trumpet_F2_p.wav" => 174.88,
            "trumpet_C3_p.wav" => 259.21,
            "trumpet_G3_p.wav" => 392.78,
            "trumpet_D4_p.wav" => 586.53,
            "trumpet_A4_p.wav" => 877.64,
        )
    })
}

fn trumpet_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trumpet_F2_f.wav" => 172.61,
            "trumpet_C3_f.wav" => 261.15,
            "trumpet_G3_f.wav" => 393.83,
            "trumpet_D4_f.wav" => 588.04,
            "trumpet_A4_f.wav" => 886.84,
        )
    })
}

fn mutetpt_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "mutetpt_A#2_p.wav" => 232.97,
            "mutetpt_D3_p.wav" => 293.86,
            "mutetpt_G3_p.wav" => 392.99,
            "mutetpt_D4_p.wav" => 586.63,
            "mutetpt_A4_p.wav" => 880.37,
        )
    })
}

fn mutetpt_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "mutetpt_A#2_f.wav" => 233.07,
            "mutetpt_D3_f.wav" => 293.30,
            "mutetpt_G3_f.wav" => 392.47,
            "mutetpt_D4_f.wav" => 586.39,
            "mutetpt_A4_f.wav" => 880.34,
        )
    })
}

fn trombone_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trombone_F1_p.wav" => 87.34,
            "trombone_A#1_p.wav" => 116.31,
            "trombone_D2_p.wav" => 146.73,
            "trombone_F2_p.wav" => 174.45,
            "trombone_C3_p.wav" => 261.43,
            "trombone_F3_p.wav" => 349.09,
        )
    })
}

fn trombone_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "trombone_F1_f.wav" => 87.21,
            "trombone_A#1_f.wav" => 116.56,
            "trombone_D2_f.wav" => 146.73,
            "trombone_F2_f.wav" => 174.53,
            "trombone_C3_f.wav" => 261.56,
            "trombone_F3_f.wav" => 349.05,
        )
    })
}

fn tuba_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "tuba_A#0_p.wav" => 58.01,
            "tuba_D#1_p.wav" => 78.25,
            "tuba_A#1_p.wav" => 116.03,
            "tuba_D2_p.wav" => 146.34,
            "tuba_F2_p.wav" => 174.46,
            "tuba_A#2_p.wav" => 231.99,
        )
    })
}

fn tuba_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "tuba_A#0_f.wav" => 58.35,
            "tuba_D#1_f.wav" => 77.78,
            "tuba_A#1_f.wav" => 116.34,
            "tuba_D2_f.wav" => 145.88,
            "tuba_F2_f.wav" => 174.42,
            "tuba_A#2_f.wav" => 233.19,
        )
    })
}

fn horn_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "horn_A#1_p.wav" => 116.90,
            "horn_D2_p.wav" => 148.36,
            "horn_F2_p.wav" => 173.95,
            "horn_A2_p.wav" => 219.46,
            "horn_C3_p.wav" => 260.59,
            "horn_D4_p.wav" => 604.11,
        )
    })
}

fn horn_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "horn_A#1_f.wav" => 116.81,
            "horn_D2_f.wav" => 146.41,
            "horn_F2_f.wav" => 173.93,
            "horn_A2_f.wav" => 219.08,
            "horn_C3_f.wav" => 260.84,
            "horn_D4_f.wav" => 604.11,
        )
    })
}

fn oboe_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "oboe_D3_p.wav" => 293.50,
            "oboe_F3_p.wav" => 347.64,
            "oboe_A#3_p.wav" => 464.35,
            "oboe_D4_p.wav" => 586.46,
            "oboe_F4_p.wav" => 698.81,
            "oboe_A#4_p.wav" => 935.72,
        )
    })
}

fn oboe_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "oboe_D3_f.wav" => 294.16,
            "oboe_F3_f.wav" => 349.95,
            "oboe_A#3_f.wav" => 466.12,
            "oboe_D4_f.wav" => 588.05,
            "oboe_F4_f.wav" => 698.94,
            "oboe_A#4_f.wav" => 930.35,
        )
    })
}

fn bassoon_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "bassoon_A#0_p.wav" => 58.31,
            "bassoon_F1_p.wav" => 87.26,
            "bassoon_C2_p.wav" => 130.70,
            "bassoon_G2_p.wav" => 195.98,
            "bassoon_D#3_p.wav" => 312.70,
            "bassoon_C4_p.wav" => 523.95,
        )
    })
}

fn bassoon_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "bassoon_A#0_f.wav" => 58.25,
            "bassoon_F1_f.wav" => 87.29,
            "bassoon_C2_f.wav" => 130.76,
            "bassoon_G2_f.wav" => 195.94,
            "bassoon_D#3_f.wav" => 311.06,
            "bassoon_C4_f.wav" => 523.15,
        )
    })
}

fn clarinet_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "clarinet_A#2_p.wav" => 232.55,
            "clarinet_D3_p.wav" => 293.36,
            "clarinet_F3_p.wav" => 349.08,
            "clarinet_A#3_p.wav" => 466.23,
            "clarinet_D4_p.wav" => 586.91,
            "clarinet_F4_p.wav" => 698.75,
        )
    })
}

fn clarinet_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "clarinet_A#2_f.wav" => 233.09,
            "clarinet_D3_f.wav" => 292.97,
            "clarinet_F3_f.wav" => 348.60,
            "clarinet_A#3_f.wav" => 466.38,
            "clarinet_D4_f.wav" => 587.88,
            "clarinet_F4_f.wav" => 700.07,
        )
    })
}

fn nylon() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "nylon_E2.wav" => 82.47,
            "nylon_B2.wav" => 124.07,
            "nylon_E3.wav" => 165.21,
            "nylon_A#3.wav" => 234.63,
            "nylon_E4.wav" => 326.69,
            "nylon_A#4.wav" => 466.15,
            "nylon_E5.wav" => 661.48,
        )
    })
}

// String sections for GM 48-49: one bank per dynamic, cello section covering
// the low split and violin section the high — `nearest` picks the section by
// root, so a low pad gets celli and a high line gets violins. Roots measured
// by autocorrelation (both sections sound one octave above their VSCO labels).
fn strsec_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_p.wav" => 65.48,
            "celens_G1_p.wav" => 97.46,
            "celens_D2_p.wav" => 146.97,
            "celens_A2_p.wav" => 219.85,
            "celens_E3_p.wav" => 329.02,
            "celens_B3_p.wav" => 493.92,
            "vlnens_G2_p.wav" => 196.06,
            "vlnens_D3_p.wav" => 293.66,
            "vlnens_A3_p.wav" => 440.80,
            "vlnens_E4_p.wav" => 660.20,
            "vlnens_B4_p.wav" => 989.79,
            "vlnens_D5_p.wav" => 1175.21,
        )
    })
}

fn strsec_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_f.wav" => 65.38,
            "celens_G1_f.wav" => 97.71,
            "celens_D2_f.wav" => 146.73,
            "celens_A2_f.wav" => 219.17,
            "celens_E3_f.wav" => 328.79,
            "celens_B3_f.wav" => 493.91,
            "vlnens_G2_f.wav" => 195.56,
            "vlnens_D3_f.wav" => 292.71,
            "vlnens_A3_f.wav" => 441.25,
            "vlnens_E4_f.wav" => 657.60,
            "vlnens_B4_f.wav" => 991.44,
            "vlnens_D5_f.wav" => 1170.87,
        )
    })
}

// GM 43 contrabass LA attack: the cello-section arco *bite*, whose low celens
// zones already sit on the contrabass register (celens_C1 measures 65.4 Hz =
// C2, celens_G1 = G2). Only the low zones are needed — the part never plays
// above ~D3 — and `nearest` repitches them by well under a tone. The bite is
// what synthesis fakes worst; the waveguide keeps the expressive sustain.
fn contrabass_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_p.wav" => 65.48,
            "celens_G1_p.wav" => 97.46,
            "celens_D2_p.wav" => 146.97,
        )
    })
}

fn contrabass_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_f.wav" => 65.38,
            "celens_G1_f.wav" => 97.71,
            "celens_D2_f.wav" => 146.73,
        )
    })
}

/// Attack-transient bank for the GM 43 contrabass (cello-section arco, low
/// zones). Velocity picks the soft / loud layer as elsewhere (VSCO v1/v3).
pub fn contrabass_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        contrabass_f()
    } else {
        contrabass_p()
    }
}

// GM 42 cello LA attack: the cello-section arco bite across the cello's full
// register — the celens zones ARE cellos (celens_C1 measures 65 Hz = C2 up to
// celens_B3 ≈ B4), so `nearest` picks the right zone per note.
fn cello_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_p.wav" => 65.48,
            "celens_G1_p.wav" => 97.46,
            "celens_D2_p.wav" => 146.97,
            "celens_A2_p.wav" => 219.85,
            "celens_E3_p.wav" => 329.02,
            "celens_B3_p.wav" => 493.92,
        )
    })
}

fn cello_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    B.get_or_init(|| {
        bank!(
            "celens_C1_f.wav" => 65.38,
            "celens_G1_f.wav" => 97.71,
            "celens_D2_f.wav" => 146.73,
            "celens_A2_f.wav" => 219.17,
            "celens_E3_f.wav" => 328.79,
            "celens_B3_f.wav" => 493.91,
        )
    })
}

/// Attack-transient bank for the GM 42 cello (cello-section arco, full range).
pub fn cello_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        cello_f()
    } else {
        cello_p()
    }
}

fn drum_crash() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| {
        hit_bank!(
            "drum_sus_cymb1_mp_rr1.wav",
            "drum_sus_cymb1_mp_rr2.wav",
            "drum_crash1_ff_rr1.wav",
            "drum_crash1_ff_rr2.wav",
        )
    })
}

fn drum_kick() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| hit_bank!("drum_kick_v3_rr1.wav", "drum_kick_v3_rr2.wav"))
}

fn drum_snare() -> &'static [HitSample] {
    static B: OnceLock<Vec<HitSample>> = OnceLock::new();
    B.get_or_init(|| hit_bank!("drum_snare2_v5_rr1.wav", "drum_snare2_v5_rr2.wav"))
}

/// Velocity picks the dynamic layer; alternating round robins keep
/// repeated notes from being byte-identical (the machine-gun tell).
pub fn piano_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => piano_pp(),
        (0..=51, true) => piano_pp_rr2(),
        (52..=95, false) => piano_mf(),
        (52..=95, true) => piano_mf_rr2(),
        (_, false) => piano_f(),
        (_, true) => piano_f_rr2(),
    }
}

pub fn violin_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        violin_f()
    } else {
        violin_p()
    }
}

pub fn flute_bank() -> &'static [Zone] {
    flute()
}

/// Bank for the layered brass programs (GM 56–60). Velocity picks the
/// dynamic layer (VSCO v1 → p, v3 → f, threshold as `violin_bank`).
/// 61 (section) is pure model (§2.7): no CC0 section sample exists, and
/// the old trumpet fall-through layered the WRONG instrument's attack.
pub fn brass_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        57 => {
            if f {
                trombone_f()
            } else {
                trombone_p()
            }
        }
        58 => {
            if f {
                tuba_f()
            } else {
                tuba_p()
            }
        }
        59 => {
            if f {
                mutetpt_f()
            } else {
                mutetpt_p()
            }
        }
        60 => {
            if f {
                horn_f()
            } else {
                horn_p()
            }
        }
        _ => {
            if f {
                trumpet_f()
            } else {
                trumpet_p()
            }
        }
    }
}

/// Bank for the layered reed programs (GM 68–71). Velocity picks the
/// dynamic layer (threshold as `violin_bank`); 69 (english horn) shares
/// the oboe bank — `LaVoice`'s repitch covers its lower fifth.
pub fn reed_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        70 => {
            if f {
                bassoon_f()
            } else {
                bassoon_p()
            }
        }
        71 => {
            if f {
                clarinet_f()
            } else {
                clarinet_p()
            }
        }
        _ => {
            if f {
                oboe_f()
            } else {
                oboe_p()
            }
        }
    }
}

/// Bank for the layered string sections (GM 48-49). Velocity picks the
/// dynamic layer (violin section v1 → p, v2 → f; cello section v1 → p,
/// v3 → f; threshold as `violin_bank`). Synth strings 50-51 stay pure
/// model (they are *synth* strings — HLD option A default).
pub fn strings_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        strsec_f()
    } else {
        strsec_p()
    }
}

/// Bank for the layered nylon guitar (GM 24). The FreePats source has one
/// take per note — no velocity layers, no round robins — so the bank is
/// flat; `LaVoice`'s `vel_amp` still scales the transient with velocity.
pub fn guitar_bank() -> &'static [Zone] {
    nylon()
}

pub fn drum_crash_bank() -> &'static [HitSample] {
    drum_crash()
}

pub fn drum_kick_bank() -> &'static [HitSample] {
    drum_kick()
}

pub fn drum_snare_bank() -> &'static [HitSample] {
    drum_snare()
}

pub fn prewarm() {
    if !crate::embedded_samples_available() {
        return;
    }
    // One decode call fills the drum-kit crate's whole PCM cache (all takes
    // decode inside a single OnceLock init).
    #[cfg(feature = "embedded-samples")]
    {
        let _ = ferrosintesis_samples_drumkit::RIDE.pcm(0, 0);
    }
    let _ = piano_bank(1, false);
    let _ = piano_bank(1, true);
    let _ = piano_bank(80, false);
    let _ = piano_bank(80, true);
    let _ = piano_bank(127, false);
    let _ = piano_bank(127, true);
    let _ = violin_bank(1);
    let _ = violin_bank(127);
    let _ = flute_bank();
    for program in 56..=60 {
        let _ = brass_bank(program, 1);
        let _ = brass_bank(program, 127);
    }
    for program in [68, 70, 71] {
        let _ = reed_bank(program, 1);
        let _ = reed_bank(program, 127);
    }
    let _ = strings_bank(1);
    let _ = strings_bank(127);
    let _ = guitar_bank();
    let _ = drum_crash_bank();
    let _ = drum_kick_bank();
    let _ = drum_snare_bank();
}

fn nearest(zones: &'static [Zone], f: f32) -> &'static Zone {
    zones
        .iter()
        .min_by(|a, b| {
            let da = (a.root / f).ln().abs();
            let db = (b.root / f).ln().abs();
            da.partial_cmp(&db).unwrap()
        })
        .unwrap()
}

#[inline]
fn smooth(x: f32) -> f32 {
    let x = x.clamp(0.0, 1.0);
    x * x * (3.0 - 2.0 * x)
}

/// Sampled attack + modeled sustain, under the §2.7 onset-ownership
/// contract — one owner per instant:
///
/// - `[0, fade_start)`: the SAMPLE owns the onset. The wrapped model runs
///   from note-start (envelopes, filters, KS loop age naturally) but its
///   output is DISCARDED — no doubled attack, no hand-authored start state.
/// - `[fade_start, fade_end)`: one sum-to-one crossfade sample→model. A
///   sample and a model at the same pitch are CORRELATED, so an equal-power
///   law can boost or cancel at the midpoint; complementary weights keep
///   the sum level-true through the seam (verified by `la_level_continuity`
///   across every wrapped program).
/// - `[fade_end, ∞)`: the MODEL owns the sustain.
pub struct LaVoice {
    sustain: Box<dyn Voice>,
    zone: &'static Zone,
    pos: f32,
    step: f32,
    base_step: f32,
    gain: f32,
    rel_gain: f32,
    rel_mul: f32,
    rel_t60_mul: f32,
    t: usize,
    fade_start: usize,
    fade_end: usize,
    buf: Vec<f32>,
}

impl LaVoice {
    /// Wrap `sustain`; falls back to the bare model when the target is too
    /// far outside the sampled range for a credible repitch.
    pub fn wrap(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> Box<dyn Voice> {
        let f = key_freq(key);
        let zone = nearest(zones, f);
        let step = f / zone.root * 44100.0 / sr;
        if !(0.5..=2.05).contains(&step) {
            return sustain;
        }
        Box::new(LaVoice {
            sustain,
            zone,
            pos: 0.0,
            step,
            base_step: step,
            gain: gain * (0.35 + 0.65 * vel_amp(vel)),
            rel_gain: 1.0,
            rel_mul: 1.0,
            rel_t60_mul: 10f32.powf(-3.0 / (0.06 * sr)),
            t: 0,
            fade_start: (fade.0 * sr) as usize,
            fade_end: (fade.1 * sr) as usize,
            buf: Vec::new(),
        })
    }
}

impl Voice for LaVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        self.buf.resize(out.len(), 0.0);
        self.buf.fill(0.0);
        let sustain_alive = self.sustain.render(&mut self.buf);
        let n = self.zone.data.len();
        let fade_len = (self.fade_end - self.fade_start).max(1) as f32;
        let mut sample_live = false;
        for (i, o) in out.iter_mut().enumerate() {
            let t = self.t + i;
            // §2.7: one sum-to-one crossfade weight — the model is silent
            // (discarded, but running) before fade_start, sole owner after
            // fade_end; the smoothstep keeps the seam edges C1-continuous.
            let u = smooth((t as f32 - self.fade_start as f32) / fade_len);
            let mut s = self.buf[i] * u;
            let j = self.pos as usize;
            if t < self.fade_end && j + 1 < n && self.rel_gain > 0.0005 {
                sample_live = true;
                let frac = self.pos - j as f32;
                let v = self.zone.data[j] * (1.0 - frac) + self.zone.data[j + 1] * frac;
                s += v * (1.0 - u) * self.gain * self.rel_gain;
                self.rel_gain *= self.rel_mul;
                self.pos += self.step;
            }
            *o += s;
        }
        self.t += out.len();
        sustain_alive || sample_live
    }

    fn note_off(&mut self) {
        self.sustain.note_off();
        // let the transient die quickly (~60 ms T60) on early releases
        self.rel_mul = self.rel_t60_mul;
    }

    fn released(&self) -> bool {
        self.sustain.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        // bend the transient with the note, and the model underneath
        self.step = self.base_step * mult;
        self.sustain.set_pitch(mult);
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        // a slur has no fresh attack: retire the transient, glide the model
        if self.sustain.legato_to(key, vel) {
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        // the LA wrapper is transparent for routing: report the model inside
        self.sustain.kind()
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        self.sustain.set_trem(rate_hz, depth);
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        // Authored CC2/CC11 timbre-tracking must reach the model inside the
        // wrap (it used to no-op here, so the samples-on render ignored the
        // controller). The engine only drives this on authored channels
        // (plus brass's neutral pressure-1.0 note-on seed, a no-op), so an
        // unauthored channel renders bit-exactly as before.
        self.sustain.set_breath(pressure, growl);
    }
}

/// Unpitched drum sample overlay. The model remains the sustaining voice; the
/// sample contributes only a short attack/body cue and obeys the same routing
/// controls as the wrapped model.
pub struct SampleOverlay {
    model: Box<dyn Voice>,
    sample: &'static HitSample,
    pos: f32,
    step: f32,
    gain: f32,
    rel_gain: f32,
    rel_mul: f32,
    rel_t60_mul: f32,
    buf: Vec<f32>,
}

impl SampleOverlay {
    pub fn wrap(
        model: Box<dyn Voice>,
        bank: &'static [HitSample],
        vel: u8,
        seed: u32,
        sr: f32,
        gain: f32,
    ) -> Box<dyn Voice> {
        let sample = &bank[(seed as usize) % bank.len()];
        Box::new(Self {
            model,
            sample,
            pos: 0.0,
            step: 44100.0 / sr,
            gain: gain * (0.35 + 0.65 * vel_amp(vel)),
            rel_gain: 1.0,
            rel_mul: 1.0,
            rel_t60_mul: 10f32.powf(-3.0 / (0.018 * sr)),
            buf: Vec::new(),
        })
    }
}

impl Voice for SampleOverlay {
    fn render(&mut self, out: &mut [f32]) -> bool {
        self.buf.resize(out.len(), 0.0);
        self.buf.fill(0.0);
        let model_alive = self.model.render(&mut self.buf);
        let mut sample_live = false;
        let n = self.sample.data.len();
        for (i, o) in out.iter_mut().enumerate() {
            let mut s = self.buf[i];
            let j = self.pos as usize;
            if j + 1 < n && self.rel_gain > 0.0005 {
                sample_live = true;
                let frac = self.pos - j as f32;
                let v = self.sample.data[j] * (1.0 - frac) + self.sample.data[j + 1] * frac;
                s += v * self.gain * self.rel_gain;
                self.rel_gain *= self.rel_mul;
                self.pos += self.step;
            }
            *o += s;
        }
        model_alive || sample_live
    }

    fn note_off(&mut self) {
        self.model.note_off();
        self.rel_mul = self.rel_t60_mul;
    }

    fn released(&self) -> bool {
        self.model.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.model.set_pitch(mult);
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        if self.model.legato_to(key, vel) {
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    fn choke(&mut self) {
        self.model.choke();
        self.rel_mul = self.rel_t60_mul;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        self.model.kind()
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        self.model.set_trem(rate_hz, depth);
    }

    fn set_vowel(&mut self, freqs: [f32; 3], qs: [f32; 3], gains: [f32; 3]) {
        self.model.set_vowel(freqs, qs, gains);
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        self.model.set_breath(pressure, growl);
    }

    fn set_vib(&mut self, depth: f32) {
        self.model.set_vib(depth);
    }
}

// ---------------------------------------------------------------------------
// Sampled cymbals (drum-kit bank, Stage B): unlike `SampleOverlay` there is no
// model underneath — the recorded hit IS the whole voice. Unpitched: the GM
// key selects a bank, never a playback pitch.
// ---------------------------------------------------------------------------

/// Per-bank output levels, calibrated so each sampled cymbal lands within a
/// couple of dB of the `MetalPlate` model it replaces at vel 100 (RMS over the
/// sample's own life) — see `sampled_cymbal_level_parity`.
#[cfg(feature = "embedded-samples")]
const CYMBAL_LEVEL: [(u8, f32); 7] = [
    (49, 0.65), // crash 1
    (57, 0.68), // crash 2
    (51, 0.45), // ride 1
    (59, 0.45), // ride 2
    (53, 0.45), // ride bell
    (52, 0.68), // china
    (55, 0.34), // splash
];

/// Anti-machine-gun micro-variation (mechanism b): every hit gets a playback
/// rate of 1 + U(-0.025, +0.025) — ±~43 cents, inaudible as pitch on an
/// unpitched cymbal but enough to decorrelate the waveform and the decay
/// length — and a gain of ×(1 + U(-0.06, +0.06)). Both are deterministic from
/// the note seed. Mechanism (a), the clean per-key round-robin cycling, lives
/// in the engine's `drum_rr` counter and arrives here as `hit_index`.
#[cfg(feature = "embedded-samples")]
const CYMBAL_RATE_JITTER: f32 = 0.025;
#[cfg(feature = "embedded-samples")]
const CYMBAL_GAIN_JITTER: f32 = 0.06;

/// A full sampled cymbal hit: velocity picks the bank's dynamic layer, the
/// engine's per-key hit counter picks the round-robin take, and the note seed
/// adds per-hit rate/gain micro-variation so even a repeated take never
/// renders twice the same.
#[cfg(feature = "embedded-samples")]
pub struct SampledCymbal {
    data: &'static [i16],
    pos: f32,
    step: f32,
    gain: f32,
    env: f32,
    fade_mul: f32,
    choke_mul: f32,
    #[cfg(test)]
    layer: usize,
    #[cfg(test)]
    rr: usize,
}

#[cfg(feature = "embedded-samples")]
impl SampledCymbal {
    fn new(
        bank: &'static ferrosintesis_samples_drumkit::Bank,
        level: f32,
        vel: u8,
        seed: u32,
        hit_index: u8,
        sr: f32,
    ) -> Self {
        let layer = bank.layer_for_velocity(vel);
        let rr = hit_index as usize % bank.round_robins;
        let mut rng = Rng::new(seed ^ 0x00C1_4BA1);
        let rate = 1.0 + CYMBAL_RATE_JITTER * rng.white();
        let gjit = 1.0 + CYMBAL_GAIN_JITTER * rng.white();
        SampledCymbal {
            data: bank.pcm(layer, rr),
            pos: 0.0,
            step: 44_100.0 / sr * rate,
            gain: level * vel_amp(vel) * gjit,
            env: 1.0,
            fade_mul: 1.0,
            // hat-grab/CC120 choke: -60 dB in ~15 ms
            choke_mul: 10f32.powf(-3.0 / (0.015 * sr)),
            #[cfg(test)]
            layer,
            #[cfg(test)]
            rr,
        }
    }
}

/// Sampled-cymbal voice for a GM channel-10 key (49/57 crash, 51/59 ride,
/// 53 ride bell, 52 china, 55 splash), or `None` for any other key. Hi-hats
/// 42/44/46 deliberately stay modeled (they keep the engine's choke group and
/// the modeled pedal articulation).
#[cfg(feature = "embedded-samples")]
pub fn sampled_cymbal(
    key: u8,
    vel: u8,
    seed: u32,
    hit_index: u8,
    sr: f32,
) -> Option<Box<dyn Voice>> {
    use ferrosintesis_samples_drumkit as kit;
    let bank: &'static kit::Bank = match key {
        49 | 57 => &kit::CRASH,
        51 | 59 => &kit::RIDE,
        53 => &kit::RIDE_BELL,
        52 => &kit::CHINA,
        55 => &kit::SPLASH,
        _ => return None,
    };
    let level = CYMBAL_LEVEL.iter().find(|(k, _)| *k == key).unwrap().1;
    Some(Box::new(SampledCymbal::new(
        bank, level, vel, seed, hit_index, sr,
    )))
}

/// Modeled-only builds have no cymbal bank; the caller falls back to the
/// `MetalPlate` model (`drums::make` also forces `samples = false` there).
#[cfg(not(feature = "embedded-samples"))]
pub fn sampled_cymbal(
    _key: u8,
    _vel: u8,
    _seed: u32,
    _hit_index: u8,
    _sr: f32,
) -> Option<Box<dyn Voice>> {
    None
}

#[cfg(feature = "embedded-samples")]
impl Voice for SampledCymbal {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        for o in out.iter_mut() {
            let j = self.pos as usize;
            if j + 1 >= n || self.env < 1e-4 {
                return false;
            }
            let frac = self.pos - j as f32;
            let a = self.data[j] as f32;
            let b = self.data[j + 1] as f32;
            *o += (a + (b - a) * frac) * (1.0 / 32768.0) * self.gain * self.env;
            self.env *= self.fade_mul;
            self.pos += self.step;
        }
        true
    }

    // A struck cymbal rings out; percussion ignores note-off (house rule,
    // same as `Drum`/`MetalPlate`).
    fn note_off(&mut self) {}

    fn released(&self) -> bool {
        true
    }

    fn choke(&mut self) {
        self.fade_mul = self.choke_mul;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "sampledcymbal"
    }
}

#[cfg(all(test, feature = "embedded-samples"))]
mod tests {
    use super::*;
    use crate::dsp::OnePole;
    use crate::voices;
    use ferrosintesis_samples_drumkit as kitbank;

    /// The five GM-routed cymbal banks (49/57, 51/59, 53, 52, 55).
    fn routed_banks() -> [&'static kitbank::Bank; 5] {
        [
            &kitbank::CRASH,
            &kitbank::RIDE,
            &kitbank::RIDE_BELL,
            &kitbank::CHINA,
            &kitbank::SPLASH,
        ]
    }

    /// Anti-machine-gun mechanism (a): the engine's per-key hit counter must
    /// walk the round-robin takes 0→1→2→3→0…, so four consecutive hits of
    /// one key use four DISTINCT takes and no pair of consecutive hits ever
    /// repeats one. (A seed-modulo pick would repeat ~25% of the time.)
    #[test]
    fn sampled_cymbal_round_robin_cycles() {
        let sr = 44100.0;
        let bank = &kitbank::RIDE;
        let takes: Vec<(usize, usize)> = (0..5u8)
            .map(|i| {
                // a fresh pseudo-random seed per hit, exactly like the engine
                let seed = 0x9E37 ^ (i as u32).wrapping_mul(2654435761);
                let v = SampledCymbal::new(bank, 0.4, 100, seed, i, sr);
                (v.layer, v.rr)
            })
            .collect();
        assert!(
            takes.iter().all(|&(l, _)| l == takes[0].0),
            "same key + velocity must stay in one layer"
        );
        let rrs: Vec<usize> = takes.iter().map(|&(_, r)| r).collect();
        assert_eq!(rrs, vec![0, 1, 2, 3, 0], "clean rr cycle with wrap");
        for w in rrs.windows(2) {
            assert_ne!(w[0], w[1], "immediate round-robin repeat");
        }
    }

    /// Velocity picks the bank's dynamic layer at the SFZ boundaries, and
    /// still scales gain continuously inside a layer.
    #[test]
    fn sampled_cymbal_velocity_selects_layer() {
        let sr = 44100.0;
        let bank = &kitbank::RIDE; // vel_hi [42, 85, 127]
        let layer = |vel: u8| SampledCymbal::new(bank, 0.4, vel, 7, 0, sr).layer;
        assert_eq!(layer(30), 0);
        assert_eq!(layer(42), 0);
        assert_eq!(layer(43), 1);
        assert_eq!(layer(85), 1);
        assert_eq!(layer(86), 2);
        assert_eq!(layer(120), 2);
        let soft = SampledCymbal::new(bank, 0.4, 30, 7, 0, sr);
        let hard = SampledCymbal::new(bank, 0.4, 120, 7, 0, sr);
        assert!(
            !std::ptr::eq(soft.data, hard.data),
            "soft and hard hits must play different takes"
        );
        assert!(hard.gain > soft.gain * 2.0, "velocity gain not continuous");
    }

    /// A choked cymbal (hat grab / CC120) reaches silence within ~20 ms and
    /// the voice then terminates.
    #[test]
    fn sampled_cymbal_choke_reaches_silence_within_20_ms() {
        let sr = 44100.0;
        let mut v = SampledCymbal::new(&kitbank::CRASH, 0.4, 110, 7, 0, sr);
        let mut head = vec![0f32; (0.30 * sr) as usize];
        assert!(v.render(&mut head));
        let pre = head[head.len() - 441..]
            .iter()
            .fold(0f32, |m, &x| m.max(x.abs()));
        assert!(pre > 1e-4, "crash should still ring at 0.3 s: {pre}");
        v.choke();
        let mut tail = vec![0f32; (0.05 * sr) as usize];
        v.render(&mut tail);
        let post = tail[(0.020 * sr) as usize..]
            .iter()
            .fold(0f32, |m, &x| m.max(x.abs()));
        assert!(
            post < pre * 2e-3,
            "choked cymbal still audible after 20 ms: {post} vs pre {pre}"
        );
        let mut more = vec![0f32; 64];
        assert!(!v.render(&mut more), "choked voice must terminate");
    }

    /// No boundary click: every routed take starts and ends on the
    /// generator's fades (2 ms fade-in, squared fade-out), and the voice's
    /// rendered stream begins near zero and dies out near zero rather than
    /// stepping. Guards a future re-prepared bank as much as the voice.
    #[test]
    fn sampled_cymbal_has_no_boundary_click() {
        let sr = 44100.0;
        for bank in routed_banks() {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let pcm = bank.pcm(layer, rr);
                    let peak = pcm.iter().map(|&v| (v as i32).abs()).max().unwrap() as f32;
                    let head = pcm[..44].iter().map(|&v| (v as i32).abs()).max().unwrap() as f32;
                    let tail = pcm[pcm.len() - 44..]
                        .iter()
                        .map(|&v| (v as i32).abs())
                        .max()
                        .unwrap() as f32;
                    let name = bank.file_name(layer, rr);
                    assert!(
                        head < 0.05 * peak,
                        "{name}: hot first ms ({head} vs {peak})"
                    );
                    assert!(tail < 0.02 * peak, "{name}: hot last ms ({tail} vs {peak})");
                }
            }
            // and through the voice: near-zero entry, near-zero exit
            let mut v = SampledCymbal::new(bank, 0.4, 110, 7, 0, sr);
            let mut buf = vec![0f32; (3.0 * sr) as usize];
            let alive = v.render(&mut buf);
            assert!(!alive, "3 s must outlast every bank take");
            let peak = buf.iter().fold(0f32, |m, &x| m.max(x.abs()));
            assert!(peak > 0.01, "{}: silent render", bank.name);
            assert!(
                buf[0].abs() < 0.05 * peak,
                "{}: rendered onset steps ({} vs peak {peak})",
                bank.name,
                buf[0]
            );
            let last = buf.iter().rposition(|&x| x != 0.0).unwrap();
            let end_peak = buf[last.saturating_sub(88)..=last]
                .iter()
                .fold(0f32, |m, &x| m.max(x.abs()));
            assert!(
                end_peak < 0.05 * peak,
                "{}: rendered tail steps ({end_peak} vs peak {peak})",
                bank.name
            );
        }
    }

    #[test]
    fn banks_parse() {
        for z in violin_f()
            .iter()
            .chain(violin_p())
            .chain(flute())
            .chain(piano_pp())
            .chain(piano_mf())
            .chain(piano_f())
            .chain(piano_pp_rr2())
            .chain(piano_mf_rr2())
            .chain(piano_f_rr2())
            .chain(trumpet_p())
            .chain(trumpet_f())
            .chain(mutetpt_p())
            .chain(mutetpt_f())
            .chain(trombone_p())
            .chain(trombone_f())
            .chain(tuba_p())
            .chain(tuba_f())
            .chain(horn_p())
            .chain(horn_f())
            .chain(oboe_p())
            .chain(oboe_f())
            .chain(bassoon_p())
            .chain(bassoon_f())
            .chain(clarinet_p())
            .chain(clarinet_f())
            .chain(nylon())
            .chain(strsec_p())
            .chain(strsec_f())
        {
            assert!(z.data.len() > 20_000, "zone too short: {}", z.data.len());
            // the tuba bank reaches A#0 (~29 Hz), hence the low floor
            assert!((25.0..2500.0).contains(&z.root), "odd root {}", z.root);
            let peak = z.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "zone not normalised: peak {peak}");
        }
        for h in drum_crash().iter().chain(drum_kick()).chain(drum_snare()) {
            assert!(
                h.data.len() > 8_000,
                "drum sample too short: {}",
                h.data.len()
            );
            let peak = h.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "drum sample not normalised: peak {peak}");
        }
    }

    fn pitch_of(seg: &[f32], sr: f32) -> f32 {
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
    }

    /// The LA fiddle at A4 must sound at 440 Hz straight through the
    /// crossfade — the repitched sample and the model have to agree.
    #[test]
    fn la_pitch_a4() {
        let sr = 44100.0;
        let mut v = voices::make(40, 69, 100, sr, 5, true);
        let mut buf = vec![0f32; 44100];
        v.render(&mut buf);
        let hz = pitch_of(&buf[6615..24255], sr); // 0.15 s – 0.55 s
        assert!((hz - 440.0).abs() < 12.0, "measured {hz} Hz");
    }

    /// The brass sample layer must not shift perceived pitch: Goertzel peak
    /// through the crossfade window (zero-crossing counters lie when a layer
    /// brightens a voice — lessons_learnt 2026.07.07).
    #[test]
    fn la_brass_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (56u8, 69u8, "trumpet"),
            (57, 55, "trombone"),
            (58, 40, "tuba"),
            (59, 69, "muted-trumpet"),
            (60, 62, "french-horn"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The layer must be audible, not just present (lessons_learnt
    /// 2026.07.06): samples-on vs samples-off of the same note must differ
    /// materially in the first 50 ms, and for the bright programs the real
    /// attack must raise the high-band fraction (the sampled bite) over the
    /// model's synthetic chiff. The french horn is exempt from the HF check:
    /// its hand-in-bell attack is genuinely dark (measured on ≈ off).
    #[test]
    fn la_brass_attack_sharpness() {
        let sr = 44100.0;
        for (program, key, hf_gain, name) in [
            (56u8, 69u8, 1.5f32, "trumpet"),
            (57, 55, 1.3, "trombone"),
            (58, 40, 2.0, "tuba"),
            (59, 69, 1.3, "muted-trumpet"),
            (60, 62, 0.0, "french-horn"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on > r_off * hf_gain,
                "{name}: attack not sharper: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The reed sample layer must not shift perceived pitch: Goertzel peak
    /// through the crossfade window (as `la_brass_pitch_integrity`); 69
    /// exercises the english horn's repitched oboe bank.
    #[test]
    fn la_reed_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (68u8, 76u8, "oboe"),
            (69, 64, "english-horn"),
            (70, 48, "bassoon"),
            (71, 60, "clarinet"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The reed layer must be audible, not just present: samples-on vs
    /// samples-off must differ materially in the first 50 ms. Unlike brass
    /// (real lip bite ADDS high band), every measured reed onset is LESS
    /// hissy than the model’s synthetic chiff (hf-frac on/off: oboe
    /// 0.53/0.67, english horn 0.38/0.39, bassoon 0.15/0.20, clarinet
    /// 0.19/0.28) — the realism gain is removing synthetic noise, so the
    /// oracle asserts that measured direction: the layer must never make
    /// the attack hissier than the pure model.
    #[test]
    fn la_reed_attack_sharpness() {
        let sr = 44100.0;
        for (program, key, name) in [
            (68u8, 76u8, "oboe"),
            (69, 64, "english-horn"),
            (70, 48, "bassoon"),
            (71, 60, "clarinet"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.05,
                "{name}: sampled attack hissier than the model: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The nylon-guitar sample layer must not shift perceived pitch: Goertzel
    /// peak through the crossfade window, several keys including both repitch
    /// edges (key 40 sits on the E2 zone; 45/57/68 land between zones; 79 is
    /// repitched up ~3 st from the top E5 zone).
    #[test]
    fn la_guitar_pitch_integrity() {
        let sr = 44100.0;
        for key in [40u8, 45, 52, 57, 64, 68, 79] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(24, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.10–0.40 s spans the fade tail and the handed-over KS string
            let hz = crate::testutil::peak_locate(&buf[4410..17640], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "nylon key {key}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The guitar layer must be audible, not just present: samples-on vs
    /// samples-off must differ materially in the first 50 ms. Measured
    /// direction (as reeds, not brass): the real pick onset is markedly LESS
    /// hissy than the model's synthetic attack-noise burst (at the HLD's
    /// initial 0.45 wrap gain, hf-frac on/off measured 0.07/0.46, 0.04/0.63,
    /// 0.23/0.47 for keys 45/52/64; direction unchanged at the level-matched
    /// 0.25) — the realism gain is replacing broadband noise with a woody
    /// pick transient, so the oracle asserts the layer never makes the
    /// attack hissier.
    #[test]
    fn la_guitar_attack_sharpness() {
        let sr = 44100.0;
        for key in [45u8, 52, 64] {
            let early = |samples: bool| {
                let mut v = voices::make(24, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "nylon key {key}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.05,
                "nylon key {key}: sampled attack hissier than the model: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The string-section sample layer must not shift perceived pitch:
    /// Goertzel peak through the crossfade window at idiomatic keys. 48/49
    /// exercise both the cello-section (low) and violin-section (high) zones;
    /// 50/51 are pure model by design but are pinned here too so a future
    /// wrap cannot land without re-passing this oracle.
    #[test]
    fn la_strings_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (48u8, 48u8, "ensemble-low-cello"),
            (48, 76, "ensemble-high-violin"),
            (49, 55, "slow-strings-low"),
            (49, 67, "slow-strings-mid"),
            (50, 60, "synth-strings-1"),
            (51, 64, "synth-strings-2"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15-0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// Synth strings 50-51 stay pure model (HLD option A): samples on/off
    /// must render byte-identical on the default bank.
    #[test]
    fn synth_strings_50_51_skip_sample_layer() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        for prog in [50u8, 51] {
            let render = |samples: bool| {
                let mut v = voices::make(prog, 60, 100, sr, 6, samples);
                let mut buf = vec![0f32; 22050];
                v.render(&mut buf);
                buf
            };
            assert_eq!(
                bits(&render(true)),
                bits(&render(false)),
                "synth strings {prog} not sample-independent"
            );
        }
    }

    /// GM 61 brass section stays pure model (§2.7): no CC0 section sample
    /// exists and the old trumpet fall-through layered the WRONG
    /// instrument's attack — samples on/off must render byte-identical so a
    /// future wrap cannot land without re-deciding that.
    #[test]
    fn brass_section_61_skips_sample_layer() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        let render = |samples: bool| {
            let mut v = voices::make(61, 69, 100, sr, 6, samples);
            let mut buf = vec![0f32; 22050];
            v.render(&mut buf);
            buf
        };
        assert_eq!(
            bits(&render(true)),
            bits(&render(false)),
            "brass section 61 not sample-independent"
        );
    }

    /// The LA wrapper forwards `set_breath` to the wrapped model (routed
    /// from the reed/flue work: authored CC2/CC11 timbre-tracking used to
    /// no-op on the samples path). Two legs: the engine's neutral brass
    /// note-on seed (pressure 1.0) is a bit-exact no-op — an unauthored
    /// channel renders exactly as before — and an authored (non-neutral)
    /// pressure genuinely reaches the model through the wrap.
    #[test]
    fn la_wrap_forwards_breath() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        let render = |prog: u8, breath: Option<(f32, f32)>| {
            let mut v = voices::make(prog, 69, 100, sr, 5, true);
            if let Some((p, g)) = breath {
                v.set_breath(p, g);
            }
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            buf
        };
        // neutral seed == no call, bit-exact (brass defaults pressure 1.0)
        assert_eq!(
            bits(&render(56, Some((1.0, 0.0)))),
            bits(&render(56, None)),
            "neutral set_breath(1.0, 0) must be a bit-exact no-op"
        );
        // authored pressure must change the render for every LA-wrapped
        // wind family the forward serves (brass 56, reed 68, flute 73)
        for prog in [56u8, 68, 73] {
            let (plain, blown) = (render(prog, None), render(prog, Some((0.4, 0.0))));
            assert_ne!(
                bits(&plain),
                bits(&blown),
                "prog {prog}: authored breath does not reach the wrapped model"
            );
        }
    }

    /// The string-section layer must be audible, not just present: samples-on
    /// vs samples-off must differ materially in the first 50 ms. Measured
    /// direction is REGISTER-DEPENDENT, unlike brass (up) or reeds/guitar
    /// (down): the real violin-section bite raises the high-band fraction up
    /// top (hf on/off 0.58/0.42 at 48@76) while the cello/mid sections are
    /// LESS hissy than the saw stack's filtered onset (0.22/0.25 at 48@48,
    /// 0.30/0.37 at 49@67). So the oracle asserts audibility plus a measured
    /// two-sided band: the layer never makes the attack wildly hissier
    /// (<1.6x) and never dulls it to mud (>0.5x).
    #[test]
    fn la_strings_attack_audibility() {
        let sr = 44100.0;
        for (program, key, name) in [
            (48u8, 48u8, "ensemble-low"),
            (48, 60, "ensemble-mid"),
            (48, 76, "ensemble-high"),
            (49, 55, "slow-low"),
            (49, 67, "slow-mid"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.6 && r_on > r_off * 0.5,
                "{name}: attack hf-frac out of the measured band: on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The sampled attack must hand over to the model without a level jump —
    /// and (§3.2, two-sided rewrite) for STRUCK/PLUCKED wrapped voices the
    /// attack must be the render's loudest instant. The second leg is what
    /// makes the seam cap ungameable: the old one-sided reading was
    /// satisfied by cutting the GM 24 wrap gain until the pick sat QUIETER
    /// than the model's sustain (upside-down for a plucked string).
    ///
    /// The no-step leg is DIFFERENTIAL (the §2.7 "measured, per-key seam
    /// limit"): each adjacent-window ratio of the wrapped render is compared
    /// with the model-only render's ratio for the same windows, and the
    /// wrap may not introduce more than a 2.4x step in either direction.
    /// An absolute cap cannot serve both families: a high plucked string
    /// legitimately decays > 2.4x per 100 ms once the pick is honest, while
    /// a sustained voice's own crescendo (the slow-speaking tuba) legitimately
    /// rises — only the step the WRAP adds on top of the voice's own
    /// envelope shape is a seam defect.
    #[test]
    fn la_level_continuity() {
        let sr = 44100.0;
        for (program, key, name, struck) in [
            (40u8, 69u8, "fiddle", false),
            (110u8, 69, "fiddle-110", false),
            (73u8, 69, "flute", false),
            (0u8, 69, "piano", true),
            (0u8, 48, "piano-low", true),
            (56u8, 69, "trumpet", false),
            (57u8, 55, "trombone", false),
            (58u8, 40, "tuba", false),
            (59u8, 69, "muted-trumpet", false),
            (60u8, 62, "french-horn", false),
            (68u8, 76, "oboe", false),
            (69u8, 64, "english-horn", false),
            (70u8, 48, "bassoon", false),
            (71u8, 60, "clarinet", false),
            (24u8, 45, "nylon-guitar-low", true),
            (24u8, 52, "nylon-guitar", true),
            (24u8, 64, "nylon-guitar-high", true),
            (48u8, 48, "string-ens-low", false),
            (48u8, 76, "string-ens-high", false),
            (49u8, 55, "slow-strings", false),
        ] {
            // 100 ms windows from 50 ms to 950 ms, wrapped and model-only
            let win = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; 44100]; // 1 s, note held
                v.render(&mut buf);
                let rms = |a: usize, b: usize| {
                    (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                };
                let coarse: Vec<f32> = (0..9)
                    .map(|k| rms(2205 + k * 4410, 2205 + (k + 1) * 4410))
                    .collect();
                let fine: Vec<f32> = (0..19).map(|k| rms(k * 2205, (k + 1) * 2205)).collect();
                (coarse, fine)
            };
            let ((w, fine), (m, _)) = (win(true), win(false));
            for (pw, pm) in w.windows(2).zip(m.windows(2)) {
                let (rw, rm) = (pw[0] / pw[1], pm[0] / pm[1]);
                let excess = (rw / rm).max(rm / rw);
                assert!(
                    excess < 2.4,
                    "{name}: wrap-introduced level step across the crossfade \
                     ({excess:.2}x beyond the model's own shape): wrapped {w:?} \
                     vs model {m:?}"
                );
            }
            // struck/plucked: the attack is the global peak — 50 ms windows
            // from t=0, the loudest must start inside the first 150 ms
            if struck {
                let attack = fine[..3].iter().fold(0f32, |mx, &x| mx.max(x));
                let late = fine[3..].iter().fold(0f32, |mx, &x| mx.max(x));
                assert!(
                    late <= attack,
                    "{name}: attack is not the peak — late window {late:.5} \
                     above attack {attack:.5} ({fine:?})"
                );
            }
        }
    }

    #[test]
    fn drum_sample_overlay_is_finite_and_forwards_controls() {
        let sr = 44100.0;
        let model = voices::make(0, 60, 100, sr, 5, false);
        let want_kind = model.kind();
        let mut v = SampleOverlay::wrap(model, drum_kick_bank(), 110, 5, sr, 0.05);
        v.set_pitch(1.01);
        assert_eq!(v.kind(), want_kind);
        v.choke();
        let mut buf = vec![0f32; (0.1 * sr) as usize];
        v.render(&mut buf);
        assert!(buf.iter().all(|x| x.is_finite()));
        assert!(buf.iter().any(|&x| x.abs() > 1e-5));
    }
}
