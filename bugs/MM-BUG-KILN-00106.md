# MM-BUG-KILN-00106 — GM 96 rain is cut off while the key is still held: the noise layer has no liveness term

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** voices / FX
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised by Claude Opus 4.5 while splitting the
  `--no-default-features` test failures of MM-BUG-KILN-00090. The failing clause was
  deliberately left LIVE and red rather than gated, because gating it would have buried a
  shipped defect — which is the whole point of KILN-00090's no-mass-gating rule.)

## Observation

**GM 96 (FX 1, rain) stops sounding while the key is still down.** Measured: the wash cuts
out at **t ≈ 4.69 s** on a held note (0.0513 RMS at 4.68 s → 0.0098 at 4.70 s), against the
oracle's 5.0 s hold.

This is **not** confined to `--no-default-features`. It is reachable from a normal,
default-feature build via the documented `--no-samples` CLI flag, so it is a shipped,
user-facing defect.

## Root cause

`Fx::render`'s liveness expression (`crates/ferrosintesis/src/voices.rs:12376`):

```rust
let rain_alive = self.rain.is_some() && (!self.rain_released || self.rain_env > 1e-4);
core_alive || self.echo_tail > 0 || rain_alive
```

Three terms — and **the layer that actually carries this voice is not one of them.**

- `echo_tail` — GM 96 has `echo_s: 0.0`, so this term is always `0`.
- `rain_alive` — `rain` is set at `voices.rs:12217`:
  ```rust
  let rain: Option<&'static [f32]> = (samples && load_rain).then(crate::sampler::rain_loop);
  ```
  so it is `None` whenever `samples` is false.
- `core_alive` — the crystal `Modal` bell, which `core_gain: 0.35` deliberately trims to
  "a hint under the wash".

So with no recorded bed, liveness collapses to a decorative bell. The **synthetic gated-noise
layer** (`grain: Option<GrainGate>`, `voices.rs:12067`) that produces the actual rain has
**no liveness term at all**. The voice is retired the instant the bell decays, mid-note.

In a default build with samples the bug is masked *structurally*, not by luck of timing:
`rain_alive` holds the voice open because the bed is present. Pass `--no-samples` and the
same expression collapses to the same broken case.

## Why this fits every observed fact

- **Why it fails now, modeled-only** — `rain: None`, `echo_tail: 0`, so only the bell keeps
  the voice alive and it decays before 5 s.
- **Why it passes in a default build** — `rain_alive` is true while held.
- **Why `--no-samples` on a default build also fails** — same `rain: None` path.
- **Why the cutoff is abrupt rather than a fade** — the voice is *retired*, not released; the
  wash is truncated rather than enveloped down.
- **Why nobody noticed** — the only oracle covering the held-note lifetime lived inside a
  test that also asserted sample-specific properties, so it had never run in a build where
  the defect is reachable.

## Suggested fix

Add a liveness term for the noise/grain layer: it is key-driven and should hold the voice
open while unreleased, exactly as `rain_alive` does for the recorded bed. Narrow and at the
right layer — the defect is a missing term in one boolean, not a design flaw in the voice.

**This changes the render** (GM 96 will sustain where it previously stopped), so it needs a
full render-diff inventory with EXPECTED diffs on tracks using GM 96, and no diffs elsewhere.
Worth an ear check on the sustained result too: the wash was never previously heard past the
bell's decay, so its steady-state character is effectively unaudited.

## Regression

`voices::tests::fx_o7_rain_96_real_recording_bed` clause (c) is the regression test and is
**deliberately left failing** in the modeled-only build (commit `5700759`). Clauses (a) and
(b) of that test were gated as genuinely sample-specific; (c) was not, precisely because it
catches this. Do not gate it to reach green.
