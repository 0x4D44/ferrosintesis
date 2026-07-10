//! GM percussion (channel 10). Every hit is a small parametric voice:
//! decaying sine partials (with downward pitch glide for membranes, and
//! dense inharmonic stacks for cymbals) plus up to two filtered noise bands
//! (e.g. snare shell + snare wires). Hits vary: frequencies and decays are
//! jittered per strike, and harder hits are brighter.

use crate::dsp::{key_freq, vel_amp, Biquad, OnePole, Rng, Sine};
use crate::sampler;
use crate::voices::Voice;
use std::f32::consts::TAU;

/// Which channel-10 kit a hit is voiced with. `V1` and `V2` are retained for
/// differential tests. `V3` is the shipped default kit. `Brush` (v0.12)
/// engages ONLY on a ch-10 Program Change of exactly 40 (the GM2 brush kit):
/// seven brush voices (tap/slap/swirl/hats/rim/kick), every other key
/// falling through to the V3 arms.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Kit {
    // V1/V2 are constructed only by the differential tests: the lib-side kit
    // dispatch is exhaustive matches (a `== Kit::V2`-style comparison would
    // silently hand a new variant the wrong arm), so outside #[cfg(test)]
    // nothing constructs them.
    #[cfg_attr(not(test), allow(dead_code))]
    V1,
    #[cfg_attr(not(test), allow(dead_code))]
    V2,
    V3,
    Brush,
}

struct Tone {
    phase: f32,
    freq: f32,
    glide: f32, // per-sample frequency multiplier (1.0 = none)
    min_freq: f32,
    amp: f32,
    decay: f32,
}

struct NoiseBand {
    amp: f32,
    decay: f32,
    filt: Biquad,
    // D4/D5 extensions: a delayed start (snare wires engage ~1.5 ms after
    // the stick), and a swell envelope (crash wash blooms over ~50 ms while
    // the chick is instant). Defaults (onset 0, env 1, floor 1) are inert.
    onset: u32,
    env: f32,
    atk: f32,
    floor: f32,
}

/// DR1 noise-coupled shimmer AM: a slow one-pole-lowpassed copy of the shared
/// per-sample white drives a random-walk amplitude flutter over the whole
/// voice sum (`norm` puts `depth` in true modulation-index / σ units, so a
/// crash's 5–15 Hz surface-mode chatter is a wobble, not an LFO). Optional and
/// `None` on v1 → the multiply is skipped entirely, so v1 stays byte-identical.
struct Shimmer {
    lp: OnePole,
    depth: f32,
    norm: f32,
}

impl Shimmer {
    fn new(rate_hz: f32, depth: f32, sr: f32) -> Self {
        // `a` cannot be read off `OnePole` (private field), so recompute it
        // from the same public formula `OnePole::lowpass` uses; `norm` is the
        // analytic 1/σ of a one-pole-filtered uniform white in [-1,1)
        // (variance a/(2−a)·1/3).
        let a = 1.0 - (-2.0 * std::f32::consts::PI * (rate_hz / sr).min(0.49)).exp();
        let norm = ((2.0 - a) / a * 3.0).sqrt();
        Shimmer {
            lp: OnePole::lowpass(rate_hz, sr),
            depth,
            norm,
        }
    }
}

/// DR4 kit-v2 snare wires: an enveloped, head-coupled cluster of three
/// bandpass "wire-mode" resonances that replaces v1's featureless broad-HP
/// wire band. It runs its own exponential decay AND tracks the 186 Hz head
/// envelope (`head^head_track`), so the bright rattle sputters out with the
/// ringing head (~110 ms) instead of on its own 0.19 s clock; a half-wave
/// 186 Hz "slap" AM makes the early rattle granular. Consumes the shared
/// per-sample `white` (zero extra RNG draws); `None` on v1 and every non-snare
/// key → the render hook is skipped, so v1 stays byte-identical.
struct WireRes {
    bands: [Biquad; 3], // bandpass wire-mode clusters
    gains: [f32; 3],    // velocity-shaped per-band gains
    amp: f32,           // overall level, own exponential decay
    decay: f32,         // dmul(0.19, sr)
    onset: u32,         // D5 delayed onset (1.5 ms), exact zero before
    env: f32,           // onset swell 0..1 (floor 0)
    atk: f32,           // 1/(0.5 ms) ramp increment
    head_amp0: f32,     // tones[0].amp at build (the 186 Hz head env reference)
    head_track: f32,    // WIRE_HEAD_TRACK exponent
    am_depth: f32,      // granular slap AM depth at full head level
}

pub struct Drum {
    tones: Vec<Tone>,
    noise: Vec<NoiseBand>,
    bursts: Vec<(u32, f32)>,  // noise re-triggers (offset samples, amp)
    shimmer: Option<Shimmer>, // DR1 noise-coupled AM; None (inert) on v1
    wire: Option<WireRes>,    // DR4 kit-v2 snare wire resonance; None on v1
    rng: Rng,
    t: u32,
    life: u32,
    gain: f32,
    sr: f32,
}

fn dmul(t60: f32, sr: f32) -> f32 {
    10f32.powf(-3.0 / (t60.max(0.005) * sr))
}

impl Drum {
    #[allow(clippy::too_many_arguments)]
    fn new(
        sr: f32,
        seed: u32,
        tones: &[(f32, f32, f32, f32)], // (freq, amp, T60, glide oct/s down; negative = up)
        noise: &[(f32, f32, Biquad)],   // (amp, T60, filter)
        life_s: f32,
        gain: f32,
    ) -> Self {
        let mut rng = Rng::new(seed);
        // D8 strike-position dither: one shared "how far off centre" draw
        // tilts the partial balance anti-correlated (edge hits starve the
        // fundamental and feed the overtones), plus small independent
        // per-partial and per-band jitter — no two hits balance identically
        let edge = rng.white();
        // per-strike variation: nothing repeats exactly
        let jf = 1.0 + 0.03 * rng.white();
        let jd = 1.0 + 0.10 * rng.white();
        let n_tones = tones.len();
        let tones = tones
            .iter()
            .enumerate()
            .map(|(i, &(f, a, t, glide_oct_per_s))| {
                let modal = if n_tones > 1 {
                    i as f32 / (n_tones - 1) as f32
                } else {
                    0.5
                };
                let tilt = 0.20 * edge * (2.0 * modal - 1.0);
                Tone {
                    phase: rng.white() * TAU,
                    freq: f * jf,
                    // positive rates glide DOWN (mult < 1) toward `min_freq`;
                    // negative rates glide UP (mult > 1) and `min_freq` acts
                    // as a ceiling (open cuica, key 79). Zero = no glide.
                    glide: if glide_oct_per_s != 0.0 {
                        2f32.powf(-glide_oct_per_s / sr)
                    } else {
                        1.0
                    },
                    min_freq: f * jf * 0.3,
                    amp: (a * (1.0 + tilt + 0.12 * rng.white())).max(0.0),
                    decay: dmul(t * jd, sr),
                }
            })
            .collect();
        let noise = noise
            .iter()
            .map(|&(amp, t, filt)| NoiseBand {
                amp: (amp * (1.0 + 0.15 * edge + 0.10 * rng.white())).max(0.0),
                decay: dmul(t * jd, sr),
                filt,
                onset: 0,
                env: 1.0,
                atk: 1.0,
                floor: 1.0,
            })
            .collect();
        Drum {
            tones,
            noise,
            bursts: Vec::new(),
            shimmer: None,
            wire: None,
            rng,
            t: 0,
            life: (life_s * sr) as u32,
            gain,
            sr,
        }
    }

    fn with_bursts(mut self, bursts: &[(f32, f32)]) -> Self {
        self.bursts = bursts
            .iter()
            .map(|&(sec, amp)| ((sec * self.sr) as u32, amp))
            .collect();
        self
    }

    /// DR1: attach a noise-coupled shimmer AM (reusing the shared per-sample
    /// white draw at render time — zero extra RNG draws).
    fn with_shimmer(mut self, rate_hz: f32, depth: f32) -> Self {
        self.shimmer = Some(Shimmer::new(rate_hz, depth, self.sr));
        self
    }

    /// DR4: attach the kit-v2 snare wire resonance (reusing the shared
    /// per-sample white at render time — zero extra RNG draws).
    fn with_wire(mut self, wire: WireRes) -> Self {
        self.wire = Some(wire);
        self
    }

    /// Upgrade noise band `idx` with a delayed onset and/or a swell
    /// (`floor` of the gain is present immediately, the rest ramps in over
    /// `atk_s`). Exact zero before the onset — denormal-safe, click-free.
    fn with_band_ext(mut self, idx: usize, onset_s: f32, atk_s: f32, floor: f32) -> Self {
        let b = &mut self.noise[idx];
        b.onset = (onset_s * self.sr) as u32;
        b.floor = floor;
        if atk_s > 0.0 {
            b.atk = 1.0 / (atk_s * self.sr);
            b.env = 0.0;
        }
        self
    }

    /// DR2: rewrite the glide limit to `ratio x` each tone's (already
    /// jittered) start frequency, so a v2 tom that starts sharp settles exactly
    /// on the table pitch (`ratio = 1/TOM_OVERSHOOT`) instead of diving to the
    /// hardwired 0.3x. With `ratio > 1` it is the CEILING of an upward glide
    /// (open cuica, key 79). No RNG draw — pure post-construction rewrite.
    fn with_glide_floor(mut self, ratio: f32) -> Self {
        for tone in &mut self.tones {
            tone.min_freq = tone.freq * ratio;
        }
        self
    }
}

impl Voice for Drum {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t >= self.life {
                return false;
            }
            let mut s = 0.0;
            for tone in &mut self.tones {
                s += tone.amp * tone.phase.sin();
                tone.phase += TAU * tone.freq / self.sr;
                if tone.phase > TAU {
                    tone.phase -= TAU;
                }
                if (tone.glide < 1.0 && tone.freq > tone.min_freq)
                    || (tone.glide > 1.0 && tone.freq < tone.min_freq)
                {
                    tone.freq *= tone.glide;
                }
                tone.amp *= tone.decay;
            }
            for &(offset, amp) in &self.bursts {
                if self.t == offset {
                    for band in &mut self.noise {
                        band.amp = band.amp.max(amp);
                    }
                }
            }
            let white = self.rng.white();
            for band in &mut self.noise {
                if self.t < band.onset {
                    continue; // exact zero before the wires engage (D5)
                }
                if band.env < 1.0 {
                    band.env = (band.env + band.atk).min(1.0);
                }
                let g = band.amp * (band.floor + (1.0 - band.floor) * band.env);
                if g > 1e-5 {
                    s += band.filt.process(white) * g;
                    band.amp *= band.decay;
                }
            }
            // DR4 kit-v2 snare wire resonance: reuse the SAME shared white (no
            // new RNG draw). The 186 Hz head envelope refs are read from the
            // just-decayed `tones[0]` before the &mut borrow of `wire`;
            // `.first()` is panic-safe for empty-tone voices (which never carry
            // a wire). `wire` is None on v1 → the block is skipped entirely, so
            // v1 stays byte-identical.
            let head_amp_now = self.tones.first().map_or(0.0, |t| t.amp);
            let head_phase_sin = self.tones.first().map_or(0.0, |t| t.phase.sin());
            if let Some(w) = self.wire.as_mut() {
                if self.t >= w.onset {
                    // D5 delayed onset: exact zero before, then a short swell.
                    if w.env < 1.0 {
                        w.env = (w.env + w.atk).min(1.0);
                    }
                    let head = (head_amp_now / w.head_amp0).clamp(0.0, 1.0);
                    let track = head.powf(w.head_track);
                    // half-wave 186 Hz granular slap, deepening with head level
                    let slap = 1.0 + w.am_depth * head * head_phase_sin.max(0.0);
                    let mut wsum = 0.0;
                    for (band, &g) in w.bands.iter_mut().zip(w.gains.iter()) {
                        wsum += band.process(white) * g;
                    }
                    s += wsum * w.amp * w.env * track * slap;
                    w.amp *= w.decay;
                }
            }
            // DR1 shimmer AM: reuse the SAME shared white (no new RNG draw). On
            // v1 shimmer is None → am == 1.0 → `x * 1.0 == x`, byte-identical.
            let am = if let Some(sh) = &mut self.shimmer {
                (1.0 + sh.depth * sh.norm * sh.lp.process(white)).clamp(0.0, 2.0)
            } else {
                1.0
            };
            *o += s * self.gain * am;
            self.t += 1;
        }
        true
    }

    fn note_off(&mut self) {} // percussion ignores note-off

    fn released(&self) -> bool {
        true
    }

    /// D6: the pedal grabs the cymbal — every decay collapses to a ~10 ms
    /// t60 and the voice's life is capped ~30 ms out (never below `t`).
    fn choke(&mut self) {
        let fast = dmul(0.010, self.sr);
        for tone in &mut self.tones {
            tone.decay = tone.decay.min(fast);
        }
        for band in &mut self.noise {
            band.decay = band.decay.min(fast);
        }
        self.life = self.life.min(self.t + (0.030 * self.sr) as u32);
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "drum"
    }
}

struct MetalMode {
    osc: Sine,
    amp: f32,
    decay: f32,
}

struct MetalPlate {
    modes: Vec<MetalMode>,
    bands: Vec<NoiseBand>,
    rng: Rng,
    shimmer: Option<Shimmer>,
    t: u32,
    life: u32,
    gain: f32,
    sr: f32,
}

struct MetalSpec {
    lo: f32,
    hi: f32,
    modes: usize,
    tone_amp: f32,
    t60_low: f32,
    t60_high: f32,
    wash_amp: f32,
    wash_t60: f32,
    wash_hp: f32,
    mid_amp: f32,
    mid_hz: f32,
    click_amp: f32,
    click_t60: f32,
    click_hp: f32,
    life: f32,
    gain: f32,
    swell: bool,
    shimmer: Option<(f32, f32)>,
}

impl MetalPlate {
    fn new(spec: &MetalSpec, sr: f32, seed: u32, vel: u8) -> Self {
        let mut rng = Rng::new(seed ^ 0xC1A5_5EED);
        let velnorm = vel as f32 / 127.0;
        let log_lo = spec.lo.ln();
        let log_span = (spec.hi / spec.lo).ln();
        let mut modes = Vec::with_capacity(spec.modes);
        for i in 0..spec.modes {
            let frac = (i as f32 + 0.37 + 0.26 * rng.white()).clamp(0.0, spec.modes as f32)
                / spec.modes as f32;
            let freq = (log_lo + log_span * frac).exp() * (1.0 + 0.018 * rng.white());
            let decay_frac = 1.0 - frac;
            let t60 = spec.t60_high + (spec.t60_low - spec.t60_high) * decay_frac.powf(0.7);
            let amp = spec.tone_amp
                * (1.0 - 0.45 * frac)
                * (0.65 + 0.55 * velnorm)
                * (0.75 + 0.25 * rng.white().abs());
            modes.push(MetalMode {
                osc: Sine::new(freq, sr, rng.white() * TAU),
                amp,
                decay: dmul(t60, sr),
            });
        }
        let hp = spec.wash_hp * (0.85 + 0.35 * velnorm);
        let mut bands = vec![
            NoiseBand {
                amp: spec.wash_amp * (0.75 + 0.35 * velnorm),
                decay: dmul(spec.wash_t60, sr),
                filt: Biquad::highpass(hp, 0.7, sr),
                onset: 0,
                env: if spec.swell { 0.0 } else { 1.0 },
                atk: if spec.swell { 1.0 / (0.050 * sr) } else { 1.0 },
                floor: if spec.swell { 0.45 } else { 1.0 },
            },
            NoiseBand {
                amp: spec.mid_amp,
                decay: dmul(spec.wash_t60 * 0.8, sr),
                filt: Biquad::bandpass(spec.mid_hz, 0.7, sr),
                onset: 0,
                env: if spec.swell { 0.0 } else { 1.0 },
                atk: if spec.swell { 1.0 / (0.040 * sr) } else { 1.0 },
                floor: if spec.swell { 0.35 } else { 1.0 },
            },
        ];
        if spec.click_amp > 0.0 {
            bands.push(NoiseBand {
                amp: spec.click_amp * velnorm,
                decay: dmul(spec.click_t60, sr),
                filt: Biquad::highpass(spec.click_hp, 0.7, sr),
                onset: 0,
                env: 1.0,
                atk: 1.0,
                floor: 1.0,
            });
        }
        Self {
            modes,
            bands,
            rng,
            shimmer: spec
                .shimmer
                .map(|(rate, depth)| Shimmer::new(rate, depth, sr)),
            t: 0,
            life: (spec.life * sr) as u32,
            gain: spec.gain * vel_amp(vel),
            sr,
        }
    }
}

impl Voice for MetalPlate {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t >= self.life {
                return false;
            }
            let mut s = 0.0;
            for mode in &mut self.modes {
                s += mode.osc.next() * mode.amp;
                mode.amp *= mode.decay;
            }
            let white = self.rng.white();
            for band in &mut self.bands {
                if band.env < 1.0 {
                    band.env = (band.env + band.atk).min(1.0);
                }
                let g = band.amp * (band.floor + (1.0 - band.floor) * band.env);
                if g > 1e-5 {
                    s += band.filt.process(white) * g;
                    band.amp *= band.decay;
                }
            }
            let am = if let Some(sh) = &mut self.shimmer {
                (1.0 + sh.depth * sh.norm * sh.lp.process(white)).clamp(0.0, 2.0)
            } else {
                1.0
            };
            *o += s * self.gain * am;
            self.t += 1;
        }
        true
    }

    fn note_off(&mut self) {}

    fn released(&self) -> bool {
        true
    }

    fn choke(&mut self) {
        let fast = dmul(0.010, self.sr);
        for mode in &mut self.modes {
            mode.decay = mode.decay.min(fast);
        }
        for band in &mut self.bands {
            band.decay = band.decay.min(fast);
        }
        self.life = self.life.min(self.t + (0.030 * self.sr) as u32);
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "drum"
    }
}

/// D1 velocity→timbre for membrane voices (HLD family A, §3.3): a harder hit
/// starts slightly sharper, glides down faster, rings longer, and carries
/// proportionally more click/noise energy (the 0.5 floor preserves ghost
/// notes). Applied ONLY to membrane keys — cymbals keep their own `velnorm`
/// handling (the V4 apply-once rule).
#[allow(clippy::type_complexity)]
fn membrane_velocity(
    tones: &[(f32, f32, f32, f32)],
    noise: &[(f32, f32, Biquad)],
    vn: f32,
) -> (Vec<(f32, f32, f32, f32)>, Vec<(f32, f32, Biquad)>) {
    let tones = tones
        .iter()
        .map(|&(f, a, t, glide)| {
            (
                f * (1.0 + 0.03 * vn),
                a,
                t * (0.85 + 0.30 * vn),
                glide * (0.6 + 0.8 * vn),
            )
        })
        .collect();
    let noise = noise
        .iter()
        .map(|&(a, t, filt)| (a * (0.5 + 0.5 * vn * vn), t, filt))
        .collect();
    (tones, noise)
}

/// D2 tom tone table: the fundamental plus the first two membrane modes at
/// the circular-membrane ratios 1.59×/2.14×, all sharing the strike's
/// down-glide so the inharmonic ratios hold while the pitch settles.
/// A shared fn so the oracle-20 structural test drives the exact shipped
/// table with the glide disabled (the glide smears any spectral read).
fn tom_tones(f0: f32, t60: f32, glide: f32) -> [(f32, f32, f32, f32); 3] {
    [
        (f0, 1.0, t60, glide),
        (f0 * 1.59, 0.40, t60 * 0.7, glide),
        (f0 * 2.14, 0.18, t60 * 0.5, glide),
    ]
}

/// DR2 kit-v2 tom: instead of starting at table pitch and diving ~21 st to the
/// 0.3x glide floor (the "pew" tell, map_drums §4 T2), a v2 tom starts 2.5 st
/// sharp and glides DOWN to the table pitch — a real tom's 1-3 st tension
/// overshoot settling in 30-80 ms.
const TOM_OVERSHOOT: f32 = 1.155; // 2^(2.5/12)
const TOM_GLIDE_V2: f32 = 4.0; // oct/s; x(0.6+0.8*vn) => 2.4-5.6 oct/s => 37-87 ms drop

/// D2 snare head modes (DRM-4): four partials with a small shared down-glide
/// — the 186 Hz fundamental plus the 280/330/430 Hz cluster a real head
/// carries. Shared with the oracle-21 structural test.
const SNARE_TONES: [(f32, f32, f32, f32); 4] = [
    (186.0, 0.8, 0.10, 4.0),
    (280.0, 0.35, 0.08, 2.0),
    (330.0, 0.30, 0.07, 2.0),
    (430.0, 0.18, 0.05, 2.0),
];

/// DR4 kit-v2 snare wire-mode clusters (key 38): three bandpass centers
/// approximating the resonant clusters of the ~20 wire partials, replacing
/// v1's featureless HP-2800 slope. Ring time Q/(πf) ≤ 0.56 ms — coloration,
/// deliberately no beats (CYM-1 rule: the constraint binds only relied-on
/// beats). Key 40 (electric snare) scales these ×1.15 for brighter wires.
const WIRE_CENTERS: [f32; 3] = [3400.0, 5100.0, 7300.0];
const WIRE_QS: [f32; 3] = [6.0, 7.0, 8.0];
/// BP-set make-up gain vs the old HP-2800 band's equivalent-noise-bandwidth:
/// √(≈19250/≈2210) ≈ 2.95; started at 2.9, calibrated by DR-O10 level parity.
const WIRE_MAKEUP: f32 = 2.9;
/// Wire re-excitation tracks head^0.4: combined with the wire's own 0.19 s
/// decay the bright rattle reaches −60 dB by ~110 ms, sputtering out with the
/// head while the retained dark-tail band carries the residual to ~350 ms.
const WIRE_HEAD_TRACK: f32 = 0.4;

/// Inharmonic cymbal partial stack — the classic bell-plate ratios.
const METAL_RATIOS: [f32; 6] = [1.0, 1.483, 1.932, 2.546, 3.363, 4.365];

/// DR1 crash twin-partial detunings (Hz): each `METAL_RATIOS` partial gets a
/// twin at `base·r + CRASH_TWIN_DF_HZ[i]`, so the 6 pairs beat at 5.6–17.5 Hz
/// (shimmer range, below the ~20 Hz roughness border).
const CRASH_TWIN_DF_HZ: [f32; 6] = [5.6, 7.9, 9.3, 11.7, 14.2, 17.5];
/// Primary renorm so a twin pair matches a v1 single-partial power:
/// 0.82² + (0.82·0.7)² = 1.002 — level-neutral by construction.
const CRASH_TONE_NORM: f32 = 0.82;
/// Wash-amp trim keeping the crash's [0,1 s] energy near-neutral vs v1. The
/// wash-only compensation √(I(1.9)/I(2.6)) ≈ 0.856 leaves +1.9 dB once the
/// longer *pair* t60s (2.8 s), the new 1180/1196 low-mid pair, and the shimmer
/// AM are added (this knob scales every crash noise band). Trimmed to 0.74 so
/// the measured v2-vs-v1 [0,1 s] RMS lands ≈ +0.7 dB — inside the design's
/// +0.6..0.8 dB budget with ~1.3 dB margin (DR-O10 calibrated).
const CRASH_WASH_AMP_V2: f32 = 0.74;

/// D7 cymbal build spec — replaces the old ~10-positional-arg `cymbal()`.
struct CymSpec {
    base: f32,
    tone_amp: f32,
    t60_first: f32,
    t60_last: f32,
    noise: (f32, f32, f32), // (amp, T60, highpass corner)
    life: f32,
    gain: f32,
    /// Stick chick/ping: (absolute amp — velocity-shape it at the call
    /// site, t60, highpass corner). Never swelled (V4/FIDE-6).
    click: Option<(f32, f32, f32)>,
    /// CYM-2 crash bloom: the WASH keeps `floor`≈0.5 of its level at t=0
    /// and swells to full over ~50 ms; impact partials stay instant.
    swell: bool,
    /// CYM-1 coloured wash: closely-spaced high-Q bandpass pairs
    /// (6000/6055, 8300/8380 Hz, Q ≈ 130 — Δf > f/Q or the beat smears,
    /// V4/DSP-3) on the shared white source, so overlapping ringdowns
    /// beat at ~55-80 Hz.
    pairs: bool,
    /// DR1 crash kit-v2 upgrade (detuned twin partials, decoupled/longer pair
    /// t60, a low-mid CYM-1 pair). `None` = legacy v1 build; the v1 tone/band
    /// vecs and their RNG-draw order are untouched.
    v2: Option<CrashV2>,
    /// DR3 kit-v2 open-hat: a second wash band (amp, t60, HP corner) with a
    /// faster decay than `noise`, so the spectral centroid falls through the
    /// tail (a real hat loses HF fastest). `None` for every v1 spec.
    noise2: Option<(f32, f32, f32)>,
    /// Kit-v2 noise-coupled shimmer AM (rate_hz, depth) applied to the whole
    /// voice sum. `None` = no shimmer (every v1 spec). Crash uses (9, 0.35);
    /// open-hat sizzle uses (45, 0.45).
    shimmer: Option<(f32, f32)>,
}

/// DR1 kit-v2 crash parameters (see the drums HLD appendix §DR1).
struct CrashV2 {
    twin_df: [f32; 6],
    pairs_t60: f32,
    low_pair: bool,
}

fn cymbal(spec: &CymSpec, sr: f32, seed: u32, vel: u8) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let mut tones = Vec::with_capacity(12);
    for (i, &r) in METAL_RATIOS.iter().enumerate() {
        let frac = i as f32 / (METAL_RATIOS.len() - 1) as f32;
        let amp = spec.tone_amp * (1.0 - 0.6 * frac) * (0.55 + 0.55 * velnorm.powf(frac + 0.5));
        let t60 = spec.t60_first + (spec.t60_last - spec.t60_first) * frac;
        match &spec.v2 {
            // DR1(b): interleaved primary + detuned twin — adjacent indices so
            // each pair lands at a near-identical `modal` (matched edge tilt),
            // keeping the pair power at the CRASH_TONE_NORM level neutrality.
            Some(v2) => {
                tones.push((spec.base * r, amp * CRASH_TONE_NORM, t60, 0.0));
                tones.push((
                    spec.base * r + v2.twin_df[i],
                    amp * CRASH_TONE_NORM * 0.7,
                    t60,
                    0.0,
                ));
            }
            None => tones.push((spec.base * r, amp, t60, 0.0)),
        }
    }
    // harder hits open the wash up higher
    let hp = spec.noise.2 * (0.85 + 0.35 * velnorm);
    let mut bands = vec![(spec.noise.0, spec.noise.1, Biquad::highpass(hp, 0.7, sr))];
    let mut swelled = vec![0usize];
    // DR3(a): open-hat's faster-decaying sizzle band. Shares the same white
    // source, differently coloured; correlated like every multi-band hit.
    if let Some((amp2, t60_2, hp2)) = spec.noise2 {
        swelled.push(bands.len());
        bands.push((
            amp2,
            t60_2,
            Biquad::highpass(hp2 * (0.85 + 0.35 * velnorm), 0.7, sr),
        ));
    }
    if spec.pairs {
        // DR1(a): the beat pairs get their own (longer) t60 in v2, decoupled
        // from the wash; v1 shares the wash t60 exactly as before.
        let pair_t60 = match &spec.v2 {
            Some(v2) => v2.pairs_t60,
            None => spec.noise.1,
        };
        for &(fa, fb) in &[(6000.0f32, 6055.0f32), (8300.0, 8380.0)] {
            for f in [fa, fb] {
                swelled.push(bands.len());
                // the pairs ARE the wash coloration (CYM-1), levelled with
                // the broadband wash. Q must be high enough that each
                // band's ring time (Q/πf ≈ 26 ms at Q 500) spans a beat
                // period, or the noise decorrelates before one cycle and
                // no beat survives — the physical limit the V4 review's
                // Δf > f/Q rule only half-captured.
                bands.push((spec.noise.0 * 6.0, pair_t60, Biquad::bandpass(f, 800.0, sr)));
            }
        }
        // DR1(c): a low-mid CYM-1 pair (1180/1196 Hz, Δf 16 Hz) puts beating
        // noise into 700–1500 Hz where the old lone 950 Hz sine used to be
        // the last survivor.
        if let Some(v2) = &spec.v2 {
            if v2.low_pair {
                for f in [1180.0f32, 1196.0] {
                    swelled.push(bands.len());
                    bands.push((
                        spec.noise.0 * 4.0,
                        v2.pairs_t60,
                        Biquad::bandpass(f, 800.0, sr),
                    ));
                }
            }
        }
    }
    if let Some((amp, t60, hp)) = spec.click {
        bands.push((amp, t60, Biquad::highpass(hp, 0.7, sr)));
    }
    let mut drum = Drum::new(sr, seed, &tones, &bands, spec.life, spec.gain * v);
    if spec.swell {
        for &idx in &swelled {
            drum = drum.with_band_ext(idx, 0.0, 0.05, 0.5);
        }
    }
    // DR1(d)/DR3(c): couple the noise shimmer AM onto everything (kit-v2 only).
    if let Some((rate, depth)) = spec.shimmer {
        drum = drum.with_shimmer(rate, depth);
    }
    Some(Box::new(drum))
}

/// DR1 crash spec for one kit — collapses the near-identical 49/57 v1/v2 pairs.
/// Pure `CymSpec` data feeding the deterministic `cymbal()`; the v1 branch
/// reproduces the exact pre-v0.9 fields, so v1 stays byte-identical (pinned by
/// the crash oracles + `v1_drum_render_is_frozen`). `t60` args are `(first, last)`.
#[allow(clippy::too_many_arguments)]
fn crash_spec(
    kit: Kit,
    base: f32,
    hp: f32,
    life: f32,
    gain: f32,
    velnorm: f32,
    t60_v1: (f32, f32),
    t60_v2: (f32, f32),
) -> CymSpec {
    // Exhaustive on purpose (the KP-O2 trap): only V1 gets the legacy build.
    // V3 and Brush crashes route to `metal_plate` in `make` before the crash
    // arms ever call this; if one ever reached here the v2 build is correct.
    let v2_kit = match kit {
        Kit::V1 => false,
        Kit::V2 | Kit::V3 | Kit::Brush => true,
    };
    let (t60_first, t60_last) = if v2_kit { t60_v2 } else { t60_v1 };
    // v2 inverts the decay order (shorter tonal t60 + longer, quieter wash).
    let (wash_amp, wash_t60) = if v2_kit {
        (CRASH_WASH_AMP_V2, 2.6)
    } else {
        (1.0, 1.9)
    };
    let (v2, shimmer) = if v2_kit {
        (
            Some(CrashV2 {
                twin_df: CRASH_TWIN_DF_HZ,
                pairs_t60: 2.8,
                low_pair: true,
            }),
            Some((9.0, 0.35)),
        )
    } else {
        (None, None)
    };
    CymSpec {
        base,
        tone_amp: 0.13,
        t60_first,
        t60_last,
        noise: (wash_amp, wash_t60, hp),
        life,
        gain,
        click: Some((0.7 * velnorm, 0.004, 8000.0)),
        swell: true,
        pairs: true,
        v2,
        noise2: None,
        shimmer,
    }
}

fn metal_spec_for(key: u8) -> MetalSpec {
    match key {
        49 => MetalSpec {
            lo: 650.0,
            hi: 14_000.0,
            modes: 44,
            tone_amp: 0.028,
            t60_low: 1.35,
            t60_high: 0.22,
            wash_amp: 1.25,
            wash_t60: 3.0,
            wash_hp: 1900.0,
            mid_amp: 0.26,
            mid_hz: 2600.0,
            click_amp: 0.95,
            click_t60: 0.004,
            click_hp: 8500.0,
            life: 4.2,
            gain: 0.34,
            swell: true,
            shimmer: Some((11.0, 0.28)),
        },
        57 => MetalSpec {
            lo: 560.0,
            hi: 13_000.0,
            modes: 44,
            tone_amp: 0.027,
            t60_low: 1.25,
            t60_high: 0.20,
            wash_amp: 1.22,
            wash_t60: 3.2,
            wash_hp: 1800.0,
            mid_amp: 0.24,
            mid_hz: 2300.0,
            click_amp: 0.90,
            click_t60: 0.004,
            click_hp: 8200.0,
            life: 4.6,
            gain: 0.35,
            swell: true,
            shimmer: Some((10.0, 0.28)),
        },
        51 | 59 => MetalSpec {
            lo: 950.0,
            hi: 12_000.0,
            modes: 36,
            tone_amp: 0.036,
            t60_low: 1.8,
            t60_high: 0.28,
            wash_amp: 0.42,
            wash_t60: 2.2,
            wash_hp: 5200.0,
            mid_amp: 0.10,
            mid_hz: 3400.0,
            click_amp: 1.05,
            click_t60: 0.045,
            click_hp: 7600.0,
            life: 2.8,
            gain: 0.39,
            swell: false,
            shimmer: Some((18.0, 0.16)),
        },
        52 => MetalSpec {
            lo: 760.0,
            hi: 14_500.0,
            modes: 38,
            tone_amp: 0.024,
            t60_low: 0.75,
            t60_high: 0.16,
            wash_amp: 1.75,
            wash_t60: 0.62,
            wash_hp: 5200.0,
            mid_amp: 0.36,
            mid_hz: 1850.0,
            click_amp: 0.45,
            click_t60: 0.006,
            click_hp: 9000.0,
            life: 1.2,
            gain: 0.44,
            swell: false,
            shimmer: Some((24.0, 0.22)),
        },
        55 => MetalSpec {
            lo: 1100.0,
            hi: 14_000.0,
            modes: 32,
            tone_amp: 0.030,
            t60_low: 0.58,
            t60_high: 0.14,
            wash_amp: 1.05,
            wash_t60: 0.34,
            wash_hp: 4600.0,
            mid_amp: 0.16,
            mid_hz: 3200.0,
            click_amp: 0.55,
            click_t60: 0.004,
            click_hp: 8500.0,
            life: 0.75,
            gain: 0.42,
            swell: false,
            shimmer: Some((22.0, 0.16)),
        },
        _ => unreachable!("no V3 metal profile for key {key}"),
    }
}

fn metal_plate(key: u8, sr: f32, seed: u32, vel: u8) -> Box<dyn Voice> {
    Box::new(MetalPlate::new(&metal_spec_for(key), sr, seed, vel))
}

fn sample_overlay(key: u8, vel: u8, sr: f32, seed: u32, voice: Box<dyn Voice>) -> Box<dyn Voice> {
    match key {
        35 | 36 => {
            sampler::SampleOverlay::wrap(voice, sampler::drum_kick_bank(), vel, seed, sr, 0.080)
        }
        38 | 40 => {
            sampler::SampleOverlay::wrap(voice, sampler::drum_snare_bank(), vel, seed, sr, 0.075)
        }
        49 | 57 => {
            sampler::SampleOverlay::wrap(voice, sampler::drum_crash_bank(), vel, seed, sr, 0.055)
        }
        _ => voice,
    }
}

// ---------------------------------------------------------------------------
// v0.12 Brush kit (ch-10 Program 40, GM2 brush kit). Key map:
//   38 brush tap / 39 brush slap / 40 brush swirl / 42|44 closed hat /
//   46 open hat / 37 rim knock / 35|36 soft-beater kick.
// Everything else falls through to the V3 arms in `make`. The swirl lives on
// key 40 — deliberately OUTSIDE the 42|44→46 choke group, so a shuffle
// pattern's swirl is never cut by a hat chick.
// ---------------------------------------------------------------------------

/// BR-O3 structural seam: the brush tap keeps the SNARE_TONES head
/// frequencies but shortens every T60 — a brush lands soft and the head
/// barely rings. No WireRes: nylon strands cannot crack the wires.
const BRUSH_TAP_TONES: [(f32, f32, f32, f32); 4] = [
    (186.0, 0.8, 0.055, 4.0),
    (280.0, 0.35, 0.045, 2.0),
    (330.0, 0.30, 0.040, 2.0),
    (430.0, 0.18, 0.030, 2.0),
];
// Level knobs, calibrated by the brush level oracles.
const BRUSH_TAP_GAIN: f32 = 1.15;
const BRUSH_SLAP_GAIN: f32 = 1.26;
const BRUSH_SWIRL_GAIN: f32 = 0.48;
const BRUSH_CLOSED_HAT_GAIN: f32 = 0.36;
const BRUSH_OPEN_HAT_GAIN: f32 = 0.44;
const BRUSH_RIM_GAIN: f32 = 0.34;
const BRUSH_KICK_GAIN: f32 = 0.85;
/// Swirl slow stir AM (a wrist turns ~5 times a second, not a 45 Hz sizzle).
const BRUSH_SWIRL_AM_RATE_HZ: f32 = 5.0;
const BRUSH_SWIRL_AM_DEPTH: f32 = 0.65;

/// Brush-tap noise bands: soft shell knock + a gentle mid-high "shhh" —
/// bandpassed, never the V2/V3 wire clusters (BR-O1).
fn brush_tap_noise(sr: f32) -> [(f32, f32, Biquad); 2] {
    [
        (0.50, 0.055, Biquad::bandpass(1300.0, 0.7, sr)),
        (0.55, 0.075, Biquad::bandpass(2900.0, 0.8, sr)),
    ]
}

/// 1a: brush tap (key 38) — the shortened head under soft brush noise.
fn brush_tap(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let (tones, noise) = membrane_velocity(&BRUSH_TAP_TONES, &brush_tap_noise(sr), velnorm);
    Some(Box::new(Drum::new(
        sr,
        seed,
        &tones,
        &noise,
        0.35,
        BRUSH_TAP_GAIN * v,
    )) as Box<dyn Voice>)
}

/// 1b: brush slap (key 39) — an accented tap whose strands land twice: the
/// burst re-excites the noise bands ~12 ms after the first contact.
fn brush_slap(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let (tones, noise) = membrane_velocity(&BRUSH_TAP_TONES, &brush_tap_noise(sr), velnorm);
    let drum = Drum::new(sr, seed, &tones, &noise, 0.40, BRUSH_SLAP_GAIN * v)
        .with_bursts(&[(0.012, 0.50)]);
    Some(Box::new(drum) as Box<dyn Voice>)
}

/// 1c core (shared with the SW-O3 no-shimmer differential clone): the swirl
/// is toneless — three staggered-swell noise bands sweeping across the head,
/// the third being the stir's "return".
fn brush_swirl_drum(vel: u8, sr: f32, seed: u32) -> Drum {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let amp = 0.7 + 0.3 * velnorm;
    Drum::new(
        sr,
        seed,
        &[],
        &[
            (amp, 0.32, Biquad::bandpass(2100.0, 0.8, sr)),
            (0.85 * amp, 0.30, Biquad::bandpass(3100.0, 0.8, sr)),
            // the RETURN stroke: hot enough to read over bands 1-2's Q-0.8
            // spread at 4 kHz (SW-O2's return-sweep oracle)
            (1.45 * amp, 0.32, Biquad::bandpass(4300.0, 0.8, sr)),
        ],
        0.85,
        BRUSH_SWIRL_GAIN * v,
    )
    .with_band_ext(0, 0.0, 0.18, 0.0)
    .with_band_ext(1, 0.22, 0.16, 0.0)
    .with_band_ext(2, 0.45, 0.14, 0.0)
}

/// 1c: brush swirl (key 40) — the staggered-swell core under a slow stir AM.
fn brush_swirl(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    Some(Box::new(
        brush_swirl_drum(vel, sr, seed).with_shimmer(BRUSH_SWIRL_AM_RATE_HZ, BRUSH_SWIRL_AM_DEPTH),
    ) as Box<dyn Voice>)
}

/// 1d: brush closed/pedal hat (keys 42|44) — the v1 hat darkened (wash corner
/// 6500→4300) and softened, with a duller stick tick.
fn brush_closed_hat(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let velnorm = vel as f32 / 127.0;
    cymbal(
        &CymSpec {
            base: 3300.0,
            tone_amp: 0.10,
            t60_first: 0.05,
            t60_last: 0.03,
            noise: (0.8, 0.035, 3600.0),
            life: 0.14,
            gain: BRUSH_CLOSED_HAT_GAIN,
            click: Some((0.7 * velnorm, 0.005, 3800.0)),
            swell: false,
            pairs: false,
            v2: None,
            // nylon strands land broad and dull: a mid wash under the top —
            // this band is most of the "darker than sticks" (BH-O1)
            noise2: Some((0.55, 0.030, 1700.0)),
            shimmer: None,
        },
        sr,
        seed,
        vel,
    )
}

/// 1e spec (shared with BH-O4's no-shimmer differential clone): the DR3 v2
/// hat anatomy (body + faster sizzle band + sizzle wobble) darkened and
/// softened for nylon strands.
fn brush_open_hat_spec() -> CymSpec {
    CymSpec {
        base: 3300.0,
        tone_amp: 0.10,
        t60_first: 0.45,
        t60_last: 0.10,
        noise: (0.55, 0.30, 3000.0),
        life: 0.95,
        gain: BRUSH_OPEN_HAT_GAIN,
        click: None,
        swell: false,
        pairs: false,
        v2: None,
        noise2: Some((0.22, 0.16, 6200.0)),
        shimmer: Some((45.0, 0.45)),
    }
}

/// 1e: brush open hat (key 46).
fn brush_open_hat(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    cymbal(&brush_open_hat_spec(), sr, seed, vel)
}

/// 1f: brush rim knock (key 37) — woodier than the stick's side-stick: lower
/// paired knock modes and a low-mid body band instead of the 2200 Hz ping.
fn brush_rim(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    Some(Box::new(Drum::new(
        sr,
        seed,
        &[(330.0, 0.6, 0.06, 0.0), (620.0, 0.35, 0.045, 0.0)],
        &[(0.55, 0.03, Biquad::bandpass(1250.0, 1.2, sr))],
        0.2,
        BRUSH_RIM_GAIN * v,
    )) as Box<dyn Voice>)
}

/// 1g: brush-kit kick (keys 35|36) — the v1 kick's tone stack verbatim (the
/// sub drop is the chest weight, kept intact) under a much softer, darker
/// beater: a felt beater played light, not a click-point rock kick.
fn brush_kick(vel: u8, sr: f32, seed: u32) -> Option<Box<dyn Voice>> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let (tones, noise) = membrane_velocity(
        &[
            (165.0, 0.8, 0.16, 28.0),
            (86.0, 1.1 + 0.4 * velnorm, 0.42, 3.0),
            (130.0, 0.4 * velnorm, 0.01, 0.0),
        ],
        &[
            (0.05, 0.005, Biquad::highpass(1500.0, 0.7, sr)),
            (0.03, 0.005, Biquad::bandpass(2200.0, 0.9, sr)),
        ],
        velnorm,
    );
    Some(Box::new(Drum::new(
        sr,
        seed,
        &tones,
        &noise,
        0.8,
        BRUSH_KICK_GAIN * v,
    )) as Box<dyn Voice>)
}

/// Build a drum voice for a GM key, or None for unmapped keys.
pub fn make(
    key: u8,
    vel: u8,
    sr: f32,
    seed: u32,
    kit: Kit,
    samples: bool,
) -> Option<Box<dyn Voice>> {
    // `kit` selects the legacy test kits or the shipped V3 default. Only V3
    // gets sample overlays, and only when the caller's sample flag is enabled.
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let d = |tones: &[(f32, f32, f32, f32)], noise: &[(f32, f32, Biquad)], life: f32, g: f32| {
        Some(Box::new(Drum::new(sr, seed, tones, noise, life, g * v)) as Box<dyn Voice>)
    };
    // membrane variant: the D1 velocity→timbre transform, then the same build
    let dm = |tones: &[(f32, f32, f32, f32)], noise: &[(f32, f32, Biquad)], life: f32, g: f32| {
        let (tones, noise) = membrane_velocity(tones, noise, velnorm);
        Some(Box::new(Drum::new(sr, seed, &tones, &noise, life, g * v)) as Box<dyn Voice>)
    };
    let one = |amp: f32, t: f32, filt: Biquad| vec![(amp, t, filt)];
    // DR2 membrane tom: V1 starts at table pitch and dives to the 0.3x floor;
    // V2 starts 2.5 st sharp and glides down to the table pitch. V1 arm is
    // byte-identical to the old `dm(&tom_tones(f0, t60, 10.0), ...)`.
    let tom = |f0: f32, t60: f32, noise: &[(f32, f32, Biquad)], life: f32, g: f32| {
        let (start_f, glide, floor) = match kit {
            Kit::V1 => (f0, 10.0, None),
            Kit::V2 | Kit::V3 | Kit::Brush => {
                (f0 * TOM_OVERSHOOT, TOM_GLIDE_V2, Some(1.0 / TOM_OVERSHOOT))
            }
        };
        let (tones, noise) = membrane_velocity(&tom_tones(start_f, t60, glide), noise, velnorm);
        let mut drum = Drum::new(sr, seed, &tones, &noise, life, g * v);
        if let Some(r) = floor {
            drum = drum.with_glide_floor(r);
        }
        Some(Box::new(drum) as Box<dyn Voice>)
    };
    // v0.12 brush kit intercept: the seven brush keys take their own voices
    // (and skip the V3 sample overlays — a brush has no stick attack); every
    // other key falls through to the (V3-behaving) arms below.
    if kit == Kit::Brush {
        match key {
            38 => return brush_tap(vel, sr, seed),
            39 => return brush_slap(vel, sr, seed),
            40 => return brush_swirl(vel, sr, seed),
            42 | 44 => return brush_closed_hat(vel, sr, seed),
            46 => return brush_open_hat(vel, sr, seed),
            37 => return brush_rim(vel, sr, seed),
            35 | 36 => return brush_kick(vel, sr, seed),
            _ => {} // V3 fall-through
        }
    }
    let voice = match key {
        35 | 36 => {
            // beater knock over a sub drop (86 -> ~45 Hz): the chest thump,
            // plus a knuckle-of-the-beater tone (D3). V3 adds a short low-mid
            // body band so the click no longer sits on a hollow sub alone.
            // (Brush is grouped with V3 for fall-through correctness, though
            // 35|36 never reach here — the brush key map intercepts them.)
            if matches!(kit, Kit::V3 | Kit::Brush) {
                let tones = [
                    (172.0, 0.76, 0.14, 30.0),
                    (78.0, 1.25 + 0.35 * velnorm, 0.46, 2.6),
                    (118.0, 0.38, 0.05, 0.0),
                    (255.0, 0.22 * velnorm, 0.018, 0.0),
                ];
                let noise = [
                    (0.45, 0.006, Biquad::highpass(2300.0, 0.7, sr)),
                    (0.42, 0.006, Biquad::bandpass(3600.0, 0.9, sr)),
                    (0.18, 0.030, Biquad::bandpass(820.0, 0.9, sr)),
                ];
                dm(&tones, &noise, 0.8, 1.0)
            } else {
                let tones = [
                    (165.0, 0.8, 0.16, 28.0),
                    (86.0, 1.1 + 0.4 * velnorm, 0.42, 3.0),
                    (130.0, 0.4 * velnorm, 0.01, 0.0),
                ];
                let noise = [
                    (0.5, 0.005, Biquad::highpass(2500.0, 0.7, sr)),
                    (0.3, 0.005, Biquad::bandpass(3500.0, 0.9, sr)),
                ];
                dm(&tones, &noise, 0.8, 1.0)
            }
        }
        37 => d(
            // side stick
            &[(430.0, 0.5, 0.05, 0.0)],
            &one(0.6, 0.03, Biquad::bandpass(2200.0, 1.5, sr)),
            0.2,
            0.55,
        ),
        38 | 40 => match kit {
            // snare (D2 + D5): four head modes; shell slap lands with the
            // stick, the wires engage ~1.5 ms later (the snare's "crack"
            // then "rattle"), with a darker rattle tail
            Kit::V1 => {
                let (tones, noise) = membrane_velocity(
                    &SNARE_TONES,
                    &[
                        (0.55, 0.09, Biquad::bandpass(1300.0, 0.7, sr)),
                        (
                            0.75,
                            0.19,
                            Biquad::highpass(2800.0 * (0.85 + 0.35 * velnorm), 0.7, sr),
                        ),
                        (0.35, 0.35, Biquad::highpass(1800.0, 0.7, sr)),
                    ],
                    velnorm,
                );
                let drum = Drum::new(sr, seed, &tones, &noise, 0.6, 0.68 * v)
                    .with_band_ext(1, 0.0015, 0.0005, 0.0)
                    .with_band_ext(2, 0.0015, 0.0005, 0.0);
                Some(Box::new(drum) as Box<dyn Voice>)
            }
            // DR4 kit-v2: drop the broad-HP wire band; the shell (idx0) and a
            // trimmed dark tail (idx1, 0.35→0.22) go through membrane_velocity
            // as before, and the wires become a head-coupled `WireRes` cluster.
            // (Kit::Brush is unreachable here — brush 38 is intercepted by the
            // brush key map above and 40 is the swirl; the arm exists only for
            // match exhaustiveness.)
            Kit::V2 | Kit::V3 | Kit::Brush => {
                let (tones, noise) = membrane_velocity(
                    &SNARE_TONES,
                    &[
                        (0.55, 0.09, Biquad::bandpass(1300.0, 0.7, sr)),
                        (0.22, 0.35, Biquad::highpass(1800.0, 0.7, sr)),
                    ],
                    velnorm,
                );
                // dark tail is now idx1 (shell idx0 keeps no onset delay).
                let drum = Drum::new(sr, seed, &tones, &noise, 0.6, 0.68 * v)
                    .with_band_ext(1, 0.0015, 0.0005, 0.0);
                // key 40 (electric snare): brighter, tighter wires — first
                // 38/40 differentiation the kit has ever had.
                let (center_mul, am_depth) = if key == 40 { (1.15, 0.48) } else { (1.0, 0.6) };
                let bands = [
                    Biquad::bandpass(WIRE_CENTERS[0] * center_mul, WIRE_QS[0], sr),
                    Biquad::bandpass(WIRE_CENTERS[1] * center_mul, WIRE_QS[1], sr),
                    Biquad::bandpass(WIRE_CENTERS[2] * center_mul, WIRE_QS[2], sr),
                ];
                // Wire level = the D1 noise-amp scale the old HP band saw
                // (`0.75·(0.5+0.5·vn²)`) × the BP/HP bandwidth make-up. The
                // per-sample render multiplies `s` by `self.gain` (= 0.68·v),
                // so `v` is applied there — carrying it here too would square
                // the velocity term and diverge from the old band's law, so it
                // is deliberately omitted (see membrane_velocity's noise map).
                let d1_noise = 0.5 + 0.5 * velnorm * velnorm;
                let amp = 0.75 * d1_noise * WIRE_MAKEUP;
                let wire = WireRes {
                    bands,
                    gains: [1.0, 0.55 + 0.45 * velnorm, 0.30 + 0.70 * velnorm],
                    amp,
                    decay: dmul(0.19, sr),
                    onset: (0.0015 * sr) as u32,
                    env: 0.0,
                    atk: 1.0 / (0.0005 * sr),
                    // built tones[0].amp = post-membrane_velocity + jitter head
                    // level; the render normalises the live head against it.
                    head_amp0: drum.tones[0].amp,
                    head_track: WIRE_HEAD_TRACK,
                    am_depth,
                };
                Some(Box::new(drum.with_wire(wire)) as Box<dyn Voice>)
            }
        },
        39 => Some(Box::new(
            Drum::new(
                sr,
                seed,
                &[],
                &[(0.9, 0.10, Biquad::bandpass(1100.0, 1.2, sr))],
                0.35,
                0.70 * v,
            )
            .with_bursts(&[(0.010, 0.75), (0.022, 0.6)]),
        ) as Box<dyn Voice>), // hand clap: three quick bursts
        41 => tom(
            100.0,
            0.32,
            &one(0.25, 0.05, Biquad::bandpass(900.0, 0.8, sr)),
            0.55,
            0.78,
        ),
        43 => tom(
            140.0,
            0.30,
            &one(0.25, 0.05, Biquad::bandpass(1100.0, 0.8, sr)),
            0.5,
            0.74,
        ),
        45 => tom(
            190.0,
            0.28,
            &one(0.25, 0.05, Biquad::bandpass(1300.0, 0.8, sr)),
            0.45,
            0.69,
        ),
        47 | 48 | 50 => tom(
            240.0,
            0.24,
            &one(0.2, 0.04, Biquad::bandpass(1500.0, 0.8, sr)),
            0.4,
            0.64,
        ),
        42 | 44 => cymbal(
            &CymSpec {
                base: 3300.0,
                tone_amp: 0.10,
                t60_first: 0.05,
                t60_last: 0.03,
                noise: (0.8, 0.035, 6500.0),
                life: 0.14,
                gain: 0.42,
                // CYM-3: the stick tick a closed/pedal hat leads with
                click: Some((1.8 * velnorm, 0.005, 9000.0)),
                swell: false,
                pairs: false,
                v2: None,
                noise2: None,
                shimmer: None,
            },
            sr,
            seed,
            vel,
        ),
        46 => {
            // DR3 open hat: v2 splits the wash into a slow body + fast sizzle
            // (the centroid falls through the tail), widens the tonal decay
            // spread so a faint pitched ring survives under the wash, and adds a
            // ~45 Hz sizzle wobble. v1 is the old single-wash static hat.
            // (Every non-V1 kit gets the DR3 hat; brush 46 never reaches here —
            // the brush key map intercepts it.)
            let spec = if matches!(kit, Kit::V2 | Kit::V3 | Kit::Brush) {
                CymSpec {
                    base: 3300.0,
                    tone_amp: 0.10,
                    t60_first: 0.45,
                    t60_last: 0.10,
                    noise: (0.55, 0.30, 6000.0),
                    life: 0.95,
                    gain: 0.40,
                    click: None,
                    swell: false,
                    pairs: false,
                    v2: None,
                    noise2: Some((0.55, 0.16, 10000.0)),
                    shimmer: Some((45.0, 0.45)),
                }
            } else {
                CymSpec {
                    base: 3300.0,
                    tone_amp: 0.10,
                    t60_first: 0.30,
                    t60_last: 0.18,
                    noise: (0.8, 0.28, 6000.0),
                    life: 0.95,
                    gain: 0.40,
                    click: None,
                    swell: false,
                    pairs: false,
                    v2: None,
                    noise2: None,
                    shimmer: None,
                }
            };
            cymbal(&spec, sr, seed, vel)
        }
        49 if matches!(kit, Kit::V3 | Kit::Brush) => Some(metal_plate(49, sr, seed, vel)),
        49 => {
            // crash: instant chick, wash blooms over ~50 ms (CYM-2), the
            // coloured pairs beat in the shimmer (CYM-1), and it rings
            // out past 3 s like a real 16" (oracle 29). DR1 (kit v2): decay
            // order inverted so no tonal partial outlives the wash, detuned
            // twin partials, a low-mid CYM-1 pair, and the shimmer AM.
            let spec = crash_spec(
                kit,
                950.0,
                4200.0,
                4.2,
                0.50,
                velnorm,
                (2.6, 1.0),
                (1.7, 0.9),
            );
            cymbal(&spec, sr, seed, vel)
        }
        52 if matches!(kit, Kit::V3 | Kit::Brush) => Some(metal_plate(52, sr, seed, vel)),
        52 => cymbal(
            // china (D7/CYM-7): trashy — compressed decay, aggressive bright
            // wash, short life; until now this key fell to the generic tick
            &CymSpec {
                base: 1400.0,
                tone_amp: 0.09,
                t60_first: 0.62,
                t60_last: 0.26,
                noise: (1.7, 0.45, 7500.0),
                life: 1.0,
                gain: 0.50,
                click: None,
                swell: false,
                pairs: false,
                v2: None,
                noise2: None,
                shimmer: None,
            },
            sr,
            seed,
            vel,
        ),
        55 if matches!(kit, Kit::V3 | Kit::Brush) => Some(metal_plate(55, sr, seed, vel)),
        55 => cymbal(
            // splash (D7/CYM-7): small and quick, split from the crash
            &CymSpec {
                base: 1600.0,
                tone_amp: 0.12,
                t60_first: 0.4,
                t60_last: 0.2,
                noise: (0.9, 0.25, 5000.0),
                life: 0.6,
                gain: 0.45,
                click: None,
                swell: false,
                pairs: false,
                v2: None,
                noise2: None,
                shimmer: None,
            },
            sr,
            seed,
            vel,
        ),
        57 if matches!(kit, Kit::V3 | Kit::Brush) => Some(metal_plate(57, sr, seed, vel)),
        57 => {
            // second crash: as key 49, DR1 kit-v2 upgrade with a slightly
            // shorter tonal t60_first (base 820 twins keep the same Δf table —
            // beat rates are Δf, base-independent).
            let spec = crash_spec(
                kit,
                820.0,
                3800.0,
                4.6,
                0.52,
                velnorm,
                (2.4, 1.0),
                (1.6, 0.9),
            );
            cymbal(&spec, sr, seed, vel)
        }
        51 | 59 if matches!(kit, Kit::V3 | Kit::Brush) => Some(metal_plate(key, sr, seed, vel)),
        51 | 59 => cymbal(
            // ride (CYM-5): a short guarded stick ping over a quiet
            // sustaining wash, with a widened tone-decay spread
            &CymSpec {
                base: 1150.0,
                tone_amp: 0.16,
                t60_first: 0.9,
                t60_last: 0.30,
                noise: (0.30, 1.3, 6000.0),
                life: 2.6,
                gain: 0.42,
                click: Some((0.55 * (0.4 + 0.6 * velnorm), 0.07, 7500.0)),
                swell: false,
                pairs: false,
                v2: None,
                noise2: None,
                shimmer: None,
            },
            sr,
            seed,
            vel,
        ),
        53 => d(
            // ride bell (D7/CYM-6): a dense inharmonic METAL_RATIOS stack on
            // a 1650 Hz base — not two pure sines — plus a sharp stick click
            // and a light sustaining wash
            &[
                (1650.0, 0.50, 0.60, 0.0),
                (1650.0 * 1.483, 0.38, 0.55, 0.0),
                (1650.0 * 1.932, 0.30, 0.50, 0.0),
                (1650.0 * 2.546, 0.24, 0.42, 0.0),
                (1650.0 * 3.363, 0.18, 0.34, 0.0),
                (1650.0 * 4.365, 0.13, 0.26, 0.0),
            ],
            &[
                (1.6 * velnorm, 0.005, Biquad::highpass(7000.0, 0.7, sr)),
                (0.05, 0.4, Biquad::highpass(6000.0, 0.7, sr)),
            ],
            1.5,
            0.5,
        ),
        54 => d(
            // tambourine
            &[(6100.0, 0.15, 0.10, 0.0), (7900.0, 0.12, 0.09, 0.0)],
            &one(0.9, 0.11, Biquad::highpass(5200.0, 0.8, sr)),
            0.35,
            0.42,
        ),
        56 => d(
            // cowbell
            &[(560.0, 0.8, 0.22, 0.0), (845.0, 0.55, 0.18, 0.0)],
            &one(0.15, 0.02, Biquad::bandpass(700.0, 2.0, sr)),
            0.5,
            0.55,
        ),
        58 => Some(Box::new(
            // vibraslap: a cluster of inharmonic tine partials over a mid
            // noise band, the whole voice amplitude-fluttered by a fast
            // noise-coupled shimmer AM — the characteristic ~0.7 s rattle
            Drum::new(
                sr,
                seed,
                &[
                    (1730.0, 0.45, 0.50, 0.0),
                    (2470.0, 0.30, 0.42, 0.0),
                    (3150.0, 0.18, 0.35, 0.0),
                ],
                &one(0.45, 0.45, Biquad::bandpass(2100.0, 1.0, sr)),
                0.85,
                0.45 * v,
            )
            .with_shimmer(28.0, 0.9),
        ) as Box<dyn Voice>),
        60 => dm(
            &[(400.0, 1.0, 0.11, 3.0)],
            &one(0.35, 0.02, Biquad::bandpass(1400.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        61 => dm(
            &[(300.0, 1.0, 0.13, 3.0)],
            &one(0.35, 0.02, Biquad::bandpass(1100.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        62 => dm(
            &[(230.0, 1.0, 0.05, 0.0)],
            &one(0.3, 0.015, Biquad::bandpass(1200.0, 1.0, sr)),
            0.2,
            0.6,
        ),
        63 => dm(
            &[(190.0, 1.0, 0.24, 3.0)],
            &one(0.3, 0.02, Biquad::bandpass(1000.0, 1.0, sr)),
            0.4,
            0.65,
        ),
        64 => dm(
            &[(145.0, 1.0, 0.28, 3.0)],
            &one(0.3, 0.02, Biquad::bandpass(800.0, 1.0, sr)),
            0.45,
            0.65,
        ),
        65 | 66 => dm(
            &[(430.0, 0.9, 0.15, 4.0)],
            &one(0.3, 0.02, Biquad::bandpass(1600.0, 1.0, sr)),
            0.3,
            0.6,
        ),
        // agogo bells (67 hi / 68 lo): the melodic-agogo modal ratios
        // (1 : 1.70 : 2.85, voices.rs GM113) on drum-kit fundamentals a
        // minor-third-ish apart, fast metallic decay plus a clank transient
        67 => d(
            &[
                (1650.0, 0.9, 0.20, 0.0),
                (2805.0, 0.55, 0.16, 0.0),
                (4700.0, 0.18, 0.10, 0.0),
            ],
            &one(0.12, 0.008, Biquad::bandpass(3500.0, 1.0, sr)),
            0.5,
            0.50,
        ),
        68 => d(
            &[
                (1220.0, 0.9, 0.22, 0.0),
                (2074.0, 0.55, 0.17, 0.0),
                (3477.0, 0.18, 0.11, 0.0),
            ],
            &one(0.12, 0.008, Biquad::bandpass(2900.0, 1.0, sr)),
            0.5,
            0.50,
        ),
        69 | 70 | 82 => d(
            // cabasa / maracas / shaker
            &[],
            &one(1.0, 0.055, Biquad::highpass(4200.0, 0.7, sr)),
            0.18,
            0.40,
        ),
        // whistles (71 short / 72 long): a pitched ~2.35 kHz tone with a
        // narrow breath band on the same centre plus a faint HF hiss —
        // the same voice at two lengths
        71 | 72 => {
            let (t60, life) = if key == 71 {
                (0.10, 0.18)
            } else {
                (0.35, 0.50)
            };
            d(
                &[(2350.0, 0.55, t60, 0.0)],
                &[
                    (0.30, t60, Biquad::bandpass(2350.0, 6.0, sr)),
                    (0.10, t60 * 0.8, Biquad::highpass(5000.0, 0.7, sr)),
                ],
                life,
                0.50,
            )
        }
        // guiros (73 short / 74 long): a notched scrape — a fast-decaying
        // mid noise band re-triggered by a pulse train of bursts (the
        // stick crossing the notches), short vs long stroke
        73 | 74 => {
            let (step, n, center, life) = if key == 73 {
                (0.011f32, 10usize, 2600.0, 0.16)
            } else {
                (0.016, 28, 2200.0, 0.50)
            };
            let bursts: Vec<(f32, f32)> = (1..n)
                .map(|i| {
                    let frac = i as f32 / n as f32;
                    (i as f32 * step, 0.9 * (1.0 - 0.5 * frac))
                })
                .collect();
            Some(Box::new(
                Drum::new(
                    sr,
                    seed,
                    &[],
                    &one(0.9, 0.012, Biquad::bandpass(center, 1.2, sr)),
                    life,
                    0.50 * v,
                )
                .with_bursts(&bursts),
            ) as Box<dyn Voice>)
        }
        75 => d(
            &[(2500.0, 1.0, 0.09, 0.0)],
            &one(0.1, 0.01, Biquad::bandpass(2500.0, 3.0, sr)),
            0.25,
            0.55,
        ),
        76 => d(
            &[(850.0, 1.0, 0.09, 0.0)],
            &one(0.25, 0.012, Biquad::bandpass(1700.0, 1.5, sr)),
            0.25,
            0.60,
        ),
        77 => d(
            &[(620.0, 1.0, 0.10, 0.0)],
            &one(0.25, 0.012, Biquad::bandpass(1300.0, 1.5, sr)),
            0.3,
            0.60,
        ),
        // cuicas (78 mute / 79 open): a pitched friction squeak — a strong
        // fundamental + weak octave sharing a pitch glide, with a light
        // friction-noise band. Mute: short, gliding DOWN to a 0.55x floor;
        // open: longer, gliding UP (negative rate) to a 1.85x ceiling.
        78 => Some(Box::new(
            Drum::new(
                sr,
                seed,
                &[(640.0, 0.9, 0.12, 7.0), (1280.0, 0.30, 0.10, 7.0)],
                &one(0.15, 0.03, Biquad::bandpass(1500.0, 1.0, sr)),
                0.18,
                0.50 * v,
            )
            .with_glide_floor(0.55),
        ) as Box<dyn Voice>),
        79 => Some(Box::new(
            Drum::new(
                sr,
                seed,
                &[(390.0, 0.9, 0.40, -2.5), (780.0, 0.25, 0.30, -2.5)],
                &one(0.12, 0.10, Biquad::bandpass(1200.0, 1.0, sr)),
                0.50,
                0.50 * v,
            )
            .with_glide_floor(1.85),
        ) as Box<dyn Voice>),
        81 => d(
            // open triangle
            &[
                (4050.0, 0.7, 1.8, 0.0),
                (6420.0, 0.45, 1.5, 0.0),
                (8900.0, 0.25, 1.2, 0.0),
            ],
            &one(0.08, 0.01, Biquad::highpass(6000.0, 0.7, sr)),
            2.5,
            0.30,
        ),
        80 => d(
            // muted triangle
            &[(4050.0, 0.7, 0.12, 0.0), (6420.0, 0.4, 0.1, 0.0)],
            &one(0.08, 0.01, Biquad::highpass(6000.0, 0.7, sr)),
            0.3,
            0.30,
        ),
        _ => d(
            // gentle generic tick so unmapped keys are audible, not silent
            &[(1000.0, 0.4, 0.05, 0.0)],
            &one(0.3, 0.02, Biquad::bandpass(2000.0, 1.0, sr)),
            0.15,
            0.4,
        ),
    };
    voice.map(|v| {
        if matches!(kit, Kit::V3 | Kit::Brush) && samples {
            sample_overlay(key, vel, sr, seed, v)
        } else {
            v
        }
    })
}

// ---------------------------------------------------------------------------
// v0.12 alt-bank percussion set B (GM 116-119). These are MELODIC-channel
// voices — dispatched from `altbank::make` by PROGRAM (CC0 bank select), not
// from the channel-10 key map above — so the MIDI key sets each drum's pitch
// register. Ported from the superseded v0.11 branch (216da4a) and namespaced
// `_b`; trunk's default-bank 112-119 voices (voices.rs) are untouched.
// ---------------------------------------------------------------------------

/// Bank-B GM 116 taiko tension overshoot: ~1.5 st sharp at the strike,
/// settling on the played pitch (slow — a big head takes its time).
const TAIKO_B_OVERSHOOT: f32 = 1.0905;
const TAIKO_B_GLIDE_OCT_S: f32 = 1.2;
const TAIKO_B_GAIN: f32 = 0.71; // level knob: altbank_b116_taiko_level_vs_timpani

/// Bank-B GM 116 taiko: a deep long-ringing membrane — fundamental + three
/// inharmonic head modes over a LP-140 Hz boom band, with a short bright
/// bachi slap band that grows super-linearly with velocity (membrane_velocity
/// noise law).
pub(crate) fn taiko_b(key: u8, vel: u8, sr: f32, seed: u32) -> Box<dyn Voice> {
    let f0 = key_freq(key.clamp(31, 55));
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let start = f0 * TAIKO_B_OVERSHOOT;
    let tones = [
        (start, 1.00, 1.5, TAIKO_B_GLIDE_OCT_S),
        (start * 1.52, 0.32, 0.8, TAIKO_B_GLIDE_OCT_S),
        (start * 1.99, 0.18, 0.55, TAIKO_B_GLIDE_OCT_S),
        (start * 2.44, 0.09, 0.40, TAIKO_B_GLIDE_OCT_S),
    ];
    let noise = [
        (1.1, 0.09, Biquad::lowpass(140.0, 0.8, sr)),
        (0.45, 0.020, Biquad::bandpass(1600.0, 0.8, sr)),
    ];
    let (tones, noise) = membrane_velocity(&tones, &noise, velnorm);
    Box::new(
        Drum::new(sr, seed, &tones, &noise, 2.4, TAIKO_B_GAIN * v)
            .with_glide_floor(1.0 / TAIKO_B_OVERSHOOT),
    )
}

const MELODIC_TOM_B_GAIN: f32 = 0.97; // level knob: altbank_b117_melodic_tom_level_vs_marimba

/// Bank-B GM 117 melodic tom: the kit-v2 tom recipe (overshoot + settle on
/// the played pitch) with a key-tracked decay and a key-tracked stick band,
/// so a tom line actually plays a melody.
pub(crate) fn melodic_tom_b(key: u8, vel: u8, sr: f32, seed: u32) -> Box<dyn Voice> {
    let f0 = key_freq(key.clamp(36, 72));
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let t60 = (0.30 * (196.0 / f0).powf(0.25)).clamp(0.18, 0.45);
    let stick_bp = (f0 * 6.0).clamp(600.0, 1600.0);
    let noise = [(0.25, 0.05, Biquad::bandpass(stick_bp, 0.8, sr))];
    let (tones, noise) = membrane_velocity(
        &tom_tones(f0 * TOM_OVERSHOOT, t60, TOM_GLIDE_V2),
        &noise,
        velnorm,
    );
    Box::new(
        Drum::new(sr, seed, &tones, &noise, 0.75, MELODIC_TOM_B_GAIN * v)
            .with_glide_floor(1.0 / TOM_OVERSHOOT),
    )
}

/// Bank-B GM 118 synth-drum "zap": the tone starts 2.83x sharp (a 1.5-octave
/// dive) and glides fast onto the played pitch, where it rings as a
/// near-pure sine.
const SYNTH_DRUM_B_ZAP_RATIO: f32 = 2.83;
const SYNTH_DRUM_B_GLIDE_OCT_S: f32 = 24.0;
const SYNTH_DRUM_B_GAIN: f32 = 0.80; // level knob: altbank_b118_synth_drum_level_vs_melodic_tom

/// Bank-B GM 118 synth drum: one zap-glide sine over a tiny >3 kHz tick.
pub(crate) fn synth_drum_b(key: u8, vel: u8, sr: f32, seed: u32) -> Box<dyn Voice> {
    let f0 = key_freq(key.clamp(33, 81));
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let tones = [(
        f0 * SYNTH_DRUM_B_ZAP_RATIO,
        1.0,
        0.55,
        SYNTH_DRUM_B_GLIDE_OCT_S,
    )];
    let noise = [(0.15, 0.004, Biquad::highpass(3000.0, 0.7, sr))];
    let (tones, noise) = membrane_velocity(&tones, &noise, velnorm);
    Box::new(
        Drum::new(sr, seed, &tones, &noise, 0.9, SYNTH_DRUM_B_GAIN * v)
            .with_glide_floor(1.0 / SYNTH_DRUM_B_ZAP_RATIO),
    )
}

// --- bank-B GM 119 reverse cymbal --------------------------------------------

/// The swell runs at most this long; note_off (or the cap) hard-stops it —
/// the reverse cymbal's abrupt cut IS the effect.
const REV_CYM_B_RISE_CAP_S: f32 = 2.5;
const REV_CYM_B_STOP_T60: f32 = 0.008;
const REV_CYM_B_LIFE_AFTER_STOP_S: f32 = 0.15;
pub(crate) const REV_CYM_B_BASE_HZ: f32 = 950.0;
const REV_CYM_B_TONE_AMP: f32 = 0.13;
const REV_CYM_B_GAIN: f32 = 0.50; // level knob: altbank_b119_reverse_cymbal_crash_handover_level

struct RevPartial {
    phase: f32,
    freq: f32,
    amp: f32,    // live level, rising
    target: f32, // the A_i cap (a crash partial's forward level)
    rise: f32,   // per-sample multiplier > 1 (a reversed T60 decay)
    onset: u32,  // sample the rise starts: (cap − t60_i), so all land together
}

struct RevBand {
    filt: Biquad,
    amp: f32,
    target: f32,
    rise: f32,
    onset: u32,
}

/// Bank-B GM 119 reverse cymbal: the crash partial stack played BACKWARDS —
/// every partial and both wash bands rise from −60 dB on their own
/// reversed-decay clock so they all peak together at the cap, then a
/// note_off (or the cap itself) cuts the whole thing dead. Honours note_off,
/// unlike `Drum`.
struct RevCymB {
    partials: Vec<RevPartial>,
    bands: Vec<RevBand>,
    rng: Rng,
    t: u32,
    cap: u32,  // sample index of the self-stop
    life: u32, // hard ceiling (stop + 0.15 s)
    stopped: bool,
    stop_mul: f32,
    released: bool,
    gain: f32,
    sr: f32,
}

impl Voice for RevCymB {
    fn render(&mut self, out: &mut [f32]) -> bool {
        for o in out.iter_mut() {
            if self.t >= self.life {
                return false;
            }
            if !self.stopped && (self.released || self.t >= self.cap) {
                self.stopped = true;
                self.life = self
                    .life
                    .min(self.t + (REV_CYM_B_LIFE_AFTER_STOP_S * self.sr) as u32);
            }
            let mut s = 0.0;
            let white = self.rng.white();
            for p in &mut self.partials {
                if self.t >= p.onset {
                    s += p.amp * p.phase.sin();
                    p.phase += TAU * p.freq / self.sr;
                    if p.phase > TAU {
                        p.phase -= TAU;
                    }
                    if self.stopped {
                        p.amp *= self.stop_mul;
                    } else if p.amp < p.target {
                        p.amp = (p.amp * p.rise).min(p.target);
                    }
                }
            }
            for b in &mut self.bands {
                if self.t >= b.onset && b.amp > 1e-6 {
                    s += b.filt.process(white) * b.amp;
                    if self.stopped {
                        b.amp *= self.stop_mul;
                    } else if b.amp < b.target {
                        b.amp = (b.amp * b.rise).min(b.target);
                    }
                }
            }
            *o += s * self.gain;
            self.t += 1;
        }
        true
    }

    fn note_off(&mut self) {
        self.released = true;
    }

    fn released(&self) -> bool {
        self.released
    }

    #[cfg(test)]
    fn kind(&self) -> &'static str {
        "revcym_b"
    }
}

/// Bank-B GM 119 factory. Key tracking is half a semitone per semitone on the
/// metal base only (a cymbal's size class, not a chromatic instrument).
pub(crate) fn reverse_cymbal_b(key: u8, vel: u8, sr: f32, seed: u32) -> Box<dyn Voice> {
    let v = vel_amp(vel);
    let velnorm = vel as f32 / 127.0;
    let base = REV_CYM_B_BASE_HZ * 2f32.powf((key.clamp(48, 72) as f32 - 60.0) / 24.0);
    let cap = (REV_CYM_B_RISE_CAP_S * sr) as u32;
    let rise_for = |t60: f32| 10f32.powf(3.0 / (t60.max(0.005) * sr)); // inverse dmul
    let mut partials = Vec::with_capacity(METAL_RATIOS.len());
    for (i, &r) in METAL_RATIOS.iter().enumerate() {
        let frac = i as f32 / (METAL_RATIOS.len() - 1) as f32;
        // the crash amp law (forward), reached at the END of the rise
        let target =
            REV_CYM_B_TONE_AMP * (1.0 - 0.6 * frac) * (0.55 + 0.55 * velnorm.powf(frac + 0.5));
        let t60 = 2.2 + (0.8 - 2.2) * frac;
        partials.push(RevPartial {
            phase: 0.0,
            freq: base * r,
            amp: target * 1e-3,
            target,
            rise: rise_for(t60),
            onset: ((REV_CYM_B_RISE_CAP_S - t60).max(0.0) * sr) as u32,
        });
    }
    let bands = vec![
        RevBand {
            filt: Biquad::highpass(3500.0, 0.7, sr),
            amp: 0.8e-3,
            target: 0.8,
            rise: rise_for(REV_CYM_B_RISE_CAP_S),
            onset: 0,
        },
        RevBand {
            filt: Biquad::highpass(8500.0, 0.7, sr),
            amp: 0.55e-3,
            target: 0.55,
            rise: rise_for(0.9),
            onset: (1.6 * sr) as u32,
        },
    ];
    Box::new(RevCymB {
        partials,
        bands,
        rng: Rng::new(seed ^ 0x9EC7_3119),
        t: 0,
        cap,
        life: cap + (REV_CYM_B_LIFE_AFTER_STOP_S * sr) as u32,
        stopped: false,
        stop_mul: dmul(REV_CYM_B_STOP_T60, sr),
        released: false,
        gain: REV_CYM_B_GAIN * v,
        sr,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::testutil;

    /// Oracle 30 (structural half, §5.3): the D1 membrane transform moves
    /// every table quantity in the designed direction — the audio spectral
    /// form is unwritable under the pitch glide, so the tables are the seam.
    #[test]
    fn membrane_velocity_transform_is_directional() {
        let sr = 44100.0;
        let tones = [(100.0, 1.0, 0.32, 10.0)];
        let noise = [(0.25, 0.05, Biquad::bandpass(900.0, 0.8, sr))];
        let (t_hard, n_hard) = membrane_velocity(&tones, &noise, 1.0);
        let (t_soft, n_soft) = membrane_velocity(&tones, &noise, 0.0);
        assert!(t_hard[0].0 > t_soft[0].0, "start pitch");
        assert!(t_hard[0].2 > t_soft[0].2, "decay t60");
        assert!(t_hard[0].3 > t_soft[0].3, "glide rate");
        assert!(n_hard[0].0 > n_soft[0].0, "click/noise energy");
        // the vn² click curve spans exactly 2x with a 0.5 ghost-note floor
        assert!((n_hard[0].0 / n_soft[0].0 - 2.0).abs() < 1e-4);
    }

    fn render_drum(key: u8, vel: u8, secs: f32) -> Vec<f32> {
        render_drum_kit(key, vel, secs, Kit::V1)
    }

    fn render_drum_kit(key: u8, vel: u8, secs: f32, kit: Kit) -> Vec<f32> {
        render_drum_kit_samples(key, vel, secs, kit, false)
    }

    fn render_drum_kit_samples(key: u8, vel: u8, secs: f32, kit: Kit, samples: bool) -> Vec<f32> {
        let sr = 44100.0;
        let mut v = make(key, vel, sr, 7, kit, samples).unwrap();
        let mut buf = vec![0f32; (sr * secs) as usize];
        v.render(&mut buf);
        buf
    }

    fn sec_window(s: &[f32], sr: f32, a: f32, b: f32) -> &[f32] {
        &s[(a * sr) as usize..(b * sr) as usize]
    }

    /// DR0 seam: spot-checks ONE kit-agnostic key (51 ride — never branches on
    /// `kit`) is byte-identical under V1 and V2, i.e. a ch-10 Program Change
    /// only ever changes the keys a v2 fix touches. (The V1==v0.8.1 baseline
    /// invariant is pinned separately by `v1_drum_render_is_frozen`.)
    #[test]
    fn kit_v2_seam_wired_and_inert_for_untouched_keys() {
        let sr = 44100.0;
        let render = |kit| {
            let mut v = make(51, 100, sr, 7, kit, false).unwrap();
            let mut buf = vec![0f32; (sr * 1.5) as usize];
            v.render(&mut buf);
            buf
        };
        let v1 = render(Kit::V1);
        let v2 = render(Kit::V2);
        assert!(v1.iter().any(|&x| x.abs() > 1e-4), "ride voice makes sound");
        assert_eq!(v1, v2, "kit-agnostic key 51 identical under V1 and V2");
    }

    /// FNV-1a over the raw f32 bits of a render buffer — a compact byte-exact
    /// fingerprint (bit-level, so it catches a sub-dB drift the golden misses).
    fn render_fingerprint(buf: &[f32]) -> u64 {
        let mut h = 0xcbf29ce484222325u64;
        for &x in buf {
            h ^= x.to_bits() as u64;
            h = h.wrapping_mul(0x100000001b3);
        }
        h
    }

    /// Byte-exact freeze of the legacy (V1) kit for representative keys, so any
    /// future edit to a shared render/build path that silently shifts V1 —
    /// below the golden's ±2.5 dB trip-wire — fails loudly here. V1 IS the
    /// v0.8.1 baseline (proven at integration by the album byte-compare); this
    /// pins it forward for every phase still to land. Contamination canary in
    /// the spirit of lessons_learnt (canaries find contamination, not drift).
    #[test]
    fn v1_drum_render_is_frozen() {
        // (key, fingerprint). Kick, snare, closed hat, crash, tom.
        let cases: [(u8, u64); 5] = [
            (36, 0x77e42657e7f8a7a3),
            (38, 0x9c6b613424fb3d46),
            (42, 0x76e3c7038c0ff8f5),
            (49, 0x3d8caf328fcc2db8),
            (41, 0x82457a61ced252c1),
        ];
        for (key, want) in cases {
            let got = render_fingerprint(&render_drum_kit(key, 100, 1.0, Kit::V1));
            assert_eq!(got, want, "V1 render of key {key} drifted (fingerprint)");
        }
    }

    /// DR-O1 (gate differential): a ch-10 Program Change makes the crash
    /// (key 49) a materially different render under kit v2 than v1 — the DR1
    /// fix engages. (The kit-agnostic key 51 stays identical, covered by
    /// `kit_v2_seam_wired_and_inert_for_untouched_keys`.)
    #[test]
    fn dr_o1_crash_v2_diverges_from_v1() {
        let v1 = render_drum_kit(49, 100, 1.0, Kit::V1);
        let v2 = render_drum_kit(49, 100, 1.0, Kit::V2);
        assert!(v1.iter().any(|&x| x.abs() > 1e-4), "v1 crash makes sound");
        assert!(v2.iter().any(|&x| x.abs() > 1e-4), "v2 crash makes sound");
        assert_ne!(v1, v2, "crash 49 must differ under kit v2 (DR1 engaged)");
    }

    /// Detuned-twin beat detector for DR-O4: in the twins' LIVE window
    /// [0.3, 1.2] s (per the master-HLD §6 DR-O4 correction — the earlier
    /// [2.0, 3.5] s window measures dead twins), bandpass the lowest primary
    /// partial + its twin (~950 / 955.6 Hz), take the rectified/smoothed
    /// envelope, detrend off the slow decay, and return the coefficient of
    /// variation (std/mean). A single sine (v1) gives a smooth decaying
    /// envelope → low CV; the 0.7-amp detuned twin (v2) beats at ~5.6 Hz →
    /// high CV. Seed 7 fixes `jf`, so primary and twin move together and the
    /// beat rate is `Δf·jf` regardless of the exact strike.
    fn twin_beat_cv(buf: &[f32]) -> f32 {
        let sr = 44100.0f32;
        let a = (0.3 * sr) as usize;
        let b = (1.2 * sr) as usize;
        // centre on the lowest primary partial (same jf for both kits).
        let center = testutil::peak_locate(&buf[a..b], sr, 905.0, 1000.0);
        let mut bp = Biquad::bandpass(center, 20.0, sr);
        let mut env_lp = OnePole::lowpass(70.0, sr);
        let mut slow = OnePole::lowpass(2.0, sr);
        // process the whole buffer so the filters settle before the window.
        let mut env = Vec::with_capacity(buf.len());
        let mut detr = Vec::with_capacity(buf.len());
        for &x in buf {
            let e = env_lp.process(bp.process(x).abs());
            detr.push((e - slow.process(e)) as f64);
            env.push(e as f64);
        }
        let mean = env[a..b].iter().sum::<f64>() / (b - a) as f64;
        let var = detr[a..b].iter().map(|&d| d * d).sum::<f64>() / (b - a) as f64;
        (var.sqrt() / mean.max(1e-12)) as f32
    }

    /// DR-O4 (corrected, master HLD §6): the detuned twin field makes the
    /// crash tail *shimmer* in the twins' live window — the ~5.6 Hz beat of
    /// the lowest primary/twin pair lifts the band-envelope CV well above the
    /// single-sine v1 render. Differential, same seed (fail-first: v1 has no
    /// twin → smooth decaying line → far less beating).
    #[test]
    fn dr_o4_crash_twin_field_beats_in_live_window() {
        let v1 = render_drum_kit(49, 100, 1.5, Kit::V1);
        let v2 = render_drum_kit(49, 100, 1.5, Kit::V2);
        let cv1 = twin_beat_cv(&v1);
        let cv2 = twin_beat_cv(&v2);
        println!(
            "DR-O4 twin-beat CV: v1={cv1:.4} v2={cv2:.4} ratio={:.2}",
            cv2 / cv1
        );
        // calibrated threshold (printed values above): v2 beats far harder.
        assert!(
            cv2 > 3.0 * cv1,
            "twin beat not present: v2 CV {cv2} vs v1 CV {cv1}"
        );
    }

    /// DR-O10 (level parity): the kit switch is a realism change, not a mix
    /// change — v2 crash 49 RMS over [0, 1 s] is within ±2 dB of v1 (the wash
    /// dominates that energy; `CRASH_WASH_AMP_V2` is its knob). Design budget
    /// ≈ +0.6..0.8 dB.
    #[test]
    fn dr_o10_crash_level_parity() {
        let sr = 44100.0;
        let win = (1.0 * sr) as usize;
        let r1 = testutil::rms(&render_drum_kit(49, 100, 1.0, Kit::V1)[..win]);
        let r2 = testutil::rms(&render_drum_kit(49, 100, 1.0, Kit::V2)[..win]);
        let db = 20.0 * (r2 / r1).log10();
        println!("DR-O10 crash49 [0,1s] RMS: v1={r1:.6} v2={r2:.6} delta={db:.3} dB");
        assert!(
            db.abs() <= 2.0,
            "crash level parity {db} dB exceeds ±2 dB (CRASH_WASH_AMP_V2 = {CRASH_WASH_AMP_V2})"
        );
    }

    /// DR-O10 (open hat): the DR3 wash split + sizzle shimmer is a realism
    /// change, not a mix change — v2 key-46 RMS over its [0, 0.95 s] life stays
    /// within ±2 dB of v1.
    #[test]
    fn dr_o10_open_hat_level_parity() {
        let r1 = testutil::rms(&render_drum_kit(46, 100, 0.95, Kit::V1));
        let r2 = testutil::rms(&render_drum_kit(46, 100, 0.95, Kit::V2));
        let db = 20.0 * (r2 / r1).log10();
        println!("DR-O10 openhat46 [0,0.95s] RMS: v1={r1:.6} v2={r2:.6} delta={db:.3} dB");
        assert!(
            db.abs() <= 2.0,
            "open-hat level parity {db} dB exceeds ±2 dB"
        );
    }

    #[test]
    fn v3_crash_tail_is_broadband_in_samples_off_and_on_modes() {
        let sr = 44100.0;
        let v2 = render_drum_kit(49, 100, 4.0, Kit::V2);
        let v3 = render_drum_kit_samples(49, 100, 4.0, Kit::V3, false);
        let v3s = render_drum_kit_samples(49, 100, 4.0, Kit::V3, true);
        for (a, b) in [(0.50, 1.50), (1.50, 3.50)] {
            let f2 = testutil::flatness(sec_window(&v2, sr, a, b), sr, 700.0, 12_000.0);
            let f3 = testutil::flatness(sec_window(&v3, sr, a, b), sr, 700.0, 12_000.0);
            let f3s = testutil::flatness(sec_window(&v3s, sr, a, b), sr, 700.0, 12_000.0);
            println!("V3 crash flatness [{a:.1},{b:.1}]s: v2={f2:.3} v3={f3:.3} v3s={f3s:.3}");
            assert!(
                f3 >= 0.18 && f3 > 1.35 * f2,
                "modeled V3 crash still too tonal"
            );
            assert!(
                f3s >= 0.18 && f3s >= 0.90 * f3,
                "sampled V3 crash regressed flatness"
            );
        }
        let r2 = testutil::rms(&v2);
        for (name, s) in [("v3", &v3), ("v3 samples", &v3s)] {
            let db = 20.0 * (testutil::rms(s) / r2.max(1e-12)).log10();
            assert!(
                db.abs() <= 3.0,
                "{name} crash level moved {db:+.2} dB vs V2"
            );
            assert!(
                s.iter().all(|x| x.is_finite()),
                "{name} crash produced non-finite samples"
            );
        }
    }

    #[test]
    fn v3_sample_overlay_engages_for_crash_kick_and_snare() {
        for key in [49u8, 36, 38] {
            let plain = render_drum_kit_samples(key, 110, 0.7, Kit::V3, false);
            let sampled = render_drum_kit_samples(key, 110, 0.7, Kit::V3, true);
            assert_ne!(plain, sampled, "sample layer did not engage for key {key}");
            assert!(
                sampled.iter().all(|x| x.is_finite()),
                "sampled key {key} non-finite"
            );
            let delta_db =
                20.0 * (testutil::rms(&sampled) / testutil::rms(&plain).max(1e-12)).log10();
            assert!(
                delta_db.abs() <= 6.0,
                "sample overlay level jump for key {key}: {delta_db:+.2} dB"
            );
        }
    }

    #[test]
    fn v3_kick_keeps_sub_without_dc() {
        let sr = 44100.0;
        let kick = render_drum_kit(36, 115, 0.8, Kit::V3);
        let sub = testutil::band_rms(
            &kick[(0.020 * sr) as usize..(0.300 * sr) as usize],
            sr,
            60.0,
            1.0,
        );
        let dc = kick.iter().sum::<f32>() / kick.len() as f32;
        let peak = kick.iter().fold(0f32, |m, &x| m.max(x.abs())).max(1e-12);
        assert!(sub > 0.01, "V3 kick lost sub body: {sub}");
        assert!(dc.abs() < 0.015 * peak, "V3 kick DC offset too high: {dc}");
    }

    #[test]
    fn v3_toms_settle_near_table_pitch() {
        let sr = 44100.0;
        for (key, table) in [(41u8, 100.0), (43, 140.0), (45, 190.0), (48, 240.0)] {
            let b = render_drum_kit(key, 100, 0.5, Kit::V3);
            let f = testutil::peak_locate(
                &b[(sr * 0.15) as usize..(sr * 0.30) as usize],
                sr,
                table * 0.65,
                table * 1.35,
            );
            assert!(
                (f - table).abs() < table * 0.22,
                "tom {key} settled at {f:.1} Hz, expected {table}"
            );
        }
    }

    #[test]
    fn v3_auxiliary_percussion_stays_audible_and_finite() {
        for key in [
            37u8, 39, 54, 56, 60, 61, 62, 63, 64, 65, 66, 69, 70, 82, 80, 81,
        ] {
            let old = render_drum_kit(key, 100, 0.6, Kit::V2);
            let new = render_drum_kit(key, 100, 0.6, Kit::V3);
            assert!(new.iter().all(|x| x.is_finite()), "key {key} non-finite");
            let nr = testutil::rms(&new);
            assert!(nr > 1e-5, "key {key} fell silent");
            let db = 20.0 * (nr / testutil::rms(&old).max(1e-12)).log10();
            assert!(db.abs() <= 4.0, "key {key} level changed {db:+.2} dB vs V2");
        }
    }

    /// DR2 (tom pitch-drop): a kit-v2 tom (key 41, table 100 Hz) settles ON the
    /// table pitch, where v1 dives ~21 st to its 0.3x floor (~30 Hz). Measured
    /// on the settled window [0.15, 0.30] s via a Goertzel peak (never
    /// zero-crossings — HLD DR-O corrections / lessons_learnt).
    #[test]
    fn dr2_tom_v2_settles_at_table_pitch() {
        let sr = 44100.0;
        let settled = |kit| {
            let b = render_drum_kit(41, 100, 0.5, kit);
            let a = (sr * 0.15) as usize;
            let z = (sr * 0.30) as usize;
            testutil::peak_locate(&b[a..z], sr, 20.0, 200.0)
        };
        let f_v1 = settled(Kit::V1);
        let f_v2 = settled(Kit::V2);
        println!("DR2 tom41 settled pitch: v1={f_v1:.1} Hz  v2={f_v2:.1} Hz");
        assert!(
            (f_v2 - 100.0).abs() < 20.0,
            "v2 tom settles near the 100 Hz table pitch (got {f_v2:.1})"
        );
        assert!(
            f_v1 < 60.0,
            "v1 tom dived far below the table (got {f_v1:.1})"
        );
        assert!(
            f_v2 > f_v1 * 1.4,
            "v2 settled pitch sits well above v1's dived pitch (v1={f_v1:.1}, v2={f_v2:.1})"
        );
    }

    /// DR3 (open-hat spectral motion): v2 splits the wash into a slow body +
    /// fast sizzle (and widens the tonal decay spread), so the spectral
    /// centroid FALLS through the tail — a real hat loses HF fastest. v1's
    /// single static wash barely moves. Measured as the early/late centroid
    /// ratio; v2 falls materially more than v1.
    #[test]
    fn dr3_open_hat_v2_centroid_falls() {
        let sr = 44100.0;
        let ratio = |kit| {
            let b = render_drum_kit(46, 100, 0.95, kit);
            let c =
                |a: f32, z: f32| testutil::centroid(&b[(sr * a) as usize..(sr * z) as usize], sr);
            let (early, late) = (c(0.02, 0.12), c(0.30, 0.50));
            (early, late, early / late)
        };
        let (e1, l1, r1) = ratio(Kit::V1);
        let (e2, l2, r2) = ratio(Kit::V2);
        println!(
            "DR3 open-hat centroid early/late: v1 {e1:.0}/{l1:.0} r={r1:.2}  v2 {e2:.0}/{l2:.0} r={r2:.2}"
        );
        assert!(
            r2 > r1 * 1.3,
            "v2 centroid falls materially more than v1 (r1={r1:.2}, r2={r2:.2})"
        );
        assert!(
            r2 > 1.25,
            "v2 early centroid well above its late (r2={r2:.2})"
        );
    }

    /// Oracle 20 (structural, §5.3): the shipped tom table carries the
    /// 1:1.59:2.14 membrane modes — verified on a glide-disabled build of
    /// the exact same table (the glide smears any spectral read).
    #[test]
    fn tom_membrane_modes_present() {
        let sr = 44100.0;
        let tones = tom_tones(100.0, 0.32, 0.0); // shipped table, glide off
        let mut v = Drum::new(sr, 7, &tones, &[], 0.6, 0.8);
        let mut buf = vec![0f32; (0.4 * sr) as usize];
        Voice::render(&mut v, &mut buf);
        // jf jitters all mode freqs ±3% together; search ±8% windows
        let floor = testutil::mag_at(&buf, sr, 100.0) * 0.05;
        for f0 in [100.0f32, 159.0, 214.0] {
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            let m = testutil::mag_at(&buf, sr, p);
            assert!(m > floor, "mode near {f0} Hz missing (mag {m})");
        }
    }

    /// Oracle 21 (structural, §5.3): all four snare head modes speak.
    #[test]
    fn snare_head_modes_present() {
        let sr = 44100.0;
        let mut tones = SNARE_TONES;
        for t in &mut tones {
            t.3 = 0.0; // disable the shared down-glide for the read
        }
        let mut v = Drum::new(sr, 7, &tones, &[], 0.5, 0.7);
        let mut buf = vec![0f32; (0.3 * sr) as usize];
        Voice::render(&mut v, &mut buf);
        let floor = testutil::mag_at(&buf, sr, 186.0) * 0.05;
        for f0 in [186.0f32, 280.0, 330.0, 430.0] {
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            let m = testutil::mag_at(&buf, sr, p);
            assert!(m > floor, "head mode near {f0} Hz missing (mag {m})");
        }
    }

    /// Oracle 22 (§5.1 corrected): the kick's >3.5 kHz beater point grows
    /// SUPER-linearly with velocity — faster than the amplitude curve.
    #[test]
    fn kick_beater_point_superlinear() {
        let sr = 44100.0;
        let hard = render_drum(36, 120, 0.5);
        let soft = render_drum(36, 30, 0.5);
        let early = (0.004 * sr) as usize;
        let point = |s: &[f32]| testutil::hp_rms(&s[..early], sr, 3500.0);
        let gain_ratio = crate::dsp::vel_amp(120) / crate::dsp::vel_amp(30);
        let point_ratio = point(&hard) / point(&soft).max(1e-9);
        assert!(
            point_ratio > 1.3 * gain_ratio,
            "beater ratio {point_ratio} vs amplitude ratio {gain_ratio}"
        );
    }

    /// Oracle 28: the ride bell is a dense inharmonic stack (≥5 partials)
    /// with a >7 kHz stick click on the front.
    #[test]
    fn ride_bell_dense_and_clicky() {
        let sr = 44100.0;
        let buf = render_drum(53, 110, 1.0);
        let floor = testutil::mag_at(&buf, sr, 1650.0) * 0.04;
        let mut found = 0;
        for r in METAL_RATIOS {
            let f0 = 1650.0 * r;
            let p = testutil::peak_locate(&buf, sr, f0 * 0.92, f0 * 1.08);
            if testutil::mag_at(&buf, sr, p) > floor {
                found += 1;
            }
        }
        assert!(found >= 5, "only {found} bell partials found");
        // stick click: >7 kHz energy concentrated at the very front
        let early = testutil::hp_rms(&buf[..(0.006 * sr) as usize], sr, 7000.0);
        let late = testutil::hp_rms(
            &buf[(0.010 * sr) as usize..(0.030 * sr) as usize],
            sr,
            7000.0,
        );
        assert!(
            early > 2.0 * late,
            "no stick click: early {early} late {late}"
        );
    }

    fn last_audible(s: &[f32]) -> f32 {
        let sr = 44100.0;
        let peak = s.iter().fold(0f32, |m, &x| m.max(x.abs())).max(1e-12);
        let idx = s.iter().rposition(|&x| x.abs() > 1e-4 * peak).unwrap_or(0);
        idx as f32 / sr
    }

    /// Oracle 29 (+ §5.2/§5.3 clauses): china and splash are genuinely
    /// distinct voices — bounded lives and the china measurably trashier
    /// (brighter wash) than the crash.
    #[test]
    fn china_splash_crash_are_distinct() {
        let sr = 44100.0;
        let china = render_drum(52, 110, 1.6);
        let splash = render_drum(55, 110, 1.2);
        let crash = render_drum(49, 110, 4.2);
        let (lc, ls, lx) = (
            last_audible(&china),
            last_audible(&splash),
            last_audible(&crash),
        );
        assert!((0.6..=1.2).contains(&lc), "china life {lc}");
        assert!(ls < 0.7, "splash life {ls}");
        assert!(lx > 3.0, "crash life {lx}");
        // spectral distinctness: china's >8 kHz : 2-4 kHz balance exceeds
        // the crash's by a clear margin at matched velocity
        let trash = |s: &[f32]| {
            testutil::hp_rms(s, sr, 8000.0) / testutil::band_rms(s, sr, 3000.0, 0.8).max(1e-9)
        };
        let (tc, tx) = (
            trash(&china[..(0.5 * sr) as usize]),
            trash(&crash[..(0.5 * sr) as usize]),
        );
        assert!(tc > 1.5 * tx, "china trash {tc} vs crash {tx}");
    }

    /// Oracle 31 (§5.3 calibrated): D8's anti-correlated strike dither makes
    /// the fundamental:overtone balance vary hit-to-hit far beyond what the
    /// old uniform jf jitter produced (which moved all modes together and
    /// left the RATIO nearly constant) — and stays bounded.
    #[test]
    fn strike_variation_is_real_and_bounded() {
        let sr = 44100.0;
        let mut ratios = Vec::new();
        for seed in 1..=8u32 {
            let tones = tom_tones(100.0, 0.32, 0.0);
            let mut v = Drum::new(sr, seed * 977, &tones, &[], 0.6, 0.8);
            let mut buf = vec![0f32; (0.3 * sr) as usize];
            Voice::render(&mut v, &mut buf);
            let f = testutil::peak_locate(&buf, sr, 92.0, 108.0);
            let m = testutil::peak_locate(&buf, sr, 146.0, 172.0);
            ratios.push(testutil::mag_at(&buf, sr, f) / testutil::mag_at(&buf, sr, m).max(1e-9));
        }
        let hi = ratios.iter().fold(f32::MIN, |m, &x| m.max(x));
        let lo = ratios.iter().fold(f32::MAX, |m, &x| m.min(x));
        assert!(hi / lo > 1.3, "ratio spread {} .. {} too uniform", lo, hi);
        assert!(hi / lo < 6.0, "ratio spread {} .. {} unbounded", lo, hi);
    }

    /// Oracle 23 (CYM-2): the crash wash BLOOMS — its >6 kHz envelope peaks
    /// after 20 ms (instant chick, swelling shimmer) while the closed hat
    /// (no swell) peaks immediately.
    #[test]
    fn crash_blooms_hat_does_not() {
        let sr = 44100.0;
        let hf_argmax_ms = |s: &[f32]| {
            let win = (0.005 * sr) as usize;
            let mut hp = Biquad::highpass(6000.0, 0.7, sr);
            let f: Vec<f32> = s.iter().map(|&x| hp.process(x)).collect();
            let (mut bi, mut bv) = (0usize, 0.0f32);
            for (i, w) in f.chunks(win).take(60).enumerate() {
                let r = testutil::rms(w);
                if r > bv {
                    bi = i;
                    bv = r;
                }
            }
            bi as f32 * 5.0
        };
        let crash = render_drum(49, 110, 0.5);
        assert!(
            hf_argmax_ms(&crash) > 20.0,
            "crash wash peaked at {} ms — no bloom",
            hf_argmax_ms(&crash)
        );
        // the chick still lands at t=0: real HF in the first 3 ms
        let chick = testutil::hp_rms(&crash[..(0.003 * sr) as usize], sr, 6000.0);
        assert!(chick > 0.02, "no chick at the front: {chick}");
        let hat = render_drum(42, 110, 0.2);
        assert!(
            hf_argmax_ms(&hat) < 10.0,
            "hat should not bloom ({} ms)",
            hf_argmax_ms(&hat)
        );
    }

    /// Oracle 24 (CYM-1, §5.3): the coloured wash BEATS — envelope
    /// autocorrelation in the 10-25 ms lag range, differential against a
    /// pairs-disabled build of the same spec.
    #[test]
    fn crash_wash_beats() {
        let sr = 44100.0;
        let spec = |pairs: bool| CymSpec {
            base: 950.0,
            tone_amp: 0.13,
            t60_first: 2.6,
            t60_last: 1.0,
            noise: (1.0, 1.9, 4200.0),
            life: 4.2,
            gain: 0.50,
            click: None,
            swell: true,
            pairs,
            v2: None,
            noise2: None,
            shimmer: None,
        };
        let render = |pairs: bool| {
            let mut v = cymbal(&spec(pairs), sr, 7, 110).unwrap();
            let mut buf = vec![0f32; (1.0 * sr) as usize];
            v.render(&mut buf);
            // listen where the 6000/6055 pair beats (a broadband read lets
            // the un-paired wash swamp the AM)
            let mut bp = Biquad::bandpass(6030.0, 15.0, sr);
            buf.iter()
                .skip((0.05 * sr) as usize)
                .map(|&x| bp.process(x))
                .collect::<Vec<f32>>()
        };
        let (with_peak, rate) =
            testutil::env_autocorr_peak(&render(true), sr, 1.0 / 100.0, 1.0 / 40.0);
        let (without_peak, _) =
            testutil::env_autocorr_peak(&render(false), sr, 1.0 / 100.0, 1.0 / 40.0);
        assert!(
            with_peak > without_peak + 0.1,
            "no added beat: with {with_peak} vs without {without_peak}"
        );
        assert!((40.0..=100.0).contains(&rate), "beat rate {rate} Hz");
    }

    /// Oracle 25 (CYM-3, §5.3 relative form): the closed hat leads with a
    /// stick tick — early:late >9 kHz ratio far above the tickless build —
    /// and the tick grows with velocity.
    #[test]
    fn closed_hat_tick() {
        let sr = 44100.0;
        let ratio = |s: &[f32]| {
            testutil::hp_rms(&s[..(0.002 * sr) as usize], sr, 9000.0)
                / testutil::hp_rms(&s[(0.010 * sr) as usize..(0.030 * sr) as usize], sr, 9000.0)
                    .max(1e-9)
        };
        let with = render_drum(42, 110, 0.15);
        // tickless comparison: same spec, click stripped
        let spec = CymSpec {
            base: 3300.0,
            tone_amp: 0.10,
            t60_first: 0.05,
            t60_last: 0.03,
            noise: (0.8, 0.035, 6500.0),
            life: 0.14,
            gain: 0.42,
            click: None,
            swell: false,
            pairs: false,
            v2: None,
            noise2: None,
            shimmer: None,
        };
        let mut v = cymbal(&spec, sr, 7, 110).unwrap();
        let mut without = vec![0f32; (0.15 * sr) as usize];
        v.render(&mut without);
        assert!(
            ratio(&with) > 1.5 * ratio(&without),
            "tick missing: {} vs {}",
            ratio(&with),
            ratio(&without)
        );
        // velocity: the tick's absolute energy grows with the hit
        let soft = render_drum(42, 40, 0.15);
        let tick = |s: &[f32]| testutil::hp_rms(&s[..(0.002 * sr) as usize], sr, 9000.0);
        assert!(
            tick(&with) > tick(&soft),
            "tick does not scale with velocity"
        );
    }

    /// Oracle 27 (CYM-5, §5.3 time-isolated): the ride ping is a short HF
    /// event over a quieter sustaining wash — early ≫ late, wash alive.
    #[test]
    fn ride_ping_over_wash() {
        let sr = 44100.0;
        let ride = render_drum(51, 110, 2.0);
        let early = testutil::hp_rms(&ride[..(0.030 * sr) as usize], sr, 7500.0);
        let late = testutil::hp_rms(
            &ride[(0.150 * sr) as usize..(0.300 * sr) as usize],
            sr,
            7500.0,
        );
        assert!(early > 3.0 * late, "no ping: early {early} vs late {late}");
        let wash = testutil::rms(&ride[(1.4 * sr) as usize..(1.8 * sr) as usize]);
        assert!(wash > 5e-6, "the wash died with the ping: {wash}");
    }

    /// Oracle 33 (D5, §5.3 ratio form): the snare wires engage ~1.5 ms after
    /// the shell slap — wire-band energy in the first 1 ms is a fraction of
    /// its 2-6 ms level, while the shell speaks from t=0.
    #[test]
    fn snare_wires_engage_late() {
        let sr = 44100.0;
        let snare = render_drum(38, 110, 0.3);
        let wire = |a: f32, b: f32| {
            testutil::hp_rms(&snare[(a * sr) as usize..(b * sr) as usize], sr, 2800.0)
        };
        let pre = wire(0.0, 0.001);
        let post = wire(0.002, 0.006);
        assert!(pre < 0.35 * post, "wires too early: {pre} vs {post}");
        let shell = testutil::band_rms(&snare[..(0.001 * sr) as usize], sr, 1300.0, 0.7);
        assert!(shell > 1e-3, "shell slap missing at t=0: {shell}");
    }

    /// Oracle 26 (D6, voice half): choke() collapses a ringing open hat
    /// within 30 ms and caps its life.
    #[test]
    fn choke_kills_open_hat() {
        let sr = 44100.0;
        let mut v = make(46, 110, sr, 7, Kit::V1, false).unwrap();
        let mut head = vec![0f32; (0.05 * sr) as usize];
        assert!(v.render(&mut head));
        let before = testutil::rms(&head[(0.03 * sr) as usize..]);
        v.choke();
        let mut tail = vec![0f32; (0.1 * sr) as usize];
        let alive = v.render(&mut tail);
        assert!(!alive, "choked voice out-lived its 30 ms cap");
        let after = testutil::rms(&tail[(0.03 * sr) as usize..]);
        assert!(after < 0.05 * before, "choke too soft: {after} vs {before}");
    }

    /// Oracle 30 (audio half): a hard kick carries proportionally more
    /// beater click and rings longer than a soft one.
    #[test]
    fn drum_velocity_shapes_timbre() {
        let sr = 44100.0;
        let hard = render_drum(36, 120, 1.0);
        let soft = render_drum(36, 30, 1.0);
        // beater-click energy normalised by the exact velocity gain the
        // engine applies (gain = g·vel_amp) — on main this ratio is 1.0
        // because the click amp is velocity-independent relative to gain
        let click = |s: &[f32], vel: u8| {
            testutil::hp_rms(&s[..(0.005 * sr) as usize], sr, 2500.0)
                / crate::dsp::vel_amp(vel).max(1e-9)
        };
        let (ch, cs) = (click(&hard, 120), click(&soft, 30));
        assert!(
            ch > 1.3 * cs,
            "click (gain-normalised) hard {ch} vs soft {cs}"
        );
        let (th, ts) = (testutil::t60_of(&hard, sr), testutil::t60_of(&soft, sr));
        assert!(th > ts, "t60 hard {th} vs soft {ts}");
    }

    /// DR-O8(a) (differential): the v2 snare wires ring as resonant bandpass
    /// clusters where v1 is a featureless HP slope. Compare the mean band-RMS
    /// at the three cluster centres (3400/5100/7300 Hz) against the mean at the
    /// two between-cluster troughs (4200/6100 Hz), Q 8, over the early window
    /// [0, 60 ms] where the head-coupled wires are strongest relative to the
    /// flat dark-tail band. v1's smooth HP slope reads near-flat (~1.06), while
    /// v2 combs up to ~1.64 — well past the design's 1.35 floor. Same seed
    /// (fail-first: v1 has no cluster structure). Measured Q 8 matches the wire
    /// Q so the peaks/troughs resolve; a broader Q smears the contrast.
    #[test]
    fn dr4_snare_wire_clusters_are_resonant_v2() {
        let sr = 44100.0;
        let v1 = render_drum_kit(38, 110, 0.2, Kit::V1);
        let v2 = render_drum_kit(38, 110, 0.2, Kit::V2);
        let (a, b) = (0usize, (0.06 * sr) as usize);
        let comb = |s: &[f32]| {
            let seg = &s[a..b];
            let mean = |fs: &[f32]| {
                fs.iter()
                    .map(|&f| testutil::band_rms(seg, sr, f, 8.0))
                    .sum::<f32>()
                    / fs.len() as f32
            };
            mean(&[3400.0, 5100.0, 7300.0]) / mean(&[4200.0, 6100.0]).max(1e-9)
        };
        let (c1, c2) = (comb(&v1), comb(&v2));
        println!(
            "DR4 wire comb (mean-centre/mean-trough, [0,60ms] Q8): v1={c1:.3} v2={c2:.3} ratio={:.2}x",
            c2 / c1
        );
        assert!(
            c2 > 1.35 && c2 > 1.4 * c1,
            "v2 wire clusters not resonant vs v1 HP slope: v1={c1:.3} v2={c2:.3}"
        );
    }

    /// DR-O10 (level parity): the v2 snare's total energy over its [0, 0.6 s]
    /// life stays within ±2 dB of v1 — `WIRE_MAKEUP` compensates the BP-set
    /// bandwidth so opting a file into kit v2 is not a snare level jump.
    #[test]
    fn dr_o10_snare_v2_level_parity() {
        let v1 = render_drum_kit(38, 100, 0.6, Kit::V1);
        let v2 = render_drum_kit(38, 100, 0.6, Kit::V2);
        let (r1, r2) = (testutil::rms(&v1), testutil::rms(&v2));
        let db = 20.0 * (r2 / r1.max(1e-12)).log10();
        println!(
            "DR-O10 snare [0,0.6s] RMS: v1={r1:.5} v2={r2:.5} delta={db:+.2} dB (WIRE_MAKEUP={WIRE_MAKEUP})"
        );
        assert!(
            db.abs() <= 2.0,
            "snare v2 level {db:+.2} dB outside ±2 dB of v1 — trim WIRE_MAKEUP"
        );
    }

    /// DR4 differentiation: v1 renders keys 38 and 40 byte-identically (the
    /// arm never branched on the key), while v2 gives the electric snare (40)
    /// its own brighter wires — the first 38/40 distinction the kit has had.
    /// Also asserts the v2 snare diverges from v1 (the DR4 fix engaged).
    #[test]
    fn dr4_key40_differentiates_only_in_v2() {
        let s38_v1 = render_drum_kit(38, 100, 0.3, Kit::V1);
        let s40_v1 = render_drum_kit(40, 100, 0.3, Kit::V1);
        assert_eq!(s38_v1, s40_v1, "v1 must render keys 38 and 40 identically");
        let s38_v2 = render_drum_kit(38, 100, 0.3, Kit::V2);
        let s40_v2 = render_drum_kit(40, 100, 0.3, Kit::V2);
        assert!(
            s38_v2.iter().any(|&x| x.abs() > 1e-4),
            "v2 snare makes sound"
        );
        assert_ne!(
            s38_v2, s40_v2,
            "v2 must render electric snare (40) differently from 38"
        );
        assert_ne!(
            s38_v2, s38_v1,
            "v2 snare must diverge from v1 (DR4 engaged)"
        );
    }

    // ---- straggler-key oracles (58, 67/68, 71/72, 73/74, 78/79) ----

    /// The nine formerly-fallback keys share one kit-agnostic match arm, so
    /// every kit renders them identically — and audibly, finitely, and no
    /// longer as the generic ~1 kHz tick (which capped life at 0.15 s).
    #[test]
    fn straggler_keys_modeled_in_all_kits() {
        for key in [58u8, 67, 68, 71, 72, 73, 74, 78, 79] {
            let v1 = render_drum_kit(key, 100, 1.0, Kit::V1);
            let v2 = render_drum_kit(key, 100, 1.0, Kit::V2);
            let v3 = render_drum_kit(key, 100, 1.0, Kit::V3);
            assert!(v1.iter().all(|x| x.is_finite()), "key {key} non-finite");
            assert!(testutil::rms(&v1) > 1e-4, "key {key} inaudible");
            assert_eq!(v1, v2, "key {key} differs V1 vs V2");
            assert_eq!(v1, v3, "key {key} differs V1 vs V3");
        }
    }

    /// Broadband envelope flutter (coefficient of variation): rectify,
    /// 200 Hz-smooth, detrend off the slow (4 Hz) decay, and return std/mean
    /// over `[a, b]` s — high for a rattling voice, low for a smooth decay.
    fn env_cv(buf: &[f32], a: f32, b: f32) -> f32 {
        let sr = 44100.0f32;
        let (ia, ib) = ((a * sr) as usize, (b * sr) as usize);
        let mut fast = OnePole::lowpass(200.0, sr);
        let mut slow = OnePole::lowpass(4.0, sr);
        let mut env = Vec::with_capacity(buf.len());
        let mut detr = Vec::with_capacity(buf.len());
        for &x in buf {
            let e = fast.process(x.abs());
            detr.push((e - slow.process(e)) as f64);
            env.push(e as f64);
        }
        let mean = env[ia..ib].iter().sum::<f64>() / (ib - ia) as f64;
        let var = detr[ia..ib].iter().map(|&d| d * d).sum::<f64>() / (ib - ia) as f64;
        (var.sqrt() / mean.max(1e-12)) as f32
    }

    /// Key 58 vibraslap: an amplitude-fluttering rattle — envelope CV in the
    /// LIVE [0.05, 0.40] s window far above a shimmer-stripped build of the
    /// exact same tine/noise voice (same seed; differential, fail-first) —
    /// that decays over ~0.7 s.
    #[test]
    fn vibraslap_rattles_and_decays() {
        let sr = 44100.0;
        let vib = render_drum(58, 100, 1.0);
        // shimmer-stripped twin of the shipped 58 build (tables mirrored)
        let mut plain = Drum::new(
            sr,
            7,
            &[
                (1730.0, 0.45, 0.50, 0.0),
                (2470.0, 0.30, 0.42, 0.0),
                (3150.0, 0.18, 0.35, 0.0),
            ],
            &[(0.45, 0.45, Biquad::bandpass(2100.0, 1.0, sr))],
            0.85,
            0.45 * crate::dsp::vel_amp(100),
        );
        let mut smooth = vec![0f32; sr as usize];
        Voice::render(&mut plain, &mut smooth);
        let (cv_vib, cv_plain) = (env_cv(&vib, 0.05, 0.40), env_cv(&smooth, 0.05, 0.40));
        println!("vibraslap env CV={cv_vib:.3} vs shimmerless CV={cv_plain:.3}");
        assert!(
            cv_vib > 1.35 * cv_plain,
            "vibraslap does not rattle: CV {cv_vib} vs shimmerless {cv_plain}"
        );
        let life = last_audible(&vib);
        assert!((0.5..=0.9).contains(&life), "vibraslap life {life}");
        let early = testutil::rms(&vib[..(0.10 * sr) as usize]);
        let late = testutil::rms(sec_window(&vib, sr, 0.55, 0.70));
        assert!(
            late < 0.3 * early,
            "vibraslap does not decay: {late} vs {early}"
        );
    }

    /// Keys 67/68 agogos: two clear bell fundamentals in their design bands
    /// (hi ~1650 Hz, lo ~1220 Hz), hi > lo at fixed velocity, both with the
    /// 1.7x modal partial speaking and a fast metallic decay.
    #[test]
    fn agogo_pair_pitched_and_fast() {
        let sr = 44100.0;
        let hi = render_drum(67, 100, 0.6);
        let lo = render_drum(68, 100, 0.6);
        fn live(b: &[f32]) -> &[f32] {
            let sr = 44100.0;
            &b[(0.005 * sr) as usize..(0.15 * sr) as usize]
        }
        let f_hi = testutil::peak_locate(live(&hi), sr, 1400.0, 1900.0);
        let f_lo = testutil::peak_locate(live(&lo), sr, 1000.0, 1450.0);
        println!("agogo pitches: hi={f_hi:.0} Hz lo={f_lo:.0} Hz");
        assert!((f_hi - 1650.0).abs() < 150.0, "hi agogo at {f_hi} Hz");
        assert!((f_lo - 1220.0).abs() < 120.0, "lo agogo at {f_lo} Hz");
        assert!(
            f_hi > 1.25 * f_lo,
            "agogo pitch order/spread: {f_hi} vs {f_lo}"
        );
        // the 1.70x mode speaks on both bells
        for (buf, f0) in [(&hi, 1650.0f32), (&lo, 1220.0)] {
            let floor = testutil::mag_at(live(buf), sr, f0) * 0.05;
            let p = testutil::peak_locate(live(buf), sr, f0 * 1.70 * 0.92, f0 * 1.70 * 1.08);
            assert!(
                testutil::mag_at(live(buf), sr, p) > floor,
                "agogo 1.7x mode missing near {} Hz",
                f0 * 1.70
            );
        }
        // fast metallic decay: late energy a small fraction of the strike
        let early = testutil::rms(&hi[..(0.05 * sr) as usize]);
        let late = testutil::rms(sec_window(&hi, sr, 0.35, 0.50));
        assert!(
            late < 0.10 * early,
            "agogo rings too long: {late} vs {early}"
        );
    }

    /// Keys 71/72 whistles: both pitched in the ~2.35 kHz design band with
    /// breath noise around the tone; the short whistle dies < 0.25 s while
    /// the long one is still audible past 0.3 s.
    #[test]
    fn whistles_pitched_short_vs_long() {
        let sr = 44100.0;
        let short = render_drum(71, 100, 0.8);
        let long = render_drum(72, 100, 0.8);
        for (name, b) in [("short", &short), ("long", &long)] {
            let f = testutil::peak_locate(&b[..(0.10 * sr) as usize], sr, 1900.0, 2700.0);
            assert!((f - 2350.0).abs() < 200.0, "{name} whistle pitch {f} Hz");
        }
        let (ls, ll) = (last_audible(&short), last_audible(&long));
        println!("whistle lives: short={ls:.3}s long={ll:.3}s");
        assert!(ls < 0.25, "short whistle life {ls}");
        assert!(ll > 0.30, "long whistle life {ll}");
        // breathiness: real energy above 5 kHz early on (the hiss band)
        let hiss = testutil::hp_rms(&long[..(0.05 * sr) as usize], sr, 5000.0);
        assert!(hiss > 1e-3, "whistle breath noise missing: {hiss}");
    }

    /// Keys 73/74 guiros: the scrape is a periodic pulse train — the envelope
    /// autocorrelation peaks at the burst rate (short ~91 Hz, long ~63 Hz) —
    /// and the two strokes have clearly different lengths.
    #[test]
    fn guiros_notched_short_vs_long() {
        let short = render_drum(73, 100, 0.8);
        let long = render_drum(74, 100, 0.8);
        let sr = 44100.0;
        let (ps, rs) = testutil::env_autocorr_peak(
            &short[..(0.15 * sr) as usize],
            sr,
            1.0 / 130.0,
            1.0 / 60.0,
        );
        let (pl, rl) =
            testutil::env_autocorr_peak(&long[..(0.45 * sr) as usize], sr, 1.0 / 90.0, 1.0 / 40.0);
        println!(
            "guiro pulse trains: short peak={ps:.3} @{rs:.0} Hz, long peak={pl:.3} @{rl:.0} Hz"
        );
        assert!(ps > 0.2, "short guiro not notched: peak {ps}");
        assert!(pl > 0.2, "long guiro not notched: peak {pl}");
        assert!((75.0..=110.0).contains(&rs), "short guiro rate {rs} Hz");
        assert!((50.0..=75.0).contains(&rl), "long guiro rate {rl} Hz");
        let (ls, ll) = (last_audible(&short), last_audible(&long));
        assert!(ls < 0.25, "short guiro life {ls}");
        assert!(ll > 0.35, "long guiro life {ll}");
    }

    /// Keys 78/79 cuicas: pitched squeaks that GLIDE — the mute cuica's
    /// fundamental falls (early > late), the open cuica's rises (late >
    /// early), both inside the ~350-750 Hz design band, and the open squeak
    /// out-lives the mute one. Goertzel peak per window, never zero-crossings.
    #[test]
    fn cuicas_glide_opposite_ways() {
        let sr = 44100.0;
        let mute = render_drum(78, 100, 0.6);
        let open = render_drum(79, 100, 0.8);
        let peak = |b: &[f32], a: f32, z: f32, lo: f32, hi: f32| {
            testutil::peak_locate(&b[(a * sr) as usize..(z * sr) as usize], sr, lo, hi)
        };
        let m_early = peak(&mute, 0.0, 0.04, 400.0, 900.0);
        let m_late = peak(&mute, 0.08, 0.14, 250.0, 500.0);
        let o_early = peak(&open, 0.0, 0.06, 300.0, 550.0);
        let o_late = peak(&open, 0.25, 0.40, 550.0, 850.0);
        println!(
            "cuica glides: mute {m_early:.0}->{m_late:.0} Hz, open {o_early:.0}->{o_late:.0} Hz"
        );
        assert!(
            m_early > 1.15 * m_late,
            "mute cuica did not glide down: {m_early} -> {m_late}"
        );
        assert!(
            o_late > 1.15 * o_early,
            "open cuica did not glide up: {o_early} -> {o_late}"
        );
        let (lm, lo_life) = (last_audible(&mute), last_audible(&open));
        assert!(lm < 0.25, "mute cuica life {lm}");
        assert!(lo_life > 0.30, "open cuica life {lo_life}");
        assert!(lo_life > lm, "open cuica must out-live mute");
    }

    // =======================================================================
    // v0.12 — the ch-10 brush kit oracles (ported from the superseded v0.11
    // branch, 216da4a, and re-anchored on trunk's V3 world: unmapped brush
    // keys fall through to V3, not V2)
    // =======================================================================

    const SR12: f32 = 44100.0;

    fn seg(buf: &[f32], a: f32, b: f32) -> &[f32] {
        &buf[(a * SR12) as usize..(b * SR12) as usize]
    }

    fn db(a: f32, b: f32) -> f32 {
        20.0 * (a / b.max(1e-12)).log10()
    }

    /// RMS of `[a, z]` s of the WHOLE-buffer highpass — filter first, then
    /// window. Highpassing a segment sliced mid-ring reads the slice
    /// boundary as a step, and that filter transient buries the band being
    /// measured.
    fn hp_win(b: &[f32], corner: f32, a: f32, z: f32) -> f32 {
        let mut hp = Biquad::highpass(corner, 0.7, SR12);
        let f: Vec<f32> = b.iter().map(|&x| hp.process(x)).collect();
        testutil::rms(seg(&f, a, z))
    }

    /// KP-O1: a key no kit remaps (56 cowbell — kit-agnostic in `make`)
    /// renders byte-identically under all four kits.
    #[test]
    fn brush_kit_inert_for_untouched_keys() {
        let v1 = render_drum_kit(56, 100, 0.6, Kit::V1);
        let v2 = render_drum_kit(56, 100, 0.6, Kit::V2);
        let v3 = render_drum_kit(56, 100, 0.6, Kit::V3);
        let br = render_drum_kit(56, 100, 0.6, Kit::Brush);
        assert!(v1.iter().any(|&x| x.abs() > 1e-4), "cowbell makes sound");
        assert_eq!(v1, v2, "cowbell 56 must not branch on kit (V1 vs V2)");
        assert_eq!(v2, v3, "cowbell 56 must not branch on kit (V2 vs V3)");
        assert_eq!(v3, br, "cowbell 56 must not branch on kit (V3 vs Brush)");
    }

    /// KP-O2 (pins the V3 fall-through, the `== Kit::V3` guard trap): unmapped
    /// brush keys fall through to the V3 voices — the crash (49, a V3 metal
    /// plate), the ride (51) and a tom (41) render byte-equal to V3 and differ
    /// from V1.
    #[test]
    fn brush_falls_back_to_v3() {
        for key in [49u8, 51, 41] {
            let v1 = render_drum_kit(key, 100, 1.0, Kit::V1);
            let v3 = render_drum_kit(key, 100, 1.0, Kit::V3);
            let br = render_drum_kit(key, 100, 1.0, Kit::Brush);
            assert_eq!(br, v3, "brush key {key} must fall back to the V3 voice");
            assert_ne!(br, v1, "brush key {key} wrongly renders the V1 voice");
        }
    }

    /// BR-O1: no wire spike — the brush tap carries far less of the V3
    /// snare's wire-cluster HF (fraction above 4.5 kHz), because nylon
    /// strands cannot crack the wires.
    #[test]
    fn brush_tap_no_wire_spike() {
        let hf_frac = |b: &[f32]| {
            let s = &b[..(0.15 * SR12) as usize];
            testutil::hp_rms(s, SR12, 4500.0) / testutil::rms(s).max(1e-12)
        };
        let brush = hf_frac(&render_drum_kit(38, 100, 0.3, Kit::Brush));
        let v3 = hf_frac(&render_drum_kit(38, 100, 0.3, Kit::V3));
        println!("BR-O1 hf fraction: brush {brush:.4} vs v3 {v3:.4}");
        assert!(
            brush <= 0.5 * v3,
            "brush tap still spikes the wires: {brush:.4} vs v3 {v3:.4}"
        );
    }

    /// BR-O2 (level knob BRUSH_TAP_GAIN): the tap sits with the V1 snare at
    /// the same velocity (±2 dB over the hit).
    #[test]
    fn brush_tap_level_vs_v1_snare() {
        let tap = render_drum_kit(38, 100, 0.25, Kit::Brush);
        let sn = render_drum_kit(38, 100, 0.25, Kit::V1);
        let d = db(
            testutil::rms(&tap[..(0.20 * SR12) as usize]),
            testutil::rms(&sn[..(0.20 * SR12) as usize]),
        );
        println!("BR-O2 tap vs v1 snare level: {d:+.2} dB");
        assert!(
            d.abs() <= 2.0,
            "brush tap level {d:+.2} dB off the v1 snare"
        );
    }

    /// BR-O3 structural seam: the tap keeps the SNARE_TONES head frequencies
    /// and amplitudes but shortens every T60 — same head, softer strike.
    #[test]
    fn brush_tap_tones_structural_seam() {
        for (i, (bt, st)) in BRUSH_TAP_TONES.iter().zip(SNARE_TONES.iter()).enumerate() {
            assert_eq!(bt.0, st.0, "tone {i}: head frequency changed");
            assert!(
                bt.2 < st.2,
                "tone {i}: brush T60 {} not shorter than snare {}",
                bt.2,
                st.2
            );
        }
    }

    /// BR-O4,5: the slap is the accented tap (louder at equal velocity), and
    /// its strands land TWICE — the 12 ms re-excitation burst lifts the
    /// 10-22 ms window relative to the first contact, where the tap's noise
    /// only decays.
    #[test]
    fn brush_slap_accent_and_double_contact() {
        let slap = render_drum_kit(39, 100, 0.3, Kit::Brush);
        let tap = render_drum_kit(38, 100, 0.3, Kit::Brush);
        let d = db(
            testutil::rms(&slap[..(0.20 * SR12) as usize]),
            testutil::rms(&tap[..(0.20 * SR12) as usize]),
        );
        println!("BR-O4 slap vs tap level: {d:+.2} dB");
        assert!(d > 0.4, "slap not an accent: {d:+.2} dB vs tap");
        let second_contact =
            |b: &[f32]| hp_win(b, 800.0, 0.013, 0.022) / hp_win(b, 800.0, 0.004, 0.011).max(1e-12);
        let rs = second_contact(&slap);
        let rt = second_contact(&tap);
        println!("BR-O5 second-contact ratio: slap {rs:.3} vs tap {rt:.3}");
        assert!(
            rs >= 1.2 * rt,
            "slap second contact missing: {rs:.3} vs tap {rt:.3}"
        );
    }

    /// SW-O1: the swirl SWELLS, it does not hit — the first 30 ms stays well
    /// under the eventual peak, which lands only after ≥50 ms.
    #[test]
    fn brush_swirl_swells_not_hits() {
        let b = render_drum_kit(40, 100, 1.0, Kit::Brush);
        let peak = b.iter().fold(0f32, |m, &x| m.max(x.abs()));
        let early = b[..(0.03 * SR12) as usize]
            .iter()
            .fold(0f32, |m, &x| m.max(x.abs()));
        let peak_t = b.iter().position(|&x| x.abs() >= 0.999 * peak).unwrap_or(0) as f32 / SR12;
        println!("SW-O1 early peak {early:.4} vs peak {peak:.4} at {peak_t:.3} s");
        assert!(
            early <= 0.4 * peak,
            "swirl hits instead of swelling: {early:.4} vs {peak:.4}"
        );
        assert!(peak_t >= 0.05, "swirl peaks too early: {peak_t:.3} s");
    }

    /// SW-O2: the stir SUSTAINS across its stroke (the mid window holds up
    /// against the early one), and the third band's 0.45 s onset is the
    /// return sweep — late HF well above the first stroke's.
    #[test]
    fn brush_swirl_sustain_and_return_sweep() {
        let b = render_drum_kit(40, 100, 1.0, Kit::Brush);
        let sustain = testutil::rms(seg(&b, 0.45, 0.70)) / testutil::rms(seg(&b, 0.10, 0.35));
        println!("SW-O2 sustain ratio {sustain:.3}");
        assert!(sustain >= 0.5, "swirl dies mid-stroke: {sustain:.3}");
        let ret = hp_win(&b, 3700.0, 0.50, 0.70) / hp_win(&b, 3700.0, 0.10, 0.30).max(1e-12);
        println!("SW-O2 return-sweep HF ratio {ret:.3}");
        assert!(ret >= 1.3, "no return sweep: late/early HF {ret:.3}");
    }

    /// SW-O3 (differential): the 5 Hz stir AM is REAL — the shipping swirl's
    /// envelope carries far more 5 Hz than the same drum without the shimmer.
    #[test]
    fn brush_swirl_slow_am_differential() {
        let am5 = |mut v: Box<dyn Voice>| {
            let mut b = vec![0f32; (1.0 * SR12) as usize];
            v.render(&mut b);
            let mut lp = OnePole::lowpass(25.0, SR12);
            let env: Vec<f32> = b.iter().map(|&x| lp.process(x.abs())).collect();
            let s = &env[(0.1 * SR12) as usize..(0.9 * SR12) as usize];
            let mean = s.iter().sum::<f32>() / s.len() as f32;
            let d: Vec<f32> = s.iter().map(|&x| x - mean).collect();
            testutil::mag_at(&d, SR12, BRUSH_SWIRL_AM_RATE_HZ) / mean.max(1e-12)
        };
        let with = am5(brush_swirl(100, SR12, 7).unwrap());
        let without = am5(Box::new(brush_swirl_drum(100, SR12, 7)));
        println!("SW-O3 5 Hz AM: with {with:.4} vs without {without:.4}");
        // the clone's staggered band swells leak a ~0.55 floor into the 5 Hz
        // bin (three onset lumps across 0.85 s), so the differential is a
        // ratio over that floor plus an absolute depth check
        assert!(with >= 0.75, "stir AM too shallow: {with:.4}");
        assert!(
            with >= 1.35 * without,
            "stir AM missing: {with:.4} vs {without:.4}"
        );
    }

    /// SW-O4: the swirl seats in the brush's mid-high "shhh" band — spectral
    /// centroid inside 1.8-4.5 kHz, not a full-band cymbal wash.
    #[test]
    fn brush_swirl_spectral_seat() {
        let b = render_drum_kit(40, 100, 1.0, Kit::Brush);
        let c = testutil::centroid(seg(&b, 0.05, 0.85), SR12);
        println!("SW-O4 swirl centroid {c:.0} Hz");
        assert!(
            (1800.0..=4500.0).contains(&c),
            "swirl centroid {c:.0} Hz outside its seat"
        );
    }

    /// BH-O1,2 (level knob BRUSH_CLOSED_HAT_GAIN): the brush closed hat is
    /// DARKER than the V1 hat (centroid ≤0.85x) at matched level (±2 dB).
    /// (42|44 never branch on kit in `make`, so V1 == V3 here — the stick
    /// anchor is the shipped hat.)
    #[test]
    fn brush_closed_hat_darker_and_level() {
        let br = render_drum_kit(42, 100, 0.16, Kit::Brush);
        let v1 = render_drum_kit(42, 100, 0.16, Kit::V1);
        let cb = testutil::centroid(&br[..(0.14 * SR12) as usize], SR12);
        let c1 = testutil::centroid(&v1[..(0.14 * SR12) as usize], SR12);
        println!("BH-O1 closed-hat centroid: brush {cb:.0} vs v1 {c1:.0} Hz");
        assert!(
            cb <= 0.85 * c1,
            "brush closed hat not darker: {cb:.0} vs {c1:.0}"
        );
        let d = db(
            testutil::rms(&br[..(0.14 * SR12) as usize]),
            testutil::rms(&v1[..(0.14 * SR12) as usize]),
        );
        println!("BH-O2 closed-hat level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "brush closed hat level {d:+.2} dB off v1");
    }

    /// BH-O3,4,5 (level knob BRUSH_OPEN_HAT_GAIN): the brush open hat keeps
    /// the DR3 anatomy (the 45 Hz sizzle wobble reads on its HF envelope)
    /// but darker than the V3 open hat (centroid ≤0.85x) at matched level.
    #[test]
    fn brush_open_hat_darker_dr3_and_level() {
        let br = render_drum_kit(46, 100, 0.95, Kit::Brush);
        let v3 = render_drum_kit(46, 100, 0.95, Kit::V3);
        let cb = testutil::centroid(seg(&br, 0.0, 0.9), SR12);
        let c3 = testutil::centroid(seg(&v3, 0.0, 0.9), SR12);
        println!("BH-O3 open-hat centroid: brush {cb:.0} vs v3 {c3:.0} Hz");
        assert!(
            cb <= 0.85 * c3,
            "brush open hat not darker: {cb:.0} vs {c3:.0}"
        );
        // DR3 sizzle wobble: `Shimmer` is lowpassed-NOISE AM (no 45 Hz
        // Goertzel line exists) — so the oracle is a differential: the
        // shipping hat's HF-envelope variability well above the identical
        // spec with the shimmer stripped.
        // flatten by DIVISION (e / slow(e)) so the tail's decay and shrinking
        // mean don't dominate — the flattened envelope of an unmodulated wash
        // is near-constant; the wobble's AM survives the division
        let hf_env_cv = |mut v: Box<dyn Voice>| {
            let mut b = vec![0f32; (0.95 * SR12) as usize];
            v.render(&mut b);
            let mut hp = Biquad::highpass(3000.0, 0.7, SR12);
            let mut lp = OnePole::lowpass(90.0, SR12);
            let mut slow = OnePole::lowpass(3.0, SR12);
            let flat: Vec<f64> = b
                .iter()
                .map(|&x| {
                    let e = lp.process(hp.process(x).abs());
                    (e / slow.process(e).max(1e-9)) as f64
                })
                .collect();
            let s = &flat[(0.1 * SR12) as usize..(0.8 * SR12) as usize];
            let mean = s.iter().sum::<f64>() / s.len() as f64;
            let var = s.iter().map(|&x| (x - mean) * (x - mean)).sum::<f64>() / s.len() as f64;
            var.sqrt() / mean.max(1e-12)
        };
        let with = hf_env_cv(make(46, 100, SR12, 7, Kit::Brush, false).unwrap());
        let mut spec = brush_open_hat_spec();
        spec.shimmer = None;
        let without = hf_env_cv(cymbal(&spec, SR12, 7, 100).unwrap());
        println!("BH-O4 sizzle wobble CV: with {with:.4} vs without {without:.4}");
        assert!(
            with >= 1.5 * without,
            "DR3 sizzle wobble missing: {with:.4} vs {without:.4}"
        );
        let d = db(
            testutil::rms(seg(&br, 0.0, 0.9)),
            testutil::rms(seg(&v3, 0.0, 0.9)),
        );
        println!("BH-O5 open-hat level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "brush open hat level {d:+.2} dB off v3");
    }

    /// BR-O6 (level knob BRUSH_RIM_GAIN): the brush rim knock is WOODIER than
    /// the stick side-stick (materially lower centroid) at matched level.
    #[test]
    fn brush_rim_woodier_and_level() {
        let br = render_drum_kit(37, 100, 0.12, Kit::Brush);
        let v1 = render_drum_kit(37, 100, 0.12, Kit::V1);
        let cb = testutil::centroid(&br[..(0.08 * SR12) as usize], SR12);
        let c1 = testutil::centroid(&v1[..(0.08 * SR12) as usize], SR12);
        println!("BR-O6 rim centroid: brush {cb:.0} vs v1 {c1:.0} Hz");
        assert!(cb <= 0.8 * c1, "brush rim not woodier: {cb:.0} vs {c1:.0}");
        let d = db(
            testutil::rms(&br[..(0.10 * SR12) as usize]),
            testutil::rms(&v1[..(0.10 * SR12) as usize]),
        );
        println!("BR-O6 rim level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "brush rim level {d:+.2} dB off v1");
    }

    /// BK-O1,2,3 (level knob BRUSH_KICK_GAIN): the brush kick keeps the V1
    /// kick's sub drop intact (86 Hz band within ±2 dB) under a much softer
    /// beater (HF fraction well below V1's), at matched overall level.
    #[test]
    fn brush_kick_soft_beater_sub_intact() {
        let br = render_drum_kit(36, 100, 0.6, Kit::Brush);
        let v1 = render_drum_kit(36, 100, 0.6, Kit::V1);
        let sub = db(
            testutil::band_rms(seg(&br, 0.0, 0.5), SR12, 86.0, 1.0),
            testutil::band_rms(seg(&v1, 0.0, 0.5), SR12, 86.0, 1.0),
        );
        println!("BK-O1 sub band delta: {sub:+.2} dB");
        assert!(sub.abs() <= 2.0, "brush kick sub drifted: {sub:+.2} dB");
        // filter first, window [1, 30] ms — inside the 5 ms-T60 beater
        // noise's life. The tone stack's t=0 onset step is identical in both
        // kits and would floor the ratio at ~0.58; the HP-2k transient it
        // excites is gone within ~0.1 ms, so a 1 ms skip clears it.
        let hf_frac = |b: &[f32]| {
            hp_win(b, 2000.0, 0.001, 0.03) / testutil::rms(&b[..(0.03 * SR12) as usize]).max(1e-12)
        };
        let hb = hf_frac(&br);
        let h1 = hf_frac(&v1);
        println!("BK-O2 beater HF fraction: brush {hb:.4} vs v1 {h1:.4}");
        assert!(
            hb <= 0.5 * h1,
            "brush beater not softer: {hb:.4} vs {h1:.4}"
        );
        let d = db(
            testutil::rms(seg(&br, 0.0, 0.5)),
            testutil::rms(seg(&v1, 0.0, 0.5)),
        );
        println!("BK-O3 kick level: {d:+.2} dB");
        assert!(d.abs() <= 2.0, "brush kick level {d:+.2} dB off v1");
    }

    /// Post-calibration byte-exact freeze of the brush kit (same contract as
    /// `v1_drum_render_is_frozen`): any shared-path edit that shifts a brush
    /// voice below the level oracles' ±2 dB trip-wire fails loudly here.
    #[test]
    fn brush_render_is_frozen() {
        // (key, fingerprint). Kick, tap, slap, swirl, closed hat, open hat.
        let cases: [(u8, u64); 6] = [
            (36, 0xf4a96bb9e49b508d),
            (38, 0xf0f2e9c7eafc3efc),
            (39, 0xcbe847e0064d5592),
            (40, 0xd7530d0e9024d083),
            (42, 0xe13957c3b7691ac5),
            (46, 0x34b8c0ef2dba6183),
        ];
        for (key, want) in cases {
            let got = render_fingerprint(&render_drum_kit(key, 100, 1.0, Kit::Brush));
            assert_eq!(got, want, "brush render of key {key} drifted: {got:#018x}");
        }
    }
}
