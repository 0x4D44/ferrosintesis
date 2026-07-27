# pluck-attack — FluidR3 differential goldens

Dev-only tooling for the **natural pluck excitation redesign**
(`wrk_docs/2026.07.19 - HLD - natural pluck excitation redesign.md`, §5 oracle D).

`gen_fluidr3_golden.py` renders isolated plucked notes through **FluidSynth +
FluidR3_GM** as a *natural* reference synth and extracts five attack-side metrics.
It prints a paste-ready Rust `FLUIDR3_GOLDEN` const; that committed const is the
**hermetic** reference the Phase-2 D-oracle compares ferrosintesis against — **no
fluidsynth runs at test time**, so the test suite stays self-contained and
zero-dependency.

## Environment (pinned)

- **FluidSynth 2.5.5** (`fluidsynth --version`).
- **FluidR3_GM.sf2**, SHA256
  `74594e8f4250680adf590507a306655a299935343583256f3b722c48a1bc1cb0`
  (148,398,306 bytes). A different soundfont ⇒ different goldens; re-fingerprint
  before regenerating.
- Reverb **and** chorus are disabled (`-R 0 -C 0`) so the goldens are a DRY
  measurement of the sample's own attack/sustain, not the player's effects.

## Regenerate

Windows Python needs Windows-style paths (not Git-Bash `/c/…`):

```bash
FLUIDSYNTH="C:/tools/fluidsynth/fluidsynth-v2.5.5-win10-x64-cpp11/bin/fluidsynth.exe" \
FLUIDR3="C:/tools/fluidsynth/soundfonts/FluidR3_GM.sf2" \
python3 tools/pluck-attack/gen_fluidr3_golden.py
```

Paste the printed const over `FLUIDR3_GOLDEN` in
`crates/ferrosintesis/src/testutil.rs`. Stdlib-only; no third-party Python deps.

## Metrics (mirror the Rust `testutil` helpers)

Grid: GM programs {24 nylon, 25 steel, 32 ac.bass, 33 fing.bass, 45 pizz,
46 harp} × keys {40, 52, 64} × vels {60, 100}. Per note, after onset detection:

| field | definition |
|-------|------------|
| `att_sus` | RMS[0, max(15 ms, 1.5/f0)] ÷ RMS[100, 250] ms |
| `tilt_db_oct` | least-squares dB/oct over 48 log-probes 300–9000 Hz on the 20 ms onset |
| `crest` | peak ÷ RMS over the attack window |
| `flatness` | geo/arith DFT mag over 500–8000 Hz on the 20 ms onset |
| `e030_e100300` | RMS[0, 30 ms] ÷ RMS[100, 300] ms |

These deliberately track the Rust `att_sus_ratio` / `spectral_tilt_db_oct` /
`crest` / `flatness` definitions. A small cross-tool residue is unavoidable
(Python DFT-probe vs Rust 4096-FFT); the D-oracle bands are intentionally loose
(D1 ratio ∈ [0.95, 1.8], D2 tilt ±4 dB/oct, D3 energy ∈ [0.5×, 2.0×]) to absorb
it while still catching a real regression.

## Why a Rust const, not JSON

The HLD names a "committed JSON". ferrosintesis has **zero third-party code
dependencies** (no serde), so a JSON parser would mean either a new dep or a
hand-rolled parser — both worse than a type-checked Rust const that the compiler
validates. The const is the repo's established golden-fixture idiom (`GOLDEN`,
`HEAD_BASELINE`). Same intent (hermetic, regenerable, documented), better fit.

## Observed (HEAD, 2026.07.19) — the gap this redesign closes

FluidR3 att/sus is far gentler than ferrosintesis' bare model: steel 0.97–1.54
(ours 2.7–8.1), nylon 1.15–2.26 (ours 1.7–8.2), pizz **0.48–0.89** (ours 4.35–41).
Pizz below 1.0 is FluidR3's loop-flattening artifact (it sits *under* the physical
ring-down R_phys) — which is exactly why the P-band anchors on physics, not on
chasing these numbers.
