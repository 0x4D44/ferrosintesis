# MM-BUG-KILN-00268 — Sax sample package still documents WAV keys and payloads after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sax sample crate / public package contract
- **Raised:** 2026-08-17T06:31:16Z
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
- **State history:** Open (2026-08-17T06:31:16Z, raised via `deltic bugs new`)

## Observation

Static review found the published sax package still promises WAV lookup names and payloads after its FLAC migration. crates/ferrosintesis-samples-sax/src/lib.rs:314-317 says get() returns embedded WAV bytes and accepts exact .wav names, but every SAMPLES entry at :15-312 uses .flac; because lookup at :317-321 is exact, a caller following the Rustdoc receives None. README.md:8 and PROVENANCE.md:10-15,54,64 likewise describe WAVs, while PROVENANCE.md:68-69 attests the retired 4,101,968-byte aggregate and old inventory_matches_packaged_wavs test; the committed 74 FLACs total 2,470,849 bytes, matching src/lib.rs:333. Expected: the public API, README, and provenance describe the actual FLAC keys/container and current packaged inventory, or intentionally preserve documented WAV aliases. Concrete fix: choose the compatibility contract, update all package-local format/name/count claims together, and add a source-derived documentation/API guard proving every documented key resolves and the reported aggregate matches the packaged set. Static review only; no app, test, build, decoder, generator, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
