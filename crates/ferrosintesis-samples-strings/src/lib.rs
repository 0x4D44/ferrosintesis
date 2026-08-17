//! Embedded CC0 1.0 solo string onset samples for ferrosintesis.
//!
//! Real SOLO cello (GM 42, Karoryfer x bigcat "Bigcat Cello", down-bow arco) and
//! SOLO double bass (GM 43, VSCO 2 CE "Solo Contrabass", non-vibrato arco), plus
//! VSCO 2 CE pizzicato double bass for GM 32 acoustic bass. The arco families
//! replace the previous onset for GM 42/43, which repitched the VSCO
//! cello-*section* (`celens`) samples — an ensemble recording that read as a small
//! cello section rather than a soloist, and (for GM 43) as a cello an octave low
//! rather than a double bass. Each sample is a mono 16-bit 44.1 kHz onset
//! stored as FLAC;
//! `ferrosintesis` plays it as the note's attack and crossfades into the
//! appropriate modeled sustain. Consumers normally access this crate through
//! `ferrosintesis`, not directly. All samples are CC0 1.0 / public-domain — no
//! attribution required; provenance is in packaged `PROVENANCE.md`.
//! Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice (not a fixed-size array) so families can be
/// added without threading a count constant through the file.
static SAMPLES: &[(&str, &[u8])] = &[
    (
        "cellosolo_A2_f.flac",
        include_bytes!("../samples/cellosolo_A2_f.flac"),
    ),
    (
        "cellosolo_A2_p.flac",
        include_bytes!("../samples/cellosolo_A2_p.flac"),
    ),
    (
        "cellosolo_A3_f.flac",
        include_bytes!("../samples/cellosolo_A3_f.flac"),
    ),
    (
        "cellosolo_A3_p.flac",
        include_bytes!("../samples/cellosolo_A3_p.flac"),
    ),
    (
        "cellosolo_A4_f.flac",
        include_bytes!("../samples/cellosolo_A4_f.flac"),
    ),
    (
        "cellosolo_A4_p.flac",
        include_bytes!("../samples/cellosolo_A4_p.flac"),
    ),
    (
        "cellosolo_C2_f.flac",
        include_bytes!("../samples/cellosolo_C2_f.flac"),
    ),
    (
        "cellosolo_C2_p.flac",
        include_bytes!("../samples/cellosolo_C2_p.flac"),
    ),
    (
        "cellosolo_C3_f.flac",
        include_bytes!("../samples/cellosolo_C3_f.flac"),
    ),
    (
        "cellosolo_C3_p.flac",
        include_bytes!("../samples/cellosolo_C3_p.flac"),
    ),
    (
        "cellosolo_C4_f.flac",
        include_bytes!("../samples/cellosolo_C4_f.flac"),
    ),
    (
        "cellosolo_C4_p.flac",
        include_bytes!("../samples/cellosolo_C4_p.flac"),
    ),
    (
        "cellosolo_C5_f.flac",
        include_bytes!("../samples/cellosolo_C5_f.flac"),
    ),
    (
        "cellosolo_C5_p.flac",
        include_bytes!("../samples/cellosolo_C5_p.flac"),
    ),
    (
        "cellosolo_F#5_f.flac",
        include_bytes!("../samples/cellosolo_F#5_f.flac"),
    ),
    (
        "cellosolo_F#5_p.flac",
        include_bytes!("../samples/cellosolo_F#5_p.flac"),
    ),
    (
        "dbass_A#1_f.flac",
        include_bytes!("../samples/dbass_A#1_f.flac"),
    ),
    (
        "dbass_A#1_p.flac",
        include_bytes!("../samples/dbass_A#1_p.flac"),
    ),
    (
        "dbass_A2_f.flac",
        include_bytes!("../samples/dbass_A2_f.flac"),
    ),
    (
        "dbass_A2_p.flac",
        include_bytes!("../samples/dbass_A2_p.flac"),
    ),
    (
        "dbass_B3_f.flac",
        include_bytes!("../samples/dbass_B3_f.flac"),
    ),
    (
        "dbass_B3_p.flac",
        include_bytes!("../samples/dbass_B3_p.flac"),
    ),
    (
        "dbass_C#3_f.flac",
        include_bytes!("../samples/dbass_C#3_f.flac"),
    ),
    (
        "dbass_C#3_p.flac",
        include_bytes!("../samples/dbass_C#3_p.flac"),
    ),
    (
        "dbass_E1_f.flac",
        include_bytes!("../samples/dbass_E1_f.flac"),
    ),
    (
        "dbass_E1_p.flac",
        include_bytes!("../samples/dbass_E1_p.flac"),
    ),
    (
        "dbass_E2_f.flac",
        include_bytes!("../samples/dbass_E2_f.flac"),
    ),
    (
        "dbass_E2_p.flac",
        include_bytes!("../samples/dbass_E2_p.flac"),
    ),
    (
        "dbass_E3_f.flac",
        include_bytes!("../samples/dbass_E3_f.flac"),
    ),
    (
        "dbass_E3_p.flac",
        include_bytes!("../samples/dbass_E3_p.flac"),
    ),
    (
        "dbass_G#3_f.flac",
        include_bytes!("../samples/dbass_G#3_f.flac"),
    ),
    (
        "dbass_G#3_p.flac",
        include_bytes!("../samples/dbass_G#3_p.flac"),
    ),
    (
        "pizzbass_E1.flac",
        include_bytes!("../samples/pizzbass_E1.flac"),
    ),
    (
        "pizzbass_G1.flac",
        include_bytes!("../samples/pizzbass_G1.flac"),
    ),
    (
        "pizzbass_A#1.flac",
        include_bytes!("../samples/pizzbass_A#1.flac"),
    ),
    (
        "pizzbass_C2.flac",
        include_bytes!("../samples/pizzbass_C2.flac"),
    ),
    (
        "pizzbass_E2.flac",
        include_bytes!("../samples/pizzbass_E2.flac"),
    ),
    (
        "pizzbass_G#2.flac",
        include_bytes!("../samples/pizzbass_G#2.flac"),
    ),
    (
        "pizzbass_A2.flac",
        include_bytes!("../samples/pizzbass_A2.flac"),
    ),
    (
        "pizzbass_G#3.flac",
        include_bytes!("../samples/pizzbass_G#3.flac"),
    ),
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
    fn inventory_matches_packaged_samples() {
        let samples_dir = Path::new(env!("CARGO_MANIFEST_DIR")).join("samples");
        let mut packaged: Vec<String> = fs::read_dir(samples_dir)
            .expect("sample directory must exist")
            .map(|entry| entry.expect("sample entry must be readable").path())
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

        assert_eq!(
            embedded, packaged,
            "embedded list must match packaged samples"
        );
        assert_eq!(embedded.len(), FILE_COUNT);
    }

    #[test]
    fn every_sample_is_a_nonempty_bank_file() {
        for (name, bytes) in SAMPLES {
            assert!(bytes.len() >= 12, "{name} is too short to be a sample");
            let riff = &bytes[..4] == b"RIFF" && &bytes[8..12] == b"WAVE";
            let flac = &bytes[..4] == b"fLaC";
            assert!(riff || flac, "{name} is neither RIFF/WAVE nor FLAC");
            assert_eq!(get(name), Some(*bytes));
        }
        assert_eq!(get("missing.wav"), None);
    }
}
