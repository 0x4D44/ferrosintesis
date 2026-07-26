//! LA-style sample layer — the Roland D-50 trick: a short PCM attack
//! transient supplies the first ~200 ms (the bow bite, the breath chiff —
//! exactly what synthesis fakes worst), then crossfades into the modeled
//! sustain, which keeps all its expressive vibrato, scoop and dynamics.
//!
//! The transients are trimmed from VSCO 2 Community Edition (CC0 / public
//! domain) sustains and embedded from two compile-time asset crates, so the tool
//! remains a single self-contained executable. Each zone's root frequency was
//! measured by autocorrelation, so repitching is cent-accurate.

use crate::dsp::{key_freq, vel_amp, vel_amp_sensed, Rng};
use crate::voices::Voice;
use std::sync::OnceLock;

pub struct Zone {
    root: f32,
    data: Vec<f32>,
    /// Memoized pitch-synchronous sustain-loop bounds — see [`Zone::sustain_loop`].
    /// `Some(None)` means "searched, no usable loop"; that verdict is cached too.
    sustain_loop: OnceLock<Option<(usize, usize)>>,
}

/// A pitch-synchronous sustain-loop search: `(zone PCM, zone root Hz)` in,
/// `(loop_start, loop_end)` out. `find_sax_loop` and `find_bottle_loop` are the two.
type LoopFinder = fn(&[f32], f32) -> Option<(usize, usize)>;

impl Zone {
    /// This zone's sustain-loop bounds, searched **at most once per zone**.
    ///
    /// `find` is an O(starts x lengths x window) scan of the zone's static PCM — for the
    /// blown bottle, 67.4 million multiply-accumulates and 30,560 square roots. Running
    /// it per NoteOn inside the audio callback blows the realtime deadline
    /// (MM-BUG-KILN-00064). The zone and its PCM are `'static` and immutable, so the
    /// answer is a constant: compute it once, here, and let
    /// [`prewarm`] force it off the realtime thread.
    fn sustain_loop(&self, find: LoopFinder) -> Option<(usize, usize)> {
        *self
            .sustain_loop
            .get_or_init(|| find(&self.data, self.root))
    }
}

/// Minimal RIFF walker for the bank's own files (16-bit mono 44.1 kHz).
fn parse_wav(bytes: &[u8]) -> Vec<f32> {
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
                channels == 1 && sr == 44100 && bits == 16,
                "sample bank must be 16-bit mono 44.1 kHz"
            );
        } else if id == b"data" {
            data = body
                .chunks_exact(2)
                .map(|c| i16::from_le_bytes([c[0], c[1]]) as f32 / 32768.0)
                .collect();
        }
        pos += 8 + len + (len & 1);
    }
    assert!(!data.is_empty(), "sample bank file has no data chunk");
    data
}

#[cfg(feature = "embedded-samples")]
fn embedded_wav(name: &str) -> &'static [u8] {
    ferrosintesis_samples_core::get(name)
        .or_else(|| ferrosintesis_samples_orchestral::get(name))
        .or_else(|| ferrosintesis_samples_orchestral2::get(name))
        .or_else(|| ferrosintesis_samples_gong::get(name))
        .or_else(|| ferrosintesis_samples_grand::get(name))
        .or_else(|| ferrosintesis_samples_vcsl_steinway::get(name))
        .or_else(|| ferrosintesis_samples_vcsl_kawai::get(name))
        .or_else(|| ferrosintesis_samples_headroom::get(name))
        .or_else(|| ferrosintesis_samples_musescore_grand::get(name))
        .or_else(|| ferrosintesis_samples_dark_salamander::get(name))
        .or_else(|| ferrosintesis_samples_ydp_grand::get(name))
        .or_else(|| ferrosintesis_samples_honkytonk::get(name))
        .or_else(|| ferrosintesis_samples_b1_upright::get(name))
        .or_else(|| ferrosintesis_samples_clavinet::get(name))
        .or_else(|| ferrosintesis_samples_musescore::get(name))
        .or_else(|| ferrosintesis_samples_sax::get(name))
        .or_else(|| ferrosintesis_samples_strings::get(name))
        .or_else(|| ferrosintesis_samples_bass::get(name))
        .or_else(|| ferrosintesis_samples_bottle::get(name))
        .or_else(|| ferrosintesis_samples_ccby::get(name))
        .or_else(|| ferrosintesis_samples_rain::get(name))
        .or_else(|| ferrosintesis_samples_mandolin::get(name))
        .or_else(|| ferrosintesis_samples_fretnoise::get(name))
        .unwrap_or_else(|| panic!("embedded sample inventory is missing {name}"))
}

#[cfg(not(feature = "embedded-samples"))]
fn embedded_wav(name: &str) -> &'static [u8] {
    panic!("sample {name} requested from a modeled-only ferrosintesis build")
}

/// The ONE way a lazily-initialized static cache in this module may be filled.
///
/// Every `static _: OnceLock<_>` here is a realtime hazard: whatever it decodes runs on
/// whichever thread touches it first, and in a live session that is the audio callback.
/// [`prewarm`] exists to force that work onto the setup thread, and the oracles below
/// prove it did — but they can only see initializations they are told about. This funnel
/// is what makes that total: `no_lazy_cache_bypasses_init_once` refuses a bare
/// `get_or_init`, so a new cache cannot be added without being recorded.
///
/// A macro rather than a function so the expansion stays byte-for-byte the old
/// `get_or_init` (the `&Vec<T>` -> `&[T]` coercion every accessor's return type relies on
/// survives), and so `line!()` reports the CACHE's own site rather than the funnel's.
/// Release builds compile to exactly the bare `get_or_init` — the bookkeeping is
/// `cfg(test)` and inside the closure, so it runs once, only on a real initialization.
macro_rules! init_once {
    ($cell:ident, $build:expr) => {
        $cell.get_or_init(|| {
            #[cfg(test)]
            crate::sampler::record_cache_init(line!());
            $build
        })
    };
}

/// The embedded real-rain ambience loop (owner-recorded 2017 field recording,
/// CC0), decoded once to mono f32 at 44.1 kHz. Unlike the pitched attack banks
/// this is a full seamless loop, not a zone set: the GM 96 rain FX voice reads
/// it cyclically as a bed under its modeled shimmer, so the wash is a real
/// downpour rather than synthetic hiss. Only present in `embedded-samples`
/// builds; the modeled-only synth keeps the pure synthetic wash.
#[cfg(feature = "embedded-samples")]
pub fn rain_loop() -> &'static [f32] {
    static L: OnceLock<Vec<f32>> = OnceLock::new();
    init_once!(L, parse_wav(embedded_wav("rain_loop.wav")))
}

/// Counts how many sample banks have run their one-time decode.
///
/// Test-only, and the whole basis of `prewarm_leaves_no_bank_uninitialized`
/// (MM-BUG-KILN-00059). Every `bank!` expansion runs exactly once, inside its
/// `OnceLock::get_or_init`, so this counts distinct bank initializations.
///
/// Reading it is race-free *after* `prewarm()` returns: at that point every bank it
/// covers is initialized, so no later call from any thread can increment it again.
#[cfg(test)]
pub(crate) static BANK_INITS: std::sync::atomic::AtomicUsize =
    std::sync::atomic::AtomicUsize::new(0);

/// Counts how many pitch-synchronous sustain-loop SEARCHES have actually run.
///
/// Test-only, and the basis of `prewarm_leaves_no_sustain_loop_unsearched` and
/// `live::realtime_note_on_after_prewarm_does_no_decode_or_loop_search`
/// (MM-BUG-KILN-00064). Incremented in the body of each `find_*_loop`, not at the
/// memo, so it also catches a rewiring that bypasses [`Zone::sustain_loop`] and
/// reintroduces the per-NoteOn scan.
///
/// Reading it is race-free *after* `prewarm()` returns, for the same reason as
/// [`BANK_INITS`]: prewarm resolves every zone's loop, so no later voice
/// construction on any thread can move it.
#[cfg(test)]
pub(crate) static LOOP_SEARCHES: std::sync::atomic::AtomicUsize =
    std::sync::atomic::AtomicUsize::new(0);

/// Source lines of every `init_once` call that has actually run its builder.
///
/// Test-only. `BANK_INITS` counts `bank!` expansions, which is narrower than "lazy
/// cache": a bank-less cache (`rain_loop`, the gong layer pair) never touches it, so
/// a coverage oracle built on it could not see one (MM-BUG-KILN-00073). Recording the
/// call SITE instead of a count makes the failure name the accessor that escaped, and
/// lets `every_lazy_cache_is_reached_by_the_exercise_sweep` check the set against the
/// `static _: OnceLock<_>` declarations the source itself carries — a derived total,
/// not a second hand-written list.
#[cfg(test)]
pub(crate) static CACHE_INIT_SITES: std::sync::Mutex<std::collections::BTreeSet<u32>> =
    std::sync::Mutex::new(std::collections::BTreeSet::new());

#[cfg(test)]
pub(crate) fn record_cache_init(line: u32) {
    CACHE_INIT_SITES
        .lock()
        .expect("cache-site registry")
        .insert(line);
}

macro_rules! bank {
    ($($file:literal => $root:expr),+ $(,)?) => {{
        #[cfg(test)]
        crate::sampler::BANK_INITS.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        vec![$(Zone {
            root: $root,
            data: parse_wav(embedded_wav($file)),
            sustain_loop: OnceLock::new(),
        }),+]
    }};
}

// Roots measured by autocorrelation in the prep script
// (see ../../tools/ferrosintesis-samples/README.md).
fn violin_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "violin_G3_f.wav" => 196.00,
            "violin_E4_f.wav" => 329.33,
            "violin_C5_f.wav" => 519.94,
            "violin_G5_f.wav" => 786.90,
            "violin_C6_f.wav" => 1040.45,
            "violin_E6_f.wav" => 1329.58,
        )
    })
}

fn violin_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "violin_G3_p.wav" => 195.11,
            "violin_E4_p.wav" => 329.51,
            "violin_C5_p.wav" => 521.61,
            "violin_G5_p.wav" => 787.21,
            "violin_C6_p.wav" => 1045.77,
            "violin_E6_p.wav" => 1320.88,
        )
    })
}

fn flute() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "flute_C4.wav" => 523.23,
            "flute_A4.wav" => 879.92,
            "flute_E5.wav" => 1320.47,
            "flute_A5.wav" => 1757.81,
            "flute_C6.wav" => 2091.31,
        )
    })
}

fn piano_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "piano_C2_pp.wav" => 65.05,
            "piano_G2_pp.wav" => 97.77,
            "piano_C3_pp.wav" => 130.68,
            "piano_G3_pp.wav" => 195.31,
            "piano_C4_pp.wav" => 261.04,
            "piano_G4_pp.wav" => 393.15,
            "piano_C5_pp.wav" => 523.65,
            "piano_G5_pp.wav" => 784.41,
            "piano_C6_pp.wav" => 1051.84,
        )
    })
}

fn piano_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "piano_C2_mf.wav" => 65.17,
            "piano_G2_mf.wav" => 98.10,
            "piano_C3_mf.wav" => 130.94,
            "piano_G3_mf.wav" => 196.23,
            "piano_C4_mf.wav" => 261.25,
            "piano_G4_mf.wav" => 393.58,
            "piano_C5_mf.wav" => 524.52,
            "piano_G5_mf.wav" => 785.35,
            "piano_C6_mf.wav" => 1050.22,
        )
    })
}

fn piano_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "piano_C2_f.wav" => 65.52,
            "piano_G2_f.wav" => 98.33,
            "piano_C3_f.wav" => 131.19,
            "piano_G3_f.wav" => 195.73,
            "piano_C4_f.wav" => 261.74,
            "piano_G4_f.wav" => 393.96,
            "piano_C5_f.wav" => 525.21,
            "piano_G5_f.wav" => 786.26,
            "piano_C6_f.wav" => 1050.00,
        )
    })
}

fn piano_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            // The pinned VSCO bank has only one pp take for C2/G2. Alias those
            // zones honestly; every other cell below contains a real second take.
            "piano_C2_pp.wav" => 65.05,
            "piano_G2_pp.wav" => 97.77,
            "piano_C3_pp_rr2.wav" => 130.60,
            "piano_G3_pp_rr2.wav" => 194.91,
            "piano_C4_pp_rr2.wav" => 261.00,
            "piano_G4_pp_rr2.wav" => 392.77,
            "piano_C5_pp_rr2.wav" => 523.95,
            "piano_G5_pp_rr2.wav" => 784.04,
            "piano_C6_pp_rr2.wav" => 1049.08,
        )
    })
}

fn piano_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "piano_C2_mf_rr2.wav" => 65.51,
            "piano_G2_mf_rr2.wav" => 98.28,
            "piano_C3_mf_rr2.wav" => 131.12,
            "piano_G3_mf_rr2.wav" => 196.23,
            "piano_C4_mf_rr2.wav" => 261.29,
            "piano_G4_mf_rr2.wav" => 393.76,
            "piano_C5_mf_rr2.wav" => 524.92,
            "piano_G5_mf_rr2.wav" => 785.18,
            "piano_C6_mf_rr2.wav" => 1049.43,
        )
    })
}

fn piano_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "piano_C2_f_rr2.wav" => 65.58,
            "piano_G2_f_rr2.wav" => 98.43,
            "piano_C3_f_rr2.wav" => 131.20,
            "piano_G3_f_rr2.wav" => 196.39,
            "piano_C4_f_rr2.wav" => 261.73,
            "piano_G4_f_rr2.wav" => 393.77,
            "piano_C5_f_rr2.wav" => 525.19,
            "piano_G5_f_rr2.wav" => 786.16,
            "piano_C6_f_rr2.wav" => 1050.12,
        )
    })
}

fn trumpet_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "trumpet_F2_p.wav" => 174.88,
            "trumpet_C3_p.wav" => 259.21,
            "trumpet_G3_p.wav" => 392.78,
            "trumpet_D4_p.wav" => 586.53,
            "trumpet_A4_p.wav" => 877.64,
        )
    })
}

fn trumpet_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "trumpet_F2_f.wav" => 172.61,
            "trumpet_C3_f.wav" => 261.15,
            "trumpet_G3_f.wav" => 393.83,
            "trumpet_D4_f.wav" => 588.04,
            "trumpet_A4_f.wav" => 886.84,
        )
    })
}

fn mutetpt_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mutetpt_A#2_p.wav" => 232.97,
            "mutetpt_D3_p.wav" => 293.86,
            "mutetpt_G3_p.wav" => 392.99,
            "mutetpt_D4_p.wav" => 586.63,
            "mutetpt_A4_p.wav" => 880.37,
        )
    })
}

fn mutetpt_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mutetpt_A#2_f.wav" => 233.07,
            "mutetpt_D3_f.wav" => 293.30,
            "mutetpt_G3_f.wav" => 392.47,
            "mutetpt_D4_f.wav" => 586.39,
            "mutetpt_A4_f.wav" => 880.34,
        )
    })
}

fn trombone_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "trombone_F1_p.wav" => 87.34,
            "trombone_A#1_p.wav" => 116.31,
            "trombone_D2_p.wav" => 146.73,
            "trombone_F2_p.wav" => 174.45,
            "trombone_C3_p.wav" => 261.43,
            "trombone_F3_p.wav" => 349.09,
        )
    })
}

fn trombone_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "trombone_F1_f.wav" => 87.21,
            "trombone_A#1_f.wav" => 116.56,
            "trombone_D2_f.wav" => 146.73,
            "trombone_F2_f.wav" => 174.53,
            "trombone_C3_f.wav" => 261.56,
            "trombone_F3_f.wav" => 349.05,
        )
    })
}

fn tuba_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "tuba_A#0_p.wav" => 58.01,
            "tuba_D#1_p.wav" => 78.25,
            "tuba_A#1_p.wav" => 116.03,
            "tuba_D2_p.wav" => 146.34,
            "tuba_F2_p.wav" => 174.46,
            "tuba_A#2_p.wav" => 231.99,
        )
    })
}

fn tuba_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "tuba_A#0_f.wav" => 58.35,
            "tuba_D#1_f.wav" => 77.78,
            "tuba_A#1_f.wav" => 116.34,
            "tuba_D2_f.wav" => 145.88,
            "tuba_F2_f.wav" => 174.42,
            "tuba_A#2_f.wav" => 233.19,
        )
    })
}

fn horn_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "horn_A#1_p.wav" => 116.90,
            "horn_D2_p.wav" => 148.36,
            "horn_F2_p.wav" => 173.95,
            "horn_A2_p.wav" => 219.46,
            "horn_C3_p.wav" => 260.59,
            "horn_D4_p.wav" => 604.11,
        )
    })
}

fn horn_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "horn_A#1_f.wav" => 116.81,
            "horn_D2_f.wav" => 146.41,
            "horn_F2_f.wav" => 173.93,
            "horn_A2_f.wav" => 219.08,
            "horn_C3_f.wav" => 260.84,
            "horn_D4_f.wav" => 604.11,
        )
    })
}

fn oboe_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "oboe_D3_p.wav" => 293.50,
            "oboe_F3_p.wav" => 347.64,
            "oboe_A#3_p.wav" => 464.35,
            "oboe_D4_p.wav" => 586.46,
            "oboe_F4_p.wav" => 698.81,
            "oboe_A#4_p.wav" => 935.72,
        )
    })
}

fn oboe_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "oboe_D3_f.wav" => 294.16,
            "oboe_F3_f.wav" => 349.95,
            "oboe_A#3_f.wav" => 466.12,
            "oboe_D4_f.wav" => 588.05,
            "oboe_F4_f.wav" => 698.94,
            "oboe_A#4_f.wav" => 930.35,
        )
    })
}

fn bassoon_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "bassoon_A#0_p.wav" => 58.31,
            "bassoon_F1_p.wav" => 87.26,
            "bassoon_C2_p.wav" => 130.70,
            "bassoon_G2_p.wav" => 195.98,
            "bassoon_D#3_p.wav" => 312.70,
            "bassoon_C4_p.wav" => 523.95,
        )
    })
}

fn bassoon_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "bassoon_A#0_f.wav" => 58.25,
            "bassoon_F1_f.wav" => 87.29,
            "bassoon_C2_f.wav" => 130.76,
            "bassoon_G2_f.wav" => 195.94,
            "bassoon_D#3_f.wav" => 311.06,
            "bassoon_C4_f.wav" => 523.15,
        )
    })
}

fn clarinet_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "clarinet_A#2_p.wav" => 232.55,
            "clarinet_D3_p.wav" => 293.36,
            "clarinet_F3_p.wav" => 349.08,
            "clarinet_A#3_p.wav" => 466.23,
            "clarinet_D4_p.wav" => 586.91,
            "clarinet_F4_p.wav" => 698.75,
        )
    })
}

fn clarinet_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "clarinet_A#2_f.wav" => 233.09,
            "clarinet_D3_f.wav" => 292.97,
            "clarinet_F3_f.wav" => 348.60,
            "clarinet_A#3_f.wav" => 466.38,
            "clarinet_D4_f.wav" => 587.88,
            "clarinet_F4_f.wav" => 700.07,
        )
    })
}

/// GM 25 steel-string acoustic — a 2017 Martin HD28 Vintage Series, CC0.
/// Roots are the MEASURED fundamentals, not the nominal note names: the
/// instrument was tuned ~3-16 cents flat and the sampler repitches from the
/// real f0, so the flatness never reaches the render.
fn steel() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steel_E2.wav" => 81.98,
            "steel_A#2.wav" => 116.33,
            "steel_E3.wav" => 164.56,
            "steel_A#3.wav" => 231.86,
            "steel_E4.wav" => 327.92,
            "steel_B4.wav" => 490.67,
            "steel_F5.wav" => 693.98,
            "steel_B5.wav" => 978.93,
        )
    })
}

/// GM 25 DEFAULT since 2026.07.23 — Arthur's own Eastman E1D dreadnought,
/// plectrum take, CC0 and first-party (no upstream, so no SHA pin to keep).
/// Masters: `samples/acoustic-guitar-eastman-e1d/picked.opus`.
///
/// Two zones stand off the nominal grid. The take's A#2 begins inside the
/// previous note's decay and its B4 is quiet and barely isolated, and
/// `trim_to_onset` finds the attack as the first sample above 3 % of peak —
/// under ~30 dB of pre-onset quiet it latches onto the wrong note. **B2** and
/// **A#4** are the well-isolated neighbours (~40–46 dB) and stand in; roots are
/// MEASURED, so a zone only has to sit near its slot. The nylon bank does the
/// same thing (B2 for its source's missing A#2).
///
/// The take reads consistently sharp (mean ≈ +11 cents) — a harder plectrum
/// attack stretches the string, and the 0.9 s window is attack-dominated. That
/// never reaches the render: the sampler repitches from these measured roots.
fn eastpick() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "eastpick_E2.wav" => 83.56,
            "eastpick_B2.wav" => 124.31,
            "eastpick_E3.wav" => 166.21,
            "eastpick_A#3.wav" => 233.27,
            "eastpick_E4.wav" => 331.56,
            "eastpick_A#4.wav" => 469.73,
            "eastpick_F5.wav" => 702.02,
            "eastpick_B5.wav" => 991.03,
        )
    })
}

/// GM 25 CC0=1 alternate — the same Eastman E1D, fingerstyle take
/// (`samples/acoustic-guitar-eastman-e1d/plucked.opus`, CC0). Warmer and much
/// darker than the picked take (centroid ~480–630 Hz vs ~2400–3000 Hz), and the
/// cleaner recording of the two: every zone sits on the nominal grid with
/// 34–56 dB of onset isolation, so no substitutions were needed. Tuning is
/// closer to nominal than the picked take (mean ≈ +4 cents) — a softer
/// fingerstyle attack stretches the string less.
fn eastpluck() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "eastpluck_E2.wav" => 83.33,
            "eastpluck_A#2.wav" => 116.61,
            "eastpluck_E3.wav" => 165.49,
            "eastpluck_A#3.wav" => 232.21,
            "eastpluck_E4.wav" => 330.31,
            "eastpluck_B4.wav" => 495.27,
            "eastpluck_F5.wav" => 699.35,
            "eastpluck_B5.wav" => 987.59,
        )
    })
}

fn nylon() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "nylon_E2.wav" => 82.47,
            "nylon_B2.wav" => 124.07,
            "nylon_E3.wav" => 165.21,
            "nylon_A#3.wav" => 234.63,
            "nylon_E4.wav" => 326.69,
            "nylon_A#4.wav" => 466.15,
            "nylon_E5.wav" => 661.48,
        )
    })
}

// String sections for GM 48-49: one bank per dynamic, cello section covering
// the low split and violin section the high — `nearest` picks the section by
// root, so a low pad gets celli and a high line gets violins. Roots measured
// by autocorrelation (both sections sound one octave above their VSCO labels).
fn strsec_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "celens_C1_p.wav" => 65.48,
            "celens_G1_p.wav" => 97.46,
            "celens_D2_p.wav" => 146.97,
            "celens_A2_p.wav" => 219.85,
            "celens_E3_p.wav" => 329.02,
            "celens_B3_p.wav" => 493.92,
            "vlnens_G2_p.wav" => 196.06,
            "vlnens_D3_p.wav" => 293.66,
            "vlnens_A3_p.wav" => 440.80,
            "vlnens_E4_p.wav" => 660.20,
            "vlnens_B4_p.wav" => 989.79,
            "vlnens_D5_p.wav" => 1175.21,
        )
    })
}

fn strsec_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "celens_C1_f.wav" => 65.38,
            "celens_G1_f.wav" => 97.71,
            "celens_D2_f.wav" => 146.73,
            "celens_A2_f.wav" => 219.17,
            "celens_E3_f.wav" => 328.79,
            "celens_B3_f.wav" => 493.91,
            "vlnens_G2_f.wav" => 195.56,
            "vlnens_D3_f.wav" => 292.71,
            "vlnens_A3_f.wav" => 441.25,
            "vlnens_E4_f.wav" => 657.60,
            "vlnens_B4_f.wav" => 991.44,
            "vlnens_D5_f.wav" => 1170.87,
        )
    })
}

// GM 43 contrabass LA attack: a REAL solo double-bass arco onset (VSCO 2 CE Solo
// Contrabass, SusNV / non-vibrato so the model's own vibrato is not doubled; CC0),
// replacing the old repitched cello-SECTION celens bite that read as a small cello
// section an octave low. Roots MEASURED at bake (source labels sit one octave below
// sounding pitch); zones span sounding E1 (~41 Hz) to B3 (~247 Hz), covering the GM43
// register with far less repitch than the old 3 zones. `nearest` picks the closest
// zone; the waveguide keeps the expressive sustain.
fn contrabass_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "dbass_E1_p.wav" => 41.22,
            "dbass_A#1_p.wav" => 57.95,
            "dbass_E2_p.wav" => 82.31,
            "dbass_A2_p.wav" => 108.96,
            "dbass_C#3_p.wav" => 137.69,
            "dbass_E3_p.wav" => 164.19,
            "dbass_G#3_p.wav" => 207.89,
            "dbass_B3_p.wav" => 244.89,
        )
    })
}

fn contrabass_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "dbass_E1_f.wav" => 41.15,
            "dbass_A#1_f.wav" => 57.63,
            "dbass_E2_f.wav" => 82.21,
            "dbass_A2_f.wav" => 109.20,
            "dbass_C#3_f.wav" => 138.30,
            "dbass_E3_f.wav" => 164.89,
            "dbass_G#3_f.wav" => 206.22,
            "dbass_B3_f.wav" => 243.45,
        )
    })
}

/// Attack-transient bank for the GM 43 contrabass (real solo double-bass arco,
/// VSCO Solo Contrabass SusNV). Velocity picks the soft / loud layer (VSCO v1/v3).
pub fn contrabass_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        contrabass_f()
    } else {
        contrabass_p()
    }
}

fn pizzbass() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "pizzbass_E1.wav" => 41.09,
            "pizzbass_G1.wav" => 48.60,
            "pizzbass_A#1.wav" => 58.25,
            "pizzbass_C2.wav" => 65.04,
            "pizzbass_E2.wav" => 82.41,
            "pizzbass_G#2.wav" => 102.12,
            "pizzbass_A2.wav" => 112.51,
            "pizzbass_G#3.wav" => 205.95,
        )
    })
}

/// GM 32 acoustic (upright/double) bass PIZZICATO onset (VSCO Solo Contrabass Pizz,
/// CC0, -strings) over the Pluck(&UPRIGHT) model. Roots MEASURED at bake (labels one
/// octave below sounding, like the arco dbass); C#3/E3 dropped (weak low fundamentals).
/// 8 zones sound E1..G#3.
pub fn pizzbass_bank() -> &'static [Zone] {
    pizzbass()
}

fn finger_bass() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "fingerbass_E1.wav" => 41.22,
            "fingerbass_F#1.wav" => 46.84,
            "fingerbass_G#1.wav" => 52.12,
            "fingerbass_A#1.wav" => 58.69,
            "fingerbass_C2.wav" => 65.40,
            "fingerbass_D2.wav" => 73.27,
        )
    })
}

/// GM 33 fingered electric-bass onset (FreePats RBX finger, CC0, -bass) over the
/// Pluck(&BASS) model; also serves GM 35 fretless (rides the finger onset — the pluck
/// attack is what the layer supplies; the model carries the fretless glide). Roots
/// MEASURED at bake near the SFZ key. 6 zones sound E1..D2.
pub fn finger_bass_bank() -> &'static [Zone] {
    finger_bass()
}

fn pick_bass() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "pickbass_E1.wav" => 41.62,
            "pickbass_F#1.wav" => 47.19,
            "pickbass_G#1.wav" => 52.55,
            "pickbass_A#1.wav" => 58.70,
            "pickbass_C2.wav" => 65.83,
            "pickbass_D2.wav" => 73.70,
            "pickbass_E2.wav" => 82.13,
        )
    })
}

/// GM 34 picked electric-bass onset (FreePats RBX pick, CC0, -bass) over the Pluck(&PICK)
/// model. Roots MEASURED at bake near the SFZ key. 7 zones sound E1..E2.
pub fn pick_bass_bank() -> &'static [Zone] {
    pick_bass()
}

fn rhodes() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "rhodes_E1.wav" => 41.21,
            "rhodes_A#1.wav" => 58.24,
            "rhodes_C#2.wav" => 69.26,
            "rhodes_E2.wav" => 82.35,
            "rhodes_G#2.wav" => 104.18,
            "rhodes_C#3.wav" => 138.59,
            "rhodes_D#5.wav" => 622.77,
            "rhodes_E5.wav" => 659.30,
            "rhodes_G#5.wav" => 826.52,
            "rhodes_A#5.wav" => 931.19,
            "rhodes_C#6.wav" => 1106.02,
        )
    })
}

/// GM 4 electric piano onset (real Fender Rhodes Mk II tine, tim.kahn Freesound 3957,
/// CC-BY, -ccby) over the electric_piano_1 model. Roots MEASURED at bake (filenames are the
/// measured pitch). 11 zones sound E1..C#6 (source lacks octave 4 — repitch bridges it).
pub fn rhodes_bank() -> &'static [Zone] {
    rhodes()
}

fn dulcimer_la() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "dulcimer_C#4.wav" => 280.62,
            "dulcimer_D4.wav" => 295.17,
            "dulcimer_E4.wav" => 330.95,
            "dulcimer_F#4.wav" => 373.89,
            "dulcimer_G4.wav" => 394.73,
            "dulcimer_A4.wav" => 442.73,
            "dulcimer_B4.wav" => 496.11,
            "dulcimer_C5.wav" => 525.46,
            "dulcimer_D5.wav" => 594.66,
        )
    })
}

/// GM 15 hammered-dulcimer onset (iternetcone Freesound 19445, CC-BY, -ccby) over the
/// Pluck(&DULCIMER) model. Roots MEASURED at bake. 9 zones sound C#4..D5.
pub fn dulcimer_bank() -> &'static [Zone] {
    dulcimer_la()
}

fn musicbox() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "musicbox_E5.wav" => 668.51,
            "musicbox_A5.wav" => 873.59,
            "musicbox_B5.wav" => 983.03,
            "musicbox_C6.wav" => 1049.43,
            "musicbox_D6.wav" => 1190.81,
            "musicbox_E6.wav" => 1328.91,
            "musicbox_F6.wav" => 1412.39,
            "musicbox_G#6.wav" => 1686.54,
            "musicbox_A6.wav" => 1784.92,
            "musicbox_B6.wav" => 2006.59,
            "musicbox_C7.wav" => 2127.34,
        )
    })
}

/// GM 10 music box onset (moodyfingers Freesound 44539, CC0, -orchestral2) over the
/// bell(MUSICBOX) model. Roots MEASURED at bake. 11 zones sound E5..C7.
pub fn musicbox_bank() -> &'static [Zone] {
    musicbox()
}

// GM 42 cello LA attack: a REAL solo cello arco onset (Karoryfer x bigcat "Bigcat
// Cello", down-bow sus, CC0), replacing the old cello-SECTION celens bite that carried
// ensemble chorus and a slow section swell (which measurably ducked the model's own
// crisper attack). Roots MEASURED at bake (source labels sit one octave below sounding
// pitch); zones span sounding C2 (~65 Hz) to F#5 (~740 Hz), the cello's full range.
// `nearest` picks the closest zone; the waveguide keeps the sustain.
fn cello_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "cellosolo_C2_p.wav" => 65.50,
            "cellosolo_A2_p.wav" => 109.19,
            "cellosolo_C3_p.wav" => 130.82,
            "cellosolo_A3_p.wav" => 215.89,
            "cellosolo_C4_p.wav" => 261.79,
            "cellosolo_A4_p.wav" => 439.37,
            "cellosolo_C5_p.wav" => 522.21,
            "cellosolo_F#5_p.wav" => 739.94,
        )
    })
}

fn cello_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "cellosolo_C2_f.wav" => 65.29,
            "cellosolo_A2_f.wav" => 109.39,
            "cellosolo_C3_f.wav" => 130.50,
            "cellosolo_A3_f.wav" => 220.00,
            "cellosolo_C4_f.wav" => 261.55,
            "cellosolo_A4_f.wav" => 439.31,
            "cellosolo_C5_f.wav" => 521.47,
            "cellosolo_F#5_f.wav" => 742.74,
        )
    })
}

/// Attack-transient bank for the GM 42 cello (real solo cello arco, Bigcat Cello
/// down-bow). Velocity picks the soft / loud layer (Bigcat p / f dynamics).
pub fn cello_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        cello_f()
    } else {
        cello_p()
    }
}

/// Velocity picks the dynamic layer; alternating round robins keep repeated
/// notes from being byte-identical, except quiet C2/G2 where the pinned source
/// has one take and both banks deliberately select it.
///
/// The VSCO upright: GM 0's DEFAULT recording until 2026.07.26, now its CC0=1
/// alternate. It is the one GM 0 bank baked with [`crate::voices::PianoSampleCal::Gm0Conditioned`]
/// envelope conditioning, and that calibration followed it into the alternate
/// slot — see `voices::GM0_SOURCES`.
pub fn piano_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => piano_pp(),
        (0..=51, true) => piano_pp_rr2(),
        (52..=95, false) => piano_mf(),
        (52..=95, true) => piano_mf_rr2(),
        (_, false) => piano_f(),
        (_, true) => piano_f_rr2(),
    }
}

// GM 0 Acoustic Grand — Salamander Grand Piano V3 (Yamaha C5), CC BY 3.0, in the
// ferrosintesis-samples-grand crate. A real concert grand, distinct from the CC0
// VSCO upright that voices GM 1/3. Roots measured by autocorrelation in prepare.py
// (F# zones stand in for the G positions — the nearest sampled pitch). RR2 is an
// adjacent-higher velocity layer, peak-matched, so repeated notes vary.
fn grand_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_pp.wav" => 65.23,
            "grand_F#2_pp.wav" => 92.00,
            "grand_C3_pp.wav" => 130.39,
            "grand_F#3_pp.wav" => 184.74,
            "grand_C4_pp.wav" => 261.50,
            "grand_F#4_pp.wav" => 369.37,
            "grand_C5_pp.wav" => 524.09,
            "grand_F#5_pp.wav" => 741.81,
            "grand_C6_pp.wav" => 1051.21,
        )
    })
}

fn grand_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_pp_rr2.wav" => 65.34,
            "grand_F#2_pp_rr2.wav" => 92.14,
            "grand_C3_pp_rr2.wav" => 130.39,
            "grand_F#3_pp_rr2.wav" => 184.80,
            "grand_C4_pp_rr2.wav" => 261.52,
            "grand_F#4_pp_rr2.wav" => 369.43,
            "grand_C5_pp_rr2.wav" => 524.17,
            "grand_F#5_pp_rr2.wav" => 741.84,
            "grand_C6_pp_rr2.wav" => 1051.95,
        )
    })
}

fn grand_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_mf.wav" => 65.62,
            "grand_F#2_mf.wav" => 92.38,
            "grand_C3_mf.wav" => 130.45,
            "grand_F#3_mf.wav" => 185.07,
            "grand_C4_mf.wav" => 262.03,
            "grand_F#4_mf.wav" => 370.25,
            "grand_C5_mf.wav" => 524.71,
            "grand_F#5_mf.wav" => 741.85,
            "grand_C6_mf.wav" => 1053.01,
        )
    })
}

fn grand_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_mf_rr2.wav" => 65.65,
            "grand_F#2_mf_rr2.wav" => 92.49,
            "grand_C3_mf_rr2.wav" => 130.47,
            "grand_F#3_mf_rr2.wav" => 185.08,
            "grand_C4_mf_rr2.wav" => 262.08,
            "grand_F#4_mf_rr2.wav" => 370.29,
            "grand_C5_mf_rr2.wav" => 524.79,
            "grand_F#5_mf_rr2.wav" => 741.87,
            "grand_C6_mf_rr2.wav" => 1053.05,
        )
    })
}

fn grand_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_f.wav" => 65.72,
            "grand_F#2_f.wav" => 92.85,
            "grand_C3_f.wav" => 130.77,
            "grand_F#3_f.wav" => 185.32,
            "grand_C4_f.wav" => 262.90,
            "grand_F#4_f.wav" => 370.52,
            "grand_C5_f.wav" => 525.38,
            "grand_F#5_f.wav" => 741.92,
            "grand_C6_f.wav" => 1054.71,
        )
    })
}

fn grand_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "grand_C2_f_rr2.wav" => 65.68,
            "grand_F#2_f_rr2.wav" => 92.97,
            "grand_C3_f_rr2.wav" => 130.85,
            "grand_F#3_f_rr2.wav" => 185.42,
            "grand_C4_f_rr2.wav" => 262.81,
            "grand_F#4_f_rr2.wav" => 370.56,
            "grand_C5_f_rr2.wav" => 525.99,
            "grand_F#5_f_rr2.wav" => 742.05,
            "grand_C6_f_rr2.wav" => 1055.09,
        )
    })
}

/// Velocity picks the dynamic layer; the seed alternates round robins, exactly
/// like [`piano_bank`]. Voices GM 0's CC0 alt bank 2 — the GM 0 DEFAULT is
/// [`b1upright_bank`], and GM 1/3 have their own defaults ([`kawai_bank`],
/// [`honkytonk_bank`]).
pub fn grand_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => grand_pp(),
        (0..=51, true) => grand_pp_rr2(),
        (52..=95, false) => grand_mf(),
        (52..=95, true) => grand_mf_rr2(),
        (_, false) => grand_f(),
        (_, true) => grand_f_rr2(),
    }
}

// GM 0 Acoustic Grand ALTERNATE bank 3 - VCSL "Grand Piano, Steinway B" (CC0,
// ferrosintesis-samples-vcsl-steinway). A warm vintage Steinway, the tonal
// contrast to the bright Salamander C5 at CC0=2. Roots measured by autocorrelation
// in prepare.py (family steinwayb); F# zones stand in for the G positions. RR2 is
// an adjacent velocity layer, peak-matched, so repeated notes vary. Selected via
// CC0 alt bank 3 on a GM 0 channel (altbank::make -> acoustic_grand_with_bank).
fn steinwayb_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_pp.wav" => 65.88,
            "steinwayb_F#2_pp.wav" => 92.54,
            "steinwayb_C3_pp.wav" => 130.91,
            "steinwayb_F#3_pp.wav" => 185.51,
            "steinwayb_C4_pp.wav" => 262.25,
            "steinwayb_F#4_pp.wav" => 371.37,
            "steinwayb_C5_pp.wav" => 525.53,
            "steinwayb_F#5_pp.wav" => 739.00,
            "steinwayb_C6_pp.wav" => 1049.52,
        )
    })
}

fn steinwayb_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_pp_rr2.wav" => 65.79,
            "steinwayb_F#2_pp_rr2.wav" => 92.40,
            "steinwayb_C3_pp_rr2.wav" => 131.27,
            "steinwayb_F#3_pp_rr2.wav" => 185.91,
            "steinwayb_C4_pp_rr2.wav" => 262.92,
            "steinwayb_F#4_pp_rr2.wav" => 372.55,
            "steinwayb_C5_pp_rr2.wav" => 526.49,
            "steinwayb_F#5_pp_rr2.wav" => 740.67,
            "steinwayb_C6_pp_rr2.wav" => 1049.34,
        )
    })
}

fn steinwayb_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_mf.wav" => 65.79,
            "steinwayb_F#2_mf.wav" => 92.40,
            "steinwayb_C3_mf.wav" => 131.27,
            "steinwayb_F#3_mf.wav" => 185.91,
            "steinwayb_C4_mf.wav" => 262.92,
            "steinwayb_F#4_mf.wav" => 372.55,
            "steinwayb_C5_mf.wav" => 526.49,
            "steinwayb_F#5_mf.wav" => 740.67,
            "steinwayb_C6_mf.wav" => 1049.34,
        )
    })
}

fn steinwayb_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_mf_rr2.wav" => 65.67,
            "steinwayb_F#2_mf_rr2.wav" => 92.39,
            "steinwayb_C3_mf_rr2.wav" => 131.39,
            "steinwayb_F#3_mf_rr2.wav" => 185.95,
            "steinwayb_C4_mf_rr2.wav" => 262.84,
            "steinwayb_F#4_mf_rr2.wav" => 372.49,
            "steinwayb_C5_mf_rr2.wav" => 526.67,
            "steinwayb_F#5_mf_rr2.wav" => 743.63,
            "steinwayb_C6_mf_rr2.wav" => 1049.46,
        )
    })
}

fn steinwayb_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_f.wav" => 65.67,
            "steinwayb_F#2_f.wav" => 92.39,
            "steinwayb_C3_f.wav" => 131.39,
            "steinwayb_F#3_f.wav" => 185.95,
            "steinwayb_C4_f.wav" => 262.84,
            "steinwayb_F#4_f.wav" => 372.49,
            "steinwayb_C5_f.wav" => 526.67,
            "steinwayb_F#5_f.wav" => 743.63,
            "steinwayb_C6_f.wav" => 1049.46,
        )
    })
}

fn steinwayb_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "steinwayb_C2_f_rr2.wav" => 65.79,
            "steinwayb_F#2_f_rr2.wav" => 92.40,
            "steinwayb_C3_f_rr2.wav" => 131.27,
            "steinwayb_F#3_f_rr2.wav" => 185.91,
            "steinwayb_C4_f_rr2.wav" => 262.92,
            "steinwayb_F#4_f_rr2.wav" => 372.55,
            "steinwayb_C5_f_rr2.wav" => 526.49,
            "steinwayb_F#5_f_rr2.wav" => 740.67,
            "steinwayb_C6_f_rr2.wav" => 1049.34,
        )
    })
}

/// Velocity picks the dynamic layer; the seed alternates round robins, exactly
/// like [`grand_bank`]. Voices GM 0 CC0 alt bank 3 (VCSL Steinway B).
pub fn steinwayb_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => steinwayb_pp(),
        (0..=51, true) => steinwayb_pp_rr2(),
        (52..=95, false) => steinwayb_mf(),
        (52..=95, true) => steinwayb_mf_rr2(),
        (_, false) => steinwayb_f(),
        (_, true) => steinwayb_f_rr2(),
    }
}

// GM 1 Bright Acoustic DEFAULT - VCSL "Grand Piano, Kawai" (CC0,
// ferrosintesis-samples-vcsl-kawai). A darker, rounder vintage grand. Roots MEASURED
// (Kawai labels sit an octave below sounding pitch - see the crate PROVENANCE); 8
// zones from the pitches with full v1..v4 coverage. This is GM 1's default
// recording (voices::make program 1), not a GM 0 alternate.
fn kawai_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_pp.wav" => 64.82,
            "kawai_A2_pp.wav" => 109.29,
            "kawai_C3_pp.wav" => 130.04,
            "kawai_A#3_pp.wav" => 231.94,
            "kawai_C4_pp.wav" => 260.88,
            "kawai_A#4_pp.wav" => 464.44,
            "kawai_C5_pp.wav" => 522.09,
            "kawai_C6_pp.wav" => 1046.16,
        )
    })
}

fn kawai_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_pp_rr2.wav" => 65.12,
            "kawai_A2_pp_rr2.wav" => 109.50,
            "kawai_C3_pp_rr2.wav" => 130.47,
            "kawai_A#3_pp_rr2.wav" => 231.60,
            "kawai_C4_pp_rr2.wav" => 261.05,
            "kawai_A#4_pp_rr2.wav" => 464.18,
            "kawai_C5_pp_rr2.wav" => 521.86,
            "kawai_C6_pp_rr2.wav" => 1045.95,
        )
    })
}

fn kawai_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_mf.wav" => 65.12,
            "kawai_A2_mf.wav" => 109.50,
            "kawai_C3_mf.wav" => 130.47,
            "kawai_A#3_mf.wav" => 231.60,
            "kawai_C4_mf.wav" => 261.05,
            "kawai_A#4_mf.wav" => 464.18,
            "kawai_C5_mf.wav" => 521.86,
            "kawai_C6_mf.wav" => 1045.95,
        )
    })
}

fn kawai_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_mf_rr2.wav" => 65.51,
            "kawai_A2_mf_rr2.wav" => 109.95,
            "kawai_C3_mf_rr2.wav" => 131.34,
            "kawai_A#3_mf_rr2.wav" => 233.31,
            "kawai_C4_mf_rr2.wav" => 261.90,
            "kawai_A#4_mf_rr2.wav" => 466.39,
            "kawai_C5_mf_rr2.wav" => 522.87,
            "kawai_C6_mf_rr2.wav" => 1046.29,
        )
    })
}

fn kawai_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_f.wav" => 65.64,
            "kawai_A2_f.wav" => 110.15,
            "kawai_C3_f.wav" => 131.01,
            "kawai_A#3_f.wav" => 234.22,
            "kawai_C4_f.wav" => 262.53,
            "kawai_A#4_f.wav" => 467.69,
            "kawai_C5_f.wav" => 524.03,
            "kawai_C6_f.wav" => 1044.80,
        )
    })
}

fn kawai_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "kawai_C2_f_rr2.wav" => 65.51,
            "kawai_A2_f_rr2.wav" => 109.95,
            "kawai_C3_f_rr2.wav" => 131.34,
            "kawai_A#3_f_rr2.wav" => 233.31,
            "kawai_C4_f_rr2.wav" => 261.90,
            "kawai_A#4_f_rr2.wav" => 466.39,
            "kawai_C5_f_rr2.wav" => 522.87,
            "kawai_C6_f_rr2.wav" => 1046.29,
        )
    })
}

/// Velocity picks the dynamic layer; the seed alternates round robins, like
/// [`grand_bank`]. Voices the GM 1 DEFAULT (VCSL Kawai) since the 2026.07.18 re-voicing.
pub fn kawai_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => kawai_pp(),
        (0..=51, true) => kawai_pp_rr2(),
        (52..=95, false) => kawai_mf(),
        (52..=95, true) => kawai_mf_rr2(),
        (_, false) => kawai_f(),
        (_, true) => kawai_f_rr2(),
    }
}

// GM 0 Acoustic Grand ALTERNATE bank 4 - Headroom / Intimate Piano (Bengt Nilsson,
// Yamaha C3), CC-BY 4.0, ferrosintesis-samples-headroom. A warm, intimate close-mic
// C3 grand. Roots MEASURED (MIDI-number labels are true sounding pitch); F# stands
// in for G. Selected via CC0 alt bank 4. ATTRIBUTION REQUIRED - see the crate NOTICE.
fn headroom_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_pp.wav" => 65.50,
            "headroom_F#2_pp.wav" => 92.37,
            "headroom_C3_pp.wav" => 131.18,
            "headroom_F#3_pp.wav" => 185.59,
            "headroom_C4_pp.wav" => 262.46,
            "headroom_F#4_pp.wav" => 372.02,
            "headroom_C5_pp.wav" => 526.16,
            "headroom_F#5_pp.wav" => 744.53,
            "headroom_C6_pp.wav" => 1054.19,
        )
    })
}

fn headroom_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_pp_rr2.wav" => 66.25,
            "headroom_F#2_pp_rr2.wav" => 92.77,
            "headroom_C3_pp_rr2.wav" => 131.60,
            "headroom_F#3_pp_rr2.wav" => 185.93,
            "headroom_C4_pp_rr2.wav" => 262.50,
            "headroom_F#4_pp_rr2.wav" => 372.24,
            "headroom_C5_pp_rr2.wav" => 526.29,
            "headroom_F#5_pp_rr2.wav" => 745.36,
            "headroom_C6_pp_rr2.wav" => 1054.02,
        )
    })
}

fn headroom_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_mf.wav" => 66.43,
            "headroom_F#2_mf.wav" => 93.07,
            "headroom_C3_mf.wav" => 132.09,
            "headroom_F#3_mf.wav" => 186.21,
            "headroom_C4_mf.wav" => 262.55,
            "headroom_F#4_mf.wav" => 372.58,
            "headroom_C5_mf.wav" => 526.52,
            "headroom_F#5_mf.wav" => 745.43,
            "headroom_C6_mf.wav" => 1054.45,
        )
    })
}

fn headroom_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_mf_rr2.wav" => 66.33,
            "headroom_F#2_mf_rr2.wav" => 93.82,
            "headroom_C3_mf_rr2.wav" => 132.37,
            "headroom_F#3_mf_rr2.wav" => 186.66,
            "headroom_C4_mf_rr2.wav" => 262.66,
            "headroom_F#4_mf_rr2.wav" => 372.72,
            "headroom_C5_mf_rr2.wav" => 526.85,
            "headroom_F#5_mf_rr2.wav" => 745.73,
            "headroom_C6_mf_rr2.wav" => 1055.27,
        )
    })
}

fn headroom_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_f.wav" => 66.23,
            "headroom_F#2_f.wav" => 94.08,
            "headroom_C3_f.wav" => 132.59,
            "headroom_F#3_f.wav" => 186.86,
            "headroom_C4_f.wav" => 262.79,
            "headroom_F#4_f.wav" => 372.89,
            "headroom_C5_f.wav" => 527.10,
            "headroom_F#5_f.wav" => 746.62,
            "headroom_C6_f.wav" => 1055.91,
        )
    })
}

fn headroom_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "headroom_C2_f_rr2.wav" => 66.33,
            "headroom_F#2_f_rr2.wav" => 93.82,
            "headroom_C3_f_rr2.wav" => 132.37,
            "headroom_F#3_f_rr2.wav" => 186.66,
            "headroom_C4_f_rr2.wav" => 262.66,
            "headroom_F#4_f_rr2.wav" => 372.72,
            "headroom_C5_f_rr2.wav" => 526.85,
            "headroom_F#5_f_rr2.wav" => 745.73,
            "headroom_C6_f_rr2.wav" => 1055.27,
        )
    })
}

/// Velocity picks the dynamic layer; the seed alternates round robins, like
/// [`grand_bank`]. Voices GM 0 CC0 alt bank 4 (Headroom/Intimate C3).
pub fn headroom_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => headroom_pp(),
        (0..=51, true) => headroom_pp_rr2(),
        (52..=95, false) => headroom_mf(),
        (52..=95, true) => headroom_mf_rr2(),
        (_, false) => headroom_f(),
        (_, true) => headroom_f_rr2(),
    }
}

// GM 1 Bright Acoustic ALTERNATE bank 2 - MuseScore_General "Grand Piano" (MIT,
// ferrosintesis-samples-musescore-grand). A warm-to-neutral GM grand. A DENSE
// SINGLE-VELOCITY multisample (MF tier); dynamics come from the LA blend + model.
// Roots MEASURED near each SF3 originalPitch. Selected via CC0 alt bank 2 on a
// GM 1 channel — not a GM 0 alternate.
fn musescoregrand_zones() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "musescoregrand_B1.wav" => 62.20,
            "musescoregrand_D2.wav" => 74.09,
            "musescoregrand_E2.wav" => 83.24,
            "musescoregrand_G2.wav" => 98.56,
            "musescoregrand_A2.wav" => 110.65,
            "musescoregrand_B2.wav" => 124.31,
            "musescoregrand_C3.wav" => 131.54,
            "musescoregrand_D3.wav" => 147.97,
            "musescoregrand_E3.wav" => 165.70,
            "musescoregrand_G3.wav" => 196.77,
            "musescoregrand_A3.wav" => 221.51,
            "musescoregrand_B3.wav" => 248.60,
            "musescoregrand_C4.wav" => 263.02,
            "musescoregrand_D4.wav" => 295.29,
            "musescoregrand_E4.wav" => 331.03,
            "musescoregrand_G4.wav" => 393.37,
            "musescoregrand_A4.wav" => 441.71,
            "musescoregrand_B4.wav" => 496.71,
            "musescoregrand_C5.wav" => 524.28,
            "musescoregrand_E5.wav" => 661.14,
            "musescoregrand_G5.wav" => 786.25,
            "musescoregrand_G#5.wav" => 832.82,
            "musescoregrand_B5.wav" => 990.56,
            "musescoregrand_C#6.wav" => 1112.86,
            "musescoregrand_D#6.wav" => 1254.21,
        )
    })
}

/// Single-velocity multisample: the same zones regardless of velocity/RR
/// (dynamics are carried by the LA blend + model). Voices GM 1 CC0 alt bank 2.
pub fn musescoregrand_bank(_vel: u8, _rr2: bool) -> &'static [Zone] {
    musescoregrand_zones()
}

// GM 0 Acoustic Grand ALTERNATE bank 5 - DARKENED Salamander (CC-BY 3.0,
// ferrosintesis-samples-dark-salamander). The CC0=2 Salamander grand with a
// high-shelf EQ cut (warmer). Same zones/roots as grand; the "is it EQ not
// instrument?" A/B, whose other endpoint is CC0=2, not the GM 0 default.
// Selected via CC0 alt bank 5.
fn darkgrand_pp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_pp.wav" => 65.22,
            "darkgrand_F#2_pp.wav" => 91.97,
            "darkgrand_C3_pp.wav" => 130.41,
            "darkgrand_F#3_pp.wav" => 184.72,
            "darkgrand_C4_pp.wav" => 261.50,
            "darkgrand_F#4_pp.wav" => 369.35,
            "darkgrand_C5_pp.wav" => 524.09,
            "darkgrand_F#5_pp.wav" => 741.86,
            "darkgrand_C6_pp.wav" => 1051.48,
        )
    })
}

fn darkgrand_pp_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_pp_rr2.wav" => 65.32,
            "darkgrand_F#2_pp_rr2.wav" => 92.13,
            "darkgrand_C3_pp_rr2.wav" => 130.40,
            "darkgrand_F#3_pp_rr2.wav" => 184.77,
            "darkgrand_C4_pp_rr2.wav" => 261.53,
            "darkgrand_F#4_pp_rr2.wav" => 369.41,
            "darkgrand_C5_pp_rr2.wav" => 524.11,
            "darkgrand_F#5_pp_rr2.wav" => 741.87,
            "darkgrand_C6_pp_rr2.wav" => 1052.11,
        )
    })
}

fn darkgrand_mf() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_mf.wav" => 65.59,
            "darkgrand_F#2_mf.wav" => 92.33,
            "darkgrand_C3_mf.wav" => 130.44,
            "darkgrand_F#3_mf.wav" => 185.00,
            "darkgrand_C4_mf.wav" => 261.89,
            "darkgrand_F#4_mf.wav" => 370.04,
            "darkgrand_C5_mf.wav" => 524.45,
            "darkgrand_F#5_mf.wav" => 741.86,
            "darkgrand_C6_mf.wav" => 1052.95,
        )
    })
}

fn darkgrand_mf_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_mf_rr2.wav" => 65.61,
            "darkgrand_F#2_mf_rr2.wav" => 92.40,
            "darkgrand_C3_mf_rr2.wav" => 130.44,
            "darkgrand_F#3_mf_rr2.wav" => 185.02,
            "darkgrand_C4_mf_rr2.wav" => 261.85,
            "darkgrand_F#4_mf_rr2.wav" => 370.07,
            "darkgrand_C5_mf_rr2.wav" => 524.50,
            "darkgrand_F#5_mf_rr2.wav" => 741.86,
            "darkgrand_C6_mf_rr2.wav" => 1052.99,
        )
    })
}

fn darkgrand_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_f.wav" => 65.69,
            "darkgrand_F#2_f.wav" => 92.72,
            "darkgrand_C3_f.wav" => 130.61,
            "darkgrand_F#3_f.wav" => 185.21,
            "darkgrand_C4_f.wav" => 262.38,
            "darkgrand_F#4_f.wav" => 370.24,
            "darkgrand_C5_f.wav" => 524.86,
            "darkgrand_F#5_f.wav" => 741.87,
            "darkgrand_C6_f.wav" => 1054.35,
        )
    })
}

fn darkgrand_f_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "darkgrand_C2_f_rr2.wav" => 65.69,
            "darkgrand_F#2_f_rr2.wav" => 92.82,
            "darkgrand_C3_f_rr2.wav" => 130.67,
            "darkgrand_F#3_f_rr2.wav" => 185.29,
            "darkgrand_C4_f_rr2.wav" => 262.32,
            "darkgrand_F#4_f_rr2.wav" => 370.26,
            "darkgrand_C5_f_rr2.wav" => 525.27,
            "darkgrand_F#5_f_rr2.wav" => 741.94,
            "darkgrand_C6_f_rr2.wav" => 1054.56,
        )
    })
}

/// Velocity picks the dynamic layer; the seed alternates round robins, like
/// [`grand_bank`]. Voices GM 0 CC0 alt bank 4 (darkened Salamander).
pub fn darkgrand_bank(vel: u8, rr2: bool) -> &'static [Zone] {
    match (vel, rr2) {
        (0..=51, false) => darkgrand_pp(),
        (0..=51, true) => darkgrand_pp_rr2(),
        (52..=95, false) => darkgrand_mf(),
        (52..=95, true) => darkgrand_mf_rr2(),
        (_, false) => darkgrand_f(),
        (_, true) => darkgrand_f_rr2(),
    }
}

// GM 1 Bright Acoustic ALTERNATE bank 1 - FreePats YDP Grand (Yamaha Disklavier Pro,
// CC-BY 3.0, ferrosintesis-samples-ydp-grand). The BRIGHT grand: harder, more present
// hammer than the distant Salamander C5. Single-velocity (middle SF2 layer); roots
// MEASURED (the YDP is tuned ~15 cents sharp - the LA layer repitches by root).
// Selected via CC0 alt bank 1 on a GM 1 channel — not a GM 0 alternate.
fn ydpgrand_zones() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "ydpgrand_C2.wav" => 66.38,
            "ydpgrand_F#2.wav" => 93.06,
            "ydpgrand_C3.wav" => 131.75,
            "ydpgrand_F#3.wav" => 186.71,
            "ydpgrand_C4.wav" => 263.56,
            "ydpgrand_F#4.wav" => 372.67,
            "ydpgrand_C5.wav" => 530.39,
            "ydpgrand_F#5.wav" => 747.92,
            "ydpgrand_C6.wav" => 1053.83,
        )
    })
}

/// Single-velocity multisample (bright YDP grand); dynamics from the LA blend +
/// model. Voices GM 1 CC0 alt bank 1.
pub fn ydpgrand_bank(_vel: u8, _rr2: bool) -> &'static [Zone] {
    ydpgrand_zones()
}

// GM 3 Honky-tonk DEFAULT - FreePats Honky-tonk (Frances Bacon player
// piano, CC0, ferrosintesis-samples-honkytonk). The DISTINCTIVE one: a detuned/jangly
// saloon/tack attack no tuned grand can make. Single-velocity; roots MEASURED (repitch
// by root keeps the note in tune while the internal unison-beat jangle survives).
// This is GM 3's default recording (voices::make program 3), not a GM 0 alternate.
fn honkytonk_zones() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "honkytonk_C2.wav" => 66.64,
            "honkytonk_F2.wav" => 88.64,
            "honkytonk_C3.wav" => 131.73,
            "honkytonk_F#3.wav" => 186.74,
            "honkytonk_C4.wav" => 264.42,
            "honkytonk_F4.wav" => 350.12,
            "honkytonk_C5.wav" => 524.27,
            "honkytonk_F#5.wav" => 739.95,
            "honkytonk_C6.wav" => 1041.02,
        )
    })
}

/// Single-velocity multisample (honky-tonk); dynamics from the LA blend + model.
/// Voices the GM 3 DEFAULT since the 2026.07.18 re-voicing.
pub fn honkytonk_bank(_vel: u8, _rr2: bool) -> &'static [Zone] {
    honkytonk_zones()
}

// GM 0 Acoustic Grand DEFAULT (CC0=0, since 2026.07.26) - Arthur's own Yamaha B1
// acoustic UPRIGHT
// (first-party Tascam DR-05 recording, CC0-1.0, ferrosintesis-samples-b1-upright).
// A real upright, not a grand: warmer and boxier, with TWO genuinely-recorded
// timbre layers (normal/hard dynamic passes) rather than one sample re-EQ'd.
// Roots are the MEASURED first partial of each note, so it plays at exact equal
// temperament while its per-note inharmonicity and Railsback stretch ride along;
// the one exception is the hard-layer B7, whose top-octave pitch is unmeasurable,
// so its root is B7's ET frequency. The normal pass has no A0 or C8 (weak at that
// dynamic, and the ladder stops short) — `nearest()` covers those keys.
fn b1_normal_zones() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "b1_normal_C1.wav" => 31.71,
            "b1_normal_E1.wav" => 40.28,
            "b1_normal_G1.wav" => 47.86,
            "b1_normal_B1.wav" => 60.91,
            "b1_normal_D2.wav" => 72.53,
            "b1_normal_F2.wav" => 86.54,
            "b1_normal_A2.wav" => 108.90,
            "b1_normal_C3.wav" => 130.11,
            "b1_normal_E3.wav" => 163.54,
            "b1_normal_G3.wav" => 194.82,
            "b1_normal_B3.wav" => 245.03,
            "b1_normal_D4.wav" => 291.58,
            "b1_normal_F4.wav" => 347.39,
            "b1_normal_A4.wav" => 437.40,
            "b1_normal_C5.wav" => 521.81,
            "b1_normal_E5.wav" => 655.74,
            "b1_normal_G5.wav" => 782.45,
            "b1_normal_B5.wav" => 983.28,
            "b1_normal_D6.wav" => 1172.50,
            "b1_normal_F6.wav" => 1390.01,
            "b1_normal_A6.wav" => 1762.43,
            "b1_normal_C7.wav" => 2076.71,
            "b1_normal_E7.wav" => 2671.42,
            "b1_normal_G7.wav" => 3149.78,
            "b1_normal_B7.wav" => 3972.30,
        )
    })
}

fn b1_hard_zones() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "b1_hard_A0.wav" => 26.77,
            "b1_hard_C1.wav" => 31.73,
            "b1_hard_E1.wav" => 40.28,
            "b1_hard_G1.wav" => 48.03,
            "b1_hard_B1.wav" => 60.98,
            "b1_hard_D2.wav" => 72.63,
            "b1_hard_F2.wav" => 86.68,
            "b1_hard_A2.wav" => 108.93,
            "b1_hard_C3.wav" => 130.33,
            "b1_hard_E3.wav" => 163.51,
            "b1_hard_G3.wav" => 195.12,
            "b1_hard_B3.wav" => 245.29,
            "b1_hard_D4.wav" => 291.92,
            "b1_hard_F4.wav" => 347.83,
            "b1_hard_A4.wav" => 438.14,
            "b1_hard_C5.wav" => 522.30,
            "b1_hard_E5.wav" => 656.13,
            "b1_hard_G5.wav" => 782.37,
            "b1_hard_B5.wav" => 983.98,
            "b1_hard_D6.wav" => 1171.69,
            "b1_hard_F6.wav" => 1385.93,
            "b1_hard_A6.wav" => 1758.61,
            "b1_hard_C7.wav" => 2068.31,
            "b1_hard_E7.wav" => 2672.11,
            "b1_hard_G7.wav" => 3152.84,
            "b1_hard_B7.wav" => 3951.07,
            "b1_hard_C8.wav" => 4255.38,
        )
    })
}

/// Two RECORDED timbre layers (normal/hard) selected by velocity — the property
/// no other bank has: the dynamics are genuinely different captured spectra, not
/// one sample re-EQ'd. Loudness still comes from the engine's shared velocity
/// law; the layer only supplies timbre. Split: `vel < 60` normal, `>= 60` hard.
/// `rr2` is ignored (no round robins in v1). Its modeled partner retains per-note
/// phase variation; the B1-specific wrapper makes their handoff robust to that
/// changing correlation (MM-BUG-KILN-00133).
/// Voices the GM 0 DEFAULT (CC0=0) since 2026.07.26; it was the CC0=5 alternate.
///
/// A third `soft` capture was recorded and dropped (2026.07.24). Measured
/// noise-subtracted spectral tilt put it just +0.8 dB from `normal` — the same
/// timbre — while carrying 11 dB less SNR (28.1 vs 39.2 dB), so it contributed
/// audible recorder hiss and almost no tone. Removing it also took the packaged
/// bank from 9.6 MB to 6.8 MB, under the crates.io 10 MiB cap.
///
/// The split sits at 60 rather than the GM-default-straddling 64+ because the
/// two captures are far apart in the treble (+8..+25 dB above B5) and `normal`
/// is dark; a higher split leaves the bright capture unreachable for music
/// written at moderate velocities. Cost, measured over the reference corpus:
/// ~80% of piano notes land on `hard` (~51% at a split of 90).
pub fn b1upright_bank(vel: u8, _rr2: bool) -> &'static [Zone] {
    if vel < 60 {
        b1_normal_zones()
    } else {
        b1_hard_zones()
    }
}

pub fn violin_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        violin_f()
    } else {
        violin_p()
    }
}

fn viola_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "viola_C3_f.wav" => 130.50,
            "viola_G3_f.wav" => 194.96,
            "viola_D4_f.wav" => 292.40,
            "viola_A4_f.wav" => 441.08,
            "viola_E5_f.wav" => 660.40,
            "viola_B5_f.wav" => 984.52,
            "viola_D6_f.wav" => 1172.20,
        )
    })
}

fn viola_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "viola_C3_p.wav" => 130.59,
            "viola_G3_p.wav" => 196.06,
            "viola_D4_p.wav" => 292.94,
            "viola_A4_p.wav" => 438.77,
            "viola_E5_p.wav" => 659.14,
            "viola_B5_p.wav" => 989.91,
            "viola_D6_p.wav" => 1172.65,
        )
    })
}

/// GM 41 viola — its OWN dedicated onset bank (VSCO Viola Section susvib), so it no
/// longer shares the solo-violin onset (fixes the 40==41 bit-shared attack). Velocity
/// picks the dynamic layer (v1 -> p, v2 -> f), threshold as `violin_bank`.
pub fn viola_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        viola_f()
    } else {
        viola_p()
    }
}

fn marimba() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "marimba_F1.wav" => 43.68,
            "marimba_C2.wav" => 65.62,
            "marimba_G2.wav" => 98.00,
            "marimba_B2.wav" => 123.40,
            "marimba_F3.wav" => 174.45,
            "marimba_C4.wav" => 262.15,
            "marimba_G4.wav" => 391.46,
            "marimba_B4.wav" => 493.90,
            "marimba_F5.wav" => 697.02,
            "marimba_C6.wav" => 1047.88,
        )
    })
}

/// GM 12 marimba onset (VSCO-2-CE Marimba, CC0) crossfaded over the wood_bar() body.
pub fn marimba_bank() -> &'static [Zone] {
    marimba()
}

fn xylo() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "xylo_G3.wav" => 195.77,
            "xylo_C4.wav" => 264.37,
            "xylo_G4.wav" => 395.62,
            "xylo_C5.wav" => 528.10,
            "xylo_G5.wav" => 789.28,
            "xylo_C6.wav" => 1056.14,
            "xylo_G6.wav" => 1584.39,
            "xylo_C7.wav" => 2116.63,
        )
    })
}

/// GM 13 xylophone onset (VSCO-2-CE Xylo, CC0) over the wood_bar() body.
pub fn xylo_bank() -> &'static [Zone] {
    xylo()
}

fn glock() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "glock_C5.wav" => 524.98,
            "glock_G5.wav" => 773.51,
            "glock_G6.wav" => 1582.22,
            "glock_C7.wav" => 2121.85,
        )
    })
}

/// GM 9 glockenspiel onset (VSCO-2-CE Glock, CC0) over the bell() body.
pub fn glock_bank() -> &'static [Zone] {
    glock()
}

fn vibes() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "vibes_A2.wav" => 112.07,
            "vibes_C3.wav" => 129.70,
            "vibes_E3.wav" => 164.64,
            "vibes_G3.wav" => 195.90,
            "vibes_B3.wav" => 246.78,
            "vibes_D4.wav" => 293.56,
            "vibes_F4.wav" => 349.08,
            "vibes_A4.wav" => 439.95,
            "vibes_C5.wav" => 523.13,
            "vibes_E5.wav" => 659.19,
        )
    })
}

/// GM 11 vibraphone onset (VCSL Soft Mallets, CC0, -orchestral2) over the
/// bell()+motor-tremolo model. Roots MEASURED at bake (labels are sounding pitch);
/// F2 dropped (weak low-bar f0). 10 zones sound A2..E5.
pub fn vibraphone_bank() -> &'static [Zone] {
    vibes()
}

fn tubular() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "tubular_C4.wav" => 261.63,
            "tubular_D4.wav" => 293.66,
            "tubular_E4.wav" => 334.83,
            "tubular_F4.wav" => 356.35,
            "tubular_G4.wav" => 393.95,
            "tubular_A4.wav" => 441.19,
            "tubular_B4.wav" => 501.37,
            "tubular_C5.wav" => 528.56,
            "tubular_D5.wav" => 583.52,
        )
    })
}

/// GM 14 tubular bells onset (VCSL Tubular Bells 2, CC0, -orchestral2) over the
/// bell(TUBULAR) model. Roots MEASURED at bake (strike tone = label); E5/F5 dropped
/// (hum-tone octave error). 9 zones sound C4..D5.
pub fn tubular_bank() -> &'static [Zone] {
    tubular()
}

fn celesta() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "celesta_F#3.wav" => 184.77,
            "celesta_C4.wav" => 261.14,
            "celesta_F#4.wav" => 370.10,
            "celesta_C5.wav" => 523.20,
            "celesta_F#5.wav" => 739.76,
            "celesta_C6.wav" => 1052.66,
            "celesta_F#6.wav" => 1481.45,
            "celesta_C7.wav" => 2098.53,
        )
    })
}

/// GM 8 celesta onset (MS Basic SF3, MIT, -musescore) over the bell(CELESTA) model.
/// Roots MEASURED at bake near the SF3 originalPitch (all clean). 8 zones sound F#3..C7.
pub fn celesta_bank() -> &'static [Zone] {
    celesta()
}

pub fn flute_bank() -> &'static [Zone] {
    flute()
}

/// Bank for the layered brass programs (GM 56–60). Velocity picks the
/// dynamic layer (VSCO v1 → p, v3 → f, threshold as `violin_bank`).
/// 61 (section) is pure model (§2.7): no CC0 section sample exists, and
/// the old trumpet fall-through layered the WRONG instrument's attack.
pub fn brass_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        57 => {
            if f {
                trombone_f()
            } else {
                trombone_p()
            }
        }
        58 => {
            if f {
                tuba_f()
            } else {
                tuba_p()
            }
        }
        59 => {
            if f {
                mutetpt_f()
            } else {
                mutetpt_p()
            }
        }
        60 => {
            if f {
                horn_f()
            } else {
                horn_p()
            }
        }
        _ => {
            if f {
                trumpet_f()
            } else {
                trumpet_p()
            }
        }
    }
}

/// Bank for the layered reed programs (GM 68–71). Velocity picks the
/// dynamic layer (threshold as `violin_bank`); 69 (english horn) shares
/// the oboe bank — `LaVoice`'s repitch covers its lower fifth.
pub fn reed_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        70 => {
            if f {
                bassoon_f()
            } else {
                bassoon_p()
            }
        }
        71 => {
            if f {
                clarinet_f()
            } else {
                clarinet_p()
            }
        }
        _ => {
            if f {
                oboe_f()
            } else {
                oboe_p()
            }
        }
    }
}

// --- GM 64-67 saxophones: MTG.SoloSax LA layer (CC-BY 4.0) --------------------
// Per-instrument, per-dynamic zone banks; roots are the MEASURED fundamentals
// (tools/ferrosintesis-samples/prepare.py `_bake_mtg_sax`). p/f are INDEPENDENT
// zone lists picked by velocity in `sax_bank`, mirroring `reed_bank`.

fn sax_sop_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_sop_G#3_p.wav" => 209.75,
            "sax_sop_C4_p.wav" => 261.55,
            "sax_sop_E4_p.wav" => 330.82,
            "sax_sop_G#4_p.wav" => 419.59,
            "sax_sop_C5_p.wav" => 530.91,
            "sax_sop_E5_p.wav" => 665.84,
            "sax_sop_G#5_p.wav" => 843.37,
            "sax_sop_C6_p.wav" => 1069.46,
            "sax_sop_E6_p.wav" => 1329.38,
        )
    })
}

fn sax_sop_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_sop_G#3_f.wav" => 209.85,
            "sax_sop_C4_f.wav" => 261.43,
            "sax_sop_E4_f.wav" => 332.00,
            "sax_sop_G#4_f.wav" => 419.58,
            "sax_sop_C5_f.wav" => 529.13,
            "sax_sop_E5_f.wav" => 667.07,
            "sax_sop_G#5_f.wav" => 842.03,
            "sax_sop_C6_f.wav" => 1069.69,
            "sax_sop_E6_f.wav" => 1344.32,
        )
    })
}

fn sax_alt_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_alt_C#3_p.wav" => 139.90,
            "sax_alt_F3_p.wav" => 173.47,
            "sax_alt_A3_p.wav" => 219.58,
            "sax_alt_C#4_p.wav" => 277.31,
            "sax_alt_F4_p.wav" => 353.06,
            "sax_alt_A4_p.wav" => 440.99,
            "sax_alt_C#5_p.wav" => 560.01,
            "sax_alt_F5_p.wav" => 707.98,
            "sax_alt_A5_p.wav" => 890.68,
        )
    })
}

fn sax_alt_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_alt_C#3_f.wav" => 140.43,
            "sax_alt_F3_f.wav" => 174.15,
            "sax_alt_A3_f.wav" => 220.50,
            "sax_alt_C#4_f.wav" => 279.95,
            "sax_alt_F4_f.wav" => 355.08,
            "sax_alt_A4_f.wav" => 444.03,
            "sax_alt_C#5_f.wav" => 562.81,
            "sax_alt_F5_f.wav" => 710.03,
            "sax_alt_A5_f.wav" => 889.20,
        )
    })
}

fn sax_ten_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_ten_G#2_p.wav" => 104.63,
            "sax_ten_C3_p.wav" => 131.41,
            "sax_ten_E3_p.wav" => 166.22,
            "sax_ten_G#3_p.wav" => 208.67,
            "sax_ten_C4_p.wav" => 263.70,
            "sax_ten_E4_p.wav" => 332.76,
            "sax_ten_G#4_p.wav" => 419.05,
            "sax_ten_C5_p.wav" => 528.68,
            "sax_ten_E5_p.wav" => 673.20,
        )
    })
}

fn sax_ten_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_ten_G#2_f.wav" => 104.54,
            "sax_ten_C3_f.wav" => 131.32,
            "sax_ten_E3_f.wav" => 166.28,
            "sax_ten_G#3_f.wav" => 209.25,
            "sax_ten_C4_f.wav" => 263.37,
            "sax_ten_E4_f.wav" => 331.10,
            "sax_ten_G#4_f.wav" => 417.77,
            "sax_ten_C5_f.wav" => 527.47,
            "sax_ten_E5_f.wav" => 674.90,
        )
    })
}

fn sax_bar_p() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_bar_C2_p.wav" => 69.65,
            "sax_bar_E2_p.wav" => 82.52,
            "sax_bar_G#2_p.wav" => 103.47,
            "sax_bar_C3_p.wav" => 130.04,
            "sax_bar_E3_p.wav" => 163.27,
            "sax_bar_G#3_p.wav" => 208.95,
            "sax_bar_C4_p.wav" => 263.75,
            "sax_bar_E4_p.wav" => 335.01,
            "sax_bar_G#4_p.wav" => 421.23,
            "sax_bar_A4_p.wav" => 450.50,
        )
    })
}

fn sax_bar_f() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sax_bar_C2_f.wav" => 65.83,
            "sax_bar_E2_f.wav" => 82.38,
            "sax_bar_G#2_f.wav" => 103.46,
            "sax_bar_C3_f.wav" => 130.22,
            "sax_bar_E3_f.wav" => 162.90,
            "sax_bar_G#3_f.wav" => 209.52,
            "sax_bar_C4_f.wav" => 261.13,
            "sax_bar_E4_f.wav" => 334.08,
            "sax_bar_G#4_f.wav" => 420.54,
            "sax_bar_A4_f.wav" => 448.84,
        )
    })
}

/// Bank for the GM 64-67 saxophone LA layer (MTG.SoloSax, CC-BY 4.0). Velocity
/// picks the dynamic layer (same >= 80 threshold as `violin_bank`/`reed_bank`).
pub fn sax_bank(program: u8, vel: u8) -> &'static [Zone] {
    let f = vel >= 80;
    match program {
        64 => {
            if f {
                sax_sop_f()
            } else {
                sax_sop_p()
            }
        }
        66 => {
            if f {
                sax_ten_f()
            } else {
                sax_ten_p()
            }
        }
        67 => {
            if f {
                sax_bar_f()
            } else {
                sax_bar_p()
            }
        }
        _ => {
            if f {
                sax_alt_f()
            } else {
                sax_alt_p()
            }
        }
    }
}

/// Bank for the layered string sections (GM 48-49). Velocity picks the
/// dynamic layer (violin section v1 → p, v2 → f; cello section v1 → p,
/// v3 → f; threshold as `violin_bank`). Synth strings 50-51 stay pure
/// model (they are *synth* strings — HLD option A default).
pub fn strings_bank(vel: u8) -> &'static [Zone] {
    if vel >= 80 {
        strsec_f()
    } else {
        strsec_p()
    }
}

/// Bank for the layered nylon guitar (GM 24). The FreePats source has one
/// take per note — no velocity layers, no round robins — so the bank is
/// flat; `LaVoice`'s `vel_amp` still scales the transient with velocity.
pub fn guitar_bank() -> &'static [Zone] {
    nylon()
}

/// GM 25 steel-string acoustic, Martin HD28 — the CC0=2 alternate since
/// 2026.07.23 (it held the default slot until the Eastman banks landed). One
/// take per note upstream — no velocity layers, no round robins — so this is a
/// single flat layer exactly like nylon, and `LaVoice`'s `vel_amp` does the
/// dynamic scaling.
pub fn steel_bank() -> &'static [Zone] {
    steel()
}

/// GM 25 DEFAULT bank — Eastman E1D, plectrum. See [`eastpick`].
pub fn eastman_picked_bank() -> &'static [Zone] {
    eastpick()
}

/// GM 25 CC0=1 alternate — Eastman E1D, fingerstyle. See [`eastpluck`].
pub fn eastman_plucked_bank() -> &'static [Zone] {
    eastpluck()
}

/// GM 6 harpsichord — VCSL "Harpsichord, Unk" (Harpsi4), a 5-octave FF–f'''
/// plucked keyboard (CC0). One take per note upstream (single register `Main`,
/// single round robin), so the bank is flat exactly like nylon/steel and
/// `LaVoice`'s `vel_amp` scales the transient with velocity. The sample owns the
/// quill pluck; the Karplus-Strong string (`HARPSICHORD` preset) carries the
/// slow-damped jangle. Roots are the MEASURED sounding fundamentals — VCSL's file
/// labels sit an octave below sounding pitch, so the bake renames each zone to
/// its sounding pitch and measures the real f0 (roots printed by prepare.py).
fn harpsichord() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "harpsi_C2.wav" => 65.64,
            "harpsi_F2.wav" => 87.44,
            "harpsi_C3.wav" => 131.38,
            "harpsi_F3.wav" => 175.14,
            "harpsi_C4.wav" => 262.36,
            "harpsi_F4.wav" => 349.68,
            "harpsi_C5.wav" => 524.79,
            "harpsi_F5.wav" => 699.37,
            "harpsi_C6.wav" => 1045.81,
            "harpsi_F6.wav" => 1394.14,
        )
    })
}

/// GM 6 harpsichord attack bank (see [`harpsichord`]).
pub fn harpsichord_bank() -> &'static [Zone] {
    harpsichord()
}

/// GM 46 orchestral harp — VCSL "Concert Harp" (CC0, `-orchestral2` crate), forte
/// layer, ~7-semitone zones G1–F7. The sample carries the pluck onset + early ring;
/// the `Pluck(&HARP)` model keeps the bendable decay — the same LA wrap as the
/// nylon/steel guitars. Roots are the MEASURED fundamentals (the harp is tuned a few
/// cents flat; we repitch from the real f0, so the flatness never reaches the render).
fn harp() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "harp_G1.wav" => 48.47,
            "harp_D2.wav" => 73.35,
            "harp_A2.wav" => 110.11,
            "harp_E3.wav" => 164.84,
            "harp_B3.wav" => 245.33,
            "harp_F4.wav" => 348.62,
            "harp_C5.wav" => 520.04,
            "harp_G5.wav" => 779.98,
            "harp_D6.wav" => 1165.80,
            "harp_A6.wav" => 1739.41,
            "harp_F7.wav" => 2744.97,
        )
    })
}

/// GM 46 harp attack bank (see [`harp`]).
pub fn harp_bank() -> &'static [Zone] {
    harp()
}

/// GM 79 ocarina — VCSL "Ocarina, Typical" sustains (CC0, `-orchestral2`). A soft
/// near-sine vessel flute: the sample carries the breath onset and the Wind model keeps
/// the body — the same wind-onset wrap as the flute. 3 zones E4–C5 (kept under one
/// octave so the ocarina's strong 2nd harmonic can't steal the root measurement);
/// `LaVoice` repitches ±1 octave, covering ~E3–C6. Roots MEASURED.
fn ocarina() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "ocarina_E4.wav" => 329.00,
            "ocarina_G#4.wav" => 414.48,
            "ocarina_C5.wav" => 519.23,
        )
    })
}

/// GM 79 ocarina attack bank (see [`ocarina`]).
pub fn ocarina_bank() -> &'static [Zone] {
    ocarina()
}

/// GM 74 recorder — VCSL Baroque recorders (CC0, `-orchestral2`): alto lows + soprano
/// mids/highs, one combined bank F3–C6 (both are recorders, one family timbre). A wind
/// onset over the Wind model, like the flute. Roots MEASURED with a per-note tight
/// ceiling — the recorder is strongly 2f-dominant (see prepare.py `TWO_F_STRONG`), so a
/// generous ceiling would have read every zone's 2nd harmonic. `LaVoice` repitches ±1 octave.
fn recorder() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "recorder_F3.wav" => 174.67,
            "recorder_A#3.wav" => 232.62,
            "recorder_E4.wav" => 329.88,
            "recorder_A#4.wav" => 467.80,
            "recorder_E5.wav" => 659.37,
            "recorder_A#5.wav" => 937.94,
            "recorder_C6.wav" => 1051.96,
        )
    })
}

/// GM 74 recorder attack bank (see [`recorder`]).
pub fn recorder_bank() -> &'static [Zone] {
    recorder()
}

/// GM 47 timpani — VCSL "Timpani 2" single hits (CC0, `-orchestral2`). STRUCK: the
/// sample owns the mallet strike + early ring, the `timpani()` model keeps the settling
/// body. 5 zones A#1–F3, roots MEASURED — a timpani's perceived pitch is its principal
/// mode, and the recorded tuning sits up to ~47 cents off the nearest note name, so we
/// repitch from the real f0 (the note in the file name is only a label).
fn timpani() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "timpani_A#1.wav" => 57.05,
            "timpani_F2.wav" => 88.17,
            "timpani_G#2.wav" => 105.64,
            "timpani_D3.wav" => 142.91,
            "timpani_F3.wav" => 173.12,
        )
    })
}

/// GM 47 timpani attack bank (see [`timpani`]).
pub fn timpani_bank() -> &'static [Zone] {
    timpani()
}

/// GM 104 sitar — MS Basic SF3 preset 104 (MIT, `-musescore` crate). The sample owns the
/// pluck + the characteristic jawari (bridge-buzz) onset, the `Pluck(&SITAR)` model carries
/// the bendable decay and sympathetic ring. 8 zones E3–G6, roots MEASURED near the SF3
/// originalPitch. (These are single struck notes — no separate sympathetic drone in the
/// sample, which is exactly what an onset layer wants.) `LaVoice` repitches ±1 octave.
fn sitar() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "sitar_E3.wav" => 165.05,
            "sitar_G3.wav" => 196.17,
            "sitar_C4.wav" => 262.53,
            "sitar_E4.wav" => 330.02,
            "sitar_C5.wav" => 524.23,
            "sitar_E5.wav" => 659.16,
            "sitar_C6.wav" => 1049.01,
            "sitar_G6.wav" => 1587.62,
        )
    })
}

/// GM 104 sitar attack bank (see [`sitar`]).
pub fn sitar_bank() -> &'static [Zone] {
    sitar()
}

/// GM 105 banjo — a real open-back 5-string bluegrass banjo (standard open-G gDGBD),
/// recorded by Arthur (CC0, `-orchestral2`). This REPLACES the earlier sfzinstruments/ganjo
/// 6-string guitar-banjo, whose recordings were spectrally dull (99.9% of energy below ~1.5 kHz,
/// no twang) and which the LA layer used to crossfade OVER the model's already-bright onset —
/// muffling the banjo. The real 5-string carries the bright pick attack + head twang the model
/// only approximates; the `Pluck(&BANJO)` model carries the decay as before. 24 zones sounding
/// D#3–G#5 (near-chromatic — every take QC-gated for pitch-clarity, no clipping, no next-pluck
/// bleed), roots MEASURED at the true sounding pitch (file names ARE the sounding pitch — no
/// octave trap; the source's sharp fretting up the neck is captured per-root so repitch plays
/// each note in tune). Near-chromatic spacing keeps repitch stretch under a tone. `LaVoice`
/// repitches ±1 octave.
fn banjo() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "banjo_D#3.wav" => 156.43,
            "banjo_F3.wav" => 176.25,
            "banjo_G3.wav" => 196.19,
            "banjo_G#3.wav" => 209.28,
            "banjo_A3.wav" => 221.81,
            "banjo_A#3.wav" => 235.29,
            "banjo_B3.wav" => 247.19,
            "banjo_C4.wav" => 263.44,
            "banjo_D4.wav" => 293.46,
            "banjo_D#4.wav" => 314.67,
            "banjo_E4.wav" => 330.58,
            "banjo_F4.wav" => 351.26,
            "banjo_F#4.wav" => 371.23,
            "banjo_G4.wav" => 390.90,
            "banjo_G#4.wav" => 414.57,
            "banjo_A4.wav" => 440.86,
            "banjo_A#4.wav" => 468.37,
            "banjo_C5.wav" => 526.41,
            "banjo_C#5.wav" => 560.81,
            "banjo_D5.wav" => 593.49,
            "banjo_D#5.wav" => 629.48,
            "banjo_E5.wav" => 669.23,
            "banjo_G5.wav" => 805.64,
            "banjo_G#5.wav" => 850.14,
        )
    })
}

/// GM 105 banjo attack bank (see [`banjo`]).
pub fn banjo_bank() -> &'static [Zone] {
    banjo()
}

/// Mandolin pluck onsets — owner-recorded, CC0, `-mandolin` crate. Reached at GM 25 (steel
/// guitar) with bank-select LSB 96: General MIDI has no mandolin program, and GM2/GS/XG all
/// place one as a bank variation of the steel guitar. Same LA shape as the nylon/steel/banjo
/// banks — the sample owns the pick attack and the first ~0.9 s (including the double course's
/// unison shimmer, which a real pair of strings gives for free), the `Pluck` model carries the
/// decay.
///
/// Ten zones sounding G3–E6 from three hand positions: open and 5th fret on all four courses,
/// plus the 10th and 12th frets on the E course. Those positions are chosen so no two coincide
/// in pitch — the courses are a fifth apart and the frets a semitone, so open/5th and 10th/12th
/// never collide, whereas the 7th fret would have duplicated the next open string exactly.
///
/// Roots are **MEASURED, not nominal**, and here that matters more than usual: the instrument's
/// open strings are in tune (within a few cents) but its fretted notes run sharp — up to
/// **+22 cents** at the 5th fret on the thickest course — so nominal pitches would detune every
/// fretted zone. `LaVoice` repitches ±1 octave from the measured root.
///
/// **One dynamic, four ROUND ROBINS.** A mandolin cannot be played at meaningfully different
/// dynamics (the owner's own finding, and a recorded 3-dynamic take measured out: the loud and
/// normal passes' spectral centroids were indistinguishable — 6/10 sign consistency, median
/// shift +0.09 harmonics). The recording budget therefore buys take VARIETY instead of dynamic
/// layers: four separate plucks of every note, so a repeated note does not replay byte-identical
/// PCM.
///
/// **The four takes are ordered, and the order is meaningful** — they were played
/// down/up/down/up, so cycling them strictly (never randomly) reproduces a real player's
/// alternating pick direction. `rr1` is the earliest of the four.
///
/// Take-to-take root spread is ~2–5 cents, i.e. the same note played four times, not four
/// different notes.
fn mandolin_rr1() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mandolin_G3_rr1.wav" => 195.57,
            "mandolin_C4_rr1.wav" => 264.95,
            "mandolin_D4_rr1.wav" => 292.93,
            "mandolin_G4_rr1.wav" => 394.37,
            "mandolin_A4_rr1.wav" => 440.41,
            "mandolin_D5_rr1.wav" => 591.60,
            "mandolin_E5_rr1.wav" => 658.52,
            "mandolin_A5_rr1.wav" => 883.17,
            "mandolin_D6_rr1.wav" => 1182.91,
            "mandolin_E6_rr1.wav" => 1328.92,
        )
    })
}

/// Mandolin take 2 — an up-stroke (see [`mandolin_rr1`]).
fn mandolin_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mandolin_G3_rr2.wav" => 195.74,
            "mandolin_C4_rr2.wav" => 264.82,
            "mandolin_D4_rr2.wav" => 292.65,
            "mandolin_G4_rr2.wav" => 395.11,
            "mandolin_A4_rr2.wav" => 439.28,
            "mandolin_D5_rr2.wav" => 591.17,
            "mandolin_E5_rr2.wav" => 656.88,
            "mandolin_A5_rr2.wav" => 883.72,
            "mandolin_D6_rr2.wav" => 1181.88,
            "mandolin_E6_rr2.wav" => 1328.13,
        )
    })
}

/// Mandolin take 3 (see [`mandolin_rr1`]).
fn mandolin_rr3() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mandolin_G3_rr3.wav" => 195.84,
            "mandolin_C4_rr3.wav" => 264.59,
            "mandolin_D4_rr3.wav" => 293.03,
            "mandolin_G4_rr3.wav" => 394.68,
            "mandolin_A4_rr3.wav" => 440.40,
            "mandolin_D5_rr3.wav" => 591.36,
            "mandolin_E5_rr3.wav" => 657.51,
            "mandolin_A5_rr3.wav" => 882.60,
            "mandolin_D6_rr3.wav" => 1181.48,
            "mandolin_E6_rr3.wav" => 1327.97,
        )
    })
}

/// Mandolin take 4 (see [`mandolin_rr1`]).
fn mandolin_rr4() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "mandolin_G3_rr4.wav" => 195.61,
            "mandolin_C4_rr4.wav" => 264.64,
            "mandolin_D4_rr4.wav" => 293.33,
            "mandolin_G4_rr4.wav" => 394.98,
            "mandolin_A4_rr4.wav" => 439.17,
            "mandolin_D5_rr4.wav" => 590.84,
            "mandolin_E5_rr4.wav" => 656.93,
            "mandolin_A5_rr4.wav" => 883.22,
            "mandolin_D6_rr4.wav" => 1181.42,
            "mandolin_E6_rr4.wav" => 1327.72,
        )
    })
}

/// How many round-robin takes the mandolin bank carries. `LaVoice` treats a bank with
/// `> 1` round robin as rotatable — that is what unlocks replaying the sampled attack on
/// every tremolo stroke instead of suppressing it.
pub const MANDOLIN_ROUND_ROBINS: usize = 4;

/// Mandolin attack bank, round-robin selected (see [`mandolin_rr1`]). `rr` is a strike
/// counter, not a random draw: cycling in order reproduces the recorded pick alternation.
pub fn mandolin_bank(rr: usize) -> &'static [Zone] {
    match rr % MANDOLIN_ROUND_ROBINS {
        0 => mandolin_rr1(),
        1 => mandolin_rr2(),
        2 => mandolin_rr3(),
        _ => mandolin_rr4(),
    }
}

/// GM 75 pan flute — MS Basic SF3 preset 75 (MIT, `-musescore`). A wind onset over the Wind
/// model, like the flute. 8 zones F#3–C7 (roots MEASURED; the SF3 zones have mixed sample
/// rates, resampled to 44.1 kHz at bake). `LaVoice` repitches ±1 octave.
fn panflute() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "panflute_F#3.wav" => 184.12,
            "panflute_C4.wav" => 261.21,
            "panflute_F#4.wav" => 368.91,
            "panflute_C5.wav" => 523.07,
            "panflute_F#5.wav" => 740.14,
            "panflute_C6.wav" => 1046.07,
            "panflute_F#6.wav" => 1478.67,
            "panflute_C7.wav" => 2092.01,
        )
    })
}

/// GM 75 pan flute attack bank (see [`panflute`]).
pub fn panflute_bank() -> &'static [Zone] {
    panflute()
}

/// GM 76 blown bottle — MS Basic SF3 preset 76 (MIT, `-musescore`). The SF3 preset has a
/// SINGLE sample (C6), so the onset engages only within ~1 octave of C6 (the `LaVoice` clamp)
/// and falls back to the modeled bottle elsewhere — thin, but a real breath onset near range.
fn bottle() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, bank!("bottle_C6.wav" => 1056.51))
}

/// GM 76 blown bottle attack bank (see [`bottle`]).
///
/// RETIRED as a render route: GM 76 now plays [`bottle_loop_voice`] (the whole-voice
/// `-bottle` recording), so no voice reaches this bank. It stays embedded and public
/// because the crate is published; do not read its presence as evidence it is live.
pub fn bottle_bank() -> &'static [Zone] {
    bottle()
}

/// GM 77 shakuhachi — MS Basic SF3 preset 77 (MIT, `-musescore`). A SINGLE sample (C5), same
/// single-zone caveat as the blown bottle: the onset engages within ~1 octave of C5.
fn shakuhachi() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, bank!("shakuhachi_C5.wav" => 521.06))
}

/// GM 77 shakuhachi attack bank (see [`shakuhachi`]).
pub fn shakuhachi_bank() -> &'static [Zone] {
    shakuhachi()
}

// --- GM 109 sampled bagpipe: looped drone + chanter (HLD 2026.07.17) ---------
//
// These are LOOPED sustains: `LoopVoice` plays the whole baked WAV on an endless
// modulo wrap. The bake (prepare.py `extract_loop` / `find_loop`) makes the seam
// continuous, so no runtime crossfade / loop metadata is needed — `Zone` is
// untouched. Roots are the MEASURED fundamentals (the pipe is ~30-50 cents flat;
// we repitch from the real f0 so the flatness never reaches the render).
//
// The buffers are SHORT (~60-145 ms) and span a WHOLE number of pitch periods.
// Both matter, and the first bake got both wrong (2026.07.20): a fractional period
// count wraps the harmonics out of phase, and a long window cannot avoid the reed's
// own level/timbre drift — together they clicked once per loop at ~2.5 Hz. The bake
// now scores candidates by the real wrap discontinuity against the source's
// continuation; `looped_sustain_banks_are_loopable` pins both properties here.

/// GM 109 chanter RR1: every loopable `_31` take in the archive — 10 zones
/// F4–G5 at ≤2-semitone spacing except the D5→F#5 hole (D#5/E5/F5 fail the
/// −14 dB wrap gate in both takes; see prepare.py `BAGPIPE_SOURCES`).
fn chanter() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "chanter_F4.wav" => 341.37,
            "chanter_G4.wav" => 383.74,
            "chanter_A4.wav" => 432.55,
            "chanter_A#4.wav" => 454.57,
            "chanter_B4.wav" => 481.39,
            "chanter_C5.wav" => 512.01,
            "chanter_C#5.wav" => 538.52,
            "chanter_D5.wav" => 578.53,
            "chanter_F#5.wav" => 716.27,
            "chanter_G5.wav" => 771.47,
        )
    })
}

/// GM 109 chanter RR2: the five loopable `_32` takes. An odd note seed plays
/// this bank (MM-REQ-KILN-00025) — real per-note take variation; keys outside
/// A4–D5 repitch a touch further here, still inside the 0.5–2.0 clamp.
fn chanter_rr2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "chanter_A4_rr2.wav" => 431.28,
            "chanter_A#4_rr2.wav" => 454.56,
            "chanter_B4_rr2.wav" => 482.11,
            "chanter_C5_rr2.wav" => 512.34,
            "chanter_D5_rr2.wav" => 578.09,
        )
    })
}

/// GM 109 bass drone (single recorded G2). One zone — `nearest` always returns it.
fn drone_g2() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, bank!("drone_G2.wav" => 98.22))
}

/// GM 109 tenor drone (single recorded G3).
fn drone_g3() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, bank!("drone_G3.wav" => 196.21))
}

pub fn chanter_bank() -> &'static [Zone] {
    chanter()
}
pub fn drone_g2_bank() -> &'static [Zone] {
    drone_g2()
}
pub fn drone_g3_bank() -> &'static [Zone] {
    drone_g3()
}

/// A looped-sample voice: plays the whole (baked-seamless) sample on an endless
/// modulo wrap under an `Adsr` amp envelope. Unlike `LaVoice` there is NO model
/// underneath — the sample IS the sound, indefinitely (a bagpipe never decays).
/// It deliberately does NOT implement `set_pitch`: GM 109 is in `vibrato_family`,
/// and the engine calls `set_pitch` on every voice on the channel; the no-op
/// default keeps CC1/bend from warbling the fixed-pitch pipe (matching the
/// modeled drone, which is immune by the same omission).
pub struct LoopVoice {
    data: &'static [f32],
    /// f64 — NOT f32. The read phase is an accumulator that climbs to `n` and
    /// resets at every wrap, so an f32 `pos` makes its rounding error a sawtooth
    /// at exactly the loop rate: measured across a 0.4 s loop the per-step error
    /// RMS ramped 28x (29 dB) from wrap to wrap, lifting the sidebands on a 5 kHz
    /// partial from -97 dB to -68 dB. That is loop-synchronous noise — the very
    /// artifact this voice must not have — for no benefit, since `data` is short
    /// and the arithmetic is off the hot path's critical chain.
    pos: f64,
    step: f64,
    gain: f32,
    env: crate::dsp::Adsr,
    /// Slow bounded read-rate random walk (MM-REQ-KILN-00026): the same
    /// `SAX_DRIFT_MAX` ±0.22 % walk `SaxLoopVoice` runs "to defeat the
    /// loop-tell" — at the ~65 ms chanter loops (~15 wraps/s) a static rate
    /// is the one residual periodicity cue. Rate only: constant amplitude is
    /// the instrument (bp_o1 pins it).
    drift: f32,
    drift_target: f32,
    t: u32,
    rng: crate::dsp::Rng,
    #[cfg(test)]
    name: &'static str,
}

impl LoopVoice {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        zones: &'static [Zone],
        target_hz: f32,
        sr: f32,
        gain: f32,
        attack: f32,
        release: f32,
        seed: u32,
        #[cfg_attr(not(test), allow(unused_variables))] name: &'static str,
    ) -> Self {
        let zone = nearest(zones, target_hz);
        // Clamp the PITCH RATIO (the coverage guard — no model fallback exists),
        // THEN apply sample-rate conversion. Never clamp the combined value: at
        // 96 kHz a unison note would clamp 0.459 -> 0.5 and read 147 cents sharp
        // (Codex review).
        let ratio = (target_hz / zone.root).clamp(0.5, 2.0);
        let step = (ratio * 44100.0 / sr) as f64;
        LoopVoice {
            data: zone.data.as_slice(),
            pos: 0.0,
            step,
            gain,
            env: crate::dsp::Adsr::new(attack, 0.0, 1.0, release, sr),
            drift: 0.0,
            drift_target: 0.0,
            t: 0,
            rng: crate::dsp::Rng::new(seed ^ 0xBA6_71FE),
            #[cfg(test)]
            name,
        }
    }
}

impl Voice for LoopVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        for o in out.iter_mut() {
            let e = self.env.next();
            let j = self.pos as usize;
            let frac = (self.pos - j as f64) as f32;
            // WRAPPED 4-point cubic neighbours — load-bearing: a one-shot
            // player's `data[j±k]` would read out of bounds / a wrong sample at
            // the loop seam and click once per loop. Cubic (not linear) keeps the
            // drone's treble when the pipe is repitched off its zone root.
            let v = crate::dsp::cubic4(
                self.data[(j + n - 1) % n],
                self.data[j],
                self.data[(j + 1) % n],
                self.data[(j + 2) % n],
                frac,
            );
            *o += v * self.gain * e;
            // Slow bounded drift walk on the read rate (shared constants with
            // the sax voice — same idiom, same bounds).
            if self.t.is_multiple_of(SAX_DRIFT_SAMP) {
                self.drift_target = SAX_DRIFT_MAX * self.rng.white();
            }
            self.drift += 0.002 * (self.drift_target - self.drift);
            self.t = self.t.wrapping_add(1);
            self.pos += self.step * (1.0 + self.drift) as f64;
            if self.pos >= n as f64 {
                self.pos -= n as f64;
            }
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        self.name
    }
}

/// GM 109 sampled chanter. Constant amplitude (velocity ignored — constant bag
/// pressure), ~10 ms attack, 0.11 s release (mirrors the modeled chanter env).
pub fn bagpipe_chanter_loop(key: u8, sr: f32, seed: u32) -> LoopVoice {
    // Odd seeds take the RR2 bank (the archive's `_32` takes): deterministic
    // per-note round-robin against machine-gunning, no level step (both banks
    // bake to the same target RMS).
    let bank = if seed & 1 == 1 {
        chanter_rr2()
    } else {
        chanter()
    };
    LoopVoice::new(
        bank,
        key_freq(key),
        sr,
        BAGPIPE_CHANTER_GAIN,
        0.010,
        0.11,
        seed,
        "bagpipe_chanter",
    )
}

/// Output gains for the sampled bagpipe. Samples are baked to a common RMS
/// (prepare.py `BAGPIPE_TARGET_RMS`), so these set the MIX: the chanter ~2x the
/// drone stack, mirroring the modeled 0.154 : 0.075. `DRONE` is per-loop (bass +
/// tenor sum to roughly this given their octave-incoherent content).
pub const BAGPIPE_CHANTER_GAIN: f32 = 0.85;
pub const BAGPIPE_DRONE_GAIN: f32 = 0.30;

pub fn prewarm() {
    if !crate::embedded_samples_available() {
        return;
    }
    // Each package owns an independent OnceLock cache. Use the packages' explicit
    // hooks so a bank move never masquerades as a shared cache.
    #[cfg(feature = "embedded-samples")]
    {
        ferrosintesis_samples_drumkit::prewarm();
        ferrosintesis_samples_drumkit2::prewarm();
    }
    // Piano-shaped banks fan out over (velocity layer x round-robin), so touching one
    // combination leaves the rest to decode inside the audio callback. Cover the grid.
    for &(vel, rr2) in &[
        (1u8, false),
        (1, true),
        (80, false),
        (80, true),
        (127, false),
        (127, true),
    ] {
        let _ = piano_bank(vel, rr2);
        let _ = grand_bank(vel, rr2);
        let _ = steinwayb_bank(vel, rr2);
        let _ = kawai_bank(vel, rr2);
        let _ = headroom_bank(vel, rr2);
        let _ = musescoregrand_bank(vel, rr2);
        let _ = darkgrand_bank(vel, rr2);
        let _ = ydpgrand_bank(vel, rr2);
        let _ = honkytonk_bank(vel, rr2);
        let _ = b1upright_bank(vel, rr2);
    }

    // Banks split into a soft and a loud layer.
    for vel in [1u8, 127] {
        let _ = violin_bank(vel);
        let _ = viola_bank(vel);
        let _ = cello_bank(vel);
        let _ = contrabass_bank(vel);
        let _ = strings_bank(vel);
    }

    // The mandolin is ONE dynamic and four round robins, so it fans out over
    // takes rather than velocity layers.
    for rr in 0..MANDOLIN_ROUND_ROBINS {
        let _ = mandolin_bank(rr);
    }

    for program in 56..=60 {
        let _ = brass_bank(program, 1);
        let _ = brass_bank(program, 127);
    }
    for program in [68, 70, 71] {
        let _ = reed_bank(program, 1);
        let _ = reed_bank(program, 127);
    }
    for program in 64..=67 {
        let _ = sax_bank(program, 1);
        let _ = sax_bank(program, 127);
    }

    let _ = marimba_bank();
    let _ = xylo_bank();
    let _ = glock_bank();
    let _ = vibraphone_bank();
    let _ = tubular_bank();
    let _ = celesta_bank();
    let _ = musicbox_bank();
    let _ = flute_bank();
    let _ = guitar_bank();
    let _ = steel_bank();
    let _ = eastman_picked_bank();
    let _ = eastman_plucked_bank();
    let _ = harp_bank();
    let _ = ocarina_bank();
    let _ = recorder_bank();
    let _ = timpani_bank();
    let _ = sitar_bank();
    let _ = banjo_bank();
    let _ = panflute_bank();
    let _ = bottle_bank();
    let _ = shakuhachi_bank();
    let _ = chanter_bank();
    let _ = drone_g2_bank();
    let _ = drone_g3_bank();
    let _ = clavinet_bank();
    let _ = harpsichord_bank();
    let _ = rhodes_bank();
    let _ = dulcimer_bank();
    let _ = pizzbass_bank();
    let _ = finger_bass_bank();
    let _ = pick_bass_bank();

    // Whole-voice LOOPED-SUSTAIN zones (GM 64-67 sax, GM 76 blown bottle). Decoding the
    // bank is only half the setup: `SaxLoopVoice::new` / `BottleLoopVoice::new` also need
    // the zone's pitch-synchronous loop bounds, and finding those scans the static PCM
    // (67.4 M multiply-accumulates for the bottle's 72,765-frame recording). Resolve every
    // zone's loop here, so no NoteOn ever runs that search inside the audio callback
    // (MM-BUG-KILN-00064). `bottle_loop_bank` is the ACTIVE GM 76 route; the `bottle_bank`
    // onset bank above is the retired one and is prewarmed separately.
    for program in 64..=67 {
        for vel in [1u8, 127] {
            for zone in sax_bank(program, vel) {
                let _ = zone.sustain_loop(find_sax_loop);
            }
        }
    }
    for zone in bottle_loop_bank() {
        let _ = zone.sustain_loop(find_bottle_loop);
    }

    // Caches with no public `*_bank` wrapper, which is exactly why they were missed
    // (MM-BUG-KILN-00073): `chanter_rr2` is reached only by an odd note seed, and the
    // rain bed and the gong's dynamic layer pair are not `Zone` banks at all. Each still
    // decodes megabytes of PCM on whichever thread reaches it first.
    #[cfg(feature = "embedded-samples")]
    {
        let _ = chanter_rr2();
        let _ = rain_loop();
        let _ = gong_layers();
        let _ = fret_noise_takes();
    }
}

fn nearest(zones: &'static [Zone], f: f32) -> &'static Zone {
    &zones[nearest_idx(zones, f)]
}

/// [`nearest`] as an INDEX. Round-robin rotation needs the index rather than the
/// reference: every take-set covers the same pitches (a few cents apart at most),
/// so holding the index guarantees a restrike rotates to another take of the SAME
/// zone rather than re-running the pitch search against slightly different roots.
fn nearest_idx(zones: &[Zone], f: f32) -> usize {
    zones
        .iter()
        .enumerate()
        .min_by(|(_, a), (_, b)| {
            let da = (a.root / f).ln().abs();
            let db = (b.root / f).ln().abs();
            da.partial_cmp(&db).unwrap()
        })
        .map(|(i, _)| i)
        .unwrap()
}

#[inline]
fn smooth(x: f32) -> f32 {
    let x = x.clamp(0.0, 1.0);
    x * x * (3.0 - 2.0 * x)
}

/// Per-program DSP of a SHARED sample inside the sample-owned window
/// (round-3 U3, plan §3.1). GM 0/1/3 wrap one piano bank at one gain, so
/// every model-layer differentiator was discarded exactly where the ear
/// decides "piano identity" — the fix processes the existing sample
/// per-program instead (zero new assets). Default-inert: `LaFx::default()`
/// takes none of the branches below, so every other wrapped program
/// renders byte-identically (the render-diff inventory is the guard).
#[derive(Clone, Copy, Default)]
pub struct LaFx {
    /// The wrapped model's `vel_sense`, when it is velocity-COMPRESSED (< 1.0).
    ///
    /// The sampled onset must follow the same velocity law as the body it fades
    /// into, and for a compressed model that law squares a compressed velocity —
    /// see the `vel_gain` site. `None` = the model uses the plain global law, so the
    /// onset does too. Only GM 6 sets it (MM-BUG-KILN-00030).
    pub vel_sense: Option<f32>,
    /// One-pole high-shelf on the sample readout: (gain_db, corner_hz).
    /// GM 1 Bright's hammer-band brightness, moved INTO the sampled onset.
    pub shelf: Option<(f32, f32)>,
    /// Two extra detuned reads of the same sample: (ratio_a, ratio_b, mix).
    /// GM 3 Honky's trichord beat, starting AT the onset. The side reads
    /// begin 5/9 ms into the zone so the hammer transient stays singular
    /// (per-read phase decorrelation — the §3.1 comb/flange watch) while
    /// their continuously-diverging phase makes true f0-band beating.
    pub detune: Option<(f32, f32, f32)>,
    /// Velocity-tracking one-pole lowpass on the sample readout: base corner
    /// (Hz). The guitar arms author this so the sampled onset darkens with a
    /// soft pick the way the model's own excitation does (its pick_lp scales
    /// by 0.10 + 1.30·vn) — without it the sample plays full brightness at
    /// every velocity and the crossfade seam mismatches (guitar-realism HLD
    /// §4). EXACT bypass — no filter state touched, no per-sample cost — at
    /// vel ≥ 100: the LA oracle fixtures all render there.
    pub vel_lp: Option<f32>,
}

/// Velocity→corner law for [`LaFx::vel_lp`]: mirrors the model's excitation
/// brightness shape; returns the one-pole coefficient, 0.0 = hard bypass.
fn vel_lp_alpha(base_hz: f32, vel: u8, sr: f32) -> f32 {
    if vel >= 100 {
        return 0.0;
    }
    let vn = vel as f32 / 127.0;
    let corner = base_hz * (0.10 + 1.30 * vn);
    1.0 - (-std::f32::consts::TAU * corner / sr).exp()
}

/// Per-note stochastic onset variation (guitar-realism HLD §4). Every draw
/// comes ONCE from the voice seed at wrap time — same seed ⇒ bit-identical
/// note; the engine's per-voice seed decorrelates repeats. Consumed only by
/// [`LaVoice::wrap_var`] (the two acoustic-guitar arms): every other LA
/// caller keeps the jitter-free path by construction, so non-guitar
/// bit-identity needs no runtime branch at all.
#[derive(Clone, Copy)]
pub struct OnsetVar {
    /// Full span of the 5 detune strata, in cents (values sit at ±half).
    /// The offset is LOCKED: applied to the sample step AND composed into
    /// every model pitch update, so the pair cannot beat through the
    /// crossfade (HLD §4, review D7/C3).
    pub detune_strata_c: f32,
    /// Additional white detune, ± cents.
    pub detune_white_c: f32,
    /// Max onset delay, seconds (uniform in [0, max)). With gain jitter,
    /// this carries most of the transient decorrelation — rate jitter is
    /// pitch-bounded on a pitched instrument (HAT lesson). One-sided
    /// (always late) by causality: a voice cannot start before its
    /// note-on; composers own anticipation.
    pub onset_max_s: f32,
    /// Strike-level jitter, ± fraction.
    pub gain_frac: f32,
}

/// The acoustic guitars' variation: an intonation-scale musical budget
/// (±5 c strata + ±1 c white ≈ ±6 c max — real fretted-intonation scatter,
/// NOT the ±45 c pitch-integrity tolerance, which is a detection bound; it
/// must also clear the ±15 c O-PITCH lattice bar stacked on the model's own
/// few-cent tuning residue), 0–6 ms pick-timing scatter, ±6 % level. The
/// transient decorrelation is carried by onset+gain (HAT lesson) — detune
/// is intonation colour, not the anti-machine-gun lever.
pub const GUITAR_VAR: OnsetVar = OnsetVar {
    detune_strata_c: 10.0,
    detune_white_c: 1.0,
    onset_max_s: 0.006,
    gain_frac: 0.06,
};

/// Sampled attack + modeled sustain, under the §2.7 onset-ownership
/// contract — one owner per instant:
///
/// - `[0, fade_start)`: the SAMPLE owns the onset. The wrapped model runs
///   from note-start (envelopes, filters, KS loop age naturally) but its
///   output is DISCARDED — no doubled attack, no hand-authored start state.
/// - `[fade_start, fade_end)`: one sum-to-one crossfade sample→model. A
///   sample and a model at the same pitch are CORRELATED, so an equal-power
///   law can boost or cancel at the midpoint; complementary weights keep
///   the sum level-true through the seam (verified by `la_level_continuity`
///   across every wrapped program).
/// - `[fade_end, ∞)`: the MODEL owns the sustain.
///
/// [`LaVoice::wrap_release_b1`] is the one measured exception: that recording
/// decays faster and can be strongly anti-correlated with its randomized model
/// during the handoff, so it phase-corrects the sample, overlaps a slightly
/// earlier model ramp, and normalizes destructive overlap from a local
/// correlation estimate. Every general wrapper retains the one-owner contract.
pub struct LaVoice {
    sustain: Box<dyn Voice>,
    zone: &'static Zone,
    pos: f32,
    step: f32,
    base_step: f32,
    /// The musical repitch ratio `target_hz / zone.root` that produced `base_step`,
    /// kept free of the `44100 / sr` output-clock conversion.
    ///
    /// Eligibility is a property of the PITCH, not of the output rate, so the
    /// `0.5..=2.05` window must be applied to this and never to `base_step`
    /// (MM-BUG-KILN-00061). Held on the struct because [`LaVoice::retrigger`] has to
    /// re-check the window against a different zone root and cannot recover the ratio
    /// from `base_step` without knowing `sr`.
    base_ratio: f32,
    gain: f32,
    rel_gain: f32,
    rel_mul: f32,
    rel_t60_mul: f32,
    t: usize,
    fade_start: usize,
    fade_end: usize,
    /// Shape the B1 handoff for its measured phase and decay mismatch: invert
    /// the sample polarity, let the model rise from note start, and normalize
    /// destructive overlap from a local energy/correlation estimate. The
    /// polarity flip is inaudible for the isolated onset; the adaptive
    /// normalization makes the overlap independent of the randomized model
    /// phase (MM-BUG-KILN-00130/00133).
    b1_phase_robust_fade: bool,
    /// Local raw sample/model energy and cross-correlation for the B1-only
    /// phase-robust handoff. Raw owner signals are tracked so the compensation
    /// is exactly unity when either crossfade weight reaches zero.
    b1_sample_power: f32,
    b1_model_power: f32,
    b1_cross_power: f32,
    b1_power_alpha: f32,
    /// Separate modeled rise endpoint. The B1 wrapper preserves the established
    /// 10%-faster rise over keys 36-50, where it keeps the recorded piano
    /// distinct, and brings the model in before sample retirement elsewhere.
    b1_model_fade_end: usize,
    /// B1 freezes its handoff weights at key-up so equal-rate damper decay
    /// cannot be distorted by a moving sample/model ratio during the gap.
    fade_hold: Option<usize>,
    buf: Vec<f32>,
    fx: LaFx,
    /// Detuned side-read positions (source-rate samples).
    pos2: f32,
    pos3: f32,
    /// High-shelf state/coefficients (one-pole: v + g·(v − lp(v))).
    shelf_lp: f32,
    shelf_a: f32,
    shelf_g: f32,
    /// Locked per-note detune (guitar-realism HLD §4): composed into every
    /// model pitch update so sample and model can never beat apart. 1.0 for
    /// every non-`wrap_var` caller.
    var_mult: f32,
    /// Onset-delay jitter in output samples (0 for non-`wrap_var` callers).
    start: usize,
    /// Velocity-brightness one-pole state + coefficient (0.0 = bypass).
    vel_lp: f32,
    vel_lp_a: f32,
    /// End-of-zone taper length in OUTPUT samples (0.0 = off, the
    /// non-`wrap_var` default): fades the sample out as the read approaches
    /// the zone's last frames so a dry-out at any sample rate degrades
    /// gracefully instead of stepping (review C8).
    end_taper: f32,
    /// Round-robin rotation state — `Some` ONLY for banks carrying more than one
    /// take. Its presence is what licenses [`LaVoice::retrigger`] to replay the
    /// sampled attack on a tremolo stroke instead of suppressing it; every
    /// single-take bank keeps `None` and therefore keeps the original behaviour
    /// bit-identically. See the retrigger doc comment for why that scoping is
    /// load-bearing.
    rr: Option<RoundRobin>,
}

/// Result of attempting to layer an LA sample over a modeled sustain.
///
/// Most callers only need [`LaVoiceBuild::voice`]. Voice construction also uses
/// [`LaVoiceBuild::used_sample`] to select the velocity calibration for the
/// voice that was actually built: an extreme-repitch fallback is the bare model
/// even when samples were requested.
pub(crate) struct LaVoiceBuild {
    pub(crate) voice: Box<dyn Voice>,
    pub(crate) used_sample: bool,
}

/// Which take a round-robin bank is currently playing, and how to reach the next.
#[derive(Clone, Copy)]
struct RoundRobin {
    /// The bank accessor (e.g. [`mandolin_bank`]); takes an index, wraps internally.
    bank: fn(usize) -> &'static [Zone],
    /// How many distinct takes the bank carries (> 1 by construction).
    takes: usize,
    /// The pitch zone this voice selected at note-on. Held as an INDEX so a
    /// restrike rotates takes of the same zone (see [`nearest_idx`]).
    zone_idx: usize,
    /// The take currently sounding.
    idx: usize,
}

pub(crate) const DEFAULT_LA_RELEASE_T60: f32 = 0.06;
/// Fixed weak-coherence target for the B1 overlap power. The cross term is
/// `2ρab√(PsPm)`, so 0.60 means ρ=0.30: neither a fully coherent boost nor an
/// uncorrelated power dip.
const B1_TARGET_CROSS_COEFF: f32 = 0.60;

impl LaVoice {
    /// Wrap `sustain`; falls back to the bare model when the target is too
    /// far outside the sampled range for a credible repitch.
    pub fn wrap(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> Box<dyn Voice> {
        Self::wrap_classified(sustain, zones, key, vel, sr, gain, fade).voice
    }

    /// [`Self::wrap`] plus whether the sample layer was actually constructed.
    ///
    /// A `false` result means the pitch was outside the credible repitch range
    /// and [`LaVoice::build`] returned the bare modeled sustain.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn wrap_classified(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> LaVoiceBuild {
        Self::wrap_fx_classified(sustain, zones, key, vel, sr, gain, fade, LaFx::default())
    }

    /// [`Self::wrap`] for a bank that carries several ROUND-ROBIN takes.
    ///
    /// `bank(i)` returns take `i` (wrapping internally); `takes` is how many there
    /// are; `rr` is the engine's per-`(channel, key)` strike counter, so the first
    /// take of a fresh note follows the recorded order rather than a random draw.
    ///
    /// Unlike every other wrapper this arms tremolo-stroke rotation: see
    /// [`LaVoice::retrigger`]. With `takes < 2` it degrades to a plain
    /// [`Self::wrap`], so it is safe to call from a voice whose bank may not have
    /// round robins.
    #[allow(clippy::too_many_arguments)] // wrap()'s shape + the round-robin trio
    pub fn wrap_rr(
        sustain: Box<dyn Voice>,
        bank: fn(usize) -> &'static [Zone],
        takes: usize,
        rr: u8,
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> Box<dyn Voice> {
        match Self::build_rr(sustain, bank, takes, rr, key, vel, sr, gain, fade) {
            Ok(la) => Box::new(la),
            Err(model) => model,
        }
    }

    /// [`Self::wrap_rr`]'s body, kept concrete so the rotation oracle can inspect
    /// the resulting voice's state directly instead of inferring it from audio.
    #[allow(clippy::too_many_arguments)]
    fn build_rr(
        sustain: Box<dyn Voice>,
        bank: fn(usize) -> &'static [Zone],
        takes: usize,
        rr: u8,
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
    ) -> Result<LaVoice, Box<dyn Voice>> {
        let idx = (rr as usize) % takes.max(1);
        let zones = bank(idx);
        let zone_idx = nearest_idx(zones, key_freq(key));
        let mut la = Self::build(
            sustain,
            zones,
            key,
            vel,
            sr,
            gain,
            fade,
            LaFx::default(),
            DEFAULT_LA_RELEASE_T60,
        )?;
        if takes >= 2 {
            la.rr = Some(RoundRobin {
                bank,
                takes,
                zone_idx,
                idx,
            });
        }
        Ok(la)
    }

    /// [`Self::wrap`] with per-program sample DSP (round-3 U3). Only the
    /// GM 0-3 piano arm passes a non-default `fx`.
    #[allow(clippy::too_many_arguments)] // mirrors wrap()'s established shape + one fx
    pub fn wrap_fx(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        fx: LaFx,
    ) -> Box<dyn Voice> {
        Self::wrap_fx_classified(sustain, zones, key, vel, sr, gain, fade, fx).voice
    }

    #[allow(clippy::too_many_arguments)]
    fn wrap_fx_classified(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        fx: LaFx,
    ) -> LaVoiceBuild {
        match Self::build(
            sustain,
            zones,
            key,
            vel,
            sr,
            gain,
            fade,
            fx,
            DEFAULT_LA_RELEASE_T60,
        ) {
            Ok(la) => LaVoiceBuild {
                voice: Box::new(la),
                used_sample: true,
            },
            Err(model) => LaVoiceBuild {
                voice: model,
                used_sample: false,
            },
        }
    }

    /// [`Self::wrap`] with an explicit note-off release time. This is a narrow
    /// opt-in for voices whose recorded attack needs a longer key-up bridge;
    /// every existing wrapper keeps [`DEFAULT_LA_RELEASE_T60`].
    #[allow(clippy::too_many_arguments)]
    pub fn wrap_release(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        release_t60: f32,
    ) -> Box<dyn Voice> {
        match Self::build(
            sustain,
            zones,
            key,
            vel,
            sr,
            gain,
            fade,
            LaFx::default(),
            release_t60,
        ) {
            Ok(la) => Box::new(la),
            Err(model) => model,
        }
    }

    /// B1-upright-specific release wrapper with its measured phase-robust
    /// handoff. Crate-private so this exceptional blend is not a general API.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn wrap_release_b1(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        release_t60: f32,
    ) -> Box<dyn Voice> {
        match Self::build(
            sustain,
            zones,
            key,
            vel,
            sr,
            gain,
            fade,
            LaFx::default(),
            release_t60,
        ) {
            Ok(mut la) => {
                la.b1_phase_robust_fade = true;
                if (36..=50).contains(&key) {
                    la.b1_model_fade_end = la.fade_end - (la.fade_end - la.fade_start) / 10;
                }
                Box::new(la)
            }
            Err(model) => model,
        }
    }

    /// [`Self::wrap_fx`] plus per-note onset variation (guitar-realism HLD
    /// §4) — the two acoustic-guitar arms only. Draws detune (locked across
    /// sample AND model), onset delay, and gain jitter from the voice seed.
    /// The extreme-repitch fallback returns the bare model UNVARIED: a bare
    /// model has no compose wrapper, so a seeded detune would be silently
    /// stripped by the first performance pitch update (code-review T1) —
    /// no variation is honest there, a half-locked one is not.
    #[allow(clippy::too_many_arguments)] // wrap_fx's established shape + (var, seed)
    pub fn wrap_var(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        fx: LaFx,
        var: OnsetVar,
        seed: u32,
    ) -> Box<dyn Voice> {
        Self::wrap_var_classified(sustain, zones, key, vel, sr, gain, fade, fx, var, seed).voice
    }

    /// [`Self::wrap_var`] plus whether the sample layer was actually constructed.
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn wrap_var_classified(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        fx: LaFx,
        var: OnsetVar,
        seed: u32,
    ) -> LaVoiceBuild {
        let mut rng = crate::dsp::Rng::new(seed ^ 0x00A1_51C5);
        let strata = [-0.5f32, -0.25, 0.0, 0.25, 0.5];
        let cents = strata[(seed >> 3) as usize % strata.len()] * var.detune_strata_c
            + rng.white() * var.detune_white_c;
        let var_mult = (cents / 1200.0).exp2();
        let gain = gain * (1.0 + var.gain_frac * rng.white());
        let start = (var.onset_max_s * sr * (0.5 + 0.5 * rng.white())) as usize;
        match Self::build(
            sustain,
            zones,
            key,
            vel,
            sr,
            gain,
            fade,
            fx,
            DEFAULT_LA_RELEASE_T60,
        ) {
            Ok(mut la) => {
                la.var_mult = var_mult;
                la.base_step *= var_mult;
                la.step = la.base_step;
                la.start = start;
                // ~5 ms end taper (review C8): at non-44.1 kHz rates the
                // source can be consumed faster than the 44.1 k fade budget
                // assumes (step folds in 44100/sr), so a zone may run dry
                // mid-fade — taper instead of stepping. Armed only here so
                // every non-guitar LA path stays bit-identical.
                la.end_taper = 0.005 * sr;
                // seat the model at the locked detune; later performance
                // pitch updates compose var_mult × mult in set_pitch()
                la.sustain.set_pitch(var_mult);
                LaVoiceBuild {
                    voice: Box::new(la),
                    used_sample: true,
                }
            }
            Err(model) => LaVoiceBuild {
                voice: model,
                used_sample: false,
            },
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn build(
        sustain: Box<dyn Voice>,
        zones: &'static [Zone],
        key: u8,
        vel: u8,
        sr: f32,
        gain: f32,
        fade: (f32, f32),
        fx: LaFx,
        release_t60: f32,
    ) -> Result<LaVoice, Box<dyn Voice>> {
        let f = key_freq(key);
        let zone = nearest(zones, f);
        // Guard the musical PITCH RATIO, then convert to the output clock — never the
        // other way round. Checking the sample-rate-converted step made eligibility a
        // function of the output rate: at 96 kHz a GM 33 E1 against the 41.22 Hz
        // finger-bass zone reads step ~0.459 and silently lost its sampled onset, while
        // a far less credible octave-up repitch read ~0.922 and engaged
        // (MM-BUG-KILN-00061). Same order as the looped-sustain voices below.
        let ratio = f / zone.root;
        if !(0.5..=2.05).contains(&ratio) {
            return Err(sustain);
        }
        let step = ratio * 44100.0 / sr;
        let (shelf_g, shelf_a) = match fx.shelf {
            Some((db, hz)) => (
                10f32.powf(db / 20.0) - 1.0,
                1.0 - (-std::f32::consts::TAU * hz / sr).exp(),
            ),
            None => (0.0, 0.0),
        };
        let vel_lp_a = match fx.vel_lp {
            Some(base_hz) => vel_lp_alpha(base_hz, vel, sr),
            None => 0.0,
        };
        // ONE velocity-level law, shared with the wrapped model, so the sampled
        // onset and the modeled body track each other exactly and their crossfade
        // ratio is velocity-invariant.
        //
        // "The same law" means the same law ON THE SAME COMPRESSED VELOCITY. A
        // model with `vel_sense < 1` (only HARPSICHORD) squares a compressed `vn`
        // rather than the raw one, so a bare `vel_amp(vel)` onset did NOT track it:
        // at v100 the sampled quill sat ~2.3 dB under the body it was supposed to
        // ride, and a later window edged out the attack — the ~12 % late bloom of
        // MM-BUG-KILN-00030, wrong for an instrument whose whole identity is the
        // pluck transient. `fx.vel_sense` carries the wrapped model's sensitivity so
        // both sides compress identically. `None` (every other voice) is
        // bit-identical to the previous bare `vel_amp`.
        //
        // NOT fixed with a floored `X + Y·vel_amp` onset: `dsp::vel_amp` forbids
        // that shape outright (it is not a power law, it asymptotes to X, and a zoo
        // of such floors is what collapsed this synth's aggregate response before).
        //
        // This used to carry a second, superlinear branch for the guitars
        // (`(vel_amp/vel_amp(100))^1.4`) whose whole job was to compensate for
        // the model's velocity FLOOR: a floored model went flat at low velocity
        // while the sample did not, so the sample rode far above it through the
        // crossfade. With the floors gone and one square law everywhere, the
        // compensation has nothing left to correct — keeping it would re-steepen
        // the guitars to v^2.8.
        let vel_gain = match fx.vel_sense {
            Some(sense) => vel_amp_sensed(vel, sense),
            None => vel_amp(vel),
        };
        let fade_start = (fade.0 * sr) as usize;
        let fade_end = (fade.1 * sr) as usize;
        let b1_model_fade_end = 2 * fade_start / 3;
        Ok(LaVoice {
            sustain,
            zone,
            pos: 0.0,
            step,
            base_step: step,
            base_ratio: ratio,
            gain: gain * vel_gain,
            rel_gain: 1.0,
            rel_mul: 1.0,
            rel_t60_mul: 10f32.powf(-3.0 / (release_t60 * sr)),
            t: 0,
            fade_start,
            fade_end,
            b1_phase_robust_fade: false,
            b1_sample_power: 0.0,
            b1_model_power: 0.0,
            b1_cross_power: 0.0,
            // 20 ms one-pole: long enough not to follow individual piano
            // cycles, short enough to follow either B1 handoff window.
            b1_power_alpha: 1.0 - (-1.0 / (0.020 * sr)).exp(),
            b1_model_fade_end,
            fade_hold: None,
            buf: Vec::new(),
            fx,
            // 5 / 9 ms into the source (44.1 kHz zone data)
            pos2: 220.0,
            pos3: 397.0,
            shelf_lp: 0.0,
            shelf_a,
            shelf_g,
            var_mult: 1.0,
            start: 0,
            vel_lp: 0.0,
            vel_lp_a,
            end_taper: 0.0,
            rr: None,
        })
    }
}

impl Voice for LaVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        self.buf.resize(out.len(), 0.0);
        self.buf.fill(0.0);
        let sustain_alive = self.sustain.render(&mut self.buf);
        let n = self.zone.data.len();
        let fade_len = (self.fade_end - self.fade_start).max(1) as f32;
        let mut sample_live = false;
        for (i, o) in out.iter_mut().enumerate() {
            let t = self.t + i;
            let blend_t = self.fade_hold.unwrap_or(t);
            // §2.7 default: one sum-to-one crossfade weight — model discarded
            // before fade_start, sole owner after fade_end. B1 is the measured
            // phase-robust exception documented on `wrap_release_b1`.
            let u = smooth((blend_t as f32 - self.fade_start as f32) / fade_len);
            let model_weight = if self.b1_phase_robust_fade {
                smooth(blend_t as f32 / self.b1_model_fade_end.max(1) as f32)
            } else {
                u
            };
            let model_raw = self.buf[i];
            let mut sample_raw = 0.0;
            let mut s = model_raw * model_weight;
            let j = self.pos as usize;
            if t >= self.start && blend_t < self.fade_end && j + 1 < n && self.rel_gain > 0.0005 {
                sample_live = true;
                let frac = self.pos - j as f32;
                // 4-point cubic read (edge-clamped): linear interpolation dulls
                // the treble and aliases the sampled attack when the zone is
                // pitched up (step up to ~2.0 across the zone splits).
                let mut v = crate::dsp::cubic4(
                    self.zone.data[j.saturating_sub(1)],
                    self.zone.data[j],
                    self.zone.data[j + 1],
                    self.zone.data[(j + 2).min(n - 1)],
                    frac,
                );
                if let Some((ra, rb, mix)) = self.fx.detune {
                    // round-3 U3: two detuned reads of the SAME data — the
                    // continuously-diverging phase beats at f0·(1−ra) etc.,
                    // real periodic AM, from the first hammer instant
                    let d = &self.zone.data;
                    let mut side = 0.0;
                    let k = self.pos2 as usize;
                    if k + 1 < n {
                        let fr = self.pos2 - k as f32;
                        side += crate::dsp::cubic4(
                            d[k.saturating_sub(1)],
                            d[k],
                            d[k + 1],
                            d[(k + 2).min(n - 1)],
                            fr,
                        );
                    }
                    self.pos2 += self.step * ra;
                    let k = self.pos3 as usize;
                    if k + 1 < n {
                        let fr = self.pos3 - k as f32;
                        side += crate::dsp::cubic4(
                            d[k.saturating_sub(1)],
                            d[k],
                            d[k + 1],
                            d[(k + 2).min(n - 1)],
                            fr,
                        );
                    }
                    self.pos3 += self.step * rb;
                    v += mix * side;
                }
                if self.fx.shelf.is_some() {
                    // round-3 U3: one-pole high-shelf — unity at DC, +g above
                    // the corner; the readout stays phase-coherent with the
                    // crossfade partner underneath
                    self.shelf_lp += (v - self.shelf_lp) * self.shelf_a;
                    v += self.shelf_g * (v - self.shelf_lp);
                }
                if self.vel_lp_a > 0.0 {
                    // guitar-realism HLD §4: a soft pick darkens the sampled
                    // onset like it darkens the string (vel ≥ 100 never
                    // reaches here — vel_lp_alpha returns a hard 0.0)
                    self.vel_lp += (v - self.vel_lp) * self.vel_lp_a;
                    v = self.vel_lp;
                }
                if self.b1_phase_robust_fade {
                    v = -v;
                }
                if self.end_taper > 0.0 {
                    // graceful dry-out (review C8): fade as the read nears
                    // the zone's last frames — exactly 1.0 (bit-transparent)
                    // while more than a taper-length of source remains
                    // (single division: taper × step is the source-domain
                    // taper span)
                    let remaining_src = n as f32 - 2.0 - self.pos;
                    v *= (remaining_src / (self.end_taper * self.step.max(1e-6))).clamp(0.0, 1.0);
                }
                if self.b1_phase_robust_fade {
                    sample_raw = v * self.gain * self.rel_gain;
                } else {
                    // Preserve the established operation order bit-for-bit for
                    // every general LA wrapper. Reassociation here moved every
                    // sampled voice in the corpus during MM-BUG-KILN-00133.
                    s += v * (1.0 - u) * self.gain * self.rel_gain;
                }
                self.rel_gain *= self.rel_mul;
                self.pos += self.step;
            }
            if self.b1_phase_robust_fade {
                s = model_raw * model_weight + sample_raw * (1.0 - u);
                let a = self.b1_power_alpha;
                self.b1_sample_power += a * (sample_raw * sample_raw - self.b1_sample_power);
                self.b1_model_power += a * (model_raw * model_raw - self.b1_model_power);
                self.b1_cross_power += a * (sample_raw * model_raw - self.b1_cross_power);

                let sample_weight = 1.0 - u;
                let actual_power = sample_weight * sample_weight * self.b1_sample_power
                    + model_weight * model_weight * self.b1_model_power
                    + 2.0 * sample_weight * model_weight * self.b1_cross_power;
                let target_power = sample_weight * sample_weight * self.b1_sample_power
                    + model_weight * model_weight * self.b1_model_power
                    + B1_TARGET_CROSS_COEFF
                        * sample_weight
                        * model_weight
                        * (self.b1_sample_power * self.b1_model_power).sqrt();
                if actual_power > 1e-16 && target_power > 0.0 {
                    // Normalize to a fixed weak-coherence target: lift
                    // destructive overlap and trim strongly constructive
                    // overlap without making the handoff quieter than its two
                    // owners. The bounds prevent a momentary near-null or
                    // near-lock from turning numerical residue into an impulse.
                    let compensation = (target_power / actual_power).sqrt().clamp(0.5, 3.0);
                    s *= compensation;
                }
            }
            *o += s;
        }
        self.t += out.len();
        sustain_alive || sample_live
    }

    fn note_off(&mut self) {
        self.sustain.note_off();
        if self.b1_phase_robust_fade {
            self.fade_hold = Some(self.t);
        }
        // Apply the configured key-up damping (60 ms T60 for default callers).
        self.rel_mul = self.rel_t60_mul;
    }

    fn released(&self) -> bool {
        self.sustain.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        // bend the transient with the note, and the model underneath. The
        // locked per-note detune composes multiplicatively (var_mult is 1.0
        // outside wrap_var): a bend/vibrato/glide update can never strip the
        // model's detune while the sample keeps it (review C3) — base_step
        // already carries var_mult, the model gets var_mult × mult.
        self.step = self.base_step * mult;
        self.sustain.set_pitch(self.var_mult * mult);
    }

    fn legato_to(&mut self, key: u8, vel: u8) -> bool {
        // a slur has no fresh attack: retire the transient, glide the model
        if self.sustain.legato_to(key, vel) {
            self.fade_hold = None;
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    fn retrigger(&mut self, key: u8, vel: u8) -> bool {
        // ROUND-ROBIN BANKS ONLY: rotate to the next take and REPLAY the sampled
        // attack, so a tremolo is carried by real recorded strokes.
        //
        // This is the deliberate exception to the rule stated below, and it is
        // scoped to `rr.is_some()` for a reason that is easy to break: this
        // method is shared by EVERY sampled voice, and GM 25 steel tremolo is
        // used by two committed albums. Replaying a SINGLE take 13×/s is exactly
        // the machine-gun artifact the suppression exists to prevent — having N
        // genuinely different takes to rotate is the precondition that makes
        // replaying safe. A bank without round robins therefore keeps the
        // original path untouched, bit for bit.
        //
        // Each stroke is naturally truncated by the next retrigger, so what
        // sounds is the recorded pick attack — which is the whole point.
        if let Some(rr) = self.rr {
            if !self.sustain.retrigger(key, vel) {
                return false;
            }
            let idx = rr.idx.wrapping_add(1);
            let zones = (rr.bank)(idx % rr.takes);
            let zone = &zones[rr.zone_idx];
            // Same key, so the pitch is unchanged: rescale by the root ratio
            // rather than recomputing from `sr`, which also preserves any active
            // bend held in `step` relative to `base_step`.
            let ratio = self.zone.root / zone.root;
            let next_ratio = self.base_ratio * ratio;
            if !(0.5..=2.05).contains(&next_ratio) {
                // Out of the credible repitch window — fall back to the modeled
                // stroke rather than playing a badly-pitched sample. Checked on the
                // PITCH ratio, not on `base_step`, which carries the 44100/sr output
                // clock and would make this depend on the render rate
                // (MM-BUG-KILN-00061).
                self.rel_mul = self.rel_t60_mul;
                return true;
            }
            self.rr = Some(RoundRobin { idx, ..rr });
            self.zone = zone;
            self.step *= ratio;
            self.base_step *= ratio;
            self.base_ratio = next_ratio;
            // Re-arm the onset: restart the crossfade clock and the read head,
            // and undo any release decay so the new stroke is at full level.
            self.t = 0;
            self.fade_hold = None;
            self.pos = 0.0;
            self.pos2 = 220.0;
            self.pos3 = 397.0;
            self.rel_gain = 1.0;
            self.rel_mul = 1.0;
            self.shelf_lp = 0.0;
            self.vel_lp = 0.0;
            return true;
        }
        // TREM: a tremolo restrike re-picks the MODEL string; the sampled
        // attack transient is NOT replayed (the identical PCM 13×/s is the
        // machine-gun artifact the drum round-robins exist to avoid) — it
        // is retired quickly, exactly like a slur. The model's own restrike
        // burst articulates every stroke, decorrelated per stroke by
        // construction.
        if self.sustain.retrigger(key, vel) {
            self.fade_hold = None;
            self.rel_mul = self.rel_t60_mul;
            true
        } else {
            false
        }
    }

    fn rr_phase(&self) -> Option<usize> {
        self.rr.map(|rr| rr.idx % rr.takes.max(1))
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        // the LA wrapper is transparent for routing: report the model inside
        self.sustain.kind()
    }

    fn set_trem(&mut self, rate_hz: f32, depth: f32) {
        self.sustain.set_trem(rate_hz, depth);
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        // Authored CC2/CC11 timbre-tracking must reach the model inside the
        // wrap (it used to no-op here, so the samples-on render ignored the
        // controller). The engine only drives this on authored channels
        // (plus brass's neutral pressure-1.0 note-on seed, a no-op), so an
        // unauthored channel renders bit-exactly as before.
        self.sustain.set_breath(pressure, growl);
    }
}

// ---------------------------------------------------------------------------
// GM 64-67 saxophone: looped real sustain (2026.07.18 holds audit)
//
// The held sax used to be 100% modeled reed past the 0.24 s sample fade — a
// static drone (liveness 0.024 vs the SC-55's 0.050). Here the WHOLE voice is the
// real recording: the attack plays through once, then a pitch-synchronous loop of
// the recorded sustain (already present in the 0.62 s take, previously discarded)
// carries the hold. The model is no longer the sustain source — a later increment
// re-adds it purely as a modulator (vibrato/brightness/breath), never summed as a
// second tonal oscillator at the same f0 (the comb trap the attack seam avoids).
// ---------------------------------------------------------------------------

/// Per-program output gain for the looped sax (index = program − 64: soprano / alto /
/// tenor / baritone). Per-program because the samples are uniformly peak-normalised but
/// the modeled reeds differ per sax (~7 dB spread), so no single constant matches.
///
/// 2026.07.18 mix-consistency nudge: +2.3 dB over the raw-parity values. Raw parity with
/// the model is NOT the right target — through the master bus-glue compressor the animated
/// loop (tremolo + breath, a fuller envelope than the dry model) is pulled ~2 dB lower in
/// the mix than the model+onset sax it replaced, leaving the sax quiet against the sibling
/// reeds (68-71, still model+onset). The lift restores it to the old shipped mix level
/// (alto hold ≈ −5.3 dB vs the piano anchor). Tuned by the in-mix measurement, guarded by
/// `sax_loop_level_parity_and_flat` (raw offset band, widened to admit this deliberate lift).
const SAX_LOOP_GAIN: [f32; 4] = [0.508, 0.377, 0.666, 0.812];

fn sax_program_gain(program: u8) -> f32 {
    SAX_LOOP_GAIN[(program.saturating_sub(64)).min(3) as usize]
}

/// Find a pitch-synchronous sustain loop inside a recorded sax note. Returns
/// `(loop_start, loop_end)` in source samples (the zone is 44.1 kHz). Runs an
/// `extract_loop`-style search over integer-period lengths derived from the measured
/// `root`, minimising a cost that combines the WRAP seam (value + slope mismatch) with
/// the loop's amplitude IMBALANCE (first-half vs second-half RMS). The imbalance term
/// is load-bearing: a clean seam alone does NOT mean a flat interior — the longest
/// seam-clean loop can span the note's natural decay and turn the hold into a ~3 Hz
/// loud→silence→loud sawtooth. The loop is therefore bounded to a SHORT window
/// (`MIN_LEN_S..MAX_LEN_S`) inside the steady body (`le < BODY_END_S`), which stays
/// clear of the recorded release. `None` when the note is too short (caller keeps the
/// modeled reed).
fn find_sax_loop(data: &[f32], root: f32) -> Option<(usize, usize)> {
    #[cfg(test)]
    LOOP_SEARCHES.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    let sr = 44100.0f32;
    if root <= 0.0 {
        return None;
    }
    let period = sr / root;
    if period < 4.0 {
        return None;
    }
    let n = data.len();
    const START_LO_S: f32 = 0.30; // past the reed chiff, into the settled body
    const START_HI_S: f32 = 0.40;
    const MIN_LEN_S: f32 = 0.05; // >= a handful of periods; short enough to stay steady
    const MAX_LEN_S: f32 = 0.13;
    const BODY_END_S: f32 = 0.50; // keep the loop clear of the recorded release/decay
    let start_lo = (START_LO_S * sr) as usize;
    let min_len = (MIN_LEN_S * sr) as usize;
    let body_end = ((BODY_END_S * sr) as usize).min(n.saturating_sub(2));
    if start_lo == 0 || body_end <= start_lo + min_len {
        return None;
    }
    let start_hi = ((START_HI_S * sr) as usize).min(body_end - min_len);
    let max_len = (MAX_LEN_S * sr) as usize;
    let stride = (period / 8.0).max(1.0) as usize;
    // Interior amplitude imbalance: |rms(first half) - rms(second half)| / mean rms.
    // A decaying loop reads high here even when its seam is clean.
    let imbalance = |ls: usize, le: usize| -> f32 {
        let mid = (ls + le) / 2;
        let rms = |a: usize, b: usize| {
            (data[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a).max(1) as f32).sqrt()
        };
        let (r1, r2) = (rms(ls, mid), rms(mid, le));
        (r1 - r2).abs() / (0.5 * (r1 + r2) + 1e-6)
    };
    let mut best: Option<(f32, usize, usize)> = None; // (cost, ls, le)
    let mut ls = start_lo;
    while ls <= start_hi {
        let mut k = ((min_len as f32 / period).ceil() as usize).max(1);
        loop {
            let l = (k as f32 * period).round() as usize;
            if l > max_len {
                break;
            }
            let le = ls + l;
            if le + 1 >= body_end {
                break;
            }
            let vseam = (data[le] - data[ls]).abs();
            let sseam = ((data[le] - data[le - 1]) - (data[ls] - data[ls - 1])).abs();
            // Weight imbalance heavily: a flat interior matters more than a perfect seam
            // (the seam is baked-near-zero by integer periods anyway).
            let cost = vseam + 0.5 * sseam + 4.0 * imbalance(ls, le);
            if best.is_none_or(|(bc, _, _)| cost < bc) {
                best = Some((cost, ls, le));
            }
            k += 1;
        }
        ls += stride;
    }
    best.map(|(_, ls, le)| (ls, le))
}

// Inc 2 — intrinsic humanisation so the looped hold BREATHES like the modeled reed did
// (inc 1 was deliberately static), plus CC11/CC2 brightness/breath response. Restrained
// by design; the numeric target is the SC-55's hold liveness (~0.05, a 20 ms frame-RMS
// CoV). Real sax vibrato couples PITCH and AMPLITUDE, so both are modulated — pitch alone
// barely moves an amplitude-based liveness metric. CC1 vibrato and pitch bend arrive
// separately via `set_pitch` (engine-driven), composing on top of the intrinsic warble.
const SAX_VIB_RATE_HZ: f32 = 5.4; // sax vibrato centre ~5–5.6 Hz
const SAX_VIB_PITCH: f32 = 0.006; // ±0.6% read-rate ≈ ±10 cents intrinsic pitch warble
const SAX_VIB_AMP: f32 = 0.05; // ±5% coupled amplitude tremolo
const SAX_VIB_DELAY_S: f32 = 0.20; // vibrato blooms after the onset
const SAX_VIB_BLOOM_S: f32 = 0.35; // ramp-in time
const SAX_DRIFT_MAX: f32 = 0.0022; // ±0.22% slow random-walk on the rate (defeats the loop-tell)
const SAX_DRIFT_SAMP: u32 = 1024; // new drift target ~ every 23 ms

// The synthetic air rides on top of a REAL recording that already breathes, so it must
// stay a subtle enhancement, not a second breath. Measured (2026.07.19, solo-sax stems,
// stock minus a breath-zeroed build) the old 0.004/0.05 pair landed the layer at −30 dB
// (Night Train, CC11 66–78) up to −24 dB mean / −21 dB peak (Atlas "corridor sax", CC11
// peaking 114) below the tone — an audible hiss at the swells. The CC lift was the
// offender (12.5× the floor at full CC): cut it ~12 dB and trim the floor ~4 dB, so even
// the worst case sits ~−32 dB — a whisper of air under the recording's own breath. Degree
// is Arthur's ear; these are the "don't double the breath" values.
const SAX_BREATH_FLOOR: f32 = 0.0025; // intrinsic air floor (was 0.004)
const SAX_BREATH_CC: f32 = 0.012; // extra air at full CC11/CC2 (was 0.05 — the too-strong "wind")
const SAX_BREATH_HP_HZ: f32 = 1800.0; // HP the noise into air, not rumble
const SAX_BRIGHT_LO_HZ: f32 = 1400.0; // CC11 brightness sweep corner: soft → dark
const SAX_BRIGHT_HI_HZ: f32 = 7000.0; // → loud, open (near pass-through)

/// GM 64-67 sax voice: recorded attack played through into a looped recorded sustain,
/// with the loop animated by intrinsic vibrato/tremolo/drift/breath (inc 2) so the hold
/// is alive rather than a static repeat. The loop is found once at construction.
pub struct SaxLoopVoice {
    data: &'static [f32],
    loop_start: usize,
    loop_end: usize,
    pos: f32,
    base_step: f32,
    step: f32,
    gain: f32,
    env: crate::dsp::Adsr,
    sr: f32,
    // A held realtime note is unbounded by MIDI semantics. `u32` wrapped after
    // 6–27 hours at supported rates and restarted bloom/drift (MM-BUG-KILN-00066).
    t: u64,
    vib_phase: f32,
    vib_inc: f32,
    drift: f32,
    drift_target: f32,
    rng: Rng,
    breath_hp: crate::dsp::OnePole,
    breath_amt: f32, // intrinsic floor + CC11
    growl: f32,      // aftertouch → deeper vibrato
    bright: crate::dsp::OnePole,
    bright_active: bool, // CC11/CC2 authored → brightness LP engaged
}

impl SaxLoopVoice {
    fn new(
        zone: &'static Zone,
        target_hz: f32,
        vel: u8,
        sr: f32,
        base_gain: f32,
        seed: u32,
    ) -> Option<Self> {
        // Cheap rejection FIRST: an out-of-range key falls back to the modeled reed, and
        // must not pay for a loop search to learn that (MM-BUG-KILN-00064).
        let ratio = target_hz / zone.root;
        if !(0.5..=2.05).contains(&ratio) {
            return None;
        }
        let (loop_start, loop_end) = zone.sustain_loop(find_sax_loop)?;
        let base_step = ratio * 44100.0 / sr;
        Some(SaxLoopVoice {
            data: zone.data.as_slice(),
            loop_start,
            loop_end,
            pos: 0.0,
            base_step,
            step: base_step,
            // p/f banks already carry the bulk of the dynamic; a gentle vel taper on top.
            gain: base_gain * vel_amp(vel),
            // near-instant attack (the sample owns the onset), ~70 ms release.
            env: crate::dsp::Adsr::new(0.004, 0.0, 1.0, 0.07, sr),
            sr,
            t: 0,
            vib_phase: 0.0,
            vib_inc: std::f32::consts::TAU * SAX_VIB_RATE_HZ / sr,
            drift: 0.0,
            drift_target: 0.0,
            rng: Rng::new(seed ^ 0x5AC0_FFEE ^ ((zone.root as u32) << 3) ^ vel as u32),
            breath_hp: crate::dsp::OnePole::lowpass(SAX_BREATH_HP_HZ, sr),
            breath_amt: SAX_BREATH_FLOOR,
            growl: 0.0,
            bright: crate::dsp::OnePole::lowpass(SAX_BRIGHT_HI_HZ, sr),
            bright_active: false,
        })
    }
}

impl Voice for SaxLoopVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let loop_len = (self.loop_end - self.loop_start) as f32;
        for o in out.iter_mut() {
            let e = self.env.next();
            let time = self.t as f32 / self.sr;
            // Intrinsic vibrato: delayed bloom, deepened by aftertouch growl; couples a
            // pitch warble and an amplitude tremolo (as a real reed's does).
            let bloom = ((time - SAX_VIB_DELAY_S) / SAX_VIB_BLOOM_S).clamp(0.0, 1.0);
            let s = self.vib_phase.sin();
            self.vib_phase += self.vib_inc;
            if self.vib_phase >= std::f32::consts::TAU {
                self.vib_phase -= std::f32::consts::TAU;
            }
            let depth = bloom * (1.0 + 2.0 * self.growl);
            // Slow bounded drift random-walk on the read rate.
            if self.t.is_multiple_of(SAX_DRIFT_SAMP as u64) {
                self.drift_target = SAX_DRIFT_MAX * self.rng.white();
            }
            self.drift += 0.002 * (self.drift_target - self.drift);
            let eff_step = self.step * (1.0 + SAX_VIB_PITCH * depth * s + self.drift);
            let amp = 1.0 + SAX_VIB_AMP * depth * s;
            // Read the looped sample. Wrapped neighbour at the seam: an unwrapped read
            // clicks once per loop.
            let j = self.pos as usize;
            let frac = self.pos - j as f32;
            let a = self.data[j];
            let jn = j + 1;
            let b = if jn >= self.loop_end {
                self.data[self.loop_start]
            } else {
                self.data[jn]
            };
            let mut tone = a + (b - a) * frac;
            if self.bright_active {
                tone = self.bright.process(tone);
            }
            // Additive HP breath noise — uncorrelated with the tone, so it is the one
            // layer that can be SUMMED without combing. Rides the note's own gain.
            let w = self.rng.white();
            let breath = (w - self.breath_hp.process(w)) * self.breath_amt;
            *o += (tone * amp + breath) * self.gain * e;
            self.pos += eff_step;
            if self.pos >= self.loop_end as f32 {
                self.pos -= loop_len;
            }
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.step = self.base_step * mult;
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        // CC11/CC2 pressure opens the timbre (brightness) and lifts breath noise; channel
        // aftertouch deepens the vibrato. Only called on AUTHORED channels (engine RD9
        // gate), so an unauthored sax keeps the intrinsic floor and its inc-1 brightness.
        let p = pressure.clamp(0.0, 1.0);
        self.bright_active = true;
        self.bright.set_cutoff(
            SAX_BRIGHT_LO_HZ + (SAX_BRIGHT_HI_HZ - SAX_BRIGHT_LO_HZ) * p,
            self.sr,
        );
        self.breath_amt = SAX_BREATH_FLOOR + SAX_BREATH_CC * p;
        self.growl = growl.clamp(0.0, 1.0);
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "saxloop"
    }
}

/// Build the looped-sustain sax voice for GM 64-67, or `None` if no usable loop /
/// the repitch is out of range (the caller keeps the modeled reed).
pub fn sax_loop_voice(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let zones = sax_bank(program, vel);
    let f = key_freq(key);
    let zone = nearest(zones, f);
    SaxLoopVoice::new(zone, f, vel, sr, sax_program_gain(program), seed)
        .map(|v| Box::new(v) as Box<dyn Voice>)
}

// ---------------------------------------------------------------------------
// GM 76 blown bottle — the whole voice is a real "blown bottle" recording
// (Freesound 349867 "Blown Bottle Two" by Terry93D, CC0 1.0). Built exactly
// like the sax (`SaxLoopVoice`): the recorded blow plays through once, then a
// pitch-synchronous loop of the recorded plateau body carries the hold,
// animated by the shared intrinsic vibrato/tremolo/drift/breath so the hold is
// alive rather than a static repeat. A blown bottle already carries its own
// breath in the recording, so the intrinsic air floor stays low. The modeled
// Wind bottle remains the `--no-samples` voice and the fallback when no usable
// loop exists / the repitch is out of range.
// ---------------------------------------------------------------------------

/// Per-program output gain for the looped blown bottle. One program, so one value
/// (unlike the sax's per-program table). Calibrated for rough parity with the modeled
/// Wind bottle it replaces: at 1.0 the peak-normalised recording ran ~+4.4 dB hot
/// (bare-voice hold RMS over 0.6-1.4 s; key 55 +3.9 dB, key 60 +5.4 dB). 0.65 (−3.7 dB)
/// lands the hold at +0.2 dB (key 55) to +1.6 dB (key 60) — inside 0..+2 dB. Guarded by
/// `bottle_loop_level_parity_and_flat`. The bottle isn't in any album, so exact parity
/// isn't critical — sane in-mix level is enough.
const BOTTLE_LOOP_GAIN: f32 = 0.65;

/// Single-zone bank for the GM 76 blown-bottle LA loop (Freesound 349867, CC0 1.0),
/// measured root 205.0 Hz.
fn bottle_loop_bank() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "bottleloop_G3.wav" => 205.0,
        )
    })
}

/// Find a pitch-synchronous sustain loop inside the recorded blown bottle. Copy of
/// [`find_sax_loop`], re-windowed for the bottle's longer plateau (the recorded blow
/// swells in over ~0.3 s then holds a ~1.2 s body). Returns `(loop_start, loop_end)`
/// in source samples (the zone is 44.1 kHz); `None` when the note is too short (the
/// caller keeps the modeled bottle).
fn find_bottle_loop(data: &[f32], root: f32) -> Option<(usize, usize)> {
    #[cfg(test)]
    LOOP_SEARCHES.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
    let sr = 44100.0f32;
    if root <= 0.0 {
        return None;
    }
    let period = sr / root;
    if period < 4.0 {
        return None;
    }
    let n = data.len();
    const START_LO_S: f32 = 0.45; // past the blow swell, into the settled body
    const START_HI_S: f32 = 0.90;
    const MIN_LEN_S: f32 = 0.05; // >= a handful of periods; short enough to stay steady
    const MAX_LEN_S: f32 = 0.15;
    const BODY_END_S: f32 = 1.45; // keep the loop clear of the recorded fade
    let start_lo = (START_LO_S * sr) as usize;
    let min_len = (MIN_LEN_S * sr) as usize;
    let body_end = ((BODY_END_S * sr) as usize).min(n.saturating_sub(2));
    if start_lo == 0 || body_end <= start_lo + min_len {
        return None;
    }
    let start_hi = ((START_HI_S * sr) as usize).min(body_end - min_len);
    let max_len = (MAX_LEN_S * sr) as usize;
    let stride = (period / 8.0).max(1.0) as usize;
    // Interior amplitude imbalance: |rms(first half) - rms(second half)| / mean rms.
    // A decaying loop reads high here even when its seam is clean.
    let imbalance = |ls: usize, le: usize| -> f32 {
        let mid = (ls + le) / 2;
        let rms = |a: usize, b: usize| {
            (data[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a).max(1) as f32).sqrt()
        };
        let (r1, r2) = (rms(ls, mid), rms(mid, le));
        (r1 - r2).abs() / (0.5 * (r1 + r2) + 1e-6)
    };
    let mut best: Option<(f32, usize, usize)> = None; // (cost, ls, le)
    let mut ls = start_lo;
    while ls <= start_hi {
        let mut k = ((min_len as f32 / period).ceil() as usize).max(1);
        loop {
            let l = (k as f32 * period).round() as usize;
            if l > max_len {
                break;
            }
            let le = ls + l;
            if le + 1 >= body_end {
                break;
            }
            let vseam = (data[le] - data[ls]).abs();
            let sseam = ((data[le] - data[le - 1]) - (data[ls] - data[ls - 1])).abs();
            // Weight imbalance heavily: a flat interior matters more than a perfect seam
            // (the seam is baked-near-zero by integer periods anyway).
            let cost = vseam + 0.5 * sseam + 4.0 * imbalance(ls, le);
            if best.is_none_or(|(bc, _, _)| cost < bc) {
                best = Some((cost, ls, le));
            }
            k += 1;
        }
        ls += stride;
    }
    best.map(|(_, ls, le)| (ls, le))
}

/// GM 76 blown-bottle voice: recorded blow played through into a looped recorded
/// plateau body, animated by intrinsic vibrato/tremolo/drift/breath (the shared
/// `SAX_VIB_*`/`SAX_DRIFT_*`/`SAX_BREATH_*` constants) so the hold is alive rather
/// than a static repeat. The loop is found once at construction. Mirrors
/// [`SaxLoopVoice`].
pub struct BottleLoopVoice {
    data: &'static [f32],
    loop_start: usize,
    loop_end: usize,
    pos: f32,
    base_step: f32,
    step: f32,
    gain: f32,
    env: crate::dsp::Adsr,
    sr: f32,
    // Mirrors SaxLoopVoice: wide enough that a valid held note cannot restart
    // its bloom/drift state at the old u32 boundary (MM-BUG-KILN-00066).
    t: u64,
    vib_phase: f32,
    vib_inc: f32,
    drift: f32,
    drift_target: f32,
    rng: Rng,
    breath_hp: crate::dsp::OnePole,
    breath_amt: f32, // intrinsic floor + CC11
    growl: f32,      // aftertouch → deeper vibrato
    bright: crate::dsp::OnePole,
    bright_active: bool, // CC11/CC2 authored → brightness LP engaged
}

impl BottleLoopVoice {
    fn new(
        zone: &'static Zone,
        target_hz: f32,
        vel: u8,
        sr: f32,
        base_gain: f32,
        seed: u32,
    ) -> Option<Self> {
        // Cheap rejection FIRST: an out-of-range key falls back to the modeled Wind
        // bottle, and must not pay for a loop search to learn that (MM-BUG-KILN-00064).
        let ratio = target_hz / zone.root;
        if !(0.5..=2.05).contains(&ratio) {
            return None;
        }
        let (loop_start, loop_end) = zone.sustain_loop(find_bottle_loop)?;
        let base_step = ratio * 44100.0 / sr;
        Some(BottleLoopVoice {
            data: zone.data.as_slice(),
            loop_start,
            loop_end,
            pos: 0.0,
            base_step,
            step: base_step,
            // a gentle vel taper on top of the recorded dynamic.
            gain: base_gain * (0.55 + 0.45 * vel_amp(vel)),
            // near-instant attack (the sample owns the onset), ~70 ms release.
            env: crate::dsp::Adsr::new(0.004, 0.0, 1.0, 0.07, sr),
            sr,
            t: 0,
            vib_phase: 0.0,
            vib_inc: std::f32::consts::TAU * SAX_VIB_RATE_HZ / sr,
            drift: 0.0,
            drift_target: 0.0,
            rng: Rng::new(seed ^ 0x5AC0_FFEE ^ ((zone.root as u32) << 3) ^ vel as u32),
            breath_hp: crate::dsp::OnePole::lowpass(SAX_BREATH_HP_HZ, sr),
            // bottles carry their own breath in the sample — keep the intrinsic floor low.
            breath_amt: SAX_BREATH_FLOOR,
            growl: 0.0,
            bright: crate::dsp::OnePole::lowpass(SAX_BRIGHT_HI_HZ, sr),
            bright_active: false,
        })
    }
}

impl Voice for BottleLoopVoice {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let loop_len = (self.loop_end - self.loop_start) as f32;
        for o in out.iter_mut() {
            let e = self.env.next();
            let time = self.t as f32 / self.sr;
            // Intrinsic vibrato: delayed bloom, deepened by aftertouch growl; couples a
            // pitch warble and an amplitude tremolo (as a real reed's does).
            let bloom = ((time - SAX_VIB_DELAY_S) / SAX_VIB_BLOOM_S).clamp(0.0, 1.0);
            let s = self.vib_phase.sin();
            self.vib_phase += self.vib_inc;
            if self.vib_phase >= std::f32::consts::TAU {
                self.vib_phase -= std::f32::consts::TAU;
            }
            let depth = bloom * (1.0 + 2.0 * self.growl);
            // Slow bounded drift random-walk on the read rate.
            if self.t.is_multiple_of(SAX_DRIFT_SAMP as u64) {
                self.drift_target = SAX_DRIFT_MAX * self.rng.white();
            }
            self.drift += 0.002 * (self.drift_target - self.drift);
            let eff_step = self.step * (1.0 + SAX_VIB_PITCH * depth * s + self.drift);
            let amp = 1.0 + SAX_VIB_AMP * depth * s;
            // Read the looped sample. Wrapped neighbour at the seam: an unwrapped read
            // clicks once per loop.
            let j = self.pos as usize;
            let frac = self.pos - j as f32;
            let a = self.data[j];
            let jn = j + 1;
            let b = if jn >= self.loop_end {
                self.data[self.loop_start]
            } else {
                self.data[jn]
            };
            let mut tone = a + (b - a) * frac;
            if self.bright_active {
                tone = self.bright.process(tone);
            }
            // Additive HP breath noise — uncorrelated with the tone, so it is the one
            // layer that can be SUMMED without combing. Rides the note's own gain.
            let w = self.rng.white();
            let breath = (w - self.breath_hp.process(w)) * self.breath_amt;
            *o += (tone * amp + breath) * self.gain * e;
            self.pos += eff_step;
            if self.pos >= self.loop_end as f32 {
                self.pos -= loop_len;
            }
            self.t += 1;
        }
        self.env.alive()
    }

    fn note_off(&mut self) {
        self.env.release();
    }

    fn released(&self) -> bool {
        self.env.released()
    }

    fn set_pitch(&mut self, mult: f32) {
        self.step = self.base_step * mult;
    }

    fn set_breath(&mut self, pressure: f32, growl: f32) {
        // CC11/CC2 pressure opens the timbre (brightness) and lifts breath noise; channel
        // aftertouch deepens the vibrato. Only called on AUTHORED channels (engine RD9
        // gate), so an unauthored bottle keeps the intrinsic floor and its brightness.
        let p = pressure.clamp(0.0, 1.0);
        self.bright_active = true;
        self.bright.set_cutoff(
            SAX_BRIGHT_LO_HZ + (SAX_BRIGHT_HI_HZ - SAX_BRIGHT_LO_HZ) * p,
            self.sr,
        );
        self.breath_amt = SAX_BREATH_FLOOR + SAX_BREATH_CC * p;
        self.growl = growl.clamp(0.0, 1.0);
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "bottleloop"
    }
}

/// Build the looped-sustain blown-bottle voice for GM 76, or `None` if no usable loop /
/// the repitch is out of range (the caller keeps the modeled bottle).
pub fn bottle_loop_voice(key: u8, vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let zones = bottle_loop_bank();
    let f = key_freq(key);
    let zone = nearest(zones, f);
    BottleLoopVoice::new(zone, f, vel, sr, BOTTLE_LOOP_GAIN, seed)
        .map(|v| Box::new(v) as Box<dyn Voice>)
}

// ---------------------------------------------------------------------------
// Sampled drum kit (drum-kit bank, Stages B/E): unlike the old kick/snare
// attack overlay there is no model underneath — the recorded hit IS the whole
// voice. Unpitched except the toms, whose two sampled drums are repitched by
// playback rate across the six GM tom keys.
// ---------------------------------------------------------------------------

/// Per-key output levels, calibrated so each sampled drum lands within a
/// couple of dB of the model it replaces at vel 100 (RMS over a fixed
/// window) — see `sampled_drum_level_parity`.
#[cfg(feature = "embedded-samples")]
const DRUM_LEVEL: [(u8, f32); 21] = [
    (35, 1.54), // kick (soft-beater alias)
    (36, 1.54), // kick
    (37, 0.28), // side stick (cross-stick)
    (38, 0.98), // snare
    (40, 0.98), // electric snare (same bank)
    (41, 0.95), // low floor tom
    (42, 0.14), // closed hi-hat
    (43, 1.04), // high floor tom
    (44, 0.13), // pedal hi-hat
    (45, 1.22), // low tom
    (46, 0.17), // open hi-hat
    (47, 1.19), // low-mid tom
    (48, 1.21), // hi-mid tom
    (49, 0.65), // crash 1
    (50, 1.22), // high tom
    (51, 0.45), // ride 1
    (52, 0.68), // china
    (53, 0.45), // ride bell
    (55, 0.34), // splash
    (57, 0.68), // crash 2
    (59, 0.45), // ride 2
];

/// The modeled tom ladder's settle pitches (drums.rs `tom(...)` arms) and the
/// measured roots of the two sampled toms. The sampled toms are repitched by
/// playback rate (`target / root`) so the six GM keys keep the same ladder as
/// the model: 41/43 pull from the ~113.5 Hz floor tom, 45/47/48/50 from the
/// ~181 Hz rack tom (the assignment that minimizes stretch — key 45's 190 Hz
/// target sits almost exactly on the rack tom's root).
#[cfg(feature = "embedded-samples")]
const TOM_LO_ROOT_HZ: f32 = 113.5;
#[cfg(feature = "embedded-samples")]
const TOM_HI_ROOT_HZ: f32 = 181.0;

/// Electric snare (key 40) plays the acoustic `SNARE` bank repitched up, so the
/// default sampled kit differentiates 38/40 the way the modeled path already
/// does (drums.rs `center_mul 1.15` — a brighter, tighter electric snare;
/// MM-BUG-KILN-00008). +2.4 st lifts the shell and shortens the decay, the
/// electric-snare character; whole-note level parity is held by `DRUM_LEVEL[40]`.
#[cfg(feature = "embedded-samples")]
const ELECTRIC_SNARE_REPITCH: f32 = 1.15;

/// Anti-machine-gun micro-variation (mechanism b), per bank profile: every
/// hit gets a playback rate of 1 + stratum + U(-rate, +rate), a gain of
/// ×(1 + U(-gain, +gain)), and an onset delay of U(0, onset_s) of silence.
/// All deterministic from the note seed (plus `hit_index` for the stratum).
/// Mechanism (a), the clean per-key round-robin cycling, lives in the
/// engine's `drum_rr` counter and arrives here as `hit_index`.
#[cfg(feature = "embedded-samples")]
struct DrumJitter {
    /// Half-width of the white playback-rate jitter.
    rate: f32,
    /// Deterministic per-hit rate offsets, cycled by `hit_index % len`
    /// (empty: none). See `HAT_JITTER` for why white jitter alone is not
    /// enough on fast repeated hits.
    strata: &'static [f32],
    /// Half-width of the white gain jitter.
    gain: f32,
    /// Maximum onset delay in seconds; each hit draws U(0, this) of silence
    /// before the sample starts, shifting the transient off the grid.
    onset_s: f32,
}

/// The pitched/tonal drums (kick, snare, toms, cymbals): gentle ±2.5% rate
/// (±~43 cents — inaudible as pitch wobble on a snare or tom, enough to
/// decorrelate the decay), ±6% gain, no onset jitter — exactly the pre-hat-
/// profile behaviour, so these banks render bit-identically to before.
#[cfg(feature = "embedded-samples")]
const DRUM_JITTER: DrumJitter = DrumJitter {
    rate: 0.025,
    strata: &[],
    gain: 0.06,
    onset_s: 0.0,
};

/// The hi-hats (42/44/46) are UNPITCHED and transient-dominated, and fast
/// 16th closed-hat lines are where Arthur heard machine-gunning (worst
/// hit-pair NCC 0.494 under the pitched profile). White jitter alone cannot
/// fix that: over 16 hits some pair sharing a round-robin take always draws
/// nearly equal rates and re-correlates. So the hats add STRATIFIED rate
/// offsets — 5 slots across ±8%, cycled by hit index; 5 is coprime with the
/// 4-take round robin, so no two hits closer than 20 apart share both take
/// and stratum, and adjacent strata (4%) minus the ±0.8% white spread still
/// guarantee ≥2.4% rate separation for every same-take pair — plus a 0-1 ms
/// onset jitter and wider ±10% gain jitter. ±8% is ±~133 cents: on a hat
/// that reads as strike-position variation, not detune.
#[cfg(feature = "embedded-samples")]
const HAT_JITTER: DrumJitter = DrumJitter {
    rate: 0.008,
    strata: &[-0.08, -0.04, 0.0, 0.04, 0.08],
    gain: 0.10,
    onset_s: 0.001,
};

/// A full sampled drum hit: velocity picks the bank's dynamic layer, the
/// engine's per-key hit counter picks the round-robin take, and the note seed
/// adds per-hit rate/gain/onset micro-variation (per the bank's `DrumJitter`
/// profile) so even a repeated take never renders twice the same. `repitch`
/// scales the playback rate on top of the jitter (1.0 for everything except
/// the toms).
#[cfg(feature = "embedded-samples")]
pub struct SampledDrum {
    data: &'static [i16],
    pos: f32,
    step: f32,
    gain: f32,
    env: f32,
    fade_mul: f32,
    choke_mul: f32,
    /// Samples of silence to emit before playback starts (onset jitter).
    delay: u32,
    /// Modeled sub-sine layered under the sampled attack (kick only; `sub_amp`
    /// is 0 for every other drum, so its render branch is skipped and those
    /// voices stay bit-identical). Virtuosity's 18" jazz kick has its
    /// fundamental at ~80 Hz and no 30-70 Hz content; this synth sub supplies
    /// the deep weight the recording can't — the same sample-attack-plus-model
    /// hybrid the LA layer uses elsewhere. Pitch drops start->end over ~20 ms
    /// (a real kick's beater-then-body swoop), amplitude decays on its own t60.
    sub_phase: f32,
    sub_incr: f32,
    sub_incr_end: f32,
    sub_pitch_mul: f32,
    sub_amp: f32,
    sub_decay: f32,
    #[cfg(test)]
    layer: usize,
    #[cfg(test)]
    rr: usize,
}

/// One strike of a sampled drum: the note velocity, the note seed (drives
/// the micro-variation), and the engine's per-key hit counter (drives the
/// round-robin take and the jitter stratum).
#[cfg(feature = "embedded-samples")]
#[derive(Clone, Copy)]
struct DrumHit {
    vel: u8,
    seed: u32,
    hit_index: u8,
}

#[cfg(feature = "embedded-samples")]
impl SampledDrum {
    fn new(
        bank: &'static ferrosintesis_samples_drumkit::Bank,
        level: f32,
        hit: DrumHit,
        sr: f32,
        repitch: f32,
        jit: &DrumJitter,
    ) -> Self {
        let layer = bank.layer_for_velocity(hit.vel);
        let rr = hit.hit_index as usize % bank.round_robins;
        let mut rng = Rng::new(hit.seed ^ 0x00C1_4BA1);
        let stratum = if jit.strata.is_empty() {
            0.0
        } else {
            jit.strata[hit.hit_index as usize % jit.strata.len()]
        };
        // draw order matters: rate then gain (as before the profiles), then
        // onset — a zero-onset profile thus renders bit-identically to the
        // pre-profile voice
        let rate = 1.0 + stratum + jit.rate * rng.white();
        let gjit = 1.0 + jit.gain * rng.white();
        let delay = (jit.onset_s * sr * (0.5 + 0.5 * rng.white())) as u32;
        SampledDrum {
            data: bank.pcm(layer, rr),
            pos: 0.0,
            step: 44_100.0 / sr * rate * repitch,
            gain: level * vel_amp(hit.vel) * gjit,
            env: 1.0,
            fade_mul: 1.0,
            // hat-grab/CC120 choke: -60 dB in ~15 ms
            choke_mul: 10f32.powf(-3.0 / (0.015 * sr)),
            delay,
            // inert by default; `with_kick_sub` turns it on for the kick only
            sub_phase: 0.0,
            sub_incr: 0.0,
            sub_incr_end: 0.0,
            sub_pitch_mul: 0.0,
            sub_amp: 0.0,
            sub_decay: 0.0,
            #[cfg(test)]
            layer,
            #[cfg(test)]
            rr,
        }
    }

    /// Engage the modeled sub-sine for a kick strike. `level` scales with the
    /// hit; the sub is a fixed proportion of the kick's own sample gain so it
    /// tracks velocity without a second velocity curve.
    fn with_kick_sub(mut self, vel: u8, sr: f32) -> Self {
        let tau = std::f32::consts::TAU;
        self.sub_incr = tau * KICK_SUB_START_HZ / sr;
        self.sub_incr_end = tau * KICK_SUB_END_HZ / sr;
        // (incr - incr_end) decays to ~e^-1 of its span every KICK_SUB_PITCH_S
        self.sub_pitch_mul = (-1.0 / (KICK_SUB_PITCH_S * sr)).exp();
        self.sub_amp = KICK_SUB_LEVEL * vel_amp(vel);
        // amplitude t60
        self.sub_decay = 10f32.powf(-3.0 / (KICK_SUB_T60_S * sr));
        self
    }
}

/// Kick sub-layer voicing. Tuned so the rendered kick's sub(30-70)/mid(140-400)
/// energy ratio lands in the "deep" band without booming; see
/// `sampled_kick_has_deep_sub`.
#[cfg(feature = "embedded-samples")]
const KICK_SUB_START_HZ: f32 = 90.0;
#[cfg(feature = "embedded-samples")]
const KICK_SUB_END_HZ: f32 = 48.0;
#[cfg(feature = "embedded-samples")]
const KICK_SUB_PITCH_S: f32 = 0.020;
#[cfg(feature = "embedded-samples")]
const KICK_SUB_T60_S: f32 = 0.16;
#[cfg(feature = "embedded-samples")]
const KICK_SUB_LEVEL: f32 = 0.55;

/// Sampled-drum voice for a GM channel-10 key (35/36 kick, 37 side stick,
/// 38 snare, 40 electric snare (SNARE repitched up), 41-50 toms, 42/44/46
/// hi-hats, 49/57 crash, 51/59 ride,
/// 53 ride bell, 52 china, 55 splash), or `None` for any other key. The
/// engine's hi-hat choke group keeps working: a closed/pedal hit chokes a
/// ringing open hat through `Voice::choke`, same as the modeled hats.
#[cfg(feature = "embedded-samples")]
pub fn sampled_drum(key: u8, vel: u8, seed: u32, hit_index: u8, sr: f32) -> Option<Box<dyn Voice>> {
    use ferrosintesis_samples_drumkit as kit;
    // The accent cymbals live in a second crate purely so neither package exceeds the
    // crates.io 10 MiB limit; `kit2::CRASH` is the same `kit::Bank` type, carrying its
    // own crate's `BankSource`. The split is invisible from here on out.
    use ferrosintesis_samples_drumkit2 as kit2;
    let (bank, repitch): (&'static kit::Bank, f32) = match key {
        35 | 36 => (&kit::KICK, 1.0),
        37 => (&kit::SIDESTICK, 1.0),
        38 => (&kit::SNARE, 1.0),
        40 => (&kit::SNARE, ELECTRIC_SNARE_REPITCH), // electric snare (MM-BUG-KILN-00008)
        41 => (&kit::TOM_LO, 100.0 / TOM_LO_ROOT_HZ),
        43 => (&kit::TOM_LO, 140.0 / TOM_LO_ROOT_HZ),
        45 => (&kit::TOM_HI, 190.0 / TOM_HI_ROOT_HZ),
        47 => (&kit::TOM_HI, 240.0 / TOM_HI_ROOT_HZ),
        48 => (&kit::TOM_HI, 293.0 / TOM_HI_ROOT_HZ),
        50 => (&kit::TOM_HI, 352.0 / TOM_HI_ROOT_HZ),
        42 => (&kit::HH_CLOSED, 1.0),
        44 => (&kit::HH_PEDAL, 1.0),
        46 => (&kit::HH_OPEN, 1.0),
        49 => (&kit2::CRASH, 1.0),
        // GM names 49 "Crash Cymbal 1" and 57 "Crash Cymbal 2" — two different cymbals.
        // Both played the same bank until 2026-07-26, so a file that scored two crashes
        // heard one, and the sizzle crash shipped in `-drumkit2` with no key able to
        // select it. A sizzle (rivetted) crash is not literally what "crash 2" names,
        // but it IS the second crash this kit owns, and a distinct second cymbal is
        // closer to what the notation asks for than a duplicate of the first.
        57 => (&kit2::CRASH_SIZZLE, 1.0),
        51 | 59 => (&kit::RIDE, 1.0),
        53 => (&kit::RIDE_BELL, 1.0),
        52 => (&kit2::CHINA, 1.0),
        55 => (&kit2::SPLASH, 1.0),
        _ => return None,
    };
    // the unpitched hats take the hard-decorrelation profile; everything
    // else keeps the gentle pitched-drum jitter (see the profile docs)
    let jit = match key {
        42 | 44 | 46 => &HAT_JITTER,
        _ => &DRUM_JITTER,
    };
    let level = DRUM_LEVEL.iter().find(|(k, _)| *k == key).unwrap().1;
    let hit = DrumHit {
        vel,
        seed,
        hit_index,
    };
    let voice = SampledDrum::new(bank, level, hit, sr, repitch, jit);
    // the kick gets a modeled sub-sine under the sampled attack for deep weight
    let voice = if matches!(key, 35 | 36) {
        voice.with_kick_sub(vel, sr)
    } else {
        voice
    };
    Some(Box::new(voice))
}

/// Modeled-only builds have no drum-kit bank; the caller falls back to the
/// models (`drums::make` also forces `samples = false` there).
#[cfg(not(feature = "embedded-samples"))]
pub fn sampled_drum(
    _key: u8,
    _vel: u8,
    _seed: u32,
    _hit_index: u8,
    _sr: f32,
) -> Option<Box<dyn Voice>> {
    None
}

#[cfg(feature = "embedded-samples")]
impl Voice for SampledDrum {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        for o in out.iter_mut() {
            // onset jitter: emit silence until the delay is spent
            if self.delay > 0 {
                self.delay -= 1;
                continue;
            }
            let j = self.pos as usize;
            if j + 1 >= n || self.env < 1e-4 {
                return false;
            }
            let frac = self.pos - j as f32;
            // 4-point cubic read (edge-clamped): the kit samples are repitched
            // along the tom ladder / hat set, and cubic keeps the transient bright.
            let v = crate::dsp::cubic4(
                self.data[j.saturating_sub(1)] as f32,
                self.data[j] as f32,
                self.data[j + 1] as f32,
                self.data[(j + 2).min(n - 1)] as f32,
                frac,
            );
            *o += v * (1.0 / 32768.0) * self.gain * self.env;
            // modeled kick sub (inert for every other drum: sub_amp == 0)
            if self.sub_amp > 1e-6 {
                *o += self.sub_amp * self.env * self.sub_phase.sin();
                self.sub_phase += self.sub_incr;
                self.sub_incr =
                    self.sub_incr_end + (self.sub_incr - self.sub_incr_end) * self.sub_pitch_mul;
                self.sub_amp *= self.sub_decay;
            }
            self.env *= self.fade_mul;
            self.pos += self.step;
        }
        true
    }

    // A struck drum rings out; percussion ignores note-off (house rule,
    // same as `Drum`/`MetalPlate`).
    fn note_off(&mut self) {}

    fn released(&self) -> bool {
        true
    }

    fn choke(&mut self) {
        self.fade_mul = self.choke_mul;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "sampleddrum"
    }
}

// ---------------------------------------------------------------------------
// GongOneShot — CC0=2 GM 14 pitched gong (a full-ring sampled one-shot).
// ---------------------------------------------------------------------------

/// The gong's measured dominant low partial — the repitch root. Both takes'
/// strongest 40-200 Hz partial sits at 99.3-99.5 Hz (≈ G2), by Goertzel scan
/// over the [0.3,2.5] s ring; the 80 Hz partial the sourcing note guessed at is
/// real but 5× weaker. Rooting here makes key 43 (G2, 98 Hz) speak at pitch.
#[cfg(feature = "embedded-samples")]
const GONG_ROOT_HZ: f32 = 99.4;
/// Gong output level. An EAR-tunable knob, defaulted to the modeled tam-tam's
/// gain (`voices::TAMTAM_GAIN`, 0.80) so the two voicings sit at the same level.
#[cfg(feature = "embedded-samples")]
const GONG_LEVEL: f32 = 0.80;
/// Velocity at/above which the loud take is chosen instead of the soft take.
/// A hard switch — the two takes are different recordings, so summing them
/// would comb-filter.
#[cfg(feature = "embedded-samples")]
const GONG_LOUD_VEL: u8 = 84;

/// Both dynamic layers, decoded once (soft, loud). The voice borrows a
/// `&'static [f32]` into the chosen take, so no per-note allocation.
#[cfg(feature = "embedded-samples")]
static GONG_LAYERS: OnceLock<(Vec<f32>, Vec<f32>)> = OnceLock::new();

#[cfg(feature = "embedded-samples")]
fn gong_layers() -> &'static (Vec<f32>, Vec<f32>) {
    init_once!(GONG_LAYERS, {
        (
            parse_wav(embedded_wav("gong_ageng_soft.wav")),
            parse_wav(embedded_wav("gong_ageng_loud.wav")),
        )
    })
}

#[cfg(feature = "embedded-samples")]
fn gong_layer(vel: u8, layers: &'static (Vec<f32>, Vec<f32>)) -> &'static [f32] {
    if vel >= GONG_LOUD_VEL {
        layers.1.as_slice()
    } else {
        layers.0.as_slice()
    }
}

/// A full-ring sampled gong one-shot that OWNS the whole voice (like
/// `SampledDrum`, not the LA attack-plus-model `LaVoice`). Velocity selects the
/// dynamic layer; the note key repitches the entire ring so the gong speaks in
/// the tam-tam register wherever it is written. The prepared sample already
/// ends on a 0.3 s fade to silence, so the voice needs no release envelope — it
/// plays to the end of the ring, then reaps its slot.
#[cfg(feature = "embedded-samples")]
pub struct GongOneShot {
    data: &'static [f32],
    pos: f32,
    step: f32,
    gain: f32,
}

/// One CC0=2 GM 14 gong strike. `seed` is unused (the take is picked by
/// velocity, not round-robin), kept for a uniform voice-factory signature.
#[cfg(feature = "embedded-samples")]
pub fn gong_one_shot(key: u8, vel: u8, sr: f32, _seed: u32) -> Box<dyn Voice> {
    let data = gong_layer(vel, gong_layers());
    // fold with the SAME window as the modeled tam-tam so external MIDIs fold
    // identically, then repitch the sample's ~99 Hz (G2) dominant to the target.
    let repitch = key_freq(crate::voices::fold_key(key, 36, 47)) / GONG_ROOT_HZ;
    Box::new(GongOneShot {
        data,
        pos: 0.0,
        step: 44_100.0 / sr * repitch,
        gain: GONG_LEVEL * vel_amp(vel),
    })
}

/// Modeled-only builds have no gong bank; the caller never reaches here
/// (`altbank::make` only routes to the gong when `samples` is true, which
/// implies the feature), so this stub only satisfies the type-checker.
#[cfg(not(feature = "embedded-samples"))]
pub fn gong_one_shot(_key: u8, _vel: u8, _sr: f32, _seed: u32) -> Box<dyn Voice> {
    panic!("gong one-shot requested from a modeled-only ferrosintesis build")
}

#[cfg(feature = "embedded-samples")]
impl Voice for GongOneShot {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        for o in out.iter_mut() {
            let j = self.pos as usize;
            // reap at the bounded tail: the prepared sample ends at zero.
            if j + 1 >= n {
                return false;
            }
            let frac = self.pos - j as f32;
            // 4-point cubic read (edge-clamped): the gong is repitched off its
            // ~99 Hz root to the written key, so a fractional step is the norm.
            let v = crate::dsp::cubic4(
                self.data[j.saturating_sub(1)],
                self.data[j],
                self.data[j + 1],
                self.data[(j + 2).min(n - 1)],
                frac,
            );
            *o += v * self.gain;
            self.pos += self.step;
        }
        true
    }

    // A struck gong rings out; percussion ignores note-off (house rule).
    fn note_off(&mut self) {}

    fn released(&self) -> bool {
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "gongoneshot"
    }
}

// ---------------------------------------------------------------------------
// GM 120 Guitar Fret Noise — the DEFAULT sampled voice (owner-recorded Eastman
// E1D finger slides, CC0, -fretnoise). A round-robin one-shot: each NoteOn plays
// one of twelve real fret-slide takes, selected by the engine's per-channel
// phase so consecutive events cannot repeat. `--no-samples` and modeled-only
// builds fall back to the `voices::SfxNoise` white-noise burst.
//
// GM SFX are pitch-less, so the take plays at native rate (no key repitch), only
// resampled to the engine rate — this preserves the recorded winding-rasp band
// that the pitch-independence oracle (and real GM semantics) require.
// ---------------------------------------------------------------------------

/// GM 120 fret-noise output level — an EAR-tunable knob (this box has no ears),
/// fitted so the sampled slide sits ~11 dB under a steel-guitar chord, matching
/// the Roland SC-55mkII / Yamaha S-YXG50 references (MM-BUG-KILN-00040). The
/// takes are body-RMS-equalised in the bake, so this one scalar sets the whole
/// bank's level.
#[cfg(feature = "embedded-samples")]
const FRETNOISE_LEVEL: f32 = 0.23;

/// The twelve fret-noise takes, each decoded once to mono f32, in the crate's
/// canonical round-robin order. Not a `Zone` bank (no pitch), so it is a plain
/// lazy cache like `rain_loop` / `gong_layers` — and, like them, it must be
/// reached by both `prewarm()` and `exercise_every_lazy_cache()`.
#[cfg(feature = "embedded-samples")]
static FRETNOISE_TAKES: OnceLock<Vec<Vec<f32>>> = OnceLock::new();

#[cfg(feature = "embedded-samples")]
pub(crate) fn fret_noise_round_robins() -> usize {
    ferrosintesis_samples_fretnoise::ROUND_ROBINS
}

#[cfg(not(feature = "embedded-samples"))]
pub(crate) fn fret_noise_round_robins() -> usize {
    0
}

#[cfg(feature = "embedded-samples")]
fn fret_noise_takes() -> &'static [Vec<f32>] {
    init_once!(FRETNOISE_TAKES, {
        (0..ferrosintesis_samples_fretnoise::ROUND_ROBINS)
            .map(|rr| parse_wav(embedded_wav(ferrosintesis_samples_fretnoise::take_name(rr))))
            .collect::<Vec<Vec<f32>>>()
    })
    .as_slice()
}

/// A fret-noise one-shot that OWNS the whole voice (like `GongOneShot`). The
/// prepared take already fades to silence, so the voice plays to the end of the
/// slide and then reaps its slot — it ignores note-off, because a fret slide is a
/// fixed gesture whose length is the recording's, not the key's.
#[cfg(feature = "embedded-samples")]
pub struct FretNoiseOneShot {
    data: &'static [f32],
    rr: usize,
    pos: f32,
    step: f32,
    gain: f32,
}

/// The default GM 120 sampled voice. `rr` is the engine-owned round-robin
/// phase and wraps at the derived bank length; `vel` scales level. `None` on a
/// modeled-only build, where the caller falls back to `SfxNoise`.
#[cfg(feature = "embedded-samples")]
pub fn sampled_fret_noise(vel: u8, sr: f32, rr: usize) -> Option<Box<dyn Voice>> {
    let takes = fret_noise_takes();
    if takes.is_empty() {
        return None;
    }
    let rr = rr % takes.len();
    Some(Box::new(FretNoiseOneShot {
        data: takes[rr].as_slice(),
        rr,
        pos: 0.0,
        // native rate, resampled to the engine rate — GM SFX carry no pitch, so
        // the written key does NOT repitch the take.
        step: 44_100.0 / sr,
        gain: FRETNOISE_LEVEL * vel_amp(vel),
    }))
}

/// Modeled-only builds have no fret-noise bank; the caller falls back to the
/// modeled `SfxNoise` burst.
#[cfg(not(feature = "embedded-samples"))]
pub fn sampled_fret_noise(_vel: u8, _sr: f32, _rr: usize) -> Option<Box<dyn Voice>> {
    None
}

#[cfg(feature = "embedded-samples")]
impl Voice for FretNoiseOneShot {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        for o in out.iter_mut() {
            let j = self.pos as usize;
            // reap at the bounded tail: the prepared take ends at zero.
            if j + 1 >= n {
                return false;
            }
            let frac = self.pos - j as f32;
            // 4-point cubic read (edge-clamped): the take is resampled off 44.1 kHz
            // to the engine rate, so a fractional step is the norm.
            let v = crate::dsp::cubic4(
                self.data[j.saturating_sub(1)],
                self.data[j],
                self.data[j + 1],
                self.data[(j + 2).min(n - 1)],
                frac,
            );
            *o += v * self.gain;
            self.pos += self.step;
        }
        true
    }

    // A fret slide is a fixed gesture; it ignores note-off and plays to its end
    // (house rule, same as the ring-out gong / struck drum).
    fn note_off(&mut self) {}

    fn released(&self) -> bool {
        true
    }

    fn rr_phase(&self) -> Option<usize> {
        Some(self.rr)
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "fretnoise"
    }
}

// --- GM 7 clavinet: the DEFAULT sampled voice (MuseScore MS Basic, MIT) ----------
//
// Eleven baked decaying notes (sounding G1-G6, pitch-synchronous loops) picked by
// `nearest` and repitched per key. Unlike the ring-out gong, a clavinet string is
// DAMPED on key release, so note-off starts a fast release fade. `--no-samples` and
// the CC0-nonzero alt bank use the modeled `Pluck(&CLAVINET)` instead (routed in
// `voices::make` / `altbank::make`).

/// Clavinet output level — an EAR-tunable knob (this box has no ears), roughly
/// level-matched to the modeled clavinet it replaces as the default voice.
#[cfg(feature = "embedded-samples")]
const CLAVINET_LEVEL: f32 = 0.80;
/// Note-off damp time (t60): a clavinet string is stopped by the key, so it mutes
/// fast — the release, not the baked body decay, governs a short note.
#[cfg(feature = "embedded-samples")]
const CLAVINET_RELEASE_T60: f32 = 0.06;

/// GM 7 clavinet sampled bank: 11 baked decaying notes, sounding G1-G6. Roots are the
/// exact nominal fundamentals — the bake loops pitch-synchronously to `originalPitch`,
/// so the sustained pitch is dead-on and `nearest` repitches minimally per key.
fn clavinet() -> &'static [Zone] {
    static B: OnceLock<Vec<Zone>> = OnceLock::new();
    init_once!(B, {
        bank!(
            "clavinet_G1.wav" => 49.00,
            "clavinet_C2.wav" => 65.41,
            "clavinet_G2.wav" => 98.00,
            "clavinet_C3.wav" => 130.81,
            "clavinet_G3.wav" => 196.00,
            "clavinet_C4.wav" => 261.63,
            "clavinet_G4.wav" => 392.00,
            "clavinet_C5.wav" => 523.25,
            "clavinet_G5.wav" => 783.99,
            "clavinet_C6.wav" => 1046.50,
            "clavinet_G6.wav" => 1567.98,
        )
    })
}

/// GM 7 clavinet sampled bank (see [`clavinet`]).
pub fn clavinet_bank() -> &'static [Zone] {
    clavinet()
}

/// GM 7 clavinet: the DEFAULT sampled voice. Plays the nearest baked zone repitched
/// to the key (like [`GongOneShot`]), but a clavinet is DAMPED on key release, so
/// note-off starts a fast release fade instead of ringing out.
#[cfg(feature = "embedded-samples")]
pub struct ClavinetSampled {
    data: &'static [f32],
    pos: f32,
    base_step: f32,
    bend: f32,
    gain: f32,
    rel_mul: f32,
    env: f32,
    releasing: bool,
}

/// One clavinet note: nearest baked zone, repitched to the key. `seed` is unused
/// (no round robins), kept for a uniform voice-factory signature.
#[cfg(feature = "embedded-samples")]
pub fn clavinet_sampled(key: u8, vel: u8, sr: f32, _seed: u32) -> Box<dyn Voice> {
    let f = key_freq(key);
    let zone = nearest(clavinet_bank(), f);
    Box::new(ClavinetSampled {
        data: zone.data.as_slice(),
        pos: 0.0,
        base_step: 44_100.0 / sr * (f / zone.root),
        bend: 1.0,
        gain: CLAVINET_LEVEL * vel_amp(vel),
        rel_mul: 10f32.powf(-3.0 / (CLAVINET_RELEASE_T60 * sr)),
        env: 1.0,
        releasing: false,
    })
}

/// Modeled-only builds have no clavinet bank; the caller never reaches here
/// (`voices::make` routes to this only when `samples` is true, which implies the
/// feature), so this stub only satisfies the type-checker.
#[cfg(not(feature = "embedded-samples"))]
pub fn clavinet_sampled(_key: u8, _vel: u8, _sr: f32, _seed: u32) -> Box<dyn Voice> {
    panic!("clavinet sample requested from a modeled-only ferrosintesis build")
}

#[cfg(feature = "embedded-samples")]
impl Voice for ClavinetSampled {
    fn render(&mut self, out: &mut [f32]) -> bool {
        let n = self.data.len();
        let step = self.base_step * self.bend;
        for o in out.iter_mut() {
            let j = self.pos as usize;
            // reap at the bounded tail: the baked note ends on a fade to zero.
            if j + 1 >= n {
                return false;
            }
            let frac = self.pos - j as f32;
            // 4-point cubic read (edge-clamped): the clavinet zone is repitched
            // to the key (and pitch-bent), so reads land between samples.
            let v = crate::dsp::cubic4(
                self.data[j.saturating_sub(1)],
                self.data[j],
                self.data[j + 1],
                self.data[(j + 2).min(n - 1)],
                frac,
            );
            *o += v * self.gain * self.env;
            self.pos += step;
            if self.releasing {
                self.env *= self.rel_mul;
                if self.env < 1e-4 {
                    return false;
                }
            }
        }
        true
    }

    fn note_off(&mut self) {
        self.releasing = true;
    }

    fn released(&self) -> bool {
        self.releasing
    }

    fn set_pitch(&mut self, mult: f32) {
        self.bend = mult;
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "clavinetsampled"
    }
}

#[cfg(all(test, feature = "embedded-samples"))]
mod tests {
    use super::*;
    use crate::dsp::OnePole;
    use crate::voices;
    use crate::voices::Voice;

    fn assert_gong_provenance_matches_velocity_boundary(provenance: &str, loud_vel: u8) {
        let soft_max = loud_vel
            .checked_sub(1)
            .expect("the loud gong boundary must leave a soft velocity range");
        let hard_switch = format!("hard switch at velocity {loud_vel}");
        let soft_range = format!("soft through velocity {soft_max}");
        assert!(
            provenance.contains(&hard_switch),
            "gong provenance must name the shipped {hard_switch}"
        );
        assert!(
            provenance.contains(&soft_range),
            "gong provenance must name the shipped {soft_range}"
        );
        assert!(
            !provenance.contains("velocity-crossfades"),
            "gong provenance must not claim that the two recordings are summed"
        );
    }

    #[test]
    fn gong_provenance_describes_the_shipped_velocity_boundary() {
        let layers = gong_layers();
        assert!(
            std::ptr::eq(gong_layer(GONG_LOUD_VEL - 1, layers), layers.0.as_slice()),
            "the velocity below GONG_LOUD_VEL must select only the soft gong take"
        );
        assert!(
            std::ptr::eq(gong_layer(GONG_LOUD_VEL, layers), layers.1.as_slice()),
            "GONG_LOUD_VEL must select only the loud gong take"
        );
        let provenance = include_str!("../../ferrosintesis-samples-gong/PROVENANCE.md");
        assert_gong_provenance_matches_velocity_boundary(provenance, GONG_LOUD_VEL);
    }

    #[test]
    #[should_panic(expected = "gong provenance must name the shipped hard switch")]
    fn gong_provenance_guard_rejects_a_stale_velocity_boundary() {
        let provenance = include_str!("../../ferrosintesis-samples-gong/PROVENANCE.md");
        assert_gong_provenance_matches_velocity_boundary(provenance, GONG_LOUD_VEL + 1);
    }

    // ---------------------------------------------------------------------------
    // Prewarm coverage (MM-BUG-KILN-00059)
    //
    // `RealtimeSynth::prewarm_samples()` promises that no sample bank decodes inside
    // the deadline-bearing audio callback. That promise was kept by a hand-maintained
    // list of calls in `prewarm()`, and the list had drifted: 22 of the 46 public bank
    // accessors were never touched, including every alternative piano bank, the
    // saxophones, the clavinet, the harpsichord and the whole bass family. Each new
    // bank landed in its own change and nobody re-read the whole list.
    //
    // Two oracles close that loop. One pins the exercise list against the source, so a
    // new accessor cannot land without being covered; the other proves prewarm reaches
    // everything the exercise list can reach. Neither can be satisfied by a partial
    // list.
    //
    // Scope: `bank!`-built `Zone` banks. The drum-kit crate's PCM cache is a separate
    // mechanism and is prewarmed by its own explicit call.
    // ---------------------------------------------------------------------------

    /// Every public bank accessor, swept across its full argument space.
    ///
    /// The sweep is deliberately exhaustive rather than representative: several
    /// accessors fan out internally on velocity or program boundaries (`grand_bank`
    /// selects among six statics, `sax_bank` among eight), and representative values
    /// walk straight past a boundary a real MIDI file would hit.
    ///
    /// Hand-maintained by necessity — Rust cannot enumerate functions — which is
    /// exactly the drift this bug was about, so
    /// `every_public_bank_accessor_is_exercised` pins it against the source.
    fn exercise_every_public_bank() {
        for &(vel, rr2) in &[
            (1u8, false),
            (1, true),
            (80, false),
            (80, true),
            (127, false),
            (127, true),
        ] {
            let _ = piano_bank(vel, rr2);
            let _ = grand_bank(vel, rr2);
            let _ = steinwayb_bank(vel, rr2);
            let _ = kawai_bank(vel, rr2);
            let _ = headroom_bank(vel, rr2);
            let _ = musescoregrand_bank(vel, rr2);
            let _ = darkgrand_bank(vel, rr2);
            let _ = ydpgrand_bank(vel, rr2);
            let _ = honkytonk_bank(vel, rr2);
            let _ = b1upright_bank(vel, rr2);
        }
        for vel in 0u8..=127 {
            let _ = violin_bank(vel);
            let _ = viola_bank(vel);
            let _ = cello_bank(vel);
            let _ = contrabass_bank(vel);
            let _ = strings_bank(vel);
        }
        // The mandolin fans out on ROUND ROBIN rather than velocity (it is a
        // single-dynamic bank). Sweep past the wrap so the modulo is exercised —
        // the engine feeds this a strike counter that grows without bound.
        for rr in 0..(MANDOLIN_ROUND_ROBINS * 2 + 1) {
            let _ = mandolin_bank(rr);
        }
        for program in 0u8..=127 {
            for vel in [0u8, 64, 127] {
                let _ = brass_bank(program, vel);
                let _ = reed_bank(program, vel);
                let _ = sax_bank(program, vel);
            }
        }
        let _ = banjo_bank();
        let _ = bottle_bank();
        let _ = celesta_bank();
        let _ = chanter_bank();
        let _ = clavinet_bank();
        let _ = drone_g2_bank();
        let _ = drone_g3_bank();
        let _ = dulcimer_bank();
        let _ = finger_bass_bank();
        let _ = flute_bank();
        let _ = glock_bank();
        let _ = guitar_bank();
        let _ = harp_bank();
        let _ = harpsichord_bank();
        let _ = marimba_bank();
        let _ = musicbox_bank();
        let _ = ocarina_bank();
        let _ = panflute_bank();
        let _ = pick_bass_bank();
        let _ = pizzbass_bank();
        let _ = recorder_bank();
        let _ = eastman_picked_bank();
        let _ = eastman_plucked_bank();
        let _ = rhodes_bank();
        let _ = shakuhachi_bank();
        let _ = sitar_bank();
        let _ = steel_bank();
        let _ = timpani_bank();
        let _ = tubular_bank();
        let _ = vibraphone_bank();
        let _ = xylo_bank();
    }

    /// Every lazy cache in the module, not only the ones behind a `pub *_bank`.
    ///
    /// `exercise_every_public_bank` is the bulk of it, but a cache reached by a private
    /// accessor (`chanter_rr2`, `bottle_loop_bank`), or holding something other than a
    /// `Zone` bank (`rain_loop`, `gong_layers`), has no public `*_bank` wrapper to be
    /// swept through — which is exactly how four of them stayed invisible to the
    /// KILN-00059 oracles (MM-BUG-KILN-00073).
    /// `every_lazy_cache_is_reached_by_the_exercise_sweep` pins this against the
    /// `static _: OnceLock<_>` declarations the source carries, so it cannot drift.
    fn exercise_every_lazy_cache() {
        exercise_every_public_bank();
        let _ = chanter_rr2();
        let _ = bottle_loop_bank();
        let _ = rain_loop();
        let _ = gong_layers();
        let _ = fret_noise_takes();
    }

    /// The source's own `static _: OnceLock<_>` declarations: (line, enclosing item).
    ///
    /// The enumeration predicate IS the fix here. `pub fn *_bank` was a hand-maintained
    /// assumption wearing a source-scan's clothing: it described the naming convention
    /// most caches happen to follow, not the property that makes one a realtime hazard —
    /// being lazily initialized. This keys off the `OnceLock` itself.
    fn declared_lazy_caches(src: &str) -> Vec<(u32, String)> {
        let mut item = String::from("<module>");
        let mut out = Vec::new();
        for (i, l) in src.lines().enumerate() {
            let t = l.trim_start();
            if let Some(rest) = t
                .strip_prefix("pub fn ")
                .or_else(|| t.strip_prefix("pub(crate) fn "))
                .or_else(|| t.strip_prefix("fn "))
            {
                if let Some(name) = rest.split('(').next() {
                    item = name.to_string();
                }
            }
            if t.starts_with("static ") && t.contains(": OnceLock<") {
                // A cache inside an accessor is named by that accessor; a module-level
                // one (`GONG_LAYERS`) has no enclosing fn, so it is named by itself —
                // never by whatever function happened to be declared above it.
                let label = if l.starts_with("static ") {
                    t.trim_start_matches("static ")
                        .split(':')
                        .next()
                        .unwrap_or("<static>")
                        .to_string()
                } else {
                    item.clone()
                };
                out.push((i as u32 + 1, label));
            }
        }
        out
    }

    /// Read `sampler.rs`, the module these oracles are derived from.
    fn sampler_source() -> String {
        std::fs::read_to_string(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("src")
                .join("sampler.rs"),
        )
        .expect("sampler.rs is readable from its own crate")
    }

    /// No cache may be initialized outside the counted `init_once!` funnel.
    ///
    /// This is what makes the coverage oracles TOTAL rather than merely current: a new
    /// `static _: OnceLock<_>` filled by a bare `get_or_init` would be invisible to the
    /// site registry, and both oracles below would keep passing while covering less —
    /// the precise failure mode of MM-BUG-KILN-00073, where `GONG_LAYERS` was invisible
    /// to *both* guards because it was not built by `bank!`.
    ///
    /// One sanctioned exception: `Zone::sustain_loop`'s memo, which is not a static and
    /// carries its own counter (`LOOP_SEARCHES`) and its own oracle.
    #[test]
    fn no_lazy_cache_bypasses_init_once() {
        let src = sampler_source();
        // Only the shipped module: this module's own test code is not a realtime path,
        // and its string literals would otherwise match themselves.
        let shipped = src
            .split_once("#[cfg(all(test, feature = \"embedded-samples\"))]")
            .expect("the test module marks the end of the shipped module")
            .0;
        let lines: Vec<&str> = shipped.lines().collect();
        let offenders: Vec<(usize, &str)> = lines
            .iter()
            .enumerate()
            .filter(|(_, l)| l.contains("get_or_init("))
            .filter(|(i, l)| {
                // The funnel's own definition, and `Zone::sustain_loop`'s memo — a
                // struct field, not a static, with its own counter and oracle.
                let t = l.trim_start();
                let near = lines[i.saturating_sub(3)..*i].join(" ");
                !t.starts_with("$cell.get_or_init(") && !near.contains(".sustain_loop")
            })
            .map(|(i, l)| (i + 1, l.trim()))
            .collect();

        assert!(
            offenders.is_empty(),
            "{} cache initialization(s) bypass the counted `init_once!` funnel, so the \
             prewarm-coverage oracles cannot see them:\n  {}\n\nUse `init_once!(CELL, \
             <builder>)` instead of a bare `get_or_init`.",
            offenders.len(),
            offenders
                .iter()
                .map(|(n, l)| format!("sampler.rs:{n}: {l}"))
                .collect::<Vec<_>>()
                .join("\n  ")
        );
    }

    /// `prewarm()` initializes EVERY lazy cache — measured in a pristine process.
    ///
    /// Two properties, both required, both order-dependent and so both measured where
    /// nothing else has run:
    ///   (a) the exercise sweep REACHES every declared cache — otherwise (b) is vacuous
    ///       for whatever it misses, which is how four caches hid behind the KILN-00059
    ///       oracles;
    ///   (b) prewarm leaves NOTHING for the sweep to initialize — the realtime contract.
    ///
    /// **The re-exec is load-bearing.** `CACHE_INIT_SITES` is process-global and
    /// `get_or_init` runs its builder exactly once ever, so any cache a *concurrent* test
    /// happened to touch first is already recorded when this test snapshots: the delta
    /// would be empty and the assertion would pass while prewarm covered nothing. That is
    /// a false GREEN, not a flake — it cannot be retried away, and it is precisely the
    /// "oracle silently covers less" failure MM-BUG-KILN-00073 is about. So the real work
    /// runs in a child process running this test alone.
    #[test]
    fn prewarm_covers_every_lazy_cache() {
        const PROBE: &str = "FERRO_PREWARM_PROBE";
        const NAME: &str = "sampler::tests::prewarm_covers_every_lazy_cache";

        if std::env::var_os(PROBE).is_none() {
            let out = std::process::Command::new(
                std::env::current_exe().expect("the test binary's own path"),
            )
            .args([NAME, "--exact", "--nocapture", "--test-threads=1"])
            .env(PROBE, "1")
            .output()
            .expect("re-exec this test binary");
            assert!(
                out.status.success(),
                "the pristine-process probe failed:\n{}\n{}",
                String::from_utf8_lossy(&out.stdout),
                String::from_utf8_lossy(&out.stderr)
            );
            return;
        }

        // --- child: nothing else in this process has touched a cache ---
        let src = sampler_source();
        let declared = declared_lazy_caches(&src);
        assert!(
            declared.len() > 100,
            "found only {} lazy caches — the scan is not reading what it thinks it is",
            declared.len()
        );
        // Nearest preceding declaration owns each recorded init site.
        let owner = |line: u32| {
            declared
                .iter()
                .rfind(|(decl, _)| *decl <= line)
                .map(|(decl, item)| (*decl, item.clone()))
                .expect("an init site always follows its own static declaration")
        };
        let sites = || CACHE_INIT_SITES.lock().expect("registry").clone();

        prewarm();
        let after_prewarm = sites();
        exercise_every_lazy_cache();
        let after_exercise = sites();

        // (a) the sweep reaches everything the source declares
        let reached: std::collections::BTreeSet<u32> =
            after_exercise.iter().map(|&l| owner(l).0).collect();
        let unreached: Vec<String> = declared
            .iter()
            .filter(|(line, _)| !reached.contains(line))
            .map(|(line, item)| format!("sampler.rs:{line} ({item})"))
            .collect();
        assert!(
            unreached.is_empty(),
            "{} of {} lazy cache(s) are never initialized by prewarm() + the exercise \
             sweep, so the coverage check is blind to them:\n  {}\n\nAdd each to \
             exercise_every_lazy_cache().",
            unreached.len(),
            declared.len(),
            unreached.join("\n  ")
        );

        // (b) prewarm left nothing for the sweep to initialize
        let late: Vec<String> = after_exercise
            .difference(&after_prewarm)
            .map(|&line| {
                let (decl, item) = owner(line);
                format!("sampler.rs:{decl} ({item})")
            })
            .collect();
        assert!(
            late.is_empty(),
            "{} lazy cache(s) were still uninitialized after prewarm() and initialized on \
             first use. In the realtime path that work happens inside fill_ring()'s \
             deadline-bearing block, which is the dropout prewarm_samples() exists to \
             prevent:\n  {}\n\nAdd each to sampler::prewarm().",
            late.len(),
            late.join("\n  ")
        );
    }

    /// The exercise list above covers every public bank accessor the source declares.
    ///
    /// Without this, adding a bank and forgetting `exercise_every_public_bank` would
    /// silently shrink what `prewarm_leaves_no_bank_uninitialized` can detect — the
    /// coverage oracle would keep passing while covering less.
    #[test]
    fn every_public_bank_accessor_is_exercised() {
        let src = std::fs::read_to_string(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("src")
                .join("sampler.rs"),
        )
        .expect("sampler.rs is readable from its own crate");

        let declared: Vec<String> = src
            .lines()
            .filter_map(|l| l.trim().strip_prefix("pub fn "))
            .filter_map(|rest| rest.split('(').next())
            .filter(|name| name.ends_with("_bank"))
            .map(str::to_string)
            .collect();

        assert!(
            declared.len() > 20,
            "found only {} public bank accessors — the scan is not reading what it \
             thinks it is",
            declared.len()
        );

        // The body of the exercise fn, so a mention in this comment cannot count.
        let body = src
            .split_once("fn exercise_every_public_bank() {")
            .expect("exercise_every_public_bank must exist")
            .1;
        let body = body
            .split_once("\n    }")
            .expect("its body must terminate")
            .0;

        let missing: Vec<&String> = declared
            .iter()
            .filter(|name| !body.contains(&format!("{name}(")))
            .collect();

        assert!(
            missing.is_empty(),
            "{} public bank accessor(s) are not exercised, so the prewarm-coverage \
             oracle silently does not cover them:\n  {}\n\nAdd each to \
             exercise_every_public_bank().",
            missing.len(),
            missing
                .iter()
                .map(|s| s.as_str())
                .collect::<Vec<_>>()
                .join("\n  ")
        );
    }

    /// After `prewarm()`, no bank decodes again — the realtime contract.
    ///
    /// Race-free despite parallel tests: once `prewarm()` returns, every bank it covers
    /// is initialized, so `BANK_INITS` is stable and no other thread can move it. A
    /// concurrent test that raced ahead of `prewarm()` incremented the counter *before*
    /// the snapshot, because `OnceLock::get_or_init` runs its closure exactly once.
    ///
    /// If this fails, the named count is how many banks a realtime NoteOn would decode
    /// inside the audio callback.
    #[test]
    fn prewarm_leaves_no_bank_uninitialized() {
        use std::sync::atomic::Ordering;

        prewarm();
        let after_prewarm = BANK_INITS.load(Ordering::SeqCst);

        exercise_every_public_bank();
        let after_exercise = BANK_INITS.load(Ordering::SeqCst);

        assert_eq!(
            after_prewarm,
            after_exercise,
            "{} sample bank(s) were still uninitialized after prewarm() and decoded on \
             first use. In the realtime path that decode happens inside fill_ring()'s \
             deadline-bearing block, which is the dropout prewarm_samples() exists to \
             prevent. Add the missing bank(s) to sampler::prewarm().",
            after_exercise - after_prewarm
        );
    }

    /// Every independently packaged drum-kit cache must have an explicit prewarm
    /// hook. Derive the package set from Cargo.toml so a third size split cannot
    /// silently repeat MM-BUG-KILN-00125.
    #[test]
    fn every_drumkit_package_cache_is_explicitly_prewarmed() {
        let manifest = std::fs::read_to_string(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("Cargo.toml"),
        )
        .expect("ferrosintesis Cargo.toml is readable");
        let packages: Vec<&str> = manifest
            .lines()
            .filter_map(|line| line.split_once(" = {").map(|(name, _)| name))
            .filter(|name| name.starts_with("ferrosintesis-samples-drumkit"))
            .collect();
        assert!(
            packages.len() >= 2,
            "found only {} drum-kit packages — the package scan proves nothing",
            packages.len()
        );

        let src = std::fs::read_to_string(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("src")
                .join("sampler.rs"),
        )
        .expect("sampler.rs is readable from its own crate");
        let body = src
            .split_once("pub fn prewarm() {")
            .expect("prewarm must exist")
            .1
            .split_once("\n}")
            .expect("its body must terminate")
            .0;
        let missing: Vec<&str> = packages
            .iter()
            .copied()
            .filter(|package| {
                let crate_name = package.replace('-', "_");
                !body.contains(&format!("{crate_name}::prewarm();"))
            })
            .collect();
        assert!(
            missing.is_empty(),
            "drum-kit package cache(s) {missing:?} are absent from sampler::prewarm(); \
             the first routed NoteOn would decode them inside the realtime callback"
        );
    }

    /// After `prewarm()`, no NoteOn runs a sustain-loop SEARCH — the other half of the
    /// realtime contract (MM-BUG-KILN-00064).
    ///
    /// Decoding the bank is only half the setup. `SaxLoopVoice`/`BottleLoopVoice`
    /// construction also needs the zone's pitch-synchronous loop bounds, and finding those
    /// is an O(starts x lengths x window) scan of the static PCM — 67.4 million
    /// multiply-accumulates and 30,560 square roots for the blown bottle's 72,765-frame
    /// recording, *per NoteOn*, inside `fill_ring()`'s deadline-bearing block.
    ///
    /// The OUT-OF-WINDOW keys are load-bearing. Those repitch outside 0.5..=2.05x the
    /// zone root and fall back to the modeled voice — and before the fix they still paid
    /// the whole search to learn that, because the constructor searched before it checked
    /// the ratio. A window-only key list would let that cost hide behind the fallback.
    ///
    /// Race-free after `prewarm()` for the same reason as
    /// `prewarm_leaves_no_bank_uninitialized`: once it returns, every reachable zone's
    /// `sustain_loop` cell is resolved, so no other thread can move the counter. The
    /// failure mode is therefore safe in one direction — when the invariant holds nothing
    /// increments at all, so a concurrent test cannot manufacture a false RED; when it is
    /// already broken, a sibling oracle's own burst can inflate the reported count. Read
    /// the number as "at least this many", and rerun with `--test-threads=1` to attribute.
    #[test]
    fn prewarm_leaves_no_sustain_loop_unsearched() {
        use std::sync::atomic::Ordering;

        prewarm();
        let searches_before = LOOP_SEARCHES.load(Ordering::SeqCst);
        let banks_before = BANK_INITS.load(Ordering::SeqCst);

        assert!(
            searches_before > 0,
            "prewarm() resolved no sustain loop at all — the counter is not wired to the \
             searches, so this oracle proves nothing"
        );

        // GM 76 blown bottle. The 205 Hz root gives a ~102..420 Hz window (keys ~44..68);
        // 30/40 and 70/100 sit outside it, on both sides.
        for key in [30u8, 40, 44, 48, 55, 60, 67, 68, 70, 100] {
            let _ = bottle_loop_voice(key, 100, 44_100.0, 7);
        }
        // GM 64-67 sax, both velocity layers, across the keyboard.
        for program in 64u8..=67 {
            for vel in [1u8, 127] {
                for key in [12u8, 21, 48, 60, 72, 108, 127] {
                    let _ = sax_loop_voice(program, key, vel, 44_100.0, 7);
                }
            }
        }

        let searched = LOOP_SEARCHES.load(Ordering::SeqCst) - searches_before;
        let decoded = BANK_INITS.load(Ordering::SeqCst) - banks_before;
        assert_eq!(
            searched, 0,
            "{searched} sustain-loop search(es) ran during voice construction after \
             prewarm(). Each one scans static PCM inside the audio callback (67.4 M \
             multiply-accumulates for the bottle) and is exactly the dropout \
             prewarm_samples() exists to prevent. Resolve the zone's loop in \
             sampler::prewarm() and read it through Zone::sustain_loop."
        );
        assert_eq!(
            decoded, 0,
            "{decoded} sample bank(s) decoded during looped-sustain voice construction \
             after prewarm(). Add them to sampler::prewarm()."
        );
    }

    /// Every sustain-loop search must be reachable ONLY through the memo, and every one
    /// must be warmed by `prewarm()` (MM-BUG-KILN-00064).
    ///
    /// The behavioural oracle above enumerates the looped-sustain voices by hand, so on
    /// its own it silently shrinks the moment someone adds a third one — the same
    /// hand-maintained-list defect that produced KILN-00059/00060/00069. This one derives
    /// the set from the source instead: it finds every `find_*_loop` the file declares,
    /// then requires (a) no call site bypasses `Zone::sustain_loop`, and (b) `prewarm()`
    /// mentions each. A new looped bank therefore cannot land un-prewarmed.
    #[test]
    fn every_sustain_loop_search_is_memoized_and_prewarmed() {
        let src = std::fs::read_to_string(
            std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                .join("src")
                .join("sampler.rs"),
        )
        .expect("sampler.rs is readable from its own crate");

        let declared: Vec<&str> = src
            .lines()
            .filter_map(|l| l.trim().strip_prefix("fn find_"))
            .filter_map(|rest| rest.split('(').next())
            .filter(|name| name.ends_with("_loop"))
            .collect();
        assert!(
            declared.len() >= 2,
            "found only {} sustain-loop searches ({declared:?}) — the scan is not reading \
             what it thinks it is",
            declared.len()
        );

        // (a) Every call site goes through the memo. Code lines only: a doc comment naming
        // a search must not launder a real bypass, and vice versa.
        let bypasses: Vec<String> = src
            .lines()
            .enumerate()
            .filter(|(_, l)| !l.trim_start().starts_with("//"))
            .filter(|(_, l)| !l.trim_start().starts_with("fn find_"))
            .filter(|(_, l)| {
                declared
                    .iter()
                    .any(|n| l.contains(&format!("find_{n}(")) && !l.contains("sustain_loop("))
            })
            .map(|(i, l)| format!("sampler.rs:{}: {}", i + 1, l.trim()))
            .collect();
        assert!(
            bypasses.is_empty(),
            "{} sustain-loop call site(s) bypass Zone::sustain_loop and re-run the search \
             on every call:\n  {}\n\nCall it as zone.sustain_loop(find_..._loop) so the \
             answer is computed once, off the realtime thread.",
            bypasses.len(),
            bypasses.join("\n  ")
        );

        // (b) prewarm() forces each one, so no first NoteOn pays for it.
        let body = src
            .split_once("pub fn prewarm() {")
            .expect("prewarm must exist")
            .1;
        let body = body.split_once("\n}").expect("its body must terminate").0;
        let unwarmed: Vec<&&str> = declared
            .iter()
            .filter(|n| !body.contains(&format!("find_{n}")))
            .collect();
        assert!(
            unwarmed.is_empty(),
            "sustain-loop search(es) {unwarmed:?} are never forced by sampler::prewarm(), \
             so the first NoteOn that needs one still runs it inside the audio callback. \
             Warm every zone of the owning bank there."
        );
    }

    use ferrosintesis_samples_drumkit as kitbank;
    use ferrosintesis_samples_drumkit2 as kitbank2;

    /// LoopVoice must sustain INDEFINITELY across many loop wraps — the runtime
    /// counterpart to prepare.py's offline seam gate (§7.1). Rendered at a
    /// REPITCHED key (A4 vs the F4-G5 zone roots, so step != 1) for far longer
    /// than one loop (~0.4 s): the RMS stays flat across three disjoint windows.
    /// This directly catches the two ways a wrap breaks — a one-shot player's
    /// `data[j+1]` panics at the seam, and a "stop at end" player goes silent
    /// after the first loop (later windows would read ~0).
    #[test]
    fn bagpipe_loop_sustains_across_wraps() {
        let sr = 44100.0;
        let mut v = bagpipe_chanter_loop(69, sr, 0);
        let mut buf = vec![0f32; (1.6 * sr) as usize];
        assert!(v.render(&mut buf), "chanter loop finished early");
        let rms = |s: &[f32]| {
            (s.iter().map(|x| (x * x) as f64).sum::<f64>() / s.len() as f64).sqrt() as f32
        };
        let e = |t0: f32, t1: f32| rms(&buf[(t0 * sr) as usize..(t1 * sr) as usize]);
        let (a, b, c) = (e(0.2, 0.4), e(0.7, 0.9), e(1.3, 1.5));
        assert!(buf.iter().all(|x| x.is_finite()), "non-finite in the loop");
        assert!(a > 1e-3, "loop is silent");
        // flat within 20% across ~3 loop lengths -> the wrap keeps producing
        for (lbl, x) in [("mid", b), ("late", c)] {
            assert!(
                (x / a - 1.0).abs() < 0.2,
                "loop level not flat at {lbl}: {a:.4} -> {x:.4} (a broken wrap \
                 would go silent or decay)"
            );
        }
    }

    /// The mandolin zone tables are forty hand-transcribed roots, and the failure
    /// they invite is silent: a mistyped or octave-shifted root still renders, just
    /// at the wrong pitch. This checks them WITHOUT re-typing the same numbers,
    /// which would only prove the copy-paste.
    ///
    /// Two independent, non-circular oracles:
    ///
    /// 1. **Interval structure.** The ten zones are open + 5th fret on four courses
    ///    plus the 10th and 12th on the E course, so their semitone steps are fixed
    ///    by the fretboard: 5, 2, 5, 2, 5, 2, 5, 5, 2. Any octave error, swapped
    ///    file or fat-fingered digit breaks that sequence. The ±60-cent tolerance
    ///    absorbs the instrument's real intonation (fretted notes run up to +22
    ///    cents sharp, so a nominal-2-semitone step genuinely measures ~1.67) while
    ///    still being four times tighter than the smallest error it must catch.
    /// 2. **Cross-take agreement.** `rr1` through `rr4` are the same ten physical
    ///    notes measured from independent takes, so their roots must agree closely.
    ///    A wrong root in one take cannot hide, because the other three disagree.
    ///
    /// Forcing both banks to decode also exercises `parse_wav`'s 16-bit/mono/44100
    /// assertion and proves `embedded_wav` can actually resolve the names through
    /// the asset-crate chain — a missing crate arm panics here rather than at a
    /// user's first mandolin note.
    #[test]
    fn mandolin_zone_roots_match_the_fretboard() {
        const STEPS: [f32; 9] = [5.0, 2.0, 5.0, 2.0, 5.0, 2.0, 5.0, 5.0, 2.0];
        let cents = |a: f32, b: f32| 1200.0 * (b / a).log2();

        let sets: Vec<&'static [Zone]> = (0..MANDOLIN_ROUND_ROBINS).map(mandolin_bank).collect();
        for i in 1..sets.len() {
            assert!(
                !std::ptr::eq(sets[0], sets[i]),
                "round robin {i} must be a distinct take-set from rr1"
            );
        }
        assert!(
            std::ptr::eq(sets[0], mandolin_bank(MANDOLIN_ROUND_ROBINS)),
            "the round-robin index must WRAP, so a strike counter can grow without bound"
        );

        for (i, zones) in sets.iter().enumerate() {
            let label = format!("rr{}", i + 1);
            assert_eq!(zones.len(), 10, "{label} take-set must have ten zones");
            for (i, z) in zones.iter().enumerate() {
                assert!(!z.data.is_empty(), "{label} zone {i} decoded empty");
                assert!(
                    (170.0..=1450.0).contains(&z.root),
                    "{label} zone {i} root {} Hz is outside the G3-E6 bank",
                    z.root
                );
            }
            for (i, w) in zones.windows(2).enumerate() {
                let got = cents(w[0].root, w[1].root) / 100.0;
                assert!(
                    (got - STEPS[i]).abs() < 0.6,
                    "{label} zones {i}->{} span {got:.2} semitones, expected {} \
                     (roots {:.2} -> {:.2} Hz) — an octave or transcription error",
                    i + 1,
                    STEPS[i],
                    w[0].root,
                    w[1].root
                );
            }
        }

        // Cross-TAKE agreement: the four round robins are four plucks of the same
        // ten physical notes, so their roots must agree closely. A bad root in one
        // take cannot hide, because the other three disagree with it.
        for z in 0..10 {
            let roots: Vec<f32> = sets.iter().map(|s| s[z].root).collect();
            let lo = roots.iter().cloned().fold(f32::INFINITY, f32::min);
            let hi = roots.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
            let spread = cents(lo, hi);
            assert!(
                spread < 30.0,
                "zone {z}: the four takes' roots span {spread:.1} cents ({lo:.2}..{hi:.2} Hz) \
                 — they are the same note played four times, so this is a bad root"
            );
        }
    }

    /// A tremolo stroke on the mandolin must ROTATE to the next recorded take and
    /// REPLAY its attack; a single-take bank must keep suppressing it.
    ///
    /// This is checked on the voice's own state rather than on rendered audio,
    /// deliberately. At 14 strokes/s the previous strokes' ring dominates any
    /// short analysis window — an attack-similarity measurement decays
    /// monotonically with stroke lag (measured 0.33/-0.05/-0.19/-0.22) and simply
    /// cannot see the take periodicity underneath. State is unambiguous where
    /// audio is not.
    ///
    /// The second half is the load-bearing one: `retrigger` is shared by EVERY
    /// sampled voice, and GM 25 steel tremolo is used by two committed albums, so
    /// a single-take bank must come out of a restrike with its read head and
    /// crossfade clock untouched — sample retiring, model re-picking, exactly as
    /// before.
    #[test]
    fn mandolin_tremolo_rotates_takes_while_single_take_banks_still_suppress() {
        let sr = 44100.0;
        let key = 76u8; // E5 — an in-tune open-string zone
        let model = || voices::make(25, key, 100, sr, 7, false);

        let mut la = match LaVoice::build_rr(
            model(),
            mandolin_bank,
            MANDOLIN_ROUND_ROBINS,
            0,
            key,
            100,
            sr,
            0.20,
            (0.05, 0.28),
        ) {
            Ok(la) => la,
            Err(_) => panic!("the mandolin bank must wrap at E5"),
        };
        assert!(
            la.rr.is_some(),
            "a 4-take bank must arm round-robin rotation"
        );

        // Walk two full cycles, recording which take each stroke plays.
        let mut seen: Vec<*const Zone> = vec![la.zone as *const Zone];
        for _ in 0..(2 * MANDOLIN_ROUND_ROBINS - 1) {
            assert!(
                la.retrigger(key, 100),
                "a plucked voice must accept a restrike"
            );
            // The onset is re-armed, i.e. the sample WILL sound again: crossfade
            // clock and read head back to zero, release decay undone.
            assert_eq!(la.t, 0, "restrike must restart the crossfade clock");
            assert_eq!(la.pos, 0.0, "restrike must rewind the sample read head");
            assert_eq!(la.rel_gain, 1.0, "restrike must undo the release decay");
            assert_eq!(
                la.rel_mul, 1.0,
                "restrike must not leave the sample decaying"
            );
            seen.push(la.zone as *const Zone);
        }

        // Strict cycling: the first four takes are pairwise distinct, and the
        // second cycle repeats them in the same order. Random selection would
        // fail the distinctness half; a stuck index would fail both.
        for i in 0..MANDOLIN_ROUND_ROBINS {
            for j in (i + 1)..MANDOLIN_ROUND_ROBINS {
                assert_ne!(
                    seen[i], seen[j],
                    "strokes {i} and {j} of one cycle must play DIFFERENT takes"
                );
            }
            assert_eq!(
                seen[i],
                seen[i + MANDOLIN_ROUND_ROBINS],
                "stroke {i} and stroke {} must play the SAME take — the takes were \
                 recorded in pick-direction order, so the cycle must be strict",
                i + MANDOLIN_ROUND_ROBINS
            );
        }

        // The scoping: a single-take bank keeps the original suppress-and-model
        // path. Its read head and clock must NOT be re-armed.
        let mut steel = match LaVoice::build(
            model(),
            steel_bank(),
            key,
            100,
            sr,
            0.20,
            (0.05, 0.28),
            LaFx::default(),
            DEFAULT_LA_RELEASE_T60,
        ) {
            Ok(la) => la,
            Err(_) => panic!("the steel bank must wrap at E5"),
        };
        assert!(
            steel.rr.is_none(),
            "a single-take bank must NOT arm rotation"
        );
        let mut buf = vec![0f32; 512];
        steel.render(&mut buf);
        let (t_before, pos_before) = (steel.t, steel.pos);
        assert!(steel.retrigger(key, 100));
        assert_eq!(
            steel.t, t_before,
            "a single-take bank must not restart its crossfade clock on a restrike"
        );
        assert_eq!(
            steel.pos, pos_before,
            "a single-take bank must not rewind its sample read head on a restrike"
        );
        assert!(
            steel.rel_mul < 1.0,
            "a single-take bank must still RETIRE its sampled attack on a restrike"
        );
    }

    /// Every LOOPED-SUSTAIN bank must be loopable: a whole number of pitch
    /// periods long, and steady in level and brightness across its own length.
    ///
    /// This is the oracle the bagpipe click needed and did not have. `LoopVoice`
    /// plays these buffers on an endless modulo wrap, so a buffer that spans a
    /// fractional period count wraps with every harmonic out of phase, and one
    /// that spans a swell in the take steps in level — both once per loop, heard
    /// as a periodic click. The shipped 0.4 s chanter buffers failed on both
    /// counts (`chanter_G5` spanned 310.39 periods; `chanter_G4` and
    /// `chanter_D5` ramped ~4 dB across the window), while the only gates were a
    /// single-sample seam step at bake time and an RMS-flatness check here —
    /// neither of which can see either defect.
    ///
    /// Deliberately written over the BANKS, not one instrument: any future looped
    /// sustain added to these crates is covered the day it lands.
    /// MM-REQ-KILN-00025/00026: per-note variation is real. An ODD seed
    /// plays the RR2 bank (a different recorded take) and two EVEN seeds
    /// share the bank yet diverge through the read-rate drift walk; the same
    /// seed stays bit-deterministic. Red-checked by neutering the mechanism.
    #[test]
    fn bagpipe_chanter_rr2_and_drift_decorrelate() {
        let sr = 44100.0;
        let render = |seed: u32| {
            let mut v = bagpipe_chanter_loop(69, sr, seed);
            let mut buf = vec![0f32; (sr * 1.5) as usize];
            v.render(&mut buf);
            buf
        };
        let a = render(0);
        let b = render(1); // RR2 bank
        let c = render(2); // same bank as `a`, different drift walk
        assert!(
            a.iter().zip(&b).any(|(x, y)| x != y),
            "RR2 bank not engaged"
        );
        let late = (sr * 1.0) as usize;
        assert!(
            a[late..].iter().zip(&c[late..]).any(|(x, y)| x != y),
            "drift walk did not decorrelate same-bank renders"
        );
        let a2 = render(0);
        assert_eq!(a, a2, "seeded render must stay deterministic");
    }

    /// MM-REQ-KILN-00025: the chanter bank covers every loopable take the
    /// FreePats archive holds — 10 RR1 zones F4-G5. The only hole is
    /// D5->F#5 (ratio 1.238): D#5/E5/F5 fail the -14 dB wrap gate in BOTH
    /// takes (probe 2026-07-21), so 1.25 is the tightest honest adjacent-gap
    /// bar. Fails against the old 6-zone table (D5->G5 = 1.333).
    #[test]
    fn bagpipe_chanter_zone_coverage() {
        let z = chanter();
        assert_eq!(z.len(), 10, "chanter RR1 zones: got {}", z.len());
        let mut roots: Vec<f32> = z.iter().map(|z| z.root).collect();
        roots.sort_by(|a, b| a.partial_cmp(b).unwrap());
        for w in roots.windows(2) {
            assert!(
                w[1] / w[0] <= 1.25,
                "adjacent zone gap {} -> {} exceeds 1.25",
                w[0],
                w[1]
            );
        }
    }

    #[test]
    fn looped_sustain_banks_are_loopable() {
        // (label, zones) — every bank played by `LoopVoice` on a modulo wrap.
        let banks: [(&str, &'static [Zone]); 4] = [
            ("chanter", chanter_bank()),
            ("chanter_rr2", chanter_rr2()),
            ("drone_g2", drone_g2_bank()),
            ("drone_g3", drone_g3_bank()),
        ];
        if !crate::embedded_samples_available() {
            return; // modeled-only build: nothing to check
        }
        for (label, zones) in banks {
            for z in zones {
                let x = z.data.as_slice();
                let n = x.len();
                assert!(n > 512, "{label}: zone too short to loop ({n})");

                // 1. WHOLE number of pitch periods. `z.root` is the measured f0,
                //    so the period is known exactly — no estimation needed.
                let period = 44100.0 / z.root;
                let cycles = n as f64 / period as f64;
                let off = (cycles - cycles.round()).abs();
                assert!(
                    off < 0.05,
                    "{label} @{:.1} Hz: loop spans {cycles:.3} periods — a \
                     fractional count wraps the harmonics out of phase",
                    z.root
                );

                // 2. STEADY level across the loop. A window that straddles a
                //    swell steps by that swell at every wrap.
                let blk = (0.020 * 44100.0) as usize;
                let nb = n / blk;
                assert!(nb >= 3, "{label}: too short for a steadiness check");
                let mut lo = f64::MAX;
                let mut hi: f64 = 0.0;
                let mut b_lo = f64::MAX;
                let mut b_hi: f64 = 0.0;
                for b in 0..nb {
                    let s = &x[b * blk..(b + 1) * blk];
                    let e: f64 = s.iter().map(|v| (*v as f64) * (*v as f64)).sum();
                    let hf: f64 = s
                        .windows(2)
                        .map(|w| {
                            let d = (w[1] - w[0]) as f64;
                            d * d
                        })
                        .sum();
                    assert!(e > 0.0, "{label}: silent block in a sustain loop");
                    lo = lo.min(e);
                    hi = hi.max(e);
                    // brightness proxy: HF energy as a fraction of total energy
                    let br = hf / e;
                    b_lo = b_lo.min(br);
                    b_hi = b_hi.max(br);
                }
                let spread_db = 10.0 * (hi / lo).log10();
                assert!(
                    spread_db < 3.0,
                    "{label} @{:.1} Hz: level varies {spread_db:.2} dB across the \
                     loop — the wrap steps by that much every cycle",
                    z.root
                );
                let bright_db = 10.0 * (b_hi / b_lo).log10();
                assert!(
                    bright_db < 4.0,
                    "{label} @{:.1} Hz: brightness varies {bright_db:.2} dB across \
                     the loop — the wrap steps in timbre every cycle",
                    z.root
                );
            }
        }
    }

    /// The committed GM-96 rain loop (`rain_loop()`) must be SEAMLESS: read
    /// cyclically, the wrap from the last sample back to the first must not
    /// click. Rain is broadband, so "no click" is self-relative — the wrap step
    /// must sit inside the signal's OWN adjacent-step distribution (here: at or
    /// below p99). A future re-bake that broke the tail->head crossfade would
    /// push the wrap discontinuity into outlier territory and this fails. Guards
    /// the committed asset, not the renderer (the offline analogue of
    /// prepare.py's seam gate).
    #[test]
    fn rain_loop_wraps_seamlessly() {
        let s = rain_loop();
        assert!(
            s.len() as f32 > 44100.0,
            "rain loop implausibly short: {} samples",
            s.len()
        );
        let mut steps: Vec<f32> = s.windows(2).map(|w| (w[1] - w[0]).abs()).collect();
        steps.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let p99 = steps[steps.len() * 99 / 100];
        let wrap = (s[s.len() - 1] - s[0]).abs();
        assert!(
            wrap <= p99,
            "rain loop wrap discontinuity {wrap:.4} exceeds the p99 adjacent step \
             {p99:.4} — the loop seam clicks (the tail->head crossfade broke)"
        );
    }

    /// The thirteen GM-routed drum banks (35/36, 37, 38/40, 41/43, 42, 44,
    /// 45/47/48/50, 46, 49/57, 51/59, 53, 52, 55). `CRASH_SIZZLE` and
    /// `SNARE_OFF` ship in the bank but have no GM key yet.
    fn routed_banks() -> [&'static kitbank::Bank; 13] {
        [
            &kitbank2::CRASH,
            &kitbank::RIDE,
            &kitbank::RIDE_BELL,
            &kitbank2::CHINA,
            &kitbank2::SPLASH,
            &kitbank::KICK,
            &kitbank::SNARE,
            &kitbank::SIDESTICK,
            &kitbank::TOM_HI,
            &kitbank::TOM_LO,
            &kitbank::HH_CLOSED,
            &kitbank::HH_OPEN,
            &kitbank::HH_PEDAL,
        ]
    }

    /// MM-BUG-KILN-00008: the sampled electric snare (key 40) must not be the
    /// acoustic snare (key 38) verbatim. Before the fix both keys mapped to
    /// `kit::SNARE` at repitch 1.0 with equal level, so at equal vel+seed+take
    /// they rendered BIT-IDENTICALLY. The fix repitches key 40 up (matching the
    /// modeled path's brighter/tighter electric snare) — a distinct, brighter drum.
    #[test]
    fn sampled_electric_snare_distinct_from_acoustic() {
        let sr = 44100.0;
        let render = |key: u8| {
            let mut v = sampled_drum(key, 100, 7, 0, sr).expect("snare key has a sampled voice");
            let mut buf = vec![0f32; (sr * 0.4) as usize];
            v.render(&mut buf);
            buf
        };
        let ac = render(38);
        let el = render(40);
        // (b) un-foolable: equal vel+seed+take must not render bit-identically.
        assert!(
            ac != el,
            "electric snare (40) renders identically to the acoustic snare (38) — same drum"
        );
        // (a) the electric snare is brighter — the whole spectrum lifts ~1.15x, so
        // its centroid rises well clear of the ±2.5% per-hit rate jitter.
        let win = |s: &[f32]| s[..(0.12 * sr) as usize].to_vec();
        let c_ac = crate::testutil::spectral_centroid(&win(&ac), sr, 200.0, 12_000.0);
        let c_el = crate::testutil::spectral_centroid(&win(&el), sr, 200.0, 12_000.0);
        println!("snare centroid: acoustic(38)={c_ac:.0} Hz electric(40)={c_el:.0} Hz");
        assert!(
            c_el > c_ac * 1.08,
            "electric snare (40) not brighter than acoustic (38): {c_el:.0} Hz vs {c_ac:.0} Hz"
        );
    }

    /// Anti-machine-gun mechanism (a): the engine's per-key hit counter must
    /// walk the round-robin takes 0→1→2→3→0…, so four consecutive hits of one
    /// key use four DISTINCT takes and no pair of consecutive hits ever repeats
    /// one. (A seed-modulo pick would repeat ~25% of the time.)
    #[test]
    fn sampled_drum_round_robin_cycles() {
        let sr = 44100.0;
        let bank = &kitbank::RIDE;
        let takes: Vec<(usize, usize)> = (0..5u8)
            .map(|i| {
                // a fresh pseudo-random seed per hit, exactly like the engine
                let seed = 0x9E37 ^ (i as u32).wrapping_mul(2654435761);
                let v = SampledDrum::new(
                    bank,
                    0.4,
                    DrumHit {
                        vel: 100,
                        seed,
                        hit_index: i,
                    },
                    sr,
                    1.0,
                    &DRUM_JITTER,
                );
                (v.layer, v.rr)
            })
            .collect();
        assert!(
            takes.iter().all(|&(l, _)| l == takes[0].0),
            "same key + velocity must stay in one layer"
        );
        let rrs: Vec<usize> = takes.iter().map(|&(_, r)| r).collect();
        assert_eq!(rrs, vec![0, 1, 2, 3, 0], "clean rr cycle with wrap");
        for w in rrs.windows(2) {
            assert_ne!(w[0], w[1], "immediate round-robin repeat");
        }
    }

    /// The kick's modeled sub-layer supplies deep low content the sampled jazz
    /// kick (fundamental ~80 Hz, nothing below) does not have. Measured as the
    /// energy of a ~50 Hz Goertzel bin: present with the sub, ~absent without.
    /// Fail-first: drop `with_kick_sub` and the ratio collapses to ~1.
    #[test]
    fn sampled_kick_has_deep_sub() {
        let sr = 44100.0;
        let hit = DrumHit {
            vel: 110,
            seed: 7,
            hit_index: 0,
        };
        let render = |sub: bool| -> Vec<f32> {
            let mut v = SampledDrum::new(&kitbank::KICK, 1.0, hit, sr, 1.0, &DRUM_JITTER);
            if sub {
                v = v.with_kick_sub(hit.vel, sr);
            }
            let mut buf = vec![0f32; (0.3 * sr) as usize];
            v.render(&mut buf);
            buf
        };
        // Goertzel magnitude at ~50 Hz (the sub's settled pitch).
        let mag50 = |x: &[f32]| -> f32 {
            let w = std::f32::consts::TAU * 50.0 / sr;
            let coeff = 2.0 * w.cos();
            let (mut s1, mut s2) = (0.0f32, 0.0f32);
            for &v in x {
                let s0 = v + coeff * s1 - s2;
                s2 = s1;
                s1 = s0;
            }
            ((s1 * s1 + s2 * s2 - coeff * s1 * s2).max(0.0)).sqrt() / x.len() as f32
        };
        let with = mag50(&render(true));
        let without = mag50(&render(false));
        eprintln!(
            "kick 50 Hz: with-sub={with:.6} without={without:.6} ratio={:.2}",
            with / without.max(1e-9)
        );
        assert!(
            with > 1.8 * without.max(1e-9),
            "kick sub-layer adds no deep 50 Hz content: with={with:.5} without={without:.5}"
        );
    }

    /// Velocity picks the bank's dynamic layer at the SFZ boundaries, and
    /// still scales gain continuously inside a layer.
    #[test]
    fn sampled_drum_velocity_selects_layer() {
        let sr = 44100.0;
        let bank = &kitbank::RIDE; // vel_hi [42, 85, 127]
        let layer = |vel: u8| {
            SampledDrum::new(
                bank,
                0.4,
                DrumHit {
                    vel,
                    seed: 7,
                    hit_index: 0,
                },
                sr,
                1.0,
                &DRUM_JITTER,
            )
            .layer
        };
        assert_eq!(layer(30), 0);
        assert_eq!(layer(42), 0);
        assert_eq!(layer(43), 1);
        assert_eq!(layer(85), 1);
        assert_eq!(layer(86), 2);
        assert_eq!(layer(120), 2);
        let soft = SampledDrum::new(
            bank,
            0.4,
            DrumHit {
                vel: 30,
                seed: 7,
                hit_index: 0,
            },
            sr,
            1.0,
            &DRUM_JITTER,
        );
        let hard = SampledDrum::new(
            bank,
            0.4,
            DrumHit {
                vel: 120,
                seed: 7,
                hit_index: 0,
            },
            sr,
            1.0,
            &DRUM_JITTER,
        );
        assert!(
            !std::ptr::eq(soft.data, hard.data),
            "soft and hard hits must play different takes"
        );
        assert!(hard.gain > soft.gain * 2.0, "velocity gain not continuous");
    }

    /// A choked cymbal (hat grab / CC120) reaches silence within ~20 ms and
    /// the voice then terminates.
    #[test]
    fn sampled_drum_choke_reaches_silence_within_20_ms() {
        let sr = 44100.0;
        let mut v = SampledDrum::new(
            &kitbank2::CRASH,
            0.4,
            DrumHit {
                vel: 110,
                seed: 7,
                hit_index: 0,
            },
            sr,
            1.0,
            &DRUM_JITTER,
        );
        let mut head = vec![0f32; (0.30 * sr) as usize];
        assert!(v.render(&mut head));
        let pre = head[head.len() - 441..]
            .iter()
            .fold(0f32, |m, &x| m.max(x.abs()));
        assert!(pre > 1e-4, "crash should still ring at 0.3 s: {pre}");
        v.choke();
        let mut tail = vec![0f32; (0.05 * sr) as usize];
        v.render(&mut tail);
        let post = tail[(0.020 * sr) as usize..]
            .iter()
            .fold(0f32, |m, &x| m.max(x.abs()));
        assert!(
            post < pre * 2e-3,
            "choked cymbal still audible after 20 ms: {post} vs pre {pre}"
        );
        let mut more = vec![0f32; 64];
        assert!(!v.render(&mut more), "choked voice must terminate");
    }

    /// No boundary click: every routed take starts and ends on the
    /// generator's fades (2 ms fade-in, squared fade-out), and the voice's
    /// rendered stream begins near zero and dies out near zero rather than
    /// stepping. Guards a future re-prepared bank as much as the voice.
    #[test]
    fn sampled_drum_has_no_boundary_click() {
        let sr = 44100.0;
        for bank in routed_banks() {
            for layer in 0..bank.layers() {
                for rr in 0..bank.round_robins {
                    let pcm = bank.pcm(layer, rr);
                    let peak = pcm.iter().map(|&v| (v as i32).abs()).max().unwrap() as f32;
                    let head = pcm[..44].iter().map(|&v| (v as i32).abs()).max().unwrap() as f32;
                    let tail = pcm[pcm.len() - 44..]
                        .iter()
                        .map(|&v| (v as i32).abs())
                        .max()
                        .unwrap() as f32;
                    let name = bank.file_name(layer, rr);
                    assert!(
                        head < 0.05 * peak,
                        "{name}: hot first ms ({head} vs {peak})"
                    );
                    assert!(tail < 0.02 * peak, "{name}: hot last ms ({tail} vs {peak})");
                }
            }
            // and through the voice: near-zero entry, near-zero exit
            let mut v = SampledDrum::new(
                bank,
                0.4,
                DrumHit {
                    vel: 110,
                    seed: 7,
                    hit_index: 0,
                },
                sr,
                1.0,
                &DRUM_JITTER,
            );
            let mut buf = vec![0f32; (3.0 * sr) as usize];
            let alive = v.render(&mut buf);
            assert!(!alive, "3 s must outlast every bank take");
            let peak = buf.iter().fold(0f32, |m, &x| m.max(x.abs()));
            assert!(peak > 0.01, "{}: silent render", bank.name);
            assert!(
                buf[0].abs() < 0.05 * peak,
                "{}: rendered onset steps ({} vs peak {peak})",
                bank.name,
                buf[0]
            );
            let last = buf.iter().rposition(|&x| x != 0.0).unwrap();
            let end_peak = buf[last.saturating_sub(88)..=last]
                .iter()
                .fold(0f32, |m, &x| m.max(x.abs()));
            assert!(
                end_peak < 0.05 * peak,
                "{}: rendered tail steps ({end_peak} vs peak {peak})",
                bank.name
            );
        }
    }

    #[test]
    fn banks_parse() {
        for z in violin_f()
            .iter()
            .chain(violin_p())
            .chain(flute())
            .chain(grand_pp())
            .chain(grand_mf())
            .chain(grand_f())
            .chain(grand_pp_rr2())
            .chain(grand_mf_rr2())
            .chain(grand_f_rr2())
            .chain(trumpet_p())
            .chain(trumpet_f())
            .chain(mutetpt_p())
            .chain(mutetpt_f())
            .chain(trombone_p())
            .chain(trombone_f())
            .chain(tuba_p())
            .chain(tuba_f())
            .chain(horn_p())
            .chain(horn_f())
            .chain(oboe_p())
            .chain(oboe_f())
            .chain(bassoon_p())
            .chain(bassoon_f())
            .chain(clarinet_p())
            .chain(clarinet_f())
            .chain(nylon())
            .chain(strsec_p())
            .chain(strsec_f())
        {
            assert!(z.data.len() > 20_000, "zone too short: {}", z.data.len());
            // the tuba bank reaches A#0 (~29 Hz), hence the low floor
            assert!((25.0..2500.0).contains(&z.root), "odd root {}", z.root);
            let peak = z.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(peak > 0.5, "zone not normalised: peak {peak}");
        }
        // The conditioned GM0 upright preserves one smooth absolute body-level
        // trend across keys, so its quieter high-register zones no longer all
        // peak above the legacy per-file-normalisation floor.
        for z in piano_pp()
            .iter()
            .chain(piano_mf())
            .chain(piano_f())
            .chain(piano_pp_rr2())
            .chain(piano_mf_rr2())
            .chain(piano_f_rr2())
        {
            assert!(z.data.len() > 20_000, "zone too short: {}", z.data.len());
            assert!((25.0..2500.0).contains(&z.root), "odd root {}", z.root);
            let peak = z.data.iter().fold(0f32, |m, &v| m.max(v.abs()));
            assert!(
                (0.12..=0.91).contains(&peak),
                "conditioned piano zone outside its shared-headroom range: peak {peak}"
            );
        }
        // (the drum-kit bank's own asset crate tests guard the sampled kit)
    }

    #[test]
    fn upright_round_robin_bank_only_aliases_declared_single_takes() {
        if !crate::embedded_samples_available() {
            return;
        }
        let pp1 = piano_pp();
        let pp2 = piano_pp_rr2();
        for zone in 0..2 {
            assert_eq!(
                pp1[zone].data, pp2[zone].data,
                "quiet C2/G2 are the declared single-take cells"
            );
        }
        for zone in 2..pp1.len() {
            assert_ne!(
                pp1[zone].data, pp2[zone].data,
                "every other quiet cell must have a real second take"
            );
        }
        for (first, second) in [(piano_mf(), piano_mf_rr2()), (piano_f(), piano_f_rr2())] {
            for zone in 0..first.len() {
                assert_ne!(
                    first[zone].data, second[zone].data,
                    "mf/f cells must have real second takes"
                );
            }
        }
    }

    fn pitch_of(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(600.0, sr);
        let mut lp2 = OnePole::lowpass(600.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut c = 0;
        for w in f.windows(2) {
            if w[0] <= 0.0 && w[1] > 0.0 {
                c += 1;
            }
        }
        c as f32 / (seg.len() as f32 / sr)
    }

    /// The LA fiddle at A4 must sound at 440 Hz straight through the
    /// crossfade — the repitched sample and the model have to agree.
    #[test]
    fn la_pitch_a4() {
        let sr = 44100.0;
        let mut v = voices::make(40, 69, 100, sr, 5, true);
        let mut buf = vec![0f32; 44100];
        v.render(&mut buf);
        let hz = pitch_of(&buf[6615..24255], sr); // 0.15 s – 0.55 s
        assert!((hz - 440.0).abs() < 12.0, "measured {hz} Hz");
    }

    /// The brass sample layer must not shift perceived pitch: Goertzel peak
    /// through the crossfade window (zero-crossing counters lie when a layer
    /// brightens a voice — lessons_learnt 2026.07.07).
    #[test]
    fn la_brass_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (56u8, 69u8, "trumpet"),
            (57, 55, "trombone"),
            (58, 40, "tuba"),
            (59, 69, "muted-trumpet"),
            (60, 62, "french-horn"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The layer must be audible, not just present (lessons_learnt
    /// 2026.07.06): samples-on vs samples-off of the same note must differ
    /// materially in the first 50 ms, and for the bright programs the real
    /// attack must raise the high-band fraction (the sampled bite) over the
    /// model's synthetic chiff. The french horn is exempt from the HF check:
    /// its hand-in-bell attack is genuinely dark (measured on ≈ off).
    #[test]
    fn la_brass_attack_sharpness() {
        let sr = 44100.0;
        for (program, key, hf_gain, name) in [
            (56u8, 69u8, 1.5f32, "trumpet"),
            (57, 55, 1.3, "trombone"),
            (58, 40, 2.0, "tuba"),
            (59, 69, 1.3, "muted-trumpet"),
            (60, 62, 0.0, "french-horn"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on > r_off * hf_gain,
                "{name}: attack not sharper: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The reed sample layer must not shift perceived pitch: Goertzel peak
    /// through the crossfade window (as `la_brass_pitch_integrity`); 69
    /// exercises the english horn's repitched oboe bank.
    #[test]
    fn la_reed_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (68u8, 76u8, "oboe"),
            (69, 64, "english-horn"),
            (70, 48, "bassoon"),
            (71, 60, "clarinet"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The reed layer must be audible, not just present: samples-on vs
    /// samples-off must differ materially in the first 50 ms. Unlike brass
    /// (real lip bite ADDS high band), every measured reed onset is LESS
    /// hissy than the model’s synthetic chiff (hf-frac on/off: oboe
    /// 0.53/0.67, english horn 0.38/0.39, bassoon 0.15/0.20, clarinet
    /// 0.19/0.28) — the realism gain is removing synthetic noise, so the
    /// oracle asserts that measured direction: the layer must never make
    /// the attack hissier than the pure model.
    #[test]
    fn la_reed_attack_sharpness() {
        let sr = 44100.0;
        for (program, key, name) in [
            (68u8, 76u8, "oboe"),
            (69, 64, "english-horn"),
            (70, 48, "bassoon"),
            (71, 60, "clarinet"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.05,
                "{name}: sampled attack hissier than the model: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The saxophone LA sample layer (MTG.SoloSax, GM 64-67) must not shift
    /// perceived pitch: Goertzel peak through the crossfade window (as
    /// `la_reed_pitch_integrity`). Each key sits inside its sax's sampled range so
    /// the layer engages rather than falling back to the bare model, and validates
    /// that the MEASURED zone roots (`sax_*` banks) repitch to the requested note.
    #[test]
    fn la_sax_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (64u8, 72u8, "soprano-sax"),
            (65, 65, "alto-sax"),
            (66, 60, "tenor-sax"),
            (67, 48, "baritone-sax"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15–0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The saxophone layer must be AUDIBLE, not a silent fallback: samples-on vs
    /// samples-off must differ materially in the first 50 ms for every sax. Guards
    /// the whole path — sax-crate resolution in `embedded_wav`, the `sax_bank`
    /// dispatch, and `LaVoice` engagement (a repitch outside 0.5..=2.05 would fall
    /// back to the bare model and this would catch it).
    #[test]
    fn la_sax_audible() {
        let sr = 44100.0;
        for (program, key, name) in [
            (64u8, 72u8, "soprano-sax"),
            (65, 65, "alto-sax"),
            (66, 60, "tenor-sax"),
            (67, 48, "baritone-sax"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: layer barely changes the onset (diff {d:.5} vs off {o:.5})"
            );
        }
    }

    /// Does the LA layer engage for this `(program, key)` at this rate?
    ///
    /// EXACT, not thresholded. When `LaVoice::build` rejects a note it returns
    /// `Err(sustain)` and the caller unwraps the very same model it would have built
    /// with `samples: false` — same program, same key, same seed — so the two renders
    /// are bit-identical. Any difference at all therefore means the sample engaged.
    #[cfg(test)]
    fn la_engaged(program: u8, key: u8, sr: f32) -> bool {
        let render = |samples: bool| {
            let mut v = voices::make(program, key, 100, sr, 5, samples);
            let mut buf = vec![0f32; (0.03 * sr) as usize];
            v.render(&mut buf);
            buf
        };
        render(true) != render(false)
    }

    /// [`la_engaged`] for a CC0 alt bank. Same exact (not thresholded) test, routed
    /// through `altbank::make` instead of `voices::make`.
    ///
    /// Needed because GM 32–35's sampled bass onset LIVES on the alt bank as of
    /// MM-BUG-KILN-00075 — asking `voices::make` whether it engages would now answer
    /// "no" for a reason that has nothing to do with the rate-eligibility guard this
    /// is here to police.
    #[cfg(test)]
    fn la_engaged_bank(program: u8, bank: u8, key: u8, sr: f32) -> bool {
        let render = |samples: bool| {
            let mut v = crate::altbank::make(program, bank, key, 100, sr, 5, samples);
            let mut buf = vec![0f32; (0.03 * sr) as usize];
            v.render(&mut buf);
            buf
        };
        render(true) != render(false)
    }

    /// MM-BUG-KILN-00061: whether a note gets its sampled onset must be a property of
    /// the MUSICAL PITCH, never of the output sample rate.
    ///
    /// `LaVoice::build` used to check the sample-rate-converted playback step against
    /// the `0.5..=2.05` repitch window. At 96 kHz that scales every step by 44100/96000
    /// = 0.459, so notes sitting near their zone root fell straight through the lower
    /// bound and silently lost the sample — while an octave-up repitch, far less
    /// credible, landed mid-window and engaged. Merely choosing a legal output rate
    /// changed the instrument.
    ///
    /// Swept over EVERY program and a spread of keys rather than the three bass
    /// programs the report named, because the guard is shared by every LA-wrapped
    /// voice — a hand-written program list would have covered only the reported
    /// symptom (the recurring defect this repo keeps re-learning). 44.1 kHz is the
    /// reference: it is the rate the zone roots were measured at, where step == ratio
    /// and the two orderings agree, so it is the only rate the old code got right.
    #[test]
    fn la_engagement_never_depends_on_output_rate() {
        let keys = [24u8, 28, 33, 40, 52, 64, 76, 88];
        let mut broken: Vec<String> = Vec::new();
        for program in 0u8..=127 {
            for &key in &keys {
                let reference = la_engaged(program, key, 44_100.0);
                for &sr in &[48_000.0f32, 96_000.0] {
                    if la_engaged(program, key, sr) != reference {
                        broken.push(format!(
                            "GM {program} key {key}: engages={reference} at 44100 Hz but \
                             {} at {sr:.0} Hz",
                            !reference
                        ));
                    }
                }
            }
        }
        assert!(
            broken.is_empty(),
            "{} (program, key, rate) combination(s) change LA sample eligibility with the \
             output rate. Eligibility must be decided on the pitch ratio \
             `target_hz / zone.root`, and only then converted to the output clock by \
             `* 44100 / sr`:\n  {}",
            broken.len(),
            broken.join("\n  ")
        );
    }

    /// The report's own repro, kept as a named regression: the bass onsets that
    /// vanished at 96 kHz (MM-BUG-KILN-00061).
    ///
    /// GM 33/35 E1 sit essentially ON the 41.22 Hz finger-bass zone root and GM 34 E2 on
    /// the 82.13 Hz pick-bass root — ratio ~1.0, the most credible repitch there is —
    /// yet all three read step ~0.46 at 96 kHz and fell back to the bare model. A1 is
    /// included as an in-window control that survived even the broken guard.
    ///
    /// Engagement only — pitch is deliberately NOT scored here. The playback step is
    /// still `ratio * 44100 / sr`, algebraically untouched by this fix; only the guard
    /// moved. And a Goertzel peak cannot resolve these notes well enough to score across
    /// rates: at 41 Hz over a 0.5 s window the bin spacing alone shifted GM 35 E1 by
    /// 35 cents between 44.1 and 48 kHz on an unmodified tree. Pinning a threshold there
    /// would measure the estimator, not the synth. Repitch pitch integrity at 44.1 kHz is
    /// already covered by `la_reed_pitch_integrity` and `la_sax_pitch_integrity`.
    /// BANK NOTE (MM-BUG-KILN-00075, 2026-07-24): these onsets moved to the CC0=1 ALT
    /// bank when the modeled bass was restored as the default, so this probes
    /// `la_engaged_bank(.., 1, ..)`. The KILN-00061 property under test is unchanged and
    /// undiluted — eligibility must follow the pitch ratio, never the output clock — it
    /// is simply asserted where the bass sample layer now lives. Asserting it on the
    /// default bank would now be vacuous: `voices::make` is samples-blind for 32..=35,
    /// so `la_engaged` is uniformly false there at every rate and would pass while
    /// testing nothing. (The all-program sweep above keeps its default-bank reading for
    /// the same reason — for 32..=35 it is consistent-because-absent, which is why this
    /// alt-bank rung is the one that carries the bass coverage.)
    #[test]
    fn la_bass_onset_engages_at_every_supported_rate() {
        for (program, key, name) in [
            (33u8, 28u8, "GM33 fingered bass E1"),
            (33, 33, "GM33 fingered bass A1"),
            (34, 40, "GM34 picked bass E2"),
            (35, 28, "GM35 fretless bass E1"),
        ] {
            for &sr in &[44_100.0f32, 48_000.0, 96_000.0] {
                assert!(
                    la_engaged_bank(program, 1, key, sr),
                    "{name}: the sampled onset does not engage on the CC0=1 alt bank at \
                     {sr:.0} Hz — this note's repitch ratio is ~1.0, the most credible \
                     there is"
                );
            }
        }
    }

    /// The looped-sustain sax (2026.07.18 holds audit) must (a) actually engage — a
    /// `SaxLoopVoice`, not the modeled fallback — for every sax at a representative key;
    /// (b) sit within ~3 dB of the modeled reed it replaces over the hold, so album mix
    /// balance is preserved; and (c) hold a FLAT sustain — no gross amplitude sawtooth
    /// from a loop that spans the recorded decay (the `find_sax_loop` imbalance term
    /// guards this; the bug read frame-RMS CoV ~0.6). Liveness is deliberately low here —
    /// movement is re-added by the modulator increment, not baked into the raw loop.
    #[test]
    fn sax_loop_level_parity_and_flat() {
        let sr = 44100.0;
        for (program, key, name) in [
            (64u8, 72u8, "soprano"),
            (65, 65, "alto"),
            (66, 60, "tenor"),
            (67, 48, "baritone"),
        ] {
            assert_eq!(
                voices::make(program, key, 100, sr, 5, true).kind(),
                "saxloop",
                "{name}: samples-on must engage the looped voice, not the modeled fallback"
            );
            let hold = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (1.5 * sr) as usize];
                v.render(&mut buf);
                buf[(0.6 * sr) as usize..(1.4 * sr) as usize].to_vec()
            };
            let (loop_h, model_h) = (hold(true), hold(false));
            let (rl, rm) = (
                crate::testutil::rms(&loop_h),
                crate::testutil::rms(&model_h),
            );
            let db = 20.0 * (rl / rm).log10();
            // Raw offset band, not symmetric parity: the mix-consistency nudge lifts the
            // loop ~+2.3 dB over the dry model (the bus compressor pulls the animated loop
            // down harder), so raw is deliberately hot. Band guards gross errors — too
            // quiet below −1 dB, too hot above +4.5 dB. See SAX_LOOP_GAIN.
            assert!(
                (-1.0..=4.5).contains(&db),
                "{name}: looped hold {db:+.1} dB vs the modeled reed — out of the raw offset \
                 band (loop {rl:.4} vs model {rm:.4})"
            );
            // Liveness window: 20 ms frame-RMS CoV over the hold must sit in a BAND — the
            // hold must BREATHE (inc-2 intrinsic vibrato/tremolo, > the static inc-1 floor)
            // but not PULSE (the decay-sawtooth bug read ~0.6; a healthy hold is well under).
            let fl = (0.02 * sr) as usize;
            let frames: Vec<f32> = loop_h
                .chunks(fl)
                .filter(|c| c.len() == fl)
                .map(crate::testutil::rms)
                .collect();
            let mean = frames.iter().sum::<f32>() / frames.len() as f32;
            let var = frames.iter().map(|&x| (x - mean).powi(2)).sum::<f32>() / frames.len() as f32;
            let cov = var.sqrt() / (mean + 1e-9);
            assert!(
                (0.025..0.12).contains(&cov),
                "{name}: hold liveness (frame-RMS CoV {cov:.3}) out of band — \
                 static (dead loop) below 0.025, or a decay-sawtooth pulse above 0.12"
            );
            // Seam guard (deterministic): the chosen loop joins loop_end back to loop_start
            // with a small value discontinuity — an integer-period, seam-minimised wrap must
            // not click. Re-derive the exact loop the voice uses.
            let zones = sax_bank(program, 100);
            let zone = nearest(zones, crate::dsp::key_freq(key));
            // Through the memo, exactly as the voice does — a direct `find_sax_loop` call
            // would bypass it and move `LOOP_SEARCHES` under a parallel prewarm oracle.
            let (ls, le) = zone
                .sustain_loop(find_sax_loop)
                .expect("a loop was found above");
            let wrap = (zone.data[le] - zone.data[ls]).abs();
            assert!(
                wrap < 0.03,
                "{name}: loop wrap discontinuity {wrap:.4} (loop {ls}..{le}) — would click"
            );
        }
    }

    /// The looped blown bottle (GM 76) must (a) actually engage — a `BottleLoopVoice`,
    /// not the modeled Wind fallback — at representative in-window keys; (b) sit within
    /// rough parity of the modeled bottle it replaces over the hold (measured +0.2 dB at
    /// key 55, +1.6 dB at key 60 with `BOTTLE_LOOP_GAIN` = 0.65); (c) hold a FLAT sustain
    /// (frame-RMS CoV live-but-not-pulsing; measured ~0.037); and (d) wrap its loop seam
    /// without a click. Built exactly like the sax (`sax_loop_level_parity_and_flat`);
    /// every band is calibrated to the bottle's OWN measured values, not the sax's.
    #[test]
    fn bottle_loop_level_parity_and_flat() {
        let sr = 44100.0;
        for key in [55u8, 60] {
            assert_eq!(
                voices::make(76, key, 100, sr, 5, true).kind(),
                "bottleloop",
                "key {key}: samples-on must engage the looped voice, not the modeled fallback"
            );
            let hold = |samples: bool| {
                let mut v = voices::make(76, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (1.5 * sr) as usize];
                v.render(&mut buf);
                buf[(0.6 * sr) as usize..(1.4 * sr) as usize].to_vec()
            };
            let (loop_h, model_h) = (hold(true), hold(false));
            let (rl, rm) = (
                crate::testutil::rms(&loop_h),
                crate::testutil::rms(&model_h),
            );
            let db = 20.0 * (rl / rm).log10();
            // Raw offset band. Measured +0.2 dB (key 55) to +1.6 dB (key 60) at
            // BOTTLE_LOOP_GAIN = 0.65; ±2 dB margin guards gross level errors either side.
            assert!(
                (-2.0..=4.0).contains(&db),
                "key {key}: looped hold {db:+.1} dB vs the modeled bottle — out of the raw \
                 offset band (loop {rl:.4} vs model {rm:.4}). See BOTTLE_LOOP_GAIN."
            );
            // Liveness: 20 ms frame-RMS CoV must sit in a band — the hold must BREATHE
            // (intrinsic vibrato/tremolo) but not PULSE (a decay-sawtooth loop reads ~0.6).
            // Measured ~0.037 for the bottle; band 0.02..0.08 gives margin both sides.
            let fl = (0.02 * sr) as usize;
            let frames: Vec<f32> = loop_h
                .chunks(fl)
                .filter(|c| c.len() == fl)
                .map(crate::testutil::rms)
                .collect();
            let mean = frames.iter().sum::<f32>() / frames.len() as f32;
            let var = frames.iter().map(|&x| (x - mean).powi(2)).sum::<f32>() / frames.len() as f32;
            let cov = var.sqrt() / (mean + 1e-9);
            assert!(
                (0.02..0.08).contains(&cov),
                "key {key}: hold liveness (frame-RMS CoV {cov:.3}) out of band — \
                 static (dead loop) below 0.02, or a decay-sawtooth pulse above 0.08"
            );
        }
        // Seam guard (deterministic, key-independent — single-zone bank): loop_end wraps
        // back to loop_start with a small value discontinuity. Measured |d| ≈ 0.006.
        let zone = nearest(bottle_loop_bank(), crate::dsp::key_freq(60));
        // Through the memo, exactly as the voice does — a direct `find_bottle_loop` call
        // would bypass it and move `LOOP_SEARCHES` under a parallel prewarm oracle.
        let (ls, le) = zone
            .sustain_loop(find_bottle_loop)
            .expect("a loop was found above");
        let wrap = (zone.data[le] - zone.data[ls]).abs();
        assert!(
            wrap < 0.03,
            "loop wrap discontinuity {wrap:.4} (loop {ls}..{le}) — would click"
        );
    }

    /// MM-BUG-KILN-00066 — loop-voice clocks must cross the old `u32`
    /// boundary without panicking or restarting the shared vibrato/drift state.
    ///
    /// A settled reference clock with the same drift-scheduler phase must render
    /// bit-identically. The absolute time differs, but both voices are past the
    /// vibrato bloom; only the cadence phase is musically relevant thereafter.
    #[test]
    fn loop_voice_clocks_cross_u32_boundary_without_modulation_reset() {
        let sr = 44100.0;
        let near_start = u32::MAX as u64 - 511;
        let period = SAX_DRIFT_SAMP as u64;
        let settled_with_same_phase = |near: u64| {
            let settled = (2.0 * sr) as u64;
            settled + (near + period - settled % period) % period
        };

        let bottle_zone = nearest(bottle_loop_bank(), crate::dsp::key_freq(60));
        let make_bottle = || {
            BottleLoopVoice::new(
                bottle_zone,
                crate::dsp::key_freq(60),
                100,
                sr,
                BOTTLE_LOOP_GAIN,
                5,
            )
            .expect("representative bottle key must engage its loop")
        };
        let (mut bottle_near, mut bottle_reference) = (make_bottle(), make_bottle());
        bottle_near.t = near_start;
        bottle_reference.t = settled_with_same_phase(near_start);
        let (mut bottle_actual, mut bottle_expected) = (vec![0.0; 1024], vec![0.0; 1024]);
        bottle_near.render(&mut bottle_actual);
        bottle_reference.render(&mut bottle_expected);
        assert!(
            bottle_near.t > u32::MAX as u64,
            "bottle clock did not cross the old u32 boundary"
        );
        assert_eq!(
            bottle_actual, bottle_expected,
            "bottle modulation reset at the old u32 boundary"
        );

        let sax_zone = nearest(sax_bank(66, 100), crate::dsp::key_freq(60));
        let make_sax = || {
            SaxLoopVoice::new(
                sax_zone,
                crate::dsp::key_freq(60),
                100,
                sr,
                sax_program_gain(66),
                5,
            )
            .expect("representative sax key must engage its loop")
        };
        let (mut sax_near, mut sax_reference) = (make_sax(), make_sax());
        sax_near.t = near_start;
        sax_reference.t = settled_with_same_phase(near_start);
        let (mut sax_actual, mut sax_expected) = (vec![0.0; 1024], vec![0.0; 1024]);
        sax_near.render(&mut sax_actual);
        sax_reference.render(&mut sax_expected);
        assert!(
            sax_near.t > u32::MAX as u64,
            "sax clock did not cross the old u32 boundary"
        );
        assert_eq!(
            sax_actual, sax_expected,
            "sax modulation reset at the old u32 boundary"
        );
    }

    /// The blown-bottle loop (GM 76) must not shift perceived pitch across its repitch
    /// window: Goertzel peak through the hold, keys spanning 0.5-2.05× the 205 Hz (≈G3)
    /// root (48 = C3 up to 67 = G4). Each key must engage the sample (not the Wind
    /// fallback) or the pitch check is meaningless. Mirrors `la_sax_pitch_integrity`.
    #[test]
    fn bottle_loop_pitch_integrity() {
        let sr = 44100.0;
        for key in [48u8, 55, 60, 67] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(76, key, 100, sr, 5, true);
            assert_eq!(
                v.kind(),
                "bottleloop",
                "key {key}: sample must engage (else the pitch check is meaningless)"
            );
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "bottle key {key}: located pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The nylon-guitar sample layer must not shift perceived pitch: Goertzel
    /// peak through the crossfade window, several keys including both repitch
    /// edges (key 40 sits on the E2 zone; 45/57/68 land between zones; 79 is
    /// repitched up ~3 st from the top E5 zone).
    #[test]
    fn la_guitar_pitch_integrity() {
        let sr = 44100.0;
        for key in [40u8, 45, 52, 57, 64, 68, 79] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(24, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.10–0.40 s spans the fade tail and the handed-over KS string
            let hz = crate::testutil::peak_locate(&buf[4410..17640], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "nylon key {key}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// The guitar layer must be audible, not just present: samples-on vs
    /// samples-off must differ materially in the first 50 ms. Measured
    /// direction (as reeds, not brass): the real pick onset is markedly LESS
    /// hissy than the model's synthetic attack-noise burst (at the HLD's
    /// initial 0.45 wrap gain, hf-frac on/off measured 0.07/0.46, 0.04/0.63,
    /// 0.23/0.47 for keys 45/52/64; direction unchanged at the level-matched
    /// 0.25) — the realism gain is replacing broadband noise with a woody
    /// pick transient, so the oracle asserts the layer never makes the
    /// attack hissier.
    #[test]
    fn la_guitar_attack_sharpness() {
        let sr = 44100.0;
        for key in [45u8, 52, 64] {
            let early = |samples: bool| {
                let mut v = voices::make(24, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "nylon key {key}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.05,
                "nylon key {key}: sampled attack hissier than the model: hf-frac on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// Guitar-realism HLD §4 / AC1 — a PRESENCE + DETERMINISM canary only:
    /// different voice seeds must decorrelate the sample-owned onset (today
    /// it replays identical PCM — the machine-gun tell), and the same seed
    /// must stay bit-identical. Audible sufficiency is deliberately NOT
    /// asserted here (HAT lesson: worst-pair NCC 0.494 still machine-gunned;
    /// the ear judges at the audition checkpoint).
    #[test]
    fn guitar_onset_variation_presence_and_determinism() {
        let sr = 44100.0;
        for program in [24u8, 25] {
            let render = |seed: u32| {
                let mut v = voices::make(program, 52, 100, sr, seed, true);
                let mut buf = vec![0f32; 2205]; // the sample-owned 50 ms
                v.render(&mut buf);
                buf
            };
            // seeds 5 and 21 land in DIFFERENT detune strata ((5>>3)%5=0 vs
            // (21>>3)%5=2), so the strata axis is exercised, not just the
            // xored white streams (code-review L4)
            let (a, a2, b) = (render(5), render(5), render(21));
            assert!(
                a.iter().zip(&a2).all(|(x, y)| x.to_bits() == y.to_bits()),
                "prog {program}: same seed must render bit-identically"
            );
            assert!(
                a.iter().zip(&b).any(|(x, y)| x.to_bits() != y.to_bits()),
                "prog {program}: different seeds replay identical onset PCM"
            );
            let dot = |x: &[f32], y: &[f32]| x.iter().zip(y).map(|(p, q)| p * q).sum::<f32>();
            let ncc = dot(&a, &b) / (dot(&a, &a).sqrt() * dot(&b, &b).sqrt()).max(1e-12);
            assert!(
                ncc < 0.99,
                "prog {program}: seeds {ncc:.4}-correlated — variation not reaching the onset"
            );
        }
    }

    /// Guitar-realism HLD §4 / AC2 — the sampled onset darkens with a soft
    /// pick (mirroring the model's own velocity→brightness law), and the
    /// filter is a HARD bypass at vel ≥ 100 so every existing vel-100
    /// fixture is untouched by construction.
    #[test]
    fn guitar_sample_layer_tracks_velocity_brightness() {
        // law-level: exact bypass at and above vel 100, active below
        for vel in 100..=127 {
            assert_eq!(super::vel_lp_alpha(5000.0, vel, 44100.0), 0.0);
        }
        assert!(super::vel_lp_alpha(5000.0, 99, 44100.0) > 0.0);
        assert!(
            super::vel_lp_alpha(5000.0, 32, 44100.0) < super::vel_lp_alpha(5000.0, 72, 44100.0),
            "corner must open with velocity"
        );
        // render-level: soft-pick onset carries a smaller HF fraction
        let sr = 44100.0;
        for program in [24u8, 25] {
            let hf_frac = |vel: u8| {
                let mut v = voices::make(program, 52, vel, sr, 5, true);
                let mut buf = vec![0f32; 2205];
                v.render(&mut buf);
                crate::testutil::hp_rms(&buf, sr, 1500.0) / crate::testutil::rms(&buf).max(1e-9)
            };
            let (soft, hard) = (hf_frac(32), hf_frac(110));
            assert!(
                soft < hard * 0.85,
                "prog {program}: soft pick not darker (hf {soft:.4} vs {hard:.4})"
            );
        }
    }

    /// Guitar-realism HLD §4 / AC2 (review C4) — the existing continuity
    /// fixtures all render at vel 100, where the velocity filter is
    /// bypassed; these rows exercise the ACTIVE filter and the jitter at
    /// low/mid velocity with the same differential seam contract.
    #[test]
    fn guitar_low_velocity_seam_continuity() {
        let sr = 44100.0;
        // Key-76 nylon rows ADDED by guitar block two: the treble_hold_hz
        // damper hold fixed the high-key over-damp cliff that had excluded
        // them from the start. Scoping measured 2026.07.19 (via a since-removed
        // temp probe over assert_wrap_seam's exact windows):
        // nylon k76 = 1.72×/1.61× at vel 72/100 (in contract) but 3.22× at
        // vel 40 — the DOCUMENTED vel-40 limit (the corner scales with the
        // velocity law), so vel 40 stays excluded. MM-BUG-KILN-00051 widened
        // the calibrated medium-velocity coverage to 56/72/86. STEEL k76 is
        // NOT added: 3.6–4.0× at EVERY velocity — a velocity-independent
        // take-vs-model LEVEL parity gap at high keys (the peak-normalized
        // recording speaks ~4× above the now-ringing model), a separate
        // calibrated wrap-gain feature — scratchpad 2026.07.19.
        for (program, key, vels) in [
            (24u8, 52u8, &[40u8, 72][..]),
            (24, 64, &[40, 72]),
            (24, 76, &[56, 72, 86]),
            (25, 52, &[40, 72]),
            (25, 64, &[40, 72]),
        ] {
            for &vel in vels {
                let label = format!("gtr-lowvel prog {program} key {key} vel {vel}");
                let fine = assert_wrap_seam(program, key, vel, sr, 0, &label);
                assert_attack_is_peak(&fine, &label);
            }
        }
    }

    /// Guitar-realism HLD §6 (4b) — static fade budget in the SOURCE domain
    /// (step folds in 44100/sr, so a rate-relative bound would lie at
    /// 48/96 kHz): at the default 44.1 kHz, the widened fade may consume at
    /// most fade_end × 44100 × 2.05 source samples, and every guitar zone
    /// must hold that much (steel_B5 at 0.706 s is the binding case).
    #[test]
    fn guitar_zone_fade_budget() {
        let (_, fade) = crate::voices::LA_GUITAR;
        let need = fade.1 * 44100.0 * 2.05;
        for (bank, name) in [
            (guitar_bank(), "nylon"),
            (steel_bank(), "steel"),
            (eastman_picked_bank(), "eastpick"),
            (eastman_plucked_bank(), "eastpluck"),
        ] {
            for z in bank {
                assert!(
                    (z.data.len() as f32) >= need,
                    "{name} zone (root {:.1} Hz): {} samples < fade budget {:.0}",
                    z.root,
                    z.data.len(),
                    need
                );
            }
        }
    }

    /// Guitar-realism HLD §6 (4b, review C8) — at a non-44.1 kHz rate the
    /// source is consumed faster than the 44.1 k budget assumes; the end
    /// taper must hand over smoothly (same differential seam contract as
    /// the continuity oracles). Key 100 at 96 kHz drives steel_B5 dry
    /// mid-fade by construction.
    #[test]
    fn guitar_zone_dry_out_tapers_at_high_rate() {
        // Skip the FIRST pair: at key 100 the steel model's near-instant
        // high-key decay (the documented handover cliff, scratchpad
        // 2026.07.18) dominates the 50–250 ms windows regardless of the
        // taper. This oracle owns the DRY-OUT region (~0.26 s on) — the
        // taper must keep those pairs step-free.
        assert_wrap_seam(25, 100, 100, 96000.0, 1, "steel key 100 @96k dry-out");
    }

    /// Guitar-realism HLD §4 / AC8 — the variation machinery must not reach any
    /// non-guitar LA path. Portable level/spectrum/envelope signature over one
    /// wrapped program (GM 56 trumpet), using the shared cross-machine-stable
    /// tolerances rather than a raw-f32 hash (MM-BUG-KILN-00057).
    ///
    /// MM-BUG-KILN-00018 intentionally changed the settled body ring; this
    /// captures that corrected render while still guarding against later
    /// guitar-only onset, pitch, or gain leakage.
    #[test]
    fn non_guitar_la_render_signature_is_stable() {
        let mut v = voices::make(56, 69, 100, 44100.0, 5, true);
        let mut buf = vec![0f32; 22050];
        v.render(&mut buf);
        crate::testutil::assert_render_signature(
            "GM56 non-guitar LA canary",
            crate::testutil::render_signature(
                &buf,
                44100.0,
                (0.0, 0.50),
                (0.0, 0.10),
                (0.35, 0.50),
            ),
            crate::testutil::RenderSignature {
                rms_db: -16.398,
                centroid_hz: 1767.767,
                late_early_db: 13.049,
            },
        );
    }

    /// The string-section sample layer must not shift perceived pitch:
    /// Goertzel peak through the crossfade window at idiomatic keys. 48/49
    /// exercise both the cello-section (low) and violin-section (high) zones;
    /// 50/51 are pure model by design but are pinned here too so a future
    /// wrap cannot land without re-passing this oracle.
    #[test]
    fn la_strings_pitch_integrity() {
        let sr = 44100.0;
        for (program, key, name) in [
            (48u8, 48u8, "ensemble-low-cello"),
            (48, 76, "ensemble-high-violin"),
            (49, 55, "slow-strings-low"),
            (49, 67, "slow-strings-mid"),
            (50, 60, "synth-strings-1"),
            (51, 64, "synth-strings-2"),
        ] {
            let f0 = crate::dsp::key_freq(key);
            let mut v = voices::make(program, key, 100, sr, 5, true);
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            // 0.15-0.55 s spans the fade tail and the handed-over sustain
            let hz = crate::testutil::peak_locate(&buf[6615..24255], sr, f0 * 0.8, f0 * 1.25);
            let cents = 1200.0 * (hz / f0).log2();
            assert!(
                cents.abs() < 45.0,
                "{name}: layered pitch {hz:.2} Hz vs nominal {f0:.2} Hz ({cents:.0} cents)"
            );
        }
    }

    /// Synth strings 50-51 stay pure model (HLD option A): samples on/off
    /// must render byte-identical on the default bank.
    #[test]
    fn synth_strings_50_51_skip_sample_layer() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        for prog in [50u8, 51] {
            let render = |samples: bool| {
                let mut v = voices::make(prog, 60, 100, sr, 6, samples);
                let mut buf = vec![0f32; 22050];
                v.render(&mut buf);
                buf
            };
            assert_eq!(
                bits(&render(true)),
                bits(&render(false)),
                "synth strings {prog} not sample-independent"
            );
        }
    }

    /// GM 61 brass section stays pure model (§2.7): no CC0 section sample
    /// exists and the old trumpet fall-through layered the WRONG
    /// instrument's attack — samples on/off must render byte-identical so a
    /// future wrap cannot land without re-deciding that.
    #[test]
    fn brass_section_61_skips_sample_layer() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        let render = |samples: bool| {
            let mut v = voices::make(61, 69, 100, sr, 6, samples);
            let mut buf = vec![0f32; 22050];
            v.render(&mut buf);
            buf
        };
        assert_eq!(
            bits(&render(true)),
            bits(&render(false)),
            "brass section 61 not sample-independent"
        );
    }

    /// The LA wrapper forwards `set_breath` to the wrapped model (routed
    /// from the reed/flue work: authored CC2/CC11 timbre-tracking used to
    /// no-op on the samples path). Two legs: the engine's neutral brass
    /// note-on seed (pressure 1.0) is a bit-exact no-op — an unauthored
    /// channel renders exactly as before — and an authored (non-neutral)
    /// pressure genuinely reaches the model through the wrap.
    #[test]
    fn la_wrap_forwards_breath() {
        let sr = 44100.0;
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        let render = |prog: u8, breath: Option<(f32, f32)>| {
            let mut v = voices::make(prog, 69, 100, sr, 5, true);
            if let Some((p, g)) = breath {
                v.set_breath(p, g);
            }
            let mut buf = vec![0f32; 44100];
            v.render(&mut buf);
            buf
        };
        // neutral seed == no call, bit-exact (brass defaults pressure 1.0)
        assert_eq!(
            bits(&render(56, Some((1.0, 0.0)))),
            bits(&render(56, None)),
            "neutral set_breath(1.0, 0) must be a bit-exact no-op"
        );
        // authored pressure must change the render for every LA-wrapped
        // wind family the forward serves (brass 56, reed 68, flute 73)
        for prog in [56u8, 68, 73] {
            let (plain, blown) = (render(prog, None), render(prog, Some((0.4, 0.0))));
            assert_ne!(
                bits(&plain),
                bits(&blown),
                "prog {prog}: authored breath does not reach the wrapped model"
            );
        }
    }

    /// The string-section layer must be audible, not just present: samples-on
    /// vs samples-off must differ materially in the first 50 ms. Measured
    /// direction is REGISTER-DEPENDENT, unlike brass (up) or reeds/guitar
    /// (down): the real violin-section bite raises the high-band fraction up
    /// top (hf on/off 0.58/0.42 at 48@76) while the cello/mid sections are
    /// LESS hissy than the saw stack's filtered onset (0.22/0.25 at 48@48,
    /// 0.30/0.37 at 49@67). So the oracle asserts audibility plus a measured
    /// two-sided band: the layer never makes the attack wildly hissier
    /// (<1.6x) and never dulls it to mud (>0.5x).
    #[test]
    fn la_strings_attack_audibility() {
        let sr = 44100.0;
        for (program, key, name) in [
            (48u8, 48u8, "ensemble-low"),
            (48, 60, "ensemble-mid"),
            (48, 76, "ensemble-high"),
            (49, 55, "slow-low"),
            (49, 67, "slow-mid"),
        ] {
            let early = |samples: bool| {
                let mut v = voices::make(program, key, 100, sr, 5, samples);
                let mut buf = vec![0f32; (0.05 * sr) as usize];
                v.render(&mut buf);
                buf
            };
            let (on, off) = (early(true), early(false));
            let diff: Vec<f32> = on.iter().zip(&off).map(|(a, b)| a - b).collect();
            let (d, o) = (crate::testutil::rms(&diff), crate::testutil::rms(&off));
            assert!(
                d > 0.3 * o,
                "{name}: onset barely changes with the layer (diff {d:.5} vs off {o:.5})"
            );
            let hf_frac = |buf: &[f32]| {
                crate::testutil::hp_rms(buf, sr, 1500.0) / crate::testutil::rms(buf).max(1e-9)
            };
            let (r_on, r_off) = (hf_frac(&on), hf_frac(&off));
            assert!(
                r_on < r_off * 1.6 && r_on > r_off * 0.5,
                "{name}: attack hf-frac out of the measured band: on {r_on:.4} vs off {r_off:.4}"
            );
        }
    }

    /// The sampled attack must hand over to the model without a level jump —
    /// and (§3.2, two-sided rewrite) for STRUCK/PLUCKED wrapped voices the
    /// attack must be the render's loudest instant. The second leg is what
    /// makes the seam cap ungameable: the old one-sided reading was
    /// satisfied by cutting the GM 24 wrap gain until the pick sat QUIETER
    /// than the model's sustain (upside-down for a plucked string).
    ///
    /// The no-step leg is DIFFERENTIAL (the §2.7 "measured, per-key seam
    /// limit"): each adjacent-window ratio of the wrapped render is compared
    /// with the model-only render's ratio for the same windows, and the
    /// wrap may not introduce more than a 2.4x step in either direction.
    /// An absolute cap cannot serve both families: a high plucked string
    /// legitimately decays > 2.4x per 100 ms once the pick is honest, while
    /// a sustained voice's own crescendo (the slow-speaking tuba) legitimately
    /// rises — only the step the WRAP adds on top of the voice's own
    /// envelope shape is a seam defect.
    #[test]
    fn la_level_continuity() {
        let sr = 44100.0;
        for (program, key, name, struck) in [
            (40u8, 69u8, "fiddle", false),
            (110u8, 69, "fiddle-110", false),
            (73u8, 69, "flute", false),
            (0u8, 69, "piano", true),
            (0u8, 48, "piano-low", true),
            (56u8, 69, "trumpet", false),
            (57u8, 55, "trombone", false),
            (58u8, 40, "tuba", false),
            (59u8, 69, "muted-trumpet", false),
            (60u8, 62, "french-horn", false),
            (68u8, 76, "oboe", false),
            (69u8, 64, "english-horn", false),
            (70u8, 48, "bassoon", false),
            (71u8, 60, "clarinet", false),
            (24u8, 45, "nylon-guitar-low", true),
            (24u8, 52, "nylon-guitar", true),
            (24u8, 64, "nylon-guitar-high", true),
            // steel rows added with the 0.30 s fade widen (HLD §6 4b — the
            // dry-out case was previously unguarded; key ≥ ~76 excluded for
            // the pre-existing high-key handover cliff, see scratchpad)
            (25u8, 45, "steel-guitar-low", true),
            (25u8, 52, "steel-guitar", true),
            (25u8, 64, "steel-guitar-high", true),
            // nylon key-76 row added with the guitar-block-two damper hold
            // (decay cliff fixed; measured 1.61× at this vel-100 fixture).
            // Steel k76 stays out of THIS fixture, but its level parity is no
            // longer open: the ~4× gap closed with the Phase-2 STEEL re-baselines
            // + the k=2 velocity law, and `la_steel_high_key_level_parity` now
            // pins keys 76/79/83 (MM-REQ-KILN-00027).
            (24u8, 76, "nylon-guitar-top", true),
            (6u8, 48, "harpsichord-low", true),
            (6u8, 60, "harpsichord", true),
            (6u8, 72, "harpsichord-high", true),
            // GM15 dulcimer: trunk added the LA onset (Freesound) while Phase-2
            // made the model Shaped + de-impulsified its click, so the seam is
            // re-guarded here like steel's — the sample was calibrated against
            // the pre-Shaped model. Keys inside the sampled range (E4..C5).
            (15u8, 64, "dulcimer-low", true),
            (15u8, 69, "dulcimer", true),
            (15u8, 72, "dulcimer-high", true),
            (48u8, 48, "string-ens-low", false),
            (48u8, 76, "string-ens-high", false),
            (49u8, 55, "slow-strings", false),
            (42u8, 48, "cello-low", false),
            (42u8, 69, "cello-high", false),
            (43u8, 40, "contrabass", false),
        ] {
            let fine = assert_wrap_seam(program, key, 100, sr, 0, name);
            // struck/plucked: the attack is the global peak — 50 ms windows
            // from t=0, the loudest must start inside the first 150 ms
            if struck {
                assert_attack_is_peak(&fine, name);
            }
        }
    }

    /// The SINGLE seam-continuity contract (code-review A4 — three tests
    /// used to carry private copies that could drift): the wrap may not add
    /// more than a 2.4× level step across adjacent 100 ms windows beyond
    /// the model's own envelope shape (windows scale with `sr`: 100 ms
    /// coarse from 50 ms, 1 s render, seed 5). `skip` drops leading window
    /// pairs a caller has documented reason to exclude. Returns the 50 ms
    /// fine windows for attack-leg callers.
    /// MM-REQ-KILN-00027: steel high-key LEVEL parity. The seam-shape oracle
    /// above cannot see this: at keys ≥76 the peak-normalized steel take
    /// speaks ~3.6–4.0× (≈12 dB) OVER the ringing model at every velocity
    /// (scratchpad 2026.07.19), because the flat LA_STEEL gain ignores how
    /// the model's spoken level falls with key. Bar 2.2×: nylon's healthy
    /// wrap sits at 1.6–1.7×, the un-tapered steel at 3.6–4.0× — red before
    /// the per-key taper, green after, honest floor 0.8× against over-taper.
    #[test]
    fn la_steel_high_key_level_parity() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        for key in [76u8, 79, 83] {
            for vel in [60u8, 100] {
                let early = |samples: bool| {
                    let mut v = voices::make(25, key, vel, sr, 5, samples);
                    let mut buf = vec![0f32; (0.4 * sr) as usize];
                    v.render(&mut buf);
                    let (a, b) = ((0.05 * sr) as usize, (0.30 * sr) as usize);
                    (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                };
                let ratio = early(true) / early(false).max(1e-12);
                assert!(
                    (0.8..2.2).contains(&ratio),
                    "steel key {key} vel {vel}: wrapped/model early-RMS ratio {ratio:.2} outside 0.8–2.2"
                );
            }
        }
    }

    /// Calibration printer for the steel high-key taper (MM-REQ-KILN-00027).
    #[test]
    #[ignore = "calibration harness — run by hand"]
    fn print_steel_wrap_level_ratios() {
        let sr = 44100.0;
        for key in [60u8, 64, 68, 72, 74, 76, 79, 83, 86, 90] {
            for vel in [60u8, 100] {
                let early = |samples: bool| {
                    let mut v = voices::make(25, key, vel, sr, 5, samples);
                    let mut buf = vec![0f32; (0.4 * sr) as usize];
                    v.render(&mut buf);
                    let (a, b) = ((0.05 * sr) as usize, (0.30 * sr) as usize);
                    (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                };
                println!(
                    "steel key {key:3} vel {vel:3}: wrapped/model {:.2}",
                    early(true) / early(false).max(1e-12)
                );
            }
        }
    }

    /// Calibration printer for the GM 32-35 bass seam taper (MM-BUG-KILN-00075).
    ///
    /// Measures the wrapped/model RMS ratio over the bass fade window [0.05, 0.35] s —
    /// the window `LaVoice` hands from sample to model, and where the whole deficit
    /// lives. Same method as the GM48/49 printer below: 3-seed geomean, because the
    /// model's per-note jitter swings a single-seed ratio enough to mis-fit a taper.
    ///
    /// Measured through `bass_la_alt`, which is where the LA bass now lives (Arthur
    /// moved it off the default bank on 2026-07-24), so this reads the real shipped
    /// path rather than a reconstruction of it.
    #[test]
    #[ignore = "calibration harness — run by hand"]
    fn print_ebass_wrap_level_ratios() {
        let sr = 44100.0;
        for program in [32u8, 33, 34, 35] {
            for key in [
                16u8, 20, 24, 28, 31, 34, 38, 40, 43, 46, 50, 52, 55, 58, 62, 64,
            ] {
                for vel in [48u8, 72, 100, 120] {
                    // Decomposed by window, because the deficit is NOT uniform across the
                    // crossfade: `LaVoice` mutes the model entirely until `fade.0`, so
                    // [0, 0.05] is sample-owned and carries the whole hit, while
                    // [0.15, 0.35] is nearly model-owned and barely moves. Measuring only
                    // the [0.05, 0.35] fade span (the GM48/49 printer's window, where the
                    // strings mismatch did live) reads this bug as a mild -2..-5 dB and
                    // would mis-fit the taper by ~10 dB.
                    let win = |seed: u32, samples: bool, t0: f32, t1: f32| {
                        let mut v = voices::bass_la_alt(program, key, vel, sr, seed, samples);
                        let mut buf = vec![0f32; (0.5 * sr) as usize];
                        v.render(&mut buf);
                        let (a, b) = ((t0 * sr) as usize, (t1 * sr) as usize);
                        (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                    };
                    let seeds = [5u32, 21, 99];
                    let geo = |t0: f32, t1: f32| {
                        let r = |s: u32| win(s, true, t0, t1) / win(s, false, t0, t1).max(1e-12);
                        (seeds.iter().map(|&s| r(s).ln()).sum::<f32>() / seeds.len() as f32).exp()
                    };
                    let (w0, w1, w2, all) = (
                        geo(0.0, 0.05),
                        geo(0.05, 0.15),
                        geo(0.15, 0.35),
                        geo(0.0, 0.35),
                    );
                    // Peak ratio too: an RMS match is NOT a peak match when the sampled
                    // onset and the modeled attack have different crest factors, so a
                    // taper fitted on RMS alone can push the sample into clipping.
                    let pk = |samples: bool| {
                        let mut v = voices::bass_la_alt(program, key, vel, sr, 5, samples);
                        let mut buf = vec![0f32; (0.5 * sr) as usize];
                        v.render(&mut buf);
                        buf[..(0.35 * sr) as usize]
                            .iter()
                            .fold(0f32, |m, x| m.max(x.abs()))
                    };
                    let (pk_on, pk_off) = (pk(true), pk(false));
                    let db = |g: f32| 20.0 * g.max(1e-12).log10();
                    println!(
                        "ebass gm{program} key {key:3} vel {vel:3}: \
                         muted[0,50ms] {w0:5.3} ({:+6.1} dB) | \
                         [50,150] {w1:5.3} ({:+6.1}) | [150,350] {w2:5.3} ({:+6.1}) | \
                         all[0,350] {all:5.3} ({:+6.1}) | peak {pk_on:.3}/{pk_off:.3} = {:.2}x",
                        db(w0),
                        db(w1),
                        db(w2),
                        db(all),
                        pk_on / pk_off.max(1e-12)
                    );
                }
            }
        }
    }

    /// MM-BUG-KILN-00075: the GM 32-35 sampled bass onset must land on the level of the
    /// model it displaces, through the window where it is the ONLY thing sounding.
    ///
    /// `LaVoice`'s crossfade is sum-to-one: the model is muted outright until `fade.0`
    /// (50 ms here), so in `[0, 50 ms]` the wrap gain IS the output level and nothing
    /// fills a deficit. One flat `LA_EBASS` / `LA_PIZZBASS` gain sat that window at 0.389
    /// geomean — **-8.2 dB, worst point -19 dB** — and a real bass line never recovers it,
    /// because 90% of its notes are shorter than the 350 ms handover.
    ///
    /// **Measured on the sample-owned window, not the fade span.** Measuring `[0.05,
    /// 0.35]` (the GM48/49 oracle's window, correct for *that* bug) reads this one as a
    /// mild -2..-5 dB, because the model term progressively dominates there and a gain
    /// barely moves it. That mis-reads the defect by ~10 dB and would pass a taper fitted
    /// 10 dB short. The printer prints all three windows so the trap stays visible.
    ///
    /// **Peak is bounded as well as level.** An RMS match is not a peak match when the
    /// sampled onset and the modeled attack have different crest factors, so a
    /// level-only bound would license a taper that restores RMS by shipping a spike.
    ///
    /// 3-seed geomean, as the strings oracle: the model's per-note jitter swings a
    /// single-seed ratio enough to false-fail. Fail-first: untapered, the GM33 low keys
    /// sit at 0.11-0.25 — far outside the 0.60 floor.
    ///
    /// The band is honestly wide on the low side because GM32 is a deliberate compromise:
    /// it is fitted on the whole handover rather than the onset (its pizzicato sample
    /// outlives the `UPRIGHT` model, so onset parity would buy a +10 dB bloom later), which
    /// leaves its onset ~3.7 dB under. That residual is a decay-SHAPE mismatch, not a gain
    /// error, and no scalar can close it.
    #[test]
    fn la_ebass_seam_level_parity() {
        let sr = 44100.0;
        let seeds = [5u32, 21, 99];
        for program in [32u8, 33, 34, 35] {
            for key in [20u8, 24, 28, 34, 40, 46, 50] {
                for vel in [48u8, 100, 120] {
                    let render = |seed: u32, samples: bool| {
                        let mut v = voices::bass_la_alt(program, key, vel, sr, seed, samples);
                        let mut buf = vec![0f32; (0.5 * sr) as usize];
                        v.render(&mut buf);
                        buf
                    };
                    let rms_win = |b: &[f32], t0: f32, t1: f32| {
                        let (a, z) = ((t0 * sr) as usize, (t1 * sr) as usize);
                        (b[a..z].iter().map(|&x| x * x).sum::<f32>() / (z - a) as f32).sqrt()
                    };
                    // Skip keys where the repitch leaves LaVoice's window: there the wrap
                    // legitimately falls back to the bare model and the ratio is exactly 1.
                    let engaged = render(5, true) != render(5, false);
                    if !engaged {
                        continue;
                    }
                    let ratio = |t0: f32, t1: f32| {
                        let r = |s: u32| {
                            rms_win(&render(s, true), t0, t1)
                                / rms_win(&render(s, false), t0, t1).max(1e-12)
                        };
                        (seeds.iter().map(|&s| r(s).ln()).sum::<f32>() / seeds.len() as f32).exp()
                    };
                    let onset = ratio(0.0, 0.05);
                    let handover = ratio(0.0, 0.35);
                    let peak = |samples: bool| {
                        render(5, samples)[..(0.35 * sr) as usize]
                            .iter()
                            .fold(0f32, |m, x| m.max(x.abs()))
                    };
                    let pk = peak(true) / peak(false).max(1e-12);

                    assert!(
                        (0.40..=1.35).contains(&onset),
                        "GM{program} key {key} vel {vel}: sampled onset sits at {onset:.3}x \
                         the model over [0, 50 ms] ({:+.1} dB). The model is MUTED there, so \
                         this gain is the whole output level — re-fit ebass_seam_gain with \
                         sampler::tests::print_ebass_wrap_level_ratios.",
                        20.0 * onset.max(1e-12).log10()
                    );
                    assert!(
                        (0.60..=1.45).contains(&handover),
                        "GM{program} key {key} vel {vel}: the whole [0, 350 ms] handover \
                         sits at {handover:.3}x the model ({:+.1} dB) — the sampled layer \
                         is not level-matched across the crossfade.",
                        20.0 * handover.max(1e-12).log10()
                    );
                    assert!(
                        pk <= 1.60,
                        "GM{program} key {key} vel {vel}: the wrapped peak is {pk:.2}x the \
                         model's. An RMS match is not a peak match — a taper must not buy \
                         level parity by shipping a transient spike."
                    );
                }
            }
        }
    }

    /// Calibration printer for the GM48/49 string-section seam taper
    /// (MM-BUG-KILN-00046). Measures the wrapped/model RMS ratio over the
    /// strings fade window [0.10, 0.40] s — where the whole excess lives
    /// (0.00 dB from b4 on) — across the sampled range and both velocity
    /// layers, so the per-key taper can be calibrated against the model's
    /// actual output rather than hand-tuned.
    #[test]
    #[ignore = "calibration harness — run by hand"]
    fn print_strings_wrap_level_ratios() {
        let sr = 44100.0;
        // Full active-wrap range: `LaVoice::build` falls back to the bare model
        // only when the repitch step leaves [0.5, 2.05], which at 44.1 kHz keeps
        // the wrap live roughly keys 25-98 — so the taper must cover the edges,
        // not just 40-84. Two seeds spot-check that the ratio is seed-stable
        // (the model carries +/-10% t60 / +/-8% bright jitter).
        for program in [48u8, 49] {
            for key in [
                28u8, 32, 36, 40, 44, 48, 52, 55, 58, 60, 64, 68, 72, 76, 80, 84, 88, 92, 96,
            ] {
                for vel in [72u8, 110] {
                    let early = |seed: u32, samples: bool| {
                        let mut v = voices::make(program, key, vel, sr, seed, samples);
                        let mut buf = vec![0f32; (0.5 * sr) as usize];
                        v.render(&mut buf);
                        let (a, b) = ((0.10 * sr) as usize, (0.40 * sr) as usize);
                        (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                    };
                    let r = |s: u32| early(s, true) / early(s, false).max(1e-12);
                    // geomean over 3 seeds — the model's per-note jitter swings a
                    // single-seed ratio by up to ~0.3, so calibrate against the
                    // seed-robust central value, not one seed's luck.
                    let seeds = [5u32, 21, 99];
                    let g =
                        (seeds.iter().map(|&s| r(s).ln()).sum::<f32>() / seeds.len() as f32).exp();
                    println!(
                        "strings gm{program} key {key:3} vel {vel:3}: geomean {g:5.2} ({:+5.1} dB)  [s5 {:.2} s21 {:.2} s99 {:.2}]",
                        20.0 * g.max(1e-12).log10(),
                        r(5),
                        r(21),
                        r(99)
                    );
                }
            }
        }
    }

    /// MM-BUG-KILN-00046: the GM48/49 string-section sampled onset must land on
    /// the `strings()` model's level through the [0.10, 0.40] s crossfade —
    /// a level-PARITY band, which the slope-only `la_level_continuity` cannot
    /// see. Before the `strings_seam_gain` taper the single `LA_STRINGS` gain
    /// sat the sample +1..+6 dB over the model at most keys (inverting GM49's
    /// swell) while repitched `celens` zones near keys 58/76 sat under it.
    ///
    /// Metric is a 3-SEED GEOMEAN — the model's per-note jitter swings a
    /// single-seed ratio ~0.3, so a single-seed bound would false-fail on other
    /// seeds. Coverage spans the edge zones (keys 33/90, near the ends of the
    /// active-wrap range) and the velocity EXTREMES (40/120, either side of the
    /// vel-80 sample-layer split), not just the mids. Fail-first: at vel ≥ 80
    /// the low-key ratio is 2.0–2.1× untapered — well outside 1.30. The band is
    /// program-aware: GM48 takes the full taper (parity both sides), GM49 is
    /// capped at 1.0 for swell protection so its under-zones sit legitimately
    /// low — hence one honest band wide enough for both, ±~2.5 dB, which the
    /// seed geomean makes meaningful rather than noise-dominated.
    #[test]
    fn la_strings_seam_level_parity() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        let seeds = [5u32, 21, 99];
        let geo_ratio = |program: u8, key: u8, vel: u8| -> f32 {
            let early = |seed: u32, samples: bool| {
                let mut v = voices::make(program, key, vel, sr, seed, samples);
                let mut buf = vec![0f32; (0.5 * sr) as usize];
                v.render(&mut buf);
                let (a, b) = ((0.10 * sr) as usize, (0.40 * sr) as usize);
                (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
            };
            (seeds
                .iter()
                .map(|&s| (early(s, true) / early(s, false).max(1e-12)).ln())
                .sum::<f32>()
                / seeds.len() as f32)
                .exp()
        };
        for program in [48u8, 49] {
            for key in [33u8, 48, 58, 68, 90] {
                for vel in [40u8, 72, 110, 120] {
                    let g = geo_ratio(program, key, vel);
                    assert!(
                        (0.75..=1.30).contains(&g),
                        "strings gm{program} key {key} vel {vel}: 3-seed-geomean wrapped/model seam ratio {g:.2} outside 0.75-1.30"
                    );
                }
            }
        }
    }

    /// MM-BUG-KILN-00046: the sampled GM49 onset must not DEGRADE the envelope
    /// shape the `strings()` model produces on its own. Deliberately RELATIVE,
    /// not an absolute "body >= onset": at low keys the model itself does not
    /// swell (the strings MODEL's low-register envelope, KILN-00053, out of this
    /// sampler seam's scope) and the sample owns a real section-attack PUNCH in
    /// [0, 0.10] s that costs body/onset even at a level-matched seam — so
    /// demanding an absolute swell would guard something this bug cannot deliver.
    /// What it pins: where the model swells (m > 1.05), the wrapped body/onset
    /// stays within 30% of the model's — which fails hard on the original +6 dB
    /// onset (w/m ~0.5-0.6) and passes the taper (worst ~0.73). 3-seed geomean
    /// (the metric swings ~0.3 per seed). Non-vacuity is asserted so the guard
    /// cannot pass by simply finding no swelling case.
    #[test]
    fn la_strings_onset_preserves_model_swell() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        let seeds = [5u32, 21, 99];
        // 3-seed geomean of body(0.8..1.2 s)/onset(0..0.4 s), for GM49.
        let geo_rise = |key: u8, vel: u8, samples: bool| -> f32 {
            let one = |seed: u32| {
                let mut v = voices::make(49, key, vel, sr, seed, samples);
                let mut buf = vec![0f32; (1.3 * sr) as usize];
                v.render(&mut buf);
                let m = |t0: f32, t1: f32| {
                    let (a, b) = ((t0 * sr) as usize, (t1 * sr) as usize);
                    (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
                };
                m(0.8, 1.2) / m(0.0, 0.4).max(1e-12)
            };
            (seeds.iter().map(|&s| one(s).ln()).sum::<f32>() / seeds.len() as f32).exp()
        };
        let mut guarded = 0usize;
        let mut worst: Option<(u8, u8, f32)> = None;
        for key in [48u8, 55, 58, 64, 68, 72] {
            for vel in [72u8, 110] {
                let (w, m) = (geo_rise(key, vel, true), geo_rise(key, vel, false));
                let wm = w / m;
                println!("gm49 swell key {key} vel {vel}: body/onset wrapped {w:.2}  model-only {m:.2}  w/m {wm:.2}");
                if m > 1.05 {
                    guarded += 1;
                    if worst.map(|(.., x)| wm < x).unwrap_or(true) {
                        worst = Some((key, vel, wm));
                    }
                }
            }
        }
        assert!(
            guarded >= 6,
            "non-vacuous guard broken: only {guarded} of 12 GM49 cases have a swelling model (m > 1.05) — the model or probe changed; re-derive before trusting this oracle"
        );
        let (key, vel, wm) = worst.expect("guarded >= 6 implies a worst case");
        assert!(
            wm >= 0.70,
            "gm49 key {key} vel {vel}: sampled onset degrades the model's swell — wrapped/model-only body/onset ratio {wm:.2} < 0.70"
        );
    }

    fn assert_wrap_seam(
        program: u8,
        key: u8,
        vel: u8,
        sr: f32,
        skip: usize,
        label: &str,
    ) -> Vec<f32> {
        assert_wrap_seam_seed(program, key, vel, sr, skip, label, 5)
    }

    #[allow(clippy::too_many_arguments)]
    fn assert_wrap_seam_seed(
        program: u8,
        key: u8,
        vel: u8,
        sr: f32,
        skip: usize,
        label: &str,
        seed: u32,
    ) -> Vec<f32> {
        let win = |samples: bool| {
            let mut v = voices::make(program, key, vel, sr, seed, samples);
            let mut buf = vec![0f32; sr as usize]; // 1 s, note held
            v.render(&mut buf);
            let w = (0.05 * sr) as usize;
            let rms = |a: usize, b: usize| {
                (buf[a..b].iter().map(|&x| x * x).sum::<f32>() / (b - a) as f32).sqrt()
            };
            let coarse: Vec<f32> = (0..9)
                .map(|k| rms(w + k * 2 * w, w + (k + 1) * 2 * w))
                .collect();
            let fine: Vec<f32> = (0..19).map(|k| rms(k * w, (k + 1) * w)).collect();
            (coarse, fine)
        };
        let ((wv, fine), (m, _)) = (win(true), win(false));
        for (pw, pm) in wv.windows(2).zip(m.windows(2)).skip(skip) {
            let (rw, rm) = (pw[0] / pw[1].max(1e-12), pm[0] / pm[1].max(1e-12));
            let excess = (rw / rm).max(rm / rw);
            assert!(
                excess < 2.4,
                "{label}: wrap-introduced level step across the crossfade \
                 ({excess:.2}x beyond the model's own shape): wrapped {wv:?} \
                 vs model {m:?}"
            );
        }
        fine
    }

    fn piano_release_reading(mut voice: Box<dyn Voice>, sr: f32) -> (f32, f32, bool) {
        let hold_len = (0.3125 * sr) as usize;
        let window = (0.020 * sr) as usize;
        let mut held = vec![0.0; hold_len];
        assert!(voice.render(&mut held), "piano died before note-off");
        let before = crate::testutil::rms(&held[hold_len - window..]);

        voice.note_off();
        let mut release = vec![0.0; (2.0 * sr) as usize];
        voice.render(&mut release);
        let mut probe = [0.0; 128];
        let alive = voice.render(&mut probe);
        let gap_start = (0.0425 * sr) as usize;
        let gap_end = (0.0625 * sr) as usize;
        let gap = crate::testutil::rms(&release[gap_start..gap_end]);
        let tail_start = (0.230 * sr) as usize;
        let tail_end = (0.250 * sr) as usize;
        let tail = crate::testutil::rms(&release[tail_start..tail_end]);
        (
            20.0 * (before / gap.max(1e-12)).log10(),
            20.0 * (before / tail.max(1e-12)).log10(),
            alive,
        )
    }

    /// How far the MEASURED release may sit from the damper curve's own prediction.
    ///
    /// Not free parameters: calibrated against measured renders, then left with just
    /// enough margin to absorb the modal body's own decay and the sampled layer
    /// bridging the gap. Both bounds are ratios OF THE CURVE, so re-shaping the
    /// damper moves the expectation with it instead of silently invalidating a
    /// hand-written dB constant.
    /// Model-only: the modal body decays slowly over 62.5 ms, so the measured drop
    /// tracks the damper closely (0.87-0.94x across keys 62/66/69).
    const GAP_RATIO_MIN_MODEL: f32 = 0.80;
    /// With the sampled onset layer the drop is SMALLER, because bridging a fast
    /// repeat is exactly what that layer is for. Still far above the ~0.10x a
    /// missing release would read, so this separates "bridged" from "absent".
    const GAP_RATIO_MIN_SAMPLED: f32 = 0.40;
    const GAP_RATIO_MAX: f32 = 1.10;
    const TAIL_RATIO_MIN: f32 = 0.75;

    #[test]
    fn gm0_fra_gap_release_bridges_then_clears() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        for samples in [false, true] {
            for key in [62u8, 66, 69] {
                let mut rr_drops = Vec::new();
                for seed in [1u32, 2] {
                    // Hold the model seed fixed while selecting each sample RR
                    // explicitly. Otherwise the measured "RR spread" also contains
                    // the model's seeded modal variation (about 0.6 dB here).
                    let voice = if samples {
                        // The GM0 DEFAULT recording, read from the source table so
                        // this tracks whatever slot 0 currently holds rather than
                        // pinning one bank by name.
                        let src = &voices::GM0_SOURCES[0];
                        voices::acoustic_grand_with_bank(
                            (src.bank)(104, seed == 2),
                            key,
                            104,
                            sr,
                            1,
                            false,
                            src.voicing(),
                        )
                    } else {
                        voices::make(0, key, 104, sr, seed, false)
                    };
                    let (gap_drop, tail_drop, alive) = piano_release_reading(voice, sr);
                    println!(
                        "GM0 key {key} seed {seed} samples={samples}: \
                         gap {gap_drop:.2} dB, 250ms {tail_drop:.2} dB"
                    );
                    // Bars DERIVED from the damper curve, not flat constants
                    // (MM-BUG-KILN-00104). A 60 dB-per-T60 exponential predicts
                    // this key's drop; the old flat 4..10 dB band assumed every
                    // key shared one release, which is the thing the felt damper
                    // models away. Deriving it also TIGHTENS the test: the old
                    // band spanned 2.5x, these span 2x and track the curve.
                    let (t60, _) = voices::PianoDamper::Felt.t60_for(key);
                    let gap_expect = 60.0 * 0.0625 / t60;
                    let tail_expect = 60.0 * 0.25 / t60;
                    println!(
                        "  key {key} t60 {t60:.3}s: gap expect {gap_expect:.2} \
                         got {gap_drop:.2} (x{:.2}), tail expect {tail_expect:.2} \
                         got {tail_drop:.2} (x{:.2})",
                        gap_drop / gap_expect,
                        tail_drop / tail_expect
                    );
                    assert!(
                        gap_drop <= gap_expect * GAP_RATIO_MAX,
                        "GM0 key {key} seed {seed} samples={samples}: 62.5ms gap drop \
                         {gap_drop:.2} dB exceeds {GAP_RATIO_MAX}x the {gap_expect:.2} dB \
                         its {t60:.3}s damper predicts — the note is cut, not damped"
                    );
                    let gap_min = if samples {
                        GAP_RATIO_MIN_SAMPLED
                    } else {
                        GAP_RATIO_MIN_MODEL
                    };
                    assert!(
                        gap_drop >= gap_expect * gap_min,
                        "GM0 key {key} seed {seed} samples={samples}: 62.5ms gap drop \
                         {gap_drop:.2} dB is under {gap_min}x the {gap_expect:.2} dB \
                         its {t60:.3}s damper predicts — the release barely engages"
                    );
                    assert!(
                        tail_drop >= tail_expect * TAIL_RATIO_MIN,
                        "GM0 key {key} seed {seed} samples={samples}: only {tail_drop:.2} dB \
                         down after 250 ms, under {TAIL_RATIO_MIN}x the {tail_expect:.2} dB \
                         its {t60:.3}s damper predicts"
                    );
                    assert!(
                        !alive,
                        "GM0 key {key} seed {seed} samples={samples}: \
                         voice remained alive 2 seconds after note-off"
                    );
                    rr_drops.push(gap_drop);
                }
                if samples {
                    assert!(
                        (rr_drops[0] - rr_drops[1]).abs() <= 2.0,
                        "GM0 key {key}: round-robin release spread {:.2} dB",
                        (rr_drops[0] - rr_drops[1]).abs()
                    );
                }
            }
        }
    }

    #[test]
    fn gm0_conditioned_bank_still_needs_the_release_override() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        for (key, seed) in [(62u8, 1u32), (66, 2), (69, 1)] {
            let legacy = voices::acoustic_grand_with_bank(
                piano_bank(104, seed & 1 == 0),
                key,
                104,
                sr,
                seed,
                false,
                voices::LEGACY_VOICING,
            );
            let (gap_drop, _, _) = piano_release_reading(legacy, sr);
            println!("conditioned GM0 key {key} legacy gap: {gap_drop:.2} dB");
            assert!(
                gap_drop > 10.0,
                "GM0 key {key}: conditioned bank unexpectedly meets the gap target \
                 on legacy release ({gap_drop:.2} dB)"
            );
        }
    }

    #[test]
    fn gm0_release_clears_across_the_piano_register() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        for samples in [false, true] {
            for key in [36u8, 60, 84] {
                let (_, tail_drop, alive) =
                    piano_release_reading(voices::make(0, key, 104, sr, 1, samples), sr);
                // Derived from the felt curve, per key — see the note in
                // `gm0_fra_gap_release_bridges_then_clears`. A flat 24 dB bar here
                // asserted that C2 damps as fast as C6, which no piano does.
                let (t60, _) = voices::PianoDamper::Felt.t60_for(key);
                let tail_expect = 60.0 * 0.25 / t60;
                println!(
                    "  key {key} samples={samples}: t60 {t60:.3}s, tail expect \
                     {tail_expect:.2} dB, got {tail_drop:.2} (x{:.2})",
                    tail_drop / tail_expect
                );
                assert!(
                    tail_drop >= tail_expect * TAIL_RATIO_MIN,
                    "GM0 key {key} samples={samples}: only {tail_drop:.2} dB down at 250 ms, \
                     under {TAIL_RATIO_MIN}x the {tail_expect:.2} dB its {t60:.3}s damper \
                     predicts"
                );
                assert!(
                    !alive,
                    "GM0 key {key} samples={samples}: alive after the 2 s reap probe"
                );
            }
        }
    }

    /// The GM0 damper reaches the GM0 ALTERNATES, and stops there.
    ///
    /// RESPECIFIED 2026.07.25 (MM-BUG-KILN-00103, Arthur). This oracle used to assert
    /// the opposite — that the calibrated release must NOT reach the alternates — back
    /// when one `Option` argument switched the sample-layer gain and the damper
    /// together. That coupling was the bug: choosing a different *recording* also cut
    /// the string release from 0.45 s to 0.10 s (and the sampled layer's to 0.06 s),
    /// which is not something a microphone can do. Arthur heard it as the B1 upright
    /// sounding thin on Tubular Bells.
    ///
    /// The bar is unchanged in strength — each voice must still match an explicitly
    /// constructed control to 0.01 dB. Only WHICH control is correct has changed, and
    /// only for the GM0 alternates. GM1's alternates, GM3 and GM24 keep the legacy
    /// damper and are still pinned here, so this test also proves the change did not
    /// spill sideways.
    #[test]
    fn gm0_damper_reaches_gm0_alternates_and_stops_there() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        let (default_drop, _, _) = piano_release_reading(voices::make(0, 66, 104, sr, 1, true), sr);
        assert!(
            default_drop <= 10.0,
            "default GM0 did not opt into the calibrated release"
        );
        for (name, voice, control) in [
            (
                // GM0 alternate: each alternate keeps its OWN bake calibration, but
                // takes the GM0 damper — that is the 00103 fix. Bank 2 is the
                // Salamander since the 2026.07.26 renumber; read it from the table
                // rather than naming a slot, so a future re-order cannot make this
                // control disagree with the voice it is checking.
                "GM0 Salamander alternate",
                crate::altbank::make(0, 2, 66, 104, sr, 1, true),
                {
                    let src = &voices::GM0_SOURCES[2];
                    voices::acoustic_grand_with_bank(
                        (src.bank)(104, false),
                        66,
                        104,
                        sr,
                        1,
                        false,
                        src.voicing(),
                    )
                },
            ),
            (
                "GM0 undefined-CC0 fallback",
                crate::altbank::make(0, 99, 66, 104, sr, 1, true),
                voices::acoustic_grand_with_bank(
                    &[],
                    66,
                    104,
                    sr,
                    1,
                    false,
                    voices::GM0_SOURCES[0].voicing(),
                ),
            ),
            (
                // GM1 now shares the modelled felt damper (Step 2). It is still
                // pinned here so a future change cannot move it silently.
                "GM1 Bright",
                voices::make(1, 66, 104, sr, 1, true),
                voices::acoustic_grand_with_bank(
                    kawai_bank(104, false),
                    66,
                    104,
                    sr,
                    1,
                    true,
                    voices::GM1_VOICING,
                ),
            ),
        ] {
            let (drop, _, _) = piano_release_reading(voice, sr);
            let (control_drop, _, _) = piano_release_reading(control, sr);
            assert!(
                (drop - control_drop).abs() <= 0.01,
                "{name}: release drifted from its explicit control \
                 ({drop:.2} dB vs {control_drop:.2} dB)"
            );
        }

        let (honky_drop, _, _) = piano_release_reading(voices::make(3, 66, 104, sr, 1, true), sr);
        assert!(
            (35.5..=36.0).contains(&honky_drop),
            "GM3 honky-tonk release drifted from its legacy window ({honky_drop:.2} dB)"
        );

        let (nylon_drop, _, _) = piano_release_reading(voices::make(24, 52, 104, sr, 1, true), sr);
        assert!(
            (5.5..=6.5).contains(&nylon_drop),
            "GM24 nylon LA release drifted from its legacy window ({nylon_drop:.2} dB)"
        );
    }

    /// Runtime zone-selection leg for the conditioned bank. The generator owns
    /// source-time attack/body shape; this checks the repitched BODY at every
    /// physical root and on both sides of each nearest-zone boundary. Attack
    /// RMS is only a silence guard here because pitching different recordings
    /// up/down changes their spectrum, which is explicitly outside conditioning.
    #[test]
    fn gm0_conditioned_bank_is_continuous_across_keys_layers_and_round_robins() {
        if !crate::embedded_samples_available() {
            return;
        }

        struct Silent;
        impl Voice for Silent {
            fn render(&mut self, _out: &mut [f32]) -> bool {
                true
            }
            fn note_off(&mut self) {}
            fn released(&self) -> bool {
                false
            }
            fn kind(&self) -> &'static str {
                "silent"
            }
        }

        let sr = 44100.0;
        let keys = [
            36u8, 39, 40, 43, 45, 46, 48, 51, 52, 55, 57, 58, 60, 63, 64, 67, 69, 70, 72, 75, 76,
            79, 81, 82, 84,
        ];
        let boundaries = [
            (39u8, 40u8),
            (45, 46),
            (51, 52),
            (57, 58),
            (63, 64),
            (69, 70),
            (75, 76),
            (81, 82),
        ];
        for vel in [48u8, 80, 104] {
            for seed in [1u32, 2] {
                let mut readings = Vec::new();
                for &key in &keys {
                    let (gain, _) = voices::LA_PIANO;
                    let bank = piano_bank(vel, seed & 1 == 0);
                    let step = key_freq(key) / nearest(bank, key_freq(key)).root * 44100.0 / sr;
                    let mut sample = LaVoice::wrap_release(
                        Box::new(Silent),
                        bank,
                        key,
                        vel,
                        sr,
                        gain,
                        (2.0, 3.0),
                        crate::voices::GM0_RELEASE_T60,
                    );
                    let mut buf = vec![0.0; sr as usize];
                    sample.render(&mut buf);
                    let attack = crate::testutil::rms(&buf[..(0.030 * sr / step) as usize]);
                    let body = crate::testutil::rms(
                        &buf[(0.140 * sr / step) as usize..(0.220 * sr / step) as usize],
                    );
                    assert!(
                        attack > 1e-4,
                        "GM0 key {key} vel {vel} seed {seed} is silent"
                    );
                    readings.push((key, body));
                }

                for &(left_key, right_key) in &boundaries {
                    let (_, left_body) = readings
                        .iter()
                        .copied()
                        .find(|&(key, _)| key == left_key)
                        .unwrap();
                    let (_, right_body) = readings
                        .iter()
                        .copied()
                        .find(|&(key, _)| key == right_key)
                        .unwrap();
                    let step_db = 20.0 * (left_body / right_body.max(1e-12)).log10();
                    assert!(
                        step_db.abs() <= 3.0,
                        "GM0 body jumps {step_db:+.2} dB across keys \
                         {left_key}/{right_key} at vel {vel} seed {seed}"
                    );
                }
            }
        }
    }

    /// Companion leg for struck/plucked rows of [`assert_wrap_seam`].
    fn assert_attack_is_peak(fine: &[f32], label: &str) {
        // Every struck voice must peak inside the 150 ms budget.
        //
        // `piano-low` used to get a 4th window: the CONDITIONED VSCO upright, GM0's
        // default until 2026.07.26, reached its hammer/body maximum in the 150-200 ms
        // window. The B1 upright that replaced it peaks in window 1 like everything
        // else (once given its own make-up gain — `PianoSampleCal::B1Upright`), so the
        // exception is retired rather than inherited. That is the point of retiring it
        // HERE: had it been left in place it would have silently absorbed the B1's
        // late-swell defect instead of exposing it.
        let attack_windows = 3;
        let attack = fine[..attack_windows].iter().fold(0f32, |mx, &x| mx.max(x));
        let late = fine[attack_windows..].iter().fold(0f32, |mx, &x| mx.max(x));
        // The `harpsichord-low` exception that used to sit here is GONE, retired by its
        // own bounded assertion exactly as designed: once `LaFx::vel_sense` made the LA
        // onset inherit the model's compression (MM-BUG-KILN-00030), the bloom fell from
        // ~1.118 to 0.743 and tripped the `<= 1.02` side of the bound. The harpsichord
        // now meets the same attack-owns-the-peak rule as every other struck voice, so
        // it needs no special case here.

        // 1 % relative tolerance. The intent is "no LATE BLOOM" — the attack owns the
        // peak — and a bloom that matters is tens of percent. An exact float compare
        // instead trips on a tie: this fired at late 0.16634 vs attack 0.16632, a
        // 0.012 % difference, which is not a bloom by any reading.
        assert!(
            late <= attack * 1.01,
            "{label}: attack is not the peak — late window {late:.5} \
             above attack {attack:.5} by more than 1% ({fine:?})"
        );
    }

    /// MM-BUG-KILN-00130/00133: the B1 upright's recorded body decays faster
    /// than the modeled body during the handoff. A scalar gain can keep the
    /// attack above the eventual sustain, but it cannot stop the envelope
    /// falling into a phase-dependent trough and then swelling back.
    #[test]
    fn b1_upright_handoff_does_not_rebound() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44_100.0;
        let window = (0.050 * sr) as usize;
        for vel in [50u8, 100] {
            for seed in [5u32, 21, 0x9E37, 0x9E37 ^ 2_654_435_761] {
                for key in 21u8..=108 {
                    let render_rebound = |samples| {
                        let mut voice = voices::make(0, key, vel, sr, seed, samples);
                        let mut out = vec![0.0; (0.700 * sr) as usize];
                        assert!(
                            voice.render(&mut out),
                            "B1 upright key {key} vel {vel} seed {seed} \
                             samples={samples} died during hold"
                        );
                        let rms: Vec<f32> =
                            out.chunks_exact(window).map(crate::testutil::rms).collect();
                        let rebound_db = (3..9)
                            .map(|i| {
                                let later = rms[i + 1..14].iter().copied().fold(0.0f32, f32::max);
                                20.0 * (later / rms[i].max(1e-12)).log10()
                            })
                            .fold(f32::NEG_INFINITY, f32::max);
                        (rebound_db, rms)
                    };
                    let (model_rebound, _) = render_rebound(false);
                    let (rebound_db, rms) = render_rebound(true);
                    // 1.5 dB admits normal modal beating. For a seed whose bare
                    // model beats slightly more, the sampled handoff must add
                    // no meaningful rebound of its own.
                    let limit = 1.5f32.max(model_rebound + 0.5);
                    assert!(
                        rebound_db <= limit,
                        "B1 upright key {key} vel {vel} seed {seed} rebounds \
                         {rebound_db:.2} dB after its crossfade trough \
                         versus {model_rebound:.2} dB model-only (limit \
                         {limit:.2} dB; 50 ms RMS: {rms:?})"
                    );
                }
            }
        }
    }

    /// GM 7 clavinet routing (2026.07.17): the DEFAULT bank is the sampled voice,
    /// while BOTH `--no-samples` and the CC0-nonzero ALT bank fall back to the modeled
    /// Pluck — the "move the existing clavinet to the alt bank" contract. A render
    /// check confirms the sampled default is a genuinely different signal from the alt.
    #[test]
    fn clavinet_default_is_sampled_alt_is_modeled() {
        let sr = 44100.0;
        assert_eq!(
            voices::make(7, 60, 100, sr, 5, true).kind(),
            "clavinetsampled",
            "GM7 default (samples on) must be the sampled clavinet"
        );
        assert_eq!(
            voices::make(7, 60, 100, sr, 5, false).kind(),
            "CLAVINET",
            "GM7 --no-samples must be the modeled Pluck"
        );
        assert_eq!(
            crate::altbank::make(7, 1, 60, 100, sr, 5, true).kind(),
            "CLAVINET",
            "GM7 CC0-nonzero alt bank must be the modeled Pluck"
        );
        // the sampled default renders a different signal from the modeled alt
        let (mut def, mut alt) = (
            voices::make(7, 60, 100, sr, 5, true),
            crate::altbank::make(7, 1, 60, 100, sr, 5, true),
        );
        let (mut db, mut ab) = (vec![0f32; 22050], vec![0f32; 22050]);
        def.render(&mut db);
        alt.render(&mut ab);
        assert_ne!(
            db, ab,
            "sampled default must differ from the modeled alt bank"
        );
    }
}
