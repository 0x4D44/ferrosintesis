# MM-BUG-CRUCIBLE-00012 — amp-lab recovery snapshots are prefix-visible to the audio thread

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** amp-lab / command delivery
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

Static review confirmed that `Outbox::pump` does not deliver its claimed atomic state
snapshot atomically to the audio thread. `D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\outbox.rs:107`
preflights room for the rig bytes plus Play/Solo, but
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\ring.rs:163`
calls `push` for every byte, and each call publishes `head` immediately at line 143.
The callback at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-021611\crates\amp-lab\src\audio.rs:304`
can consume a complete bank/program prefix, observe the ring temporarily empty, and
render before the remaining NRPN and transport commands are published.

Expected: a recovery or A/B snapshot becomes visible as one state. Actual: a callback
can render a partially recalled rig. This is a residual of closed
MM-BUG-KILN-00083: its capacity preflight prevents drops, not concurrent prefix
visibility. The app and tests were not run in this read-only review.

## Fix

Add a producer batch operation that writes all commands into unpublished slots and
advances `head` once with a Release store. Use one batch for rig + Play + Solo. Add an
interleaving regression that pauses the producer mid-batch and proves the consumer sees
either no snapshot or the complete snapshot, never a prefix.

## Notes

Confirmed independently by the correctness, reliability, and maintainability lenses,
then by the devil's advocate.
