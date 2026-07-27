//! Embedded MIT-licensed MuseScore "MS Basic" instrument-onset samples for
//! ferrosintesis.
//!
//! Attack transients extracted from the MuseScore "MS Basic" soundfont (MIT;
//! FluidR3Mono lineage) for programs whose modeled onset benefits from a real one:
//! the GM 104 sitar (pluck + jawari buzz), the GM 75/76/77 pipes, and the GM 8 celesta
//! (metal-bar bell strike). Each WAV is a
//! mono 16-bit 44.1 kHz onset; `ferrosintesis` crossfades it into the modeled sustain.
//! Consumers normally access this crate through `ferrosintesis`. Attribution
//! obligations (the MS Basic acknowledgement set) are in `NOTICE`; the GM 7
//! clavinet from the same soundfont ships separately in `ferrosintesis-samples-clavinet`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice so families can be added without a count constant.
static SAMPLES: &[(&str, &[u8])] = &[
    ("bottle_C6.wav", include_bytes!("../samples/bottle_C6.wav")),
    (
        "panflute_C4.wav",
        include_bytes!("../samples/panflute_C4.wav"),
    ),
    (
        "panflute_C5.wav",
        include_bytes!("../samples/panflute_C5.wav"),
    ),
    (
        "panflute_C6.wav",
        include_bytes!("../samples/panflute_C6.wav"),
    ),
    (
        "panflute_C7.wav",
        include_bytes!("../samples/panflute_C7.wav"),
    ),
    (
        "panflute_F#3.wav",
        include_bytes!("../samples/panflute_F#3.wav"),
    ),
    (
        "panflute_F#4.wav",
        include_bytes!("../samples/panflute_F#4.wav"),
    ),
    (
        "panflute_F#5.wav",
        include_bytes!("../samples/panflute_F#5.wav"),
    ),
    (
        "panflute_F#6.wav",
        include_bytes!("../samples/panflute_F#6.wav"),
    ),
    (
        "shakuhachi_C5.wav",
        include_bytes!("../samples/shakuhachi_C5.wav"),
    ),
    ("sitar_C4.wav", include_bytes!("../samples/sitar_C4.wav")),
    ("sitar_C5.wav", include_bytes!("../samples/sitar_C5.wav")),
    ("sitar_C6.wav", include_bytes!("../samples/sitar_C6.wav")),
    ("sitar_E3.wav", include_bytes!("../samples/sitar_E3.wav")),
    ("sitar_E4.wav", include_bytes!("../samples/sitar_E4.wav")),
    ("sitar_E5.wav", include_bytes!("../samples/sitar_E5.wav")),
    ("sitar_G3.wav", include_bytes!("../samples/sitar_G3.wav")),
    ("sitar_G6.wav", include_bytes!("../samples/sitar_G6.wav")),
    (
        "celesta_F#3.wav",
        include_bytes!("../samples/celesta_F#3.wav"),
    ),
    (
        "celesta_C4.wav",
        include_bytes!("../samples/celesta_C4.wav"),
    ),
    (
        "celesta_F#4.wav",
        include_bytes!("../samples/celesta_F#4.wav"),
    ),
    (
        "celesta_C5.wav",
        include_bytes!("../samples/celesta_C5.wav"),
    ),
    (
        "celesta_F#5.wav",
        include_bytes!("../samples/celesta_F#5.wav"),
    ),
    (
        "celesta_C6.wav",
        include_bytes!("../samples/celesta_C6.wav"),
    ),
    (
        "celesta_F#6.wav",
        include_bytes!("../samples/celesta_F#6.wav"),
    ),
    (
        "celesta_C7.wav",
        include_bytes!("../samples/celesta_C7.wav"),
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
