# MM-BUG-CRUCIBLE-00002 — Published YDP provenance calls tritone-spaced roots minor thirds

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** YDP sample crate / provenance
- **Raised:** 2026-07-31
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new`) -> Fixed (2026-07-31T07:33:20Z, deltic:auto role=fix run=fix-20260731T072613Z-p65064-n373806300-c1 branch=task/bug-MM-BUG-CRUCIBLE-00002-run-fix-20260731T072613Z-p65064-n373806300-c1 code=52be8b538f5678d5730d0edf746a32f4e0fd9d97 gate=manual)

## Observation

**Symptom.** The packaged provenance says the nine C/F-sharp roots use
"C/F# minor thirds" at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\crates\ferrosintesis-samples-ydp-grand\PROVENANCE.md:10`.

The same document lists MIDI roots `36/42/48/54/60/66/72/78/84` at line 38, and
the generator defines that exact sequence at
`D:\worktrees\ferrosintesis\20260731-REV-CLA@CRUCIBLE-code-review-005314\tools\ferrosintesis-samples\prepare.py:881`.
Each adjacent pair differs by six semitones, a tritone. A minor third is three
semitones.

**Expected.** Published provenance distinguishes the selected tritone-spaced
bank from the denser minor-third sampling in the upstream SoundFont.

**Actual.** The package overstates its selected zone density by a factor of two.
Runtime roots remain correct, but maintainers can make a rebake or interpolation
decision from false provenance.

**Concrete fix.** Describe the selected roots as "C/F-sharp roots every six
semitones" or "tritone-spaced" in `PROVENANCE.md` and the generator comments.
Keep the separate, accurate statement that each selected root exists in the
source layer's minor-third sampling. Add a source-derived interval assertion
and a negative documentation fixture for the stale phrase.

**Effort:** Extra small.

## Fix

<unfixed — raised only>

## Notes

A 2026-07-26 review reported the same wording class in a different bank's
generator comment, but no bug or requirement tracks this published YDP
provenance defect.

Static code review only. No application or test harness was run.
