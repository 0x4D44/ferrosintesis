# MM-BUG-KILN-00007 — Sample playback (LA layer, drums, gong) pitch-shifts with 2-point linear interpolation: up-pitch aliasing and treble loss

- **State:** Closed
- **Priority:** Should
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Fixed (2026-07-18, `25ebc13`) → Closed (2026-07-18, independently verified by OpenAI Codex on `55c829e`)

## Observation

The LA sample layer is the synth's realism showpiece, yet its resampler is the
crudest interpolator in the codebase. `LoopVoice::render`
(`crates/ferrosintesis/src/sampler.rs:~1350`, `a + (b - a) * frac`), the
sampled-drum reader (`sampler.rs:~2002`) and the gong reader (`sampler.rs:~2120`)
all use 2-point linear interpolation, at repitch ratios up to 2.0
(`sampler.rs:~1329`).

Linear interpolation at step > 1 (pitching up) both attenuates HF and folds
interpolation images back as aliasing — exactly on the sampled brass/strings/
piano zones that are stretched upward. The proven cubic-Lagrange tap
(`dsp.rs:344`, `DelayLine::tap_cubic`, verified by `cubic_tap_retains_treble_ring`
at `dsp.rs:727`) is deliberately confined to the Karplus-Strong loop by an
explicit "buses keep the linear tap" decision (`dsp.rs:~337`).

## Fix

Fixed in `25ebc13` (branch `task/20260718-TSK-HUM-ferrosintesis-cubic-sample-interpolation`).

The KS loop's 4-point cubic-Lagrange kernel was factored into a shared
`dsp::cubic4(pm1, p0, p1, p2, fr)`, and `DelayLine::tap_cubic` refactored onto it
(bit-exact — the weight mapping was verified and the existing
`cubic_tap_retains_treble_ring` oracle still passes). All seven fractional sample
reads now route through `cubic4` instead of 2-point linear:

- `LoopVoice::render` (bagpipe drone) — **modulo-wrapped** neighbours `(j+n−1)%n …
  (j+2)%n`, preserving the seamless loop.
- `LaVoice::render` — the main seam read plus its two detuned side-reads
  (`pos2`/`pos3`), **edge-clamped** (`j.saturating_sub(1)`, `(j+2).min(n−1)`).
- `SampledDrum::render` (i16 kit), `GongOneShot::render`, `ClavinetSampled::render`
  — edge-clamped.

Linear interpolation at a fractional step both lowpasses the treble and folds
interpolation images back as aliasing; the effect is worst when a zone is pitched
up (step to ~2.0 across the LA zone splits), which is the normal case for the
sample layer. Cubic-Lagrange on the central interval is passive (|H| ≤ 1).

### Verification

- **New differential oracle** `dsp::cubic4_is_exact_and_beats_linear_on_treble`:
  `cubic4` is grid-exact, reconstructs a cubic exactly, and retains >1.04× the
  energy of linear on a pitched-up near-Nyquist tone.
- **Full lib suite green** — 488 passed, 0 failed. Every LA-seam oracle
  (`la_level_continuity`, per-family pitch-integrity, attack-sharpness) held; the
  tolerant `RenderSignature` freezes (±0.15 dB / ±2% / ±0.30 dB) absorbed the
  change — no golden re-capture needed.
- **clippy `-D warnings` clean; fmt applied.**
- **Render-diff** (baseline `origin/main` vs new release binary, 4 representative
  tracks — Slipstream/Hammerhead, Winter Guests, Bright Matter, opus4-8/First
  Light): `--no-samples` renders **bit-identical** on all four (the change is
  confined to the sample path — nothing in the modeled path moved), and samples-on
  renders **differ** on all four (expected reach; default-on timbre improvement).
  Confirms additive-only scoping with zero contamination.

Shipped code → one version bump owed at integration (not applied on the branch).
Second-eyes verification pending before `Closed` (two-eyes rule).

### Independent closure verification (2026-07-18, OpenAI Codex)

- Re-ran `dsp::tests::cubic4_is_exact_and_beats_linear_on_treble` on trunk build
  `55c829e`; the shared cubic kernel remains grid/cubic exact and clears the >1.04×
  high-frequency-energy differential over linear interpolation.
- Confirmed the original observation at pre-fix `9adbd1b`: all seven fractional
  sample reads used two-point linear interpolation (the existing summary said six,
  but its own enumeration contains seven: loop, LA main, two LA side reads, drum,
  gong, and clavinet). The fixed tree routes all seven through `dsp::cubic4`.
- The regression is genuinely red for the old implementation: substituting its
  linear expression for the cubic side makes the test's energy ratio exactly 1.0,
  below the required 1.04. The focused differential test passes with the fix.
- The independent workspace gate on the same build passed: `cargo test --workspace`,
  `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo fmt --all -- --check`.
  No unconverted sample reader or residual gap was found.

## Notes

- Touches the sampled render path → gate behind the full render-diff inventory
  (CLAUDE.md); this is a default-on timbre improvement, so expected diffs are on
  every album that uses a sampled program.
- The DSP audit rated this "the single biggest audible upgrade to the sampled
  instruments."
