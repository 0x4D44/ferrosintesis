//! Embedded CC0 1.0 instrument-onset samples for ferrosintesis.
//!
//! The second CC0 onset crate: the original `ferrosintesis-samples-orchestral` is
//! at the crates.io per-crate size cap, so newer CC0 families land here. Each
//! sample is a mono 16-bit 44.1 kHz attack transient stored as FLAC; `ferrosintesis` plays it as a note's
//! onset and crossfades into the modeled sustain. Consumers normally access this
//! crate through `ferrosintesis`, not directly. All samples are CC0 1.0 /
//! public-domain — no attribution required. The canonical packaged inventory
//! and source provenance are in `PROVENANCE.md`.
//! Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

/// Embedded (file-name, bytes) pairs. Names include the `.wav` suffix and are
/// case-sensitive. Kept as a slice (not a fixed-size array) so families can be
/// added without threading a count constant through the file.
static SAMPLES: &[(&str, &[u8])] = &[
    (
        "banjo_A#3.flac",
        include_bytes!("../samples/banjo_A#3.flac"),
    ),
    (
        "banjo_A#4.flac",
        include_bytes!("../samples/banjo_A#4.flac"),
    ),
    ("banjo_A3.flac", include_bytes!("../samples/banjo_A3.flac")),
    ("banjo_A4.flac", include_bytes!("../samples/banjo_A4.flac")),
    ("banjo_B3.flac", include_bytes!("../samples/banjo_B3.flac")),
    (
        "banjo_C#5.flac",
        include_bytes!("../samples/banjo_C#5.flac"),
    ),
    ("banjo_C4.flac", include_bytes!("../samples/banjo_C4.flac")),
    ("banjo_C5.flac", include_bytes!("../samples/banjo_C5.flac")),
    (
        "banjo_D#3.flac",
        include_bytes!("../samples/banjo_D#3.flac"),
    ),
    (
        "banjo_D#4.flac",
        include_bytes!("../samples/banjo_D#4.flac"),
    ),
    (
        "banjo_D#5.flac",
        include_bytes!("../samples/banjo_D#5.flac"),
    ),
    ("banjo_D4.flac", include_bytes!("../samples/banjo_D4.flac")),
    ("banjo_D5.flac", include_bytes!("../samples/banjo_D5.flac")),
    ("banjo_E4.flac", include_bytes!("../samples/banjo_E4.flac")),
    ("banjo_E5.flac", include_bytes!("../samples/banjo_E5.flac")),
    (
        "banjo_F#4.flac",
        include_bytes!("../samples/banjo_F#4.flac"),
    ),
    ("banjo_F3.flac", include_bytes!("../samples/banjo_F3.flac")),
    ("banjo_F4.flac", include_bytes!("../samples/banjo_F4.flac")),
    (
        "banjo_G#3.flac",
        include_bytes!("../samples/banjo_G#3.flac"),
    ),
    (
        "banjo_G#4.flac",
        include_bytes!("../samples/banjo_G#4.flac"),
    ),
    (
        "banjo_G#5.flac",
        include_bytes!("../samples/banjo_G#5.flac"),
    ),
    ("banjo_G3.flac", include_bytes!("../samples/banjo_G3.flac")),
    ("banjo_G4.flac", include_bytes!("../samples/banjo_G4.flac")),
    ("banjo_G5.flac", include_bytes!("../samples/banjo_G5.flac")),
    ("harp_A2.flac", include_bytes!("../samples/harp_A2.flac")),
    ("harp_A6.flac", include_bytes!("../samples/harp_A6.flac")),
    ("harp_B3.flac", include_bytes!("../samples/harp_B3.flac")),
    ("harp_C5.flac", include_bytes!("../samples/harp_C5.flac")),
    ("harp_D2.flac", include_bytes!("../samples/harp_D2.flac")),
    ("harp_D6.flac", include_bytes!("../samples/harp_D6.flac")),
    ("harp_E3.flac", include_bytes!("../samples/harp_E3.flac")),
    ("harp_F4.flac", include_bytes!("../samples/harp_F4.flac")),
    ("harp_F7.flac", include_bytes!("../samples/harp_F7.flac")),
    ("harp_G1.flac", include_bytes!("../samples/harp_G1.flac")),
    ("harp_G5.flac", include_bytes!("../samples/harp_G5.flac")),
    (
        "ocarina_C5.flac",
        include_bytes!("../samples/ocarina_C5.flac"),
    ),
    (
        "ocarina_E4.flac",
        include_bytes!("../samples/ocarina_E4.flac"),
    ),
    (
        "ocarina_G#4.flac",
        include_bytes!("../samples/ocarina_G#4.flac"),
    ),
    (
        "recorder_A#3.flac",
        include_bytes!("../samples/recorder_A#3.flac"),
    ),
    (
        "recorder_A#4.flac",
        include_bytes!("../samples/recorder_A#4.flac"),
    ),
    (
        "recorder_A#5.flac",
        include_bytes!("../samples/recorder_A#5.flac"),
    ),
    (
        "recorder_C6.flac",
        include_bytes!("../samples/recorder_C6.flac"),
    ),
    (
        "recorder_E4.flac",
        include_bytes!("../samples/recorder_E4.flac"),
    ),
    (
        "recorder_E5.flac",
        include_bytes!("../samples/recorder_E5.flac"),
    ),
    (
        "recorder_F3.flac",
        include_bytes!("../samples/recorder_F3.flac"),
    ),
    (
        "timpani_A#1.flac",
        include_bytes!("../samples/timpani_A#1.flac"),
    ),
    (
        "timpani_D3.flac",
        include_bytes!("../samples/timpani_D3.flac"),
    ),
    (
        "timpani_F2.flac",
        include_bytes!("../samples/timpani_F2.flac"),
    ),
    (
        "timpani_F3.flac",
        include_bytes!("../samples/timpani_F3.flac"),
    ),
    (
        "timpani_G#2.flac",
        include_bytes!("../samples/timpani_G#2.flac"),
    ),
    (
        "viola_A4_f.flac",
        include_bytes!("../samples/viola_A4_f.flac"),
    ),
    (
        "viola_A4_p.flac",
        include_bytes!("../samples/viola_A4_p.flac"),
    ),
    (
        "viola_B5_f.flac",
        include_bytes!("../samples/viola_B5_f.flac"),
    ),
    (
        "viola_B5_p.flac",
        include_bytes!("../samples/viola_B5_p.flac"),
    ),
    (
        "viola_C3_f.flac",
        include_bytes!("../samples/viola_C3_f.flac"),
    ),
    (
        "viola_C3_p.flac",
        include_bytes!("../samples/viola_C3_p.flac"),
    ),
    (
        "viola_D4_f.flac",
        include_bytes!("../samples/viola_D4_f.flac"),
    ),
    (
        "viola_D4_p.flac",
        include_bytes!("../samples/viola_D4_p.flac"),
    ),
    (
        "viola_D6_f.flac",
        include_bytes!("../samples/viola_D6_f.flac"),
    ),
    (
        "viola_D6_p.flac",
        include_bytes!("../samples/viola_D6_p.flac"),
    ),
    (
        "viola_E5_f.flac",
        include_bytes!("../samples/viola_E5_f.flac"),
    ),
    (
        "viola_E5_p.flac",
        include_bytes!("../samples/viola_E5_p.flac"),
    ),
    (
        "viola_G3_f.flac",
        include_bytes!("../samples/viola_G3_f.flac"),
    ),
    (
        "viola_G3_p.flac",
        include_bytes!("../samples/viola_G3_p.flac"),
    ),
    (
        "marimba_F1.flac",
        include_bytes!("../samples/marimba_F1.flac"),
    ),
    (
        "marimba_C2.flac",
        include_bytes!("../samples/marimba_C2.flac"),
    ),
    (
        "marimba_G2.flac",
        include_bytes!("../samples/marimba_G2.flac"),
    ),
    (
        "marimba_B2.flac",
        include_bytes!("../samples/marimba_B2.flac"),
    ),
    (
        "marimba_F3.flac",
        include_bytes!("../samples/marimba_F3.flac"),
    ),
    (
        "marimba_C4.flac",
        include_bytes!("../samples/marimba_C4.flac"),
    ),
    (
        "marimba_G4.flac",
        include_bytes!("../samples/marimba_G4.flac"),
    ),
    (
        "marimba_B4.flac",
        include_bytes!("../samples/marimba_B4.flac"),
    ),
    (
        "marimba_F5.flac",
        include_bytes!("../samples/marimba_F5.flac"),
    ),
    (
        "marimba_C6.flac",
        include_bytes!("../samples/marimba_C6.flac"),
    ),
    ("xylo_G3.flac", include_bytes!("../samples/xylo_G3.flac")),
    ("xylo_C4.flac", include_bytes!("../samples/xylo_C4.flac")),
    ("xylo_G4.flac", include_bytes!("../samples/xylo_G4.flac")),
    ("xylo_C5.flac", include_bytes!("../samples/xylo_C5.flac")),
    ("xylo_G5.flac", include_bytes!("../samples/xylo_G5.flac")),
    ("xylo_C6.flac", include_bytes!("../samples/xylo_C6.flac")),
    ("xylo_G6.flac", include_bytes!("../samples/xylo_G6.flac")),
    ("xylo_C7.flac", include_bytes!("../samples/xylo_C7.flac")),
    ("glock_C5.flac", include_bytes!("../samples/glock_C5.flac")),
    ("glock_G5.flac", include_bytes!("../samples/glock_G5.flac")),
    ("glock_G6.flac", include_bytes!("../samples/glock_G6.flac")),
    ("glock_C7.flac", include_bytes!("../samples/glock_C7.flac")),
    ("vibes_A2.flac", include_bytes!("../samples/vibes_A2.flac")),
    ("vibes_C3.flac", include_bytes!("../samples/vibes_C3.flac")),
    ("vibes_E3.flac", include_bytes!("../samples/vibes_E3.flac")),
    ("vibes_G3.flac", include_bytes!("../samples/vibes_G3.flac")),
    ("vibes_B3.flac", include_bytes!("../samples/vibes_B3.flac")),
    ("vibes_D4.flac", include_bytes!("../samples/vibes_D4.flac")),
    ("vibes_F4.flac", include_bytes!("../samples/vibes_F4.flac")),
    ("vibes_A4.flac", include_bytes!("../samples/vibes_A4.flac")),
    ("vibes_C5.flac", include_bytes!("../samples/vibes_C5.flac")),
    ("vibes_E5.flac", include_bytes!("../samples/vibes_E5.flac")),
    (
        "tubular_C4.flac",
        include_bytes!("../samples/tubular_C4.flac"),
    ),
    (
        "tubular_D4.flac",
        include_bytes!("../samples/tubular_D4.flac"),
    ),
    (
        "tubular_E4.flac",
        include_bytes!("../samples/tubular_E4.flac"),
    ),
    (
        "tubular_F4.flac",
        include_bytes!("../samples/tubular_F4.flac"),
    ),
    (
        "tubular_G4.flac",
        include_bytes!("../samples/tubular_G4.flac"),
    ),
    (
        "tubular_A4.flac",
        include_bytes!("../samples/tubular_A4.flac"),
    ),
    (
        "tubular_B4.flac",
        include_bytes!("../samples/tubular_B4.flac"),
    ),
    (
        "tubular_C5.flac",
        include_bytes!("../samples/tubular_C5.flac"),
    ),
    (
        "tubular_D5.flac",
        include_bytes!("../samples/tubular_D5.flac"),
    ),
    (
        "musicbox_E5.flac",
        include_bytes!("../samples/musicbox_E5.flac"),
    ),
    (
        "musicbox_A5.flac",
        include_bytes!("../samples/musicbox_A5.flac"),
    ),
    (
        "musicbox_B5.flac",
        include_bytes!("../samples/musicbox_B5.flac"),
    ),
    (
        "musicbox_C6.flac",
        include_bytes!("../samples/musicbox_C6.flac"),
    ),
    (
        "musicbox_D6.flac",
        include_bytes!("../samples/musicbox_D6.flac"),
    ),
    (
        "musicbox_E6.flac",
        include_bytes!("../samples/musicbox_E6.flac"),
    ),
    (
        "musicbox_F6.flac",
        include_bytes!("../samples/musicbox_F6.flac"),
    ),
    (
        "musicbox_G#6.flac",
        include_bytes!("../samples/musicbox_G#6.flac"),
    ),
    (
        "musicbox_A6.flac",
        include_bytes!("../samples/musicbox_A6.flac"),
    ),
    (
        "musicbox_B6.flac",
        include_bytes!("../samples/musicbox_B6.flac"),
    ),
    (
        "musicbox_C7.flac",
        include_bytes!("../samples/musicbox_C7.flac"),
    ),
    (
        "eastpick_E2.flac",
        include_bytes!("../samples/eastpick_E2.flac"),
    ),
    (
        "eastpick_B2.flac",
        include_bytes!("../samples/eastpick_B2.flac"),
    ),
    (
        "eastpick_E3.flac",
        include_bytes!("../samples/eastpick_E3.flac"),
    ),
    (
        "eastpick_A#3.flac",
        include_bytes!("../samples/eastpick_A#3.flac"),
    ),
    (
        "eastpick_E4.flac",
        include_bytes!("../samples/eastpick_E4.flac"),
    ),
    (
        "eastpick_A#4.flac",
        include_bytes!("../samples/eastpick_A#4.flac"),
    ),
    (
        "eastpick_F5.flac",
        include_bytes!("../samples/eastpick_F5.flac"),
    ),
    (
        "eastpick_B5.flac",
        include_bytes!("../samples/eastpick_B5.flac"),
    ),
    (
        "eastpluck_E2.flac",
        include_bytes!("../samples/eastpluck_E2.flac"),
    ),
    (
        "eastpluck_A#2.flac",
        include_bytes!("../samples/eastpluck_A#2.flac"),
    ),
    (
        "eastpluck_E3.flac",
        include_bytes!("../samples/eastpluck_E3.flac"),
    ),
    (
        "eastpluck_A#3.flac",
        include_bytes!("../samples/eastpluck_A#3.flac"),
    ),
    (
        "eastpluck_E4.flac",
        include_bytes!("../samples/eastpluck_E4.flac"),
    ),
    (
        "eastpluck_B4.flac",
        include_bytes!("../samples/eastpluck_B4.flac"),
    ),
    (
        "eastpluck_F5.flac",
        include_bytes!("../samples/eastpluck_F5.flac"),
    ),
    (
        "eastpluck_B5.flac",
        include_bytes!("../samples/eastpluck_B5.flac"),
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
