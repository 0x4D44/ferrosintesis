//! Embedded CC BY 4.0 and CC BY 3.0 MTG.SoloSax saxophone samples for GM 64-67.
//!
//! Real solo-saxophone single notes (soprano/alto/tenor/baritone) from the MTG
//! good-sounds.org dataset (Neumann U87), supplying recorded attack plus looped recorded sustain
//! for the GM 64-67 saxophones. The modeled reed is the
//! `--no-samples` or unusable-loop fallback. Consumers normally access this crate
//! through `ferrosintesis`. Attribution obligations are in `NOTICE`.
//! Licence/provenance: see `NOTICE` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 74;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "sax_alt_A3_f.wav",
        include_bytes!("../samples/sax_alt_A3_f.wav"),
    ),
    (
        "sax_alt_A3_p.wav",
        include_bytes!("../samples/sax_alt_A3_p.wav"),
    ),
    (
        "sax_alt_A4_f.wav",
        include_bytes!("../samples/sax_alt_A4_f.wav"),
    ),
    (
        "sax_alt_A4_p.wav",
        include_bytes!("../samples/sax_alt_A4_p.wav"),
    ),
    (
        "sax_alt_A5_f.wav",
        include_bytes!("../samples/sax_alt_A5_f.wav"),
    ),
    (
        "sax_alt_A5_p.wav",
        include_bytes!("../samples/sax_alt_A5_p.wav"),
    ),
    (
        "sax_alt_C#3_f.wav",
        include_bytes!("../samples/sax_alt_C#3_f.wav"),
    ),
    (
        "sax_alt_C#3_p.wav",
        include_bytes!("../samples/sax_alt_C#3_p.wav"),
    ),
    (
        "sax_alt_C#4_f.wav",
        include_bytes!("../samples/sax_alt_C#4_f.wav"),
    ),
    (
        "sax_alt_C#4_p.wav",
        include_bytes!("../samples/sax_alt_C#4_p.wav"),
    ),
    (
        "sax_alt_C#5_f.wav",
        include_bytes!("../samples/sax_alt_C#5_f.wav"),
    ),
    (
        "sax_alt_C#5_p.wav",
        include_bytes!("../samples/sax_alt_C#5_p.wav"),
    ),
    (
        "sax_alt_F3_f.wav",
        include_bytes!("../samples/sax_alt_F3_f.wav"),
    ),
    (
        "sax_alt_F3_p.wav",
        include_bytes!("../samples/sax_alt_F3_p.wav"),
    ),
    (
        "sax_alt_F4_f.wav",
        include_bytes!("../samples/sax_alt_F4_f.wav"),
    ),
    (
        "sax_alt_F4_p.wav",
        include_bytes!("../samples/sax_alt_F4_p.wav"),
    ),
    (
        "sax_alt_F5_f.wav",
        include_bytes!("../samples/sax_alt_F5_f.wav"),
    ),
    (
        "sax_alt_F5_p.wav",
        include_bytes!("../samples/sax_alt_F5_p.wav"),
    ),
    (
        "sax_bar_A4_f.wav",
        include_bytes!("../samples/sax_bar_A4_f.wav"),
    ),
    (
        "sax_bar_A4_p.wav",
        include_bytes!("../samples/sax_bar_A4_p.wav"),
    ),
    (
        "sax_bar_C2_f.wav",
        include_bytes!("../samples/sax_bar_C2_f.wav"),
    ),
    (
        "sax_bar_C2_p.wav",
        include_bytes!("../samples/sax_bar_C2_p.wav"),
    ),
    (
        "sax_bar_C3_f.wav",
        include_bytes!("../samples/sax_bar_C3_f.wav"),
    ),
    (
        "sax_bar_C3_p.wav",
        include_bytes!("../samples/sax_bar_C3_p.wav"),
    ),
    (
        "sax_bar_C4_f.wav",
        include_bytes!("../samples/sax_bar_C4_f.wav"),
    ),
    (
        "sax_bar_C4_p.wav",
        include_bytes!("../samples/sax_bar_C4_p.wav"),
    ),
    (
        "sax_bar_E2_f.wav",
        include_bytes!("../samples/sax_bar_E2_f.wav"),
    ),
    (
        "sax_bar_E2_p.wav",
        include_bytes!("../samples/sax_bar_E2_p.wav"),
    ),
    (
        "sax_bar_E3_f.wav",
        include_bytes!("../samples/sax_bar_E3_f.wav"),
    ),
    (
        "sax_bar_E3_p.wav",
        include_bytes!("../samples/sax_bar_E3_p.wav"),
    ),
    (
        "sax_bar_E4_f.wav",
        include_bytes!("../samples/sax_bar_E4_f.wav"),
    ),
    (
        "sax_bar_E4_p.wav",
        include_bytes!("../samples/sax_bar_E4_p.wav"),
    ),
    (
        "sax_bar_G#2_f.wav",
        include_bytes!("../samples/sax_bar_G#2_f.wav"),
    ),
    (
        "sax_bar_G#2_p.wav",
        include_bytes!("../samples/sax_bar_G#2_p.wav"),
    ),
    (
        "sax_bar_G#3_f.wav",
        include_bytes!("../samples/sax_bar_G#3_f.wav"),
    ),
    (
        "sax_bar_G#3_p.wav",
        include_bytes!("../samples/sax_bar_G#3_p.wav"),
    ),
    (
        "sax_bar_G#4_f.wav",
        include_bytes!("../samples/sax_bar_G#4_f.wav"),
    ),
    (
        "sax_bar_G#4_p.wav",
        include_bytes!("../samples/sax_bar_G#4_p.wav"),
    ),
    (
        "sax_sop_C4_f.wav",
        include_bytes!("../samples/sax_sop_C4_f.wav"),
    ),
    (
        "sax_sop_C4_p.wav",
        include_bytes!("../samples/sax_sop_C4_p.wav"),
    ),
    (
        "sax_sop_C5_f.wav",
        include_bytes!("../samples/sax_sop_C5_f.wav"),
    ),
    (
        "sax_sop_C5_p.wav",
        include_bytes!("../samples/sax_sop_C5_p.wav"),
    ),
    (
        "sax_sop_C6_f.wav",
        include_bytes!("../samples/sax_sop_C6_f.wav"),
    ),
    (
        "sax_sop_C6_p.wav",
        include_bytes!("../samples/sax_sop_C6_p.wav"),
    ),
    (
        "sax_sop_E4_f.wav",
        include_bytes!("../samples/sax_sop_E4_f.wav"),
    ),
    (
        "sax_sop_E4_p.wav",
        include_bytes!("../samples/sax_sop_E4_p.wav"),
    ),
    (
        "sax_sop_E5_f.wav",
        include_bytes!("../samples/sax_sop_E5_f.wav"),
    ),
    (
        "sax_sop_E5_p.wav",
        include_bytes!("../samples/sax_sop_E5_p.wav"),
    ),
    (
        "sax_sop_E6_f.wav",
        include_bytes!("../samples/sax_sop_E6_f.wav"),
    ),
    (
        "sax_sop_E6_p.wav",
        include_bytes!("../samples/sax_sop_E6_p.wav"),
    ),
    (
        "sax_sop_G#3_f.wav",
        include_bytes!("../samples/sax_sop_G#3_f.wav"),
    ),
    (
        "sax_sop_G#3_p.wav",
        include_bytes!("../samples/sax_sop_G#3_p.wav"),
    ),
    (
        "sax_sop_G#4_f.wav",
        include_bytes!("../samples/sax_sop_G#4_f.wav"),
    ),
    (
        "sax_sop_G#4_p.wav",
        include_bytes!("../samples/sax_sop_G#4_p.wav"),
    ),
    (
        "sax_sop_G#5_f.wav",
        include_bytes!("../samples/sax_sop_G#5_f.wav"),
    ),
    (
        "sax_sop_G#5_p.wav",
        include_bytes!("../samples/sax_sop_G#5_p.wav"),
    ),
    (
        "sax_ten_C3_f.wav",
        include_bytes!("../samples/sax_ten_C3_f.wav"),
    ),
    (
        "sax_ten_C3_p.wav",
        include_bytes!("../samples/sax_ten_C3_p.wav"),
    ),
    (
        "sax_ten_C4_f.wav",
        include_bytes!("../samples/sax_ten_C4_f.wav"),
    ),
    (
        "sax_ten_C4_p.wav",
        include_bytes!("../samples/sax_ten_C4_p.wav"),
    ),
    (
        "sax_ten_C5_f.wav",
        include_bytes!("../samples/sax_ten_C5_f.wav"),
    ),
    (
        "sax_ten_C5_p.wav",
        include_bytes!("../samples/sax_ten_C5_p.wav"),
    ),
    (
        "sax_ten_E3_f.wav",
        include_bytes!("../samples/sax_ten_E3_f.wav"),
    ),
    (
        "sax_ten_E3_p.wav",
        include_bytes!("../samples/sax_ten_E3_p.wav"),
    ),
    (
        "sax_ten_E4_f.wav",
        include_bytes!("../samples/sax_ten_E4_f.wav"),
    ),
    (
        "sax_ten_E4_p.wav",
        include_bytes!("../samples/sax_ten_E4_p.wav"),
    ),
    (
        "sax_ten_E5_f.wav",
        include_bytes!("../samples/sax_ten_E5_f.wav"),
    ),
    (
        "sax_ten_E5_p.wav",
        include_bytes!("../samples/sax_ten_E5_p.wav"),
    ),
    (
        "sax_ten_G#2_f.wav",
        include_bytes!("../samples/sax_ten_G#2_f.wav"),
    ),
    (
        "sax_ten_G#2_p.wav",
        include_bytes!("../samples/sax_ten_G#2_p.wav"),
    ),
    (
        "sax_ten_G#3_f.wav",
        include_bytes!("../samples/sax_ten_G#3_f.wav"),
    ),
    (
        "sax_ten_G#3_p.wav",
        include_bytes!("../samples/sax_ten_G#3_p.wav"),
    ),
    (
        "sax_ten_G#4_f.wav",
        include_bytes!("../samples/sax_ten_G#4_f.wav"),
    ),
    (
        "sax_ten_G#4_p.wav",
        include_bytes!("../samples/sax_ten_G#4_p.wav"),
    ),
];

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

    // Aggregate byte size of the 74 embedded WAVs; regenerate with prepare.py
    // and re-pin if the bank changes. Guards against an accidental sample re-cut.
    const EXPECTED_BYTES: usize = 4_101_968;

    #[test]
    fn inventory_matches_packaged_wavs() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
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
}
