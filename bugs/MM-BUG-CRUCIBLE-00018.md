# MM-BUG-CRUCIBLE-00018 — amp-lab event-cap overflow permanently drops note events

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / realtime sequencer
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T065846Z-p87252-n946572800-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00018-run-fix-20260801T065846Z-p87252-n946572800-c1
- **Owner base:** 91d1b991ca18e3dcf6eb48126e25afadce3c293b
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T06:58:46Z
- **Owner until:** 2026-08-01T08:58:46Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`)

## Observation

When a render block schedules more than 256 events,
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\audio.rs:141`
increments xruns and returns from the emitter without retaining the event.
`Player::advance` still increments its cursor at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\seq.rs:216`,
so the event is permanently discarded. A dropped NoteOff can leave a voice sounding; a
dropped NoteOn can silence a note. The comment at `audio.rs:142` says “keep playing rather
than dropping the event”, the opposite of the implementation.

Expected: overflow preserves MIDI semantics, even if event offsets must degrade, or resets
safely. Actual: dense regenerated backing data corrupts note state. The current embedded
614-event loop produces only a handful per normal callback, so the trigger is a future
dense asset or unusually large block. This pass did not execute that case.

## Fix

On overflow, preserve events through a bounded fallback that may coarsen offsets, or stop
the player and issue a hard reset rather than continuing with corrupted note state. Add a
regression with more than 256 same-block messages that proves paired note-offs are not
lost and that the overflow policy is explicit.

## Notes

Confirmed by direct control-flow review and the devil's advocate. Severity is Low because
the shipped backing stays well below the cap.
