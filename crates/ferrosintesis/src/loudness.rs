//! BS.1770-4 integrated loudness (LUFS) — a from-scratch reference meter.
//!
//! Deliberately self-contained (its own biquad, no dependency on `dsp`/`engine`)
//! so it is an INDEPENDENT oracle for the render path: a bug in the engine's DSP
//! cannot hide inside a meter that shares its code.
//!
//! Implements ITU-R BS.1770-4 / EBU R128 integrated loudness:
//!   1. K-weighting pre-filter (stage-1 high shelf + stage-2 RLB high-pass),
//!      coefficients re-derived for the actual sample rate via the RBJ cookbook
//!      bilinear transform (the tabulated constants in the standard are 48 kHz
//!      only — our render rate is 44.1 kHz).
//!   2. 400 ms blocks, 100 ms hop (75 % overlap), channel-weighted mean square.
//!   3. Two-stage gating: absolute −70 LUFS, then relative −10 LU.
//!
//! Calibration is pinned by the EBU Tech 3341 normative test (a stereo 1 kHz sine
//! at −23 dBFS reads −23.0 LUFS) in the unit tests below — an external, non-circular
//! oracle that needs no reference implementation.

const ABS_GATE_LUFS: f32 = -70.0;
const REL_GATE_LU: f32 = -10.0;
const OFFSET: f32 = -0.691; // BS.1770 loudness constant

/// A minimal transposed-direct-form-II biquad. Coefficients and state are f64:
/// the RLB high-pass at 38 Hz has poles very close to the unit circle and is
/// ill-conditioned in f32 — the reference implementations run in double.
#[derive(Clone, Copy)]
struct Biquad {
    b0: f64,
    b1: f64,
    b2: f64,
    a1: f64,
    a2: f64,
    z1: f64,
    z2: f64,
}

impl Biquad {
    #[inline]
    fn process(&mut self, x: f64) -> f64 {
        let y = self.b0 * x + self.z1;
        self.z1 = self.b1 * x - self.a1 * y + self.z2;
        self.z2 = self.b2 * x - self.a2 * y;
        y
    }

    /// BS.1770 stage-1 pre-filter — the Zölzer high-shelf, in the exact form
    /// libebur128 uses to re-derive coefficients at any sample rate (the RBJ
    /// cookbook shelf is a DIFFERENT analog prototype and is ~0.2 dB off at 1 kHz).
    fn pre_filter(fs: f64) -> Self {
        let f0 = 1681.974450956;
        let g = 3.999843853973;
        let q = 0.707175236955;
        let k = (std::f64::consts::PI * f0 / fs).tan();
        let vh = 10f64.powf(g / 20.0);
        let vb = vh.powf(0.499666774155);
        let a0 = 1.0 + k / q + k * k;
        Self {
            b0: (vh + vb * k / q + k * k) / a0,
            b1: 2.0 * (k * k - vh) / a0,
            b2: (vh - vb * k / q + k * k) / a0,
            a1: 2.0 * (k * k - 1.0) / a0,
            a2: (1.0 - k / q + k * k) / a0,
            z1: 0.0,
            z2: 0.0,
        }
    }

    /// BS.1770 stage-2 RLB high-pass (numerator exactly [1, −2, 1]).
    fn rlb_high_pass(fs: f64) -> Self {
        let f0 = 38.135470876024;
        let q = 0.500327037324;
        let k = (std::f64::consts::PI * f0 / fs).tan();
        let a0 = 1.0 + k / q + k * k;
        Self {
            b0: 1.0,
            b1: -2.0,
            b2: 1.0,
            a1: 2.0 * (k * k - 1.0) / a0,
            a2: (1.0 - k / q + k * k) / a0,
            z1: 0.0,
            z2: 0.0,
        }
    }
}

/// The BS.1770 K-weighting pre-filter (stage 1) + RLB high-pass (stage 2),
/// coefficients derived for the given sample rate.
fn k_weighting(fs: f64) -> (Biquad, Biquad) {
    (Biquad::pre_filter(fs), Biquad::rlb_high_pass(fs))
}

/// K-weight one channel's samples (stage 1 then stage 2), returning the filtered
/// signal in f64.
fn k_weight_channel(samples: &[f32], fs: f64) -> Vec<f64> {
    let (mut shelf, mut hp) = k_weighting(fs);
    samples
        .iter()
        .map(|&x| hp.process(shelf.process(x as f64)))
        .collect()
}

/// Integrated loudness (LUFS) of an interleaved-stereo f32 buffer per BS.1770-4.
/// Returns `f32::NEG_INFINITY` for silence / signals with no gated blocks.
pub fn integrated_lufs(interleaved_stereo: &[f32], fs: f32) -> f32 {
    let n_frames = interleaved_stereo.len() / 2;
    if n_frames == 0 {
        return f32::NEG_INFINITY;
    }
    // De-interleave.
    let mut left = Vec::with_capacity(n_frames);
    let mut right = Vec::with_capacity(n_frames);
    for f in 0..n_frames {
        left.push(interleaved_stereo[2 * f]);
        right.push(interleaved_stereo[2 * f + 1]);
    }
    let fs = fs as f64;
    let l = k_weight_channel(&left, fs);
    let r = k_weight_channel(&right, fs);

    let block = (0.400 * fs).round() as usize; // 400 ms
    let hop = (0.100 * fs).round() as usize; // 100 ms (75 % overlap)
    if n_frames < block {
        return f32::NEG_INFINITY;
    }
    // Channel-weighted mean-square (z = z_L + z_R, G_L = G_R = 1.0) per block.
    let mut z: Vec<f64> = Vec::new();
    let mut start = 0;
    while start + block <= n_frames {
        let end = start + block;
        let mut sl = 0.0f64;
        let mut sr = 0.0f64;
        for i in start..end {
            sl += l[i] * l[i];
            sr += r[i] * r[i];
        }
        z.push((sl + sr) / block as f64); // sum of per-channel mean squares
        start += hop;
    }
    if z.is_empty() {
        return f32::NEG_INFINITY;
    }
    // Block loudness l_j = OFFSET + 10 log10(z_j).
    let offset = OFFSET as f64;
    let loud = |zj: f64| -> f64 {
        if zj <= 0.0 {
            f64::NEG_INFINITY
        } else {
            offset + 10.0 * zj.log10()
        }
    };
    // Absolute gate.
    let abs_kept: Vec<f64> = z
        .iter()
        .copied()
        .filter(|&zj| loud(zj) >= ABS_GATE_LUFS as f64)
        .collect();
    if abs_kept.is_empty() {
        return f32::NEG_INFINITY;
    }
    // Relative threshold from the mean z over abs-gated blocks.
    let mean_abs: f64 = abs_kept.iter().sum::<f64>() / abs_kept.len() as f64;
    let rel_thresh = offset + 10.0 * mean_abs.log10() + REL_GATE_LU as f64;
    let rel_kept: Vec<f64> = abs_kept
        .into_iter()
        .filter(|&zj| loud(zj) >= rel_thresh)
        .collect();
    if rel_kept.is_empty() {
        return f32::NEG_INFINITY;
    }
    let mean_rel: f64 = rel_kept.iter().sum::<f64>() / rel_kept.len() as f64;
    (offset + 10.0 * mean_rel.log10()) as f32
}

#[cfg(test)]
mod tests {
    use super::*;

    fn stereo_sine(freq: f32, peak: f32, secs: f32, fs: f32) -> Vec<f32> {
        let n = (secs * fs) as usize;
        let mut v = Vec::with_capacity(n * 2);
        for i in 0..n {
            let s = peak * (2.0 * std::f32::consts::PI * freq * i as f32 / fs).sin();
            v.push(s);
            v.push(s);
        }
        v
    }

    /// EBU Tech 3341 normative calibration: a stereo 1 kHz sine at −23 dBFS reads
    /// −23.0 LUFS. This pins the K-weighting coefficients + block math + the OFFSET
    /// constant against an EXTERNAL spec number (not a reference implementation).
    #[test]
    fn ebu_3341_minus23_calibration_48k() {
        let peak = 10f32.powf(-23.0 / 20.0); // −23 dBFS
        let sig = stereo_sine(1000.0, peak, 5.0, 48000.0);
        let lufs = integrated_lufs(&sig, 48000.0);
        assert!(
            (lufs - (-23.0)).abs() < 0.1,
            "48k 1kHz −23dBFS should read −23.0 LUFS, got {lufs}"
        );
    }

    /// The coefficients must re-derive correctly at the render rate too.
    #[test]
    fn ebu_3341_minus23_calibration_44k1() {
        let peak = 10f32.powf(-23.0 / 20.0);
        let sig = stereo_sine(1000.0, peak, 5.0, 44100.0);
        let lufs = integrated_lufs(&sig, 44100.0);
        assert!(
            (lufs - (-23.0)).abs() < 0.1,
            "44.1k 1kHz −23dBFS should read −23.0 LUFS, got {lufs}"
        );
    }

    /// Scaling invariance: halving amplitude drops loudness by exactly 6.02 LU.
    /// A rock-solid physical invariant that needs no reference value.
    #[test]
    fn scaling_is_minus_6db() {
        let a = stereo_sine(1000.0, 0.5, 5.0, 44100.0);
        let b = stereo_sine(1000.0, 0.25, 5.0, 44100.0);
        let la = integrated_lufs(&a, 44100.0);
        let lb = integrated_lufs(&b, 44100.0);
        assert!(
            ((la - lb) - 6.0206).abs() < 0.02,
            "halving amplitude should be −6.02 LU, got {}",
            la - lb
        );
    }

    /// Gating: a loud second followed by 10 s of silence must read close to the
    /// loud passage (silence gated out), not the naive time-average (~−10 LU lower).
    #[test]
    fn silence_is_gated_out() {
        let fs = 44100.0;
        let mut sig = stereo_sine(1000.0, 0.5, 3.0, fs); // 3 s loud
        sig.extend(std::iter::repeat_n(0.0f32, (10.0 * fs) as usize * 2)); // 10 s silence
        let gated = integrated_lufs(&sig, fs);
        let loud_only = integrated_lufs(&stereo_sine(1000.0, 0.5, 5.0, fs), fs);
        // Naive time-averaging would sit ~11 LU lower; gating must recover the
        // loud passage to within a few tenths (boundary blocks aside).
        assert!(
            (gated - loud_only).abs() < 0.3,
            "silence should be gated out (gated {gated} vs loud-only {loud_only})"
        );
    }

    /// Pure silence has no gated blocks → −inf, not a panic or NaN.
    #[test]
    fn silence_is_neg_inf() {
        let sig = vec![0.0f32; 44100 * 2];
        assert_eq!(integrated_lufs(&sig, 44100.0), f32::NEG_INFINITY);
    }
}
