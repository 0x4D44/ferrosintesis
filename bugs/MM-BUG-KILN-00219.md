# MM-BUG-KILN-00219 — Clavinet embeds and decodes more than one second of unreachable audio per zone

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** clavinet sample assets / binary and runtime footprint
- **Raised:** 2026-08-16T13:44:22Z
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
- **State history:** Open (2026-08-16T13:44:22Z, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

All eleven packaged clavinet WAVs contain 70,560 PCM frames (1.600 seconds). The runtime loop search at D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-141612\crates\ferrosintesis\src\sampler.rs:5518-5530 restricts the loop start to at most 0.34 seconds and its length to at most 0.11 seconds, so every selected loop ends by 0.45 seconds. ClavinetSampled::sample_at and render at sampler.rs:5672-5718 wrap all later reads into that loop; they never consume any frame after loop_end.

At least 50,715 frames per file are therefore unreachable. Across eleven zones, the shipped bank carries at least 1,115,730 unused embedded PCM bytes and decodes them into another 2,231,460 unused f32 bytes. The audio behavior is not shown wrong; the confirmed defect is avoidable binary and resident-memory cost.

Expected: the packaged and decoded data ends after the last frame the renderer can reach, plus only the interpolation guard it requires. Actual: most of every asset is embedded and decoded but cannot be read.

Concrete fix: trim each baked WAV after a proved-safe interpolation guard beyond the maximum selected loop end, or change the voice to use the tail. Add a source-reachability oracle and a differential check proving representative roots, sample rates, and pitch bends remain bit-equivalent. Update the aggregate-size canary and provenance. Static review only; no app, build, test, render, generator, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
