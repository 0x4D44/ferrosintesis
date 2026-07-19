//! Embedded CC0 1.0 solo-bowed-string onset samples for ferrosintesis.
//!
//! Real SOLO cello (GM 42, Karoryfer x bigcat "Bigcat Cello", down-bow arco) and
//! SOLO double bass (GM 43, VSCO 2 CE "Solo Contrabass", non-vibrato arco) attack
//! transients. These replace the previous onset for GM 42/43, which repitched the
//! VSCO cello-*section* (`celens`) samples — an ensemble recording that read as a
//! small cello section rather than a soloist, and (for GM 43) as a cello an octave
//! low rather than a double bass. Each WAV is a mono 16-bit 44.1 kHz onset;
//! `ferrosintesis` plays it as the note's attack and crossfades into the modeled
//! bowed-string waveguide sustain. Consumers normally access this crate through
//! `ferrosintesis`, not directly. All samples are CC0 1.0 / public-domain — no
//! attribution required; provenance is in README.md and `tools/ferrosintesis-samples/`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice (not a fixed-size array) so families can be
/// added without threading a count constant through the file.
static SAMPLES: &[(&str, &[u8])] = &[
    (
        "cellosolo_A2_f.wav",
        include_bytes!("../samples/cellosolo_A2_f.wav"),
    ),
    (
        "cellosolo_A2_p.wav",
        include_bytes!("../samples/cellosolo_A2_p.wav"),
    ),
    (
        "cellosolo_A3_f.wav",
        include_bytes!("../samples/cellosolo_A3_f.wav"),
    ),
    (
        "cellosolo_A3_p.wav",
        include_bytes!("../samples/cellosolo_A3_p.wav"),
    ),
    (
        "cellosolo_A4_f.wav",
        include_bytes!("../samples/cellosolo_A4_f.wav"),
    ),
    (
        "cellosolo_A4_p.wav",
        include_bytes!("../samples/cellosolo_A4_p.wav"),
    ),
    (
        "cellosolo_C2_f.wav",
        include_bytes!("../samples/cellosolo_C2_f.wav"),
    ),
    (
        "cellosolo_C2_p.wav",
        include_bytes!("../samples/cellosolo_C2_p.wav"),
    ),
    (
        "cellosolo_C3_f.wav",
        include_bytes!("../samples/cellosolo_C3_f.wav"),
    ),
    (
        "cellosolo_C3_p.wav",
        include_bytes!("../samples/cellosolo_C3_p.wav"),
    ),
    (
        "cellosolo_C4_f.wav",
        include_bytes!("../samples/cellosolo_C4_f.wav"),
    ),
    (
        "cellosolo_C4_p.wav",
        include_bytes!("../samples/cellosolo_C4_p.wav"),
    ),
    (
        "cellosolo_C5_f.wav",
        include_bytes!("../samples/cellosolo_C5_f.wav"),
    ),
    (
        "cellosolo_C5_p.wav",
        include_bytes!("../samples/cellosolo_C5_p.wav"),
    ),
    (
        "cellosolo_F#5_f.wav",
        include_bytes!("../samples/cellosolo_F#5_f.wav"),
    ),
    (
        "cellosolo_F#5_p.wav",
        include_bytes!("../samples/cellosolo_F#5_p.wav"),
    ),
    (
        "dbass_A#1_f.wav",
        include_bytes!("../samples/dbass_A#1_f.wav"),
    ),
    (
        "dbass_A#1_p.wav",
        include_bytes!("../samples/dbass_A#1_p.wav"),
    ),
    (
        "dbass_A2_f.wav",
        include_bytes!("../samples/dbass_A2_f.wav"),
    ),
    (
        "dbass_A2_p.wav",
        include_bytes!("../samples/dbass_A2_p.wav"),
    ),
    (
        "dbass_B3_f.wav",
        include_bytes!("../samples/dbass_B3_f.wav"),
    ),
    (
        "dbass_B3_p.wav",
        include_bytes!("../samples/dbass_B3_p.wav"),
    ),
    (
        "dbass_C#3_f.wav",
        include_bytes!("../samples/dbass_C#3_f.wav"),
    ),
    (
        "dbass_C#3_p.wav",
        include_bytes!("../samples/dbass_C#3_p.wav"),
    ),
    (
        "dbass_E1_f.wav",
        include_bytes!("../samples/dbass_E1_f.wav"),
    ),
    (
        "dbass_E1_p.wav",
        include_bytes!("../samples/dbass_E1_p.wav"),
    ),
    (
        "dbass_E2_f.wav",
        include_bytes!("../samples/dbass_E2_f.wav"),
    ),
    (
        "dbass_E2_p.wav",
        include_bytes!("../samples/dbass_E2_p.wav"),
    ),
    (
        "dbass_E3_f.wav",
        include_bytes!("../samples/dbass_E3_f.wav"),
    ),
    (
        "dbass_E3_p.wav",
        include_bytes!("../samples/dbass_E3_p.wav"),
    ),
    (
        "dbass_G#3_f.wav",
        include_bytes!("../samples/dbass_G#3_f.wav"),
    ),
    (
        "dbass_G#3_p.wav",
        include_bytes!("../samples/dbass_G#3_p.wav"),
    ),
    (
        "pizzbass_E1.wav",
        include_bytes!("../samples/pizzbass_E1.wav"),
    ),
    (
        "pizzbass_G1.wav",
        include_bytes!("../samples/pizzbass_G1.wav"),
    ),
    (
        "pizzbass_A#1.wav",
        include_bytes!("../samples/pizzbass_A#1.wav"),
    ),
    (
        "pizzbass_C2.wav",
        include_bytes!("../samples/pizzbass_C2.wav"),
    ),
    (
        "pizzbass_E2.wav",
        include_bytes!("../samples/pizzbass_E2.wav"),
    ),
    (
        "pizzbass_G#2.wav",
        include_bytes!("../samples/pizzbass_G#2.wav"),
    ),
    (
        "pizzbass_A2.wav",
        include_bytes!("../samples/pizzbass_A2.wav"),
    ),
    (
        "pizzbass_G#3.wav",
        include_bytes!("../samples/pizzbass_G#3.wav"),
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
