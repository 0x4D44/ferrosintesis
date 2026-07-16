//! Alt bank — GM Bank-Select alternate orchestral voicings.
//!
//! A frozen, isolated resurrection of the v0.9 strings (48-51), choir (52-54)
//! and bowed (40-45) voicings from `v09-backup-pre-rebase`, which trunk's
//! reqs-loop independently superseded. Selected per channel by `CC0 != 0`
//! (engine `Strip.alt_bank`); the default bank and `voices::make` are untouched,
//! so every committed album stays byte-identical. The voice code below is lifted
//! verbatim from that ref — do NOT "improve" it; its whole point is fidelity to
//! the v0.9 renders. See the 2026.07.09 alt-bank HLD in `wrk_docs/`.

use crate::dsp::{key_freq, vel_amp, Adsr, Biquad, BlepSaw, Drift, OnePole, Rng, Sine};
use crate::voices::{Pluck, PluckPreset, Voice};
use std::f32::consts::TAU;

/// Control-rate decimation (matches `voices::CTRL`): the SawStack/Bowed run
/// their per-note modulation once per this many samples.
const CTRL: u32 = 16;

/// LA layering gain/fade for the bowed attack samples (as v0.9's `make`).
const LA_VIOLIN: (f32, (f32, f32)) = (0.30, (0.12, 0.38));

/// Per-sample amplitude multiplier for a -60 dB decay over `t60` seconds
/// (local copy of `voices::t60_mul`, kept identical).
fn t60_mul(t60: f32, sr: f32) -> f32 {
    10f32.powf(-3.0 / (t60.max(0.01) * sr))
}

/// Violin pizzicato (GM 45): the v0.9 `PIZZ` preset, written out in full so the
/// alt bank stays frozen (it does NOT share `voices::DEFAULTS`, which may drift).
const PIZZ: PluckPreset = PluckPreset {
    t60: 0.9,
    bright: 2600.0,
    pick_lp: 1600.0,
    pos: 0.30,
    h1_floor: 0.0,
    amp: 0.58,
    attack_s: 0.0,
    rel_t60: 0.10,
    body: BODY_VIOLIN,
    out_lp: 0.0,
    pickup: 0.0,
    sub: 0.0,
    kick: 0.0,
    cab_lp: 0.0,
    click: 0.6,
    click_hp: 900.0,
    click_post: false,
    attack_noise: 0.25,
    stop_thump: 0.5,
    sub_shape: (0.0, 0.0),
    sub_ramp: 220,
    grit: false,
    buzz: 0.0,
    wound_all: false,
    wound_key_split: true,
    harmonic: false,
    mwah: None, // no fretless vocal bloom on a pizzicato
    // v0.12 course fields: the exact literals the Pluck core used to hardcode
    // (the frozen pre-course polarization voicing).
    course_detune: 1.0013,
    course_t60: 0.42,
    course_bright: 1.15,
    course_mix: (0.74, 0.26),
    course_couple: crate::voices::K_COUPLE,
    // v0.15 electric-guitar v2 fields: explicitly inert (no pickup circuit,
    // no sustainer) — a pizzicato is acoustic and frozen.
    pickup_rlc: (0.0, 0.0),
    sustain: 0.0,
    // v0.16 sitar/banjo fields: explicitly inert (no jawari bridge buzz, no
    // drum-head membrane) — the frozen v0.9 pizzicato has neither.
    jawari: None,
    membrane: &[],
    // v0.16 §2.10 field at its inert default: 1.0 keeps the exact historic
    // velocity arithmetic (bit stream included).
    vel_sense: 1.0,
    // TREM: no tremolo restrike — plucked-tremolo is not the pizzicato
    // idiom (a fast string tremolo is bowed), and the alt bank stays frozen.
    trem: false,
    #[cfg(test)]
    name: "PIZZ",
};

// --- bowed bodies + program tables (BW-2) ---
/// Shared body-resonance tables (BW-2): (freq Hz, Q, gain dB) peak EQs.
/// BODY_VIOLIN reproduces the v0.8.1 inline `Bowed::new` values exactly, so
/// program 40 stays bit-identical.
pub(crate) const BODY_VIOLIN: &[(f32, f32, f32)] =
    &[(280.0, 1.2, 5.0), (610.0, 1.8, 4.0), (1350.0, 1.5, 3.0)];

/// Viola: ~15% larger corpus, a fifth down. Air mode ≈ 220 Hz, corpus modes
/// ≈ 0.78× violin, plus the viola's characteristic nasal band just above 1 kHz.
pub(crate) const BODY_VIOLA: &[(f32, f32, f32)] =
    &[(220.0, 1.3, 5.0), (475.0, 1.8, 4.0), (1200.0, 1.6, 3.5)];

/// Cello: A0 ≈ 100–110 Hz, first corpus (B1) cluster ≈ 190–230 Hz, and the
/// bridge/"vocal" formant ≈ 650 Hz that gives the cello its singing mid.
pub(crate) const BODY_CELLO: &[(f32, f32, f32)] =
    &[(105.0, 1.1, 5.5), (220.0, 1.5, 4.5), (650.0, 1.4, 3.5)];

/// Contrabass: A0 ≈ 60–65 Hz, first top-plate modes ≈ 100–120 Hz, mid formant
/// ≈ 380 Hz. Slightly hotter low peaks: the saw source is weak down there and
/// a real bass's large plates radiate the fundamental region.
pub(crate) const BODY_CONTRABASS: &[(f32, f32, f32)] =
    &[(62.0, 1.0, 5.5), (115.0, 1.3, 4.5), (380.0, 1.4, 3.0)];

/// BW-2: which body a program owns. Violin (40) and tremolo (44) share the
/// violin plates; 45 never reaches `Bowed` (BW-1 routes it to `Pluck`). The
/// 42/43 cello/contrabass bodies ship UNCONDITIONALLY in v0.9 — Arthur chose
/// to ship them and the co-shipping brass voice already re-renders The Iron
/// Tide (HLD §4.3), satisfying the appendix's "iff brass re-renders" condition.
fn bowed_body(program: u8) -> &'static [(f32, f32, f32)] {
    match program {
        41 => BODY_VIOLA,
        42 => BODY_CELLO,
        43 => BODY_CONTRABASS,
        _ => BODY_VIOLIN,
    }
}

/// BW-2: per-program bow character — (vibrato rate Hz, bow-pressure LP floor,
/// bow-pressure LP span). Bigger instruments oscillate slower (rate) and open
/// their brightness ceiling lower (heavier strings/bow). Violin (40) and
/// tremolo (44) keep the exact v0.8.1 numbers, so 40 stays bit-identical.
fn bowed_voice(program: u8) -> (f32, f32, f32) {
    match program {
        41 => (5.1, 800.0, 4600.0), // viola
        42 => (4.8, 700.0, 3800.0), // cello
        43 => (4.2, 550.0, 2800.0), // contrabass
        _ => (5.3, 900.0, 5200.0),  // violin / tremolo
    }
}

// BW-3 bow-tremolo (program 44 only; trem_rate == 0.0 elsewhere)
const TREM_RATE_LO_HZ: f32 = 6.0; // relaxed tremolo at vel 0
const TREM_RATE_VEL_HZ: f32 = 3.0; // + up to 3 Hz: 6–9 Hz across velocity
const TREM_DEPTH_LO: f32 = 0.50; // trough gain 0.50 = −6 dB dips
const TREM_DEPTH_VEL: f32 = 0.15; // harder bowing is more detached (−9 dB max)
const TREM_BITE_S: f32 = 0.018; // bow-noise burst after each reversal
const TREM_JITTER: f32 = 0.06; // ±6% per-stroke rate humanisation
const TREM_AMP_JITTER: f32 = 0.10; // ±10% per-stroke level scatter

pub struct Bowed {
    saw: BlepSaw,
    base_f: f32,
    bend: f32,
    scoop: f32,
    body: Vec<Biquad>, // BW-2: program-selected plates (Nyquist-guarded)
    lp: OnePole,       // bow-pressure brightness: opens with the envelope
    press_lo: f32,     // BW-2: per-program pressure-LP floor / span
    press_span: f32,
    env: Adsr,
    vib: Sine,
    vib_depth: f32,
    vib_delay: u32,
    vib_val: f32,
    // BW-3 bow-tremolo state (inert unless trem_rate > 0.0, i.e. program 44)
    trem_rate: f32,
    trem_rate_cur: f32,
    trem_phase: f32,
    trem_depth: f32,
    trem_stroke_gain: f32,
    trem_gain: f32,
    trem_bite_until: u32,
    rng: Rng,
    t: u32,
    attack_samples: u32,
    last_env: f32,
    amp: f32,
    sr: f32,
}

impl Bowed {
    fn new(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        let vn = vel as f32 / 127.0;
        let attack = vel_attack(0.07, vel);
        let (vib_rate, press_lo, press_span) = bowed_voice(program);
        // BW-3: velocity opens both stroke speed and inter-stroke separation.
        let (trem_rate, trem_depth) = if program == 44 {
            (
                TREM_RATE_LO_HZ + TREM_RATE_VEL_HZ * vn,
                TREM_DEPTH_LO + TREM_DEPTH_VEL * vn,
            )
        } else {
            (0.0, 0.0)
        };
        Bowed {
            saw: BlepSaw::new(f * 0.975, sr, rng.white() * 0.5 + 0.5),
            base_f: f,
            bend: 1.0,
            scoop: 0.975 + 0.008 * vn,
            // BW-2: same Nyquist-guard idiom as Modal::new; at 44.1 kHz every
            // table keeps all three peaks, so program 40 stays bit-identical.
            body: bowed_body(program)
                .iter()
                .filter(|&&(bf, _, _)| bf < sr * 0.45)
                .map(|&(bf, q, g)| Biquad::peak(bf, q, g, sr))
                .collect(),
            lp: OnePole::lowpass(1400.0, sr),
            press_lo,
            press_span,
            env: Adsr::new(attack, 0.2, 0.9, 0.18, sr),
            // The LFO is ticked once per CTRL samples in render(), so it must
            // be built at the CONTROL rate — built at full `sr` it ran 16×
            // slow (the 4th instance of MM-BUG-KILN-00004's idiom bug; the
            // voices.rs Wind/Reed/Bowed/BowedString instances are all fixed).
            vib: Sine::new(vib_rate * (1.0 + 0.1 * rng.white()), sr / CTRL as f32, 0.0),
            vib_depth: 0.0045,
            vib_delay: (0.22 * sr) as u32,
            vib_val: 0.0,
            trem_rate,
            trem_rate_cur: trem_rate,
            trem_phase: 0.0,
            trem_depth,
            trem_stroke_gain: 1.0,
            trem_gain: 1.0,
            trem_bite_until: 0,
            rng,
            t: 0,
            attack_samples: (attack * sr) as u32,
            last_env: 0.0,
            amp: 0.40 * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }
}

impl Voice for Bowed {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.scoop += 0.03 * (1.0 - self.scoop);
                let v = self.vib.next();
                self.vib_val = v;
                let vib = if self.t > self.vib_delay {
                    let ramp = ((self.t - self.vib_delay) as f32 / (0.2 * self.sr)).min(1.0);
                    self.vib_depth * ramp * v
                } else {
                    0.0
                };
                self.saw
                    .set_freq(self.base_f * self.bend * self.scoop * (1.0 + vib), self.sr);
                // more bow pressure -> brighter tone (per-instrument ceiling, BW-2)
                self.lp
                    .set_cutoff(self.press_lo + self.press_span * self.last_env, self.sr);
                // BW-3 bow-tremolo (program 44 only): a raised-cosine amplitude
                // stroke with a bow-noise bite retrigger at each reversal.
                if self.trem_rate > 0.0 {
                    self.trem_phase += self.trem_rate_cur * CTRL as f32 / self.sr;
                    if self.trem_phase >= 1.0 {
                        // stroke reversal == amplitude trough == zero bow speed:
                        // fire the slip-transient bite here, as a real bow does.
                        self.trem_phase -= 1.0;
                        self.trem_bite_until = self.t + (TREM_BITE_S * self.sr) as u32;
                        self.trem_stroke_gain = 1.0 + TREM_AMP_JITTER * self.rng.white();
                        self.trem_rate_cur =
                            self.trem_rate * (1.0 + TREM_JITTER * self.rng.white());
                    }
                    // phase 0 (the reversal) is the trough; amplitude peaks at 0.5.
                    let c = (std::f32::consts::TAU * self.trem_phase).cos();
                    self.trem_gain = self.trem_stroke_gain
                        * ((1.0 - self.trem_depth) + self.trem_depth * 0.5 * (1.0 - c));
                }
            }
            let e = self.env.next();
            self.last_env = e;
            // bow noise: loud while the bow bites (onset, and each tremolo
            // reversal), quieter once the string speaks
            let noise_amp = if self.t < self.attack_samples * 2 || self.t < self.trem_bite_until {
                0.10
            } else {
                0.028
            } * (1.0 + 0.4 * self.vib_val);
            let mut s = self.saw.next() + self.rng.white() * noise_amp * e;
            for b in &mut self.body {
                s = b.process(s);
            }
            s = self.lp.process(s);
            // trem_gain stays exactly 1.0 for programs 40–43 (× 1.0 is bit-exact).
            *o += s * self.amp * e * self.trem_gain;
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
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // one bow, new finger: glide over via the scoop, no fresh bite
        let new_f = key_freq(key);
        self.scoop = (self.base_f * self.scoop / new_f).clamp(0.85, 1.18);
        self.base_f = new_f;
        true
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "bowed"
    }
}

// ---------------------------------------------------------------------------
// SawStack (strings / choir)
// ---------------------------------------------------------------------------

struct Layer {
    osc: BlepSaw,
    ratio: f32,
    vib_phase: f32,
    vib_rate: f32,   // Hz — every player's wobble is their own
    vib_depth: f32,  // fractional pitch deviation — was stack-level (v0.9 §4.1)
    vib_delay: u32,  // CH-3 per-layer vibrato onset (v1: the old global delay)
    vib_ramp_s: f32, // CH-3 per-layer vibrato ramp seconds (v1: 1.0)
    gain: f32,       // CH-2 register/section weight (v1: 1.0 → ×1.0 is bit-exact)
    drift: Drift,
}

/// ST1 envelope-coupled brightness state (strings 48/49/51). The Lp cutoff
/// tracks the note's own `Adsr` level (bow-pressure proxy), like `Bowed`.
/// Carries the cutoff/Q the caller built the filter from — `Biquad` exposes
/// coefficients, not cutoff/Q, so they cannot be recovered from `filt`.
struct EnvBright {
    floor: f32,     // closed-tone cutoff = base_cut × floor
    ref_level: f32, // `open` clamps to 1.0 at this env level (= preset sustain)
    base_cut: f32,  // fully-open cutoff (= the v0.8.1 static cutoff)
    q: f32,         // filter Q for the ST1 retunes
}

enum StackFilter {
    Lp(Biquad),
    /// Vocal formants that morph from a closed schwa into the vowel over the
    /// first ~150 ms of the note ("mm-ah").
    Formant {
        bands: [Biquad; 3],
        gains: [f32; 3],
        cur: [f32; 3],
        tgt: [f32; 3],
        qs: [f32; 3],
    },
}

pub struct SawStack {
    layers: Vec<Layer>,
    base_f: f32,
    bend: f32, // channel pitch multiplier (bend / fine-tune / aftertouch vibrato)
    filt: StackFilter,
    env: Adsr,
    breath: f32,
    rng: Rng,
    sweep: Option<(f32, f32, f32, f32)>, // (lfo phase, rate Hz, base cutoff, octaves)
    sweep_q: f32,
    lp_base: f32, // ST1 envelope-brightness filter state (sentinel 0 when inert)
    lp_q: f32,
    lp_cur: f32,
    env_bright: Option<EnvBright>, // ST1; None for choir / pad / static synth-strings
    last_env: f32,                 // ST1 bow-pressure proxy (the note's own Adsr level)
    ext: Option<ChoirExt>,         // choir v2 (CH-0..CH-4); None on v1 / strings / pad
    t: u32,
    amp: f32,
    sr: f32,
}

impl SawStack {
    #[allow(clippy::too_many_arguments)]
    fn new(
        key: u8,
        vel: u8,
        sr: f32,
        seed: u32,
        n_osc: usize,
        detune: f32,
        drift_depth: f32,
        filt: StackFilter,
        env: Adsr,
        vib: (f32, f32, f32), // (hz, depth, delay s)
        breath: f32,
        sweep: Option<(f32, f32, f32)>, // (rate, base, octaves)
        sweep_q: f32,
        amp: f32,
        env_bright: Option<EnvBright>, // ST1 envelope-brightness (strings); None = inert
        sub_layers: usize,             // ST3-51: last `sub_layers` layers drop an octave
    ) -> Self {
        let f = key_freq(key);
        let mut rng = Rng::new(seed);
        // v1 vibrato onset delay — copied uniformly into every layer (CH-3
        // per-layer state; identical arithmetic ⇒ bit-identical to the old
        // stack-level field).
        let vd = (vib.2 * sr) as u32;
        // ST3-51 low-key guard: below E2 a sub-octave layer would fall under
        // ~41 Hz, so a low divisi reverts to ordinary spread members (no mud).
        let sub_active = if key >= 40 { sub_layers } else { 0 };
        let layers = (0..n_osc)
            .map(|i| {
                // The v1 path (sub_active == 0) computes exactly the v0.8.1
                // ratio; only the unused program 51 takes the sub branch.
                let ratio = if sub_active > 0 && i >= n_osc - sub_active {
                    // octave-down layer with its own small ±0.004 detune, so
                    // the pair does not beat into chorus mud
                    let s = if i % 2 == 0 { 1.0 } else { -1.0 };
                    0.5 * (1.0 + 0.004 * s)
                } else if n_osc > 1 {
                    let spread = (i as f32 / (n_osc - 1) as f32) * 2.0 - 1.0;
                    1.0 + detune * spread
                } else {
                    1.0
                };
                Layer {
                    osc: BlepSaw::new(f * ratio, sr, rng.white() * 0.5 + 0.5),
                    ratio,
                    vib_phase: rng.white() * std::f32::consts::PI,
                    vib_rate: vib.0 * (1.0 + 0.15 * rng.white()),
                    vib_depth: vib.1, // copied uniformly — no new Rng draw (v1 byte-safe)
                    vib_delay: vd,    // v1: the old global delay (copied, never drawn)
                    vib_ramp_s: 1.0,  // v1: fixed 1 s ramp (÷1.0 is bit-exact)
                    gain: 1.0,        // v1: no register weighting (×1.0 is bit-exact)
                    drift: Drift::new(seed ^ (0x1234 + i as u32 * 977), drift_depth, 2800),
                }
            })
            .collect();
        let sweep_phase = rng.white() * std::f32::consts::PI;
        // Sentinels are never read on the None path — the `StackFilter::Lp`
        // arm gates the ST1 retune on `env_bright.is_some()`.
        let (lp_base, lp_q, lp_cur) = match &env_bright {
            Some(eb) => (eb.base_cut, eb.q, eb.base_cut),
            None => (0.0, 0.0, 0.0),
        };
        SawStack {
            layers,
            base_f: f,
            bend: 1.0,
            filt,
            env,
            breath,
            rng,
            sweep: sweep.map(|(rate, base, oct)| (sweep_phase, rate, base, oct)),
            sweep_q,
            lp_base,
            lp_q,
            lp_cur,
            env_bright,
            last_env: 0.0,
            ext: None, // v1 path: choir v2 is built by the separate `choir_v2` factory
            t: 0,
            amp: amp * (0.4 + 0.6 * vel_amp(vel)),
            sr,
        }
    }

    fn control_tick(&mut self) {
        let sr = self.sr;
        let t = self.t;
        let base_f = self.base_f;
        let bend = self.bend;
        // CH-3: each layer ramps its own vibrato in from its own onset delay.
        // On the v1 path every layer carries the old global delay and a 1 s
        // ramp (÷1.0), so the computation is bit-identical to v0.8.1.
        for layer in &mut self.layers {
            layer.vib_phase += TAU * layer.vib_rate * CTRL as f32 / sr;
            let ramp = if t > layer.vib_delay {
                (((t - layer.vib_delay) as f32) / sr / layer.vib_ramp_s).min(1.0)
            } else {
                0.0
            };
            let vib = if ramp > 0.0 && layer.vib_depth > 0.0 {
                layer.vib_depth * ramp * layer.vib_phase.sin()
            } else {
                0.0
            };
            let drift = layer.drift.next();
            layer
                .osc
                .set_freq(base_f * layer.ratio * bend * (1.0 + vib + drift), sr);
        }
        // CH-1: during the consonant hold the vowel morph is frozen at the
        // closed schwa. `released` is always true on the v1 path (ext None),
        // so the morph runs exactly as v0.8.1.
        let released = self.ext.as_ref().is_none_or(|e| t >= e.hum_hold);
        match &mut self.filt {
            StackFilter::Formant {
                bands,
                cur,
                tgt,
                qs,
                ..
            } => {
                if released {
                    for i in 0..3 {
                        if (tgt[i] - cur[i]).abs() > 1.0 {
                            cur[i] += 0.045 * (tgt[i] - cur[i]);
                            bands[i].retune_bandpass(cur[i], qs[i], sr);
                        }
                    }
                }
            }
            StackFilter::Lp(b) => {
                if let Some((phase, rate, base, oct)) = &mut self.sweep {
                    *phase += TAU * *rate * CTRL as f32 / sr;
                    let cut = *base * 2f32.powf(*oct * 0.5 * (phase.sin() + 1.0));
                    b.retune_lowpass(cut.min(sr * 0.4), self.sweep_q, sr);
                } else if let Some(eb) = &self.env_bright {
                    // ST1 envelope-coupled brightness: the section opens as a
                    // note swells and closes as it dies (Bowed's env→cutoff
                    // idiom). `open` clamps to 1.0 from end-of-attack onward, so
                    // a held note's steady cutoff is exactly the v0.8.1 base —
                    // the audible change is confined to attack/release. 1 Hz
                    // epsilon ⇒ zero retunes at steady sustain (formant-morph
                    // idiom). sweep XOR env_bright: no preset carries both.
                    let open = (self.last_env / eb.ref_level).min(1.0);
                    let cut = self.lp_base * (eb.floor + (1.0 - eb.floor) * open);
                    if (cut - self.lp_cur).abs() > 1.0 {
                        b.retune_lowpass(cut, self.lp_q, sr);
                        self.lp_cur = cut;
                    }
                }
            }
        }
        // CH-1: once the hold releases the lips open — a level lift (applied in
        // render) and a brightening lowpass (closed lips damp F2/F3; the square
        // keeps it dark until the mouth is well open).
        if let Some(ext) = &mut self.ext {
            if released {
                ext.mouth += CHOIR2_MOUTH_RATE * (1.0 - ext.mouth);
            }
            let cut = CHOIR2_HUM_LP.0 + (CHOIR2_HUM_LP.1 - CHOIR2_HUM_LP.0) * ext.mouth * ext.mouth;
            ext.hum_lp.set_cutoff(cut, sr);
        }
    }
}

impl Voice for SawStack {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t.is_multiple_of(CTRL) {
                self.control_tick();
            }
            let mut s = 0.0;
            for layer in &mut self.layers {
                // ×1.0 on the v1 path (bit-exact); CH-2 register/section weight on v2.
                s += layer.osc.next() * layer.gain;
            }
            s /= self.layers.len() as f32;
            // CH-1: the onset breath transient rides on top of the sustain floor
            // (0.0 on the v1 path, so the noise-draw sequence is unchanged).
            let breath_now = self.breath + self.ext.as_ref().map_or(0.0, |e| e.breath_env);
            if breath_now > 0.0 {
                s += self.rng.white() * breath_now;
            }
            s = match &mut self.filt {
                StackFilter::Lp(b) => b.process(s),
                StackFilter::Formant { bands, gains, .. } => {
                    let mut y = 0.0;
                    for (b, g) in bands.iter_mut().zip(gains.iter()) {
                        y += b.process(s) * *g;
                    }
                    y
                }
            };
            // CH-1: closed-lips lowpass + mouth-opening level lift (v2 only).
            if let Some(ext) = &mut self.ext {
                s = ext.hum_lp.process(s);
                s *= CHOIR2_HUM_GAIN + (1.0 - CHOIR2_HUM_GAIN) * ext.mouth;
                ext.breath_env *= ext.breath_mul;
            }
            let e = self.env.next();
            self.last_env = e; // ST1 bow-pressure proxy (read at control rate)
            *o += s * self.amp * e;
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
        // applied at control rate on top of each layer's detune/vibrato/drift
        self.bend = mult;
    }

    fn legato_to(&mut self, key: u8, _vel: u8) -> bool {
        // CH-4: a choir-v2 voice sings a melisma — the new note retunes the
        // ringing voice on one vowel (no fresh consonant/breath). v1 SawStacks
        // (strings / pad / choir-v1) keep the trait default (false → retrigger).
        if self.ext.is_some() {
            self.base_f = key_freq(key);
            true
        } else {
            false
        }
    }

    fn set_vowel(&mut self, freqs: [f32; 3], qs: [f32; 3], gains: [f32; 3]) {
        if let StackFilter::Formant {
            tgt,
            qs: q,
            gains: g,
            ..
        } = &mut self.filt
        {
            *tgt = freqs;
            *q = qs;
            *g = gains;
        }
    }

    fn set_vib(&mut self, depth: f32) {
        // ST2 section vibrato: every player deepens their own wobble (the
        // pitches stay decorrelated via the existing per-layer rate/phase
        // jitter, so the section reads as shimmer, not a coherent warble).
        for l in &mut self.layers {
            l.vib_depth = depth;
        }
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        // The v2 discriminant is reachable only through the engine's CC73 gate
        // (`choir_v2` sets `ext`); `voices::make` always builds v1 (ext None).
        if self.ext.is_some() {
            "choir2"
        } else {
            "sawstack"
        }
    }
}

/// Soft notes speak slower: scale an attack time by velocity.
fn vel_attack(base: f32, vel: u8) -> f32 {
    base * (1.45 - 0.65 * (vel as f32 / 127.0))
}

fn strings(program: u8, key: u8, vel: u8, sr: f32, seed: u32) -> SawStack {
    // Per the strings appendix §5. 48/49 are v0.8.1 EXCEPT env_bright (ST1
    // envelope-brightness, default per Arthur — the attack/release open/close
    // the tone while the held-note steady cutoff stays the v0.8.1 base). ST3:
    // 50 = Solina string machine (wide static detune, no player vibrato, bright
    // resonant Lp, static filter = authentic), 51 = dark octave pad (2 sub-octave
    // layers). Both 50/51 are unused by every album → free.
    // (n_osc, sub, detune, drift, lp_hz, lp_q, A, D, S, R, vib, amp, env_bright)
    let (n_osc, sub, detune, drift, lp_hz, lp_q, a, d, s, r, vib, amp, eb) = match program {
        49 => (
            5usize,
            0usize,
            0.007,
            0.0035,
            3200.0,
            0.7,
            vel_attack(0.45, vel),
            0.3,
            0.85,
            0.8,
            (5.1, 0.003, 0.22),
            0.22,
            Some((0.52, 0.85)),
        ),
        50 => (
            4,
            0,
            0.013,
            0.0012,
            5200.0,
            0.9,
            vel_attack(0.05, vel),
            0.25,
            0.9,
            0.45,
            (5.5, 0.0, 0.22),
            0.22,
            None,
        ),
        51 => (
            6,
            2,
            0.010,
            0.0030,
            2600.0,
            0.6,
            vel_attack(0.55, vel),
            0.4,
            0.9,
            1.0,
            (4.8, 0.002, 0.35),
            0.24,
            Some((0.45, 0.9)),
        ),
        _ => (
            5,
            0,
            0.007,
            0.0035,
            4200.0,
            0.7,
            vel_attack(0.07, vel),
            0.3,
            0.85,
            0.35,
            (5.1, 0.003, 0.22),
            0.22,
            Some((0.52, 0.85)),
        ),
    };
    let env_bright = eb.map(|(floor, ref_level)| EnvBright {
        floor,
        ref_level,
        base_cut: lp_hz,
        q: lp_q,
    });
    SawStack::new(
        key,
        vel,
        sr,
        seed,
        n_osc,
        detune,
        drift,
        StackFilter::Lp(Biquad::lowpass(lp_hz, lp_q, sr)),
        Adsr::new(a, d, s, r, sr),
        vib,
        0.0,
        None,
        lp_q,
        amp,
        env_bright,
        sub,
    )
}

/// ST2 wheel-off restore target — each strings program's default per-layer
/// vibrato depth (the constructed value), so CC1 returning to 0 restores the
/// program default on the final engaged pass. Mirrors `organ_trem_base`.
pub fn strings_vib_base(program: u8) -> f32 {
    match program {
        50 => 0.0,   // synth string machine: no player vibrato
        51 => 0.002, // dark octave pad: slow shallow
        _ => 0.003,  // 48/49 string ensembles
    }
}

// --- Choir v2 (ChoirExt onset + SATB scatter) ---
/// CH-2: one SATB section. Cents are relative to the written pitch.
struct ChoirSection {
    off_cents: f32,        // systematic intonation lean
    scatter_cents: f32,    // ± uniform per-note draw
    drift: f32,            // Drift depth for this section
    vib_rate_mul: f32,     // × 4.6 Hz base
    vib_depth_mul: f32,    // × 0.006 base
    vib_delay: (f32, f32), // s, per-layer uniform draw range (CH-3)
    reg: (u8, u8),         // full-weight key range (CH-2 register)
}

/// S, A, T, B — the §4 parameter table. Offsets ≤ 6 cents keep the cluster
/// centre on pitch (harmony intact); scatter grows toward the low voices;
/// vibrato slows and shallows toward the basses (physiology).
const CHOIR2_SECTIONS: [ChoirSection; 4] = [
    ChoirSection {
        off_cents: 3.0,
        scatter_cents: 4.0,
        drift: 0.0035,
        vib_rate_mul: 1.12,
        vib_depth_mul: 1.00,
        vib_delay: (0.20, 0.55),
        reg: (60, 84),
    },
    ChoirSection {
        off_cents: -2.0,
        scatter_cents: 6.0,
        drift: 0.0040,
        vib_rate_mul: 0.97,
        vib_depth_mul: 0.95,
        vib_delay: (0.30, 0.60),
        reg: (53, 74),
    },
    ChoirSection {
        off_cents: 5.0,
        scatter_cents: 8.0,
        drift: 0.0045,
        vib_rate_mul: 1.05,
        vib_depth_mul: 0.90,
        vib_delay: (0.28, 0.58),
        reg: (47, 69),
    },
    ChoirSection {
        off_cents: -6.0,
        scatter_cents: 10.0,
        drift: 0.0055,
        vib_rate_mul: 0.85,
        vib_depth_mul: 0.70,
        vib_delay: (0.35, 0.80),
        reg: (36, 62),
    },
];

const CHOIR2_REG_FADE: f32 = 7.0; // semitones of gain fade outside a section reg
const CHOIR2_REG_FLOOR: f32 = 0.25; // a section never fully mutes
const CHOIR2_HUM_GAIN: f32 = 0.45; // −6.9 dB closed-lips level (CH-1)
const CHOIR2_MOUTH_RATE: f32 = 0.030; // mouth-open slew per CTRL tick
const CHOIR2_HUM_LP: (f32, f32) = (900.0, 8000.0); // closed→open lowpass cutoff Hz
const CHOIR2_BREATH_T60: f32 = 0.09; // onset breath decay, seconds

/// CH-1 consonant/breath onset state — present only on the v2 voice
/// (`SawStack.ext`); `None` on every v1 stack keeps that path bit-exact.
struct ChoirExt {
    hum_hold: u32,   // samples: vowel morph frozen, mouth closed
    mouth: f32,      // 0 closed → 1 open (level + brightness shading)
    hum_lp: OnePole, // CHOIR2_HUM_LP sweep, post-formant-sum
    breath_env: f32, // one-shot onset breath amplitude (decays)
    breath_mul: f32, // per-sample decay = t60_mul(CHOIR2_BREATH_T60, sr)
}

/// CH-2 register weight: 1.0 inside `reg`, fading linearly to
/// `CHOIR2_REG_FLOOR` over `CHOIR2_REG_FADE` semitones outside it.
fn reg_weight(key: u8, reg: (u8, u8)) -> f32 {
    let d = if key < reg.0 {
        (reg.0 - key) as f32
    } else if key > reg.1 {
        (key - reg.1) as f32
    } else {
        0.0
    };
    if d <= 0.0 {
        1.0
    } else {
        let t = (d / CHOIR2_REG_FADE).min(1.0);
        1.0 - (1.0 - CHOIR2_REG_FLOOR) * t
    }
}

/// The factory the engine calls when a channel has authored CC73 and the
/// program is 52–54 (CH-0 gate). Builds a `SawStack` directly with `ext =
/// Some(..)` and per-section (SATB) layer draws — a separate path from
/// `SawStack::new`, so the v1 constructor and its RNG stream are untouched.
pub fn choir_v2(program: u8, key: u8, vel: u8, sr: f32, seed: u32, amt: f32) -> SawStack {
    use std::f32::consts::PI;
    let f = key_freq(key);
    let vn = vel as f32 / 127.0;
    let mut rng = Rng::new(seed);

    // Per-program vowel target + onset multipliers + amp (§5). 54 finally
    // splits from 53 with an "eh" vowel (VOWEL_ANCHORS[3] = [400,1900,2600]).
    // amps pinned by oracle CH-O7 (±1.5 dB vs the v1 render): the 8-layer
    // decorrelation loss is a touch more than the design's √2 (1.10·√2≈1.56),
    // so 52/53 land at 1.87; 54's 6-layer "eh" matches v1's ooh at 1.55.
    let (tgt, hold_mul, br_mul, base_amp): ([f32; 3], f32, f32, f32) = match program {
        52 => ([660.0, 1120.0, 2500.0], 1.0, 1.0, 1.87), // aah
        53 => ([330.0, 870.0, 2300.0], 1.25, 0.7, 1.87), // ooh
        _ => ([400.0, 1900.0, 2600.0], 0.5, 1.4, 1.55),  // 54 "eh"
    };
    let qs = [9.0, 10.0, 9.0];
    let start = [500.0, 1400.0, 2400.0]; // closed-mouth schwa

    let mut layers: Vec<Layer> = Vec::new();
    if program == 54 {
        // 6 layers: 4 scattered unison (±12 cents) + 2 sub-octave (±5 cents)
        // when key ≥ 48; below key 48 the subs revert to unison (mud guard).
        // Uniform scatter, no section leans — a synth stack, not a room.
        let sub_active = key >= 48;
        for i in 0..6u32 {
            let (cents, base_ratio) = if i >= 4 {
                let c = rng.white() * 5.0;
                (c, if sub_active { 0.5 } else { 1.0 })
            } else {
                (rng.white() * 12.0, 1.0)
            };
            let ratio = base_ratio * 2f32.powf(cents / 1200.0);
            let phase = rng.white() * 0.5 + 0.5;
            let vib_phase = rng.white() * PI;
            let vib_rate = 4.6 * (1.0 + 0.15 * rng.white());
            let vib_delay_s = 0.40 + 0.40 * (rng.white() * 0.5 + 0.5); // 0.40–0.80 s
            let vib_ramp_s = 0.5 + 0.7 * (rng.white() * 0.5 + 0.5); // 0.5–1.2 s
            layers.push(Layer {
                osc: BlepSaw::new(f * ratio, sr, phase),
                ratio,
                vib_phase,
                vib_rate,
                vib_depth: 0.005,
                vib_delay: (vib_delay_s * sr) as u32,
                vib_ramp_s,
                gain: 1.0,
                drift: Drift::new(seed ^ (0x1234 + i * 977), 0.0035, 2800),
            });
        }
    } else {
        // 52/53: 8 layers = 2 per SATB section, laid out [S,S,A,A,T,T,B,B].
        for i in 0..8u32 {
            let sec = &CHOIR2_SECTIONS[(i / 2) as usize];
            let cents = sec.off_cents + rng.white() * sec.scatter_cents;
            let ratio = 2f32.powf(cents / 1200.0);
            let phase = rng.white() * 0.5 + 0.5;
            let vib_phase = rng.white() * PI;
            let vib_rate = 4.6 * sec.vib_rate_mul * (1.0 + 0.15 * rng.white());
            let (dlo, dhi) = sec.vib_delay;
            let vib_delay_s = dlo + (dhi - dlo) * (rng.white() * 0.5 + 0.5);
            let vib_ramp_s = 0.5 + 0.7 * (rng.white() * 0.5 + 0.5); // 0.5–1.2 s
            layers.push(Layer {
                osc: BlepSaw::new(f * ratio, sr, phase),
                ratio,
                vib_phase,
                vib_rate,
                vib_depth: 0.006 * sec.vib_depth_mul,
                vib_delay: (vib_delay_s * sr) as u32,
                vib_ramp_s,
                gain: reg_weight(key, sec.reg),
                drift: Drift::new(seed ^ (0x1234 + i * 977), sec.drift, 2800),
            });
        }
    }

    // CH-2 renormalization: force the mean gain to 1 so `s /= layers.len()` in
    // render stays level-flat across the keyboard (register weighting only
    // reshapes the section balance, never the overall loudness).
    let n = layers.len() as f32;
    let sum: f32 = layers.iter().map(|l| l.gain).sum();
    if sum > 0.0 {
        let k = n / sum;
        for l in &mut layers {
            l.gain *= k;
        }
    }

    // CH-1 onset: a closed consonant hold (velocity shortens it, per-program
    // scales it), then the mouth opens; the breath transient is vowel-coloured
    // by the formant bank (injected pre-filter) and dies in ~90 ms.
    let hum_hold_s = (0.035 + 0.075 * amt) * (1.3 - 0.6 * vn) * hold_mul;
    let breath0 = 0.10 * amt * (0.3 + 0.7 * vn) * br_mul;
    let ext = ChoirExt {
        hum_hold: (hum_hold_s * sr) as u32,
        mouth: 0.0,
        hum_lp: OnePole::lowpass(CHOIR2_HUM_LP.0, sr),
        breath_env: breath0,
        breath_mul: t60_mul(CHOIR2_BREATH_T60, sr),
    };

    SawStack {
        layers,
        base_f: f,
        bend: 1.0,
        filt: StackFilter::Formant {
            bands: [
                Biquad::bandpass(start[0], qs[0], sr),
                Biquad::bandpass(start[1], qs[1], sr),
                Biquad::bandpass(start[2], qs[2], sr),
            ],
            gains: [1.0, 0.55, 0.28],
            cur: start,
            tgt,
            qs,
        },
        env: Adsr::new(vel_attack(0.28, vel), 0.3, 0.9, 0.4, sr),
        breath: 0.02,
        rng,
        sweep: None,
        sweep_q: 0.7,
        lp_base: 0.0,
        lp_q: 0.0,
        lp_cur: 0.0,
        env_bright: None,
        last_env: 0.0,
        ext: Some(ext),
        t: 0,
        amp: base_amp * (0.4 + 0.6 * vel_amp(vel)),
        sr,
    }
}

#[cfg(test)]
impl SawStack {
    /// CH-O4: the per-layer pitch ratios (scatter structural check).
    pub(crate) fn layer_ratios(&self) -> Vec<f32> {
        self.layers.iter().map(|l| l.ratio).collect()
    }
    /// CH-O5: the post-renormalization per-layer gains (level-flatness check).
    pub(crate) fn layer_gains(&self) -> Vec<f32> {
        self.layers.iter().map(|l| l.gain).collect()
    }
    /// CH-O6a: the per-layer vibrato onset delays (samples) and ramp lengths.
    pub(crate) fn layer_vib_delays(&self) -> Vec<u32> {
        self.layers.iter().map(|l| l.vib_delay).collect()
    }
    pub(crate) fn layer_vib_ramps(&self) -> Vec<f32> {
        self.layers.iter().map(|l| l.vib_ramp_s).collect()
    }
}

/// CH-O5 helper: the raw (pre-renormalization) register weight a section
/// assigns to `key` — tested directly because renormalization couples every
/// section's absolute gain (see the appendix §8 CH-O5 note).
#[cfg(test)]
pub(crate) fn choir2_reg_weight(key: u8, section: usize) -> f32 {
    reg_weight(key, CHOIR2_SECTIONS[section].reg)
}

// ---------------------------------------------------------------------------
// Factory — the alt bank remaps only 40-45/48-54; everything else delegates to
// the default `voices::make`, so an alt-bank channel still plays its other
// instruments normally.
// ---------------------------------------------------------------------------

pub fn make(
    program: u8,
    bank: u8,
    key: u8,
    vel: u8,
    sr: f32,
    seed: u32,
    samples: bool,
) -> Box<dyn Voice> {
    let samples = samples && crate::embedded_samples_available();
    match program {
        // The default GM19 is the Leslie drawbar. CC0=1 selects the same legacy
        // Leslie voice for scores that intentionally want that secondary colour
        // (notably The Ninth Bell — byte-identical). CC0=2 selects the restored
        // CathedralOrgan pipe model (its own wind-chest breathing + CC11 reed
        // swell + dedicated stone-room reverb).
        19 => match bank {
            2 => crate::voices::cathedral_organ(key, vel, sr, seed),
            _ => crate::voices::legacy_church_organ(key, vel, sr, seed),
        },
        40..=43 => {
            let model = Box::new(Bowed::new(program, key, vel, sr, seed));
            if samples {
                let (gain, fade) = LA_VIOLIN;
                crate::sampler::LaVoice::wrap(
                    model,
                    crate::sampler::violin_bank(vel),
                    key,
                    vel,
                    sr,
                    gain,
                    fade,
                )
            } else {
                model
            }
        }
        44 => Box::new(Bowed::new(44, key, vel, sr, seed)),
        45 => Box::new(Pluck::new(&PIZZ, key, vel, sr, seed)),
        // Alt-bank strings stay the frozen v0.9 SawStack built HERE (this
        // module's own `strings`), never `voices::make` — so the default
        // bank's LA_STRINGS sampled attack layer (voices.rs, GM 48-49)
        // cannot reach alt-bank channels regardless of the samples flag.
        48..=51 => Box::new(strings(program, key, vel, sr, seed)),
        52..=54 => Box::new(choir_v2(program, key, vel, sr, seed, 1.0)),
        // Alt-bank brass stays the frozen v0.9 pure model: the default bank's
        // sampled attack layer (voices.rs LA_BRASS) must not reach alt-bank
        // channels, so the fall-through pins samples off for 56–61.
        56..=61 => crate::voices::make(program, key, vel, sr, seed, false),
        // Same freeze for the alt-bank guitars: the default bank's LA_GUITAR
        // layer (voices.rs, GM 24 nylon and — since 2026.07.16 — GM 25 steel)
        // must not reach alt-bank channels. This pin was placed for 24 while 25
        // still had no layer, explicitly so 25 "stays frozen if one lands"; the
        // Martin HD28 bank landed, so it is now load-bearing for both, and CC0!=0
        // is how a score keeps the pure-model steel. Pinned by
        // altbank_guitars_skip_sample_layer.
        24..=25 => crate::voices::make(program, key, vel, sr, seed, false),
        // Opt-in SUSTAINING lead voicing of the driven guitar (GM 29/30): a
        // held note rings for its whole duration (amp sustain) for a soaring
        // lead with bends and legato. The default-bank 29/30 voice (the
        // decaying DRIVE preset) is untouched; the channel-wide overdrive/
        // cabinet Drive insert still applies (it is program-keyed in engine.rs).
        29 | 30 => Box::new(Pluck::new(&crate::voices::DRIVE_LEAD, key, vel, sr, seed)),
        // Same freeze for alt-bank reeds: the default bank's LA_REED layer
        // (voices.rs, GM 68–71) must not reach alt-bank channels.
        68..=71 => crate::voices::make(program, key, vel, sr, seed, false),
        // v0.12: the alt bank's GM 14 is a tam-tam / gong ageng (the default
        // bank keeps tubular bells).
        14 => Box::new(crate::voices::tam_tam(key, vel, sr, seed)),
        // v0.12 alt-bank percussion set B: a SECOND voicing of GM 112-119
        // (ported from the superseded v0.11 branch), coexisting with the
        // default-bank 112-119 voices, which stay exactly as shipped.
        112 => Box::new(crate::voices::tinkle_bell_b(key, vel, sr, seed)),
        113 => Box::new(crate::voices::agogo_b(key, vel, sr, seed)),
        114 => Box::new(crate::voices::steel_drum_b(key, vel, sr, seed)),
        115 => Box::new(crate::voices::woodblock_b(key, vel, sr, seed)),
        116 => crate::drums::taiko_b(key, vel, sr, seed),
        117 => crate::drums::melodic_tom_b(key, vel, sr, seed),
        118 => crate::drums::synth_drum_b(key, vel, sr, seed),
        119 => crate::drums::reverse_cymbal_b(key, vel, sr, seed),
        _ => crate::voices::make(program, key, vel, sr, seed, samples),
    }
}

// ---------------------------------------------------------------------------
// Alt-bank voice oracles.
//
// Ported from the v0.9 `voices.rs` test module (`v09-backup-pre-rebase`), the
// same ref the voice code above was lifted from. They exercise the alt bank's
// Bowed / pizz / tremolo (40–45), SawStack strings (48–51) and choir v2 (52–54)
// through the alt factory `make` (via `use super::*`), so they pin the
// resurrected voicings against the alt module going forward. Seed-pinned,
// sr 44100; pitch via `peak_locate` (never zero crossings).
// ---------------------------------------------------------------------------
#[cfg(test)]
mod tests {
    use super::*;
    use crate::testutil::{
        assert_render_signature, band_rms, centroid, env_autocorr_peak_detrend, flatness, hp_rms,
        mag_at, peak_locate, render_signature, rms, RenderSignature, BW_TREM_PEAK_FLOOR,
    };

    // --- render helpers (ported from the v0.9 test module) -----------------

    /// Render a bare `Bowed` voice (note held) for `secs` seconds.
    fn render_bowed(program: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = Bowed::new(program, key, vel, sr, seed);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    /// Render an alt-factory `make` voice (note held) for `secs` seconds.
    /// (v0.9 called `crate::voices::make`; here it goes through the alt `make`
    /// so 40–45 route to the resurrected Bowed/PIZZ voicings.)
    fn render_make(program: u8, key: u8, vel: u8, secs: f32, seed: u32, samples: bool) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(program, 1, key, vel, sr, seed, samples);
        let mut buf = vec![0f32; (secs * sr) as usize];
        v.render(&mut buf);
        buf
    }

    /// Render an alt-factory strings voice (`make` → `strings` for 48–51).
    fn render_str(prog: u8, key: u8, secs: f32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(prog, 1, key, 100, sr, 7, false);
        let mut b = vec![0f32; (sr * secs) as usize];
        v.render(&mut b);
        b
    }

    /// Render a fresh choir-v2 voice `secs` seconds (no note_off) into a buffer.
    fn render_choir2(prog: u8, key: u8, vel: u8, amt: f32, secs: f32, seed: u32) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = choir_v2(prog, key, vel, sr, seed, amt);
        let mut b = vec![0f32; (secs * sr) as usize];
        v.render(&mut b);
        b
    }

    // --- Bowed / pizz / tremolo (BW-1/2/3) ---------------------------------

    /// The fiddle's scoop should settle: pitch after a second must be much
    /// closer to nominal than at the onset.
    #[test]
    fn bowed_scoop_settles() {
        let sr = 44100.0;
        let mut v = Bowed::new(40, 69, 100, sr, 11);
        let mut buf = vec![0f32; 44100 * 2];
        v.render(&mut buf);
        let measure = |seg: &[f32]| {
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
        };
        let late = measure(&buf[44100..44100 + 22050]);
        assert!((late - 440.0).abs() < 8.0, "late pitch {late} Hz");
    }

    /// The Bowed vibrato LFO is ticked once per CTRL samples in render(), so
    /// it must be BUILT at the control rate. The 4th instance of
    /// MM-BUG-KILN-00004's idiom bug built it at full `sr`, running the
    /// labelled ~4-5 Hz vibrato at ~0.3 Hz. Counts the LFO's own rising
    /// zero-crossings across two seconds of control ticks (the same pin
    /// voices.rs keeps on `control_lfo`).
    #[test]
    fn bowed_vibrato_lfo_runs_at_control_rate() {
        let sr = 44100.0;
        for (program, rate) in [(40u8, 5.3f32), (41, 5.1), (42, 4.8), (43, 4.2)] {
            let mut v = Bowed::new(program, 60, 100, sr, 11);
            let ticks = (2.0 * sr / CTRL as f32) as usize;
            let mut prev = v.vib.next();
            let mut crossings = 0u32;
            for _ in 1..ticks {
                let cur = v.vib.next();
                if prev <= 0.0 && cur > 0.0 {
                    crossings += 1;
                }
                prev = cur;
            }
            let hz = crossings as f32 / 2.0;
            // the build jitters the rate ±10%; the crossing count adds ±0.5
            assert!(
                (hz - rate).abs() <= 0.10 * rate + 0.5,
                "GM{program} alt-bank vibrato runs at {hz:.2} Hz, labelled {rate} Hz"
            );
        }
    }

    /// BW-O1 — pizzicato 45 decays like a pluck; arco 40 sustains.
    #[test]
    fn pizz_decays_like_a_pluck() {
        let sr = 44100.0;
        let win = |b: &[f32], lo: f32, hi: f32| rms(&b[(lo * sr) as usize..(hi * sr) as usize]);
        let pizz = render_make(45, 69, 100, 2.0, 7, false);
        let ratio = win(&pizz, 1.55, 1.95) / win(&pizz, 0.10, 0.35);
        let arco = render_make(40, 69, 100, 2.0, 7, false);
        let arco_ratio = win(&arco, 1.55, 1.95) / win(&arco, 0.10, 0.35);
        println!("BW-O1: pizz sustain {ratio:.4}, arco sustain {arco_ratio:.4}");
        assert!(ratio < 0.10, "pizz sustain ratio {ratio} (should decay)");
        assert!(
            arco_ratio > 0.7,
            "arco sustain ratio {arco_ratio} (should sustain)"
        );
    }

    /// BW-O2 — pizzicato 45 sounds at pitch, and follows set_pitch (INT-5).
    #[test]
    fn pizz_sounds_at_pitch() {
        let sr = 44100.0;
        let plain = render_make(45, 69, 100, 0.7, 3, false);
        let f0 = peak_locate(
            &plain[(0.05 * sr) as usize..(0.6 * sr) as usize],
            sr,
            300.0,
            600.0,
        );
        assert!((f0 - 440.0).abs() / 440.0 < 0.005, "pizz pitch {f0} Hz");
        // a whole tone up via set_pitch (composed into the ringing string)
        let mut v = make(45, 1, 69, 100, sr, 3, false);
        v.set_pitch(2f32.powf(2.0 / 12.0));
        let mut buf = vec![0f32; (0.7 * sr) as usize];
        v.render(&mut buf);
        let f1 = peak_locate(
            &buf[(0.05 * sr) as usize..(0.6 * sr) as usize],
            sr,
            350.0,
            700.0,
        );
        assert!(
            (f1 - 493.88).abs() / 493.88 < 0.005,
            "bent pizz pitch {f1} Hz"
        );
    }

    /// BW-O3 — the pizzicato body resonator lifts the 280 Hz band. Same-seed
    /// differential against a body-less PIZZ, so the excitation is identical and
    /// only the body EQ chain differs.
    #[test]
    fn pizz_body_engaged() {
        let sr = 44100.0;
        let mut with = Pluck::new(&PIZZ, 61, 100, sr, 9);
        let mut without = Pluck::new(&PluckPreset { body: &[], ..PIZZ }, 61, 100, sr, 9);
        let mut a = vec![0f32; (0.6 * sr) as usize];
        let mut b = vec![0f32; (0.6 * sr) as usize];
        with.render(&mut a);
        without.render(&mut b);
        let (aba, abb) = (band_rms(&a, sr, 280.0, 1.2), band_rms(&b, sr, 280.0, 1.2));
        println!(
            "BW-O3: abs 280 Hz band body {aba:.4} vs no-body {abb:.4} (ratio {:.3})",
            aba / abb
        );
        assert!(aba >= 1.25 * abb, "pizz body 280 Hz lift {aba} vs {abb}");
    }

    /// BW-O4 — per-instrument bodies darken the tone monotonically
    /// (contrabass < cello < viola < violin) and the cello lifts its low band.
    #[test]
    fn bowed_bodies_differ() {
        let sr = 44100.0;
        let keys = [45u8, 48, 52, 55, 59];
        let bright = |p: u8| {
            keys.iter()
                .map(|&k| {
                    let buf = render_bowed(p, k, 96, 1.0, 4);
                    hp_rms(&buf[(0.2 * sr) as usize..(0.9 * sr) as usize], sr, 2500.0)
                })
                .sum::<f32>()
                / keys.len() as f32
        };
        let (b40, b41, b42, b43) = (bright(40), bright(41), bright(42), bright(43));
        let m = |hi: f32, lo: f32| (hi - lo) / lo;
        println!(
            "BW-O4 mean hp2.5k: violin {b40:.5} viola {b41:.5} cello {b42:.5} bass {b43:.5} | margins v>vla {:.3} vla>vc {:.3} vc>cb {:.3}",
            m(b40, b41),
            m(b41, b42),
            m(b42, b43)
        );
        // strict monotone ordering is the hard spec (measured margins ≥ 5%)
        assert!(
            b43 < b42 && b42 < b41 && b41 < b40,
            "brightness order cb {b43} vc {b42} vla {b41} v {b40}"
        );
        // low-band: the cello lifts the 98 Hz (G2) region vs the violin
        let low = |p: u8| {
            let buf = render_bowed(p, 43, 96, 1.0, 4);
            let seg = &buf[(0.2 * sr) as usize..(0.9 * sr) as usize];
            band_rms(seg, sr, 98.0, 1.1) / rms(seg)
        };
        let (l42, l40) = (low(42), low(40));
        println!(
            "BW-O4 low-band: cello {l42:.4} vs violin {l40:.4} (ratio {:.3})",
            l42 / l40
        );
        assert!(l42 >= 1.20 * l40, "cello low-band {l42} vs violin {l40}");
    }

    /// BW-O5 — the bow-tremolo (program 44) amplitude-modulates at ~6-9 Hz and
    /// harder bowing tremolos faster: the AM autocorrelation peaks in-band, the
    /// rate tracks `6 + 3·vel`, and vel 127 is at least 1.5 Hz faster than vel 32.
    #[test]
    fn tremolo_rate_and_velocity() {
        let sr = 44100.0;
        let measure = |vel: u8| {
            let buf = render_bowed(44, 69, vel, 2.5, 5);
            let seg = &buf[(0.4 * sr) as usize..(2.4 * sr) as usize];
            env_autocorr_peak_detrend(seg, sr, 0.08, 0.20, 4.0)
        };
        let (peak100, rate100) = measure(100);
        let (_, rate32) = measure(32);
        let (_, rate127) = measure(127);
        assert!(
            peak100 >= BW_TREM_PEAK_FLOOR,
            "tremolo peak {peak100} < floor"
        );
        let exp100 = 6.0 + 3.0 * (100.0 / 127.0);
        let exp32 = 6.0 + 3.0 * (32.0 / 127.0);
        assert!(
            (rate100 - exp100).abs() / exp100 < 0.15,
            "vel100 rate {rate100} vs {exp100}"
        );
        assert!(
            (rate32 - exp32).abs() / exp32 < 0.15,
            "vel32 rate {rate32} vs {exp32}"
        );
        assert!(
            rate127 - rate32 >= 1.5,
            "velocity rate spread {} Hz",
            rate127 - rate32
        );
    }

    /// BW-O6 — each tremolo reversal re-bites: broadband bow-noise energy jumps
    /// right after each amplitude minimum (the bite fires at the reversal, where
    /// bow speed is zero — §3 BW-3).
    #[test]
    fn tremolo_rebites() {
        let sr = 44100.0;
        let buf = render_bowed(44, 69, 100, 2.5, 5);
        // stroke reversals = local minima of the rectified 200 Hz-LP envelope
        // (self-locating, so immune to the ±6% per-stroke rate jitter)
        let mut lp = OnePole::lowpass(200.0, sr);
        let env: Vec<f32> = buf.iter().map(|&x| lp.process(x.abs())).collect();
        let w = (0.02 * sr) as usize; // ±20 ms local-minimum neighbourhood
        let (lo, hi) = ((0.4 * sr) as usize, (2.3 * sr) as usize);
        let mut minima = Vec::new();
        let mut i = lo;
        while i < hi {
            let is_min =
                (i.saturating_sub(w)..=(i + w).min(env.len() - 1)).all(|j| env[i] <= env[j]);
            if is_min {
                minima.push(i);
                i += (0.06 * sr) as usize; // step past this stroke
            } else {
                i += 1;
            }
        }
        // one-period comb isolates the aperiodic bow-noise bite from the saw
        let period = (sr / key_freq(69)) as usize; // ≈ 100 samples at A4
        let resid: Vec<f32> = (0..buf.len())
            .map(|i| {
                if i >= period {
                    buf[i] - buf[i - period]
                } else {
                    0.0
                }
            })
            .collect();
        let ww = (0.018 * sr) as usize; // window ≈ the 18 ms bite (TREM_BITE_S)
        let mut ratios = Vec::new();
        for &mn in &minima {
            if mn < ww || mn + ww >= buf.len() {
                continue;
            }
            let before = hp_rms(&resid[mn - ww..mn], sr, 3000.0);
            let after = hp_rms(&resid[mn..mn + ww], sr, 3000.0);
            if before > 1e-9 {
                ratios.push(after / before);
            }
        }
        let mean = ratios.iter().sum::<f32>() / ratios.len().max(1) as f32;
        println!(
            "BW-O6: {} reversals, mean rebite hp3k ratio {mean:.3}",
            ratios.len()
        );
        assert!(
            minima.len() >= 8,
            "found too few reversals: {}",
            minima.len()
        );
        assert!(mean >= 1.3, "rebite noise ratio {mean}");
    }

    /// BW-O7 — tremolo 44 and pizzicato 45 ignore the LA sample layer (no wrap):
    /// samples on/off render byte-identical. Arco 40 still wraps (must differ).
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn bowed_44_45_skip_sample_layer() {
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        for prog in [44u8, 45u8] {
            let on = render_make(prog, 69, 100, 0.5, 6, true);
            let off = render_make(prog, 69, 100, 0.5, 6, false);
            assert_eq!(
                bits(&on),
                bits(&off),
                "program {prog} not sample-independent"
            );
        }
        let on = render_make(40, 69, 100, 0.5, 6, true);
        let off = render_make(40, 69, 100, 0.5, 6, false);
        assert_ne!(
            bits(&on),
            bits(&off),
            "arco 40 should wrap the sample layer"
        );
    }

    /// Alt-bank strings 48-51 must ignore the default bank's LA_STRINGS
    /// sampled attack layer: samples on/off render byte-identical (the
    /// frozen v0.9 invariant, same guard as brass/reeds/guitar).
    #[test]
    fn altbank_strings_skip_sample_layer() {
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        for prog in 48..=51u8 {
            let on = render_make(prog, 60, 100, 0.5, 6, true);
            let off = render_make(prog, 60, 100, 0.5, 6, false);
            assert_eq!(
                bits(&on),
                bits(&off),
                "alt-bank strings {prog} not sample-independent"
            );
        }
    }

    /// Alt-bank guitars 24-25 must ignore the default bank's LA_GUITAR sampled
    /// attack layer: samples on/off render byte-identical (the same guard as
    /// brass/reeds/strings).
    ///
    /// This became load-bearing for 25 on 2026.07.16, when the Martin HD28 CC0
    /// bank gave the default steel an LA layer for the first time. Before that
    /// the assertion was vacuous — 25 had no layer to skip — so the `24..=25`
    /// pin in `make` was untested and a future edit could have silently let the
    /// sampled attack through to alt-bank channels. CC0!=0 is how a score asks
    /// for the pure-model steel, so this test is what keeps that promise.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn altbank_guitars_skip_sample_layer() {
        let bits = |b: &[f32]| b.iter().map(|x| x.to_bits()).collect::<Vec<_>>();
        for prog in 24..=25u8 {
            let on = render_make(prog, 52, 100, 0.5, 6, true);
            let off = render_make(prog, 52, 100, 0.5, 6, false);
            assert_eq!(
                bits(&on),
                bits(&off),
                "alt-bank guitar {prog} not sample-independent"
            );
        }
    }

    /// The alt-bank steel must be a real alternative to the default, not a
    /// copy of it: with samples available, default-bank GM 25 (LA-layered) and
    /// alt-bank GM 25 (pure model) must diverge in the attack window. Guards
    /// the other direction from `altbank_guitars_skip_sample_layer` — together
    /// they pin that CC0!=0 selects a genuinely different, un-layered voice.
    #[cfg(feature = "embedded-samples")]
    #[test]
    fn altbank_steel_differs_from_the_layered_default() {
        if !crate::embedded_samples_available() {
            return;
        }
        let sr = 44100.0;
        let alt = render_make(25, 52, 100, 0.5, 6, true);
        let mut d = crate::voices::make(25, 52, 100, sr, 6, true);
        let mut def = vec![0f32; (0.5 * sr) as usize];
        d.render(&mut def);
        let win = (0.05 * sr) as usize;
        let diff: Vec<f32> = alt[..win]
            .iter()
            .zip(&def[..win])
            .map(|(a, b)| a - b)
            .collect();
        let (dr, ar) = (rms(&diff), rms(&alt[..win]));
        assert!(
            dr > 0.3 * ar,
            "alt-bank steel 25 barely differs from the layered default \
             (diff {dr:.5} vs alt {ar:.5}) — is the LA layer leaking through?"
        );
    }

    /// BW-O9 — level bounds. Part (a): the pizz does not jump OUT of the arco's
    /// mix by being LOUDER, and sits within the plucked-string family's level
    /// range (vs the adjacent HARP pluck, now with its soundboard). Part (b):
    /// the per-instrument Bowed
    /// bodies (41/42/43) stay within ±3 dB of the violin (same voice family).
    #[test]
    fn bowed_family_level_match() {
        let sr = 44100.0;
        let db = |a: f32, b: f32| 20.0 * (a / b).log10();
        let ewin = |b: &[f32]| rms(&b[(0.05 * sr) as usize..(0.35 * sr) as usize]);
        // (a) pizz 45 vs arco 40 and vs the HARP pluck, early window [0.05,0.35]s
        let pizz = render_make(45, 69, 100, 0.4, 8, false);
        let arco = render_make(40, 69, 100, 0.4, 8, false);
        let harp = render_make(46, 69, 100, 0.4, 8, false);
        let d_arco = db(ewin(&pizz), ewin(&arco));
        let d_harp = db(ewin(&pizz), ewin(&harp));
        println!("BW-O9: pizz vs arco {d_arco:.2} dB, pizz vs harp {d_harp:.2} dB");
        assert!(
            d_arco <= 3.0,
            "pizz louder than arco ({d_arco} dB) — would jump out"
        );
        assert!(
            d_harp.abs() <= 10.0,
            "pizz {d_harp} dB off the HARP pluck reference"
        );
        // (b) per-instrument bodies 41/42/43 vs violin 40 at A3 (key 57), same
        // Bowed family — the appendix's ±3 dB applies here
        for p in [41u8, 42, 43] {
            let a = render_bowed(p, 57, 100, 1.0, 8);
            let v40 = render_bowed(40, 57, 100, 1.0, 8);
            let d = db(rms(&a), rms(&v40));
            println!("BW-O9: prog{p} vs violin {d:.2} dB");
            assert!(d.abs() <= 3.0, "prog {p} level {d} dB off violin");
        }
    }

    // --- SawStack / strings (ST1/2/3) --------------------------------------

    /// Portable SawStack contamination canary against the alt module. The
    /// v0.9 form pinned `make(89)` (pad, Lp) and `make(52)` (then a v1 choir).
    /// In the alt factory `make(52)` routes to `choir_v2` and `make(89)`
    /// delegates to trunk's pad, so both signatures are calibrated to what the
    /// alt module actually renders. Tight level, spectrum, and envelope
    /// signatures catch contamination without depending on non-portable raw
    /// floating-point fingerprints.
    #[test]
    fn sawstack_v1_signatures_are_stable() {
        let sr = 44100.0;
        let render = |prog: u8, key: u8| {
            let mut v = make(prog, 1, key, 100, sr, 7, false);
            let mut b = vec![0f32; (sr * 1.5) as usize];
            v.render(&mut b);
            b
        };
        let pad = render(89, 60);
        let choir = render(52, 60);
        assert_render_signature(
            "alt pad(89)",
            render_signature(&pad, sr, (0.2, 0.8), (0.1, 0.3), (0.9, 1.3)),
            RenderSignature {
                rms_db: -21.567,
                centroid_hz: 611.243,
                late_early_db: 1.923,
            },
        );
        assert_render_signature(
            "alt choir(52)",
            render_signature(&choir, sr, (0.2, 0.8), (0.1, 0.3), (0.9, 1.3)),
            RenderSignature {
                rms_db: -29.502,
                centroid_hz: 1308.458,
                late_early_db: 2.215,
            },
        );
    }

    /// ST1 (envelope-coupled brightness): a string-ensemble note's attack (env
    /// rising, filter partly closed) is darker than its sustain (env at the
    /// preset level, filter fully open = the v0.8.1 base cutoff).
    #[test]
    fn st1_env_brightness_opens_the_tone() {
        let sr = 44100.0;
        let b = render_str(48, 60, 1.5);
        let seg = |a: f32, z: f32| &b[(a * sr) as usize..(z * sr) as usize];
        let attack = centroid(seg(0.005, 0.03), sr);
        let sustain = centroid(seg(0.6, 1.0), sr);
        assert!(
            attack < 0.9 * sustain,
            "ST1 attack {attack:.0} Hz not < 0.9x sustain {sustain:.0} Hz"
        );
    }

    /// ST3 (synth-strings identity): 50 (SynthStr1, static filter — no ST1
    /// env-brightness) and 51 (SynthStr2, dark octave pad) get their own
    /// voices. 50 renders distinctly from 48; 51 is darker than 48 and carries
    /// a sub-octave 48 lacks.
    #[test]
    fn st3_synth_strings_identity() {
        let sr = 44100.0;
        // 50 and 51 are their own voices, not clones of 48.
        assert_ne!(
            render_str(50, 60, 0.5),
            render_str(48, 60, 0.5),
            "50 renders distinctly from 48"
        );
        // 51 (dark octave pad, Lp 2600 + sub-octave layers) is measurably darker
        // than the plain 48 ensemble (Lp 4200) and carries a sub-octave 48 lacks.
        let b51 = render_str(51, 60, 1.0);
        let s51 = &b51[(0.3 * sr) as usize..(0.9 * sr) as usize];
        let b48 = render_str(48, 60, 1.0);
        let s48 = &b48[(0.3 * sr) as usize..(0.9 * sr) as usize];
        assert!(
            centroid(s51, sr) < 0.85 * centroid(s48, sr),
            "51 darker than 48 ({:.0} vs {:.0})",
            centroid(s51, sr),
            centroid(s48, sr)
        );
        let f0 = key_freq(60);
        assert!(
            mag_at(s51, sr, f0 * 0.5) > 0.2 * mag_at(s51, sr, f0),
            "51 sub-octave present ({:.4} vs f0 {:.4})",
            mag_at(s51, sr, f0 * 0.5),
            mag_at(s51, sr, f0)
        );
    }

    /// ST2 (CC1 section vibrato): deepening every layer's vibrato via `set_vib`
    /// spreads the carrier into FM sidebands, so the on-f0 prominence drops vs
    /// the shallow default. Measured at A5 (β decisive).
    #[test]
    fn st2_section_vibrato_spreads_carrier() {
        let sr = 44100.0;
        let carrier = |depth: f32| {
            let mut v = make(48, 1, 81, 100, sr, 7, false); // A5
            v.set_vib(depth);
            let mut b = vec![0f32; (sr * 2.0) as usize];
            v.render(&mut b);
            let seg = &b[(1.4 * sr) as usize..(1.9 * sr) as usize];
            mag_at(seg, sr, key_freq(81)) / rms(seg).max(1e-9)
        };
        let shallow = carrier(0.003); // wheel off (base)
        let deep = carrier(0.012); // full wheel
        assert!(
            deep < 0.7 * shallow,
            "ST2 deep vibrato collapses the carrier: deep {deep:.4} not < 0.7x shallow {shallow:.4}"
        );
    }

    // --- Choir v2 (CH-0..CH-4) ---------------------------------------------

    /// CH-O1 (voice half): in the alt factory both `make(52..=54)` and
    /// `choir_v2(52..=54)` build the v2 choir (`kind()=="choir2"`). (The v0.9
    /// form asserted `make` built a v1 "sawstack"; the alt factory routes 52–54
    /// straight to `choir_v2`, so the expected kind is adapted to "choir2".)
    #[test]
    fn ch_o1_choir_v2_kind() {
        let sr = 44100.0;
        for prog in 52..=54u8 {
            assert_eq!(make(prog, 1, 60, 96, sr, 7, false).kind(), "choir2");
            assert_eq!(choir_v2(prog, 60, 96, sr, 7, 0.75).kind(), "choir2");
        }
    }

    /// CH-O2 (consonant darkness): the closed onset is far darker than the open
    /// vowel — early-window centroid < 0.55× the sustained-vowel centroid.
    #[test]
    fn ch_o2_consonant_darkness() {
        let sr = 44100.0;
        let b = render_choir2(52, 60, 96, 96.0 / 127.0, 3.0, 7);
        let seg = |a: f32, z: f32| &b[(a * sr) as usize..(z * sr) as usize];
        let early = centroid(seg(0.020, 0.090), sr);
        let late = centroid(seg(0.500, 0.900), sr);
        println!(
            "CH-O2 early {early:.0} Hz late {late:.0} Hz ratio {:.3}",
            early / late
        );
        assert!(
            early < 0.55 * late,
            "consonant not dark: early {early:.0} not < 0.55x late {late:.0}"
        );
    }

    /// CH-O3 (consonant level shading + breath, differential): amt=1 vs amt=0,
    /// same seed (same RNG stream). The difference is an onset phenomenon and
    /// the breath makes the amt=1 early window noisier (flatness ≥ 1.5×).
    #[test]
    fn ch_o3_consonant_shading_and_breath() {
        let sr = 44100.0;
        let hi = render_choir2(52, 60, 96, 1.0, 3.0, 7);
        let lo = render_choir2(52, 60, 96, 0.0, 3.0, 7);
        let diff: Vec<f32> = hi.iter().zip(&lo).map(|(a, b)| a - b).collect();
        let s = |a: f32, z: f32| ((a * sr) as usize, (z * sr) as usize);
        let (o0, o1) = s(0.0, 0.2);
        let (u0, u1) = s(1.0, 1.2);
        let (e0, e1) = s(0.020, 0.090);
        let onset = rms(&diff[o0..o1]);
        let sustain = rms(&diff[u0..u1]).max(1e-12);
        let onset_db = 20.0 * (onset / sustain).log10();
        let f_hi = flatness(&hi[e0..e1], sr, 800.0, 4000.0);
        let f_lo = flatness(&lo[e0..e1], sr, 800.0, 4000.0);
        println!(
            "CH-O3 onset {onset:.5} sustain {sustain:.6} ({onset_db:.1} dB); \
             flatness hi {f_hi:.4} lo {f_lo:.4} ratio {:.2}",
            f_hi / f_lo
        );
        assert!(
            onset > 2.0 * sustain,
            "consonant diff not an onset: {onset_db:.1} dB"
        );
        assert!(
            f_hi >= 1.5 * f_lo,
            "breath not noisier: flatness hi {f_hi:.4} vs lo {f_lo:.4}"
        );
    }

    /// CH-O4 (scatter, structural): per-note random SATB scatter with systematic
    /// section leans. (a) every ratio sits within its section's ±scatter of the
    /// section lean; (b) the tenor pair leans sharp and the bass pair flat;
    /// (c) two seeds share no micro-tuning (round-robin).
    #[test]
    fn ch_o4_scatter_is_sectioned() {
        let sr = 44100.0;
        let r1 = choir_v2(52, 60, 96, sr, 7, 0.75).layer_ratios();
        let r2 = choir_v2(52, 60, 96, sr, 13, 0.75).layer_ratios();
        assert_eq!(r1.len(), 8);
        // (a) structural bound per layer
        for (i, &r) in r1.iter().enumerate() {
            let sec = &CHOIR2_SECTIONS[i / 2];
            let cents = 1200.0 * r.log2();
            assert!(
                (cents - sec.off_cents).abs() <= sec.scatter_cents + 0.05,
                "layer {i} cents {cents:.2} outside {}±{}",
                sec.off_cents,
                sec.scatter_cents
            );
        }
        // (b) systematic lean emerges over many seeds (scatter averages out)
        let n = 48u32;
        let (mut ten, mut bas) = (0.0f64, 0.0f64);
        for s in 0..n {
            let r = choir_v2(52, 60, 96, sr, 100 + s, 0.75).layer_ratios();
            ten += (600.0 * (r[4].log2() + r[5].log2())) as f64;
            bas += (600.0 * (r[6].log2() + r[7].log2())) as f64;
        }
        ten /= n as f64;
        bas /= n as f64;
        println!("CH-O4 tenor lean {ten:.2} cents, bass lean {bas:.2} cents");
        assert!(ten > 1.0, "tenor pair should lean sharp: {ten:.2} cents");
        assert!(bas < -1.0, "bass pair should sag flat: {bas:.2} cents");
        // (c) round-robin: no shared micro-tuning across seeds
        for &a in &r1 {
            for &b in &r2 {
                assert!((a - b).abs() > 1e-9, "seeds share a micro-tuning");
            }
        }
    }

    /// CH-O5 (register weighting, structural). On the raw (pre-renorm) section
    /// weights: a soprano low note and a bass high note both floor to ≤ 0.35×
    /// their in-range weight. On the post-renorm gains: the mean is exactly 1
    /// (keeps `s /= len` level-safe) and no gain is zero.
    #[test]
    fn ch_o5_register_weighting() {
        // raw section weights (soprano = section 0, bass = section 3)
        let sop_lo = choir2_reg_weight(40, 0);
        let sop_hi = choir2_reg_weight(72, 0);
        assert!(
            sop_lo <= 0.35 * sop_hi,
            "soprano key40 {sop_lo} not <= 0.35x key72 {sop_hi}"
        );
        let bas_hi = choir2_reg_weight(79, 3);
        let bas_lo = choir2_reg_weight(50, 3);
        assert!(
            bas_hi <= 0.35 * bas_lo,
            "bass key79 {bas_hi} not <= 0.35x key50 {bas_lo}"
        );
        // post-renorm level flatness across the keyboard
        let sr = 44100.0;
        for key in [40u8, 48, 60, 72, 79] {
            let g = choir_v2(52, key, 96, sr, 7, 0.75).layer_gains();
            let mean = g.iter().sum::<f32>() / g.len() as f32;
            assert!((mean - 1.0).abs() < 1e-4, "key {key} mean gain {mean}");
            assert!(g.iter().all(|&x| x > 0.0), "key {key} has a zero gain");
        }
    }

    /// CH-O6 (shimmer). (a) Structural: the 8 vibrato onset delays span ≥ 0.25 s
    /// and are not all equal; ramps span ≥ 0.3 s. (b) Audio: a same-seed depth-0
    /// vs depth-on difference render isolates the vibrato from the identical
    /// static cluster — its energy blooms from the early window to the late one.
    #[test]
    fn ch_o6_shimmer_blooms() {
        let sr = 44100.0;
        let v = choir_v2(52, 60, 96, sr, 7, 0.75);
        let d = v.layer_vib_delays();
        let dmin = *d.iter().min().unwrap() as f32 / sr;
        let dmax = *d.iter().max().unwrap() as f32 / sr;
        assert!(
            dmax - dmin >= 0.25,
            "vib delays span only {:.3} s",
            dmax - dmin
        );
        assert!(d.iter().any(|&x| x != d[0]), "vib delays all equal");
        let r = v.layer_vib_ramps();
        let rmin = r.iter().cloned().fold(f32::MAX, f32::min);
        let rmax = r.iter().cloned().fold(f32::MIN, f32::max);
        assert!(
            rmax - rmin >= 0.3,
            "vib ramps span only {:.3} s",
            rmax - rmin
        );
        // (b) difference render: depth-on minus depth-0 = the vibrato alone
        let full = render_choir2(52, 60, 96, 0.75, 3.0, 7);
        let mut vz = choir_v2(52, 60, 96, sr, 7, 0.75);
        vz.set_vib(0.0);
        let mut z = vec![0f32; (3.0 * sr) as usize];
        vz.render(&mut z);
        let diff: Vec<f32> = full.iter().zip(&z).map(|(a, b)| a - b).collect();
        let seg = |a: f32, zt: f32| &diff[(a * sr) as usize..(zt * sr) as usize];
        let early = rms(seg(0.1, 0.6)).max(1e-12);
        let late = rms(seg(2.0, 2.9));
        let db = 20.0 * (late / early).log10();
        println!("CH-O6 shimmer early {early:.6} late {late:.6} ({db:.1} dB)");
        assert!(late >= 2.0 * early, "shimmer did not bloom: {db:.1} dB");
    }

    // =======================================================================
    // v0.12 — alt-bank percussion set B (GM 112-119) + GM 14 tam-tam oracles.
    // Ported from the superseded v0.11 branch (216da4a); the voices were
    // default-bank there, so the oracles now render through the alt factory
    // `make` and anchor their level knobs to DEFAULT-bank comparators
    // (glockenspiel 9 / xylophone 13 / marimba 12 / timpani 47), which are
    // unchanged since the branch forked.
    // =======================================================================

    const SR12: f32 = 44100.0;

    /// Render an alt-bank voice via the alt factory (the real CC0 seam).
    fn render_alt(program: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        render_make(program, key, vel, secs, seed, false)
    }

    /// Render the DEFAULT-bank voice of the same program (comparators, and
    /// the bank-B distinctness differentials).
    fn render_def(program: u8, key: u8, vel: u8, secs: f32, seed: u32) -> Vec<f32> {
        let mut v = crate::voices::make(program, key, vel, SR12, seed, false);
        let mut buf = vec![0f32; (SR12 * secs) as usize];
        v.render(&mut buf);
        buf
    }

    fn seg12(buf: &[f32], a: f32, b: f32) -> &[f32] {
        &buf[(a * SR12) as usize..(b * SR12) as usize]
    }

    fn db_ratio(a: f32, b: f32) -> f32 {
        20.0 * (a / b.max(1e-12)).log10()
    }

    fn max_abs(s: &[f32]) -> f32 {
        s.iter().fold(0f32, |m, &x| m.max(x.abs()))
    }

    /// First time (seconds) the raw |sample| reaches 90% of the render's peak.
    fn rise_to_090_s(buf: &[f32]) -> f32 {
        let peak = max_abs(buf);
        buf.iter()
            .position(|&x| x.abs() >= 0.9 * peak)
            .map_or(f32::INFINITY, |i| i as f32 / SR12)
    }

    /// RMS of `[a, z]` s of the WHOLE-buffer highpass — filter first, then
    /// window (a mid-ring slice boundary excites the filter as a step).
    fn hp_win(b: &[f32], corner: f32, a: f32, z: f32) -> f32 {
        let mut hp = Biquad::highpass(corner, 0.7, SR12);
        let f: Vec<f32> = b.iter().map(|&x| hp.process(x)).collect();
        rms(seg12(&f, a, z))
    }

    /// T1+T2: bank-B GM 112 tinkle bell speaks at the written pitch (folded
    /// register) and rings out in well under a second (fast-fading small
    /// bell, not a glock sustain and not a one-sample click).
    #[test]
    fn altbank_b112_tinkle_pitch_and_decay() {
        let b = render_alt(112, 84, 100, 1.2, 0x11_2001);
        // pitch: Goertzel argmax (never zero-crossings) on the early ring
        let f = peak_locate(seg12(&b, 0.02, 0.40), SR12, 700.0, 1500.0);
        assert!(
            (f / 1046.5 - 1.0).abs() <= 0.015,
            "B112 key 84 pitch {f:.1} Hz vs 1046.5 Hz"
        );
        let late = rms(seg12(&b, 0.80, 1.00));
        let early = rms(seg12(&b, 0.02, 0.22));
        let ratio = late / early.max(1e-12);
        println!("B112 decay ratio late/early = {ratio:.4}");
        assert!(
            (0.005..=0.12).contains(&ratio),
            "B112 decay ratio {ratio:.4} outside [0.005, 0.12]"
        );
    }

    /// T3 (level knob TINKLE_B_GAIN): the tinkle bell sits with the
    /// mallet/bell family — within ±2 dB of the default-bank glockenspiel at
    /// the SAME key (matched pitch per lessons_learnt).
    #[test]
    fn altbank_b112_tinkle_level_vs_glock() {
        let tink = render_alt(112, 84, 100, 0.4, 0x11_2002);
        let glock = render_def(9, 84, 100, 0.4, 0x11_2002);
        let d = db_ratio(
            rms(seg12(&tink, 0.02, 0.32)),
            rms(seg12(&glock, 0.02, 0.32)),
        );
        println!("B112 vs glock level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B112 level {d:+.2} dB off glock (>2 dB)");
    }

    /// T4: the three bank-B Modal percussion voices are genuinely new
    /// timbres — brighter centroid than the celesta at matched pitch, and
    /// render-hash distinct from every default-bank keyboard-percussion
    /// program AND from each other at the same key/vel/seed.
    #[test]
    fn altbank_b112_114_timbre_distinct_at_matched_pitch() {
        let key = 84;
        let seed = 0x11_2003;
        let tink = render_alt(112, key, 100, 0.4, seed);
        let cele = render_def(8, key, 100, 0.4, seed);
        // Brightness at matched pitch, in the strike's live window (the upper
        // modes carrying the "tinkle" have sub-second t60s). Measured as the
        // above-2-kHz energy share — the 20-bin log centroid is a bin-placement
        // lottery for sparse line spectra and cannot carry this comparison.
        let bright = |b: &[f32]| {
            let s = seg12(b, 0.01, 0.11);
            hp_rms(s, SR12, 2000.0) / rms(s).max(1e-12)
        };
        let bt = bright(&tink);
        let bc = bright(&cele);
        println!("B112 hp2k share {bt:.3} vs celesta {bc:.3}");
        assert!(
            bt >= 1.25 * bc,
            "B112 brightness {bt:.3} not >=1.25x celesta {bc:.3}"
        );
        let mut renders: Vec<(String, Vec<f32>)> = [112u8, 113, 114]
            .iter()
            .map(|&p| (format!("alt{p}"), render_alt(p, key, 100, 0.8, seed)))
            .collect();
        for p in [8u8, 9, 10, 12, 14] {
            renders.push((format!("def{p}"), render_def(p, key, 100, 0.8, seed)));
        }
        for i in 0..renders.len() {
            for j in (i + 1)..renders.len() {
                assert_ne!(
                    renders[i].1, renders[j].1,
                    "{} and {} render identically at key {key}",
                    renders[i].0, renders[j].0
                );
            }
        }
    }

    /// A1+A2: bank-B GM 113 agogo speaks at the written pitch and is SHORT —
    /// a dry clang bell, gone within half a second.
    #[test]
    fn altbank_b113_agogo_pitch_short_decay() {
        let b = render_alt(113, 81, 100, 0.6, 0x11_3001);
        let f = peak_locate(seg12(&b, 0.01, 0.15), SR12, 600.0, 1200.0);
        assert!(
            (f / 880.0 - 1.0).abs() <= 0.015,
            "B113 key 81 pitch {f:.1} Hz vs 880 Hz"
        );
        let ratio = rms(seg12(&b, 0.30, 0.40)) / rms(seg12(&b, 0.01, 0.11)).max(1e-12);
        println!("B113 decay ratio = {ratio:.4}");
        assert!(
            (0.002..=0.06).contains(&ratio),
            "B113 decay ratio {ratio:.4} outside [0.002, 0.06]"
        );
    }

    /// A3: the agogo's identity is the cowbell-family clang partial near
    /// 1.51x f0 — present and prominent, but below the fundamental.
    #[test]
    fn altbank_b113_agogo_clang_mode() {
        let b = render_alt(113, 81, 100, 0.3, 0x11_3002);
        let s = seg12(&b, 0.01, 0.15);
        let clang_f = peak_locate(s, SR12, 1.45 * 880.0, 1.60 * 880.0);
        let ratio = mag_at(s, SR12, clang_f) / mag_at(s, SR12, 880.0).max(1e-12);
        println!("B113 clang mode at {clang_f:.0} Hz, clang/fund = {ratio:.3}");
        assert!(
            (0.25..=1.2).contains(&ratio),
            "B113 clang/fundamental ratio {ratio:.3} outside [0.25, 1.2]"
        );
    }

    /// A4 (level knob AGOGO_B_GAIN): within ±2 dB of the default-bank
    /// xylophone at the same key (both short bright percussion in the same
    /// register).
    #[test]
    fn altbank_b113_agogo_level_vs_xylophone() {
        let ago = render_alt(113, 81, 100, 0.3, 0x11_3003);
        let xyl = render_def(13, 81, 100, 0.3, 0x11_3003);
        let d = db_ratio(rms(seg12(&ago, 0.01, 0.21)), rms(seg12(&xyl, 0.01, 0.21)));
        println!("B113 vs xylophone level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B113 level {d:+.2} dB off xylophone");
    }

    /// S1: the steel pan's spectral signature — a strong octave (2.000x) and
    /// near-twelfth (3.011x) over the fundamental, and an octave FAR more
    /// prominent than the marimba's (whose modes sit at 3.0/5.2, not 2.0).
    #[test]
    fn altbank_b114_steel_octave_twelfth_prominence() {
        let f0 = 261.63_f32;
        let pan = render_alt(114, 60, 100, 1.0, 0x11_4001);
        let s = seg12(&pan, 0.05, 0.60);
        let fund = mag_at(s, SR12, f0).max(1e-12);
        let oct = mag_at(s, SR12, 2.0 * f0) / fund;
        let twelfth = mag_at(s, SR12, 3.011 * f0) / fund;
        let mar = render_def(12, 60, 100, 1.0, 0x11_4001);
        let mseg = seg12(&mar, 0.05, 0.60);
        let moct = mag_at(mseg, SR12, 2.0 * f0) / mag_at(mseg, SR12, f0).max(1e-12);
        println!("B114 oct {oct:.3} twelfth {twelfth:.3}; marimba oct {moct:.3}");
        assert!(oct >= 0.40, "B114 octave/fund {oct:.3} < 0.40");
        assert!(twelfth >= 0.20, "B114 twelfth/fund {twelfth:.3} < 0.20");
        assert!(
            oct >= 3.0 * moct,
            "B114 octave {oct:.3} not >=3x marimba's {moct:.3}"
        );
    }

    /// S2: a rubber pan mallet lands SOFT — the render takes materially longer
    /// to reach 90% of its peak than the hard-struck xylophone.
    #[test]
    fn altbank_b114_steel_soft_attack_vs_xylophone() {
        let pan = render_alt(114, 60, 100, 0.3, 0x11_4002);
        let xyl = render_def(13, 60, 100, 0.3, 0x11_4002);
        let t_pan = rise_to_090_s(&pan);
        let t_xyl = rise_to_090_s(&xyl);
        println!(
            "B114 rise {:.1} ms, xylophone {:.1} ms",
            t_pan * 1e3,
            t_xyl * 1e3
        );
        assert!(t_pan >= 0.006, "B114 attack {:.1} ms < 6 ms", t_pan * 1e3);
        assert!(
            t_xyl < 0.004,
            "xylophone attack {:.1} ms >= 4 ms",
            t_xyl * 1e3
        );
    }

    /// S3: the pan's signature shimmer — the 2.000/2.018 octave twin pair
    /// beats at 0.018*f0 (~4.7 Hz at C4). Bandpass the octave, flatten the
    /// decay, then read the AM rate off the envelope autocorrelation.
    #[test]
    fn altbank_b114_steel_octave_twin_shimmer() {
        let f0 = 261.63_f32;
        let pan = render_alt(114, 60, 100, 1.3, 0x11_4003);
        // window starts at 0.30 s: the decay-flattening tracker (tau ~0.13 s)
        // must converge before the beat is read, or its warm-up ramp aliases
        // into the lag window as a phantom rate
        let (peak, rate) = twin_beat_autocorr(&pan, 2.0 * f0, 0.30, 1.25, 0.12, 0.35);
        println!("B114 twin beat: peak {peak:.3} at {rate:.2} Hz");
        assert!(
            peak >= 0.20,
            "B114 twin-beat autocorr peak {peak:.3} < 0.20"
        );
        assert!(
            (rate - 4.7).abs() <= 1.2,
            "B114 twin-beat rate {rate:.2} Hz not 4.7 +/- 1.2 Hz"
        );
    }

    /// Beat detector for decaying twin pairs: bandpass at `bp_f` (Q 8), take
    /// the rectified envelope, FLATTEN the exponential decay by dividing by a
    /// lagged one-pole of the same envelope (an exponential decay becomes a
    /// near-constant under that division; the beat's AM survives), then a
    /// mean-removed normalised autocorrelation over the lag window. The
    /// plain env_autocorr on these percussive twins is decay-dominated (the
    /// t60s here are ~1 s, a 60 dB/s trend that buries a +/-1-2 dB beat), so
    /// the flattening is load-bearing — see lessons_learnt on measuring a
    /// feature inside its live window.
    fn twin_beat_autocorr(
        buf: &[f32],
        bp_f: f32,
        a_s: f32,
        z_s: f32,
        lag_lo_s: f32,
        lag_hi_s: f32,
    ) -> (f32, f32) {
        let mut bp = Biquad::bandpass(bp_f, 8.0, SR12);
        let mut env_lp = OnePole::lowpass(40.0, SR12);
        let mut slow = OnePole::lowpass(1.2, SR12);
        let mut flat = Vec::with_capacity(buf.len());
        for &x in buf {
            let e = env_lp.process(bp.process(x).abs());
            let s = slow.process(e);
            flat.push(e / s.max(1e-9));
        }
        let s = &flat[(a_s * SR12) as usize..(z_s * SR12) as usize];
        let mean = s.iter().sum::<f32>() / s.len() as f32;
        let d: Vec<f64> = s.iter().map(|&x| (x - mean) as f64).collect();
        let zero: f64 = d.iter().map(|&x| x * x).sum();
        if zero <= 0.0 {
            return (0.0, 0.0);
        }
        let lag_lo = ((lag_lo_s * SR12) as usize).max(1);
        let lag_hi = ((lag_hi_s * SR12) as usize).min(d.len() - 1);
        let (mut best, mut best_lag) = (f64::MIN, lag_lo);
        for lag in lag_lo..=lag_hi {
            let c: f64 = (0..d.len() - lag).map(|i| d[i] * d[i + lag]).sum::<f64>() / zero;
            if c > best {
                best = c;
                best_lag = lag;
            }
        }
        (best as f32, SR12 / best_lag as f32)
    }

    /// S4 (level knob STEELPAN_B_GAIN): within ±2 dB of the default-bank
    /// marimba at the same key.
    #[test]
    fn altbank_b114_steel_level_vs_marimba() {
        let pan = render_alt(114, 60, 100, 0.5, 0x11_4004);
        let mar = render_def(12, 60, 100, 0.5, 0x11_4004);
        let d = db_ratio(rms(seg12(&pan, 0.02, 0.42)), rms(seg12(&mar, 0.02, 0.42)));
        println!("B114 vs marimba level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B114 level {d:+.2} dB off marimba");
    }

    /// B115-1..3: the woodblock speaks at the written pitch inside its
    /// register, rings only a few tens of ms, and CLAMPS (not folds) keys
    /// below its register onto the boundary note.
    #[test]
    fn altbank_b115_woodblock_pitch_decay_and_clamp() {
        let b = render_alt(115, 72, 100, 0.3, 0x11_5001);
        let f = peak_locate(seg12(&b, 0.002, 0.08), SR12, 350.0, 800.0);
        assert!(
            (f / 523.25 - 1.0).abs() <= 0.03,
            "B115 key 72 pitch {f:.1} Hz vs 523.25 Hz"
        );
        let t60 = crate::testutil::t60_of(&b, SR12);
        println!("B115 t60 = {t60:.3} s");
        assert!(
            (0.04..=0.16).contains(&t60),
            "B115 t60 {t60:.3} s outside [0.04, 0.16]"
        );
        // clamp check: key 36 lands on the low boundary (key 60 = 261.63 Hz),
        // NOT an octave fold of C2
        let lo = render_alt(115, 36, 100, 0.3, 0x11_5001);
        let fl = peak_locate(seg12(&lo, 0.002, 0.08), SR12, 180.0, 420.0);
        assert!(
            (fl / 261.63 - 1.0).abs() <= 0.03,
            "B115 key 36 should clamp to 261.63 Hz, got {fl:.1} Hz"
        );
    }

    /// B115-4 (level knob WOODBLOCK_B_GAIN): within ±2 dB of the default-bank
    /// xylophone at the same key over the block's whole life.
    #[test]
    fn altbank_b115_woodblock_level_vs_xylophone() {
        let blk = render_alt(115, 72, 100, 0.10, 0x11_5002);
        let xyl = render_def(13, 72, 100, 0.10, 0x11_5002);
        let d = db_ratio(rms(&blk), rms(&xyl));
        println!("B115 vs xylophone level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B115 level {d:+.2} dB off xylophone");
    }

    /// Dispatch guard: every bank-B program 112-119 renders something real,
    /// DIFFERENT from the default-bank voice of the same program (bank B is
    /// genuinely a second voicing, not an alias), and the eight are pairwise
    /// distinct.
    #[test]
    fn altbank_b112_119_dispatch_distinct() {
        let seed = 0x11_5003;
        let mut renders = Vec::new();
        for p in 112u8..=119 {
            let b = render_alt(p, 60, 100, 0.5, seed);
            assert!(b.iter().any(|&x| x.abs() > 1e-6), "B{p} renders silence");
            let default = render_def(p, 60, 100, 0.5, seed);
            assert_ne!(b, default, "B{p} renders identically to the default bank");
            renders.push((p, b));
        }
        for i in 0..renders.len() {
            for j in (i + 1)..renders.len() {
                assert_ne!(
                    renders[i].1, renders[j].1,
                    "B{} and B{} render identically",
                    renders[i].0, renders[j].0
                );
            }
        }
    }

    /// B116-1,2: the taiko settles ON the written pitch (key 43 → ~98 Hz,
    /// read AFTER the 1.5-st tension overshoot has glided out) and stays a
    /// deep drum — spectral centroid under 300 Hz.
    #[test]
    fn altbank_b116_taiko_settled_pitch_and_darkness() {
        let b = render_alt(116, 43, 100, 1.2, 7);
        let f = peak_locate(seg12(&b, 0.20, 1.0), SR12, 60.0, 140.0);
        println!("B116 settled pitch {f:.1} Hz (want ~98)");
        assert!(
            (92.1..=107.8).contains(&f),
            "B116 settled pitch {f:.1} Hz outside [0.94, 1.10] x 98"
        );
        let c = centroid(seg12(&b, 0.02, 1.15), SR12);
        println!("B116 centroid {c:.0} Hz");
        assert!(c < 300.0, "B116 centroid {c:.0} Hz not a deep drum");
    }

    /// B116-3,4: the bachi slap grows super-linearly with velocity (the HF
    /// fraction at vel 127 well above vel 40's, level-normalised), and the
    /// boom rings 0.9-2.0 s.
    #[test]
    fn altbank_b116_taiko_velocity_slap_and_boom() {
        // Measure the slap INSIDE its own life ([2, 40] ms — skip the first
        // 2 ms, where the tones' onset step radiates a velocity-independent
        // splat) and above 2.5 kHz — the 1.6 kHz Q-0.8 slap band still
        // passes ~0.8 there while the 98 Hz tones are 55 dB down. Filter
        // the WHOLE render, then window (see hp_win).
        let slap_frac = |vel: u8| {
            let b = render_alt(116, 43, vel, 0.5, 7);
            hp_win(&b, 2500.0, 0.002, 0.04) / rms(&b).max(1e-12)
        };
        let hard = slap_frac(127);
        let soft = slap_frac(40);
        println!("B116 slap fraction: vel127 {hard:.4} vs vel40 {soft:.4}");
        assert!(
            hard > 1.4 * soft,
            "B116 slap not velocity-shaped: {hard:.4} vs {soft:.4}"
        );
        let b = render_alt(116, 43, 100, 2.6, 7);
        let t60 = crate::testutil::t60_of(&b, SR12);
        println!("B116 t60 {t60:.2} s");
        assert!(
            (0.9..=2.0).contains(&t60),
            "B116 t60 {t60:.2} s outside [0.9, 2.0]"
        );
    }

    /// B116-5 (level knob TAIKO_B_GAIN): the taiko's level is pinned against
    /// the default-bank timpani at the same key. Originally 0..+3 dB; the
    /// voice-quality §2.5 timpani retune (thump 1.1→0.5·v, sounding T60s ×3)
    /// deliberately made the timpani ring ~4 dB hotter over this window, and
    /// the alt bank is FROZEN (TAIKO_B_GAIN must not chase a reference), so
    /// the pin moves with the reference: measured −4.21 dB, guarded ±1.5.
    #[test]
    fn altbank_b116_taiko_level_vs_timpani() {
        let tai = render_alt(116, 43, 100, 1.0, 7);
        let tim = render_def(47, 43, 100, 1.0, 7);
        let d = db_ratio(rms(seg12(&tai, 0.02, 1.0)), rms(seg12(&tim, 0.02, 1.0)));
        println!("B116 vs timpani level: {d:+.2} dB");
        assert!(
            (-5.7..=-2.7).contains(&d),
            "B116 level {d:+.2} dB outside [-5.7, -2.7] of the retuned timpani"
        );
    }

    /// B117-1,2,3: the melodic tom settles ON the written pitch, approaches
    /// it FROM ABOVE (the kit-v2 overshoot), and tracks the keyboard — an
    /// octave apart stays an octave apart.
    #[test]
    fn altbank_b117_melodic_tom_pitch_drop_and_tracking() {
        let settled = |key: u8, lo: f32, hi: f32| {
            let b = render_alt(117, key, 100, 0.5, 7);
            peak_locate(seg12(&b, 0.10, 0.35), SR12, lo, hi)
        };
        let f57 = settled(57, 150.0, 300.0);
        println!("B117 settled pitch {f57:.1} Hz (want ~220)");
        assert!(
            (206.8..=242.0).contains(&f57),
            "B117 settled pitch {f57:.1} Hz outside [0.94, 1.10] x 220"
        );
        let b = render_alt(117, 57, 100, 0.5, 7);
        let early = peak_locate(seg12(&b, 0.002, 0.030), SR12, 150.0, 350.0);
        println!("B117 early pitch {early:.1} Hz vs settled {f57:.1}");
        assert!(
            early >= 1.05 * f57,
            "B117 does not land from above: early {early:.1} vs settled {f57:.1}"
        );
        let f45 = settled(45, 80.0, 160.0);
        let ratio = f57 / f45;
        println!("B117 octave tracking 57/45: {ratio:.3}");
        assert!(
            (1.88..=2.12).contains(&ratio),
            "B117 octave tracking {ratio:.3} outside [1.88, 2.12]"
        );
    }

    /// B117-4 (level knob MELODIC_TOM_B_GAIN — calibrate BEFORE the synth
    /// drum's B118-4, which anchors to this voice): within ±2 dB of the
    /// default-bank marimba at the same key.
    #[test]
    fn altbank_b117_melodic_tom_level_vs_marimba() {
        let tom = render_alt(117, 57, 100, 0.4, 7);
        let mar = render_def(12, 57, 100, 0.4, 7);
        let d = db_ratio(rms(seg12(&tom, 0.02, 0.35)), rms(seg12(&mar, 0.02, 0.35)));
        println!("B117 vs marimba level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B117 level {d:+.2} dB off marimba");
    }

    /// B118-1,2,3: the synth drum ZAPS — the tone starts ≥1.8x above where it
    /// settles (read inside the glide, deliberately: a direction check), the
    /// settled pitch is the written key, and the settled ring is a near-pure
    /// sine (negligible HF, most energy in the fundamental's band).
    #[test]
    fn altbank_b118_synth_drum_zap_and_purity() {
        let b = render_alt(118, 45, 100, 0.6, 7);
        let early = peak_locate(seg12(&b, 0.002, 0.020), SR12, 130.0, 400.0);
        let settled = peak_locate(seg12(&b, 0.15, 0.45), SR12, 90.0, 135.0);
        println!("B118 zap: early {early:.1} Hz -> settled {settled:.1} Hz");
        assert!(
            early >= 1.8 * settled,
            "B118 zap ratio {:.2} < 1.8",
            early / settled
        );
        assert!(
            (103.4..=121.0).contains(&settled),
            "B118 settled pitch {settled:.1} Hz outside [0.94, 1.10] x 110"
        );
        // HP corner at 1 kHz: the 2nd-order highpass leaks a pure 110 Hz
        // sine at (110/corner)² — 500 Hz would spend 0.048 of the 0.06
        // budget on the fundamental itself. Filter first, then window.
        let s = seg12(&b, 0.15, 0.45);
        let hf = hp_win(&b, 1000.0, 0.15, 0.45) / rms(s).max(1e-12);
        let band = band_rms(s, SR12, settled, 2.0) / rms(s).max(1e-12);
        println!("B118 purity: hf frac {hf:.4}, band frac {band:.3}");
        assert!(hf < 0.06, "B118 settled ring not pure: hf {hf:.4}");
        assert!(band > 0.7, "B118 fundamental band frac {band:.3} <= 0.7");
    }

    /// B118-4 (level knob SYNTH_DRUM_B_GAIN, calibrated AFTER B117 per the
    /// anchor ordering): within ±2 dB of the bank-B melodic tom at the same
    /// key.
    #[test]
    fn altbank_b118_synth_drum_level_vs_melodic_tom() {
        let syn = render_alt(118, 45, 100, 0.6, 7);
        let tom = render_alt(117, 45, 100, 0.6, 7);
        let d = db_ratio(rms(seg12(&syn, 0.02, 0.50)), rms(seg12(&tom, 0.02, 0.50)));
        println!("B118 vs melodic tom level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "B118 level {d:+.2} dB off melodic tom");
    }

    /// B119-1,2: the reverse cymbal SWELLS in a staircase (each half-second
    /// window well above the last, ≥10x across the rise) and then stops
    /// dead: −34 dB within 50 ms of note_off, and even unreleased it
    /// self-caps — nothing renders past 3.5 s.
    #[test]
    fn altbank_b119_reverse_cymbal_swell_and_stop() {
        let b = render_alt(119, 60, 100, 3.0, 7);
        let w = |a, z| rms(seg12(&b, a, z));
        let (w1, w2, w3, w4) = (w(0.2, 0.7), w(0.7, 1.2), w(1.2, 1.7), w(1.7, 2.2));
        println!("B119 staircase: {w1:.5} {w2:.5} {w3:.5} {w4:.5}");
        assert!(w2 >= 1.6 * w1, "B119 swell stalls: w2/w1 {:.2}", w2 / w1);
        assert!(w3 >= 1.6 * w2, "B119 swell stalls: w3/w2 {:.2}", w3 / w2);
        assert!(w4 >= 1.6 * w3, "B119 swell stalls: w4/w3 {:.2}", w4 / w3);
        assert!(w4 >= 10.0 * w1, "B119 total swell {:.1}x < 10x", w4 / w1);
        // note_off hard stop: render 1.0 s, release, then 0.2 s more
        let mut v = make(119, 1, 60, 100, SR12, 7, false);
        let mut pre = vec![0f32; SR12 as usize];
        v.render(&mut pre);
        v.note_off();
        let mut post = vec![0f32; (0.2 * SR12) as usize];
        v.render(&mut post);
        let before = rms(&pre[(0.95 * SR12) as usize..]);
        let after = rms(&post[(0.05 * SR12) as usize..(0.10 * SR12) as usize]);
        let drop = db_ratio(after, before);
        println!("B119 stop: {drop:+.1} dB 50-100 ms after note_off");
        assert!(drop <= -34.0, "B119 stop only {drop:+.1} dB");
        // self-cap: unreleased, the voice dies on its own before 3.5 s
        let mut v = make(119, 1, 60, 100, SR12, 7, false);
        let mut buf = vec![0f32; (4.0 * SR12) as usize];
        let alive = v.render(&mut buf);
        assert!(!alive, "B119 still renders after a 4 s unreleased buffer");
        let late = rms(seg12(&buf, 3.5, 3.95));
        assert!(late <= 1e-6, "B119 audible past 3.5 s: rms {late}");
    }

    /// B119-3: the swell BRIGHTENS as it grows — the reversed decays give the
    /// highest metal partial (4.365x base, t60 0.8 → a 75 dB/s rise from its
    /// 1.7 s onset) a far steeper climb than the fundamental (27 dB/s from
    /// 0.3 s), so the partial-stack TILT (top/fundamental Goertzel ratio)
    /// swings hard toward the top late in the rise. (Noise-band ratios can't
    /// read this: hp9000/hp3500 of the HP-3500 wash is already ~0.86 with a
    /// hard ceiling of 1.0 — no headroom for a 1.2x oracle.)
    #[test]
    fn altbank_b119_reverse_cymbal_brightens() {
        let b = render_alt(119, 60, 100, 3.0, 7);
        let base = crate::drums::REV_CYM_B_BASE_HZ; // key 60 → no size-class transposition
        let tilt = |a: f32, z: f32| {
            let s = seg12(&b, a, z);
            mag_at(s, SR12, base * 4.365) / mag_at(s, SR12, base).max(1e-9)
        };
        let early = tilt(1.0, 1.5);
        let late = tilt(2.2, 2.5);
        println!("B119 partial tilt: early {early:.4} -> late {late:.4}");
        // measured 3.15x at the pinned seed; the early read is a noise floor
        // (the top partial is onset-gated until 1.7 s), so 2.5x keeps margin
        assert!(
            late >= 2.5 * early,
            "B119 does not brighten: tilt {early:.4} -> {late:.4}"
        );
    }

    /// B119-4 (level knob REV_CYM_B_GAIN): the swell's last 0.3 s hands over
    /// at the level a V1 crash opens with (±3 dB) — the classic reverse-into-
    /// downbeat splice.
    #[test]
    fn altbank_b119_reverse_cymbal_crash_handover_level() {
        let rev = render_alt(119, 60, 100, 2.6, 7);
        let crash = {
            let mut v =
                crate::drums::make(49, 100, SR12, 7, crate::drums::Kit::V1, false, 0).unwrap();
            let mut buf = vec![0f32; (0.5 * SR12) as usize];
            v.render(&mut buf);
            buf
        };
        let d = db_ratio(
            rms(seg12(&rev, 2.2, 2.5)),
            rms(&crash[..(0.3 * SR12) as usize]),
        );
        println!("B119 handover vs V1 crash: {d:+.2} dB");
        assert!(d.abs() <= 3.0, "B119 handover {d:+.2} dB off the V1 crash");
    }

    // --- v0.12 CC0-alt GM 14 tam-tam / gong ageng (G1-G4) -------------------

    /// Whole-buffer bandpass at `f` (Q 8), then windowed RMS — filter FIRST
    /// so a window boundary sliced mid-ring doesn't excite the filter as a
    /// step and bury the band being measured.
    fn bp_win(b: &[f32], sr: f32, f: f32, a: f32, z: f32) -> f32 {
        let mut bp = Biquad::bandpass(f, 8.0, sr);
        let filt: Vec<f32> = b.iter().map(|&x| bp.process(x)).collect();
        rms(&filt[(a * sr) as usize..(z * sr) as usize])
    }

    /// G1: the gong's upper modes BLOOM — the summed energy of the idx>=2
    /// mode bands (2.09x/2.98x/3.82x/4.76x of the 98 Hz fundamental) peaks
    /// 0.25-1.0 s after the strike, NOT at it (splash-proof: the bands are
    /// narrow Q-8 reads far from the 1.1 kHz splash center). Positive
    /// control: the default-bank tubular bell peaks in its first window.
    #[test]
    fn altbank_gm14_tamtam_bloom_onset() {
        let sr = 44100.0;
        let argmax_t = |b: &[f32], bands: &[f32]| {
            let (mut best, mut best_t) = (0.0f32, 0.0f32);
            let mut t = 0.0f32;
            while t + 0.1 <= 1.5 {
                let e = bands
                    .iter()
                    .map(|&f| bp_win(b, sr, f, t, t + 0.1).powi(2))
                    .sum::<f32>()
                    .sqrt();
                if e > best {
                    best = e;
                    best_t = t;
                }
                t += 0.05;
            }
            best_t
        };
        let gong = render_make(14, 43, 100, 2.0, 7, false);
        let f0 = 98.0f32;
        let bloom_bands: Vec<f32> = [2.09f32, 2.98, 3.82, 4.76].iter().map(|r| r * f0).collect();
        let t_gong = argmax_t(&gong, &bloom_bands);
        // positive control: the tubular bell strikes at once — its overall
        // >150 Hz energy peaks in the first window
        let tube = {
            let mut v = crate::voices::make(14, 43, 100, sr, 7, false);
            let mut b = vec![0f32; (2.0 * sr) as usize];
            v.render(&mut b);
            b
        };
        let t_tube = {
            let mut hp = Biquad::highpass(150.0, 0.7, sr);
            let filt: Vec<f32> = tube.iter().map(|&x| hp.process(x)).collect();
            let (mut best, mut best_t) = (0.0f32, 0.0f32);
            let mut t = 0.0f32;
            while t + 0.1 <= 1.5 {
                let e = rms(&filt[(t * sr) as usize..((t + 0.1) * sr) as usize]);
                if e > best {
                    best = e;
                    best_t = t;
                }
                t += 0.05;
            }
            best_t
        };
        println!("G1 bloom argmax: gong {t_gong:.2} s, tubular control {t_tube:.2} s");
        assert!(
            (0.25..=1.0).contains(&t_gong),
            "gong upper modes peak at {t_gong:.2} s — no bloom"
        );
        assert!(t_tube < 0.25, "tubular control peaks late: {t_tube:.2} s");
    }

    /// G2: the gong speaks in its 65-124 Hz register wherever it is written —
    /// keys 43 and 67 fold to the same 98 Hz fundamental (pitch class
    /// preserved), and far-out keys 24/60/90 stay inside the register.
    #[test]
    fn altbank_gm14_tamtam_fundamental_folds() {
        let sr = 44100.0;
        let fundamental = |key: u8| {
            let b = render_make(14, key, 100, 2.0, 7, false);
            peak_locate(
                &b[(0.3 * sr) as usize..(1.8 * sr) as usize],
                sr,
                55.0,
                140.0,
            )
        };
        for key in [43u8, 67] {
            let f = fundamental(key);
            println!("G2 key {key}: fundamental {f:.1} Hz");
            assert!(
                (f - 98.0).abs() <= 0.02 * 98.0,
                "key {key} fundamental {f:.1} Hz not ~98"
            );
        }
        for key in [24u8, 60, 90] {
            let f = fundamental(key);
            println!("G2 key {key}: fundamental {f:.1} Hz");
            assert!(
                (61.7..=126.0).contains(&f),
                "key {key} fundamental {f:.1} Hz outside the gong register"
            );
        }
    }

    /// G3: the gong RINGS — the 3 s decay from the [1.0, 1.5] window to the
    /// [4.0, 4.5] window sits between −30 and −12 dB (T60 6-15 s).
    #[test]
    fn altbank_gm14_tamtam_decay_t60() {
        let sr = 44100.0;
        let b = render_make(14, 43, 100, 5.0, 7, false);
        let w = |a: f32, z: f32| rms(&b[(a * sr) as usize..(z * sr) as usize]);
        let ratio = w(4.0, 4.5) / w(1.0, 1.5).max(1e-12);
        println!("G3 gong decay ratio over 3 s: {ratio:.4}");
        assert!(
            (0.0316..=0.251).contains(&ratio),
            "gong decay ratio {ratio:.4} outside [-30, -12] dB / 3 s"
        );
    }

    /// G4: the strike leads with a short bright SPLASH — high-band energy in
    /// the first 120 ms well above the same band half a second later. The
    /// read is a CASCADED (4th-order) highpass at 2.5 kHz: the top bloom
    /// mode (854 Hz) is −37 dB there, while the broad 1.1 kHz Q-0.6 splash
    /// still carries real energy — a single 2nd-order HP at 1.5 kHz leaks
    /// the bloomed modes at −10 dB and drowns the comparison.
    #[test]
    fn altbank_gm14_tamtam_splash_transient() {
        let sr = 44100.0;
        let b = render_make(14, 43, 100, 1.0, 7, false);
        let mut hp1 = Biquad::highpass(2500.0, 0.7, sr);
        let mut hp2 = Biquad::highpass(2500.0, 0.7, sr);
        let filt: Vec<f32> = b.iter().map(|&x| hp2.process(hp1.process(x))).collect();
        let early = rms(&filt[..(0.12 * sr) as usize]);
        let late = rms(&filt[(0.5 * sr) as usize..(0.62 * sr) as usize]);
        println!("G4 splash hp2500x2: early {early:.5} vs late {late:.5}");
        assert!(
            early >= 3.0 * late,
            "no splash transient: early {early:.5} vs late {late:.5}"
        );
    }
}
