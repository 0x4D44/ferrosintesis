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
        (0, -41.28, 1020.2),
        (1, -42.07, 2020.8),
        (2, -42.68, 1107.1),
        (3, -40.13, 528.8),
        (4, -36.90, 932.2),
        (5, -24.61, 294.6),
        (6, -27.13, 194.4),
        (7, -24.35, 567.6),
        (8, -37.21, 2683.1),
        (9, -23.26, 483.9),
    ];
    /// Full-mix pre-normalise master peak (re-captured with the table above).
    const GOLDEN_MASTER_PEAK: f32 = 1.04280;

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
            (19, "organ"),
            (24, "NYLON"),
            (25, "STEEL"),
            (26, "CLEAN"),
            (27, "CLEAN"),
            (28, "MUTED"),
            (29, "DRIVE"),
            (30, "DRIVE"),
            (31, "HARMONIC"), // Phase 4 (G7)
            (32, "UPRIGHT"),  // Phase 4 (B2)
            (33, "BASS"),
            (34, "PICK"), // Phase 4 (B2)
            (35, "FRETLESS"),
            (36, "SLAP"),      // Phase 4 (B2)
            (37, "SLAP"),      // Phase 4 (B2)
            (38, "synthbass"), // Phase 5 (B4)
            (39, "synthbass"), // Phase 5 (B4)
            (40, "bowed"),
            (46, "HARP"),
            (47, "modal"),
            (48, "sawstack"),
            (52, "sawstack"),
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
            (110, "bowed"),
            (108, "modal"),
            (120, "sfx"),
            (127, "sfx"),
        ];
        for &(prog, want) in cases {
            let v = crate::voices::make(prog, 60, 100, SR, 7, false);
            assert_eq!(v.kind(), want, "program {prog}");
        }
        // drums route through drums::make
        let d = crate::drums::make(38, 100, SR, 7, crate::drums::Kit::V1).expect("snare voice");
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
