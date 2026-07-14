//! Embedded CC0 sampled-cymbal drum-kit bank for ferrosintesis.
//!
//! Mono 16-bit 44.1 kHz WAVs trimmed from two CC0 1.0 sources by
//! `tools/ferrosintesis-samples/prepare_drumkit.py`: Virtuosity Drums
//! (`mid` mic set -- ride bow/bell, crash, sizzle crash, hi-hat
//! closed/open/pedal/splash) and Karoryfer Big Rusty Drums (18" china).
//! See `PROVENANCE.md` for the pinned revisions, license text, and the
//! full articulation inventory.
//!
//! Stage A ships the assets and accessors only; the synth wires them up
//! in a later stage. Consumers normally access this crate through
//! `ferrosintesis`.

#![forbid(unsafe_code)]

use std::sync::OnceLock;

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 109;

/// Sample rate of every embedded WAV, in hertz.
pub const SAMPLE_RATE_HZ: u32 = 44_100;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
    (
        "china_vl1_rr1.wav",
        include_bytes!("../samples/china_vl1_rr1.wav"),
    ),
    (
        "china_vl1_rr2.wav",
        include_bytes!("../samples/china_vl1_rr2.wav"),
    ),
    (
        "china_vl1_rr3.wav",
        include_bytes!("../samples/china_vl1_rr3.wav"),
    ),
    (
        "china_vl1_rr4.wav",
        include_bytes!("../samples/china_vl1_rr4.wav"),
    ),
    (
        "china_vl2_rr1.wav",
        include_bytes!("../samples/china_vl2_rr1.wav"),
    ),
    (
        "china_vl2_rr2.wav",
        include_bytes!("../samples/china_vl2_rr2.wav"),
    ),
    (
        "china_vl2_rr3.wav",
        include_bytes!("../samples/china_vl2_rr3.wav"),
    ),
    (
        "china_vl2_rr4.wav",
        include_bytes!("../samples/china_vl2_rr4.wav"),
    ),
    (
        "china_vl3_rr1.wav",
        include_bytes!("../samples/china_vl3_rr1.wav"),
    ),
    (
        "china_vl3_rr2.wav",
        include_bytes!("../samples/china_vl3_rr2.wav"),
    ),
    (
        "china_vl3_rr3.wav",
        include_bytes!("../samples/china_vl3_rr3.wav"),
    ),
    (
        "china_vl3_rr4.wav",
        include_bytes!("../samples/china_vl3_rr4.wav"),
    ),
    (
        "china_vl4_rr1.wav",
        include_bytes!("../samples/china_vl4_rr1.wav"),
    ),
    (
        "china_vl4_rr2.wav",
        include_bytes!("../samples/china_vl4_rr2.wav"),
    ),
    (
        "china_vl4_rr3.wav",
        include_bytes!("../samples/china_vl4_rr3.wav"),
    ),
    (
        "china_vl4_rr4.wav",
        include_bytes!("../samples/china_vl4_rr4.wav"),
    ),
    (
        "china_vl5_rr1.wav",
        include_bytes!("../samples/china_vl5_rr1.wav"),
    ),
    (
        "china_vl5_rr2.wav",
        include_bytes!("../samples/china_vl5_rr2.wav"),
    ),
    (
        "china_vl5_rr3.wav",
        include_bytes!("../samples/china_vl5_rr3.wav"),
    ),
    (
        "china_vl5_rr4.wav",
        include_bytes!("../samples/china_vl5_rr4.wav"),
    ),
    (
        "crash_vl1_rr1.wav",
        include_bytes!("../samples/crash_vl1_rr1.wav"),
    ),
    (
        "crash_vl1_rr2.wav",
        include_bytes!("../samples/crash_vl1_rr2.wav"),
    ),
    (
        "crash_vl1_rr3.wav",
        include_bytes!("../samples/crash_vl1_rr3.wav"),
    ),
    (
        "crash_vl1_rr4.wav",
        include_bytes!("../samples/crash_vl1_rr4.wav"),
    ),
    (
        "crash_vl2_rr1.wav",
        include_bytes!("../samples/crash_vl2_rr1.wav"),
    ),
    (
        "crash_vl2_rr2.wav",
        include_bytes!("../samples/crash_vl2_rr2.wav"),
    ),
    (
        "crash_vl2_rr3.wav",
        include_bytes!("../samples/crash_vl2_rr3.wav"),
    ),
    (
        "crash_vl2_rr4.wav",
        include_bytes!("../samples/crash_vl2_rr4.wav"),
    ),
    (
        "crash_vl3_rr1.wav",
        include_bytes!("../samples/crash_vl3_rr1.wav"),
    ),
    (
        "crash_vl3_rr2.wav",
        include_bytes!("../samples/crash_vl3_rr2.wav"),
    ),
    (
        "crash_vl3_rr3.wav",
        include_bytes!("../samples/crash_vl3_rr3.wav"),
    ),
    (
        "crash_vl3_rr4.wav",
        include_bytes!("../samples/crash_vl3_rr4.wav"),
    ),
    (
        "hhc_vl1_rr1.wav",
        include_bytes!("../samples/hhc_vl1_rr1.wav"),
    ),
    (
        "hhc_vl1_rr2.wav",
        include_bytes!("../samples/hhc_vl1_rr2.wav"),
    ),
    (
        "hhc_vl1_rr3.wav",
        include_bytes!("../samples/hhc_vl1_rr3.wav"),
    ),
    (
        "hhc_vl1_rr4.wav",
        include_bytes!("../samples/hhc_vl1_rr4.wav"),
    ),
    (
        "hhc_vl2_rr1.wav",
        include_bytes!("../samples/hhc_vl2_rr1.wav"),
    ),
    (
        "hhc_vl2_rr2.wav",
        include_bytes!("../samples/hhc_vl2_rr2.wav"),
    ),
    (
        "hhc_vl2_rr3.wav",
        include_bytes!("../samples/hhc_vl2_rr3.wav"),
    ),
    (
        "hhc_vl2_rr4.wav",
        include_bytes!("../samples/hhc_vl2_rr4.wav"),
    ),
    (
        "hhc_vl3_rr1.wav",
        include_bytes!("../samples/hhc_vl3_rr1.wav"),
    ),
    (
        "hhc_vl3_rr2.wav",
        include_bytes!("../samples/hhc_vl3_rr2.wav"),
    ),
    (
        "hhc_vl3_rr3.wav",
        include_bytes!("../samples/hhc_vl3_rr3.wav"),
    ),
    (
        "hhc_vl3_rr4.wav",
        include_bytes!("../samples/hhc_vl3_rr4.wav"),
    ),
    (
        "hhc_vl4_rr1.wav",
        include_bytes!("../samples/hhc_vl4_rr1.wav"),
    ),
    (
        "hhc_vl4_rr2.wav",
        include_bytes!("../samples/hhc_vl4_rr2.wav"),
    ),
    (
        "hhc_vl4_rr3.wav",
        include_bytes!("../samples/hhc_vl4_rr3.wav"),
    ),
    (
        "hhc_vl4_rr4.wav",
        include_bytes!("../samples/hhc_vl4_rr4.wav"),
    ),
    (
        "hho_vl1_rr1.wav",
        include_bytes!("../samples/hho_vl1_rr1.wav"),
    ),
    (
        "hho_vl1_rr2.wav",
        include_bytes!("../samples/hho_vl1_rr2.wav"),
    ),
    (
        "hho_vl1_rr3.wav",
        include_bytes!("../samples/hho_vl1_rr3.wav"),
    ),
    (
        "hho_vl2_rr1.wav",
        include_bytes!("../samples/hho_vl2_rr1.wav"),
    ),
    (
        "hho_vl2_rr2.wav",
        include_bytes!("../samples/hho_vl2_rr2.wav"),
    ),
    (
        "hho_vl2_rr3.wav",
        include_bytes!("../samples/hho_vl2_rr3.wav"),
    ),
    (
        "hho_vl3_rr1.wav",
        include_bytes!("../samples/hho_vl3_rr1.wav"),
    ),
    (
        "hho_vl3_rr2.wav",
        include_bytes!("../samples/hho_vl3_rr2.wav"),
    ),
    (
        "hho_vl3_rr3.wav",
        include_bytes!("../samples/hho_vl3_rr3.wav"),
    ),
    (
        "hho_vl4_rr1.wav",
        include_bytes!("../samples/hho_vl4_rr1.wav"),
    ),
    (
        "hho_vl4_rr2.wav",
        include_bytes!("../samples/hho_vl4_rr2.wav"),
    ),
    (
        "hho_vl4_rr3.wav",
        include_bytes!("../samples/hho_vl4_rr3.wav"),
    ),
    (
        "hhp_vl1_rr1.wav",
        include_bytes!("../samples/hhp_vl1_rr1.wav"),
    ),
    (
        "hhp_vl1_rr2.wav",
        include_bytes!("../samples/hhp_vl1_rr2.wav"),
    ),
    (
        "hhp_vl1_rr3.wav",
        include_bytes!("../samples/hhp_vl1_rr3.wav"),
    ),
    (
        "hhp_vl1_rr4.wav",
        include_bytes!("../samples/hhp_vl1_rr4.wav"),
    ),
    (
        "hhp_vl2_rr1.wav",
        include_bytes!("../samples/hhp_vl2_rr1.wav"),
    ),
    (
        "hhp_vl2_rr2.wav",
        include_bytes!("../samples/hhp_vl2_rr2.wav"),
    ),
    (
        "hhp_vl2_rr3.wav",
        include_bytes!("../samples/hhp_vl2_rr3.wav"),
    ),
    (
        "hhp_vl2_rr4.wav",
        include_bytes!("../samples/hhp_vl2_rr4.wav"),
    ),
    (
        "hhp_vl3_rr1.wav",
        include_bytes!("../samples/hhp_vl3_rr1.wav"),
    ),
    (
        "hhp_vl3_rr2.wav",
        include_bytes!("../samples/hhp_vl3_rr2.wav"),
    ),
    (
        "hhp_vl3_rr3.wav",
        include_bytes!("../samples/hhp_vl3_rr3.wav"),
    ),
    (
        "hhp_vl3_rr4.wav",
        include_bytes!("../samples/hhp_vl3_rr4.wav"),
    ),
    (
        "ride_vl1_rr1.wav",
        include_bytes!("../samples/ride_vl1_rr1.wav"),
    ),
    (
        "ride_vl1_rr2.wav",
        include_bytes!("../samples/ride_vl1_rr2.wav"),
    ),
    (
        "ride_vl1_rr3.wav",
        include_bytes!("../samples/ride_vl1_rr3.wav"),
    ),
    (
        "ride_vl1_rr4.wav",
        include_bytes!("../samples/ride_vl1_rr4.wav"),
    ),
    (
        "ride_vl2_rr1.wav",
        include_bytes!("../samples/ride_vl2_rr1.wav"),
    ),
    (
        "ride_vl2_rr2.wav",
        include_bytes!("../samples/ride_vl2_rr2.wav"),
    ),
    (
        "ride_vl2_rr3.wav",
        include_bytes!("../samples/ride_vl2_rr3.wav"),
    ),
    (
        "ride_vl2_rr4.wav",
        include_bytes!("../samples/ride_vl2_rr4.wav"),
    ),
    (
        "ride_vl3_rr1.wav",
        include_bytes!("../samples/ride_vl3_rr1.wav"),
    ),
    (
        "ride_vl3_rr2.wav",
        include_bytes!("../samples/ride_vl3_rr2.wav"),
    ),
    (
        "ride_vl3_rr3.wav",
        include_bytes!("../samples/ride_vl3_rr3.wav"),
    ),
    (
        "ride_vl3_rr4.wav",
        include_bytes!("../samples/ride_vl3_rr4.wav"),
    ),
    (
        "ridebell_vl1_rr1.wav",
        include_bytes!("../samples/ridebell_vl1_rr1.wav"),
    ),
    (
        "ridebell_vl1_rr2.wav",
        include_bytes!("../samples/ridebell_vl1_rr2.wav"),
    ),
    (
        "ridebell_vl1_rr3.wav",
        include_bytes!("../samples/ridebell_vl1_rr3.wav"),
    ),
    (
        "ridebell_vl2_rr1.wav",
        include_bytes!("../samples/ridebell_vl2_rr1.wav"),
    ),
    (
        "ridebell_vl2_rr2.wav",
        include_bytes!("../samples/ridebell_vl2_rr2.wav"),
    ),
    (
        "ridebell_vl2_rr3.wav",
        include_bytes!("../samples/ridebell_vl2_rr3.wav"),
    ),
    (
        "ridebell_vl3_rr1.wav",
        include_bytes!("../samples/ridebell_vl3_rr1.wav"),
    ),
    (
        "ridebell_vl3_rr2.wav",
        include_bytes!("../samples/ridebell_vl3_rr2.wav"),
    ),
    (
        "ridebell_vl3_rr3.wav",
        include_bytes!("../samples/ridebell_vl3_rr3.wav"),
    ),
    (
        "sizzle_vl1_rr1.wav",
        include_bytes!("../samples/sizzle_vl1_rr1.wav"),
    ),
    (
        "sizzle_vl1_rr2.wav",
        include_bytes!("../samples/sizzle_vl1_rr2.wav"),
    ),
    (
        "sizzle_vl1_rr3.wav",
        include_bytes!("../samples/sizzle_vl1_rr3.wav"),
    ),
    (
        "sizzle_vl1_rr4.wav",
        include_bytes!("../samples/sizzle_vl1_rr4.wav"),
    ),
    (
        "sizzle_vl2_rr1.wav",
        include_bytes!("../samples/sizzle_vl2_rr1.wav"),
    ),
    (
        "sizzle_vl2_rr2.wav",
        include_bytes!("../samples/sizzle_vl2_rr2.wav"),
    ),
    (
        "sizzle_vl2_rr3.wav",
        include_bytes!("../samples/sizzle_vl2_rr3.wav"),
    ),
    (
        "sizzle_vl2_rr4.wav",
        include_bytes!("../samples/sizzle_vl2_rr4.wav"),
    ),
    (
        "sizzle_vl3_rr1.wav",
        include_bytes!("../samples/sizzle_vl3_rr1.wav"),
    ),
    (
        "sizzle_vl3_rr2.wav",
        include_bytes!("../samples/sizzle_vl3_rr2.wav"),
    ),
    (
        "sizzle_vl3_rr3.wav",
        include_bytes!("../samples/sizzle_vl3_rr3.wav"),
    ),
    (
        "sizzle_vl3_rr4.wav",
        include_bytes!("../samples/sizzle_vl3_rr4.wav"),
    ),
    (
        "splash_vl1_rr1.wav",
        include_bytes!("../samples/splash_vl1_rr1.wav"),
    ),
    (
        "splash_vl1_rr2.wav",
        include_bytes!("../samples/splash_vl1_rr2.wav"),
    ),
    (
        "splash_vl1_rr3.wav",
        include_bytes!("../samples/splash_vl1_rr3.wav"),
    ),
    (
        "splash_vl1_rr4.wav",
        include_bytes!("../samples/splash_vl1_rr4.wav"),
    ),
];

/// A cymbal articulation: `vel_hi.len()` velocity layers x `round_robins`
/// round-robin takes. File names follow `<name>_vl{L}_rr{R}.wav`, 1-based.
pub struct Bank {
    /// Articulation stem, e.g. `"ride"`.
    pub name: &'static str,
    /// Inclusive upper MIDI velocity of each layer, ascending (last is 127).
    /// Parsed from the source repos' SFZ mappings; a layer covers
    /// `(previous hi + 1)..=hi`, the first starting at 0.
    pub vel_hi: &'static [u8],
    /// Round-robin takes per velocity layer.
    pub round_robins: usize,
}

/// Ride cymbal, bow hit (`mid_ride_ride`).
pub static RIDE: Bank = Bank {
    name: "ride",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
};
/// Ride cymbal, bell hit (`mid_ride_bell`).
pub static RIDE_BELL: Bank = Bank {
    name: "ridebell",
    vel_hi: &[42, 85, 127],
    round_robins: 3,
};
/// Crash cymbal, normal hit (`mid_crash_crash`).
pub static CRASH: Bank = Bank {
    name: "crash",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
};
/// Sizzle crash (`mid_crash_sizzle`).
pub static CRASH_SIZZLE: Bank = Bank {
    name: "sizzle",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
};
/// Hi-hat splash (`mid_hh_splash`) -- one full-range velocity layer at the
/// source; the nearest thing this kit has to a splash cymbal.
pub static SPLASH: Bank = Bank {
    name: "splash",
    vel_hi: &[127],
    round_robins: 4,
};
/// Hi-hat, closed hit (`mid_hh_closed`).
pub static HH_CLOSED: Bank = Bank {
    name: "hhc",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 4,
};
/// Hi-hat, open hit (`mid_hh_open`).
pub static HH_OPEN: Bank = Bank {
    name: "hho",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 3,
};
/// Hi-hat, pedal (`mid_hh_pedal`).
pub static HH_PEDAL: Bank = Bank {
    name: "hhp",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
};
/// 18" china, stick hit (Big Rusty Drums `cn`, overhead mic).
pub static CHINA: Bank = Bank {
    name: "china",
    vel_hi: &[25, 51, 76, 101, 127],
    round_robins: 4,
};

/// Every articulation in the kit.
pub static BANKS: [&Bank; 9] = [
    &RIDE,
    &RIDE_BELL,
    &CRASH,
    &CRASH_SIZZLE,
    &SPLASH,
    &HH_CLOSED,
    &HH_OPEN,
    &HH_PEDAL,
    &CHINA,
];

impl Bank {
    /// Number of velocity layers.
    pub fn layers(&self) -> usize {
        self.vel_hi.len()
    }

    /// The 0-based velocity layer covering a MIDI velocity.
    pub fn layer_for_velocity(&self, velocity: u8) -> usize {
        self.vel_hi
            .iter()
            .position(|&hi| velocity <= hi)
            .unwrap_or(self.vel_hi.len() - 1)
    }

    /// File name of a take (0-based indices), e.g. `file_name(0, 0)` is
    /// `"ride_vl1_rr1.wav"`.
    ///
    /// Panics if `layer` or `rr` is out of range.
    pub fn file_name(&self, layer: usize, rr: usize) -> String {
        assert!(
            layer < self.layers() && rr < self.round_robins,
            "{}: take vl{}/rr{} out of range ({} layers x {} round robins)",
            self.name,
            layer + 1,
            rr + 1,
            self.layers(),
            self.round_robins,
        );
        format!("{}_vl{}_rr{}.wav", self.name, layer + 1, rr + 1)
    }

    /// Raw embedded WAV bytes for a take (0-based indices).
    pub fn wav(&self, layer: usize, rr: usize) -> &'static [u8] {
        let name = self.file_name(layer, rr);
        get(&name).expect("the embedded inventory covers every bank take")
    }

    /// Decoded mono 16-bit PCM at 44.1 kHz for a take (0-based indices).
    /// All files are decoded once on first use and cached.
    pub fn pcm(&self, layer: usize, rr: usize) -> &'static [i16] {
        let name = self.file_name(layer, rr);
        pcm(&name).expect("the embedded inventory covers every bank take")
    }
}

/// Returns the embedded WAV bytes for an exact file name.
///
/// Names include the `.wav` suffix and are case-sensitive.
pub fn get(name: &str) -> Option<&'static [u8]> {
    SAMPLES
        .iter()
        .find(|(candidate, _)| *candidate == name)
        .map(|(_, bytes)| *bytes)
}

/// Returns the decoded mono 16-bit 44.1 kHz PCM for an exact file name.
pub fn pcm(name: &str) -> Option<&'static [i16]> {
    static CACHE: OnceLock<Vec<Vec<i16>>> = OnceLock::new();
    let cache = CACHE.get_or_init(|| SAMPLES.iter().map(|(_, b)| decode_wav(b)).collect());
    let idx = SAMPLES
        .iter()
        .position(|(candidate, _)| *candidate == name)?;
    Some(&cache[idx])
}

/// Minimal RIFF walker for the bank's own files (16-bit mono 44.1 kHz).
fn decode_wav(bytes: &[u8]) -> Vec<i16> {
    assert!(&bytes[0..4] == b"RIFF" && &bytes[8..12] == b"WAVE");
    let mut pos = 12;
    let mut data = Vec::new();
    while pos + 8 <= bytes.len() {
        let id = &bytes[pos..pos + 4];
        let len = u32::from_le_bytes(bytes[pos + 4..pos + 8].try_into().unwrap()) as usize;
        let body = &bytes[pos + 8..(pos + 8 + len).min(bytes.len())];
        if id == b"fmt " {
            let channels = u16::from_le_bytes(body[2..4].try_into().unwrap());
            let sr = u32::from_le_bytes(body[4..8].try_into().unwrap());
            let bits = u16::from_le_bytes(body[14..16].try_into().unwrap());
            assert!(
                channels == 1 && sr == SAMPLE_RATE_HZ && bits == 16,
                "drum-kit bank must be 16-bit mono 44.1 kHz"
            );
        } else if id == b"data" {
            data = body
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes([c[0], c[1]]))
                .collect();
        }
        pos += 8 + len + (len & 1);
    }
    assert!(!data.is_empty(), "drum-kit bank file has no data chunk");
    data
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
    fn banks_cover_the_whole_inventory() {
        let mut from_banks: Vec<String> = BANKS
            .iter()
            .flat_map(|bank| {
                (0..bank.layers()).flat_map(move |layer| {
                    (0..bank.round_robins).map(move |rr| bank.file_name(layer, rr))
                })
            })
            .collect();
        from_banks.sort();
        let mut embedded: Vec<String> =
            SAMPLES.iter().map(|(name, _)| (*name).to_owned()).collect();
        embedded.sort();
        assert_eq!(from_banks, embedded);
        for bank in BANKS {
            assert_eq!(*bank.vel_hi.last().unwrap(), 127, "{}", bank.name);
            assert!(bank.vel_hi.windows(2).all(|w| w[0] < w[1]), "{}", bank.name);
        }
    }

    #[test]
    fn layer_for_velocity_respects_the_sfz_splits() {
        assert_eq!(RIDE.layer_for_velocity(1), 0);
        assert_eq!(RIDE.layer_for_velocity(42), 0);
        assert_eq!(RIDE.layer_for_velocity(43), 1);
        assert_eq!(RIDE.layer_for_velocity(85), 1);
        assert_eq!(RIDE.layer_for_velocity(86), 2);
        assert_eq!(RIDE.layer_for_velocity(127), 2);
        assert_eq!(HH_CLOSED.layer_for_velocity(31), 0);
        assert_eq!(HH_CLOSED.layer_for_velocity(32), 1);
        assert_eq!(HH_CLOSED.layer_for_velocity(96), 3);
        assert_eq!(CHINA.layer_for_velocity(25), 0);
        assert_eq!(CHINA.layer_for_velocity(102), 4);
        assert_eq!(SPLASH.layer_for_velocity(64), 0);
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

    const EXPECTED_BYTES: usize = 16392538;

    #[test]
    fn decoded_banks_are_valid_audio() {
        // duration bounds per articulation: (min_s, max_s) after trim/cap
        for (bank, min_s, max_s) in [
            (&RIDE, 0.5, 1.25),
            (&CRASH, 2.0, 2.85),
            (&HH_CLOSED, 0.2, 1.25),
            (&CHINA, 1.5, 2.25),
        ] {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let pcm = bank.pcm(layer, rr);
                    let dur = pcm.len() as f64 / SAMPLE_RATE_HZ as f64;
                    let peak = pcm.iter().map(|&v| (v as i32).abs()).max().unwrap();
                    let rms = (pcm
                        .iter()
                        .map(|&v| (v as f64 / 32768.0).powi(2))
                        .sum::<f64>()
                        / pcm.len() as f64)
                        .sqrt();
                    let name = bank.file_name(layer, rr);
                    println!(
                        "{name}: {dur:.3} s @ {SAMPLE_RATE_HZ} Hz, peak {:.3}, rms {rms:.3}",
                        peak as f64 / 32768.0
                    );
                    assert!((min_s..=max_s).contains(&dur), "{name}: {dur:.3} s");
                    // peak-normalized to 0.9 by the generator
                    let peak_f = peak as f64 / 32768.0;
                    assert!((0.85..=0.92).contains(&peak_f), "{name}: peak {peak_f:.3}");
                    assert!(rms > 0.01, "{name}: rms {rms:.4} is silence");
                }
            }
        }
    }
}
