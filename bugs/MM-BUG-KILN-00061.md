# MM-BUG-KILN-00061 — LA sample eligibility changes with output rate and drops bass onsets at 96 kHz

- **State:** Open
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

## Notes

- No existing bug or open requirement matched the output-rate-dependent LA fallback.
- The correctness, reliability, test-coverage, and devil's-advocate passes independently
  confirmed the defect.
- The existing 96 kHz steel dry-out test at `sampler.rs:5260-5272` uses extreme key 100,
  whose large upward pitch ratio crosses the incorrect lower bound; it does not exercise
  zone-root notes and therefore does not refute this defect.

