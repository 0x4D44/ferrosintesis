# MM-BUG-CRUCIBLE-00013 — amp-lab backlog recovery reallocates before rendering audio

- **State:** Fixed
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T05:47:01Z, deltic:auto role=fix run=fix-20260801T052423Z-p69264-n537202200-c1 branch=task/bug-MM-BUG-CRUCIBLE-00013-run-fix-20260801T052423Z-p69264-n537202200-c1 code=be7f0e96383ca4724eb74071f42e7740f1322ef6 gate=manual)

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

## Notes

Confirmed independently by the correctness, performance, and reliability lenses, then
by the devil's advocate. The work is excessive but bounded by the 4,095-entry ring; it is
not described as unbounded.
