# MM-BUG-KILN-00013 — Live/realtime path has no global polyphony cap: a dense stream can blow the audio-callback deadline

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
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

`EngineCore` keeps `active: Vec::new()` unbounded (`crates/ferrosintesis/src/
engine.rs:~1149`); the only voice steal is per-channel
`DRIVEN_GUITAR_VOICE_LIMIT = 8` (`engine.rs:~205`,
`make_room_for_driven_guitar`). There is no global `MAX_VOICES` / oldest-quietest
steal in either path. Harmless offline (no deadline), but a live stream that
stacks hundreds of un-released voices can push `render_block_add` past the
audio-callback budget and cause xruns/dropouts. A realtime synth normally caps
total polyphony and steals the oldest/quietest.

## Fix

Add a global polyphony cap with oldest/quietest voice stealing, active only in
the live path (`live.rs`); offline keeps unbounded polyphony since it has no
deadline.

## Notes

- Scope to the realtime surface so offline determinism/goldens are untouched.
- `live` is documented as the secondary surface — this is robustness, not a
  render-quality defect.
