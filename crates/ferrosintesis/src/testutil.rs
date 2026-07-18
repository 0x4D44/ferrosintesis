//! Test-only shared oracle helpers and the Phase-0 guard oracles of the
//! realism HLD (§5 helper API, §5.3 corrections). Oracle 0 calibrates every
//! helper against golden synthetic signals before any feature oracle trusts
//! it. The module is `#[cfg(test)]`-gated in main.rs — it compiles away in
//! the shipped binary and is the one explicit exemption from the HLD's
//! "no new modules" rule (§4 impact map).

use crate::dsp::{Biquad, OnePole, Rng};
use crate::engine::{self, Options};
use crate::midi::{Ev, EvKind, Song};

// ---------------------------------------------------------------------------
// Measurement helpers (HLD §5 + §5.3)
// ---------------------------------------------------------------------------

/// Plain RMS of a segment.
pub(crate) fn rms(seg: &[f32]) -> f32 {
    if seg.is_empty() {
        return 0.0;
    }
    (seg.iter().map(|&x| (x as f64) * (x as f64)).sum::<f64>() / seg.len() as f64).sqrt() as f32
}

/// RMS of the segment through a constant-peak bandpass at (f, q).
pub(crate) fn band_rms(seg: &[f32], sr: f32, f: f32, q: f32) -> f32 {
    let mut bp = Biquad::bandpass(f, q, sr);
    let filtered: Vec<f32> = seg.iter().map(|&x| bp.process(x)).collect();
    rms(&filtered)
}

/// Spectral RMS inside an explicit frequency range. Exact DFT bins over a Hann
/// window make this a real band measurement rather than a narrow-Q proxy.
pub(crate) fn spectral_band_rms(seg: &[f32], sr: f32, lo: f32, hi: f32) -> f32 {
    assert!(lo >= 0.0 && hi > lo && hi < sr * 0.5);
    let n = seg.len();
    if n < 2 {
        return 0.0;
    }
    let windowed: Vec<f32> = seg
        .iter()
        .enumerate()
        .map(|(i, &x)| {
            let window = 0.5 - 0.5 * (std::f32::consts::TAU * i as f32 / (n - 1) as f32).cos();
            x * window
        })
        .collect();
    let bin_hz = sr / n as f32;
    let first = (lo / bin_hz).ceil().max(1.0) as usize;
    let last = (hi / bin_hz).floor() as usize;
    let energy = (first..=last)
        .map(|bin| mag_at(&windowed, sr, bin as f32 * bin_hz).powi(2))
        .sum::<f32>();
    (0.5 * energy).sqrt()
}

/// Spectral centroid over exact DFT bins. The bounded 4096-sample window keeps
/// adjacent-note organ comparisons stable without turning tests into an FFT
/// implementation or adding a dependency.
pub(crate) fn spectral_centroid(seg: &[f32], sr: f32, lo: f32, hi: f32) -> f32 {
    let n = seg.len().min(4096);
    if n < 2 {
        return 0.0;
    }
    let windowed: Vec<f32> = seg[..n]
        .iter()
        .enumerate()
        .map(|(i, &x)| {
            let window = 0.5 - 0.5 * (std::f32::consts::TAU * i as f32 / (n - 1) as f32).cos();
            x * window
        })
        .collect();
    let bin_hz = sr / n as f32;
    let first = (lo / bin_hz).ceil().max(1.0) as usize;
    let last = (hi / bin_hz).floor().min((n / 2) as f32) as usize;
    let (weighted, total) = (first..=last).fold((0.0f64, 0.0f64), |(weighted, total), bin| {
        let freq = bin as f32 * bin_hz;
        let magnitude = mag_at(&windowed, sr, freq) as f64;
        (weighted + freq as f64 * magnitude, total + magnitude)
    });
    if total > 0.0 {
        (weighted / total) as f32
    } else {
        0.0
    }
}

/// RMS of the segment above `f` (2nd-order highpass, Q 0.7).
pub(crate) fn hp_rms(seg: &[f32], sr: f32, f: f32) -> f32 {
    let mut hp = Biquad::highpass(f, 0.7, sr);
    let filtered: Vec<f32> = seg.iter().map(|&x| hp.process(x)).collect();
    rms(&filtered)
}

/// Single-bin Goertzel magnitude, normalised so a unit-amplitude sine at an
/// on-bin frequency reads ≈ 1.0.
pub(crate) fn mag_at(seg: &[f32], sr: f32, f: f32) -> f32 {
    let w = 2.0 * std::f64::consts::PI * (f as f64) / (sr as f64);
    let coeff = 2.0 * w.cos();
    let (mut s1, mut s2) = (0.0f64, 0.0f64);
    for &x in seg {
        let s0 = x as f64 + coeff * s1 - s2;
        s2 = s1;
        s1 = s0;
    }
    let power = s1 * s1 + s2 * s2 - coeff * s1 * s2;
    (power.max(0.0).sqrt() / (seg.len() as f64 / 2.0)) as f32
}

/// Spectral centroid over 20 log-spaced Goertzel bins, 100 Hz .. 12 kHz:
/// Σ f·|X(f)| / Σ |X(f)|.
pub(crate) fn centroid(seg: &[f32], sr: f32) -> f32 {
    let (lo, hi, n) = (100.0f32, 12_000.0f32, 20u32);
    let (mut num, mut den) = (0.0f64, 0.0f64);
    for i in 0..n {
        let f = lo * (hi / lo).powf(i as f32 / (n - 1) as f32);
        let m = mag_at(seg, sr, f) as f64;
        num += f as f64 * m;
        den += m;
    }
    if den <= 0.0 {
        0.0
    } else {
        (num / den) as f32
    }
}

/// Cross-machine-stable render tripwire. Raw `f32` fingerprints vary with
/// optimizer/CPU codegen even when the audible signal is unchanged; these three
/// measurements retain a tight level, spectrum, and envelope guard without
/// depending on last-bit identity.
#[derive(Clone, Copy, Debug)]
pub(crate) struct RenderSignature {
    pub(crate) rms_db: f32,
    pub(crate) centroid_hz: f32,
    pub(crate) late_early_db: f32,
}

pub(crate) const SIGNATURE_RMS_TOL_DB: f32 = 0.15;
pub(crate) const SIGNATURE_CENTROID_TOL: f32 = 0.02;
pub(crate) const SIGNATURE_ENVELOPE_TOL_DB: f32 = 0.30;

fn signature_window(samples: &[f32], sr: f32, window: (f32, f32)) -> &[f32] {
    let start = (window.0 * sr) as usize;
    let end = (window.1 * sr) as usize;
    assert!(
        window.0 >= 0.0 && window.1 > window.0 && end <= samples.len(),
        "signature window {:?} outside {:.3}s render",
        window,
        samples.len() as f32 / sr
    );
    &samples[start..end]
}

pub(crate) fn render_signature(
    samples: &[f32],
    sr: f32,
    body: (f32, f32),
    early: (f32, f32),
    late: (f32, f32),
) -> RenderSignature {
    let body = signature_window(samples, sr, body);
    let early_rms = rms(signature_window(samples, sr, early)).max(1e-12);
    let late_rms = rms(signature_window(samples, sr, late)).max(1e-12);
    RenderSignature {
        rms_db: 20.0 * rms(body).max(1e-12).log10(),
        centroid_hz: centroid(body, sr),
        late_early_db: 20.0 * (late_rms / early_rms).log10(),
    }
}

pub(crate) fn signature_matches(got: RenderSignature, expected: RenderSignature) -> bool {
    (got.rms_db - expected.rms_db).abs() <= SIGNATURE_RMS_TOL_DB
        && (got.centroid_hz / expected.centroid_hz.max(1e-12) - 1.0).abs() <= SIGNATURE_CENTROID_TOL
        && (got.late_early_db - expected.late_early_db).abs() <= SIGNATURE_ENVELOPE_TOL_DB
}

pub(crate) fn assert_render_signature(
    label: &str,
    got: RenderSignature,
    expected: RenderSignature,
) {
    assert!(
        signature_matches(got, expected),
        "{label} render signature drifted: got {got:?}, expected {expected:?} \
         (tolerances: rms ±{SIGNATURE_RMS_TOL_DB:.2} dB, centroid ±{:.1}%, envelope ±{SIGNATURE_ENVELOPE_TOL_DB:.2} dB)",
        SIGNATURE_CENTROID_TOL * 100.0
    );
}

/// Argmax of `mag_at` over a fine log grid (0.5% steps) in [f_lo, f_hi].
pub(crate) fn peak_locate(seg: &[f32], sr: f32, f_lo: f32, f_hi: f32) -> f32 {
    let mut f = f_lo;
    let (mut best_f, mut best_m) = (f_lo, 0.0f32);
    while f <= f_hi {
        let m = mag_at(seg, sr, f);
        if m > best_m {
            best_m = m;
            best_f = f;
        }
        f *= 1.005;
    }
    best_f
}

/// Fundamental estimate: double 700 Hz lowpass, count rising zero crossings.
pub(crate) fn pitch_hz(seg: &[f32], sr: f32) -> f32 {
    let mut lp1 = OnePole::lowpass(700.0, sr);
    let mut lp2 = OnePole::lowpass(700.0, sr);
    let f: Vec<f32> = seg.iter().map(|&x| lp2.process(lp1.process(x))).collect();
    let mut c = 0u32;
    for w in f.windows(2) {
        if w[0] <= 0.0 && w[1] > 0.0 {
            c += 1;
        }
    }
    c as f32 / (seg.len() as f32 / sr)
}

/// Decay time from the 10 ms windowed-RMS envelope: time from the peak
/// window to −30 dB below it, doubled (exact for an exponential decay).
/// Returns +∞ when the segment never drops 30 dB.
pub(crate) fn t60_of(seg: &[f32], sr: f32) -> f32 {
    let win = (0.01 * sr) as usize;
    if win == 0 || seg.len() < win * 2 {
        return 0.0;
    }
    let env: Vec<f32> = seg.chunks(win).map(rms).collect();
    let (mut pi, mut pv) = (0usize, 0.0f32);
    for (i, &v) in env.iter().enumerate() {
        if v > pv {
            pi = i;
            pv = v;
        }
    }
    let target = pv * 10f32.powf(-30.0 / 20.0);
    for (i, &v) in env.iter().enumerate().skip(pi + 1) {
        if v <= target {
            return ((i - pi) * win) as f32 / sr * 2.0;
        }
    }
    f32::INFINITY
}

/// Normalised L/R cross-correlation at lag 0: ≈1 mono, ≈0 independent,
/// ≈−1 inverted.
pub(crate) fn inter_corr(l: &[f32], r: &[f32]) -> f32 {
    let n = l.len().min(r.len());
    let (mut lr, mut ll, mut rr) = (0.0f64, 0.0f64, 0.0f64);
    for i in 0..n {
        lr += l[i] as f64 * r[i] as f64;
        ll += l[i] as f64 * l[i] as f64;
        rr += r[i] as f64 * r[i] as f64;
    }
    if ll <= 0.0 || rr <= 0.0 {
        return 0.0;
    }
    (lr / (ll.sqrt() * rr.sqrt())) as f32
}

/// AM-rate detector (oracle 24): rectify → 200 Hz envelope lowpass →
/// DETREND (subtract a 15 Hz-lowpassed copy, so a decaying tail's trend
/// doesn't saturate the autocorrelation) → normalised autocorrelation peak
/// over the lag window. Returns (peak in 0..1, rate in Hz at the peak lag).
pub(crate) fn env_autocorr_peak(seg: &[f32], sr: f32, lag_lo_s: f32, lag_hi_s: f32) -> (f32, f32) {
    // Oracle-24 and every 15 Hz caller keep the calibrated corner.
    env_autocorr_peak_detrend(seg, sr, lag_lo_s, lag_hi_s, 15.0)
}

/// Minimum tremolo AM autocorrelation peak the alt-bank Bowed(44) must reach.
pub(crate) const BW_TREM_PEAK_FLOOR: f32 = 0.55;

/// Detrend-corner variant of `env_autocorr_peak`: the highpass `detrend_hz` is a
/// parameter, not a hard-coded 15 Hz. The alt-bank bow-tremolo (44) sits at
/// 6-9 Hz — below the 15 Hz corner, which would attenuate its AM fundamental —
/// so its rate oracle passes `detrend_hz = 4.0`.
pub(crate) fn env_autocorr_peak_detrend(
    seg: &[f32],
    sr: f32,
    lag_lo_s: f32,
    lag_hi_s: f32,
    detrend_hz: f32,
) -> (f32, f32) {
    let mut lp = OnePole::lowpass(200.0, sr);
    let env: Vec<f32> = seg.iter().map(|&x| lp.process(x.abs())).collect();
    let mut slow = OnePole::lowpass(detrend_hz, sr);
    let d: Vec<f64> = env.iter().map(|&x| (x - slow.process(x)) as f64).collect();
    let zero: f64 = d.iter().map(|&x| x * x).sum();
    if zero <= 0.0 {
        return (0.0, 0.0);
    }
    let lag_lo = ((lag_lo_s * sr) as usize).max(1);
    let lag_hi = ((lag_hi_s * sr) as usize).min(d.len().saturating_sub(1));
    let (mut best, mut best_lag) = (f64::MIN, lag_lo);
    for lag in lag_lo..=lag_hi {
        let c: f64 = (0..d.len() - lag).map(|i| d[i] * d[i + lag]).sum::<f64>() / zero;
        if c > best {
            best = c;
            best_lag = lag;
        }
    }
    (best as f32, sr / best_lag as f32)
}

/// Spectral flatness over 24 log-spaced Goertzel bins in [lo, hi]:
/// geometric mean / arithmetic mean — ≈1 flat (noise), → 0 peaked (tone).
pub(crate) fn flatness(seg: &[f32], sr: f32, lo: f32, hi: f32) -> f32 {
    let n = 24u32;
    let (mut logs, mut sum) = (0.0f64, 0.0f64);
    for i in 0..n {
        let f = lo * (hi / lo).powf(i as f32 / (n - 1) as f32);
        let m = (mag_at(seg, sr, f) as f64).max(1e-12);
        logs += m.ln();
        sum += m;
    }
    ((logs / n as f64).exp() / (sum / n as f64)) as f32
}

/// Kurtosis (4th standardised moment, `E[(x−μ)^4]/σ^4`) — a grain /
/// impulsiveness detector. A Gaussian process reads ≈ 3.0; smooth
/// bandpass-filtered noise (the filter's memory sums many inputs → CLT) sits
/// near 3.0 too; a sparse, spiky, gated grain train reads far higher
/// (leptokurtic). This is the detector that proves the snare wire buzz becomes
/// a granular crackle rather than a smooth "shhh" (HLD P-S1): a differential
/// ratio (grainy render / smooth render) rather than an absolute threshold.
pub(crate) fn kurtosis(seg: &[f32]) -> f32 {
    let n = seg.len();
    if n < 2 {
        return 0.0;
    }
    let mean = seg.iter().map(|&x| x as f64).sum::<f64>() / n as f64;
    let (mut m2, mut m4) = (0.0f64, 0.0f64);
    for &x in seg {
        let d = x as f64 - mean;
        let d2 = d * d;
        m2 += d2;
        m4 += d2 * d2;
    }
    m2 /= n as f64;
    m4 /= n as f64;
    if m2 <= 0.0 {
        return 0.0;
    }
    (m4 / (m2 * m2)) as f32
}

/// Band-limited RMS envelope E(t; lo, hi) over 25 ms windows, 5 ms hop, 3-tap
/// smoothed — the cymbal-bloom trajectory (HLD cascade oracle). Times *when* a
/// band's energy peaks: a real crash's high band blooms tens of ms after the
/// strike, its low band peaks at t=0. Pair with `traj_peak_time_s`.
pub(crate) fn traj(seg: &[f32], sr: f32, lo: f32, hi: f32) -> Vec<f32> {
    let win = (0.025 * sr) as usize;
    let hop = (0.005 * sr) as usize;
    if win == 0 || hop == 0 || seg.len() < win {
        return Vec::new();
    }
    let mut e = Vec::new();
    let mut i = 0;
    while i + win <= seg.len() {
        e.push(spectral_band_rms(&seg[i..i + win], sr, lo, hi));
        i += hop;
    }
    // 3-tap moving average (endpoints clamp).
    (0..e.len())
        .map(|k| {
            let a = e[k.saturating_sub(1)];
            let c = e[(k + 1).min(e.len() - 1)];
            (a + e[k] + c) / 3.0
        })
        .collect()
}

/// First-crossing peak time (seconds) of a `traj`: the CENTER time of the first
/// window reaching ≥ 0.90·max. First-crossing (not argmax) is robust where a
/// noisy wash plateau would let argmax wander tens of ms. Assumes `traj`'s
/// 25 ms window / 5 ms hop convention (so the first window's center is 12.5 ms).
pub(crate) fn traj_peak_time_s(tr: &[f32]) -> f32 {
    if tr.is_empty() {
        return 0.0;
    }
    let max = tr.iter().cloned().fold(0.0f32, f32::max);
    let thr = 0.90 * max;
    for (k, &v) in tr.iter().enumerate() {
        if v >= thr {
            return k as f32 * 0.005 + 0.0125;
        }
    }
    0.0
}

/// High-precision mean fundamental period, in SAMPLES, of a sustained tone.
/// Isolates the fundamental with two cascaded bandpasses at `f_expect`, finds
/// every rising zero crossing with linear interpolation, and averages the
/// period over the whole crossing train (first-to-last / count), so the
/// per-crossing interpolation error divides by the number of cycles. This is
/// the tuning-measurement primitive for the waveguide `loop_comp` sweeps
/// (lesson 2026.07.11: measure, never assume `sr/f − 1`).
pub(crate) fn mean_period_samples(seg: &[f32], sr: f32, f_expect: f32) -> f32 {
    let mut b1 = Biquad::bandpass(f_expect, 4.0, sr);
    let mut b2 = Biquad::bandpass(f_expect, 4.0, sr);
    let f: Vec<f32> = seg.iter().map(|&x| b2.process(b1.process(x))).collect();
    // skip the filter settle before trusting crossings
    let skip = ((0.1 * sr) as usize).min(f.len() / 4);
    let mut first = None;
    let mut last = None;
    let mut count = 0u32;
    for i in skip..f.len().saturating_sub(1) {
        if f[i] <= 0.0 && f[i + 1] > 0.0 {
            let t = i as f64 + (f[i] / (f[i] - f[i + 1])) as f64;
            if first.is_none() {
                first = Some(t);
            }
            last = Some(t);
            count += 1;
        }
    }
    match (first, last) {
        (Some(a), Some(b)) if count >= 2 => ((b - a) / (count - 1) as f64) as f32,
        _ => 0.0,
    }
}

/// FM vibrato detector: (normalised autocorrelation peak 0..1, modulation rate
/// in Hz) of the fundamental's instantaneous-frequency track, searched over
/// `[rate_lo, rate_hi]`. Two cascaded bandpasses isolate the fundamental,
/// interpolated rising zero crossings give a per-cycle frequency series
/// (sample rate ≈ f0 — ample for single-digit-Hz vibrato), a moving-average
/// detrend removes drift/wander, and the autocorrelation peak names the rate.
/// This measures the SHIPPED render — no internal LFO fields — so a
/// control-rate LFO built at the wrong sample rate (the 16×-slow idiom bug,
/// MM-BUG-KILN-00003/00004) cannot hide from it.
pub(crate) fn fm_mod_rate(seg: &[f32], sr: f32, f0: f32, rate_lo: f32, rate_hi: f32) -> (f32, f32) {
    let mut b1 = Biquad::bandpass(f0, 6.0, sr);
    let mut b2 = Biquad::bandpass(f0, 6.0, sr);
    let f: Vec<f32> = seg.iter().map(|&x| b2.process(b1.process(x))).collect();
    let skip = ((0.15 * sr) as usize).min(f.len() / 4);
    let mut times: Vec<f64> = Vec::new();
    for i in skip..f.len().saturating_sub(1) {
        if f[i] <= 0.0 && f[i + 1] > 0.0 {
            times.push(i as f64 + (f[i] / (f[i] - f[i + 1])) as f64);
        }
    }
    if times.len() < 32 {
        return (0.0, 0.0);
    }
    let raw: Vec<f64> = times
        .windows(2)
        .map(|w| sr as f64 / (w[1] - w[0]))
        .collect();
    // cycle-series sample rate ≈ the mean fundamental frequency
    let cyc_sr = (raw.len() as f64 * sr as f64 / (times[times.len() - 1] - times[0])) as f32;
    // Pre-smooth the cycle series with a short centred boxcar: bow-grit phase
    // noise is broadband up to the cycle Nyquist, while the vibrato lives at
    // or below rate_hi — a window ≈ a third of the fastest searched period
    // kills most per-cycle jitter without touching the searched band.
    let sm = ((cyc_sr / (3.0 * rate_hi)) as usize).max(1);
    let freqs: Vec<f64> = (0..raw.len())
        .map(|i| {
            let a = i.saturating_sub(sm);
            let b = (i + sm + 1).min(raw.len());
            raw[a..b].iter().sum::<f64>() / (b - a) as f64
        })
        .collect();
    // detrend: subtract a centred moving average (~0.4 s) so slow drift and
    // the note's scoop cannot masquerade as (or mask) periodic vibrato
    let half = ((0.2 * cyc_sr) as usize).max(1);
    let d: Vec<f64> = (0..freqs.len())
        .map(|i| {
            let a = i.saturating_sub(half);
            let b = (i + half + 1).min(freqs.len());
            let mean = freqs[a..b].iter().sum::<f64>() / (b - a) as f64;
            freqs[i] - mean
        })
        .collect();
    let zero: f64 = d.iter().map(|&x| x * x).sum();
    if zero <= 0.0 {
        return (0.0, 0.0);
    }
    let lag_lo = ((cyc_sr / rate_hi) as usize).max(1);
    let lag_hi = ((cyc_sr / rate_lo) as usize).min(d.len().saturating_sub(1));
    if lag_hi <= lag_lo {
        return (0.0, 0.0);
    }
    let mut corr = Vec::with_capacity(lag_hi - lag_lo + 1);
    let mut best = f64::MIN;
    let mut best_i = 0usize;
    for lag in lag_lo..=lag_hi {
        let c: f64 = (0..d.len() - lag).map(|i| d[i] * d[i + lag]).sum::<f64>() / zero;
        corr.push(c);
        if c > best {
            best = c;
            best_i = lag - lag_lo;
        }
    }
    // A periodic modulation correlates almost equally at 2×/3× its period, so
    // the GLOBAL argmax can read an octave low. Take the smallest-lag LOCAL
    // MAXIMUM within 85 % of the peak — the modulation's true period — and
    // refine the lag with a parabolic fit through its neighbours.
    let mut i = best_i;
    for j in 1..corr.len().saturating_sub(1) {
        if corr[j] >= corr[j - 1] && corr[j] >= corr[j + 1] && corr[j] >= 0.85 * best {
            i = j;
            break;
        }
    }
    let lag_f = if i >= 1 && i + 1 < corr.len() {
        let (a, b, c) = (corr[i - 1], corr[i], corr[i + 1]);
        let denom = a - 2.0 * b + c;
        let delta = if denom.abs() > 1e-12 {
            (0.5 * (a - c) / denom).clamp(-1.0, 1.0)
        } else {
            0.0
        };
        (lag_lo + i) as f64 + delta
    } else {
        (lag_lo + i) as f64
    };
    (best.max(0.0) as f32, (cyc_sr as f64 / lag_f) as f32)
}

// ---------------------------------------------------------------------------
// The fixed multi-family reference song (oracles 34/35/38)
// ---------------------------------------------------------------------------

/// Deterministic reference song covering every family this design touches
/// plus two untouched canaries (piano, strings). Committed behaviour: the
/// golden fixture below is captured from THIS song on the pre-work build.
pub(crate) fn reference_song() -> Song {
    let mut ev: Vec<(f64, EvKind)> = Vec::new();
    let progs: &[(u8, u8)] = &[
        (0, 24), // nylon
        (1, 25), // steel
        (2, 26), // clean
        (3, 28), // muted
        (4, 30), // drive
        (5, 33), // fingered bass
        (6, 35), // fretless
        (7, 0),  // piano (canary)
        (8, 48), // strings (canary)
    ];
    for &(ch, prog) in progs {
        ev.push((0.0, EvKind::Prog { ch, prog }));
    }
    let mut note = |ch: u8, t: f64, key: u8, vel: u8, dur: f64| {
        ev.push((t, EvKind::NoteOn { ch, key, vel }));
        ev.push((t + dur, EvKind::NoteOff { ch, key }));
    };
    // nylon
    note(0, 0.00, 52, 60, 0.6);
    note(0, 0.70, 57, 90, 0.6);
    note(0, 1.40, 64, 110, 0.9);
    // steel
    note(1, 0.10, 48, 40, 0.6);
    note(1, 0.80, 55, 90, 0.6);
    note(1, 1.50, 64, 120, 0.9);
    // clean
    note(2, 0.20, 55, 70, 0.5);
    note(2, 0.90, 62, 100, 0.5);
    note(2, 1.60, 67, 120, 0.8);
    // muted chugs
    note(3, 0.00, 40, 100, 0.2);
    note(3, 0.25, 40, 80, 0.2);
    note(3, 0.50, 45, 110, 0.2);
    note(3, 0.75, 47, 90, 0.2);
    // drive
    note(4, 0.30, 45, 90, 1.2);
    note(4, 1.60, 52, 115, 1.2);
    // bass
    note(5, 0.00, 28, 70, 0.7);
    note(5, 0.75, 33, 100, 0.7);
    note(5, 1.50, 40, 120, 0.9);
    // fretless
    note(6, 0.20, 31, 60, 0.8);
    note(6, 1.10, 38, 95, 0.8);
    note(6, 2.00, 43, 115, 0.8);
    // piano canary
    note(7, 0.00, 60, 80, 1.0);
    note(7, 1.00, 64, 100, 1.0);
    note(7, 2.00, 67, 110, 1.0);
    // strings canary
    note(8, 0.00, 60, 85, 2.0);
    note(8, 0.50, 67, 95, 1.8);
    // drums (NoteOffs omitted: percussion ignores them)
    let mut hit = |t: f64, key: u8, vel: u8| ev.push((t, EvKind::NoteOn { ch: 9, key, vel }));
    for (i, &t) in [0.0, 0.5, 1.0, 1.5].iter().enumerate() {
        hit(t, 36, if i % 2 == 0 { 110 } else { 92 });
    }
    hit(0.25, 38, 105);
    hit(1.25, 38, 70);
    for i in 0..8 {
        hit(i as f64 * 0.25, 42, if i % 2 == 0 { 90 } else { 60 });
    }
    hit(1.875, 46, 100);
    hit(2.00, 49, 115);
    hit(2.20, 45, 100);
    hit(2.35, 47, 100);
    hit(2.50, 41, 100);
    hit(2.75, 51, 85);
    hit(3.00, 51, 95);

    ev.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
    Song {
        events: ev.into_iter().map(|(sec, kind)| Ev { sec, kind }).collect(),
        seconds: 4.0,
        markers: Vec::new(),
        title: String::new(),
        initial_bpm: 120.0,
    }
}

/// Render options the golden fixture is captured (and compared) with.
pub(crate) fn reference_opts(sr: f32, solo: u16) -> Options {
    Options {
        sr,
        wet: 0.32,
        tail: 1.5,
        delay_s: 0.25,
        samples: false,
        solo,
    }
}

#[allow(dead_code)] // consumed by the Phase-5/6 oracles (32b stereo width etc.)
pub(crate) fn left(stereo: &[f32]) -> Vec<f32> {
    stereo.iter().step_by(2).copied().collect()
}

#[allow(dead_code)] // consumed by the Phase-5/6 oracles (32b stereo width etc.)
pub(crate) fn right(stereo: &[f32]) -> Vec<f32> {
    stereo.iter().skip(1).step_by(2).copied().collect()
}

pub(crate) fn mono(stereo: &[f32]) -> Vec<f32> {
    stereo
        .chunks_exact(2)
        .map(|p| 0.5 * (p[0] + p[1]))
        .collect()
}

// ---------------------------------------------------------------------------
// Oracle 0 — helper calibration on golden synthetic signals
// ---------------------------------------------------------------------------

#[cfg(test)]
mod calibration {
    use super::*;

    fn sine(f: f32, amp: f32, sr: f32, secs: f32) -> Vec<f32> {
        (0..(secs * sr) as usize)
            .map(|i| amp * (std::f32::consts::TAU * f * i as f32 / sr).sin())
            .collect()
    }

    fn noise(seed: u32, sr: f32, secs: f32) -> Vec<f32> {
        let mut rng = Rng::new(seed);
        (0..(secs * sr) as usize).map(|_| rng.white()).collect()
    }

    #[test]
    fn mag_at_resolves_a_pure_tone() {
        let sr = 44100.0;
        let s = sine(1000.0, 1.0, sr, 1.0);
        let on = mag_at(&s, sr, 1000.0);
        let off = mag_at(&s, sr, 2000.0);
        assert!(on > 0.8, "on-bin magnitude {on}");
        assert!(off < 0.1 * on, "octave-away leakage {off} vs {on}");
    }

    #[test]
    fn band_rms_peaks_in_band() {
        let sr = 44100.0;
        let s = sine(1000.0, 1.0, sr, 1.0);
        // Q 2: theory puts an octave-away tone at 1/√(1+Q²(f/f0−f0/f)²) ≈ 0.32×
        let inb = band_rms(&s, sr, 1000.0, 2.0);
        let out = band_rms(&s, sr, 2000.0, 2.0);
        assert!(inb > 0.5, "in-band rms {inb}");
        assert!(out < 0.4 * inb, "octave-away band rms {out} vs {inb}");
        let hp = hp_rms(&s, sr, 4000.0);
        assert!(hp < 0.1 * inb, "hp leakage {hp}");

        let ranged = spectral_band_rms(&s, sr, 800.0, 1_200.0);
        let excluded = spectral_band_rms(&s, sr, 2_000.0, 4_000.0);
        assert!(ranged > 0.4, "range rms {ranged}");
        assert!(excluded < 0.1 * ranged, "range leakage {excluded}/{ranged}");

        let spectral_center = spectral_centroid(&s, sr, 100.0, 4_000.0);
        assert!(
            (spectral_center - 1_000.0).abs() < 20.0,
            "centroid {spectral_center}"
        );
    }

    #[test]
    fn rms_and_pitch_recover_a_unit_sine() {
        let sr = 44100.0;
        let s = sine(440.0, 1.0, sr, 1.0);
        let r = rms(&s);
        assert!(
            (r - std::f32::consts::FRAC_1_SQRT_2).abs() < 0.01,
            "unit-sine rms {r}"
        );
        let p = pitch_hz(&s, sr);
        assert!((p - 440.0).abs() < 5.0, "pitch {p}");
    }

    #[test]
    fn centroid_orders_noise_above_low_sine() {
        let sr = 44100.0;
        let n = centroid(&noise(7, sr, 1.0), sr);
        let t = centroid(&sine(200.0, 1.0, sr, 1.0), sr);
        assert!(n > t * 2.0, "noise centroid {n} vs 200 Hz sine {t}");
    }

    #[test]
    fn portable_render_signature_detects_level_spectrum_and_envelope_drift() {
        let sr = 44100.0;
        let mut base: Vec<f32> = (0..sr as usize)
            .map(|i| {
                let t = i as f32 / sr;
                let env = if t < 0.5 { 1.0 } else { 0.55 };
                env * (0.7 * (std::f32::consts::TAU * 440.0 * t).sin()
                    + 0.3 * (std::f32::consts::TAU * 3520.0 * t).sin())
            })
            .collect();
        let windows = ((0.05, 0.95), (0.10, 0.35), (0.65, 0.90));
        let expected = render_signature(&base, sr, windows.0, windows.1, windows.2);

        let gain = 10f32.powf(0.25 / 20.0);
        let louder: Vec<f32> = base.iter().map(|&x| x * gain).collect();
        assert!(!signature_matches(
            render_signature(&louder, sr, windows.0, windows.1, windows.2),
            expected
        ));

        let mut lp = OnePole::lowpass(1200.0, sr);
        let darker: Vec<f32> = base.iter().map(|&x| lp.process(x)).collect();
        assert!(!signature_matches(
            render_signature(&darker, sr, windows.0, windows.1, windows.2),
            expected
        ));

        for x in &mut base[(0.5 * sr) as usize..] {
            *x *= 0.95;
        }
        assert!(!signature_matches(
            render_signature(&base, sr, windows.0, windows.1, windows.2),
            expected
        ));
    }

    #[test]
    fn t60_of_recovers_a_known_decay() {
        let sr = 44100.0;
        let t60 = 0.5f32;
        let s: Vec<f32> = (0..(sr as usize))
            .map(|i| {
                let t = i as f32 / sr;
                10f32.powf(-3.0 * t / t60) * (std::f32::consts::TAU * 500.0 * t).sin()
            })
            .collect();
        let m = t60_of(&s, sr);
        assert!((m - t60).abs() < 0.1 * t60, "measured t60 {m} vs {t60}");
    }

    #[test]
    fn inter_corr_calibrates() {
        let sr = 44100.0;
        let a = noise(3, sr, 0.5);
        let b = noise(4, sr, 0.5);
        let inv: Vec<f32> = a.iter().map(|&x| -x).collect();
        assert!(inter_corr(&a, &a) > 0.99);
        assert!(inter_corr(&a, &b).abs() < 0.1);
        assert!(inter_corr(&a, &inv) < -0.99);
    }

    #[test]
    fn peak_locate_finds_a_tone() {
        let sr = 44100.0;
        let s = sine(700.0, 1.0, sr, 0.5);
        let p = peak_locate(&s, sr, 400.0, 1200.0);
        assert!((p - 700.0).abs() < 8.0, "located {p}");
    }

    #[test]
    fn env_autocorr_recovers_am_rate() {
        let sr = 44100.0;
        let s: Vec<f32> = (0..(sr as usize))
            .map(|i| {
                let t = i as f32 / sr;
                (1.0 + 0.8 * (std::f32::consts::TAU * 60.0 * t).sin())
                    * (std::f32::consts::TAU * 6000.0 * t).sin()
            })
            .collect();
        let (peak, rate) = env_autocorr_peak(&s, sr, 1.0 / 100.0, 1.0 / 40.0);
        assert!(peak > 0.3, "autocorr peak {peak}");
        assert!((rate - 60.0).abs() < 8.0, "AM rate {rate}");
    }

    /// Oracle-0 for `mean_period_samples`: a pure tone's period is recovered
    /// far below the tenth-of-a-sample precision the waveguide `loop_comp`
    /// measurement needs, and a small noise floor does not disturb it.
    #[test]
    fn mean_period_recovers_a_known_tone() {
        let sr = 44100.0;
        let f = 130.8127; // C3
        let want = sr / f;
        let clean = sine(f, 0.5, sr, 2.0);
        let p = mean_period_samples(&clean, sr, f);
        assert!(
            (p - want).abs() < 0.02,
            "clean period {p:.4} vs {want:.4} samples"
        );
        let mut rng = Rng::new(3);
        let noisy: Vec<f32> = clean.iter().map(|&x| x + 0.02 * rng.white()).collect();
        let p = mean_period_samples(&noisy, sr, f);
        assert!(
            (p - want).abs() < 0.05,
            "noisy period {p:.4} vs {want:.4} samples"
        );
    }

    /// Oracle-0 for `fm_mod_rate`: a ±0.2 % FM at 4.8 Hz on a C3 carrier — the
    /// BowedString vibrato's exact shape — is detected confidently at the right
    /// rate, while the same depth at the 16×-slow bug rate (0.29 Hz) yields no
    /// confident in-band detection. Calibrated before the bowed-vibrato oracle
    /// trusts it.
    #[test]
    fn fm_mod_rate_recovers_synthetic_vibrato() {
        let sr = 44100.0;
        let f0 = 130.8127f32;
        let fm = |mod_hz: f32| -> Vec<f32> {
            let mut rng = Rng::new(9);
            let mut phase = 0.0f64;
            (0..(4.0 * sr) as usize)
                .map(|i| {
                    let t = i as f32 / sr;
                    let inst = f0 as f64
                        * (1.0 + 0.002 * (std::f64::consts::TAU * mod_hz as f64 * t as f64).sin());
                    phase += std::f64::consts::TAU * inst / sr as f64;
                    (phase.sin() * 0.5) as f32 + 0.01 * rng.white()
                })
                .collect()
        };
        let (peak, rate) = fm_mod_rate(&fm(4.8), sr, f0, 2.0, 10.0);
        assert!(peak > 0.6, "true vibrato autocorr peak {peak:.3}");
        assert!(
            (rate - 4.8).abs() / 4.8 < 0.06,
            "true vibrato rate {rate:.2} Hz"
        );
        let (slow_peak, slow_rate) = fm_mod_rate(&fm(0.29), sr, f0, 2.0, 10.0);
        assert!(
            slow_peak < 0.5 || (slow_rate - 4.8).abs() / 4.8 > 0.25,
            "16x-slow vibrato must not read as a named-rate detection: \
             peak {slow_peak:.3} rate {slow_rate:.2} Hz"
        );
    }

    #[test]
    fn flatness_separates_noise_from_tone() {
        let sr = 44100.0;
        let fn_ = flatness(&noise(9, sr, 1.0), sr, 500.0, 8000.0);
        let ft = flatness(&sine(1000.0, 1.0, sr, 1.0), sr, 500.0, 8000.0);
        assert!(fn_ > 0.4, "noise flatness {fn_}");
        assert!(ft < 0.2, "tone flatness {ft}");
        assert!(fn_ > 3.0 * ft, "noise {fn_} vs tone {ft}");
    }

    /// Oracle-0 for `kurtosis`: smooth bandpass-filtered white reads ≈ 3
    /// (Gaussian-ish via the filter's central-limit averaging), while a sparse
    /// gated grain train reads far higher — so a grainy/smooth ratio cleanly
    /// separates the two. Calibrated here before P-S1's snare oracle trusts it.
    #[test]
    fn kurtosis_flags_grain_over_smooth_noise() {
        let sr = 44100.0;
        // smooth: bandpassed uniform white — the biquad's memory pushes the
        // output toward Gaussian, so kurtosis lands near 3.0.
        let raw = noise(11, sr, 0.5);
        let mut bp = Biquad::bandpass(4000.0, 3.0, sr);
        let smooth: Vec<f32> = raw.iter().map(|&x| bp.process(x)).collect();
        let k_smooth = kurtosis(&smooth);
        // grain: a sparse click train (~2.5% of samples are unit impulses) —
        // leptokurtic, kurtosis ≈ 1/q ≫ 3.
        let mut rng = Rng::new(5);
        let grain: Vec<f32> = (0..(0.5 * sr) as usize)
            .map(|_| {
                let u = rng.white();
                if u.abs() > 0.95 {
                    u.signum()
                } else {
                    0.0
                }
            })
            .collect();
        let k_grain = kurtosis(&grain);
        assert!(
            (k_smooth - 3.0).abs() < 1.5,
            "smooth-noise kurtosis {k_smooth} (expect ≈ 3)"
        );
        assert!(
            k_grain > 3.0 * k_smooth,
            "grain kurtosis {k_grain} not ≫ smooth {k_smooth}"
        );
    }

    /// Oracle-0 for the cymbal-bloom trajectory (`traj` + `traj_peak_time_s`):
    /// calibrated on SYN-A (a known low→high migrating spectrum whose high band
    /// blooms at 51 ms) and SYN-B (pure decays from t=0, no bloom) before C1's
    /// crash oracle trusts it. SYN-A's high band must peak ~51 ms after t=0 while
    /// its low band peaks immediately; SYN-B's high band must NOT bloom.
    #[test]
    fn bloom_trajectory_machinery_calibrates() {
        let sr = 44100.0;
        let syn = |bloom: bool| -> Vec<f32> {
            let mut rng = Rng::new(11);
            (0..(0.3 * sr) as usize)
                .map(|i| {
                    let t = i as f32 / sr;
                    let low = (-t / 0.20).exp() * (std::f32::consts::TAU * 900.0 * t).sin();
                    let high_env = if bloom {
                        // alpha function peaking at 51 ms, value 1 at the peak
                        let x = t / 0.051;
                        x * x * (2.0 * (1.0 - x)).exp()
                    } else {
                        (-t / 0.06).exp() // legacy: pure decay from t=0
                    };
                    let high = high_env
                        * 0.5
                        * ((std::f32::consts::TAU * 7000.0 * t).sin()
                            + (std::f32::consts::TAU * 9100.0 * t).sin());
                    low + high + 0.01 * rng.white()
                })
                .collect()
        };
        let a = syn(true);
        let b = syn(false);
        let low_a = traj_peak_time_s(&traj(&a, sr, 700.0, 1200.0));
        let high_a = traj_peak_time_s(&traj(&a, sr, 6000.0, 11000.0));
        let high_b = traj_peak_time_s(&traj(&b, sr, 6000.0, 11000.0));
        println!(
            "BLOOM machinery: SYN-A low={:.1}ms high={:.1}ms; SYN-B high={:.1}ms",
            low_a * 1000.0,
            high_a * 1000.0,
            high_b * 1000.0
        );
        // SYN-A: low peaks immediately, high blooms clearly later.
        assert!(low_a <= 0.020, "SYN-A low peak too late: {low_a}");
        // The first-crossing estimator reads ~37 ms for this true-51 ms bloom: it
        // fires when the WINDOWED envelope first reaches 0.9·max, ~13 ms ahead of
        // the true peak. This ~13 ms early bias is exactly why C1's high-band
        // bloom window is [20, 90] ms, not [40, 80] — SYN-A pins the bias here.
        assert!(
            (0.028..=0.048).contains(&high_a),
            "SYN-A high bloom time {high_a} (expect ~37 ms measured for a true 51 ms bloom)"
        );
        assert!(
            high_a - low_a >= 0.015,
            "SYN-A no bloom delay: {}",
            high_a - low_a
        );
        // SYN-B: high also peaks at t=0 → the detector must NOT report a bloom.
        assert!(high_b <= 0.020, "SYN-B false bloom: high={high_b}");
    }
}

// ---------------------------------------------------------------------------
// Phase-0 guards: oracles 34 (golden mix balance), 35 (determinism),
// 36 (GM routing), 38 (compute budget, manual advisory)
// ---------------------------------------------------------------------------

#[cfg(test)]
mod guards {
    use super::*;

    const SR: f32 = 44100.0;

    /// Golden per-channel fixture: (channel, rms dBFS, centroid Hz), captured
    /// from `reference_song()` per-channel solo renders on the PRE-WORK build
    /// (v0.7.0 main). Deliberate per-family voicing changes UPDATE this table
    /// in the same commit, with the reason in the commit message (HLD §5.2
    /// oracle-34 procedure) — it is a drift trip-wire, not a freeze.
    /// Regenerate with: cargo test print_golden_fixture -- --ignored --nocapture
    const GOLDEN: &[(u8, f32, f32)] = &[
        // Re-captured after Phase 3 (the Cabinet): CLEAN (ch 2) deliberately
        // darker above 4.5 kHz, DRIVE (ch 4) re-voiced through the new cab;
        // the Phase-1 velocity law shifts the guitar/bass channels slightly
        // at their written velocities. The canaries (ch 7 piano, ch 8
        // strings) are BIT-EXACT vs the pre-work capture — proof the
        // untouched families are untouched.
        // Re-captured after Phase 6 (KS core): K1's cubic tap keeps treble
        // ring (guitars brighter), the K4 wound split darkens low DRIVE keys,
        // and the re-voiced bass presets sit under the wound factor. The
        // canaries (ch 7 piano, ch 8 strings) remain BIT-EXACT vs pre-work.
        // Re-captured after the flatwound bass revoice (BASS/FRETLESS presets,
        // GM 33/35): the two bass channels (ch 5, ch 6) now sit deeper and
        // darker — more sub weight, highs rolled off (centroid 369->295 and
        // 211->195 Hz). Every other channel, INCLUDING the ch 7 piano and ch 8
        // strings canaries, is BIT-EXACT vs pre-revoice: the change is
        // contained to the two bass presets, as intended.
        // Re-captured after GM 35 fretless mwah: only ch 6's displayed RMS and
        // centroid change at the displayed precision and the master peak moves
        // by 0.00002; every other displayed channel, including canaries, is
        // unchanged.
        // Re-captured after guitar v2 unit A (pickup coil RLC on CLEAN /
        // MUTED / DRIVE): ch 2 brighter (4.2 kHz single-coil peak), ch 3 a
        // touch darker (3 kHz coil under the palm), ch 4 brighter through the
        // drive (3.3 kHz humbucker peak). The nylon/steel/bass/piano/strings
        // rows are BIT-EXACT vs the pre-work capture (see also the
        // v2_untouched_pluck_signatures_are_stable portable signature guard).
        // Re-captured after guitar v2 unit C (Drive v2: two stages + sag):
        // ch 4 sits 7.0 dB higher and darker — the sag compressor holds
        // decayed note tails up, and a decayed KS tail is fundamental-heavy
        // (unit D's sustainer + the drive's re-harmonization act on the
        // string itself). Loud-point level match vs v1 is +0.3/−0.1 dB
        // (drive_level_probe); the tail lift is the feature, knob = sag_target.
        // Every other row, including ch 2/ch 3, is BIT-EXACT vs the unit-A
        // capture — the drive insert touches programs 29/30 only.
        // Re-captured after guitar v2 unit B (the 26/27 split): ch 2 is now
        // the JAZZ hollowbody — warmer and rounder (centroid 1216 -> 855 Hz)
        // by design; every other row is BIT-EXACT vs the unit-C capture.
        // Re-captured after guitar v2 unit D (the string sustainer): ch 4's
        // held notes now hold their fundamental instead of dying (centroid
        // 727 -> 468 Hz, RMS ~unchanged) — the V6b oracle pins the post-Drive
        // 2f0 content so the held tone stays harmonic, and DRIVE_LEAD's
        // 11 kHz damper is the brighter opt-in lead. All other rows
        // BIT-EXACT vs the unit-B capture.
        // Re-captured after the voice-quality overhaul §2.6 deleted the
        // Drive's inverted sag gain (it slewed UP to 4x as the note decayed
        // — a real amp clips hardest at the pick): ch 4 is 4.4 dB quieter
        // and brighter (centroid 468 -> 814 Hz) with the tail no longer
        // artificially held up and fundamental-heavy; held-note sustain now
        // lives at the string layer (DRIVE.sustain 0.35 -> 0.5) and O-ATTACK
        // pins the no-late-bloom shape. All other rows BIT-EXACT vs the
        // unit-D capture — the drive insert touches programs 29/30 only.
        (0, -40.22, 899.2),
        (1, -41.50, 2030.2),
        (2, -41.49, 855.0),
        (3, -39.97, 485.9),
        // Re-captured (ch 4 only) after round 2's driven-guitar rework
        // ("clean, dark sustain"): hotter drive staging (DRIVE amp/sustain/
        // bright + Drive g1/bias, post level-re-matched end-to-end) leaves
        // ch 4 −0.6 dB and darker (centroid 814 → 545 Hz).
        // Re-captured (ch 4 only) after round-3 U2 restored the main/alt
        // contrast: the default DRIVE bank lost its e-bow hold (sustain
        // 0.7 → 0.0), so held tails decay instead of settling into the
        // fundamental-heavy hold — near-identical RMS (−0.1 dB) but brighter
        // on average (centroid 545 → 808 Hz). Every other row, including the
        // ch 7 piano and ch 8 strings canaries, is BIT-EXACT vs the prior
        // capture: the change is contained to the default drive preset.
        (4, -32.96, 808.2),
        // Re-captured after the muffled-flatwound bass re-voice (kick + big sub
        // + muffle, GM33): ch 5 louder (the low-end WEIGHT Arthur approved) and
        // darker (the muffle). Every other channel — INCLUDING the ch 7 piano
        // and ch 8 strings canaries — is BIT-EXACT vs the pre-revoice capture:
        // the change is contained to the BASS preset, as intended.
        (5, -19.40, 241.3),
        (6, -27.13, 194.4),
        (7, -24.35, 567.6),
        // Re-captured (ch 8 only) after the SC-55-referenced per-program loudness
        // trim: StringEns1 (GM 48) is PROGRAM_TRIM_DB[48] = +5.5 dB louder to match
        // the SC-55's section balance. RMS -37.21 -> -31.72 dB (+5.49); centroid
        // 2382 -> 2381 Hz — unchanged, proving the trim is level-only (timbre-
        // neutral). Every other row, including the ch 7 piano canary, is bit-exact
        // vs the prior capture: the trim touches only the corrected programs, and
        // this reference song uses just one (ch 8). See engine::PROGRAM_TRIM_DB.
        (8, -31.72, 2380.6),
        // Re-captured after the default drum kit moved from V1 to V3:
        // channel 10 is deliberately brighter and slightly louder. Re-pinned
        // after the later V3 cymbal-density work moved the fixture within its
        // guard tolerance.
        // Re-captured after the D10d kit-balance rebalance (hi-hats up, ride/crash
        // down, snare/toms forward) + the D10e +6 dB drum-bus forward level: ch 10
        // is 5.1 dB louder and brighter (centroid 685 -> 737 Hz, hats up), and the
        // master peak nearly doubles. Every melodic channel (0-8), including the
        // ch 7 piano and ch 8 strings canaries, is BIT-EXACT vs the prior capture —
        // proof the change is contained to the drum bus.
        (9, -17.16, 737.4),
    ];
    /// Full-mix pre-normalise master peak (re-captured with the table above).
    const GOLDEN_MASTER_PEAK: f32 = 2.27034;

    const RMS_TOL_DB: f32 = 2.5;
    const CENTROID_TOL: f32 = 0.20; // ±20% spectral-balance clause

    fn solo_render(ch: u8) -> Vec<f32> {
        let song = reference_song();
        engine::render(&song, &reference_opts(SR, 1u16 << ch)).0
    }

    fn db(x: f32) -> f32 {
        20.0 * x.max(1e-12).log10()
    }

    /// Oracle 34 (guard): per-channel RMS within ±2.5 dB and centroid within
    /// ±20% of the committed golden fixture; master peak within ±2.5 dB.
    #[test]
    fn golden_mix_balance_holds() {
        assert!(
            GOLDEN.len() > 1 && GOLDEN_MASTER_PEAK > 0.0,
            "golden fixture not captured — run print_golden_fixture on the pre-work build"
        );
        for &(ch, g_rms_db, g_cent) in GOLDEN {
            let out = solo_render(ch);
            let m = mono(&out);
            let r = db(rms(&m));
            assert!(
                (r - g_rms_db).abs() <= RMS_TOL_DB,
                "ch {ch}: rms {r:.2} dB vs golden {g_rms_db:.2} dB"
            );
            let c = centroid(&m, SR);
            assert!(
                (c / g_cent - 1.0).abs() <= CENTROID_TOL,
                "ch {ch}: centroid {c:.0} Hz vs golden {g_cent:.0} Hz"
            );
        }
        let song = reference_song();
        let (_, stats) = engine::render(&song, &reference_opts(SR, 0xFFFF));
        assert!(
            (db(stats.peak) - db(GOLDEN_MASTER_PEAK)).abs() <= RMS_TOL_DB,
            "master peak {:.3} vs golden {GOLDEN_MASTER_PEAK:.3}",
            stats.peak
        );
    }

    /// Regenerates the GOLDEN table (paste-ready). `--ignored --nocapture`.
    #[test]
    #[ignore]
    fn print_golden_fixture() {
        println!("    const GOLDEN: &[(u8, f32, f32)] = &[");
        for ch in [0u8, 1, 2, 3, 4, 5, 6, 7, 8, 9] {
            let out = solo_render(ch);
            let m = mono(&out);
            println!(
                "        ({ch}, {:.2}, {:.1}),",
                db(rms(&m)),
                centroid(&m, SR)
            );
        }
        let song = reference_song();
        let (_, stats) = engine::render(&song, &reference_opts(SR, 0xFFFF));
        println!("    ];");
        println!("    const GOLDEN_MASTER_PEAK: f32 = {:.5};", stats.peak);
    }

    /// Oracle 35 (guard): two same-input renders are bit-identical.
    #[test]
    fn determinism_bit_identical() {
        let song = reference_song();
        let a = engine::render(&song, &reference_opts(SR, 0xFFFF)).0;
        let b = engine::render(&song, &reference_opts(SR, 0xFFFF)).0;
        assert_eq!(a.len(), b.len());
        assert!(
            a.iter().zip(&b).all(|(x, y)| x.to_bits() == y.to_bits()),
            "same-seed renders differ"
        );
    }

    /// Oracle 36 (structural half): `voices::make` routes each GM program to
    /// the intended voice/preset, and the Drive insert decision is pinned.
    /// This table pins the CURRENT routing; Phases 4/5 update it when the new
    /// presets (HARMONIC, UPRIGHT, PICK, SLAP, SynthBass) land.
    #[test]
    fn gm_routing_pins_voice_kinds() {
        let cases: &[(u8, &str)] = &[
            (0, "modal"),
            (6, "HARPSICHORD"), // voice-quality §2.10: plucked, not additive
            (7, "CLAVINET"),
            (8, "modal"),
            (16, "organ"),
            // 19 rejoined the drawbar arm in round 2 (CathedralOrgan retired);
            // both banks are the same organ() voice now
            (19, "organ"),
            (22, "reed"), // voice-quality §2.11: free reed, not drawbar organ
            (24, "NYLON"),
            (25, "STEEL"),
            (26, "JAZZ"), // guitar v2 unit B: the 26/27 split
            (27, "CLEAN"),
            (28, "MUTED"),
            (29, "DRIVE"),
            (30, "DRIVE"),
            (31, "HARMONIC"), // Phase 4 (G7)
            (32, "UPRIGHT"),  // Phase 4 (B2)
            (33, "BASS"),
            (34, "PICK"), // Phase 4 (B2)
            (35, "FRETLESS"),
            (36, "SLAP"),      // Phase 4 (B2): thumb slap
            (37, "SLAP_POP"),  // Stage 5a (B2): bridge pop
            (38, "synthbass"), // Phase 5 (B4)
            (39, "synthbass"), // Phase 5 (B4)
            (40, "bowed"),
            (46, "HARP"),
            (47, "modal"),
            (48, "sawstack"),
            (52, "choir2"), // GM 52-54: ChoirV2 formant engine (2026.07.10)
            (72, "wind"),
            // Synth FX 96-103 (Stage 3): all route to the `Fx` wrapper voice.
            // 98 (crystal) is the inert preset — same "fx" kind, frozen audio.
            (96, "fx"),
            (97, "fx"),
            (98, "fx"),
            (99, "fx"),
            (100, "fx"),
            (101, "fx"),
            (102, "fx"),
            (103, "fx"),
            (104, "SITAR"),
            (105, "BANJO"),
            (106, "SHAMISEN"),
            (107, "KOTO"),
            (109, "reed"),
            (110, "bowed"),
            (111, "reed"),
            (108, "modal"),
            (112, "modal"),
            (113, "modal"),
            (114, "modal"),
            (115, "modal"),
            (116, "modal"),
            (117, "modal"),
            (118, "modal"),
            (119, "reverse_cym"),
            (120, "sfx"),
            (127, "sfx"),
        ];
        for &(prog, want) in cases {
            let v = crate::voices::make(prog, 60, 100, SR, 7, false);
            assert_eq!(v.kind(), want, "program {prog}");
        }
        // drums route through drums::make
        let d = crate::drums::make(38, 100, SR, 7, crate::drums::Kit::V1, false, 0)
            .expect("snare voice");
        assert_eq!(d.kind(), "drum");
        // the Drive-insert decision, single source of truth
        for p in 0u8..=127 {
            assert_eq!(
                engine::needs_drive(p),
                matches!(p, 29 | 30),
                "needs_drive({p})"
            );
        }
    }

    /// Oracle 38 (manual advisory, NOT a merge gate): render wall-clock for
    /// the reference song. Run by hand:
    /// cargo test render_budget_advisory -- --ignored --nocapture
    #[test]
    #[ignore]
    fn render_budget_advisory() {
        let song = reference_song();
        let started = std::time::Instant::now();
        let (out, stats) = engine::render(&song, &reference_opts(SR, 0xFFFF));
        let secs = started.elapsed().as_secs_f64();
        println!(
            "reference render: {secs:.2} s wall, {} samples, {} voices, peak {:.3}",
            out.len(),
            stats.voices_spawned,
            stats.peak
        );
        assert!(
            secs < 120.0,
            "render blew the generous ceiling: {secs:.1} s"
        );
    }
}

// ---------------------------------------------------------------------------
// Stage 0 (woodwind/LA HLD §9.1): synth-wide anti-clone distinctness matrix
// ---------------------------------------------------------------------------

/// Every GM program should render as an audibly distinct instrument from the
/// other seven in its family. This matrix renders all 128 programs (model only,
/// `samples=false` — the layer the per-program preset tables control, and where
/// the collapses are worst) at fixed probe keys, reduces each to a small timbre
/// feature vector, and asserts every within-family pair differs by at least
/// [`EPS`] on its most-distinguishing feature — UNLESS the pair is on [`ALLOW`].
///
/// Every entry is a [`Why::Collapse`] — a KNOWN current collapse the woodwind/LA
/// HLD schedules a fix for. Deleting the entry is part of that stage's definition
/// of done, and the matrix then proves the fix landed.
/// `allowlisted_collapses_are_really_clones` fails loudly the moment a stage
/// differentiates a family, forcing the delete. (There is no longer any
/// "legitimately near-identical" exemption: Stage 4 split the last such pair,
/// Synth Strings 50/51, into genuinely distinct instruments.)
///
/// A brand-new accidental collapse (a future edit that makes two programs render
/// the same) is on neither list, so it fails here — exactly the guard the pipe
/// family's 8→2 collapse never had. The pre-existing drift/canary freeze lives in
/// `mod guards` (`golden_mix_balance_holds`, `determinism_bit_identical`); this
/// module adds only the missing distinctness axis.
///
/// **Blind spot (round-3 plan §2.2, kept deliberately):** this matrix renders
/// `samples: false` and its 5-feature vector carries zero temporal information,
/// so it certifies MODEL-arm divergence only — it cannot see a clone whose
/// audible sameness lives in a shared LA sample layer, a shared onset, or a
/// shared envelope (GM 0/1, 0/3 and 4/5 all scored "distinct" here while the
/// ear called them clones — measured 2026-07-16: 0.179/0.225/0.363, above the
/// accepted-distinct sax pair 64/65 at 0.170). It stays as the
/// model-preset-layer tripwire (byte-level arm collapse regardless of sample
/// masking); the ear-facing anti-clone gate is `perceptual_distinctness` below
/// (samples ON, two-tier, temporal features).
#[cfg(test)]
mod distinctness {
    use super::*;

    const SR: f32 = 44100.0;
    const NKEYS: usize = 2;
    /// Two probe keys spanning ~two octaves; the register-dependent voices then
    /// differ on more than one note, the register-independent collapses on none.
    const PROBE_KEYS: [u8; NKEYS] = [48, 72];
    const VEL: u8 = 100;
    const SECS: f32 = 0.7;
    const SEED: u32 = 7;

    /// Max relative feature difference below which two renders are treated as the
    /// same instrument. Current hard collapses render byte-identically (score 0);
    /// genuinely distinct programs score far higher (the exemplar brass/reed
    /// families clear [`MARGIN`], pinned by `epsilon_is_calibrated_on_the_good_families`).
    const EPS: f32 = 0.03;
    /// The exemplar good families must separate every within-family pair by at
    /// least this (1.5×EPS), so `EPS` sits safely below true instrument-to-
    /// instrument distance (HLD §12 Q1). The binding constraint is the
    /// soprano/alto sax pair (GM 64/65 ≈ 0.055) — genuinely the two closest
    /// good-family instruments — so the headroom below it is deliberately modest.
    const MARGIN: f32 = 1.5 * EPS;

    /// Timbre feature vector: [centroid Hz, flatness, odd/even harmonic ratio,
    /// HF fraction, h2/h1]. Chosen to read timbre, not pitch (harmonic ratios are
    /// pitch-relative; centroid/flatness are compared only at matched probe keys).
    type Feat = [f32; 5];
    /// One program's feature vector at each probe key (kept per-key, not averaged
    /// — see [`score`]).
    type FeatSet = [Feat; NKEYS];
    /// Per-feature floors: keep a near-zero feature from manufacturing a large
    /// relative difference. Same order as `Feat`.
    const FLOOR: Feat = [100.0, 0.05, 0.10, 0.02, 0.05];

    #[derive(Clone, Copy)]
    enum Why {
        /// Known current collapse; the named HLD stage removes this entry.
        Collapse(u8),
    }

    /// Unordered program pairs exempt from the distinctness assertion, kept sorted
    /// (a < b). Every `Collapse` entry cites the HLD stage that deletes it.
    const ALLOW: &[(u8, u8, Why)] = &[
        // -- Stage 1: Pipe 72-79 — DONE. The `whistle` bool became an 8-entry
        //    WindPreset table, so all 28 pipe pairs are now genuinely distinct
        //    instruments and carry no exemption. (This is the pattern: a stage's
        //    definition of done includes deleting its entries, after which the
        //    matrix itself proves the fix.)
        // -- Stage 2: Synth Pad 88-95 — DONE. 88,89,90,91,92,93,94 shared one base
        //    pad; each moving member now has its own identity (88 struck / 90
        //    polysynth / 91 choir-formant / 92 bowed-swell / 93 metallic-clang /
        //    94 halo-noise) over the shared SawStack, chiefly via the one-shot
        //    filter envelope. 89 (warm) and 95 (sweep) are frozen bit-for-bit. All
        //    21 former collapses are deleted and the matrix proves the split. --
        // -- Stage 3: Synth FX 96-103 — DONE. The crystal bell {96,98,100,102} and
        //    base pad {97,99,101,103} became eight distinct `Fx` presets separated
        //    by TIME and RANDOMNESS (96 aperiodic droplets / 97 opens / 99 closes /
        //    100 blooms late / 101 lurches / 102 repeats / 103 falls), over the same
        //    two cores. 98 (crystal) is frozen bit-for-bit (inert wrapper). All nine
        //    former collapses are deleted and the matrix now proves the split. --
        // -- Stage 4: Ensemble 48-55 — DONE. 50/51 (Synth Strings 1/2) became a
        //    divide-down string machine (`synth_strings`, shared BBD chorus),
        //    distinct from the acoustic section 48/49 and from each other, so
        //    all three former collapses (48/50, 48/51, 50/51) are deleted and the
        //    matrix now proves the split. --
        // -- Stage 5: minor collapses --
        // Stage 5a — DONE: organ 16/17 (17 got the Percussion tab + thinned
        // drawbars) and bass 36/37 (37 became the bridge-pop SLAP_POP) are split,
        // so (16,17) and (36,37) are deleted and the matrix proves each fix.
        // (26, 27) was a Collapse: both shared CLEAN. Guitar v2 split them into
        // JAZZ (neck hollowbody) and CLEAN (bright single-coil) — differentiated,
        // so the stale collapse entry is deleted (this oracle's own contract).
        // -- Stage 7a: piano 0-3 — DONE (round 2). The GM0..=3 alias split into
        //    the grand (0), a brighter-voiced grand (1), a CP-style electric
        //    grand (2, higher inharmonicity / fast decay / no soundboard
        //    aftersound) and the wide-trichord honky-tonk (3); all six former
        //    collapse entries are deleted and the matrix proves the split. --
        (29, 30, Why::Collapse(5)), // guitar: two "overdrive/distortion" share DRIVE — Stage 7b
    ];

    fn allow_reason(a: u8, b: u8) -> Option<Why> {
        let (lo, hi) = if a <= b { (a, b) } else { (b, a) };
        ALLOW
            .iter()
            .find(|&&(x, y, _)| x == lo && y == hi)
            .map(|&(_, _, w)| w)
    }

    fn render(program: u8, key: u8) -> Vec<f32> {
        let mut v = crate::voices::make(program, key, VEL, SR, SEED, false);
        let mut buf = vec![0f32; (SECS * SR) as usize];
        v.render(&mut buf);
        buf
    }

    fn f0_of(key: u8) -> f32 {
        440.0 * 2f32.powf((key as f32 - 69.0) / 12.0)
    }

    fn feat_one(seg: &[f32], f0: f32) -> Feat {
        // Skip the 50 ms onset for a stable steady-state read.
        let start = ((0.05 * SR) as usize).min(seg.len());
        let body = &seg[start..];
        let m = |mult: f32| mag_at(body, SR, f0 * mult);
        let odd = m(1.0) + m(3.0) + m(5.0);
        let even = m(2.0) + m(4.0) + m(6.0);
        [
            centroid(body, SR),
            flatness(body, SR, 500.0, 9000.0),
            odd / (even + 1e-6),
            hp_rms(body, SR, 3000.0) / rms(body).max(1e-9),
            m(2.0) / (m(1.0) + 1e-6),
        ]
    }

    fn features(program: u8) -> FeatSet {
        std::array::from_fn(|k| feat_one(&render(program, PROBE_KEYS[k]), f0_of(PROBE_KEYS[k])))
    }

    /// Relative feature difference at one probe key: the max over features of
    /// `|a−b| / (|a|+|b|+floor)`. Byte-identical renders → 0; distinct → higher.
    fn feat_dist(a: &Feat, b: &Feat) -> f32 {
        (0..5)
            .map(|i| (a[i] - b[i]).abs() / (a[i].abs() + b[i].abs() + FLOOR[i]))
            .fold(0.0, f32::max)
    }

    /// Distance between two programs: the max over probe keys of [`feat_dist`].
    /// Comparing like-for-like per key (rather than averaging the keys' features
    /// first) keeps byte-identical collapses at 0 while giving genuinely distinct
    /// programs full headroom — averaging could cancel a bright-low / dark-high
    /// difference of opposite sign across the two keys.
    fn score(a: &FeatSet, b: &FeatSet) -> f32 {
        a.iter()
            .zip(b)
            .map(|(x, y)| feat_dist(x, y))
            .fold(0.0, f32::max)
    }

    /// Rendered once (seed fixed → deterministic), shared across the tests below.
    fn all_feats() -> &'static [FeatSet] {
        static CELL: std::sync::OnceLock<Vec<FeatSet>> = std::sync::OnceLock::new();
        CELL.get_or_init(|| (0..128u8).map(features).collect())
    }

    /// The headline guard: within every GM family, no two programs render as the
    /// same instrument unless explicitly allowlisted.
    #[test]
    fn every_gm_family_is_free_of_unexpected_clones() {
        let feats = all_feats();
        let mut failures = Vec::new();
        for fam in 0..16u8 {
            let base = fam * 8;
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let s = score(&feats[a as usize], &feats[b as usize]);
                    if s < EPS && allow_reason(a, b).is_none() {
                        failures.push(format!(
                            "GM {a} vs {b}: score {s:.4} < EPS {EPS} (unexpected clone)"
                        ));
                    }
                }
            }
        }
        assert!(
            failures.is_empty(),
            "anti-clone matrix — unexpected clones:\n{}",
            failures.join("\n")
        );
    }

    /// Every `Collapse` entry must still be an actual clone on this build. When a
    /// stage differentiates the family, this fails — and deleting the now-stale
    /// entry is part of that stage's definition of done.
    #[test]
    fn allowlisted_collapses_are_really_clones() {
        let feats = all_feats();
        for &(a, b, why) in ALLOW {
            let Why::Collapse(stage) = why;
            let s = score(&feats[a as usize], &feats[b as usize]);
            assert!(
                s < EPS,
                "GM {a} vs {b} is allowlisted as a Stage-{stage} collapse but now \
                 scores {s:.4} >= EPS {EPS} — already differentiated; delete this ALLOW entry"
            );
        }
    }

    /// EPS calibration: the exemplar per-program families (brass 56-63, reed
    /// 64-71) must separate every within-family pair well above EPS, so EPS sits
    /// safely below genuine instrument-to-instrument distance (HLD §12 Q1).
    #[test]
    fn epsilon_is_calibrated_on_the_good_families() {
        let feats = all_feats();
        for (base, name) in [(56u8, "brass"), (64u8, "reed")] {
            let mut min_s = f32::INFINITY;
            let (mut ma, mut mb) = (0u8, 0u8);
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let s = score(&feats[a as usize], &feats[b as usize]);
                    if s < min_s {
                        min_s = s;
                        (ma, mb) = (a, b);
                    }
                }
            }
            assert!(
                min_s >= MARGIN,
                "{name}: tightest pair GM {ma}/{mb} scores {min_s:.4} < MARGIN {MARGIN} — \
                 EPS {EPS} has too thin a margin below the good families"
            );
        }
    }

    /// Calibration aid (not a gate): print every within-family pair's score, and
    /// its allowlist tag. Run: `cargo test print_distinctness_matrix -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn print_distinctness_matrix() {
        let feats = all_feats();
        for fam in 0..16u8 {
            let base = fam * 8;
            println!("--- GM family {}..={} ---", base, base + 7);
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let s = score(&feats[a as usize], &feats[b as usize]);
                    let tag = match allow_reason(a, b) {
                        Some(Why::Collapse(_)) => " [Collapse]",
                        None => "",
                    };
                    let flag = if s < EPS && allow_reason(a, b).is_none() {
                        "  <== UNEXPECTED CLONE"
                    } else {
                        ""
                    };
                    println!("  GM {a:3} vs {b:3}: {s:.4}{tag}{flag}");
                }
            }
        }
    }
}

/// Round-3 Wave-0 perceptual anti-clone oracle — implements
/// `wrk_docs/2026.07.16 - HLD - perceptual distinctness oracle.md` (ACCEPTED,
/// including the §7 two-tier addendum).
///
/// Where `mod distinctness` above measures the MODEL arms (samples off, no
/// temporal features), this module measures what the EAR gets: `samples: true`,
/// one 3 s no-note-off render per (program, probe key {48, 72}), five time
/// windows, and a 7-dimension timbre "passport" — D1 envelope, D2 tilt,
/// D3 tilt-removed harmonic shape, D4 noise/tonality, D5 modulation, D6 onset,
/// D7 energy-weighted band-spectrogram — aggregated with a saturating
/// bounded-influence sum (§2.3): `S = Σ Wᵢ·min(dᵢ, 2)`, blended
/// `0.4·SHORT + 0.6·LONG` per key, mean over keys (never max).
///
/// Two-tier (§7): a pair whose W1 onsets render (near-)identically —
/// [`is_shared_onset`] — shares an LA bank or a code arm, so it is scored on
/// the model-owned tail only (D1/D3/D4 over W3–W5, vs [`BAR_TAIL`]): *given
/// identical onsets, does the model inject a real instrument difference in the
/// sustain?* Independent-onset pairs get the full metric vs [`BAR_FULL`].
/// Dropping D5 modulation from tail credit is the key lever: a shared-onset
/// pair cannot earn distinctness through detune-beat or tremolo alone (T4).
///
/// Every `CAL`-marked constant was frozen by the §2.4 calibration run on the
/// HEAD this module landed on (see `perceptual_bar_is_calibrated`). Do NOT
/// iterate weights/JNDs to green — that is how green-but-wrong oracles are
/// born. The sanctioned maximum is ONE documented revision with a physical
/// diagnosis (§2.4, T2), then the pair is ear-adjudicated (§6).
#[cfg(all(test, feature = "embedded-samples"))]
mod perceptual_distinctness {
    use super::*;

    const SR: f32 = 44100.0;
    const SECS: f32 = 3.0;
    const VEL: u8 = 100;
    const SEED: u32 = 7;
    const NKEYS: usize = 2;
    const PROBE_KEYS: [u8; NKEYS] = [48, 72];
    /// D7 band count: 16 log-spaced bands, 100 Hz → 10 kHz (§2.2 D7).
    const NB: usize = 16;
    /// D3 harmonic passport depth (k = 1..=10).
    const NH: usize = 10;

    /// §2.2 windows. W3 starts past every LA fade seam's midpoint and every LA
    /// fade ends by 0.85 s (`la_fade_ends_before_model_owned_window` in
    /// voices.rs pins < 0.90 — tripwire T7), so W4/W5 are model-owned for
    /// every wrapped program and W1 is sample-owned.
    const WINDOWS: [(f32, f32); 5] = [
        (0.02, 0.12),
        (0.12, 0.45),
        (0.45, 0.90),
        (0.90, 1.70),
        (1.70, 2.80),
    ];
    /// SHORT view = {W1, W2}; LONG view = {W1..W5} (§2.2). The SHORT view is
    /// what keeps shared-onset verdicts honest: a pair must differ where the
    /// music lives, not only in second three of a held note.
    const SHORT_NW: usize = 2;
    const V_SHORT: usize = 0;
    const V_LONG: usize = 1;
    /// Post-onset spectral-analysis span per view (D2/D3/D4). The onset's own
    /// spectral content is D6's axis (§2.2 anti-correlation: one physical knob
    /// earns credit on one axis), so these spans start after W1. The LONG span
    /// (W3–W5) is model-owned for every wrapped program and doubles as the
    /// Tier-2 tail span (§7).
    const SPAN_SHORT: (f32, f32) = (0.12, 0.45);
    const SPAN_TAIL: (f32, f32) = (0.45, 2.80);
    /// D5 modulation span (LONG-only; SHORT has too few cycles, §2.2 D5).
    const SPAN_MOD: (f32, f32) = (0.12, 2.80);

    // ---- §2.3 aggregation ----
    const W_DIM: [f32; 7] = [0.15, 0.05, 0.12, 0.09, 0.12, 0.12, 0.35];
    const DIM_CAP: f32 = 2.0;
    /// Tier-2 renormaliser: the kept dims' raw weights (D1 .15 + D3 .12 +
    /// D4 .09) sum to 0.36; dividing keeps the tail score on the same
    /// 0..2 scale as the full score so the two BARs are comparable.
    const W_TAIL_SUM: f32 = 0.36;

    // ---- CAL JNDs (§2.2). Absolute-scale members (dB, log2, log-rate):
    // δ = |a−b| / JND. Ratio members: δ = (|a−b| / (|a|+|b|+floor)) / JND. ----
    /// D1: attack time to 90 % peak, compared in log10 seconds (~30 % JND).
    const JND_ATTACK_LOG10: f32 = 0.12;
    /// D1 SHORT decay slope (dB/s) — early decays are steep, so a wider JND.
    const JND_SLOPE_SHORT: f32 = 4.0;
    /// D1 LONG / tail decay slopes (dB/s).
    const JND_SLOPE: f32 = 3.0;
    /// D1 sustain level (dB).
    const JND_SUSTAIN_DB: f32 = 3.0;
    /// D1 envelope roughness (std/mean of the 10 ms env; ratio member).
    const FLOOR_ROUGH: f32 = 0.05;
    const JND_ROUGH: f32 = 0.25;
    /// D2 centroid (log2 octaves) — deliberately coarse; brightness is EQ,
    /// not identity, and D2 carries the lowest weight.
    const JND_CENT_LOG2: f32 = 0.20;
    /// D2/D6 HF fraction (> 3 kHz energy share; ratio member).
    const FLOOR_HF: f32 = 0.02;
    const JND_HF: f32 = 0.30;
    /// D3 tilt-removed harmonic-shape residual distance (dB RMS).
    const JND_D3_DB: f32 = 2.5;
    /// D3 rel-dB floor: harmonics more than 35 dB under the loudest are noise.
    const H_FLOOR_DB: f32 = -35.0;
    /// D4 spectral flatness (ratio member).
    const FLOOR_FLAT: f32 = 0.05;
    const JND_FLAT: f32 = 0.30;
    /// D4 harmonic fraction (ratio member).
    const FLOOR_HARM_FRAC: f32 = 0.05;
    const JND_HARM_FRAC: f32 = 0.25;
    /// D4 log-kurtosis (ln units; grain/impulsiveness).
    const JND_LOG_KURT: f32 = 0.35;
    /// D5 AM/FM depth (normalised autocorrelation peak, 0..1).
    const JND_MOD_DEPTH: f32 = 0.25;
    /// D5 AM rate (log2 octaves), credited only when BOTH depths exceed the
    /// gate (§2.2 D5).
    const JND_AM_RATE_LOG2: f32 = 0.5;
    const AM_RATE_GATE: f32 = 0.25;
    /// D6 onset centroid (log2 octaves) — finer than D2: the attack is where
    /// the ear decides what an instrument IS.
    const JND_ONSET_CENT_LOG2: f32 = 0.25;
    /// D6 onset-energy share (ratio member).
    const FLOOR_ONSET_SHARE: f32 = 0.02;
    const JND_ONSET_SHARE: f32 = 0.30;
    /// D7 energy-weighted cell distance (dB). T2's one sanctioned lever if
    /// GM4/5 lands above BAR_FULL: power→power^1.5 weighting or JND 2.5→3.
    const JND_D7_DB: f32 = 2.5;
    /// D7 drop threshold: cells where BOTH members sit under −40 dB rel the
    /// loudest cell are inaudible — excluded (§2.2 D7).
    const D7_DROP_DB: f32 = -40.0;

    /// §7 tier classifier threshold: rms(W1_a − W1_b) / max(rms) < 2 % at
    /// BOTH probe keys ⇒ the onsets are the same audible object.
    const SHARED_ONSET_REL: f32 = 0.02;

    // ---- Thresholds (§2.4 + §7) — FROZEN by the 2026-07-16 calibration run
    // on HEAD 33579ac (data: `print_perceptual_matrix`, recorded in the
    // round-3 build journal). Key outcomes:
    //   NEG_tail  (0,1)=0.0905  (0,3)=0.6043  (1,3)=0.5505  (29,30)=0.0000
    //   POS_full  (83,87)=0.1071 (64,65)=0.1404 (11,12)=0.8039
    //             (16,23)=0.8719 (17,21)=1.1442; brass min (57,60)=0.5535,
    //             reed tier-1 min (64,65)=0.1404
    //   (4,5) UNDER-REDS: full score 1.0236 ≫ min(POS) — the §2.4 gap is
    //   empty and inverted 15×, beyond any sanctioned JND revision. Verdict
    //   per §2.4/§7's own fallback: (4,5) is EAR-ADJUDICATED (round-3 EAR
    //   list) — at matched pitch our GM4/5 renders genuinely differ in
    //   envelope (D1) and band energy (D7); the ear's "very similar" verdict
    //   is about instrument-class identity, the §6.1 honest limit. The U5
    //   e-piano split carries its own fail-first oracles instead; its
    //   before/after jump in THIS matrix (baseline 1.0236) is reported, not
    //   gated.
    //   (72,73) classified INDEPENDENT-onset: the flute fade starts at
    //   0.06 s, so the piccolo-vs-flute models already diverge inside W1
    //   (T8 investigated: early crossfade, NOT a bare-model fallback).
    // ----
    /// FROZEN: no NEG_full anchor survives calibration ((29,30) is tail-tier
    /// byte-identical, (4,5) ear-adjudicated above), so the bar sits under
    /// min(POS_full)/MARGIN_MUL = 0.0824 with ~10 % drift headroom — while
    /// still far above the ~0 a byte-identical or near-clone regression
    /// scores. Every observed full-tier pair clears 0.1071.
    const BAR_FULL: f32 = 0.075;
    /// FROZEN per §2.4's NEG-side rule applied to the tail tier:
    /// 1.25 · max(NEG_tail) = 1.25 · 0.6043 = 0.755 → 0.76. Deliberately
    /// strict — (0,3)'s 0.60 is detune line-splitting reading as harmonic
    /// shape, and the ear still called it a clone — so a shared-onset pair
    /// below this bar is "not proven distinct" and goes through one ear
    /// adjudication (§6/§7), never a threshold nudge. POS_tail is anchored
    /// on nothing by design.
    const BAR_TAIL: f32 = 0.76;
    /// POS pairs must clear MARGIN_MUL·BAR (the no-false-alarm side).
    const MARGIN_MUL: f32 = 1.3;

    /// Ear-accepted distinct pairs asserted ≥ `MARGIN_MUL · BAR_FULL` (§7
    /// POS_full; all classify independent-onset). 48/49, 72/73 and 40/44 are
    /// deliberately absent: reported by `print_perceptual_matrix`, adjudicated
    /// by ear once (§6/§7), never silently anchored.
    const POS_FULL: &[(u8, u8)] = &[(64, 65), (16, 23), (17, 21), (83, 87), (11, 12)];

    #[derive(Clone, Copy)]
    enum Why {
        /// Known perceived clone; the cited round-3 unit deletes this entry —
        /// `allowlisted_perceived_clones_are_still_clones` forces the delete
        /// the moment the voice fix lands (the mechanical GREEN transition).
        Collapse(&'static str),
        /// Shared-onset pair awaiting its one batched human ear A/B (round-3
        /// build journal, EAR-A/B list). Not asserted in either direction
        /// (§6/§7: numeric features cannot decide this class).
        EarPending(&'static str),
    }

    /// Unordered program pairs exempt from the tier-bar assertion, kept
    /// sorted (a < b). The RED-on-HEAD observation (2026-07-16, empty ALLOW):
    /// the tail tier flagged exactly (0,1), (0,3), (1,3), (29,30) — the
    /// round-3 perceived clones — plus the two shared-bank adjudication
    /// candidates below; the full tier flagged nothing at the frozen bar.
    const ALLOW: &[(u8, u8, Why)] = &[
        // Round-3 complaint #1/#2 (GM 0/1/3 piano sameness): FIXED by U3 —
        // the per-program sample DSP (GM1 shelf, GM3 detuned reads)
        // un-shared the onsets, the pairs reclassified to the full tier and
        // cleared BAR_FULL, and their three Collapse entries were deleted
        // (this oracle's own contract).
        // Round-3 complaint #10/#11: both share the literal Pluck DRIVE arm.
        // Plan review M3: the round-3 complaint is MAIN-vs-ALT, which U2
        // fixed at the preset layer (DRIVE decays, DRIVE_LEAD holds) WITHOUT
        // splitting 29 from 30 — the two programs deliberately still share
        // the arm, byte_identical_arms_score_zero still pins it, and this
        // entry stays until a future 29≠30 split (overdriven vs distortion
        // voicing) deletes both together.
        (29, 30, Why::Collapse("a future GM29≠30 voicing split")),
        // §7 contingent controls — shared violin/strings banks; the model
        // tails measure 0.13/0.06, far under BAR_TAIL. Probable true
        // positives the old matrix missed (40/41 = the repitched-violin
        // viola proxy). One batched human listen each decides: EarAccepted
        // or a voice-fix requirement (viola bank = roadmap Stage 3).
        (
            40,
            41,
            Why::EarPending("viola is a repitched-violin proxy — same or different?"),
        ),
        (
            48,
            49,
            Why::EarPending("string ensembles 1/2 — real swell-time difference?"),
        ),
    ];

    fn allow_reason(a: u8, b: u8) -> Option<Why> {
        let (lo, hi) = if a <= b { (a, b) } else { (b, a) };
        ALLOW
            .iter()
            .find(|&&(x, y, _)| x == lo && y == hi)
            .map(|&(_, _, w)| w)
    }

    // ------------------------------------------------------------------
    // Rendering + passport extraction
    // ------------------------------------------------------------------

    fn f0_of(key: u8) -> f32 {
        440.0 * 2f32.powf((key as f32 - 69.0) / 12.0)
    }

    fn render3s(program: u8, key: u8, samples: bool) -> Vec<f32> {
        // §2.1: a silent samples-off run would measure a different instrument
        // and invalidate every threshold in this module.
        assert!(crate::embedded_samples_available());
        let mut v = crate::voices::make(program, key, VEL, SR, SEED, samples);
        let mut buf = vec![0f32; (SECS * SR) as usize];
        v.render(&mut buf);
        buf
    }

    fn seg(buf: &[f32], w: (f32, f32)) -> &[f32] {
        &buf[(w.0 * SR) as usize..(w.1 * SR) as usize]
    }

    fn db(x: f32) -> f32 {
        20.0 * x.max(1e-7).log10()
    }

    /// Window-RMS decay slope in dB/s between two windows' midpoints, clamped
    /// so silence-vs-silence reads 0 and silence transitions stay bounded.
    fn slope_db_per_s(buf: &[f32], early: (f32, f32), late: (f32, f32)) -> f32 {
        let dt = 0.5 * (late.0 + late.1) - 0.5 * (early.0 + early.1);
        ((db(rms(seg(buf, late))) - db(rms(seg(buf, early)))) / dt).clamp(-150.0, 150.0)
    }

    /// D3/D4 harmonic scan: peak-searched ±4 % around k·f0 (9-point 1 % grid,
    /// §2.2 D3 — catches the off-grid EP partials), rel-dB against the loudest
    /// harmonic floored at −35 dB, plus the harmonic energy fraction.
    fn harmonics(s: &[f32], f0: f32) -> ([f32; NH], f32) {
        let mut mag = [0f32; NH];
        for (k, m) in mag.iter_mut().enumerate() {
            let fk = (k + 1) as f32 * f0;
            if fk > 0.45 * SR {
                break;
            }
            let mut best = 0f32;
            for j in 0..9 {
                best = best.max(mag_at(s, SR, fk * (0.96 + 0.01 * j as f32)));
            }
            *m = best;
        }
        let total = rms(s).max(1e-9);
        let harm_frac = (mag.iter().map(|&m| 0.5 * m * m).sum::<f32>() / (total * total)).min(1.5);
        let loudest = mag.iter().fold(1e-9f32, |a, &b| a.max(b));
        let rel: [f32; NH] =
            std::array::from_fn(|k| (20.0 * (mag[k].max(1e-9) / loudest).log10()).max(H_FLOOR_DB));
        (rel, harm_frac)
    }

    /// Least-squares line in (log2 k, dB) subtracted: what is left is the
    /// spectral SHAPE that survives an EQ change (§2.2 D3).
    fn tilt_residuals(rel: &[f32; NH]) -> [f32; NH] {
        let xs: [f32; NH] = std::array::from_fn(|k| ((k + 1) as f32).log2());
        let n = NH as f32;
        let sx: f32 = xs.iter().sum();
        let sy: f32 = rel.iter().sum();
        let sxx: f32 = xs.iter().map(|x| x * x).sum();
        let sxy: f32 = xs.iter().zip(rel.iter()).map(|(x, y)| x * y).sum();
        let denom = n * sxx - sx * sx;
        let beta = if denom.abs() > 1e-9 {
            (n * sxy - sx * sy) / denom
        } else {
            0.0
        };
        let alpha = (sy - beta * sx) / n;
        std::array::from_fn(|k| rel[k] - (alpha + beta * xs[k]))
    }

    /// D5 AM detector on the f0-band (§2.2 D5): bandpass Q≈8 at f0 (the
    /// anti-flange defence — true detuned-unison beating makes periodic
    /// f0-band AM; a static comb makes tilt but no AM), rectified envelope
    /// decimated to ~200 Hz (the decimation is what keeps a 0.08–1.2 s lag
    /// autocorrelation affordable across 256 passports), slow-moving-average
    /// detrend, normalised autocorrelation peak → (depth, rate Hz). A
    /// modulation index gate keeps a flat envelope's noise floor from
    /// reading as periodic AM.
    fn am_depth_rate(s: &[f32], f0: f32) -> (f32, f32) {
        let mut bp = Biquad::bandpass(f0, 8.0, SR);
        let mut lp = OnePole::lowpass(30.0, SR);
        let dec = (SR / 200.0) as usize;
        let mut env: Vec<f64> = Vec::with_capacity(s.len() / dec + 1);
        for (i, &x) in s.iter().enumerate() {
            let e = lp.process(bp.process(x).abs());
            if i % dec == dec - 1 {
                env.push(e as f64);
            }
        }
        let esr = SR / dec as f32;
        let n = env.len();
        if n < 8 {
            return (0.0, 0.0);
        }
        let mean_env = env.iter().sum::<f64>() / n as f64;
        if mean_env <= 1e-7 {
            return (0.0, 0.0);
        }
        let half = (0.6 * esr) as usize;
        let d: Vec<f64> = (0..n)
            .map(|i| {
                let a = i.saturating_sub(half);
                let b = (i + half + 1).min(n);
                env[i] - env[a..b].iter().sum::<f64>() / (b - a) as f64
            })
            .collect();
        let zero: f64 = d.iter().map(|&x| x * x).sum();
        // modulation index: rms of the periodic residue vs the mean level
        if zero <= 0.0 || (zero / n as f64).sqrt() / mean_env < 0.02 {
            return (0.0, 0.0);
        }
        let lag_lo = ((0.08 * esr) as usize).max(1);
        let lag_hi = ((1.2 * esr) as usize).min(n - 2);
        if lag_hi <= lag_lo {
            return (0.0, 0.0);
        }
        let (mut best, mut best_lag) = (f64::MIN, lag_lo);
        for lag in lag_lo..=lag_hi {
            let c: f64 = (0..n - lag).map(|i| d[i] * d[i + lag]).sum::<f64>() / zero;
            if c > best {
                best = c;
                best_lag = lag;
            }
        }
        (best.max(0.0) as f32, esr / best_lag as f32)
    }

    /// The 7-dimension timbre passport of one (program, probe-key) render
    /// (§2.2). Index convention for the per-view arrays: [V_SHORT, V_LONG].
    struct Passport {
        /// Raw W1 segment — the §7 tier classifier and test 6 read it.
        w1: Vec<f32>,
        w1_rms: f32,
        // D1 envelope
        attack_log10: f32,
        slope_short: f32,
        slope_long: f32,
        slope_w34: f32,
        slope_w45: f32,
        sustain_db: f32,
        roughness: f32,
        // D2 tilt (per view)
        cent_log2: [f32; 2],
        hf_frac: [f32; 2],
        // D3 harmonic shape (per view): tilt-removed residuals + rel-linear
        // amplitudes (the per-k significance weights)
        h_resid: [[f32; NH]; 2],
        h_lin: [[f32; NH]; 2],
        // D4 noise/tonality (per view)
        flat: [f32; 2],
        harm_frac: [f32; 2],
        log_kurt: [f32; 2],
        // D5 modulation (LONG only)
        am_depth: f32,
        am_rate_log2: f32,
        fm_depth: f32,
        // D6 onset
        onset_cent_log2: f32,
        onset_hf: f32,
        onset_flat: f32,
        onset_share: f32,
        // D7 band-spectrogram: absolute cell dB, per window × band
        cell_db: [[f32; NB]; 5],
    }

    fn band_f(i: usize) -> f32 {
        100.0 * 100f32.powf(i as f32 / (NB - 1) as f32)
    }

    impl Passport {
        fn new(program: u8, key: u8) -> Passport {
            let buf = render3s(program, key, true);
            let f0 = f0_of(key);

            // D1 — attack over [0, 0.45]
            let att_span = &buf[..(0.45 * SR) as usize];
            let mut lp = OnePole::lowpass(200.0, SR);
            let env: Vec<f32> = att_span.iter().map(|&x| lp.process(x.abs())).collect();
            let peak = env.iter().fold(0.0f32, |a, &b| a.max(b));
            let attack_s = if peak <= 1e-7 {
                0.45
            } else {
                env.iter()
                    .position(|&e| e >= 0.9 * peak)
                    .map(|i| i as f32 / SR)
                    .unwrap_or(0.45)
            };
            let rough = {
                let s = seg(&buf, (0.90, 2.80));
                let win = (0.010 * SR) as usize;
                let e: Vec<f32> = s.chunks(win).map(rms).collect();
                let mean = e.iter().sum::<f32>() / e.len() as f32;
                if mean < 1e-6 {
                    0.0
                } else {
                    (e.iter().map(|&v| (v - mean) * (v - mean)).sum::<f32>() / e.len() as f32)
                        .sqrt()
                        / mean
                }
            };

            // D2/D3/D4 per view
            let spans = [SPAN_SHORT, SPAN_TAIL];
            let mut cent_log2 = [0f32; 2];
            let mut hf_frac = [0f32; 2];
            let mut h_resid = [[0f32; NH]; 2];
            let mut h_lin = [[0f32; NH]; 2];
            let mut flat = [0f32; 2];
            let mut harm_frac = [0f32; 2];
            let mut log_kurt = [0f32; 2];
            for (v, &span) in spans.iter().enumerate() {
                let s = seg(&buf, span);
                cent_log2[v] = centroid(s, SR).max(50.0).log2();
                hf_frac[v] = hp_rms(s, SR, 3000.0) / rms(s).max(1e-9);
                let (rel, hfr) = harmonics(s, f0);
                h_resid[v] = tilt_residuals(&rel);
                h_lin[v] = std::array::from_fn(|k| 10f32.powf(rel[k] / 20.0));
                flat[v] = flatness(s, SR, 500.0, 9000.0);
                harm_frac[v] = hfr;
                log_kurt[v] = kurtosis(s).max(1.5).ln();
            }

            // D5 (LONG only)
            let mod_span = seg(&buf, SPAN_MOD);
            let (am_depth, am_rate) = am_depth_rate(mod_span, f0);
            let fm_depth = fm_mod_rate(mod_span, SR, f0, 3.0, 9.0).0;

            // D6 — [0, 0.12] incl. t=0 (the attack transient itself)
            let onset = &buf[..(0.12 * SR) as usize];
            let onset_share = rms(onset) / rms(&buf[..(2.80 * SR) as usize]).max(1e-9);

            // D7 cells
            let mut cell_db = [[0f32; NB]; 5];
            for (w, &win) in WINDOWS.iter().enumerate() {
                let s = seg(&buf, win);
                for (b, cell) in cell_db[w].iter_mut().enumerate() {
                    *cell = db(band_rms(s, SR, band_f(b), 3.5));
                }
            }

            let w1: Vec<f32> = seg(&buf, WINDOWS[0]).to_vec();
            let w1_rms = rms(&w1);
            Passport {
                w1,
                w1_rms,
                attack_log10: attack_s.max(0.005).log10(),
                slope_short: slope_db_per_s(&buf, (0.12, 0.25), (0.32, 0.45)),
                slope_long: slope_db_per_s(&buf, WINDOWS[1], WINDOWS[4]),
                slope_w34: slope_db_per_s(&buf, WINDOWS[2], WINDOWS[3]),
                slope_w45: slope_db_per_s(&buf, WINDOWS[3], WINDOWS[4]),
                sustain_db: (db(rms(seg(&buf, WINDOWS[4]))) - db(rms(seg(&buf, (0.05, 0.30)))))
                    .clamp(-120.0, 20.0),
                roughness: rough,
                cent_log2,
                hf_frac,
                h_resid,
                h_lin,
                flat,
                harm_frac,
                log_kurt,
                am_depth,
                am_rate_log2: am_rate.max(0.5).log2(),
                fm_depth,
                onset_cent_log2: centroid(onset, SR).max(50.0).log2(),
                onset_hf: hp_rms(onset, SR, 3000.0) / rms(onset).max(1e-9),
                onset_flat: flatness(onset, SR, 500.0, 9000.0),
                onset_share,
                cell_db,
            }
        }

        fn assert_finite(&self, label: &str) {
            let mut all: Vec<f32> = vec![
                self.w1_rms,
                self.attack_log10,
                self.slope_short,
                self.slope_long,
                self.slope_w34,
                self.slope_w45,
                self.sustain_db,
                self.roughness,
                self.am_depth,
                self.am_rate_log2,
                self.fm_depth,
                self.onset_cent_log2,
                self.onset_hf,
                self.onset_flat,
                self.onset_share,
            ];
            all.extend_from_slice(&self.cent_log2);
            all.extend_from_slice(&self.hf_frac);
            all.extend_from_slice(&self.flat);
            all.extend_from_slice(&self.harm_frac);
            all.extend_from_slice(&self.log_kurt);
            for v in 0..2 {
                all.extend_from_slice(&self.h_resid[v]);
                all.extend_from_slice(&self.h_lin[v]);
            }
            for row in &self.cell_db {
                all.extend_from_slice(row);
            }
            assert!(
                all.iter().all(|x| x.is_finite()),
                "{label}: non-finite passport feature"
            );
        }
    }

    /// One render per (program, probe key), shared by every test below.
    fn passports() -> &'static [[Passport; NKEYS]] {
        static CELL: std::sync::OnceLock<Vec<[Passport; NKEYS]>> = std::sync::OnceLock::new();
        CELL.get_or_init(|| {
            (0..128u8)
                .map(|p| std::array::from_fn(|k| Passport::new(p, PROBE_KEYS[k])))
                .collect()
        })
    }

    // ------------------------------------------------------------------
    // Pair distances (§2.2–§2.3, §7)
    // ------------------------------------------------------------------

    fn d_abs(a: f32, b: f32, jnd: f32) -> f32 {
        (a - b).abs() / jnd
    }

    fn d_rel(a: f32, b: f32, floor: f32, jnd: f32) -> f32 {
        ((a - b).abs() / (a.abs() + b.abs() + floor)) / jnd
    }

    /// D3: per-k significance-weighted RMS of the tilt-removed residual
    /// difference, in dB (§2.2 D3). Significance = pair-max linear power of
    /// the harmonic, so inaudible harmonics cannot carry the verdict.
    fn d3_dist(a: &Passport, b: &Passport, v: usize) -> f32 {
        let (mut num, mut wsum) = (0f32, 0f32);
        for k in 0..NH {
            let w = (a.h_lin[v][k] * a.h_lin[v][k]).max(b.h_lin[v][k] * b.h_lin[v][k]);
            let dr = a.h_resid[v][k] - b.h_resid[v][k];
            num += w * dr * dr;
            wsum += w;
        }
        if wsum <= 0.0 {
            0.0
        } else {
            (num / wsum).sqrt() / JND_D3_DB
        }
    }

    /// D7: energy-weighted mean |ΔdB| over the view's audible cells (§2.2 D7).
    /// Each member's cells are normalised to its own loudest cell (level-free:
    /// this reads WHERE the energy is and how it moves, not how loud the
    /// program is); weighting by pair-max linear power is the audibility
    /// weighting the old matrix lacked.
    fn d7_dist(a: &Passport, b: &Passport, v: usize) -> f32 {
        let nw = if v == V_SHORT {
            SHORT_NW
        } else {
            WINDOWS.len()
        };
        let max_of = |p: &Passport| {
            p.cell_db[..nw]
                .iter()
                .flatten()
                .fold(f32::MIN, |m, &x| m.max(x))
        };
        let (ma, mb) = (max_of(a), max_of(b));
        let (mut num, mut wsum) = (0f32, 0f32);
        for w in 0..nw {
            for k in 0..NB {
                let ra = a.cell_db[w][k] - ma;
                let rb = b.cell_db[w][k] - mb;
                if ra < D7_DROP_DB && rb < D7_DROP_DB {
                    continue;
                }
                let wgt = 10f32.powf(ra / 10.0).max(10f32.powf(rb / 10.0));
                num += wgt * (ra - rb).abs();
                wsum += wgt;
            }
        }
        if wsum <= 0.0 {
            0.0
        } else {
            (num / wsum) / JND_D7_DB
        }
    }

    /// Full-metric per-view dimension distances [d1..d7] (§2.2).
    fn dims_view(a: &Passport, b: &Passport, v: usize) -> [f32; 7] {
        let d1 = if v == V_SHORT {
            (d_abs(a.attack_log10, b.attack_log10, JND_ATTACK_LOG10)
                + d_abs(a.slope_short, b.slope_short, JND_SLOPE_SHORT))
                / 2.0
        } else {
            (d_abs(a.attack_log10, b.attack_log10, JND_ATTACK_LOG10)
                + d_abs(a.slope_long, b.slope_long, JND_SLOPE)
                + d_abs(a.sustain_db, b.sustain_db, JND_SUSTAIN_DB)
                + d_rel(a.roughness, b.roughness, FLOOR_ROUGH, JND_ROUGH))
                / 4.0
        };
        let d2 = (d_abs(a.cent_log2[v], b.cent_log2[v], JND_CENT_LOG2)
            + d_rel(a.hf_frac[v], b.hf_frac[v], FLOOR_HF, JND_HF))
            / 2.0;
        let d3 = d3_dist(a, b, v);
        let d4 = (d_rel(a.flat[v], b.flat[v], FLOOR_FLAT, JND_FLAT)
            + d_rel(
                a.harm_frac[v],
                b.harm_frac[v],
                FLOOR_HARM_FRAC,
                JND_HARM_FRAC,
            )
            + d_abs(a.log_kurt[v], b.log_kurt[v], JND_LOG_KURT))
            / 3.0;
        let d5 = if v == V_SHORT {
            0.0
        } else {
            let mut sum = d_abs(a.am_depth, b.am_depth, JND_MOD_DEPTH)
                + d_abs(a.fm_depth, b.fm_depth, JND_MOD_DEPTH);
            let mut n = 2.0;
            if a.am_depth > AM_RATE_GATE && b.am_depth > AM_RATE_GATE {
                sum += d_abs(a.am_rate_log2, b.am_rate_log2, JND_AM_RATE_LOG2);
                n += 1.0;
            }
            sum / n
        };
        let d6 = (d_abs(a.onset_cent_log2, b.onset_cent_log2, JND_ONSET_CENT_LOG2)
            + d_rel(a.onset_hf, b.onset_hf, FLOOR_HF, JND_HF)
            + d_rel(a.onset_flat, b.onset_flat, FLOOR_FLAT, JND_FLAT)
            + d_rel(
                a.onset_share,
                b.onset_share,
                FLOOR_ONSET_SHARE,
                JND_ONSET_SHARE,
            ))
            / 4.0;
        let d7 = d7_dist(a, b, v);
        [d1, d2, d3, d4, d5, d6, d7]
    }

    fn s_of(dims: &[f32; 7]) -> f32 {
        dims.iter()
            .zip(W_DIM.iter())
            .map(|(&d, &w)| w * d.min(DIM_CAP))
            .sum()
    }

    /// Tier-1 score: 0.4·SHORT + 0.6·LONG per key, mean over keys (§2.3).
    fn score_full(a: &[Passport; NKEYS], b: &[Passport; NKEYS]) -> f32 {
        (0..NKEYS)
            .map(|k| {
                0.4 * s_of(&dims_view(&a[k], &b[k], V_SHORT))
                    + 0.6 * s_of(&dims_view(&a[k], &b[k], V_LONG))
            })
            .sum::<f32>()
            / NKEYS as f32
    }

    /// Tier-2 tail dimension distances [d1_tail, d3, d4]: envelope SHAPE in
    /// the model-owned tail (W3→W4, W4→W5 slopes + roughness), harmonic shape
    /// and noise character over W3–W5. D6/D2/D5 carry no credit (§7).
    fn dims_tail(a: &Passport, b: &Passport) -> [f32; 3] {
        let d1 = (d_abs(a.slope_w34, b.slope_w34, JND_SLOPE)
            + d_abs(a.slope_w45, b.slope_w45, JND_SLOPE)
            + d_rel(a.roughness, b.roughness, FLOOR_ROUGH, JND_ROUGH))
            / 3.0;
        [d1, d3_dist(a, b, V_LONG), {
            (d_rel(a.flat[V_LONG], b.flat[V_LONG], FLOOR_FLAT, JND_FLAT)
                + d_rel(
                    a.harm_frac[V_LONG],
                    b.harm_frac[V_LONG],
                    FLOOR_HARM_FRAC,
                    JND_HARM_FRAC,
                )
                + d_abs(a.log_kurt[V_LONG], b.log_kurt[V_LONG], JND_LOG_KURT))
                / 3.0
        }]
    }

    /// Tier-2 score: renormalised D1/D3/D4 bounded sum over the tail, mean
    /// over keys (§7).
    fn score_tail(a: &[Passport; NKEYS], b: &[Passport; NKEYS]) -> f32 {
        (0..NKEYS)
            .map(|k| {
                let d = dims_tail(&a[k], &b[k]);
                (W_DIM[0] * d[0].min(DIM_CAP)
                    + W_DIM[2] * d[1].min(DIM_CAP)
                    + W_DIM[3] * d[2].min(DIM_CAP))
                    / W_TAIL_SUM
            })
            .sum::<f32>()
            / NKEYS as f32
    }

    /// §7 tier classifier: byte-identical sampled onsets drive the W1
    /// difference to ~0; near-silent W1s (slow swells) are also "shared" —
    /// their identity legitimately lives in the tail. Auto-reclassifies when
    /// a voice later gets its own bank (no hardcoded pair labels).
    fn is_shared_onset(a: &[Passport; NKEYS], b: &[Passport; NKEYS]) -> bool {
        (0..NKEYS).all(|k| {
            let denom = a[k].w1_rms.max(b[k].w1_rms);
            if denom < 1e-5 {
                return true;
            }
            let diff: f32 = rms(&a[k]
                .w1
                .iter()
                .zip(b[k].w1.iter())
                .map(|(&x, &y)| x - y)
                .collect::<Vec<f32>>());
            diff / denom < SHARED_ONSET_REL
        })
    }

    #[derive(Clone, Copy, PartialEq, Eq, Debug)]
    enum Tier {
        Full,
        Tail,
    }

    fn score_pair(a: &[Passport; NKEYS], b: &[Passport; NKEYS]) -> (Tier, f32, f32) {
        if is_shared_onset(a, b) {
            (Tier::Tail, score_tail(a, b), BAR_TAIL)
        } else {
            (Tier::Full, score_full(a, b), BAR_FULL)
        }
    }

    // ------------------------------------------------------------------
    // The six oracle tests (§3) + the §7 tier freeze
    // ------------------------------------------------------------------

    /// §3 test 1 — the headline guard: within every GM family, no two
    /// programs SOUND like the same instrument (samples on, tier-appropriate
    /// bar) unless explicitly allowlisted.
    #[test]
    fn every_gm_family_sounds_free_of_unexpected_clones() {
        let ps = passports();
        let mut failures = Vec::new();
        for fam in 0..16u8 {
            let base = fam * 8;
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let (tier, s, bar) = score_pair(&ps[a as usize], &ps[b as usize]);
                    if s < bar && allow_reason(a, b).is_none() {
                        failures.push(format!(
                            "GM {a} vs {b}: {tier:?} score {s:.4} < bar {bar} (perceived clone)"
                        ));
                    }
                }
            }
        }
        assert!(
            failures.is_empty(),
            "perceptual anti-clone matrix — unexpected clones:\n{}",
            failures.join("\n")
        );
    }

    /// §3 test 2 — every `Collapse` entry is still a perceived clone on this
    /// build. The moment a round-3 voice fix lands, this fails and forces the
    /// entry's deletion: the mechanical GREEN transition.
    #[test]
    fn allowlisted_perceived_clones_are_still_clones() {
        let ps = passports();
        for &(a, b, why) in ALLOW {
            if let Why::Collapse(unit) = why {
                let (tier, s, bar) = score_pair(&ps[a as usize], &ps[b as usize]);
                assert!(
                    s < bar,
                    "GM {a} vs {b} is allowlisted as a {unit} collapse but now scores \
                     {s:.4} >= {tier:?} bar {bar} — already differentiated; delete this \
                     ALLOW entry (and its {unit} journal line)"
                );
            }
        }
    }

    /// §3 test 3 — the no-false-alarm side + drift alarm: every POS control
    /// pair (ear-accepted distinct) clears the margin above BAR_FULL, and the
    /// brass/reed exemplar families keep every independent-onset pair above
    /// it too. A trip here on an untouched pair means the metric drifted —
    /// investigate before committing, recalibrate only deliberately (T5).
    #[test]
    fn perceptual_bar_is_calibrated() {
        let ps = passports();
        let margin = MARGIN_MUL * BAR_FULL;
        for &(a, b) in POS_FULL {
            let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
            assert!(
                tier == Tier::Full,
                "POS pair GM {a}/{b} classified {tier:?} — a POS_FULL control must be \
                 independent-onset; if a bank change made these share an onset, T8 says \
                 investigate the routing, never reclassify silently"
            );
            assert!(
                s >= margin,
                "POS pair GM {a}/{b} scores {s:.4} < MARGIN_P {margin:.4} — the \
                 calibration gap collapsed (T5)"
            );
        }
        for (base, name) in [(56u8, "brass"), (64u8, "reed")] {
            let mut min_s = f32::INFINITY;
            let (mut ma, mut mb) = (0u8, 0u8);
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
                    if tier == Tier::Full && s < min_s {
                        min_s = s;
                        (ma, mb) = (a, b);
                    }
                }
            }
            assert!(
                min_s >= margin,
                "{name}: tightest independent-onset pair GM {ma}/{mb} scores {min_s:.4} \
                 < MARGIN_P {margin:.4} — BAR_FULL has too thin a margin below the good \
                 families"
            );
        }
    }

    /// §3 test 4 — while GM 29/30 share the literal `Pluck::new(&DRIVE)` arm
    /// they must score EXACTLY zero at every stage of the metric (byte-identical
    /// ⇒ 0, §2.3). The drive main≠alt unit replaces this with a distinctness
    /// assertion when it splits the arm.
    #[test]
    fn byte_identical_arms_score_zero() {
        let ps = passports();
        let a = &ps[29];
        let b = &ps[30];
        for k in 0..NKEYS {
            let diff: f32 = a[k]
                .w1
                .iter()
                .zip(b[k].w1.iter())
                .map(|(&x, &y)| (x - y).abs())
                .fold(0.0, f32::max);
            assert!(
                diff == 0.0,
                "GM 29/30 W1 renders differ at key {} — the shared DRIVE arm split \
                 without updating this oracle",
                PROBE_KEYS[k]
            );
        }
        assert!(score_full(a, b) < 1e-6, "GM 29/30 full score not ~0");
        assert!(score_tail(a, b) < 1e-6, "GM 29/30 tail score not ~0");
    }

    /// §3 test 5 — premetric sanity: score(a,a) = 0 exactly, symmetry, and
    /// every feature of every passport finite (catches NaN / denormal /
    /// asymmetric-formula bugs).
    #[test]
    fn metric_is_a_premetric() {
        let ps = passports();
        for (i, p) in ps.iter().enumerate() {
            for (k, pk) in p.iter().enumerate() {
                pk.assert_finite(&format!("GM {i} key {}", PROBE_KEYS[k]));
            }
        }
        for &p in &[0usize, 4, 19, 25, 29, 40, 52, 56, 64, 72, 88, 104] {
            assert!(
                score_full(&ps[p], &ps[p]) == 0.0 && score_tail(&ps[p], &ps[p]) == 0.0,
                "GM {p}: self-distance is not exactly zero"
            );
        }
        for &(a, b) in &[(0u8, 1u8), (4, 5), (24, 25), (56, 60), (64, 71), (88, 92)] {
            let (pa, pb) = (&ps[a as usize], &ps[b as usize]);
            assert!(
                (score_full(pa, pb) - score_full(pb, pa)).abs() < 1e-9
                    && (score_tail(pa, pb) - score_tail(pb, pa)).abs() < 1e-9
                    && is_shared_onset(pa, pb) == is_shared_onset(pb, pa),
                "GM {a}/{b}: metric is not symmetric"
            );
        }
    }

    /// §3 test 6 — the wrong-path tripwire (T1): every LA-wrapped program's
    /// sample layer actually engages at the probe keys, guarding
    /// `LaVoice::wrap`'s silent bare-model fallback when a repitch leaves the
    /// 0.5–2.05 zone window. The program list mirrors the `make()` wiring
    /// (every `LaVoice::wrap` arm).
    ///
    /// Measured deviation from the HLD's ">0.5 dB W1 RMS" criterion: the
    /// repo's own `la_level_continuity` contract level-matches the sampled
    /// onset to the model's (GM 68 oboe measured −0.24 dB at key 72 while
    /// fully engaged), so an RMS delta is blind to a CORRECT engagement. The
    /// waveform difference reads the same intent robustly: exactly 0 on the
    /// bare-model fallback, O(1) when a different (sampled) onset plays.
    #[test]
    fn sample_layer_engaged_at_probe_keys() {
        // Every LaVoice::wrap arm whose sample engages at one of the two probe keys
        // (C3=48, C5=72). GM 76 blown bottle is wrapped too but OMITTED: its single C6
        // zone repitches to ratio 0.495 at C5 — just under the 0.5 clamp — so it renders
        // bare-model at both probe keys (it engages only ~C#5 and up). GM 78 whistle is
        // model-only by design.
        const LA_WRAPPED: &[u8] = &[
            0, 1, 3, 6, 24, 25, 40, 41, 42, 43, 46, 47, 48, 49, 56, 57, 58, 59, 60, 68, 69, 70, 71,
            72, 73, 74, 75, 77, 79, 104, 105, 110,
        ];
        let ps = passports();
        let mut failures = Vec::new();
        for &prog in LA_WRAPPED {
            let mut rel_diffs = Vec::new();
            for k in 0..NKEYS {
                let on = &ps[prog as usize][k].w1;
                let off = {
                    let mut v = crate::voices::make(prog, PROBE_KEYS[k], VEL, SR, SEED, false);
                    let mut buf = vec![0f32; (0.13 * SR) as usize];
                    v.render(&mut buf);
                    seg(&buf, WINDOWS[0]).to_vec()
                };
                let diff: Vec<f32> = on.iter().zip(off.iter()).map(|(&x, &y)| x - y).collect();
                let denom = ps[prog as usize][k].w1_rms.max(rms(&off)).max(1e-9);
                rel_diffs.push((PROBE_KEYS[k], rms(&diff) / denom));
            }
            if !rel_diffs.iter().any(|&(_, d)| d > 0.05) {
                failures.push(format!(
                    "GM {prog}: W1 on/off waveform rel-diffs {rel_diffs:.3?} — LA layer \
                     not engaged at either probe key (silent bare-model fallback?)"
                ));
            }
        }
        assert!(failures.is_empty(), "{}", failures.join("\n"));
    }

    /// §7 — freeze which within-family pairs are shared-onset, so a future
    /// bank change cannot silently move a pair between tiers (each tier has
    /// its own bar, so a silent move changes the effective gate). T8: a
    /// nominally shared-bank pair MISSING from this list means a silent
    /// bare-model fallback — investigate the routing, don't reclassify.
    #[test]
    fn onset_tier_classification_is_stable() {
        /// Pinned on the module's landing HEAD (2026-07-16 calibration run);
        /// re-pinned after U3's piano sample-DSP un-shared the GM 0/1/3 onsets,
        /// then again (2026-07-18) when GM 41 viola got its OWN dedicated onset
        /// bank (VSCO Viola Section susvib, MM-BUG-KILN-00005): 40 and 41 no longer
        /// share a bank, so the pair is now INDEPENDENT-onset and scores on the
        /// full metric — the deliberate GREEN transition, and the viola fix itself.
        /// 48/49 share the strings bank, 29/30 a literal code arm. 72/73 share the
        /// flute bank but classify INDEPENDENT — the 0.06 s fade start lets the
        /// piccolo/flute models diverge inside W1 (investigated, not a fallback), so
        /// full-tier is honest.
        const SHARED_ONSET_PAIRS: &[(u8, u8)] = &[(29, 30), (48, 49)];
        let ps = passports();
        let mut got = Vec::new();
        for fam in 0..16u8 {
            let base = fam * 8;
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    if is_shared_onset(&ps[a as usize], &ps[b as usize]) {
                        got.push((a, b));
                    }
                }
            }
        }
        assert!(
            got == SHARED_ONSET_PAIRS,
            "shared-onset tier membership changed.\n  pinned: {SHARED_ONSET_PAIRS:?}\n  \
             got:    {got:?}\nA pair moving tiers changes its effective bar — re-pin \
             deliberately (and re-adjudicate the pair) or fix the routing (T8)."
        );
    }

    // ===== Class-identity oracle (MM-BUG-KILN-00006) =====
    // Absolute two-sided ranges on the probe-key MEAN of ONE physically-scaled
    // Passport field, per instrument family — the §5 "is it really X" check that
    // a voice belongs to its CLASS (not merely differs from siblings). Calibrated
    // RED-before/GREEN-after from `print_passport_fields` (freeze 2026-07-18).
    // `sustain_db` (D1) is the load-bearing axis: sustained families hold near 0,
    // struck/plucked families decay to very negative. Ranges encode CLASS, not
    // realism (HLD §6 — realism stays ear-only).

    struct ClassRange {
        label: &'static str,
        programs: &'static [u8],
        field: &'static str,
        get: fn(&Passport) -> f32,
        lo: f32,
        hi: f32,
    }

    /// Probe-key mean (§2.1: keys 48 & 72) of one Passport field for a program.
    fn class_field_mean(prog: u8, get: fn(&Passport) -> f32) -> f32 {
        let p = &passports()[prog as usize];
        0.5 * (get(&p[0]) + get(&p[1]))
    }

    const CLASS_RANGES: &[ClassRange] = &[
        // Organ 16-23: pipe/free-reed organs HOLD their level with no decay (the
        // §5 worked example). Measured sustain_db = -0.28..+5.5; a -6 dB floor
        // clears every member with margin and REDs a decaying voice (piano -18).
        // NOTE: the HLD's "low flatness" does NOT hold in Passport space (organs
        // measure flat_L ~0.32-0.46) — sustain_db is the honest organ axis.
        ClassRange {
            label: "organ 16-23",
            programs: &[16, 17, 18, 19, 20, 21, 22, 23],
            field: "sustain_db",
            get: |p| p.sustain_db,
            lo: -6.0,
            hi: 20.0,
        },
        // Keyboards + chromatic percussion 0-15: struck/plucked — every member
        // DECAYS (energy gone by W5). Measured sustain_db = -16..-118 (highest:
        // piano GM1 -16.3, tubular-bell GM14 -17.1); a -10 dB ceiling clears all
        // with margin and REDs a sustained voice (organ GM19 = -0.3). The decay
        // TIME varies (xylophone vs tubular bell) but the LEVEL is always negative.
        ClassRange {
            label: "keyboard+chrom-perc 0-15",
            programs: &[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            field: "sustain_db",
            get: |p| p.sustain_db,
            lo: -120.0,
            hi: -10.0,
        },
        // Plucked strings 24-37,46,104-108: guitars, basses, harp, and ethnic
        // plucks (sitar/banjo/shamisen/koto/kalimba) — all DECAY (KS/pluck models).
        // Measured sustain_db = -39..-118; same -10 dB decays ceiling. Carve 38/39
        // synth bass (they HOLD, +0.4 — a synth bass is not a plucked string). 29/30
        // driven guitar are KEPT: the e-bow latch doesn't engage on a plain held
        // note, so they measure decaying (-39.8) like the rest.
        ClassRange {
            label: "plucked 24-37,46,104-108",
            programs: &[
                24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 46, 104, 105, 106, 107, 108,
            ],
            field: "sustain_db",
            get: |p| p.sustain_db,
            lo: -120.0,
            hi: -10.0,
        },
        // Bowed strings 40-43,110 (violin/viola/cello/contrabass/fiddle): HELD by
        // the bow — sustain_db measured +3.3..+9.1. Carve 44 (tremolo strings —
        // a member trait) and 45 (pizzicato — a PLUCK, sustain -105, decays).
        ClassRange {
            label: "bowed-sustain 40-43,110",
            programs: &[40, 41, 42, 43, 110],
            field: "sustain_db",
            get: |p| p.sustain_db,
            lo: -5.0,
            hi: 20.0,
        },
        // Bowed strings carry VIBRATO — the HLD §5 "strings FM depth" worked
        // example. fm_depth measured 0.45..0.92 (>> a non-vibrato piano's ~0.05).
        ClassRange {
            label: "bowed-vibrato 40-43,110",
            programs: &[40, 41, 42, 43, 110],
            field: "fm_depth",
            get: |p| p.fm_depth,
            lo: 0.1,
            hi: 1.0,
        },
        // String/synth ensemble + choir 48-54: sustained pads/sections. sustain_db
        // measured 48/49 = -5.5 (lowest), 50-54 = -1.0..+1.3; a -7 dB floor clears
        // -5.5 with ~1.5 dB margin. Carve 55 (orchestra hit — a one-shot stab).
        ClassRange {
            label: "ensemble/choir 48-54",
            programs: &[48, 49, 50, 51, 52, 53, 54],
            field: "sustain_db",
            get: |p| p.sustain_db,
            lo: -7.0,
            hi: 20.0,
        },
    ];

    /// The class-identity oracle: every in-scope voice's field-mean falls in its
    /// family's class range. A failure prints the program, field and value.
    #[test]
    fn class_identity_ranges_hold() {
        for r in CLASS_RANGES {
            for &prog in r.programs {
                let v = class_field_mean(prog, r.get);
                assert!(
                    (r.lo..=r.hi).contains(&v),
                    "{}: GM{prog} {} = {v:.4}, out of class range [{}, {}]",
                    r.label,
                    r.field,
                    r.lo,
                    r.hi
                );
            }
        }
    }

    /// RED-before guard: each class range must have discriminating power — a
    /// wrong-class exemplar must fall OUTSIDE it. This freezes that (e.g.) the
    /// organ sustain floor genuinely rejects a decaying piano, so the range is a
    /// real gate, not a vacuous always-true bound. One control per range.
    #[test]
    fn class_ranges_reject_wrong_class() {
        // (range label, a wrong-class program that MUST be out of range, why)
        let controls: &[(&str, u8, &str)] = &[
            (
                "organ 16-23",
                0,
                "piano decays (sustain_db ~ -18), must fail the held-level floor",
            ),
            (
                "keyboard+chrom-perc 0-15",
                19,
                "organ holds (sustain_db ~ 0), must fail the decays ceiling",
            ),
            (
                "plucked 24-37,46,104-108",
                40,
                "violin bows/holds (sustain_db ~ +7), must fail the decays ceiling",
            ),
            (
                "bowed-sustain 40-43,110",
                0,
                "piano decays (sustain_db ~ -18), must fail the held floor",
            ),
            (
                "bowed-vibrato 40-43,110",
                0,
                "piano has no vibrato (fm_depth ~ 0.05), must fail the vibrato floor",
            ),
            (
                "ensemble/choir 48-54",
                0,
                "piano decays (sustain_db ~ -18), must fail the held floor",
            ),
        ];
        for &(label, wrong, why) in controls {
            let r = CLASS_RANGES
                .iter()
                .find(|r| r.label == label)
                .unwrap_or_else(|| panic!("no class range labelled {label}"));
            let v = class_field_mean(wrong, r.get);
            assert!(
                !(r.lo..=r.hi).contains(&v),
                "{label}: wrong-class GM{wrong} {} = {v:.4} is INSIDE [{}, {}] — \
                 range lacks discriminating power ({why})",
                r.field,
                r.lo,
                r.hi
            );
        }
    }

    /// Calibration instrument for the class-identity oracle (MM-BUG-KILN-00006):
    /// dumps, per GM program, the probe-key MEAN (§2.1: keys 48 & 72) of the
    /// physically-scaled Passport fields the oracle asserts on. Not a gate — the
    /// numbers it prints are what the `class_identity_ranges_hold` ranges freeze
    /// against (RED-before/GREEN-after), never tuned to green.
    /// Run: `cargo test print_passport_fields -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn print_passport_fields() {
        let ps = passports();
        println!("prog  attack_log10   sustain_db   flat_L   harm_frac_L   fm_depth   cent_log2_L");
        for prog in 0..128u8 {
            let p = &ps[prog as usize];
            let km = |g: fn(&Passport) -> f32| 0.5 * (g(&p[0]) + g(&p[1]));
            println!(
                "GM{prog:3}  {:11.4}  {:10.3}  {:7.4}  {:10.4}  {:9.4}  {:10.4}",
                km(|q| q.attack_log10),
                km(|q| q.sustain_db),
                km(|q| q.flat[V_LONG]),
                km(|q| q.harm_frac[V_LONG]),
                km(|q| q.fm_depth),
                km(|q| q.cent_log2[V_LONG]),
            );
        }
    }

    /// Calibration aid (not a gate): the §2.4/§7 control tables plus every
    /// within-family pair's tier, score and per-dimension distances.
    /// Run: `cargo test print_perceptual_matrix -- --ignored --nocapture`.
    #[test]
    #[ignore]
    fn print_perceptual_matrix() {
        let ps = passports();
        for fam in 0..16u8 {
            let base = fam * 8;
            println!("--- GM family {}..={} ---", base, base + 7);
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let (pa, pb) = (&ps[a as usize], &ps[b as usize]);
                    let (tier, s, bar) = score_pair(pa, pb);
                    let tag = match allow_reason(a, b) {
                        Some(Why::Collapse(u)) => format!(" [Collapse → {u}]"),
                        Some(Why::EarPending(q)) => format!(" [EarPending: {q}]"),
                        None => String::new(),
                    };
                    let flag = if s < bar && allow_reason(a, b).is_none() {
                        "  <== PERCEIVED CLONE"
                    } else {
                        ""
                    };
                    match tier {
                        Tier::Full => {
                            let d0 = dims_view(&pa[0], &pb[0], V_LONG);
                            let d1 = dims_view(&pa[1], &pb[1], V_LONG);
                            println!(
                                "  GM {a:3} vs {b:3}: FULL {s:.4}{tag}{flag}  longdims \
                                 k48 {d0:.2?} k72 {d1:.2?}"
                            );
                        }
                        Tier::Tail => {
                            let d0 = dims_tail(&pa[0], &pb[0]);
                            let d1 = dims_tail(&pa[1], &pb[1]);
                            println!(
                                "  GM {a:3} vs {b:3}: TAIL {s:.4}{tag}{flag}  taildims \
                                 k48 {d0:.2?} k72 {d1:.2?}"
                            );
                        }
                    }
                }
            }
        }
        println!("\n=== §2.4 / §7 calibration controls ===");
        let mut neg_full: f32 = 0.0;
        let mut neg_tail: f32 = 0.0;
        for &(a, b) in &[(0u8, 1u8), (0, 3), (4, 5), (29, 30)] {
            let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
            println!("NEG GM {a}/{b}: {tier:?} {s:.4}");
            match tier {
                Tier::Full => neg_full = neg_full.max(s),
                Tier::Tail => neg_tail = neg_tail.max(s),
            }
        }
        let mut pos_min = f32::INFINITY;
        for &(a, b) in POS_FULL {
            let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
            println!("POS GM {a}/{b}: {tier:?} {s:.4}");
            pos_min = pos_min.min(s);
        }
        for (base, name) in [(56u8, "brass"), (64u8, "reed")] {
            let mut fam_min = f32::INFINITY;
            for a in base..base + 8 {
                for b in (a + 1)..base + 8 {
                    let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
                    if tier == Tier::Full {
                        fam_min = fam_min.min(s);
                    }
                }
            }
            println!("{name} family tier-1 minimum: {fam_min:.4}");
            pos_min = pos_min.min(fam_min);
        }
        for &(a, b) in &[(40u8, 41u8), (48, 49), (72, 73), (40, 44)] {
            let (tier, s, _) = score_pair(&ps[a as usize], &ps[b as usize]);
            println!("ADJUDICATE GM {a}/{b}: {tier:?} {s:.4} (ear once, §6/§7)");
        }
        println!(
            "BAR_FULL gap: [{:.4}, {:.4}] (geomean {:.4}); current {BAR_FULL}",
            1.25 * neg_full,
            pos_min / MARGIN_MUL,
            (1.25 * neg_full * pos_min / MARGIN_MUL).sqrt().max(0.0)
        );
        println!(
            "BAR_TAIL lower anchor: {:.4} (POS_tail anchored on nothing, §7); current {BAR_TAIL}",
            1.25 * neg_tail
        );
    }
}
