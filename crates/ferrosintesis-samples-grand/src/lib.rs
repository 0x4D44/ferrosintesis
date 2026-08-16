//! Embedded CC BY 3.0 Salamander Grand Piano V3 attack/body samples for the
//! GM 0 Acoustic Grand alternate (CC0=2).
//!
//! A real Yamaha C5 concert grand (9 pitch zones C2–C6 × 3 dynamics × 2 round
//! robins), voicing the GM 0 Acoustic Grand CC0=2 alternate so it is a distinct
//! instrument from the CC0 VSCO *upright* that is the GM 0 CC0=1 alternate.
//! Consumers normally access this crate
//! through `ferrosintesis`. Attribution obligations are in `NOTICE`.
//! Licence/provenance: see `NOTICE` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of sample files embedded in this package.
pub const FILE_COUNT: usize = 54;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "grand_C2_f.flac",
        include_bytes!("../samples/grand_C2_f.flac"),
    ),
    (
        "grand_C2_f_rr2.flac",
        include_bytes!("../samples/grand_C2_f_rr2.flac"),
    ),
    (
        "grand_C2_mf.flac",
        include_bytes!("../samples/grand_C2_mf.flac"),
    ),
    (
        "grand_C2_mf_rr2.flac",
        include_bytes!("../samples/grand_C2_mf_rr2.flac"),
    ),
    (
        "grand_C2_pp.flac",
        include_bytes!("../samples/grand_C2_pp.flac"),
    ),
    (
        "grand_C2_pp_rr2.flac",
        include_bytes!("../samples/grand_C2_pp_rr2.flac"),
    ),
    (
        "grand_C3_f.flac",
        include_bytes!("../samples/grand_C3_f.flac"),
    ),
    (
        "grand_C3_f_rr2.flac",
        include_bytes!("../samples/grand_C3_f_rr2.flac"),
    ),
    (
        "grand_C3_mf.flac",
        include_bytes!("../samples/grand_C3_mf.flac"),
    ),
    (
        "grand_C3_mf_rr2.flac",
        include_bytes!("../samples/grand_C3_mf_rr2.flac"),
    ),
    (
        "grand_C3_pp.flac",
        include_bytes!("../samples/grand_C3_pp.flac"),
    ),
    (
        "grand_C3_pp_rr2.flac",
        include_bytes!("../samples/grand_C3_pp_rr2.flac"),
    ),
    (
        "grand_C4_f.flac",
        include_bytes!("../samples/grand_C4_f.flac"),
    ),
    (
        "grand_C4_f_rr2.flac",
        include_bytes!("../samples/grand_C4_f_rr2.flac"),
    ),
    (
        "grand_C4_mf.flac",
        include_bytes!("../samples/grand_C4_mf.flac"),
    ),
    (
        "grand_C4_mf_rr2.flac",
        include_bytes!("../samples/grand_C4_mf_rr2.flac"),
    ),
    (
        "grand_C4_pp.flac",
        include_bytes!("../samples/grand_C4_pp.flac"),
    ),
    (
        "grand_C4_pp_rr2.flac",
        include_bytes!("../samples/grand_C4_pp_rr2.flac"),
    ),
    (
        "grand_C5_f.flac",
        include_bytes!("../samples/grand_C5_f.flac"),
    ),
    (
        "grand_C5_f_rr2.flac",
        include_bytes!("../samples/grand_C5_f_rr2.flac"),
    ),
    (
        "grand_C5_mf.flac",
        include_bytes!("../samples/grand_C5_mf.flac"),
    ),
    (
        "grand_C5_mf_rr2.flac",
        include_bytes!("../samples/grand_C5_mf_rr2.flac"),
    ),
    (
        "grand_C5_pp.flac",
        include_bytes!("../samples/grand_C5_pp.flac"),
    ),
    (
        "grand_C5_pp_rr2.flac",
        include_bytes!("../samples/grand_C5_pp_rr2.flac"),
    ),
    (
        "grand_C6_f.flac",
        include_bytes!("../samples/grand_C6_f.flac"),
    ),
    (
        "grand_C6_f_rr2.flac",
        include_bytes!("../samples/grand_C6_f_rr2.flac"),
    ),
    (
        "grand_C6_mf.flac",
        include_bytes!("../samples/grand_C6_mf.flac"),
    ),
    (
        "grand_C6_mf_rr2.flac",
        include_bytes!("../samples/grand_C6_mf_rr2.flac"),
    ),
    (
        "grand_C6_pp.flac",
        include_bytes!("../samples/grand_C6_pp.flac"),
    ),
    (
        "grand_C6_pp_rr2.flac",
        include_bytes!("../samples/grand_C6_pp_rr2.flac"),
    ),
    (
        "grand_F#2_f.flac",
        include_bytes!("../samples/grand_F#2_f.flac"),
    ),
    (
        "grand_F#2_f_rr2.flac",
        include_bytes!("../samples/grand_F#2_f_rr2.flac"),
    ),
    (
        "grand_F#2_mf.flac",
        include_bytes!("../samples/grand_F#2_mf.flac"),
    ),
    (
        "grand_F#2_mf_rr2.flac",
        include_bytes!("../samples/grand_F#2_mf_rr2.flac"),
    ),
    (
        "grand_F#2_pp.flac",
        include_bytes!("../samples/grand_F#2_pp.flac"),
    ),
    (
        "grand_F#2_pp_rr2.flac",
        include_bytes!("../samples/grand_F#2_pp_rr2.flac"),
    ),
    (
        "grand_F#3_f.flac",
        include_bytes!("../samples/grand_F#3_f.flac"),
    ),
    (
        "grand_F#3_f_rr2.flac",
        include_bytes!("../samples/grand_F#3_f_rr2.flac"),
    ),
    (
        "grand_F#3_mf.flac",
        include_bytes!("../samples/grand_F#3_mf.flac"),
    ),
    (
        "grand_F#3_mf_rr2.flac",
        include_bytes!("../samples/grand_F#3_mf_rr2.flac"),
    ),
    (
        "grand_F#3_pp.flac",
        include_bytes!("../samples/grand_F#3_pp.flac"),
    ),
    (
        "grand_F#3_pp_rr2.flac",
        include_bytes!("../samples/grand_F#3_pp_rr2.flac"),
    ),
    (
        "grand_F#4_f.flac",
        include_bytes!("../samples/grand_F#4_f.flac"),
    ),
    (
        "grand_F#4_f_rr2.flac",
        include_bytes!("../samples/grand_F#4_f_rr2.flac"),
    ),
    (
        "grand_F#4_mf.flac",
        include_bytes!("../samples/grand_F#4_mf.flac"),
    ),
    (
        "grand_F#4_mf_rr2.flac",
        include_bytes!("../samples/grand_F#4_mf_rr2.flac"),
    ),
    (
        "grand_F#4_pp.flac",
        include_bytes!("../samples/grand_F#4_pp.flac"),
    ),
    (
        "grand_F#4_pp_rr2.flac",
        include_bytes!("../samples/grand_F#4_pp_rr2.flac"),
    ),
    (
        "grand_F#5_f.flac",
        include_bytes!("../samples/grand_F#5_f.flac"),
    ),
    (
        "grand_F#5_f_rr2.flac",
        include_bytes!("../samples/grand_F#5_f_rr2.flac"),
    ),
    (
        "grand_F#5_mf.flac",
        include_bytes!("../samples/grand_F#5_mf.flac"),
    ),
    (
        "grand_F#5_mf_rr2.flac",
        include_bytes!("../samples/grand_F#5_mf_rr2.flac"),
    ),
    (
        "grand_F#5_pp.flac",
        include_bytes!("../samples/grand_F#5_pp.flac"),
    ),
    (
        "grand_F#5_pp_rr2.flac",
        include_bytes!("../samples/grand_F#5_pp_rr2.flac"),
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
    const EXPECTED_BYTES: usize = 2361631;

    #[test]
    fn inventory_matches_packaged_samples() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|entry| {
                entry
                    .expect("sample directory entry must be readable")
                    .path()
            })
            .filter(|path| {
                matches!(
                    path.extension().and_then(OsStr::to_str),
                    Some("wav" | "flac")
                )
            })
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
    fn every_sample_is_a_nonempty_bank_file_with_the_expected_size() {
        assert_eq!(
            SAMPLES.iter().map(|(_, bytes)| bytes.len()).sum::<usize>(),
            EXPECTED_BYTES
        );
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a sample");
            let riff = &bytes[..4] == b"RIFF" && &bytes[8..12] == b"WAVE";
            let flac = &bytes[..4] == b"fLaC";
            assert!(riff || flac, "{name} is neither RIFF/WAVE nor FLAC");
            assert_eq!(get(name), Some(bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }
}
