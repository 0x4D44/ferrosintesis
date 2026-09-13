# MM-BUG-KILN-00265 — Orchestral2 family regeneration can publish a partial mixed bank after a late failure

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** orchestral2 sample generation / family publication atomicity
- **Raised:** 2026-08-17T04:26:14Z
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
- **State history:** Open (2026-08-17T04:26:14Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T16:53:31Z, deltic:auto role=fix run=fix-20260913T164231Z-1cdf7492 branch=task/bug-MM-BUG-KILN-00265-run-fix-20260913T164231Z-1cdf7492 code=dc135609700fbed7bb02c16e31b203655e3f0eaa gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: generic-family staging and rollback reversals redden the harp old-bank tests through main; three direct writers remain, split to MM-BUG-CRU-00070)

## Observation

The documented non-banjo path publishes a selected family one file at a time.
`tools/ferrosintesis-samples/prepare.py:5733-5779` reads, transforms, measures, and
immediately writes each selected output. `write_wav_mono` at lines 4247-4263 uses
a `.part` file plus `os.replace`, which makes one file replacement atomic but
provides no family-level staging, final exact-inventory transaction, or rollback.

A late source read, transform, pitch measurement, allocation, or write failure
therefore leaves an already-published prefix beside an untouched suffix. Under the
current WAV/FLAC mismatch that means a partial set of new, unconsumed WAVs beside
the old FLAC bank; correcting only the target format would expose a more dangerous
half-new active FLAC bank. Every surviving file can remain individually valid, so
per-file validation cannot detect the mixed generation.

Expected: any failed family regeneration leaves the prior family bank byte-for-byte
unchanged. Concrete fix: generate every selected family's final-format files in an
empty staging directory, validate its exact inventory and payload contracts, then
publish the family with rollback. Add negative controls for a late transform
failure and an injected replacement failure; both must preserve the old bank.
Static control-flow review only; no failure injection, generator, test, app,
decoder, render, or exploratory harness ran.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `dc135609`) by an agent other than the fixer.

`GenericFamilyWholeBankPublicationTest` drives `prepare.main()` with `--only=harp`; a failure on the 3rd transform and on the 2nd publish both leave the old harp bank and no transaction artifacts.

**Fails-before (method B).** The staging redirect fails the late-transform test (`harp_C4.wav` published into the live bank); the rollback reversal fails the publication test on the snapshot. Restored; both pass on HEAD.

**Residual split to MM-BUG-CRU-00070.** `_bake_honkytonk`, the bagpipe/chanter bake and `_bake_gong_bank` still write each output into the live crate and convert per file, so a late failure there can leave a mixed bank (found by reading the code).

## Notes

This is distinct from `MM-BUG-KILN-00262`: correcting the WAV/FLAC target alone
does not make multi-file publication atomic. Open `MM-BUG-KILN-00252` covers the
separate one-time `to_flac.py` migration tool, not these family bakes.
