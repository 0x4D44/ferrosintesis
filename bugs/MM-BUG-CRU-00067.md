# MM-BUG-CRU-00067 — gen_crate_lib.py silently deletes the drum-kit crate's hand-written bank API

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / crate lib generator
- **Raised:** 2026-09-13T19:23:49Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T212218Z-6db24862
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00067-run-fix-20260913T212218Z-6db24862
- **Owner base:** 653eaa78a8a4aa21a62be7d7af443f03e73ab1db
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T21:22:18Z
- **Owner until:** 2026-09-13T23:22:18Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:49Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual split at independent verification of MM-BUG-KILN-00224 (2026-09-13, trunk 8b6a6f86). The record asked that the generic generator reject custom crates. Fix fcc9d108 refuses only the core crate, keyed on the single core-only token PIANO_SINGLE_TAKE_CELLS. Running tools/ferrosintesis-samples/gen_crate_lib.py on a TEMP copy of crates/ferrosintesis-samples-drumkit exits 0 and rewrites lib.rs without its hand-written BANKS, pcm, prewarm and related API (4 matching items became 0). The drumkit docs name neither tool, so nothing warns a regenerator. Expected: the generator refuses any crate whose lib.rs carries API it does not generate, derived rather than keyed on one token.

## Fix

<unfixed — raised only>

## Notes
