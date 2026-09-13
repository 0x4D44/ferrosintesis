# MM-BUG-KILN-00282 — Drumkit public API still documents WAV keys and bytes after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** core drum-kit sample crate / public package contract
- **Raised:** 2026-08-17T11:39:51Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T183617Z-401f80e3
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00282-run-fix-20260913T183617Z-401f80e3
- **Owner base:** cca859fbfb85165b6aed05ecdf55699ebf445ca3
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T18:36:17Z
- **Owner until:** 2026-09-13T20:36:17Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T11:39:51Z, raised via `deltic bugs new`)

## Observation

Static review found that the independently published core drum-kit package still
promises WAV lookup names and WAV payloads after its inventory moved to FLAC.
`crates/ferrosintesis-samples-drumkit/src/lib.rs:561-578`, `:726-730`, and
`:740-743` describe `BankSource::wav`, `Bank::wav`, and `get` in WAV terms and
say exact names carry a `.wav` suffix. `README.md:3-6` repeats that contract.
Every `SAMPLES` key at `src/lib.rs:34-547` and every name constructed by
`Bank::file_name` at `:702-709` is now `.flac`.

A standalone caller following the published contract, for example
`get("kick_vl1_rr1.wav")`, therefore receives `None`. A caller using
`Bank::wav()` receives bytes beginning with `fLaC`, not a RIFF/WAVE stream.
`PROVENANCE.md:18-22,74-75,100-107` also inventories the retired WAV outputs and
their 9,632,990-byte aggregate, while the current Rust pin is 5,428,756 bytes at
`src/lib.rs:963`.

Expected: public Rustdoc, README, provenance, lookup keys, and returned encoded
container agree. Actual: in-repo PCM playback works through `Bank::pcm`, but the
published raw-asset contract names nonexistent keys and the wrong byte format.
This was confirmed from the exact static name table and lookup implementation;
no app, build, test, decoder, package, or exploratory harness ran.

## Fix

<unfixed — raised only. Choose the supported compatibility contract, update all
package-local surfaces together, and add a source-derived check proving a
documented real key resolves and the documented container matches its magic.
Aliases must not return FLAC under a name that still promises WAV bytes. Estimated
effort: Small.>

## Notes
