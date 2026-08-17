# MM-BUG-KILN-00265 — Orchestral2 family regeneration can publish a partial mixed bank after a late failure

- **State:** Open
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
- **State history:** Open (2026-08-17T04:26:14Z, raised via `deltic bugs new`)

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

## Notes

This is distinct from `MM-BUG-KILN-00262`: correcting the WAV/FLAC target alone
does not make multi-file publication atomic. Open `MM-BUG-KILN-00252` covers the
separate one-time `to_flac.py` migration tool, not these family bakes.
