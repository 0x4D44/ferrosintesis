# MM-BUG-CRU-00056 — RealtimeSynth NoteOn-burst regression never exceeds the pending-command budget, so it passes with an unbounded queue

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / realtime MIDI queue tests
- **Raised:** 2026-09-13T19:19:58Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260913T193612Z-67a263c9
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00056-run-fix-20260913T193612Z-67a263c9
- **Owner base:** c890ee3d4bb08fe6bd014496bcc8794ca9fb6584
- **Owner fingerprint:** -
- **Owner since:** 2026-09-13T19:36:12Z
- **Owner until:** 2026-09-13T21:36:12Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:19:58Z, raised via `deltic bugs new` model=claude-opus-5)

## Observation

Split from MM-BUG-CRUCIBLE-00025 at independent verification (2026-09-13, trunk 8b6a6f86). The fix (9d10dcdd) bounded the live pending queue at 1024 commands. Its test noteon_burst_is_bounded_and_capped (crates/ferrosintesis/src/live.rs) claims to send far more note-ons than either budget, but its loop sends 9 channels x 88 keys = 792 note-ons, under LIVE_MAX_PENDING=1024. With PendingQueue reverted to an unbounded Vec, five sibling tests go red but this one stays green, so it cannot detect the defect it is named for. Expected: the burst exceeds the pending budget and fails without the bound. Also, nothing covers the quadratic-to-linear enforce_voice_cap change: the differential test passes against both implementations by design.

## Fix

<unfixed — raised only>

## Notes
