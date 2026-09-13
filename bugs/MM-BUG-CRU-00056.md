# MM-BUG-CRU-00056 — RealtimeSynth NoteOn-burst regression never exceeds the pending-command budget, so it passes with an unbounded queue

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** ferrosintesis / realtime MIDI queue tests
- **Raised:** 2026-09-13T19:19:58Z
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
- **State history:** Open (2026-09-13T19:19:58Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T19:47:03Z, deltic:auto role=fix run=fix-20260913T193612Z-67a263c9 branch=task/bug-MM-BUG-CRU-00056-run-fix-20260913T193612Z-67a263c9 code=e4df90580b0d8ec8d71157d162cd20ff26fd064f gate=manual) -> Closed (2026-09-13T20:23:48Z, independent verify by Codex run=verify-20260913T201920Z-c84219cd: burst now exceeds the queue budget and the realtime tests pass)

## Observation

Split from MM-BUG-CRUCIBLE-00025 at independent verification (2026-09-13, trunk 8b6a6f86). The fix (9d10dcdd) bounded the live pending queue at 1024 commands. Its test noteon_burst_is_bounded_and_capped (crates/ferrosintesis/src/live.rs) claims to send far more note-ons than either budget, but its loop sends 9 channels x 88 keys = 792 note-ons, under LIVE_MAX_PENDING=1024. With PendingQueue reverted to an unbounded Vec, five sibling tests go red but this one stays green, so it cannot detect the defect it is named for. Expected: the burst exceeds the pending budget and fails without the bound. Also, nothing covers the quadratic-to-linear enforce_voice_cap change: the differential test passes against both implementations by design.

## Fix

`e4df90580b0d8ec8d71157d162cd20ff26fd064f` (`Make the realtime burst oracle exceed its pending budget`) changes
`noteon_burst_is_bounded_and_capped` to feed `LIVE_MAX_PENDING * 2` commands, wrapping
valid channel/key slots only after exhausting the available piano-key pairs. The commit also
adds a source-shape guard that requires `enforce_voice_cap` to use one linear retain pass.

### Verification (closure) (2026-09-13, Codex, independent)

Compared the claimed fix with the separate open `MM-BUG-KIL-00309` record; they share
`live.rs` but describe different defects. Verified `e4df90580b0d8ec8d71157d162cd20ff26fd064f`
with `cargo test -p ferrosintesis --lib live::tests::`: 27 passed, including the named
burst regression. The related `engine::tests::enforce_voice_cap_uses_a_single_linear_retain_pass`
also passed, and `cargo fmt --all -- --check` passed.

For a negative control, I temporarily replaced the fixed array queue with an unbounded
`Vec`. The named burst test failed at the budget assertion, proving the expanded fixture
detects the original false-green. I restored the fixed queue, reran all 27 realtime tests,
and confirmed a clean source diff.

## Notes
