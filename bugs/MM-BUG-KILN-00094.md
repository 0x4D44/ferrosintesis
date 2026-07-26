# MM-BUG-KILN-00094 — GM120 can repeat the same fret-noise take on consecutive events

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** synth / GM120 fret-noise round-robin
- **Raised:** 2026-07-24
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — replaced global-seed selection with a canonical per-channel twelve-take phase)

## Observation

The asset API says the synth cycles twelve takes so consecutive fret-noise events
do not repeat (`crates/ferrosintesis-samples-fretnoise/src/lib.rs:64-80`).
The consumer does not maintain a round-robin phase. It hashes the engine's global
voice seed and reduces it modulo twelve
(`crates/ferrosintesis/src/sampler.rs:4592-4604`).

The engine constructs that seed from `voice_seed_index`
(`crates/ferrosintesis/src/engine.rs:2576`) and advances the index for each accepted
voice at line 2714. Static evaluation of the exact wrapping-`u32` formulas shows
that isolated GM120 voice indices 27 and 28 both select zero-based take 10. Five
more adjacent repeats occur within the first 64 voices: 33/34, 44/45, 52/53,
55/56, and 61/62.

**Expected.** A twelve-take round-robin honoring the documented anti-machine-gun
contract never immediately reuses the previous take.

**Actual.** The seed hash provides aggregate variety but permits adjacent identical
rasps. The current oracle at `crates/ferrosintesis/src/voices.rs:16857-16880`
requires only eight distinct fingerprints among 24 seeds, so it cannot detect this
contract breach.

No audio render or audible comparison ran. The repeated take identity and reachable
voice indices are source-confirmed; how objectionable one repeated rasp sounds is
unverified.

## Fix

Make GM120 take selection own an explicit deterministic phase, preferably per
channel, and advance it exactly once for every accepted sampled GM120 event. Pass
the selected take index to `sampled_fret_noise`. If seeded pseudo-random ordering is
an intentional requirement, retain it only with previous-take rejection and update
the API name and tests to state that contract precisely.

Add an engine-level regression over more than 64 isolated and interleaved GM120
events. Require no adjacent equality, every take reachable, and deterministic wrap
or deterministic no-repeat behavior as selected above.

Estimated effort: Small–Medium.

## Resolution — 2026-07-26

`EngineCore` now owns one GM120 round-robin phase per MIDI channel. Every
accepted sampled fret-noise spawn advances exactly once through the derived
twelve-take bank, regardless of written key, unrelated accepted voices, or
another channel's GM120 events. The phase wraps at the bank length rather than
at an integer boundary.

The engine passes the selected take directly to `sampled_fret_noise`. Standalone
`voices::make` callers retain their prior deterministic seed mapping, while the
modeled-only path remains unchanged. `FretNoiseOneShot::rr_phase` exposes the
actual sounding take to the engine-level regression rather than inferring it
from counters or waveform similarity.

## Verification — 2026-07-26

- The fail-first engine oracle reproduced take 2 where channel 0's first
  canonical take had to be 0.
- The corrected oracle passes 528 interleaved GM120 events: 264 per channel,
  22 complete cycles each, all twelve takes reached, no adjacent replay, and
  no phase consumption by other programs, written keys, or channels. This also
  crosses a naive `u8` counter boundary.
- All 6 focused GM120 voice tests pass, including modeled and sampled routing,
  pitch independence, one-shot lifecycle, timbre, level, and standalone seed
  variation.
- The complete default suite passed (731 tests, 27 ignored), the true
  model-only suite passed (628 tests, 22 ignored), and both doc-test sets passed
  (4 each).
- Strict workspace clippy and true model-only clippy passed with warnings
  denied; formatting and `git diff --check` passed.
- Fresh release binaries from exact baseline `5c2b4fe`, full 124-MIDI inventory
  at 11.025 kHz: no catalog MIDI reaches GM120, so all 124 stayed
  byte-identical, with zero contamination and zero missed reachable paths.

## Notes

`MM-BUG-KILN-00040` is Fixed awaiting independent verification. Its original level
and timbre defect is distinct; this residual gap is split into a new ID rather than
reopening or overloading it.
