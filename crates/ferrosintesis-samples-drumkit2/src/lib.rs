//! Embedded CC0 accent-cymbal banks for ferrosintesis -- crash, splash and an
//! 18" china.
//!
//! The overflow half of the sampled drum kit. `ferrosintesis-samples-drumkit`
//! packaged at 15.8 MiB, over the crates.io 10 MiB per-crate limit; cymbals are
//! the long-decaying, largest files, so moving these banks keeps each package
//! below that limit. It is a PACKAGING seam and nothing else --
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
//! `ferrosintesis`. Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

use std::sync::OnceLock;

pub use ferrosintesis_samples_drumkit::{Bank, BankSource, SAMPLE_RATE_HZ};

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 36;

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

static PCM_CACHE: OnceLock<Vec<Vec<i16>>> = OnceLock::new();

/// This crate's own embedded inventory, handed to each [`Bank`] below so that
/// [`Bank::wav`] resolves against the crate that actually holds the bytes.
pub static SOURCE: BankSource = BankSource {
    wav: get,
    pcm,
    pcm_by_index,
};

/// Crash cymbal, normal hit (`mid_crash_crash`). GM 49 / 57.
pub static CRASH: Bank = Bank {
    name: "crash",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 20,
};
/// Hi-hat splash (`mid_hh_splash`) -- one full-range velocity layer at the
/// source; the nearest thing this kit has to a splash cymbal. GM 55.
pub static SPLASH: Bank = Bank {
    name: "splash",
    vel_hi: &[127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 32,
};
/// 18" china, stick hit (Big Rusty Drums `cn`, overhead mic). GM 52.
pub static CHINA: Bank = Bank {
    name: "china",
    vel_hi: &[25, 51, 76, 101, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 0,
};

/// Every articulation in this half of the kit.
pub static BANKS: [&Bank; 3] = [&CRASH, &SPLASH, &CHINA];

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
    let idx = SAMPLES
        .iter()
        .position(|(candidate, _)| *candidate == name)?;
    Some(&decoded_samples()[idx])
}

/// Returns decoded PCM at an exact inventory index.
#[doc(hidden)]
pub fn pcm_by_index(index: usize) -> Option<&'static [i16]> {
    SAMPLES.get(index)?;
    Some(decoded_samples()[index].as_slice())
}

/// Decode this package's complete PCM inventory now.
///
/// Call away from a realtime thread so the first accent-cymbal hit does no decoding.
pub fn prewarm() {
    let _ = decoded_samples();
}

/// Number of times this package's PCM cache has initialized (zero or one).
///
/// Hidden diagnostic used to enforce the realtime prewarm contract end to end.
#[doc(hidden)]
pub fn pcm_cache_initializations() -> usize {
    usize::from(PCM_CACHE.get().is_some())
}

fn decoded_samples() -> &'static Vec<Vec<i16>> {
    PCM_CACHE.get_or_init(|| SAMPLES.iter().map(|(_, bytes)| decode_wav(bytes)).collect())
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
    use std::ffi::OsStr;
    use std::fs;
    use std::path::Path;

    fn validate_packaged_inventory(mut packaged: Vec<String>) -> Result<(), String> {
        let mut embedded: Vec<String> =
            SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();
        let mut unique = embedded.clone();
        unique.sort();
        unique.dedup();
        if SAMPLES.len() != FILE_COUNT || unique.len() != FILE_COUNT {
            return Err(format!(
                "SAMPLES has {} rows, {} unique names; FILE_COUNT is {FILE_COUNT}",
                SAMPLES.len(),
                unique.len(),
            ));
        }

        packaged.sort();
        embedded.sort();
        if packaged != embedded {
            let unembedded: Vec<&str> = packaged
                .iter()
                .filter(|name| embedded.binary_search(name).is_err())
                .map(String::as_str)
                .collect();
            let unpackaged: Vec<&str> = embedded
                .iter()
                .filter(|name| packaged.binary_search(name).is_err())
                .map(String::as_str)
                .collect();
            return Err(format!(
                "packaged WAVs absent from SAMPLES: {unembedded:?}; \
                 SAMPLES entries absent from the package: {unpackaged:?}",
            ));
        }
        Ok(())
    }

    /// The embedded table must match the packaged directory exactly. Catches a
    /// sample added to `samples/` without regenerating, and vice versa.
    #[test]
    fn inventory_matches_packaged_wavs() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let packaged = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|entry| {
                entry
                    .expect("sample directory entry must be readable")
                    .path()
            })
            .filter(|path| path.extension() == Some(OsStr::new("wav")))
            .map(|path| {
                path.file_name()
                    .expect("sample must have a file name")
                    .to_string_lossy()
                    .into_owned()
            })
            .collect();
        validate_packaged_inventory(packaged)
            .unwrap_or_else(|error| panic!("packaged inventory mismatch: {error}"));

        for (name, bytes) in SAMPLES.iter() {
            assert!(name.ends_with(".wav"), "{name} is not a .wav");
            assert!(bytes.len() > 44, "{name} is smaller than a WAV header");
        }
    }

    #[test]
    fn inventory_comparison_rejects_an_unembedded_packaged_wav() {
        let mut packaged: Vec<String> =
            SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();
        packaged.push("unembedded_fixture.wav".to_owned());

        let error = validate_packaged_inventory(packaged)
            .expect_err("an unembedded packaged WAV must fail the inventory oracle");
        assert!(error.contains("unembedded_fixture.wav"), "{error}");
    }

    /// Velocity splits, carried over from the core crate's test when these banks
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
        const EXPECTED_BYTES: usize = 7647408;
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

    #[test]
    fn lookup_misses_do_not_initialize_pcm_cache() {
        const PROBE: &str = "FERRO_DRUMKIT2_PCM_MISS_PROBE";
        const NAME: &str = "tests::lookup_misses_do_not_initialize_pcm_cache";

        if std::env::var_os(PROBE).is_none() {
            let output = std::process::Command::new(
                std::env::current_exe().expect("the test binary's own path"),
            )
            .args([NAME, "--exact", "--nocapture", "--test-threads=1"])
            .env(PROBE, "1")
            .output()
            .expect("re-exec this test in a pristine process");
            assert!(
                output.status.success(),
                "the pristine-process PCM lookup probe failed:\n{}\n{}",
                String::from_utf8_lossy(&output.stdout),
                String::from_utf8_lossy(&output.stderr),
            );
            return;
        }

        assert_eq!(pcm_cache_initializations(), 0);
        assert_eq!(pcm("missing.wav"), None);
        assert_eq!(pcm_by_index(SAMPLES.len()), None);
        assert_eq!(
            pcm_cache_initializations(),
            0,
            "failed lookups initialized the package-wide PCM cache",
        );

        assert!(!pcm(SAMPLES[0].0)
            .expect("known sample must resolve")
            .is_empty());
        assert_eq!(
            pcm_cache_initializations(),
            1,
            "a valid lookup must preserve intentional eager initialization",
        );
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
                    let index = bank.take_index(layer, rr);
                    assert!(
                        get(&name).is_some(),
                        "{name}: bank {} does not resolve in this crate",
                        bank.name
                    );
                    assert_eq!(
                        SAMPLES[index].0, name,
                        "{} mapped the wrong take",
                        bank.name
                    );
                    assert!(std::ptr::eq(
                        bank.pcm(layer, rr),
                        pcm_by_index(index).expect("bank index is in range"),
                    ));
                    assert!(!bank.pcm(layer, rr).is_empty(), "{name}: empty PCM");
                    takes += 1;
                }
            }
        }
        assert_eq!(takes, FILE_COUNT, "banks do not cover the embedded files");
    }
}
