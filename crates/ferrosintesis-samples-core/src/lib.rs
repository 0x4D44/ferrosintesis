//! Embedded CC0 attack-transient samples for piano, violin, and flute voices.
//!
//! Consumers normally access this crate through `ferrosintesis`.
//! Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 69;

/// Upright-piano pitch/dynamic cells with only one take in the pinned source.
pub const PIANO_SINGLE_TAKE_CELLS: [(&str, &str); 2] = [("C2", "pp"), ("G2", "pp")];

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    ("flute_A4.wav", include_bytes!("../samples/flute_A4.wav")),
    ("flute_A5.wav", include_bytes!("../samples/flute_A5.wav")),
    ("flute_C4.wav", include_bytes!("../samples/flute_C4.wav")),
    ("flute_C6.wav", include_bytes!("../samples/flute_C6.wav")),
    ("flute_E5.wav", include_bytes!("../samples/flute_E5.wav")),
    (
        "piano_C2_f.wav",
        include_bytes!("../samples/piano_C2_f.wav"),
    ),
    (
        "piano_C2_f_rr2.wav",
        include_bytes!("../samples/piano_C2_f_rr2.wav"),
    ),
    (
        "piano_C2_mf.wav",
        include_bytes!("../samples/piano_C2_mf.wav"),
    ),
    (
        "piano_C2_mf_rr2.wav",
        include_bytes!("../samples/piano_C2_mf_rr2.wav"),
    ),
    (
        "piano_C2_pp.wav",
        include_bytes!("../samples/piano_C2_pp.wav"),
    ),
    (
        "piano_C3_f.wav",
        include_bytes!("../samples/piano_C3_f.wav"),
    ),
    (
        "piano_C3_f_rr2.wav",
        include_bytes!("../samples/piano_C3_f_rr2.wav"),
    ),
    (
        "piano_C3_mf.wav",
        include_bytes!("../samples/piano_C3_mf.wav"),
    ),
    (
        "piano_C3_mf_rr2.wav",
        include_bytes!("../samples/piano_C3_mf_rr2.wav"),
    ),
    (
        "piano_C3_pp.wav",
        include_bytes!("../samples/piano_C3_pp.wav"),
    ),
    (
        "piano_C3_pp_rr2.wav",
        include_bytes!("../samples/piano_C3_pp_rr2.wav"),
    ),
    (
        "piano_C4_f.wav",
        include_bytes!("../samples/piano_C4_f.wav"),
    ),
    (
        "piano_C4_f_rr2.wav",
        include_bytes!("../samples/piano_C4_f_rr2.wav"),
    ),
    (
        "piano_C4_mf.wav",
        include_bytes!("../samples/piano_C4_mf.wav"),
    ),
    (
        "piano_C4_mf_rr2.wav",
        include_bytes!("../samples/piano_C4_mf_rr2.wav"),
    ),
    (
        "piano_C4_pp.wav",
        include_bytes!("../samples/piano_C4_pp.wav"),
    ),
    (
        "piano_C4_pp_rr2.wav",
        include_bytes!("../samples/piano_C4_pp_rr2.wav"),
    ),
    (
        "piano_C5_f.wav",
        include_bytes!("../samples/piano_C5_f.wav"),
    ),
    (
        "piano_C5_f_rr2.wav",
        include_bytes!("../samples/piano_C5_f_rr2.wav"),
    ),
    (
        "piano_C5_mf.wav",
        include_bytes!("../samples/piano_C5_mf.wav"),
    ),
    (
        "piano_C5_mf_rr2.wav",
        include_bytes!("../samples/piano_C5_mf_rr2.wav"),
    ),
    (
        "piano_C5_pp.wav",
        include_bytes!("../samples/piano_C5_pp.wav"),
    ),
    (
        "piano_C5_pp_rr2.wav",
        include_bytes!("../samples/piano_C5_pp_rr2.wav"),
    ),
    (
        "piano_C6_f.wav",
        include_bytes!("../samples/piano_C6_f.wav"),
    ),
    (
        "piano_C6_f_rr2.wav",
        include_bytes!("../samples/piano_C6_f_rr2.wav"),
    ),
    (
        "piano_C6_mf.wav",
        include_bytes!("../samples/piano_C6_mf.wav"),
    ),
    (
        "piano_C6_mf_rr2.wav",
        include_bytes!("../samples/piano_C6_mf_rr2.wav"),
    ),
    (
        "piano_C6_pp.wav",
        include_bytes!("../samples/piano_C6_pp.wav"),
    ),
    (
        "piano_C6_pp_rr2.wav",
        include_bytes!("../samples/piano_C6_pp_rr2.wav"),
    ),
    (
        "piano_G2_f.wav",
        include_bytes!("../samples/piano_G2_f.wav"),
    ),
    (
        "piano_G2_f_rr2.wav",
        include_bytes!("../samples/piano_G2_f_rr2.wav"),
    ),
    (
        "piano_G2_mf.wav",
        include_bytes!("../samples/piano_G2_mf.wav"),
    ),
    (
        "piano_G2_mf_rr2.wav",
        include_bytes!("../samples/piano_G2_mf_rr2.wav"),
    ),
    (
        "piano_G2_pp.wav",
        include_bytes!("../samples/piano_G2_pp.wav"),
    ),
    (
        "piano_G3_f.wav",
        include_bytes!("../samples/piano_G3_f.wav"),
    ),
    (
        "piano_G3_f_rr2.wav",
        include_bytes!("../samples/piano_G3_f_rr2.wav"),
    ),
    (
        "piano_G3_mf.wav",
        include_bytes!("../samples/piano_G3_mf.wav"),
    ),
    (
        "piano_G3_mf_rr2.wav",
        include_bytes!("../samples/piano_G3_mf_rr2.wav"),
    ),
    (
        "piano_G3_pp.wav",
        include_bytes!("../samples/piano_G3_pp.wav"),
    ),
    (
        "piano_G3_pp_rr2.wav",
        include_bytes!("../samples/piano_G3_pp_rr2.wav"),
    ),
    (
        "piano_G4_f.wav",
        include_bytes!("../samples/piano_G4_f.wav"),
    ),
    (
        "piano_G4_f_rr2.wav",
        include_bytes!("../samples/piano_G4_f_rr2.wav"),
    ),
    (
        "piano_G4_mf.wav",
        include_bytes!("../samples/piano_G4_mf.wav"),
    ),
    (
        "piano_G4_mf_rr2.wav",
        include_bytes!("../samples/piano_G4_mf_rr2.wav"),
    ),
    (
        "piano_G4_pp.wav",
        include_bytes!("../samples/piano_G4_pp.wav"),
    ),
    (
        "piano_G4_pp_rr2.wav",
        include_bytes!("../samples/piano_G4_pp_rr2.wav"),
    ),
    (
        "piano_G5_f.wav",
        include_bytes!("../samples/piano_G5_f.wav"),
    ),
    (
        "piano_G5_f_rr2.wav",
        include_bytes!("../samples/piano_G5_f_rr2.wav"),
    ),
    (
        "piano_G5_mf.wav",
        include_bytes!("../samples/piano_G5_mf.wav"),
    ),
    (
        "piano_G5_mf_rr2.wav",
        include_bytes!("../samples/piano_G5_mf_rr2.wav"),
    ),
    (
        "piano_G5_pp.wav",
        include_bytes!("../samples/piano_G5_pp.wav"),
    ),
    (
        "piano_G5_pp_rr2.wav",
        include_bytes!("../samples/piano_G5_pp_rr2.wav"),
    ),
    (
        "violin_C5_f.wav",
        include_bytes!("../samples/violin_C5_f.wav"),
    ),
    (
        "violin_C5_p.wav",
        include_bytes!("../samples/violin_C5_p.wav"),
    ),
    (
        "violin_C6_f.wav",
        include_bytes!("../samples/violin_C6_f.wav"),
    ),
    (
        "violin_C6_p.wav",
        include_bytes!("../samples/violin_C6_p.wav"),
    ),
    (
        "violin_E4_f.wav",
        include_bytes!("../samples/violin_E4_f.wav"),
    ),
    (
        "violin_E4_p.wav",
        include_bytes!("../samples/violin_E4_p.wav"),
    ),
    (
        "violin_E6_f.wav",
        include_bytes!("../samples/violin_E6_f.wav"),
    ),
    (
        "violin_E6_p.wav",
        include_bytes!("../samples/violin_E6_p.wav"),
    ),
    (
        "violin_G3_f.wav",
        include_bytes!("../samples/violin_G3_f.wav"),
    ),
    (
        "violin_G3_p.wav",
        include_bytes!("../samples/violin_G3_p.wav"),
    ),
    (
        "violin_G5_f.wav",
        include_bytes!("../samples/violin_G5_f.wav"),
    ),
    (
        "violin_G5_p.wav",
        include_bytes!("../samples/violin_G5_p.wav"),
    ),
];

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    // Preserve the old low-level lookups while representing these cells
    // truthfully as aliases rather than embedding duplicate payload files.
    let name = match name {
        "piano_C2_pp_rr2.wav" => "piano_C2_pp.wav",
        "piano_G2_pp_rr2.wav" => "piano_G2_pp.wav",
        _ => name,
    };
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

    const EXPECTED_BYTES: usize = 9236760;

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
        assert_eq!(get("piano_C2_pp_rr2.wav"), get("piano_C2_pp.wav"));
        assert_eq!(get("piano_G2_pp_rr2.wav"), get("piano_G2_pp.wav"));
    }
}
