# MM-BUG-KILN-00017 — Electric pianos (GM 4–5) have no tine-strike LA onset layer

- **State:** Closed
- **Priority:** Could
- **Severity:** Medium
- **Area:** sampler
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-20, Claude Opus 4.8 (1M) — GM4 Rhodes onset landed `b8d47e1`; GM5 model-only by design) → Closed (2026-07-21, independently verified by Codex GPT-5: GM4 onset oracle red-before/green-after; GM5 premise corrected to modeled FM by design; workspace tests and clippy green)

## Observation

`electric_piano_1` (GM 4) and `fm_electric_piano` (GM 5) are pure models
(`crates/ferrosintesis/src/voices.rs:~10700`). The Rhodes/Wurlitzer tine "bark"
is an onset transient the model fakes weakly, and these are among the most-played
GM patches. The grand/upright precedent (`voices.rs:~10689`) shows the LA wrap
generalizes to keyboard timbres.

The round-3 records already earmarked a `jRhodes` CC0 onset unit (Tier-1 asset
unit U8), blocked only on a human download-and-inspect of sample fitness.

## Fix

Add tine-strike onset banks for GM 4–5 via `LaVoice::wrap`, using
`contrabass_bank` as the wiring template, once the CC0 source is vetted.

### Fix summary (2026-07-20) — LANDED

GM 4 got a real Fender Rhodes Mk II tine onset over `electric_piano_1`, in the new `-ccby` crate
(`b8d47e1`). Source: **tim.kahn** Freesound pack 3957, **CC-BY 4.0** — the earmarked `jRhodes` set
was *rejected* (its sample bytes are CC-BY-**NC**, correcting the round-3 "CC0 covers the WAV bytes"
premise; see the 2026-07-19 sourcing HLD). GM 5 stays **model-only** by design (a DX EP *is* FM —
round-3 §7.2). Pure model preserved as the CC0!=0 alt; oracle + render-diff (0 contamination) green.

### Verification summary (2026-07-21 — Codex GPT-5)

Independent of the Claude Opus 4.8 fixer. On `b8d47e1^`, adding GM4 to the committed
default-layer oracle failed with an attack-window difference of exactly 0.00000: samples-on
was still the pure model. Current trunk passed
`altbank_sampled_programs_preserve_pure_model_and_default_layers`, proving the Rhodes onset
engages and the CC0 alternate remains sample-independent. Source review confirmed GM4 wraps
`rhodes_bank`; GM5 deliberately remains its dedicated FM model because a DX electric piano
is synthesized by FM, correcting the original two-program premise rather than leaving a gap.
Workspace tests and clippy were green.

## Notes

- Enhancement filed as a bug per the maintainer routing decision (2026-07-18).
- Also feeds MM-BUG-KILN-00006's concern: 4/5 is a documented perceived-clone
  pair; distinct sampled onsets would help separate them.
