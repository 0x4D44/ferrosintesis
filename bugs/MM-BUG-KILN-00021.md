# MM-BUG-KILN-00021 — Poly-aftertouch (0xA0) is dropped by the live MIDI parser though the engine handles it

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** live
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, Claude Opus 4.8 (1M) — `live.rs:channel_event` forwards 0xA0) → Closed (2026-07-18, independently verified by OpenAI Codex on `55c829e`)

## Observation

`channel_event` returns `None` for status 0xA0 (`crates/ferrosintesis/src/
live.rs:~485`), so poly-aftertouch is silently dropped in the realtime path. The
offline parser handles it (`midi.rs:~222`) and the engine acts on it
(`engine.rs:~1357`, per-note pressure → vibrato/growl on aftertouch-family
programs). Channel aftertouch (0xD0) works in both paths; only per-key pressure is
lost live.

## Fix

Map 0xA0 in the live parser to `EvKind::PolyAftertouch` (the engine already
consumes it) — a two-line change closing an offline/live feature gap.

### Independent closure verification (2026-07-18, OpenAI Codex)

- Re-ran the original byte-stream observation on trunk build `55c829e` through
  `live::tests::parser_emits_poly_aftertouch_and_consumes_system_common`; 0xA0 now
  produces the expected per-key `EvKind::PolyAftertouch` command.
- Re-ran `engine::tests::poly_aftertouch_targets_only_the_pressed_note`; the shared
  engine still applies that event only to the pressed note.
- Confirmed the regression's red side at pre-fix `d2b2462`: `channel_event` mapped
  0xA0 to `None`, and the old parser test explicitly expected it to be ignored. The
  corrected parser expectation cannot pass on that path and passes after the fix.
- The independent workspace gate on the same build passed: `cargo test --workspace`,
  `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo fmt --all -- --check`.
  The offline/live gap is closed and no residual was found.

## Notes

- Rare in practice, but a real capability the offline path has and the live path
  throws away before the shared engine sees it.
