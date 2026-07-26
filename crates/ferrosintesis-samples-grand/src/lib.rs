//! Embedded CC BY 3.0 Salamander Grand Piano V3 attack/body samples for the
//! GM 0 Acoustic Grand alternate (CC0=2).
//!
//! A real Yamaha C5 concert grand (9 pitch zones C2–C6 × 3 dynamics × 2 round
//! robins), voicing the GM 0 Acoustic Grand CC0=2 alternate so it is a distinct
//! instrument from the CC0 VSCO *upright* that is the GM 0 CC0=1 alternate.
//! Consumers normally access this crate
//! through `ferrosintesis`. Attribution obligations are in `NOTICE`.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 54;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "grand_C2_f.wav",
        include_bytes!("../samples/grand_C2_f.wav"),
    ),
    (
        "grand_C2_f_rr2.wav",
        include_bytes!("../samples/grand_C2_f_rr2.wav"),
    ),
    (
        "grand_C2_mf.wav",
        include_bytes!("../samples/grand_C2_mf.wav"),
    ),
    (
        "grand_C2_mf_rr2.wav",
        include_bytes!("../samples/grand_C2_mf_rr2.wav"),
    ),
    (
        "grand_C2_pp.wav",
        include_bytes!("../samples/grand_C2_pp.wav"),
    ),
    (
        "grand_C2_pp_rr2.wav",
        include_bytes!("../samples/grand_C2_pp_rr2.wav"),
    ),
    (
        "grand_C3_f.wav",
        include_bytes!("../samples/grand_C3_f.wav"),
    ),
    (
        "grand_C3_f_rr2.wav",
        include_bytes!("../samples/grand_C3_f_rr2.wav"),
    ),
    (
        "grand_C3_mf.wav",
        include_bytes!("../samples/grand_C3_mf.wav"),
    ),
    (
        "grand_C3_mf_rr2.wav",
        include_bytes!("../samples/grand_C3_mf_rr2.wav"),
    ),
    (
        "grand_C3_pp.wav",
        include_bytes!("../samples/grand_C3_pp.wav"),
    ),
    (
        "grand_C3_pp_rr2.wav",
        include_bytes!("../samples/grand_C3_pp_rr2.wav"),
    ),
    (
        "grand_C4_f.wav",
        include_bytes!("../samples/grand_C4_f.wav"),
    ),
    (
        "grand_C4_f_rr2.wav",
        include_bytes!("../samples/grand_C4_f_rr2.wav"),
    ),
    (
        "grand_C4_mf.wav",
        include_bytes!("../samples/grand_C4_mf.wav"),
    ),
    (
        "grand_C4_mf_rr2.wav",
        include_bytes!("../samples/grand_C4_mf_rr2.wav"),
    ),
    (
        "grand_C4_pp.wav",
        include_bytes!("../samples/grand_C4_pp.wav"),
    ),
    (
        "grand_C4_pp_rr2.wav",
        include_bytes!("../samples/grand_C4_pp_rr2.wav"),
    ),
    (
        "grand_C5_f.wav",
        include_bytes!("../samples/grand_C5_f.wav"),
    ),
    (
        "grand_C5_f_rr2.wav",
        include_bytes!("../samples/grand_C5_f_rr2.wav"),
    ),
    (
        "grand_C5_mf.wav",
        include_bytes!("../samples/grand_C5_mf.wav"),
    ),
    (
        "grand_C5_mf_rr2.wav",
        include_bytes!("../samples/grand_C5_mf_rr2.wav"),
    ),
    (
        "grand_C5_pp.wav",
        include_bytes!("../samples/grand_C5_pp.wav"),
    ),
    (
        "grand_C5_pp_rr2.wav",
        include_bytes!("../samples/grand_C5_pp_rr2.wav"),
    ),
    (
        "grand_C6_f.wav",
        include_bytes!("../samples/grand_C6_f.wav"),
    ),
    (
        "grand_C6_f_rr2.wav",
        include_bytes!("../samples/grand_C6_f_rr2.wav"),
    ),
    (
        "grand_C6_mf.wav",
        include_bytes!("../samples/grand_C6_mf.wav"),
    ),
    (
        "grand_C6_mf_rr2.wav",
        include_bytes!("../samples/grand_C6_mf_rr2.wav"),
    ),
    (
        "grand_C6_pp.wav",
        include_bytes!("../samples/grand_C6_pp.wav"),
    ),
    (
        "grand_C6_pp_rr2.wav",
        include_bytes!("../samples/grand_C6_pp_rr2.wav"),
    ),
    (
        "grand_F#2_f.wav",
        include_bytes!("../samples/grand_F#2_f.wav"),
    ),
    (
        "grand_F#2_f_rr2.wav",
        include_bytes!("../samples/grand_F#2_f_rr2.wav"),
    ),
    (
        "grand_F#2_mf.wav",
        include_bytes!("../samples/grand_F#2_mf.wav"),
    ),
    (
        "grand_F#2_mf_rr2.wav",
        include_bytes!("../samples/grand_F#2_mf_rr2.wav"),
    ),
    (
        "grand_F#2_pp.wav",
        include_bytes!("../samples/grand_F#2_pp.wav"),
    ),
    (
        "grand_F#2_pp_rr2.wav",
        include_bytes!("../samples/grand_F#2_pp_rr2.wav"),
    ),
    (
        "grand_F#3_f.wav",
        include_bytes!("../samples/grand_F#3_f.wav"),
    ),
    (
        "grand_F#3_f_rr2.wav",
        include_bytes!("../samples/grand_F#3_f_rr2.wav"),
    ),
    (
        "grand_F#3_mf.wav",
        include_bytes!("../samples/grand_F#3_mf.wav"),
    ),
    (
        "grand_F#3_mf_rr2.wav",
        include_bytes!("../samples/grand_F#3_mf_rr2.wav"),
    ),
    (
        "grand_F#3_pp.wav",
        include_bytes!("../samples/grand_F#3_pp.wav"),
    ),
    (
        "grand_F#3_pp_rr2.wav",
        include_bytes!("../samples/grand_F#3_pp_rr2.wav"),
    ),
    (
        "grand_F#4_f.wav",
        include_bytes!("../samples/grand_F#4_f.wav"),
    ),
    (
        "grand_F#4_f_rr2.wav",
        include_bytes!("../samples/grand_F#4_f_rr2.wav"),
    ),
    (
        "grand_F#4_mf.wav",
        include_bytes!("../samples/grand_F#4_mf.wav"),
    ),
    (
        "grand_F#4_mf_rr2.wav",
        include_bytes!("../samples/grand_F#4_mf_rr2.wav"),
    ),
    (
        "grand_F#4_pp.wav",
        include_bytes!("../samples/grand_F#4_pp.wav"),
    ),
    (
        "grand_F#4_pp_rr2.wav",
        include_bytes!("../samples/grand_F#4_pp_rr2.wav"),
    ),
    (
        "grand_F#5_f.wav",
        include_bytes!("../samples/grand_F#5_f.wav"),
    ),
    (
        "grand_F#5_f_rr2.wav",
        include_bytes!("../samples/grand_F#5_f_rr2.wav"),
    ),
    (
        "grand_F#5_mf.wav",
        include_bytes!("../samples/grand_F#5_mf.wav"),
    ),
    (
        "grand_F#5_mf_rr2.wav",
        include_bytes!("../samples/grand_F#5_mf_rr2.wav"),
    ),
    (
        "grand_F#5_pp.wav",
        include_bytes!("../samples/grand_F#5_pp.wav"),
    ),
    (
        "grand_F#5_pp_rr2.wav",
        include_bytes!("../samples/grand_F#5_pp_rr2.wav"),
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

    // Aggregate byte size of the 54 embedded WAVs; regenerate with prepare.py and
    // re-pin if the bank changes. Guards against an accidental sample re-cut.
    const EXPECTED_BYTES: usize = 7_184_592;

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
