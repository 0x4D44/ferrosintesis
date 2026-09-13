# MM-BUG-KILN-00245 — Grand regeneration can publish a partial mixed bank after a late failure

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** grand sample generation / failure atomicity
- **Raised:** 2026-08-16T22:56:42Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-16T22:56:42Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T07:28:39Z, deltic:auto role=fix run=fix-20260913T071216Z-bc95a17e branch=task/bug-MM-BUG-KILN-00245-run-fix-20260913T071216Z-bc95a17e code=d7283e3d gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: staging and rollback reversals each redden the grand old-bank snapshot tests)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `d7283e3d`) by an agent other than the fixer.

`GrandWholeBankPublicationTest` injects failures on the 3rd transform and a late replacement into `_bake_grand`; on HEAD the old bank is preserved with no artifacts.

**Fails-before (method B).** The staging redirect fails the late-transform test (`grand_C4_f.wav` published into the live bank); the rollback reversal fails the publication test on the snapshot. Restored; both pass on HEAD. Grand is out of the generic per-file loop and published as one transaction.

## Notes

This is distinct from `MM-BUG-KILN-00244`: fixing the WAV/FLAC target alone still
permits a half-new bank after a late failure. Sibling failure-atomicity bugs cover
other generators, not this grand path.
