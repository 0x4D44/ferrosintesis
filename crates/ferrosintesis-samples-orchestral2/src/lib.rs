//! Embedded CC0 1.0 instrument-onset samples for ferrosintesis.
//!
//! The second CC0 onset crate: the original `ferrosintesis-samples-orchestral` is
//! at the crates.io per-crate size cap, so newer CC0 families land here. Each WAV
//! is a mono 16-bit 44.1 kHz attack transient; `ferrosintesis` plays it as a note's
//! onset and crossfades into the modeled sustain. Consumers normally access this
//! crate through `ferrosintesis`, not directly. All samples are CC0 1.0 /
//! public-domain — no attribution required; provenance is in README.md and
//! `tools/ferrosintesis-samples/`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice (not a fixed-size array) so families can be
/// added without threading a count constant through the file.
static SAMPLES: &[(&str, &[u8])] = &[
    ("harp_A2.wav", include_bytes!("../samples/harp_A2.wav")),
    ("harp_A6.wav", include_bytes!("../samples/harp_A6.wav")),
    ("harp_B3.wav", include_bytes!("../samples/harp_B3.wav")),
    ("harp_C5.wav", include_bytes!("../samples/harp_C5.wav")),
    ("harp_D2.wav", include_bytes!("../samples/harp_D2.wav")),
    ("harp_D6.wav", include_bytes!("../samples/harp_D6.wav")),
    ("harp_E3.wav", include_bytes!("../samples/harp_E3.wav")),
    ("harp_F4.wav", include_bytes!("../samples/harp_F4.wav")),
    ("harp_F7.wav", include_bytes!("../samples/harp_F7.wav")),
    ("harp_G1.wav", include_bytes!("../samples/harp_G1.wav")),
    ("harp_G5.wav", include_bytes!("../samples/harp_G5.wav")),
];

/// Number of embedded WAV files.
pub const FILE_COUNT: usize = SAMPLES.len();

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::ffi::OsStr;
    use std::fs;
    use std::path::Path;

    #[test]
    fn inventory_matches_packaged_wavs() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|entry| entry.expect("sample entry must be readable").path())
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

        assert_eq!(embedded, packaged, "embedded list must match packaged WAVs");
        assert_eq!(embedded.len(), FILE_COUNT);
    }

    #[test]
    fn every_sample_is_a_nonempty_wav() {
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 44, "{name} is too short to be a WAV");
            assert_eq!(&bytes[..4], b"RIFF", "{name} has no RIFF header");
            assert_eq!(&bytes[8..12], b"WAVE", "{name} has no WAVE signature");
            assert_eq!(get(name), Some(*bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }
}
