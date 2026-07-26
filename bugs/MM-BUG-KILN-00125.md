# MM-BUG-KILN-00125 — Realtime prewarm omits the split accent-cymbal PCM cache

- **State:** Fixed
- **Priority:** Should
- **Severity:** High
- **Area:** sampler / realtime drum kit
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T070129Z-p8852-n850611500-c1 branch=task/bug-MM-BUG-KILN-00125-run-fix-20260726T070129Z-p8852-n850611500-c1 code=62f6efc1175a1b8b8d3dff0aa99d595385ccd8f9 gate=manual)

## Observation

`RealtimeSynth::prewarm_samples()` promises to decode every embedded sample bank away
from the audio callback:
`crates/ferrosintesis/src/live.rs:211-224`.

`sampler::prewarm()` warms only
`ferrosintesis_samples_drumkit::RIDE.pcm(0, 0)` at
`crates/ferrosintesis/src/sampler.rs:2814-2823`. That initializes the core drum-kit
crate's cache at
`crates/ferrosintesis-samples-drumkit/src/lib.rs:778-785`.

The four banks moved to `ferrosintesis-samples-drumkit2` have an independent
crate-local `OnceLock` cache at
`crates/ferrosintesis-samples-drumkit2/src/lib.rs:274-281`. Sharing the `Bank` type
does not share storage: each `BankSource` points to its owning crate's `pcm`
function.

After prewarming, the first live GM 49/57 crash, GM 52 china, or GM 55 splash
NoteOn routes to the companion crate at
`crates/ferrosintesis/src/sampler.rs:4517-4542`. `SampledDrum::new` calls
`bank.pcm()` at `crates/ferrosintesis/src/sampler.rs:4432-4457`, so that first
accent hit decodes all 48 companion WAVs inside the deadline-bearing
`RealtimeSynth::fill_ring()` path at `crates/ferrosintesis/src/live.rs:292-305`.
The companion crate pins 10,619,904 embedded bytes at
`crates/ferrosintesis-samples-drumkit2/src/lib.rs:344-352`.

Expected: no sample cache initializes after `prewarm_samples()` returns.

Actual: the companion cache remains cold until the first routed accent-cymbal hit.
The decode and allocation are source-confirmed; exact wall time and audible dropout
duration are unmeasured because this pass did not run the application or a timing
probe.

## Fix

Warm one companion bank, such as
`ferrosintesis_samples_drumkit2::CRASH.pcm(0, 0)`, from `sampler::prewarm()`.
Prefer a common explicit prewarm hook on each asset crate so another packaging split
cannot silently add a new independent cache.

Add an end-to-end realtime regression that calls `prewarm_samples()`, sends a
companion GM key, renders one block, and proves no companion-cache initialization
occurred. A test-only initialization counter or cache-state probe in the companion
crate would make the oracle direct.

Estimated effort: Small for the call; Small–Medium for the durable oracle.

## Notes

Closed bug `MM-BUG-KILN-00073` strengthened prewarm coverage for lazy caches declared
inside `sampler.rs`. Its source scan explicitly cannot enumerate a dependency crate's
private `OnceLock`, so this post-split omission is new rather than a duplicate.
