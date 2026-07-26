# MM-BUG-KILN-00125 — Realtime prewarm omits the split accent-cymbal PCM cache

- **State:** Closed
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
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T070129Z-p8852-n850611500-c1 branch=task/bug-MM-BUG-KILN-00125-run-fix-20260726T070129Z-p8852-n850611500-c1 code=62f6efc1175a1b8b8d3dff0aa99d595385ccd8f9 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, `clippy --workspace --exclude amp-lab --all-targets -D warnings`, `clippy -p ferrosintesis --no-default-features --all-targets -D warnings`, `test -p ferrosintesis --no-default-features --locked` (629 passed) and `test --workspace --exclude amp-lab --locked` (734 passed) - 1465 tests, 0 failures. Original observation re-run END TO END, and the fix proven non-vacuous by reverting it. Each drum asset package now exposes its own `prewarm()` hook that calls `decoded_samples()`, i.e. the real `PCM_CACHE.get_or_init` that decodes that package's whole inventory - so the core crate keeps exactly the coverage its old `RIDE.pcm(0, 0)` call gave it, and the companion is covered for the first time. `realtime_accent_cymbals_are_prewarmed_before_the_audio_block` drives a real `RealtimeSynth`, calls `prewarm_samples()`, asserts the companion cache is already warm, then sends the four routed companion GM keys (49/52/55/57), renders a block and asserts the initialization count did NOT move; an `active_voice_count() >= 4` clause stops it passing vacuously if routing ever stopped reaching the companion bank. To prove the guards genuinely guard, I deleted the single `ferrosintesis_samples_drumkit2::prewarm();` line from the tracked source and re-ran: BOTH went red - the source oracle naming the exact package ("are absent from sampler::prewarm(); the first routed NoteOn would decode them inside the realtime callback") and the realtime test reporting this bug's symptom verbatim ("prewarm_samples() returned while the companion drum cache was still cold"). Restored; `git status --porcelain` clean. The two sibling oracles from MM-BUG-KILN-00073 (`prewarm_leaves_no_bank_uninitialized`, `every_public_bank_accessor_is_exercised`) still pass, so nothing was weakened. I also attacked the new guard's enumeration predicate, since this repo's doctrine is that a derived oracle is only as good as its predicate: it derives the package set from `ferrosintesis/Cargo.toml` with a `>= 2` non-vacuity floor and DOES pick up a hypothetical `-drumkit3` declared in the repo's mandated inline-table form, but it keys on the `ferrosintesis-samples-drumkit` name prefix, so a future asset crate split under a DIFFERENT name carrying its own private `OnceLock` would evade it. I censused every sample crate for that gap and it is theoretical rather than live: only `-drumkit` and `-drumkit2` hold a private `OnceLock` today and both are hooked, so there is no uncovered cache to split into a new ID. Recorded here as the watch item for the next packaging split.)

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
