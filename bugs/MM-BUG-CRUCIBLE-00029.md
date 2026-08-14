# MM-BUG-CRUCIBLE-00029 — Legal MIDI delta sequences wrap cumulative tick time and evade duration limits

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** ferrosintesis / MIDI timing
- **Raised:** 2026-08-14T11:47:23Z
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
- **State history:** Open (2026-08-14T11:47:23Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

## Observation

Each individual MIDI delta can be a legal four-byte VLQ, but absolute track time is held in
`u32` and deliberately wrapped at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\midi.rs:259`
and `midi.rs:271`.

With division 65,535 and a valid 1,000,000-microsecond tempo, 22 successive maximum legal
deltas (`FF FF FF 7F`) place the final event at about 90,113 seconds, just over the public
24-hour limit. The `u32` sum wraps to about 24,576 seconds. The event is sorted back into
the earlier timeline and the duration check at `midi.rs:433-439` sees only the wrapped
6.8-hour value, so the hostile file evades the limit and renders events in the wrong order.

Expected: cumulative time is monotonic and the 24-hour guard evaluates the true tick.
Actual: legal deltas can wrap, reorder events, and bypass the resource guard.

## Fix

Carry absolute ticks as `u64` through raw events, tempo records, markers, sorting, and
tick-to-seconds conversion, or reject cumulative overflow with `checked_add`. Enforce the
duration limit against the unwrapped value. Add a 22-maximum-delta fixture that is rejected
as too long and a near-boundary fixture that remains monotonic. Estimated effort: Medium.

## Notes
