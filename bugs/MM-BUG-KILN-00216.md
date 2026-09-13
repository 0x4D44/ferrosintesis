# MM-BUG-KILN-00216 — LaVoice allocates scratch storage inside realtime rendering

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime sampled voices
- **Raised:** 2026-08-16T12:38:59Z
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
- **State history:** Open (2026-08-16T12:38:59Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T05:26:42Z, deltic:auto role=fix run=fix-20260913T050202Z-f0606a5c branch=task/bug-MM-BUG-KILN-00216-run-fix-20260913T050202Z-f0606a5c code=1bb5b439fc2ddbc346ba3c582876a2d13e06e51b gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: heap scratch restored fails both inline-scratch tests with 64-frame growth; no-default clippy dead-code break split to MM-BUG-CRU-00063)

## Observation

`LaVoice` stores its per-voice render scratch as `Vec<f32>` at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-131612\crates\ferrosintesis\src\sampler.rs:3378`.
`LaVoice::build` initializes it with `Vec::new()` at line 3832. The first call to
`LaVoice::render` then calls `resize(out.len(), 0.0)` at line 3852, which must
allocate capacity for a fresh sampled voice.

This render runs in the deadline-bearing realtime block. The documented setup
calls do not reserve this allocation: `RealtimeSynth::prewarm_samples()` warms
sample caches, while `reserve_realtime_storage()` reserves engine voice/index
vectors (`crates/ferrosintesis/src/live.rs:295-320`). Every newly constructed
sampled GM 4 or GM 15 NoteOn therefore grows a separate scratch vector on its
first audio callback; a chord repeats the allocator call once per new voice.

Expected: after both realtime setup calls, rendering a fresh sampled NoteOn
performs no heap allocation. Actual: the per-voice scratch allocation is deferred
to first render.

## Fix

Unfixed; raised only.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `1bb5b439`) by an agent other than the fixer.

**Original observation re-derived.** `LaVoice::render` uses an inline `[f32; 64]` buffer for blocks of at most `LIVE_BLOCK` (64) frames; the heap `long_buf` grows only for longer offline slices.

**Fails-before (method B).** Making render always resize `long_buf` fails `la_realtime_block_does_not_grow_render_scratch` and `sampled_gm4_and_gm15_realtime_blocks_use_inline_scratch` (both left 64, right 0), so the GM4/GM15 construction-path test is not vacuous. Restored; `git diff` empty; both pass on HEAD.

**Residual split to MM-BUG-CRU-00063 (Must).** The `#[cfg(test)]` probe `Voice::realtime_scratch_capacity_for_test` is only called from tests gated on `embedded-samples`, so the required `cargo clippy -p ferrosintesis --no-default-features --all-targets -D warnings` step fails with dead code.

## Notes

Use bounded inline/chunked scratch or reserve the buffer before realtime use,
then delegate directly to the sustain after the sample handover. Add an
allocation-count oracle around fresh GM 4 and GM 15 NoteOns after both setup
calls. Estimated effort: Medium.

Static review only. Allocator latency and dropout duration are unverified; no
app, test, build, render, package command, or exploratory harness ran.
