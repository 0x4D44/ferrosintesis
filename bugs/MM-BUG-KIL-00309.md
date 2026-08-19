# MM-BUG-KIL-00309 — Realtime accent-cymbal prewarm guard is tautological and schedule-dependent

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** realtime synth / prewarm contract tests
- **Raised:** 2026-08-19T09:33:21Z
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
- **State history:** Open (2026-08-19T09:33:21Z, raised via `deltic bugs new`)

## Observation

`realtime_accent_cymbals_are_prewarmed_before_the_audio_block`
(`crates/ferrosintesis/src/live.rs:1365-1395`, raised for MM-BUG-KILN-00125) does
not reliably prove its contract, for two stacked reasons:

1. **The post-render assertion is unreachable-by-construction.**
   `ferrosintesis_samples_drumkit2::pcm_cache_initializations()` is
   `usize::from(PCM_CACHE.get().is_some())`
   (`crates/ferrosintesis-samples-drumkit2/src/lib.rs:251-253`) — a saturating 0/1
   over a `OnceLock` that never resets. Once line 1372 has asserted `before == 1`,
   line 1390's `assert_eq!(…, before)` after `render_add` cannot fail whatever the
   audio block does. The oracle's second half is dead code.
2. **The first assertion is contaminated by process-global state.** All unit tests
   share one libtest binary, and sampler tests reach kit2 PCM through
   `Bank::pcm()` — `sampled_drum_choke_reaches_silence_within_20_ms`
   (`crates/ferrosintesis/src/sampler.rs:7324`) and
   `sampled_drum_has_no_boundary_click` (`sampler.rs:7363`, via `routed_banks()`
   which includes CRASH/CHINA/SPLASH). Whenever one of those runs first, the cache
   is already warm and `before == 1` regardless of whether
   `prewarm_samples()` reached `drumkit2::prewarm()`.

Concrete regression it can miss: remove `ferrosintesis_samples_drumkit2::prewarm()`
from `sampler::prewarm()` (`sampler.rs:3010`); this test then fails only on
schedules where it runs before any kit2-touching sampler test — a flaky-red,
usually-green guard for a realtime contract whose failure mode is FLAC-decoding
~7.6 MB inside the audio callback. The `BANK_INITS` delta oracle deliberately does
not cover drumkit2 (packages own independent caches, `sampler.rs:3005-3006`), and
the prewarm source-scan is textual, so this test is the only end-to-end guard.

Expected: the guard fails deterministically when the accent-cymbal package is not
prewarmed before the audio block. Actual: half of it is vacuous and the other half
depends on test scheduling. Current prewarm coverage is correct; false-green oracle
defect. Same saturating-counter shape the crate's own re-exec probe already works
around (MM-BUG-CRUCIBLE-00035).

## Fix

Either re-exec this test in a pristine child keyed on
`pcm_cache_initializations() == 0` (the drumkit2 lib.rs:435-483 pattern) and assert
0 before `prewarm_samples()`, 1 after, 1 after `render_add`; or replace the
saturating diagnostic with a monotonic decode counter in the drumkit2 crate and
assert a zero delta across the render block (the `BANK_INITS` shape,
live.rs:1340). Prove the fixed test goes red with `sampler.rs:3010` removed.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941), devil's-advocate lens.
Estimated effort: Small-Medium.
