# MM-BUG-KILN-00042 — Karplus-Strong plucked decay is 2–12x too fast and steepens with register: the fixed-cutoff in-loop damper's f³ law plus the f^-0.55 t60 key-scale kill 22 GM programs' ring

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** synth
- **Raised:** 2026-07-22
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
- **State history:** Open (2026-07-22, raised from the M-CAL v3 certified full-128 derivation run; headline finding of `wrk_docs/2026.07.22 - M-CAL v3 certified derivation report.md`, verified independently against the raw measurement TSVs and the source)

## Observation

**Symptom.** ferrosintesis' plucked and struck notes decay far faster than both
independent reference synths, and the gap **grows with register**. 37 of 128 programs
fail the M-CAL v3 shape/short envelope guard; 22 of them are the Karplus-Strong
(`Pluck`) programs — GM 6, 7, 15, 24–32, 34–37, 45, 46, 104–107 — including **Guitar
8 of 8** and **Bass 5 of 6 modelled**.

Measured at velocity 110, peak-normalised BS.1770 momentary trajectory (b0..b8, 400 ms
blocks, 100 ms hop), note held 1.30 s:

| | ferro | SC-55mkII | S-YXG50 |
|---|---|---|---|
| GM24 nylon guitar, key 68, at b8 | **−42.2 dB** | −11.0 dB | −12.7 dB |
| GM32 acoustic bass, key 34, at b8 | **−18.3 dB** | −9.4 dB | −6.0 dB |
| GM112 tinkle bell, key 60, at b8 | **−30.4 dB** | −13.0 dB | −21.9 dB |

Decay rate (dB/s from the peak block to the last block within 40 dB of it), median over
the 22 `Pluck` programs:

| probe key | ferro | SC-55 | S-YXG50 |
|---|---|---|---|
| lowest | **−23.7** | −9.7 | −10.7 |
| highest | **−57.0** | −12.5 | −16.3 |

The two references agree with each other to a median 3.0 dB/s on this set, so **ferro is
the outlier, not a reference quirk**.

Per-key, the references are nearly flat across two octaves while ferro steepens
monotonically (v110, ferro / SC-55 = ratio):

```
GM24  k48 -23.7/-10.3=2.3x  k58 -40.3/-11.3=3.6x  k68 -52.8/-13.8=3.8x  k73  -94.1/-14.5= 6.5x
GM26  k48 -35.5/ -9.2=3.9x  k58 -47.4/-10.2=4.7x  k68 -78.8/-10.6=7.4x  k73 -119.9/-10.9=11.0x
GM32  k24 -14.6/-12.0=1.2x  k34 -22.9/-11.8=1.9x  k44 -39.3/-11.4=3.5x  k49  -49.2/-11.6= 4.2x
GM104 k48 -36.7/ -5.2=7.1x  k58 -48.5/ -6.7=7.2x  k68 -77.7/ -6.4=12.2x k73  -92.8/ -8.4=11.0x
GM107 k48 -24.0/-19.7=1.2x  k58 -31.6/-19.4=1.6x  k68 -90.6/-19.9=4.6x  k73 -247.1/-20.2=12.2x
```

**Expected.** A plucked GM voice's held-note envelope should track a GM reference's to
within the guard's 12 dB shape tolerance, as ferro's sustained families already do (the
sustained cohort's median shape_dev is 2.38 dB). Decay rate should be roughly flat in
register, as both references are.

**Actual.** shape_dev reaches 26–40 dB on the guitar/ethnic plucks; on GM28, 31, 45,
105, 106, 107 the note falls more than 40 dB below its own peak inside the 1.2 s window
and becomes unmetrable. Every affected program is guard-excluded from the level
calibration, so **no static `PROGRAM_TRIM_DB` entry can be derived for them at all** —
this is why an earlier level-only calibration produced wrong-signed trims for these
families.

**Reproduce.**

```
cargo build --release -p ferrosintesis-cli --example raw_dump --example calmeter
python tools/instrument-balance/mkprobe.py chunk{0..3}
./target/release/examples/raw_dump.exe _cal/probe_chunkN.mid _cal/ferro_chunkN.f32.wav
/c/apps/mdmidiemu.exe _cal/probe_chunkN.mid --wav _cal/sc55_chunkN.wav --synth sc55 --roms <sc55 roms>
/c/apps/mdmidiemu.exe _cal/probe_chunkN.mid --wav _cal/yxg_chunkN.wav  --synth syxg50 \
    --dll /d/language/mdsc55/mdmu80-syxg50-helper/assets/syxg50.dll
./target/release/examples/calmeter.exe _cal/ferro_chunkN.f32.wav _cal/plan_chunkN.tsv ferro
./target/release/examples/calmeter.exe _cal/sc55_chunkN.wav  _cal/plan_chunkN.tsv sc55
./target/release/examples/calmeter.exe _cal/yxg_chunkN.wav   _cal/plan_chunkN.tsv syxg50
python tools/instrument-balance/derive_trims.py _cal/ferro_full.levels.tsv \
    _cal/sc55_full.levels.tsv _cal/yxg_full.levels.tsv
```

Read the `shape/short` exclusions in the "guard-excluded" block, or peak-normalise
`b0..b8` per row of the three `_cal/*_full.levels.tsv` files directly.

## Root cause

`crates/ferrosintesis/src/voices.rs:3459` — the KS loop step
`self.dl.push(self.damp.process(s) * self.loop_gain + input + fb)` applies **two**
per-round-trip losses, both wrong in register, shared by every `Pluck` preset.

**1. The in-loop damper — dominant at high keys, dB/s grows as ~f³.**
`damp: OnePole::lowpass(bright, sr)` (`voices.rs:3329`) is a **fixed-cutoff** one-pole
inside the loop. Its magnitude at the fundamental (`dsp.rs:271`,
`OnePole::lowpass_mag`) is ≈ 1 − ½(f/fc)², so the per-trip loss grows as f², and the
loop makes f trips per second — total dB/s ∝ f³. The code already documents this cliff
(`voices.rs:2314-2324`: "the one-pole loss/trip ≈ ½(f/fc)² times f0 trips/s — the 'E6
dies in 100 ms' cliff"). Worked example, `KOTO` (`bright` 1900 Hz, opened to ~2031 Hz at
v110): the damper alone gives **2.4 dB/s at key 48** and **203.5 dB/s at key 73**.
Measured ferro rates at those keys: −24.0 and −247.1 dB/s.

**2. The t60 key-scale — dominant at low keys.** `voices.rs:3932`:

```rust
let t60 = (t60_base * (220.0 / f).powf(0.55)).clamp(0.25, 14.0) * (1.0 - 0.12 * wound);
```

feeding `loop_gain: 10f32.powf(-3.0 / (t60 * f))` (`voices.rs:3330`). Since
`loop_gain^f` per second is exactly `10^(-3/t60)`, the loop-gain term is precisely
−60/t60 dB/s — so the f^-0.55 scale shortens the ring by a further **2.7x** across the
probe's two octaves, on top of the damper.

**3. The correct mitigation exists but is authored on two presets.** `treble_hold_hz`
(`voices.rs:3923-3927`) grows `bright` as (f/anchor)^1.5 above the anchor, which holds
the damper's dB/s share flat instead of ~f³. It is set only on `NYLON`
(`voices.rs:2476`) and `STEEL` (`voices.rs:2576`), both at 500 Hz, and defaults to 0.0
(`voices.rs:2419`) for the other 20 `Pluck` presets. That predicts — and the data
confirms — that GM24/25 are the *mildest* guitars at the top key (6.5x / 4.3x) while the
un-held GM26/27 are the worst (11.0x / 6.2x). Even on NYLON/STEEL the anchor only bites
above 500 Hz, so most of the probe register is unprotected.

**4. Secondary terms on the same path.** The vertical polarization runs at
`course_t60: 0.42` (`voices.rs:2423`) — 2.4x faster than the horizontal, at a 0.26 mix —
pulling early energy down further. And several presets' `t60` baselines are short even
at the BOTTOM key: `SITAR` 2.1 (7.1x), `FRETLESS` 2.6 (5.1x), `CLAVINET` 0.78 (5.6x),
`JAZZ` 2.4 (3.9x). So the fix has a shared-law half and a per-preset-baseline half.

**Not the sampler.** `LA_GUITAR = (0.42, (0.05, 0.28))` (`voices.rs:8404`) and the
LaVoice contract "`[fade_end, ∞)`: the MODEL owns the sustain" (`sampler.rs:2547-2555`)
mean the sample layer is gone by 0.20–0.28 s, **before** the guard's body window
(b2..b8 = 0.2–1.2 s) opens. Fully-sampled GM24 and un-sampled GM26/27 fail identically,
which confirms it.

**Not a measurement artefact.** The probe holds each note 1.30 s against a 1.2 s window
(`tools/instrument-balance/mkprobe.py`), so no note-off / `rel_t60` enters the body;
CC7=50 keeps the master bus compressor certified inert; the metric is peak-normalised,
so it is anchor- and level-independent; and ferro's sustained families pass the same
guard at a 2.38 dB median shape_dev.

## Scope — what this bug is and is NOT

**IN (one shared root cause, 22 programs, all `Pluck`/`KsLoop`):** GM 6 harpsichord,
7 clavinet, 15 dulcimer, 24–31 guitars, 32/34/35/36/37 basses, 45 pizzicato, 46 harp,
104 sitar, 105 banjo, 106 shamisen, 107 koto.

**OUT — separate voices with their own envelope constants** (each needs its own
investigation; do NOT fold them in): GM2 `electric_grand_piano`, GM10 music box,
GM55 `orch_hit`, GM108 kalimba `bell()`, GM112 `tinkle_bell`, GM116 `taiko_drum`,
GM117 `melodic_tom`, GM118 `synth_drum`, GM123 `SfxBird`, GM127 `SfxGunshot`.
GM120 fret noise is already MM-BUG-KILN-00040.

**OUT — not "ferro decays too fast" at all** (they fail the guard for other reasons):
GM121 breath noise SUSTAINS +40 dB where both references are one-shots (opposite sign);
GM98 likewise; GM113 agogo fails because the *reference* dies (ref-dead on 5 keys);
GM115 woodblock is sub-hop on both engines — a meter-resolution exclusion, not a defect;
GM15 dulcimer's references disagree on direction (SC-55 +10.9, S-YXG50 −1.9).

## Fix direction

Two coupled halves, both ear-in-the-loop, both needing the render-diff inventory:

1. **Fix the shared register law.** Either author `treble_hold_hz` across the plucked
   presets with per-instrument anchors, or (better) make the loop damper's *cutoff track
   the fundamental* so the per-second HF loss is a designed constant rather than an f³
   accident. This is the change that flattens the ratio curve.
2. **Re-fit the per-preset `t60` baselines** against the reference panel at the bottom
   of each instrument's register, once the law no longer confounds the measurement.

Then re-run the M-CAL v3 derivation: the plucked families should pass the shape guard,
at which point a static `PROGRAM_TRIM_DB` becomes derivable for them for the first time.

A regression guard should assert the *ratio* directly: ferro's decay rate at the top of
a preset's register must be within a bounded multiple of its rate at the bottom (the
references sit near 1.3x; ferro is at 2.4–12x today).

## Notes

- Blocks the level-calibration programme for these families. MM-BUG-KILN-00019 (the
  0.70x-damped `PROGRAM_TRIM_DB`) is the *level* lane; this finding is the proof that
  the level lane cannot reach the plucked families at all — a scalar cannot reconcile a
  gap that grows ~30 dB over 900 ms.
- **Supersedes MM-BUG-KILN-00039** (GM107 koto ~13 dB low-register level explosion).
  That bug is the same mechanism observed as a level tilt on one program: the koto's low
  `bright` (1900 Hz) against the f³ damper law makes its high notes die, collapsing their
  body median. Its proposed fix (per-key level compensation) would paper over the decay
  defect with a gain curve. Recommend folding 00039 in, or re-pointing it at this root
  cause.
- **Overlaps MM-BUG-KILN-00037** (GM31 flageolet timbre) on the program, not the defect.
  GM31 is the worst decay offender in the set (35x) because `HARMONIC`'s t60 is scaled by
  the *retuned* loop frequency (`voices.rs:3911`, `f = note_f * harm`), so the flageolet
  takes both the shorter t60 and the higher damper loss of a note an octave/twelfth up.
  Fixing 00037's excitation thinning will not fix the decay.
- `scratchpad.md` (2026.07.18/19 entries) already records this mechanism as "the KS
  string over-damps" and marks it RESOLVED — but the resolution was scoped to GM24/25 via
  `treble_hold_hz`. It was never ledgered and never generalised.
- Distinct from MM-BUG-KILN-00029 (velocity-domain turnover in `BowedString` /
  `PickupShaper`) and MM-BUG-KILN-00030 (harpsichord onset/sustain crossfade ratio inside
  the first 200 ms).

## Independent review corrections (2026-07-22)

A second agent re-derived this from the raw TSVs and the source and CONFIRMED the root cause
and the fix layer. Five tightenings, none of which change the verdict:

1. **"The two references agree within 3.0 dB/s" is overstated at the top of the range.**
   Recomputed medians at key 73: SC-55 -12.1, S-YXG50 -18.3 dB/s - a 6.2 dB/s gap. Ferro
   (-46.0) is still 2.5-3.8x outside BOTH, so "ferro is the outlier" is untouched, but the
   correct claim is that the two references *bracket a far slower decay*, not that they agree
   tightly.
2. **The KOTO "measured -247 dB/s" does not reproduce** from `_cal/ferro_full.levels.tsv`
   under any obvious block pair; GM107 key 73 v110 gives -213 dB/s over b0->b2. This makes the
   corroboration TIGHTER, not weaker: the analytic -203.5 dB/s sits within 5% of -213.
3. **"GM24/25 are mildest because of `treble_hold_hz`" is only partly true.** Within the probe
   range only key 73 (587 Hz) clears the 500 Hz anchor, yet GM24 is already milder than GM26
   at key 48 (-25.1 vs -37.7) where the hold is inert. That gap is preset baselines (NYLON
   t60 3.8 / bright 3800, `voices.rs:2448-2449`, vs JAZZ 2.4 / 3600, `voices.rs:2607-2608`).
   The hold is still the right lever; it is not the explanation for that particular gap.
4. **The metric is BROADBAND, so the fundamental-only analytic is a LOWER bound.** Partial n
   sees loss proportional to n^2, so an RMS metric decays faster than the fundamental. For
   GM24 key 48 the two cited terms predict ~14.7 dB/s where ferro measures 25.1. Do NOT chase
   the remainder as a third mechanism - it is the broadband partials plus the vertical
   polarisation (`course_t60: 0.42`, mix 0.26, `voices.rs:2423`).
5. **MM-BUG-KILN-00039's proposed fix must be struck.** Its "add per-key level compensation to
   the koto" would bake this decay defect in permanently behind a gain curve. GM107 at key 48
   (-21.0 dB/s) sits BETWEEN the two references (SC-55 -17.3, S-YXG50 -26.2) and at key 53 is
   slower than both: the koto is not "too loud low", it is DEAD HIGH (b2 already -90.3 dBm at
   key 73), which is what tilts its median.

**Prior art (found by the reviewer, strengthens the fix):** `scratchpad.md` records this exact
mechanism being found and fixed for the GM24/25 guitars on 2026-07-19 - "the KS string
over-damps - RESOLVED by guitar block two's `treble_hold_hz` damper hold" - with the
generalisation to the rest of the family never done. The fix shape is therefore already proven
in-tree; this bug is largely about applying it to the other 20 presets.

**Scope note.** This entry absorbs a separately-triaged finding that the probe measures the
bass family partly below the K-weighting knee. That investigation converged on THIS root cause:
only probe keys 24-34 are knee-polluted, while keys 39/44/49 (78-139 Hz, where the RLB filter
is within ~1 dB of flat) still show the decline - so the slope is a real property of ferro's
plucked voices, not a measurement artefact.
