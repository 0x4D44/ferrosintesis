# MM-BUG-KILN-00061 — LA sample eligibility changes with output rate and drops bass onsets at 96 kHz

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler / sample-rate conversion
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Codex during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Scope on investigation: **186** (program, key,
  rate) combinations were affected, not the 3 bass programs reported, and there was a
  **second** SRC-scaled guard in `LaVoice::retrigger`. Awaits independent two-eyes closure.)

## Observation

**Symptom.** `LaVoice::build()` applies its credible-repitch range to the
sample-rate-converted playback step instead of the musical pitch ratio. Merely changing
the legal output sample rate therefore changes whether a note gets its sampled onset.

**Expected.** A note whose `target_hz / zone.root` lies in the documented
`0.5..=2.05` repitch range should use the sample at every supported output rate. Output
rate should change only the source-to-output clock conversion.

**Actual.** `crates/ferrosintesis/src/sampler.rs:2762-2766` computes
`step = (target_hz / zone.root) * 44100 / output_sr`, then checks `step` against
`0.5..=2.05`. At 96 kHz:

- GM 33/35 E1 against the 41.22 Hz finger-bass zone produces `step ≈ 0.459` and
  silently returns the bare model.
- GM 34 E2 against the 82.13 Hz pick-bass zone produces `step ≈ 0.461` and also
  returns the model.
- A much less credible E3 repitch from that E2 zone produces `step ≈ 0.922` and
  unexpectedly engages.

The public offline and realtime builders accept 96 kHz without a sample-layer caveat
at `crates/ferrosintesis/src/engine.rs:1708-1731` and
`crates/ferrosintesis/src/live.rs:58-78`. The sibling looped sample voices already use
the correct order—guard the pitch ratio, then apply `44100 / sr`—at
`sampler.rs:2320-2326`, `:3145-3151`, and `:3407-3413`.

This review did not run or render the application. The branch outcome is nevertheless
source-confirmed from the formula and return path.

## Fix

Compute `ratio = target_hz / zone.root`, validate `ratio` against `0.5..=2.05`, then
compute `step = ratio * 44100.0 / sr`.

Add samples-on versus samples-off engagement and pitch regressions for GM 33 E1/A1,
GM 34 E2, and GM 35 E1 at 44.1, 48, and 96 kHz. Add GM 33–35 to the canonical
sampled-program inventories that currently omit them.

## Scope on investigation

The report named GM 33/34/35 and one call site. Both were understated.

**The blast radius is 186 combinations, not 3 programs.** `LaVoice::build` is the shared
entry point for *every* LA-wrapped voice, so the defect reached everything with a sample
layer. Measured by the new sweep against the pre-fix tree — programs 0..=127 x keys
{24, 28, 33, 40, 52, 64, 76, 88} x rates {44.1, 48, 96} kHz — **186** (program, key, rate)
combinations changed eligibility with the output rate. Almost all are 96 kHz losing a
sample that 44.1 kHz keeps; a few (e.g. GM 4 key 64) already broke at 48 kHz.

**There was a second SRC-scaled guard.** `LaVoice::retrigger` re-checks the window when a
round-robin stroke rotates to a new zone, and it too tested a step
(`base_step * root_ratio`) against the pitch window. Same defect, same file, ~200 lines
down; fixing only the reported site would have left tremolo restrikes rate-dependent.

## Resolution

`crates/ferrosintesis/src/sampler.rs`:

- `LaVoice::build` computes `ratio = target_hz / zone.root`, validates **that** against
  `0.5..=2.05`, and only then converts to the output clock with `* 44100.0 / sr`. The
  `step` expression itself is unchanged, operation for operation, so playback pitch is
  algebraically identical — only the guard moved.
- `LaVoice` carries the musical `base_ratio` alongside `base_step`, because `retrigger`
  must re-check the window against a different zone root and cannot recover the ratio
  from `base_step` without knowing `sr`. `retrigger` now guards `base_ratio * root_ratio`.

Two oracles, both proven to fail on the pre-fix tree:

- `la_engagement_never_depends_on_output_rate` — the derived sweep described above.
  Engagement is detected EXACTLY rather than by threshold: when `build` rejects a note it
  returns `Err(sustain)`, and the caller unwraps the same model `samples: false` would
  have built, so the two renders are bit-identical. Any difference means the sample
  engaged. Red at 186; green at 0.
- `la_bass_onset_engages_at_every_supported_rate` — the report's own notes (GM 33 E1/A1,
  GM 34 E2, GM 35 E1) at 44.1/48/96 kHz, kept as a named regression.

Pitch is deliberately not scored across rates. The step formula is unchanged, and a
Goertzel peak cannot resolve a 41 Hz note well enough to compare rates: on an **unmodified**
tree the bin spacing alone moved GM 35 E1 by 35 cents between 44.1 and 48 kHz. Pinning a
threshold there would have measured the estimator, not the synth.

Behaviour at 44.1 kHz is unchanged (there `step == ratio`, so the two orderings agree),
which is why the album render-diff is clean — the CLI default rate is 44.1 kHz.

## Notes

- **Raised MM-BUG-KILN-00074 while building the sweep**, and deliberately did not fix it:
  GM 42/43 at C1 **panic** at 96 kHz because `BowedString`'s delay lines are sized in fixed
  samples (`voices.rs:8436-8437`). A different mechanism in a different file. The sweep
  carries a two-entry skip list naming that bug, to be deleted when it lands.
- The report asked to "add GM 33-35 to the canonical sampled-program inventories that
  currently omit them". Not done: no such single inventory was found in the source, and
  the sweep now covers all 128 programs derivationally, which is strictly stronger than
  adding three entries to a hand-maintained list. If a specific inventory was meant, it
  needs naming.
- No existing bug or open requirement matched the output-rate-dependent LA fallback.
- The correctness, reliability, test-coverage, and devil's-advocate passes independently
  confirmed the defect.
- The existing 96 kHz steel dry-out test at `sampler.rs:5260-5272` uses extreme key 100,
  whose large upward pitch ratio crosses the incorrect lower bound; it does not exercise
  zone-root notes and therefore does not refute this defect.

