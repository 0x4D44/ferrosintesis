# MM-BUG-CRUCIBLE-00013 — amp-lab backlog recovery reallocates before rendering audio

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / realtime audio
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T05:47:01Z, deltic:auto role=fix run=fix-20260801T052423Z-p69264-n537202200-c1 branch=task/bug-MM-BUG-CRUCIBLE-00013-run-fix-20260801T052423Z-p69264-n537202200-c1 code=be7f0e96383ca4724eb74071f42e7740f1322ef6 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 9ec1281; fixer was OpenAI GPT-5 Codex)

## Observation

Static review confirmed that callback recovery can exceed the synth command
reservation. The callback drains every available entry at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\audio.rs:304`;
the ring holds 4,095 entries at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\ring.rs:29`.
`RealtimeSynth.pending` reserves only 128 commands at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\ferrosintesis\src\live.rs:188`,
and each completed MIDI message pushes into that `Vec` at line 484. A stalled callback
followed by more than 128 queued messages therefore reallocates on the deadline-bearing
audio thread. The callback also processes the entire fixed-size backlog before rendering.

Expected: post-setup callback work stays allocation-free and within a safe control
budget. Actual: the ring bounds total memory, but a legal backlog exceeds the 128-command
reservation and can compound the stall. This is the untested burst residual of closed
MM-BUG-KILN-00082 and the backlog hardening deliberately left open by
MM-BUG-KILN-00083. No timing or audibility measurement ran in this static pass.

## Fix

Bound command work per callback and coalesce idempotent rig/Play/Solo/Panic state. Keep
the remaining MIDI batch within an explicit fixed capacity and define overflow recovery.
Add allocation and work-budget regressions for more than 128 completed messages and a
fully occupied mixed command ring.

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `9ec1281` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-12-13`.

**Original observation reproduced, with a measurement the static report could not
make.** Reverting only the two production knobs — `MAX_QUEUED_COMMANDS` back to
4095 and `Outbox::send_knob` back to the incremental knob triple, tests untouched —
made the regression fail with exactly the reported mechanism:

> one callback drained 450 UI commands and allocated 1 times

450 bytes is the 50 edits x 9-byte triple from the report (150 completed messages),
and the single allocation is `RealtimeSynth.pending` growing past its retained
128-command reservation **on the audio thread**. `more_than_128_completed_messages_
coalesce_to_the_latest_snapshot` failed alongside it. Restoring `ring.rs` /
`outbox.rs` (md5 `1b06cf16…` / `b677bb98…`) turned both green.

**Root cause addressed.** Three parts, and all three are needed: the ring now caps
at 63 entries (one 61-command snapshot plus two spare for panic), so at most 21
complete MIDI messages can reach one callback — comfortably inside the 128
reservation; every enqueue carries the whole state, so rapid edits coalesce in
`Outbox` rather than queueing; and the callback drains one *captured* publication
into a fixed `[Cmd; 63]` stack buffer via `drain_published`, so concurrent
publication cannot extend the work it already committed to. `Consumer::pop` is now
`#[cfg(test)]`, closing the unbounded `while let Some(c) = rx.pop()` path.

**Checked for a behaviour regression, found none.** Every knob edit now costs 61
ring entries instead of 9, but `Cmd::Midi` never reaches the ring from a live
performance path — `send_cmd` is only ever called with `Play`/`Solo` in
`main.rs`, and the sequencer runs inside `Core`. So the smaller ring cannot drop
note events. Play/Solo coalescing is idempotent and `Core::command` now early-returns
on an unchanged value.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 33 pass / 0 fail, including both allocation oracles; `cargo clippy
--all-targets -- -D warnings` clean; `cargo fmt -- --check` clean. The fix touches
no root-workspace crate, so the root gate is not implicated and was not run.

## Notes

Confirmed independently by the correctness, performance, and reliability lenses, then
by the devil's advocate. The work is excessive but bounded by the 4,095-entry ring; it is
not described as unbounded.
