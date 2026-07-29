//! Embedded CC0 sampled drum-kit bank for ferrosintesis -- the core kit.
//!
//! Mono 16-bit 44.1 kHz WAVs trimmed from CC0 1.0 Virtuosity Drums (`mid` mic
//! set) by `tools/ferrosintesis-samples/prepare_drumkit.py`: kick, snare
//! center/cross-stick, hi/low toms, ride bow/bell, and hi-hat
//! closed/open/pedal. See `PROVENANCE.md` for the pinned revisions, license
//! text, and the full articulation inventory -- including which banks' "round
//! robins" are adjacent source velocity layers (the deep-layered articulations
//! have no true round robins at the source).
//!
//! The three accent-cymbal banks -- crash, splash and the Karoryfer
//! Big Rusty Drums 18" china -- live in the companion crate
//! `ferrosintesis-samples-drumkit2`. That is a PACKAGING split, not a musical
//! one: the combined kit packaged at 15.8 MiB and crates.io rejects any crate
//! over 10 MiB. The cymbals are the long-decaying, largest files, so moving
//! those long cymbals keeps both packages below the limit. The [`Bank`]
//! type stays here and stays single; see [`BankSource`] for how a bank in the
//! other crate reaches its own bytes.
//!
//! Consumers normally access this crate through `ferrosintesis`, which depends
//! on both halves and routes GM channel-10 keys across them transparently.
//! `ferrosintesis`. Licence/provenance: see `LICENSE-CC0` / `PROVENANCE.md`.

#![forbid(unsafe_code)]

use std::sync::OnceLock;

/// Number of WAV files embedded in this package.
pub const FILE_COUNT: usize = 128;

/// Sample rate of every embedded WAV, in hertz.
pub const SAMPLE_RATE_HZ: u32 = 44_100;

static SAMPLES: [(&str, &[u8]); FILE_COUNT] = [
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
        "kick_vl1_rr1.wav",
        include_bytes!("../samples/kick_vl1_rr1.wav"),
    ),
    (
        "kick_vl1_rr2.wav",
        include_bytes!("../samples/kick_vl1_rr2.wav"),
    ),
    (
        "kick_vl1_rr3.wav",
        include_bytes!("../samples/kick_vl1_rr3.wav"),
    ),
    (
        "kick_vl1_rr4.wav",
        include_bytes!("../samples/kick_vl1_rr4.wav"),
    ),
    (
        "kick_vl2_rr1.wav",
        include_bytes!("../samples/kick_vl2_rr1.wav"),
    ),
    (
        "kick_vl2_rr2.wav",
        include_bytes!("../samples/kick_vl2_rr2.wav"),
    ),
    (
        "kick_vl2_rr3.wav",
        include_bytes!("../samples/kick_vl2_rr3.wav"),
    ),
    (
        "kick_vl2_rr4.wav",
        include_bytes!("../samples/kick_vl2_rr4.wav"),
    ),
    (
        "kick_vl3_rr1.wav",
        include_bytes!("../samples/kick_vl3_rr1.wav"),
    ),
    (
        "kick_vl3_rr2.wav",
        include_bytes!("../samples/kick_vl3_rr2.wav"),
    ),
    (
        "kick_vl3_rr3.wav",
        include_bytes!("../samples/kick_vl3_rr3.wav"),
    ),
    (
        "kick_vl3_rr4.wav",
        include_bytes!("../samples/kick_vl3_rr4.wav"),
    ),
    (
        "kick_vl4_rr1.wav",
        include_bytes!("../samples/kick_vl4_rr1.wav"),
    ),
    (
        "kick_vl4_rr2.wav",
        include_bytes!("../samples/kick_vl4_rr2.wav"),
    ),
    (
        "kick_vl4_rr3.wav",
        include_bytes!("../samples/kick_vl4_rr3.wav"),
    ),
    (
        "kick_vl4_rr4.wav",
        include_bytes!("../samples/kick_vl4_rr4.wav"),
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
        "sidestick_vl1_rr1.wav",
        include_bytes!("../samples/sidestick_vl1_rr1.wav"),
    ),
    (
        "sidestick_vl1_rr2.wav",
        include_bytes!("../samples/sidestick_vl1_rr2.wav"),
    ),
    (
        "sidestick_vl1_rr3.wav",
        include_bytes!("../samples/sidestick_vl1_rr3.wav"),
    ),
    (
        "sidestick_vl2_rr1.wav",
        include_bytes!("../samples/sidestick_vl2_rr1.wav"),
    ),
    (
        "sidestick_vl2_rr2.wav",
        include_bytes!("../samples/sidestick_vl2_rr2.wav"),
    ),
    (
        "sidestick_vl2_rr3.wav",
        include_bytes!("../samples/sidestick_vl2_rr3.wav"),
    ),
    (
        "sidestick_vl3_rr1.wav",
        include_bytes!("../samples/sidestick_vl3_rr1.wav"),
    ),
    (
        "sidestick_vl3_rr2.wav",
        include_bytes!("../samples/sidestick_vl3_rr2.wav"),
    ),
    (
        "sidestick_vl3_rr3.wav",
        include_bytes!("../samples/sidestick_vl3_rr3.wav"),
    ),
    (
        "snare_vl1_rr1.wav",
        include_bytes!("../samples/snare_vl1_rr1.wav"),
    ),
    (
        "snare_vl1_rr2.wav",
        include_bytes!("../samples/snare_vl1_rr2.wav"),
    ),
    (
        "snare_vl1_rr3.wav",
        include_bytes!("../samples/snare_vl1_rr3.wav"),
    ),
    (
        "snare_vl2_rr1.wav",
        include_bytes!("../samples/snare_vl2_rr1.wav"),
    ),
    (
        "snare_vl2_rr2.wav",
        include_bytes!("../samples/snare_vl2_rr2.wav"),
    ),
    (
        "snare_vl2_rr3.wav",
        include_bytes!("../samples/snare_vl2_rr3.wav"),
    ),
    (
        "snare_vl3_rr1.wav",
        include_bytes!("../samples/snare_vl3_rr1.wav"),
    ),
    (
        "snare_vl3_rr2.wav",
        include_bytes!("../samples/snare_vl3_rr2.wav"),
    ),
    (
        "snare_vl3_rr3.wav",
        include_bytes!("../samples/snare_vl3_rr3.wav"),
    ),
    (
        "snare_vl4_rr1.wav",
        include_bytes!("../samples/snare_vl4_rr1.wav"),
    ),
    (
        "snare_vl4_rr2.wav",
        include_bytes!("../samples/snare_vl4_rr2.wav"),
    ),
    (
        "snare_vl4_rr3.wav",
        include_bytes!("../samples/snare_vl4_rr3.wav"),
    ),
    (
        "snare_vl5_rr1.wav",
        include_bytes!("../samples/snare_vl5_rr1.wav"),
    ),
    (
        "snare_vl5_rr2.wav",
        include_bytes!("../samples/snare_vl5_rr2.wav"),
    ),
    (
        "snare_vl5_rr3.wav",
        include_bytes!("../samples/snare_vl5_rr3.wav"),
    ),
    (
        "snare_vl6_rr1.wav",
        include_bytes!("../samples/snare_vl6_rr1.wav"),
    ),
    (
        "snare_vl6_rr2.wav",
        include_bytes!("../samples/snare_vl6_rr2.wav"),
    ),
    (
        "snare_vl6_rr3.wav",
        include_bytes!("../samples/snare_vl6_rr3.wav"),
    ),
    (
        "tomhi_vl1_rr1.wav",
        include_bytes!("../samples/tomhi_vl1_rr1.wav"),
    ),
    (
        "tomhi_vl1_rr2.wav",
        include_bytes!("../samples/tomhi_vl1_rr2.wav"),
    ),
    (
        "tomhi_vl1_rr3.wav",
        include_bytes!("../samples/tomhi_vl1_rr3.wav"),
    ),
    (
        "tomhi_vl2_rr1.wav",
        include_bytes!("../samples/tomhi_vl2_rr1.wav"),
    ),
    (
        "tomhi_vl2_rr2.wav",
        include_bytes!("../samples/tomhi_vl2_rr2.wav"),
    ),
    (
        "tomhi_vl2_rr3.wav",
        include_bytes!("../samples/tomhi_vl2_rr3.wav"),
    ),
    (
        "tomhi_vl3_rr1.wav",
        include_bytes!("../samples/tomhi_vl3_rr1.wav"),
    ),
    (
        "tomhi_vl3_rr2.wav",
        include_bytes!("../samples/tomhi_vl3_rr2.wav"),
    ),
    (
        "tomhi_vl3_rr3.wav",
        include_bytes!("../samples/tomhi_vl3_rr3.wav"),
    ),
    (
        "tomhi_vl4_rr1.wav",
        include_bytes!("../samples/tomhi_vl4_rr1.wav"),
    ),
    (
        "tomhi_vl4_rr2.wav",
        include_bytes!("../samples/tomhi_vl4_rr2.wav"),
    ),
    (
        "tomhi_vl4_rr3.wav",
        include_bytes!("../samples/tomhi_vl4_rr3.wav"),
    ),
    (
        "tomlo_vl1_rr1.wav",
        include_bytes!("../samples/tomlo_vl1_rr1.wav"),
    ),
    (
        "tomlo_vl1_rr2.wav",
        include_bytes!("../samples/tomlo_vl1_rr2.wav"),
    ),
    (
        "tomlo_vl1_rr3.wav",
        include_bytes!("../samples/tomlo_vl1_rr3.wav"),
    ),
    (
        "tomlo_vl2_rr1.wav",
        include_bytes!("../samples/tomlo_vl2_rr1.wav"),
    ),
    (
        "tomlo_vl2_rr2.wav",
        include_bytes!("../samples/tomlo_vl2_rr2.wav"),
    ),
    (
        "tomlo_vl2_rr3.wav",
        include_bytes!("../samples/tomlo_vl2_rr3.wav"),
    ),
    (
        "tomlo_vl3_rr1.wav",
        include_bytes!("../samples/tomlo_vl3_rr1.wav"),
    ),
    (
        "tomlo_vl3_rr2.wav",
        include_bytes!("../samples/tomlo_vl3_rr2.wav"),
    ),
    (
        "tomlo_vl3_rr3.wav",
        include_bytes!("../samples/tomlo_vl3_rr3.wav"),
    ),
    (
        "tomlo_vl4_rr1.wav",
        include_bytes!("../samples/tomlo_vl4_rr1.wav"),
    ),
    (
        "tomlo_vl4_rr2.wav",
        include_bytes!("../samples/tomlo_vl4_rr2.wav"),
    ),
    (
        "tomlo_vl4_rr3.wav",
        include_bytes!("../samples/tomlo_vl4_rr3.wav"),
    ),
];

static PCM_CACHE: OnceLock<Vec<Vec<i16>>> = OnceLock::new();

/// Where a bank's embedded takes actually live.
///
/// A `Bank` descriptor and the WAVs it names are not always in the same crate. The three
/// accent-cymbal banks (crash, splash, china) were split out into
/// `ferrosintesis-samples-drumkit2` so that neither package exceeds the crates.io 10 MiB
/// per-crate limit — the combined kit packaged at 15.8 MiB and was rejected outright.
///
/// The split is a PACKAGING seam, not a musical one, so the `Bank` type stays here and
/// stays single: `SampledDrum` holds one `&'static Bank` and does not care which crate
/// embedded the bytes. Each bank simply carries the lookups of its owning crate.
pub struct BankSource {
    /// Raw embedded WAV bytes for an exact file name, or `None` if absent.
    pub wav: fn(&str) -> Option<&'static [u8]>,
    /// Decoded mono 16-bit 44.1 kHz PCM for an exact file name, or `None` if absent.
    pub pcm: fn(&str) -> Option<&'static [i16]>,
    /// Decoded PCM at an exact inventory index, or `None` if out of range.
    pub pcm_by_index: fn(usize) -> Option<&'static [i16]>,
}

/// This crate's own embedded inventory. `ferrosintesis-samples-drumkit2` declares its own.
pub static SOURCE: BankSource = BankSource {
    wav: get,
    pcm,
    pcm_by_index,
};

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
    /// The crate embedding this bank's takes. See [`BankSource`].
    pub source: &'static BankSource,
    /// First take in the owning source's PCM cache.
    #[doc(hidden)]
    pub first_sample_index: usize,
}

/// Ride cymbal, bow hit (`mid_ride_ride`).
pub static RIDE: Bank = Bank {
    name: "ride",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 56,
};
/// Ride cymbal, bell hit (`mid_ride_bell`).
pub static RIDE_BELL: Bank = Bank {
    name: "ridebell",
    vel_hi: &[42, 85, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 68,
};
/// Hi-hat, closed hit (`mid_hh_closed`).
pub static HH_CLOSED: Bank = Bank {
    name: "hhc",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 0,
};
/// Hi-hat, open hit (`mid_hh_open`).
pub static HH_OPEN: Bank = Bank {
    name: "hho",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 16,
};
/// Hi-hat, pedal (`mid_hh_pedal`).
pub static HH_PEDAL: Bank = Bank {
    name: "hhp",
    vel_hi: &[42, 85, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 28,
};
/// Kick drum, snares on (`kickmic_kick_snon`) -- the source's full 4x4 grid of
/// velocity layers x TRUE round robins.
pub static KICK: Bank = Bank {
    name: "kick",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 4,
    source: &SOURCE,
    first_sample_index: 40,
};
/// Snare, center hit (`mid_snare_center`). The source has 36 single-take
/// velocity layers and no round robins; each of this bank's 6 layers fills
/// its 3 round-robin slots with adjacent source layers -- distinct takes at
/// near-identical dynamics (see PROVENANCE.md).
pub static SNARE: Bank = Bank {
    name: "snare",
    vel_hi: &[21, 41, 63, 84, 105, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 86,
};
/// Snare cross-stick (`mid_snare_crossstick`) -- the GM 37 side stick;
/// adjacent-layer round robins.
pub static SIDESTICK: Bank = Bank {
    name: "sidestick",
    vel_hi: &[47, 87, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 77,
};
/// High (rack) tom, center hit (`mid_htom_center`), root ~181 Hz;
/// adjacent-layer round robins.
pub static TOM_HI: Bank = Bank {
    name: "tomhi",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 104,
};
/// Low (floor) tom, center hit (`mid_ltom_center`), root ~113.5 Hz;
/// adjacent-layer round robins.
pub static TOM_LO: Bank = Bank {
    name: "tomlo",
    vel_hi: &[31, 63, 95, 127],
    round_robins: 3,
    source: &SOURCE,
    first_sample_index: 116,
};

/// Every articulation in the kit.
pub static BANKS: [&Bank; 10] = [
    &RIDE, &RIDE_BELL, &HH_CLOSED, &HH_OPEN, &HH_PEDAL, &KICK, &SNARE, &SIDESTICK, &TOM_HI, &TOM_LO,
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
        self.take_index(layer, rr);
        format!("{}_vl{}_rr{}.wav", self.name, layer + 1, rr + 1)
    }

    /// Owning source's direct cache index for a take (0-based indices).
    #[doc(hidden)]
    pub fn take_index(&self, layer: usize, rr: usize) -> usize {
        assert!(
            layer < self.layers() && rr < self.round_robins,
            "{}: take vl{}/rr{} out of range ({} layers x {} round robins)",
            self.name,
            layer + 1,
            rr + 1,
            self.layers(),
            self.round_robins,
        );
        self.first_sample_index + layer * self.round_robins + rr
    }

    /// Raw embedded WAV bytes for a take (0-based indices).
    pub fn wav(&self, layer: usize, rr: usize) -> &'static [u8] {
        let name = self.file_name(layer, rr);
        (self.source.wav)(&name).expect("the embedded inventory covers every bank take")
    }

    /// Decoded mono 16-bit PCM at 44.1 kHz for a take (0-based indices).
    /// All files are decoded once on first use and cached.
    pub fn pcm(&self, layer: usize, rr: usize) -> &'static [i16] {
        let index = self.take_index(layer, rr);
        (self.source.pcm_by_index)(index).expect("the embedded inventory covers every bank take")
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
    let cache = decoded_samples();
    let idx = SAMPLES
        .iter()
        .position(|(candidate, _)| *candidate == name)?;
    Some(&cache[idx])
}

/// Returns decoded PCM at an exact inventory index.
#[doc(hidden)]
pub fn pcm_by_index(index: usize) -> Option<&'static [i16]> {
    decoded_samples().get(index).map(Vec::as_slice)
}

/// Decode this package's complete PCM inventory now.
///
/// Call away from a realtime thread so the first drum hit does no decoding.
pub fn prewarm() {
    let _ = decoded_samples();
}

/// Number of times this package's PCM cache has initialized (zero or one).
///
/// Hidden diagnostic used to enforce the realtime prewarm contract end to end.
#[doc(hidden)]
pub fn pcm_cache_initializations() -> usize {
    usize::from(PCM_CACHE.get().is_some())
}

fn decoded_samples() -> &'static Vec<Vec<i16>> {
    PCM_CACHE.get_or_init(|| SAMPLES.iter().map(|(_, bytes)| decode_wav(bytes)).collect())
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
    fn bank_take_indices_match_the_owning_inventory() {
        for bank in BANKS {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let index = bank.take_index(layer, rr);
                    let name = bank.file_name(layer, rr);
                    assert_eq!(
                        SAMPLES[index].0, name,
                        "{} mapped the wrong take",
                        bank.name
                    );
                    assert!(std::ptr::eq(
                        bank.pcm(layer, rr),
                        pcm_by_index(index).expect("bank index is in range"),
                    ));
                }
            }
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
        assert_eq!(KICK.layer_for_velocity(31), 0);
        assert_eq!(KICK.layer_for_velocity(32), 1);
        assert_eq!(KICK.layer_for_velocity(127), 3);
        assert_eq!(SNARE.layer_for_velocity(21), 0);
        assert_eq!(SNARE.layer_for_velocity(22), 1);
        assert_eq!(SNARE.layer_for_velocity(85), 4);
        assert_eq!(SNARE.layer_for_velocity(106), 5);
        assert_eq!(TOM_LO.layer_for_velocity(64), 2);
        assert_eq!(SIDESTICK.layer_for_velocity(90), 2);
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

    const EXPECTED_BYTES: usize = 9632990;

    #[test]
    fn decoded_banks_are_valid_audio() {
        // duration bounds per articulation: (min_s, max_s) after trim/cap
        for (bank, min_s, max_s) in [
            (&RIDE, 0.5, 1.25),
            (&HH_CLOSED, 0.2, 1.25),
            (&KICK, 0.3, 0.65),
            (&SNARE, 0.3, 0.65),
            (&SIDESTICK, 0.2, 0.45),
            (&TOM_HI, 0.5, 0.85),
            (&TOM_LO, 0.5, 0.85),
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
