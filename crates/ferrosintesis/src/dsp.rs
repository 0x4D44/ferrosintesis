//! Small DSP building blocks: oscillators, envelopes, filters, noise.

use std::f32::consts::PI;

/// xorshift32 — deterministic, seedable noise source.
pub struct Rng(u32);

impl Rng {
    pub fn new(seed: u32) -> Self {
        Rng(seed.max(1))
    }

    pub fn next_u32(&mut self) -> u32 {
        let mut x = self.0;
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        self.0 = x;
        x
    }

    /// White noise in [-1, 1).
    pub fn white(&mut self) -> f32 {
        (self.next_u32() as f32 / u32::MAX as f32) * 2.0 - 1.0
    }
}

/// Sine oscillator as a 2-D rotation — one complex multiply per sample,
/// no `sin()` calls in the inner loop. Ideal for big additive banks.
#[derive(Clone, Copy)]
pub struct Sine {
    re: f32,
    im: f32,
    cr: f32,
    ci: f32,
}

impl Sine {
    pub fn new(freq: f32, sr: f32, phase: f32) -> Self {
        let w = 2.0 * PI * freq / sr;
        Sine {
            re: phase.cos(),
            im: phase.sin(),
            cr: w.cos(),
            ci: w.sin(),
        }
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        let (re, im) = (self.re, self.im);
        self.re = re * self.cr - im * self.ci;
        self.im = re * self.ci + im * self.cr;
        self.im
    }

    /// Retune in place (keeps phase continuity).
    pub fn set_freq(&mut self, freq: f32, sr: f32) {
        let w = 2.0 * PI * freq / sr;
        self.cr = w.cos();
        self.ci = w.sin();
    }
}

/// Two-operator FM (strictly: phase-modulation, the DX convention) pair —
/// one modulator phase-modulating one carrier (round-3 U5, the GM5 DX-style
/// electric piano: a DX EP *is* FM, so it is modeled as FM rather than
/// faked additively). Explicit phase accumulators — the rotating-phasor
/// [`Sine`] cannot be phase-modulated. Two sines per sample: fine for an
/// offline per-voice oscillator.
pub struct FmPair {
    car: f32,
    md: f32,
    car_dw: f32,
    md_dw: f32,
    ratio: f32,
}

impl FmPair {
    pub fn new(freq: f32, ratio: f32, sr: f32) -> Self {
        FmPair {
            car: 0.0,
            md: 0.0,
            car_dw: freq / sr,
            md_dw: freq * ratio / sr,
            ratio,
        }
    }

    /// Retune in place (keeps both phases — bend-continuous).
    pub fn set_freq(&mut self, freq: f32, sr: f32) {
        self.car_dw = freq / sr;
        self.md_dw = freq * self.ratio / sr;
    }

    /// Next sample with modulation `index` (radians of carrier-phase swing).
    #[inline]
    pub fn next(&mut self, index: f32) -> f32 {
        let m = (core::f32::consts::TAU * self.md).sin();
        let y = (core::f32::consts::TAU * self.car + index * m).sin();
        self.car += self.car_dw;
        if self.car >= 1.0 {
            self.car -= 1.0;
        }
        self.md += self.md_dw;
        if self.md >= 1.0 {
            self.md -= 1.0;
        }
        y
    }
}

/// polyBLEP residual for a unit-amplitude step at a phase discontinuity —
/// corrects the samples just before and after the wrap. Shared by the saw
/// and pulse oscillators.
#[inline]
fn polyblep(t: f32, dt: f32) -> f32 {
    if t < dt {
        let x = t / dt;
        x + x - x * x - 1.0
    } else if t > 1.0 - dt {
        let x = (t - 1.0) / dt;
        x * x + x + x + 1.0
    } else {
        0.0
    }
}

/// Band-limited sawtooth (polyBLEP).
pub struct BlepSaw {
    phase: f32,
    inc: f32,
}

impl BlepSaw {
    pub fn new(freq: f32, sr: f32, phase: f32) -> Self {
        BlepSaw {
            phase: phase.rem_euclid(1.0),
            inc: freq / sr,
        }
    }

    pub fn set_freq(&mut self, freq: f32, sr: f32) {
        self.inc = freq / sr;
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        let out = 2.0 * self.phase - 1.0 - polyblep(self.phase, self.inc);
        self.phase += self.inc;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
        }
        out
    }
}

/// Band-limited pulse / square (polyBLEP at both edges). `duty` in (0, 1);
/// 0.5 is a square, whose even harmonics cancel. No DC correction for
/// duty != 0.5 — only 0.5 is used today (duty is clamped to a safe range).
pub struct BlepPulse {
    phase: f32,
    inc: f32,
    duty: f32,
}

impl BlepPulse {
    pub fn new(freq: f32, sr: f32, phase: f32, duty: f32) -> Self {
        BlepPulse {
            phase: phase.rem_euclid(1.0),
            inc: freq / sr,
            duty: duty.clamp(0.05, 0.95),
        }
    }

    pub fn set_freq(&mut self, freq: f32, sr: f32) {
        self.inc = freq / sr;
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        // +1 for the first `duty` of the cycle, -1 after; polyBLEP added at the
        // rising edge (phase 0) and subtracted at the falling edge (phase `duty`).
        let mut out = if self.phase < self.duty { 1.0 } else { -1.0 };
        out += polyblep(self.phase, self.inc);
        out -= polyblep((self.phase - self.duty).rem_euclid(1.0), self.inc);
        self.phase += self.inc;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
        }
        out
    }
}

/// Clamp a pulse duty cycle so the two polyBLEP step corrections (each `2·inc`
/// wide) cannot overlap — a safety net at extreme `f/sr` only (RD1 §3.2).
/// Degrades to an exact square when even that is impossible (`inc ≥ 0.25`).
#[inline]
fn guard_width(width: f32, inc: f32) -> f32 {
    let lo = 2.0 * inc;
    let hi = 1.0 - 2.0 * inc;
    if lo >= hi {
        0.5
    } else {
        width.clamp(lo, hi)
    }
}

/// Band-limited rectangular pulse (polyBLEP), duty cycle `width` ∈ (0, 1). The
/// reed source. Distinct from `BlepPulse`: this is **zero-DC for ANY width** and
/// scaled as a difference of two saws, where `BlepPulse` is a ±1 square used
/// only at duty 0.5. Zero-DC by construction: the signal sits at level `w−1` for
/// the fraction `w` of the period and at `+w` for the remaining `1−w`, so the
/// two areas cancel (mean = 0) for any width. Only the harmonic MAGNITUDE
/// spectrum is load-bearing downstream (tanh is odd; every reed oracle measures
/// magnitudes), so the sign/phase of the two levels are immaterial. The Fourier
/// amplitude of harmonic n is `2·|sin(πnw)|/(πn)`: width 0.5 nulls all evens (an
/// exact square — the clarinet's hollow odd spectrum), narrow widths are
/// even-rich (a double reed's short pressure pulse).
pub struct ReedPulse {
    phase: f32,
    inc: f32,
    width: f32,
}

impl ReedPulse {
    pub fn new(freq: f32, sr: f32, phase: f32, width: f32) -> Self {
        let inc = freq / sr;
        ReedPulse {
            phase: phase.rem_euclid(1.0),
            inc,
            width: guard_width(width, inc),
        }
    }

    /// Retune in place (phase-continuous); re-applies the width guard against
    /// the new `f/sr`. Width itself is fixed per note (chosen at spawn).
    pub fn set_freq(&mut self, freq: f32, sr: f32) {
        self.inc = freq / sr;
        self.width = guard_width(self.width, self.inc);
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        // difference of two naive saws, the second shifted by (1 − width), each
        // with its own polyBLEP correction (discontinuities at t=0 and t=width)
        let p2 = (self.phase + 1.0 - self.width).rem_euclid(1.0);
        let out = 0.5
            * ((2.0 * self.phase - 1.0 - polyblep(self.phase, self.inc))
                - (2.0 * p2 - 1.0 - polyblep(p2, self.inc)));
        self.phase += self.inc;
        if self.phase >= 1.0 {
            self.phase -= 1.0;
        }
        out
    }
}

/// One-pole lowpass: z += a * (x - z).
#[derive(Clone, Copy)]
pub struct OnePole {
    a: f32,
    z: f32,
}

impl OnePole {
    /// |H(f)| of a one-pole lowpass designed by `OnePole::lowpass(cutoff, sr)`.
    ///
    /// Closed form, shared by the KS sustainer's headroom math and the
    /// coupled-loop margin oracle so test and shipped code cannot drift apart.
    pub(crate) fn lowpass_mag(cutoff: f32, f: f32, sr: f32) -> f32 {
        let a = 1.0 - (-2.0 * core::f32::consts::PI * (cutoff / sr).min(0.49)).exp();
        let b = 1.0 - a;
        let w = 2.0 * core::f32::consts::PI * f / sr;
        a / (1.0 - 2.0 * b * w.cos() + b * b).sqrt()
    }

    pub fn lowpass(cutoff: f32, sr: f32) -> Self {
        let a = 1.0 - (-2.0 * PI * (cutoff / sr).min(0.49)).exp();
        OnePole { a, z: 0.0 }
    }

    /// Move the cutoff without touching the state (no clicks).
    pub fn set_cutoff(&mut self, cutoff: f32, sr: f32) {
        self.a = 1.0 - (-2.0 * PI * (cutoff / sr).min(0.49)).exp();
    }

    #[inline]
    pub fn process(&mut self, x: f32) -> f32 {
        self.z += self.a * (x - self.z);
        self.z
    }
}

/// Interpolating delay line (power-of-two ring buffer).
pub struct DelayLine {
    buf: Vec<f32>,
    mask: usize,
    idx: usize,
}

impl DelayLine {
    pub fn new(max_samples: usize) -> Self {
        let size = (max_samples + 2).next_power_of_two();
        DelayLine {
            buf: vec![0.0; size],
            mask: size - 1,
            idx: 0,
        }
    }

    #[inline]
    pub fn push(&mut self, x: f32) {
        self.idx = (self.idx + 1) & self.mask;
        self.buf[self.idx] = x;
    }

    /// Scale the whole line (the tremolo pick-catch): g ≤ 1 only removes
    /// energy, so loop passivity is trivially preserved.
    pub fn scale(&mut self, g: f32) {
        for x in &mut self.buf {
            *x *= g;
        }
    }

    /// Read `delay` samples back (linear interpolation), before the next push.
    #[inline]
    pub fn tap(&self, delay: f32) -> f32 {
        let d = delay.max(1.0);
        let i = d.floor() as usize;
        let frac = d - i as f32;
        let a = self.buf[(self.idx + self.buf.len() - i) & self.mask];
        let b = self.buf[(self.idx + self.buf.len() - i - 1) & self.mask];
        a + (b - a) * frac
    }

    /// K1: 4-point cubic-Lagrange read, used ONLY inside `KsLoop::tick` —
    /// linear interpolation lowpasses the loop at fractional delays and dulls
    /// short treble strings. Evaluated strictly in the central interval
    /// (fractional offset between the two middle stencil points), where
    /// Lagrange is passive (|H| ≤ 1) — the correct stability basis, not
    /// "FIR → safe" (V4/DSP-1). Buses keep the linear `tap`.
    #[inline]
    pub fn tap_cubic(&self, delay: f32) -> f32 {
        let d = delay.max(2.0);
        let i = d.floor() as usize;
        let fr = d - i as f32;
        let at = |k: usize| self.buf[(self.idx + self.buf.len() - k) & self.mask];
        // point lies between at(i) and at(i+1) in delay-space; stencil {-1,0,1,2}
        cubic4(at(i - 1), at(i), at(i + 1), at(i + 2), fr)
    }
}

/// 4-point cubic-Lagrange interpolation on the stencil {-1, 0, 1, 2}, evaluated
/// at fractional offset `fr ∈ [0, 1)` measured from `p0` toward `p1` — the value
/// at `fr` on the cubic through (`pm1`, `p0`, `p1`, `p2`).
///
/// The kernel behind [`DelayLine::tap_cubic`], and the read used by the sampler's
/// fractional sample players (LA layer, drums, gong, clavinet, looped drone) in
/// place of 2-point linear interpolation: linear both dulls the treble and folds
/// interpolation images back as aliasing when a sample is pitched up (step > 1),
/// which is exactly what the LA layer does across its zone splits (up to step
/// 2.0). Lagrange evaluated on the central interval is passive (|H| ≤ 1).
#[inline]
pub fn cubic4(pm1: f32, p0: f32, p1: f32, p2: f32, fr: f32) -> f32 {
    let w_m1 = -fr * (fr - 1.0) * (fr - 2.0) / 6.0;
    let w_0 = (fr + 1.0) * (fr - 1.0) * (fr - 2.0) / 2.0;
    let w_1 = -(fr + 1.0) * fr * (fr - 2.0) / 2.0;
    let w_2 = (fr + 1.0) * fr * (fr - 1.0) / 6.0;
    w_m1 * pm1 + w_0 * p0 + w_1 * p1 + w_2 * p2
}

/// A slow random pitch walk — the drift of a human player. `next()` is meant
/// to be called at control rate (once per ~16 samples).
pub struct Drift {
    rng: Rng,
    value: f32,
    target: f32,
    depth: f32,
    hold: u32,
    count: u32,
}

impl Drift {
    pub fn new(seed: u32, depth: f32, hold_ticks: u32) -> Self {
        Drift {
            rng: Rng::new(seed),
            value: 0.0,
            target: 0.0,
            depth,
            hold: hold_ticks.max(1),
            count: 0,
        }
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        if self.count == 0 {
            self.target = self.rng.white() * self.depth;
            self.count = self.hold;
        }
        self.count -= 1;
        self.value += 0.015 * (self.target - self.value);
        self.value
    }
}

/// RBJ biquad.
#[derive(Clone, Copy)]
pub struct Biquad {
    b0: f32,
    b1: f32,
    b2: f32,
    a1: f32,
    a2: f32,
    x1: f32,
    x2: f32,
    y1: f32,
    y2: f32,
}

impl Biquad {
    fn from_coeffs(b0: f32, b1: f32, b2: f32, a0: f32, a1: f32, a2: f32) -> Self {
        Biquad {
            b0: b0 / a0,
            b1: b1 / a0,
            b2: b2 / a0,
            a1: a1 / a0,
            a2: a2 / a0,
            x1: 0.0,
            x2: 0.0,
            y1: 0.0,
            y2: 0.0,
        }
    }

    pub fn lowpass(freq: f32, q: f32, sr: f32) -> Self {
        let w = 2.0 * PI * (freq / sr).min(0.49);
        let (sw, cw) = (w.sin(), w.cos());
        let alpha = sw / (2.0 * q);
        Self::from_coeffs(
            (1.0 - cw) / 2.0,
            1.0 - cw,
            (1.0 - cw) / 2.0,
            1.0 + alpha,
            -2.0 * cw,
            1.0 - alpha,
        )
    }

    /// Retune as a lowpass in place, preserving filter state (no clicks).
    pub fn retune_lowpass(&mut self, freq: f32, q: f32, sr: f32) {
        let fresh = Self::lowpass(freq, q, sr);
        self.b0 = fresh.b0;
        self.b1 = fresh.b1;
        self.b2 = fresh.b2;
        self.a1 = fresh.a1;
        self.a2 = fresh.a2;
    }

    pub fn highpass(freq: f32, q: f32, sr: f32) -> Self {
        let w = 2.0 * PI * (freq / sr).min(0.49);
        let (sw, cw) = (w.sin(), w.cos());
        let alpha = sw / (2.0 * q);
        Self::from_coeffs(
            (1.0 + cw) / 2.0,
            -(1.0 + cw),
            (1.0 + cw) / 2.0,
            1.0 + alpha,
            -2.0 * cw,
            1.0 - alpha,
        )
    }

    /// Retune as a highpass in place, preserving filter state (no clicks).
    /// The reed rasp stage (RD10) tracks its sub-fundamental guard at 0.55·f0
    /// from this at CTRL rate.
    pub fn retune_highpass(&mut self, freq: f32, q: f32, sr: f32) {
        let fresh = Self::highpass(freq, q, sr);
        self.b0 = fresh.b0;
        self.b1 = fresh.b1;
        self.b2 = fresh.b2;
        self.a1 = fresh.a1;
        self.a2 = fresh.a2;
    }

    /// Constant-peak-gain bandpass.
    pub fn bandpass(freq: f32, q: f32, sr: f32) -> Self {
        let w = 2.0 * PI * (freq / sr).min(0.49);
        let (sw, cw) = (w.sin(), w.cos());
        let alpha = sw / (2.0 * q);
        Self::from_coeffs(alpha, 0.0, -alpha, 1.0 + alpha, -2.0 * cw, 1.0 - alpha)
    }

    /// Retune as a bandpass in place, preserving filter state (no clicks).
    pub fn retune_bandpass(&mut self, freq: f32, q: f32, sr: f32) {
        let fresh = Self::bandpass(freq, q, sr);
        self.b0 = fresh.b0;
        self.b1 = fresh.b1;
        self.b2 = fresh.b2;
        self.a1 = fresh.a1;
        self.a2 = fresh.a2;
    }

    /// Retune as a peak EQ in place, preserving filter state (no clicks).
    /// The reed honk (RD2) redesigns its formant slots from this at CTRL
    /// rate — gain moves with blowing pressure, centre and Q never do.
    pub fn retune_peak(&mut self, freq: f32, q: f32, gain_db: f32, sr: f32) {
        let fresh = Self::peak(freq, q, gain_db, sr);
        self.b0 = fresh.b0;
        self.b1 = fresh.b1;
        self.b2 = fresh.b2;
        self.a1 = fresh.a1;
        self.a2 = fresh.a2;
    }

    pub fn peak(freq: f32, q: f32, gain_db: f32, sr: f32) -> Self {
        let a = 10f32.powf(gain_db / 40.0);
        let w = 2.0 * PI * (freq / sr).min(0.49);
        let (sw, cw) = (w.sin(), w.cos());
        let alpha = sw / (2.0 * q);
        Self::from_coeffs(
            1.0 + alpha * a,
            -2.0 * cw,
            1.0 - alpha * a,
            1.0 + alpha / a,
            -2.0 * cw,
            1.0 - alpha / a,
        )
    }

    #[inline]
    pub fn process(&mut self, x: f32) -> f32 {
        let y = self.b0 * x + self.b1 * self.x1 + self.b2 * self.x2
            - self.a1 * self.y1
            - self.a2 * self.y2;
        self.x2 = self.x1;
        self.x1 = x;
        self.y2 = self.y1;
        self.y1 = y;
        y
    }
}

/// Exponential ADSR. `next()` returns the current level.
pub struct Adsr {
    stage: u8, // 0 attack, 1 decay, 2 sustain, 3 release, 4 dead
    level: f32,
    a: f32,
    d: f32,
    s: f32,
    r: f32,
}

fn coeff(seconds: f32, sr: f32) -> f32 {
    1.0 - (-1.0 / (seconds.max(1e-4) * sr)).exp()
}

impl Adsr {
    pub fn new(attack: f32, decay: f32, sustain: f32, release: f32, sr: f32) -> Self {
        Adsr {
            stage: 0,
            level: 0.0,
            a: coeff(attack * 0.4, sr), // overshoot curve reaches 1.0 near `attack`
            d: coeff(decay, sr),
            s: sustain,
            r: coeff(release, sr),
        }
    }

    #[inline]
    pub fn next(&mut self) -> f32 {
        match self.stage {
            0 => {
                self.level += self.a * (1.3 - self.level);
                if self.level >= 1.0 {
                    self.level = 1.0;
                    self.stage = 1;
                }
            }
            1 => {
                self.level += self.d * (self.s - self.level);
                if (self.level - self.s).abs() < 1e-4 {
                    self.stage = 2;
                }
            }
            2 => {}
            3 => {
                self.level += self.r * (0.0 - self.level);
                if self.level < 1e-4 {
                    self.level = 0.0;
                    self.stage = 4;
                }
            }
            _ => {}
        }
        self.level
    }

    pub fn release(&mut self) {
        if self.stage < 3 {
            self.stage = 3;
        }
    }

    pub fn released(&self) -> bool {
        self.stage >= 3
    }

    pub fn alive(&self) -> bool {
        self.stage < 4
    }
}

/// A filtered, exponentially-decaying noise one-shot (HLD family B) —
/// summed in PARALLEL with a voice's output, never into a feedback loop.
/// One struct, per-use config: the pick click, finger/fret noise, slap pop,
/// stop thump and palm chuff each pass their own filter, gain and decay.
pub struct Burst {
    filt: Biquad,
    gain: f32,
    env: f32,   // current amplitude (starts at 0 until triggered)
    decay: f32, // per-sample multiplier for the configured t60
}

impl Burst {
    pub fn new(filt: Biquad, gain: f32, t60: f32, sr: f32) -> Self {
        Burst {
            filt,
            gain,
            env: 0.0,
            decay: 10f32.powf(-3.0 / (t60.max(1e-4) * sr)),
        }
    }

    /// Arm the one-shot at `level` (relative to the configured gain).
    pub fn trigger(&mut self, level: f32) {
        self.env = self.env.max(level);
    }

    /// Next sample; ~0 cost once the envelope has died.
    #[inline]
    pub fn tick(&mut self, rng: &mut Rng) -> f32 {
        if self.env < 1e-5 {
            return 0.0;
        }
        let y = self.filt.process(rng.white()) * self.gain * self.env;
        self.env *= self.decay;
        y
    }
}

/// A sparse aperiodic grain train (PhISEM-style) — the rain/droplet gate. Each
/// sample a grain fires (`e ← 1`) when a fresh uniform draw undercuts the
/// per-sample probability `p`, then rings down by `decay` (a T60). Between grains
/// the gate sits at ~0 — that silence is what makes rain *rain*, where a
/// continuous bandpassed-noise bed only hisses. Used as `noise_bp.process(rng.white()) * gate`.
///
/// Rate is grains-per-SECOND, converted to `p = hz/sr` at construction. That is
/// the one deliberate improvement over the private `Grain` in `drums.rs`, whose
/// raw per-sample probability is silently sample-rate dependent; the dozen lines
/// are duplicated on purpose rather than shared — unifying them would perturb the
/// drums' RNG draw order and byte-change every drum-bearing album for no gain.
pub struct GrainGate {
    e: f32,
    decay: f32,
    p: f32, // per-sample fire probability = hz / sr
}

impl GrainGate {
    pub fn new(hz: f32, t60: f32, sr: f32) -> Self {
        GrainGate {
            e: 0.0,
            decay: 10f32.powf(-3.0 / (t60.max(1e-4) * sr)),
            p: (hz / sr).clamp(0.0, 1.0),
        }
    }

    /// Next gate value in [0, 1]; draws exactly one uniform sample from `rng`.
    #[inline]
    pub fn next(&mut self, rng: &mut Rng) -> f32 {
        if rng.white() * 0.5 + 0.5 < self.p {
            self.e = 1.0;
        }
        let out = self.e;
        self.e *= self.decay;
        out
    }
}

/// MIDI key -> frequency (A440 equal temperament).
pub fn key_freq(key: u8) -> f32 {
    440.0 * 2f32.powf((key as f32 - 69.0) / 12.0)
}

/// Perceptual-ish velocity curve.
pub fn vel_amp(vel: u8) -> f32 {
    (vel as f32 / 127.0).powf(1.6)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sine_stays_bounded() {
        let mut s = Sine::new(440.0, 44100.0, 0.0);
        let mut peak = 0f32;
        for _ in 0..44100 {
            peak = peak.max(s.next().abs());
        }
        assert!(peak <= 1.001 && peak > 0.99, "peak {peak}");
    }

    #[test]
    fn adsr_reaches_sustain_and_dies() {
        let sr = 44100.0;
        let mut e = Adsr::new(0.01, 0.05, 0.6, 0.05, sr);
        for _ in 0..8820 {
            e.next();
        }
        let lvl = e.next();
        assert!((lvl - 0.6).abs() < 0.05, "sustain level {lvl}");
        e.release();
        for _ in 0..22050 {
            e.next();
        }
        assert!(!e.alive());
    }

    #[test]
    fn key_freq_a4() {
        assert!((key_freq(69) - 440.0).abs() < 1e-3);
        assert!((key_freq(60) - 261.626).abs() < 0.01);
    }

    /// Oracle 16 (K1, §5.3 DSP-level): twin hand-built KS loops at a
    /// worst-case fractional delay — the cubic tap keeps ring energy the
    /// linear tap's interpolation lowpass eats.
    #[test]
    fn cubic_tap_retains_treble_ring() {
        let sr = 44100.0;
        let energy = |cubic: bool| {
            let delay = 12.5f32; // ~3.5 kHz string, frac 0.5 (worst case)
            let mut dl = DelayLine::new(20);
            // nearly-open damper: the interpolator's own loss dominates,
            // which is exactly the defect K1 removes
            let mut damp = OnePole::lowpass(16000.0, sr);
            // zero-mean excitation: the loop also resonates at DC, which
            // decays only via the gain and would swamp both taps equally
            for i in 0..13 {
                dl.push(match i {
                    0 => 1.0,
                    1 => -1.0,
                    _ => 0.0,
                });
            }
            let mut acc = 0.0f64;
            for n in 0..(0.3 * sr) as usize {
                let s = if cubic {
                    dl.tap_cubic(delay)
                } else {
                    dl.tap(delay)
                };
                dl.push(damp.process(s) * 0.997);
                if n > (0.05 * sr) as usize {
                    acc += (s as f64) * (s as f64);
                }
            }
            acc.sqrt()
        };
        let (c, l) = (energy(true), energy(false));
        assert!(c > 1.15 * l, "cubic {c} vs linear {l}");
        // and the cubic tap is exact on the grid (weights sum to 1)
        let mut dl = DelayLine::new(16);
        for i in 0..12 {
            dl.push(i as f32);
        }
        assert!((dl.tap_cubic(3.0) - dl.tap(3.0)).abs() < 1e-4);
    }

    /// K1 extended to the sampler: the same 4-point cubic kernel that feeds the
    /// KS loop now reads the sampler's fractional sample positions (LA layer,
    /// drums, gong, clavinet, looped drone). It must (a) pass exactly through
    /// the sample grid and reproduce a cubic exactly, and (b) retain the
    /// high-frequency energy that 2-point linear interpolation eats when a
    /// sample is read at a fractional, pitched-up step — the read step reaches
    /// 2.0 across the LA zone splits, where linear both dulls treble and aliases.
    #[test]
    fn cubic4_is_exact_and_beats_linear_on_treble() {
        // (a) exact on the grid: fr = 0 -> p0, fr = 1 -> p1
        assert!((cubic4(3.0, 7.0, 11.0, 19.0, 0.0) - 7.0).abs() < 1e-6);
        assert!((cubic4(3.0, 7.0, 11.0, 19.0, 1.0) - 11.0).abs() < 1e-6);
        // exact reconstruction of a cubic on nodes {-1, 0, 1, 2}
        let g = |x: f32| x * x * x - 2.0 * x + 1.0;
        for &fr in &[0.1f32, 0.37, 0.5, 0.83] {
            let got = cubic4(g(-1.0), g(0.0), g(1.0), g(2.0), fr);
            assert!(
                (got - g(fr)).abs() < 1e-4,
                "cubic reconstruction fr={fr}: {got} vs {}",
                g(fr)
            );
        }
        // (b) resample a near-Nyquist tone at a fractional pitch-up step; cubic
        // keeps more energy than linear, whose fractional read lowpasses/aliases.
        let sr = 44100.0;
        let n = 4096usize;
        let src: Vec<f32> = (0..n)
            .map(|k| (std::f32::consts::TAU * 9000.0 * k as f32 / sr).sin())
            .collect();
        let read = |cubic: bool| {
            let step = 1.4993f32; // dense fractional coverage, pitched up
            let mut pos = 1.0f32;
            let mut acc = 0.0f64;
            while (pos as usize) + 2 < n {
                let j = pos as usize;
                let fr = pos - j as f32;
                let s = if cubic {
                    cubic4(src[j - 1], src[j], src[j + 1], src[j + 2], fr)
                } else {
                    src[j] + (src[j + 1] - src[j]) * fr
                };
                acc += (s as f64) * (s as f64);
                pos += step;
            }
            acc.sqrt()
        };
        let (c, l) = (read(true), read(false));
        assert!(
            c > 1.04 * l,
            "cubic {c} vs linear {l} (cubic should retain more treble)"
        );
    }

    /// Oracle 4a: a duty-0.5 `BlepPulse` is a band-limited square — its even
    /// harmonics cancel (H2 << H1) and it carries no DC — unlike a saw, whose
    /// 2nd harmonic is ~half the fundamental.
    #[test]
    fn blep_pulse_square_nulls_even_harmonics() {
        let sr = 44100.0;
        let n = sr as usize; // 1 s window
        let mut p = BlepPulse::new(220.0, sr, 0.0, 0.5);
        let ps: Vec<f32> = (0..n).map(|_| p.next()).collect();
        let (p1, p2) = (
            crate::testutil::mag_at(&ps, sr, 220.0),
            crate::testutil::mag_at(&ps, sr, 440.0),
        );
        let dc = ps.iter().sum::<f32>() / n as f32;
        assert!(p2 < 0.05 * p1, "square H2 {p2} not << H1 {p1}");
        assert!(dc.abs() < 0.02, "square DC {dc}");

        let mut s = BlepSaw::new(220.0, sr, 0.0);
        let ss: Vec<f32> = (0..n).map(|_| s.next()).collect();
        let (s1, s2) = (
            crate::testutil::mag_at(&ss, sr, 220.0),
            crate::testutil::mag_at(&ss, sr, 440.0),
        );
        assert!(s2 > 0.3 * s1, "saw H2 {s2} should be strong vs H1 {s1}");
    }

    /// RD-O0 (guard): `ReedPulse` calibration — the reed source must match its
    /// analytic magnitude spectrum, be DC-free, and fold aliasing below −34 dB,
    /// verified before any reed feature oracle trusts it. The alias floor is
    /// measured at a LOW fundamental so fold-back is spectrally *separable* from
    /// the real harmonics (a broadband high-pass would conflate the two — a
    /// band-limited pulse has genuine harmonics all the way to Nyquist).
    #[test]
    fn reed_pulse_calibration() {
        use crate::testutil::mag_at;
        use std::f32::consts::PI;
        let sr = 44100.0;
        let w = 0.30f32;
        let norm = 0.5 / (w * (1.0 - w)).sqrt();

        // (i) spectrum: harmonics 1..=5 of a 1 kHz pulse match 2|sin(πnw)|/(πn)·norm
        let mut p = ReedPulse::new(1000.0, sr, 0.0, w);
        let sig: Vec<f32> = (0..sr as usize).map(|_| p.next() * norm).collect();
        for n in 1..=5u32 {
            let nn = n as f32;
            let want = 2.0 * (PI * nn * w).sin().abs() / (PI * nn) * norm;
            let got = mag_at(&sig, sr, 1000.0 * nn);
            assert!(
                (got - want).abs() <= 0.10 * want,
                "harmonic {n}: got {got:.4} want {want:.4}"
            );
        }
        // (ii) zero-DC by construction
        let mean = sig.iter().sum::<f32>() / sig.len() as f32;
        assert!(mean.abs() < 1e-3, "DC mean {mean:.6}");

        // (iii) alias floor: at f=200, sr=44100 every above-Nyquist image folds
        // to an ODD multiple of 100 Hz — bins no real 200-Hz harmonic (an even
        // multiple of 100) can occupy, and 100 Hz clear of the nearest (a
        // Goertzel sinc-null over the 1 s window). Their RMS / the fundamental
        // isolates genuine fold-back; a BLEP-less pulse fails this by several×.
        let mut p = ReedPulse::new(200.0, sr, 0.0, w);
        let sig: Vec<f32> = (0..sr as usize).map(|_| p.next() * norm).collect();
        let fund = mag_at(&sig, sr, 200.0);
        let (mut acc, mut cnt) = (0.0f64, 0u32);
        let mut b = 100.0f32;
        while b <= 21_900.0 {
            let m = mag_at(&sig, sr, b) as f64;
            acc += m * m;
            cnt += 1;
            b += 200.0; // 100, 300, 500, … (odd multiples of 100)
        }
        let alias = (acc / cnt as f64).sqrt() as f32 / fund;
        assert!(alias < 0.02, "alias floor {alias:.4} (need < 0.02)");
    }

    /// `GrainGate` fires at ~`hz` grains/SECOND (not a raw per-sample probability)
    /// and is sparse between grains. A grain onset is a fresh 0→1 jump of `e`; the
    /// count of onsets over one second must track `hz` across sample rates, which
    /// is exactly the sample-rate independence the drums `Grain` lacks.
    #[test]
    fn grain_gate_rate_is_grains_per_second() {
        for sr in [22050.0f32, 44100.0, 48000.0] {
            let mut g = GrainGate::new(40.0, 0.02, sr);
            let mut rng = Rng::new(9);
            let mut onsets = 0u32;
            let mut prev = 0.0f32;
            let mut nonzero = 0u32;
            let n = sr as usize;
            for _ in 0..n {
                let v = g.next(&mut rng);
                // a fresh grain fires when the envelope jumps back up to 1.0
                if v > prev + 0.5 {
                    onsets += 1;
                }
                if v > 0.02 {
                    nonzero += 1;
                }
                prev = v;
            }
            assert!(
                (30..=52).contains(&onsets),
                "sr {sr}: {onsets} grain onsets/s (want ~40)"
            );
            // sparse: with a 20 ms ring at 40/s the gate is open well under half
            // the time — the silence between grains is the point.
            assert!(
                (nonzero as f32) < 0.55 * n as f32,
                "sr {sr}: gate open {}% — not sparse",
                100 * nonzero / n as u32
            );
        }
    }
}
