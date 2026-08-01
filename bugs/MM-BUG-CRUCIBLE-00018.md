# MM-BUG-CRUCIBLE-00018 — amp-lab event-cap overflow permanently drops note events

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** amp-lab / realtime sequencer
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T07:12:22Z, deltic:auto role=fix run=fix-20260801T065846Z-p87252-n946572800-c1 branch=task/bug-MM-BUG-CRUCIBLE-00018-run-fix-20260801T065846Z-p87252-n946572800-c1 code=2d1d62bf4ba4ef53058d1a69cb0e1192ebab683a gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 7dfc278; fixer was OpenAI GPT-5 Codex)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `7dfc278` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-18`.

**Original observation reproduced, including the consequence it could only predict.**
Reverting just the overflow handling to the pre-fix drop-and-continue (test
untouched) made `event_overflow_stops_and_resets_instead_of_losing_note_offs` fail
with `44 != 1` — 300 scheduled events against a 256 capacity, so 44 were silently
discarded and the player advanced past every one.

The report said "a dropped NoteOff can leave a voice sounding" but could not run it.
I built a throwaway fixture that orders all 150 note-ons before all 150 note-offs, so
overflow eats only note-offs, and measured the pre-fix path:

    after overflow: xruns=44 playing=true pos=0 live_voices=128

128 stuck voices, transport still running. The stranded-note consequence is real, not
just plausible. Restoring `audio.rs` (md5 `86993745…`) turned the regression green,
and its own assertions pin the opposite state: one xrun, `playing == false`,
`pos == 0`, `active_voice_count() == 0`, and an empty pending batch.

**The fix picks the safer of the two options the bug offered.** It takes "stop the
player and hard-reset" rather than "coarsen offsets and continue" — the partial batch
is discarded before it can be applied, so no prefix of a corrupted sequence reaches
the synth. `MAX_EVENTS_PER_BLOCK` keeps its allocation-free purpose, and the comment
that contradicted the code is gone. Resuming is a deliberate transport toggle, which
is the right call for a state that is known to be corrupt.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 44 pass / 0 fail; `cargo clippy --all-targets -- -D warnings` clean;
`cargo fmt -- --check` clean.

## Notes

Confirmed by direct control-flow review and the devil's advocate. Severity is Low because
the shipped backing stays well below the cap.
