//! Embedded CC0 attack-transient samples for orchestral and drum voices.
//!
//! Consumers normally access this crate through `ferrosintesis`.

#![forbid(unsafe_code)]

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 139;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "bassoon_A#0_f.wav",
        include_bytes!("../samples/bassoon_A#0_f.wav"),
    ),
    (
        "bassoon_A#0_p.wav",
        include_bytes!("../samples/bassoon_A#0_p.wav"),
    ),
    (
        "bassoon_C2_f.wav",
        include_bytes!("../samples/bassoon_C2_f.wav"),
    ),
    (
        "bassoon_C2_p.wav",
        include_bytes!("../samples/bassoon_C2_p.wav"),
    ),
    (
        "bassoon_C4_f.wav",
        include_bytes!("../samples/bassoon_C4_f.wav"),
    ),
    (
        "bassoon_C4_p.wav",
        include_bytes!("../samples/bassoon_C4_p.wav"),
    ),
    (
        "bassoon_D#3_f.wav",
        include_bytes!("../samples/bassoon_D#3_f.wav"),
    ),
    (
        "bassoon_D#3_p.wav",
        include_bytes!("../samples/bassoon_D#3_p.wav"),
    ),
    (
        "bassoon_F1_f.wav",
        include_bytes!("../samples/bassoon_F1_f.wav"),
    ),
    (
        "bassoon_F1_p.wav",
        include_bytes!("../samples/bassoon_F1_p.wav"),
    ),
    (
        "bassoon_G2_f.wav",
        include_bytes!("../samples/bassoon_G2_f.wav"),
    ),
    (
        "bassoon_G2_p.wav",
        include_bytes!("../samples/bassoon_G2_p.wav"),
    ),
    (
        "celens_A2_f.wav",
        include_bytes!("../samples/celens_A2_f.wav"),
    ),
    (
        "celens_A2_p.wav",
        include_bytes!("../samples/celens_A2_p.wav"),
    ),
    (
        "celens_B3_f.wav",
        include_bytes!("../samples/celens_B3_f.wav"),
    ),
    (
        "celens_B3_p.wav",
        include_bytes!("../samples/celens_B3_p.wav"),
    ),
    (
        "celens_C1_f.wav",
        include_bytes!("../samples/celens_C1_f.wav"),
    ),
    (
        "celens_C1_p.wav",
        include_bytes!("../samples/celens_C1_p.wav"),
    ),
    (
        "celens_D2_f.wav",
        include_bytes!("../samples/celens_D2_f.wav"),
    ),
    (
        "celens_D2_p.wav",
        include_bytes!("../samples/celens_D2_p.wav"),
    ),
    (
        "celens_E3_f.wav",
        include_bytes!("../samples/celens_E3_f.wav"),
    ),
    (
        "celens_E3_p.wav",
        include_bytes!("../samples/celens_E3_p.wav"),
    ),
    (
        "celens_G1_f.wav",
        include_bytes!("../samples/celens_G1_f.wav"),
    ),
    (
        "celens_G1_p.wav",
        include_bytes!("../samples/celens_G1_p.wav"),
    ),
    (
        "clarinet_A#2_f.wav",
        include_bytes!("../samples/clarinet_A#2_f.wav"),
    ),
    (
        "clarinet_A#2_p.wav",
        include_bytes!("../samples/clarinet_A#2_p.wav"),
    ),
    (
        "clarinet_A#3_f.wav",
        include_bytes!("../samples/clarinet_A#3_f.wav"),
    ),
    (
        "clarinet_A#3_p.wav",
        include_bytes!("../samples/clarinet_A#3_p.wav"),
    ),
    (
        "clarinet_D3_f.wav",
        include_bytes!("../samples/clarinet_D3_f.wav"),
    ),
    (
        "clarinet_D3_p.wav",
        include_bytes!("../samples/clarinet_D3_p.wav"),
    ),
    (
        "clarinet_D4_f.wav",
        include_bytes!("../samples/clarinet_D4_f.wav"),
    ),
    (
        "clarinet_D4_p.wav",
        include_bytes!("../samples/clarinet_D4_p.wav"),
    ),
    (
        "clarinet_F3_f.wav",
        include_bytes!("../samples/clarinet_F3_f.wav"),
    ),
    (
        "clarinet_F3_p.wav",
        include_bytes!("../samples/clarinet_F3_p.wav"),
    ),
    (
        "clarinet_F4_f.wav",
        include_bytes!("../samples/clarinet_F4_f.wav"),
    ),
    (
        "clarinet_F4_p.wav",
        include_bytes!("../samples/clarinet_F4_p.wav"),
    ),
    (
        "drum_crash1_ff_rr1.wav",
        include_bytes!("../samples/drum_crash1_ff_rr1.wav"),
    ),
    (
        "drum_crash1_ff_rr2.wav",
        include_bytes!("../samples/drum_crash1_ff_rr2.wav"),
    ),
    (
        "drum_kick_v3_rr1.wav",
        include_bytes!("../samples/drum_kick_v3_rr1.wav"),
    ),
    (
        "drum_kick_v3_rr2.wav",
        include_bytes!("../samples/drum_kick_v3_rr2.wav"),
    ),
    (
        "drum_snare2_v5_rr1.wav",
        include_bytes!("../samples/drum_snare2_v5_rr1.wav"),
    ),
    (
        "drum_snare2_v5_rr2.wav",
        include_bytes!("../samples/drum_snare2_v5_rr2.wav"),
    ),
    (
        "drum_sus_cymb1_mp_rr1.wav",
        include_bytes!("../samples/drum_sus_cymb1_mp_rr1.wav"),
    ),
    (
        "drum_sus_cymb1_mp_rr2.wav",
        include_bytes!("../samples/drum_sus_cymb1_mp_rr2.wav"),
    ),
    (
        "horn_A#1_f.wav",
        include_bytes!("../samples/horn_A#1_f.wav"),
    ),
    (
        "horn_A#1_p.wav",
        include_bytes!("../samples/horn_A#1_p.wav"),
    ),
    ("horn_A2_f.wav", include_bytes!("../samples/horn_A2_f.wav")),
    ("horn_A2_p.wav", include_bytes!("../samples/horn_A2_p.wav")),
    ("horn_C3_f.wav", include_bytes!("../samples/horn_C3_f.wav")),
    ("horn_C3_p.wav", include_bytes!("../samples/horn_C3_p.wav")),
    ("horn_D2_f.wav", include_bytes!("../samples/horn_D2_f.wav")),
    ("horn_D2_p.wav", include_bytes!("../samples/horn_D2_p.wav")),
    ("horn_D4_f.wav", include_bytes!("../samples/horn_D4_f.wav")),
    ("horn_D4_p.wav", include_bytes!("../samples/horn_D4_p.wav")),
    ("horn_F2_f.wav", include_bytes!("../samples/horn_F2_f.wav")),
    ("horn_F2_p.wav", include_bytes!("../samples/horn_F2_p.wav")),
    (
        "mutetpt_A#2_f.wav",
        include_bytes!("../samples/mutetpt_A#2_f.wav"),
    ),
    (
        "mutetpt_A#2_p.wav",
        include_bytes!("../samples/mutetpt_A#2_p.wav"),
    ),
    (
        "mutetpt_A4_f.wav",
        include_bytes!("../samples/mutetpt_A4_f.wav"),
    ),
    (
        "mutetpt_A4_p.wav",
        include_bytes!("../samples/mutetpt_A4_p.wav"),
    ),
    (
        "mutetpt_D3_f.wav",
        include_bytes!("../samples/mutetpt_D3_f.wav"),
    ),
    (
        "mutetpt_D3_p.wav",
        include_bytes!("../samples/mutetpt_D3_p.wav"),
    ),
    (
        "mutetpt_D4_f.wav",
        include_bytes!("../samples/mutetpt_D4_f.wav"),
    ),
    (
        "mutetpt_D4_p.wav",
        include_bytes!("../samples/mutetpt_D4_p.wav"),
    ),
    (
        "mutetpt_G3_f.wav",
        include_bytes!("../samples/mutetpt_G3_f.wav"),
    ),
    (
        "mutetpt_G3_p.wav",
        include_bytes!("../samples/mutetpt_G3_p.wav"),
    ),
    ("nylon_A#3.wav", include_bytes!("../samples/nylon_A#3.wav")),
    ("nylon_A#4.wav", include_bytes!("../samples/nylon_A#4.wav")),
    ("nylon_B2.wav", include_bytes!("../samples/nylon_B2.wav")),
    ("nylon_E2.wav", include_bytes!("../samples/nylon_E2.wav")),
    ("nylon_E3.wav", include_bytes!("../samples/nylon_E3.wav")),
    ("nylon_E4.wav", include_bytes!("../samples/nylon_E4.wav")),
    ("nylon_E5.wav", include_bytes!("../samples/nylon_E5.wav")),
    (
        "oboe_A#3_f.wav",
        include_bytes!("../samples/oboe_A#3_f.wav"),
    ),
    (
        "oboe_A#3_p.wav",
        include_bytes!("../samples/oboe_A#3_p.wav"),
    ),
    (
        "oboe_A#4_f.wav",
        include_bytes!("../samples/oboe_A#4_f.wav"),
    ),
    (
        "oboe_A#4_p.wav",
        include_bytes!("../samples/oboe_A#4_p.wav"),
    ),
    ("oboe_D3_f.wav", include_bytes!("../samples/oboe_D3_f.wav")),
    ("oboe_D3_p.wav", include_bytes!("../samples/oboe_D3_p.wav")),
    ("oboe_D4_f.wav", include_bytes!("../samples/oboe_D4_f.wav")),
    ("oboe_D4_p.wav", include_bytes!("../samples/oboe_D4_p.wav")),
    ("oboe_F3_f.wav", include_bytes!("../samples/oboe_F3_f.wav")),
    ("oboe_F3_p.wav", include_bytes!("../samples/oboe_F3_p.wav")),
    ("oboe_F4_f.wav", include_bytes!("../samples/oboe_F4_f.wav")),
    ("oboe_F4_p.wav", include_bytes!("../samples/oboe_F4_p.wav")),
    ("steel_A#2.wav", include_bytes!("../samples/steel_A#2.wav")),
    ("steel_A#3.wav", include_bytes!("../samples/steel_A#3.wav")),
    ("steel_B4.wav", include_bytes!("../samples/steel_B4.wav")),
    ("steel_B5.wav", include_bytes!("../samples/steel_B5.wav")),
    ("steel_E2.wav", include_bytes!("../samples/steel_E2.wav")),
    ("steel_E3.wav", include_bytes!("../samples/steel_E3.wav")),
    ("steel_E4.wav", include_bytes!("../samples/steel_E4.wav")),
    ("steel_F5.wav", include_bytes!("../samples/steel_F5.wav")),
    (
        "trombone_A#1_f.wav",
        include_bytes!("../samples/trombone_A#1_f.wav"),
    ),
    (
        "trombone_A#1_p.wav",
        include_bytes!("../samples/trombone_A#1_p.wav"),
    ),
    (
        "trombone_C3_f.wav",
        include_bytes!("../samples/trombone_C3_f.wav"),
    ),
    (
        "trombone_C3_p.wav",
        include_bytes!("../samples/trombone_C3_p.wav"),
    ),
    (
        "trombone_D2_f.wav",
        include_bytes!("../samples/trombone_D2_f.wav"),
    ),
    (
        "trombone_D2_p.wav",
        include_bytes!("../samples/trombone_D2_p.wav"),
    ),
    (
        "trombone_F1_f.wav",
        include_bytes!("../samples/trombone_F1_f.wav"),
    ),
    (
        "trombone_F1_p.wav",
        include_bytes!("../samples/trombone_F1_p.wav"),
    ),
    (
        "trombone_F2_f.wav",
        include_bytes!("../samples/trombone_F2_f.wav"),
    ),
    (
        "trombone_F2_p.wav",
        include_bytes!("../samples/trombone_F2_p.wav"),
    ),
    (
        "trombone_F3_f.wav",
        include_bytes!("../samples/trombone_F3_f.wav"),
    ),
    (
        "trombone_F3_p.wav",
        include_bytes!("../samples/trombone_F3_p.wav"),
    ),
    (
        "trumpet_A4_f.wav",
        include_bytes!("../samples/trumpet_A4_f.wav"),
    ),
    (
        "trumpet_A4_p.wav",
        include_bytes!("../samples/trumpet_A4_p.wav"),
    ),
    (
        "trumpet_C3_f.wav",
        include_bytes!("../samples/trumpet_C3_f.wav"),
    ),
    (
        "trumpet_C3_p.wav",
        include_bytes!("../samples/trumpet_C3_p.wav"),
    ),
    (
        "trumpet_D4_f.wav",
        include_bytes!("../samples/trumpet_D4_f.wav"),
    ),
    (
        "trumpet_D4_p.wav",
        include_bytes!("../samples/trumpet_D4_p.wav"),
    ),
    (
        "trumpet_F2_f.wav",
        include_bytes!("../samples/trumpet_F2_f.wav"),
    ),
    (
        "trumpet_F2_p.wav",
        include_bytes!("../samples/trumpet_F2_p.wav"),
    ),
    (
        "trumpet_G3_f.wav",
        include_bytes!("../samples/trumpet_G3_f.wav"),
    ),
    (
        "trumpet_G3_p.wav",
        include_bytes!("../samples/trumpet_G3_p.wav"),
    ),
    (
        "tuba_A#0_f.wav",
        include_bytes!("../samples/tuba_A#0_f.wav"),
    ),
    (
        "tuba_A#0_p.wav",
        include_bytes!("../samples/tuba_A#0_p.wav"),
    ),
    (
        "tuba_A#1_f.wav",
        include_bytes!("../samples/tuba_A#1_f.wav"),
    ),
    (
        "tuba_A#1_p.wav",
        include_bytes!("../samples/tuba_A#1_p.wav"),
    ),
    (
        "tuba_A#2_f.wav",
        include_bytes!("../samples/tuba_A#2_f.wav"),
    ),
    (
        "tuba_A#2_p.wav",
        include_bytes!("../samples/tuba_A#2_p.wav"),
    ),
    (
        "tuba_D#1_f.wav",
        include_bytes!("../samples/tuba_D#1_f.wav"),
    ),
    (
        "tuba_D#1_p.wav",
        include_bytes!("../samples/tuba_D#1_p.wav"),
    ),
    ("tuba_D2_f.wav", include_bytes!("../samples/tuba_D2_f.wav")),
    ("tuba_D2_p.wav", include_bytes!("../samples/tuba_D2_p.wav")),
    ("tuba_F2_f.wav", include_bytes!("../samples/tuba_F2_f.wav")),
    ("tuba_F2_p.wav", include_bytes!("../samples/tuba_F2_p.wav")),
    (
        "vlnens_A3_f.wav",
        include_bytes!("../samples/vlnens_A3_f.wav"),
    ),
    (
        "vlnens_A3_p.wav",
        include_bytes!("../samples/vlnens_A3_p.wav"),
    ),
    (
        "vlnens_B4_f.wav",
        include_bytes!("../samples/vlnens_B4_f.wav"),
    ),
    (
        "vlnens_B4_p.wav",
        include_bytes!("../samples/vlnens_B4_p.wav"),
    ),
    (
        "vlnens_D3_f.wav",
        include_bytes!("../samples/vlnens_D3_f.wav"),
    ),
    (
        "vlnens_D3_p.wav",
        include_bytes!("../samples/vlnens_D3_p.wav"),
    ),
    (
        "vlnens_D5_f.wav",
        include_bytes!("../samples/vlnens_D5_f.wav"),
    ),
    (
        "vlnens_D5_p.wav",
        include_bytes!("../samples/vlnens_D5_p.wav"),
    ),
    (
        "vlnens_E4_f.wav",
        include_bytes!("../samples/vlnens_E4_f.wav"),
    ),
    (
        "vlnens_E4_p.wav",
        include_bytes!("../samples/vlnens_E4_p.wav"),
    ),
    (
        "vlnens_G2_f.wav",
        include_bytes!("../samples/vlnens_G2_f.wav"),
    ),
    (
        "vlnens_G2_p.wav",
        include_bytes!("../samples/vlnens_G2_p.wav"),
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

    const EXPECTED_BYTES: usize = 7931912;

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
    }
}
