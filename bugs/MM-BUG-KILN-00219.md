# MM-BUG-KILN-00219 — Clavinet embeds and decodes more than one second of unreachable audio per zone

- **State:** Closed
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
- **State history:** Open (2026-08-16T13:44:22Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T15:57:32Z, deltic:auto role=fix run=fix-20260913T154255Z-e6d44563 branch=task/bug-MM-BUG-KILN-00219-run-fix-20260913T154255Z-e6d44563 code=6ee2af43e4ead58a1422302ad2e03b0ab2dacaf9 gate=manual) -> Closed (2026-09-13T19:25:30Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: trimmed clavinet assets are exact prefixes with identical loops and 1485 bit-identical renders; its two gate breaks split to MM-BUG-CRU-00064)

## Observation

All eleven packaged clavinet WAVs contain 70,560 PCM frames (1.600 seconds). The runtime loop search at D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-141612\crates\ferrosintesis\src\sampler.rs:5518-5530 restricts the loop start to at most 0.34 seconds and its length to at most 0.11 seconds, so every selected loop ends by 0.45 seconds. ClavinetSampled::sample_at and render at sampler.rs:5672-5718 wrap all later reads into that loop; they never consume any frame after loop_end.

At least 50,715 frames per file are therefore unreachable. Across eleven zones, the shipped bank carries at least 1,115,730 unused embedded PCM bytes and decodes them into another 2,231,460 unused f32 bytes. The audio behavior is not shown wrong; the confirmed defect is avoidable binary and resident-memory cost.

Expected: the packaged and decoded data ends after the last frame the renderer can reach, plus only the interpolation guard it requires. Actual: most of every asset is embedded and decoded but cannot be read.

Concrete fix: trim each baked WAV after a proved-safe interpolation guard beyond the maximum selected loop end, or change the voice to use the tail. Add a source-reachability oracle and a differential check proving representative roots, sample rates, and pitch bends remain bit-equivalent. Update the aggregate-size canary and provenance. Static review only; no app, build, test, render, generator, or exploratory harness ran. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `6ee2af43`) by an agent other than the fixer.

**Original observation re-run.** All 11 clavinet assets went from 70,560 to 19,849 frames. Decoding the `6ee2af43^` assets: each trimmed asset equals the old asset's first 19,849 samples, the prefix SHA-256 pins match, loop points are identical in all 11 zones (largest loop end 17,842), and 1,485 renders on old versus trimmed data are bit-identical (3 keys per zone; 22.05/44.1/96 kHz; bends 0.25x-4x; 3 velocities; with note-off). `ClavinetSampled::sample_at` never reads at or beyond `loop_end`.

**Regression.** `sampler::tests::clavinet_assets_end_at_the_runtime_reachable_prefix` passes on HEAD; the old 70,560-frame assets fail its length-equals-reach assertion (method A).

**Residual split to MM-BUG-CRU-00064 (Must).** The landing broke two required gates: `CLAVINET_RUNTIME_GUARD_FRAMES`/`CLAVINET_REACH_FRAMES` are dead outside tests (workspace clippy), and the pre-existing `banks_parse` 20,000-frame floor now rejects the bank. The measured reachability shows the floor, not the trim, needs the adjustment.

## Notes
