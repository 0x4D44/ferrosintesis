//! Embedded CC BY 3.0 gong-ageng samples for the GM14 CC0=2 pitched gong.
//!
//! Two full-ring one-shot layers (soft + loud). Consumers normally access this
//! crate through `ferrosintesis`. Attribution obligations are in `NOTICE`.
//! Licence/provenance: see `NOTICE` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of sample files embedded in this package.
pub const FILE_COUNT: usize = 2;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "gong_ageng_loud.flac",
        include_bytes!("../samples/gong_ageng_loud.flac"),
    ),
    (
        "gong_ageng_soft.flac",
        include_bytes!("../samples/gong_ageng_soft.flac"),
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

    const EXPECTED_BYTES: usize = 1160636;

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
