# MM-BUG-KILN-00216 — LaVoice allocates scratch storage inside realtime rendering

- **State:** Open
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
- **State history:** Open (2026-08-16T12:38:59Z, raised via `deltic bugs new`)

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

## Notes

Use bounded inline/chunked scratch or reserve the buffer before realtime use,
then delegate directly to the sustain after the sample handover. Add an
allocation-count oracle around fresh GM 4 and GM 15 NoteOns after both setup
calls. Estimated effort: Medium.

Static review only. Allocator latency and dropout duration are unverified; no
app, test, build, render, package command, or exploratory harness ran.
