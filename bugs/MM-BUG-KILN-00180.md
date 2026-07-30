# MM-BUG-KILN-00180 — The MM-BUG-KILN-00178 roughness bar (0.996) is fitted to the removed zone, not derived: six shipping baritone zones sit below it

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** oracle design / sampled sax zones
- **Raised:** 2026-07-30
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-30, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-30, deltic:auto role=fix run=fix-20260730T083147Z-p60316-n677279500-c1 branch=task/bug-MM-BUG-KILN-00180-run-fix-20260730T083147Z-p60316-n677279500-c1 code=f1ad832dd1a1a6e1acb0fa572dd7aaa9ff0950bc gate=manual) -> Closed (2026-07-30, independently verified by claude-opus-5@high on trunk 53902d0; fix authored by OpenAI Codex GPT-5, so two-eyes holds)

## Observation

Residual split from MM-BUG-KILN-00178 during its independent two-eyes closure.
MM-BUG-KILN-00178's audio defect is genuinely fixed; this is a guard-durability
defect in the oracle that fix shipped with. Not a shipped audio defect.

`baritone_sax_key58_avoids_a_rough_source_zone` in
`crates/ferrosintesis/src/sampler.rs` asserts the zone key 58 selects has
`best_cycle_correlation > 0.996`. That bar is fitted: it sits in the narrow gap
between the zone the fix removed and the zone key 58 now lands on, and it does
not describe "rough".

Measured on trunk 73ec2f2 with the G#3 zones temporarily restored, applying the
test's own `best_cycle_correlation` to **every** zone in both baritone banks:

| bank | zone root Hz | cycle-corr | below the 0.996 bar? |
| --- | ---: | ---: | --- |
| bar_p | 69.65 | 0.99646 | |
| bar_p | 82.52 | 0.99596 | yes |
| bar_p | 103.47 | 0.99342 | yes |
| bar_p | 130.04 | 0.99560 | yes |
| bar_p | 163.27 | 0.99699 | |
| bar_p | 208.95 | 0.99481 | yes — removed by 00178 |
| bar_p | 263.75 | 0.99753 | |
| bar_p | 335.01 | 0.99794 | |
| bar_p | 421.23 | 0.99807 | |
| bar_p | 450.50 | 0.99833 | |
| bar_f | 65.83 | 0.99683 | |
| bar_f | 82.38 | 0.99571 | yes |
| bar_f | 103.46 | 0.99604 | |
| bar_f | 130.22 | 0.99296 | yes |
| bar_f | 162.90 | 0.99696 | |
| bar_f | 209.52 | **0.77865** | yes — removed by 00178, the real defect |
| bar_f | 261.13 | 0.99821 | |
| bar_f | 334.08 | 0.99962 | |
| bar_f | 420.54 | 0.99967 | |
| bar_f | 448.84 | 0.99674 | |

The genuinely broken take is `sax_bar_G#3_f.wav` at **0.779** — two orders of
magnitude further from 1.0 than anything else, and decisive evidence for
MM-BUG-KILN-00178's diagnosis. Every other zone spans 0.9930–0.9997, ordinary
take-to-take variation.

**Expected.** The bar separates the 0.779 outlier from the healthy population —
derived from the measured spread (e.g. a population-relative bar, or a
differential against the bank median, in the `snare_grain_is_aperiodic_and_impulsive_v3`
pattern MM-BUG-KILN-00179 cites).

**Actual.** A hand-written 0.996 that five *healthy* shipping zones already sit
below (bar_p 82.52 / 103.47 / 130.04, bar_f 82.38 / 130.22). The test passes only
because it checks one key, and that key happens to land on a zone above the bar.
Any later change to zone roots, bank contents, or the checked key can make an
ordinary zone selected and trip a false failure; equally, a real 0.85 take
elsewhere in the bank goes unchecked.

This is the fitted-threshold half of the defect class CLAUDE.md documents under
"Hand-maintained lists are the recurring defect here — derive them", and the
ledger already carries MM-BUG-KILN-00179 for the sibling oracle's missing
positive control.

**Second, smaller residual.** Removing both G#3 zones opens a 163.27 → 263.75 Hz
gap in `sax_bar_p` (and 162.90 → 261.13 in `sax_bar_f`) — 8.3 semitones, so a
worst-case repitch of ±4.15 semitones for keys in the middle of the baritone
range. Nothing guards maximum zone stretch. Whether that is audible was not
assessed; the alternative (keeping a 0.779 take) is plainly worse, so this is
recorded rather than argued.

**Repro.** In `crates/ferrosintesis/src/sampler.rs`, restore the two
`"sax_bar_G#3_p.wav" => 208.95` / `"sax_bar_G#3_f.wav" => 209.52` lines to
`sax_bar_p()` / `sax_bar_f()`, then apply `best_cycle_correlation` (copied from
the test) to every zone of `sax_bank(67, 72)` and `sax_bank(67, 110)`. The WAVs
are still packaged — MM-BUG-KILN-00178 deliberately kept them for provenance.

## Fix

`f1ad832d` (OpenAI Codex GPT-5) at `crates/ferrosintesis/src/sampler.rs`, replacing
`baritone_sax_key58_avoids_a_rough_source_zone` with
`baritone_sax_bank_rejects_the_rough_source_population_outlier`:

- Censuses **every** zone in both runtime banks rather than the one zone a single
  key selects, so changing a key or a zone boundary can no longer hide a rough take.
- Derives the bar from the shipping population: `outlier_bar = 10 x median(1 - correlation)`.
  No absolute constant is compared against a recording.
- Loads both packaged-but-unshipped G#3 takes as controls — the forte take as the
  **positive** control that must be the unique outlier, the soft take as a
  **negative** control that must not be flagged.
- Asserts three things: exactly one outlier exists, it is `sax_bar_G#3_f.wav`, and
  it is not in a runtime bank.

## Notes

**Independent verification, 2026-07-30, claude-opus-5@high on trunk 53902d0**
(worktree `D:\worktrees\midi-music\20260730-TSK-HUM-verify-close-kiln180`).
I raised this bug but did not fix it — the fix is GPT-5's, so the two-eyes rule
holds (it binds the fixer, not the reporter).

**Original observation replicated exactly.** Forcing the new assertion to print its
census reproduces all 20 values in the Observation table digit-for-digit — every
shipping zone from bar_p 69.65 Hz = 0.99646 through bar_f 448.84 Hz = 0.99674, plus
`sax_bar_G#3_p.wav` = 0.99481 and `sax_bar_G#3_f.wav` = 0.77865. Same measurements,
so the fix is judged against the numbers that raised the bug.

**The complaint is resolved: the bar now sits in a real gap.** The derived bar is
0.03105 roughness (correlation 0.96895):

| | roughness | vs bar |
| --- | ---: | --- |
| worst *healthy* shipping zone (bar_f 130.22 Hz) | 0.00704 | 4.4x below |
| derived bar | 0.03105 | — |
| the real defect (`sax_bar_G#3_f.wav`) | 0.22135 | 7.1x above |

All five healthy zones this bug named as wrongly-flagged (bar_p 82.52 / 103.47 /
130.04, bar_f 82.38 / 130.22) now pass with margin. The old 0.996 bar sat *inside*
the healthy population; this one sits in the empty band between the population and
the outlier.

**Discrimination proven in both directions — the check the old bar failed.**

- Restoring the rough `sax_bar_G#3_f.wav` to `sax_bar_f()` **fails**: two outliers
  against an expected one (the bar itself barely moved, 0.03105 -> 0.03171, so a
  single contaminating entry cannot drag the population bar over its own outlier).
- Restoring the healthy `sax_bar_G#3_p.wav` to `sax_bar_p()` **passes**. The old bar
  would have failed this — 0.99481 is below 0.996. That is the false-positive this
  bug was raised about, and it is gone.

**Not vacuous under the mutations that would have holed it.** A metric stuck at 1.0
gives median 0, bar 0, zero outliers -> fails. A metric stuck at 0 gives bar 10,
zero outliers -> fails. Dropping the controls gives zero outliers -> fails. A bank
contaminated with many rough takes raises the median until nothing is an outlier ->
fails. Every path I could construct fails closed rather than passing silently.

**Feature gating checked, and correct.** Under `--no-default-features` the test is
compiled out (0 run, 745 filtered). That is not the MM-BUG-KILN-00020 pattern: this
oracle censuses embedded sample banks, which do not exist in a modeled-only build,
so it has nothing to assert there. MM-BUG-KILN-00020's vanished oracle was still
meaningful without samples; this one is not.

**Coverage of the parent bug is not lost.** MM-BUG-KILN-00178's property was "key 58
must not select a rough zone". "No shipping zone is rough" strictly implies it, so
the replacement is stronger, not narrower.

**Second residual from the Observation — the 8.3-semitone zone gap — is NOT addressed
by this fix, and that is correct.** It was recorded as an observation, not a defect;
nothing here claims to guard zone stretch, and no evidence has been gathered that it
is audible. Not carried forward as a new ID: raising a bug with no observed symptom
would be speculative. If a stretch artifact is ever heard, it should be raised on its
own evidence.

**Gates green on the exact tree:** `cargo test --workspace --release` 842 passed /
0 failed in `ferrosintesis` plus every sample crate green;
`cargo clippy --workspace --all-targets -- -D warnings` clean;
`cargo fmt --all -- --check` clean.

Verification mutations were temporary and are not committed; the tree was restored
to 53902d0 and confirmed clean before the gate run.
