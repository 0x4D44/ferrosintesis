//! Embedded MIT-licensed clavinet samples for the GM7 default sampled clavinet.
//!
//! Eleven baked, pitch-synchronous decaying clavinet notes (sounding G1-G6),
//! extracted from the MuseScore "MS Basic" soundfont (MIT). Consumers normally
//! access this crate through `ferrosintesis`. Attribution obligations are in
//! `NOTICE`; source and pin are in `PROVENANCE.md`.
//! Licence/provenance: see `NOTICE` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of sample files embedded in this package.
pub const FILE_COUNT: usize = 11;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "clavinet_C2.flac",
        include_bytes!("../samples/clavinet_C2.flac"),
    ),
    (
        "clavinet_C3.flac",
        include_bytes!("../samples/clavinet_C3.flac"),
    ),
    (
        "clavinet_C4.flac",
        include_bytes!("../samples/clavinet_C4.flac"),
    ),
    (
        "clavinet_C5.flac",
        include_bytes!("../samples/clavinet_C5.flac"),
    ),
    (
        "clavinet_C6.flac",
        include_bytes!("../samples/clavinet_C6.flac"),
    ),
    (
        "clavinet_G1.flac",
        include_bytes!("../samples/clavinet_G1.flac"),
    ),
    (
        "clavinet_G2.flac",
        include_bytes!("../samples/clavinet_G2.flac"),
    ),
    (
        "clavinet_G3.flac",
        include_bytes!("../samples/clavinet_G3.flac"),
    ),
    (
        "clavinet_G4.flac",
        include_bytes!("../samples/clavinet_G4.flac"),
    ),
    (
        "clavinet_G5.flac",
        include_bytes!("../samples/clavinet_G5.flac"),
    ),
    (
        "clavinet_G6.flac",
        include_bytes!("../samples/clavinet_G6.flac"),
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

    const EXPECTED_BYTES: usize = 529574;

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
