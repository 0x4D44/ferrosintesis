# MM-BUG-CRU-00071 — Drum-kit publish_staged swaps files one at a time with no rollback

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** drum-kit sample generation / failure atomicity
- **Raised:** 2026-09-13T19:26:12Z
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
- **State history:** Open (2026-09-13T19:26:12Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Residual found at independent verification of MM-BUG-KILN-00283 (2026-09-13, trunk 8b6a6f86), by reading the code. Fix 82e6b571 makes tools prepare_drumkit.py publish FLAC-only banks and reject stale WAVs, but publish_staged moves each staged take into place with os.replace one file at a time and has no rollback. A failure mid-swap leaves a partly published two-package kit (drumkit and drumkit2). No committed test checks that a successful publish writes .flac names either. Expected: whole-kit transactional publication with rollback, like _publish_staged_flac_bank.

## Fix

<unfixed — raised only>

## Notes
