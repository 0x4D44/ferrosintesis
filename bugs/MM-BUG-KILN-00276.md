# MM-BUG-KILN-00276 — ScaledVoice allocates scratch storage on its first realtime render

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / realtime velocity-corrected voices
- **Raised:** 2026-08-17T09:41:38Z
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
- **State history:** Open (2026-08-17T09:41:38Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T18:10:44Z, deltic:auto role=fix run=fix-20260913T175902Z-4ca006d0 branch=task/bug-MM-BUG-KILN-00276-run-fix-20260913T175902Z-4ca006d0 code=1a6e21862ca095aaecf7e05de4973d26eeeb9a0d gate=manual)

## Observation

Observation: ScaledVoice owns scratch: Vec<f32> at crates/ferrosintesis/src/voices.rs:14151-14158. apply_vel_correction constructs every non-square-law wrapper with Vec::new() at :14255-14271. The first ScaledVoice::render call clears and resizes that empty vector to the block length at :14179-14190, which allocates inside RealtimeSynth::fill_ring's deadline-bearing render at crates/ferrosintesis/src/live.rs:397-417. Any corrected voice, including the program families listed at voices.rs:14124-14135 and corrected drum wrappers, can pay this allocation once per new note. prewarm_samples and reserve_realtime_storage do not reserve this per-wrapper scratch.

Expected: after documented realtime setup, voice rendering does not defer scratch allocation to the callback. Actual: every newly created ScaledVoice allocates on its first render block.

Concrete fix: use bounded inline scratch for the 64-frame realtime block, pre-size the scratch at construction off the render loop, or provide a reusable engine scratch pool. Add a counting-allocator regression around a fresh corrected melodic voice and corrected drum voice after realtime setup.

Static review only. Open MM-BUG-KILN-00216 tracks the same defect shape in LaVoice, but not this independent wrapper or its wider set of programs. Estimated effort: Small-Medium.

## Fix

<unfixed — raised only>

## Notes
