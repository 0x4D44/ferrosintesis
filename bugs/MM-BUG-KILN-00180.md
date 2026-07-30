# MM-BUG-KILN-00180 — The MM-BUG-KILN-00178 roughness bar (0.996) is fitted to the removed zone, not derived: six shipping baritone zones sit below it

- **State:** Open
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
- **State history:** Open (2026-07-30, raised via `deltic bugs new` model=claude-opus-5@high)

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

<unfixed — raised only>

## Notes
