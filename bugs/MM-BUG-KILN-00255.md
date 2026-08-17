# MM-BUG-KILN-00255 — MuseScore-grand regeneration can publish a partial mixed bank after a late failure

- **State:** Open
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
- **State history:** Open (2026-08-17T02:30:15Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

`_bake_musescore_grand` publishes each of the 25 zones directly into the tracked package as soon as that zone finishes at tools/ferrosintesis-samples/prepare.py:4647-4666. `write_wav_mono` at :4247-4263 uses a `.part` plus `os.replace`, which makes one file atomic but provides no bank-level staging, rollback, or final exact-inventory transaction. A late Ogg decode, sample read, resample, pitch measurement, allocation, or write failure therefore leaves an already-replaced prefix beside the untouched suffix. Every surviving file can remain individually valid while the bank combines two bakes. Expected: any failed regeneration leaves the prior 25-zone bank byte-identical. Actual: publication is interleaved with generation, so late failure exposes a partial mixed generation. Concrete fix: produce every final-format zone in an empty staging directory, validate exact inventory and payload contracts there, then publish the whole bank with rollback. Add negative controls for a late transform failure and an injected replacement failure; both must preserve the old bank. This is distinct from MM-BUG-KILN-00254: correcting the WAV/FLAC target alone still permits a half-new bank. MM-BUG-KILN-00245 covers the separate 54-zone grand crate. Static control-flow review only; no failure injection or generator ran. Estimated effort: Medium.

## Fix

<unfixed — raised only>

## Notes
