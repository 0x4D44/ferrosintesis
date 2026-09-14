# MM-BUG-CRU-00067 — gen_crate_lib.py silently deletes the drum-kit crate's hand-written bank API

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / crate lib generator
- **Raised:** 2026-09-13T19:23:49Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260914T213431Z-3eb22655
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00067-run-verify-20260914T213431Z-3eb22655
- **Owner base:** 7feb1d38d066638dc487d3f6c6c0b637e71bff6f
- **Owner fingerprint:** sha256:b2553ae54229c9b7235ea60cfd1421342e0adaf356c62407fc806a4e2503fd97
- **Owner since:** 2026-09-14T21:34:31Z
- **Owner until:** 2026-09-14T23:34:31Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:23:49Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T21:31:50Z, deltic:auto role=fix run=fix-20260913T212218Z-6db24862 branch=task/bug-MM-BUG-CRU-00067-run-fix-20260913T212218Z-6db24862 code=d5e8573225b757402d273ff610b6ad7c2b09bbc7 gate=manual)

## Observation

Residual split at independent verification of MM-BUG-KILN-00224 (2026-09-13, trunk 8b6a6f86). The record asked that the generic generator reject custom crates. Fix fcc9d108 refuses only the core crate, keyed on the single core-only token PIANO_SINGLE_TAKE_CELLS. Running tools/ferrosintesis-samples/gen_crate_lib.py on a TEMP copy of crates/ferrosintesis-samples-drumkit exits 0 and rewrites lib.rs without its hand-written BANKS, pcm, prewarm and related API (4 matching items became 0). The drumkit docs name neither tool, so nothing warns a regenerator. Expected: the generator refuses any crate whose lib.rs carries API it does not generate, derived rather than keyed on one token.

## Fix

<unfixed — raised only>

## Notes
