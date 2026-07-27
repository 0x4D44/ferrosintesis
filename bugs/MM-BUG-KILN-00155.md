# MM-BUG-KILN-00155 — A modeled GM 24 nylon voice self-oscillates and diverges to 1.7e12, silently crushing the whole render

- **State:** Fixed
- **Priority:** Must
- **Severity:** High
- **Area:** voices / plucked (Karplus-Strong polarization coupling)
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised by claude-opus-5@high while regenerating the test-corpus renders) → Fixed (2026-07-27, claude-opus-5@high)

## Observation

Rendering the test corpus on trunk `59e5553` (ferrosintesis v0.21.56), a voice on channel 5 of
`test-corpus/reference-midi/mike-oldfield/04-incantations-part-iv-xg.mid` **self-oscillates**: its
amplitude grows exponentially for ~2.5 minutes until it reaches ~1.7e12. Loudness normalization then
scales the entire mix down to keep that peak under the true-peak ceiling, so the actual music becomes
inaudible. The render is destroyed, and nothing in the pipeline errors or warns.

### Repro (23 s)

```
ferrosintesis test-corpus/reference-midi/mike-oldfield/04-incantations-part-iv-xg.mid --solo 5 -o ch5.wav
```

Final line reports:

```
wrote ch5.wav (74.5 MB) in 22.9 s — 333 voices, peak 1705829728256.00, max polyphony 23
```

A sane peak here is order 0.1–3. Every other corpus file measured sits in that range (see blast radius).

### Impact, measured

Full-mix render of the same file, versus the render of the identical MIDI on the 2026-07-19 trunk:

| render | mean volume | max |
|---|---|---|
| 2026-07-19 trunk | −20.2 dB | −4.5 dB |
| trunk `59e5553` | **−39.9 dB** | −3.0 dB |

~20 dB of level lost. The encoded `.opus` falls from 123 kb/s to 27 kb/s — near-silence with one lone
full-scale spike. The MIDI is unchanged since 2026-07-17, so the input is not what changed.

### It is a modeled voice, not the sample layer

`--solo 5 --no-samples` reports a **bit-identical** peak of `1705829728256.00`. The LA sample layer,
the GM 24 crossfade seam (`4831afe`) and the B1 handoff work are therefore all excluded.

### It is the GM 24 nylon voice, and it is genuine self-oscillation

Channel 5 carries two programs. Bank/program events:

```
tick    409  CC0=0
tick    410  CC32=113
tick    411  PROGRAM 24      <- nylon guitar, runs to 160.82 s
tick  98112  CC0=0
tick  98112  CC32=3
tick  98112  PROGRAM 48      <- XG Slow Strings variation, at 160.82 s
```

`CC32=113` matches no `make_variation` arm, so program 24 dispatches to the plain modeled `NYLON`
`Pluck`. Per-second peak envelope of the soloed channel (16-bit WAV, values below ~1 LSB read as 1):

```
   0s..110s        1      (real signal is present but scaled ~1e12 down by normalization)
 115s        2
 120s        3
 125s        6
 130s       15
 135s       40
 140s      103
 145s      272
 150s      719
 155s     1903
 160s     8705   <- maximum, at 160.82 s
 165s       29
 170s        1
```

That is a constant **1.215×/second** exponential — the signature of a Karplus-Strong / waveguide loop
whose round-trip gain is ≥ 1, so the string never loses energy and instead compounds it. The growth
runs entirely inside the GM 24 section. The maximum lands at **exactly 160.82 s**, the instant of the
program change to 48 — the program change tears the runaway voice down, after which the channel decays
to nothing within ~3 s. Samples around the peak form a smooth high-amplitude sinusoid, not a click, so
this is a ringing oscillator being cut off rather than a discontinuity artefact.

### Blast radius: one file, but not one MIDI's fault

Eight other corpus files render sane peaks on the same binary — `02-moonlight-shadow` 1.87,
`03-ommadawn` 1.98, `06-amarok` 1.45, `07-amarok-happy` 1.98, `08-amarok-busy` 2.66,
`10-the-bell-steve-farrell` 1.72, `jean-michel-jarre/01-oxygene-part-4` 1.55,
`gabriel-knight/01-main-theme` 0.96. `01-tubular-bells-part-one` renders peak 0.98. The six-track
`demos/ferrosintesis_reference` album renders at healthy levels too.

So no in-repo album is affected today. That is **not** evidence the bug is minor: ferrosintesis is a
generic GM player, an unstable loop gain is reachable by any file that holds a nylon-guitar note long
enough, and the failure is silent and total when it does trigger.

## Fix

**Root cause: the K3 polarization coupling read its partner plane one sample stale.**

A plucked voice runs two coupled Karplus-Strong loops (horizontal and vertical string
polarizations). The design is a skew-symmetric rotation — the comment at the coupling site says
"energy sloshes between the planes … none is created" — and `coupled_loop_margin_holds` proves the
step matrix `[[a, k], [-k, a]]` is bounded, `|λ| = sqrt(a² + k²)`.

The shipped code did not implement that matrix. It coupled each plane to the other's **previous**
sample (`h_prev` / `v_prev`), and that one-sample lag adds a phase error of 2π/D per round trip,
where D is the loop delay in samples. D shrinks with pitch, so the error grows toward the top of the
register until the rotation stops being energy-neutral and starts generating. Below about key 92
(D ≳ 25 samples) it stays a contraction; above it, it does not.

The fix splits the loop step into `KsLoop::tick_read` / `tick_write`. The read half depends only on
the delay line, never on the input, so `Pluck::render` reads BOTH planes before writing EITHER and
couples each to the other's value at the same instant. That is the matrix the oracle already
assumes, so shipped code and proof now describe the same system. `h_prev` / `v_prev` are deleted.

**The lag was also feeding the e-bow, so two recalibrations follow.** Below the divergence
threshold the stale read was still mildly generative, and the sustainer had been living off that
free energy without anyone knowing. With the loop made an honest contraction the driver has to
supply it, so:

- `sus_headroom` now sizes the drive against the **pair** — `1 − sqrt(a² + k²)` — instead of the
  single loop's `1 − a`. A coupled pair sheds less per trip than either loop alone, so the old basis
  over-pushed by `k²/2a`; because that error scales with the deficit it landed differently at every
  pitch, which is what tilted the hold across the register (3.7 dB spread against a 3.0 dB bar).
- `SUS_K_OVER` 1.18 → 1.45 restores the settle time the lag used to supply. Key 64 now reaches its
  hold by ~5 s against ~4 s on trunk, inside the oracle's band, and the slur window spread comes
  back to 1.4 dB (trunk 2.4 dB, bar ~3 dB).

`sustain_holds_high_notes`, `sustain_survives_bends_and_slurs` and `driven_sustain_stays_distorted`
are the gates for that, and all three are green.

Why the loop gain itself was NOT the fix (my first hypothesis, refuted by measurement): `a` is
0.993–0.997 across the WHOLE register, essentially flat, while only keys ≥ 93 diverge — so `a` does
not discriminate. The guaranteed-stable coupling bound `k ≤ sqrt((1−a_h)(1−a_v))` evaluates to
0.0037–0.0105 everywhere, below the shipped `k = 0.02` even at keys that are demonstrably stable;
clamping to it would have gutted the polarization beat across every plucked note to fix a top-octave
defect. The lag was the defect, and removing it costs nothing elsewhere.

### Verification

- `held_plucked_notes_decay_at_every_key` (new, in `crates/ferrosintesis/src/voices.rs`) renders a
  held note for every plucked preset × key 21..=108 step 3 and requires a later window to be quieter
  than an earlier one. **Proven two-sided**: it FAILS on the pre-fix coupling (`NYLON key 96`, late/
  early ratio 2.205) and PASSES after (worst 0.67). It is deliberately RENDERED, because the
  closed-form `coupled_loop_margin_holds` reported `a² + k² ≈ 0.99` throughout — a closed form can
  only police the model it was derived from, and the lag was outside that model.
- Minimal repro, before → after: a single held GM 24 note, 40 s — key 93 `165 → 0.05`,
  key 96 `2,154,993 → 0.05`, key 100 `8,857 → 0.04`.
- The reported file, `04-incantations-part-iv-xg.mid`: channel-5 solo peak `1.7e12 → 0.07`; full mix
  peak `1.08e35 → 0.91`; full-mix level `mean −39.9 dB → −20.6 dB`, against the healthy 2026-07-19
  render's −20.2 dB.
- `cargo test --workspace --release`: **774 passed, 0 failed**. `cargo clippy --workspace
  --all-targets -- -D warnings`: clean, and clean again under `--no-default-features` (the
  modeled-only shipped configuration, which the new oracle also passes). `cargo fmt --all` applied.
- **Render-diff inventory over all 124 album MIDIs: 80 EXPECTED changed, 44 EXPECTED same,
  0 CONTAMINATION, 0 NOT REACHED.** Every track that plays a touched program moved and every track
  that plays none held still — no silent channel picked up DC, no RNG stream was re-rolled.
- The touched-program list handed to that inventory was derived by MEASUREMENT, not by reading the
  dispatch: one held note per GM program 0..127 rendered through both binaries and compared, which
  reported exactly `6, 15, 24..39, 45, 46, 104..107`. That set is the plucked family and nothing
  else — a hand-read list is the failure mode this repo keeps rediscovering, so the enumeration is
  taken from behaviour instead.
- Two baselines re-pinned, both NYLON-only and annotated where they live: the v2 signature envelope
  (`−16.290 → −15.011`; `rms_db` and `centroid_hz` stayed inside tolerance and the BASS control did
  not move at all) and three key-64 G7 canary cells (`+0.14 / +0.13 / +0.10 dB`). NYLON keys 40 and
  52 did not move, which is the delay-length dependence the diagnosis predicts — a uniform shift
  across the grid would have meant something else was wrong.

## Notes

**Verified by observation:** every number above — the 1.7e12 peak, its bit-identical reproduction under
`--no-samples`, the exponential envelope and its 1.215×/s rate, the peak landing exactly at the
160.82 s program change, the −39.9 vs −20.2 dB full-mix comparison, and all nine blast-radius peaks.

**Inference, not yet proven:**
- That the mechanism is specifically a Karplus-Strong loop gain ≥ 1. The exponential envelope and the
  plucked dispatch make it very likely, but the loop-gain value has not been read out of the code.
- That the runaway note begins early in the GM 24 section (~10–15 s). Extrapolating the constant
  1.215×/s rate backwards implies it, but growth below ~115 s sits under the 16-bit floor and was not
  measured directly. The specific triggering (key, velocity) pair is therefore **not yet identified**.

**Not done: the culprit commit was not bisected.** It is somewhere in `0cc8e7f..59e5553`
(2026-07-19 06:51 → 2026-07-26). Commit `4831afe`'s own rationale refers to "the plucked-family decay
re-fit" and "the now-longer-running `NYLON` model", which is the right neighbourhood to look first — a
decay re-fit that lengthens ring time is exactly the change that can push a loop gain past 1. Excluded
already: `3571509` (the XG Slow Strings variation) predates the healthy 2026-07-19 render, and
`d151e82` is test-only.

Found while regenerating the test-corpus renders on the current synth; the healthy predecessor is
preserved at `test-corpus/reference-midi-opus/mike-oldfield/2026.07.19 - 04-incantations-part-iv-xg.opus`,
and the defective render is tagged `Incantations Part IV [DEFECTIVE RENDER]` so it cannot be mistaken
for a good one.
