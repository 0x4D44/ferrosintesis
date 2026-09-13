# MM-BUG-CRUCIBLE-00029 — Legal MIDI delta sequences wrap cumulative tick time and evade duration limits

- **State:** Closed
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
- **State history:** Open (2026-08-14T11:47:23Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T10:27:17Z, deltic:auto role=fix run=fix-20260815T101815Z-p35368-n819711200-c1 branch=task/bug-MM-BUG-CRUCIBLE-00029-run-fix-20260815T101815Z-p35368-n819711200-c1 code=eb74fa4 gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: legal long-delta file rejected as TooLong with its true duration; both tests fail with a wrapping u32 accumulator)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `eb74fa42`) by an agent other than the fixer.

**Original observation re-run.** The recorded fixture uses division 65535, which sets the SMPTE bit and is correctly rejected as unsupported. Its legal equivalent (22 maximal deltas, division 32767, 1,000,000 us tempo) is rejected: "song is 180229 s long, which exceeds the 86400 s limit".

**Fails-before (method B).** With the tick accumulator wrapping as `u32` again, both regressions fail ("the guard saw 131075.99 s, not the true 139268.25 s"; "song is 131.076 s; expected 139.268 s"). Restored; `git diff` empty; both pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
