# MM-BUG-CRUCIBLE-00022 — Bass rebakes retain obsolete packaged WAVs

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** electric-bass sample generation / output inventory
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T071307Z-p76832-n922353200-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00022-run-fix-20260801T071307Z-p76832-n922353200-c1
- **Owner base:** 9eaa6195e79ae0de1f3e0d6c4273ff04a4f87346
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T07:13:07Z
- **Owner until:** 2026-08-01T09:13:07Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`)

## Observation

`main()` validates generated output inventory only for Steinway, Kawai, and Headroom at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:5369`.
The generic writer enumerates only current `FINGERBASS_SOURCES` and `PICKBASS_SOURCES`
keys at lines 5575–5621. Removing or renaming a bass mapping therefore writes the current
set but neither rejects nor removes the old family-owned WAV.

`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\gen_crate_lib.py:84`
then scans and embeds every `.wav` still present, so an obsolete take is republished.
The derived guard at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\crates\ferrosintesis\src\inventory.rs:219`
tracks only whether any validator appears before a function's first transitive write.
Unrelated conditional validations make `main()` look guarded; the scoped assertions at
lines 1024–1034 cover only Kawai and Steinway.

Expected: a selected bass rebake rejects obsolete finger/pick outputs before any fetch or
write. Actual: a retired source entry can remain packaged and the source-derived oracle
stays green.

This is a family/path-sensitivity residual of closed `MM-BUG-KILN-00145` and
`MM-BUG-KILN-00156`, not their original helper-enumeration defect. No Open bug covers bass.

## Fix

Validate the combined finger/pick expected set for the shared bass crate before any
selected bass side effect. Strengthen the oracle to associate each selected output family
and expected table with its own validation path. Add a negative control where an unrelated
family's conditional validator appears before the bass write, and a bass regression that
removes one mapping while leaving its old WAV on disk.

## Notes

The current committed inventory is internally consistent; the defect is the unguarded
retirement path. Static review only. No generator, application, test, build, render, or
exploratory harness ran. Estimated effort: Small–Medium.
