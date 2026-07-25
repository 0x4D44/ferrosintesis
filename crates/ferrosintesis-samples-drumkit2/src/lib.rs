//! Embedded CC0 accent-cymbal banks for ferrosintesis -- crash, sizzle crash,
//! splash and an 18" china.
//!
//! The overflow half of the sampled drum kit. `ferrosintesis-samples-drumkit`
//! packaged at 15.8 MiB, over the crates.io 10 MiB per-crate limit; cymbals are
//! the long-decaying, largest files, so moving exactly these four banks splits
//! ~20.5 MB into two ~10.5 MB halves. It is a PACKAGING seam and nothing else --
//! same sources, same pinned revisions, same `prepare_drumkit.py`, byte-identical
//! renders. The ride, ride bell and hi-hats are cymbals too and stayed behind.
//!
//! The [`Bank`] descriptor type is shared, and lives in the core crate, so a
//! consumer holds one `&'static Bank` and never has to know which half embedded
//! the bytes. Each bank here carries [`SOURCE`], this crate's own inventory.
//!
//! Mono 16-bit 44.1 kHz. CC0-1.0 -- no attribution obligation; see
//! `PROVENANCE.md` for the pinned source revisions and the articulation
//! inventory. Consumers normally access this crate through `ferrosintesis`.

#![forbid(unsafe_code)]

use std::sync::OnceLock;

pub use ferrosintesis_samples_drumkit::{Bank, BankSource, SAMPLE_RATE_HZ};

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 48;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "china_vl1_rr1.wav",
        include_bytes!("../samples/china_vl1_rr1.wav"),
    ),
    (
        "china_vl1_rr2.wav",
        include_bytes!("../samples/china_vl1_rr2.wav"),
    ),
    (
        "china_vl1_rr3.wav",
        include_bytes!("../samples/china_vl1_rr3.wav"),
    ),
    (
        "china_vl1_rr4.wav",
        include_bytes!("../samples/china_vl1_rr4.wav"),
    ),
    (
        "china_vl2_rr1.wav",
        include_bytes!("../samples/china_vl2_rr1.wav"),
    ),
    (
        "china_vl2_rr2.wav",
        include_bytes!("../samples/china_vl2_rr2.wav"),
    ),
    (
        "china_vl2_rr3.wav",
        include_bytes!("../samples/china_vl2_rr3.wav"),
    ),
    (
        "china_vl2_rr4.wav",
        include_bytes!("../samples/china_vl2_rr4.wav"),
    ),
    (
        "china_vl3_rr1.wav",
        include_bytes!("../samples/china_vl3_rr1.wav"),
    ),
    (
        "china_vl3_rr2.wav",
        include_bytes!("../samples/china_vl3_rr2.wav"),
    ),
    (
        "china_vl3_rr3.wav",
        include_bytes!("../samples/china_vl3_rr3.wav"),
    ),
    (
        "china_vl3_rr4.wav",
        include_bytes!("../samples/china_vl3_rr4.wav"),
    ),
    (
        "china_vl4_rr1.wav",
        include_bytes!("../samples/china_vl4_rr1.wav"),
    ),
    (
        "china_vl4_rr2.wav",
        include_bytes!("../samples/china_vl4_rr2.wav"),
    ),
    (
        "china_vl4_rr3.wav",
        include_bytes!("../samples/china_vl4_rr3.wav"),
    ),
    (
        "china_vl4_rr4.wav",
        include_bytes!("../samples/china_vl4_rr4.wav"),
    ),
    (
        "china_vl5_rr1.wav",
        include_bytes!("../samples/china_vl5_rr1.wav"),
    ),
    (
        "china_vl5_rr2.wav",
        include_bytes!("../samples/china_vl5_rr2.wav"),
    ),
    (
        "china_vl5_rr3.wav",
        include_bytes!("../samples/china_vl5_rr3.wav"),
    ),
    (
        "china_vl5_rr4.wav",
        include_bytes!("../samples/china_vl5_rr4.wav"),
    ),
    (
        "crash_vl1_rr1.wav",
        include_bytes!("../samples/crash_vl1_rr1.wav"),
    ),
    (
        "crash_vl1_rr2.wav",
        include_bytes!("../samples/crash_vl1_rr2.wav"),
    ),
    (
        "crash_vl1_rr3.wav",
        include_bytes!("../samples/crash_vl1_rr3.wav"),
    ),
    (
        "crash_vl1_rr4.wav",
        include_bytes!("../samples/crash_vl1_rr4.wav"),
    ),
    (
        "crash_vl2_rr1.wav",
        include_bytes!("../samples/crash_vl2_rr1.wav"),
    ),
    (
        "crash_vl2_rr2.wav",
        include_bytes!("../samples/crash_vl2_rr2.wav"),
    ),
    (
        "crash_vl2_rr3.wav",
        include_bytes!("../samples/crash_vl2_rr3.wav"),
    ),
    (
        "crash_vl2_rr4.wav",
        include_bytes!("../samples/crash_vl2_rr4.wav"),
    ),
    (
        "crash_vl3_rr1.wav",
        include_bytes!("../samples/crash_vl3_rr1.wav"),
    ),
    (
        "crash_vl3_rr2.wav",
        include_bytes!("../samples/crash_vl3_rr2.wav"),
    ),
    (
        "crash_vl3_rr3.wav",
        include_bytes!("../samples/crash_vl3_rr3.wav"),
    ),
    (
        "crash_vl3_rr4.wav",
        include_bytes!("../samples/crash_vl3_rr4.wav"),
    ),
    (
        "sizzle_vl1_rr1.wav",
        include_bytes!("../samples/sizzle_vl1_rr1.wav"),
    ),
    (
        "sizzle_vl1_rr2.wav",
        include_bytes!("../samples/sizzle_vl1_rr2.wav"),
    ),
    (
        "sizzle_vl1_rr3.wav",
        include_bytes!("../samples/sizzle_vl1_rr3.wav"),
    ),
    (
        "sizzle_vl1_rr4.wav",
        include_bytes!("../samples/sizzle_vl1_rr4.wav"),
    ),
    (
        "sizzle_vl2_rr1.wav",
        include_bytes!("../samples/sizzle_vl2_rr1.wav"),
    ),
    (
        "sizzle_vl2_rr2.wav",
        include_bytes!("../samples/sizzle_vl2_rr2.wav"),
    ),
    (
        "sizzle_vl2_rr3.wav",
        include_bytes!("../samples/sizzle_vl2_rr3.wav"),
    ),
    (
        "sizzle_vl2_rr4.wav",
        include_bytes!("../samples/sizzle_vl2_rr4.wav"),
    ),
    (
        "sizzle_vl3_rr1.wav",
        include_bytes!("../samples/sizzle_vl3_rr1.wav"),
    ),
    (
        "sizzle_vl3_rr2.wav",
        include_bytes!("../samples/sizzle_vl3_rr2.wav"),
    ),
    (
        "sizzle_vl3_rr3.wav",
        include_bytes!("../samples/sizzle_vl3_rr3.wav"),
    ),
    (
        "sizzle_vl3_rr4.wav",
        include_bytes!("../samples/sizzle_vl3_rr4.wav"),
    ),
    (
        "splash_vl1_rr1.wav",
        include_bytes!("../samples/splash_vl1_rr1.wav"),
    ),
    (
        "splash_vl1_rr2.wav",
        include_bytes!("../samples/splash_vl1_rr2.wav"),
    ),
    (
        "splash_vl1_rr3.wav",
        include_bytes!("../samples/splash_vl1_rr3.wav"),
    ),
    (
        "splash_vl1_rr4.wav",
        include_bytes!("../samples/splash_vl1_rr4.wav"),
    ),
];

/// This crate's own embedded inventory, handed to each [`Bank`] below so that
/// [`Bank::wav`] resolves against the crate that actually holds the bytes.
pub static SOURCE: BankSource = BankSource { wav: get, pcm };

/// Crash cymbal, normal hit (`mid_crash_crash`). GM 49 / 57.
pub static CRASH: Bank = Bank {
    name: "crash",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
    source: &SOURCE,
};
/// Sizzle crash (`mid_crash_sizzle`).
///
/// Reachable through the `Bank` API but not routed by any GM channel-10 key.
/// That is deliberate: ferrosintesis is a generic GM player and this bank is
/// part of the public instrument. Do not cull it for lack of an in-repo user.
pub static CRASH_SIZZLE: Bank = Bank {
    name: "sizzle",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
    source: &SOURCE,
};
/// Hi-hat splash (`mid_hh_splash`) -- one full-range velocity layer at the
/// source; the nearest thing this kit has to a splash cymbal. GM 55.
pub static SPLASH: Bank = Bank {
    name: "splash",
    vel_hi: &[127],
    round_robins: 4,
    source: &SOURCE,
};
/// 18" china, stick hit (Big Rusty Drums `cn`, overhead mic). GM 52.
pub static CHINA: Bank = Bank {
    name: "china",
    vel_hi: &[25, 51, 76, 101, 127],
    round_robins: 4,
    source: &SOURCE,
};

/// Every articulation in this half of the kit.
pub static BANKS: [&Bank; 4] = [&CRASH, &CRASH_SIZZLE, &SPLASH, &CHINA];

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

/// Returns the decoded mono 16-bit 44.1 kHz PCM for an exact file name.
pub fn pcm(name: &str) -> Option<&'static [i16]> {
    static CACHE: OnceLock<Vec<Vec<i16>>> = OnceLock::new();
    let cache = CACHE.get_or_init(|| SAMPLES.iter().map(|(_, b)| decode_wav(b)).collect());
    let idx = SAMPLES
        .iter()
        .position(|(candidate, _)| *candidate == name)?;
    Some(&cache[idx])
}

/// Minimal RIFF walker for the bank's own files (16-bit mono 44.1 kHz).
fn decode_wav(bytes: &[u8]) -> Vec<i16> {
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
                channels == 1 && sr == SAMPLE_RATE_HZ && bits == 16,
                "drum-kit bank must be 16-bit mono 44.1 kHz"
            );
        } else if id == b"data" {
            data = body
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes([c[0], c[1]]))
                .collect();
        }
        pos += 8 + len + (len & 1);
    }
    assert!(!data.is_empty(), "drum-kit bank file has no data chunk");
    data
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The embedded table must match the packaged directory exactly. Catches a
    /// sample added to `samples/` without regenerating, and vice versa.
    #[test]
    fn inventory_matches_packaged_wavs() {
        assert_eq!(SAMPLES.len(), FILE_COUNT);
        let mut names: Vec<&str> = SAMPLES.iter().map(|(n, _)| *n).collect();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), FILE_COUNT, "duplicate file name in SAMPLES");
        for (name, bytes) in SAMPLES.iter() {
            assert!(name.ends_with(".wav"), "{name} is not a .wav");
            assert!(bytes.len() > 44, "{name} is smaller than a WAV header");
        }
    }

    /// Velocity splits, carried over from the core crate's test when these four
    /// banks moved here. Parsed from the source SFZ `hivel` bounds, not guessed.
    #[test]
    fn layer_for_velocity_respects_the_sfz_splits() {
        assert_eq!(CHINA.layer_for_velocity(25), 0);
        assert_eq!(CHINA.layer_for_velocity(102), 4);
        assert_eq!(SPLASH.layer_for_velocity(64), 0);
        assert_eq!(CRASH.layer_for_velocity(42), 0);
        assert_eq!(CRASH.layer_for_velocity(43), 1);
        assert_eq!(CRASH.layer_for_velocity(127), 2);
    }

    /// Aggregate embedded size, pinned. Catches a sample silently replaced by a
    /// re-cut of a different length.
    #[test]
    fn every_sample_is_a_nonempty_wav_with_the_expected_aggregate_size() {
        const EXPECTED_BYTES: usize = 10619904;
        assert_eq!(
            SAMPLES.iter().map(|(_, bytes)| bytes.len()).sum::<usize>(),
            EXPECTED_BYTES
        );
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a WAV");
            assert_eq!(&bytes[..4], b"RIFF", "{name} has no RIFF header");
            assert_eq!(&bytes[8..12], b"WAVE", "{name} has no WAVE signature");
            assert_eq!(get(name), Some(bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }

    /// Duration bounds per articulation, carried over from the core crate's
    /// `decoded_banks_are_valid_audio` when these banks moved.
    #[test]
    fn decoded_banks_are_valid_audio() {
        for (bank, min_s, max_s) in [(&CRASH, 2.0, 2.85), (&CHINA, 1.5, 2.25)] {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let pcm = bank.pcm(layer, rr);
                    let dur = pcm.len() as f64 / SAMPLE_RATE_HZ as f64;
                    assert!(
                        dur >= min_s && dur <= max_s,
                        "{}: vl{}/rr{} is {dur:.3} s, outside {min_s}..{max_s}",
                        bank.name,
                        layer + 1,
                        rr + 1,
                    );
                    let peak = pcm.iter().map(|&v| (v as i32).abs()).max().unwrap();
                    assert!(peak > 16_000, "{}: peak {peak} is too quiet", bank.name);
                }
            }
        }
    }

    /// Every take every bank names must resolve through this crate's `SOURCE`.
    ///
    /// This is the oracle for the split: a bank whose `source` still pointed at
    /// the core crate would compile fine and panic only when that drum was first
    /// struck, mid-render. Proving every take resolves here makes the seam a
    /// build-time fact rather than a runtime hope.
    #[test]
    fn every_bank_take_resolves_through_this_crates_source() {
        let mut takes = 0;
        for bank in BANKS {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let name = bank.file_name(layer, rr);
                    assert!(
                        get(&name).is_some(),
                        "{name}: bank {} does not resolve in this crate",
                        bank.name
                    );
                    assert!(!bank.pcm(layer, rr).is_empty(), "{name}: empty PCM");
                    takes += 1;
                }
            }
        }
        assert_eq!(takes, FILE_COUNT, "banks do not cover the embedded files");
    }
}
