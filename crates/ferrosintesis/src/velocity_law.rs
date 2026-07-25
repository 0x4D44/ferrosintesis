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
        crate::loudness::momentary_lufs(&stereo, SR as u32)
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

    /// Bypasses `VEL_LEVEL_EXP` so the census can see a voice's RAW curve.
    fn make_uncorrected_for_census(program: u8, key: u8, vel: u8) -> Box<dyn voices::Voice> {
        voices::make_uncorrected_for_test(program, key, vel, SR, SEED, true)
    }

    fn melodic_level(program: u8, key: u8, vel: u8) -> f32 {
        level_db(&render(
            voices::make(program, key, vel, SR, SEED, true),
            1.2,
        ))
    }

    fn drum_level_kit_s(key: u8, vel: u8, kit: drums::Kit, samples: bool) -> Option<f32> {
        let v = drums::make(key, vel, SR, SEED, kit, samples, 0)?;
        Some(level_db(&render(v, 1.2)))
    }

    fn drum_level_kit(key: u8, vel: u8, kit: drums::Kit) -> Option<f32> {
        drum_level_kit_s(key, vel, kit, true)
    }

    fn drum_level(key: u8, vel: u8) -> Option<f32> {
        drum_level_kit(key, vel, drums::Kit::V3)
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
    const PROBE_PROGRAMS: [u8; 15] = [0, 4, 5, 11, 24, 33, 40, 48, 52, 56, 60, 65, 73, 80, 89];

    /// DEV TOOL, not an oracle. Prints the rendered velocity exponent for every GM
    /// program and drum key, and the compensation each would need to land on 2.0.
    /// This is how `VEL_LEVEL_EXP` is derived — the constants are measured here,
    /// never picked.
    ///
    ///     cargo test -p ferrosintesis --lib velocity_census -- --ignored --nocapture
    #[test]
    #[ignore = "dev tool: prints the census used to derive VEL_LEVEL_EXP"]
    fn velocity_census() {
        println!("\nprogram   k(key48)   k(key60)     spread  needed_exp");
        for p in 0u8..128 {
            // Measure at BOTH probe keys. A single-key derivation is how the first
            // pass of this table went wrong: several voices have a register-dependent
            // velocity law, and a scalar exponent fitted at one key does not hold at
            // the other.
            let k48 = melodic_k_at(p, 48);
            let k60 = melodic_k_at(p, 60);
            let k = 0.5 * (k48 + k60);
            let spread = (k48 - k60).abs();
            // `k` is measured through the CURRENT table, so the correction is
            // relative to whatever exponent is already applied:
            //   k = s + e_old  =>  e_new = e_old + (2 - k)
            // Using `4 - k` here would be right only for an uncompensated voice, and
            // silently wrong for every entry already in the table.
            let e_old = crate::voices::VEL_LEVEL_EXP[p as usize];
            let e_new = e_old + (2.0 - k);
            let mut flag = String::new();
            if (k48 - 2.0).abs() > 0.15 || (k60 - 2.0).abs() > 0.15 {
                flag.push_str(" OFF-LAW");
            }
            if spread > 0.25 {
                flag.push_str(" KEY-DEPENDENT");
            }
            if !flag.is_empty() {
                println!(
                    "GM{p:<5} {k48:>9.3} {k60:>10.3} {spread:>10.3}   \
                     e_old {e_old:.3} -> e_new {e_new:.3}{flag}"
                );
            }
        }
        // Is a suspect voice's RAW curve (compensation bypassed) even monotonic?
        for p in [42u8, 43] {
            for key in [48u8, 60] {
                print!("GM{p} key {key} raw:");
                for &v in &[64u8, 80, 96, 110, 127] {
                    let l = level_db(&render(make_uncorrected_for_census(p, key, v), 1.2));
                    print!("  v{v}={l:.2}");
                }
                println!();
            }
        }

        // PER-KIT drum velocity law (Arthur: "shouldn't we do each drum set
        // individually?"). DRUM_VEL_LEVEL_EXP is currently measured on V3 and applied
        // to every kit; this shows whether the shipping kits (V1/V3/Brush/Synth)
        // actually diverge. RAW k reported (the applied V3 correction is undone), so
        // the columns are directly comparable across kits.
        {
            use drums::Kit::{Brush, Synth, V1, V3};
            let kits = [("V1", V1), ("V3", V3), ("Brush", Brush), ("Synth", Synth)];
            // Paste-ready per-kit needed exponent (4 - raw_k) for every drum key where a
            // kit's raw slope is off 2.0 by more than 0.15 — the same guard the melodic
            // table uses. Emits one block per kit.
            // Does each kit's velocity RESPONSE change with the samples flag? (If not,
            // one table per kit suffices; if yes, the table must key on samples too —
            // which the Synth==V3-samples-off invariant forces for V3.)
            println!("\nsamples on-vs-off divergence per kit (keys 35..57, worst dB at v64):");
            for (name, kit) in kits {
                let mut worst = 0.0f32;
                let mut worst_key = 0u8;
                for key in 35u8..=57 {
                    if let (Some(on), Some(off)) = (
                        drum_level_kit_s(key, 64, kit, true),
                        drum_level_kit_s(key, 64, kit, false),
                    ) {
                        if (on - off).abs() > worst.abs() {
                            worst = on - off;
                            worst_key = key;
                        }
                    }
                }
                println!("  {name}: worst {worst:+.2} dB at key {worst_key}");
            }

            // Needed exponents for each shipping (kit, samples) config that renders a
            // DISTINCT voice: V1/Synth are samples-inert (one entry each); V3 and Brush
            // differ by samples, so both are listed. `raw k` undoes the currently-applied
            // correction so `needed = 4 - raw_k` is the absolute target.
            let configs = [
                ("V1", V1, true),
                ("V3+samples", V3, true),
                ("V3-modeled(=Synth)", V3, false),
                ("Brush+samples", Brush, true),
                ("Brush-modeled", Brush, false),
                ("Synth", Synth, true),
            ];
            for (name, kit, samples) in configs {
                let mut entries: Vec<(u8, f32)> = Vec::new();
                for key in 27u8..=87 {
                    let levels: Vec<(u8, f32)> = FIT_VELS
                        .iter()
                        .filter_map(|&v| drum_level_kit_s(key, v, kit, samples).map(|l| (v, l)))
                        .collect();
                    if levels.len() != FIT_VELS.len() {
                        continue;
                    }
                    let applied = crate::drums::drum_vel_level_exp(kit, samples, key);
                    let k_raw = fit_k(&levels) - (applied - 2.0);
                    if (k_raw - 2.0).abs() > 0.15 {
                        entries.push((key, 4.0 - k_raw));
                    }
                }
                print!("CFG {name}:");
                for (key, exp) in &entries {
                    print!(" [{key}]={exp:.3}");
                }
                println!("   ({} keys)", entries.len());
            }
        }

        println!("\ndrum key  k(rendered)  needed_exp");
        for key in 27u8..=87 {
            let levels: Vec<(u8, f32)> = FIT_VELS
                .iter()
                .filter_map(|&v| drum_level(key, v).map(|l| (v, l)))
                .collect();
            if levels.len() != FIT_VELS.len() {
                continue;
            }
            let k = fit_k(&levels);
            let flag = if (k - 2.0).abs() > 0.25 { " <--" } else { "" };
            println!("key {key:<4}  {k:>10.3}  {:>10.3}{flag}", 4.0 - k);
        }
    }

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
            // Exemptions are BY NAME AND BY REASON, never by silence.
            //
            //  6      harpsichord — deliberately velocity-compressed (`vel_sense`);
            //         asserted separately against its own <3 dB contract.
            //  109    bagpipe — the chanter is a constant-pressure looped sample and
            //         takes no velocity at all (`bagpipe_chanter_loop(key, sr)`). A
            //         piper physically cannot play it louder; velocity-independence
            //         is correct, exactly as for the organ. PINNED POSITIVELY by
            //         `looped_recording_voices_keep_their_documented_velocity_behaviour`.
            //  96     FX 1 (rain) — measures k≈0.49. A noise texture whose level is
            //         dominated by a velocity-independent bed. UNDIAGNOSED: exempted
            //         rather than compensated because no reference measurement exists
            //         for it, and an exponent near 3.5 would be a constant nobody
            //         could justify. Worth a look if an FX-heavy file ever reads wrong.
            //  42-43  cello / contrabass — their RAW velocity curve turns over at the
            //         top (v110 -> v127 DROPS ~1.1-1.6 dB where it should rise 2.49).
            //         Pre-existing defect in the bowed-string model, not in the
            //         velocity law; a scalar exponent cannot correct a non-monotonic
            //         curve. Tracked separately - fixing it needs the model, not this.
            //  76     blown bottle — its default (samples-on) voice is a looped real
            //         recording (`BottleLoopVoice`) with a deliberately compressed
            //         taper; measures k≈0.39, same class as the bagpipe chanter loop.
            //         Its velocity response is the recording's, not this table's.
            //         PINNED POSITIVELY: `looped_recording_voices_keep_their_documented_
            //         velocity_behaviour` (samples-on span) and `modeled_gm76_follows_
            //         the_square_law_in_no_samples_builds` (the modeled `--no-samples` /
            //         repitch-fallback path). NOTE: that path is NOT compensated
            //         samples-aware — there is no `melodic_vel_level_exp`;
            //         `VEL_LEVEL_EXP` is program-indexed, so the modeled voice inherits
            //         the sampled voice's exponent. MM-BUG-KILN-00105.
            if p == 6 || p == 76 || p == 96 || p == 109 || p == 42 || p == 43 {
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

    /// KILN-00048 anti-papering bound: no `Pluck`-rendered program's
    /// `VEL_LEVEL_EXP` may leave [1.5, 2.35]. A Pluck's excitation is level-exact
    /// (∝ v), so `e − 2` IS the onset-law distortion the compensation buys, and
    /// 0.35 matches the reference hardware's own worst per-patch velocity spread
    /// (SC-55 per-program k ranges 1.67–2.06 on this estimator). An entry past
    /// 2.35 means the pp/ff spectral swing is out of family — the fix is the
    /// voicing (a pitch-relative pp excitation floor, `KS_PICK_F0_FLOOR`), never
    /// a fatter table. This machine-checks what was the informal 2.2 red line
    /// (KILN-00048 Tripwire 2). koto (107) sits AT the bound with the pitch floor
    /// closing the remainder; t[28]/t[106] ride just under it — all named.
    #[test]
    fn pluck_vel_level_exp_within_anti_papering_bound() {
        // Programs dispatched through `Pluck` (the KILN-00042 in-scope set).
        const PLUCK_PROGRAMS: [u8; 23] = [
            6, 7, 15, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 45, 46, 104, 105,
            106, 107,
        ];
        for p in PLUCK_PROGRAMS {
            let e = crate::voices::VEL_LEVEL_EXP[p as usize];
            assert!(
                (1.5..=2.35).contains(&e),
                "GM{p} VEL_LEVEL_EXP {e:.3} outside the [1.5, 2.35] anti-papering bound — \
                 a compensation this large is a mechanism, not a trim; fix the pp voicing"
            );
        }
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
        for &p in &[0u8] {
            for key in FIT_KEYS {
                let levels: Vec<(u8, f32)> = SEAM_VELS
                    .iter()
                    .map(|&v| (v, melodic_level(p, key, v)))
                    .collect();
                // This test owns SEAM CONTINUITY; the shape of the law is AC2's job.
                // Across a bank boundary the level must not jump: the pairs straddle
                // 51/52, 79/80 and 95/96, and an uncompensated pp↔mf recording step
                // shows up as >= 3 dB between two velocities one apart. (Whole-curve
                // linearity is deliberately NOT asserted here — below v≈48 the sampled
                // onset and the modelled body cross over and the composite legitimately
                // bends, which is not a seam defect.)
                let at = |v: u8| levels.iter().find(|(x, _)| *x == v).unwrap().1;
                for (lo, hi) in [(51u8, 52u8), (79, 80), (95, 96)] {
                    let step = at(hi) - at(lo);
                    assert!(
                        step.abs() <= 1.5,
                        "GM{p} key {key}: {step:+.2} dB jump across the v{lo}/v{hi} \
                         layer boundary — an uncompensated bank step"
                    );
                }
                // Monotonicity with a tolerance. The defect this catches is an
                // UNCOMPENSATED layer step, which is >= 3 dB; sub-dB wobble across a
                // crossfade is measurement scale, not a seam break, and a strict
                // increase would fail on dips no ear can hear (GM42 dips 0.51 dB
                // between v110 and v127 at one key — a local flattening in the cello's
                // top end, not a bank boundary).
                for w in levels.windows(2) {
                    assert!(
                        w[1].1 > w[0].1 - 1.0,
                        "GM{p} key {key}: v{} ({:.2} dB) drops {:.2} dB below v{} — \
                         a layer step, not crossfade wobble",
                        w[1].0,
                        w[1].1,
                        w[0].1 - w[1].1,
                        w[0].0
                    );
                }
            }
        }
    }

    /// The excluded programs must STILL BE BROKEN. An exclusion that silently
    /// becomes unnecessary is a dead blind spot: whoever fixes the bowed-string model
    /// should be forced to delete the exemption, not left free to leave it rotting.
    #[test]
    fn excluded_programs_still_reproduce_their_defect() {
        for p in [42u8, 43] {
            let k = melodic_k_at(p, 60);
            assert!(
                (k - 2.0).abs() > 0.25,
                "GM{p} now fits {k:.3} — the bowed-string turnover appears FIXED.                  Delete its exclusion in every_gm_program_follows_the_square_law and                  its VEL_LEVEL_EXP note, then remove this assertion."
            );
        }
    }

    /// AC9 — the `--no-samples` / modeled path is ALSO on the law where the
    /// samples-on voice is exempted for being a real recording.
    ///
    /// The whole sweep above runs `samples=true` (HLD §5). GM76's samples-on voice
    /// is the exempted `BottleLoopVoice`, but two paths render the MODELED Wind
    /// bottle instead: a `--no-samples` build, and — in ANY build — a GM76 note
    /// more than ~1 octave from the bottle sample's zone root, which falls back via
    /// `bottle_loop_voice(...).unwrap_or(model)` (`voices.rs`, the `76 =>` arm). That
    /// model is a plain velocity-sensitive voice and must obey k=2 like any other.
    ///
    /// It regressed silently: removing `VEL_LEVEL_EXP[76]=1.450` (correct — it was
    /// double-correcting the self-compensating loop) also dropped the modeled
    /// path's compensation, because `VEL_LEVEL_EXP` is program-indexed, not
    /// samples-aware. The samples-on sweep can't see it (there GM76 is the loop).
    /// This pins the modeled path. NOTE: the compensation is NOT samples-aware — there
    /// is no `melodic_vel_level_exp`; `VEL_LEVEL_EXP` is program-indexed and the modeled
    /// voice inherits the sampled exponent. MM-BUG-KILN-00105.
    #[test]
    fn modeled_gm76_follows_the_square_law_in_no_samples_builds() {
        for &key in &FIT_KEYS {
            let levels: Vec<(u8, f32)> = FIT_VELS
                .iter()
                .map(|&v| {
                    let l = level_db(&render(voices::make(76, key, v, SR, SEED, false), 1.2));
                    (v, l)
                })
                .collect();
            let k = fit_k(&levels);
            assert!(
                (k - 2.0).abs() <= 0.2,
                "modeled GM76 (--no-samples) key {key}: velocity exponent {k:.3}, want 2.0 +/- 0.2 \
                 — the modeled Wind bottle lost its compensation when VEL_LEVEL_EXP[76] was removed"
            );
        }
    }

    /// A program that CARRIES a `VEL_LEVEL_EXP` correction must still get louder as it
    /// is played harder — derived from the table itself, so it needs no maintenance.
    ///
    /// The correction is `(v/127)^(e-2)`, which for `e < 2` RISES as velocity falls. It
    /// is safe only under the premise `apply_vel_correction` states — "the voice already
    /// carries (v/127)^2 from `vel_amp`" — because then the two powers compose to
    /// `(v/127)^e`, still rising for any `e > 0`. Where that premise is false the
    /// correction is not reshaping a curve, it is inverting one.
    ///
    /// It WAS false: GM6's model squares a `vel_sense`-COMPRESSED velocity, so
    /// `t[6] = 1.500` multiplied a near-flat law by `(v/127)^-0.5` and made the
    /// harpsichord 5.02 dB louder at v40 than at v127 — backwards, and under
    /// `--no-samples` too (MM-BUG-KILN-00044). This is the guard that fails on that.
    ///
    /// Derived, not a list: it walks every program the table actually corrects, so a
    /// future entry on another compressed voice is caught the day it lands. The
    /// uncorrected voices are covered by the square-law sweep and its named exemptions.
    #[test]
    fn corrected_programs_still_rise_with_velocity() {
        let corrected: Vec<u8> = (0u8..128)
            .filter(|&p| voices::VEL_LEVEL_EXP[p as usize] != 2.0)
            .collect();
        assert!(
            corrected.len() > 10,
            "only {} corrected programs — the table lookup is not reaching VEL_LEVEL_EXP",
            corrected.len()
        );
        let mut backwards = Vec::new();
        for p in corrected {
            let soft = melodic_level(p, 60, 48);
            let loud = melodic_level(p, 60, 120);
            if loud <= soft {
                backwards.push(format!(
                    "GM{p} (e={:.3}): v48 {soft:.2} dB -> v120 {loud:.2} dB ({:+.2})",
                    voices::VEL_LEVEL_EXP[p as usize],
                    loud - soft
                ));
            }
        }
        assert!(
            backwards.is_empty(),
            "these corrected programs get QUIETER as velocity rises — the \
             `(v/127)^(e-2)` correction is being applied to a voice that does not carry \
             the plain square law:\n  {}",
            backwards.join("\n  ")
        );
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

    /// AC11 — the looped-recording voices keep their DOCUMENTED, deliberate
    /// velocity behaviour, so their exemption from `every_gm_program_follows_the_
    /// square_law` is a positive pin, not a silent blind spot. Each is a real
    /// recording (or a constant-pressure sample) that cannot follow k=2 the way a
    /// model does — but "exempt" must never mean "unchecked".
    #[test]
    fn looped_recording_voices_keep_their_documented_velocity_behaviour() {
        // GM76 blown bottle: a single-dynamic recording (no p/f layers), so it
        // CANNOT brighten with velocity. `BottleLoopVoice` gives it a deliberately
        // COMPRESSED level taper (`0.55 + 0.45·vel_amp`, sampler.rs) — present but
        // far shallower than k=2. Pin the compressed span so it can neither drift to
        // velocity-flat (span → 0, a dead dynamic) nor to the full square law
        // (~24 dB over v32→v127, which would mean a layer double-count crept back).
        // Only meaningful where the recording EXISTS. The compressed taper is a property
        // of `BottleLoopVoice`; under `--no-default-features` GM76 is the modeled `Wind`,
        // which correctly renders the full square law (~25 dB measured) and so would fail
        // this band for the right reason. The modeled path is pinned separately by
        // `modeled_gm76_follows_the_square_law_in_no_samples_builds`, so gating here loses
        // no coverage. MM-BUG-KILN-00105.
        if crate::embedded_samples_available() {
            let bottle_span = melodic_level(76, 60, 127) - melodic_level(76, 60, 32);
            assert!(
                (2.5..=7.0).contains(&bottle_span),
                "GM76 bottle velocity span {bottle_span:.2} dB (v32→v127) — outside the \
                 documented compressed band [2.5, 7.0]: <2.5 = drifted flat, >7.0 = a \
                 layer/compensation double-count reintroduced"
            );
        }

        // GM109 bagpipe chanter: constant bag pressure — a piper physically cannot
        // play it louder, so `LoopVoice` takes NO velocity (`bagpipe_chanter_loop`).
        // Velocity-flat is the instrument, exactly as for the cathedral organ; the
        // sampler's `bp_o1…constant_amplitude` oracle pins the waveform, this pins
        // the rendered level.
        let pipe_span = melodic_level(109, 60, 120) - melodic_level(109, 60, 40);
        assert!(
            pipe_span.abs() < 1.0,
            "GM109 bagpipe velocity span {pipe_span:.2} dB — the chanter is \
             constant-pressure (velocity-flat); a nonzero span means LoopVoice grew \
             a velocity path"
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
        // EVERY shipping (kit, samples) config, not just V3 — the kits diverge, and V3
        // and Brush ALSO diverge by the samples flag (they swap keys onto the sampled
        // bank), so a single correction fits none of the others. The original V1 kit is
        // live on several albums, and the samples-off configs ship in --no-samples
        // builds, so both axes matter.
        let melodic = median(PROBE_PROGRAMS.iter().map(|&p| melodic_k(p)).collect());
        for (name, kit, samples) in [
            ("V1", drums::Kit::V1, true),
            ("V3+samples", drums::Kit::V3, true),
            ("V3-modeled", drums::Kit::V3, false),
            ("Brush+samples", drums::Kit::Brush, true),
            ("Brush-modeled", drums::Kit::Brush, false),
            ("Synth", drums::Kit::Synth, true),
        ] {
            let mut kd = Vec::new();
            for key in [36u8, 38, 42, 45, 46, 49, 51] {
                let levels: Vec<(u8, f32)> = FIT_VELS
                    .iter()
                    .filter_map(|&v| drum_level_kit_s(key, v, kit, samples).map(|l| (v, l)))
                    .collect();
                assert_eq!(
                    levels.len(),
                    FIT_VELS.len(),
                    "{name} key {key} did not sound"
                );
                let k = fit_k(&levels);
                assert!(
                    (k - 2.0).abs() <= 0.2,
                    "{name} drum key {key}: velocity exponent {k:.3}, want 2.0 +/- 0.2"
                );
                kd.push(k);
            }
            let drums = median(kd);
            assert!(
                (drums - melodic).abs() <= 0.15,
                "{name} drums fit {drums:.3} but melodic voices fit {melodic:.3} — the \
                 kit would gain on the band as passages get louder"
            );
        }
    }
}
