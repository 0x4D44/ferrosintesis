# MM-BUG-KILN-00268 — Sax sample package still documents WAV keys and payloads after FLAC conversion

- **State:** Fixed
- **Priority:** Should
- **Severity:** Low
- **Area:** sax sample crate / public package contract
- **Raised:** 2026-08-17T06:31:16Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T200702Z-48529a1c
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00268-run-verify-20260913T200702Z-48529a1c
- **Owner base:** e8e4ccafbe921b7959b7e26eec094a7e6a3e873b
- **Owner fingerprint:** sha256:bc040e02c985ed9ddb2232bd8cf57f1fa5c5e611bbc08c704ceabb9c4ce247a2
- **Owner since:** 2026-09-13T20:07:02Z
- **Owner until:** 2026-09-13T22:07:02Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-17T06:31:16Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T17:14:26Z, deltic:auto role=fix run=fix-20260913T165737Z-8cc00e5a branch=task/bug-MM-BUG-KILN-00268-run-fix-20260913T165737Z-8cc00e5a code=024a4be09358530268ad9293dc9e871bd0a87a65 gate=manual)

## Observation

Static review found the published sax package still promises WAV lookup names and payloads after its FLAC migration. crates/ferrosintesis-samples-sax/src/lib.rs:314-317 says get() returns embedded WAV bytes and accepts exact .wav names, but every SAMPLES entry at :15-312 uses .flac; because lookup at :317-321 is exact, a caller following the Rustdoc receives None. README.md:8 and PROVENANCE.md:10-15,54,64 likewise describe WAVs, while PROVENANCE.md:68-69 attests the retired 4,101,968-byte aggregate and old inventory_matches_packaged_wavs test; the committed 74 FLACs total 2,470,849 bytes, matching src/lib.rs:333. Expected: the public API, README, and provenance describe the actual FLAC keys/container and current packaged inventory, or intentionally preserve documented WAV aliases. Concrete fix: choose the compatibility contract, update all package-local format/name/count claims together, and add a source-derived documentation/API guard proving every documented key resolves and the reported aggregate matches the packaged set. Static review only; no app, test, build, decoder, generator, render, package command, or exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

## Notes
