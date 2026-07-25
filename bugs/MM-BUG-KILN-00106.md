# MM-BUG-KILN-00106 — GM 96 rain is cut off while the key is still held: the noise layer has no liveness term

- **State:** Closed
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
- **State history:** Open (2026-07-25, raised by Claude Opus 4.5 while splitting the `--no-default-features` test failures of MM-BUG-KILN-00090. The failing clause was deliberately left LIVE and red rather than gated, because gating it would have buried a shipped defect — which is the whole point of KILN-00090's no-mass-gating rule.) → Fixed (2026-07-25, Codex GPT-5.6-Sol; synthetic rain liveness now follows key hold with default, samples-off, and modeled-only regression coverage; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded mid-hold cut-off reproduced by removing only the liveness term)

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

The `Fx` liveness expression now includes the synthetic grain wash while its key
is held. Note-off clears that term, so the modeled wash yields to the existing
core release; the sampled rain bed keeps its envelope-driven fade-out unchanged.

The previously red modeled-only regression now passes. It also exercises explicit
samples-off mode, proves the wash remains audibly nonzero near five seconds, and
proves both sampled and modeled paths terminate after note-off. All eleven
default-feature FX oracles and all ten modeled-only FX oracles pass, as do strict
clippy and the focused test on Rust 1.87.

The required render inventory compared release binaries from `origin/main`
`583d8d3` and this fix over all 124 catalog MIDIs at 11.025 kHz: all 124 were
byte-identical, with zero contamination. The scanner found no catalog MIDI that
sounds GM 96, so no album render was expected to move; the focused regression
proves the changed samples-off path is reached.

## Regression

`voices::tests::fx_o7_rain_96_real_recording_bed` clause (c) is the regression
test. Clauses (a) and (b) remain gated as genuinely sample-specific; clause (c)
remains active in every build because key-hold lifetime is the voice's contract,
not an asset property.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before: removing **only** the `synthetic_rain_alive` term from `Fx::is_alive` fails
`fx_o7_rain_96_real_recording_bed` with

```
96 rain (samples-off) died while the note was still held — the wash must sustain
```

which is the recorded symptom — GM 96 cut off while the key is still down — on the modeled
path, where the noise layer has no liveness term of its own.

Green after: passes on trunk, as does `fx_o2_rain_96_is_a_fused_aperiodic_wash`. The
modeled-only suite (614 tests, `--no-default-features`) is green, which is the configuration
where the synthetic wash is the only rain there is.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.
