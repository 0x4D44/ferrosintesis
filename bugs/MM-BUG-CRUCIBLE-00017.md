# MM-BUG-CRUCIBLE-00017 — amp-lab MIDI parser panics or silently accepts truncated tracks

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / sequencer
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`)

## Observation

`Loop::parse` returns `Result`, but malformed track data can panic or silently succeed.
At
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\seq.rs:77`,
a missing declared `MTrk` breaks and later returns `Ok`. A track ending after a delta and
status `0xFF` reaches `data[i]` at line 102 with `i == end` and panics. The tempo payload
check at line 108 uses the whole file length instead of the current track end, allowing a
read into the next chunk; other truncations break without an error.

Expected: malformed declared tracks return a descriptive `Err` through `audio::start`.
Actual: a damaged or partially regenerated embedded asset can crash startup or become an
empty/incorrect loop. Runtime input is compile-time embedded, so this is reliability, not
an external security boundary. The malformed cases were confirmed from bounds and control
flow; this pass did not execute them.

## Fix

Make VLQ, meta, SysEx, and channel-message reads fallible and bounded by the declared
track end. Reject missing/truncated declared tracks. Add regressions for terminal `0xFF`,
truncated VLQ, overlong meta/SysEx payload, and a missing second track.

## Notes

Confirmed by the reliability and maintainability lenses and the devil's advocate. The
security lens correctly refuted attacker reachability in the current binary.
