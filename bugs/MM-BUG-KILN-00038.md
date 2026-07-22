# MM-BUG-KILN-00038 — GM61 Brass Section has no LA sample layer (pure 5-player waveshaper) and reads synthetic

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
  instrument-audition review; "quiet synthetic" — Arthur's ear, code-confirmed)

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
