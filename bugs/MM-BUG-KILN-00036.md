# MM-BUG-KILN-00036 — GM21 Accordion is a sparse 12-sine additive stack: reads thin/synthetic AND perceptually quiet

- **State:** Blocked
- **Priority:** Could
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-21
- **Owner:** Arthur
- **Owner role:** human
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
  cross-agent reconciliation) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — current trunk still has the measured sparse additive voice, but Arthur must choose a modeled-reed target or approve a sourced LA accordion layer before an audible fix has a correctness target)

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

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Current trunk still matches the diagnosis:
`organ(21)` is twelve sine entries plus `with_reed_noise(0.018, ...)`. The later
musette work made H2–H4 beat correctly, but did not add the broadband body this
audition found missing.

Unblock when Arthur chooses one of these audible product targets:

1. **Modeled accordion:** authorize a noise-excited reed/broadband buzz and
   per-partial instability pass, with an A/B target of “spectrally rich French
   musette, clearly fuller than GM23 bandoneon without becoming an organ”.
2. **LA accordion:** provide an owner recording or approve a CC0/CC-BY source
   and its retained provenance, plus the intended onset/body crossfade policy.

After either choice, the Build must add a class-identity oracle for broadband
reed energy, retain the existing per-harmonic musette and drier-bandoneon
oracles, remeasure perceived level after the timbre change, and run the full
catalog render-diff required for `voices.rs` changes. Picking either synthesis
or sampling unattended would invent both the timbre contract and asset scope.

## Note

The M-CAL derivation report and the audition markers labelled this slot "Percussive Organ"
in places — GM21 is **Accordion**; GM17 is Percussive Organ. Correct the label where it
appears.
