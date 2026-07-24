//! Embedded CC0 owner-recorded fret-noise one-shots for GM 120 (Guitar Fret Noise).
//!
//! Twelve finger-slide takes on Arthur's Eastman E1D (all strings damped at the nut),
//! played as a round-robin one-shot bank by `ferrosintesis`. Consumers normally access
//! this crate through `ferrosintesis`. CC0-1.0 (public-domain dedication) — no
//! attribution obligation; see `PROVENANCE.md` for the recording provenance.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 12;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "fretnoise_rr01.wav",
        include_bytes!("../samples/fretnoise_rr01.wav"),
    ),
    (
        "fretnoise_rr02.wav",
        include_bytes!("../samples/fretnoise_rr02.wav"),
    ),
    (
        "fretnoise_rr03.wav",
        include_bytes!("../samples/fretnoise_rr03.wav"),
    ),
    (
        "fretnoise_rr04.wav",
        include_bytes!("../samples/fretnoise_rr04.wav"),
    ),
    (
        "fretnoise_rr05.wav",
        include_bytes!("../samples/fretnoise_rr05.wav"),
    ),
    (
        "fretnoise_rr06.wav",
        include_bytes!("../samples/fretnoise_rr06.wav"),
    ),
    (
        "fretnoise_rr07.wav",
        include_bytes!("../samples/fretnoise_rr07.wav"),
    ),
    (
        "fretnoise_rr08.wav",
        include_bytes!("../samples/fretnoise_rr08.wav"),
    ),
    (
        "fretnoise_rr09.wav",
        include_bytes!("../samples/fretnoise_rr09.wav"),
    ),
    (
        "fretnoise_rr10.wav",
        include_bytes!("../samples/fretnoise_rr10.wav"),
    ),
    (
        "fretnoise_rr11.wav",
        include_bytes!("../samples/fretnoise_rr11.wav"),
    ),
    (
        "fretnoise_rr12.wav",
        include_bytes!("../samples/fretnoise_rr12.wav"),
    ),
];

/// The number of round-robin takes in the bank. The synth cycles these so
/// consecutive fret-noise events do not repeat the same sample.
pub const ROUND_ROBINS: usize = FILE_COUNT;

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

/// The file name of round-robin take `rr` (0-based, wraps at [`ROUND_ROBINS`]).
pub fn take_name(rr: usize) -> &'static str {
    SAMPLES[rr % ROUND_ROBINS].0
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::OsStr;
    use std::fs;
    use std::path::Path;

    const EXPECTED_BYTES: usize = 1_021_972;

    #[test]
    fn inventory_matches_packaged_wavs() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|entry| entry.expect("sample dir entry must be readable").path())
            .filter(|path| path.extension() == Some(OsStr::new("wav")))
            .map(|path| {
                path.file_name()
                    .expect("sample must have a file name")
                    .to_string_lossy()
                    .into_owned()
            })
            .collect();
        packaged.sort();

        let mut embedded: Vec<String> =
            SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();
        embedded.sort();

        assert_eq!(packaged.len(), FILE_COUNT);
        assert_eq!(embedded, packaged);
    }

    #[test]
    fn every_sample_is_a_nonempty_wav_with_the_expected_aggregate_size() {
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
    fn take_name_wraps_round_robin() {
        assert_eq!(take_name(0), "fretnoise_rr01.wav");
        assert_eq!(take_name(ROUND_ROBINS), take_name(0));
        assert_eq!(take_name(ROUND_ROBINS + 3), take_name(3));
    }
}
