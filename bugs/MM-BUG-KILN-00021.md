# MM-BUG-KILN-00021 — Poly-aftertouch (0xA0) is dropped by the live MIDI parser though the engine handles it

- **State:** Open
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

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

## Notes

- Rare in practice, but a real capability the offline path has and the live path
  throws away before the shared engine sees it.
