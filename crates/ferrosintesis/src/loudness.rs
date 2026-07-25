//! BS.1770-4 integrated loudness (LUFS) — a from-scratch reference meter.
//!
//! Deliberately self-contained (its own biquad, no dependency on `dsp`/`engine`)
//! so it is an INDEPENDENT oracle for the render path: a bug in the engine's DSP
//! cannot hide inside a meter that shares its code.
//!
//! Implements ITU-R BS.1770-4 / EBU R128 integrated loudness:
//!   1. K-weighting pre-filter (stage-1 high shelf + stage-2 RLB high-pass),
//!      coefficients re-derived for the actual sample rate via the Zölzer
//!      shelving formulation libebur128 uses (the tabulated constants in the
//!      standard are 48 kHz only — our render rate is 44.1 kHz).
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

/// Channel-weighted mean square (`z_j`) for each BS.1770 block: 400 ms window,
/// 100 ms hop (75 % overlap), `z = z_L + z_R` with `G_L = G_R = 1.0`.
///
/// Shared by [`integrated_lufs`] and [`momentary_lufs`] so the two can never drift
/// apart: the gating in the former and the per-block series in the latter are two
/// readings of exactly the same numbers.
fn block_mean_squares(interleaved_stereo: &[f32], fs: f32) -> Vec<f64> {
    let n_frames = interleaved_stereo.len() / 2;
    if n_frames == 0 {
        return Vec::new();
    }
    let fs = fs as f64;
    let block = (0.400 * fs).round() as usize; // 400 ms
    let hop = (0.100 * fs).round() as usize; // 100 ms (75 % overlap)
    if block == 0 || hop == 0 || n_frames < block {
        return Vec::new();
    }
    // De-interleave.
    let mut left = Vec::with_capacity(n_frames);
    let mut right = Vec::with_capacity(n_frames);
    for f in 0..n_frames {
        left.push(interleaved_stereo[2 * f]);
        right.push(interleaved_stereo[2 * f + 1]);
    }
    let l = k_weight_channel(&left, fs);
    let r = k_weight_channel(&right, fs);

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
    z
}

/// Block loudness `l_j = OFFSET + 10 log10(z_j)`; `-inf` for a zero block.
#[inline]
fn block_loudness(zj: f64) -> f64 {
    if zj <= 0.0 {
        f64::NEG_INFINITY
    } else {
        OFFSET as f64 + 10.0 * zj.log10()
    }
}

/// Momentary loudness (LUFS) per BS.1770: one value per 400 ms block on a 100 ms
/// hop, **ungated** and in time order.
///
/// This is the short-window counterpart to [`integrated_lufs`]. Integrated loudness
/// answers "how loud is this programme overall"; the momentary series answers "how
/// loud is it *right now*", which is what you need to compare individual musical
/// events whose decay envelopes differ — a long window would let tail length leak
/// into a level estimate.
///
/// Returns an empty vector for a buffer shorter than one 400 ms block or a sample
/// rate too small to represent a nonzero 400 ms block and 100 ms hop. Blocks that
/// are exactly zero read `f32::NEG_INFINITY`; callers that want the standard
/// gating should apply it themselves (or use [`integrated_lufs`]).
pub fn momentary_lufs(interleaved_stereo: &[f32], fs: u32) -> Vec<f32> {
    let fs = fs as f32;
    block_mean_squares(interleaved_stereo, fs)
        .into_iter()
        .map(|zj| block_loudness(zj) as f32)
        .collect()
}

/// Integrated loudness (LUFS) of an interleaved-stereo f32 buffer per BS.1770-4.
/// Returns `f32::NEG_INFINITY` for silence / signals with no gated blocks.
pub fn integrated_lufs(interleaved_stereo: &[f32], fs: u32) -> f32 {
    let fs = fs as f32;
    let z = block_mean_squares(interleaved_stereo, fs);
    if z.is_empty() {
        return f32::NEG_INFINITY;
    }
    let offset = OFFSET as f64;
    let loud = block_loudness;
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

// ---------------------------------------------------------------------------
// True-peak metering (ITU-R BS.1770-4 Annex 2): 4× oversample, then max |x|.
// ---------------------------------------------------------------------------

const TP_OVERSAMPLE: usize = 4;
const TP_TAPS_PER_PHASE: usize = 12;

/// A 4-phase polyphase interpolation FIR (windowed sinc), each phase normalized
/// to unit DC gain so interpolated samples match amplitude. Built once per call.
fn tp_polyphase() -> [[f32; TP_TAPS_PER_PHASE]; TP_OVERSAMPLE] {
    let n = TP_OVERSAMPLE * TP_TAPS_PER_PHASE; // prototype length
    let center = (n as f64 - 1.0) / 2.0;
    let mut proto = [0.0f64; TP_OVERSAMPLE * TP_TAPS_PER_PHASE];
    for (i, p) in proto.iter_mut().enumerate() {
        let x = i as f64 - center;
        // Normalized sinc at cutoff = original Nyquist (fc = 1/OVERSAMPLE).
        let s = if x.abs() < 1e-9 {
            1.0
        } else {
            let a = std::f64::consts::PI * x / TP_OVERSAMPLE as f64;
            a.sin() / a
        };
        // Blackman window.
        let w = 0.42 - 0.5 * (2.0 * std::f64::consts::PI * i as f64 / (n as f64 - 1.0)).cos()
            + 0.08 * (4.0 * std::f64::consts::PI * i as f64 / (n as f64 - 1.0)).cos();
        *p = s * w;
    }
    // Split into phases and normalize each to unit sum.
    let mut phases = [[0.0f32; TP_TAPS_PER_PHASE]; TP_OVERSAMPLE];
    for (ph, phase) in phases.iter_mut().enumerate() {
        let mut sum = 0.0f64;
        for k in 0..TP_TAPS_PER_PHASE {
            sum += proto[ph + TP_OVERSAMPLE * k];
        }
        let g = if sum.abs() > 1e-12 { 1.0 / sum } else { 1.0 };
        for k in 0..TP_TAPS_PER_PHASE {
            phase[k] = (proto[ph + TP_OVERSAMPLE * k] * g) as f32;
        }
    }
    phases
}

/// Per-frame 4×-oversampled true-peak envelope (linear) of one channel: entry `i`
/// is the max |interpolated sub-sample| anchored at frame `i` (and the raw sample).
fn channel_true_peak_env(
    c: &[f32],
    phases: &[[f32; TP_TAPS_PER_PHASE]; TP_OVERSAMPLE],
) -> Vec<f32> {
    let mut env = vec![0.0f32; c.len()];
    for (i, e) in env.iter_mut().enumerate() {
        let mut peak = c[i].abs();
        for phase in phases.iter() {
            let mut acc = 0.0f32;
            for (k, &coef) in phase.iter().enumerate() {
                if i >= k {
                    acc += c[i - k] * coef;
                }
            }
            peak = peak.max(acc.abs());
        }
        *e = peak;
    }
    env
}

/// Max 4×-oversampled true peak (linear) of one channel.
fn channel_true_peak(c: &[f32], phases: &[[f32; TP_TAPS_PER_PHASE]; TP_OVERSAMPLE]) -> f32 {
    channel_true_peak_env(c, phases)
        .into_iter()
        .fold(0.0f32, f32::max)
}

/// True peak of an interleaved-stereo buffer in dBTP (dB relative to full scale,
/// inter-sample). Returns `f32::NEG_INFINITY` for pure silence.
pub fn true_peak_dbtp(interleaved_stereo: &[f32], _fs: u32) -> f32 {
    let phases = tp_polyphase();
    let n_frames = interleaved_stereo.len() / 2;
    let mut left = Vec::with_capacity(n_frames);
    let mut right = Vec::with_capacity(n_frames);
    for f in 0..n_frames {
        left.push(interleaved_stereo[2 * f]);
        right.push(interleaved_stereo[2 * f + 1]);
    }
    let peak = channel_true_peak(&left, &phases).max(channel_true_peak(&right, &phases));
    if peak <= 0.0 {
        f32::NEG_INFINITY
    } else {
        20.0 * peak.log10()
    }
}

/// Attack/release ramp times for the true-peak limiter. The attack is kept a few
/// ms rather than sub-ms so the gain is near-flat across the 12-tap interpolation
/// window: a steep ramp there re-inflates the interpolated peak above g·env and
/// stalls convergence. 5 ms of anticipatory pre-duck is inaudible for transients.
const TP_ATTACK_MS: f32 = 5.0;
const TP_RELEASE_MS: f32 = 100.0;
/// Headroom below the stated ceiling. Covers (a) waveform reshaping by the
/// time-varying gain and (b) the ~0.5 dB our 4× true-peak meter reads under
/// ffmpeg/libebur128 on transient-rich material. This is FREE: loudness is
/// measured before limiting, so a lower true-peak does not change the LUFS.
const TP_SAFETY_DB: f32 = 1.0;
/// Max limiter passes. A fast attack ramp straddling the FIR window slightly
/// inflates the interpolated peak above g·env, so one pass can under-correct;
/// re-measuring the limited buffer and re-limiting converges in a few passes.
const TP_MAX_PASSES: usize = 12;

/// One bounded-slope limiter pass over de-interleaved channels: returns true if
/// any gain reduction was applied (i.e. the buffer was over the ceiling).
fn limit_pass(
    left: &mut [f32],
    right: &mut [f32],
    fs: f32,
    ceil_lin: f32,
    phases: &[[f32; TP_TAPS_PER_PHASE]; TP_OVERSAMPLE],
) -> bool {
    let n = left.len();
    if n == 0 {
        return false;
    }
    let env_l = channel_true_peak_env(left, phases);
    let env_r = channel_true_peak_env(right, phases);
    let mut g: Vec<f32> = (0..n)
        .map(|i| {
            let env = env_l[i].max(env_r[i]);
            if env > ceil_lin {
                ceil_lin / env
            } else {
                1.0
            }
        })
        .collect();
    if g.iter().all(|&x| x >= 1.0) {
        return false; // already under the ceiling
    }
    // Backward pass = anticipatory attack (gain reaches the reduction BEFORE the
    // peak); forward pass = gentle release (no pumping). Both bounded-slope → no clicks.
    let atk_step = 10f32.powf((20.0 / (TP_ATTACK_MS / 1000.0 * fs)) / 20.0);
    for i in (0..n - 1).rev() {
        let ramp = g[i + 1] * atk_step;
        if ramp < g[i] {
            g[i] = ramp;
        }
    }
    let rel_step = 10f32.powf((20.0 / (TP_RELEASE_MS / 1000.0 * fs)) / 20.0);
    for i in 1..n {
        let ramp = g[i - 1] * rel_step;
        if ramp < g[i] {
            g[i] = ramp;
        }
    }
    for i in 0..n {
        left[i] *= g[i];
        right[i] *= g[i];
    }
    true
}

/// In-place true-peak limiter on an interleaved-stereo buffer: pulls every
/// 4×-oversampled true peak to `ceiling_dbtp` (less a safety margin), with a
/// click-free anticipatory attack and a gentle release. One shared gain per frame
/// preserves the stereo image. Content already under the ceiling is unchanged.
/// Iterated to convergence so a fast attack ramp can't leave residual overshoot.
pub fn limit_true_peak(interleaved_stereo: &mut [f32], fs: u32, ceiling_dbtp: f32) {
    let fs = fs as f32;
    let n_frames = interleaved_stereo.len() / 2;
    if n_frames == 0 {
        return;
    }
    let ceil_lin = 10f32.powf((ceiling_dbtp - TP_SAFETY_DB) / 20.0);
    let phases = tp_polyphase();

    let mut left: Vec<f32> = (0..n_frames).map(|f| interleaved_stereo[2 * f]).collect();
    let mut right: Vec<f32> = (0..n_frames)
        .map(|f| interleaved_stereo[2 * f + 1])
        .collect();

    for _ in 0..TP_MAX_PASSES {
        if !limit_pass(&mut left, &mut right, fs, ceil_lin, &phases) {
            break;
        }
    }
    for f in 0..n_frames {
        interleaved_stereo[2 * f] = left[f];
        interleaved_stereo[2 * f + 1] = right[f];
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn stereo_sine(freq: f32, peak: f32, secs: f32, fs: f32) -> Vec<f32> {
        stereo_sine_phase(freq, peak, secs, fs, 0.0)
    }

    fn stereo_sine_phase(freq: f32, peak: f32, secs: f32, fs: f32, phase: f32) -> Vec<f32> {
        let n = (secs * fs) as usize;
        let mut v = Vec::with_capacity(n * 2);
        for i in 0..n {
            let s = peak * (2.0 * std::f32::consts::PI * freq * i as f32 / fs + phase).sin();
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
        let lufs = integrated_lufs(&sig, 48000);
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
        let lufs = integrated_lufs(&sig, 44100);
        assert!(
            (lufs - (-23.0)).abs() < 0.1,
            "44.1k 1kHz −23dBFS should read −23.0 LUFS, got {lufs}"
        );
    }

    /// The momentary series inherits the EBU 3341 calibration: on steady tone
    /// EVERY 400 ms block must read the same −23.0 LUFS the integrated meter does.
    /// This pins the shared `block_mean_squares` path — if a future edit breaks the
    /// block grid or the offset for one caller, it breaks for both.
    #[test]
    fn momentary_matches_ebu_calibration_on_steady_tone() {
        let peak = 10f32.powf(-23.0 / 20.0);
        for &fs in &[44100.0f32, 48000.0] {
            let sig = stereo_sine(1000.0, peak, 5.0, fs);
            let m = momentary_lufs(&sig, fs as u32);
            // 5 s at 400 ms/100 ms hop → floor((5.0 − 0.4)/0.1) + 1 = 47 blocks.
            assert_eq!(m.len(), 47, "fs={fs}: unexpected block count");
            for (i, &b) in m.iter().enumerate() {
                assert!(
                    (b - (-23.0)).abs() < 0.1,
                    "fs={fs} block {i}: steady −23 dBFS tone should read −23.0 LUFS, got {b}"
                );
            }
        }
    }

    /// Invalid tiny rates must not turn the 100 ms hop into a zero increment.
    #[test]
    fn sub_five_hz_rates_return_without_looping() {
        let one_frame = [0.0, 0.0];
        for fs in 0..=4 {
            assert!(
                momentary_lufs(&one_frame, fs).is_empty(),
                "fs={fs} should have no representable momentary block"
            );
            assert_eq!(
                integrated_lufs(&one_frame, fs),
                f32::NEG_INFINITY,
                "fs={fs} should have no integrated loudness"
            );
        }
    }

    /// The momentary series must TRACK a level change that integrated loudness
    /// averages away — the property that makes it the right tool for comparing
    /// individual musical events. A quiet half followed by a loud half reads as two
    /// plateaus 20 LU apart, not as one mean.
    #[test]
    fn momentary_tracks_a_step_that_integrated_averages() {
        let fs = 44100.0f32;
        let mut sig = stereo_sine(1000.0, 10f32.powf(-43.0 / 20.0), 3.0, fs);
        sig.extend(stereo_sine(1000.0, 10f32.powf(-23.0 / 20.0), 3.0, fs));
        let m = momentary_lufs(&sig, fs as u32);
        // Sample well inside each plateau, clear of the 400 ms straddling blocks.
        let quiet = m[10];
        let loud = m[m.len() - 10];
        assert!(
            (quiet - (-43.0)).abs() < 0.1,
            "first plateau should read −43.0, got {quiet}"
        );
        assert!(
            (loud - (-23.0)).abs() < 0.1,
            "second plateau should read −23.0, got {loud}"
        );
        // Integrated, by contrast, gates the quiet half out entirely and reports
        // only the loud one — which is exactly why it cannot compare events.
        let integrated = integrated_lufs(&sig, fs as u32);
        assert!(
            (integrated - (-23.0)).abs() < 0.5,
            "integrated should report ~−23.0 (quiet half relative-gated out), got {integrated}"
        );
    }

    /// Scaling invariance: halving amplitude drops loudness by exactly 6.02 LU.
    /// A rock-solid physical invariant that needs no reference value.
    #[test]
    fn scaling_is_minus_6db() {
        let a = stereo_sine(1000.0, 0.5, 5.0, 44100.0);
        let b = stereo_sine(1000.0, 0.25, 5.0, 44100.0);
        let la = integrated_lufs(&a, 44100);
        let lb = integrated_lufs(&b, 44100);
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
        let gated = integrated_lufs(&sig, fs as u32);
        let loud_only = integrated_lufs(&stereo_sine(1000.0, 0.5, 5.0, fs), fs as u32);
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
        assert_eq!(integrated_lufs(&sig, 44100), f32::NEG_INFINITY);
    }

    fn sample_peak_dbfs(interleaved: &[f32]) -> f32 {
        let p = interleaved.iter().fold(0.0f32, |m, &x| m.max(x.abs()));
        20.0 * p.log10()
    }

    /// A full-scale fs/4 tone at 45° phase samples at ±0.707 (−3 dBFS) while its
    /// true crest is 0 dBFS: the 4× oversampler must recover most of that 3 dB gap.
    #[test]
    fn true_peak_recovers_intersample() {
        let fs = 44100.0;
        let sig = stereo_sine_phase(fs / 4.0, 1.0, 1.0, fs, std::f32::consts::FRAC_PI_4);
        let tp = true_peak_dbtp(&sig, fs as u32);
        let sp = sample_peak_dbfs(&sig); // ≈ −3.01 dBFS
        assert!(
            tp > sp + 2.0,
            "oversampler should recover most of the inter-sample crest (tp {tp} vs sp {sp})"
        );
        assert!(
            (tp - 0.0).abs() < 0.6,
            "true peak of a full-scale sine should be ~0 dBTP, got {tp}"
        );
    }

    /// A low tone's crest lands essentially on the samples: true peak ≈ sample peak.
    #[test]
    fn true_peak_low_tone_matches_sample() {
        let fs = 44100.0;
        let sig = stereo_sine(100.0, 0.5, 1.0, fs);
        let tp = true_peak_dbtp(&sig, fs as u32);
        assert!(
            (tp - (-6.0206)).abs() < 0.2,
            "0.5-amp low tone should read ~-6.02 dBTP, got {tp}"
        );
    }

    #[test]
    fn true_peak_silence_neg_inf() {
        let sig = vec![0.0f32; 4410 * 2];
        assert_eq!(true_peak_dbtp(&sig, 44100), f32::NEG_INFINITY);
    }

    /// The limiter must bring an over-ceiling signal's true peak to the ceiling.
    #[test]
    fn limiter_meets_ceiling() {
        let fs = 44100.0;
        let mut sig = stereo_sine(1000.0, 2.0, 1.0, fs); // true peak ≈ +6 dBTP
        assert!(true_peak_dbtp(&sig, fs as u32) > 5.0);
        limit_true_peak(&mut sig, fs as u32, -1.0);
        let tp = true_peak_dbtp(&sig, fs as u32);
        assert!(
            tp <= -0.9,
            "limited true peak must sit at/under the -1 dBTP ceiling, got {tp}"
        );
    }

    /// Content already under the ceiling passes through untouched (no gain, no pumping).
    #[test]
    fn limiter_unity_under_ceiling() {
        let fs = 44100.0;
        let orig = stereo_sine(440.0, 0.3, 1.0, fs); // ~-10.5 dBTP, well under -1
        let mut sig = orig.clone();
        limit_true_peak(&mut sig, fs as u32, -1.0);
        let max_diff = orig
            .iter()
            .zip(&sig)
            .fold(0.0f32, |m, (a, b)| m.max((a - b).abs()));
        assert!(
            max_diff < 1e-6,
            "under-ceiling content must be unchanged, max sample diff {max_diff}"
        );
    }

    /// After a loud transient, the gain must release back to unity so the quiet
    /// tail that follows is left untouched (proves release, not permanent ducking).
    #[test]
    fn limiter_releases_to_unity() {
        let fs = 44100.0;
        let mut burst = stereo_sine(1000.0, 2.5, 0.05, fs); // loud transient
        let tail = stereo_sine(300.0, 0.2, 0.6, fs); // quiet tail, under ceiling
        burst.extend_from_slice(&tail);
        let orig = burst.clone();
        limit_true_peak(&mut burst, fs as u32, -1.0);
        // Compare only the LAST 0.2 s (well past the 100 ms release): must be unchanged.
        let start = orig.len() - (0.2 * fs) as usize * 2;
        let max_diff = orig[start..]
            .iter()
            .zip(&burst[start..])
            .fold(0.0f32, |m, (a, b)| m.max((a - b).abs()));
        assert!(
            max_diff < 1e-5,
            "gain must release to unity for the quiet tail, max diff {max_diff}"
        );
    }
}
