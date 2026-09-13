# MM-BUG-KILN-00270 — Strings sample package still documents WAV keys and payloads after FLAC conversion

- **State:** Closed
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
- **State history:** Open (2026-08-17T07:29:00Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:20:07Z, deltic:auto role=fix run=fix-20260913T171158Z-2f3c0d9d branch=task/bug-MM-BUG-KILN-00270-run-fix-20260913T171158Z-2f3c0d9d code=2c961483aa4cc8575b42b13ae079c8e4302b562b gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: strings docs state FLAC payloads and exact .flac keys; pre-fix docs fail the contract test in 3 subtests)

## Observation

Static review found that the published strings sample package still promises WAV lookup names and payloads after its FLAC migration. crates/ferrosintesis-samples-strings/src/lib.rs:18-20 and :184-190 say names use the .wav suffix and get returns WAV bytes, but every SAMPLES key at :23-180 uses .flac; lookup at :190-195 is exact, so a caller following the documented contract receives None. README.md:6 and :21 and PROVENANCE.md:3 and :17-18 repeat the retired container and filenames, while the committed package has 40 FLACs and no WAVs. Expected: the public API, README, and provenance describe the actual FLAC keys/container, or intentionally preserve documented WAV aliases. Concrete fix: choose the compatibility contract, update all package-local format and key claims together, and add a source-derived documentation/API guard proving every documented key resolves. Static review only; no app, test, build, decoder, generator, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `2c961483`) by an agent other than the fixer.

**Original observation re-derived.** At raise time `lib.rs`, README and PROVENANCE said WAV; `904cbe94` and `db16a45b` removed most of it and `2c961483` added explicit FLAC-payload and `.flac`-key statements. HEAD's packaged docs have no WAV claims; 40 FLACs on disk; every embedded key resolves and `.wav` returns None.

**Fails-before (method A).** With README, PROVENANCE and `lib.rs` from `2c961483^`, `StringsPackagedDocumentContractTest` fails in 3 subtests. It passes on HEAD, as does `every_packaged_key_resolves_as_an_exact_flac_name`.

## Notes
