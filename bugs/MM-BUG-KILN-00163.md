# MM-BUG-KILN-00163 — Kawai rebakes can retain stale WAVs behind an unrelated family validation

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** Kawai sample generation / output inventory
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
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-28, deltic:auto role=fix run=fix-20260728T223542Z-p16556-n556412300-c1 branch=task/bug-MM-BUG-KILN-00163-run-fix-20260728T223542Z-p16556-n556412300-c1 code=4c68345 gate=manual)

## Observation

Static reproduction: D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\prepare.py:727 defines KAWAI_SOURCES, but main validates only the headroom family at :5324 before the generic writer includes KAWAI_SOURCES at :5526 and writes selected files at :5571. Removing or renaming a Kawai source entry therefore leaves its old packaged WAV untouched; D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\tools\ferrosintesis-samples\gen_crate_lib.py:30 scans the remaining directory and re-embeds that obsolete file. The class oracle at D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-201002\crates\ferrosintesis\src\inventory.rs:171 models validation as one unscoped boolean, so Headroom's conditional, family-specific check marks main validated for every later family. Current Kawai inventory is internally consistent; the confirmed failure is that retiring a source or zone can appear successful while the obsolete timbre is republished. Expected: every selected generated family rejects on-disk WAVs outside its current expected set before writing. Actual: Kawai performs no family-scoped validation. Concrete fix: validate (kawai, KAWAI_SOURCES) before any selected Kawai write, strengthen the source-derived oracle to associate each validation with its family and expected set, and add a removed-Kawai-entry/stale-file negative control. This is a residual of closed MM-BUG-KILN-00145 and MM-BUG-KILN-00156, not their original name-enumeration defect.

## Fix

<unfixed — raised only>

## Notes
