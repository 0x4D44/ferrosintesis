# MM-BUG-KILN-00036 — GM21 Accordion is a sparse 12-sine additive stack: reads thin/synthetic AND perceptually quiet

- **State:** Open
- **Priority:** Could
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL
  instrument-audition review; timbre defect confirmed by Fable 5 + Codex gpt-5.6-sol
  cross-agent reconciliation)

## Observation

In the neutral reference audition, GM21 (Accordion, musette) sounds **very quiet AND
"wrong sound"** to the ear, yet the max-momentary level metric reads it as roughly
matched to the SC-55. Both symptoms have one cause.

## Root cause

`organ()` case 21 (`crates/ferrosintesis/src/voices.rs:5644`) builds the accordion as a
**static 12-sine additive stack** — fundamental + detuned (±16 c) reed pairs on h1–h4,
harmonics falling 2.0→0.24 … 4.0→0.05 — plus only a token `.with_reed_noise(0.018, …)`.
There is no broadband reed buzz and no sampled body. The thin pure-sine spectrum excites
few critical bands, so it (a) reads quiet perceptually despite equal K-weighted energy
(few bands summed) and (b) sounds synthetic next to the SC-55's spectrally-rich sampled
accordion. A level trim cannot fix "wrong sound".

## Fix direction

Add spectral richness: a broadband reed buzz (noise-excited reed model) or more partials
with per-partial jitter, or an LA accordion onset/body sample layer. Related: closed bug
MM-BUG-KILN-00006 (no class-identity timbre oracle) — a Passport-style oracle would pin it.

## Note

The M-CAL derivation report and the audition markers labelled this slot "Percussive Organ"
in places — GM21 is **Accordion**; GM17 is Percussive Organ. Correct the label where it
appears.
