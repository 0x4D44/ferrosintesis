# MM-BUG-KILN-00245 — Grand regeneration can publish a partial mixed bank after a late failure

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample generation / failure atomicity
- **Raised:** 2026-08-16T22:56:42Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T201456Z-6331e256
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00245-run-verify-20260913T201456Z-6331e256
- **Owner base:** 7c7de7ccb81fd0ff984c20019e07e50a6ceccfab
- **Owner fingerprint:** sha256:bb321a6807ba55f61526b85f843fb36d4a9a2e765c561998faccbb0eae1465e5
- **Owner since:** 2026-09-13T20:14:56Z
- **Owner until:** 2026-09-13T22:14:56Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T22:56:42Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T07:28:39Z, deltic:auto role=fix run=fix-20260913T071216Z-bc95a17e branch=task/bug-MM-BUG-KILN-00245-run-fix-20260913T071216Z-bc95a17e code=d7283e3d gate=manual)

## Observation

The documented grand bake processes 54 outputs in the generic loop and calls
`write_wav_mono` for each completed file at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\tools\ferrosintesis-samples\prepare.py:5733-5778`.
`write_wav_mono` makes one file atomic at `prepare.py:4247-4265`, but the bank has
no staging directory, rollback, or final exact-inventory publication step.

If a later source read, transform, pitch measurement, allocation, or write fails,
the already-written prefix remains beside the untouched suffix. Every file can be
individually valid, so the current name/count/magic checks do not establish that
the bank comes from one bake. Expected: a failed regeneration preserves the prior
54-file bank byte-for-byte. Actual: a late failure publishes a partial mixed
generation. Static control-flow review only; no generator or failure injection ran.

## Fix

<unfixed — raised only. Generate all 54 final-format outputs in an empty staging
directory, validate the exact inventory and payload contracts there, then publish
the complete bank with rollback. Add negative controls for a late transform failure
and an injected replacement failure; both must preserve the prior bank.>

## Notes

This is distinct from `MM-BUG-KILN-00244`: fixing the WAV/FLAC target alone still
permits a half-new bank after a late failure. Sibling failure-atomicity bugs cover
other generators, not this grand path.
