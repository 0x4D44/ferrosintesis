//! The render engine: walks the event list in 64-sample blocks, spawns and
//! mixes voices per channel, applies each channel's strip (program-aware
//! distortion insert, CC74 brightness filter + CC71 resonance, CC7 volume,
//! CC11 expression, CC1 mod-wheel vibrato / Leslie ramp, CC64 sustain and
//! CC66 sostenuto pedals, CC67 una corda, CC5/CC65 portamento, CC70 choir
//! vowel morph, channel aftertouch, RPN 0/1 bend range and fine tune,
//! CC10 pan with a Haas micro-delay for real width, CC91 reverb send) and
//! three global buses: a hall reverb, a stereo chorus (ensembles breathe),
//! and a tempo-derived ping-pong echo (the classic delayed-lead sound).
//! Every v0.7 controller is opt-in ("authored"): a file that never sends it
//! renders bit-identically to v0.6.

use crate::dsp::{key_freq, Biquad, DelayLine, OnePole, Rng};
use crate::midi::{EvKind, Song};
use crate::reverb::{CathedralReverb, Reverb};
use crate::{drums, voices};
use std::f32::consts::{FRAC_PI_2, TAU};

const BLOCK: usize = 64;

// CC1 mod wheel. Melodic sustained voices (plucks, bowed, winds) get an
// engine-level vibrato LFO per channel, multiplied on top of the channel's
// pitch-bend; organs morph their tremulant toward Leslie-fast instead.
const VIB_RATE_HZ: f32 = 5.3; // vibrato LFO rate
const VIB_DEPTH_CENTS: f32 = 35.0; // pitch depth at mod = 1
const ST_CC1_VIB_DEPTH: f32 = 0.012; // alt-bank strings: full-wheel per-layer section vibrato depth
const LESLIE_SLOW_HZ: f32 = 0.9; // tremulant rate the rotor brakes down to (chorale)
const LESLIE_FAST_HZ: f32 = 6.8; // tremulant rate the rotor spins up to
const LESLIE_INERTIA_S: f32 = 1.5; // rotor time constant (spin-up/down)
const LESLIE_DEPTH_ADD: f32 = 0.10; // extra tremulant depth at mod = 1

// The cathedral room runs hotter than the shared hall: the biggest single
// "presence" lever for the organ is the wet return, and scaling it here (rather
// than the global `--wet`) leaves every other instrument's hall untouched and
// keeps CC91 semantics intact. Bounded above by the low-chord headroom test.
const CATHEDRAL_WET_SCALE: f32 = 1.30;

// CC11 swell → cathedral-organ reed-rasp drive. Thresholded, not linear: a chorus
// reed is on/off with registration and the snarl belongs to the top of the
// dynamic. In (squared) expression terms the knee 0.25 lands at CC11 ≈ 64 (a
// half-open swell stays smooth), and γ > 1 concentrates the snarl's growth in the
// last quarter of pedal travel — how a swell crescendo feels. Opt-in: unauthored
// CC11 ⇒ drive 0 ⇒ byte-identical.
const ORGAN_SWELL_KNEE: f32 = 0.25;
const ORGAN_SWELL_GAMMA: f32 = 1.6;

// CC74 brightness: a resonant 2-pole lowpass on the channel's dry path,
// ahead of the bus sends, so the wah colours the reverb and echo too.
// 0..127 maps exponentially WAH_MIN_HZ..WAH_MAX_HZ; 127 is a true bypass.
const WAH_MIN_HZ: f32 = 300.0;
const WAH_MAX_HZ: f32 = 12000.0;
const WAH_Q: f32 = 1.4;
const WAH_SLEW_S: f32 = 0.02; // cutoff smoothing so a CC74 LFO doesn't zipper

// CC71 resonance: Q of the CC74 filter, 0..127 exponential. A channel that
// never authors CC71 stays at WAH_Q exactly.
const RES_MIN_Q: f32 = 0.7;
const RES_MAX_Q: f32 = 8.0;

// CC5 portamento time: 0..127 maps exponentially PORTA_MIN_S..PORTA_MAX_S.
const PORTA_MIN_S: f32 = 0.005;
const PORTA_MAX_S: f32 = 0.6;

// D10: fixed drum-room send level (ch 9 only, un-highpassed so the kick
// keeps its body; the room is pre-hall).
const ROOM_SEND: f32 = 0.35;

// D10e: overall drum-bus level relative to the band. The +6 dB "drum forward"
// lift (was 2.0) is REMOVED — a global kit lift is a MIXING decision baked into
// the instrument, and it dominated most mixes. A scalar -18 LUFS normalize is
// balance-transparent (it multiplies every channel equally), so the fader passes
// straight through as RELATIVE drums-vs-band level; the old comment's "+6 nominal
// -> ~+3 audible via limiter absorption" was an ear-estimate under a backwards
// model (the limiter only clamps transients above the ceiling, not integrated
// loudness). The synth now presents the kit level-matched to the band (1.0),
// consistent with the SC-55 reference; an album that genuinely wants drums forward
// authors that as ch-10 CC7 in its own mix. Kept as a tunable constant rather than
// deleted so the drums-vs-band point can be re-seated by ear.
// See wrk_docs/2026.07.20 - HLD - instrument balance oracle + drum-forward recalibration.md.
const DRUM_FORWARD: f32 = 1.0;

// Channel aftertouch (0xDn): "crescendo inside a held note" — pressure adds
// vibrato depth and gain on the sustained melodic families.
const AT_VIB_RATE_HZ: f32 = 5.0;
const AT_VIB_CENTS: f32 = 25.0; // pitch depth at full pressure
const AT_GAIN_DB: f32 = 2.5; // gain lift at full pressure
const BAGPIPE_DRONE_KEY: u8 = u8::MAX;
/// Chanter silence (with no drone-control hold) after which the latched
/// bagpipe drone is released — the bag emptying at the end of the tune. Long
/// enough to bridge musical rests and articulation gaps, short enough that
/// the drone dies inside a normal render tail.
const BAGPIPE_DRONE_HANG_S: f32 = 1.0;

/// Melodic sustained families that take the engine-level CC1 vibrato:
/// plucks (except palm-mute 28), bowed strings, SawStack strings/choir, harmonica,
/// winds, synth leads. Drums, Leslie organs, pads and modal instruments (piano,
/// bells) are left alone.
fn vibrato_family(program: u8) -> bool {
    // guitars (no palm-mute 28), basses, bowed strings, harp, SawStack strings/choir,
    // brass (56-63), reeds (64-71/109/111), winds, leads, banjo, fiddle. Orchestra hit (55)
    // is excluded — a one-shot stab does not vibrato (symmetric with timpani).
    matches!(
        program,
        22 | 24..=27 | 29..=46 | 48..=54 | 56..=71 | 72..=79 | 80..=87 | 104..=107
            | 109..=111
    )
}

fn organ_leslie_family(program: u8, bank: u8) -> bool {
    // 16..=18 always. GM19 is the Leslie drawbar on the default bank and the
    // CC0=1 legacy bank; the CC0=2 bank is the restored CathedralOrgan pipe
    // model, which has its own wind-chest motion and takes no Leslie ramp.
    matches!(program, 16..=18) || (program == 19 && bank != 2)
}

fn cathedral_organ(program: u8, bank: u8) -> bool {
    // GM19 on the CC0=2 alt bank: the restored cathedral pipe organ (wind-chest
    // breathing + CC11 reed-rasp swell + its own dedicated stone-room reverb).
    // Default-bank and CC0=1 GM19 are the Leslie drawbar and are NOT cathedral.
    program == 19 && bank == 2
}

fn cc1_pitch_vibrato_target(program: u8, alt: bool) -> bool {
    vibrato_family(program) && !(alt && matches!(program, 52..=54 | 22))
}

/// Families that answer channel aftertouch: the vibrato families plus
/// Modal, organ, string/choir SawStack and pad programs. Drums stay out:
/// pressure is not a pitched-body gesture for percussion.
fn aftertouch_family(program: u8) -> bool {
    vibrato_family(program)
        || matches!(
            program,
            0..=23 | 47 | 48..=54 | 80..=95 | 96 | 98 | 100 | 102 | 108
        )
}

fn vowel_family(program: u8) -> bool {
    matches!(program, 52..=54 | 91)
}

// CC70 vowel morph anchors for the choir programs (52-54). Bass/baritone
// formant values; "mm" keeps the closed hum the v0.6 onset morph starts from,
// with the upper bands shaded down the way closed lips actually mute them.
/// The interpolated vowel a voice's formant bank is retuned to: three band
/// centre frequencies (Hz), their Qs, and their linear gains.
type Vowel = ([f32; 3], [f32; 3], [f32; 3]);
/// One CC70 morph anchor: the CC value it sits at (0..127) paired with the
/// `Vowel` (band frequencies, Qs, gains) the choir speaks at that value.
type VowelAnchor = (f32, [f32; 3], [f32; 3], [f32; 3]);
const VOWEL_ANCHORS: [VowelAnchor; 4] = [
    (
        0.0,
        [500.0, 1400.0, 2400.0],
        [12.0, 10.0, 9.0],
        [1.0, 0.30, 0.10],
    ), // mm
    (
        42.0,
        [350.0, 600.0, 2400.0],
        [10.0, 12.0, 9.0],
        [1.0, 0.35, 0.10],
    ), // oo
    (
        84.0,
        [600.0, 1040.0, 2250.0],
        [9.0, 10.0, 9.0],
        [1.0, 0.60, 0.35],
    ), // ah
    (
        127.0,
        [400.0, 1900.0, 2600.0],
        [9.0, 10.0, 9.0],
        [1.0, 0.85, 0.50],
    ), // eh
];

/// Interpolate the vowel tables at a (smoothed) CC70 position.
fn vowel_at(pos: f32) -> Vowel {
    let p = pos.clamp(0.0, 127.0);
    let hi = VOWEL_ANCHORS
        .iter()
        .position(|a| a.0 >= p)
        .unwrap_or(VOWEL_ANCHORS.len() - 1);
    if hi == 0 {
        let a = &VOWEL_ANCHORS[0];
        return (a.1, a.2, a.3);
    }
    let (a, b) = (&VOWEL_ANCHORS[hi - 1], &VOWEL_ANCHORS[hi]);
    let t = (p - a.0) / (b.0 - a.0);
    let mut f = [0f32; 3];
    let mut q = [0f32; 3];
    let mut g = [0f32; 3];
    for i in 0..3 {
        f[i] = a.1[i] + (b.1[i] - a.1[i]) * t;
        q[i] = a.2[i] + (b.2[i] - a.2[i]) * t;
        g[i] = a.3[i] + (b.3[i] - a.3[i]) * t;
    }
    (f, q, g)
}

/// The GM programs that get the overdrive/cabinet channel insert — the
/// single source of truth for the Prog handler and oracle 36.
pub(crate) fn needs_drive(prog: u8) -> bool {
    matches!(prog, 29 | 30)
}

/// Driven guitar strings can sustain indefinitely while physically/pedal held.
/// Eight voices preserve two power chords plus lead/doubling while bounding the
/// per-channel CPU and level wall from pathological stacked MIDI.
const DRIVEN_GUITAR_VOICE_LIMIT: usize = 8;

/// D9: static per-piece kit placement (drummer's perspective) in pan space
/// [0, 1], 0.5 = centre. Kick/snare stay centred; hats sit left; the toms
/// sweep across; ride/bell and china/crash-2 sit right, crash-1 left.
/// Authored CC10 OFFSETS this table (centre leaves it verbatim).
pub(crate) fn drum_pan(key: u8) -> f32 {
    match key {
        42 | 44 | 46 => 0.33,
        41 => 0.55,
        43 | 45 => 0.62,
        47 | 48 => 0.42,
        50 => 0.32,
        51 | 53 | 59 => 0.70,
        49 | 55 => 0.25,
        52 | 57 => 0.75,
        _ => 0.5,
    }
}

/// D10d: per-key kit-balance trim. The kit voicing — the sampled `DRUM_LEVEL`
/// table and the modeled kit it is level-matched to — inherited a balance where,
/// measured on the Hey Jude reference, the hi-hats sit ~19 dB under the kick/snare
/// while the crash/ride sit only ~2 dB under them. That reads as "the hats vanish
/// and the cymbals are too loud." This trim corrects it for BOTH kits at once
/// (applied in the drum mix, so it scales the sampled and modeled voices equally
/// and preserves their level parity): the hi-hats come up ~+11 dB, the loud accent
/// cymbals come down, and the backbone (kick/snare/toms/stick/aux) stays put.
fn kit_balance(key: u8) -> f32 {
    match key {
        42 | 44 | 46 => 4.5,                // hi-hats: ~19 dB too quiet -> up ~+13 dB
        38 | 40 => 1.8, // snare: well forward (it sat behind the toms; +2.6 -> ~+5 dB)
        41 | 43 | 45 | 47 | 48 | 50 => 1.6, // toms: forward ~+4 dB
        49 => 0.5,      // crash 1 (hard-left, used rhythmically): pulled down further
        57 => 0.68,     // crash 2 (right): stays an accent
        51 | 59 => 0.55, // ride: too loud and too sustained
        53 => 0.72,     // ride bell
        52 => 0.68,     // china
        55 => 0.68,     // splash
        _ => 1.0,       // kick/side-stick/tamb/cowbell: unchanged
    }
}

/// The 5-biquad speaker-cabinet model (HLD G1): low-end resonance, a mid
/// scoop, a presence peak, and a two-pole-pair cliff that both voices the
/// amp and acts as the decimation filter for the 2× nonlinear path. Built
/// at the 2× rate; shared with the oracle-3 response test.
pub(crate) fn cab_biquads(sr2: f32) -> [Biquad; 5] {
    [
        Biquad::peak(100.0, 1.2, 4.0, sr2),
        Biquad::peak(500.0, 1.0, -3.0, sr2),
        Biquad::peak(2600.0, 1.5, 5.0, sr2),
        // elements CAB_CLIFF.. are the anti-alias decimation cliff and must
        // stay LAST in Drive::chain (MicroCab inserts before them)
        Biquad::lowpass(4000.0, 0.9, sr2),
        Biquad::lowpass(3800.0, 0.8, sr2),
    ]
}

/// Index of the first lowpass-cliff biquad in [`cab_biquads`]'s array — the
/// named seam `Drive::chain` splits at so the fine-structure FIR can never
/// silently drift to the wrong side of the anti-alias cliff (review A3).
pub(crate) const CAB_CLIFF: usize = 3;

/// MicroCab taps: (delay ms, gain), numerically optimized against the full
/// constraint set at once (250 k-candidate search, journal 2026.07.18):
/// ≥ 6 magnitude alternations of ≥ 1.5 dB across 900–3600 Hz, total swing
/// 6.2 dB (musical, not gutting), 3→6 kHz tilt −0.07 dB (the decimation
/// cliff's margin is untouched), ≤ 1.6 dB span below 800 Hz (review I8's
/// real concern — the drive voicing EQs and the asymmetry-oracle bins stay
/// clean; delays beyond I8's draft 0.55 ms cap are fine BECAUSE this
/// low-band bound is enforced directly), |H| peak 1.52 (≫ alias margin).
/// Hand-picking taps kept failing one bound or another — a delay tap
/// ripples at every frequency equally, so only joint optimization finds
/// the corner of the constraint box.
const MICRO_CAB_TAPS: [(f32, f32); 5] = [
    (0.360, 0.110),
    (0.593, 0.110),
    (0.625, -0.157),
    (0.783, 0.115),
    (0.895, -0.238),
];

/// Ripple depth for the SUSTAINING driven lead (the CC0 alt bank,
/// `voices::DRIVE_LEAD`) as a fraction of `MICRO_CAB_TAPS`.
///
/// `MicroCab` normalizes its ripple to unity on the 900–3600 Hz band
/// AVERAGE, which makes it level-neutral for broadband material — a chugging
/// rhythm guitar spreads its energy across the band and averages the comb
/// out. That assumption fails for a lead that HOLDS ONE PITCH for seconds:
/// it samples the ripple at exactly one frequency and keeps whatever it
/// finds there. With only 5 taps at 0.36–0.90 ms the comb is coarse (ripple
/// periods 1.1–2.8 kHz), so a held tone can park squarely in a null:
/// measured on Three-Sixty-One's finale, C6 lost 2.08 dB and E6 1.03 dB at
/// the fundamental while their 2nd/3rd harmonics gained 2.8 dB — the note
/// went thin, not merely quiet, and Arthur heard the lead recede
/// (2026.07.20 journal).
///
/// So the depth is a property of the BANK, not of the amp: the default bank
/// keeps the full ripple Arthur approved for rhythm work (depth 1.0 —
/// bit-identical), and the sustaining lead gets a quarter of it. At 0.25 the
/// worst deviation any held pitch can suffer anywhere in the band falls
/// 3.39 dB → 0.85 dB (C6 −0.47, E6 −0.24) while the ripple stays measurably
/// present at 1.54 dB swing, so the lead still speaks through a cabinet
/// rather than a DI. The macro cab shape (`cab_biquads`) is untouched either
/// way — this scales only the fine structure on top of it.
pub(crate) const MICRO_CAB_LEAD_DEPTH: f32 = 0.25;

/// Cabinet fine structure (guitar-realism HLD §5): the dense magnitude
/// ripple a real cab's cone breakup and edge reflections put on top of the
/// smooth biquad response — a sparse FIR (direct + 5 taps, `MICRO_CAB_TAPS`)
/// normalized so the 900–3600 Hz band-average magnitude is unity (the
/// ripple recolors the band without moving its level, review D9). Runs
/// inside the cab section BEFORE the two lowpass cliff biquads, so the
/// anti-alias cliff stays the last element of the 2× nonlinear path
/// (review I5/D6 resolution). This deliberately revives the guitar-v2
/// decision-log "ripple comb (deferred)" — v2 parked it as polish; this is
/// that polish (review S10).
///
/// `depth` scales the tap gains before normalization (see
/// [`MICRO_CAB_LEAD_DEPTH`]); the band-average stays unity at every depth,
/// so depth changes the ripple's DEVIATION, never the band's level.
pub(crate) struct MicroCab {
    buf: Vec<f32>,
    pos: usize,
    taps: [(usize, f32); 5],
    direct: f32,
}

impl MicroCab {
    /// `depth` 1.0 is the full cabinet ripple (the default driven bank);
    /// [`MICRO_CAB_LEAD_DEPTH`] is the sustaining lead's shallower one.
    pub(crate) fn with_depth(sr2: f32, depth: f32) -> Self {
        let taps_s: Vec<(usize, f32)> = MICRO_CAB_TAPS
            .iter()
            .map(|&(ms, g)| (((ms * 1e-3 * sr2).round() as usize).max(1), g * depth))
            .collect();
        // band-average |H| over 900–3600 Hz (closed form for the sparse FIR)
        let mut avg = 0.0;
        let grid: Vec<f32> = (0..28).map(|k| 900.0 + k as f32 * 100.0).collect();
        for &f in &grid {
            let w = std::f32::consts::TAU * f / sr2;
            let (mut re, mut im) = (1.0f32, 0.0f32);
            for &(d, g) in &taps_s {
                re += g * (w * d as f32).cos();
                im -= g * (w * d as f32).sin();
            }
            avg += (re * re + im * im).sqrt();
        }
        avg /= grid.len() as f32;
        let norm = 1.0 / avg.max(1e-6);
        let max_d = taps_s.iter().map(|&(d, _)| d).max().unwrap_or(1);
        let mut taps = [(0usize, 0f32); 5];
        for (o, &(d, g)) in taps.iter_mut().zip(&taps_s) {
            *o = (d, g * norm);
        }
        MicroCab {
            buf: vec![0.0; (max_d + 1).next_power_of_two()],
            pos: 0,
            taps,
            direct: norm,
        }
    }

    #[inline]
    pub(crate) fn process(&mut self, x: f32) -> f32 {
        let mask = self.buf.len() - 1;
        self.buf[self.pos] = x;
        let mut y = self.direct * x;
        for &(d, g) in &self.taps {
            y += g * self.buf[(self.pos + self.buf.len() - d) & mask];
        }
        self.pos = (self.pos + 1) & mask;
        y
    }
}

/// Overdrive/distortion channel insert for GM programs 29/30 (guitar v2,
/// HLD §3.C): program-keyed pre-voicing → stage-1 biased (asymmetric) tanh
/// → interstage tilt EQ → stage-2 tanh → DC blocker → speaker cabinet, the
/// whole nonlinear chain at 2× rate. The cab's cliff replaces the old
/// box-average decimator, so the shaper fizz dies in the cabinet instead
/// of aliasing down.
///
/// The chain is STATIC: the loudest instant (the pick) drives the tanh
/// stages hardest, which is exactly how a real amp clips. The old
/// "power-supply sag" gain (`sag_target / env`, slewing UP to 4× as the
/// note decayed) had the temporal polarity backwards — it faked sustain by
/// blooming the tail — and was deleted (voice-quality overhaul §2.6);
/// held-note sustain is the string's e-bow sustainer (`DRIVE.sustain`).
struct Drive {
    program: u8,
    /// Whether this insert was built for the CC0 alt bank (the sustaining
    /// `DRIVE_LEAD` voicing). Stored so the strip can tell a stale insert
    /// from a current one when the bank changes mid-song; it selects the
    /// `MicroCab` depth at construction and is DSP-irrelevant thereafter.
    alt: bool,
    pre: Biquad,
    voice: Biquad,
    g1: f32,
    bias: f32,
    tilt: Biquad,
    g2: f32,
    post: f32,
    dcb: Biquad,
    cab: [Biquad; 5],
    micro: MicroCab,
    prev: f32,
}

impl Drive {
    /// `alt` = the channel's CC0 bank is non-zero, i.e. the strip is playing
    /// the sustaining `DRIVE_LEAD` voicing rather than the decaying default.
    /// It selects the cabinet fine-structure depth only (see
    /// [`MICRO_CAB_LEAD_DEPTH`]); gain staging and voicing EQ are unchanged,
    /// so the default bank stays bit-identical.
    fn new(program: u8, alt: bool, sr: f32) -> Self {
        let sr2 = sr * 2.0;
        // 30 = distortion (scooped chug), 29 = overdrive (mid-push lead).
        // Two gentler stages replace v1's single hot tanh.
        //
        // Round 2 ("clean, dark sustain"): g1 raised 2.5→9.0 / 4.5→8.0 and
        // the DRIVE preset now feeds the insert ~7 dB hotter (voices.rs
        // DRIVE: amp 0.7→1.5, sustain 0.5→0.7, bright 4800→9000), so the
        // e-bow-held tail keeps audible harmonic edge
        // (driven_sustain_stays_distorted). Measured ceiling: the hold's
        // clipping depth is structurally capped by the §2.6 sag-catcher
        // (o_attack_sustained_plucks_no_late_bloom) — a deeply squared hold
        // out-RMSes the broadband attack window (crest-factor inversion,
        // measured at DRIVE.amp ≥ 2.0), so the hold sits at the tanh knee,
        // not in hard clip. `post` re-matched end-to-end (o_attack_held_note
        // _probe early window, key 45 vel 100: 29 0.0368, 30 0.0423 — the
        // pre-round-2 levels).
        let (g1, g2, post, bias) = if program == 30 {
            (8.0, 3.0, 0.145, 0.9)
        } else {
            // bias raised with g1 (0.45→0.9): at the hotter swing the old
            // bias point washed out of the curvature and the even-harmonic
            // warmth vanished (drive_asymmetry_and_dc's 2nd-vs-3rd floor)
            (9.0, 2.0, 0.12, 0.9)
        };
        let (voice, tilt) = if program == 30 {
            (
                Biquad::peak(650.0, 0.9, -5.0, sr2),
                // deepen the scoop between the stages: stage 2 re-saturates
                // the mids the voicing pulled, so pull again where it counts
                Biquad::peak(700.0, 0.9, -4.0, sr2),
            )
        } else {
            (
                Biquad::peak(800.0, 0.8, 4.0, sr2),
                // upper-mid push into stage 2: the singing lead bite
                Biquad::peak(1200.0, 0.8, 2.0, sr2),
            )
        };
        Drive::from_stages(program, alt, sr2, voice, g1, bias, tilt, g2, post)
    }

    /// Shared field construction for both the program-gated `new` and the XG
    /// `amp_sim` insert: the pre-HPF, the post-shaper DC blocker, the 5-biquad
    /// cabinet, and the interpolation state are identical; only the voicing EQ
    /// and gain staging differ. `program` is stored but DSP-irrelevant
    /// (`chain`/`process` never read it).
    #[allow(clippy::too_many_arguments)]
    fn from_stages(
        program: u8,
        alt: bool,
        sr2: f32,
        voice: Biquad,
        g1: f32,
        bias: f32,
        tilt: Biquad,
        g2: f32,
        post: f32,
    ) -> Self {
        Drive {
            program,
            alt,
            pre: Biquad::highpass(90.0, 0.7, sr2),
            voice,
            g1,
            bias,
            tilt,
            g2,
            post,
            // a real DC blocker after the shapers: the biased tanh produces
            // large signal-dependent DC that the cab's unity-at-DC biquads
            // cannot remove (V4/CORR-1)
            dcb: Biquad::highpass(20.0, 0.7, sr2),
            cab: cab_biquads(sr2),
            micro: MicroCab::with_depth(sr2, if alt { MICRO_CAB_LEAD_DEPTH } else { 1.0 }),
            prev: 0.0,
        }
    }

    /// XG Amp Simulator (Variation) as a per-part insert: the same amp+cabinet
    /// DSP as `new`, with the two gain stages scaled by the XG Drive parameter
    /// (0..127). Voiced as an overdriven-guitar amp (the reference file targets
    /// the electric-guitar channel); the cabinet is the shared 5-biquad
    /// decimation filter — exactly ONE cabinet, since the insert REPLACES the
    /// program drive rather than stacking after it. `post` trims the hotter
    /// settings so the wet stage stays near unity for the apply-site dry/wet
    /// blend; Arthur's ear is the final tuning (oracles check direction).
    fn amp_sim(sr: f32, drive_0_127: u8) -> Self {
        let sr2 = sr * 2.0;
        let d = drive_0_127 as f32 / 127.0;
        // Quadratic drive curve: nearly clean at low settings, hot at full, so
        // the knob is expressive across its range (a linear map saturates the
        // first stage too early and Drive barely moves the tone). The file's
        // Drive 24 (d ~= 0.19) sits in gentle overdrive.
        let g1 = 1.0 + d * d * 16.0;
        let g2 = 1.5 + d * 1.5;
        let bias = 0.7;
        // more drive compresses harder, so trim output as gain rises to hold a
        // roughly constant wet level for the blend.
        let post = 0.28 / (1.0 + d * 1.5);
        let voice = Biquad::peak(800.0, 0.8, 4.0, sr2);
        let tilt = Biquad::peak(1200.0, 0.8, 2.0, sr2);
        // The XG insert is an amp simulator, not a bank voicing: full ripple.
        Drive::from_stages(0, false, sr2, voice, g1, bias, tilt, g2, post)
    }

    #[inline]
    fn chain(&mut self, x: f32) -> f32 {
        let v = self.voice.process(self.pre.process(x));
        // stage 1: biased tanh referenced to its bias point — the curvature
        // asymmetry (even harmonics) stays, but silence maps to exactly zero
        let s1 = (v * self.g1 + self.bias).tanh() - self.bias.tanh();
        // interstage tilt, then the gentler symmetric second stage
        let s2 = (self.tilt.process(s1) * self.g2).tanh();
        let mut y = self.dcb.process(s2);
        // voicing biquads, then the fine structure, then the lowpass cliff
        // LAST (it is the decimation filter — review I5/D6)
        for c in &mut self.cab[..CAB_CLIFF] {
            y = c.process(y);
        }
        y = self.micro.process(y);
        for c in &mut self.cab[CAB_CLIFF..] {
            y = c.process(y);
        }
        y
    }

    fn process(&mut self, buf: &mut [f32]) {
        for x in buf.iter_mut() {
            // 2x oversampling via midpoint interpolation; the cab's steep
            // lowpass cliff is the decimation filter, so we keep the
            // sample-aligned output instead of box-averaging
            let mid = 0.5 * (self.prev + *x);
            self.prev = *x;
            let _ = self.chain(mid);
            *x = self.chain(*x) * self.post;
        }
    }

    /// Test-only: neutralise the pre-voicing EQ (oracle 5's gain-matched
    /// reference — a 0 dB peak is an identity biquad).
    #[cfg(test)]
    fn with_flat_voice(mut self) -> Self {
        self.voice = Biquad::peak(800.0, 0.8, 0.0, 88_200.0);
        self
    }
}

/// Per-program bus sends (chorus, echo). Reverb stays CC91-authored.
fn fx_profile(program: u8, bank: u8) -> (f32, f32) {
    match program {
        19 if bank == 2 => (0.0, 0.0), // cathedral organ (CC0=2): the case/room supplies width
        16..=23 => (0.20, 0.0),        // legacy organs/free reeds: gentle ensemble
        24 | 25 => (0.12, 0.08),       // acoustic guitars: a touch of both
        26..=31 => (0.10, 0.30),       // electric guitars: the delayed-lead sound
        42 | 43 => (0.0, 0.06), // solo cello/contrabass: dry & forward, no ensemble chorus to smear the single-voice identity, only a trace of slap
        40..=45 | 110 => (0.10, 0.10), // fiddle + other bowed strings (40 == 110 kept for the gm110 oracle)
        46 => (0.15, 0.0),             // harp
        48..=51 => (0.35, 0.0),        // string ensembles
        52..=54 => (0.30, 0.0),        // choir
        56..=60 => (0.0, 0.0),         // solo brass: hall (CC91) is the space, no ensemble fake
        61..=63 => (0.25, 0.0),        // brass section / synth brass: section-width chorus
        64..=67 => (0.06, 0.10),       // saxes: lead voice, a touch of width and slap echo
        109 => (0.06, 0.0),            // bagpipe: small width, no slap echo on the drone
        111 => (0.04, 0.08),           // shanai: dry forward reed with a trace of slap
        72..=79 => (0.0, 0.22),        // flute / whistle
        80..=87 => (0.15, 0.25),       // synth leads: focused, with the delayed-lead echo
        88..=95 => (0.45, 0.0),        // pads
        // Synth FX (Stage 3): split per preset. 98 (crystal) keeps its pre-split
        // values — part of the 7-album freeze. 102 (echoes) gets a LOW bus-echo
        // send: its repeats are INTERNAL to the voice, so a bus echo would double
        // them. The rest are gut-feel (chorus shimmer + a little bus echo).
        96 => (0.30, 0.20),    // rain: droplets are internal; light shimmer
        97 => (0.35, 0.25),    // soundtrack: wide swell
        98 => (0.30, 0.35),    // crystal: FROZEN — unchanged from the pre-split arm
        99 => (0.30, 0.25),    // atmosphere: wash
        100 => (0.30, 0.30),   // brightness: shimmer as it blooms
        101 => (0.25, 0.30),   // goblins: a touch less width, more echo scatter
        102 => (0.30, 0.05),   // echoes: internal repeats — starve the bus echo
        103 => (0.20, 0.30),   // sci-fi: focused zap, echoed
        8..=10 => (0.0, 0.15), // celesta / glockenspiel / music box
        14 => (0.0, 0.08),     // tubular bells
        15 => (0.10, 0.0),     // hammered dulcimer: sub-beat width, no echo
        _ => (0.0, 0.0),
    }
}

/// SC-55-referenced per-program loudness trim (dB), applied at the melodic
/// channel strip. `0.0` = untouched.
///
/// ferrosintesis has no per-instrument loudness normalisation — each voice
/// carries its own hand-tuned gain, and only the whole *mix* is normalised to
/// −18 LUFS. That leaves the raw instrument-to-instrument balance uneven (e.g.
/// solo strings/brass and flutes run hot; string sections and choir run quiet).
/// This table nudges the sustained families toward the balance a Roland
/// SC-55mkII produces for the same GM programs, measured at equal note/velocity
/// (see `wrk_docs/2026.07.17 - CR - instrument level audit + SC-55 trim.md`).
///
/// It is deliberately CONSERVATIVE: sustained voices only (whole-note RMS is a
/// fair loudness proxy there), 0.70× the measured delta, clamped to ±6 dB, with
/// a 1 dB dead-band. Struck/plucked/percussive voices (piano, guitar, mallets,
/// drums) and noise/FX are left at 0.0 — their apparent "deficit" is usually a
/// faster decay envelope, not a level error, so trimming them would misfire.
/// (An M-CAL v2 pass — an envelope-guarded, multi-window metric — will calibrate
/// the percussive families; see `wrk_docs/2026.07.21 - HLD - M-CAL v2 envelope-
/// guarded metric.md`. The 21-Jul max-momentary derivation was rejected: it is a
/// temporal-envelope artifact for short/percussive voices, not a level reading.)
///
/// GM6 harpsichord is the ONE documented plucked exception (+6 dB): the audit
/// used the fair EARLY-window RMS (0–150 ms, immune to the decay-artifact trap)
/// and still measured it ~10 dB under the SC-55 balance against the piano anchor;
/// its too-fast decay is fixed independently in the `HARPSICHORD` preset, so the
/// "deficit is only a decay artifact" objection does not apply here. The trim is
/// the right lever because it lifts the sampled quill onset and the modeled body
/// UNIFORMLY post-wrap (raising the model `amp` alone would shift the attack/
/// sustain balance). See the 2026.07.18 holds audit.
///
/// Timbre-neutral: it scales the dry voice and all its FX sends together (the
/// strip gain `g` feeds both), preserving each channel's wet/dry ratio.
#[rustfmt::skip] // keep the 8-per-row GM grid aligned for readability
pub(crate) const PROGRAM_TRIM_DB: [f32; 128] = [
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  6.0,  0.0, //   0-7   Piano (6 harpsichord +6dB; rest untouched)
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, //   8-15  ChromPerc  (untouched)
    -4.5, -3.0, -1.5, -6.0, -3.0, -5.0, -1.0, -4.5, //  16-23  Organ
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, //  24-31  Guitar     (untouched)
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, //  32-39  Bass       (untouched)
    -4.0, -4.0, -3.5, -6.0, -4.0,  0.0,  0.0,  0.0, //  40-47  Strings (bowed; pizz/harp/timpani=0)
     5.5,  1.5,  6.0,  5.0,  2.5,  6.0,  5.0,  0.0, //  48-55  Ensemble (sections/choir; orch-hit=0)
    -6.0, -6.0, -6.0, -2.0, -3.0, -2.0,  0.0,  5.0, //  56-63  Brass
     0.0, -2.5, -3.0, -3.0,  2.0,  1.5,  0.0,  0.0, //  64-71  Reed
    -4.0, -4.0, -2.0, -5.0, -6.0, -6.0,  0.0,  0.0, //  72-79  Pipe
    -4.0,  0.0,  0.0,  0.0, -2.0,  5.5,  1.0,  1.0, //  80-87  SynthLead
     4.0,  0.0,  2.0,  5.0,  3.0, -5.0,  0.0,  0.0, //  88-95  SynthPad
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, //  96-103 SynthFX    (untouched)
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, // 104-111 Ethnic     (untouched)
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, // 112-119 Percussive (untouched)
     0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, // 120-127 SoundFX    (untouched)
];

/// Linear gain for the SC-55-referenced per-program loudness trim (see
/// `PROGRAM_TRIM_DB`). Returns exactly `1.0` for untouched programs.
#[inline]
pub(crate) fn program_trim_lin(program: u8) -> f32 {
    let db = PROGRAM_TRIM_DB[program as usize];
    if db == 0.0 {
        1.0
    } else {
        10f32.powf(db / 20.0)
    }
}

/// Stereo chorus bus: one modulated delay line, quadrature taps L/R.
struct Chorus {
    dl: DelayLine,
    phase: f32,
    rate: f32,
    base: f32,
    depth: f32,
    sr: f32,
}

impl Chorus {
    fn new(sr: f32) -> Self {
        Chorus {
            dl: DelayLine::new((0.040 * sr) as usize),
            phase: 0.0,
            rate: 0.35,
            base: 0.018 * sr,
            depth: 0.005 * sr,
            sr,
        }
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        for i in 0..send.len() {
            self.dl.push(send[i]);
            self.phase += TAU * self.rate / self.sr;
            if self.phase > TAU {
                self.phase -= TAU;
            }
            let tl = self.dl.tap(self.base + self.depth * self.phase.sin());
            let tr = self
                .dl
                .tap(self.base + self.depth * (self.phase + FRAC_PI_2).sin());
            l[i] += tl * 0.55;
            r[i] += tr * 0.55;
        }
    }

    /// Re-tune the LFO in place (the XG Chorus Type mapping). `base_s + depth_s`
    /// must fit inside the 40 ms delay line so the modulated tap never reads
    /// past the buffer (asserted). Rate is the LFO frequency in Hz. Delay-line
    /// length and phase are unchanged, so reconfiguring to the current values is
    /// an exact no-op.
    fn reconfigure(&mut self, rate_hz: f32, base_s: f32, depth_s: f32) {
        assert!(
            base_s + depth_s <= 0.040,
            "chorus sweep {base_s}+{depth_s}s exceeds the 40 ms line"
        );
        self.rate = rate_hz;
        self.base = base_s * self.sr;
        self.depth = depth_s * self.sr;
    }
}

/// Ping-pong echo bus: repeats alternate sides, darkening as they fade.
struct PingPong {
    left: DelayLine,
    right: DelayLine,
    time: f32,
    feedback: f32,
    lp_l: OnePole,
    lp_r: OnePole,
}

impl PingPong {
    fn new(sr: f32, time_s: f32) -> Self {
        let samples = (time_s * sr).max(64.0);
        PingPong {
            left: DelayLine::new(samples as usize + 4),
            right: DelayLine::new(samples as usize + 4),
            time: samples,
            feedback: 0.34,
            lp_l: OnePole::lowpass(3200.0, sr),
            lp_r: OnePole::lowpass(3200.0, sr),
        }
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        // Per-block denormal flush (MM-BUG-KILN-00027).
        self.lp_l.flush();
        self.lp_r.flush();
        for i in 0..send.len() {
            let out_l = self.left.tap(self.time);
            let out_r = self.right.tap(self.time);
            self.left.push(crate::dsp::flush_denormal(
                send[i] + self.lp_r.process(out_r) * self.feedback,
            ));
            self.right.push(crate::dsp::flush_denormal(
                self.lp_l.process(out_l) * self.feedback,
            ));
            l[i] += out_l * 0.8;
            r[i] += out_r * 0.8;
        }
    }
}

/// Sympathetic resonance: lightly-damped comb resonators fed by a send and
/// returned quietly. Parameterized (G5/V4): the piano instance rings one
/// comb per pitch class C3..B3; the guitar instance rings the six open
/// strings of acoustic guitars (prog 24|25 only).
struct Sympathetic {
    combs: Vec<(DelayLine, f32, OnePole)>,
    hp: Biquad,
    feedback: f32,
    input: f32,
    ret: f32,
}

impl Sympathetic {
    fn new(
        sr: f32,
        freqs: &[f32],
        damp_hz: f32,
        feedback: f32,
        hp_hz: f32,
        input: f32,
        ret: f32,
    ) -> Self {
        let combs = freqs
            .iter()
            .map(|&f| {
                let d = sr / f;
                (
                    DelayLine::new(d as usize + 4),
                    d,
                    OnePole::lowpass(damp_hz, sr),
                )
            })
            .collect();
        Sympathetic {
            combs,
            hp: Biquad::highpass(hp_hz, 0.7, sr),
            feedback,
            input,
            ret,
        }
    }

    /// The piano's undamped strings (the original v0.5 instance).
    fn piano(sr: f32) -> Self {
        let freqs: Vec<f32> = (0..12)
            .map(|k| 130.81 * 2f32.powf(k as f32 / 12.0))
            .collect();
        Self::new(sr, &freqs, 2600.0, 0.85, 170.0, 0.05, 0.55)
    }

    /// The acoustic guitar's open strings E2 A2 D3 G3 B3 E4 (GTR-3/KS-6).
    fn guitar(sr: f32) -> Self {
        Self::new(
            sr,
            &[82.41, 110.0, 146.83, 196.0, 246.94, 329.63],
            3400.0,
            0.85,
            120.0,
            0.03,
            0.30,
        )
    }

    /// The sitar's tarab strings (GM 104, v0.16): thirteen sympathetic
    /// strings under the frets. Tuned chromatically C4..C5 — the same
    /// raga-agnostic trick as the piano instance — with a brighter damper
    /// and a higher feedback than the guitar bus, so the halo shimmers and
    /// briefly outlasts the plucked string (per-trip 0.955 keeps every comb
    /// a strict contraction).
    fn sitar(sr: f32) -> Self {
        let freqs: Vec<f32> = (0..13)
            .map(|k| 261.63 * 2f32.powf(k as f32 / 12.0))
            .collect();
        let damp_hz = 5200.0;
        let mut s = Self::new(sr, &freqs, damp_hz, 0.955, 200.0, 0.035, 0.35);
        // At feedback 0.955 each comb's resonance is only a few Hz wide, so
        // the in-loop damper's phase delay (plus the write→read sample)
        // detunes the peak right off the played pitch — compensate the
        // delay exactly as KsLoop::delay_for does. The wider piano/guitar
        // instances (fb 0.85) stay untouched and bit-identical.
        let a = 1.0 - (-2.0 * std::f32::consts::PI * (damp_hz / sr).min(0.49)).exp();
        let b = 1.0 - a;
        for ((_, d, _), &f) in s.combs.iter_mut().zip(freqs.iter()) {
            let w = 2.0 * std::f32::consts::PI * f / sr;
            let d1p = ((b * w.sin()) / (1.0 - b * w.cos())).atan() / w;
            *d = (sr / f - d1p - 1.0).max(2.0);
        }
        s
    }

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
        // Per-block denormal flush (MM-BUG-KILN-00027): the damp one-poles and
        // the input HP otherwise park below the floor when the send goes quiet.
        self.hp.flush();
        for (_, _, damp) in &mut self.combs {
            damp.flush();
        }
        for i in 0..send.len() {
            let x = self.hp.process(send[i]) * self.input;
            let mut sum = 0.0;
            for (dl, d, damp) in &mut self.combs {
                let mut y = dl.tap(*d);
                if y.abs() < 1e-20 {
                    y = 0.0; // denormal flush
                }
                dl.push(x + damp.process(y) * self.feedback);
                sum += y;
            }
            let w = sum * self.ret;
            l[i] += w;
            r[i] += w;
        }
    }
}

/// Master-bus glue: a slow 2:1 compressor (a dB or two of gentle movement)
/// and a whisper of saturation, so the mix couples like a record instead of
/// arithmetic.
struct BusGlue {
    env: f32,
    gain: f32,
    atk: f32,
    rel: f32,
    thr: f32,
    shelf_l: Biquad,
    shelf_r: Biquad,
}

impl BusGlue {
    fn new(sr: f32) -> Self {
        BusGlue {
            env: 0.0,
            gain: 1.0,
            atk: 1.0 - (-1.0 / (0.015 * sr)).exp(),
            rel: 1.0 - (-1.0 / (0.250 * sr)).exp(),
            thr: 0.32,
            shelf_l: Biquad::peak(95.0, 0.7, 1.5, sr),
            shelf_r: Biquad::peak(95.0, 0.7, 1.5, sr),
        }
    }

    fn process(&mut self, l: &mut [f32], r: &mut [f32]) {
        // Per-block denormal flush (MM-BUG-KILN-00027).
        self.shelf_l.flush();
        self.shelf_r.flush();
        for i in 0..l.len() {
            let xl = self.shelf_l.process(l[i]);
            let xr = self.shelf_r.process(r[i]);
            let level = xl.abs().max(xr.abs());
            let k = if level > self.env { self.atk } else { self.rel };
            self.env = crate::dsp::flush_denormal(self.env + k * (level - self.env));
            let target = if self.env > self.thr {
                (self.thr / self.env).sqrt() // 2:1 above threshold
            } else {
                1.0
            };
            let kg = if target < self.gain {
                self.atk
            } else {
                self.rel
            };
            self.gain += kg * (target - self.gain);
            // gentle tape-ish saturation on the glued signal
            let gl = xl * self.gain;
            let gr = xr * self.gain;
            l[i] = gl + 0.12 * ((gl * 1.4).tanh() / 1.4 - gl);
            r[i] = gr + 0.12 * ((gr * 1.4).tanh() / 1.4 - gr);
        }
    }
}

struct Strip {
    program: u8,
    kit: drums::Kit,    // channel-10 kit version; V3 by default
    alt_bank: bool,     // CC0 != 0 selects the alt orchestral voicings (altbank::make)
    alt_bank_value: u8, // raw CC0 value: 0 default, 1 legacy alt, 2 GM19 cathedral organ
    xg_drum: bool,      // CC0 == 127: XG drum-kit bank — route this channel to the drum path
    gs_drum: bool,      // GS "Use for Rhythm Part" SysEx — same routing, separate origin
    // (a GS rhythm part still sends CC0=0, so it cannot share xg_drum)
    volume: f32, // CC7 as amplitude (squared curve); slewed current value
    pan: f32,    // 0..1; slewed current value
    // CC7 volume / CC10 pan controller slew (prime-on-first-block). The handler
    // sets only `*_target` + `*_authored`; the per-block mix loop snaps the current
    // value to the target on the first block after authoring (reproducing MIDI
    // last-write-wins for a same-tick burst), then one-pole slews toward the target
    // thereafter — so a foreign GM fade or pan sweep ramps instead of stepping at
    // block boundaries. A channel that never authors CC7/CC10 keeps its default.
    volume_target: f32,
    volume_authored: bool,
    volume_primed: bool,
    pan_target: f32,
    pan_authored: bool,
    pan_primed: bool,
    bend: f32,     // channel pitch multiplier: wheel × range × fine-tune
    legato: bool,  // CC68: new notes slur into the ringing voice
    sustain: bool, // CC64: NoteOffs are held until the pedal lifts
    // v0.7 authored controllers (all inert until first touched)
    bend_wheel: f32, // last wheel position in ±2-normalised semitones
    bend_range: f32, // RPN 0: bend range in semitones (GM default 2)
    fine: f32,       // RPN 1: fine tune as a frequency multiplier
    rpn_msb: u8,     // CC101/CC100 select; 127/127 = null
    rpn_lsb: u8,
    data_msb: u8, // last CC6, so CC38 can refine it
    porta_on: bool,
    porta_time: f32,        // CC5 glide time in seconds
    last_freq: Option<f32>, // most recent NoteOn pitch (portamento origin)
    // CC32 bank-select LSB: selects an XG variation voice via make_variation.
    // Persists across Reset All Controllers (bank select is not a RAC controller).
    bank_lsb: u8,
    // CC84 portamento control: a pending one-shot glide source key, consumed by
    // the next NoteOn (glides regardless of CC65 porta-on). Cleared by RAC.
    porta_control: Option<u8>,
    bagpipe_drone_holds: u8, // low GM109 notes currently holding the synthetic drone
    bagpipe_drone_live: bool, // a channel drone is sounding — gates the latch tick
    bagpipe_drone_hang: u32, // blocks of chanter silence so far (drone release countdown)
    soft: bool,              // CC67 una corda
    sost_down: bool,         // CC66 sostenuto pedal position
    vowel_authored: bool,    // CC70 selects a static vowel on choir programs
    vowel_target: f32,       // CC70 value 0..127
    vowel_cur: f32,          // slewed per block
    at_authored: bool,       // channel aftertouch seen on this channel
    at_target: f32,          // pressure 0..1, smoothed like CC11
    at_cur: f32,
    at_phase: f32, // aftertouch vibrato LFO phase
    at_gain: f32,  // pressure gain lift (1.0 = none)
    vib_mult: f32, // this block's CC1 vibrato factor, for composition
    res: f32,      // CC71 resonance: current filter Q, slewed
    res_target: f32,
    expr_target: f32,
    expr: f32,
    // CC11 has been authored at least once (opt-in / authored-channel
    // invariant: `expr` defaults to 1.0).
    expr_authored: bool,
    // CC2 breath: a second expression lane (squared, smoothed like CC11)
    // aimed at sustained-excitation voices. NEUTRAL (1.0) until first
    // authored — deliberately NOT the GM power-on default of 0, which would
    // silence every channel that never sends CC2 (authored-channel invariant).
    breath_authored: bool,
    breath_target: f32,
    breath: f32,
    mod_target: f32, // CC1, smoothed into mod_cur like expression
    mod_cur: f32,
    mod_engaged: bool,  // mod machinery active (stays on through spin-down)
    mod_authored: bool, // CC1 has been sent at least once on this channel
    vib_phase: f32,
    leslie_rate: f32, // current tremulant rate/depth, slewed with inertia
    leslie_depth: f32,
    reverb_send: f32,
    chorus_send: f32,
    chorus_authored: bool,
    delay_send: f32,
    delay_authored: bool,
    organ_wind: f32,
    organ_trem_phase: f32,
    drive: Option<Drive>,
    // XG Variation Amp-Simulator insertion: an amp/cab insert that REPLACES the
    // program `drive` on this channel, paired with its dry/wet weight (0..1).
    // Set ONLY by XG effect SysEx (`resolve_variation`); program_change /
    // needs_drive / rederive_program_defaults never touch it — so an album,
    // which sends no SysEx, never installs one and stays byte-identical.
    xg_insert: Option<(Drive, f32)>,
    wah: Option<Biquad>, // CC74 brightness filter; None = true bypass
    wah_legacy: Option<Biquad>,
    wah_cathedral: Option<Biquad>,
    // second wah instance for channel 9's stereo drum pair (D9 strip
    // parity: an authored ch-9 CC74/71 keeps filtering the whole kit)
    wah_r: Option<Biquad>,
    cutoff: f32, // current wah cutoff Hz, slewed toward cutoff_target
    cutoff_target: f32,
    haas: DelayLine,
    haas_delay: f32, // samples of far-side delay; 0 disables
}

impl Strip {
    fn new(sr: f32) -> Self {
        Strip {
            program: 0,
            kit: drums::Kit::V3,
            alt_bank: false,
            alt_bank_value: 0,
            xg_drum: false,
            gs_drum: false,
            volume: (100.0f32 / 127.0).powi(2),
            pan: 0.5,
            // Targets equal the current defaults, so the slew is a bit-exact no-op
            // until the first CC7/CC10 is authored (D6: the SAME expression, not a
            // rounded literal).
            volume_target: (100.0f32 / 127.0).powi(2),
            volume_authored: false,
            volume_primed: false,
            pan_target: 0.5,
            pan_authored: false,
            pan_primed: false,
            bend: 1.0,
            legato: false,
            sustain: false,
            bend_wheel: 0.0,
            bend_range: 2.0,
            fine: 1.0,
            rpn_msb: 127,
            rpn_lsb: 127,
            data_msb: 0,
            porta_on: false,
            porta_time: PORTA_MIN_S,
            last_freq: None,
            bank_lsb: 0,
            porta_control: None,
            bagpipe_drone_holds: 0,
            bagpipe_drone_live: false,
            bagpipe_drone_hang: 0,
            soft: false,
            sost_down: false,
            vowel_authored: false,
            vowel_target: 0.0,
            vowel_cur: 0.0,
            at_authored: false,
            at_target: 0.0,
            at_cur: 0.0,
            at_phase: 0.0,
            at_gain: 1.0,
            vib_mult: 1.0,
            res: WAH_Q,
            res_target: WAH_Q,
            expr_target: 1.0,
            expr: 1.0,
            expr_authored: false,
            breath_authored: false,
            breath_target: 1.0,
            breath: 1.0,
            mod_target: 0.0,
            mod_cur: 0.0,
            mod_engaged: false,
            mod_authored: false,
            vib_phase: 0.0,
            leslie_rate: 0.0,
            leslie_depth: 0.0,
            reverb_send: 0.3,
            chorus_send: 0.0,
            chorus_authored: false,
            delay_send: 0.0,
            delay_authored: false,
            organ_wind: 0.0,
            organ_trem_phase: 0.0,
            drive: None,
            xg_insert: None,
            wah: None,
            wah_legacy: None,
            wah_cathedral: None,
            wah_r: None,
            cutoff: WAH_MAX_HZ,
            cutoff_target: WAH_MAX_HZ,
            haas: DelayLine::new((0.006 * sr) as usize + 4),
            haas_delay: 0.0,
        }
    }
}

/// How to render a [`Song`](crate::offline::Song).
///
/// Start from [`Options::default`] and refine with the `with_*` builders. The fields
/// are private on purpose: that is what lets a future minor release add a render knob,
/// or rename one, without breaking your code. Read them back with the accessors.
///
/// ```
/// use ferrosintesis::offline::Options;
///
/// let opt = Options::default()
///     .with_sample_rate(48_000.0)
///     .with_echo(0.0); // no echo bus
///
/// assert_eq!(opt.sample_rate(), 48_000.0);
/// assert_eq!(opt.echo(), 0.0);
/// ```
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct Options {
    pub(crate) sr: f32,
    pub(crate) wet: f32,
    pub(crate) tail: f32,
    pub(crate) delay_s: f32,
    pub(crate) samples: bool,
    pub(crate) solo: u16,
}

impl Default for Options {
    fn default() -> Self {
        Self {
            sr: 44_100.0,
            wet: 0.32,
            tail: 6.0,
            delay_s: 0.375,
            samples: true,
            solo: 0xFFFF,
        }
    }
}

impl Options {
    /// Set the output sample rate in Hz. Default 44100.
    pub fn with_sample_rate(mut self, sr: f32) -> Self {
        self.sr = sr;
        self
    }

    /// Set the reverb send, 0.0 (dry) to 1.0. Default 0.32.
    pub fn with_reverb(mut self, wet: f32) -> Self {
        self.wet = wet;
        self
    }

    /// Set how many seconds of reverb tail are rendered past the last note-off.
    /// Default 6.0.
    pub fn with_tail(mut self, tail: f32) -> Self {
        self.tail = tail;
        self
    }

    /// Enable or disable the embedded PCM attack-sample layer. Default true. Has no
    /// effect when the crate is built without the `embedded-samples` feature.
    pub fn with_samples(mut self, samples: bool) -> Self {
        self.samples = samples;
        self
    }

    /// Set the echo time in seconds. Pass 0.0 to disable the echo bus. Default 0.375.
    pub fn with_echo(mut self, delay_s: f32) -> Self {
        self.delay_s = delay_s;
        self
    }

    /// Set the channel bitmask: bit *n* enables MIDI channel *n*. Notes on masked-out
    /// channels are dropped, which is how you render a single-instrument stem. The
    /// tempo map is unaffected, so a stem lines up with the full mix. Default `0xFFFF`.
    pub fn with_solo(mut self, solo: u16) -> Self {
        self.solo = solo;
        self
    }

    /// The output sample rate in Hz.
    pub fn sample_rate(&self) -> f32 {
        self.sr
    }

    /// The reverb send, 0.0 (dry) to 1.0.
    pub fn reverb(&self) -> f32 {
        self.wet
    }

    /// Seconds of reverb tail rendered past the last note-off.
    pub fn tail(&self) -> f32 {
        self.tail
    }

    /// The echo time in seconds; 0.0 means the echo bus is disabled.
    pub fn echo(&self) -> f32 {
        self.delay_s
    }

    /// Whether the embedded PCM attack-sample layer is enabled. Always renders as
    /// disabled when the crate is built without the `embedded-samples` feature.
    pub fn samples(&self) -> bool {
        self.samples
    }

    /// The channel bitmask: bit *n* enables MIDI channel *n*.
    pub fn solo(&self) -> u16 {
        self.solo
    }
}

/// What a render cost, returned alongside the audio.
///
/// `#[non_exhaustive]`: new counters may be added in a minor release.
#[derive(Debug, Clone, Copy, PartialEq)]
#[non_exhaustive]
pub struct Stats {
    /// Total voices allocated over the whole render.
    pub voices_spawned: u64,
    /// Largest absolute sample value in the returned buffer, before any normalization.
    pub peak: f32,
    /// The most voices alive at once.
    pub max_polyphony: usize,
    #[cfg(test)]
    pub(crate) cathedral_return_peak: f32,
}

impl Default for Stats {
    fn default() -> Self {
        Self {
            voices_spawned: 0,
            peak: 0.0,
            max_polyphony: 0,
            #[cfg(test)]
            cathedral_return_peak: 0.0,
        }
    }
}

/// A progress report, passed to the callback given to
/// [`render_with_progress`](crate::offline::render_with_progress).
///
/// `#[non_exhaustive]`: new fields may be added in a minor release.
#[derive(Debug, Clone, Copy, PartialEq)]
#[non_exhaustive]
pub struct Progress {
    /// Seconds of audio rendered so far.
    pub rendered_seconds: f64,
    /// Total seconds this render will produce, including the reverb tail.
    pub total_seconds: f64,
    /// Voices alive at this instant.
    pub active_voices: usize,
}

impl Progress {
    /// Fraction of the render completed, in `0.0..=1.0`.
    pub fn fraction(&self) -> f64 {
        if self.total_seconds <= 0.0 {
            return 1.0;
        }
        (self.rendered_seconds / self.total_seconds).clamp(0.0, 1.0)
    }
}

struct Active {
    ch: u8,
    key: u8,
    program: u8,     // spawn-time program: program changes affect future notes
    held: bool,      // NoteOff arrived while the sustain pedal was down
    sost: bool,      // CC66: was ringing when the sostenuto pedal went down
    sost_held: bool, // NoteOff deferred by the sostenuto pedal
    // CC5/CC65 portamento: (semitone offset from the target, per-block slew)
    glide: Option<(f32, f32)>,
    alt: bool, // spawn-time bank: this voice is an alt-bank voicing (per-voice CC1 routing)
    alt_bank_value: u8, // spawn-time raw CC0 value (2 = GM19 cathedral organ routing)
    // spawn-time routing: this voice goes to the drum path (ch9, or an XG-drum
    // channel that had CC0==127). Frozen at spawn like `alt`, so a mid-note CC0
    // change only affects later notes. Gates both mix passes.
    is_drum: bool,
    // Poly (key) aftertouch (0xAn): a per-note pressure lane mirroring the
    // channel lane (same smoothing, LFO rate and depths). Channel and key
    // pressure COMPOSE: the dB gain lifts add and the vibrato factors
    // multiply — matching how CC7 x CC11 x channel-AT gain already stack in
    // the strip. All defaults are exact no-ops (multiply by 1.0), so a note
    // that never receives 0xAn renders bit-identically.
    poly_authored: bool,
    poly_target: f32, // pressure 0..1
    poly_cur: f32,    // smoothed like the channel at_cur
    poly_phase: f32,  // per-note pressure-vibrato LFO phase
    poly_mult: f32,   // this block's pitch factor (1.0 = none)
    poly_gain: f32,   // per-note gain lift (1.0 = none)
    voice: Box<dyn voices::Voice>,
}

#[derive(Clone, Copy)]
pub(crate) struct CoreOptions {
    pub sr: f32,
    pub wet: f32,
    pub delay_s: f32,
    pub samples: bool,
    pub solo: u16,
    pub gtr_symp_on: bool,
    pub drum_room_on: bool,
    pub sitar_symp_on: bool,
}

impl CoreOptions {
    fn from_options(
        opt: &Options,
        gtr_symp_on: bool,
        drum_room_on: bool,
        sitar_symp_on: bool,
    ) -> Self {
        Self {
            sr: opt.sr,
            wet: opt.wet,
            delay_s: opt.delay_s,
            samples: opt.samples,
            solo: opt.solo,
            gtr_symp_on,
            drum_room_on,
            sitar_symp_on,
        }
    }
}

/// The shared hall's default tuning (Freeverb comb feedback / damping). Single
/// source of truth for `EngineCore::new` and the XG System On reset, so the two
/// can never drift apart.
const DEFAULT_HALL_ROOM: f32 = 0.86;
const DEFAULT_HALL_DAMP: f32 = 0.35;

/// XG Reverb Type Hall 1 = type word (0x01, 0x00). Re-tuned (Arthur's "faithful"
/// steer) as a larger, brighter concert hall than the engine default: more comb
/// feedback (longer RT) and less damping (brighter tail). Applied only when a
/// file requests it; oracles check DIRECTION, not XG-exact numbers.
const HALL1_TYPE: [u8; 2] = [0x01, 0x00];
const HALL1_ROOM: f32 = 0.92;
const HALL1_DAMP: f32 = 0.22;

/// XG Chorus Type Chorus 1 = type word (0x41, 0x00). Faithful moderate chorus:
/// a touch faster and deeper than the engine default. Params are (LFO rate Hz,
/// base delay s, sweep depth s); `base + depth` stays inside the 40 ms line.
const CHORUS1_TYPE: [u8; 2] = [0x41, 0x00];
const CHORUS1_RATE: f32 = 0.8;
const CHORUS1_BASE_S: f32 = 0.018;
const CHORUS1_DEPTH_S: f32 = 0.006;

/// The engine chorus defaults — MIRROR `Chorus::new` (guarded by the
/// reconfigure-to-defaults-is-a-no-op test). Single source for the System On
/// reset.
const DEFAULT_CHORUS_RATE: f32 = 0.35;
const DEFAULT_CHORUS_BASE_S: f32 = 0.018;
const DEFAULT_CHORUS_DEPTH_S: f32 = 0.005;

/// XG Variation Type MSB for the Amp Simulator (the only variation type we
/// model). The LSB (0x11 in the reference file) is undocumented in the MU100/
/// MU128 map and ignored — treated as the basic Amp Sim.
const AMP_SIM_TYPE_MSB: u8 = 0x4B;
/// XG Variation Connection: 0 = INSERTION (a per-part insert), 1 = SYSTEM (a
/// global send bus — a non-goal; SYSTEM installs no insert).
const XG_VAR_INSERTION: u8 = 0x00;

/// XG effect-block state (Effect1): the pending variation-insertion config,
/// mutated ONLY by XG effect SysEx (`EvKind::XgEffectParam` / `XgReset`). No
/// album sends any SysEx, so every field's default leaves the render
/// bit-identical: `var_part = 127` (OFF) installs no insert, and the reverb /
/// chorus recognizers only fire on the exact Hall 1 / Chorus 1 type words. The
/// reverb/chorus *type* changes act on the live `Reverb`/`Chorus` in place, so
/// no state is duplicated here — only the variation, which is resolved into a
/// per-strip `xg_insert` after each parameter update.
#[derive(Clone, Copy)]
struct XgEffects {
    var_type_msb: u8,   // Variation Type MSB (Amp Simulator = 0x4B)
    var_type_lsb: u8,   // Variation Type LSB (0x11 undocumented -> basic Amp Sim)
    var_connection: u8, // 0 = INSERTION, 1 = SYSTEM
    var_part: u8,       // target Part 0..63; 127 = OFF (no insert)
    var_drive: u8,      // Variation Param1 = Drive (0..127)
    var_drywet: u8,     // Variation Param10 = Dry/Wet (1..127; 127 = full wet)
}

impl XgEffects {
    fn new() -> Self {
        // Defaults chosen so the resolve is a no-op: part OFF => no insert.
        XgEffects {
            var_type_msb: 0,
            var_type_lsb: 0,
            var_connection: 0,
            var_part: 127,
            var_drive: 0,
            var_drywet: 127,
        }
    }
}

pub(crate) struct EngineCore {
    opt: CoreOptions,
    strips: Vec<Strip>,
    active: Vec<Active>,
    reverb: Reverb,
    cathedral: CathedralReverb,
    rev_hp: Biquad,
    chorus: Chorus,
    echo: Option<PingPong>,
    symp: Sympathetic,
    gtr_symp: Sympathetic,
    sitar_symp: Sympathetic,
    // set the first time a strip sounds program 104; until then the tarab
    // bus is never processed, so sitar-less renders stay bit-identical
    sitar_seen: bool,
    drum_room: Reverb,
    glue: BusGlue,
    stats: Stats,
    // Deterministic voice-seed position. Usually advances with voices_spawned,
    // but GM System On resets synthesis state while public Stats stay cumulative.
    voice_seed_index: u64,
    ch_buf: Vec<[f32; BLOCK]>,
    legacy_buf: Vec<[f32; BLOCK]>,
    cathedral_buf: Vec<[f32; BLOCK]>,
    scratch: [f32; BLOCK],
    send_rev: [f32; BLOCK],
    send_cathedral: [f32; BLOCK],
    send_cho: [f32; BLOCK],
    send_del: [f32; BLOCK],
    send_sym: [f32; BLOCK],
    send_sym_gtr: [f32; BLOCK],
    send_sym_sitar: [f32; BLOCK],
    send_room: [f32; BLOCK],
    drum_l: [f32; BLOCK],
    drum_r: [f32; BLOCK],
    mix_l: [f32; BLOCK],
    mix_r: [f32; BLOCK],
    expr_smooth: f32,
    leslie_k: f32,
    wah_smooth: f32,
    // Per-key channel-10 hit counter (wraps): the sampled cymbals cycle their
    // round-robin takes from it, so consecutive hits of the SAME key step
    // 0→1→2→3→0… deterministically no matter what other drums interleave.
    // (A seed-modulo pick would immediate-repeat ~1/rr of the time — the
    // machine-gun artifact.)
    drum_rr: [u8; 128],
    // TREM1 (tremolo restrike): the running sample clock (advanced per
    // rendered block; events are block-quantised, so this is exactly their
    // resolution) and the per-(channel, key) time of the previous NoteOn —
    // together they give the same-key inter-onset interval that gates the
    // tremolo-restrike path in note_on.
    now: u64,
    key_on_at: Vec<[u64; 128]>,
    // XG effect-block state (variation insertion + the reverb/chorus type
    // recognizers). Defaults are inert; only XG SysEx mutates it.
    xg: XgEffects,
}

/// TREM1: a same-key NoteOn this close (in seconds) to the previous one on
/// the same channel is a tremolo stroke — re-excite the still-ringing
/// plucked voice instead of spawning a fresh one from silence. 100 ms
/// (10 strokes/s) separates genuine tremolo (mandolin/guitar tremolo is
/// 10–16 strokes/s, IOI ≤ 100 ms) from intentional same-note picking
/// (5–7 notes/s, IOI ≥ 143 ms, 43% above the gate), which must keep its
/// full per-note articulation.
const TREM_IOI_MAX_S: f32 = 0.10;

impl EngineCore {
    pub(crate) fn new(opt: CoreOptions) -> Self {
        let opt = CoreOptions {
            samples: opt.samples && crate::embedded_samples_available(),
            ..opt
        };
        let sr = opt.sr;
        Self {
            opt,
            strips: (0..16).map(|_| Strip::new(sr)).collect(),
            active: Vec::new(),
            reverb: Reverb::new(sr, DEFAULT_HALL_ROOM, DEFAULT_HALL_DAMP, opt.wet),
            cathedral: CathedralReverb::new(sr, opt.wet * CATHEDRAL_WET_SCALE),
            rev_hp: Biquad::highpass(150.0, 0.7, sr),
            chorus: Chorus::new(sr),
            echo: (opt.delay_s > 0.0).then(|| PingPong::new(sr, opt.delay_s)),
            symp: Sympathetic::piano(sr),
            gtr_symp: Sympathetic::guitar(sr),
            sitar_symp: Sympathetic::sitar(sr),
            sitar_seen: false,
            drum_room: Reverb::with_predelay(sr, 0.42, 0.55, opt.wet * 0.9, 0.003),
            glue: BusGlue::new(sr),
            stats: Stats::default(),
            voice_seed_index: 0,
            ch_buf: vec![[0f32; BLOCK]; 16],
            legacy_buf: vec![[0f32; BLOCK]; 16],
            cathedral_buf: vec![[0f32; BLOCK]; 16],
            scratch: [0f32; BLOCK],
            send_rev: [0f32; BLOCK],
            send_cathedral: [0f32; BLOCK],
            send_cho: [0f32; BLOCK],
            send_del: [0f32; BLOCK],
            send_sym: [0f32; BLOCK],
            send_sym_gtr: [0f32; BLOCK],
            send_sym_sitar: [0f32; BLOCK],
            send_room: [0f32; BLOCK],
            drum_l: [0f32; BLOCK],
            drum_r: [0f32; BLOCK],
            mix_l: [0f32; BLOCK],
            mix_r: [0f32; BLOCK],
            expr_smooth: 1.0 - (-(BLOCK as f32) / (0.03 * sr)).exp(),
            leslie_k: 1.0 - (-(BLOCK as f32) / (LESLIE_INERTIA_S * sr)).exp(),
            wah_smooth: 1.0 - (-(BLOCK as f32) / (WAH_SLEW_S * sr)).exp(),
            drum_rr: [0; 128],
            now: 0,
            key_on_at: vec![[u64::MAX; 128]; 16],
            xg: XgEffects::new(),
        }
    }

    pub(crate) fn hard_reset(&mut self) {
        let opt = self.opt;
        *self = Self::new(opt);
    }

    /// Restore fresh GM synthesis/channel state while whole-render diagnostics
    /// remain cumulative for the offline API.
    fn gm_system_on(&mut self) {
        let stats = self.stats;
        self.hard_reset();
        self.stats = stats;
    }

    pub(crate) fn active_voice_count(&self) -> usize {
        self.active.len()
    }

    pub(crate) fn stats(&self) -> Stats {
        self.stats
    }

    fn is_bagpipe_drone(a: &Active, ch: u8) -> bool {
        a.ch == ch && a.program == 109 && a.key == BAGPIPE_DRONE_KEY
    }

    fn ensure_bagpipe_drone(&mut self, ch: u8, key: u8, vel: u8) {
        if self
            .active
            .iter()
            .any(|a| Self::is_bagpipe_drone(a, ch) && !a.voice.released())
        {
            return;
        }
        let seed = 0xBA60 ^ (self.voice_seed_index as u32).wrapping_mul(2654435761);
        // Sampled drone by default; modeled when samples are off or on the CC0
        // alt bank — the same rule the chanter uses in voices::make, so the two
        // paths agree (HLD 2026.07.17 §5). `opt.samples` already folds in
        // embedded-availability.
        let sampled = self.opt.samples && !self.strips[ch as usize].alt_bank;
        let voice: Box<dyn voices::Voice> = if sampled {
            Box::new(voices::bagpipe_drone_sampled(key, self.opt.sr))
        } else {
            Box::new(voices::bagpipe_drone(key, vel, self.opt.sr, seed))
        };
        self.active.push(Active {
            ch,
            key: BAGPIPE_DRONE_KEY,
            program: 109,
            held: false,
            sost: false,
            sost_held: false,
            glide: None,
            alt: false,
            alt_bank_value: 0,
            is_drum: false, // the bagpipe drone is a melodic voice, never a drum
            poly_authored: false,
            poly_target: 0.0,
            poly_cur: 0.0,
            poly_phase: 0.0,
            poly_mult: 1.0,
            poly_gain: 1.0,
            voice,
        });
        self.stats.voices_spawned += 1;
        self.voice_seed_index += 1;
        self.strips[ch as usize].bagpipe_drone_live = true;
        self.strips[ch as usize].bagpipe_drone_hang = 0;
    }

    fn release_bagpipe_drone_if_idle(&mut self, ch: u8) {
        if self.strips[ch as usize].bagpipe_drone_holds > 0 {
            return;
        }
        let has_chant = self.active.iter().any(|a| {
            a.ch == ch && a.program == 109 && a.key != BAGPIPE_DRONE_KEY && !a.voice.released()
        });
        if has_chant {
            return;
        }
        for a in self
            .active
            .iter_mut()
            .filter(|a| Self::is_bagpipe_drone(a, ch) && !a.voice.released())
        {
            a.voice.note_off();
        }
        self.strips[ch as usize].bagpipe_drone_live = false;
        self.strips[ch as usize].bagpipe_drone_hang = 0;
    }

    /// Bagpipe drone latch (block rate). One CONTINUOUS drone per channel: a
    /// chanter gap must not release it — a real set of pipes never stops its
    /// drones between melody notes. The drone releases only after
    /// [`BAGPIPE_DRONE_HANG_S`] of chanter silence with no drone-control
    /// hold: the bag emptying at the end of the tune. Gated on
    /// `bagpipe_drone_live`, so every channel that never spawned a drone
    /// (every non-GM109 channel, hence every existing album) does no work —
    /// and sees no behaviour change — here.
    fn tick_bagpipe_drone_latch(&mut self) {
        let hang_blocks = (BAGPIPE_DRONE_HANG_S * self.opt.sr / BLOCK as f32) as u32;
        for ci in 0..self.strips.len() {
            if !self.strips[ci].bagpipe_drone_live {
                continue;
            }
            let ch = ci as u8;
            let has_drone = self
                .active
                .iter()
                .any(|a| Self::is_bagpipe_drone(a, ch) && !a.voice.released());
            if !has_drone {
                // released/choked elsewhere (CC120/123, authored stop)
                self.strips[ci].bagpipe_drone_live = false;
                self.strips[ci].bagpipe_drone_hang = 0;
                continue;
            }
            let holding = self.strips[ci].bagpipe_drone_holds > 0
                || self.active.iter().any(|a| {
                    a.ch == ch
                        && a.program == 109
                        && a.key != BAGPIPE_DRONE_KEY
                        && !a.voice.released()
                });
            if holding {
                self.strips[ci].bagpipe_drone_hang = 0;
            } else {
                self.strips[ci].bagpipe_drone_hang += 1;
                if self.strips[ci].bagpipe_drone_hang >= hang_blocks {
                    for a in self
                        .active
                        .iter_mut()
                        .filter(|a| Self::is_bagpipe_drone(a, ch) && !a.voice.released())
                    {
                        a.voice.note_off();
                    }
                    self.strips[ci].bagpipe_drone_live = false;
                    self.strips[ci].bagpipe_drone_hang = 0;
                }
            }
        }
    }

    fn make_room_for_driven_guitar(&mut self, ch: u8) {
        let active = self
            .active
            .iter()
            .filter(|a| a.ch == ch && needs_drive(a.program) && !a.voice.released())
            .count();
        let release_count = active.saturating_sub(DRIVEN_GUITAR_VOICE_LIMIT - 1);
        for a in self
            .active
            .iter_mut()
            .filter(|a| a.ch == ch && needs_drive(a.program) && !a.voice.released())
            .take(release_count)
        {
            // Voice stealing is a hard safety boundary: it overrides both pedal
            // deferrals and drops Pluck's e-bow driver through note_off().
            a.held = false;
            a.sost = false;
            a.sost_held = false;
            a.voice.note_off();
        }
    }

    /// Bound total polyphony to `cap`, stealing the oldest/quietest voices until
    /// the count is back at `cap`. Called ONLY from the realtime wrapper
    /// (`live::RealtimeSynth`), which has an audio-callback deadline a dense
    /// stream of un-released voices could otherwise blow. The offline path never
    /// calls this — it has no deadline, so its polyphony stays unbounded and its
    /// renders bit-identical.
    ///
    /// Victim choice: the oldest **released** voice (already decaying, so the
    /// quietest available proxy — the `Voice` trait exposes no level query),
    /// else the oldest voice overall (`active` is push-ordered, so index 0 is
    /// oldest — and the longest-ringing voice is the most decayed). Stealing is
    /// a hard cut, so it can click under genuine overload; that is the safety
    /// valve's cost versus xruns/dropouts.
    pub(crate) fn enforce_voice_cap(&mut self, cap: usize) {
        while self.active.len() > cap {
            let victim = self
                .active
                .iter()
                .position(|a| a.voice.released())
                .unwrap_or(0);
            self.active.remove(victim);
        }
    }

    pub(crate) fn handle_event(&mut self, kind: EvKind) {
        match kind {
            // --solo: muted channels keep their CCs but lose their notes
            EvKind::NoteOn { ch, .. } | EvKind::NoteOff { ch, .. }
                if self.opt.solo & (1u16 << ch) == 0 => {}
            EvKind::NoteOn { ch, key, vel } => self.note_on(ch, key, vel),
            EvKind::NoteOff { ch, key } => self.note_off(ch, key),
            EvKind::Cc { ch, num, val } => self.cc(ch, num, val),
            EvKind::Bend { ch, semis } => self.bend(ch, semis),
            EvKind::Aftertouch { ch, val } => {
                let s = &mut self.strips[ch as usize];
                s.at_target = val as f32 / 127.0;
                s.at_authored = true;
            }
            // Poly (key) aftertouch targets only the ringing voice(s) on that
            // key. Same family gate as the channel lane (drums stay out) —
            // gated at event time so unaffected notes never engage the lane.
            EvKind::PolyAftertouch { ch, key, val } => {
                if ch != 9 {
                    let p = val as f32 / 127.0;
                    for a in self.active.iter_mut().filter(|a| {
                        a.ch == ch
                            && a.key == key
                            && !a.voice.released()
                            && aftertouch_family(a.program)
                    }) {
                        a.poly_target = p;
                        a.poly_authored = true;
                    }
                }
            }
            EvKind::Prog { ch, prog } => self.program_change(ch, prog),
            // GS "Use for Rhythm Part": flag/unflag the channel a drum part. Frozen
            // into each voice's `is_drum` at spawn, so only later notes are affected.
            EvKind::DrumMode { ch, on } => self.strips[ch as usize].gs_drum = on,
            // GS Reset: revert part modes — clear every GS-declared rhythm part (ch9
            // stays drums via the ch==9 rule; the other GS reset effects aren't modeled).
            EvKind::GsReset => {
                for s in &mut self.strips {
                    s.gs_drum = false;
                }
            }
            EvKind::GmReset => self.gm_system_on(),
            // XG effect SysEx (reverb/chorus type + the variation Amp-Sim
            // insertion). Byte-inert for every album (0 send any SysEx): the
            // reverb/chorus recognizers only fire on the exact Hall 1 / Chorus 1
            // words, and the variation resolves to an insert only when a real
            // Part (< 64) is targeted — default part is OFF.
            EvKind::XgReset => self.xg_reset(),
            EvKind::XgEffectParam { addr_lo, data, len } => {
                self.handle_xg_effect_param(addr_lo, data, len)
            }
        }
    }

    /// XG System On resets the XG effect block to defaults only. Unlike GM
    /// System On, it leaves voices and channel state untouched. Reverb/chorus
    /// return to constructor tuning and every variation insert is cleared.
    fn xg_reset(&mut self) {
        self.xg = XgEffects::new();
        // Restore the hall and chorus to their construction tuning (a no-op
        // unless a prior XG type event moved them). Only the shared hall — never
        // the cathedral or the drum room.
        self.reverb
            .reconfigure(DEFAULT_HALL_ROOM, DEFAULT_HALL_DAMP);
        self.chorus.reconfigure(
            DEFAULT_CHORUS_RATE,
            DEFAULT_CHORUS_BASE_S,
            DEFAULT_CHORUS_DEPTH_S,
        );
        self.resolve_variation();
    }

    /// Apply one XG Effect1 parameter. Semantics live here (the parser stays a
    /// dumb decoder, per the GS idiom): reverb/chorus *type* recognizers act on
    /// the live buses in place; variation params accumulate into `self.xg` and
    /// re-resolve the insert idempotently, so the t=0 message order is
    /// irrelevant. Unrecognized offsets (returns at 0x0C/0x2C/0x56, unknown
    /// types) are parsed-and-ignored by design.
    fn handle_xg_effect_param(&mut self, addr_lo: u8, data: [u8; 2], len: u8) {
        // XG data words are 7-bit halves; a value <= 127 lives in the LSB.
        let value14 = ((data[0] as u16) << 7) | (data[1] as u16);
        let value7 = value14.min(127) as u8;
        match addr_lo {
            // Reverb Type: Hall 1 re-tunes the shared hall; every other type
            // keeps the current bus (falls through to `_`). Reverb Return (0x0C)
            // is parsed-and-ignored — returns are unity here.
            0x00 if data == HALL1_TYPE => self.reverb.reconfigure(HALL1_ROOM, HALL1_DAMP),
            // Chorus Type: Chorus 1 re-tunes the chorus LFO; every other type
            // keeps the current bus. Chorus Return (0x2C) parsed-and-ignored.
            0x20 if data == CHORUS1_TYPE => {
                self.chorus
                    .reconfigure(CHORUS1_RATE, CHORUS1_BASE_S, CHORUS1_DEPTH_S)
            }
            // Variation Type (MSB,LSB). Amp Simulator = 0x4B; LSB ignored.
            0x40 => {
                self.xg.var_type_msb = data[0];
                self.xg.var_type_lsb = if len >= 2 { data[1] } else { 0 };
                self.resolve_variation();
            }
            // Variation Param 1 = Drive (0..127).
            0x42 => {
                self.xg.var_drive = value7;
                self.resolve_variation();
            }
            // Variation Param 10 = Dry/Wet (1..127; 127 = full wet).
            0x54 => {
                self.xg.var_drywet = value7;
                self.resolve_variation();
            }
            // Variation Connection: 0 = INSERTION, 1 = SYSTEM.
            0x5A => {
                self.xg.var_connection = data[0];
                self.resolve_variation();
            }
            // Variation Part: 0..63 target part; 127 = OFF.
            0x5B => {
                self.xg.var_part = data[0];
                self.resolve_variation();
            }
            _ => {}
        }
    }

    /// (Re)resolve the variation config into the per-strip insert. Idempotent —
    /// re-run after every parameter update, so the t=0 message order is
    /// irrelevant and a later part/connection/type change moves or removes the
    /// insert. At most one insert exists at a time (XG has a single variation
    /// block): clear every strip, then install on the target iff it is an Amp
    /// Simulator, INSERTION-connected, and aimed at a real part.
    fn resolve_variation(&mut self) {
        for s in &mut self.strips {
            s.xg_insert = None;
        }
        let is_amp_sim = self.xg.var_type_msb == AMP_SIM_TYPE_MSB;
        let insertion = self.xg.var_connection == XG_VAR_INSERTION;
        let part = self.xg.var_part as usize;
        if is_amp_sim && insertion && part < self.strips.len() {
            // Dry/Wet 1..127 -> weight 0..1 (127 = full wet). Blended at the
            // apply site; the Drive itself carries no blend.
            let wet = f32::from(self.xg.var_drywet.saturating_sub(1)) / 126.0;
            let insert = Drive::amp_sim(self.opt.sr, self.xg.var_drive);
            self.strips[part].xg_insert = Some((insert, wet.clamp(0.0, 1.0)));
        }
    }

    fn note_on(&mut self, ch: u8, key: u8, vel: u8) {
        let sr = self.opt.sr;
        let ci = ch as usize;
        let porta_from = self.strips[ci].last_freq;
        let program = self.strips[ci].program;
        let bagpipe_drone_control =
            ch != 9 && program == 109 && key <= voices::BAGPIPE_DRONE_CONTROL_MAX;
        // TREM1: same-key inter-onset interval (in samples) against the
        // previous NoteOn of this (channel, key); the clock updates on EVERY
        // melodic NoteOn so a slow passage keeps re-arming a long IOI.
        let trem_prev = if ch != 9 {
            let prev = self.key_on_at[ci][key as usize];
            self.key_on_at[ci][key as usize] = self.now;
            prev
        } else {
            u64::MAX
        };
        let trem_restrike =
            trem_prev != u64::MAX && (self.now - trem_prev) as f32 <= TREM_IOI_MAX_S * sr;
        if ch != 9 && !bagpipe_drone_control {
            self.strips[ci].last_freq = Some(key_freq(key));
        }
        if bagpipe_drone_control {
            self.strips[ci].bagpipe_drone_holds =
                self.strips[ci].bagpipe_drone_holds.saturating_add(1);
            self.ensure_bagpipe_drone(ch, key, vel);
            return;
        }
        if ch != 9 && program == 109 {
            self.ensure_bagpipe_drone(ch, key, vel);
        }
        if ch != 9 && self.strips[ci].legato {
            let mut ringing = self.active.iter_mut().filter(|a| {
                a.ch == ch
                    && a.key != BAGPIPE_DRONE_KEY
                    && !a.held
                    && !a.sost_held
                    && !a.voice.released()
            });
            if let (Some(a), None) = (ringing.next(), ringing.next()) {
                if a.voice.legato_to(key, vel) {
                    a.key = key;
                    return;
                }
            }
        }
        // TREM1: a fast same-key restrike (IOI ≤ 100 ms — a tremolo stroke)
        // re-picks the still-ringing plucked voice instead of spawning a new
        // one from silence: a fresh spawn is a broadband restart transient,
        // and 10–16 of those per second read as a click train, not a
        // tremolo. Scoped by CAPABILITY: only Pluck implements retrigger()
        // (a plucked string physically IS re-struck while ringing); winds /
        // bowed / reeds / brass return the default false and keep full
        // per-note re-articulation — their legato_to (a slur) must never be
        // conscripted for this. The explicit CC68 legato path above still
        // wins where authored.
        if ch != 9 && trem_restrike {
            let prog = self.strips[ci].program;
            let alt = self.strips[ci].alt_bank;
            if let Some(a) = self
                .active
                .iter_mut()
                .rev()
                .find(|a| a.ch == ch && a.key == key && a.program == prog && a.alt == alt)
            {
                if a.voice.retrigger(key, vel) {
                    // the stroke re-opens the voice's gate: its NoteOff (and
                    // the pedal state at that time) now governs it afresh
                    a.held = false;
                    a.sost_held = false;
                    // consume this stroke's seed slot so every LATER spawn
                    // draws exactly the seed it would have pre-change — the
                    // render diff stays confined to the tremolo itself
                    self.stats.voices_spawned += 1;
                    self.voice_seed_index += 1;
                    return;
                }
            }
        }

        // CC84 (portamento control): consume the pending one-shot glide source
        // now that every early-return path (bagpipe / legato / tremolo restrike)
        // is past and a fresh voice will actually spawn.
        let porta_ctrl = self.strips[ci].porta_control.take();

        let vel = if ch != 9
            && self.strips[ci].soft
            && voices::is_acoustic_piano(self.strips[ci].program)
        {
            ((vel as f32 * 0.75).round() as u8).max(1)
        } else {
            vel
        };

        if ch == 9 && matches!(key, 42 | 44 | 46) {
            for a in self
                .active
                .iter_mut()
                .filter(|a| a.ch == 9 && matches!(a.key, 42 | 44 | 46))
            {
                a.voice.choke();
            }
        }

        if ch != 9 && needs_drive(program) {
            self.make_room_for_driven_guitar(ch);
        }

        let seed = 0x9E37 ^ (self.voice_seed_index as u32).wrapping_mul(2654435761);
        // ch9 is always drums; a channel declared a drum part by XG (CC0==127) or GS
        // ("Use for Rhythm Part" SysEx) joins the drum path. `strips[ci].kit` is
        // `strips[9].kit` when ch==9, so ch9 is unchanged; a declared drum channel uses
        // the default V3 kit (its kit is never reassigned).
        let is_drum = ch == 9 || self.strips[ci].xg_drum || self.strips[ci].gs_drum;
        let voice = if is_drum {
            let rr = self.drum_rr[key as usize];
            self.drum_rr[key as usize] = rr.wrapping_add(1);
            drums::make(
                key,
                vel,
                sr,
                seed,
                self.strips[ci].kit,
                self.opt.samples,
                rr,
            )
        } else {
            let prog = self.strips[ci].program;
            Some(if self.strips[ci].alt_bank {
                crate::altbank::make(
                    prog,
                    self.strips[ci].alt_bank_value,
                    key,
                    vel,
                    sr,
                    seed,
                    self.opt.samples,
                )
            } else {
                // XG bank-LSB variation, else base GM. Same `seed` on both paths,
                // so an undefined (prog, bank_lsb) is bit-identical to base.
                voices::make_variation(
                    prog,
                    self.strips[ci].bank_lsb,
                    key,
                    vel,
                    sr,
                    seed,
                    self.opt.samples,
                )
                .unwrap_or_else(|| voices::make(prog, key, vel, sr, seed, self.opt.samples))
            })
        };

        if let Some(mut voice) = voice {
            let s = &self.strips[ci];
            if s.bend != 1.0 {
                voice.set_pitch(s.bend);
            }
            if s.vowel_authored && vowel_family(s.program) {
                let (f, q, g) = vowel_at(s.vowel_cur);
                voice.set_vowel(f, q, g);
            }
            // BR9: brass opens its timbre with breath (CC11 expression). Seed
            // the new voice at the channel's current pressure so a note born
            // mid-swell starts open, not from silence.
            if matches!(s.program, 56..=63) {
                voice.set_breath((s.expr * s.breath).sqrt().min(1.3), 0.0);
            }
            // RD9 (§2.8.3): reeds open their timbre from the same CC2/CC11
            // lanes — but only once AUTHORED, so a channel that never sends
            // them renders controller-identically to before (§2.8.2; brass
            // predates that invariant and keeps its unconditional seed).
            if matches!(s.program, 64..=71 | 109 | 111)
                && (s.expr_authored || s.breath_authored || s.at_authored)
            {
                voice.set_breath((s.expr * s.breath).sqrt().min(1.0), 0.0);
            }
            // WD9 (§2.8.5.3): the flue arm of the same authored-only seam —
            // a note born mid-swell starts at the channel's pressure.
            if matches!(s.program, 72..=79)
                && (s.expr_authored || s.breath_authored || s.at_authored)
            {
                voice.set_breath((s.expr * s.breath).sqrt().min(1.0), 0.0);
            }
            // Glide source: CC84 (an explicit one-shot source key that glides
            // regardless of CC65 porta-on) takes precedence; otherwise the CC65
            // legato-portamento path from the previous NoteOn pitch.
            let glide = if ch != 9 {
                let src = porta_ctrl
                    .map(key_freq)
                    .or(if s.porta_on { porta_from } else { None });
                src.and_then(|from| {
                    let semis = 12.0 * (from / key_freq(key)).log2();
                    (semis.abs() > 1e-3).then(|| {
                        let k = 1.0 - (-(BLOCK as f32) / (s.porta_time.max(1e-3) * sr)).exp();
                        voice.set_pitch(s.bend * 2f32.powf(semis / 12.0));
                        (semis, k)
                    })
                })
            } else {
                None
            };
            self.active.push(Active {
                ch,
                key,
                program: if is_drum {
                    128
                } else {
                    self.strips[ci].program
                },
                held: false,
                sost: false,
                sost_held: false,
                glide,
                alt: self.strips[ci].alt_bank,
                alt_bank_value: self.strips[ci].alt_bank_value,
                is_drum,
                poly_authored: false,
                poly_target: 0.0,
                poly_cur: 0.0,
                poly_phase: 0.0,
                poly_mult: 1.0,
                poly_gain: 1.0,
                voice,
            });
            self.stats.voices_spawned += 1;
            self.voice_seed_index += 1;
        }
    }

    fn note_off(&mut self, ch: u8, key: u8) {
        let mut drone_stop = false;
        if ch != 9 && key <= voices::BAGPIPE_DRONE_CONTROL_MAX {
            let holds = &mut self.strips[ch as usize].bagpipe_drone_holds;
            drone_stop = *holds == 1; // this NoteOff ends the last authored hold
            *holds = holds.saturating_sub(1);
        }
        if let Some(a) = self
            .active
            .iter_mut()
            .find(|a| a.ch == ch && a.key == key && !a.held && !a.sost_held && !a.voice.released())
        {
            let s = &self.strips[ch as usize];
            if ch != 9 && s.sustain {
                a.held = true;
            } else if ch != 9 && a.sost {
                a.sost_held = true;
            } else {
                a.voice.note_off();
            }
        }
        // Chanter NoteOffs no longer release the channel drone — the old
        // per-note release/re-spawn made the "continuous" drone pump at every
        // note boundary (and re-strike at the NEW note's pitch). The drone
        // latches; only an AUTHORED stop (the last low drone-control note
        // ending) releases it here, and otherwise the block-rate hang timer
        // in `tick_bagpipe_drone_latch` releases it after sustained silence.
        if drone_stop {
            self.release_bagpipe_drone_if_idle(ch);
        }
    }

    fn cc(&mut self, ch: u8, num: u8, val: u8) {
        let sr = self.opt.sr;
        let s = &mut self.strips[ch as usize];
        let v = val as f32 / 127.0;
        match num {
            0 => {
                // XG: bank MSB 127 selects a drum kit on this channel — route it to
                // the drum path, not the alt orchestral bank. Every other value keeps
                // the existing bank behavior (1/2 = alt voicings, 0 = default), so a
                // channel that never sends 127 is byte-identical to before.
                if val == 127 {
                    s.xg_drum = true;
                    s.alt_bank = false;
                    s.alt_bank_value = 0;
                } else {
                    s.xg_drum = false;
                    s.alt_bank = val != 0; // CC0 bank select: non-zero = alt voicings
                    s.alt_bank_value = val; // raw value: 1 = legacy alt, 2 = GM19 cathedral organ
                }
                let (cho, del) = fx_profile(s.program, s.alt_bank_value);
                if !s.chorus_authored {
                    s.chorus_send = cho;
                }
                if !s.delay_authored {
                    s.delay_send = del;
                }
                // The bank selects the driven cabinet's fine-structure depth
                // (MICRO_CAB_LEAD_DEPTH), so a CC0 that arrives AFTER the
                // program change must rebuild the insert — our albums order
                // bank-select first, but a foreign GM file need not.
                if needs_drive(s.program) && s.drive.as_ref().map(|d| d.alt) != Some(s.alt_bank) {
                    s.drive = Some(Drive::new(s.program, s.alt_bank, sr));
                }
            }
            1 => {
                s.mod_target = v;
                s.mod_authored = true;
            }
            2 => {
                // Breath controller: same squared taper as CC11 expression.
                s.breath_target = v * v;
                s.breath_authored = true;
            }
            5 => s.porta_time = PORTA_MIN_S * (PORTA_MAX_S / PORTA_MIN_S).powf(v),
            6 | 38 => {
                if num == 6 {
                    s.data_msb = val;
                }
                let (msb, lsb) = if num == 6 {
                    (val, 0)
                } else {
                    (s.data_msb, val)
                };
                match (s.rpn_msb, s.rpn_lsb) {
                    (0, 0) => s.bend_range = msb.clamp(1, 24) as f32 + lsb as f32 / 100.0,
                    (0, 1) => {
                        let raw = ((msb as i32) << 7 | lsb as i32) - 8192;
                        let cents = raw as f32 * (100.0 / 8192.0);
                        s.fine = 2f32.powf(cents / 1200.0);
                    }
                    _ => {}
                }
                if matches!((s.rpn_msb, s.rpn_lsb), (0, 0) | (0, 1)) {
                    s.bend = 2f32.powf(s.bend_wheel * (s.bend_range * 0.5) / 12.0) * s.fine;
                    let mult = s.bend;
                    for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                        a.voice.set_pitch(mult);
                    }
                }
            }
            // CC7 volume / CC10 pan: author the target only; the per-block mix loop
            // primes-then-slews the current value (and derives haas_delay from the
            // slewed pan). See Strip's controller-slew fields.
            7 => {
                s.volume_target = v * v;
                s.volume_authored = true;
            }
            10 => {
                s.pan_target = v;
                s.pan_authored = true;
            }
            11 => {
                s.expr_target = v * v;
                s.expr_authored = true;
            }
            32 => s.bank_lsb = val, // XG bank-select LSB: selects a variation voice at note-on
            64 => {
                s.sustain = val >= 64;
                if !s.sustain {
                    for a in self.active.iter_mut().filter(|a| a.ch == ch && a.held) {
                        a.held = false;
                        if a.sost {
                            a.sost_held = true;
                        } else {
                            a.voice.note_off();
                        }
                    }
                }
            }
            65 => s.porta_on = val >= 64,
            66 => {
                let down = val >= 64;
                if down && !s.sost_down {
                    for a in self
                        .active
                        .iter_mut()
                        .filter(|a| a.ch == ch && !a.voice.released())
                    {
                        a.sost = true;
                    }
                } else if !down && s.sost_down {
                    for a in self.active.iter_mut().filter(|a| a.ch == ch && a.sost) {
                        a.sost = false;
                        if a.sost_held {
                            a.sost_held = false;
                            if s.sustain {
                                a.held = true;
                            } else {
                                a.voice.note_off();
                            }
                        }
                    }
                }
                s.sost_down = down;
            }
            67 => s.soft = val >= 64,
            68 => s.legato = val >= 64,
            70 => {
                if !s.vowel_authored {
                    s.vowel_cur = val as f32;
                }
                s.vowel_target = val as f32;
                s.vowel_authored = true;
            }
            71 => {
                s.res_target = RES_MIN_Q * (RES_MAX_Q / RES_MIN_Q).powf(v);
                if s.wah.is_none() {
                    s.wah = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    s.wah_legacy = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    s.wah_cathedral = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    if ch == 9 {
                        s.wah_r = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    }
                }
            }
            74 => {
                s.cutoff_target = WAH_MIN_HZ * (WAH_MAX_HZ / WAH_MIN_HZ).powf(v);
                if val < 127 && s.wah.is_none() {
                    s.wah = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    s.wah_legacy = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    s.wah_cathedral = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    if ch == 9 {
                        s.wah_r = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                    }
                }
            }
            84 => s.porta_control = Some(val), // portamento control: one-shot glide source key
            91 => s.reverb_send = v,
            93 => {
                s.chorus_send = v;
                s.chorus_authored = true;
            }
            94 => {
                s.delay_send = v;
                s.delay_authored = true;
            }
            98 | 99 => {
                // NRPN select (CC98 param LSB / CC99 param MSB): ferrosintesis
                // models no NRPN parameter, but an NRPN select MUST still
                // invalidate the RPN latch so a following Data-Entry (CC6/38)
                // cannot write into the previously-selected RPN — e.g. corrupt the
                // RPN 0,0 bend range to 24 semitones on a GS/XG file that used an
                // RPN then an NRPN without an intervening RPN-Null. Park the latch
                // at null (127,127), the same inert state as an RPN-Null
                // (MM-BUG-KILN-00034). This is the guard only, not NRPN support.
                s.rpn_msb = 127;
                s.rpn_lsb = 127;
            }
            100 => s.rpn_lsb = val,
            101 => s.rpn_msb = val,
            120 => self.all_sound_off(ch),
            121 => self.reset_all_controllers(ch),
            123 => self.all_notes_off(ch),
            _ => {}
        }
    }

    fn bend(&mut self, ch: u8, semis: f32) {
        let s = &mut self.strips[ch as usize];
        s.bend_wheel = semis;
        let mult = 2f32.powf(semis * (s.bend_range * 0.5) / 12.0) * s.fine;
        s.bend = mult;
        for a in self.active.iter_mut().filter(|a| a.ch == ch) {
            a.voice.set_pitch(mult);
        }
    }

    fn program_change(&mut self, ch: u8, prog: u8) {
        let s = &mut self.strips[ch as usize];
        s.program = prog;
        // Drums use the best current kit by default. GM/GM2 Program Changes on
        // channel 10 are retained as authored metadata, not a compatibility
        // downgrade path — with three GM2 exceptions, a small "kit bank" ladder:
        //   40 EXACTLY — the GM2 brush kit (v0.12).
        //   24 EXACTLY — the GM2 Electronic slot (v0.18): the modeled "synth
        //                kit", V3 voices with the sampled replacement layer off.
        //   25 EXACTLY — the ORIGINAL kit (v0.19): `V1`, the pre-"kit-v2" drum
        //                voices from before the 9-10 Jul 2026 realism overhaul
        //                (no DR3 open-hat sizzle, original crash). Three-Sixty-One
        //                asks for it by name; V1 is held byte-stable by
        //                `v1_drum_render_signatures_are_stable`.
        // Any other program keeps selecting V3 (the committed showcase demo
        // authors prog 8 and must stay V3).
        if ch == 9 {
            s.kit = match prog {
                40 => drums::Kit::Brush,
                25 => drums::Kit::V1,
                24 => drums::Kit::Synth,
                _ => drums::Kit::V3,
            };
        }
        // Effect send levels are persistent CHANNEL state, not program state: GM /
        // MMA RP-015 keeps CC91/93/94 across a Program Change. So the program's
        // fx_profile is only a DEFAULT — it may fill a send the file never authored,
        // but it must not overwrite one the file did. This mirrors the CC0 bank arm
        // above, which already guards on the same flags; Program Change used to
        // clobber both the value and the authored flag, so a foreign file that set
        // CC93/CC94 and then changed program mid-song lost its sends
        // (MM-BUG-KILN-00033).
        let (cho, del) = if ch == 9 {
            (0.0, 0.0)
        } else {
            fx_profile(prog, s.alt_bank_value)
        };
        if !s.chorus_authored {
            s.chorus_send = cho;
        }
        if !s.delay_authored {
            s.delay_send = del;
        }
        if needs_drive(prog) {
            // rebuild on a program CHANGE too: 29<->30 mid-song choreography
            // is an authored idiom, and the two programs differ in voicing,
            // stage gains and sag target (review C3). The BANK is part of the
            // identity as well — it picks the cabinet fine-structure depth —
            // so a bank change must rebuild just as a program change does.
            let alt = s.alt_bank;
            if s.drive.as_ref().map(|d| (d.program, d.alt)) != Some((prog, alt)) {
                s.drive = Some(Drive::new(prog, alt, self.opt.sr));
            }
        } else {
            s.drive = None;
        }
    }

    /// Rebuild the program-derived drive insert after CC121.
    ///
    /// CC121 changes neither program nor bank, so the insert's *configuration* is
    /// unchanged — this only returns its internal sag/filter memory to spawn state,
    /// which is what CC121 has always done here. It no longer re-derives the effect
    /// sends: those are persistent channel state RP-015 preserves, and resetting
    /// them discarded an authored CC93/CC94 (MM-BUG-KILN-00033).
    fn rederive_program_drive(&mut self, ch: u8) {
        let prog = self.strips[ch as usize].program;
        let bank = self.strips[ch as usize].alt_bank_value;
        self.strips[ch as usize].drive =
            needs_drive(prog).then(|| Drive::new(prog, bank != 0, self.opt.sr));
    }

    fn all_sound_off(&mut self, ch: u8) {
        if ch != 9 {
            self.strips[ch as usize].bagpipe_drone_holds = 0;
            self.strips[ch as usize].bagpipe_drone_live = false;
            self.strips[ch as usize].bagpipe_drone_hang = 0;
        }
        self.active.retain_mut(|a| {
            if a.ch == ch {
                a.voice.choke();
                false
            } else {
                true
            }
        });
    }

    fn all_notes_off(&mut self, ch: u8) {
        if ch != 9 {
            self.strips[ch as usize].bagpipe_drone_holds = 0;
        }
        let sustain = self.strips[ch as usize].sustain;
        for a in self
            .active
            .iter_mut()
            .filter(|a| a.ch == ch && !a.voice.released())
        {
            if ch != 9 && sustain {
                a.held = true;
            } else if ch != 9 && a.sost {
                a.sost_held = true;
            } else {
                a.voice.note_off();
            }
        }
    }

    /// CC121 Reset All Controllers.
    ///
    /// MMA RP-015 enumerates a SHORT list: modulation, expression, the four pedals,
    /// portamento control's pending source key, the RPN/NRPN selector (→ Null),
    /// pitch-bend position (→ centre) and channel/poly pressure. Everything else on
    /// the channel is explicitly preserved — volume, pan, program, bank, the effect
    /// sends, the CC70-79 sound controllers, and the VALUES an RPN wrote. That last
    /// one is the subtle part: RAC nulls the RPN *selector*, it does not revert what
    /// the selector set, so the pitch-bend range and fine tuning survive
    /// (MM-BUG-KILN-00033).
    fn reset_all_controllers(&mut self, ch: u8) {
        let ci = ch as usize;
        let s = &mut self.strips[ci];
        // Pitch bend returns to CENTRE — which is the channel's fine tuning, not
        // 1.0. `fine` (RPN 0,1) and `bend_range` (RPN 0,0) are RPN-set values and
        // survive, so a later bend still spans the range the file asked for.
        s.bend_wheel = 0.0;
        s.bend = s.fine;
        s.rpn_msb = 127;
        s.rpn_lsb = 127;
        s.data_msb = 0;
        s.porta_on = false;
        s.last_freq = None;
        s.porta_control = None; // pending CC84 source is cleared; bank_lsb persists (not a RAC controller)
        s.sustain = false;
        s.sost_down = false;
        s.soft = false;
        s.legato = false;
        s.at_authored = false;
        s.at_target = 0.0;
        s.at_cur = 0.0;
        s.at_gain = 1.0;
        s.mod_target = 0.0;
        s.mod_cur = 0.0;
        s.mod_engaged = false;
        s.mod_authored = false;
        s.vib_mult = 1.0;
        s.organ_trem_phase = 0.0;
        s.expr_target = 1.0;
        s.expr = 1.0;
        s.expr_authored = false;
        s.breath_authored = false;
        s.breath_target = 1.0;
        s.breath = 1.0;
        // Deliberately NOT reset, because RP-015 preserves them: the CC5 portamento
        // TIME (only the CC65 switch resets), the CC70 vowel / CC71 resonance /
        // CC74 cutoff sound controllers together with the wah filters that realise
        // them, and the CC93/94 effect sends.
        self.rederive_program_drive(ch);

        let program = self.strips[ci].program;
        let bend = self.strips[ci].bend;
        let vowel = self.strips[ci].vowel_cur;
        let choir_vowel = matches!(program, 52..=54).then(|| vowel_at(vowel));
        for a in self.active.iter_mut().filter(|a| a.ch == ch) {
            if a.held || a.sost_held {
                a.voice.note_off();
            }
            a.held = false;
            a.sost = false;
            a.sost_held = false;
            a.glide = None;
            // CC121 also drops any per-note key-pressure lane back to its
            // exact spawn defaults (all no-ops).
            a.poly_authored = false;
            a.poly_target = 0.0;
            a.poly_cur = 0.0;
            a.poly_phase = 0.0;
            a.poly_mult = 1.0;
            a.poly_gain = 1.0;
            // Centred bend, but still scaled by the preserved fine tuning.
            a.voice.set_pitch(bend);
            if organ_leslie_family(a.program, a.alt_bank_value) {
                let (rate, depth) = voices::organ_trem_base(a.program);
                a.voice.set_trem(rate, depth);
            }
            if let Some((freqs, qs, gains)) = choir_vowel {
                a.voice.set_vowel(freqs, qs, gains);
            }
        }
    }

    pub(crate) fn render_block_add(&mut self, n: usize, out: &mut [f32]) {
        debug_assert!(n <= BLOCK);
        debug_assert!(out.len() >= n * 2);
        // TREM1 sample clock: events for this block were already applied at
        // now == block start; advance for the next block's events.
        self.now += n as u64;
        let sr = self.opt.sr;

        self.tick_bagpipe_drone_latch();

        for (ci, strip) in self.strips.iter_mut().enumerate() {
            strip.mod_cur += self.expr_smooth * (strip.mod_target - strip.mod_cur);
            let on = strip.mod_cur > 1e-3;
            let ch = ci as u8;
            let leslie_program = self
                .active
                .iter()
                .find(|a| a.ch == ch && organ_leslie_family(a.program, a.alt_bank_value))
                .map(|a| a.program)
                .or_else(|| {
                    (strip.mod_authored && organ_leslie_family(strip.program, strip.alt_bank_value))
                        .then_some(strip.program)
                });
            let active_pitch_vibrato = self
                .active
                .iter()
                .any(|a| a.ch == ch && cc1_pitch_vibrato_target(a.program, a.alt));
            let pending_pitch_vibrato = vibrato_family(strip.program);
            if ci == 9 || (!on && !strip.mod_engaged && leslie_program.is_none()) {
                continue;
            }
            let m = if on { strip.mod_cur } else { 0.0 };
            let mut engaged = false;
            if let Some(program) = leslie_program {
                let (base_rate, base_depth) = voices::organ_trem_base(program);
                if !strip.mod_engaged || strip.leslie_depth <= 0.0 {
                    strip.leslie_rate = if strip.mod_authored {
                        LESLIE_SLOW_HZ
                    } else {
                        base_rate
                    };
                    strip.leslie_depth = base_depth;
                }
                let target_rate = if strip.mod_authored {
                    LESLIE_SLOW_HZ + (LESLIE_FAST_HZ - LESLIE_SLOW_HZ) * m
                } else {
                    base_rate
                };
                let target_depth = base_depth + LESLIE_DEPTH_ADD * m;
                strip.leslie_rate += self.leslie_k * (target_rate - strip.leslie_rate);
                strip.leslie_depth += self.leslie_k * (target_depth - strip.leslie_depth);
                for a in self
                    .active
                    .iter_mut()
                    .filter(|a| a.ch == ch && organ_leslie_family(a.program, a.alt_bank_value))
                {
                    a.voice.set_trem(strip.leslie_rate, strip.leslie_depth);
                }
                engaged |= strip.mod_authored || on || (strip.leslie_rate - base_rate).abs() > 0.01;
            }
            if (on || strip.mod_engaged) && (active_pitch_vibrato || pending_pitch_vibrato) {
                strip.vib_phase += TAU * VIB_RATE_HZ * n as f32 / sr;
                if strip.vib_phase > TAU {
                    strip.vib_phase -= TAU;
                }
                let factor = 2f32.powf(m * VIB_DEPTH_CENTS / 1200.0 * strip.vib_phase.sin());
                strip.vib_mult = factor;
                let mult = strip.bend * factor;
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                    // Alt-bank strings/choir restore v0.9 CC1 semantics PER HELD
                    // voice (a.alt is the spawn-time bank): strings deepen their
                    // own decorrelated per-layer vibrato via set_vib (not the
                    // coherent set_pitch warble); choir gets no CC1. Every default
                    // voice takes the identical set_pitch path, so a channel with
                    // no alt voices is byte-for-byte unchanged.
                    if a.alt && matches!(a.program, 48..=51) {
                        let base = crate::altbank::strings_vib_base(a.program);
                        a.voice.set_vib(base + (ST_CC1_VIB_DEPTH - base) * m);
                    } else if a.alt && matches!(a.program, 52..=54) {
                        // alt-bank choir: no CC1 pitch vibrato (v0.9)
                    } else if a.alt && a.program == 22 {
                        // alt-bank 22 delegates to the default voice, but keeps
                        // the alt bank's spawn-time CC1 semantics.
                    } else if vibrato_family(a.program) {
                        a.voice.set_pitch(mult);
                    }
                }
                engaged |= on;
            } else if !active_pitch_vibrato {
                strip.vib_mult = 1.0;
            }
            strip.mod_engaged = engaged;
        }

        // The cathedral organ breathes as one wind chest. Pressure and the
        // signed tremulant sample are channel-global, while each rank applies
        // its own sensitivity inside the voice. Legacy GM19 remains on the
        // Leslie path above.
        for (ci, strip) in self.strips.iter_mut().enumerate() {
            if ci == 9 {
                continue;
            }
            let ch = ci as u8;
            let cat_notes = self
                .active
                .iter()
                .filter(|a| a.ch == ch && cathedral_organ(a.program, a.alt_bank_value))
                .count();
            let load = cat_notes.saturating_sub(1).min(9) as f32 / 9.0;
            let target = load;
            let tau = if target > strip.organ_wind {
                0.35
            } else {
                1.20
            };
            let k = 1.0 - (-(BLOCK as f32) / (tau * sr)).exp();
            strip.organ_wind += k * (target - strip.organ_wind);
            let trem = if cat_notes > 0 && strip.mod_cur > 1e-4 {
                strip.organ_trem_phase += TAU * 5.5 * n as f32 / sr;
                if strip.organ_trem_phase > TAU {
                    strip.organ_trem_phase -= TAU;
                }
                strip.organ_trem_phase.sin() * strip.mod_cur
            } else {
                0.0
            };
            // Reed-rasp drive from the swell (CC11). Opt-in: 0 unless CC11 authored.
            let drive = if strip.expr_authored {
                ((strip.expr - ORGAN_SWELL_KNEE) / (1.0 - ORGAN_SWELL_KNEE))
                    .clamp(0.0, 1.0)
                    .powf(ORGAN_SWELL_GAMMA)
            } else {
                0.0
            };
            for a in self
                .active
                .iter_mut()
                .filter(|a| a.ch == ch && cathedral_organ(a.program, a.alt_bank_value))
            {
                a.voice.set_organ_pressure(strip.organ_wind, trem);
                a.voice.set_organ_swell(drive);
            }
        }

        for (ci, strip) in self.strips.iter_mut().enumerate() {
            if ci == 9 {
                continue;
            }
            let ch = ci as u8;
            if strip.vowel_authored && vowel_family(strip.program) {
                strip.vowel_cur += self.expr_smooth * (strip.vowel_target - strip.vowel_cur);
                let (f, q, g) = vowel_at(strip.vowel_cur);
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_vowel(f, q, g);
                }
            }
            // Poly (key) aftertouch: advance each authored note's private
            // pressure lane first, so the channel-AT and glide sites below can
            // compose its factor in. Unauthored notes keep poly_mult/poly_gain
            // at exactly 1.0 (a bit-exact no-op).
            let mut any_poly = false;
            for a in self
                .active
                .iter_mut()
                .filter(|a| a.ch == ch && a.poly_authored)
            {
                a.poly_cur += self.expr_smooth * (a.poly_target - a.poly_cur);
                a.poly_gain = 10f32.powf(a.poly_cur * AT_GAIN_DB / 20.0);
                a.poly_phase += TAU * AT_VIB_RATE_HZ * n as f32 / sr;
                if a.poly_phase > TAU {
                    a.poly_phase -= TAU;
                }
                a.poly_mult = 2f32.powf(a.poly_cur * AT_VIB_CENTS / 1200.0 * a.poly_phase.sin());
                any_poly = true;
            }
            let channel_at = strip.at_authored && aftertouch_family(strip.program);
            let mut at_vib = 1.0f32;
            if channel_at {
                strip.at_cur += self.expr_smooth * (strip.at_target - strip.at_cur);
                strip.at_gain = 10f32.powf(strip.at_cur * AT_GAIN_DB / 20.0);
                strip.at_phase += TAU * AT_VIB_RATE_HZ * n as f32 / sr;
                if strip.at_phase > TAU {
                    strip.at_phase -= TAU;
                }
                at_vib = 2f32.powf(strip.at_cur * AT_VIB_CENTS / 1200.0 * strip.at_phase.sin());
                // `!a.is_drum`: an XG/GS drum channel on this strip keeps its at_gain
                // (computed above) but its percussion voices must not be pitch-bent —
                // the same reason ch9 skips this whole block (ci==9 continues earlier).
                for a in self.active.iter_mut().filter(|a| a.ch == ch && !a.is_drum) {
                    // Alt strings/choir take CC1 via set_vib, so the coherent
                    // vib_mult factor must not compose into their aftertouch
                    // pitch (v0.9 kept 48-54 out of vibrato_family; aftertouch
                    // still applies). Default voices are byte-for-byte unchanged.
                    let vm = if a.alt && (matches!(a.program, 48..=54) || a.program == 22) {
                        1.0
                    } else {
                        strip.vib_mult
                    };
                    a.voice.set_pitch(strip.bend * vm * at_vib * a.poly_mult);
                }
            }
            // Poly-only channels: no channel-AT loop ran, so authored notes
            // apply their own pitch factor here (glides are handled below).
            if any_poly && !channel_at {
                for a in self
                    .active
                    .iter_mut()
                    .filter(|a| a.ch == ch && a.poly_authored && a.glide.is_none())
                {
                    let vm = if a.alt && (matches!(a.program, 48..=54) || a.program == 22) {
                        1.0
                    } else {
                        strip.vib_mult
                    };
                    a.voice.set_pitch(strip.bend * vm * a.poly_mult);
                }
            }
            // BR9: brass breath — CC11 expression opens the timbre, channel
            // aftertouch adds flutter growl. A no-op on every 56-63 channel that
            // authors neither (only The Iron Tide uses brass, waived §4.3).
            if matches!(strip.program, 56..=63) {
                // CC2 breath composes into the pressure (1.0 = no-op) so a
                // breath-authored brass line also opens/closes its timbre.
                let p = (strip.expr * strip.breath).sqrt().min(1.3);
                let g = if strip.at_authored { strip.at_cur } else { 0.0 };
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_breath(p, g);
                }
            }
            // RD9 (§2.8.3): the reed breath seam, AUTHORED-only (§2.8.2 — an
            // unauthored reed channel must render exactly as before; contrast
            // the unconditional brass site above). Aftertouch rides along as
            // the growl arg, reserved for the §2.8.4 rasp stage.
            if matches!(strip.program, 64..=71 | 109 | 111)
                && (strip.expr_authored || strip.breath_authored || strip.at_authored)
            {
                let p = (strip.expr * strip.breath).sqrt().min(1.0);
                let g = if strip.at_authored { strip.at_cur } else { 0.0 };
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_breath(p, g);
                }
            }
            // WD9 (§2.8.5.3): the flue breath seam — same authored-only gate,
            // same lanes. `Wind` has no growl consumer, so nothing rides the
            // second arg. An unauthored flue channel never reaches here and
            // renders controller-identically to before.
            if matches!(strip.program, 72..=79)
                && (strip.expr_authored || strip.breath_authored || strip.at_authored)
            {
                let p = (strip.expr * strip.breath).sqrt().min(1.0);
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_breath(p, 0.0);
                }
            }
            for a in self.active.iter_mut().filter(|a| a.ch == ch) {
                if let Some((semis, k)) = &mut a.glide {
                    *semis -= *k * *semis;
                    let done = semis.abs() < 0.005;
                    let gm = if done { 1.0 } else { 2f32.powf(*semis / 12.0) };
                    // Same alt-orchestral CC1 exclusion as the aftertouch site.
                    let vm = if a.alt && (matches!(a.program, 48..=54) || a.program == 22) {
                        1.0
                    } else {
                        strip.vib_mult
                    };
                    a.voice
                        .set_pitch(strip.bend * vm * at_vib * a.poly_mult * gm);
                    if done {
                        a.glide = None;
                    }
                }
            }
        }

        for buf in self.ch_buf.iter_mut() {
            buf[..n].fill(0.0);
        }
        for buf in self.legacy_buf.iter_mut() {
            buf[..n].fill(0.0);
        }
        for buf in self.cathedral_buf.iter_mut() {
            buf[..n].fill(0.0);
        }
        self.stats.max_polyphony = self.stats.max_polyphony.max(self.active.len());
        self.active.retain_mut(|a| {
            if a.is_drum {
                return true; // drums render in the dedicated pass below
            }
            self.scratch[..n].fill(0.0);
            let alive = a.voice.render(&mut self.scratch[..n]);
            // Per-note poly-AT gain lift; multiplies UNDER the strip's channel
            // at_gain so channel and key pressure add in dB. Skipped entirely
            // (1.0) for notes that never authored poly AT.
            if a.poly_gain != 1.0 {
                for x in self.scratch[..n].iter_mut() {
                    *x *= a.poly_gain;
                }
            }
            let buf = if cathedral_organ(a.program, a.alt_bank_value) {
                &mut self.cathedral_buf[a.ch as usize]
            } else if a.program == 19 && a.alt {
                &mut self.legacy_buf[a.ch as usize]
            } else {
                &mut self.ch_buf[a.ch as usize]
            };
            for (dst, src) in buf[..n].iter_mut().zip(self.scratch[..n].iter()) {
                *dst += *src;
            }
            alive
        });

        self.mix_l[..n].fill(0.0);
        self.mix_r[..n].fill(0.0);
        self.send_rev[..n].fill(0.0);
        self.send_cathedral[..n].fill(0.0);
        self.send_cho[..n].fill(0.0);
        self.send_del[..n].fill(0.0);
        self.send_sym[..n].fill(0.0);
        self.send_sym_gtr[..n].fill(0.0);
        self.send_sym_sitar[..n].fill(0.0);
        self.send_room[..n].fill(0.0);
        for (ci, strip) in self.strips.iter_mut().enumerate() {
            let buf = &mut self.ch_buf[ci];
            let legacy = &mut self.legacy_buf[ci];
            let cathedral = &mut self.cathedral_buf[ci];
            if let Some((xg, wet)) = &mut strip.xg_insert {
                // XG Amp-Simulator insertion REPLACES the program drive on this
                // channel (one amp+cabinet, never two in series). Dry/Wet blend
                // at BASE rate — outside Drive's internal 2x — so Drive::process
                // stays byte-for-byte the program-drive path: copy the dry
                // block, process 100% wet, then interpolate by the weight.
                let wet = *wet;
                if wet >= 1.0 {
                    xg.process(&mut buf[..n]);
                } else {
                    let mut dry = [0f32; BLOCK];
                    dry[..n].copy_from_slice(&buf[..n]);
                    xg.process(&mut buf[..n]);
                    for (b, d) in buf[..n].iter_mut().zip(&dry[..n]) {
                        *b = *d * (1.0 - wet) + *b * wet;
                    }
                }
            } else if let Some(drive) = &mut strip.drive {
                drive.process(&mut buf[..n]);
            }
            if let Some(wah) = &mut strip.wah {
                strip.cutoff += self.wah_smooth * (strip.cutoff_target - strip.cutoff);
                strip.res += self.wah_smooth * (strip.res_target - strip.res);
                wah.retune_lowpass(strip.cutoff, strip.res, sr);
                if ci != 9 {
                    for x in buf[..n].iter_mut() {
                        *x = wah.process(*x);
                    }
                }
            }
            if let Some(wah) = &mut strip.wah_legacy {
                wah.retune_lowpass(strip.cutoff, strip.res, sr);
                for x in legacy[..n].iter_mut() {
                    *x = wah.process(*x);
                }
            }
            if let Some(wah) = &mut strip.wah_cathedral {
                wah.retune_lowpass(strip.cutoff, strip.res, sr);
                for x in cathedral[..n].iter_mut() {
                    *x = wah.process(*x);
                }
            }
            // CC7 volume / CC10 pan (prime-on-first-block): snap to the authored
            // target on the first block after authoring — reproducing MIDI
            // last-write-wins for a same-tick burst and the old instant set — then
            // one-pole slew toward it thereafter, so a fade or pan sweep ramps rather
            // than stepping at block boundaries. haas_delay is derived once per block
            // from the slewed pan (single source of truth; tracks the sweep). A
            // channel that never authors CC7/CC10 keeps its default byte-for-byte.
            if strip.volume_authored {
                if strip.volume_primed {
                    strip.volume += self.expr_smooth * (strip.volume_target - strip.volume);
                } else {
                    strip.volume = strip.volume_target;
                    strip.volume_primed = true;
                }
            }
            if strip.pan_authored {
                if strip.pan_primed {
                    strip.pan += self.expr_smooth * (strip.pan_target - strip.pan);
                } else {
                    strip.pan = strip.pan_target;
                    strip.pan_primed = true;
                }
                strip.haas_delay = 0.005 * sr * (strip.pan - 0.5).abs() * 2.0;
            }
            strip.expr += self.expr_smooth * (strip.expr_target - strip.expr);
            if strip.breath_authored {
                strip.breath += self.expr_smooth * (strip.breath_target - strip.breath);
            }
            // SC-55-referenced per-program loudness trim (melodic channels only;
            // ch9 drums are key-indexed and levelled by kit_balance()). `g` feeds
            // both the dry mix and every FX send below, so this scales the whole
            // voice together — pure level, timbre- and wet/dry-neutral.
            let trim = if ci != 9 {
                program_trim_lin(strip.program)
            } else {
                1.0
            };
            let g = strip.volume * strip.expr * strip.at_gain * strip.breath * trim;
            if g < 1e-6 {
                continue;
            }
            let theta = strip.pan * FRAC_PI_2;
            let (gl, gr) = (g * theta.cos(), g * theta.sin());
            let rs = strip.reverb_send * 0.9;
            let is_piano = ci != 9 && voices::is_acoustic_piano(strip.program);
            let is_ac_gtr = ci != 9 && matches!(strip.program, 24 | 25);
            let is_sitar = ci != 9 && strip.program == 104;
            if is_sitar {
                self.sitar_seen = true;
            }
            let haas = strip.haas_delay;
            let legacy_cho = if strip.chorus_authored {
                strip.chorus_send
            } else {
                0.20
            };
            let legacy_del = if strip.delay_authored {
                strip.delay_send
            } else {
                0.0
            };
            let cathedral_cho = if strip.chorus_authored {
                strip.chorus_send
            } else {
                0.0
            };
            let cathedral_del = if strip.delay_authored {
                strip.delay_send
            } else {
                0.0
            };
            for i in 0..n {
                let (ordinary_x, legacy_x, cathedral_x) = (buf[i], legacy[i], cathedral[i]);
                let x = ordinary_x + legacy_x + cathedral_x;
                strip.haas.push(x);
                let (xl, xr) = if haas < 1.0 {
                    (x, x)
                } else if strip.pan < 0.5 {
                    (x, strip.haas.tap(haas))
                } else {
                    (strip.haas.tap(haas), x)
                };
                self.mix_l[i] += xl * gl;
                self.mix_r[i] += xr * gr;
                let (ordinary_s, legacy_s, cathedral_s) =
                    (ordinary_x * g, legacy_x * g, cathedral_x * g);
                let xs = ordinary_s + legacy_s + cathedral_s;
                self.send_rev[i] += (ordinary_s + legacy_s) * rs;
                self.send_cathedral[i] += cathedral_s * rs;
                self.send_cho[i] += ordinary_s * strip.chorus_send
                    + legacy_s * legacy_cho
                    + cathedral_s * cathedral_cho;
                self.send_del[i] += ordinary_s * strip.delay_send
                    + legacy_s * legacy_del
                    + cathedral_s * cathedral_del;
                if is_piano {
                    self.send_sym[i] += xs;
                }
                if is_ac_gtr {
                    self.send_sym_gtr[i] += xs;
                }
                if is_sitar {
                    self.send_sym_sitar[i] += xs;
                }
            }
        }

        {
            self.drum_l[..n].fill(0.0);
            self.drum_r[..n].fill(0.0);
            self.active.retain_mut(|a| {
                if !a.is_drum {
                    return true;
                }
                self.scratch[..n].fill(0.0);
                let alive = a.voice.render(&mut self.scratch[..n]);
                // Per-key placement, shared by both drum paths: the channel's own
                // pan offset (strips[9] for the main kit, since a.ch == 9 there) plus
                // the per-key kit map and balance.
                let s = &self.strips[a.ch as usize];
                let pan = (drum_pan(a.key) + (s.pan - 0.5)).clamp(0.0, 1.0);
                let theta = pan * FRAC_PI_2;
                let bal = kit_balance(a.key);
                let (ul, ur) = (theta.cos() * bal, theta.sin() * bal);
                if a.ch == 9 {
                    // Main kit: accumulate raw into the drum bus; the shared wah +
                    // bus master g9 are applied after the closure (path unchanged).
                    for i in 0..n {
                        self.drum_l[i] += self.scratch[i] * ul;
                        self.drum_r[i] += self.scratch[i] * ur;
                    }
                } else {
                    // XG/GS drum channel: scaled by its OWN gain straight into the master
                    // mix — bypassing ch9's bus master and wah — with its own CC91
                    // reverb and the shared drum room. The `(scratch*ul)*gc` association
                    // mirrors the ch9 path, so a single hit is byte-equal to the same
                    // hit on ch9 (gc == g9 when the strips match).
                    let gc = s.volume * s.expr * s.at_gain * s.breath * DRUM_FORWARD;
                    if gc >= 1e-6 {
                        let rs = s.reverb_send * 0.9;
                        for i in 0..n {
                            let xl = (self.scratch[i] * ul) * gc;
                            let xr = (self.scratch[i] * ur) * gc;
                            self.mix_l[i] += xl;
                            self.mix_r[i] += xr;
                            let mono = 0.5 * (xl + xr);
                            self.send_rev[i] += mono * rs;
                            self.send_room[i] += mono * ROOM_SEND;
                        }
                    }
                }
                alive
            });
            let s9 = &mut self.strips[9];
            if let Some(wl) = &mut s9.wah {
                for x in self.drum_l[..n].iter_mut() {
                    *x = wl.process(*x);
                }
            }
            if let Some(wr) = &mut s9.wah_r {
                wr.retune_lowpass(s9.cutoff, s9.res, sr);
                for x in self.drum_r[..n].iter_mut() {
                    *x = wr.process(*x);
                }
            }
            let g9 = s9.volume * s9.expr * s9.at_gain * s9.breath * DRUM_FORWARD;
            if g9 >= 1e-6 {
                let rs = s9.reverb_send * 0.9;
                for i in 0..n {
                    let (xl, xr) = (self.drum_l[i] * g9, self.drum_r[i] * g9);
                    self.mix_l[i] += xl;
                    self.mix_r[i] += xr;
                    let mono = 0.5 * (xl + xr);
                    self.send_rev[i] += mono * rs;
                    self.send_room[i] += mono * ROOM_SEND;
                }
            }
        }

        self.symp.process(
            &self.send_sym[..n],
            &mut self.mix_l[..n],
            &mut self.mix_r[..n],
        );
        if self.opt.gtr_symp_on {
            self.gtr_symp.process(
                &self.send_sym_gtr[..n],
                &mut self.mix_l[..n],
                &mut self.mix_r[..n],
            );
        }
        // tarab bus: gated on `sitar_seen` (not just the option) so a render
        // with no program 104 anywhere never even touches the combs
        if self.opt.sitar_symp_on && self.sitar_seen {
            self.sitar_symp.process(
                &self.send_sym_sitar[..n],
                &mut self.mix_l[..n],
                &mut self.mix_r[..n],
            );
        }
        self.chorus.process(
            &self.send_cho[..n],
            &mut self.mix_l[..n],
            &mut self.mix_r[..n],
        );
        if let Some(echo) = &mut self.echo {
            echo.process(
                &self.send_del[..n],
                &mut self.mix_l[..n],
                &mut self.mix_r[..n],
            );
        }
        if self.opt.drum_room_on {
            self.drum_room.process(
                &self.send_room[..n],
                &mut self.mix_l[..n],
                &mut self.mix_r[..n],
            );
        }
        for x in self.send_rev[..n].iter_mut() {
            *x = self.rev_hp.process(*x);
        }
        self.reverb.process(
            &self.send_rev[..n],
            &mut self.mix_l[..n],
            &mut self.mix_r[..n],
        );
        self.cathedral.process(
            &self.send_cathedral[..n],
            &mut self.mix_l[..n],
            &mut self.mix_r[..n],
        );
        #[cfg(test)]
        {
            self.stats.cathedral_return_peak = self
                .stats
                .cathedral_return_peak
                .max(self.cathedral.debug_return_peak());
        }
        self.glue
            .process(&mut self.mix_l[..n], &mut self.mix_r[..n]);

        for i in 0..n {
            out[i * 2] += self.mix_l[i];
            out[i * 2 + 1] += self.mix_r[i];
            let m = self.mix_l[i].abs().max(self.mix_r[i].abs());
            if m > self.stats.peak {
                self.stats.peak = m;
            }
        }
    }
}

pub fn render(song: &Song, opt: &Options) -> (Vec<f32>, Stats) {
    render_buses_with_progress(song, opt, true, true, true, &mut |_| {})
}

pub fn render_with_progress(
    song: &Song,
    opt: &Options,
    on_progress: &mut dyn FnMut(Progress),
) -> (Vec<f32>, Stats) {
    render_buses_with_progress(song, opt, true, true, true, on_progress)
}

/// The A/B oracle entry point (19, 32a): render the same song with the
/// guitar-sympathetic, drum-room, or sitar-tarab bus disabled. The public
/// `render` always enables all three — no shipped knob — so this is
/// test-only.
#[cfg(test)]
pub(crate) fn render_buses(
    song: &Song,
    opt: &Options,
    gtr_symp_on: bool,
    drum_room_on: bool,
    sitar_symp_on: bool,
) -> (Vec<f32>, Stats) {
    render_buses_with_progress(
        song,
        opt,
        gtr_symp_on,
        drum_room_on,
        sitar_symp_on,
        &mut |_| {},
    )
}

pub(crate) fn render_buses_with_progress(
    song: &Song,
    opt: &Options,
    gtr_symp_on: bool,
    drum_room_on: bool,
    sitar_symp_on: bool,
    on_progress: &mut dyn FnMut(Progress),
) -> (Vec<f32>, Stats) {
    let sr = opt.sr;
    let total = ((song.seconds + opt.tail as f64) * sr as f64) as usize;
    let mut out = vec![0f32; total * 2]; // interleaved stereo

    let mut core = EngineCore::new(CoreOptions::from_options(
        opt,
        gtr_symp_on,
        drum_room_on,
        sitar_symp_on,
    ));

    let events: Vec<(usize, EvKind)> = song
        .events
        .iter()
        .map(|e| ((e.sec * sr as f64) as usize, e.kind))
        .collect();
    let mut ev_i = 0;

    let mut next_report = total / 10;

    let mut block_start = 0usize;
    while block_start < total {
        let n = BLOCK.min(total - block_start);

        // apply events that fall inside this block (quantised to block start)
        while ev_i < events.len() && events[ev_i].0 < block_start + n {
            let (_, kind) = events[ev_i];
            ev_i += 1;

            core.handle_event(kind);
        }

        core.render_block_add(n, &mut out[block_start * 2..(block_start + n) * 2]);

        block_start += n;
        if block_start >= next_report {
            on_progress(Progress {
                rendered_seconds: block_start as f64 / sr as f64,
                total_seconds: total as f64 / sr as f64,
                active_voices: core.active_voice_count(),
            });
            next_report += total / 10;
        }
    }
    (out, core.stats())
}

/// Scale by `scale`, TPDF-dither, and quantise to interleaved i16. Shared by the
/// peak- and loudness-normalisation paths so both dither identically.
fn dither_quantize(samples: &[f32], scale: f32) -> Vec<i16> {
    let mut rng = Rng::new(0xD17E);
    samples
        .iter()
        .map(|&x| {
            let dither = (rng.white() + rng.white()) * 0.5; // triangular, ±1 LSB
            ((x * scale).clamp(-1.0, 1.0) * 32767.0 + dither)
                .round()
                .clamp(-32768.0, 32767.0) as i16
        })
        .collect()
}

/// Peak-normalise to `target` and convert to interleaved i16 with TPDF dither.
pub fn normalize_to_i16(samples: &[f32], peak: f32, target: f32) -> Vec<i16> {
    let scale = if peak > 1e-9 { target / peak } else { 1.0 };
    dither_quantize(samples, scale)
}

/// Max loudness-recovery iterations and the LUFS tolerance for "on target".
const LOUDNESS_MAX_ITERS: usize = 6;
const LOUDNESS_TOL_DB: f32 = 0.3;

/// Loudness-normalise: bring integrated loudness (BS.1770-4) to `target_lufs`,
/// true-peak-limit to `ceiling_dbtp`, then TPDF-dither to interleaved i16.
///
/// The gain is a single scalar, so every composed within-track dynamic (and every
/// `analyze.py` ratio oracle) is preserved exactly; only over-ceiling transients
/// are touched, by the limiter. On a high-crest track a low ceiling removes enough
/// peak energy to drop the loudness below target, so we iterate: re-measure and
/// re-apply the residual makeup, re-limit, until on target. Because limiting only
/// ever removes energy, loudness approaches the target from below and never
/// overshoots — so this converges (or, for a track that genuinely cannot reach the
/// target without over-limiting, lands as close as the ceiling allows). Silence
/// (no gated blocks) passes through ungained.
pub fn normalize_loudness(
    samples: &[f32],
    sr: f32,
    target_lufs: f32,
    ceiling_dbtp: f32,
) -> Vec<i16> {
    let mut buf: Vec<f32> = samples.to_vec();
    for _ in 0..LOUDNESS_MAX_ITERS {
        let measured = crate::loudness::integrated_lufs(&buf, sr);
        if !measured.is_finite() {
            break; // silence — leave ungained
        }
        let delta = target_lufs - measured;
        if delta.abs() < LOUDNESS_TOL_DB {
            break; // on target
        }
        let g = 10f32.powf(delta / 20.0);
        for x in buf.iter_mut() {
            *x *= g;
        }
        crate::loudness::limit_true_peak(&mut buf, sr, ceiling_dbtp);
    }
    dither_quantize(&buf, 1.0)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::midi::Ev;

    /// The SC-55-referenced per-program loudness trim (`PROGRAM_TRIM_DB`) is
    /// CONSERVATIVE by design: it corrects sustained families only and leaves
    /// struck/plucked/percussive voices and noise/FX untouched. This oracle pins
    /// that scope contract — so a future edit cannot silently trim piano, guitar
    /// or drums — plus the flagship calibrated anchors and the dB→linear mapping.
    #[test]
    fn program_trim_scope_and_calibration() {
        // The corrected set = the sustained ranges (bowed strings only;
        // pizz/harp/timpani and the orchestra-hit stab stay out) PLUS the one
        // documented plucked exception, GM6 harpsichord (measured ~10 dB low by
        // the fair early-window RMS — see PROGRAM_TRIM_DB). Its complement MUST be
        // untouched (0.0 dB, unity gain).
        let is_corrected = |p: u8| {
            matches!(p,
                6          // harpsichord (documented plucked exception)
                | 16..=23  // Organ
                | 40..=44  // bowed strings (pizz 45 / harp 46 / timpani 47 excluded)
                | 48..=54  // string & synth sections + choir (orch-hit 55 excluded)
                | 56..=63  // Brass
                | 64..=71  // Reed
                | 72..=79  // Pipe
                | 80..=87  // SynthLead
                | 88..=95) // SynthPad
        };
        for p in 0u8..128 {
            if !is_corrected(p) {
                assert_eq!(
                    PROGRAM_TRIM_DB[p as usize], 0.0,
                    "program {p} is outside the conservative scope and must stay at 0.0 dB"
                );
                assert_eq!(
                    program_trim_lin(p),
                    1.0,
                    "untouched program {p} must be unity gain"
                );
            }
        }

        // Flagship corrections: sections/choir lifted, solo strings/brass/flutes/
        // organ trimmed.
        assert_eq!(PROGRAM_TRIM_DB[50], 6.0); // SynthStrings1 — lifted
        assert_eq!(PROGRAM_TRIM_DB[53], 6.0); // VoiceOohs     — lifted
        assert_eq!(PROGRAM_TRIM_DB[56], -6.0); // Trumpet      — trimmed
        assert_eq!(PROGRAM_TRIM_DB[58], -6.0); // Tuba         — trimmed
        assert_eq!(PROGRAM_TRIM_DB[43], -6.0); // Contrabass   — trimmed
        assert_eq!(PROGRAM_TRIM_DB[73], -4.0); // Flute        — trimmed
        assert_eq!(PROGRAM_TRIM_DB[19], -6.0); // ChurchOrgan  — trimmed
        assert_eq!(PROGRAM_TRIM_DB[6], 6.0); // Harpsichord   — plucked exception, lifted

        // Every entry within the ±6 dB clamp.
        for (p, &db) in PROGRAM_TRIM_DB.iter().enumerate() {
            assert!(
                (-6.0..=6.0).contains(&db),
                "program {p} trim {db} dB is outside the ±6 dB clamp"
            );
        }

        // dB → linear mapping.
        assert!(
            (program_trim_lin(56) - 0.5012).abs() < 1e-3,
            "-6 dB ≈ 0.501×"
        );
        assert!(
            (program_trim_lin(53) - 1.9953).abs() < 1e-3,
            "+6 dB ≈ 1.995×"
        );
        assert_eq!(
            program_trim_lin(0),
            1.0,
            "untouched program must be exactly unity"
        );
    }

    /// `render_with_progress` must be a pure observer: attaching a progress callback
    /// cannot move a single sample.
    ///
    /// This pins the property the v0.17 API pass claimed and would otherwise only have
    /// asserted. It matters because the callback path is now the ONLY path — `render`
    /// delegates to it with a no-op closure — so a future change that let the callback
    /// (or the counter that fires it) touch engine state would silently re-voice every
    /// album in this repo. A bit-exact compare inside one build is a valid oracle here:
    /// both renders run in the same binary, so there is no cross-profile float-reorder
    /// trap (see lessons_learnt.md).
    #[test]
    fn render_with_progress_is_bit_identical_to_render() {
        // Something with a bit of everything: pitched voices, a program change, a
        // controller, and a drum hit on channel 10.
        let mut events = Vec::new();
        for (sec, kind) in [
            (0.0, EvKind::Prog { ch: 0, prog: 46 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 91,
                    val: 80,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 9,
                    key: 38,
                    vel: 110,
                },
            ),
            (
                0.40,
                EvKind::NoteOn {
                    ch: 0,
                    key: 67,
                    vel: 90,
                },
            ),
            (0.90, EvKind::NoteOff { ch: 0, key: 60 }),
            (1.20, EvKind::NoteOff { ch: 0, key: 67 }),
        ] {
            events.push(Ev { sec, kind });
        }
        let song = Song {
            events,
            seconds: 1.5,
            markers: Vec::new(),
            title: String::new(),
            initial_bpm: 120.0,
        };
        let opt = Options::default().with_tail(0.5);

        let (plain, plain_stats) = render(&song, &opt);

        let mut seen = Vec::new();
        let (observed, observed_stats) = render_with_progress(&song, &opt, &mut |p| seen.push(p));

        assert_eq!(
            plain, observed,
            "attaching a progress callback changed the rendered audio"
        );
        assert_eq!(plain_stats.peak, observed_stats.peak);
        assert_eq!(plain_stats.voices_spawned, observed_stats.voices_spawned);

        // And the callback must actually have fired, or the test proves nothing.
        assert!(!seen.is_empty(), "progress callback never fired");
        assert!(seen.iter().all(|p| (0.0..=1.0).contains(&p.fraction())));
        // Monotonic, and it reaches the end.
        assert!(seen
            .windows(2)
            .all(|w| w[1].rendered_seconds >= w[0].rendered_seconds));
    }

    /// U4 full-chain oracle: loudness-normalising an arbitrary-level stereo tone
    /// must land the decoded i16 at the target LUFS and under the true-peak ceiling.
    #[test]
    fn normalize_loudness_hits_target_and_ceiling() {
        let fs = 44100.0;
        // A −30 dBFS-ish 1 kHz stereo sine (needs boosting toward −18).
        let n = (fs * 5.0) as usize;
        let mut sig = Vec::with_capacity(n * 2);
        for i in 0..n {
            let s = 0.03 * (2.0 * std::f32::consts::PI * 1000.0 * i as f32 / fs).sin();
            sig.push(s);
            sig.push(s);
        }
        let pcm = normalize_loudness(&sig, fs, -18.0, -1.0);
        let dec: Vec<f32> = pcm.iter().map(|&s| s as f32 / 32768.0).collect();
        let lufs = crate::loudness::integrated_lufs(&dec, fs);
        let tp = crate::loudness::true_peak_dbtp(&dec, fs);
        assert!(
            (lufs - (-18.0)).abs() < 0.5,
            "decoded loudness should be ~-18 LUFS, got {lufs}"
        );
        assert!(
            tp <= -0.8,
            "decoded true peak should be <= ceiling, got {tp}"
        );
    }

    /// When the loudness gain leaves the signal under the ceiling, the path is a
    /// pure scalar: output must equal input×gain to within the dither (±1 LSB).
    #[test]
    fn normalize_loudness_is_pure_scalar_under_ceiling() {
        let fs = 44100.0;
        let n = (fs * 5.0) as usize;
        let mut sig = Vec::with_capacity(n * 2);
        for i in 0..n {
            let s = 0.05 * (2.0 * std::f32::consts::PI * 440.0 * i as f32 / fs).sin();
            sig.push(s);
            sig.push(s);
        }
        // Target the signal's own loudness → gain ≈ 1, no limiting.
        let measured = crate::loudness::integrated_lufs(&sig, fs);
        let pcm = normalize_loudness(&sig, fs, measured, 0.0);
        // Reference: same dither/quantise with unity scale, no gain, no limiter.
        let reference = normalize_to_i16(&sig, 1.0, 1.0);
        let max_lsb = pcm
            .iter()
            .zip(&reference)
            .map(|(a, b)| (a - b).unsigned_abs())
            .max()
            .unwrap();
        assert!(max_lsb <= 1, "pure-scalar path drifted by {max_lsb} LSB");
    }

    /// High-crest recovery: a quiet body with sparse loud transients, normalised
    /// under an aggressive ceiling. Single-pass gain+limit lands well below target
    /// (the limiter eats the transient energy); the recovery loop must lift it back
    /// to the target by raising the body, while the true peak stays at the ceiling.
    #[test]
    fn normalize_loudness_recovers_on_high_crest() {
        let fs = 44100.0;
        let n = (fs * 6.0) as usize;
        let burst_period = fs as usize / 3; // a burst ~every 0.33 s
        let burst_len = fs as usize / 200; // ~5 ms bursts
        let mut sig = Vec::with_capacity(n * 2);
        for i in 0..n {
            let t = i as f32 / fs;
            let mut s = 0.05 * (2.0 * std::f32::consts::PI * 180.0 * t).sin(); // quiet body
            if i % burst_period < burst_len {
                s += 0.55 * (2.0 * std::f32::consts::PI * 1200.0 * t).sin(); // loud transient
            }
            sig.push(s);
            sig.push(s);
        }
        // Single-pass reference (what the old code did): gain to target, limit once.
        let raw = crate::loudness::integrated_lufs(&sig, fs);
        let g = 10f32.powf((-18.0 - raw) / 20.0);
        let mut once: Vec<f32> = sig.iter().map(|&x| x * g).collect();
        crate::loudness::limit_true_peak(&mut once, fs, -6.0);
        let single = crate::loudness::integrated_lufs(&once, fs);
        assert!(
            single < -18.0 - 0.5,
            "test signal must under-shoot single-pass (got {single}) or it proves nothing"
        );

        // Full path with the recovery loop.
        let pcm = normalize_loudness(&sig, fs, -18.0, -6.0);
        let dec: Vec<f32> = pcm.iter().map(|&s| s as f32 / 32768.0).collect();
        let lufs = crate::loudness::integrated_lufs(&dec, fs);
        let tp = crate::loudness::true_peak_dbtp(&dec, fs);
        assert!(
            (lufs - (-18.0)).abs() < 0.4,
            "recovery loop should reach ~-18 LUFS, got {lufs} (single-pass was {single})"
        );
        assert!(
            tp <= -5.8,
            "true peak must respect the -6 dBTP ceiling, got {tp}"
        );
    }

    fn test_song(events: Vec<(f64, EvKind)>, seconds: f64) -> Song {
        Song {
            events: events
                .into_iter()
                .map(|(sec, kind)| Ev { sec, kind })
                .collect(),
            seconds,
            markers: Vec::new(),
            title: String::new(),
            initial_bpm: 120.0,
        }
    }

    /// Dry options: no reverb, no echo, no LA samples — the tests below
    /// measure the voices themselves, not the room.
    fn test_opts(sr: f32) -> Options {
        Options {
            sr,
            wet: 0.0,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
        }
    }

    fn left(stereo: &[f32]) -> Vec<f32> {
        stereo.iter().step_by(2).copied().collect()
    }

    fn rms(seg: &[f32]) -> f32 {
        (seg.iter().map(|&x| (x * x) as f64).sum::<f64>() / seg.len() as f64).sqrt() as f32
    }

    /// A same-key repeated-note figure on one channel: `n` NoteOn/NoteOff
    /// pairs, `ioi` seconds apart, each gated `gate` seconds — the tremolo
    /// (and, at slow ioi, picked-repeat) test figure.
    fn repeat_song(prog: u8, key: u8, n: usize, ioi: f64, gate: f64, secs: f64) -> Song {
        let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog })];
        for i in 0..n {
            let t = 0.1 + i as f64 * ioi;
            ev.push((
                t,
                EvKind::NoteOn {
                    ch: 0,
                    key,
                    vel: 55,
                },
            ));
            ev.push((t + gate, EvKind::NoteOff { ch: 0, key }));
        }
        test_song(ev, secs)
    }

    /// p10/p90 ratio of the f0-carrier magnitude track (Goertzel per 10 ms
    /// frame) over [t0, t1] — the "does the TONE persist between strokes"
    /// scalar. A ratio, so the −18 LUFS single-scalar loudness normalisation
    /// (and any other pure gain) cannot move it.
    fn carrier_p10_over_p90(out: &[f32], sr: f32, f0: f32, t0: f64, t1: f64) -> f32 {
        let hop = (0.010 * sr) as usize;
        let (a, b) = (
            (t0 * sr as f64) as usize / hop,
            (t1 * sr as f64) as usize / hop,
        );
        let mut mags: Vec<f32> = (a..b)
            .map(|k| crate::testutil::mag_at(&out[k * hop..(k + 1) * hop], sr, f0))
            .collect();
        mags.sort_by(|x, y| x.partial_cmp(y).unwrap());
        mags[mags.len() / 10] / mags[mags.len() * 9 / 10].max(1e-12)
    }

    /// TREM1 oracle: a fast same-key repeated figure on the steel guitar
    /// (GM 25) — 40 strokes at 75 ms IOI, 45 ms gate, the measured shape of
    /// the reported defect — must render as a TREMOLO (one string whose
    /// fundamental persists between strokes, re-picked per stroke), not as
    /// 13 fresh-voice restarts per second (a click train).
    ///
    /// Clause (a) is the perceptual defect itself: the f0 CARRIER's
    /// trough/peak ratio across the steady run. Fresh spawns + the hard
    /// 0.15 s release + G6 release-darkening leave nothing ringing between
    /// strokes (measured 0.03), and — the HFfrac lesson — gross-band
    /// metrics can't see that (overlapping released twins fill the gaps
    /// with broadband hash; broadband p10/p90 moved the WRONG way on an
    /// intermediate fix). The carrier ratio tracks exactly the thing the
    /// ear streams into "one continuous note": tonal energy at f0 in the
    /// gaps. With the restrike path it measures 0.22.
    ///
    /// Clause (b) rejects the opposite degeneracy: the strokes must still
    /// ARTICULATE (broadband 20 ms-frame ripple ≥ 4 dB) — a fix that slurs
    /// the run into one flat held note fails here.
    ///
    /// Clause (c) pins the IOI gate: the same figure at 200 ms IOI is
    /// intentional picking and must keep dying between notes (carrier ratio
    /// stays at the articulated floor, measured 0.006). If the gate ever
    /// widens into picking territory, this clause reds.
    #[test]
    fn fast_same_key_restrikes_shimmer_not_click_train() {
        let sr = 44100.0;
        let key = 83u8; // B5 — treble worst case: fundamental t60 ~130 ms
        let f0 = crate::dsp::key_freq(key);

        // (a) + (b): the defect figure — 40 strokes, 13.3/s
        let song = repeat_song(25, key, 40, 0.075, 0.045, 3.6);
        let out = left(&render(&song, &test_opts(sr)).0);
        let carrier = carrier_p10_over_p90(&out, sr, f0, 0.6, 2.9);
        assert!(
            carrier > 0.10,
            "tremolo carrier collapses between strokes: f0 p10/p90 = {carrier:.3} \
             (fresh-spawn click train ≈ 0.03, restrike shimmer ≈ 0.22)"
        );
        let frame = (0.020 * sr) as usize;
        let a = (0.6 * sr) as usize / frame;
        let b = (2.9 * sr) as usize / frame;
        let mut frames: Vec<f32> = (a..b)
            .map(|k| rms(&out[k * frame..(k + 1) * frame]))
            .collect();
        frames.sort_by(|x, y| x.partial_cmp(y).unwrap());
        let ripple = frames[frames.len() / 10] / frames[frames.len() * 9 / 10].max(1e-12);
        assert!(
            ripple < 0.63,
            "strokes no longer articulate (broadband ripple {ripple:.3} ≥ 0.63 \
             ≈ under 4 dB): the tremolo degenerated into a slur"
        );

        // (c): 200 ms IOI is PICKING — each note must still die away
        let slow = repeat_song(25, key, 12, 0.200, 0.045, 3.6);
        let out = left(&render(&slow, &test_opts(sr)).0);
        let slow_carrier = carrier_p10_over_p90(&out, sr, f0, 0.6, 2.4);
        assert!(
            slow_carrier < 0.05,
            "slow same-note picking lost its articulation: f0 p10/p90 = \
             {slow_carrier:.3} (articulated ≈ 0.006) — the tremolo IOI gate \
             has widened into picking territory"
        );
    }

    fn drum_song(hits: &[(f64, u8, u8)], secs: f64, ccs: &[(u8, u8)]) -> Song {
        let mut ev: Vec<(f64, EvKind)> = ccs
            .iter()
            .map(|&(num, val)| (0.0, EvKind::Cc { ch: 9, num, val }))
            .collect();
        for &(t, key, vel) in hits {
            ev.push((t, EvKind::NoteOn { ch: 9, key, vel }));
        }
        ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        test_song(ev, secs)
    }

    fn drum_prog_song(prog: Option<u8>) -> Song {
        let mut ev = Vec::new();
        if let Some(prog) = prog {
            ev.push((0.0, EvKind::Prog { ch: 9, prog }));
        }
        for (t, key, vel) in [
            (0.05, 36, 110),
            (0.30, 38, 104),
            (0.55, 46, 96),
            (0.85, 49, 108),
            (1.30, 51, 102),
        ] {
            ev.push((t, EvKind::NoteOn { ch: 9, key, vel }));
        }
        test_song(ev, 2.0)
    }

    fn right(stereo: &[f32]) -> Vec<f32> {
        stereo.iter().skip(1).step_by(2).copied().collect()
    }

    #[test]
    fn channel_10_program_change_keeps_v3_default_kit() {
        let sr = 44100.0;
        let opts = test_opts(sr);
        let no_pc = render(&drum_prog_song(None), &opts).0;
        assert!(rms(&no_pc) > 1e-4, "default drum kit should sound");
        for prog in [0u8, 8, 16] {
            let got = render(&drum_prog_song(Some(prog)), &opts).0;
            assert_eq!(
                got, no_pc,
                "channel-10 Program Change {prog} changed the V3 kit"
            );
        }
    }

    /// Channel-10 Program Change 24 (the GM2 Electronic slot) selects the
    /// modeled "synth kit": with samples ON it must NOT take the realistic
    /// sampled drum kit the default V3 does, and it must render exactly as the
    /// samples-OFF modeled path (the synth kit is inert to the global samples
    /// flag). This is the seam Three-Sixty-One rides back onto the synth drums.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn channel_10_program_24_selects_the_synth_kit() {
        let sr = 44100.0;
        let sampled = Options {
            samples: true,
            ..test_opts(sr)
        };
        // Samples ON: the default V3 kit plays the realistic sampled kit...
        let default_kit = render(&drum_prog_song(None), &sampled).0;
        // ...but PC 24 switches to the modeled synth kit, which must differ.
        let synth = render(&drum_prog_song(Some(24)), &sampled).0;
        assert_ne!(
            synth, default_kit,
            "channel-10 PC 24 did not switch off the sampled kit"
        );
        // The synth kit ignores the samples flag — identical to samples-off.
        let modeled = render(&drum_prog_song(Some(24)), &test_opts(sr)).0;
        assert_eq!(
            synth, modeled,
            "synth kit differs from the samples-off modeled path"
        );
    }

    /// Channel-10 Program Change 25 selects the ORIGINAL kit (`Kit::V1`) — the
    /// drum voices from before the 9-10 Jul 2026 "kit-v2"/realism overhaul, which
    /// Three-Sixty-One asks for. It must be a genuinely distinct kit from both the
    /// sampled default and the PC-24 synth kit. V1's *sound* is pinned separately
    /// (and byte-exactly) by `v1_drum_render_signatures_are_stable`; this test
    /// pins the ch-10 selection wiring that makes it reachable.
    #[test]
    fn channel_10_program_25_selects_the_original_v1_kit() {
        let sr = 44100.0;
        let sampled = Options {
            samples: true,
            ..test_opts(sr)
        };
        let default_kit = render(&drum_prog_song(None), &sampled).0;
        let original = render(&drum_prog_song(Some(25)), &sampled).0;
        let synth = render(&drum_prog_song(Some(24)), &sampled).0;
        assert!(rms(&original) > 1e-4, "PC 25 original kit should sound");
        assert_ne!(
            original, default_kit,
            "channel-10 PC 25 did not leave the sampled default kit"
        );
        assert_ne!(
            original, synth,
            "channel-10 PC 25 selected the synth kit, not the original V1 kit"
        );
        // V1 predates the sampled layer entirely, so the samples flag is inert.
        let dry = render(&drum_prog_song(Some(25)), &test_opts(sr)).0;
        assert_eq!(
            original, dry,
            "the original V1 kit must ignore the samples flag"
        );
    }

    /// XG drum-kit bank routing (CC0=127). Yamaha XG declares a drum kit on ANY
    /// channel via bank MSB 127; the Incantations Part IV reference uses ch14 for a
    /// conga part that way, which before this fix misrendered as a GM Drawbar Organ
    /// (program 16) hammering the D4/Eb4/E4 conga keys. Three fresh-engine renders,
    /// dry (`test_opts` wet=0):
    ///   drum9  — key 62 on ch9 (the built-in drum channel)
    ///   xg13   — key 62 on ch13 with CC0=127 + program 16  → must take the drum path
    ///   organ  — key 62 on ch13 with program 16 but NO CC0=127 → the old behaviour
    /// A SINGLE isolated hit, so the compared paths can't diverge on FP associativity
    /// or voice overlap; the XG parallel path mirrors ch9's `(scratch*ul)*g`
    /// association, so byte-equality with the ch9 hit holds exactly. Do NOT fold that
    /// association, and do NOT extend this equality to overlapping voices.
    #[test]
    fn xg_bank_127_routes_channel_to_drums() {
        let sr = 44100.0;
        let opt = test_opts(sr);
        let key = 62u8; // GM/XG "mute hi conga"; as GM program 16 it is D4 ≈ 293.66 Hz

        let hit = |ch: u8, xg: bool| -> Vec<f32> {
            let mut ev = Vec::new();
            if xg {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch,
                        num: 0,
                        val: 127,
                    },
                )); // XG drum-kit bank
            }
            ev.push((0.0, EvKind::Prog { ch, prog: 16 })); // XG Rock kit / GM Drawbar Organ
            ev.push((0.05, EvKind::NoteOn { ch, key, vel: 100 }));
            render(&test_song(ev, 1.5), &opt).0
        };

        let drum9 = hit(9, true); // ch9: CC0=127 is inert (already drums)
        let xg13 = hit(13, true); // ch14 XG-drum: the fix routes this to the drum path
        let organ = hit(13, false); // ch14 without CC0=127: the pre-fix Drawbar Organ

        // The XG-drum hit takes the drum path — byte-identical to the same hit on ch9.
        assert_eq!(
            xg13, drum9,
            "CC0=127 on ch13 must render key {key} as a drum, identical to ch9"
        );
        // ...and is NOT the melodic organ it produced before.
        assert_ne!(
            xg13, organ,
            "CC0=127 must route away from the melodic Drawbar Organ"
        );

        // Bug-proof: the organ SUSTAINS the conga-key pitch (D4); a drum decays. Compare
        // late-tail energy at D4 (1.0–1.4 s, long after the 0.05 s onset) — the organ's
        // is far larger. (Raw onset magnitude is weaker: a conga has some D4 attack too.)
        let f0 = crate::dsp::key_freq(key); // D4
        let tail = |out: &[f32]| {
            let m = left(out);
            let a = sr as usize; // 1.0 s
            let b = (1.4 * sr as f64) as usize;
            crate::testutil::mag_at(&m[a..b], sr, f0)
        };
        assert!(
            tail(&xg13) < 0.1 * tail(&organ),
            "drum tail at D4 ({}) must be far below the sustained organ ({})",
            tail(&xg13),
            tail(&organ)
        );
    }

    /// GS "Use for Rhythm Part" routes a non-drum channel to the drum path — the GS
    /// counterpart of the XG test above. A GS rhythm hit on ch11 is byte-identical to
    /// the same hit on ch9 (single hit; the parallel drum path mirrors ch9's
    /// association, and a fresh ch11 strip shares ch9's default gain/pan), and differs
    /// from the same note played as a melodic voice.
    #[test]
    fn gs_rhythm_part_routes_channel_to_drums() {
        let sr = 44100.0;
        let opt = test_opts(sr);
        let key = 62u8;
        let render_ev = |ev: Vec<(f64, EvKind)>| render(&test_song(ev, 1.5), &opt).0;

        let gs = render_ev(vec![
            (0.0, EvKind::DrumMode { ch: 11, on: true }), // GS: ch11 is a rhythm part
            (
                0.05,
                EvKind::NoteOn {
                    ch: 11,
                    key,
                    vel: 100,
                },
            ),
        ]);
        let drum9 = render_ev(vec![(
            0.05,
            EvKind::NoteOn {
                ch: 9,
                key,
                vel: 100,
            },
        )]);
        let melodic = render_ev(vec![
            (0.0, EvKind::Prog { ch: 11, prog: 0 }), // grand piano, no rhythm-part flag
            (
                0.05,
                EvKind::NoteOn {
                    ch: 11,
                    key,
                    vel: 100,
                },
            ),
        ]);

        assert_eq!(
            gs, drum9,
            "GS rhythm part (ch11) must render as a drum, identical to ch9"
        );
        assert_ne!(
            gs, melodic,
            "GS rhythm part must not render as a melodic voice"
        );
    }

    /// The GS flag is separate from the XG flag: an ordinary `CC0=0` bank select (which
    /// a real GS rhythm part still sends) must NOT clear it, and a GS Reset MUST. These
    /// guard the two-flag decision and the reset handling.
    #[test]
    fn gs_rhythm_survives_bank_select_but_not_reset() {
        let sr = 44100.0;
        let opt = test_opts(sr);
        let key = 62u8;
        let render_ev = |ev: Vec<(f64, EvKind)>| render(&test_song(ev, 1.5), &opt).0;

        let drum9 = render_ev(vec![(
            0.05,
            EvKind::NoteOn {
                ch: 9,
                key,
                vel: 100,
            },
        )]);
        let melodic = render_ev(vec![
            (0.0, EvKind::Prog { ch: 11, prog: 0 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 11,
                    key,
                    vel: 100,
                },
            ),
        ]);

        // GS rhythm part, then the ordinary bank-select + program a real GS file sends
        // to pick the kit — still drums (gs_drum is immune to CC0, unlike xg_drum).
        let after_bank = render_ev(vec![
            (0.0, EvKind::DrumMode { ch: 11, on: true }),
            (
                0.01,
                EvKind::Cc {
                    ch: 11,
                    num: 0,
                    val: 0,
                },
            ), // bank select MSB 0
            (
                0.02,
                EvKind::Cc {
                    ch: 11,
                    num: 32,
                    val: 0,
                },
            ), // bank select LSB 0
            (0.03, EvKind::Prog { ch: 11, prog: 0 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 11,
                    key,
                    vel: 100,
                },
            ),
        ]);
        assert_eq!(
            after_bank, drum9,
            "GS rhythm part must survive CC0=0 + PC (proves gs_drum is not the CC0-driven xg_drum)"
        );

        // GS Reset reverts the part mode → the same note is melodic again.
        let after_reset = render_ev(vec![
            (0.0, EvKind::DrumMode { ch: 11, on: true }),
            (0.02, EvKind::GsReset),
            (0.03, EvKind::Prog { ch: 11, prog: 0 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 11,
                    key,
                    vel: 100,
                },
            ),
        ]);
        assert_eq!(
            after_reset, melodic,
            "GS Reset must clear the rhythm part (renders melodic, identical to a plain ch11 note)"
        );
    }

    /// Oracle (D10d, kit internal balance): the kit voicing was cymbal-heavy and
    /// hat-light — measured on the Hey Jude reference the hi-hats sat ~19 dB under
    /// the kick and the crash only ~2 dB under, so a standard beat lost its hats
    /// and the cymbals dominated. The `kit_balance` trim corrects it. This locks in
    /// the corrected balance on the DEFAULT (sampled) kit: the hi-hats must be
    /// audible against the kick (not buried), the crash must sit below the kick (an
    /// accent, not the loudest voice), and the snare/toms must be forward (near the
    /// kick). Isolated equal-velocity hits, dry (wet=0), so it measures the
    /// voices + trim, not the room; each level is taken relative to the kick, so
    /// the shape survives the renderer's normalization.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn kit_internal_balance_hats_audible_crash_an_accent() {
        let sr = 44100.0;
        let mut opt = test_opts(sr);
        opt.samples = true;
        // one hit each, 1 s apart: kick, snare, closed hat, crash, tom.
        let hits = [
            (0.0, 36, 100),
            (1.0, 38, 100),
            (2.0, 42, 100),
            (3.0, 49, 100),
            (4.0, 45, 100),
        ];
        let out = render(&drum_song(&hits, 5.0, &[]), &opt).0;
        let mono = left(&out);
        let db = |t: f64| {
            let a = (t * sr as f64) as usize;
            let b = ((t + 0.4) * sr as f64) as usize;
            20.0 * rms(&mono[a..b.min(mono.len())]).max(1e-9).log10()
        };
        let (kick, snare, hat, crash, tom) = (db(0.0), db(1.0), db(2.0), db(3.0), db(4.0));
        // Measured margins at the shipped trim: hat-kick ~-11.7, crash-kick ~-11.9,
        // snare-kick ~-6.2, tom-kick ~-4.4 dB. Reverting the hat trim drops hat-kick
        // to ~-24.8 and trips the first assert (fail-first verified).
        // hi-hats must be audible against the kick (they were ~19-26 dB under before)
        assert!(
            hat - kick > -16.0,
            "hi-hats buried vs kick: {:.1} dB",
            hat - kick
        );
        // crash sits below the kick — an accent, not the loudest voice
        assert!(crash < kick, "crash not below kick: {:.1} dB", crash - kick);
        // snare and toms are forward (within ~9 dB of the kick)
        assert!(
            snare - kick > -9.0,
            "snare too far back: {:.1} dB",
            snare - kick
        );
        assert!(tom - kick > -9.0, "toms too far back: {:.1} dB", tom - kick);
    }

    #[cfg(feature = "embedded-samples")]
    #[test]
    fn samples_option_reaches_channel_10_drums() {
        let sr = 44100.0;
        let song = drum_prog_song(None);
        let off = render(&song, &test_opts(sr)).0;
        let mut on_opts = test_opts(sr);
        on_opts.samples = true;
        let on = render(&song, &on_opts).0;
        assert_ne!(off, on, "samples=true did not alter channel-10 drums");
        assert!(
            on.iter().all(|x| x.is_finite()),
            "sampled drum render produced non-finite samples"
        );
        let db = 20.0 * (rms(&on) / rms(&off).max(1e-12)).log10();
        assert!(
            db.abs() <= 6.0,
            "samples changed drum render level by {db:+.2} dB"
        );
    }

    /// Oracle 32b (D9, §5.3): the kit images across the stereo field —
    /// decorrelated L/R with real placement — without any Haas trickery
    /// (mono sum loses < 1 dB), and kick/snare stay centred.
    #[test]
    fn kit_images_in_stereo_without_mono_loss() {
        let sr = 44100.0;
        let mut hits = Vec::new();
        for i in 0..8 {
            hits.push((i as f64 * 0.25, 42u8, 90u8)); // hats left
        }
        // ride right — matched in density and level to the (now hat-forward) kit so
        // the pattern actually exercises the L/R spread. Since the D10d rebalance
        // trims the ride and lifts the hats, a sparse quiet ride would let the
        // dominant left-panned hats correlate the field; a present ride keeps both
        // sides live (the point of the oracle), while a real mono collapse would
        // still peg corr near 1.0.
        for i in 0..8 {
            hits.push((0.125 + i as f64 * 0.25, 51, 120)); // ride right
        }
        let song = drum_song(&hits, 2.2, &[]);
        let out = render(&song, &test_opts(sr)).0;
        let (l, r) = (left(&out), right(&out));
        let corr = crate::testutil::inter_corr(&l, &r);
        assert!(
            corr < 0.93,
            "kit stereo field collapsed toward a mono point source: corr {corr}"
        );
        // placement: hats-only song leans left, and the mono sum holds up
        let hat_song = drum_song(
            &(0..8)
                .map(|i| (i as f64 * 0.25, 42, 90))
                .collect::<Vec<_>>(),
            2.2,
            &[],
        );
        let hout = render(&hat_song, &test_opts(sr)).0;
        let (hl, hr) = (left(&hout), right(&hout));
        assert!(
            rms(&hl) > 1.2 * rms(&hr),
            "hats not left: L {} R {}",
            rms(&hl),
            rms(&hr)
        );
        let mono: Vec<f32> = hl.iter().zip(&hr).map(|(a, b)| 0.5 * (a + b)).collect();
        let mid = ((rms(&hl).powi(2) + rms(&hr).powi(2)) / 2.0).sqrt();
        let loss_db = 20.0 * (rms(&mono) / mid.max(1e-12)).log10();
        assert!(loss_db > -1.0, "mono collapse: {loss_db:.2} dB");
        // kick/snare centred
        let kick_song = drum_song(&[(0.05, 36, 110), (0.55, 38, 105)], 1.2, &[]);
        let kout = render(&kick_song, &test_opts(sr)).0;
        let (kl, kr) = (left(&kout), right(&kout));
        let bal = rms(&kl) / rms(&kr).max(1e-12);
        assert!((0.95..=1.05).contains(&bal), "kick/snare off centre: {bal}");
    }

    /// Oracle 42 (D9 strip parity — the review's converged CRITICAL):
    /// CC7 silences the kit, CC74 darkens it, CC91 still reaches the hall,
    /// and authored CC10 shifts the whole image.
    #[test]
    fn drum_strip_parity_preserved() {
        let sr = 44100.0;
        let hits: Vec<(f64, u8, u8)> = (0..6).map(|i| (0.05 + i as f64 * 0.2, 42, 100)).collect();
        // CC7 = 0 silences
        let silent = render(&drum_song(&hits, 1.6, &[(7, 0)]), &test_opts(sr)).0;
        assert!(
            rms(&silent) < 1e-6,
            "CC7=0 drums still audible: {}",
            rms(&silent)
        );
        // CC74 = 20 darkens
        let plain = render(&drum_song(&hits, 1.6, &[]), &test_opts(sr)).0;
        let dark = render(&drum_song(&hits, 1.6, &[(74, 20)]), &test_opts(sr)).0;
        let cent = |s: &[f32]| {
            let m: Vec<f32> = s.chunks_exact(2).map(|p| 0.5 * (p[0] + p[1])).collect();
            crate::testutil::centroid(&m, sr)
        };
        assert!(
            cent(&dark) < 0.8 * cent(&plain),
            "ch-9 wah dead: dark {} vs plain {}",
            cent(&dark),
            cent(&plain)
        );
        // CC91 still reaches the hall: wet render, tail after the last hit
        let wet_opts = || Options {
            wet: 0.32,
            ..test_opts(sr)
        };
        let kick = |cc91: u8| {
            let song = drum_song(&[(0.05, 36, 115)], 2.0, &[(91, cc91)]);
            render(&song, &wet_opts()).0
        };
        let tail =
            |s: &[f32], t0: f32, t1: f32| rms(&left(s)[(t0 * sr) as usize..(t1 * sr) as usize]);
        assert!(
            tail(&kick(127), 1.2, 1.9) > 2.0 * tail(&kick(0), 1.2, 1.9),
            "drum hall send lost"
        );
        // authored CC10 shifts the kit image (hats table-left → pushed right)
        let panned = render(&drum_song(&hits, 1.6, &[(10, 127)]), &test_opts(sr)).0;
        let (pl, pr) = (left(&panned), right(&panned));
        assert!(
            rms(&pr) > 1.2 * rms(&pl),
            "CC10 ignored on ch 9: L {} R {}",
            rms(&pl),
            rms(&pr)
        );
    }

    #[test]
    fn cc121_resets_controllers_but_preserves_mix_state() {
        let sr = 44100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        });
        core.handle_event(EvKind::Prog { ch: 0, prog: 30 });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 7,
            val: 80,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 10,
            val: 20,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 64,
            val: 127,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 1,
            val: 100,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 74,
            val: 20,
        });
        // Effect sends, an RPN-set bend range, and a portamento TIME. RP-015
        // preserves every one of these across CC121 (MM-BUG-KILN-00033).
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 93,
            val: 100,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 94,
            val: 40,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 5,
            val: 90,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 101,
            val: 0,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 100,
            val: 0,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 6,
            val: 12,
        });
        let porta_time_before = core.strips[0].porta_time;
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 121,
            val: 0,
        });

        // CC7/CC10 now prime at block rate (prime-on-first-block), so advance one
        // block to snap volume/pan to their authored targets. CC121 does not reset
        // volume or pan (correct GM semantics), so the block preserves them.
        let mut sink = [0f32; BLOCK * 2];
        core.render_block_add(BLOCK, &mut sink);

        let s = &core.strips[0];

        // --- RP-015 RESETS these ---
        assert!(!s.sustain, "CC64 must reset");
        assert!(!s.mod_authored, "CC1 must reset");
        assert_eq!(s.expr, 1.0, "CC11 must reset to full");
        assert_eq!(s.expr_target, 1.0);
        assert_eq!(s.rpn_msb, 127, "RPN selector must park at Null");
        assert_eq!(s.rpn_lsb, 127);
        assert_eq!(s.bend_wheel, 0.0, "pitch bend must return to centre");

        // --- RP-015 PRESERVES these ---
        assert!((s.volume - (80.0f32 / 127.0).powi(2)).abs() < 1e-6);
        assert!((s.pan - 20.0 / 127.0).abs() < 1e-6);
        assert!(
            s.drive.is_some(),
            "program-derived drive should be restored"
        );
        // Effect sends are persistent channel state, not program state.
        assert_eq!(
            s.chorus_send,
            100.0 / 127.0,
            "CC121 discarded the authored CC93 chorus send"
        );
        assert_eq!(
            s.delay_send,
            40.0 / 127.0,
            "CC121 discarded the authored CC94 delay send"
        );
        assert!(s.chorus_authored && s.delay_authored);
        // CC121 nulls the RPN SELECTOR; it does not revert what the selector set.
        assert_eq!(
            s.bend_range, 12.0,
            "CC121 reverted the RPN-set pitch-bend range"
        );
        assert_eq!(s.fine, 1.0);
        // Bend is centred, but centre is scaled by the preserved fine tuning.
        assert_eq!(s.bend, s.fine);
        // CC70-79 sound controllers survive, and so must the filters realising them.
        assert!(
            s.wah.is_some(),
            "CC121 tore down the CC74 filter — CC74 is a preserved sound controller"
        );
        assert!(
            s.cutoff_target < WAH_MAX_HZ,
            "CC121 reverted the authored CC74 cutoff"
        );
        assert_eq!(s.res_target, WAH_Q, "CC71 was never authored here");
        // Only the CC65 portamento SWITCH resets; the CC5 TIME is setup state.
        assert!(!s.porta_on, "CC65 must reset");
        assert_eq!(
            s.porta_time, porta_time_before,
            "CC121 reverted the authored CC5 portamento time"
        );
    }

    /// MM-BUG-KILN-00035: GM System On is a full synthesis/channel reset, but
    /// public diagnostics still describe the complete offline render.
    #[test]
    fn gm_system_on_restores_fresh_state_and_preserves_stats() {
        let mut core = slew_test_core(44_100.0);
        let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };
        for kind in [
            EvKind::Prog { ch: 0, prog: 30 },
            cc(7, 80),
            cc(101, 0),
            cc(100, 0),
            cc(6, 12),
            EvKind::DrumMode { ch: 0, on: true },
            EvKind::XgEffectParam {
                addr_lo: 0x40,
                data: [0x4B, 0x11],
                len: 2,
            },
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100,
            },
            EvKind::NoteOn {
                ch: 1,
                key: 64,
                vel: 100,
            },
        ] {
            core.handle_event(kind);
        }
        let mut audio = [0.0; BLOCK * 2];
        core.render_block_add(BLOCK, &mut audio);
        let before = core.stats();
        assert_eq!(before.voices_spawned, 2);
        assert_eq!(before.max_polyphony, 2);
        assert!(before.peak > 0.0);
        assert_eq!(core.voice_seed_index, 2);
        assert_eq!(core.strips[0].program, 30);
        assert_eq!(core.strips[0].bend_range, 12.0);
        assert!(core.strips[0].gs_drum);
        assert_eq!(core.xg.var_type_msb, 0x4B);

        core.handle_event(EvKind::GmReset);

        let strip = &core.strips[0];
        assert_eq!(core.active_voice_count(), 0);
        assert_eq!(strip.program, 0);
        assert_eq!(strip.volume, (100.0f32 / 127.0).powi(2));
        assert!(!strip.volume_authored);
        assert_eq!(strip.bend_range, 2.0);
        assert_eq!((strip.rpn_msb, strip.rpn_lsb), (127, 127));
        assert!(!strip.gs_drum);
        assert_eq!(core.xg.var_type_msb, 0);
        assert_eq!(core.xg.var_part, 127);
        assert_eq!(core.stats(), before);
        assert_eq!(core.voice_seed_index, 0);
    }

    /// MM-BUG-KILN-00034: an NRPN select (CC98/99) must invalidate the RPN latch,
    /// so a later Data-Entry cannot corrupt the RPN-set pitch-bend range. Without
    /// the guard, CC6 after an NRPN select is still interpreted against the
    /// latched RPN 0,0 (a common GS/XG sequence: set bend range, then use an NRPN
    /// without an RPN-Null).
    #[test]
    fn nrpn_select_does_not_corrupt_the_rpn_bend_range() {
        let sr = 44100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        });
        let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };

        // Select RPN 0,0 and set the pitch-bend range to 2 semitones.
        core.handle_event(cc(101, 0)); // RPN MSB = 0
        core.handle_event(cc(100, 0)); // RPN LSB = 0
        core.handle_event(cc(6, 2)); // data entry → bend range 2
        assert_eq!(core.strips[0].bend_range, 2.0);

        // Select an NRPN (no intervening RPN-Null) then send Data-Entry. The NRPN
        // select must have parked the RPN latch, so this CC6 is inert — it must
        // NOT be re-interpreted as the bend range (which would clamp to 24).
        core.handle_event(cc(99, 1)); // NRPN MSB
        core.handle_event(cc(98, 8)); // NRPN LSB
        core.handle_event(cc(6, 80)); // would set bend range 24 without the guard

        assert_eq!(
            core.strips[0].bend_range, 2.0,
            "NRPN select failed to invalidate the RPN latch — bend range corrupted"
        );
        // The latch sits at null, so a genuine RPN can still be re-selected later.
        assert_eq!(core.strips[0].rpn_msb, 127);
        assert_eq!(core.strips[0].rpn_lsb, 127);
    }

    /// MM-BUG-KILN-00033: effect sends are persistent CHANNEL state (GM / RP-015),
    /// so a Program Change must not discard a send the file authored with CC93 /
    /// CC94. The program's `fx_profile` is a default that fills an UNauthored send
    /// only — exactly the rule the CC0 bank arm already followed.
    #[test]
    fn program_change_preserves_authored_effect_sends() {
        let sr = 44100.0;
        let core_opts = || CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        };

        // A channel that AUTHORS its sends keeps them across a Program Change.
        let mut core = EngineCore::new(core_opts());
        let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };
        core.handle_event(EvKind::Prog { ch: 0, prog: 30 });
        core.handle_event(cc(93, 100));
        core.handle_event(cc(94, 20));
        let (authored_cho, authored_del) = (100.0 / 127.0, 20.0 / 127.0);
        assert_eq!(core.strips[0].chorus_send, authored_cho);
        assert_eq!(core.strips[0].delay_send, authored_del);

        // Program 48 (string ensemble) profiles to (0.35, 0.0) — it must NOT
        // overwrite the authored values, and the authored flags must survive:
        // the mix reads them to pick the legacy/cathedral bus feeds.
        core.handle_event(EvKind::Prog { ch: 0, prog: 48 });
        assert_eq!(
            core.strips[0].chorus_send, authored_cho,
            "Program Change discarded the authored CC93 chorus send"
        );
        assert_eq!(
            core.strips[0].delay_send, authored_del,
            "Program Change discarded the authored CC94 delay send"
        );
        assert!(core.strips[0].chorus_authored);
        assert!(core.strips[0].delay_authored);

        // A channel that authors NOTHING still tracks the program's profile — the
        // default path is unchanged, so silent files render exactly as before.
        let mut bare = EngineCore::new(core_opts());
        bare.handle_event(EvKind::Prog { ch: 0, prog: 30 });
        assert_eq!(bare.strips[0].chorus_send, 0.10);
        assert_eq!(bare.strips[0].delay_send, 0.30);
        bare.handle_event(EvKind::Prog { ch: 0, prog: 48 });
        assert_eq!(bare.strips[0].chorus_send, 0.35);
        assert_eq!(bare.strips[0].delay_send, 0.0);

        // Authoring only ONE of the pair leaves the other on the program default.
        let mut half = EngineCore::new(core_opts());
        half.handle_event(EvKind::Cc {
            ch: 0,
            num: 93,
            val: 64,
        });
        half.handle_event(EvKind::Prog { ch: 0, prog: 48 });
        assert_eq!(half.strips[0].chorus_send, 64.0 / 127.0);
        assert_eq!(half.strips[0].delay_send, 0.0);
    }

    // ---- MM-BUG-KILN-00011: CC7 volume / CC10 pan controller slew ----

    fn slew_test_core(sr: f32) -> EngineCore {
        EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        })
    }

    fn advance_blocks(core: &mut EngineCore, blocks: usize) {
        let mut sink = [0f32; BLOCK * 2];
        for _ in 0..blocks {
            core.render_block_add(BLOCK, &mut sink);
        }
    }

    /// AC1 (confinement) + AC3 (prime): a channel that never authors CC7/CC10 keeps
    /// its defaults byte-for-byte across many blocks; authoring latches but does not
    /// change the current value until a block primes it.
    #[test]
    fn cc7_cc10_unauthored_channel_is_unchanged() {
        let sr = 44100.0;
        let default_vol = (100.0f32 / 127.0).powi(2);
        let mut core = slew_test_core(sr);
        advance_blocks(&mut core, 50);
        let s = &core.strips[0];
        assert_eq!(s.volume, default_vol);
        assert_eq!(s.pan, 0.5);
        assert_eq!(s.haas_delay, 0.0);
        assert!(!s.volume_authored && !s.pan_authored);
        assert!(!s.volume_primed && !s.pan_primed);
    }

    /// AC3: the first block after authoring snaps volume/pan to the *last* value
    /// authored before that block (MIDI last-write-wins for a same-tick burst), with
    /// no glide from the default; haas_delay derives from the snapped pan.
    #[test]
    fn cc7_cc10_prime_on_first_block_is_last_write_wins() {
        let sr = 44100.0;
        let default_vol = (100.0f32 / 127.0).powi(2);
        let mut core = slew_test_core(sr);
        // ch0: a single set at t0 (volume 80, pan 96).
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 7,
            val: 80,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 10,
            val: 96,
        });
        // ch1: a same-tick pan burst 54 then 64 — the last write must win.
        core.handle_event(EvKind::Cc {
            ch: 1,
            num: 10,
            val: 54,
        });
        core.handle_event(EvKind::Cc {
            ch: 1,
            num: 10,
            val: 64,
        });

        // Authored but not yet primed: current values are still the defaults.
        assert!(core.strips[0].volume_authored && !core.strips[0].volume_primed);
        assert_eq!(core.strips[0].volume, default_vol);
        assert_eq!(core.strips[0].pan, 0.5);

        advance_blocks(&mut core, 1);

        // Snapped to the authored targets (no glide from the default).
        assert!((core.strips[0].volume - (80.0f32 / 127.0).powi(2)).abs() < 1e-9);
        assert!((core.strips[0].pan - 96.0 / 127.0).abs() < 1e-9);
        assert!(core.strips[0].volume_primed && core.strips[0].pan_primed);
        // Same-tick burst resolved to the LAST value (64/127), not the first (54/127).
        assert!(
            (core.strips[1].pan - 64.0 / 127.0).abs() < 1e-9,
            "same-tick burst must snap to the last authored value; got {}",
            core.strips[1].pan
        );
        // haas_delay follows the snapped pan.
        let want_haas = 0.005 * sr * (96.0f32 / 127.0 - 0.5).abs() * 2.0;
        assert!((core.strips[0].haas_delay - want_haas).abs() < 1e-6);
    }

    /// AC2 + AC6: a post-prime CC7/CC10 change slews as the CC11 one-pole (exact
    /// step), moving a fraction per block, monotonically, without overshoot, and
    /// converging to the target. haas_delay tracks the slewed pan.
    #[test]
    fn cc7_cc10_post_prime_change_slews_one_pole_monotone() {
        let sr = 44100.0;
        let smooth = 1.0 - (-(BLOCK as f32) / (0.03 * sr)).exp();
        let mut core = slew_test_core(sr);
        // Prime: volume to full, pan hard-left.
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 7,
            val: 127,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 10,
            val: 0,
        });
        advance_blocks(&mut core, 1);
        assert!(
            core.strips[0].pan.abs() < 1e-9,
            "pan primed to hard-left (0)"
        );
        assert!(
            (core.strips[0].volume - 1.0).abs() < 1e-9,
            "volume primed to full"
        );

        // Post-prime change: volume -> 0 (fade), pan -> hard-right (sweep).
        let v0 = core.strips[0].volume; // 1.0
        let p0 = core.strips[0].pan; // 0.0
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 7,
            val: 0,
        });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 10,
            val: 127,
        });
        advance_blocks(&mut core, 1);

        // Exact one-pole step, not a jump.
        let want_v = v0 + smooth * (0.0 - v0);
        let want_p = p0 + smooth * (1.0 - p0);
        assert!(
            (core.strips[0].volume - want_v).abs() < 1e-6,
            "volume one-pole step"
        );
        assert!(
            (core.strips[0].pan - want_p).abs() < 1e-6,
            "pan one-pole step"
        );
        assert!(core.strips[0].volume < v0 && core.strips[0].volume > 0.0);
        assert!(core.strips[0].pan > p0 && core.strips[0].pan < 1.0);

        // Monotone, no overshoot, converges.
        let mut prev_v = core.strips[0].volume;
        let mut prev_p = core.strips[0].pan;
        for _ in 0..500 {
            advance_blocks(&mut core, 1);
            let (v, p) = (core.strips[0].volume, core.strips[0].pan);
            assert!(
                v <= prev_v + 1e-7 && v >= -1e-6,
                "volume monotone down, no undershoot"
            );
            assert!(
                p >= prev_p - 1e-7 && p <= 1.0 + 1e-6,
                "pan monotone up, no overshoot"
            );
            prev_v = v;
            prev_p = p;
        }
        assert!(core.strips[0].volume.abs() < 1e-3, "volume converges to 0");
        assert!(
            (core.strips[0].pan - 1.0).abs() < 1e-3,
            "pan converges to 1"
        );
        // haas tracks the slewed pan each block.
        let want_haas = 0.005 * sr * (core.strips[0].pan - 0.5).abs() * 2.0;
        assert!((core.strips[0].haas_delay - want_haas).abs() < 1e-6);
    }

    /// AC7: during a realistic incremental auto-pan the Haas tap advances in small
    /// per-block steps (no click), unlike the old instant retune which flipped the
    /// whole ~220-sample delay to the other channel at each CC event.
    #[test]
    fn cc10_haas_tap_advances_smoothly_not_in_jumps() {
        let sr = 44100.0;
        let full_range = 0.005 * sr; // ~220 samples: hard-pan Haas delay
        let mut core = slew_test_core(sr);
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 10,
            val: 0,
        });
        advance_blocks(&mut core, 1); // prime hard-left

        // Fast auto-pan: bump the target one CC unit every 4 blocks, 0 -> 127.
        let mut prev = core.strips[0].haas_delay;
        let mut max_block_step = 0.0f32;
        let mut next_v = 1u8;
        for block in 0..700usize {
            if block % 4 == 0 && next_v <= 127 {
                core.handle_event(EvKind::Cc {
                    ch: 0,
                    num: 10,
                    val: next_v,
                });
                next_v += 1;
            }
            advance_blocks(&mut core, 1);
            let h = core.strips[0].haas_delay;
            max_block_step = max_block_step.max((h - prev).abs());
            prev = h;
        }
        // A smooth tap moves well under a sample per block here; the old instant
        // side-flip moved the full ~220-sample delay at once. Bound generously to
        // stay robust while still catching a regression to jump behaviour.
        assert!(
            max_block_step < 0.02 * full_range,
            "Haas tap should advance smoothly: max per-block step {:.3} samples (range {:.1})",
            max_block_step,
            full_range
        );
    }

    /// Oracle 32a (D10, §5.2/§5.3 A/B): the drum room adds early energy a
    /// room-less render lacks, and non-drum channels get no room at all.
    #[test]
    fn drum_room_early_reflections() {
        let sr = 44100.0;
        let song = drum_song(&[(0.05, 36, 115)], 1.0, &[(91, 0)]);
        let opts = Options {
            wet: 0.32,
            ..test_opts(sr)
        };
        let with = render_buses(&song, &opts, true, true, true).0;
        let without = render_buses(&song, &opts, true, false, true).0;
        // the room's first reflections: ~5-30 ms after the kick onset
        let win = |s: &[f32]| left(s)[(0.055 * sr) as usize..(0.085 * sr) as usize].to_vec();
        let diff: Vec<f32> = win(&with)
            .iter()
            .zip(win(&without))
            .map(|(a, b)| a - b)
            .collect();
        assert!(rms(&diff) > 1e-4, "no early room energy: {}", rms(&diff));
        // a piano note gets no room send
        let piano = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 0 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 60,
                        vel: 100,
                    },
                ),
                (0.8, EvKind::NoteOff { ch: 0, key: 60 }),
            ],
            1.2,
        );
        let a = render_buses(&piano, &opts, true, true, true).0;
        let b = render_buses(&piano, &opts, true, false, true).0;
        assert!(
            a.iter().zip(&b).all(|(x, y)| x.to_bits() == y.to_bits()),
            "non-ch9 audio leaked into the drum room"
        );
    }

    /// Oracle 19 (G5, §5.3 difference signal): the guitar-sympathetic bus
    /// rings the open strings under an acoustic guitar, and stays silent
    /// for the driven electric.
    #[test]
    fn guitar_sympathetic_rings_open_strings() {
        let sr = 44100.0;
        let strum = |prog: u8| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog })];
            for (i, &key) in [40u8, 45, 50, 55, 59, 64].iter().enumerate() {
                let t = i as f64 * 0.012;
                ev.push((
                    t,
                    EvKind::NoteOn {
                        ch: 0,
                        key,
                        vel: 105,
                    },
                ));
                ev.push((1.2, EvKind::NoteOff { ch: 0, key }));
            }
            test_song(ev, 1.6)
        };
        let opts = test_opts(sr);
        let with = render_buses(&strum(24), &opts, true, true, true).0;
        let without = render_buses(&strum(24), &opts, false, true, true).0;
        let d: Vec<f32> = left(&with)
            .iter()
            .zip(left(&without))
            .map(|(a, b)| a - b)
            .collect();
        let tail = &d[(0.3 * sr) as usize..(0.8 * sr) as usize];
        let ring: f32 = [82.41f32, 110.0, 146.83]
            .iter()
            .map(|&f| crate::testutil::band_rms(tail, sr, f, 8.0))
            .sum();
        assert!(ring > 1e-5, "sympathetic strings silent: {ring}");
        // prog 30 (driven electric) must not feed the bus at all
        let e_with = render_buses(&strum(30), &opts, true, true, true).0;
        let e_without = render_buses(&strum(30), &opts, false, true, true).0;
        assert!(
            e_with
                .iter()
                .zip(&e_without)
                .all(|(x, y)| x.to_bits() == y.to_bits()),
            "electric guitar leaked into the sympathetic bus"
        );
    }

    /// Tarab oracle (GM 104, v0.16, §5.3 difference signal): the sitar's
    /// thirteen sympathetic strings ring under a sitar note — the bus-on
    /// minus bus-off difference is exactly the tarab return, comb-shaped
    /// around the resonating strings — and a banjo (or anything else)
    /// leaves the bus bit-identically silent.
    #[test]
    fn sitar_tarab_strings_ring_sympathetically() {
        let sr = 44100.0;
        let song = |prog: u8| {
            test_song(
                vec![
                    (0.0, EvKind::Prog { ch: 0, prog }),
                    (
                        0.02,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 62,
                            vel: 105,
                        },
                    ),
                    (1.0, EvKind::NoteOff { ch: 0, key: 62 }),
                ],
                1.8,
            )
        };
        let opts = test_opts(sr);
        let with = render_buses(&song(104), &opts, true, true, true).0;
        let without = render_buses(&song(104), &opts, true, true, false).0;
        let d: Vec<f32> = left(&with)
            .iter()
            .zip(left(&without))
            .map(|(a, b)| a - b)
            .collect();
        let (w0, w1) = ((0.20 * sr) as usize, (1.20 * sr) as usize);
        let ring = rms(&d[w0..w1]);
        let dry = rms(&left(&without)[w0..w1]);
        // the return is a real halo relative to the dry sitar, not dust
        assert!(
            ring > 1e-3 * dry,
            "tarab strings silent: return {ring} vs dry {dry}"
        );
        // …and it is comb-shaped: the D4 tarab string (the played pitch)
        // rings far above a probe BELOW the whole bank (261.63 Hz bottom
        // string; probes between combs are useless — thirteen strings'
        // overtone series blanket everything above)
        let played = crate::testutil::band_rms(&d[w0..w1], sr, 293.66, 8.0);
        let probe = crate::testutil::band_rms(&d[w0..w1], sr, 225.0, 8.0);
        assert!(
            played > 2.0 * probe,
            "tarab return not comb-shaped: D4 {played} vs 225 Hz {probe}"
        );
        // a banjo playing the same note must not feed the bus at all
        let b_with = render_buses(&song(105), &opts, true, true, true).0;
        let b_without = render_buses(&song(105), &opts, true, true, false).0;
        assert!(
            b_with
                .iter()
                .zip(&b_without)
                .all(|(x, y)| x.to_bits() == y.to_bits()),
            "banjo leaked into the tarab bus"
        );
    }

    /// Oracle 26 (D6, engine half): a closed-hat strike chokes the ringing
    /// open hat in the full render path.
    #[test]
    fn closed_hat_chokes_open_in_engine() {
        let sr = 44100.0;
        let open_only = drum_song(&[(0.05, 46, 110)], 1.0, &[]);
        let choked = drum_song(&[(0.05, 46, 110), (0.25, 42, 90)], 1.0, &[]);
        let a = render(&open_only, &test_opts(sr)).0;
        let b = render(&choked, &test_opts(sr)).0;
        let w = |s: &[f32]| rms(&left(s)[(0.32 * sr) as usize..(0.45 * sr) as usize]);
        assert!(
            w(&b) < 0.3 * w(&a),
            "open hat survived the choke: {} vs {}",
            w(&b),
            w(&a)
        );
    }

    /// Normalized cross-correlation of two equal windows, max |r| over
    /// ±`max_lag` samples — the anti-machine-gun similarity measure.
    fn ncc_max(a: &[f32], b: &[f32], max_lag: usize) -> f32 {
        fn ncc_at(a: &[f32], b: &[f32]) -> f32 {
            let (mut sab, mut saa, mut sbb) = (0f64, 0f64, 0f64);
            for (&x, &y) in a.iter().zip(b) {
                sab += (x * y) as f64;
                saa += (x * x) as f64;
                sbb += (y * y) as f64;
            }
            (sab / (saa.sqrt() * sbb.sqrt()).max(1e-30)) as f32
        }
        let n = a.len().min(b.len()) - max_lag;
        let mut best = 0f32;
        for lag in 0..=max_lag {
            best = best.max(ncc_at(&a[..n], &b[lag..lag + n]).abs());
            best = best.max(ncc_at(&a[lag..lag + n], &b[..n]).abs());
        }
        best
    }

    /// First sample above 5% of the window's peak — a hit's true onset,
    /// undoing the engine's block-quantized voice spawn.
    fn hit_onset(w: &[f32]) -> usize {
        let peak = w.iter().fold(0f32, |m, &x| m.max(x.abs()));
        w.iter().position(|&x| x.abs() > 0.05 * peak).unwrap_or(0)
    }

    /// Rate-warp-searching NCC: max correlation over playback-rate ratios
    /// ±5.5% (the jitter spread of two hits), warping `b` from its detected
    /// onset and comparing a 40 ms window that starts 30 ms in — past the
    /// stick transient every take of one cymbal shares, into the
    /// take-specific wash. A rate-jittered copy of the SAME take re-aligns
    /// near its true ratio and reads high; a different take stays low at
    /// every warp. Plain NCC cannot make this distinction — ±2.5% rate
    /// jitter alone already decorrelates the window (measured ~0.07-0.19 for
    /// the same take), which would let a seed-modulo repeat sail through.
    fn warp_ncc(a: &[f32], b: &[f32]) -> f32 {
        let (a, b) = (&a[hit_onset(a)..], &b[hit_onset(b)..]);
        let w0 = 1323usize; // window start: 30 ms
        let n = 1764usize; // window length: 40 ms
        let lag = 48usize; // residual onset-estimate error
        let steps = 220;
        // correlate FIRST DIFFERENCES: differencing tilts the measure toward
        // the high-frequency sizzle that is take-specific, away from the low
        // plate modes every take of one cymbal shares
        let da: Vec<f32> = a[w0..w0 + n + lag + 1]
            .windows(2)
            .map(|p| p[1] - p[0])
            .collect();
        let mut warped = vec![0f32; w0 + n + lag + 1];
        let mut best = 0f32;
        for s in 0..=steps {
            let r = 0.945 + 0.11 * s as f32 / steps as f32;
            for (i, w) in warped.iter_mut().enumerate() {
                let x = i as f32 * r;
                let j = x as usize;
                let frac = x - j as f32;
                *w = b[j] * (1.0 - frac) + b[j + 1] * frac;
            }
            let dw: Vec<f32> = warped[w0..].windows(2).map(|p| p[1] - p[0]).collect();
            best = best.max(ncc_max(&da, &dw, lag));
        }
        best
    }

    /// THE anti-machine-gun oracle (Stage C headline). Eight ride hits of the
    /// SAME key through the full engine path, so the per-key round-robin
    /// counter drives the take and the note seed drives the micro-variation:
    ///
    ///  * consecutive hits must be genuinely different TAKES: their
    ///    warp-searched NCC stays low. Seed-modulo rr picking repeats a take
    ///    back-to-back, the warp search re-aligns it through the rate jitter,
    ///    and this clause goes red (fail-first proven);
    ///  * NO pair of the eight may correlate like a clone (plain NCC ~1.0)
    ///    and no two hits may be bit-identical: dropping the rate/gain
    ///    micro-variation makes hits 0&4/1&5/… (same take after the 4-take
    ///    wrap) exact clones and this clause goes red (fail-first proven).
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn sampled_ride_hits_are_decorrelated() {
        let sr = 44100.0;
        let n_hits = 8usize;
        let spacing = 1.3f64; // ride takes are ~1.2 s: windows never overlap
        let hits: Vec<(f64, u8, u8)> = (0..n_hits)
            .map(|i| (0.05 + spacing * i as f64, 51u8, 100u8))
            .collect();
        // dry drum bus: zero the sends so hit windows hold only the voice
        let song = drum_song(
            &hits,
            0.05 + spacing * n_hits as f64,
            &[(91, 0), (93, 0), (94, 0)],
        );
        let opt = Options {
            samples: true,
            ..test_opts(sr)
        };
        let s = render(&song, &opt).0;
        let mono: Vec<f32> = s.chunks_exact(2).map(|p| p[0] + p[1]).collect();
        let win = |i: usize| {
            let at = ((0.05 + spacing * i as f64) * sr as f64) as usize;
            &mono[at..at + (0.20 * sr) as usize]
        };
        let mut worst_any = 0f32;
        for i in 0..n_hits {
            for j in (i + 1)..n_hits {
                assert_ne!(win(i), win(j), "hits {i} and {j} are bit-identical");
                let r = ncc_max(win(i), win(j), 128);
                if j == i + 1 || j == i + 4 {
                    println!("ride hits {i}-{j}: plain ncc {r:.3}");
                }
                worst_any = worst_any.max(r);
            }
        }
        // calibration visibility: same-take pairs (i, i+4) must read HIGH
        // under the warp search — that head-room is what lets the consecutive
        // clause catch a seed-modulo repeat
        for i in 0..n_hits - 4 {
            let r = warp_ncc(win(i), win(i + 4));
            println!("ride hits {i}-{} (same take): warp ncc {r:.3}", i + 4);
        }
        let mut worst_consecutive = 0f32;
        for i in 0..n_hits - 1 {
            let r = warp_ncc(win(i), win(i + 1));
            println!("ride hits {i}-{}: warp ncc {r:.3}", i + 1);
            worst_consecutive = worst_consecutive.max(r);
        }
        // Calibration (measured on this bank): distinct takes warp-NCC
        // 0.12-0.48; the same take under micro-variation re-aligns to
        // 0.70-0.86; a clone is 1.0. The 0.60 threshold sits ≥0.10 clear of
        // both populations.
        assert!(
            worst_consecutive < 0.60,
            "consecutive ride hits warp-correlate {worst_consecutive:.3} — round-robin repeat"
        );
        assert!(
            worst_any < 0.98,
            "some ride hit pair is a clone: ncc {worst_any:.3}"
        );
    }

    /// Stage E (engine half): the hi-hat choke group survives the sampled
    /// kit — a closed (42) or pedal (44) strike chokes the ringing SAMPLED
    /// open hat (46) within ~30 ms, exactly as the modeled hats behave
    /// (`closed_hat_chokes_open_in_engine`).
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn sampled_closed_or_pedal_hat_chokes_open_in_engine() {
        let sr = 44100.0;
        let opt = Options {
            samples: true,
            ..test_opts(sr)
        };
        let open_only = drum_song(&[(0.05, 46, 110)], 1.0, &[]);
        let a = render(&open_only, &opt).0;
        // 30 ms after the choking hit the open ring must be gone (the voice
        // fade is -60 dB in ~15 ms). The window also contains the choker's
        // OWN body (the pedal chick rings well past 200 ms), so the oracle
        // measures the RESIDUAL: choked-render energy minus the energy of
        // the choker played alone. An unchoked open hat leaves its full ring
        // in the residual; a choked one leaves almost nothing.
        let w = |s: &[f32]| rms(&left(s)[(0.28 * sr) as usize..(0.45 * sr) as usize]);
        for choker in [42u8, 44] {
            let choked = drum_song(&[(0.05, 46, 110), (0.25, choker, 90)], 1.0, &[]);
            let b = render(&choked, &opt).0;
            let solo = drum_song(&[(0.25, choker, 90)], 1.0, &[]);
            let c = render(&solo, &opt).0;
            let residual = (w(&b).powi(2) - w(&c).powi(2)).max(0.0).sqrt();
            println!(
                "choker {choker}: open-only {:.5}, choked {:.5}, choker-solo {:.5}, residual {:.5}",
                w(&a),
                w(&b),
                w(&c),
                residual
            );
            assert!(
                residual < 0.35 * w(&a),
                "sampled open hat survived the key-{choker} choke: residual {residual} vs open ring {}",
                w(&a)
            );
        }
    }

    /// THE Stage E anti-machine-gun oracle for the highest-stakes piece:
    /// hats play continuous 16ths. Sixteen closed-hat (42) hits at 16th-note
    /// spacing (120 bpm, 0.125 s) through the full engine path, so the
    /// per-key round-robin counter cycles the 4 takes and the note seed
    /// drives the per-hit rate/gain micro-variation:
    ///
    ///  * every hit window must be audible and NO pair bit-identical;
    ///  * NO pair — same-take or cross-take — may correlate above 0.35
    ///    (listener-verified: the pre-hat-profile kit read worst-pair 0.494
    ///    and Arthur heard it as machine-gunny). Uniform ±2.5% rate jitter
    ///    cannot reach this: over 16 hits some same-take pair always lands
    ///    within a fraction of a percent in rate, re-correlating the
    ///    transient (fail-first: threshold tightened before the hat jitter
    ///    profile landed — the old engine read 0.494 against this 0.35).
    ///    The hat profile answers with STRATIFIED rate offsets
    ///    (hit_index % 5 over ±7%, coprime with the 4-take round-robin, so
    ///    no two hits closer than 20 apart share take AND rate stratum)
    ///    plus onset jitter (U(0, 1 ms)) and wider gain jitter;
    ///  * the same-take pairs (i, i+4 after the 4-take wrap) must differ
    ///    SUBSTANTIALLY (normalized difference energy — the ride oracle's
    ///    diff/rms measure).
    ///
    /// The clone detector is calibrated FAIL-FIRST inside the test: two
    /// voices built with the same seed and same hit index (what a
    /// machine-gun engine would produce) render bit-identically and read
    /// NCC 1.0 — the reading the engine path must never approach.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn sampled_fast_closed_hats_do_not_machine_gun() {
        let sr = 44100.0;
        // fail-first calibration: same seed + same take == a true machine gun
        let clone_hat = || {
            let mut w = vec![0f32; (0.10 * sr) as usize];
            let mut v = drums::make(42, 100, sr, 0xBEEF, drums::Kit::V3, true, 3).unwrap();
            v.render(&mut w);
            w
        };
        let (c1, c2) = (clone_hat(), clone_hat());
        assert_eq!(c1, c2, "identical seed+take must render bit-identically");
        let clone_ncc = ncc_max(&c1, &c2, 128);
        assert!(
            clone_ncc > 0.999,
            "clone detector miscalibrated: {clone_ncc:.4}"
        );

        let n = 16usize;
        let dt = 0.125f64; // 16th notes at 120 bpm
        let hits: Vec<(f64, u8, u8)> = (0..n).map(|i| (0.05 + dt * i as f64, 42, 100)).collect();
        // dry drum bus: zero the sends so hit windows hold only the voice
        let song = drum_song(
            &hits,
            0.05 + dt * n as f64 + 0.3,
            &[(91, 0), (93, 0), (94, 0)],
        );
        let opt = Options {
            samples: true,
            ..test_opts(sr)
        };
        let s = render(&song, &opt).0;
        let mono: Vec<f32> = s.chunks_exact(2).map(|p| p[0] + p[1]).collect();
        let win = |i: usize| -> &[f32] {
            let at = ((0.05 + dt * i as f64) * sr as f64) as usize;
            &mono[at..at + (0.10 * sr) as usize]
        };
        for i in 0..n {
            assert!(
                rms(win(i)) > 1e-4,
                "hat hit {i} is silent — sampled hat not routed?"
            );
        }
        let mut worst_any = 0f32;
        for i in 0..n {
            for j in (i + 1)..n {
                assert_ne!(win(i), win(j), "hat hits {i} and {j} are bit-identical");
                worst_any = worst_any.max(ncc_max(win(i), win(j), 128));
            }
        }
        let mut worst_diff = f32::INFINITY;
        for i in 0..n - 4 {
            let (a, b) = (win(i), win(i + 4));
            let diff: Vec<f32> = a.iter().zip(b).map(|(x, y)| x - y).collect();
            worst_diff = worst_diff.min(rms(&diff) / rms(a).max(1e-9));
        }
        println!(
            "fast hats: max pairwise ncc {worst_any:.3} (clone reads {clone_ncc:.3}), \
             min same-take diff/rms {worst_diff:.3}"
        );
        assert!(
            worst_any < 0.35,
            "some hat pair correlates {worst_any:.3} (limit 0.35) — MACHINE-GUN: \
             the hat jitter profile is not decorrelating repeats"
        );
        assert!(
            worst_diff > 0.4,
            "same-take hats nearly identical (diff/rms {worst_diff:.3}) — \
             MACHINE-GUN: the micro-variation is not decorrelating repeats"
        );
    }

    /// Oracle 3 (§5.1/§5.3): the cabinet's magnitude response, measured on
    /// the linear cab chain alone at the 2× rate it runs at — presence peak,
    /// steep HF cliff, low-end resonance.
    #[test]
    fn cabinet_response_shape() {
        let sr2 = 88_200.0;
        let mut cab = cab_biquads(sr2);
        let mut ir = vec![0f32; 16384];
        ir[0] = 1.0;
        for x in ir.iter_mut() {
            let mut y = *x;
            for c in cab.iter_mut() {
                y = c.process(y);
            }
            *x = y;
        }
        let db = |f: f32| 20.0 * crate::testutil::mag_at(&ir, sr2, f).max(1e-12).log10();
        assert!(
            db(2600.0) - db(1000.0) >= 3.0,
            "presence: 2600 {:.1} dB vs 1000 {:.1} dB",
            db(2600.0),
            db(1000.0)
        );
        assert!(
            db(6000.0) - db(3000.0) <= -18.0,
            "cliff: 6000 {:.1} dB vs 3000 {:.1} dB",
            db(6000.0),
            db(3000.0)
        );
        assert!(
            db(100.0) - db(300.0) >= 2.0,
            "low resonance: 100 {:.1} dB vs 300 {:.1} dB",
            db(100.0),
            db(300.0)
        );
    }

    /// Guitar-realism HLD §5 / AC4 (bar recalibrated in-implementation, HLD
    /// §14 rider): MicroCab standalone puts genuine fine structure on the
    /// 900–3600 Hz band — ≥ 6 magnitude alternations of ≥ 1.5 dB (the
    /// drafted "≥ 2 dB" was physically over-spec'd for a ≤ 0.9 ms sparse
    /// FIR: a 250 k-candidate search found no tap set meeting it inside the
    /// cliff-tilt and low-band bounds) — while the band-average stays
    /// ~unity and the total swing stays musical. Whether it reads as "cab"
    /// vs "phaser" is the audition's call — this pins presence and level.
    #[test]
    fn micro_cab_ripple_fine_structure() {
        let sr2 = 88_200.0;
        let mut mc = MicroCab::with_depth(sr2, 1.0);
        let mut ir = vec![0f32; 4096];
        ir[0] = 1.0;
        for x in ir.iter_mut() {
            *x = mc.process(*x);
        }
        let db = |f: f32| 20.0 * crate::testutil::mag_at(&ir, sr2, f).max(1e-12).log10();
        let grid: Vec<f32> = (0..55).map(|k| 900.0 + k as f32 * 50.0).collect();
        let curve: Vec<f32> = grid.iter().map(|&f| db(f)).collect();
        // count direction reversals with >= 1.5 dB swing from the running
        // extreme (dir 0 = no run yet: track both extremes)
        const DEPTH: f32 = 1.5;
        let (mut alternations, mut dir) = (0usize, 0i8);
        let (mut mn, mut mx) = (curve[0], curve[0]);
        for &v in &curve[1..] {
            if dir >= 0 {
                mx = mx.max(v);
            }
            if dir <= 0 {
                mn = mn.min(v);
            }
            if dir >= 0 && mx - v >= DEPTH {
                alternations += 1;
                dir = -1;
                mn = v;
            } else if dir <= 0 && v - mn >= DEPTH {
                alternations += 1;
                dir = 1;
                mx = v;
            }
        }
        assert!(
            alternations >= 6,
            "fine structure too smooth: {alternations} alternations >= 1.5 dB in 900-3600 Hz ({curve:?})"
        );
        // band-average parity vs an identity (bare impulse) measured the
        // same way — mag_at carries a fixed impulse-scale offset, so the
        // contract is relative, not absolute
        let mut ident = vec![0f32; 4096];
        ident[0] = 1.0;
        let dbi = |f: f32| 20.0 * crate::testutil::mag_at(&ident, sr2, f).max(1e-12).log10();
        let avg: f32 = grid.iter().map(|&f| db(f) - dbi(f)).sum::<f32>() / grid.len() as f32;
        assert!(
            avg.abs() < 1.5,
            "band-average moved: {avg:.2} dB (normalization contract)"
        );
        let (lo, hi) = curve
            .iter()
            .fold((f32::MAX, f32::MIN), |(a, b), &v| (a.min(v), b.max(v)));
        assert!(
            hi - lo <= 10.0,
            "standalone ripple swing {:.1} dB — too deep to stay musical",
            hi - lo
        );
    }

    /// The cabinet ripple must not cost a SUSTAINING lead its money note.
    ///
    /// `MicroCab` normalizes to unity on the 900–3600 Hz band AVERAGE, which
    /// is level-neutral for broadband material but not for a voice holding
    /// ONE pitch: it keeps whatever the ripple does at that single frequency.
    /// At full depth the comb is coarse enough to swallow a held tone whole —
    /// measured on Three-Sixty-One's finale, C6 −2.08 dB and E6 −1.03 dB at
    /// the fundamental with their harmonics +2.8 dB, i.e. thin rather than
    /// merely quiet (2026.07.20 journal). [`MICRO_CAB_LEAD_DEPTH`] bounds
    /// that for the CC0 alt bank while keeping the ripple audible.
    ///
    /// RED if the lead depth is restored to full (worst-case deviation goes
    /// back over 3 dB), and RED the other way if someone zeroes the ripple
    /// instead of shallowing it (the lead would stop speaking through a cab).
    #[test]
    fn sustaining_lead_cab_ripple_is_bounded_at_every_held_pitch() {
        let sr2 = 88_200.0;
        let curve = |depth: f32| -> Vec<f32> {
            let mut mc = MicroCab::with_depth(sr2, depth);
            let mut ir = vec![0f32; 4096];
            ir[0] = 1.0;
            for x in ir.iter_mut() {
                *x = mc.process(*x);
            }
            let mut ident = vec![0f32; 4096];
            ident[0] = 1.0;
            (0..=270)
                .map(|k| {
                    let f = 900.0 + k as f32 * 10.0;
                    20.0 * (crate::testutil::mag_at(&ir, sr2, f).max(1e-12)
                        / crate::testutil::mag_at(&ident, sr2, f).max(1e-12))
                    .log10()
                })
                .collect()
        };
        let worst = |c: &[f32]| c.iter().fold(0f32, |m, v| m.max(v.abs()));
        let swing = |c: &[f32]| {
            let (lo, hi) = c
                .iter()
                .fold((f32::MAX, f32::MIN), |(a, b), &v| (a.min(v), b.max(v)));
            hi - lo
        };
        let (full, lead) = (curve(1.0), curve(MICRO_CAB_LEAD_DEPTH));

        // (1) the pathology is real at full depth — this is what the default
        // bank still carries, deliberately, for broadband rhythm work
        assert!(
            worst(&full) > 2.5,
            "full-depth ripple only {:.2} dB deep — the premise of this fix is gone",
            worst(&full)
        );
        // (2) ... and is bounded below audibility for a held tone on the lead
        assert!(
            worst(&lead) < 1.0,
            "sustaining lead can lose {:.2} dB on a held pitch (want < 1.0)",
            worst(&lead)
        );
        // (3) ... without deleting the cabinet: the ripple is still there
        assert!(
            swing(&lead) > 0.8,
            "lead ripple flattened to {:.2} dB swing — that is a DI, not a cab",
            swing(&lead)
        );
        // (4) the specific tones that provoked this: C6 and E6 recover
        let at = |c: &[f32], f: f32| c[((f - 900.0) / 10.0).round() as usize];
        for (name, f0, want) in [("C6", 1050.0, 1.0), ("E6", 1320.0, 0.5)] {
            let gain = at(&lead, f0) - at(&full, f0);
            assert!(
                gain >= want,
                "{name} ({f0} Hz) recovers only {gain:.2} dB (want >= {want})"
            );
        }
    }

    /// The bank is part of the driven insert's identity, so a CC0 that lands
    /// AFTER the program change must rebuild it. Our albums order bank-select
    /// first (`fix(albums): order bank select before program changes`), but a
    /// foreign GM file need not, and the two orderings must agree.
    #[test]
    fn cc0_bank_select_reaches_the_driven_cabinet_in_either_order() {
        let sr = 44100.0;
        let opts = test_opts(sr);
        let song = |bank_first: bool, bank: u8| {
            let mut ev = Vec::new();
            if bank_first {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: bank,
                    },
                ));
                ev.push((0.0, EvKind::Prog { ch: 0, prog: 29 }));
            } else {
                ev.push((0.0, EvKind::Prog { ch: 0, prog: 29 }));
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: bank,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 88,
                    vel: 104,
                },
            ));
            test_song(ev, 2.0)
        };
        let alt_first = render(&song(true, 1), &opts).0;
        let alt_after = render(&song(false, 1), &opts).0;
        let default_bank = render(&song(true, 0), &opts).0;

        assert!(rms(&alt_first) > 1e-4, "the driven lead should sound");
        assert_eq!(
            alt_first, alt_after,
            "CC0 after the program change did not reach the driven cabinet — \
             the insert was left on the default bank's ripple depth"
        );
        assert_ne!(
            alt_first, default_bank,
            "the alt bank renders identically to the default — the shallower \
             lead cabinet ripple is not wired up"
        );
    }

    /// Guitar-realism HLD §5 / AC4 (review C5) — the SHIPPED series response
    /// (MicroCab into the cab biquads) keeps the macro cabinet shape the
    /// coarse oracle pins on the biquads alone, bounds the ripple depth, and
    /// holds broadband level parity with the biquads-only cab.
    #[test]
    fn micro_cab_combined_keeps_macro_shape() {
        let sr2 = 88_200.0;
        let run = |with_micro: bool| {
            let mut cab = cab_biquads(sr2);
            let mut mc = MicroCab::with_depth(sr2, 1.0);
            let mut ir = vec![0f32; 16384];
            ir[0] = 1.0;
            for x in ir.iter_mut() {
                let mut y = *x;
                for c in &mut cab[..CAB_CLIFF] {
                    y = c.process(y);
                }
                if with_micro {
                    y = mc.process(y);
                }
                for c in &mut cab[CAB_CLIFF..] {
                    y = c.process(y);
                }
                *x = y;
            }
            ir
        };
        let ir = run(true);
        let db = |ir: &[f32], f: f32| 20.0 * crate::testutil::mag_at(ir, sr2, f).max(1e-12).log10();
        // the same three macro anchors cabinet_response_shape pins
        assert!(
            db(&ir, 2600.0) - db(&ir, 1000.0) >= 3.0,
            "presence lost: 2600 {:.1} vs 1000 {:.1}",
            db(&ir, 2600.0),
            db(&ir, 1000.0)
        );
        assert!(
            db(&ir, 6000.0) - db(&ir, 3000.0) <= -18.0,
            "cliff lost: 6000 {:.1} vs 3000 {:.1}",
            db(&ir, 6000.0),
            db(&ir, 3000.0)
        );
        assert!(
            db(&ir, 100.0) - db(&ir, 300.0) >= 2.0,
            "low resonance lost: 100 {:.1} vs 300 {:.1}",
            db(&ir, 100.0),
            db(&ir, 300.0)
        );
        // ripple depth bounded: within 900-3600 the swing stays musical
        let vals: Vec<f32> = (0..28).map(|k| db(&ir, 900.0 + k as f32 * 100.0)).collect();
        let (mn, mx) = vals
            .iter()
            .fold((f32::MAX, f32::MIN), |(a, b), &v| (a.min(v), b.max(v)));
        assert!(
            mx - mn <= 14.0,
            "ripple guts the band: {:.1} dB swing in 900-3600",
            mx - mn
        );
        // broadband level parity vs the biquads-only cab
        let base = run(false);
        let band_avg = |ir: &[f32]| {
            (0..28)
                .map(|k| db(ir, 300.0 + k as f32 * 100.0))
                .sum::<f32>()
                / 28.0
        };
        let delta = band_avg(&ir) - band_avg(&base);
        assert!(
            delta.abs() < 1.5,
            "combined cab level moved {delta:.2} dB vs biquads-only"
        );
    }

    /// Oracle 4 (§5.3): the biased shaper adds a real 2nd harmonic (a pure
    /// sine in, so 2f can only come from the new asymmetry) and the DC
    /// blocker holds the sustained output DC-free.
    #[test]
    fn drive_asymmetry_and_dc() {
        let sr = 44100.0;
        let mut drive = Drive::new(29, false, sr);
        let f0 = 110.0;
        let mut buf: Vec<f32> = (0..(sr as usize))
            .map(|i| 0.5 * (std::f32::consts::TAU * f0 * i as f32 / sr).sin())
            .collect();
        drive.process(&mut buf);
        // skip the DC-blocker settling (§5.3: window starts ≥50 ms in)
        let seg = &buf[(0.05 * sr) as usize..];
        let dc = seg.iter().map(|&x| x as f64).sum::<f64>() / seg.len() as f64;
        assert!(dc.abs() < 1e-3, "sustained DC {dc}");
        let m2 = crate::testutil::mag_at(seg, sr, 2.0 * f0);
        let m3 = crate::testutil::mag_at(seg, sr, 3.0 * f0);
        assert!(m2 > 0.1 * m3, "2nd harmonic {m2} vs 3rd {m3}");
    }

    /// Oracle 5 (§5.1 differential): the program-keyed pre-voicing shifts
    /// the 600 Hz : 2 kHz balance in the intended direction against a
    /// voice-bypassed reference — prog 30 scoops the mids, prog 29 pushes.
    #[test]
    fn drive_pre_voicing_direction() {
        let sr = 44100.0;
        let input: Vec<f32> = {
            let mut rng = crate::dsp::Rng::new(11);
            (0..(sr as usize)).map(|_| rng.white() * 0.3).collect()
        };
        let ratio = |prog: u8, flat: bool| {
            let mut d = Drive::new(prog, false, sr);
            if flat {
                d = d.with_flat_voice();
            }
            let mut buf = input.clone();
            d.process(&mut buf);
            crate::testutil::band_rms(&buf, sr, 600.0, 1.0)
                / crate::testutil::band_rms(&buf, sr, 2000.0, 1.0).max(1e-9)
        };
        assert!(
            ratio(30, false) < ratio(30, true),
            "prog 30 should scoop the mids"
        );
        assert!(
            ratio(29, false) > ratio(29, true),
            "prog 29 should push the mids"
        );
    }

    /// V6b (guitar v2): the held-lead steady state stays HARMONIC through the
    /// engine — the sustainer converges toward the fundamental (by design;
    /// the damper's tilted loss stands), and the Drive's tanh re-harmonizes
    /// it. A naked-sine pass (the T16 "wooden glockenspiel" failure mode,
    /// which measures ≤ −50 dB here) fails the 2f0 pin.
    ///
    /// Floor provenance: −20 dB was calibrated when the sag boost ran the
    /// held tail ×4 hotter into the shapers; with the inverted sag deleted
    /// (§2.6) the level-matched static drive at the e-bow's hold level
    /// (DRIVE.sustain = 0.5) measures −24.9 dB, so the anti-naked-sine floor
    /// is re-pinned at −30 dB (5 dB margin, matching the old pin's margin).
    #[test]
    fn sustained_lead_stays_harmonic_through_drive() {
        let sr = 44100.0;
        // Round-3 U2: the held-lead idiom lives on the CC0 alt bank now —
        // the default DRIVE bank decays again (plan §3.6), so this pin
        // follows the sustainer to DRIVE_LEAD via bank-select 1.
        let events = vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 29 }),
            // silence the default echo send so the pin reads the dry voice
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 94,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 76,
                    vel: 100,
                },
            ),
        ];
        let out = left(&render(&test_song(events, 3.2), &test_opts(sr)).0);
        let seg = &out[(2.5 * sr) as usize..(3.0 * sr) as usize];
        let f0 = 659.26;
        let m1 = crate::testutil::mag_at(seg, sr, f0).max(1e-12);
        let m2 = crate::testutil::mag_at(seg, sr, 2.0 * f0);
        let rel = 20.0 * (m2 / m1).log10();
        println!("V6b: 2f0 at {rel:.1} dB rel f0 in the 2.5–3.0 s window");
        assert!(
            rel >= -30.0,
            "held lead lost its harmonics: 2f0 {rel:.1} dB rel f0"
        );
    }

    /// Round-2 GM029/030 ("clean, dark sustain"): the e-bow-held tail must
    /// keep an audible harmonic edge, not decay to a warm near-sine. The
    /// sustainer holds the string near a pure fundamental, so only the
    /// Drive's regeneration puts harmonics in the deep hold — THD of
    /// harmonics 2..=16 vs f0, through the full engine (dry: chorus/echo
    /// silenced), in the 5.5–6.0 s window of a held note (past the ~6 s
    /// e-bow climb, the pick's own partials long dead). Pre-round-2 the
    /// four rows measured −32.8/−35.8/−35.5/−35.4 dB (inaudible); the
    /// floors sit ~3 dB above those and ~3 dB below the shipped values.
    /// The depth is capped structurally: a harder-clipped hold turns
    /// square and its windowed RMS overtakes the broadband attack,
    /// tripping the §2.6 sag-catcher (o_attack_sustained_plucks_no_late_
    /// bloom) — so the hold rides the tanh knee, not the rail.
    #[test]
    fn driven_sustain_stays_distorted() {
        let sr = 44100.0;
        for (prog, key, floor) in [
            (29u8, 40u8, -29.0f32), // E2: low chug register
            (29, 45, -28.0),        // A2: open-string lead register
            (30, 40, -33.0),
            (30, 45, -29.0),
        ] {
            let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };
            let events = vec![
                // Round-3 U2: the e-bow hold lives on the CC0 alt bank
                // (DRIVE_LEAD); the default bank decays, so a 5.5 s window
                // on it would read string remnants, not a held tail.
                (0.0, cc(0, 1)),
                (0.0, EvKind::Prog { ch: 0, prog }),
                (0.0, cc(93, 0)),
                (0.0, cc(94, 0)),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key,
                        vel: 100,
                    },
                ),
            ];
            let out = left(&render(&test_song(events, 6.2), &test_opts(sr)).0);
            let f0 = 440.0 * 2f32.powf((key as f32 - 69.0) / 12.0);
            let seg = &out[(5.5 * sr) as usize..(6.0 * sr) as usize];
            let m1 = crate::testutil::mag_at(seg, sr, f0).max(1e-12);
            let mut pow = 0.0f32;
            for n in 2..=16u32 {
                let m = crate::testutil::mag_at(seg, sr, n as f32 * f0);
                pow += m * m;
            }
            let thd = 20.0 * (pow.sqrt() / m1).log10();
            println!("driven sustain prog {prog} key {key}: THD(2..16) {thd:.1} dB rel f0");
            assert!(
                thd >= floor,
                "prog {prog} key {key}: held sustain went clean — THD {thd:.1} dB \
                 rel f0 (floor {floor})"
            );
        }
    }

    /// V9 (guitar v2): aliasing floor — a pure steady sine fed DIRECTLY into
    /// the Drive (a rendered voice would confound legitimate string
    /// inharmonicity: detuned polarizations, coupling, noise excitation).
    /// Every predicted fold-back bin — the 2× nonlinear stage folds at
    /// 88.2 kHz, the sample-aligned decimation folds again at 44.1 kHz —
    /// must sit ≤ −40 dB below the fundamental.
    #[test]
    fn drive_alias_floor() {
        let sr = 44100.0;
        let f0 = 1301.0; // high-lead register, harmonics off any tidy divisor
        let fold = |f: f32, fs: f32| {
            let r = f % fs;
            if r > fs / 2.0 {
                fs - r
            } else {
                r
            }
        };
        for prog in [29u8, 30] {
            let mut d = Drive::new(prog, false, sr);
            let mut buf: Vec<f32> = (0..(sr as usize))
                .map(|i| 0.5 * (std::f32::consts::TAU * f0 * i as f32 / sr).sin())
                .collect();
            d.process(&mut buf);
            let seg = &buf[(0.2 * sr) as usize..];
            let m0 = crate::testutil::mag_at(seg, sr, f0).max(1e-12);
            let mut worst = -200.0f32;
            let mut worst_bin = 0.0f32;
            for n in 2..=80u32 {
                let fh = n as f32 * f0;
                if fh <= sr / 2.0 {
                    continue; // a true harmonic, not an alias
                }
                let alias = fold(fold(fh, sr * 2.0), sr);
                if !(100.0..=20_000.0).contains(&alias) {
                    continue;
                }
                // skip bins that coincide with legitimate harmonics
                if (alias / f0 - (alias / f0).round()).abs() * f0 < 8.0 {
                    continue;
                }
                let rel = 20.0 * (crate::testutil::mag_at(seg, sr, alias) / m0).log10();
                if rel > worst {
                    worst = rel;
                    worst_bin = alias;
                }
            }
            println!("V9 prog {prog}: worst alias {worst:.1} dB rel f0 at {worst_bin:.0} Hz");
            assert!(
                worst <= -40.0,
                "prog {prog}: alias at {worst_bin:.0} Hz is {worst:.1} dB rel f0"
            );
        }
    }

    /// Level-match probe (diagnostic, `--ignored --nocapture`): post-drive RMS
    /// of steady 220 Hz sines at a loud and a tail operating point, per
    /// program — the two-point loudness reference for re-matching `post`
    /// across Drive revisions (guitar v2 HLD §3.C).
    #[test]
    #[ignore]
    fn drive_level_probe() {
        let sr = 44100.0;
        for prog in [29u8, 30] {
            for amp in [0.5f32, 0.05] {
                let mut d = Drive::new(prog, false, sr);
                let mut buf: Vec<f32> = (0..(sr as usize))
                    .map(|i| amp * (std::f32::consts::TAU * 220.0 * i as f32 / sr).sin())
                    .collect();
                d.process(&mut buf);
                let r = crate::testutil::rms(&buf[(0.2 * sr) as usize..]);
                println!(
                    "drive probe prog {prog} amp {amp}: rms {r:.5} ({:.2} dBFS)",
                    20.0 * r.max(1e-12).log10()
                );
            }
        }
    }

    // -----------------------------------------------------------------
    // O-ATTACK (§3.1): "a struck/plucked voice's attack is its loudest
    // instant", measured on a windowed-RMS envelope through the FULL
    // engine — never a single global sample peak (noise/beating/body
    // resonance can nudge a raw peak; a 30 ms RMS window cannot).
    // -----------------------------------------------------------------

    /// Windowed-RMS envelope: 30 ms windows on a 10 ms hop, as
    /// (window-start seconds, rms) pairs.
    fn rms_env(sig: &[f32], sr: f32) -> Vec<(f32, f32)> {
        let win = (0.030 * sr) as usize;
        let hop = (0.010 * sr) as usize;
        let mut v = Vec::new();
        let mut a = 0usize;
        while a + win <= sig.len() {
            v.push((a as f32 / sr, rms(&sig[a..a + win])));
            a += hop;
        }
        v
    }

    /// One note through the engine, dry: reverb wet 0, echo bus disabled
    /// (`delay_s: 0`), chorus/echo/reverb sends zeroed so a bus tail cannot
    /// masquerade as a late bloom of the voice itself.
    fn o_attack_render(
        program: u8,
        key: u8,
        vel: u8,
        secs: f64,
        samples: bool,
        sr: f32,
    ) -> Vec<f32> {
        let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };
        let events = vec![
            (
                0.0,
                EvKind::Prog {
                    ch: 0,
                    prog: program,
                },
            ),
            (0.0, cc(91, 0)),
            (0.0, cc(93, 0)),
            (0.0, cc(94, 0)),
            (0.05, EvKind::NoteOn { ch: 0, key, vel }),
        ];
        let mut opt = test_opts(sr);
        opt.samples = samples;
        left(&render(&test_song(events, secs), &opt).0)
    }

    /// The property: no post-attack window's RMS may exceed the attack
    /// window's loudest RMS. The attack window is per-class (`attack_s`),
    /// not a hard 80 ms constant — bar percussion speaks fast, timpani and
    /// tubular bells slower.
    fn assert_attack_dominates(sig: &[f32], sr: f32, note_s: f32, attack_s: f32, name: &str) {
        let env = rms_env(sig, sr);
        let attack = env
            .iter()
            .filter(|(t, _)| *t >= note_s - 0.005 && *t < note_s + attack_s)
            .map(|&(_, r)| r)
            .fold(0f32, f32::max);
        assert!(attack > 1e-5, "{name}: silent attack window");
        let (mut worst, mut worst_t) = (0f32, 0f32);
        for &(t, r) in env.iter().filter(|(t, _)| *t >= note_s + attack_s) {
            if r > worst {
                (worst, worst_t) = (r, t);
            }
        }
        assert!(
            worst <= attack,
            "{name}: late bloom — window at {worst_t:.2} s has rms {worst:.5} \
             above the attack's {attack:.5}"
        );
    }

    /// O-ATTACK, struck/plucked leg: Modal (piano/bells/mallets/timpani)
    /// and non-sustaining Pluck presets, model-only through the engine.
    #[test]
    fn o_attack_struck_attack_dominates() {
        let sr = 44100.0;
        for (program, key, attack_s, name) in [
            (0u8, 60u8, 0.15f32, "acoustic piano"),
            (6, 60, 0.12, "harpsichord"), // §2.10: guards the new Pluck route
            (9, 84, 0.12, "glockenspiel"),
            (12, 72, 0.10, "marimba"),
            (14, 65, 0.20, "tubular bells"),
            (47, 50, 0.20, "timpani"),
            (24, 52, 0.12, "nylon guitar"),
            (25, 52, 0.12, "steel guitar"),
            (45, 60, 0.10, "pizzicato"),
            (46, 60, 0.12, "harp"),
        ] {
            let sig = o_attack_render(program, key, 100, 3.0, false, sr);
            assert_attack_dominates(&sig, sr, 0.05, attack_s, name);
        }
    }

    /// O-ATTACK, sampled leg: the LA-wrapped struck voices with the sample
    /// layer on, through the engine (a pick quieter than the model's 200 ms
    /// sustain is upside-down for a plucked string). Under the pre-§2.7
    /// crossfade the model's own onset ran UNDER the sample (a doubled
    /// attack) and masked the GM-24 gain cut even here; once the contract
    /// gives the sample sole onset ownership, the 0.25 hack fails
    /// `la_level_continuity`'s attack-is-the-peak leg (measured: nylon key
    /// 45 inverts at 0.25), and this engine-level leg pins the fixed gain.
    #[test]
    fn o_attack_sampled_struck_attack_dominates() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        for (program, key, attack_s, name) in [
            (0u8, 60u8, 0.20f32, "acoustic piano (LA)"),
            (24, 52, 0.12, "nylon guitar (LA)"),
            (24, 57, 0.12, "nylon guitar (LA), mid"),
            (24, 64, 0.12, "nylon guitar (LA), high"),
        ] {
            let sig = o_attack_render(program, key, 100, 3.0, true, sr);
            assert_attack_dominates(&sig, sr, 0.05, attack_s, name);
        }
    }

    /// O-ATTACK, sustaining-pluck leg (`sustain > 0`: the DRIVE e-bow):
    /// a held distorted note may HOLD, but no late window may exceed the
    /// pick — the §2.6 sag-inversion catcher. The deleted sag law's restore
    /// target was an ABSOLUTE level, so a quiet pick (vel 20-30) was boosted
    /// past its own attack ~0.2 s in, and at ff the sag's slow limit cycle
    /// grew past the pick by ~7 s (measured 1.00-1.04x pre-fix on every row
    /// here; the static two-stage cascade keeps all four well below 1).
    #[test]
    fn o_attack_sustained_plucks_no_late_bloom() {
        let sr = 44100.0;
        for (program, vel, secs, name) in [
            (29u8, 20u8, 4.0, "overdrive pp"),
            (29, 100, 4.0, "overdrive ff"),
            (30, 30, 4.0, "distortion p"),
            (30, 100, 8.0, "distortion ff, long hold"),
        ] {
            let sig = o_attack_render(program, 45, vel, secs, false, sr);
            assert_attack_dominates(&sig, sr, 0.05, 0.15, name);
        }
    }

    /// O-ATTACK, unit leg: the Drive insert itself on a known decaying
    /// input (−15 dB/s, 220 Hz), pinning recovery at the unit rather than
    /// only end-to-end. Two clauses: (a) windowed output RMS never RISES
    /// (0.5 dB tolerance) — a recovery gain law that outruns the decay
    /// fails; (b) the tail genuinely DECAYS — ≥ 12 dB from the 0.05-0.10 s
    /// window to the 1.80-1.95 s window. The deleted sag law held that
    /// decay to 5.6 dB (measured, prog 30) by slewing gain up to 4x as the
    /// envelope fell; the static two-stage cascade measures 16.6 dB.
    #[test]
    fn o_attack_drive_never_blooms_on_decay() {
        let sr = 44100.0;
        let n = (2.0 * sr) as usize;
        for prog in [29u8, 30] {
            let mut d = Drive::new(prog, false, sr);
            let mut buf: Vec<f32> = (0..n)
                .map(|i| {
                    let t = i as f32 / sr;
                    0.5 * 10f32.powf(-15.0 * t / 20.0) * (std::f32::consts::TAU * 220.0 * t).sin()
                })
                .collect();
            d.process(&mut buf);
            let win = (0.05 * sr) as usize;
            let env: Vec<f32> = buf.chunks_exact(win).map(rms).collect();
            // (a) skip the first pair: filter/DC-blocker settling
            for (k, pair) in env.windows(2).enumerate().skip(1) {
                assert!(
                    pair[1] <= pair[0] * 1.06,
                    "prog {prog}: output rose on a decaying input at window {k}: \
                     {:.5} -> {:.5}",
                    pair[0],
                    pair[1]
                );
            }
            // (b) the decay must pass through, not be recovered away
            let db = |a: f32, z: f32| {
                20.0 * rms(&buf[(a * sr) as usize..(z * sr) as usize])
                    .max(1e-12)
                    .log10()
            };
            let decay = db(0.05, 0.10) - db(1.80, 1.95);
            assert!(
                decay >= 12.0,
                "prog {prog}: tail held up — decay {decay:.1} dB < 12 \
                 (a sag-like envelope-inverse recovery gain)"
            );
        }
    }

    /// Diagnostic (`--ignored --nocapture`): held-note level through the
    /// engine for the driven guitars — the §2.6 loudness-risk probe. Prints
    /// the windowed RMS of a 3.5 s held note at 0.2–0.5 s vs 2.5–3.0 s so a
    /// sustain collapse after a Drive change is measured, not guessed.
    #[test]
    #[ignore = "diagnostic probe, not a gate"]
    fn o_attack_held_note_probe() {
        let sr = 44100.0;
        for prog in [29u8, 30] {
            let sig = o_attack_render(prog, 45, 100, 3.5, false, sr);
            let w = |a: f32, z: f32| rms(&sig[(a * sr) as usize..(z * sr) as usize]);
            let (early, late) = (w(0.2, 0.5), w(2.5, 3.0));
            println!(
                "prog {prog}: early {early:.5} ({:.1} dB), late {late:.5} ({:.1} dB), \
                 drop {:.1} dB",
                20.0 * early.max(1e-9).log10(),
                20.0 * late.max(1e-9).log10(),
                20.0 * (early.max(1e-9) / late.max(1e-9)).log10()
            );
        }
    }

    /// The bus glue must tame loud material, pass quiet material nearly
    /// unchanged, and never blow up.
    #[test]
    fn glue_compresses_and_stays_sane() {
        let sr = 44100.0;
        let mut glue = BusGlue::new(sr);
        let mut l: Vec<f32> = (0..44100)
            .map(|i| (i as f32 * 220.0 / sr * std::f32::consts::TAU).sin() * 0.8)
            .collect();
        let mut r = l.clone();
        glue.process(&mut l, &mut r);
        let out_peak = l[22050..].iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(out_peak < 0.8, "no gain reduction: {out_peak}");
        assert!(out_peak > 0.3, "over-compressed: {out_peak}");
        assert!(l.iter().all(|x| x.is_finite()));

        let mut glue2 = BusGlue::new(sr);
        let mut ql: Vec<f32> = (0..44100)
            .map(|i| (i as f32 * 220.0 / sr * std::f32::consts::TAU).sin() * 0.05)
            .collect();
        let mut qr = ql.clone();
        glue2.process(&mut ql, &mut qr);
        let q_peak = ql[22050..].iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(
            (q_peak - 0.05).abs() < 0.012,
            "quiet signal changed: {q_peak}"
        );
    }

    /// Isolate the fundamental, find interpolated rising zero-crossings,
    /// smooth the per-cycle frequency over 8 cycles, and report max − min:
    /// how far the pitch wanders inside the segment.
    fn cycle_freq_spread(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(700.0, sr);
        let mut lp2 = OnePole::lowpass(700.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut times = Vec::new();
        for i in 1..f.len() {
            if f[i - 1] <= 0.0 && f[i] > 0.0 {
                times.push((i - 1) as f32 - f[i - 1] / (f[i] - f[i - 1]));
            }
        }
        let freqs: Vec<f32> = times.windows(2).map(|w| sr / (w[1] - w[0])).collect();
        let smooth: Vec<f32> = freqs
            .windows(8)
            .map(|w| w.iter().sum::<f32>() / 8.0)
            .collect();
        let hi = smooth.iter().fold(f32::MIN, |m, &x| m.max(x));
        let lo = smooth.iter().fold(f32::MAX, |m, &x| m.min(x));
        hi - lo
    }

    /// Like [`cycle_freq_spread`], but ZERO-PHASE band-limits around `f0` first
    /// so a sub-octave partial cannot leak into the fundamental's zero-crossing
    /// count and inflate the reading. GM19's 16' foundation adds a partial at
    /// `f0/2`; that sub-octave sits inside `cycle_freq_spread`'s 700 Hz passband
    /// and wanders its per-cycle frequency estimate. A single causal high/band-
    /// pass would RING and bias the spread further UP, so we apply a `Biquad`
    /// bandpass forward, reverse the buffer, filter again, and reverse back
    /// (filtfilt): the two passes cancel phase and ringing, leaving a real pitch
    /// vibrato (whose fundamental stays inside the [0.75·f0, 1.5·f0] band)
    /// untouched while rejecting the f0/2 sub-octave and 2·f0 harmonic.
    fn cycle_freq_spread_f0(seg: &[f32], sr: f32, f0: f32) -> f32 {
        // Q ≈ 1.3 puts the single-pass −3 dB skirts near [0.75·f0, 1.5·f0]; the
        // second (reverse) pass squares the magnitude, deepening sub-octave and
        // harmonic rejection without adding phase distortion.
        let q = 1.3;
        let mut fwd = Biquad::bandpass(f0, q, sr);
        let forward: Vec<f32> = seg.iter().map(|&x| fwd.process(x)).collect();
        let mut rev = Biquad::bandpass(f0, q, sr);
        let mut back: Vec<f32> = forward.iter().rev().map(|&x| rev.process(x)).collect();
        back.reverse();
        cycle_freq_spread(&back, sr)
    }

    fn render_cc1_program(program: u8, cc1: Option<u8>, cc1_before_note: bool) -> Vec<f32> {
        let mut events = Vec::new();
        if program == 19 {
            events.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ));
        }
        events.extend([
            (
                0.0,
                EvKind::Prog {
                    ch: 0,
                    prog: program,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
        ]);
        if cc1_before_note {
            if let Some(val) = cc1 {
                events.push((0.0, EvKind::Cc { ch: 0, num: 1, val }));
            }
        }
        events.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 69,
                vel: 100,
            },
        ));
        if !cc1_before_note {
            if let Some(val) = cc1 {
                events.push((0.60, EvKind::Cc { ch: 0, num: 1, val }));
            }
        }
        events.push((3.85, EvKind::NoteOff { ch: 0, key: 69 }));
        left(&render(&test_song(events, 4.0), &test_opts(44100.0)).0)
    }

    fn render_cc1_events(events: Vec<(f64, EvKind)>) -> Vec<f32> {
        left(&render(&test_song(events, 4.0), &test_opts(44100.0)).0)
    }

    fn am_rate(mono: &[f32], sr: f32, t0: f32, t1: f32) -> f32 {
        let mut env_lps = [OnePole::lowpass(12.0, sr); 4];
        let env: Vec<f32> = mono
            .iter()
            .map(|&x| {
                let mut y = x.abs();
                for lp in env_lps.iter_mut() {
                    y = lp.process(y);
                }
                y
            })
            .collect();
        let mut trend = OnePole::lowpass(1.2, sr);
        let det: Vec<f32> = env.iter().map(|&x| x - trend.process(x)).collect();
        let seg = &det[(t0 * sr) as usize..(t1 * sr) as usize];
        let crossings = seg.windows(2).filter(|w| w[0] <= 0.0 && w[1] > 0.0).count();
        crossings as f32 / (t1 - t0)
    }

    fn render_bowed_program_with_mod(program: u8, mod_val: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (
                    0.0,
                    EvKind::Prog {
                        ch: 0,
                        prog: program,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: mod_val,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 100,
                    },
                ),
                (2.4, EvKind::NoteOff { ch: 0, key: 69 }),
            ],
            2.5,
        );
        left(&render(&song, &test_opts(44100.0)).0)
    }

    fn render_bowed_controls(
        program: u8,
        key: u8,
        mod_val: u8,
        aftertouch: u8,
        samples: bool,
    ) -> Vec<f32> {
        let song = test_song(
            vec![
                (
                    0.0,
                    EvKind::Prog {
                        ch: 0,
                        prog: program,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: mod_val,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key,
                        vel: 100,
                    },
                ),
                (
                    0.10,
                    EvKind::Aftertouch {
                        ch: 0,
                        val: aftertouch,
                    },
                ),
                (2.4, EvKind::NoteOff { ch: 0, key }),
            ],
            2.5,
        );
        let opt = Options {
            samples,
            ..test_opts(44100.0)
        };
        left(&render(&song, &opt).0)
    }

    fn render_bowed_with_mod(mod_val: u8) -> Vec<f32> {
        render_bowed_program_with_mod(40, mod_val)
    }

    /// CC1 = 127 on a bowed note must produce a periodic pitch deviation
    /// far beyond the voice's own gentle vibrato; CC1 = 0 must not.
    #[test]
    fn cc1_mod_wheel_adds_vibrato() {
        let sr = 44100.0;
        let plain = render_bowed_with_mod(0);
        let modded = render_bowed_with_mod(127);
        let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let spread_plain = cycle_freq_spread(&plain[a..b], sr);
        let spread_mod = cycle_freq_spread(&modded[a..b], sr);
        // 35 cents of vibrato on A4 swings ~18 Hz peak-to-peak
        assert!(
            spread_mod > 10.0,
            "mod vibrato too shallow: {spread_mod} Hz"
        );
        assert!(
            spread_mod > 2.0 * spread_plain,
            "plain {spread_plain} Hz vs mod {spread_mod} Hz"
        );
    }

    #[test]
    fn gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato() {
        let sr = 44100.0;
        let routed = crate::voices::make(110, 69, 100, sr, 5, true);
        assert_eq!(
            routed.kind(),
            "bowed",
            "GM 110 must use the bowed/LA fiddle path"
        );
        assert!(vibrato_family(110), "GM 110 must take authored CC1 vibrato");
        assert_eq!(
            fx_profile(110, 0),
            fx_profile(40, 0),
            "GM 110 should use the fiddle bus profile"
        );

        let plain = render_bowed_program_with_mod(110, 0);
        let modded = render_bowed_program_with_mod(110, 127);
        let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let spread_plain = cycle_freq_spread(&plain[a..b], sr);
        let spread_mod = cycle_freq_spread(&modded[a..b], sr);
        assert!(
            spread_mod > 10.0,
            "GM 110 mod vibrato too shallow: {spread_mod} Hz"
        );
        assert!(
            spread_mod > 2.0 * spread_plain,
            "GM 110 plain {spread_plain} Hz vs mod {spread_mod} Hz"
        );
    }

    /// Natural vibrato, CC1 and channel aftertouch compose without either
    /// cancelling into dropouts or exceeding the signed pitch bound.
    #[test]
    fn bowed_natural_cc1_aftertouch_composition_is_bounded() {
        let sr = 44100.0;
        let range = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let cents = |spread_hz: f32, f0: f32| {
            let half = spread_hz * 0.5;
            1200.0 * ((f0 + half) / f0).log2()
        };
        // GM43 is a bowed-string *waveguide* (harmonic-rich): its strong low
        // partials (H2/H3 rival H1) fool the zero-crossing `cycle_freq_spread`
        // into reading a huge false pitch spread. Its pitch bound is enforced
        // with an autocorrelation measure in `bowedstring_gm43_pitch_bounded`.
        for (program, key, samples) in [
            (40u8, 69u8, false),
            (110, 69, false),
            (40, 69, true),
            (110, 69, true),
        ] {
            let plain = render_bowed_controls(program, key, 0, 0, samples);
            let modded = render_bowed_controls(program, key, 127, 0, samples);
            let composed = render_bowed_controls(program, key, 127, 127, samples);
            let f0 = crate::dsp::key_freq(key);
            let plain_c = cents(cycle_freq_spread(&plain[range.0..range.1], sr), f0);
            let mod_c = cents(cycle_freq_spread(&modded[range.0..range.1], sr), f0);
            let both_c = cents(cycle_freq_spread(&composed[range.0..range.1], sr), f0);
            assert!(
                (4.0..=12.0).contains(&plain_c),
                "GM{program} samples={samples}: autonomous excursion {plain_c:.1} cents"
            );
            assert!(
                mod_c >= 2.0 * plain_c,
                "GM{program} samples={samples}: CC1 {mod_c:.1} vs natural {plain_c:.1} cents"
            );
            assert!(
                both_c < 75.0,
                "GM{program} samples={samples}: composed excursion {both_c:.1} cents"
            );

            let seg = &composed[range.0..range.1];
            let win = (0.01 * sr) as usize;
            let levels: Vec<f32> = seg.chunks(win).map(rms).collect();
            let mut ordered = levels.clone();
            ordered.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let median = ordered[ordered.len() / 2];
            let floor = levels.iter().copied().fold(f32::INFINITY, f32::min);
            assert!(
                floor >= 0.25 * median,
                "GM{program} samples={samples}: controller beat dropout {floor:.5} vs median {median:.5}"
            );
        }
    }

    /// Robust fundamental-frequency spread (cents) via per-window
    /// autocorrelation with a parabolic peak refine. Unlike zero-crossing
    /// counting, autocorrelation locks to the fundamental *period* even when the
    /// low harmonics are strong (a bowed string's H2/H3 rival H1), so it does
    /// not mis-read a harmonic-rich waveguide's stable pitch as unstable.
    fn autocorr_cents_spread(seg: &[f32], sr: f32, f0: f32) -> f32 {
        let win = 2048usize;
        let hop = 2048usize;
        let lag_lo = (sr / (f0 * 1.5)).floor().max(2.0) as usize;
        let lag_hi = ((sr / (f0 * 0.67)).ceil() as usize).min(win - 2);
        let mut freqs = Vec::new();
        let mut start = 0;
        while start + win <= seg.len() {
            let w = &seg[start..start + win];
            let mean = w.iter().sum::<f32>() / win as f32;
            let acf = |lag: usize| -> f32 {
                let mut a = 0.0f32;
                for i in 0..(win - lag) {
                    a += (w[i] - mean) * (w[i + lag] - mean);
                }
                a
            };
            let mut best_lag = lag_lo;
            let mut best = f32::MIN;
            for lag in lag_lo..=lag_hi {
                let a = acf(lag);
                if a > best {
                    best = a;
                    best_lag = lag;
                }
            }
            // sub-lag parabolic refine for sub-cent resolution
            let refined = if best_lag > lag_lo && best_lag < lag_hi {
                let (y0, y1, y2) = (acf(best_lag - 1), best, acf(best_lag + 1));
                let d = y0 - 2.0 * y1 + y2;
                best_lag as f32 + if d != 0.0 { 0.5 * (y0 - y2) / d } else { 0.0 }
            } else {
                best_lag as f32
            };
            freqs.push(sr / refined);
            start += hop;
        }
        if freqs.len() < 2 {
            return 0.0;
        }
        let hi = freqs.iter().copied().fold(f32::MIN, f32::max);
        let lo = freqs.iter().copied().fold(f32::MAX, f32::min);
        1200.0 * (hi / lo).log2()
    }

    /// GM43 waveguide: autonomous pitch is a gentle vibrato + human drift, CC1
    /// deepens it, and CC1 + aftertouch compose without a runaway excursion or
    /// amplitude dropouts — the same invariants as the saw-voice test above, but
    /// measured with autocorrelation (robust to the waveguide's strong low
    /// harmonics, which the zero-crossing measure cannot count correctly).
    #[test]
    fn bowedstring_gm43_pitch_bounded() {
        let sr = 44100.0;
        let range = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        for (key, samples) in [(45u8, false), (45u8, true), (40u8, false)] {
            let f0 = crate::dsp::key_freq(key);
            let plain = render_bowed_controls(43, key, 0, 0, samples);
            let modded = render_bowed_controls(43, key, 127, 0, samples);
            let composed = render_bowed_controls(43, key, 127, 127, samples);
            let plain_c = autocorr_cents_spread(&plain[range.0..range.1], sr, f0);
            let mod_c = autocorr_cents_spread(&modded[range.0..range.1], sr, f0);
            let both_c = autocorr_cents_spread(&composed[range.0..range.1], sr, f0);
            // autonomous pitch is the deepened natural arco vibrato + human drift.
            // Measured ~28-32 cents pk-pk since the bass vibrato was deepened to a
            // realistic depth (was ~10-12 when the vibrato ran ~5-10x too shallow) —
            // present and expressive, but bounded, never a runaway warble.
            assert!(
                (3.0..=42.0).contains(&plain_c),
                "GM43 key={key} samples={samples}: autonomous excursion {plain_c:.1} cents"
            );
            // CC1 clearly deepens the vibrato
            assert!(
                mod_c >= 2.0 * plain_c,
                "GM43 key={key} samples={samples}: CC1 {mod_c:.1} vs natural {plain_c:.1} cents"
            );
            // CC1 + aftertouch compose without a runaway (the zero-crossing
            // measure read a false ~1780 cents here; the true excursion is ~130
            // with the deepened natural vibrato underneath the maxed controllers)
            assert!(
                both_c < 150.0,
                "GM43 key={key} samples={samples}: composed excursion {both_c:.1} cents"
            );
            // no controller-induced amplitude dropouts
            let seg = &composed[range.0..range.1];
            let win = (0.01 * sr) as usize;
            let levels: Vec<f32> = seg.chunks(win).map(rms).collect();
            let mut ordered = levels.clone();
            ordered.sort_by(|a, b| a.partial_cmp(b).unwrap());
            let median = ordered[ordered.len() / 2];
            let floor = levels.iter().copied().fold(f32::INFINITY, f32::min);
            assert!(
                floor >= 0.25 * median,
                "GM43 key={key} samples={samples}: controller beat dropout {floor:.5} vs median {median:.5}"
            );
        }
    }

    #[test]
    fn bagpipe_shanai_route_to_reed_engine_with_drone_or_double_reed() {
        let sr = 44100.0;
        assert_eq!(
            crate::voices::make(109, 67, 100, sr, 5, false).kind(),
            "reed",
            "GM109 bagpipe chanter must use the reed voice"
        );
        assert_eq!(
            crate::voices::make(111, 72, 100, sr, 5, false).kind(),
            "reed",
            "GM111 shanai must use the reed voice"
        );
        assert!(vibrato_family(109), "bagpipe should take authored reed CC1");
        assert!(vibrato_family(111), "shanai should take authored reed CC1");

        let bagpipe = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 109 }),
                (
                    0.0,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 43,
                        vel: 70,
                    },
                ),
                (
                    0.12,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 67,
                        vel: 104,
                    },
                ),
                (0.42, EvKind::NoteOff { ch: 0, key: 67 }),
                (
                    0.50,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 104,
                    },
                ),
                (0.82, EvKind::NoteOff { ch: 0, key: 69 }),
                (1.10, EvKind::NoteOff { ch: 0, key: 43 }),
            ],
            1.45,
        );
        let (bagpipe_out, stats) = render(&bagpipe, &test_opts(sr));
        assert_eq!(
            stats.voices_spawned, 3,
            "one low drone control plus two chanters should spawn one channel drone and two reed chanters"
        );
        let bagpipe_l = left(&bagpipe_out);
        let root = key_freq(43);
        let fifth = root * 1.5;
        let drone_only = &bagpipe_l[(0.05 * sr) as usize..(0.11 * sr) as usize];
        let drone_root = crate::testutil::band_rms(drone_only, sr, root, 8.0);
        let drone_fifth = crate::testutil::band_rms(drone_only, sr, fifth, 8.0);
        let drone_level = rms(drone_only);
        assert!(
            drone_root > 0.18 * drone_level,
            "bagpipe drone root band weak: root/drone {:.3}",
            drone_root / drone_level.max(1e-9)
        );
        // Highland drones are OCTAVES (tenor pair + bass), never a dedicated
        // fifth oscillator. The bound allows the bass drone's own 3rd
        // harmonic (an odd-harmonic square at root/2 puts its 3rd exactly on
        // the twelfth, ≈0.41 of root here — physically real on any pipe) but
        // rejects the old fifth oscillator (measured 0.73 of root).
        assert!(
            drone_fifth < 0.55 * drone_root,
            "bagpipe drone carries a FIFTH ({:.3} of root) — Highland drones \
             are a tenor pair plus a bass octave",
            drone_fifth / drone_root.max(1e-9)
        );
        let body = &bagpipe_l[(0.20 * sr) as usize..(0.74 * sr) as usize];
        let body_rms = rms(body);
        let body_drone = crate::testutil::band_rms(body, sr, root, 8.0);
        let body_bass = crate::testutil::band_rms(body, sr, root * 0.5, 6.0);
        let chanter = crate::testutil::band_rms(body, sr, key_freq(67), 10.0)
            + crate::testutil::band_rms(body, sr, key_freq(69), 10.0);
        assert!(
            body_drone > 0.06 * body_rms && chanter > 0.10 * body_rms,
            "bagpipe needs drone plus chanter: drone/body {:.3}, chanter/body {:.3}",
            body_drone / body_rms.max(1e-9),
            chanter / body_rms.max(1e-9)
        );
        assert!(
            body_bass > 0.04 * body_rms,
            "bagpipe drone has no bass octave: bass/body {:.3}",
            body_bass / body_rms.max(1e-9)
        );
        assert!(
            body_rms < 0.12,
            "bagpipe drone+chanter level too hot before normalisation: {body_rms:.4}"
        );
        let release_tail = rms(&bagpipe_l[(1.30 * sr) as usize..(1.42 * sr) as usize]);
        assert!(
            release_tail < 0.25 * body_rms,
            "bagpipe drone did not release with the channel: tail/body {:.3}",
            release_tail / body_rms.max(1e-9)
        );

        let render_voice = |program: u8, key: u8, secs: f32| {
            let mut voice = crate::voices::make(program, key, 110, sr, 9, false);
            let mut buf = vec![0f32; (secs * sr) as usize];
            voice.render(&mut buf);
            buf
        };
        let shanai = render_voice(111, 72, 1.4);
        let clarinet = render_voice(71, 72, 1.4);
        let seg_start = (0.35 * sr) as usize;
        let seg_end = (1.20 * sr) as usize;
        let sh_seg = &shanai[seg_start..seg_end];
        let cl_seg = &clarinet[seg_start..seg_end];
        let prom = |s: &[f32], f: f32| crate::testutil::band_rms(s, sr, f, 2.5) / rms(s).max(1e-9);
        assert!(
            prom(sh_seg, 1200.0) > 1.25 * prom(cl_seg, 1200.0),
            "shanai nasal formant too weak vs clarinet: {:.3} vs {:.3}",
            prom(sh_seg, 1200.0),
            prom(cl_seg, 1200.0)
        );
        let f0 = key_freq(72);
        let sh_h1 = crate::testutil::band_rms(sh_seg, sr, f0, 12.0);
        let sh_h2 = crate::testutil::band_rms(sh_seg, sr, f0 * 2.0, 12.0);
        let cl_h1 = crate::testutil::band_rms(cl_seg, sr, f0, 12.0);
        let cl_h2 = crate::testutil::band_rms(cl_seg, sr, f0 * 2.0, 12.0);
        assert!(
            sh_h2 / sh_h1.max(1e-9) > 2.0 * (cl_h2 / cl_h1.max(1e-9)),
            "shanai should be even-rich like a double reed: shanai {:.3}, clarinet {:.3}",
            sh_h2 / sh_h1.max(1e-9),
            cl_h2 / cl_h1.max(1e-9)
        );

        let high = render_voice(111, 87, 0.24);
        let seg = &high[(0.06 * sr) as usize..(0.22 * sr) as usize];
        let f_alias = sr / 35.5;
        let fund = crate::testutil::mag_at(seg, sr, f_alias).max(1e-12);
        let mut acc = 0.0f64;
        let mut cnt = 0u32;
        let mut k = 1.5f32;
        while f_alias * k < 0.4 * sr {
            let r = crate::testutil::mag_at(seg, sr, f_alias * k) / fund;
            acc += (r as f64) * (r as f64);
            cnt += 1;
            k += 1.0;
        }
        let alias = (acc / cnt as f64).sqrt() as f32;
        assert!(
            alias < 0.03,
            "shanai fold-back alias floor too high: {alias:.4}"
        );
    }

    /// BP-O3: the channel drone is CONTINUOUS across chanter note boundaries.
    /// A real set of pipes never stops its drones between melody notes; the
    /// old engine released the drone at every chanter NoteOff (when no other
    /// chanter rang) and spawned a FRESH one — at the NEW note's pitch — on
    /// the next NoteOn: an amplitude notch plus a pitch lurch at every note
    /// boundary. One latched drone per channel, released only by an authored
    /// drone-control stop or the block-rate hang timer (the bag emptying).
    #[test]
    fn bagpipe_drone_is_continuous_across_chanter_note_boundaries() {
        let sr = 44100.0;
        // A plain chanter melody — NO low drone-control note (the shape of a
        // real-world GM 109 file): two notes with a 20 ms articulation gap.
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 109 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 67,
                        vel: 96,
                    },
                ),
                (0.60, EvKind::NoteOff { ch: 0, key: 67 }),
                (
                    0.62,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 96,
                    },
                ),
                (1.20, EvKind::NoteOff { ch: 0, key: 69 }),
            ],
            1.30,
        );
        let (out, stats) = render(&song, &test_opts(sr));
        let l = left(&out);
        let win = |a: f32, b: f32| &l[(a * sr) as usize..(b * sr) as usize];
        // Tenor drones sit an octave below the FIRST chanter note (196 Hz)
        // and must still be there, at the SAME pitch, during the second note.
        let tenor_w1 = crate::testutil::band_rms(win(0.25, 0.55), sr, 196.0, 8.0);
        let tenor_w2 = crate::testutil::band_rms(win(0.70, 1.15), sr, 196.0, 8.0);
        let tenor_hold = tenor_w2 / tenor_w1.max(1e-9);
        // The bass drone (98 Hz — steady, no beat partner) must not notch at
        // the 0.60/0.62 boundary: 100 ms windows, 50 ms hop, min vs median.
        let mut env98: Vec<(f32, f32)> = Vec::new();
        let mut t = 0.20f32;
        while t + 0.10 <= 1.151 {
            env98.push((
                t,
                crate::testutil::band_rms(win(t, t + 0.10), sr, 98.0, 8.0),
            ));
            t += 0.05;
        }
        let mut all: Vec<f32> = env98.iter().map(|&(_, e)| e).collect();
        all.sort_by(|a, b| a.partial_cmp(b).unwrap());
        let med = all[all.len() / 2];
        let dip = env98
            .iter()
            .filter(|&&(t0, _)| (0.40..=0.90).contains(&t0))
            .map(|&(_, e)| e)
            .fold(f32::INFINITY, f32::min)
            / med.max(1e-9);
        let body = rms(win(0.25, 1.15));
        println!(
            "BP-O3: voices {}, tenor hold {tenor_hold:.3}, bass med/body {:.3}, \
             bass dip {dip:.3}",
            stats.voices_spawned,
            med / body.max(1e-9)
        );
        // ONE drone for the whole channel: 2 chanters + 1 drone. The per-note
        // release/re-spawn bug spawned a second drone (4 voices).
        assert_eq!(
            stats.voices_spawned, 3,
            "two chanter notes must share ONE latched channel drone \
             (2 chanters + 1 drone); more means a re-spawn per note"
        );
        // The sharp presence discriminator: pre-fix the 98 Hz band was pure
        // leakage floor (0.023 of body); the real bass drone reads ~0.13.
        assert!(
            med > 0.06 * body,
            "the drone has no steady bass octave at 98 Hz (med/body {:.4})",
            med / body.max(1e-9)
        );
        // The tenor PAIR beats (~0.78 Hz), so this band's level swings with
        // beat phase across the two windows (deterministically 0.41 here);
        // the floor only requires the tenors to still be audibly present.
        assert!(
            tenor_hold >= 0.25,
            "tenor drone collapsed across the note boundary (note2/note1 \
             196 Hz band {tenor_hold:.3}) — released and re-spawned at the \
             new note's pitch"
        );
        assert!(
            dip >= 0.5,
            "bass drone notches at the chanter note boundary: min/median {dip:.3}"
        );
    }

    // --- GM 109 sampled bagpipe oracles (HLD 2026.07.17 §7) ------------------

    #[cfg(test)]
    fn bp_opts(sr: f32, samples: bool) -> Options {
        Options {
            samples,
            ..test_opts(sr)
        }
    }

    /// A held note on ch0 program 109, optional alt-bank (CC0 = `bank`).
    #[cfg(test)]
    fn bagpipe_song(key: u8, secs: f64, bank: Option<u8>) -> Song {
        let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog: 109 })];
        if let Some(v) = bank {
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: v,
                },
            ));
        }
        ev.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            },
        ));
        ev.push((secs - 0.1, EvKind::NoteOff { ch: 0, key }));
        test_song(ev, secs)
    }

    /// Dispatch + the MANDATORY alt-bank arm (§7.2). Samples-on the default bank
    /// engages the SAMPLED bagpipe (differs from the model); the CC0 alt bank and
    /// samples-off both render the MODEL, byte-identical — proving the model
    /// stays reachable and that BOTH halves (chanter via altbank::make, drone via
    /// ensure_bagpipe_drone reading alt_bank) honour the bank.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn bagpipe_sampled_dispatch_and_alt_bank_are_coherent() {
        let sr = 44100.0;
        let bits = |v: &[f32]| v.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        let (model, _) = render(&bagpipe_song(69, 1.0, None), &bp_opts(sr, false));
        let (sampled, _) = render(&bagpipe_song(69, 1.0, None), &bp_opts(sr, true));
        let (alt, _) = render(&bagpipe_song(69, 1.0, Some(1)), &bp_opts(sr, true));
        assert_ne!(
            bits(&model),
            bits(&sampled),
            "samples-on 109 did not engage the sampled bagpipe"
        );
        assert_eq!(
            bits(&alt),
            bits(&model),
            "alt-bank (CC0=1) 109 must render the byte-identical model — the \
             mandatory altbank arm is missing, or the drone ignored alt_bank"
        );
    }

    /// The sampled drone's octave stack AND the drone-control branch (§7.6b).
    /// A drone-control note (key <= 54) sounds the tenor AT its key pitch, with
    /// the bass an octave below. Key 43 (G2, ~98 Hz) must therefore show energy
    /// at ~98 (tenor at pitch) and ~49 (bass octave below). If the at-pitch
    /// branch were dropped, the tenor would sit at ~49 and 98 would be empty.
    /// Level stays near the modeled drone (§7.6c balance).
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn bagpipe_sampled_drone_octave_and_control_pitch() {
        let sr = 44100.0;
        // drone-control note only (no chanter): key 43 spawns the drone at pitch
        let song = {
            let ev = vec![
                (0.0, EvKind::Prog { ch: 0, prog: 109 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 43,
                        vel: 100,
                    },
                ),
                (1.4, EvKind::NoteOff { ch: 0, key: 43 }),
            ];
            test_song(ev, 1.5)
        };
        let (out, _) = render(&song, &bp_opts(sr, true));
        let l = left(&out);
        let win = &l[(0.4 * sr) as usize..(1.2 * sr) as usize];
        let tenor = crate::testutil::band_rms(win, sr, 98.0, 8.0);
        let bass = crate::testutil::band_rms(win, sr, 49.0, 6.0);
        let body = rms(win).max(1e-9);
        assert!(
            tenor > 0.06 * body,
            "no tenor at the control pitch (98 Hz {:.4} of body) — the \
             drone-control at-pitch branch is missing",
            tenor / body
        );
        assert!(
            bass > 0.04 * body,
            "no bass octave below (49 Hz {:.4} of body)",
            bass / body
        );
        // balance: within a factor of the modeled drone's level (not swamping)
        let (m, _) = render(&song, &bp_opts(sr, false));
        let (rs, rm) = (rms(&left(&out)), rms(&left(&m)).max(1e-9));
        assert!(
            (0.4..=2.5).contains(&(rs / rm)),
            "sampled drone level {rs:.4} is off the modeled {rm:.4} (x{:.2})",
            rs / rm
        );
    }

    /// Coverage extremes (§7.8): the step clamp and the ratio-then-SRC order.
    /// Spawn keys 55 / 81 / 84 (drive the drone repitch past the guard) at
    /// 44.1 / 48 / 96 kHz — every render must be finite and non-silent, never a
    /// panic, NaN, silence, or wild pitch.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn bagpipe_sampled_coverage_extremes_are_finite() {
        for &sr in &[44100.0f32, 48000.0, 96000.0] {
            for &key in &[55u8, 81, 84] {
                let (out, _) = render(&bagpipe_song(key, 0.6, None), &bp_opts(sr, true));
                assert!(
                    out.iter().all(|x| x.is_finite()),
                    "non-finite sample at key {key}, {sr} Hz"
                );
                assert!(
                    rms(&left(&out)) > 1e-4,
                    "silent render at key {key}, {sr} Hz"
                );
            }
        }
    }

    /// Vibrato depth as max-min of a peak-located (Goertzel) pitch track —
    /// robust on the lead's bright, detuned spectrum where the zero-crossing
    /// `cycle_freq_spread` lies (repo lesson).
    fn pitch_spread(sig: &[f32], sr: f32, f_lo: f32, f_hi: f32) -> f32 {
        let w = (0.08 * sr) as usize;
        let hop = (0.02 * sr) as usize;
        let (mut lo, mut hi) = (f32::MAX, f32::MIN);
        let mut i = 0;
        while i + w <= sig.len() {
            let p = crate::testutil::peak_locate(&sig[i..i + w], sr, f_lo, f_hi);
            lo = lo.min(p);
            hi = hi.max(p);
            i += hop;
        }
        hi - lo
    }

    fn render_sawstack_with_mod(prog: u8, mod_val: Option<u8>) -> Vec<f32> {
        let mut events = vec![
            (0.0, EvKind::Prog { ch: 0, prog }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
        ];
        if let Some(val) = mod_val {
            events.push((0.0, EvKind::Cc { ch: 0, num: 1, val }));
        }
        events.extend([
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (2.4, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        left(&render(&test_song(events, 2.5), &test_opts(44100.0)).0)
    }

    fn render_lead_with_mod(mod_val: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 81 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: mod_val,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 100,
                    },
                ),
                (2.4, EvKind::NoteOff { ch: 0, key: 69 }),
            ],
            2.5,
        );
        left(&render(&song, &test_opts(44100.0)).0)
    }

    /// Oracle 5: CC1 gives a synth lead mod-wheel vibrato — the pitch wanders
    /// far more than the (detuned-stack) baseline with the wheel down.
    #[test]
    fn cc1_mod_wheel_adds_vibrato_on_lead() {
        let sr = 44100.0;
        let plain = render_lead_with_mod(0);
        let modded = render_lead_with_mod(127);
        let (a, b) = ((0.6 * sr) as usize, (2.2 * sr) as usize);
        let spread_plain = pitch_spread(&plain[a..b], sr, 400.0, 480.0);
        let spread_mod = pitch_spread(&modded[a..b], sr, 400.0, 480.0);
        assert!(
            spread_mod > 12.0,
            "lead mod vibrato too shallow: {spread_mod} Hz"
        );
        assert!(
            spread_mod > 2.0 * spread_plain,
            "plain {spread_plain} Hz vs mod {spread_mod} Hz"
        );
    }

    fn sawstack_legato_render(prog: u8, cc68: Option<u8>) -> (Vec<f32>, Stats) {
        let mut events = vec![(0.0, EvKind::Prog { ch: 0, prog })];
        if let Some(val) = cc68 {
            events.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 68,
                    val,
                },
            ));
        }
        events.extend([
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ),
            (
                0.30,
                EvKind::NoteOn {
                    ch: 0,
                    key: 64,
                    vel: 100,
                },
            ),
            (1.0, EvKind::NoteOff { ch: 0, key: 64 }),
        ]);
        let (stereo, stats) = render(&test_song(events, 1.2), &test_opts(44100.0));
        (left(&stereo), stats)
    }

    /// Req MM-REQ-KILN-00009: strings and choir opt into CC1 vibrato and CC68
    /// legato; pads stay outside the CC68 slur family.
    #[test]
    fn strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in() {
        let sr = 44100.0;
        for prog in 48..=54 {
            let untouched = render_sawstack_with_mod(prog, None);
            let wheel_zero = render_sawstack_with_mod(prog, Some(0));
            assert!(
                untouched
                    .iter()
                    .zip(&wheel_zero)
                    .all(|(a, b)| a.to_bits() == b.to_bits()),
                "program {prog} CC1=0 should not change an otherwise untouched channel"
            );

            let modded = render_sawstack_with_mod(prog, Some(127));
            let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
            let spread_plain = pitch_spread(&wheel_zero[a..b], sr, 360.0, 520.0);
            let spread_mod = pitch_spread(&modded[a..b], sr, 360.0, 520.0);
            assert!(
                spread_mod > 9.0,
                "program {prog} CC1 vibrato too shallow: {spread_mod} Hz"
            );
            assert!(
                spread_mod > 1.5 * spread_plain,
                "program {prog} plain {spread_plain} Hz vs mod {spread_mod} Hz"
            );

            assert_eq!(
                sawstack_legato_render(prog, None).1.voices_spawned,
                2,
                "program {prog} without CC68 must still re-attack"
            );
            let (slurred, stats) = sawstack_legato_render(prog, Some(127));
            assert_eq!(
                stats.voices_spawned, 1,
                "program {prog} with CC68 should slur into one voice"
            );
            let f_after = crate::testutil::peak_locate(
                &slurred[(0.55 * sr) as usize..(0.9 * sr) as usize],
                sr,
                300.0,
                360.0,
            );
            let want = key_freq(64);
            assert!(
                (f_after - want).abs() < 6.0,
                "program {prog} slurred pitch {f_after}, want {want}"
            );
        }

        assert_eq!(
            sawstack_legato_render(89, Some(127)).1.voices_spawned,
            2,
            "pads must stay outside the CC68 slur family"
        );
    }

    /// Round-2 GM019: the DEFAULT bank is the drawbar church organ with the
    /// CC1 Leslie (the voice the audition preferred); the CathedralOrgan
    /// pipe model is retired. A default-bank GM19 with CC1 pinned high must
    /// show the Leslie spin-up — the AM rate climbs from the chorale brake
    /// toward Leslie-fast — not the cathedral's fixed 5.5 Hz tremulant
    /// (whose rate never moved, only its depth).
    #[test]
    fn default_gm19_cc1_ramps_the_leslie() {
        let sr = 44100.0;
        let cc = |num: u8, val: u8| EvKind::Cc { ch: 0, num, val };
        let out = render_cc1_events(vec![
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (0.0, cc(93, 0)),
            (0.0, cc(1, 127)),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ),
        ]);
        let early = am_rate(&out, sr, 0.15, 1.15);
        let late = am_rate(&out, sr, 2.9, 3.9);
        assert!(
            late > early + 2.5 && late >= 5.5,
            "default GM19 CC1 must Leslie-ramp: early {early:.2} Hz late {late:.2} Hz"
        );
    }

    #[test]
    fn gm22_cc1_is_harmonica_vibrato_not_leslie() {
        let sr = 44100.0;

        let gm19 = render_cc1_program(19, Some(127), true);
        let gm19_early = am_rate(&gm19, sr, 0.15, 1.15);
        let gm19_late = am_rate(&gm19, sr, 2.9, 3.9);
        assert!(
            gm19_late > gm19_early + 2.5 && gm19_late >= 5.5,
            "GM19 Leslie ramp regressed: early {gm19_early:.2} Hz late {gm19_late:.2} Hz"
        );

        let gm22_plain = render_cc1_program(22, None, true);
        let gm22_mod = render_cc1_program(22, Some(127), true);
        let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let plain_spread = cycle_freq_spread(&gm22_plain[a..b], sr);
        let mod_spread = cycle_freq_spread(&gm22_mod[a..b], sr);
        assert!(
            mod_spread > 8.0 && mod_spread >= 2.0 * plain_spread.max(1.0),
            "GM22 CC1 should be pitch vibrato, not inert: plain {plain_spread:.2} Hz mod {mod_spread:.2} Hz"
        );
        assert!(
            !organ_leslie_family(22, 0),
            "GM22 must stay out of the Leslie controller branch"
        );

        for program in [20u8, 21, 23] {
            assert!(
                !organ_leslie_family(program, 0),
                "GM{program} must stay out of the Leslie controller branch"
            );
            let plain = render_cc1_program(program, None, true);
            let modded = render_cc1_program(program, Some(127), true);
            assert_eq!(modded, plain, "GM{program} CC1 must be inert");
        }

        let gm19_then_22 = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.019,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 0,
                },
            ),
            (0.02, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let changed_spread = cycle_freq_spread(&gm19_then_22[a..b], sr);
        assert!(
            changed_spread > 8.0,
            "program change 19->22 lost GM22 CC1 vibrato: {changed_spread:.2} Hz"
        );

        let gm22_then_19 = render_cc1_events(vec![
            (0.0, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.019,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.02, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let back_early = am_rate(&gm22_then_19, sr, 0.15, 1.15);
        let back_late = am_rate(&gm22_then_19, sr, 2.9, 3.9);
        assert!(
            back_late > back_early + 2.5 && back_late >= 5.5,
            "program change 22->19 lost Leslie ramp: early {back_early:.2} late {back_late:.2}"
        );

        let held_gm19_after_prog22 = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (
                0.59,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 0,
                },
            ),
            (0.60, EvKind::Prog { ch: 0, prog: 22 }),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let held19_early = am_rate(&held_gm19_after_prog22, sr, 0.15, 1.15);
        let held19_late = am_rate(&held_gm19_after_prog22, sr, 2.9, 3.9);
        // GM19's held note is key 69; its 16' foundation adds a partial at
        // key_freq(69)/2 that would leak into a plain zero-crossing spread. The
        // zero-phase f0-band-limited spread rejects that sub-octave (see
        // `cycle_freq_spread_f0`) so this measures the fundamental's pitch
        // wander only — GM19's Leslie is amplitude modulation, not vibrato.
        let held19_pitch_spread =
            cycle_freq_spread_f0(&held_gm19_after_prog22[a..b], sr, key_freq(69));
        println!(
            "gm22_cc1: held19_pitch_spread {held19_pitch_spread:.2} Hz (f0-filtered), GM22 mod_spread {mod_spread:.2} Hz plain_spread {plain_spread:.2} Hz"
        );
        assert!(
            held19_late > held19_early + 2.5 && held19_late >= 5.5,
            "held GM19 lost Leslie after program change to GM22: early {held19_early:.2} late {held19_late:.2}"
        );
        assert!(
            held19_pitch_spread < 4.0,
            "held GM19 picked up GM22 pitch vibrato after program change: {held19_pitch_spread:.2} Hz"
        );

        let held_gm22_after_prog19 = render_cc1_events(vec![
            (0.0, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (
                0.59,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.60, EvKind::Prog { ch: 0, prog: 19 }),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let held22_pitch_spread = cycle_freq_spread(&held_gm22_after_prog19[a..b], sr);
        assert!(
            held22_pitch_spread > 8.0,
            "held GM22 lost harmonica vibrato after program change to GM19: {held22_pitch_spread:.2} Hz"
        );

        let held_plain = render_cc1_program(22, None, false);
        let held_mod = render_cc1_program(22, Some(127), false);
        let held_plain_spread = cycle_freq_spread(&held_plain[(1.0 * sr) as usize..b], sr);
        let held_mod_spread = cycle_freq_spread(&held_mod[(1.0 * sr) as usize..b], sr);
        assert!(
            held_mod_spread > held_plain_spread + 6.0,
            "held GM22 note did not pick up CC1 vibrato: plain {held_plain_spread:.2} mod {held_mod_spread:.2}"
        );

        let reset = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.02,
                EvKind::Cc {
                    ch: 0,
                    num: 121,
                    val: 0,
                },
            ),
            (
                0.03,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 0,
                },
            ),
            (0.04, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.06,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let reset_early = am_rate(&reset, sr, 0.15, 1.15);
        let reset_late = am_rate(&reset, sr, 2.9, 3.9);
        let reset_spread = cycle_freq_spread(&reset[a..b], sr);
        // "CC121 did not leak CC1" means the post-reset channel must behave exactly
        // like a GM22 that never received CC1 — so measure against THAT control
        // rather than an absolute AM bound. GM22 has an intrinsic delayed-onset
        // vibrato whose AM ramps 0 -> ~6 Hz across the note, so an absolute
        // "must not rise" bound scores the harmonica's own voice, not a Leslie
        // leak. It held only because a Program Change used to re-derive chorus 0.20
        // over this setup's authored CC93=0, and that wash suppressed the envelope
        // detector; effect sends now survive a Program Change per RP-015
        // (MM-BUG-KILN-00033), so the control comparison is both correct and
        // stricter — it pins reset to the un-modulated voice instead of to a range.
        let plain_early = am_rate(&gm22_plain, sr, 0.15, 1.15);
        let plain_late = am_rate(&gm22_plain, sr, 2.9, 3.9);
        assert!(
            (reset_early - plain_early).abs() <= 1.0
                && (reset_late - plain_late).abs() <= 1.0
                && (reset_spread - plain_spread).abs() <= 1.0
                && reset_spread < mod_spread * 0.6,
            "GM reset leaked CC1 into GM22: AM {reset_early:.2}->{reset_late:.2} vs \
             never-modulated control {plain_early:.2}->{plain_late:.2}; spread \
             {reset_spread:.2} vs control {plain_spread:.2} / modulated {mod_spread:.2}"
        );

        let alt_plain = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        let alt_mod = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 22 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 127,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (3.85, EvKind::NoteOff { ch: 0, key: 69 }),
        ]);
        assert_eq!(
            alt_mod, alt_plain,
            "alt-bank GM22 must not take default-bank CC1 vibrato"
        );
    }

    /// CC1 = 127 on the secondary organ spins the tremulant up like a Leslie: the
    /// amplitude-modulation rate must climb over ~2 s, not jump.
    #[test]
    fn cc1_leslie_spins_up_with_inertia() {
        let sr = 44100.0;
        let song = test_song(
            vec![
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: 1,
                    },
                ),
                (0.0, EvKind::Prog { ch: 0, prog: 19 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 1,
                        val: 127,
                    },
                ),
                (
                    0.02,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 57,
                        vel: 100,
                    },
                ),
                (3.95, EvKind::NoteOff { ch: 0, key: 57 }),
            ],
            4.0,
        );
        let mono = left(&render(&song, &test_opts(sr)).0);
        // Count tremulant cycles (rising envelope crossings) per window with the
        // shared module `am_rate` follower (4× OnePole @12 Hz, detrended @1.2 Hz).
        // The old local follower here (2× @15 Hz, detrend @1.5 Hz) was under-
        // damped: it let the GM19 16' foundation's sub-octave partial leak into
        // the amplitude envelope and mis-counted the AM rate. The steeper module
        // follower is immune to that sub-octave — the real Leslie tremolo is pure
        // amplitude modulation and is unchanged.
        // CC1 = 127 is authored at t = 0, so the rotor starts at rest
        // (LESLIE_SLOW_HZ ≈ 0.9 Hz) and slews toward 6.8 Hz with a 1.5 s time
        // constant. The windowed AM rate averages ~2 Hz early (rotor still low
        // and climbing) and ~6 Hz late (settled fast). The `late >= 5.5` floor
        // matches every sibling Leslie-ramp assertion under the module `am_rate`
        // follower (`default_gm19_cc1_ramps_the_leslie`, the GM19 clauses of
        // `gm22_cc1_is_harmonica_vibrato_not_leslie`): the steeper 4× follower
        // resolves the settled fast rate as 6 detrended crossings/s, a touch
        // below the old under-damped follower's ~7.
        let early = am_rate(&mono, sr, 0.15, 1.15);
        let late = am_rate(&mono, sr, 2.9, 3.9);
        println!("cc1_leslie_spins_up_with_inertia: early {early:.2} Hz late {late:.2} Hz");
        assert!(
            late > early + 3.0,
            "sweep too narrow: early {early} Hz, late {late} Hz"
        );
        assert!(
            early < 3.5,
            "rotor started too fast (should brake to slow): {early} Hz"
        );
        assert!(late >= 5.5, "rotor never got fast: {late} Hz");
    }

    /// Anti-masking guard for the U7b Leslie/vibrato measurement redesign: the
    /// fixed measurements must still DISCRIMINATE a real defect, not trivially
    /// pass. (a) A STALLED Leslie (GM19, no CC1 authored — the rotor never
    /// ramps) reads a flat, low `am_rate` that must FAIL cc1_leslie's own
    /// discrimination (`late > early + 3.0` ramp AND `late >= 5.5` speed):
    /// measured stalled ≈ early 2 / late 5, active ≈ early 2 / late 6, so the
    /// pair separate. (b) The f0-band-limited cycle spread must still read LARGE
    /// (~20 Hz) for GM22's real pitch vibrato — the band-limit rejects GM19's
    /// 16' sub-octave without nulling a genuine vibrato.
    #[test]
    fn leslie_and_vibrato_measures_still_catch_defects() {
        let sr = 44100.0;
        let stalled = render_cc1_events(vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.02,
                EvKind::NoteOn {
                    ch: 0,
                    key: 57,
                    vel: 100,
                },
            ),
            (3.95, EvKind::NoteOff { ch: 0, key: 57 }),
        ]);
        let early = am_rate(&stalled, sr, 0.15, 1.15);
        let late = am_rate(&stalled, sr, 2.9, 3.9);
        assert!(
            !(late > early + 3.0 && late >= 5.5),
            "stalled Leslie would falsely pass cc1_leslie — the measurement masks a stuck rotor: early {early:.2} late {late:.2}"
        );

        let (a, b) = ((0.8 * sr) as usize, (2.2 * sr) as usize);
        let gm22_mod = render_cc1_program(22, Some(127), true);
        let gm22_f0 = cycle_freq_spread_f0(&gm22_mod[a..b], sr, key_freq(69));
        assert!(
            gm22_f0 > 8.0,
            "f0-band-limit nulled GM22's real pitch vibrato: {gm22_f0:.2} Hz"
        );
    }

    fn render_pluck_with_cc74(cc74: Option<u8>) -> Vec<f32> {
        let mut events = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 25 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 94,
                    val: 0,
                },
            ),
        ];
        if let Some(val) = cc74 {
            events.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 74,
                    val,
                },
            ));
        }
        events.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 64,
                vel: 110,
            },
        ));
        events.push((1.5, EvKind::NoteOff { ch: 0, key: 64 }));
        render(&test_song(events, 1.6), &test_opts(44100.0)).0
    }

    /// CC74 = 20 must strip the top off a bright pluck; CC74 = 127 must be
    /// a true bypass — bit-identical to a render with no filter in the path.
    #[test]
    fn cc74_brightness_filter() {
        let sr = 44100.0;
        let dark = left(&render_pluck_with_cc74(Some(20)));
        let open = render_pluck_with_cc74(Some(127));
        let none = render_pluck_with_cc74(None);
        assert!(open == none, "CC74=127 is not a true bypass");
        // fraction of energy above 3 kHz — collapses with the cutoff ~535 Hz
        let hf_frac = |sig: &[f32]| {
            let mut hp = Biquad::highpass(3000.0, 0.7, sr);
            let (mut hf, mut total) = (0.0f64, 0.0f64);
            for &x in sig {
                let y = hp.process(x);
                hf += (y * y) as f64;
                total += (x * x) as f64;
            }
            hf / total.max(1e-12)
        };
        let f_dark = hf_frac(&dark);
        let f_open = hf_frac(&left(&open));
        assert!(
            f_dark < 0.25 * f_open,
            "no darkening: dark {f_dark} vs open {f_open}"
        );
    }

    /// A NoteOff under the sustain pedal keeps ringing until CC64 lifts,
    /// then releases and dies away.
    #[test]
    fn cc64_sustain_pedal_holds_notes() {
        let sr = 44100.0;
        let events = |pedal: bool| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog: 19 })];
            if pedal {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 64,
                        val: 127,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((0.5, EvKind::NoteOff { ch: 0, key: 60 }));
            if pedal {
                ev.push((
                    2.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 64,
                        val: 0,
                    },
                ));
            }
            ev
        };
        let held = left(&render(&test_song(events(true), 3.2), &test_opts(sr)).0);
        let plain = left(&render(&test_song(events(false), 3.2), &test_opts(sr)).0);
        let w = |sig: &[f32], t0: f32, t1: f32| rms(&sig[(t0 * sr) as usize..(t1 * sr) as usize]);
        // a second past the NoteOff the pedalled organ still sounds
        let held_mid = w(&held, 1.4, 1.9);
        let plain_mid = w(&plain, 1.4, 1.9);
        assert!(
            held_mid > 10.0 * plain_mid.max(1e-9),
            "pedal didn't hold: {held_mid} vs {plain_mid}"
        );
        // pedal up at 2.0 s: released, and decayed away a second later
        let after = w(&held, 3.0, 3.4);
        assert!(
            after < 0.05 * held_mid,
            "pedal-up didn't release: {after} vs {held_mid}"
        );
    }

    /// --solo of a channel with no notes renders true silence, even when
    /// other channels are full of notes.
    #[test]
    fn solo_mutes_other_channels() {
        let sr = 44100.0;
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 25 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 60,
                        vel: 100,
                    },
                ),
                (
                    0.06,
                    EvKind::NoteOn {
                        ch: 2,
                        key: 67,
                        vel: 100,
                    },
                ),
                (0.5, EvKind::NoteOff { ch: 0, key: 60 }),
                (0.5, EvKind::NoteOff { ch: 2, key: 67 }),
            ],
            1.0,
        );
        let mut opt = test_opts(sr);
        opt.solo = 1 << 5; // channel 5 never plays a note
        let (out, stats) = render(&song, &opt);
        assert_eq!(stats.voices_spawned, 0);
        assert!(
            out.iter().all(|&x| x == 0.0),
            "solo of an empty channel must be silent"
        );
        // soloing channel 0 keeps exactly its own notes
        opt.solo = 1 << 0;
        let (out2, stats2) = render(&song, &opt);
        assert_eq!(stats2.voices_spawned, 1);
        assert!(out2.iter().any(|&x| x != 0.0));
    }

    // ---- v0.7 authored-controller checks on real rendered audio -----------

    /// Mean fundamental over a segment: lowpass to the fundamental, then
    /// count rising zero-crossings per second.
    fn mean_freq(seg: &[f32], sr: f32) -> f32 {
        let mut lp1 = OnePole::lowpass(700.0, sr);
        let mut lp2 = OnePole::lowpass(700.0, sr);
        let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
        let mut c = 0;
        for w in f.windows(2) {
            if w[0] <= 0.0 && w[1] > 0.0 {
                c += 1;
            }
        }
        c as f32 / (seg.len() as f32 / sr)
    }

    /// Fraction of a signal's energy above `hz`.
    fn energy_above(sig: &[f32], hz: f32, sr: f32) -> f64 {
        let mut hp = Biquad::highpass(hz, 0.7, sr);
        let (mut hi, mut total) = (0.0f64, 0.0f64);
        for &x in sig {
            let y = hp.process(x);
            hi += (y * y) as f64;
            total += (x * x) as f64;
        }
        hi / total.max(1e-12)
    }

    /// Fraction of a signal's energy in a band around `center`.
    fn band_frac(sig: &[f32], center: f32, q: f32, sr: f32) -> f64 {
        let mut bp = Biquad::bandpass(center, q, sr);
        let (mut band, mut total) = (0.0f64, 0.0f64);
        for &x in sig {
            let y = bp.process(x);
            band += (y * y) as f64;
            total += (x * x) as f64;
        }
        band / total.max(1e-12)
    }

    fn render_program_vowel(program: u8, cc70: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (
                    0.0,
                    EvKind::Prog {
                        ch: 0,
                        prog: program,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ), // dry: no chorus bus
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 70,
                        val: cc70,
                    },
                ),
                (
                    0.02,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 48,
                        vel: 90,
                    },
                ),
                (2.4, EvKind::NoteOff { ch: 0, key: 48 }),
            ],
            2.5,
        );
        left(&render(&song, &test_opts(44100.0)).0)
    }

    fn render_program_late_vowel(program: u8, cc70: Option<u8>) -> Vec<f32> {
        let mut events = vec![
            (
                0.0,
                EvKind::Prog {
                    ch: 0,
                    prog: program,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.02,
                EvKind::NoteOn {
                    ch: 0,
                    key: 48,
                    vel: 90,
                },
            ),
        ];
        if let Some(val) = cc70 {
            events.push((
                0.70,
                EvKind::Cc {
                    ch: 0,
                    num: 70,
                    val,
                },
            ));
        }
        events.push((2.4, EvKind::NoteOff { ch: 0, key: 48 }));
        left(&render(&test_song(events, 2.5), &test_opts(44100.0)).0)
    }

    fn render_choir_vowel(cc70: u8) -> Vec<f32> {
        render_program_vowel(52, cc70)
    }

    /// CC70 = 84 ("ah") opens the choir's upper formants (gains 0.60/0.35)
    /// far past CC70 = 0 ("mm", gains 0.30/0.10) — a measurable spectral
    /// shift on the sustained vowel, not just a level change.
    #[test]
    fn cc70_vowel_morph_opens_formants() {
        let sr = 44100.0;
        let mm = render_choir_vowel(0);
        let ah = render_choir_vowel(84);
        // measure well after the onset morph has settled to the CC70 vowel
        let (a, b) = ((1.0 * sr) as usize, (2.0 * sr) as usize);
        let f_mm = energy_above(&mm[a..b], 1500.0, sr);
        let f_ah = energy_above(&ah[a..b], 1500.0, sr);
        assert!(
            f_ah > 1.5 * f_mm,
            "vowel didn't open: mm {f_mm} vs ah {f_ah}"
        );
    }

    /// GM 91 choir-pad is also a formant-capable SawStack once the channel
    /// authors CC70; it must not stay on the plain lowpass pad path.
    #[test]
    fn choir_pad_91_cc70_vowel_morph_opens_formants() {
        let sr = 44100.0;
        let mm = render_program_vowel(91, 0);
        let ah = render_program_vowel(91, 84);
        let (a, b) = ((1.0 * sr) as usize, (2.0 * sr) as usize);
        let f_mm = energy_above(&mm[a..b], 1500.0, sr);
        let f_ah = energy_above(&ah[a..b], 1500.0, sr);
        assert!(
            f_ah > 1.5 * f_mm,
            "choir-pad vowel didn't open: mm {f_mm} vs ah {f_ah}"
        );

        // 91 is now a choir FORMANT by default (an open "aah"), so a late CC70
        // RETARGETS the vowel rather than opening one from a plain lowpass. A
        // contrasting closed "mm" (0) must audibly darken the default open vowel,
        // proving retargeting still works — while staying bit-inert until the
        // controller is actually authored.
        let plain = render_program_late_vowel(91, None);
        let late = render_program_late_vowel(91, Some(0));
        let (pre_a, pre_b) = ((0.2 * sr) as usize, (0.55 * sr) as usize);
        assert!(
            plain[pre_a..pre_b]
                .iter()
                .zip(&late[pre_a..pre_b])
                .all(|(a, b)| a.to_bits() == b.to_bits()),
            "future CC70 changed program 91 before the controller was authored"
        );
        let (a, b) = ((1.4 * sr) as usize, (2.2 * sr) as usize);
        let f_plain = energy_above(&plain[a..b], 1500.0, sr);
        let f_late = energy_above(&late[a..b], 1500.0, sr);
        assert!(
            f_late < 0.8 * f_plain,
            "late-authored closed vowel didn't retarget the default open choir formant: plain {f_plain} vs mm {f_late}"
        );
    }

    /// RPN 0 rescales the pitch-bend range and RPN 1 fine-tune is a constant
    /// pitch multiplier — both read off a plucked A4's rendered pitch.
    #[test]
    fn rpn_bend_range_and_fine_tune() {
        let sr = 44100.0;
        let cc = |num, val| EvKind::Cc { ch: 0, num, val };
        // Read the rendered pitch with a Goertzel peak refined by a parabolic
        // interpolation in log-frequency (the engine already routes precise
        // pitch through peak_locate). mean_freq's zero-crossing count quantizes
        // to ~0.5% over this window AND mis-counts when a bright pluck's 2nd
        // harmonic leaks past its 700 Hz lowpass — too coarse for the fine-tune
        // ratio, and timbre-sensitive (it tips when the steel voice brightens).
        let render_freq = |setup: Vec<(f64, EvKind)>, win: (f32, f32), band: (f32, f32)| -> f32 {
            let mut ev = vec![
                (0.0, EvKind::Prog { ch: 0, prog: 25 }),
                (0.0, cc(93, 0)),
                (0.0, cc(94, 0)),
            ];
            ev.extend(setup);
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 110,
                },
            ));
            ev.push((2.5, EvKind::NoteOff { ch: 0, key: 69 }));
            let mono = left(&render(&test_song(ev, 2.6), &test_opts(sr)).0);
            let seg = &mono[(win.0 * sr) as usize..(win.1 * sr) as usize];
            let c = crate::testutil::peak_locate(seg, sr, band.0, band.1);
            // parabolic vertex over the geometric (×1.005) neighbours of the peak
            let lm = crate::testutil::mag_at(seg, sr, c / 1.005);
            let cm = crate::testutil::mag_at(seg, sr, c);
            let hm = crate::testutil::mag_at(seg, sr, c * 1.005);
            let denom = lm - 2.0 * cm + hm;
            let delta = if denom.abs() > 1e-9 {
                (0.5 * (lm - hm) / denom).clamp(-1.0, 1.0)
            } else {
                0.0
            };
            c * 1.005f32.powf(delta)
        };
        // same half-deflection wheel; GM default range 2 vs RPN-widened 12
        let win = (0.25, 0.7);
        let narrow = render_freq(
            vec![(0.04, EvKind::Bend { ch: 0, semis: 1.0 })],
            win,
            (430.0, 510.0),
        );
        let wide = render_freq(
            vec![
                (0.01, cc(101, 0)),
                (0.01, cc(100, 0)),
                (0.01, cc(6, 12)),
                (0.04, EvKind::Bend { ch: 0, semis: 1.0 }),
            ],
            win,
            (560.0, 690.0),
        );
        // range 2 -> +1 semitone (~466 Hz); range 12 -> +6 semitones (~622 Hz)
        assert!((narrow - 466.2).abs() < 12.0, "narrow bend: {narrow} Hz");
        assert!((wide - 622.3).abs() < 20.0, "wide bend: {wide} Hz");
        // fine tune: RPN 1, +50 cents (MSB 96, LSB 0) with no wheel
        let plain = render_freq(vec![], win, (410.0, 475.0));
        let fine = render_freq(
            vec![(0.01, cc(101, 0)), (0.01, cc(100, 1)), (0.01, cc(6, 96))],
            win,
            (410.0, 475.0),
        );
        let ratio = fine / plain;
        assert!(
            (ratio - 2f32.powf(50.0 / 1200.0)).abs() < 0.008,
            "fine-tune ratio {ratio} (plain {plain} -> fine {fine})"
        );
    }

    /// Req MM-REQ-KILN-00008: Modal and Organ voices must honour the
    /// engine's composed pitch multiplier, not swallow it in the trait default.
    #[test]
    fn modal_organ_pitch_controls_move_sustained_notes() {
        let sr = 44100.0;
        let cc = |num, val| EvKind::Cc { ch: 0, num, val };
        let cases = [(11u8, "modal vibraphone"), (19u8, "organ")];

        let render_case =
            |prog: u8, mut ev: Vec<(f64, EvKind)>, seconds: f64| -> (Vec<f32>, Stats) {
                let mut base = vec![
                    (0.0, EvKind::Prog { ch: 0, prog }),
                    (0.0, cc(91, 0)),
                    (0.0, cc(93, 0)),
                    (0.0, cc(94, 0)),
                ];
                base.append(&mut ev);
                let (stereo, stats) = render(&test_song(base, seconds), &test_opts(sr));
                (left(&stereo), stats)
            };
        let peak = |sig: &[f32], t0: f32, t1: f32, lo: f32, hi: f32| {
            crate::testutil::peak_locate(&sig[(t0 * sr) as usize..(t1 * sr) as usize], sr, lo, hi)
        };

        for (prog, name) in cases {
            let (bent, _) = render_case(
                prog,
                vec![
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 110,
                        },
                    ),
                    (1.0, EvKind::Bend { ch: 0, semis: 1.0 }),
                    (2.45, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                2.7,
            );
            let pre = peak(&bent, 0.35, 0.80, 420.0, 460.0);
            let post = peak(&bent, 1.45, 2.10, 445.0, 490.0);
            assert!((pre - 440.0).abs() < 8.0, "{name}: pre-bend pitch {pre}");
            assert!(
                (post - 466.2).abs() < 10.0,
                "{name}: pitch bend stayed inert, got {post} Hz"
            );

            let (wide, _) = render_case(
                prog,
                vec![
                    (0.01, cc(101, 0)),
                    (0.01, cc(100, 0)),
                    (0.01, cc(6, 12)),
                    (0.04, EvKind::Bend { ch: 0, semis: 1.0 }),
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 110,
                        },
                    ),
                    (1.2, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                1.5,
            );
            let wide_pitch = peak(&wide, 0.35, 0.90, 585.0, 660.0);
            assert!(
                (wide_pitch - 622.3).abs() < 18.0,
                "{name}: RPN bend range stayed inert, got {wide_pitch} Hz"
            );

            let (plain, _) = render_case(
                prog,
                vec![
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 110,
                        },
                    ),
                    (1.2, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                1.5,
            );
            let (fine, _) = render_case(
                prog,
                vec![
                    (0.01, cc(101, 0)),
                    (0.01, cc(100, 1)),
                    (0.01, cc(6, 96)),
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 110,
                        },
                    ),
                    (1.2, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                1.5,
            );
            let plain_pitch = peak(&plain, 0.35, 0.90, 420.0, 460.0);
            let fine_pitch = peak(&fine, 0.35, 0.90, 440.0, 475.0);
            let want_ratio = 2f32.powf(50.0 / 1200.0);
            let ratio = fine_pitch / plain_pitch;
            assert!(
                (ratio - want_ratio).abs() < 0.012,
                "{name}: RPN fine tune stayed inert, ratio {ratio}"
            );

            let (glide, stats) = render_case(
                prog,
                vec![
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 100,
                        },
                    ),
                    (0.45, EvKind::NoteOff { ch: 0, key: 69 }),
                    (1.0, cc(65, 127)),
                    (1.0, cc(5, 109)),
                    (
                        2.0,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 81,
                            vel: 110,
                        },
                    ),
                    (3.7, EvKind::NoteOff { ch: 0, key: 81 }),
                ],
                4.0,
            );
            assert_eq!(
                stats.voices_spawned, 2,
                "{name}: portamento should spawn a new voice"
            );
            let early = peak(&glide, 2.06, 2.18, 405.0, 485.0);
            let late = peak(&glide, 3.25, 3.60, 820.0, 940.0);
            assert!(
                early < 500.0,
                "{name}: glide did not start near old pitch: {early}"
            );
            assert!(
                (late - 880.0).abs() < 35.0,
                "{name}: glide did not settle to target: {late}"
            );

            let (pressed, _) = render_case(
                prog,
                vec![
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 100,
                        },
                    ),
                    (0.10, EvKind::Aftertouch { ch: 0, val: 127 }),
                    (2.5, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                2.7,
            );
            let (unpressed, _) = render_case(
                prog,
                vec![
                    (
                        0.05,
                        EvKind::NoteOn {
                            ch: 0,
                            key: 69,
                            vel: 100,
                        },
                    ),
                    (2.5, EvKind::NoteOff { ch: 0, key: 69 }),
                ],
                2.7,
            );
            let a = (1.25 * sr) as usize;
            let b = (2.30 * sr) as usize;
            let plain_spread = pitch_spread(&unpressed[a..b], sr, 405.0, 485.0);
            let pressed_spread = pitch_spread(&pressed[a..b], sr, 405.0, 485.0);
            assert!(
                pressed_spread > 5.0 && pressed_spread > 1.5 * plain_spread,
                "{name}: aftertouch vibrato inert, plain {plain_spread} Hz vs pressed {pressed_spread} Hz"
            );
        }
    }

    /// CC5/CC65 portamento spawns a fresh, normally-attacked voice that
    /// starts at the previous note's pitch and glides to its own target —
    /// distinct from CC68 legato, which retunes the ringing voice in place.
    #[test]
    fn portamento_glides_from_previous_pitch() {
        let sr = 44100.0;
        let cc = |num, val| EvKind::Cc { ch: 0, num, val };
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 25 }),
                (0.0, cc(93, 0)),
                (0.0, cc(94, 0)),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 100,
                    },
                ), // A4 origin
                (0.5, EvKind::NoteOff { ch: 0, key: 69 }),
                (1.0, cc(65, 127)), // portamento on
                (1.0, cc(5, 109)),  // glide time ~0.3 s
                (
                    2.5,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 57,
                        vel: 110,
                    },
                ), // A3 target
                (4.2, EvKind::NoteOff { ch: 0, key: 57 }),
            ],
            4.5,
        );
        let (stereo, stats) = render(&song, &test_opts(sr));
        // a normal attack, not a legato retune: two distinct voices
        assert_eq!(stats.voices_spawned, 2);
        let mono = left(&stereo);
        let win = |t0: f32, t1: f32| mean_freq(&mono[(t0 * sr) as usize..(t1 * sr) as usize], sr);
        let early = win(2.55, 2.68); // just after onset: still near 440
                                     // settled target read via Goertzel peak — the K1 cubic tap keeps the
                                     // 2nd harmonic ringing, which double-counts zero crossings
        let late = crate::testutil::peak_locate(
            &mono[(3.8 * sr) as usize..(4.1 * sr) as usize],
            sr,
            195.0,
            245.0,
        );
        assert!(early > 320.0, "glide didn't start high: {early} Hz");
        assert!(
            (late - 220.0).abs() < 12.0,
            "glide didn't reach target: {late} Hz"
        );
    }

    fn render_pluck_resonance(cc71: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 25 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 93,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 94,
                        val: 0,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 74,
                        val: 41,
                    },
                ), // cutoff ~990 Hz
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 71,
                        val: cc71,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 64,
                        vel: 110,
                    },
                ), // E4, 3rd ~990
                (1.5, EvKind::NoteOff { ch: 0, key: 64 }),
            ],
            1.6,
        );
        left(&render(&song, &test_opts(44100.0)).0)
    }

    /// CC71 raises the CC74 filter's Q: with the cutoff parked on the note's
    /// 3rd harmonic, high resonance builds a peak there that low resonance
    /// does not.
    #[test]
    fn cc71_resonance_builds_a_peak() {
        let sr = 44100.0;
        let flat = render_pluck_resonance(0); // Q ~0.7
        let peaky = render_pluck_resonance(127); // Q ~8.0
        let (a, b) = ((0.3 * sr) as usize, (1.4 * sr) as usize);
        let e_flat = band_frac(&flat[a..b], 990.0, 4.0, sr);
        let e_peaky = band_frac(&peaky[a..b], 990.0, 4.0, sr);
        assert!(
            e_peaky > 1.5 * e_flat,
            "resonance built no peak: flat {e_flat} vs peaky {e_peaky}"
        );
    }

    fn render_bowed_aftertouch(at: Option<u8>) -> Vec<f32> {
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 40 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 90,
                },
            ),
        ];
        if let Some(v) = at {
            ev.push((0.1, EvKind::Aftertouch { ch: 0, val: v })); // pressure mid-note
        }
        ev.push((2.4, EvKind::NoteOff { ch: 0, key: 69 }));
        left(&render(&test_song(ev, 2.5), &test_opts(44100.0)).0)
    }

    /// Channel aftertouch swells a held bowed note: a gain bloom (~+2.5 dB)
    /// and deeper pitch vibrato than the voice's own.
    #[test]
    fn aftertouch_swells_gain_and_vibrato() {
        let sr = 44100.0;
        let plain = render_bowed_aftertouch(None);
        let pressed = render_bowed_aftertouch(Some(127));
        let (a, b) = ((1.5 * sr) as usize, (2.2 * sr) as usize);
        let ratio = rms(&pressed[a..b]) / rms(&plain[a..b]).max(1e-9);
        assert!(
            (1.15..1.6).contains(&ratio),
            "aftertouch gain bloom off: {ratio}x"
        );
        let sp_plain = cycle_freq_spread(&plain[a..b], sr);
        let sp_press = cycle_freq_spread(&pressed[a..b], sr);
        assert!(
            sp_press > sp_plain + 3.0,
            "no aftertouch vibrato: plain {sp_plain} Hz vs pressed {sp_press} Hz"
        );
    }

    fn render_poly_at_chord(poly: bool) -> Vec<f32> {
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 40 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 90,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 76,
                    vel: 90,
                },
            ),
        ];
        if poly {
            ev.push((
                0.1,
                EvKind::PolyAftertouch {
                    ch: 0,
                    key: 69,
                    val: 127,
                },
            ));
        }
        ev.push((2.4, EvKind::NoteOff { ch: 0, key: 69 }));
        ev.push((2.4, EvKind::NoteOff { ch: 0, key: 76 }));
        left(&render(&test_song(ev, 2.5), &test_opts(44100.0)).0)
    }

    /// Anti-machine-gun, END TO END through the engine (not the voice in isolation):
    /// a fast repeated ride must NOT sound like one sample retriggered. The engine's
    /// per-key round-robin counter cycles the 4 takes, and the note seed drives a per-hit
    /// micro-variation, so even the two hits that land on the SAME round-robin take (hit 0
    /// and hit 4 of a 4-take bank) are meaningfully different.
    ///
    /// The guard: the same-take pair (0, 4) must differ SUBSTANTIALLY. A machine-gun
    /// (fixed take, no micro-variation) renders them bit-identical, so their difference
    /// energy is exactly zero; with the micro-variation's ±40-cent playback-rate spread the
    /// two same-take hits phase-decorrelate, so the normalized difference energy is large.
    /// This is the oracle that fails if the round-robin is seed-modulo (can repeat a take
    /// back-to-back) or if the micro-variation is dropped.
    #[test]
    fn sampled_ride_does_not_machine_gun() {
        let sr = 44100.0;
        let opts = Options {
            samples: true,
            ..test_opts(sr)
        };
        if !crate::embedded_samples_available() {
            return; // the modeled-only build has no sampled cymbals to guard
        }
        // 5 ISOLATED ride hits on ch10, 1.6 s apart — WIDER than the ride's ~1.2 s ring, so
        // no prior hit's tail bleeds into the next attack window. That isolation is
        // load-bearing: at close spacing hit 4's window would contain hits 0-3's overlapping
        // tails and differ from hit 0 for that reason alone, passing the test without ever
        // exercising the micro-variation. With the RIDE bank's 4 round-robins the counter
        // cycles 0,1,2,3,0, so hit 0 and hit 4 both land on take rr0 — a CLEAN same-take pair.
        let gap = 1.6f64;
        let mut ev = Vec::new();
        for i in 0..5u32 {
            let t = 0.05 + gap * i as f64;
            ev.push((
                t,
                EvKind::NoteOn {
                    ch: 9,
                    key: 51,
                    vel: 100,
                },
            ));
            ev.push((t + gap - 0.1, EvKind::NoteOff { ch: 9, key: 51 }));
        }
        let mono = left(&render(&test_song(ev, 0.05 + gap * 5.0), &opts).0);

        let hit = |i: usize| -> &[f32] {
            let a = ((0.05 + gap as f32 * i as f32) * sr) as usize;
            &mono[a..a + (0.06 * sr) as usize]
        };
        let rms = |x: &[f32]| (x.iter().map(|v| v * v).sum::<f32>() / x.len() as f32).sqrt();

        for i in 0..5 {
            assert!(
                rms(hit(i)) > 1e-3,
                "ride hit {i} is silent — sampled cymbal not routed?"
            );
        }
        // The load-bearing check: hits 0 and 4 are the SAME round-robin take, both isolated,
        // yet must differ SUBSTANTIALLY. A machine-gun (fixed take, no micro-variation)
        // renders them bit-identical -> diff/rms == 0; the ±40-cent playback-rate spread
        // phase-decorrelates them -> diff/rms is large. Verified fail-first: with the rate
        // jitter neutralized this drops to ~0.06 (gain jitter only) and the assert fails.
        let h0 = hit(0);
        let h4 = hit(4);
        let diff: Vec<f32> = h0.iter().zip(h4).map(|(a, b)| a - b).collect();
        let ratio = rms(&diff) / rms(h0).max(1e-9);
        assert!(
            ratio > 0.5,
            "same-round-robin ride hits are nearly identical (diff/rms = {ratio:.3}) — \
             MACHINE-GUN: the micro-variation is not decorrelating repeats"
        );
    }

    /// Poly (key) aftertouch is per-note: pressing A4 in an A4+E5 violin
    /// double stop deepens A4's vibrato while the chord-mate E5 stays steady.
    #[test]
    fn poly_aftertouch_targets_only_the_pressed_note() {
        let sr = 44100.0;
        let plain = render_poly_at_chord(false);
        let pressed = render_poly_at_chord(true);
        let (a, b) = ((1.5 * sr) as usize, (2.2 * sr) as usize);
        let sp_a_plain = pitch_spread(&plain[a..b], sr, 405.0, 485.0);
        let sp_a_press = pitch_spread(&pressed[a..b], sr, 405.0, 485.0);
        assert!(
            sp_a_press > 5.0 && sp_a_press > 1.5 * sp_a_plain,
            "poly AT vibrato inert on the pressed note: plain {sp_a_plain} Hz vs pressed {sp_a_press} Hz"
        );
        let sp_e_plain = pitch_spread(&plain[a..b], sr, 610.0, 710.0);
        let sp_e_press = pitch_spread(&pressed[a..b], sr, 610.0, 710.0);
        assert!(
            sp_e_press < 5.0f32.max(1.5 * sp_e_plain),
            "poly AT leaked onto the chord-mate: plain {sp_e_plain} Hz vs pressed {sp_e_press} Hz"
        );
    }

    fn render_flute_breath(cc2: Option<u8>) -> Vec<f32> {
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 73 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
        ];
        if let Some(v) = cc2 {
            ev.push((
                0.5,
                EvKind::Cc {
                    ch: 0,
                    num: 2,
                    val: v,
                },
            )); // breath backs off mid-note
        }
        ev.push((2.4, EvKind::NoteOff { ch: 0, key: 69 }));
        left(&render(&test_song(ev, 2.5), &test_opts(44100.0)).0)
    }

    /// CC2 breath is an expression-like scaler (squared taper): a flute
    /// note whose breath backs off to 40 mid-note sits far below the
    /// untouched render once the smoothing settles.
    #[test]
    fn cc2_breath_scales_wind_level() {
        let sr = 44100.0;
        let plain = render_flute_breath(None);
        let soft = render_flute_breath(Some(40));
        let (a, b) = ((1.5 * sr) as usize, (2.2 * sr) as usize);
        let ratio = rms(&soft[a..b]) / rms(&plain[a..b]).max(1e-9);
        assert!(
            (0.01..0.4).contains(&ratio),
            "CC2 breath backoff inert or overdone: {ratio}x"
        );
    }

    /// The authored-channel invariant for the new lanes: full-scale CC2
    /// (target 1.0, the never-authored default) and a poly aftertouch aimed
    /// at a key with nothing ringing are both bit-exact no-ops.
    #[test]
    fn breath_and_poly_at_neutral_until_authored() {
        let plain = render_flute_breath(None);
        let full = render_flute_breath(Some(127));
        assert_eq!(plain, full, "CC2=127 must be a bit-exact no-op");
        let base = |extra: Option<EvKind>| {
            let mut ev = vec![
                (0.0, EvKind::Prog { ch: 0, prog: 40 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 69,
                        vel: 90,
                    },
                ),
            ];
            if let Some(e) = extra {
                ev.push((0.1, e));
            }
            ev.push((2.0, EvKind::NoteOff { ch: 0, key: 69 }));
            left(&render(&test_song(ev, 2.2), &test_opts(44100.0)).0)
        };
        let untouched = base(None);
        let missed = base(Some(EvKind::PolyAftertouch {
            ch: 0,
            key: 60, // nothing ringing on this key
            val: 127,
        }));
        assert_eq!(
            untouched, missed,
            "poly AT on a silent key must be a bit-exact no-op"
        );
    }

    /// CC66 sostenuto holds only the notes ringing when the pedal went down:
    /// a note struck *after* pedal-down is not sustained (unlike CC64), and
    /// the captured note releases when the pedal lifts.
    #[test]
    fn cc66_sostenuto_holds_only_captured_notes() {
        let sr = 44100.0;
        let cc = |num, val| EvKind::Cc { ch: 0, num, val };
        // captured: note rings, THEN the pedal goes down over it
        let captured = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 19 }),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 60,
                        vel: 100,
                    },
                ),
                (0.3, cc(66, 127)), // pedal down captures the ringing note
                (0.5, EvKind::NoteOff { ch: 0, key: 60 }), // deferred by sostenuto
                (2.0, cc(66, 0)),   // pedal up releases it
            ],
            3.5,
        );
        // after: the pedal is already down when the note is struck
        let after = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 19 }),
                (0.05, cc(66, 127)), // pedal down over nothing
                (
                    0.3,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 60,
                        vel: 100,
                    },
                ),
                (0.5, EvKind::NoteOff { ch: 0, key: 60 }), // not captured: dies now
                (2.5, cc(66, 0)),
            ],
            3.5,
        );
        let cap = left(&render(&captured, &test_opts(sr)).0);
        let aft = left(&render(&after, &test_opts(sr)).0);
        let w = |sig: &[f32], t0: f32, t1: f32| rms(&sig[(t0 * sr) as usize..(t1 * sr) as usize]);
        let cap_mid = w(&cap, 1.4, 1.9);
        let aft_mid = w(&aft, 1.4, 1.9);
        assert!(
            cap_mid > 10.0 * aft_mid.max(1e-9),
            "sostenuto didn't select: captured {cap_mid} vs after {aft_mid}"
        );
        // pedal up at 2.5 s: the captured note lets go and decays
        let cap_after = w(&cap, 3.0, 3.4);
        assert!(
            cap_after < 0.05 * cap_mid,
            "pedal-up didn't release: {cap_after} vs {cap_mid}"
        );
    }

    fn dry_core() -> EngineCore {
        EngineCore::new(CoreOptions::from_options(
            &test_opts(44100.0),
            false,
            false,
            false,
        ))
    }

    fn unreleased_driven(core: &EngineCore, ch: u8) -> usize {
        core.active
            .iter()
            .filter(|a| a.ch == ch && needs_drive(a.program) && !a.voice.released())
            .count()
    }

    /// MM-BUG-KILN-00013: the realtime voice cap (`enforce_voice_cap`) must never
    /// touch the offline path — it has no deadline, so it keeps unbounded
    /// polyphony and its goldens stay bit-identical. Spawn far more distinct
    /// voices than `live::LIVE_MAX_VOICES` (128) through the shared event path and
    /// confirm nothing was stolen.
    #[test]
    fn offline_polyphony_is_unbounded() {
        let mut core = dry_core();
        let mut spawned = 0usize;
        'outer: for ch in 0u8..9 {
            for key in 21u8..=108 {
                core.handle_event(EvKind::NoteOn { ch, key, vel: 80 });
                spawned += 1;
                if spawned >= 300 {
                    break 'outer;
                }
            }
        }
        assert_eq!(
            core.active_voice_count(),
            spawned,
            "offline polyphony was capped: {} of {spawned} voices survived",
            core.active_voice_count()
        );
    }

    /// MM-BUG-KILN-00013: the cap steals the RIGHT voices — the oldest first,
    /// and any released (decaying) voice before an older un-released one — not
    /// just the right COUNT.
    #[test]
    fn enforce_voice_cap_steals_oldest_released_first() {
        let mut core = dry_core();
        for key in 60u8..66 {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
        }
        assert_eq!(core.active_voice_count(), 6);
        // No voice is released, so the two OLDEST (keys 60, 61) are stolen.
        core.enforce_voice_cap(4);
        let keys: Vec<u8> = core.active.iter().map(|a| a.key).collect();
        assert_eq!(
            keys,
            vec![62, 63, 64, 65],
            "oldest not stolen first: {keys:?}"
        );
        // Release the NEWEST (65); capping to 3 must steal that released voice
        // before any older un-released one.
        core.handle_event(EvKind::NoteOff { ch: 0, key: 65 });
        core.enforce_voice_cap(3);
        let keys: Vec<u8> = core.active.iter().map(|a| a.key).collect();
        assert_eq!(
            keys,
            vec![62, 63, 64],
            "released voice not stolen first: {keys:?}"
        );
    }

    #[test]
    fn driven_guitar_voice_limit_releases_oldest_across_programs_per_channel() {
        let mut core = dry_core();
        core.handle_event(EvKind::Prog { ch: 0, prog: 29 });
        for key in 40..44 {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
        }
        core.handle_event(EvKind::Prog { ch: 0, prog: 30 });
        for key in 44..48 {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
        }
        core.handle_event(EvKind::Prog { ch: 1, prog: 29 });
        core.handle_event(EvKind::NoteOn {
            ch: 1,
            key: 52,
            vel: 100,
        });
        assert_eq!(unreleased_driven(&core, 0), DRIVEN_GUITAR_VOICE_LIMIT);

        core.handle_event(EvKind::NoteOn {
            ch: 0,
            key: 60,
            vel: 100,
        });
        assert_eq!(unreleased_driven(&core, 0), DRIVEN_GUITAR_VOICE_LIMIT);
        assert_eq!(unreleased_driven(&core, 1), 1, "other channel was stolen");
        let oldest = core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 40)
            .unwrap();
        assert!(
            oldest.voice.released(),
            "oldest driven voice was not stolen"
        );
        let newest = core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 60)
            .unwrap();
        assert!(!newest.voice.released(), "newest driven voice was stolen");
    }

    #[test]
    fn driven_guitar_voice_limit_overrides_sustain_pedal() {
        let mut core = dry_core();
        core.handle_event(EvKind::Prog { ch: 0, prog: 29 });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 64,
            val: 127,
        });
        for key in 40..48 {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
            core.handle_event(EvKind::NoteOff { ch: 0, key });
        }
        assert!(core.active.iter().filter(|a| a.ch == 0).all(|a| a.held));

        core.handle_event(EvKind::NoteOn {
            ch: 0,
            key: 60,
            vel: 100,
        });
        let oldest = core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 40)
            .unwrap();
        assert!(oldest.voice.released() && !oldest.held);

        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 64,
            val: 0,
        });
        assert_eq!(unreleased_driven(&core, 0), 1);
        assert!(core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 60)
            .is_some_and(|a| !a.voice.released()));
    }

    #[test]
    fn driven_guitar_voice_limit_overrides_sostenuto_capture() {
        let mut core = dry_core();
        core.handle_event(EvKind::Prog { ch: 0, prog: 30 });
        for key in 40..48 {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
        }
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 66,
            val: 127,
        });
        for key in 40..48 {
            core.handle_event(EvKind::NoteOff { ch: 0, key });
        }
        assert!(core
            .active
            .iter()
            .filter(|a| a.ch == 0)
            .all(|a| a.sost && a.sost_held));

        core.handle_event(EvKind::NoteOn {
            ch: 0,
            key: 60,
            vel: 100,
        });
        let oldest = core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 40)
            .unwrap();
        assert!(oldest.voice.released() && !oldest.sost && !oldest.sost_held);

        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 66,
            val: 0,
        });
        assert_eq!(unreleased_driven(&core, 0), 1);
        assert!(core
            .active
            .iter()
            .find(|a| a.ch == 0 && a.key == 60)
            .is_some_and(|a| !a.voice.released()));
    }

    fn render_piano_una_corda(soft: bool) -> Vec<f32> {
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 0 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
        ];
        if soft {
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 67,
                    val: 127,
                },
            )); // una corda on
        }
        ev.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100,
            },
        ));
        ev.push((3.0, EvKind::NoteOff { ch: 0, key: 60 }));
        left(&render(&test_song(ev, 3.5), &test_opts(44100.0)).0)
    }

    fn render_keyboard_una_corda(program: u8, soft: bool) -> Vec<f32> {
        let mut ev = vec![
            (
                0.0,
                EvKind::Prog {
                    ch: 0,
                    prog: program,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ),
        ];
        if soft {
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 67,
                    val: 127,
                },
            ));
        }
        ev.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100,
            },
        ));
        ev.push((1.0, EvKind::NoteOff { ch: 0, key: 60 }));
        left(&render(&test_song(ev, 1.4), &test_opts(44100.0)).0)
    }

    /// CC67 una corda softens the piano strike: the scaled velocity makes it
    /// both quieter and duller (velocity drives the model's brightness).
    #[test]
    fn cc67_una_corda_softens_piano() {
        let sr = 44100.0;
        let normal = render_piano_una_corda(false);
        let soft = render_piano_una_corda(true);
        let (a, b) = ((0.06 * sr) as usize, (0.5 * sr) as usize);
        let r_norm = rms(&normal[a..b]);
        let r_soft = rms(&soft[a..b]);
        assert!(
            r_soft < 0.9 * r_norm,
            "una corda not quieter: {r_soft} vs {r_norm}"
        );
        let hf_norm = energy_above(&normal[a..b], 3000.0, sr);
        let hf_soft = energy_above(&soft[a..b], 3000.0, sr);
        assert!(
            hf_soft < 0.85 * hf_norm,
            "una corda not duller: soft {hf_soft} vs normal {hf_norm}"
        );
    }

    #[test]
    fn keyboard_voices_una_corda_is_acoustic_piano_only() {
        let sr = 44100.0;
        let normal = render_keyboard_una_corda(0, false);
        let soft = render_keyboard_una_corda(0, true);
        let (a, b) = ((0.06 * sr) as usize, (0.5 * sr) as usize);
        assert!(
            rms(&soft[a..b]) < 0.9 * rms(&normal[a..b]),
            "GM0 una corda positive control did not soften"
        );

        for program in 4u8..=7 {
            let plain = render_keyboard_una_corda(program, false);
            let soft = render_keyboard_una_corda(program, true);
            assert!(
                plain
                    .iter()
                    .zip(&soft)
                    .all(|(x, y)| x.to_bits() == y.to_bits()),
                "GM{program} was still velocity-scaled by acoustic-piano CC67"
            );
        }
    }

    // -----------------------------------------------------------------------
    // v0.9 engine oracles: programs 55-71 (brass / reeds / orchestra hit)
    // now answer CC1 vibrato, channel aftertouch, CC11 breath, CC68 slur and
    // the section-chorus/echo sends. Every feature oracle here FAILS on
    // v0.8.1 (55-71 rendered as a decaying steel pluck with dead
    // CC1/AT/CC11-timbre and (0,0) sends); the pitch is always argmax of
    // `mag_at` (Goertzel), never zero crossings, per the lessons file.
    // -----------------------------------------------------------------------

    /// Argmax-located fundamental (Hz) spread, in cents, across `n` equal
    /// windows in [t0, t1] of `sig`; each window's pitch is `peak_locate` in
    /// [flo, fhi].
    fn pitch_spread_cents(
        sig: &[f32],
        sr: f32,
        t0: f32,
        t1: f32,
        n: usize,
        flo: f32,
        fhi: f32,
    ) -> f32 {
        let span = (t1 - t0) / n as f32;
        let (mut lo, mut hi) = (f32::MAX, f32::MIN);
        for i in 0..n {
            let a = ((t0 + i as f32 * span) * sr) as usize;
            let b = ((t0 + (i + 1) as f32 * span) * sr) as usize;
            let f = crate::testutil::peak_locate(&sig[a..b], sr, flo, fhi);
            lo = lo.min(f);
            hi = hi.max(f);
        }
        1200.0 * (hi / lo).log2()
    }

    fn render_brass_cc1(cc1: Option<u8>) -> Vec<f32> {
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 56 }),
            (
                0.0,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
        ];
        if let Some(v) = cc1 {
            ev.push((
                0.5,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: v,
                },
            ));
        }
        ev.push((3.0, EvKind::NoteOff { ch: 0, key: 69 }));
        left(&render(&test_song(ev, 3.2), &test_opts(44100.0)).0)
    }

    /// E55-1: CC1 vibrato is live on a dry brass voice (prog 56 Trumpet,
    /// fx_profile (0,0), reverb off) — the pitch wander is unambiguously the
    /// 5.3 Hz engine LFO. Needs the vibrato_family 56..=71 edit (E1).
    #[test]
    fn e55_1_cc1_vibrato_live_on_brass() {
        let sr = 44100.0;
        let plain = render_brass_cc1(None);
        let modded = render_brass_cc1(Some(127));
        let sp_plain = pitch_spread_cents(&plain, sr, 1.2, 1.92, 12, 380.0, 500.0);
        let sp_mod = pitch_spread_cents(&modded, sr, 1.2, 1.92, 12, 380.0, 500.0);
        assert!(
            sp_mod >= 20.0,
            "CC1 brass vibrato too shallow: {sp_mod:.1} cents"
        );
        assert!(
            sp_mod >= 2.0 * sp_plain,
            "CC1 vibrato not 2x the no-CC1 spread: mod {sp_mod:.1} vs plain {sp_plain:.1} cents"
        );
    }

    fn brass_slur_song(cc68: u8) -> (Vec<f32>, Stats) {
        // A4 held through, B4 struck at 0.8 s while A4 still sounds; both off
        // at 2.5 s. CC68=127 makes it one breath (slur), CC68=0 two attacks.
        let ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 57 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 68,
                    val: cc68,
                },
            ),
            (
                0.0,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (
                0.8,
                EvKind::NoteOn {
                    ch: 0,
                    key: 71,
                    vel: 100,
                },
            ),
            (2.5, EvKind::NoteOff { ch: 0, key: 69 }),
            (2.5, EvKind::NoteOff { ch: 0, key: 71 }),
        ];
        let (out, stats) = render(&test_song(ev, 2.7), &test_opts(44100.0));
        (left(&out), stats)
    }

    /// E55-3: a CC68 brass phrase (prog 57 Trombone) slurs A4->B4 as one
    /// breath — exactly ONE sustained voice (no second attack), which reaches
    /// B4 and is still ringing 0.8 s later. The same phrase with CC68=0
    /// spawns two voices: the polyphony collapse IS the "no second attack
    /// transient" proof (a second attack requires a second voice). The
    /// sustained-B4 clause is the brass-voice contract that fails on the
    /// v0.8.1 steel pluck (which has decayed to ~1% by [1.6, 2.0]). The
    /// brass onset is spectrally dark by design (the BR_BLOOM "waa"), so an
    /// HF-chiff comparison is NOT a valid discriminator here — see the report.
    /// Cross-owned with the brass voice's legato_to (already in-tree).
    #[test]
    fn e55_3_cc68_brass_slur_no_second_attack() {
        let sr = 44100.0;
        let (slur, slur_stats) = brass_slur_song(127);
        let (_, tongued_stats) = brass_slur_song(0);
        assert_eq!(
            slur_stats.max_polyphony, 1,
            "brass slur spawned a second voice"
        );
        assert_eq!(
            tongued_stats.max_polyphony, 2,
            "the tongued (CC68=0) phrase should be two voices"
        );
        let f = crate::testutil::peak_locate(
            &slur[(1.6 * sr) as usize..(2.0 * sr) as usize],
            sr,
            400.0,
            560.0,
        );
        let target = 493.883_f32; // key_freq(71) = B4
        assert!(
            (f / target - 1.0).abs() <= 0.005,
            "slur target pitch off: {f:.1} Hz vs {target:.1} Hz"
        );
        // sustained, not a decaying pluck: the slurred voice still rings 0.8 s
        // after the slur (a v0.8.1 STEEL pluck would be ~1% here).
        let sus = rms(&slur[(1.6 * sr) as usize..(2.0 * sr) as usize]);
        let early = rms(&slur[(0.3 * sr) as usize..(0.6 * sr) as usize]);
        assert!(
            sus > 0.5 * early,
            "slurred brass voice decayed like a pluck: sustain ratio {:.3}",
            sus / early
        );
    }

    fn render_chord(prog: u8) -> Vec<f32> {
        let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog })];
        for &k in &[60u8, 64, 67] {
            ev.push((
                0.02,
                EvKind::NoteOn {
                    ch: 0,
                    key: k,
                    vel: 100,
                },
            ));
            ev.push((3.0, EvKind::NoteOff { ch: 0, key: k }));
        }
        ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        render(&test_song(ev, 3.2), &test_opts(44100.0)).0
    }

    /// E55-4a: a brass-section chord (prog 61, chorus send 0.25) decorrelates
    /// L/R through the quadrature chorus taps; a dry double-reed chord (prog
    /// 68, sends (0,0)) at centre pan stays ~mono. Needs the fx_profile edit.
    #[test]
    fn e55_4a_section_chorus_decorrelates() {
        let sr = 44100.0;
        let (a, b) = ((0.5 * sr) as usize, (3.0 * sr) as usize);
        let sec = render_chord(61);
        let corr_sec = crate::testutil::inter_corr(&left(&sec)[a..b], &right(&sec)[a..b]);
        let dry = render_chord(68);
        let corr_dry = crate::testutil::inter_corr(&left(&dry)[a..b], &right(&dry)[a..b]);
        assert!(
            corr_sec <= 0.97,
            "section chorus did not decorrelate: corr {corr_sec:.4}"
        );
        assert!(
            corr_dry >= 0.999,
            "dry reed chord not ~mono at centre: corr {corr_dry:.4}"
        );
    }

    fn opts_delay(delay_s: f32) -> Options {
        Options {
            sr: 44100.0,
            wet: 0.0,
            tail: 1.0,
            delay_s,
            samples: false,
            solo: 0xFFFF,
        }
    }

    fn render_sax_echo(delay_s: f32) -> Vec<f32> {
        let ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 65 }),
            (
                0.0,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (0.3, EvKind::NoteOff { ch: 0, key: 69 }),
        ];
        crate::testutil::mono(&render(&test_song(ev, 1.2), &opts_delay(delay_s)).0)
    }

    /// E55-4b: a staccato sax note (prog 65, echo send 0.10) produces a real
    /// ping-pong repeat ~0.25 s later. The delayed-vs-dry difference signal
    /// isolates the echo copy from the dry tail (the corrected oracle form).
    /// Needs the fx_profile edit.
    #[test]
    fn e55_4b_sax_echo_present() {
        let sr = 44100.0;
        let wet = render_sax_echo(0.25);
        let dry = render_sax_echo(0.0);
        let (a, b) = ((0.55 * sr) as usize, (0.65 * sr) as usize);
        let d: Vec<f32> = wet[a..b]
            .iter()
            .zip(&dry[a..b])
            .map(|(x, y)| x - y)
            .collect();
        let e = rms(&d);
        const FLOOR: f32 = 1e-4; // well above render numerical noise
        assert!(
            e >= FLOOR,
            "sax echo missing in the difference window: rms {e:.3e}"
        );
    }

    fn render_brass_cc11(ramp: bool) -> Vec<f32> {
        // prog 57 Trombone, A2 (key 45) held; CC11 either ramps 30->127 or is
        // pinned at 127.
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 57 }),
            (
                0.0,
                EvKind::NoteOn {
                    ch: 0,
                    key: 45,
                    vel: 100,
                },
            ),
        ];
        if ramp {
            for i in 0..=20u32 {
                let t = 0.1 + i as f64 * 0.09;
                let v = (30 + i * (127 - 30) / 20) as u8;
                ev.push((
                    t,
                    EvKind::Cc {
                        ch: 0,
                        num: 11,
                        val: v,
                    },
                ));
            }
        } else {
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 11,
                    val: 127,
                },
            ));
        }
        ev.push((2.5, EvKind::NoteOff { ch: 0, key: 45 }));
        ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        left(&render(&test_song(ev, 2.7), &test_opts(44100.0)).0)
    }

    /// BR-O4: a CC11 ramp 30->127 opens the brass timbre (centroid rises) AND
    /// raises level, while a pinned CC11=127 stays timbrally flat past the
    /// bloom — the differential isolates the BR9 pressure path from the amp
    /// envelope. Needs the BR9 CC11 writer.
    #[test]
    fn br_o4_cc11_opens_brass_tone() {
        let sr = 44100.0;
        let cf = |sig: &[f32], t0: f32, t1: f32| {
            crate::testutil::centroid(&sig[(t0 * sr) as usize..(t1 * sr) as usize], sr)
        };
        let rw = |sig: &[f32], t0: f32, t1: f32| rms(&sig[(t0 * sr) as usize..(t1 * sr) as usize]);
        let ramp = render_brass_cc11(true);
        let pinned = render_brass_cc11(false);
        let ramp_c = cf(&ramp, 1.8, 2.3) / cf(&ramp, 0.3, 0.8);
        let ramp_r = rw(&ramp, 1.8, 2.3) / rw(&ramp, 0.3, 0.8).max(1e-9);
        let pin_c = cf(&pinned, 1.8, 2.3) / cf(&pinned, 0.3, 0.8);
        assert!(
            ramp_c >= 1.3,
            "CC11 ramp didn't brighten: centroid ratio {ramp_c:.2}"
        );
        assert!(
            ramp_r >= 2.0,
            "CC11 ramp didn't swell: rms ratio {ramp_r:.2}"
        );
        assert!(
            pin_c < 1.1,
            "pinned CC11 shouldn't drift timbre: centroid ratio {pin_c:.2}"
        );
    }

    /// BR-O14: bent + vibratoed brass lands on the right pitch (INT-5). Prog
    /// 56 A4, CC1=90 active, PB +2 semis: the composed bend x vibrato pitch
    /// sits at B4 +/-25 cents; a downward bend spanning NoteOff drags the
    /// release tail >= 80 cents down (set_pitch reaches released voices,
    /// INT-2).
    #[test]
    fn br_o14_bend_and_vibrato_liveness() {
        let sr = 44100.0;
        let mut ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 56 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 90,
                },
            ),
            (
                0.02,
                EvKind::NoteOn {
                    ch: 0,
                    key: 69,
                    vel: 100,
                },
            ),
            (0.5, EvKind::Bend { ch: 0, semis: 2.0 }),
        ];
        // a downward pitch fall spanning the NoteOff at 2.0 s: +2 -> -2 semis
        for i in 0..=10u32 {
            let t = 1.9 + i as f64 * 0.04;
            let semis = 2.0 - i as f32 * 0.4;
            ev.push((t, EvKind::Bend { ch: 0, semis }));
        }
        ev.push((2.0, EvKind::NoteOff { ch: 0, key: 69 }));
        ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
        let m = left(&render(&test_song(ev, 2.6), &test_opts(sr)).0);
        let target = 493.883_f32; // B4 = A4 + 2 semitones
        let held = crate::testutil::peak_locate(
            &m[(1.0 * sr) as usize..(1.5 * sr) as usize],
            sr,
            440.0,
            540.0,
        );
        let cents = 1200.0 * (held / target).log2();
        assert!(
            cents.abs() <= 25.0,
            "bent+vibratoed brass pitch off: {held:.1} Hz ({cents:.1} cents from B4)"
        );
        let tail = crate::testutil::peak_locate(
            &m[(2.02 * sr) as usize..(2.16 * sr) as usize],
            sr,
            340.0,
            520.0,
        );
        let tail_cents = 1200.0 * (tail / target).log2();
        assert!(
            tail_cents <= -80.0,
            "release tail didn't track the fall: {tail:.1} Hz ({tail_cents:.1} cents from B4)"
        );
    }

    /// RD-O10: reed CC1/CC68 completeness (INT-5/INT-2), engine-level.
    /// (a) A CC68 tenor-sax phrase (prog 66) slurs E4->G4 as ONE voice; the
    /// same phrase with CC68=0 spawns two. (b) A held clarinet (prog 71) with
    /// CC1=96 and PB +2 semis lands within +/-3% of the bent target under the
    /// active modulator. Needs the vibrato_family 64..=71 edit.
    #[test]
    fn rd_o10_reed_slur_and_pitch_liveness() {
        let sr = 44100.0;
        let slur_song = |cc68: u8| {
            let mut ev = vec![
                (0.0, EvKind::Prog { ch: 0, prog: 66 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 68,
                        val: cc68,
                    },
                ),
                (
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 64,
                        vel: 100,
                    },
                ),
                (
                    0.4,
                    EvKind::NoteOn {
                        ch: 0,
                        key: 67,
                        vel: 100,
                    },
                ),
                (1.5, EvKind::NoteOff { ch: 0, key: 64 }),
                (1.5, EvKind::NoteOff { ch: 0, key: 67 }),
            ];
            ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
            render(&test_song(ev, 1.7), &test_opts(sr))
        };
        let (slur_out, slur_stats) = slur_song(127);
        let (_, tongued_stats) = slur_song(0);
        assert_eq!(
            slur_stats.max_polyphony, 1,
            "reed slur spawned a second voice"
        );
        assert_eq!(
            tongued_stats.max_polyphony, 2,
            "tongued reed should be 2 voices"
        );
        let m = left(&slur_out);
        let g4 = 391.995_f32; // key_freq(67)
        let f = crate::testutil::peak_locate(
            &m[(0.8 * sr) as usize..(1.3 * sr) as usize],
            sr,
            320.0,
            460.0,
        );
        // ±1%: G4 sits mid-grid on peak_locate's 0.5% argmax grid (bracketing
        // points 392.61 / 394.57 Hz), so ±0.5% is tighter than the measurement
        // resolution; ±1% still rejects the E4 origin (16% away). See report.
        assert!(
            (f / g4 - 1.0).abs() <= 0.01,
            "reed slur target off: {f:.1} Hz vs {g4:.1} Hz"
        );

        // (b) CC1 + PB liveness on a held clarinet note (key 62 = D4)
        let ev = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 71 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 96,
                },
            ),
            (
                0.02,
                EvKind::NoteOn {
                    ch: 0,
                    key: 62,
                    vel: 100,
                },
            ),
            (0.5, EvKind::Bend { ch: 0, semis: 2.0 }),
            (2.0, EvKind::NoteOff { ch: 0, key: 62 }),
        ];
        let m2 = left(&render(&test_song(ev, 2.2), &test_opts(sr)).0);
        let target = 329.628_f32; // key_freq(62) * 2^(2/12)
        let f2 = crate::testutil::peak_locate(
            &m2[(1.0 * sr) as usize..(1.5 * sr) as usize],
            sr,
            280.0,
            380.0,
        );
        assert!(
            (f2 / target - 1.0).abs() <= 0.03,
            "clarinet bent+vibrato pitch off: {f2:.1} Hz vs {target:.1} Hz"
        );
    }

    // --- Alt bank (GM Bank-Select alternate orchestral voicings) ---

    fn bank_song(cc0: Option<u8>, prog: u8) -> Vec<(f64, EvKind)> {
        let mut ev = Vec::new();
        if let Some(v) = cc0 {
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: v,
                },
            ));
        }
        ev.push((0.0, EvKind::Prog { ch: 0, prog }));
        ev.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 100,
            },
        ));
        ev.push((1.5, EvKind::NoteOff { ch: 0, key: 60 }));
        ev
    }

    /// AC2 + AC4: `CC0 != 0` routes each in-scope program to the alt voicing,
    /// which is a genuinely different render from the default (proving the bank
    /// switch reaches a distinct voice — bowed cello 42, strings 48, choir 52).
    /// Per-voice character is proven by the `altbank` voice oracles; here we
    /// assert the routing produces a real, non-trivial difference. (GM19 left
    /// this list in round 2: both banks are the same drawbar voice now, pinned
    /// bit-identical by default_gm19_is_the_legacy_drawbar_voice.)
    #[test]
    fn alt_bank_selects_distinct_voices() {
        let sr = 44100.0;
        for prog in [42u8, 48, 52] {
            let alt = left(&render(&test_song(bank_song(Some(1), prog), 2.0), &test_opts(sr)).0);
            let def = left(&render(&test_song(bank_song(None, prog), 2.0), &test_opts(sr)).0);
            assert_eq!(alt.len(), def.len());
            // Not byte-identical → the bank routed to a different factory.
            assert_ne!(
                alt, def,
                "prog {prog}: alt bank must produce a distinct render"
            );
            // And a non-trivial magnitude (a real voice swap, not a rounding blip).
            let diff: Vec<f32> = alt.iter().zip(&def).map(|(a, b)| a - b).collect();
            let ratio = rms(&diff) / rms(&def).max(1e-9);
            assert!(
                ratio > 0.01,
                "prog {prog}: alt render too close to default (diff/base = {ratio:.4})"
            );
        }
    }

    /// AC5: the bank latches (CC121 reset-all-controllers does NOT clear it),
    /// `CC0 == 0` returns to the default bank byte-identically, and an alt-bank
    /// channel delegates a non-orchestral program to the default voice.
    #[test]
    fn alt_bank_latch_reset_and_delegation() {
        let sr = 44100.0;
        let def = left(&render(&test_song(bank_song(None, 48), 2.0), &test_opts(sr)).0);
        let alt = left(&render(&test_song(bank_song(Some(1), 48), 2.0), &test_opts(sr)).0);

        // CC0=1 then CC121 → still alt (bank is not a performance controller).
        let rac = vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (0.0, EvKind::Prog { ch: 0, prog: 48 }),
            (
                0.02,
                EvKind::Cc {
                    ch: 0,
                    num: 121,
                    val: 0,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ),
            (1.5, EvKind::NoteOff { ch: 0, key: 60 }),
        ];
        let after_rac = left(&render(&test_song(rac, 2.0), &test_opts(sr)).0);
        assert_eq!(after_rac, alt, "CC121 must not clear the bank");

        // CC0=1 then CC0=0 → back to the default bank.
        let reset = vec![
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 1,
                },
            ),
            (
                0.02,
                EvKind::Cc {
                    ch: 0,
                    num: 0,
                    val: 0,
                },
            ),
            (0.03, EvKind::Prog { ch: 0, prog: 48 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ),
            (1.5, EvKind::NoteOff { ch: 0, key: 60 }),
        ];
        let after_reset = left(&render(&test_song(reset, 2.0), &test_opts(sr)).0);
        assert_eq!(after_reset, def, "CC0=0 must return to the default bank");

        // Alt bank + a non-orchestral program (piano 0) delegates to default.
        let alt_piano = left(&render(&test_song(bank_song(Some(1), 0), 2.0), &test_opts(sr)).0);
        let def_piano = left(&render(&test_song(bank_song(None, 0), 2.0), &test_opts(sr)).0);
        assert_eq!(
            alt_piano, def_piano,
            "alt bank must delegate non-orchestral programs to the default voice"
        );
    }

    /// Unit 1 (XG CC32 infra): a bank-select LSB naming no *defined* XG
    /// variation falls back to the base GM voice **byte-identically** — the
    /// dispatch reuses the same `seed`, so an undefined `(program, bank_lsb)`
    /// is bit-for-bit the pre-change render. LSB 113 is undefined for every
    /// program (the reference file's 112/113/115/117 all sit past the max
    /// defined XG bank, 101), so this invariant holds even as defined
    /// variations get added in later units.
    #[test]
    fn cc32_undefined_bank_falls_back_byte_identical() {
        let sr = 44100.0;
        let song = |lsb: Option<u8>, prog: u8| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog })];
            if let Some(v) = lsb {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 32,
                        val: v,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((1.0, EvKind::NoteOff { ch: 0, key: 60 }));
            ev
        };
        for prog in [24u8, 0, 48, 30] {
            let base = left(&render(&test_song(song(None, prog), 1.5), &test_opts(sr)).0);
            let undef = left(&render(&test_song(song(Some(113), prog), 1.5), &test_opts(sr)).0);
            assert_eq!(
                base, undef,
                "prog {prog}: an undefined CC32 bank must fall back to base GM byte-identically"
            );
        }
    }

    /// Unit 10 (integration): a *defined* CC32 variation routes through the full
    /// engine path — the CC32 handler sets `bank_lsb`, and note-on dispatches
    /// `make_variation` — producing a render that genuinely differs from the
    /// base program. Covers each of the eight defined `(program, LSB)` pairs
    /// end-to-end (the per-voice character is pinned by the voices oracles; here
    /// we prove the wiring reaches a distinct voice, not just the fallback).
    #[test]
    fn cc32_defined_bank_selects_the_variation() {
        let sr = 44100.0;
        // (program, bank LSB, a key in a sensible range for that program)
        let variations: &[(u8, u8, u8)] = &[
            (24, 96, 60),  // Ukulele
            (105, 98, 60), // Oud
            (116, 96, 45), // Gran Cassa
            (48, 3, 60),   // Slow Strings
            (30, 41, 45),  // Feedback Gtr 2
            (99, 19, 60),  // Hollow Release
            (33, 45, 40),  // Fingered Bass 2
            (50, 65, 60),  // Str5
        ];
        let song = |lsb: Option<u8>, prog: u8, key: u8| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 0, prog })];
            if let Some(v) = lsb {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 32,
                        val: v,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key,
                    vel: 100,
                },
            ));
            ev.push((1.6, EvKind::NoteOff { ch: 0, key }));
            ev
        };
        for &(prog, lsb, key) in variations {
            let base = left(&render(&test_song(song(None, prog, key), 2.0), &test_opts(sr)).0);
            let var = left(&render(&test_song(song(Some(lsb), prog, key), 2.0), &test_opts(sr)).0);
            assert_eq!(base.len(), var.len());
            assert_ne!(
                base, var,
                "prog {prog} + CC32={lsb}: the variation must render differently from the base"
            );
            // And a non-trivial magnitude — a real voice swap, not a rounding blip.
            let diff: Vec<f32> = base.iter().zip(&var).map(|(a, b)| a - b).collect();
            let ratio = rms(&diff) / rms(&base).max(1e-9);
            assert!(
                ratio > 0.01,
                "prog {prog} + CC32={lsb}: variation render too close to base (diff/base = {ratio:.4})"
            );
        }
    }

    /// Unit 1 (CC84 portamento control): a `CC84=src` before a NoteOn makes
    /// that note glide up from `key_freq(src)` even with NO CC65 porta-on,
    /// honoring the CC5 glide time — and the pending source is consumed once,
    /// so a following NoteOn with no CC84 starts at its own pitch. Detected by
    /// source-pitch energy (`mag_at`), which is phase-insensitive.
    #[test]
    fn cc84_glides_from_source_without_porta_on_and_is_consumed_once() {
        let sr = 44100.0;
        let src = 48u8; // portamento source key — an octave below the played key
        let key = 60u8;
        let f_src = key_freq(src);
        let events = |cc84: bool| {
            let mut ev = vec![
                // square lead: fast attack, clean fundamental, no sub-octave
                (0.0, EvKind::Prog { ch: 0, prog: 80 }),
                // long glide time so the scoop spans the onset window
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 5,
                        val: 110,
                    },
                ),
            ];
            if cc84 {
                ev.push((
                    0.01,
                    EvKind::Cc {
                        ch: 0,
                        num: 84,
                        val: src,
                    },
                ));
            }
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key,
                    vel: 100,
                },
            ));
            ev.push((0.90, EvKind::NoteOff { ch: 0, key }));
            // A second note with no CC84 must not glide (source already consumed).
            ev.push((
                1.30,
                EvKind::NoteOn {
                    ch: 0,
                    key,
                    vel: 100,
                },
            ));
            ev.push((2.10, EvKind::NoteOff { ch: 0, key }));
            ev
        };
        let render_mono = |cc84: bool| {
            crate::testutil::mono(&render(&test_song(events(cc84), 2.4), &test_opts(sr)).0)
        };
        let with_cc84 = render_mono(true);
        let baseline = render_mono(false);
        let e_src = |buf: &[f32], t0: f32, t1: f32| {
            crate::testutil::mag_at(&buf[(t0 * sr) as usize..(t1 * sr) as usize], sr, f_src)
        };

        // Note 1 onset: the CC84 render scoops up from key 48 → real energy at
        // the source pitch; the no-CC84 baseline sits at key 60 with none.
        let n1_cc84 = e_src(&with_cc84, 0.05, 0.12);
        let n1_base = e_src(&baseline, 0.05, 0.12);
        // Note 2 onset (CC84 render): no CC84 was sent → no source-pitch scoop.
        let n2_cc84 = e_src(&with_cc84, 1.30, 1.37);
        assert!(
            n1_cc84 > 1e-3,
            "note-1 onset should carry real energy: {n1_cc84:.6}"
        );
        assert!(
            n1_cc84 > 5.0 * n1_base,
            "CC84 must glide from key {src}: onset source-pitch energy cc84 {n1_cc84:.5} vs no-CC84 base {n1_base:.5}"
        );
        assert!(
            n1_cc84 > 5.0 * n2_cc84,
            "CC84 must be consumed once: note-1 source-pitch energy {n1_cc84:.5} vs note-2 {n2_cc84:.5}"
        );
    }

    // ---- XG effect SysEx (reverb/chorus type, variation Amp-Sim insertion) ----

    /// Unit 2 (byte-identity spine): the XG effect block is inert until a real
    /// effect is recognized. A song carrying XG System On + a non-Hall reverb
    /// type + a non-Chorus chorus type + an Amp-Sim variation routed to SYSTEM
    /// (never an insert) renders BYTE-IDENTICALLY to the same song with no XG
    /// SysEx — even with the hall bus active (wet > 0). The per-unit face of
    /// the album-wide render-diff = 0 hard gate; stays valid across units 3-5
    /// because none of these words resolve to a recognized effect.
    #[test]
    fn xg_inert_effect_params_are_byte_identical() {
        let sr = 44100.0;
        let opts = Options {
            sr,
            wet: 0.3,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
        };
        let phrase: Vec<(f64, EvKind)> = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 29 }),
            (0.0, EvKind::Prog { ch: 1, prog: 48 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 45,
                    vel: 100,
                },
            ),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 1,
                    key: 60,
                    vel: 90,
                },
            ),
            (0.9, EvKind::NoteOff { ch: 0, key: 45 }),
            (0.9, EvKind::NoteOff { ch: 1, key: 60 }),
        ];
        let mut with_inert_xg: Vec<(f64, EvKind)> = vec![
            (0.0, EvKind::XgReset),
            // reverb type = a non-Hall1 word -> recognizer no-op
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x00,
                    data: [0x02, 0x00],
                    len: 2,
                },
            ),
            // chorus type = a non-Chorus1 word -> no-op
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x20,
                    data: [0x42, 0x00],
                    len: 2,
                },
            ),
            // Amp-Sim variation type, real Drive/Dry-Wet, but SYSTEM connection
            // and a real part -> resolves to NO insert (system bus is a non-goal).
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x40,
                    data: [0x4B, 0x11],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x42,
                    data: [0x00, 0x18],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x54,
                    data: [0x00, 0x64],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x5A,
                    data: [0x01, 0x00],
                    len: 1,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x5B,
                    data: [0x0E, 0x00],
                    len: 1,
                },
            ),
        ];
        with_inert_xg.extend(phrase.clone());
        let base = render(&test_song(phrase, 1.6), &opts).0;
        let xg = render(&test_song(with_inert_xg, 1.6), &opts).0;
        assert_eq!(
            base, xg,
            "inert XG effect params must not perturb the render (byte-identity spine)"
        );
    }

    /// Unit 2 (state wiring): the reference file's variation block decodes into
    /// the `XgEffects` state exactly — Amp Simulator type, Drive 24, Dry/Wet
    /// 100, INSERTION connection, Part 15 (0-based 14) — and a following XG
    /// System On resets every field to its inert default.
    #[test]
    fn xg_effect_params_update_state() {
        let sr = 44100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        });
        for kind in [
            EvKind::XgEffectParam {
                addr_lo: 0x40,
                data: [0x4B, 0x11],
                len: 2,
            },
            EvKind::XgEffectParam {
                addr_lo: 0x42,
                data: [0x00, 0x18],
                len: 2,
            },
            EvKind::XgEffectParam {
                addr_lo: 0x54,
                data: [0x00, 0x64],
                len: 2,
            },
            EvKind::XgEffectParam {
                addr_lo: 0x5A,
                data: [0x00, 0x00],
                len: 1,
            },
            EvKind::XgEffectParam {
                addr_lo: 0x5B,
                data: [0x0E, 0x00],
                len: 1,
            },
        ] {
            core.handle_event(kind);
        }
        assert_eq!(core.xg.var_type_msb, 0x4B, "Amp Simulator type MSB");
        assert_eq!(core.xg.var_drive, 24, "Drive 24");
        assert_eq!(core.xg.var_drywet, 100, "Dry/Wet 100");
        assert_eq!(core.xg.var_connection, 0, "INSERTION");
        assert_eq!(core.xg.var_part, 14, "Part 15 = 0-based channel 14");

        core.handle_event(EvKind::XgReset);
        assert_eq!(core.xg.var_part, 127, "System On resets Part to OFF");
        assert_eq!(core.xg.var_drive, 0, "System On resets Drive");
    }

    /// Unit 3 (Hall 1 recognizer targets ONLY the hall): the Hall 1 type word
    /// re-tunes the shared hall's combs to HALL1_ROOM and leaves the drum room
    /// untouched (the cathedral is a different type and has no reconfigure path
    /// at all). A following XG System On restores the hall to its default.
    #[test]
    fn xg_hall1_reconfigures_only_the_hall() {
        let sr = 44100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.3,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: true,
            drum_room_on: true,
            sitar_symp_on: true,
        });
        let hall_before = core.reverb.debug_comb_feedback();
        let drum_before = core.drum_room.debug_comb_feedback();
        core.handle_event(EvKind::XgEffectParam {
            addr_lo: 0x00,
            data: HALL1_TYPE,
            len: 2,
        });
        assert_eq!(
            core.reverb.debug_comb_feedback(),
            HALL1_ROOM,
            "hall re-tuned to Hall 1"
        );
        assert_ne!(
            core.reverb.debug_comb_feedback(),
            hall_before,
            "hall feedback actually changed"
        );
        assert_eq!(
            core.drum_room.debug_comb_feedback(),
            drum_before,
            "drum room must be untouched"
        );
        core.handle_event(EvKind::XgReset);
        assert_eq!(
            core.reverb.debug_comb_feedback(),
            DEFAULT_HALL_ROOM,
            "System On restores the hall default"
        );
    }

    /// Unit 3 (Hall 1 changes the render; other reverb types are inert): with
    /// the hall bus active, a Hall 1 type event changes the rendered tail vs a
    /// no-XG render, while an unrecognized reverb type leaves it byte-identical.
    #[test]
    fn xg_hall1_changes_render_other_types_inert() {
        let sr = 44100.0;
        let opts = Options {
            sr,
            wet: 0.4,
            tail: 0.8,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
        };
        let song = |reverb_type: Option<[u8; 2]>| {
            let mut ev: Vec<(f64, EvKind)> = Vec::new();
            if let Some(t) = reverb_type {
                ev.push((
                    0.0,
                    EvKind::XgEffectParam {
                        addr_lo: 0x00,
                        data: t,
                        len: 2,
                    },
                ));
            }
            // strings: a sustained tone with a real tail into the hall
            ev.push((0.0, EvKind::Prog { ch: 0, prog: 48 }));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((0.5, EvKind::NoteOff { ch: 0, key: 60 }));
            test_song(ev, 1.2)
        };
        let base = render(&song(None), &opts).0;
        let hall1 = render(&song(Some(HALL1_TYPE)), &opts).0;
        let other = render(&song(Some([0x02, 0x00])), &opts).0;
        assert_ne!(base, hall1, "Hall 1 must change the hall render");
        assert_eq!(base, other, "an unrecognized reverb type must be inert");
    }

    /// Unit 4 (Chorus::reconfigure mechanism): reconfiguring the LFO changes the
    /// processed output; reconfiguring to the engine defaults is an exact no-op
    /// (this also PROVES DEFAULT_CHORUS_* mirror Chorus::new — the byte-identity
    /// spine for System On); and rate alone is wired (Chorus 1 rate over the
    /// default base/depth still changes the output).
    #[test]
    fn chorus_reconfigure_changes_output_and_defaults_are_noop() {
        let sr = 44100.0;
        let n = (0.5 * sr) as usize;
        let send: Vec<f32> = (0..n)
            .map(|i| (TAU * 220.0 * i as f32 / sr).sin())
            .collect();
        let run = |reconfig: Option<(f32, f32, f32)>| {
            let mut c = Chorus::new(sr);
            if let Some((r, b, d)) = reconfig {
                c.reconfigure(r, b, d);
            }
            let mut l = vec![0.0; n];
            let mut r = vec![0.0; n];
            c.process(&send, &mut l, &mut r);
            (l, r)
        };
        let default = run(None);
        let same = run(Some((
            DEFAULT_CHORUS_RATE,
            DEFAULT_CHORUS_BASE_S,
            DEFAULT_CHORUS_DEPTH_S,
        )));
        let chorus1 = run(Some((CHORUS1_RATE, CHORUS1_BASE_S, CHORUS1_DEPTH_S)));
        let rate_only = run(Some((
            CHORUS1_RATE,
            DEFAULT_CHORUS_BASE_S,
            DEFAULT_CHORUS_DEPTH_S,
        )));
        assert_eq!(default, same, "reconfigure to the defaults must be a no-op");
        assert_ne!(default, chorus1, "Chorus 1 params must change the output");
        assert_ne!(default, rate_only, "the LFO rate must be wired");
    }

    /// Unit 4 (Chorus 1 recognizer): with a pad on the chorus bus, a Chorus 1
    /// type event changes the render vs no-XG; an unrecognized chorus type is
    /// inert.
    #[test]
    fn xg_chorus1_changes_render_other_types_inert() {
        let sr = 44100.0;
        let opts = Options {
            sr,
            wet: 0.0,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
        };
        let song = |chorus_type: Option<[u8; 2]>| {
            let mut ev: Vec<(f64, EvKind)> = Vec::new();
            if let Some(t) = chorus_type {
                ev.push((
                    0.0,
                    EvKind::XgEffectParam {
                        addr_lo: 0x20,
                        data: t,
                        len: 2,
                    },
                ));
            }
            // pad (fx_profile 88..=95 -> chorus_send 0.45)
            ev.push((0.0, EvKind::Prog { ch: 0, prog: 90 }));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((0.6, EvKind::NoteOff { ch: 0, key: 60 }));
            test_song(ev, 1.2)
        };
        let base = render(&song(None), &opts).0;
        let chorus1 = render(&song(Some(CHORUS1_TYPE)), &opts).0;
        let other = render(&song(Some([0x00, 0x00])), &opts).0;
        assert_ne!(base, chorus1, "Chorus 1 must change the chorus render");
        assert_eq!(base, other, "an unrecognized chorus type must be inert");
    }

    /// The XG Effect1 messages that install an Amp-Simulator variation on
    /// `part`, with the given Drive / Dry-Wet / connection.
    fn xg_amp_sim_block(part: u8, drive: u8, drywet: u8, connection: u8) -> Vec<(f64, EvKind)> {
        vec![
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x40,
                    data: [AMP_SIM_TYPE_MSB, 0x00],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x42,
                    data: [0x00, drive],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x54,
                    data: [0x00, drywet],
                    len: 2,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x5A,
                    data: [connection, 0x00],
                    len: 1,
                },
            ),
            (
                0.0,
                EvKind::XgEffectParam {
                    addr_lo: 0x5B,
                    data: [part, 0x00],
                    len: 1,
                },
            ),
        ]
    }

    /// Unit 5 (routing): an Amp-Sim INSERTION on part 14 changes that channel's
    /// render, leaves a non-target channel byte-identical, and installs nothing
    /// when connection == SYSTEM or the part is OFF (127).
    #[test]
    fn xg_variation_routes_to_the_target_channel_only() {
        let sr = 44100.0;
        let opts = |solo: u16| Options {
            sr,
            wet: 0.0,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo,
        };
        let song = |xg: Vec<(f64, EvKind)>| {
            let mut ev = vec![
                (0.0, EvKind::Prog { ch: 14, prog: 29 }),
                (0.0, EvKind::Prog { ch: 0, prog: 29 }),
            ];
            ev.extend(xg);
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 14,
                    key: 45,
                    vel: 100,
                },
            ));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 52,
                    vel: 100,
                },
            ));
            ev.push((0.9, EvKind::NoteOff { ch: 14, key: 45 }));
            ev.push((0.9, EvKind::NoteOff { ch: 0, key: 52 }));
            test_song(ev, 1.4)
        };
        let insert = xg_amp_sim_block(14, 24, 100, XG_VAR_INSERTION);
        let all = 0xFFFF;
        let ch0_only = 1u16 << 0;

        let base = render(&song(vec![]), &opts(all)).0;
        let with_var = render(&song(insert.clone()), &opts(all)).0;
        assert_ne!(
            base, with_var,
            "the Amp-Sim insert must change the target render"
        );

        let ch0_base = render(&song(vec![]), &opts(ch0_only)).0;
        let ch0_var = render(&song(insert.clone()), &opts(ch0_only)).0;
        assert_eq!(
            ch0_base, ch0_var,
            "a non-target channel must be byte-identical"
        );

        let system = render(&song(xg_amp_sim_block(14, 24, 100, 0x01)), &opts(all)).0;
        assert_eq!(system, base, "SYSTEM connection must install no insert");
        let off = render(
            &song(xg_amp_sim_block(127, 24, 100, XG_VAR_INSERTION)),
            &opts(all),
        )
        .0;
        assert_eq!(off, base, "part OFF (127) must install no insert");
    }

    /// Unit 5 (REPLACE, not stack — white-box): with the Amp-Sim insert on a
    /// program-29 channel, the presence or absence of the program `drive` makes
    /// no difference — the insert takes precedence and the program drive never
    /// runs. Under a (wrong) STACK the two would differ.
    #[test]
    fn xg_variation_replaces_not_stacks_the_program_drive() {
        let build = |clear_drive: bool| {
            let mut core = EngineCore::new(CoreOptions {
                sr: 44100.0,
                wet: 0.0,
                delay_s: 0.0,
                samples: false,
                solo: 0xFFFF,
                gtr_symp_on: true,
                drum_room_on: true,
                sitar_symp_on: true,
            });
            core.handle_event(EvKind::Prog { ch: 14, prog: 29 });
            assert!(
                core.strips[14].drive.is_some(),
                "program 29 builds a program drive"
            );
            for (_, kind) in xg_amp_sim_block(14, 24, 100, XG_VAR_INSERTION) {
                core.handle_event(kind);
            }
            assert!(
                core.strips[14].xg_insert.is_some(),
                "Amp-Sim insert must be installed"
            );
            if clear_drive {
                core.strips[14].drive = None;
            }
            core.handle_event(EvKind::NoteOn {
                ch: 14,
                key: 45,
                vel: 100,
            });
            let mut out = Vec::new();
            let mut sink = vec![0f32; BLOCK * 2];
            for _ in 0..30 {
                sink.iter_mut().for_each(|x| *x = 0.0);
                core.render_block_add(BLOCK, &mut sink);
                out.extend_from_slice(&sink);
            }
            out
        };
        assert_eq!(
            build(false),
            build(true),
            "the insert must REPLACE the program drive (it never runs when an insert is present)"
        );
    }

    /// Unit 5 (Dry/Wet blend): lower Dry/Wet moves the render monotonically away
    /// from full-wet toward the dry (un-amped) signal — the base-rate apply-site
    /// blend interpolates linearly.
    #[test]
    fn xg_variation_drywet_blends_toward_full_wet() {
        let sr = 44100.0;
        let opts = Options {
            sr,
            wet: 0.0,
            tail: 0.5,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
        };
        let render_dw = |drywet: u8| {
            let mut ev = vec![(0.0, EvKind::Prog { ch: 14, prog: 29 })];
            ev.extend(xg_amp_sim_block(14, 90, drywet, XG_VAR_INSERTION));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 14,
                    key: 45,
                    vel: 100,
                },
            ));
            ev.push((0.9, EvKind::NoteOff { ch: 14, key: 45 }));
            left(&render(&test_song(ev, 1.4), &opts).0)
        };
        let full = render_dw(127);
        let mid = render_dw(64);
        let dry = render_dw(1);
        let dist =
            |a: &[f32], b: &[f32]| rms(&a.iter().zip(b).map(|(x, y)| x - y).collect::<Vec<_>>());
        let d_dry = dist(&dry, &full);
        let d_mid = dist(&mid, &full);
        assert!(d_mid > 1e-6, "Dry/Wet 64 must differ from full wet");
        assert!(
            d_dry > d_mid * 1.3,
            "lower Dry/Wet must move monotonically away from full wet: dry {d_dry:.6} mid {d_mid:.6}"
        );
    }

    /// Unit 5 (Drive parameter): more XG Drive drives the amp-sim harder — a pure
    /// sine picks up more 2nd/3rd-harmonic energy relative to its fundamental.
    #[test]
    fn amp_sim_higher_drive_adds_harmonics() {
        let sr = 44100.0;
        let f0 = 200.0;
        let n = 8192;
        let thd = |drive: u8| {
            let mut buf: Vec<f32> = (0..n)
                .map(|i| 0.3 * (TAU * f0 * i as f32 / sr).sin())
                .collect();
            Drive::amp_sim(sr, drive).process(&mut buf);
            let fund = crate::testutil::mag_at(&buf, sr, f0).max(1e-9);
            let h2 = crate::testutil::mag_at(&buf, sr, 2.0 * f0);
            let h3 = crate::testutil::mag_at(&buf, sr, 3.0 * f0);
            (h2 + h3) / fund
        };
        let mild = thd(20);
        let hot = thd(110);
        assert!(
            hot > mild * 1.5,
            "more XG Drive must add harmonics: mild {mild:.4} hot {hot:.4}"
        );
    }

    /// KP-O3 (v0.12 brush kit selection seam, re-anchored on trunk's V3
    /// default): a ch-10 Program Change of EXACTLY 40 selects the brush kit;
    /// any other program keeps selecting V3 (the showcase demo's prog 8 must
    /// not change meaning), and a later non-40 program hands the channel back
    /// to V3 for subsequently spawned hits.
    #[test]
    fn ch10_program_40_selects_brush() {
        let sr = 44100.0;
        let song = |progs: &[(f64, u8)]| {
            let mut ev: Vec<(f64, EvKind)> = progs
                .iter()
                .map(|&(t, p)| (t, EvKind::Prog { ch: 9, prog: p }))
                .collect();
            ev.push((
                0.3,
                EvKind::NoteOn {
                    ch: 9,
                    key: 38,
                    vel: 100,
                },
            ));
            ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
            test_song(ev, 1.0)
        };
        let r = |progs: &[(f64, u8)]| render(&song(progs), &test_opts(sr)).0;
        let v3 = r(&[]);
        let prog8 = r(&[(0.0, 8)]);
        let brush = r(&[(0.0, 40)]);
        let back = r(&[(0.0, 40), (0.1, 8)]);
        assert_eq!(prog8, v3, "non-40 programs must keep the V3 kit");
        assert_ne!(brush, v3, "prog 40 must select Brush, not V3");
        assert_eq!(back, v3, "a later non-40 program must hand back to V3");
    }

    /// G5 (v0.12 tam-tam, authored-only): a GM 14 channel that never authors
    /// CC0 renders byte-identically with and without an explicit CC0=0
    /// (tubular bells, the default bank), and only a non-zero CC0 swaps in
    /// the alt-bank tam-tam — whose ~98 Hz gong fundamental confirms the
    /// routing.
    #[test]
    fn alt_bank_gm14_tamtam_authored_only() {
        let sr = 44100.0;
        let base = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 14 }),
            (
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 43,
                    vel: 100,
                },
            ),
        ];
        let with_cc0 = |val: u8| {
            let mut ev = vec![(0.0, EvKind::Cc { ch: 0, num: 0, val })];
            ev.extend(base.iter().cloned());
            ev
        };
        let no_cc = render(&test_song(base.clone(), 2.0), &test_opts(sr)).0;
        let cc0_zero = render(&test_song(with_cc0(0), 2.0), &test_opts(sr)).0;
        let cc0_alt = render(&test_song(with_cc0(8), 2.0), &test_opts(sr)).0;
        assert_eq!(cc0_zero, no_cc, "CC0=0 must be a no-op (default bank)");
        assert_ne!(cc0_alt, no_cc, "CC0!=0 on GM 14 must swap in the tam-tam");
        let l = left(&cc0_alt);
        let f = crate::testutil::peak_locate(
            &l[(0.5 * sr) as usize..(1.8 * sr) as usize],
            sr,
            55.0,
            140.0,
        );
        assert!(
            (f - 98.0).abs() <= 3.0,
            "alt GM 14 fundamental {f:.1} Hz is not the key-43 gong"
        );
    }

    /// Cathedral GM19 and the legacy CC0=1 GM19 can overlap on one channel
    /// without sharing their spawn-time tremulant/Leslie, chorus-default, or
    /// room routes. The oracle compares that overlap with the same two voices
    /// on separate, identically controlled channels: global linear buses and
    /// the final glue must see the same signal either way.
    #[test]
    fn gm19_bank_overlap_matches_split_channels() {
        let sr = 44100.0;
        let overlap_events = |split: bool, first_alt: bool| {
            let first_ch = 0;
            let second_ch = u8::from(split);
            let mut events = vec![];
            for (ch, alt) in [(first_ch, first_alt), (second_ch, !first_alt)] {
                events.push((
                    0.0,
                    EvKind::Cc {
                        ch,
                        num: 0,
                        val: u8::from(alt),
                    },
                ));
                events.push((0.0, EvKind::Prog { ch, prog: 19 }));
                if !split {
                    break;
                }
            }
            events.push((
                0.05,
                EvKind::NoteOn {
                    ch: first_ch,
                    key: 48,
                    vel: 100,
                },
            ));
            if !split {
                events.push((
                    0.30,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: u8::from(!first_alt),
                    },
                ));
            }
            events.push((
                0.35,
                EvKind::NoteOn {
                    ch: second_ch,
                    key: 60,
                    vel: 100,
                },
            ));
            for (time, num, val) in [
                (0.45, 91, 100),
                (0.50, 1, 90),
                (0.65, 93, 64),
                (0.75, 94, 72),
            ] {
                events.push((time, EvKind::Cc { ch: 0, num, val }));
                if split {
                    events.push((time, EvKind::Cc { ch: 1, num, val }));
                }
            }
            events.push((
                1.00,
                EvKind::Cc {
                    ch: 0,
                    num: 121,
                    val: 0,
                },
            ));
            if split {
                events.push((
                    1.00,
                    EvKind::Cc {
                        ch: 1,
                        num: 121,
                        val: 0,
                    },
                ));
            }
            events.push((
                1.50,
                EvKind::NoteOff {
                    ch: first_ch,
                    key: 48,
                },
            ));
            events.push((
                1.70,
                EvKind::NoteOff {
                    ch: second_ch,
                    key: 60,
                },
            ));
            events
        };

        let mut opts = test_opts(sr);
        opts.wet = 0.32;
        opts.delay_s = 0.12;
        opts.tail = 1.0;
        for first_alt in [false, true] {
            let overlap = render(&test_song(overlap_events(false, first_alt), 2.0), &opts).0;
            let split = render(&test_song(overlap_events(true, first_alt), 2.0), &opts).0;
            assert_eq!(overlap.len(), split.len());
            let diff: Vec<f32> = overlap.iter().zip(&split).map(|(x, y)| x - y).collect();
            let ratio = rms(&diff) / rms(&split).max(1e-9);
            assert!(
                ratio < 2e-4,
                "held GM19 routes leaked with first_alt={first_alt}: diff/base {ratio:.6}"
            );
        }
    }

    /// Round-2 GM019 differential pin: with the CathedralOrgan retired, the
    /// default bank IS the legacy drawbar voice — a default-bank GM19 render
    /// must be bit-identical to the CC0=1 render under identical controls
    /// (this is what let the audition drop its GM19 A/B slot). Any drift
    /// here means the banks' routing or spawn paths diverged again.
    #[test]
    fn default_gm19_is_the_legacy_drawbar_voice() {
        let events = |alt: bool| {
            let mut ev = Vec::new();
            if alt {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: 1,
                    },
                ));
            }
            ev.push((0.0, EvKind::Prog { ch: 0, prog: 19 }));
            ev.push((
                0.2,
                EvKind::Cc {
                    ch: 0,
                    num: 1,
                    val: 96,
                },
            ));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 60,
                    vel: 100,
                },
            ));
            ev.push((1.6, EvKind::NoteOff { ch: 0, key: 60 }));
            ev
        };
        let mut opts = test_opts(44100.0);
        opts.wet = 0.32;
        opts.delay_s = 0.12;
        opts.tail = 0.5;
        let default_bank = render(&test_song(events(false), 2.0), &opts).0;
        let legacy = render(&test_song(events(true), 2.0), &opts).0;
        assert!(
            default_bank
                .iter()
                .zip(&legacy)
                .all(|(a, b)| a.to_bits() == b.to_bits()),
            "default GM19 and CC0 legacy GM19 renders diverged"
        );
    }

    /// GM19 CC0=2 selects the restored CathedralOrgan pipe model — a distinct
    /// church-organ colour from the default/CC0=1 Leslie drawbar, carrying its
    /// own long stone-room FDN reverb tail. Default and CC0=1 stay the Leslie
    /// (bit-identical). Regression-first: before the restore CC0=2 fell through
    /// to legacy_church_organ, so all three banks rendered identically and both
    /// asserts below (distinct + wet tail) would fail.
    #[test]
    fn gm19_cc0_2_is_the_cathedral_organ() {
        let events = |bank: u8| {
            let mut ev = Vec::new();
            if bank > 0 {
                ev.push((
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 0,
                        val: bank,
                    },
                ));
            }
            ev.push((0.0, EvKind::Prog { ch: 0, prog: 19 }));
            ev.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key: 48,
                    vel: 100,
                },
            ));
            ev.push((1.2, EvKind::NoteOff { ch: 0, key: 48 }));
            ev
        };
        let mut opts = test_opts(44100.0);
        opts.wet = 0.32;
        opts.tail = 1.0;
        let default_bank = render(&test_song(events(0), 2.5), &opts).0;
        let legacy = render(&test_song(events(1), 2.5), &opts).0;
        let cathedral = render(&test_song(events(2), 2.5), &opts).0;
        // Default and CC0=1 are the identical Leslie drawbar (Ninth Bell safety).
        assert!(
            default_bank
                .iter()
                .zip(&legacy)
                .all(|(a, b)| a.to_bits() == b.to_bits()),
            "default and CC0=1 GM19 must stay the identical Leslie drawbar"
        );
        // CC0=2 is a genuinely different render: the cathedral pipe voice.
        assert!(
            cathedral
                .iter()
                .zip(&legacy)
                .any(|(a, b)| a.to_bits() != b.to_bits()),
            "CC0=2 GM19 did not differ from the Leslie — cathedral voice not routed"
        );
        // The cathedral rings on its dedicated stone-room FDN well past the
        // note-off; measure RMS in the final 0.3 s vs the Leslie's shared-hall
        // decay.
        let sr = 44100usize;
        let tail = |v: &[f32]| {
            let seg = &v[v.len().saturating_sub((0.3 * sr as f32) as usize)..];
            (seg.iter().map(|x| x * x).sum::<f32>() / seg.len().max(1) as f32).sqrt()
        };
        let (cat_tail, leg_tail) = (tail(&cathedral), tail(&legacy));
        assert!(
            cat_tail > leg_tail * 2.0 && cat_tail > 1e-4,
            "cathedral reverb tail ({cat_tail:.2e}) should ring well past the Leslie's ({leg_tail:.2e})"
        );
    }
}
