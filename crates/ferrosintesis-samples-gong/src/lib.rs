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

/// Returns the embedded FLAC bytes for an exact file name.
///
/// Supported names are `gong_ageng_loud.flac` and `gong_ageng_soft.flac`.
/// Names are case-sensitive.
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
    const DOCUMENTED_KEYS: [&str; FILE_COUNT] = ["gong_ageng_loud.flac", "gong_ageng_soft.flac"];

    #[test]
    fn documented_flac_lookup_contract_matches_packaged_inventory() {
        let api = include_str!("../src/lib.rs");
        let readme = include_str!("../README.md");
        let provenance = include_str!("../PROVENANCE.md");
        let stale_api_wording = ["embedded", "WAV", "bytes"].join(" ");
        let stale_api_suffix = ["`", ".", "wav", "` suffix"].concat();

        assert!(api.contains("Returns the embedded FLAC bytes"));
        assert!(!api.contains(&stale_api_wording));
        assert!(!api.contains(&stale_api_suffix));
        assert!(readme.contains("mono 16-bit 44.1 kHz FLACs"));
        assert!(readme.contains("encoded FLAC bytes"));
        assert!(!readme.contains("raw WAV bytes"));
        assert!(!readme.contains(&format!("Names include the {stale_api_suffix}")));
        assert!(provenance.contains("Aggregate: 1,160,636 bytes"));
        assert!(!provenance.contains("inventory_matches_packaged_wavs"));
        assert!(!provenance.contains("| `gong_ageng_soft.wav` | 261890 |"));
        assert!(!provenance.contains("| `gong_ageng_loud.wav` | 261893 |"));

        for name in DOCUMENTED_KEYS {
            assert!(readme.contains(name), "README must document {name}");
            assert!(provenance.contains(name), "PROVENANCE must document {name}");
            assert!(
                get(name).is_some(),
                "documented lookup key {name} must resolve"
            );
        }
    }

    #[test]
    fn inventory_matches_packaged_flac_samples() {
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
        assert!(packaged.iter().all(|name| name.ends_with(".flac")));
        assert_eq!(embedded, packaged);
    }

    #[test]
    fn every_sample_is_a_nonempty_bank_file_with_the_expected_size() {
        assert_eq!(
            SAMPLES.iter().map(|(_, bytes)| bytes.len()).sum::<usize>(),
            EXPECTED_BYTES,
            "packaged sample byte total differs; for FLAC banks, the pin is ffmpeg libavformat Lavf62.12.101 — check the encoder/version and recipe before re-pinning",
        );
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a sample");
            assert_eq!(&bytes[..4], b"fLaC", "{name} is not a FLAC file");
            assert_eq!(get(name), Some(bytes));
        }
        assert_eq!(get("missing.flac"), None);
        assert_eq!(get("gong_ageng_soft.wav"), None);
        assert_eq!(get("gong_ageng_loud.wav"), None);
    }
}
