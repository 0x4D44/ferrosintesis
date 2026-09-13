# MM-BUG-KILN-00255 — MuseScore-grand regeneration can publish a partial mixed bank after a late failure

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** MuseScore grand sample generation / failure atomicity
- **Raised:** 2026-08-17T02:30:15Z
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
- **State history:** Open (2026-08-17T02:30:15Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T08:24:14Z, deltic:auto role=fix run=fix-20260913T081457Z-35db8830 branch=task/bug-MM-BUG-KILN-00255-run-fix-20260913T081457Z-35db8830 code=6cd7e62e3db5b6dc83396510dcb665371068b58f gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: staging and rollback reversals each redden the MuseScore-grand old-bank tests)

## Observation

`_bake_musescore_grand` publishes each of the 25 zones directly into the tracked package as soon as that zone finishes at tools/ferrosintesis-samples/prepare.py:4647-4666. `write_wav_mono` at :4247-4263 uses a `.part` plus `os.replace`, which makes one file atomic but provides no bank-level staging, rollback, or final exact-inventory transaction. A late Ogg decode, sample read, resample, pitch measurement, allocation, or write failure therefore leaves an already-replaced prefix beside the untouched suffix. Every surviving file can remain individually valid while the bank combines two bakes. Expected: any failed regeneration leaves the prior 25-zone bank byte-identical. Actual: publication is interleaved with generation, so late failure exposes a partial mixed generation. Concrete fix: produce every final-format zone in an empty staging directory, validate exact inventory and payload contracts there, then publish the whole bank with rollback. Add negative controls for a late transform failure and an injected replacement failure; both must preserve the old bank. This is distinct from MM-BUG-KILN-00254: correcting the WAV/FLAC target alone still permits a half-new bank. MM-BUG-KILN-00245 covers the separate 54-zone grand crate. Static control-flow review only; no failure injection or generator ran. Estimated effort: Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `6cd7e62e`) by an agent other than the fixer.

`MuseScoreGrandWholeBankPublicationTest` runs a fake SF3 through `_bake_musescore_grand`; a failure on the 3rd `measure_f0` and a late replacement failure both leave the exact old bank on HEAD.

**Fails-before (method B).** The staging redirect fails the late-transform test (`musescoregrand_E2.wav` published into the live bank); the rollback reversal fails the replacement test on the snapshot. Restored; both pass on HEAD. The concurrent-intermediate race in the same function remains open as MM-BUG-KILN-00256.

## Notes
