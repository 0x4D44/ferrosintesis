//! Embedded MIT-licensed MuseScore "MS Basic" instrument-onset samples for
//! ferrosintesis.
//!
//! Attack transients extracted from the MuseScore "MS Basic" soundfont (MIT;
//! FluidR3Mono lineage) for programs whose modeled onset benefits from a real one:
//! the GM 104 sitar (pluck + jawari buzz), GM 61 brass section, GM 75/76/77 pipes,
//! and GM 8 celesta (metal-bar bell strike). Each WAV is a
//! mono 16-bit 44.1 kHz onset; `ferrosintesis` crossfades it into the modeled sustain.
//! Consumers normally access this crate through `ferrosintesis`. Attribution
//! obligations (the MS Basic acknowledgement set) are in `NOTICE`; the GM 7
//! clavinet from the same soundfont ships separately in `ferrosintesis-samples-clavinet`.
//! Licence/provenance: see `NOTICE` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice so families can be added without a count constant.
static SAMPLES: &[(&str, &[u8])] = &[
    (
        "bottle_C6.flac",
        include_bytes!("../samples/bottle_C6.flac"),
    ),
    (
        "brasssection_F2.flac",
        include_bytes!("../samples/brasssection_F2.flac"),
    ),
    (
        "brasssection_C3.flac",
        include_bytes!("../samples/brasssection_C3.flac"),
    ),
    (
        "brasssection_F#3.flac",
        include_bytes!("../samples/brasssection_F#3.flac"),
    ),
    (
        "brasssection_A#3.flac",
        include_bytes!("../samples/brasssection_A#3.flac"),
    ),
    (
        "brasssection_C4.flac",
        include_bytes!("../samples/brasssection_C4.flac"),
    ),
    (
        "brasssection_F4.flac",
        include_bytes!("../samples/brasssection_F4.flac"),
    ),
    (
        "brasssection_A4.flac",
        include_bytes!("../samples/brasssection_A4.flac"),
    ),
    (
        "brasssection_C5.flac",
        include_bytes!("../samples/brasssection_C5.flac"),
    ),
    (
        "brasssection_F5.flac",
        include_bytes!("../samples/brasssection_F5.flac"),
    ),
    (
        "brasssection_C6.flac",
        include_bytes!("../samples/brasssection_C6.flac"),
    ),
    (
        "panflute_C4.flac",
        include_bytes!("../samples/panflute_C4.flac"),
    ),
    (
        "panflute_C5.flac",
        include_bytes!("../samples/panflute_C5.flac"),
    ),
    (
        "panflute_C6.flac",
        include_bytes!("../samples/panflute_C6.flac"),
    ),
    (
        "panflute_C7.flac",
        include_bytes!("../samples/panflute_C7.flac"),
    ),
    (
        "panflute_F#3.flac",
        include_bytes!("../samples/panflute_F#3.flac"),
    ),
    (
        "panflute_F#4.flac",
        include_bytes!("../samples/panflute_F#4.flac"),
    ),
    (
        "panflute_F#5.flac",
        include_bytes!("../samples/panflute_F#5.flac"),
    ),
    (
        "panflute_F#6.flac",
        include_bytes!("../samples/panflute_F#6.flac"),
    ),
    (
        "shakuhachi_C5.flac",
        include_bytes!("../samples/shakuhachi_C5.flac"),
    ),
    ("sitar_C4.flac", include_bytes!("../samples/sitar_C4.flac")),
    ("sitar_C5.flac", include_bytes!("../samples/sitar_C5.flac")),
    ("sitar_C6.flac", include_bytes!("../samples/sitar_C6.flac")),
    ("sitar_E3.flac", include_bytes!("../samples/sitar_E3.flac")),
    ("sitar_E4.flac", include_bytes!("../samples/sitar_E4.flac")),
    ("sitar_E5.flac", include_bytes!("../samples/sitar_E5.flac")),
    ("sitar_G3.flac", include_bytes!("../samples/sitar_G3.flac")),
    ("sitar_G6.flac", include_bytes!("../samples/sitar_G6.flac")),
    (
        "celesta_F#3.flac",
        include_bytes!("../samples/celesta_F#3.flac"),
    ),
    (
        "celesta_C4.flac",
        include_bytes!("../samples/celesta_C4.flac"),
    ),
    (
        "celesta_F#4.flac",
        include_bytes!("../samples/celesta_F#4.flac"),
    ),
    (
        "celesta_C5.flac",
        include_bytes!("../samples/celesta_C5.flac"),
    ),
    (
        "celesta_F#5.flac",
        include_bytes!("../samples/celesta_F#5.flac"),
    ),
    (
        "celesta_C6.flac",
        include_bytes!("../samples/celesta_C6.flac"),
    ),
    (
        "celesta_F#6.flac",
        include_bytes!("../samples/celesta_F#6.flac"),
    ),
    (
        "celesta_C7.flac",
        include_bytes!("../samples/celesta_C7.flac"),
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

        assert_eq!(embedded, packaged, "embedded list must match packaged WAVs");
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

    #[test]
    fn brass_section_inventory_is_the_reviewed_ten_zone_bank() {
        let names: Vec<&str> = SAMPLES
            .iter()
            .map(|(name, _)| *name)
            .filter(|name| name.starts_with("brasssection_"))
            .collect();
        assert_eq!(
            names,
            [
                "brasssection_F2.flac",
                "brasssection_C3.flac",
                "brasssection_F#3.flac",
                "brasssection_A#3.flac",
                "brasssection_C4.flac",
                "brasssection_F4.flac",
                "brasssection_A4.flac",
                "brasssection_C5.flac",
                "brasssection_F5.flac",
                "brasssection_C6.flac",
            ]
        );
    }
}
