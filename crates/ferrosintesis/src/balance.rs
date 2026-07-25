//! Instrument-balance oracles: does `PROGRAM_TRIM_DB` reach the audio, and by
//! exactly how much?
//!
//! ## The gap this closes
//!
//! Before this module, **nothing in the suite measured a rendered program level at
//! all**. `engine::tests::program_trim_scope_and_calibration` asserts the TABLE'S
//! CONTENTS — which programs are non-zero and by how much — and is blind to what
//! those numbers do to the audio. The one full-128 sweep asserts the velocity
//! SLOPE, which is blind to absolute gain by construction. A trim could have been
//! silently dropped from the signal path, or applied twice, and both would have
//! stayed green. Two oracles close it: one proves the dB->gain conversion is
//! exact, the other proves the strip actually applies it. Either alone is
//! insufficient - a correct conversion nothing calls is a silent no-op.
//!
//! ## What is deliberately NOT asserted here, and why
//!
//! Not that programs are equally loud, and **not that the trim narrows any family's
//! internal spread**. Both would be wrong.
//!
//! `PROGRAM_TRIM_DB` levels the melodic programs toward the balance a Roland
//! SC-55mkII produces. The stated goal is fidelity to the GM corpus, not flatness:
//! "Arthur chose to level toward a real GM module's balance (keeps
//! flute-quieter-than-trumpet) rather than flatten to equal loudness"
//! (`wrk_docs/2026.07.17 - CR - instrument level audit + SC-55 trim.md`). A control
//! taken 2026.07.25 found ferrosintesis's program-to-program spread statistically
//! indistinguishable from the reference modules' own — within ±1 dB of its own
//! median, ferro 11–16 %, SC-55 14 %, S-YXG50 14 %.
//!
//! Measured on 2026.07.25, the trim NARROWS six families (Ensemble −6.0, Lead −5.5,
//! Pad −4.6, Reed −2.2, Brass −2.2, Percussive −1.0 dB) and WIDENS five (Ethnic
//! +5.0, Pipe +4.1, ChromPerc +1.5, Organ +0.9, Strings +0.5 dB). Widening is not a
//! defect: if the SC-55's Pipe family is internally wide, then widening ferro's Pipe
//! family is the trim working correctly. An oracle asserting "the trim must narrow"
//! would encode precisely the flatness goal this design rejected, so it is not
//! written here. Deciding whether each widening is faithful needs the reference
//! module, which a unit test cannot reach — that lives in the closed-loop re-derive
//! (MM-BUG-KILN-00107). `report_trim_effect_on_family_spread` below prints the
//! table for whoever runs it.
//!
//! ## Method
//!
//! Early-window RMS, 0–150 ms. That is this repo's own documented fair metric for
//! cross-program comparison — the `PROGRAM_TRIM_DB` doc comment used it for GM6
//! precisely because it is "immune to the decay-artifact trap". A whole-note RMS
//! penalises a fast decay for decaying, which is how the rejected 21-Jul
//! max-momentary derivation came out wrong in SIGN on ~8 voices.
//!
//! Known blind spot, stated rather than hidden: the early window is unfair to
//! voices that SWELL. GM119 Reverse Cymbal is a swell by definition, reads as near
//! silence at 0–150 ms, and single-handedly makes the Percussive family span 45 dB
//! in the report below. That is a metric artifact, not a balance defect. It is why
//! the report tests are diagnostics rather than gates.

#[cfg(test)]
mod tests {
    use crate::engine::PROGRAM_TRIM_DB;

    const SR: f32 = 44100.0;
    /// This repo's documented fair cross-program window (see module docs).
    const EARLY_WINDOW_S: f32 = 0.150;

    /// The sixteen GM families, in program order; each is exactly 8 programs.
    const FAMILIES: [&str; 16] = [
        "Piano",
        "ChromPerc",
        "Organ",
        "Guitar",
        "Bass",
        "Strings",
        "Ensemble",
        "Brass",
        "Reed",
        "Pipe",
        "Lead",
        "Pad",
        "SynthFX",
        "Ethnic",
        "Percussive",
        "SoundFX",
    ];

    /// The measurement grid. Several keys so one unlucky sample-bank root cannot
    /// dominate, and both a soft and a loud velocity.
    const CELLS: [(u8, u8); 5] = [(48, 80), (60, 80), (72, 80), (60, 55), (60, 105)];

    /// Raw early-window level of a voice in dB, with NO trim applied. This is what
    /// `voices::make` produces; the trim lives downstream at the channel strip.
    fn voice_level_db(program: u8, key: u8, vel: u8) -> f32 {
        let n = (EARLY_WINDOW_S * SR) as usize;
        let mut buf = vec![0.0f32; n];
        let mut v = crate::voices::make(program, key, vel, SR, 0x5EED_1234, true);
        let mut i = 0;
        while i < n {
            let k = 64.min(n - i);
            v.render(&mut buf[i..i + k]);
            i += k;
        }
        let energy: f32 = buf.iter().map(|x| x * x).sum();
        20.0 * (energy / n as f32).sqrt().max(1e-12).log10()
    }

    /// Mean raw level over the grid.
    fn voice_level_mean(program: u8) -> f32 {
        CELLS
            .iter()
            .map(|&(k, v)| voice_level_db(program, k, v))
            .sum::<f32>()
            / CELLS.len() as f32
    }

    /// THE GATE. Every program's trim reaches the audio, at exactly its tabled value.
    ///
    /// `program_trim_lin` is the one conversion from the table to a strip gain. This
    /// asserts the round trip: the linear gain it hands the strip, expressed back in
    /// dB, equals the table entry — for all 128 programs, including the 0.0 entries
    /// which must yield EXACTLY unity so an untouched program is bit-identical.
    ///
    /// SCOPE, stated honestly: this exercises the pure conversion, so it catches a
    /// wrong sign, a wrong logarithm base (the classic power-vs-amplitude factor of
    /// two), a non-unity gain on an untouched program, and any table/gain
    /// divergence. It does NOT by itself prove the trim reaches the audio — if the
    /// strip stopped calling `program_trim_lin`, this test would still pass. That
    /// second half is `the_strip_actually_applies_the_program_trim` below; the two
    /// are only sufficient together.
    #[test]
    fn every_program_trim_reaches_the_strip_at_its_tabled_value() {
        let mut worst = (0u8, 0.0f32);
        for p in 0..128u8 {
            let tabled = PROGRAM_TRIM_DB[p as usize];
            let lin = crate::engine::program_trim_lin(p);

            if tabled == 0.0 {
                assert_eq!(
                    lin, 1.0,
                    "GM{p} has no trim but program_trim_lin returned {lin}, not exactly 1.0. \
                     An untouched program must be bit-identical, so this must be exact \
                     equality and not a tolerance."
                );
                continue;
            }

            assert!(
                lin > 0.0 && lin.is_finite(),
                "GM{p}: trim {tabled} dB produced a non-positive or non-finite gain {lin}"
            );
            let round_trip = 20.0 * lin.log10();
            let err = (round_trip - tabled).abs();
            if err > worst.1 {
                worst = (p, err);
            }
            assert!(
                err < 1e-4,
                "GM{p}: tabled {tabled:+.2} dB but program_trim_lin gives {lin} \
                 = {round_trip:+.4} dB (error {err:.6} dB). The table and the gain \
                 conversion have diverged."
            );
            assert_eq!(
                lin > 1.0,
                tabled > 0.0,
                "GM{p}: trim {tabled:+.2} dB produced gain {lin}, which moves the level \
                 the WRONG WAY. A boost must be >1.0 and a cut <1.0."
            );
        }
        println!(
            "all 128 program trims round-trip; worst error GM{} at {:.2e} dB",
            worst.0, worst.1
        );
    }

    /// The strip actually APPLIES the trim — the half the round-trip cannot see.
    ///
    /// Two oracles, because one is not enough: a correct conversion that nothing
    /// calls is a silent no-op. This asserts, from the source, that the melodic
    /// channel-strip gain is multiplied by `program_trim_lin(strip.program)`, and
    /// that ch9 drums are excluded (they are key-indexed and levelled by
    /// `kit_balance`, so a program trim there would be wrong).
    ///
    /// A source scan rather than a render diff on purpose: an end-to-end level
    /// comparison between two DIFFERENT programs cannot isolate the trim, because
    /// their voices, their `fx_profile` sends and their bus contributions all differ
    /// too. The wiring is the checkable invariant.
    #[test]
    fn the_strip_actually_applies_the_program_trim() {
        let src = include_str!("engine.rs");
        let call = "program_trim_lin(strip.program)";
        assert!(
            src.contains(call),
            "the channel strip no longer calls `{call}` — the per-program trim has              been disconnected from the signal path, and every level oracle that              checks only the TABLE would stay green through that regression"
        );

        // The gain that reaches the mix must include the trim as a factor.
        let g_line = src
            .lines()
            .find(|l| l.contains("let g = strip.volume"))
            .expect("the strip gain line `let g = strip.volume ...` has moved or been renamed");
        assert!(
            g_line.contains("trim"),
            "the strip gain no longer includes the program trim:
  {g_line}"
        );

        // Drums must stay out of it.
        assert!(
            src.contains("if ci != 9 {"),
            "the ch9 drum exclusion around the program trim has gone; a program-indexed              trim on the key-indexed drum channel would mis-level the kit"
        );
    }

    /// The derivation tool must read one exact shipped table and derive every zero pin.
    ///
    /// Python's self-test exercises the parser semantics, but the repository gate does
    /// not invoke that script. This source oracle keeps the invariant in the ordinary
    /// Rust suite: an anchored `findall` must reject zero or multiple exact declarations,
    /// the zero-pin parser must fail when it finds no canonical decisions, and both
    /// production values must come from one read of `engine.rs`.
    #[test]
    fn trim_derivation_reads_one_exact_engine_state() {
        let tool = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(2)
            .expect("crates/ferrosintesis sits two levels below the repo root")
            .join("tools/instrument-balance/derive_trims.py");
        let src = std::fs::read_to_string(&tool)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", tool.display()));
        let parsers = src
            .split_once("def parse_shipped(")
            .and_then(|(_, rest)| rest.split_once("\ndef load_shipped("))
            .map(|(body, _)| body)
            .expect("derive_trims.py must define its engine parsers before load_shipped");
        let ear_parser = parsers
            .split_once("def parse_ear_decided(")
            .map(|(_, body)| body)
            .expect("derive_trims.py must define parse_ear_decided");

        for required in ["_SHIPPED_RE.findall(text)", "if len(matches) != 1:"] {
            assert!(
                parsers.contains(required),
                "derive_trims.py no longer enforces `{required}` while parsing the shipped \
                 trim table; a sibling, missing, or cfg-gated duplicate declaration could \
                 silently produce proposals against the wrong table"
            );
        }
        assert!(
            src.contains(r"\bconst\s+PROGRAM_TRIM_DB\b"),
            "derive_trims.py no longer anchors the shipped-table parser to the exact \
             `const PROGRAM_TRIM_DB` declaration; a prefixed sibling can match"
        );
        for required in [
            "_EAR_DECIDED_RE.findall(text)",
            "if not matches:",
            "if invalid:",
            "if len(programs) != len(set(programs)):",
        ] {
            assert!(
                ear_parser.contains(required),
                "derive_trims.py no longer enforces `{required}` while deriving recorded \
                 zero-valued ear decisions; a missing, duplicate, or invalid pin could \
                 silently change which programs the tool is allowed to propose"
            );
        }
        assert!(
            src.contains(r"assert_eq!\(\s*PROGRAM_TRIM_DB\["),
            "derive_trims.py no longer derives ear decisions from canonical \
             `assert_eq!(PROGRAM_TRIM_DB[P], 0.0);` pins"
        );

        let assignments: Vec<&str> = src
            .lines()
            .map(|line| line.split('#').next().unwrap_or("").trim())
            .filter(|line| {
                line.split_once('=')
                    .map(|(lhs, _)| {
                        lhs.split(',')
                            .map(str::trim)
                            .any(|name| name == "SHIPPED" || name == "EAR_DECIDED")
                    })
                    .unwrap_or(false)
            })
            .collect();
        assert_eq!(
            assignments,
            ["SHIPPED, EAR_DECIDED = load_shipped()"],
            "derive_trims.py must assign SHIPPED and EAR_DECIDED exactly once from the \
             same engine.rs read; a literal or alternate assignment recreates source drift"
        );
    }

    /// The cross-run oracle needs a complete, reference-addressed baseline and must keep
    /// guard-excluded rows in its comparison. Otherwise a large regression can exclude
    /// itself from the very check intended to detect it (MM-BUG-KILN-00118).
    #[test]
    fn residual_baseline_covers_every_program_and_both_references() {
        let tools = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
            .ancestors()
            .nth(2)
            .expect("crates/ferrosintesis sits two levels below the repo root")
            .join("tools/instrument-balance");
        let baseline_path = tools.join("residual-baseline.csv");
        let baseline = std::fs::read_to_string(&baseline_path)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", baseline_path.display()));
        let mut data = baseline
            .lines()
            .filter(|line| !line.trim().is_empty() && !line.starts_with('#'));
        assert_eq!(
            data.next(),
            Some("program,reference,residual_db,shipped_db,guard_excluded")
        );

        let mut keys = std::collections::BTreeSet::new();
        let mut gm6 = Vec::new();
        for line in data {
            let columns: Vec<&str> = line.split(',').collect();
            assert_eq!(columns.len(), 5, "malformed residual baseline row: {line}");
            let program: u8 = columns[0]
                .parse()
                .unwrap_or_else(|e| panic!("bad program in `{line}`: {e}"));
            assert!(
                matches!(columns[1], "sc55" | "yxg"),
                "unidentified reference in `{line}`"
            );
            if !columns[2].is_empty() {
                let residual: f32 = columns[2]
                    .parse()
                    .unwrap_or_else(|e| panic!("bad residual in `{line}`: {e}"));
                assert!(residual.is_finite(), "non-finite residual in `{line}`");
            }
            let shipped: f32 = columns[3]
                .parse()
                .unwrap_or_else(|e| panic!("bad shipped trim in `{line}`: {e}"));
            assert!(shipped.is_finite(), "non-finite shipped trim in `{line}`");
            assert!(
                matches!(columns[4], "true" | "false"),
                "bad guard state in `{line}`"
            );
            assert!(
                keys.insert((program, columns[1])),
                "duplicate residual baseline row: {line}"
            );
            if program == 6 {
                gm6.push((columns[1], columns[2], columns[4]));
            }
        }
        let expected: std::collections::BTreeSet<(u8, &str)> = (0..128)
            .flat_map(|program| [(program, "sc55"), (program, "yxg")])
            .collect();
        assert_eq!(keys, expected, "baseline must cover all 256 reference rows");
        assert_eq!(
            gm6,
            [("sc55", "-5.58", "true"), ("yxg", "-3.12", "true")],
            "GM6 is the live excluded-on-both residual example"
        );

        let tool_path = tools.join("derive_trims.py");
        let tool = std::fs::read_to_string(&tool_path)
            .unwrap_or_else(|e| panic!("cannot read {}: {e}", tool_path.display()));
        for required in [
            "DRIFT_FLAG_DB = 1.0",
            "def residual_baseline_findings(",
            "old[\"guard_excluded\"] != new[\"guard_excluded\"]",
            "new_residual + new[\"shipped_db\"]",
            "baseline excluded={old['guard_excluded']}",
            "return 0 if compare_residual_baseline(refs) else 1",
        ] {
            assert!(
                tool.contains(required),
                "derive_trims.py no longer enforces cross-run invariant `{required}`"
            );
        }
    }

    /// The gate above must REJECT a table/gain divergence, otherwise it is decorative.
    ///
    /// Written because this repo has been bitten by oracles that passed on documents
    /// gutted to a bare list of names: a guard that cannot fail proves nothing.
    #[test]
    fn the_trim_gate_rejects_a_divergent_conversion() {
        // A deliberately wrong conversion: amplitude law (20·log10) applied as a
        // power law (10·log10) — the classic factor-of-two dB bug.
        let wrong = |db: f32| 10f32.powf(db / 10.0);
        let mut caught = 0;
        for p in 0..128u8 {
            let tabled = PROGRAM_TRIM_DB[p as usize];
            if tabled == 0.0 {
                continue;
            }
            let round_trip = 20.0 * wrong(tabled).log10();
            if (round_trip - tabled).abs() >= 1e-4 {
                caught += 1;
            }
        }
        assert!(
            caught > 0,
            "the round-trip check cannot detect a power-vs-amplitude dB error, so it \
             would pass on a synth whose trims were all half as strong as tabled"
        );
        // And it must not fire on the correct conversion.
        let right = |db: f32| 10f32.powf(db / 20.0);
        for p in 0..128u8 {
            let tabled = PROGRAM_TRIM_DB[p as usize];
            if tabled == 0.0 {
                continue;
            }
            assert!(
                (20.0 * right(tabled).log10() - tabled).abs() < 1e-4,
                "the check rejects the CORRECT conversion at GM{p} — it is too tight"
            );
        }
    }

    /// GM85's formant bank keeps its make-up gain.
    ///
    /// The regression this pins (MM-BUG-KILN-00108) is the exact shape nothing in
    /// the suite could see: `ec8bfd7` replaced GM85's lowpass with three vocal
    /// formant bandpasses and left off the make-up, dropping it 16.0 dB. Every
    /// existing level check stayed green, and the M-CAL residual oracle could not
    /// catch it either — the fall was large enough to trip that tool's own
    /// pitch-tilt guard, so the program excluded itself from the check meant to
    /// flag it.
    ///
    /// Bar: GM85 must sit within 6 dB of GM84, its nearest sibling in the same
    /// family and the same commit. Measured post-fix at +3.4 dB; the regression put
    /// it at -12.6 dB, so this fails loudly if the make-up is removed or the
    /// formant bank is re-voiced without one. Deliberately a BAND, not a target:
    /// GM85 is allowed to be voiced louder or quieter than GM84, just not by an
    /// order of magnitude.
    #[test]
    fn gm85_formant_bank_keeps_its_make_up_gain() {
        let gm84 = voice_level_mean(84);
        let gm85 = voice_level_mean(85);
        let delta = gm85 - gm84;
        println!("GM85 {gm85:.2} dB vs GM84 {gm84:.2} dB -> {delta:+.2} dB");
        assert!(
            delta.abs() <= 6.0,
            "GM85 sits {delta:+.2} dB from GM84 (bar +/-6). A formant bandpass bank              passes far less broadband energy than a lowpass, so it needs a make-up              gain - see LEAD85_FORMANT_MAKEUP_DB in voices.rs. MM-BUG-KILN-00108 was              exactly this, at -12.6 dB."
        );
    }

    /// REPORT ONLY — per-family internal spread, and what the trim does to it.
    ///
    /// Diagnostic, not a gate: see the module docs for why "the trim must narrow" is
    /// the wrong assertion, and for the swell-voice blind spot that inflates
    /// Percussive. Run with `--ignored` when reviewing the balance.
    #[test]
    #[ignore = "diagnostic; run with --ignored when reviewing instrument balance"]
    fn report_trim_effect_on_family_spread() {
        let spread = |family: usize, trimmed: bool| -> f32 {
            let levels: Vec<f32> = ((family * 8)..(family * 8 + 8))
                .map(|p| voice_level_mean(p as u8) + if trimmed { PROGRAM_TRIM_DB[p] } else { 0.0 })
                .collect();
            levels.iter().cloned().fold(f32::NEG_INFINITY, f32::max)
                - levels.iter().cloned().fold(f32::INFINITY, f32::min)
        };
        println!(
            "\n{:>3} {:<11} {:>10} {:>10} {:>10}   effect",
            "#", "family", "untrimmed", "trimmed", "change"
        );
        for (f, name) in FAMILIES.iter().enumerate() {
            let (un, tr) = (spread(f, false), spread(f, true));
            let d = tr - un;
            let touched = ((f * 8)..(f * 8 + 8)).any(|p| PROGRAM_TRIM_DB[p] != 0.0);
            let effect = if !touched {
                "untouched"
            } else if d < -0.05 {
                "narrows"
            } else if d > 0.05 {
                "widens"
            } else {
                "neutral"
            };
            println!("{f:>3} {name:<11} {un:>9.2}  {tr:>9.2}  {d:>+9.2}   {effect}");
        }
        println!("\n(widening is not a defect - the target is SC-55 fidelity, not flatness)\n");
    }
}
