# MM-BUG-KILN-00161 — Kawai package provenance maps two zones to wrong upstream labels

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample package / provenance
- **Raised:** 2026-07-28
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260728T213933Z-p12724-n661330200-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00161-run-fix-20260728T213933Z-p12724-n661330200-c1
- **Owner base:** 9cbbbba96abc3a177e1eefb43ca123bf1bb1f74a
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T21:39:33Z
- **Owner until:** 2026-07-28T23:39:33Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

Static reproduction: compare `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\PROVENANCE.md:38` with `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:723`. The packaged table says sounding A2 comes from source label A0 and sounding A3 comes from A1. The generator actually maps A2 to A1 and A#3 to A#2. The embedded filenames at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:13` and measured roots at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\sampler.rs:1373` corroborate the generator. This misidentifies the upstream source for 12 of 48 published WAVs; runtime audio and CC0 licensing are unaffected. Expected: packaged provenance exactly describes the source mapping used to bake every zone. Actual: two hand-transcribed rows contradict the generator from their original commit. Concrete fix: correct the rows to A2 -> A1 and A#3 -> A#2, then add a source-derived oracle comparing the packaged mapping with `_KAWAI_ZONE_LABEL`, including an intentionally wrong-row negative control.

## Fix

<unfixed — raised only>

## Notes
