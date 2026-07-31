# MM-BUG-CRUCIBLE-00002 — Published YDP provenance calls tritone-spaced roots minor thirds

- **State:** Closed
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
- **State history:** Open (2026-07-31, raised via `deltic bugs new`) -> Fixed (2026-07-31T07:33:20Z, deltic:auto role=fix run=fix-20260731T072613Z-p65064-n373806300-c1 branch=task/bug-MM-BUG-CRUCIBLE-00002-run-fix-20260731T072613Z-p65064-n373806300-c1 code=52be8b538f5678d5730d0edf746a32f4e0fd9d97 gate=manual) -> Closed (2026-07-31, claude-opus-5; independent two-eyes verification on trunk `ddd71e6`. The fixer was `deltic:auto role=fix` with GPT-5.6 as the authoring model on `52be8b5`; I did not fix it. ORIGINAL OBSERVATION re-checked: the packaged line the report cited now reads "9 pitch zones (C2-C6, C/F-sharp roots every six semitones)", and the generator comment plus the `_bake_ydp_grand` docstring match. The roots themselves are unchanged (36/42/48/54/60/66/72/78/84) and remain correct at runtime, as the report said. The report's "keep the separate, accurate statement" instruction was honoured: `PROVENANCE.md` still records that each selected root is "present in layer 3's minor-third sampling", so the distinction between our tritone-spaced SELECTION and the denser SOURCE survives. TWO-SIDED: reverse-applying only `PROVENANCE.md` + `prepare.py` makes `YdpZoneProvenanceTest.test_packaged_provenance_matches_the_selected_root_intervals` FAIL on the missing spacing phrase; restoring makes it pass. The oracle derives the interval set from `prepare.YDP_ZONE_MIDI` itself rather than from a second hand-written list, and carries the requested negative fixture `test_stale_minor_third_claim_is_rejected`. Repo gate green on the exact tree (fmt, both clippy configurations, both test suites, and the Python sample-tool suite). NOT a residual of this fix, but recorded here so it stays discoverable: one instance of the same wording class survives at `tools/ferrosintesis-samples/prepare.py:773`, where the `_HEADROOM_ZONE_MIDI` grid — the same 36..84 tritone spacing — is still commented "C/F# every minor third". That is the pre-existing report-only instance the 2026.07.26 review logged and that this bug's own Notes explicitly carved out; it is an internal generator comment, not published provenance, so it is outside this bug's recorded scope and is left for a separate decision.)

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

Landed in `52be8b5`: the packaged `PROVENANCE.md` line and the two `prepare.py`
comments now describe the selected roots as C/F-sharp every six semitones, while
the separate, accurate statement about the source layer's minor-third sampling is
retained. `YdpZoneProvenanceTest` derives the interval set from
`prepare.YDP_ZONE_MIDI` and carries a negative fixture for the stale phrase.

## Notes

A 2026-07-26 review reported the same wording class in a different bank's
generator comment, but no bug or requirement tracks this published YDP
provenance defect.

Static code review only. No application or test harness was run.
