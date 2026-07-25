# MM-BUG-KILN-00038 — GM61 Brass Section has no LA sample layer (pure 5-player waveshaper) and reads synthetic

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
  instrument-audition review; "quiet synthetic" — Arthur's ear, code-confirmed) → Blocked (2026-07-25, GPT-5.6 Codex on KILN-Windows — trunk deliberately keeps GM61 model-only because the old sample was a wrong solo trumpet and no licensed brass-section onset exists; Arthur must approve a source or a modeled-section target)

## Observation

GM61 (Brass Section) sounds "quiet synthetic" next to the SC-55's sampled brass. Its LEVEL
is roughly right (M-CAL residual −1.15 dB); the complaint is timbre.

## Root cause

`BR_SECTION` (`crates/ferrosintesis/src/voices.rs:10091`) is a **pure model** — 5 waveshaped
`brass_valve` players with **no LA sample layer**. The dispatch `61..=63 => Box::new(brass(...))`
(`voices.rs:12340`) has no `LaVoice` wrap, and the prior solo-trumpet sample layer was
deliberately dropped (comment `voices.rs:10094`). A 5-player detuned-waveshaper section reads
synthetic against sampled brass.

## Fix direction

Add an LA brass onset/body sample layer for the section (as the solo brass once had), or
enrich per-player spectral variance (breath noise, per-player formant jitter). Level trim
is not the lever. Related: MM-BUG-KILN-00018 (closed) fixed the natural-brass h2–h5 low-mid
formant ring; the section-specific "no sample layer" synthetic quality is separate.

### Blocker — 2026-07-25

Blocking owner: **Arthur**. Current trunk confirms the diagnosis and the
intentional boundary: GM61 remains a five-player model, while its former LA
layer was removed because it replayed a solo trumpet and no CC0 brass-section
sample exists. Restoring that asset would reintroduce the wrong instrument.

Unblock with one of these concrete inputs:

1. **LA section:** provide an owner recording or approve a CC0/CC-BY
   multi-player brass-section source, with retained provenance and the intended
   onset/body crossfade.
2. **Modeled section:** authorize a per-player spectral-variance pass and state
   the listening target—breath/formant diversity that reads as a section while
   remaining distinct from solo GM56–60 and synth brass GM62/63.

Either route changes audible voicing. The Build must add a section-identity
oracle, preserve the existing brass-family controls, and run the full catalog
render-diff required for `voices.rs`/`sampler.rs` changes. Selecting an asset
source or voicing character unattended would guess at both product and
licensing decisions.
