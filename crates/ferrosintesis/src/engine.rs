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

// Channel aftertouch (0xDn): "crescendo inside a held note" — pressure adds
// vibrato depth and gain on the sustained melodic families.
const AT_VIB_RATE_HZ: f32 = 5.0;
const AT_VIB_CENTS: f32 = 25.0; // pitch depth at full pressure
const AT_GAIN_DB: f32 = 2.5; // gain lift at full pressure
const BAGPIPE_DRONE_KEY: u8 = u8::MAX;

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

fn organ_leslie_family(program: u8, alt: bool) -> bool {
    matches!(program, 16..=18) || (program == 19 && alt)
}

fn cathedral_organ(program: u8, alt: bool) -> bool {
    program == 19 && !alt
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

/// The 5-biquad speaker-cabinet model (HLD G1): low-end resonance, a mid
/// scoop, a presence peak, and a two-pole-pair cliff that both voices the
/// amp and acts as the decimation filter for the 2× nonlinear path. Built
/// at the 2× rate; shared with the oracle-3 response test.
pub(crate) fn cab_biquads(sr2: f32) -> [Biquad; 5] {
    [
        Biquad::peak(100.0, 1.2, 4.0, sr2),
        Biquad::peak(500.0, 1.0, -3.0, sr2),
        Biquad::peak(2600.0, 1.5, 5.0, sr2),
        Biquad::lowpass(4000.0, 0.9, sr2),
        Biquad::lowpass(3800.0, 0.8, sr2),
    ]
}

/// Overdrive/distortion channel insert for GM programs 29/30 (guitar v2,
/// HLD §3.C): program-keyed pre-voicing → power-supply SAG gain → stage-1
/// biased (asymmetric) tanh → interstage tilt EQ → stage-2 tanh → DC
/// blocker → speaker cabinet, the whole nonlinear chain at 2× rate. The
/// cab's cliff replaces the old box-average decimator, so the shaper fizz
/// dies in the cabinet instead of aliasing down.
///
/// The sag stage is what a real amp's drooping supply does, with the real
/// temporal polarity: a fast-attack envelope means pick transients pass at
/// unity gain, then as the note DECAYS the gain recovers (slew-limited, the
/// supply recharging) and holds the tail in saturation — compression
/// sustain and bloom, never an onset blast.
struct Drive {
    program: u8,
    pre: Biquad,
    voice: Biquad,
    g1: f32,
    bias: f32,
    tilt: Biquad,
    g2: f32,
    post: f32,
    dcb: Biquad,
    cab: [Biquad; 5],
    prev: f32,
    // sag state
    env: f32,
    g_sag: f32,
    sag_target: f32, // T: the post-voicing level the sag tries to restore
    g_max: f32,      // recovery ceiling (test-varied by V5's differential)
    atk_k: f32,
    rel_k: f32,
    slew_up: f32,
    idle: u32, // consecutive near-silent 2× samples
    idle_snap: u32,
}

/// Sag recovery ceiling: +12 dB (HLD §3.C G_MAX ≈ 4).
const SAG_G_MAX: f32 = 4.0;

impl Drive {
    fn new(program: u8, sr: f32) -> Self {
        let sr2 = sr * 2.0;
        // 30 = distortion (scooped chug), 29 = overdrive (mid-push lead).
        // Two gentler stages replace v1's single hot tanh; `post` is
        // level-matched to v1 at the loud operating point (drive_level_probe:
        // 29 −9.9 dBFS, 30 −11.6 dBFS on a 0.5-amp 220 Hz sine).
        let (g1, g2, post, bias, sag_target) = if program == 30 {
            (4.5, 3.0, 0.30, 0.5, 0.33)
        } else {
            // bias 0.45: the gentler two-stage 29 needs MORE stage-1 asymmetry
            // than v1's single hot tanh to keep its even-harmonic warmth
            // (drive_asymmetry_and_dc's 2nd-vs-3rd floor)
            (2.5, 2.0, 0.42, 0.45, 0.60)
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
        Drive {
            program,
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
            prev: 0.0,
            env: 0.0,
            g_sag: 1.0,
            sag_target,
            g_max: SAG_G_MAX,
            // attack ≤ 1 ms so the envelope catches the pick before the sag
            // could boost it; release ≈ 180 ms tracks the note's decay
            atk_k: 1.0 - (-1.0 / (0.0005 * sr2)).exp(),
            rel_k: 1.0 - (-1.0 / (0.180 * sr2)).exp(),
            // recovery slew: +12 dB per ~150 ms — the supply recharging
            slew_up: 10f32.powf(12.0 / 20.0 / (0.150 * sr2)),
            // born idle: without this, a first note 0.2-0.4 s into the render
            // meets a gain pre-charged toward g_max by the silent gap
            // (review C2 follow-up)
            idle: (0.4 * sr2) as u32,
            idle_snap: (0.4 * sr2) as u32,
        }
    }

    #[inline]
    fn chain(&mut self, x: f32) -> f32 {
        let v = self.voice.process(self.pre.process(x));
        // sag follower + gain law: g eases toward T/env (clamped [1, g_max]);
        // upward motion is slew-limited (recovery), downward inherits the
        // fast attack of `env` (transients pass at ~unity)
        // idle bookkeeping FIRST: a long-silent channel pins its sag target
        // back to unity and snaps its filter state to exact zero (denormal
        // guard) — without the pin, a silent env would read as "fully
        // decayed" and slew the gain to g_max, booby-trapping the entrance
        let a = v.abs();
        if a < 1e-6 {
            self.idle = self.idle.saturating_add(1);
            if self.idle == self.idle_snap {
                self.reset_state();
            }
        } else {
            self.idle = 0;
        }
        self.env += if a > self.env { self.atk_k } else { self.rel_k } * (a - self.env);
        let target = if self.idle >= self.idle_snap {
            1.0
        } else {
            (self.sag_target / self.env.max(self.sag_target / self.g_max)).max(1.0)
        };
        self.g_sag = if target < self.g_sag {
            target
        } else {
            (self.g_sag * self.slew_up).min(target)
        };
        // stage 1: biased tanh referenced to its bias point — the curvature
        // asymmetry (even harmonics) stays, but silence maps to exactly zero
        let s1 = (v * self.g_sag * self.g1 + self.bias).tanh() - self.bias.tanh();
        // interstage tilt, then the gentler symmetric second stage
        let s2 = (self.tilt.process(s1) * self.g2).tanh();
        let mut y = self.dcb.process(s2);
        for c in &mut self.cab {
            y = c.process(y);
        }
        y
    }

    fn reset_state(&mut self) {
        self.pre.reset();
        self.voice.reset();
        self.tilt.reset();
        self.dcb.reset();
        for c in &mut self.cab {
            c.reset();
        }
        self.env = 0.0;
        self.g_sag = 1.0;
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

    /// Test-only: pin the sag recovery ceiling (V5's differential leg
    /// compares g_max = 1, i.e. sag OFF, against the shipped ceiling).
    #[cfg(test)]
    fn with_sag_gmax(mut self, g: f32) -> Self {
        self.g_max = g;
        self
    }
}

/// Per-program bus sends (chorus, echo). Reverb stays CC91-authored.
fn fx_profile(program: u8, alt: bool) -> (f32, f32) {
    match program {
        19 if !alt => (0.0, 0.0), // cathedral organ: the case/room supplies width
        16..=23 => (0.20, 0.0),   // legacy organs/free reeds: gentle ensemble
        24 | 25 => (0.12, 0.08),  // acoustic guitars: a touch of both
        26..=31 => (0.10, 0.30),  // electric guitars: the delayed-lead sound
        40..=45 | 110 => (0.10, 0.10), // fiddle
        46 => (0.15, 0.0),        // harp
        48..=51 => (0.35, 0.0),   // string ensembles
        52..=54 => (0.30, 0.0),   // choir
        56..=60 => (0.0, 0.0),    // solo brass: hall (CC91) is the space, no ensemble fake
        61..=63 => (0.25, 0.0),   // brass section / synth brass: section-width chorus
        64..=67 => (0.06, 0.10),  // saxes: lead voice, a touch of width and slap echo
        109 => (0.06, 0.0),       // bagpipe: small width, no slap echo on the drone
        111 => (0.04, 0.08),      // shanai: dry forward reed with a trace of slap
        72..=79 => (0.0, 0.22),   // flute / whistle
        80..=87 => (0.15, 0.25),  // synth leads: focused, with the delayed-lead echo
        88..=95 => (0.45, 0.0),   // pads
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
        for i in 0..send.len() {
            let out_l = self.left.tap(self.time);
            let out_r = self.right.tap(self.time);
            self.left
                .push(send[i] + self.lp_r.process(out_r) * self.feedback);
            self.right.push(self.lp_l.process(out_l) * self.feedback);
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

    fn process(&mut self, send: &[f32], l: &mut [f32], r: &mut [f32]) {
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
        for i in 0..l.len() {
            let xl = self.shelf_l.process(l[i]);
            let xr = self.shelf_r.process(r[i]);
            let level = xl.abs().max(xr.abs());
            let k = if level > self.env { self.atk } else { self.rel };
            self.env += k * (level - self.env);
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
    kit: drums::Kit, // channel-10 kit version; V3 by default
    alt_bank: bool,  // CC0 != 0 selects the alt orchestral voicings (altbank::make)
    volume: f32,     // CC7 as amplitude (squared curve)
    pan: f32,        // 0..1
    bend: f32,       // channel pitch multiplier: wheel × range × fine-tune
    legato: bool,    // CC68: new notes slur into the ringing voice
    sustain: bool,   // CC64: NoteOffs are held until the pedal lifts
    // v0.7 authored controllers (all inert until first touched)
    bend_wheel: f32, // last wheel position in ±2-normalised semitones
    bend_range: f32, // RPN 0: bend range in semitones (GM default 2)
    fine: f32,       // RPN 1: fine tune as a frequency multiplier
    rpn_msb: u8,     // CC101/CC100 select; 127/127 = null
    rpn_lsb: u8,
    data_msb: u8, // last CC6, so CC38 can refine it
    porta_on: bool,
    porta_time: f32,         // CC5 glide time in seconds
    last_freq: Option<f32>,  // most recent NoteOn pitch (portamento origin)
    bagpipe_drone_holds: u8, // low GM109 notes currently holding the synthetic drone
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
    // CC11 has been authored at least once. Gates the cathedral-organ reed rasp
    // (swell drive): `expr` defaults to 1.0, so without this a silent organ would
    // snarl at full drive — the opt-in / authored-channel invariant needs the flag.
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
            volume: (100.0f32 / 127.0).powi(2),
            pan: 0.5,
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
            bagpipe_drone_holds: 0,
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

pub struct Options {
    pub sr: f32,
    pub wet: f32,
    pub tail: f32,
    pub delay_s: f32,  // echo time; 0 disables the echo bus
    pub samples: bool, // LA attack-sample layer on the solo voices
    pub solo: u16,     // channel bitmask; note events elsewhere are dropped
    pub verbose: bool,
}

#[derive(Clone, Copy)]
pub struct Stats {
    pub voices_spawned: u64,
    pub peak: f32,
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
}

impl CoreOptions {
    fn from_options(opt: &Options, gtr_symp_on: bool, drum_room_on: bool) -> Self {
        Self {
            sr: opt.sr,
            wet: opt.wet,
            delay_s: opt.delay_s,
            samples: opt.samples,
            solo: opt.solo,
            gtr_symp_on,
            drum_room_on,
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
    drum_room: Reverb,
    glue: BusGlue,
    stats: Stats,
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
    send_room: [f32; BLOCK],
    drum_l: [f32; BLOCK],
    drum_r: [f32; BLOCK],
    mix_l: [f32; BLOCK],
    mix_r: [f32; BLOCK],
    expr_smooth: f32,
    leslie_k: f32,
    wah_smooth: f32,
}

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
            reverb: Reverb::new(sr, 0.86, 0.35, opt.wet),
            cathedral: CathedralReverb::new(sr, opt.wet * CATHEDRAL_WET_SCALE),
            rev_hp: Biquad::highpass(150.0, 0.7, sr),
            chorus: Chorus::new(sr),
            echo: (opt.delay_s > 0.0).then(|| PingPong::new(sr, opt.delay_s)),
            symp: Sympathetic::piano(sr),
            gtr_symp: Sympathetic::guitar(sr),
            drum_room: Reverb::with_predelay(sr, 0.42, 0.55, opt.wet * 0.9, 0.003),
            glue: BusGlue::new(sr),
            stats: Stats::default(),
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
            send_room: [0f32; BLOCK],
            drum_l: [0f32; BLOCK],
            drum_r: [0f32; BLOCK],
            mix_l: [0f32; BLOCK],
            mix_r: [0f32; BLOCK],
            expr_smooth: 1.0 - (-(BLOCK as f32) / (0.03 * sr)).exp(),
            leslie_k: 1.0 - (-(BLOCK as f32) / (LESLIE_INERTIA_S * sr)).exp(),
            wah_smooth: 1.0 - (-(BLOCK as f32) / (WAH_SLEW_S * sr)).exp(),
        }
    }

    pub(crate) fn hard_reset(&mut self) {
        let opt = self.opt;
        *self = Self::new(opt);
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
        let seed = 0xBA60 ^ (self.stats.voices_spawned as u32).wrapping_mul(2654435761);
        let voice = Box::new(voices::bagpipe_drone(key, vel, self.opt.sr, seed));
        self.active.push(Active {
            ch,
            key: BAGPIPE_DRONE_KEY,
            program: 109,
            held: false,
            sost: false,
            sost_held: false,
            glide: None,
            alt: false,
            poly_authored: false,
            poly_target: 0.0,
            poly_cur: 0.0,
            poly_phase: 0.0,
            poly_mult: 1.0,
            poly_gain: 1.0,
            voice,
        });
        self.stats.voices_spawned += 1;
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
        }
    }

    fn note_on(&mut self, ch: u8, key: u8, vel: u8) {
        let sr = self.opt.sr;
        let ci = ch as usize;
        let porta_from = self.strips[ci].last_freq;
        let program = self.strips[ci].program;
        let bagpipe_drone_control =
            ch != 9 && program == 109 && key <= voices::BAGPIPE_DRONE_CONTROL_MAX;
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

        let seed = 0x9E37 ^ (self.stats.voices_spawned as u32).wrapping_mul(2654435761);
        let voice = if ch == 9 {
            drums::make(key, vel, sr, seed, self.strips[9].kit, self.opt.samples)
        } else {
            let prog = self.strips[ci].program;
            Some(if self.strips[ci].alt_bank {
                crate::altbank::make(prog, key, vel, sr, seed, self.opt.samples)
            } else {
                voices::make(prog, key, vel, sr, seed, self.opt.samples)
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
            let glide = if ch != 9 && s.porta_on {
                porta_from.and_then(|from| {
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
                program: if ch == 9 {
                    128
                } else {
                    self.strips[ci].program
                },
                held: false,
                sost: false,
                sost_held: false,
                glide,
                alt: self.strips[ci].alt_bank,
                poly_authored: false,
                poly_target: 0.0,
                poly_cur: 0.0,
                poly_phase: 0.0,
                poly_mult: 1.0,
                poly_gain: 1.0,
                voice,
            });
            self.stats.voices_spawned += 1;
        }
    }

    fn note_off(&mut self, ch: u8, key: u8) {
        if ch != 9 && key <= voices::BAGPIPE_DRONE_CONTROL_MAX {
            let holds = &mut self.strips[ch as usize].bagpipe_drone_holds;
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
        if ch != 9 {
            self.release_bagpipe_drone_if_idle(ch);
        }
    }

    fn cc(&mut self, ch: u8, num: u8, val: u8) {
        let sr = self.opt.sr;
        let s = &mut self.strips[ch as usize];
        let v = val as f32 / 127.0;
        match num {
            0 => {
                s.alt_bank = val != 0; // CC0 bank select: non-zero = alt voicings
                let (cho, del) = fx_profile(s.program, s.alt_bank);
                if !s.chorus_authored {
                    s.chorus_send = cho;
                }
                if !s.delay_authored {
                    s.delay_send = del;
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
            7 => s.volume = v * v,
            10 => {
                s.pan = v;
                s.haas_delay = 0.005 * sr * (v - 0.5).abs() * 2.0;
            }
            11 => {
                s.expr_target = v * v;
                s.expr_authored = true;
            }
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
            91 => s.reverb_send = v,
            93 => {
                s.chorus_send = v;
                s.chorus_authored = true;
            }
            94 => {
                s.delay_send = v;
                s.delay_authored = true;
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
        // downgrade path — with one GM2 exception (v0.12): program 40 EXACTLY
        // is the GM2 brush kit; any other program keeps selecting V3 (the
        // committed showcase demo authors prog 8 and must stay V3).
        if ch == 9 {
            s.kit = if prog == 40 {
                drums::Kit::Brush
            } else {
                drums::Kit::V3
            };
        }
        let (cho, del) = if ch == 9 {
            (0.0, 0.0)
        } else {
            fx_profile(prog, s.alt_bank)
        };
        s.chorus_send = cho;
        s.chorus_authored = false;
        s.delay_send = del;
        s.delay_authored = false;
        if needs_drive(prog) {
            // rebuild on a program CHANGE too: 29<->30 mid-song choreography
            // is an authored idiom, and the two programs differ in voicing,
            // stage gains and sag target (review C3)
            if s.drive.as_ref().map(|d| d.program) != Some(prog) {
                s.drive = Some(Drive::new(prog, self.opt.sr));
            }
        } else {
            s.drive = None;
        }
    }

    fn rederive_program_defaults(&mut self, ch: u8) {
        let prog = self.strips[ch as usize].program;
        let alt = self.strips[ch as usize].alt_bank;
        let s = &mut self.strips[ch as usize];
        let (cho, del) = if ch == 9 {
            (0.0, 0.0)
        } else {
            fx_profile(prog, alt)
        };
        s.chorus_send = cho;
        s.chorus_authored = false;
        s.delay_send = del;
        s.delay_authored = false;
        s.drive = needs_drive(prog).then(|| Drive::new(prog, self.opt.sr));
    }

    fn all_sound_off(&mut self, ch: u8) {
        if ch != 9 {
            self.strips[ch as usize].bagpipe_drone_holds = 0;
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

    fn reset_all_controllers(&mut self, ch: u8) {
        let ci = ch as usize;
        let s = &mut self.strips[ci];
        s.bend = 1.0;
        s.bend_wheel = 0.0;
        s.bend_range = 2.0;
        s.fine = 1.0;
        s.rpn_msb = 127;
        s.rpn_lsb = 127;
        s.data_msb = 0;
        s.porta_on = false;
        s.porta_time = PORTA_MIN_S;
        s.last_freq = None;
        s.sustain = false;
        s.sost_down = false;
        s.soft = false;
        s.legato = false;
        s.vowel_authored = false;
        s.vowel_target = 0.0;
        s.vowel_cur = 0.0;
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
        s.res = WAH_Q;
        s.res_target = WAH_Q;
        s.expr_target = 1.0;
        s.expr = 1.0;
        s.expr_authored = false;
        s.breath_authored = false;
        s.breath_target = 1.0;
        s.breath = 1.0;
        s.wah = None;
        s.wah_legacy = None;
        s.wah_cathedral = None;
        s.wah_r = None;
        s.cutoff = WAH_MAX_HZ;
        s.cutoff_target = WAH_MAX_HZ;
        self.rederive_program_defaults(ch);

        let program = self.strips[ci].program;
        let choir_vowel = matches!(program, 52..=54).then(|| vowel_at(0.0));
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
            a.voice.set_pitch(1.0);
            if organ_leslie_family(a.program, a.alt) {
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
        let sr = self.opt.sr;

        for (ci, strip) in self.strips.iter_mut().enumerate() {
            strip.mod_cur += self.expr_smooth * (strip.mod_target - strip.mod_cur);
            let on = strip.mod_cur > 1e-3;
            let ch = ci as u8;
            let leslie_program = self
                .active
                .iter()
                .find(|a| a.ch == ch && organ_leslie_family(a.program, a.alt))
                .map(|a| a.program)
                .or_else(|| {
                    (strip.mod_authored && organ_leslie_family(strip.program, strip.alt_bank))
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
                    .filter(|a| a.ch == ch && organ_leslie_family(a.program, a.alt))
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
                .filter(|a| a.ch == ch && cathedral_organ(a.program, a.alt))
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
                .filter(|a| a.ch == ch && cathedral_organ(a.program, a.alt))
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
                for a in self.active.iter_mut().filter(|a| a.ch == ch) {
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
            if a.ch == 9 {
                return true;
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
            let buf = if cathedral_organ(a.program, a.alt) {
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
        self.send_room[..n].fill(0.0);
        for (ci, strip) in self.strips.iter_mut().enumerate() {
            let buf = &mut self.ch_buf[ci];
            let legacy = &mut self.legacy_buf[ci];
            let cathedral = &mut self.cathedral_buf[ci];
            if let Some(drive) = &mut strip.drive {
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
            strip.expr += self.expr_smooth * (strip.expr_target - strip.expr);
            if strip.breath_authored {
                strip.breath += self.expr_smooth * (strip.breath_target - strip.breath);
            }
            let g = strip.volume * strip.expr * strip.at_gain * strip.breath;
            if g < 1e-6 {
                continue;
            }
            let theta = strip.pan * FRAC_PI_2;
            let (gl, gr) = (g * theta.cos(), g * theta.sin());
            let rs = strip.reverb_send * 0.9;
            let is_piano = ci != 9 && voices::is_acoustic_piano(strip.program);
            let is_ac_gtr = ci != 9 && matches!(strip.program, 24 | 25);
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
            }
        }

        {
            let s9 = &mut self.strips[9];
            self.drum_l[..n].fill(0.0);
            self.drum_r[..n].fill(0.0);
            let pan_off = s9.pan - 0.5;
            self.active.retain_mut(|a| {
                if a.ch != 9 {
                    return true;
                }
                self.scratch[..n].fill(0.0);
                let alive = a.voice.render(&mut self.scratch[..n]);
                let pan = (drum_pan(a.key) + pan_off).clamp(0.0, 1.0);
                let theta = pan * FRAC_PI_2;
                let (ul, ur) = (theta.cos(), theta.sin());
                for i in 0..n {
                    self.drum_l[i] += self.scratch[i] * ul;
                    self.drum_r[i] += self.scratch[i] * ur;
                }
                alive
            });
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
            let g9 = s9.volume * s9.expr * s9.at_gain * s9.breath;
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
    render_buses(song, opt, true, true)
}

/// The real renderer; the bus switches exist so the A/B oracles (19, 32a)
/// can render the same song with the guitar-sympathetic or drum-room bus
/// disabled. The public `render` always enables both — no shipped knob.
pub(crate) fn render_buses(
    song: &Song,
    opt: &Options,
    gtr_symp_on: bool,
    drum_room_on: bool,
) -> (Vec<f32>, Stats) {
    let sr = opt.sr;
    let total = ((song.seconds + opt.tail as f64) * sr as f64) as usize;
    let mut out = vec![0f32; total * 2]; // interleaved stereo

    let mut core = EngineCore::new(CoreOptions::from_options(opt, gtr_symp_on, drum_room_on));

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
        if opt.verbose && block_start >= next_report {
            eprintln!(
                "  rendered {:>3.0}%  ({:.1} s, {} live voices)",
                block_start as f64 / total as f64 * 100.0,
                block_start as f64 / sr as f64,
                core.active_voice_count()
            );
            next_report += total / 10;
        }
    }
    (out, core.stats())
}

/// Peak-normalise to `target` and convert to interleaved i16 with TPDF dither.
pub fn normalize_to_i16(samples: &[f32], peak: f32, target: f32) -> Vec<i16> {
    let scale = if peak > 1e-9 { target / peak } else { 1.0 };
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::midi::Ev;

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
            verbose: false,
        }
    }

    fn left(stereo: &[f32]) -> Vec<f32> {
        stereo.iter().step_by(2).copied().collect()
    }

    fn rms(seg: &[f32]) -> f32 {
        (seg.iter().map(|&x| (x * x) as f64).sum::<f64>() / seg.len() as f64).sqrt() as f32
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
        for i in 0..4 {
            hits.push((0.125 + i as f64 * 0.5, 51, 95)); // ride right
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
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 121,
            val: 0,
        });

        let s = &core.strips[0];
        assert!((s.volume - (80.0f32 / 127.0).powi(2)).abs() < 1e-6);
        assert!((s.pan - 20.0 / 127.0).abs() < 1e-6);
        assert!(!s.sustain);
        assert!(!s.mod_authored);
        assert_eq!(s.expr, 1.0);
        assert_eq!(s.expr_target, 1.0);
        assert!(s.wah.is_none());
        assert!(
            s.drive.is_some(),
            "program-derived drive should be restored"
        );
        assert_eq!(s.bend, 1.0);
        assert_eq!(s.rpn_msb, 127);
        assert_eq!(s.rpn_lsb, 127);
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
        let with = render_buses(&song, &opts, true, true).0;
        let without = render_buses(&song, &opts, true, false).0;
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
        let a = render_buses(&piano, &opts, true, true).0;
        let b = render_buses(&piano, &opts, true, false).0;
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
        let with = render_buses(&strum(24), &opts, true, true).0;
        let without = render_buses(&strum(24), &opts, false, true).0;
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
        let e_with = render_buses(&strum(30), &opts, true, true).0;
        let e_without = render_buses(&strum(30), &opts, false, true).0;
        assert!(
            e_with
                .iter()
                .zip(&e_without)
                .all(|(x, y)| x.to_bits() == y.to_bits()),
            "electric guitar leaked into the sympathetic bus"
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

    /// Oracle 4 (§5.3): the biased shaper adds a real 2nd harmonic (a pure
    /// sine in, so 2f can only come from the new asymmetry) and the DC
    /// blocker holds the sustained output DC-free.
    #[test]
    fn drive_asymmetry_and_dc() {
        let sr = 44100.0;
        let mut drive = Drive::new(29, sr);
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
            let mut d = Drive::new(prog, sr);
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
    /// it. A naked-sine pass (the T16 "wooden glockenspiel" failure mode)
    /// fails the 2f0 pin.
    #[test]
    fn sustained_lead_stays_harmonic_through_drive() {
        let sr = 44100.0;
        let events = vec![
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
            rel >= -20.0,
            "held lead lost its harmonics: 2f0 {rel:.1} dB rel f0"
        );
    }

    /// V5 (guitar v2): the sag stage — differential AND temporal. The same
    /// −30 dB-decaying 220 Hz tone runs through g_max = 4 (shipped) vs
    /// g_max = 1 (sag inert): (a) the first 30 ms match within 1 dB — the
    /// fast-attack law passes transients at unity, so an inverted or
    /// permanently-boosted law fails here; (b) the sag render's tail decays
    /// ≥ 6 dB less — static two-stage compression alone cannot pass a
    /// differential; (c) after >0.4 s of true silence the insert snaps to
    /// idle (g_sag = 1, env = 0, filter state zeroed) so a fresh entrance
    /// never starts boosted; (d) output stays bounded.
    #[test]
    fn drive_sag_compression() {
        let sr = 44100.0;
        let n = (2.0 * sr) as usize;
        let decaying: Vec<f32> = (0..n)
            .map(|i| {
                let t = i as f32 / sr;
                0.5 * 10f32.powf(-30.0 * t / 2.0 / 20.0) * (std::f32::consts::TAU * 220.0 * t).sin()
            })
            .collect();
        let render = |gmax: f32| {
            let mut d = Drive::new(30, sr).with_sag_gmax(gmax);
            let mut buf = decaying.clone();
            d.process(&mut buf);
            buf
        };
        let on = render(SAG_G_MAX);
        let off = render(1.0);
        let db = |s: &[f32]| 20.0 * crate::testutil::rms(s).max(1e-12).log10();
        let win = |s: &[f32], a: f32, z: f32| db(&s[(a * sr) as usize..(z * sr) as usize]);
        // (a) transients pass at unity
        let (a_on, a_off) = (win(&on, 0.0, 0.03), win(&off, 0.0, 0.03));
        assert!(
            (a_on - a_off).abs() <= 1.0,
            "onset windows differ: sag {a_on:.2} dB vs off {a_off:.2} dB"
        );
        // (b) the tail is held up by recovery, not by static compression
        let decay_on = win(&on, 0.05, 0.10) - win(&on, 1.80, 1.95);
        let decay_off = win(&off, 0.05, 0.10) - win(&off, 1.80, 1.95);
        println!("V5 tail decay: sag {decay_on:.1} dB vs off {decay_off:.1} dB");
        assert!(
            decay_off - decay_on >= 6.0,
            "sag differential {:.1} dB < 6",
            decay_off - decay_on
        );
        // (c) idle reset after a burst + true silence
        let mut d = Drive::new(30, sr);
        let mut two = vec![0f32; sr as usize];
        for (i, x) in two.iter_mut().enumerate().take((0.05 * sr) as usize) {
            *x = 0.5 * (std::f32::consts::TAU * 220.0 * i as f32 / sr).sin();
        }
        d.process(&mut two);
        assert!(
            d.g_sag == 1.0 && d.env == 0.0,
            "idle state after 0.95 s silence: g_sag {} env {}",
            d.g_sag,
            d.env
        );
        // (d) bounded
        let peak = on.iter().fold(0f32, |m, &x| m.max(x.abs()));
        assert!(peak <= 1.0, "drive output peak {peak}");
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
            let mut d = Drive::new(prog, sr);
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
                let mut d = Drive::new(prog, sr);
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
            fx_profile(110, false),
            fx_profile(40, false),
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
            // autonomous pitch is a gentle vibrato + human drift (measured
            // ~10-12 cents) — present, but never a warble
            assert!(
                (3.0..=22.0).contains(&plain_c),
                "GM43 key={key} samples={samples}: autonomous excursion {plain_c:.1} cents"
            );
            // CC1 clearly deepens the vibrato
            assert!(
                mod_c >= 2.0 * plain_c,
                "GM43 key={key} samples={samples}: CC1 {mod_c:.1} vs natural {plain_c:.1} cents"
            );
            // CC1 + aftertouch compose without a runaway (the zero-crossing
            // measure read a false ~1780 cents here; the true excursion is ~110)
            assert!(
                both_c < 130.0,
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
            drone_root > 0.18 * drone_level && drone_fifth > 0.08 * drone_level,
            "bagpipe drone bands weak: root/drone {:.3}, fifth/drone {:.3}",
            drone_root / drone_level.max(1e-9),
            drone_fifth / drone_level.max(1e-9)
        );
        let body = &bagpipe_l[(0.20 * sr) as usize..(0.74 * sr) as usize];
        let body_rms = rms(body);
        let body_drone = crate::testutil::band_rms(body, sr, root, 8.0);
        let chanter = crate::testutil::band_rms(body, sr, key_freq(67), 10.0)
            + crate::testutil::band_rms(body, sr, key_freq(69), 10.0);
        assert!(
            body_drone > 0.06 * body_rms && chanter > 0.10 * body_rms,
            "bagpipe needs drone plus chanter: drone/body {:.3}, chanter/body {:.3}",
            body_drone / body_rms.max(1e-9),
            chanter / body_rms.max(1e-9)
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
            !organ_leslie_family(22, false),
            "GM22 must stay out of the Leslie controller branch"
        );

        for program in [20u8, 21, 23] {
            assert!(
                !organ_leslie_family(program, false),
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
        let held19_pitch_spread = cycle_freq_spread(&held_gm19_after_prog22[a..b], sr);
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
        assert!(
            reset_late <= reset_early + 2.0 && reset_spread < mod_spread * 0.6,
            "GM reset leaked CC1 into GM22: AM {reset_early:.2}->{reset_late:.2}, spread {reset_spread:.2}"
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
        // envelope-follow the whole take, detrend, then count tremulant
        // cycles (rising crossings) per window — the AM rate
        let mut lp1 = OnePole::lowpass(15.0, sr);
        let mut lp2 = OnePole::lowpass(15.0, sr);
        let env: Vec<f32> = mono
            .iter()
            .map(|&x| lp2.process(lp1.process(x.abs())))
            .collect();
        let mut trend = OnePole::lowpass(1.5, sr);
        let det: Vec<f32> = env.iter().map(|&x| x - trend.process(x)).collect();
        let am_rate = |t0: f32, t1: f32| {
            let seg = &det[(t0 * sr) as usize..(t1 * sr) as usize];
            let mut c = 0;
            for w in seg.windows(2) {
                if w[0] <= 0.0 && w[1] > 0.0 {
                    c += 1;
                }
            }
            c as f32 / (t1 - t0)
        };
        // CC1 = 127 is authored at t = 0, so the rotor starts at rest
        // (LESLIE_SLOW_HZ ≈ 0.9 Hz) and slews toward 6.8 Hz with a 1.5 s
        // time constant — a much wider sweep than the old ~4.2→6.8 nudge.
        // The windowed AM rate averages ~2 Hz early (rotor still low and
        // climbing) and ~7 Hz late (settled fast).
        let early = am_rate(0.15, 1.15);
        let late = am_rate(2.9, 3.9);
        assert!(
            late > early + 3.0,
            "sweep too narrow: early {early} Hz, late {late} Hz"
        );
        assert!(
            early < 3.5,
            "rotor started too fast (should brake to slow): {early} Hz"
        );
        assert!(late > 6.0, "rotor never got fast: {late} Hz");
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
        let render_freq = |setup: Vec<(f64, EvKind)>, win: (f32, f32)| -> f32 {
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
            mean_freq(&mono[(win.0 * sr) as usize..(win.1 * sr) as usize], sr)
        };
        // same half-deflection wheel; GM default range 2 vs RPN-widened 12
        let win = (0.25, 0.7);
        let narrow = render_freq(vec![(0.04, EvKind::Bend { ch: 0, semis: 1.0 })], win);
        let wide = render_freq(
            vec![
                (0.01, cc(101, 0)),
                (0.01, cc(100, 0)),
                (0.01, cc(6, 12)),
                (0.04, EvKind::Bend { ch: 0, semis: 1.0 }),
            ],
            win,
        );
        // range 2 -> +1 semitone (~466 Hz); range 12 -> +6 semitones (~622 Hz)
        assert!((narrow - 466.2).abs() < 12.0, "narrow bend: {narrow} Hz");
        assert!((wide - 622.3).abs() < 20.0, "wide bend: {wide} Hz");
        // fine tune: RPN 1, +50 cents (MSB 96, LSB 0) with no wheel
        let plain = render_freq(vec![], win);
        let fine = render_freq(
            vec![(0.01, cc(101, 0)), (0.01, cc(100, 1)), (0.01, cc(6, 96))],
            win,
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
        EngineCore::new(CoreOptions::from_options(&test_opts(44100.0), false, false))
    }

    fn unreleased_driven(core: &EngineCore, ch: u8) -> usize {
        core.active
            .iter()
            .filter(|a| a.ch == ch && needs_drive(a.program) && !a.voice.released())
            .count()
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
            verbose: false,
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
    /// assert the routing produces a real, non-trivial difference.
    #[test]
    fn alt_bank_selects_distinct_voices() {
        let sr = 44100.0;
        for prog in [19u8, 42, 48, 52] {
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

    #[test]
    fn default_gm19_cc1_is_fixed_cathedral_tremulant() {
        let sr = 44100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: false,
            drum_room_on: false,
        });
        core.handle_event(EvKind::Prog { ch: 0, prog: 19 });
        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 1,
            val: 127,
        });
        core.handle_event(EvKind::NoteOn {
            ch: 0,
            key: 57,
            vel: 100,
        });
        let mut block = [0.0f32; BLOCK * 2];
        for _ in 0..20 {
            core.render_block_add(BLOCK, &mut block);
        }
        let rate_at = |core: &mut EngineCore, block: &mut [f32; BLOCK * 2]| {
            let before = core.strips[0].organ_trem_phase;
            block.fill(0.0);
            core.render_block_add(BLOCK, block);
            let after = core.strips[0].organ_trem_phase;
            let delta = (after - before).rem_euclid(TAU);
            delta * sr / (TAU * BLOCK as f32)
        };
        let early = rate_at(&mut core, &mut block);
        for _ in 0..500 {
            block.fill(0.0);
            core.render_block_add(BLOCK, &mut block);
        }
        let late = rate_at(&mut core, &mut block);
        assert!(
            (5.4..=5.6).contains(&early) && (5.4..=5.6).contains(&late),
            "cathedral tremulant must stay near 5.5 Hz: early {early:.2}, late {late:.2}"
        );
        assert!(
            (late - early).abs() <= 0.01,
            "cathedral tremulant must not Leslie-ramp: early {early:.2}, late {late:.2}"
        );
        assert!(!organ_leslie_family(19, false));
        assert!(organ_leslie_family(19, true));
    }

    // Oracle C3 — the cathedral reverb is genuinely wet in the FULL MIX (proves
    // the `opt.wet * CATHEDRAL_WET_SCALE` routing, not just the FDN in isolation).
    // A GM19 chord is held, released, and left to ring; the tail a full 1–2 s
    // after note-off must still sit within ~22 dB of the sustain — a long, present
    // stone room, not a dab of ambience. Guards against the send being unrouted or
    // the wet scale reverting. Calibration (@wet 0.32, 1–2 s after release):
    //   CATHEDRAL_WET_SCALE 1.30 (shipping)  tail ≈ −20.8 dB
    //   CATHEDRAL_WET_SCALE 1.00 (a revert)  tail ≈ −23.1 dB  → fails
    // −22.0 is the midpoint; the 2.2 dB gap is exactly the 1.30× wet return.
    #[test]
    fn cathedral_organ_tail_is_wet_in_the_full_mix() {
        let sr = 44_100.0;
        let mut events = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 7,
                    val: 127,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 11,
                    val: 127,
                },
            ),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 91,
                    val: 127,
                },
            ),
        ];
        for key in [60u8, 64, 67] {
            events.push((
                0.05,
                EvKind::NoteOn {
                    ch: 0,
                    key,
                    vel: 96,
                },
            ));
            events.push((2.0, EvKind::NoteOff { ch: 0, key }));
        }
        let mut opts = test_opts(sr);
        opts.wet = 0.32;
        opts.tail = 4.0;
        let (stereo, _stats) = render(&test_song(events, 2.2), &opts);
        let l = left(&stereo);
        let r = right(&stereo);
        let win = |a: f32, b: f32| -> f32 {
            let (i, j) = ((a * sr) as usize, ((b * sr) as usize).min(l.len()));
            let n = (j - i).max(1) as f32;
            let e: f32 = (i..j).map(|k| l[k] * l[k] + r[k] * r[k]).sum::<f32>() / (2.0 * n);
            e.sqrt()
        };
        let sustain = win(1.0, 1.9);
        let tail = win(3.0, 4.0); // 1–2 s after the 2.0 s note-off
        let tail_db = 20.0 * (tail / sustain.max(1e-12)).log10();
        println!("cathedral C3  tail {tail_db:.2} dB below sustain (sustain={sustain:.4} tail={tail:.4})");
        assert!(
            tail_db >= -22.0,
            "cathedral tail only {tail_db:.2} dB below sustain — reverb not wet in the mix"
        );
    }

    // Render a single sustained GM19 note at a given authored CC11 swell. `None` =
    // unauthored = the byte-identity baseline (CC11 is a gain lane, so authored 0
    // would be silence, never a valid baseline). Dry (wet 0), left channel.
    #[cfg(test)]
    fn render_gm19_swell(cc11: Option<u8>) -> Vec<f32> {
        let sr = 44_100.0;
        let mut events = vec![
            (0.0, EvKind::Prog { ch: 0, prog: 19 }),
            (
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 7,
                    val: 127,
                },
            ),
        ];
        if let Some(v) = cc11 {
            events.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 11,
                    val: v,
                },
            ));
        }
        events.push((
            0.05,
            EvKind::NoteOn {
                ch: 0,
                key: 60,
                vel: 96,
            },
        ));
        events.push((3.0, EvKind::NoteOff { ch: 0, key: 60 }));
        let mut opts = test_opts(sr);
        opts.wet = 0.0;
        opts.tail = 0.2;
        left(&render(&test_song(events, 3.0), &opts).0)
    }

    #[cfg(test)]
    fn rasp_body_rms(s: &[f32]) -> f32 {
        (s.iter().map(|x| x * x).sum::<f32>() / s.len().max(1) as f32).sqrt()
    }

    // Oracle A — the reed rasp grows with the swell (CC11). Level-normalized
    // metrics (CC11 is a gain lane, so absolute level differs between drive points
    // and must cancel): `hfr` = high-frequency (>2 kHz) band mass / rms, plus the
    // spectral centroid. The driven reed table + lift push dense partials into the
    // 2–8 kHz band as drive rises; the threshold keeps a half-open swell smooth.
    // Calibration @44.1k (key 60, LIFT_DB=8): hfr 0.277/0.278/0.304/0.378 at
    // unauth/64/110/127; centroid 1755 → 2843; cc64 stays ≈ unauthored.
    #[test]
    fn cathedral_reed_rasp_grows_with_swell() {
        let sr = 44_100.0;
        let metrics = |cc: Option<u8>| {
            let rendered = render_gm19_swell(cc);
            let body = &rendered[(1.0 * sr) as usize..(2.8 * sr) as usize];
            let r = rasp_body_rms(body).max(1e-9);
            (
                crate::testutil::hp_rms(body, sr, 2_000.0) / r,
                crate::testutil::spectral_centroid(body, sr, 100.0, 12_000.0),
            )
        };
        let (hfr_u, cen_u) = metrics(None);
        let (hfr_64, _) = metrics(Some(64));
        let (hfr_110, _) = metrics(Some(110));
        let (hfr_127, cen_127) = metrics(Some(127));
        println!(
            "rasp hfr u/64/110/127 = {hfr_u:.4}/{hfr_64:.4}/{hfr_110:.4}/{hfr_127:.4}  cen u/127 = {cen_u:.0}/{cen_127:.0}"
        );
        assert!(
            hfr_64 <= 1.10 * hfr_u,
            "half-open swell (cc64) is not smooth: {hfr_64:.4} vs unauth {hfr_u:.4}"
        );
        assert!(
            hfr_110 > hfr_64 && hfr_127 > hfr_110,
            "rasp not monotone in the swell: {hfr_64:.4}/{hfr_110:.4}/{hfr_127:.4}"
        );
        assert!(
            hfr_127 >= 1.25 * hfr_u,
            "full-drive rasp too weak: hfr {hfr_127:.4} vs unauth {hfr_u:.4}"
        );
        assert!(
            cen_127 >= 1.30 * cen_u,
            "full-drive centroid did not lift: {cen_127:.0} vs unauth {cen_u:.0}"
        );
    }

    // Oracle B — the rasp is band-limited spectrum, not aliasing. The mechanism is
    // a band-limited table crossfade (no time-domain nonlinearity), so energy off
    // the f0/2 harmonic lattice can only be Goertzel leakage + wander smear — which
    // stays ~40 dB down. A tanh-without-oversampling reed would fold products into
    // these off-lattice slots at ~−25 dB. Probes (2k+1)·f0/4 across 6–13 kHz.
    // Calibration: unauth −46.5 dB, cc127 −41.5 dB relative to rms.
    #[test]
    fn cathedral_reed_rasp_is_band_limited_not_aliased() {
        let sr = 44_100.0;
        let f0 = 261.63_f32;
        let offlat = |cc: Option<u8>| {
            let rendered = render_gm19_swell(cc);
            let body = &rendered[(1.0 * sr) as usize..(2.8 * sr) as usize];
            let r = rasp_body_rms(body).max(1e-9);
            let mut e = 0.0f32;
            let mut k = 1u32;
            loop {
                let f = (2 * k + 1) as f32 * f0 / 4.0;
                if f > 13_000.0 {
                    break;
                }
                if f >= 6_000.0 {
                    let m = crate::testutil::mag_at(body, sr, f);
                    e += m * m;
                }
                k += 1;
            }
            e.sqrt() / r
        };
        let base = offlat(None);
        let full = offlat(Some(127));
        println!(
            "off-lattice u/127 = {base:.6}/{full:.6} ({:.1}/{:.1} dB)",
            20.0 * base.log10(),
            20.0 * full.log10()
        );
        // Measured full-drive off-lattice is −61.7 dB; 0.005 = −46 dB leaves ~15 dB
        // margin yet fails a realistic aliasing reed (~−25 dB) by ~20 dB.
        assert!(
            full <= 0.005,
            "full-drive off-lattice {:.1} dB — inharmonic/aliasing content crept in",
            20.0 * full.log10()
        );
        assert!(
            base <= 0.005,
            "baseline off-lattice {:.1} dB",
            20.0 * base.log10()
        );
    }

    // Oracle C — an organ that never authors CC11 retains its pre-feature level,
    // spectrum, and envelope; CC11=127 MUST differ, proving the feature is wired.
    #[test]
    fn cathedral_organ_without_cc11_matches_baseline_signature() {
        let no_cc11_render = render_gm19_swell(None);
        crate::testutil::assert_render_signature(
            "unauthored GM19",
            crate::testutil::render_signature(
                &no_cc11_render,
                44100.0,
                (0.5, 2.5),
                (0.2, 0.7),
                (2.0, 2.7),
            ),
            crate::testutil::RenderSignature {
                rms_db: -20.478,
                centroid_hz: 1107.038,
                late_early_db: 0.051,
            },
        );
        let with_cc11 = render_gm19_swell(Some(127));
        assert_ne!(
            no_cc11_render, with_cc11,
            "CC11 did not change the render — the reed rasp is not wired"
        );
    }

    #[test]
    fn cathedral_organ_low_chord_and_pedal_keep_mix_headroom() {
        let sr = 44_100.0;
        let chord_events = |keys: &[u8]| {
            let mut events = vec![
                (0.0, EvKind::Prog { ch: 0, prog: 19 }),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 7,
                        val: 127,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 11,
                        val: 127,
                    },
                ),
                (
                    0.0,
                    EvKind::Cc {
                        ch: 0,
                        num: 91,
                        val: 127,
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
                        num: 94,
                        val: 0,
                    },
                ),
            ];
            for &key in keys {
                events.push((
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key,
                        vel: 100,
                    },
                ));
                events.push((2.20, EvKind::NoteOff { ch: 0, key }));
            }
            events
        };
        let mut opts = test_opts(sr);
        opts.wet = 0.32;
        opts.tail = 2.0;

        let low_keys = [24, 28, 31, 36, 40, 43, 48, 52];
        let (_low_render, low_stats) = render(&test_song(chord_events(&low_keys), 2.4), &opts);
        assert!(
            low_stats.cathedral_return_peak < 1.0,
            "dense low chord cathedral return peaked at {}",
            low_stats.cathedral_return_peak
        );

        let plenum = [48, 55, 60, 64, 67, 72, 76];
        let mut plenum_with_pedal = plenum.to_vec();
        plenum_with_pedal.push(36);
        let (without, without_stats) = render(&test_song(chord_events(&plenum), 2.4), &opts);
        let (with, with_stats) = render(&test_song(chord_events(&plenum_with_pedal), 2.4), &opts);
        let peak_delta_db = 20.0 * (with_stats.peak / without_stats.peak.max(1e-12)).log10();
        assert!(
            peak_delta_db <= 3.0,
            "adding the 32-foot pedal raised raw peak {peak_delta_db:.2}dB"
        );

        let normalized_midband = |stereo: &[f32], peak: f32| {
            let mut hp = Biquad::highpass(250.0, 0.707, sr);
            let mut lp = Biquad::lowpass(8_000.0, 0.707, sr);
            let scale = 10f32.powf(-1.0 / 20.0) / peak.max(1e-12);
            let from = (0.40 * sr) as usize;
            let to = (1.80 * sr) as usize;
            let mut energy = 0.0f64;
            let mut count = 0usize;
            for (frame, pair) in stereo.chunks_exact(2).enumerate() {
                let mono = 0.5 * (pair[0] + pair[1]) * scale;
                let filtered = lp.process(hp.process(mono));
                if (from..to).contains(&frame) {
                    energy += (filtered as f64) * (filtered as f64);
                    count += 1;
                }
            }
            (energy / count.max(1) as f64).sqrt() as f32
        };
        let mid_without = normalized_midband(&without, without_stats.peak);
        let mid_with = normalized_midband(&with, with_stats.peak);
        let mid_loss_db = 20.0 * (mid_with / mid_without.max(1e-12)).log10();
        assert!(
            mid_loss_db >= -1.5,
            "32-foot pedal cost {mid_loss_db:.2}dB of normalized 250Hz-8kHz level"
        );
    }

    #[test]
    fn cathedral_organ_wind_load_settles_and_recovers() {
        let sr = 44_100.0;
        let mut core = EngineCore::new(CoreOptions {
            sr,
            wet: 0.0,
            delay_s: 0.0,
            samples: false,
            solo: 0xFFFF,
            gtr_symp_on: false,
            drum_room_on: false,
        });
        core.handle_event(EvKind::Prog { ch: 0, prog: 19 });
        for key in [36, 43, 48, 52, 55, 60, 64, 67, 72, 76] {
            core.handle_event(EvKind::NoteOn {
                ch: 0,
                key,
                vel: 100,
            });
        }
        let mut block = [0.0f32; BLOCK * 2];
        for _ in 0..((1.5 * sr) as usize / BLOCK) {
            block.fill(0.0);
            core.render_block_add(BLOCK, &mut block);
        }
        assert!(
            (0.95..=1.0).contains(&core.strips[0].organ_wind),
            "ten-note wind load settled at {}",
            core.strips[0].organ_wind
        );

        core.handle_event(EvKind::Cc {
            ch: 0,
            num: 123,
            val: 0,
        });
        for _ in 0..((2.0 * sr) as usize / BLOCK) {
            block.fill(0.0);
            core.render_block_add(BLOCK, &mut block);
        }
        assert!(
            core.strips[0].organ_wind < 0.25,
            "wind chest had not recovered after two seconds: {}",
            core.strips[0].organ_wind
        );
    }

    /// Manual release-mode gate from signed HLD AC12. Run explicitly with
    /// `cargo test --release cathedral_organ_render_budget -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn cathedral_organ_render_budget() {
        use std::time::Instant;

        fn chord(alt: bool) -> Vec<(f64, EvKind)> {
            let keys = [
                36u8, 40, 43, 48, 52, 55, 60, 64, 67, 72, 76, 79, 84, 88, 91, 96,
            ];
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
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 91,
                    val: 0,
                },
            ));
            ev.push((
                0.0,
                EvKind::Cc {
                    ch: 0,
                    num: 93,
                    val: 0,
                },
            ));
            for &key in &keys {
                ev.push((
                    0.05,
                    EvKind::NoteOn {
                        ch: 0,
                        key,
                        vel: 100,
                    },
                ));
                ev.push((4.8, EvKind::NoteOff { ch: 0, key }));
            }
            ev
        }

        let opts = test_opts(44100.0);
        let legacy = test_song(chord(true), 5.0);
        let cathedral = test_song(chord(false), 5.0);
        let _ = render(&legacy, &opts);
        let _ = render(&cathedral, &opts);
        let t0 = Instant::now();
        let _ = render(&legacy, &opts);
        let old = t0.elapsed();
        let t1 = Instant::now();
        let _ = render(&cathedral, &opts);
        let new = t1.elapsed();
        let ratio = new.as_secs_f64() / old.as_secs_f64().max(1e-9);
        println!("16-note 5 s GM19: legacy {old:?}, cathedral {new:?}, ratio {ratio:.2}x");
        assert!(
            ratio <= 3.0,
            "cathedral render budget {ratio:.2}x exceeds 3x"
        );
    }
}
