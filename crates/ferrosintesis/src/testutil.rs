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

/// Aperiodicity of a sustained tone's amplitude envelope. Rectify → 10 Hz
/// envelope lowpass → decimate by 64 → mean-subtract → peak *normalised*
/// autocorrelation over `[lag_lo_s, lag_hi_s]`, plus the coefficient of
/// variation `std/mean` of the decimated envelope.
///
/// A static, phase-locked additive tone beats at constant rates, so its
/// envelope is quasi-periodic and its autocorrelation re-peaks at multi-second
/// lags (returns high). Independent slow random walks give an envelope whose
/// autocorrelation has decayed away by such lags (returns low). The CoV is a
/// "shimmer present at all" floor. Deterministic; no wall clock. The existing
/// `env_autocorr_peak*` runs at full rate and 15 Hz-detrends — far too slow at
/// multi-second lags and it would erase the 0.15–2.5 Hz wander band, so this is
/// a purpose-built decimated, mean-subtracted variant.
pub(crate) fn env_aperiodicity(seg: &[f32], sr: f32, lag_lo_s: f32, lag_hi_s: f32) -> (f32, f32) {
    const DECIM: usize = 64;
    let mut lp = OnePole::lowpass(10.0, sr);
    let mut env: Vec<f32> = Vec::with_capacity(seg.len() / DECIM + 1);
    for (i, &x) in seg.iter().enumerate() {
        let e = lp.process(x.abs());
        if i % DECIM == 0 {
            env.push(e);
        }
    }
    if env.len() < 4 {
        return (0.0, 0.0);
    }
    let mean = env.iter().sum::<f32>() / env.len() as f32;
    if mean <= 1e-12 {
        return (0.0, 0.0);
    }
    let var = env.iter().map(|&e| (e - mean) * (e - mean)).sum::<f32>() / env.len() as f32;
    let cov = var.sqrt() / mean;
    let d: Vec<f64> = env.iter().map(|&e| (e - mean) as f64).collect();
    let zero: f64 = d.iter().map(|&x| x * x).sum();
    if zero <= 0.0 {
        return (0.0, cov);
    }
    let env_sr = sr / DECIM as f32;
    let lag_lo = ((lag_lo_s * env_sr) as usize).max(1);
    let lag_hi = ((lag_hi_s * env_sr) as usize).min(d.len().saturating_sub(1));
    let mut best = f64::MIN;
    for lag in lag_lo..=lag_hi {
        let c: f64 = (0..d.len() - lag).map(|i| d[i] * d[i + lag]).sum::<f64>() / zero;
        if c > best {
            best = c;
        }
    }
    (best.max(0.0) as f32, cov)
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
        verbose: false,
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
        (0, -41.28, 1020.2),
        (1, -42.07, 2020.8),
        (2, -41.49, 855.0),
        (3, -39.97, 485.9),
        (4, -27.95, 468.1),
        (5, -24.61, 294.6),
        (6, -27.13, 194.4),
        (7, -24.35, 567.6),
        (8, -37.21, 2683.1),
        // Re-captured after the default drum kit moved from V1 to V3:
        // channel 10 is deliberately brighter and slightly louder. Re-pinned
        // after the later V3 cymbal-density work moved the fixture within its
        // guard tolerance.
        (9, -22.30, 685.2),
    ];
    /// Full-mix pre-normalise master peak (re-captured with the table above).
    const GOLDEN_MASTER_PEAK: f32 = 1.25446;

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
            (8, "modal"),
            (16, "organ"),
            (19, "cathedral-organ"),
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
            (97, "sawstack"),
            (98, "modal"),
            (99, "sawstack"),
            (101, "sawstack"),
            (103, "sawstack"),
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
        let d =
            crate::drums::make(38, 100, SR, 7, crate::drums::Kit::V1, false).expect("snare voice");
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
        // -- Stage 2: Synth Pad 88-95 — 88,89,90,91,92,93,94 share one base pad.
        //    91 (halo/"sweep") only differs via a CC-driven vowel morph, inert
        //    with no controller, so it renders as the base pad here too. 95
        //    (bowed sweep) is the lone distinct member. --
        (88, 89, Why::Collapse(2)),
        (88, 90, Why::Collapse(2)),
        (88, 91, Why::Collapse(2)),
        (88, 92, Why::Collapse(2)),
        (88, 93, Why::Collapse(2)),
        (88, 94, Why::Collapse(2)),
        (89, 90, Why::Collapse(2)),
        (89, 91, Why::Collapse(2)),
        (89, 92, Why::Collapse(2)),
        (89, 93, Why::Collapse(2)),
        (89, 94, Why::Collapse(2)),
        (90, 91, Why::Collapse(2)),
        (90, 92, Why::Collapse(2)),
        (90, 93, Why::Collapse(2)),
        (90, 94, Why::Collapse(2)),
        (91, 92, Why::Collapse(2)),
        (91, 93, Why::Collapse(2)),
        (91, 94, Why::Collapse(2)),
        (92, 93, Why::Collapse(2)),
        (92, 94, Why::Collapse(2)),
        (93, 94, Why::Collapse(2)),
        // -- Stage 3: Synth FX 96-103 — crystal bell {96,98,100,102},
        //    base pad {97,99,103} (101 is pad(95), stands alone) --
        (96, 98, Why::Collapse(3)),
        (96, 100, Why::Collapse(3)),
        (96, 102, Why::Collapse(3)),
        (98, 100, Why::Collapse(3)),
        (98, 102, Why::Collapse(3)),
        (100, 102, Why::Collapse(3)),
        (97, 99, Why::Collapse(3)),
        (97, 103, Why::Collapse(3)),
        (99, 103, Why::Collapse(3)),
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
        (29, 30, Why::Collapse(5)), // guitar: two "overdrive/distortion" share DRIVE — Stage 7b
        (0, 1, Why::Collapse(5)),   // piano: acoustic-grand family shares one Modal — Stage 7a
        (0, 2, Why::Collapse(5)),
        (0, 3, Why::Collapse(5)),
        (1, 2, Why::Collapse(5)),
        (1, 3, Why::Collapse(5)),
        (2, 3, Why::Collapse(5)),
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
