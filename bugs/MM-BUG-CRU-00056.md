# MM-BUG-CRU-00056 — RealtimeSynth NoteOn-burst regression never exceeds the pending-command budget, so it passes with an unbounded queue

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / realtime MIDI queue tests
- **Raised:** 2026-09-13T19:19:58Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T201920Z-c84219cd
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRU-00056-run-verify-20260913T201920Z-c84219cd
- **Owner base:** 769107652f35e46cef37233b8254cbd84368fb63
- **Owner fingerprint:** sha256:04a5e5d602f608148fa17cfaf0c2d09df72d3dc1c91eb6fd53ac8cfc847fa33f
- **Owner since:** 2026-09-13T20:19:20Z
- **Owner until:** 2026-09-13T22:19:20Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-09-13T19:19:58Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T19:47:03Z, deltic:auto role=fix run=fix-20260913T193612Z-67a263c9 branch=task/bug-MM-BUG-CRU-00056-run-fix-20260913T193612Z-67a263c9 code=e4df90580b0d8ec8d71157d162cd20ff26fd064f gate=manual)

## Observation

Split from MM-BUG-CRUCIBLE-00025 at independent verification (2026-09-13, trunk 8b6a6f86). The fix (9d10dcdd) bounded the live pending queue at 1024 commands. Its test noteon_burst_is_bounded_and_capped (crates/ferrosintesis/src/live.rs) claims to send far more note-ons than either budget, but its loop sends 9 channels x 88 keys = 792 note-ons, under LIVE_MAX_PENDING=1024. With PendingQueue reverted to an unbounded Vec, five sibling tests go red but this one stays green, so it cannot detect the defect it is named for. Expected: the burst exceeds the pending budget and fails without the bound. Also, nothing covers the quadratic-to-linear enforce_voice_cap change: the differential test passes against both implementations by design.

## Fix

<unfixed — raised only>

## Notes
