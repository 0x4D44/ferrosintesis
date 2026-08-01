# MM-BUG-CRUCIBLE-00012 — amp-lab recovery snapshots are prefix-visible to the audio thread

- **State:** Closed
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol xhigh from a static multi-lens review; Deltic mint was sandbox-blocked, so the ID was allocated per `bugs/README.md`) -> Fixed (2026-08-01T05:22:18Z, deltic:auto role=fix run=fix-20260801T050649Z-p90352-n433912700-c1 branch=task/bug-MM-BUG-CRUCIBLE-00012-run-fix-20260801T050649Z-p90352-n433912700-c1 code=44781045b80ef112a9fec37fde22deda9042b2c7 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 9ec1281; fixer was OpenAI GPT-5 Codex)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `9ec1281` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-12-13`.

**Root cause addressed at the right layer.** The per-byte publication is gone from
the snapshot path: `Producer::push_generated` writes every slot behind an
unpublished local `head` and advances the shared `head` once with a `Release`
store, and `Outbox` reaches it through `push_batch` / `push_midi`. `Producer::free`
is now `#[cfg(test)]`, so no production caller can preflight-then-publish
separately again — the fix removes the *shape* of the bug, not just its instance.
The consumer's `Acquire` load of `head` pairs with that store, so the copied slots
are the ones the release published.

**Fails-before proved by reverting only the publication mechanism.** Replacing the
write-behind loop with the pre-fix per-item `self.push(...)` (test untouched) made
`ring::tests::batch_is_published_atomically` fail exactly as reported — the
consumer observed the prefix `Some(Midi(193))` while the producer was still inside
the batch. Restoring `ring.rs` (md5 `1b06cf16…`) turned it green.

**Gates** (amp-lab is its own workspace, so these run from `crates/amp-lab/`):
`cargo test` 33 pass / 0 fail; `cargo clippy --all-targets -- -D warnings` clean;
`cargo fmt -- --check` clean. The fix touches no root-workspace crate, so the root
gate is not implicated and was not run.

## Notes

Confirmed independently by the correctness, reliability, and maintainability lenses,
then by the devil's advocate.
