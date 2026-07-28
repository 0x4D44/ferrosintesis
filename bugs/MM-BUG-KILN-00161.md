# MM-BUG-KILN-00161 — Kawai package provenance maps two zones to wrong upstream labels

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample package / provenance
- **Raised:** 2026-07-28
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T213933Z-p12724-n661330200-c1 branch=task/bug-MM-BUG-KILN-00161-run-fix-20260728T213933Z-p12724-n661330200-c1 code=b95a70f5e45d9729acab3756a4febc1eed2e4f4a gate=manual)

## Observation

Static reproduction: compare `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\PROVENANCE.md:38` with `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:723`. The packaged table says sounding A2 comes from source label A0 and sounding A3 comes from A1. The generator actually maps A2 to A1 and A#3 to A#2. The embedded filenames at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis-samples-vcsl-kawai\src\lib.rs:13` and measured roots at `D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\sampler.rs:1373` corroborate the generator. This misidentifies the upstream source for 12 of 48 published WAVs; runtime audio and CC0 licensing are unaffected. Expected: packaged provenance exactly describes the source mapping used to bake every zone. Actual: two hand-transcribed rows contradict the generator from their original commit. Concrete fix: correct the rows to A2 -> A1 and A#3 -> A#2, then add a source-derived oracle comparing the packaged mapping with `_KAWAI_ZONE_LABEL`, including an intentionally wrong-row negative control.

## Fix

<unfixed — raised only>

## Notes
