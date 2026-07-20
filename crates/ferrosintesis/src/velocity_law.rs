//! Velocity-law oracles — the aggregate `amp ∝ (v/127)²` contract.
//!
//! See `wrk_docs/2026.07.20 - HLD - velocity law alignment to k=2.md`.
//!
//! ## Why this exists
//!
//! Both real GM reference modules implement note-on velocity as
//! `amp = (v/127)²`. Measured on a 9-velocity probe, the Roland SC-55mkII fits an
//! exponent of 1.997 and the Yamaha S-YXG50 fits 1.981, and the square law
//! reproduces the SC-55's measured levels to within **0.22 dB** at every point
//! from v=32 to v=127. Two independent implementations agreeing that closely is a
//! specification (the DLS/SoundFont convention), not a preference.
//!
//! ferrosintesis previously fitted **0.66** with a 0.36–2.03 spread across
//! programs, because `vel_amp` used an exponent of 1.6 *and* 14 call sites wrapped
//! it in a floor `X + Y·vel_amp(v)` — which is not a power law at all, since it
//! asymptotes to `X` as v→0. Composed dynamics therefore rendered at roughly 40 %
//! of their authored dB range, and — because drums used the bare curve while most
//! melodic voices used a floor — drums gained on the band as passages got louder.
//!
//! These oracles pin the corrected law so it cannot silently drift back.
//!
//! ## What is deliberately NOT pinned here
//!
//! Voices that should not track velocity at all (the cathedral organ — real pipe
//! organs are velocity-independent) and deliberately-compressed patches using the
//! `vel_sense` mechanism (GM6 harpsichord). Both are asserted separately, by name,
//! so an exemption is always an explicit decision rather than an omission.

#[cfg(test)]
mod tests {
    use crate::drums;
    use crate::dsp::vel_amp;
    use crate::voices;

    const SR: f32 = 44100.0;
    const SEED: u32 = 0x5EED_1234;
    /// Velocities the law is fitted over. Below v=32 the two reference modules
    /// disagree with each other by more than 6 dB (the SC-55 lifts its bottom end,
    /// the S-YXG50 does not), so there is no stable target down there.
    const FIT_VELS: [u8; 7] = [32, 48, 64, 80, 96, 110, 127];

    /// Maximum BS.1770 momentary block, in LUFS.
    ///
    /// This is deliberately the SAME estimator that measured the reference modules
    /// and justified the design — not a plain RMS. It matters because the three
    /// retained timbre floors (`voices.rs:6914` cutoff, `:8080` bow speed, `:5367`
    /// chiff) make spectrum velocity-dependent BY DESIGN, and a K-weighted meter
    /// and an unweighted one can then fit visibly different slopes on bright or
    /// bass-heavy patches. Measuring the fix with a different instrument from the
    /// one that found the defect is how you get a green suite and a wrong synth.
    fn level_db(samples: &[f32]) -> f32 {
        // The meter takes interleaved stereo; these are mono voice renders.
        let stereo: Vec<f32> = samples.iter().flat_map(|&s| [s, s]).collect();
        crate::loudness::momentary_lufs(&stereo, SR)
            .into_iter()
            .fold(f32::NEG_INFINITY, f32::max)
    }

    fn render(mut v: Box<dyn voices::Voice>, secs: f32) -> Vec<f32> {
        let n = (secs * SR) as usize;
        let mut buf = vec![0f32; n];
        // Render in blocks, as the engine does — a voice may key its internal
        // block processing off the slice length it is handed.
        for chunk in buf.chunks_mut(64) {
            if !v.render(chunk) {
                break;
            }
        }
        buf
    }

    fn melodic_level(program: u8, key: u8, vel: u8) -> f32 {
        level_db(&render(voices::make(program, key, vel, SR, SEED, true), 1.2))
    }

    fn drum_level(key: u8, vel: u8) -> Option<f32> {
        let v = drums::make(key, vel, SR, SEED, drums::Kit::V3, true, 0)?;
        Some(level_db(&render(v, 1.2)))
    }

    /// Least-squares slope of level(dB) against `20·log10(v/127)`.
    ///
    /// For `amp = (v/127)^k` the level in dB is `20·k·log10(v/127)`, so this slope
    /// IS the exponent k. Fitting a slope rather than differencing two points makes
    /// the estimate robust to any single velocity landing on a sample-layer seam.
    fn fit_k(levels: &[(u8, f32)]) -> f32 {
        let pts: Vec<(f32, f32)> = levels
            .iter()
            .map(|&(v, l)| (20.0 * (v as f32 / 127.0).log10(), l))
            .collect();
        let n = pts.len() as f32;
        let mx = pts.iter().map(|p| p.0).sum::<f32>() / n;
        let my = pts.iter().map(|p| p.1).sum::<f32>() / n;
        let num: f32 = pts.iter().map(|p| (p.0 - mx) * (p.1 - my)).sum();
        let den: f32 = pts.iter().map(|p| (p.0 - mx).powi(2)).sum();
        num / den
    }

    fn median(mut xs: Vec<f32>) -> f32 {
        xs.sort_by(|a, b| a.partial_cmp(b).unwrap());
        xs[xs.len() / 2]
    }

    /// Keys the law is checked at. Two registers, an octave apart — a sample bank's
    /// root selection and a model's register gain curve both vary with key, so a
    /// single register can flatter or damn a voice unfairly.
    const FIT_KEYS: [u8; 2] = [48, 60];

    /// k for one melodic program at one key. Asserted PER KEY, never averaged:
    /// averaging can hide one key fitting low and another high, which is precisely
    /// the key-scaling defect worth catching.
    fn melodic_k_at(program: u8, key: u8) -> f32 {
        let levels: Vec<(u8, f32)> = FIT_VELS
            .iter()
            .map(|&v| (v, melodic_level(program, key, v)))
            .collect();
        fit_k(&levels)
    }

    /// Worst (furthest from 2.0) k across the probe keys, for summary statistics.
    fn melodic_k(program: u8) -> f32 {
        FIT_KEYS
            .iter()
            .map(|&k| melodic_k_at(program, k))
            .fold(f32::NAN, |a, b| {
                if a.is_nan() || (b - 2.0).abs() > (a - 2.0).abs() {
                    b
                } else {
                    a
                }
            })
    }

    /// Programs spanning both the modeled and sampled paths and every family that
    /// carries a level law. Excludes GM6 (deliberately compressed via `vel_sense`)
    /// and the cathedral organ (deliberately velocity-independent) — both asserted
    /// by name in `exempt_voices_keep_their_documented_velocity_behaviour`.
    const PROBE_PROGRAMS: [u8; 16] = [0, 4, 5, 11, 24, 33, 40, 42, 48, 52, 56, 60, 65, 73, 80, 89];

    /// AC1 — the definition site. Pinned against drive-by tuning: this exponent is
    /// measured from hardware, not chosen.
    #[test]
    fn vel_amp_is_the_square_law() {
        assert_eq!(vel_amp(127), 1.0, "full velocity must be unity gain");
        for v in [1u8, 8, 32, 64, 100, 126, 127] {
            let want = (v as f32 / 127.0).powi(2);
            assert!(
                (vel_amp(v) - want).abs() < 1e-6,
                "vel_amp({v}) = {}, want {want}",
                vel_amp(v)
            );
        }
        // The old law (exponent 1.6) must not pass: at v=32 it is ~4.8 dB hotter.
        let old = (32.0f32 / 127.0).powf(1.6);
        assert!(
            (vel_amp(32) - old).abs() > 0.02,
            "vel_amp still matches the retired 1.6 exponent"
        );
    }

    /// AC2 — every velocity-sensitive melodic voice follows the law at its rendered
    /// output, not just at the `vel_amp` call.
    ///
    /// Tolerances: every failure mode sits far outside ±0.2 — the bare old law fits
    /// 1.6, any floor with X ≥ 0.2 fits ≤ ~1.2, and a double-counted sample layer
    /// reads ≥ ~2.4 — while velocity-tracked brightness legitimately adds only
    /// ~0.05–0.15 of slope to an RMS measurement. The S-YXG50's own 1.96–2.05 spread
    /// shows the law is this tight in real hardware.
    #[test]
    fn melodic_voices_follow_the_square_law() {
        let mut ks = Vec::new();
        for &p in &PROBE_PROGRAMS {
            for &key in &FIT_KEYS {
                let k = melodic_k_at(p, key);
                assert!(
                    (k - 2.0).abs() <= 0.2,
                    "GM{p} key {key}: velocity exponent {k:.3}, want 2.0 +/- 0.2"
                );
                ks.push(k);
            }
        }
        let m = median(ks);
        assert!(
            (m - 2.0).abs() <= 0.1,
            "median melodic exponent {m:.3}, want 2.0 +/- 0.1"
        );
    }

    /// AC2b — coverage. A 16-program probe cannot prove "every velocity-sensitive
    /// voice": `voices.rs:3861` carries its own `powf` literal, so a voice can miss
    /// the shared helper entirely. Sweep ALL 128 programs at one key and assert the
    /// law, so no program can quietly sit on a private velocity curve.
    ///
    /// Exclusions are by name and by reason, never by silence.
    #[test]
    fn every_gm_program_follows_the_square_law() {
        let mut offenders = Vec::new();
        for p in 0u8..128 {
            // GM6 is deliberately velocity-compressed (vel_sense); GM16-20 drawbar
            // organs include the velocity-independent cathedral voice. Both are
            // asserted separately in the exemption test.
            if p == 6 || (16..=20).contains(&p) {
                continue;
            }
            let k = melodic_k_at(p, 60);
            if !k.is_finite() || (k - 2.0).abs() > 0.25 {
                offenders.push((p, k));
            }
        }
        assert!(
            offenders.is_empty(),
            "programs off the square law (k, want 2.0 +/- 0.25): {}",
            offenders
                .iter()
                .map(|(p, k)| format!("GM{p}={k:.2}"))
                .collect::<Vec<_>>()
                .join(", ")
        );
    }

    /// AC3 — sampled voices compose an embedded per-layer loudness with the synth's
    /// gain law. If a layer step is not compensated, the composite stops being a
    /// straight line on the log-log fit even when its endpoints look right, and it
    /// can go non-monotonic across a layer boundary. Residual ≤ 1.0 dB catches that:
    /// an uncompensated raw pp↔mf recording step is ≥ 3 dB, while round-robin jitter
    /// contributes only ~0.3 dB.
    #[test]
    fn sampled_voices_stay_linear_across_layer_seams() {
        // The shared fit set does NOT straddle the bank thresholds, so on its own it
        // cannot see a layer seam at all. Sample either side of every documented
        // boundary (51/52, 79/80, 95/96) — a seam is invisible unless you measure
        // across it.
        const SEAM_VELS: [u8; 11] = [32, 48, 51, 52, 64, 79, 80, 95, 96, 110, 127];
        for &p in &[0u8, 42, 43] {
            for key in FIT_KEYS {
                let levels: Vec<(u8, f32)> = SEAM_VELS
                    .iter()
                    .map(|&v| (v, melodic_level(p, key, v)))
                    .collect();
                let k = fit_k(&levels);
                let x0 = 20.0 * (127.0f32 / 127.0).log10();
                let l0 = levels.last().unwrap().1;
                for &(v, l) in &levels {
                    let x = 20.0 * (v as f32 / 127.0).log10();
                    let predicted = l0 + k * (x - x0);
                    assert!(
                        (l - predicted).abs() <= 1.0,
                        "GM{p} key {key} v{v}: {l:.2} dB is {:.2} dB off the fitted law",
                        l - predicted
                    );
                }
                for w in levels.windows(2) {
                    assert!(
                        w[1].1 > w[0].1,
                        "GM{p} key {key}: v{} ({:.2} dB) not louder than v{} ({:.2} dB)",
                        w[1].0,
                        w[1].1,
                        w[0].0,
                        w[0].1
                    );
                }
            }
        }
    }

    /// AC4 — the exemptions, asserted by name so that dropping one is a deliberate
    /// act rather than an omission. The cathedral organ has its own dedicated test
    /// (`cathedral_organ_steady_level_is_velocity_independent`) which must keep
    /// passing unmodified; this pins the other exemption.
    #[test]
    fn exempt_voices_keep_their_documented_velocity_behaviour() {
        // GM6 harpsichord: a real harpsichord's plucking mechanism is nearly
        // velocity-independent. It uses `vel_sense` to compress velocity BEFORE the
        // global law rather than reintroducing a level floor.
        let soft = melodic_level(6, 60, 72);
        let loud = melodic_level(6, 60, 110);
        assert!(
            loud - soft < 3.0,
            "GM6 harpsichord velocity span {:.2} dB — the vel_sense contract is <3 dB",
            loud - soft
        );
        assert!(
            loud > soft,
            "GM6 must still respond to velocity, just weakly"
        );
    }

    /// AC6 — the drums follow the SAME law as the melodic voices.
    ///
    /// This is the oracle for Arthur's original complaint. Drums previously used the
    /// bare curve (5.89 dB over v=72→110) while most melodic voices used a floor
    /// (2.71 dB), so the kit gained on the band as a passage got louder — a balance
    /// *instability* that no static level constant can correct. Sharing one exponent
    /// makes the drums/band ratio velocity-invariant by construction; this test is
    /// what stops that symmetry being broken again.
    #[test]
    fn drums_follow_the_same_law_as_melodic_voices() {
        let mut kd = Vec::new();
        for key in [36u8, 38, 42, 45, 46, 49, 51] {
            let levels: Vec<(u8, f32)> = FIT_VELS
                .iter()
                .filter_map(|&v| drum_level(key, v).map(|l| (v, l)))
                .collect();
            assert_eq!(levels.len(), FIT_VELS.len(), "drum key {key} did not sound");
            let k = fit_k(&levels);
            assert!(
                (k - 2.0).abs() <= 0.2,
                "drum key {key}: velocity exponent {k:.3}, want 2.0 +/- 0.2"
            );
            kd.push(k);
        }
        let melodic = median(PROBE_PROGRAMS.iter().map(|&p| melodic_k(p)).collect());
        let drums = median(kd);
        assert!(
            (drums - melodic).abs() <= 0.15,
            "drums fit {drums:.3} but melodic voices fit {melodic:.3} — the kit would \
             gain on the band as passages get louder"
        );
    }
}
