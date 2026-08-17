# MM-BUG-KILN-00270 — Strings sample package still documents WAV keys and payloads after FLAC conversion

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** strings sample crate / public package contract
- **Raised:** 2026-08-17T07:29:00Z
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
- **State history:** Open (2026-08-17T07:29:00Z, raised via `deltic bugs new`)

## Observation

Static review found that the published strings sample package still promises WAV lookup names and payloads after its FLAC migration. crates/ferrosintesis-samples-strings/src/lib.rs:18-20 and :184-190 say names use the .wav suffix and get returns WAV bytes, but every SAMPLES key at :23-180 uses .flac; lookup at :190-195 is exact, so a caller following the documented contract receives None. README.md:6 and :21 and PROVENANCE.md:3 and :17-18 repeat the retired container and filenames, while the committed package has 40 FLACs and no WAVs. Expected: the public API, README, and provenance describe the actual FLAC keys/container, or intentionally preserve documented WAV aliases. Concrete fix: choose the compatibility contract, update all package-local format and key claims together, and add a source-derived documentation/API guard proving every documented key resolves. Static review only; no app, test, build, decoder, generator, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
