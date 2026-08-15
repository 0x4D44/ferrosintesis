//! Embedded CC0 Freesound blown-bottle loop sample for GM 76.
//!
//! A single real "blown bottle" recording (Freesound 349867, CC0 1.0), baked into a
//! looped-sustain take that voices the GM 76 blown bottle as an LA sample layer. The
//! recorded attack blows through once, then a pitch-synchronous loop of the recorded
//! body carries the hold. Consumers normally access this crate through `ferrosintesis`.
//! CC0 1.0 — no attribution required; provenance is in `PROVENANCE.md`.
//! Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 1;

static SAMPLES: [(&str, &[u8]); 1] = [(
    "bottleloop_G3.wav",
    include_bytes!("../samples/bottleloop_G3.wav"),
)];

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
    fn embedded_names_are_unique() {
        let mut names: Vec<&str> = SAMPLES.iter().map(|(name, _)| *name).collect();
        let total = names.len();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), total, "duplicate sample name in the bank");
        assert_eq!(total, FILE_COUNT);
    }

    #[test]
    fn every_sample_is_a_nonempty_wav() {
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a WAV");
            assert_eq!(&bytes[..4], b"RIFF", "{name} has no RIFF header");
            assert_eq!(&bytes[8..12], b"WAVE", "{name} has no WAVE signature");
            assert_eq!(get(name), Some(bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }
}
