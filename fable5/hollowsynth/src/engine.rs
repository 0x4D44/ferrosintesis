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
use crate::reverb::Reverb;
use crate::{drums, voices};
use std::f32::consts::{FRAC_PI_2, TAU};

const BLOCK: usize = 64;

// CC1 mod wheel. Melodic sustained voices (plucks, bowed, winds) get an
// engine-level vibrato LFO per channel, multiplied on top of the channel's
// pitch-bend; organs morph their tremulant toward Leslie-fast instead.
const VIB_RATE_HZ: f32 = 5.3; // vibrato LFO rate
const VIB_DEPTH_CENTS: f32 = 35.0; // pitch depth at mod = 1
const LESLIE_SLOW_HZ: f32 = 0.9; // tremulant rate the rotor brakes down to (chorale)
const LESLIE_FAST_HZ: f32 = 6.8; // tremulant rate the rotor spins up to
const LESLIE_INERTIA_S: f32 = 1.5; // rotor time constant (spin-up/down)
const LESLIE_DEPTH_ADD: f32 = 0.10; // extra tremulant depth at mod = 1

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

/// Melodic sustained families that take the engine-level CC1 vibrato:
/// plucks (except palm-mute 28), bowed strings, winds. Drums, organs and
/// modal instruments (piano, bells) are left alone.
fn vibrato_family(program: u8) -> bool {
    // guitars (no palm-mute 28), basses, bowed strings, harp, winds, banjo
    matches!(program, 24..=27 | 29..=46 | 72..=79 | 104..=107)
}

/// Families that answer channel aftertouch: the vibrato families plus
/// organs, string/choir SawStacks and pads. Drums and the Modal
/// (piano/bell) family are left alone — pressure cannot swell a struck
/// string.
fn aftertouch_family(program: u8) -> bool {
    vibrato_family(program) || matches!(program, 16..=23 | 48..=54 | 80..=95)
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

/// Overdrive/distortion channel insert for GM programs 29/30 (HLD G1):
/// program-keyed pre-voicing → biased (asymmetric) tanh → DC blocker →
/// speaker cabinet, the whole nonlinear chain at 2× rate. The cab's cliff
/// replaces the old box-average decimator, so the tanh fizz dies in the
/// cabinet instead of aliasing down.
struct Drive {
    pre: Biquad,
    voice: Biquad,
    gain: f32,
    bias: f32,
    post: f32,
    dcb: Biquad,
    cab: [Biquad; 5],
    prev: f32,
}

impl Drive {
    fn new(program: u8, sr: f32) -> Self {
        // 30 = distortion (scooped chug), 29 = overdrive (mid-push lead)
        let (gain, post, bias) = if program == 30 {
            (7.0, 0.30, 0.55)
        } else {
            (3.5, 0.42, 0.40)
        };
        let voice = if program == 30 {
            Biquad::peak(650.0, 0.9, -5.0, sr * 2.0)
        } else {
            Biquad::peak(800.0, 0.8, 4.0, sr * 2.0)
        };
        Drive {
            pre: Biquad::highpass(90.0, 0.7, sr * 2.0),
            voice,
            gain,
            bias,
            post,
            // a real DC blocker after the shaper: the biased tanh produces
            // large signal-dependent DC that the cab's unity-at-DC biquads
            // cannot remove (V4/CORR-1)
            dcb: Biquad::highpass(20.0, 0.7, sr * 2.0),
            cab: cab_biquads(sr * 2.0),
            prev: 0.0,
        }
    }

    #[inline]
    fn chain(&mut self, x: f32) -> f32 {
        // biased tanh referenced to its bias point: the curvature asymmetry
        // (even harmonics) stays, but silence maps to exactly zero — no
        // startup thump on channels that merely HAVE a drive. The blocker
        // then only handles the signal-dependent rectification DC.
        let shaped = (self.voice.process(self.pre.process(x)) * self.gain + self.bias).tanh()
            - self.bias.tanh();
        let mut y = self.dcb.process(shaped);
        for c in &mut self.cab {
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
fn fx_profile(program: u8) -> (f32, f32) {
    match program {
        16..=23 => (0.20, 0.0),   // organs: gentle ensemble
        24 | 25 => (0.12, 0.08),  // acoustic guitars: a touch of both
        26..=31 => (0.10, 0.30),  // electric guitars: the delayed-lead sound
        40..=45 => (0.10, 0.10),  // fiddle
        46 => (0.15, 0.0),        // harp
        48..=51 => (0.35, 0.0),   // string ensembles
        52..=54 => (0.30, 0.0),   // choir
        72..=79 => (0.0, 0.22),   // flute / whistle
        80..=95 => (0.45, 0.0),   // pads
        96..=103 => (0.30, 0.35), // crystal: shimmer and echo
        8..=10 => (0.0, 0.15),    // celesta / glockenspiel / music box
        14 | 15 => (0.0, 0.08),   // tubular bells
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
    volume: f32,   // CC7 as amplitude (squared curve)
    pan: f32,      // 0..1
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
    soft: bool,             // CC67 una corda
    sost_down: bool,        // CC66 sostenuto pedal position
    vowel_authored: bool,   // CC70 selects a static vowel on choir programs
    vowel_target: f32,      // CC70 value 0..127
    vowel_cur: f32,         // slewed per block
    at_authored: bool,      // channel aftertouch seen on this channel
    at_target: f32,         // pressure 0..1, smoothed like CC11
    at_cur: f32,
    at_phase: f32, // aftertouch vibrato LFO phase
    at_gain: f32,  // pressure gain lift (1.0 = none)
    vib_mult: f32, // this block's CC1 vibrato factor, for composition
    res: f32,      // CC71 resonance: current filter Q, slewed
    res_target: f32,
    expr_target: f32,
    expr: f32,
    mod_target: f32, // CC1, smoothed into mod_cur like expression
    mod_cur: f32,
    mod_engaged: bool,  // mod machinery active (stays on through spin-down)
    mod_authored: bool, // CC1 has been sent at least once on this channel
    vib_phase: f32,
    leslie_rate: f32, // current tremulant rate/depth, slewed with inertia
    leslie_depth: f32,
    reverb_send: f32,
    chorus_send: f32,
    delay_send: f32,
    drive: Option<Drive>,
    wah: Option<Biquad>, // CC74 brightness filter; None = true bypass
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
            mod_target: 0.0,
            mod_cur: 0.0,
            mod_engaged: false,
            mod_authored: false,
            vib_phase: 0.0,
            leslie_rate: 0.0,
            leslie_depth: 0.0,
            reverb_send: 0.3,
            chorus_send: 0.0,
            delay_send: 0.0,
            drive: None,
            wah: None,
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

pub struct Stats {
    pub voices_spawned: u64,
    pub peak: f32,
    pub max_polyphony: usize,
}

struct Active {
    ch: u8,
    key: u8,
    held: bool,      // NoteOff arrived while the sustain pedal was down
    sost: bool,      // CC66: was ringing when the sostenuto pedal went down
    sost_held: bool, // NoteOff deferred by the sostenuto pedal
    // CC5/CC65 portamento: (semitone offset from the target, per-block slew)
    glide: Option<(f32, f32)>,
    voice: Box<dyn voices::Voice>,
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

    let mut strips: Vec<Strip> = (0..16).map(|_| Strip::new(sr)).collect();
    let mut active: Vec<Active> = Vec::new();
    let mut reverb = Reverb::new(sr, 0.86, 0.35, opt.wet);
    let mut rev_hp = Biquad::highpass(150.0, 0.7, sr); // keep the lows dry and tight
    let mut chorus = Chorus::new(sr);
    let mut echo = (opt.delay_s > 0.0).then(|| PingPong::new(sr, opt.delay_s));
    let mut symp = Sympathetic::piano(sr);
    // G5: the acoustic guitars' open strings ring along (prog 24|25 only)
    let mut gtr_symp = Sympathetic::guitar(sr);
    // D10: a tight pre-hall drum room — fb 0.42 ≈ 0.29 s t60, ~3 ms predelay
    let mut drum_room = Reverb::with_predelay(sr, 0.42, 0.55, opt.wet * 0.9, 0.003);
    let mut glue = BusGlue::new(sr);
    let mut stats = Stats {
        voices_spawned: 0,
        peak: 0.0,
        max_polyphony: 0,
    };

    let events: Vec<(usize, EvKind)> = song
        .events
        .iter()
        .map(|e| ((e.sec * sr as f64) as usize, e.kind))
        .collect();
    let mut ev_i = 0;

    let mut ch_buf = vec![[0f32; BLOCK]; 16];
    let mut scratch = [0f32; BLOCK];
    let mut send_rev = [0f32; BLOCK];
    let mut send_cho = [0f32; BLOCK];
    let mut send_del = [0f32; BLOCK];
    let mut send_sym = [0f32; BLOCK];
    let mut send_sym_gtr = [0f32; BLOCK];
    let mut send_room = [0f32; BLOCK];
    let mut drum_l = [0f32; BLOCK];
    let mut drum_r = [0f32; BLOCK];
    let mut mix_l = [0f32; BLOCK];
    let mut mix_r = [0f32; BLOCK];
    let expr_smooth = 1.0 - (-(BLOCK as f32) / (0.03 * sr)).exp();
    let leslie_k = 1.0 - (-(BLOCK as f32) / (LESLIE_INERTIA_S * sr)).exp();
    let wah_smooth = 1.0 - (-(BLOCK as f32) / (WAH_SLEW_S * sr)).exp();
    let mut next_report = total / 10;

    let mut block_start = 0usize;
    while block_start < total {
        let n = BLOCK.min(total - block_start);

        // apply events that fall inside this block (quantised to block start)
        while ev_i < events.len() && events[ev_i].0 < block_start + n {
            let (_, kind) = events[ev_i];
            ev_i += 1;
            match kind {
                // --solo: muted channels keep their CCs but lose their notes
                EvKind::NoteOn { ch, .. } | EvKind::NoteOff { ch, .. }
                    if opt.solo & (1u16 << ch) == 0 => {}
                EvKind::NoteOn { ch, key, vel } => {
                    // portamento origin: the channel's most recent pitch
                    let porta_from = strips[ch as usize].last_freq;
                    if ch != 9 {
                        strips[ch as usize].last_freq = Some(key_freq(key));
                    }
                    // CC68 legato: slur into the channel's one ringing voice
                    // (pedal-held voices are past their NoteOff — not slurred)
                    if ch != 9 && strips[ch as usize].legato {
                        let mut ringing = active.iter_mut().filter(|a| {
                            a.ch == ch && !a.held && !a.sost_held && !a.voice.released()
                        });
                        if let (Some(a), None) = (ringing.next(), ringing.next()) {
                            if a.voice.legato_to(key, vel) {
                                a.key = key;
                                continue;
                            }
                        }
                    }
                    // CC67 una corda: the soft pedal softens the strike —
                    // the scaled velocity drives the piano's brightness too
                    let vel = if ch != 9
                        && strips[ch as usize].soft
                        && strips[ch as usize].program <= 7
                    {
                        ((vel as f32 * 0.75).round() as u8).max(1)
                    } else {
                        vel
                    };
                    // D6 hat choke: any hat strike silences the hats already
                    // ringing (the pedal closes / the stick lands)
                    if ch == 9 && matches!(key, 42 | 44 | 46) {
                        for a in active
                            .iter_mut()
                            .filter(|a| a.ch == 9 && matches!(a.key, 42 | 44 | 46))
                        {
                            a.voice.choke();
                        }
                    }
                    let seed = 0x9E37 ^ (stats.voices_spawned as u32).wrapping_mul(2654435761);
                    let voice = if ch == 9 {
                        drums::make(key, vel, sr, seed)
                    } else {
                        Some(voices::make(
                            strips[ch as usize].program,
                            key,
                            vel,
                            sr,
                            seed,
                            opt.samples,
                        ))
                    };
                    if let Some(mut voice) = voice {
                        let s = &strips[ch as usize];
                        let bend = s.bend;
                        if bend != 1.0 {
                            voice.set_pitch(bend);
                        }
                        if s.vowel_authored && matches!(s.program, 52..=54) {
                            let (f, q, g) = vowel_at(s.vowel_cur);
                            voice.set_vowel(f, q, g);
                        }
                        // CC65 portamento: the fresh (normally-attacked)
                        // voice starts at the previous pitch and glides in
                        let glide = if ch != 9 && s.porta_on {
                            porta_from.and_then(|from| {
                                let semis = 12.0 * (from / key_freq(key)).log2();
                                (semis.abs() > 1e-3).then(|| {
                                    let k = 1.0
                                        - (-(BLOCK as f32) / (s.porta_time.max(1e-3) * sr)).exp();
                                    voice.set_pitch(s.bend * 2f32.powf(semis / 12.0));
                                    (semis, k)
                                })
                            })
                        } else {
                            None
                        };
                        active.push(Active {
                            ch,
                            key,
                            held: false,
                            sost: false,
                            sost_held: false,
                            glide,
                            voice,
                        });
                        stats.voices_spawned += 1;
                    }
                }
                EvKind::NoteOff { ch, key } => {
                    if let Some(a) = active.iter_mut().find(|a| {
                        a.ch == ch && a.key == key && !a.held && !a.sost_held && !a.voice.released()
                    }) {
                        if ch != 9 && strips[ch as usize].sustain {
                            a.held = true; // CC64: the pedal keeps it ringing
                        } else if ch != 9 && a.sost {
                            a.sost_held = true; // CC66: sostenuto defers it
                        } else {
                            a.voice.note_off();
                        }
                    }
                }
                EvKind::Cc { ch, num, val } => {
                    let s = &mut strips[ch as usize];
                    let v = val as f32 / 127.0;
                    match num {
                        1 => {
                            // first CC1 of any value makes the wheel authoritative
                            // on this channel for the rest of the render
                            s.mod_target = v;
                            s.mod_authored = true;
                        }
                        5 => s.porta_time = PORTA_MIN_S * (PORTA_MAX_S / PORTA_MIN_S).powf(v),
                        6 | 38 => {
                            // RPN data entry (MSB, optionally refined by LSB)
                            if num == 6 {
                                s.data_msb = val;
                            }
                            let (msb, lsb) = if num == 6 {
                                (val, 0)
                            } else {
                                (s.data_msb, val)
                            };
                            match (s.rpn_msb, s.rpn_lsb) {
                                (0, 0) => {
                                    // RPN 0: pitch-bend range, semitones + cents
                                    s.bend_range = msb.clamp(1, 24) as f32 + lsb as f32 / 100.0;
                                }
                                (0, 1) => {
                                    // RPN 1: fine tune. MSB-only reduces to
                                    // cents = (v - 64) * 100 / 64.
                                    let raw = ((msb as i32) << 7 | lsb as i32) - 8192;
                                    let cents = raw as f32 * (100.0 / 8192.0);
                                    s.fine = 2f32.powf(cents / 1200.0);
                                }
                                _ => {}
                            }
                            if matches!((s.rpn_msb, s.rpn_lsb), (0, 0) | (0, 1)) {
                                // recompose the channel multiplier and push it
                                // to everything already sounding
                                s.bend =
                                    2f32.powf(s.bend_wheel * (s.bend_range * 0.5) / 12.0) * s.fine;
                                let mult = s.bend;
                                for a in active.iter_mut().filter(|a| a.ch == ch) {
                                    a.voice.set_pitch(mult);
                                }
                            }
                        }
                        7 => s.volume = v * v,
                        10 => {
                            s.pan = v;
                            // far ear hears a panned source a moment later
                            s.haas_delay = 0.005 * sr * (v - 0.5).abs() * 2.0;
                        }
                        11 => s.expr_target = v * v,
                        64 => {
                            s.sustain = val >= 64;
                            if !s.sustain {
                                // pedal up: everything it was holding lets go
                                // (unless the sostenuto pedal also has it)
                                for a in active.iter_mut().filter(|a| a.ch == ch && a.held) {
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
                                // capture exactly the notes ringing now
                                for a in active
                                    .iter_mut()
                                    .filter(|a| a.ch == ch && !a.voice.released())
                                {
                                    a.sost = true;
                                }
                            } else if !down && s.sost_down {
                                for a in active.iter_mut().filter(|a| a.ch == ch && a.sost) {
                                    a.sost = false;
                                    if a.sost_held {
                                        a.sost_held = false;
                                        if s.sustain {
                                            a.held = true; // CC64 takes over
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
                            // choir vowel select; ringing notes crossfade to it
                            if !s.vowel_authored {
                                s.vowel_cur = val as f32;
                            }
                            s.vowel_target = val as f32;
                            s.vowel_authored = true;
                        }
                        71 => {
                            s.res_target = RES_MIN_Q * (RES_MAX_Q / RES_MIN_Q).powf(v);
                            if s.wah.is_none() {
                                // resonance needs the filter in the path; it
                                // enters wide open and slews from there
                                s.wah = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                                if ch == 9 {
                                    s.wah_r = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                                }
                            }
                        }
                        74 => {
                            s.cutoff_target = WAH_MIN_HZ * (WAH_MAX_HZ / WAH_MIN_HZ).powf(v);
                            if val < 127 && s.wah.is_none() {
                                // the filter enters the path transparently:
                                // wide open, then slews down to the target
                                s.wah = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                                if ch == 9 {
                                    s.wah_r = Some(Biquad::lowpass(WAH_MAX_HZ, WAH_Q, sr));
                                }
                            }
                        }
                        91 => s.reverb_send = v,
                        93 => s.chorus_send = v,
                        94 => s.delay_send = v,
                        100 => s.rpn_lsb = val,
                        101 => s.rpn_msb = val,
                        _ => {}
                    }
                }
                EvKind::Bend { ch, semis } => {
                    // `semis` is decoded at the GM ±2 default; rescale by the
                    // channel's RPN 0 range and compose the RPN 1 fine tune
                    let s = &mut strips[ch as usize];
                    s.bend_wheel = semis;
                    let mult = 2f32.powf(semis * (s.bend_range * 0.5) / 12.0) * s.fine;
                    s.bend = mult;
                    for a in active.iter_mut().filter(|a| a.ch == ch) {
                        a.voice.set_pitch(mult);
                    }
                }
                EvKind::Aftertouch { ch, val } => {
                    let s = &mut strips[ch as usize];
                    s.at_target = val as f32 / 127.0;
                    s.at_authored = true;
                }
                EvKind::Prog { ch, prog } => {
                    let s = &mut strips[ch as usize];
                    s.program = prog;
                    let (cho, del) = if ch == 9 {
                        (0.0, 0.0)
                    } else {
                        fx_profile(prog)
                    };
                    s.chorus_send = cho;
                    s.delay_send = del;
                    if needs_drive(prog) {
                        if s.drive.is_none() {
                            s.drive = Some(Drive::new(prog, sr));
                        }
                    } else {
                        s.drive = None;
                    }
                }
            }
        }

        // CC1 mod wheel: per-block pitch/tremulant updates, before the
        // voices render. Nothing here runs for channels that never move
        // the wheel (mod_authored stays false), so mod-free renders are
        // bit-identical to v0.5.
        for (ci, strip) in strips.iter_mut().enumerate() {
            strip.mod_cur += expr_smooth * (strip.mod_target - strip.mod_cur);
            let on = strip.mod_cur > 1e-3;
            // an authored organ channel keeps its rotor under CC1 control even
            // at mod = 0 (that means "brake to slow", not "revert to idle")
            let authored_organ = strip.mod_authored && matches!(strip.program, 16..=23);
            if ci == 9 || (!on && !strip.mod_engaged && !authored_organ) {
                continue;
            }
            let m = if on { strip.mod_cur } else { 0.0 };
            let ch = ci as u8;
            if matches!(strip.program, 16..=23) {
                // organs: the wheel is a Leslie speed control — the channel's
                // one rotor slews with real inertia, and every organ voice on
                // the channel follows it. Once the wheel has been touched, CC1
                // is authoritative: it sweeps the rotor across the full Leslie
                // range (slow chorale .. fast) rather than nudging the program
                // idle, so CC1 = 0 brakes to LESLIE_SLOW_HZ and CC1 = 127 spins
                // up to LESLIE_FAST_HZ. Channels that never author CC1 fall back
                // to the program idle (unreachable here, kept for clarity).
                let (base_rate, base_depth) = voices::organ_trem_base(strip.program);
                if !strip.mod_engaged {
                    // rotor starts at rest: LESLIE_SLOW for an authored channel,
                    // else the program idle
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
                // base depth stays audible even at the slow chorale rate; the
                // wheel only adds extra swirl on top as it spins up
                let target_depth = base_depth + LESLIE_DEPTH_ADD * m;
                strip.leslie_rate += leslie_k * (target_rate - strip.leslie_rate);
                strip.leslie_depth += leslie_k * (target_depth - strip.leslie_depth);
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_trem(strip.leslie_rate, strip.leslie_depth);
                }
                // an authored channel stays engaged for good (its rotor is now
                // CC1-driven); an unauthored one coasts until it reaches idle
                strip.mod_engaged =
                    strip.mod_authored || on || (strip.leslie_rate - base_rate).abs() > 0.01;
            } else if vibrato_family(strip.program) {
                strip.vib_phase += TAU * VIB_RATE_HZ * n as f32 / sr;
                if strip.vib_phase > TAU {
                    strip.vib_phase -= TAU;
                }
                // vibrato multiplies on top of the channel's bend multiplier;
                // the final pass (m = 0) snaps pitch back to the bare bend
                let factor = 2f32.powf(m * VIB_DEPTH_CENTS / 1200.0 * strip.vib_phase.sin());
                strip.vib_mult = factor; // aftertouch/glides compose with it
                let mult = strip.bend * factor;
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_pitch(mult);
                }
                strip.mod_engaged = on;
            } else {
                strip.mod_engaged = false;
            }
        }

        // v0.7 authored controllers: CC70 vowel morph, channel aftertouch,
        // CC5/65 portamento glides. Every branch is gated on authored state,
        // so files that never send them render bit-identically to v0.6.
        for (ci, strip) in strips.iter_mut().enumerate() {
            if ci == 9 {
                continue;
            }
            let ch = ci as u8;
            // CC70: slew the vowel position and retarget ringing formants;
            // the voice's own control-rate smoothing removes any zipper
            if strip.vowel_authored && matches!(strip.program, 52..=54) {
                strip.vowel_cur += expr_smooth * (strip.vowel_target - strip.vowel_cur);
                let (f, q, g) = vowel_at(strip.vowel_cur);
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_vowel(f, q, g);
                }
            }
            // channel aftertouch: pressure smoothed like CC11, adding
            // vibrato depth and a gain lift — a crescendo inside the note
            let mut at_vib = 1.0f32;
            if strip.at_authored && aftertouch_family(strip.program) {
                strip.at_cur += expr_smooth * (strip.at_target - strip.at_cur);
                strip.at_gain = 10f32.powf(strip.at_cur * AT_GAIN_DB / 20.0);
                strip.at_phase += TAU * AT_VIB_RATE_HZ * n as f32 / sr;
                if strip.at_phase > TAU {
                    strip.at_phase -= TAU;
                }
                at_vib = 2f32.powf(strip.at_cur * AT_VIB_CENTS / 1200.0 * strip.at_phase.sin());
                let mult = strip.bend * strip.vib_mult * at_vib;
                for a in active.iter_mut().filter(|a| a.ch == ch) {
                    a.voice.set_pitch(mult);
                }
            }
            // portamento: each gliding voice approaches its own pitch
            for a in active.iter_mut().filter(|a| a.ch == ch) {
                if let Some((semis, k)) = &mut a.glide {
                    *semis -= *k * *semis;
                    let done = semis.abs() < 0.005;
                    let gm = if done { 1.0 } else { 2f32.powf(*semis / 12.0) };
                    a.voice.set_pitch(strip.bend * strip.vib_mult * at_vib * gm);
                    if done {
                        a.glide = None;
                    }
                }
            }
        }

        // voices -> channel buffers. Channel 9 (drums) is HELD OUT here and
        // rendered in the dedicated per-piece pass below (D9) — the strip
        // pass would collapse the kit to a mono point source.
        for buf in ch_buf.iter_mut() {
            buf[..n].fill(0.0);
        }
        stats.max_polyphony = stats.max_polyphony.max(active.len());
        active.retain_mut(|a| {
            if a.ch == 9 {
                return true;
            }
            scratch[..n].fill(0.0);
            let alive = a.voice.render(&mut scratch[..n]);
            let buf = &mut ch_buf[a.ch as usize];
            for i in 0..n {
                buf[i] += scratch[i];
            }
            alive
        });

        // channel strips -> stereo mix + bus sends
        mix_l[..n].fill(0.0);
        mix_r[..n].fill(0.0);
        send_rev[..n].fill(0.0);
        send_cho[..n].fill(0.0);
        send_del[..n].fill(0.0);
        send_sym[..n].fill(0.0);
        send_sym_gtr[..n].fill(0.0);
        send_room[..n].fill(0.0);
        for (ci, strip) in strips.iter_mut().enumerate() {
            let buf = &mut ch_buf[ci];
            if let Some(drive) = &mut strip.drive {
                drive.process(&mut buf[..n]);
            }
            if let Some(wah) = &mut strip.wah {
                // CC74 brightness: on the dry path before the sends tap it,
                // so the wah colours the reverb and echo too; the cutoff and
                // CC71 resonance slew per block so riding CCs don't zipper.
                // Channel 9's filter STATE is reserved for the drum pair in
                // the D9 pass — only the slew/retune happens here.
                strip.cutoff += wah_smooth * (strip.cutoff_target - strip.cutoff);
                strip.res += wah_smooth * (strip.res_target - strip.res);
                wah.retune_lowpass(strip.cutoff, strip.res, sr);
                if ci != 9 {
                    for x in buf[..n].iter_mut() {
                        *x = wah.process(*x);
                    }
                }
            }
            strip.expr += expr_smooth * (strip.expr_target - strip.expr);
            let g = strip.volume * strip.expr * strip.at_gain;
            if g < 1e-6 {
                continue;
            }
            let theta = strip.pan * FRAC_PI_2;
            let (gl, gr) = (g * theta.cos(), g * theta.sin());
            let rs = strip.reverb_send * 0.9;
            let is_piano = ci != 9 && strip.program <= 7;
            let is_ac_gtr = ci != 9 && matches!(strip.program, 24 | 25);
            let haas = strip.haas_delay;
            for i in 0..n {
                let x = buf[i];
                strip.haas.push(x);
                // the far channel is delayed a few milliseconds — Haas
                // localisation instead of a bare level difference
                let (xl, xr) = if haas < 1.0 {
                    (x, x)
                } else if strip.pan < 0.5 {
                    (x, strip.haas.tap(haas))
                } else {
                    (strip.haas.tap(haas), x)
                };
                mix_l[i] += xl * gl;
                mix_r[i] += xr * gr;
                let xs = x * g;
                send_rev[i] += xs * rs;
                send_cho[i] += xs * strip.chorus_send;
                send_del[i] += xs * strip.delay_send;
                if is_piano {
                    send_sym[i] += xs;
                }
                if is_ac_gtr {
                    send_sym_gtr[i] += xs;
                }
            }
        }

        // D9: the dedicated ch-9 pass — every drum voice pans per piece
        // (LEVEL-ONLY equal power, no Haas: the mono-collapse lesson) into a
        // stereo pair that then gets full strip parity: CC74/71 wah pair,
        // CC7/CC11 gain, the CC91 hall send, and the D10 room send.
        {
            let s9 = &mut strips[9];
            drum_l[..n].fill(0.0);
            drum_r[..n].fill(0.0);
            let pan_off = s9.pan - 0.5; // authored CC10 offsets the kit table
            active.retain_mut(|a| {
                if a.ch != 9 {
                    return true;
                }
                scratch[..n].fill(0.0);
                let alive = a.voice.render(&mut scratch[..n]);
                let pan = (drum_pan(a.key) + pan_off).clamp(0.0, 1.0);
                let theta = pan * FRAC_PI_2;
                let (ul, ur) = (theta.cos(), theta.sin());
                for i in 0..n {
                    drum_l[i] += scratch[i] * ul;
                    drum_r[i] += scratch[i] * ur;
                }
                alive
            });
            if let Some(wl) = &mut s9.wah {
                for x in drum_l[..n].iter_mut() {
                    *x = wl.process(*x);
                }
            }
            if let Some(wr) = &mut s9.wah_r {
                wr.retune_lowpass(s9.cutoff, s9.res, sr);
                for x in drum_r[..n].iter_mut() {
                    *x = wr.process(*x);
                }
            }
            let g9 = s9.volume * s9.expr * s9.at_gain;
            if g9 >= 1e-6 {
                let rs = s9.reverb_send * 0.9;
                for i in 0..n {
                    let (xl, xr) = (drum_l[i] * g9, drum_r[i] * g9);
                    mix_l[i] += xl;
                    mix_r[i] += xr;
                    let mono = 0.5 * (xl + xr);
                    send_rev[i] += mono * rs; // the kit keeps its hall
                    send_room[i] += mono * ROOM_SEND;
                }
            }
        }

        symp.process(&send_sym[..n], &mut mix_l[..n], &mut mix_r[..n]);
        if gtr_symp_on {
            gtr_symp.process(&send_sym_gtr[..n], &mut mix_l[..n], &mut mix_r[..n]);
        }
        chorus.process(&send_cho[..n], &mut mix_l[..n], &mut mix_r[..n]);
        if let Some(echo) = &mut echo {
            echo.process(&send_del[..n], &mut mix_l[..n], &mut mix_r[..n]);
        }
        if drum_room_on {
            // pre-hall: the kit sits in a tight room inside the hall
            drum_room.process(&send_room[..n], &mut mix_l[..n], &mut mix_r[..n]);
        }
        for x in send_rev[..n].iter_mut() {
            *x = rev_hp.process(*x);
        }
        reverb.process(&send_rev[..n], &mut mix_l[..n], &mut mix_r[..n]);
        glue.process(&mut mix_l[..n], &mut mix_r[..n]);

        for i in 0..n {
            out[(block_start + i) * 2] = mix_l[i];
            out[(block_start + i) * 2 + 1] = mix_r[i];
            let m = mix_l[i].abs().max(mix_r[i].abs());
            if m > stats.peak {
                stats.peak = m;
            }
        }

        block_start += n;
        if opt.verbose && block_start >= next_report {
            eprintln!(
                "  rendered {:>3.0}%  ({:.1} s, {} live voices)",
                block_start as f64 / total as f64 * 100.0,
                block_start as f64 / sr as f64,
                active.len()
            );
            next_report += total / 10;
        }
    }
    (out, stats)
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

    fn right(stereo: &[f32]) -> Vec<f32> {
        stereo.iter().skip(1).step_by(2).copied().collect()
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
        assert!(corr < 0.9, "kit still a mono point source: corr {corr}");
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

    fn render_bowed_with_mod(mod_val: u8) -> Vec<f32> {
        let song = test_song(
            vec![
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

    /// CC1 = 127 on an organ spins the tremulant up like a Leslie: the
    /// amplitude-modulation rate must climb over ~2 s, not jump.
    #[test]
    fn cc1_leslie_spins_up_with_inertia() {
        let sr = 44100.0;
        let song = test_song(
            vec![
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

    fn render_choir_vowel(cc70: u8) -> Vec<f32> {
        let song = test_song(
            vec![
                (0.0, EvKind::Prog { ch: 0, prog: 52 }),
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
        let late = win(3.8, 4.1); // settled at the A3 target ~220
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
}
