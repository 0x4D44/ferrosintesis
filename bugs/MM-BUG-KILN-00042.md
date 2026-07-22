# MM-BUG-KILN-00042 — Karplus-Strong plucked decay is 2–12x too fast and steepens with register: the fixed-cutoff in-loop damper's f³ law plus the f^-0.55 t60 key-scale kill 22 GM programs' ring

- **State:** Fixed
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
- **State history:**
  - Open (2026-07-22, raised from the M-CAL v3 certified full-128 derivation run; headline finding of `wrk_docs/2026.07.22 - M-CAL v3 certified derivation report.md`, verified independently against the raw measurement TSVs and the source)
  - Fixed (2026-07-23, Claude Opus 4.8 (1M) — relative-budget `DamperHold` in `crates/ferrosintesis/src/voices.rs`; median register tilt 5.00x → 3.42x vs references 1.72–1.82x, koto 14.1x → 1.0x; both vetted rendered identity oracles green; new closed-form tilt oracle + rendered `damper_hold_preserves_instrument_identity`. Six of the 22 programs are `Off` opt-outs deferred to follow-ups: GM6/GM7 (piano family in flight), GM33/GM35 (KILN-00048), the DRIVE_LEAD driven-guitar CC0 alt-bank sustainer (KILN-00049). Top-register identity residual is KILN-00050. Fixing commit on branch `847510e` (pre-integration; awaits independent two-eyes closure). Suite 619 pass / 0 fail.)

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

## The GM29/30 driven-guitar `PROGRAM_TRIM_DB` lift is a workaround for THIS bug (2026-07-22)

An unintegrated branch, `task/20260719-TSK-HUM-driven-guitar-29-30-mix-presence-trim`
(commit `006fda6`, clean worktree, raised 3 days before this bug), sets
`PROGRAM_TRIM_DB[29] = [30] = +6.0` — the table's clamp maximum. Its stated root cause is
"the Drive stage was calibrated for SOLO loudness", evidenced by a distortion lead
rendering 8.2 dB band-RMS under a fingered bass on the Incantations Part IV reference
despite a higher CC7 (68 vs 44).

**That diagnosis is wrong, and the measurement it rests on is a symptom of this bug.**
GM29/30 route to `Pluck::new(&DRIVE, …)` (`voices.rs:12112`), and `DRIVE`
(`voices.rs:2622`) never sets `treble_hold_hz`, so it inherits the 0.0 default — the
unmitigated f³ damper law. Direct measurement on the standard 6-key probe (v110, note
held 1.30 s, peak-normalised b0..b8):

| | GM29 decay over 1.2 s | GM30 decay over 1.2 s |
|---|---|---|
| key 48 (C3) | 6.6 dB | 14.2 dB |
| key 63 (D#4) | 7.1 dB | 13.0 dB |
| key 68 (G#4) | 20.0 dB | 31.2 dB |
| key 73 (C#5) | 22.6 dB | 29.4 dB |
| **register spread (k73 − k48)** | **+15.9 dB** | **+15.2 dB** |

A lead line sits at keys 63–80; a fingered bass sits at keys 28–48. The lead loses
20–31 dB inside one second while the bass loses 14 — which *is* the reported ~8 dB
inversion. The defect is register-dependent decay, so a flat per-program scalar is the
wrong lever in kind, not merely in magnitude: it lifts the low register (already correct,
and the loudest row at −30.8 dB) by the same amount it lifts the top.

**Counterfactual — the correct fix delivers the missing level by itself.** Authoring
`treble_hold_hz` on `DRIVE` (experiment only, reverted; the anchor sweep is the useful
result):

| anchor | GM29 register spread | GM30 register spread |
|---|---|---|
| 0 (today) | +15.9 dB | +15.2 dB |
| 500 Hz (the NYLON/STEEL value) | +12.7 dB | +11.9 dB |
| **300 Hz** | **−0.1 dB** | **−1.9 dB** |
| 200 Hz | −0.1 dB | −1.9 dB |

500 Hz barely helps because the measured cliff sits between keys 63 (311 Hz) and 68
(415 Hz), below the anchor. **300 Hz flattens the register response almost exactly**, and
200 Hz buys no further tilt correction while beginning to over-hold the mid register
(GM29 key 63: 7.07 → 5.25 dB) — so 300 is a well-conditioned optimum for this preset, not
a fitted guess. Keys 48/53/58 are **bit-unchanged** at 300 Hz: the fix is surgical to the
broken register.

Integrated note loudness recovered by the 300 Hz fix alone, no trim:

```
GM29  k63 +0.19   k68 +4.50   k73 +6.42      lead register (63/68/73) mean +4.03 dB
GM30  k63 +0.41   k68 +5.50   k73 +7.14      low register  (48/53/58) mean +0.00 dB
```

So the fix returns **+6.4 / +7.1 dB exactly where the complaint was**, and 0 dB where it
was not. Landing both would put the lead register ~12 dB up — roughly 6 dB too loud — and
would raise the low register by 6 dB it never needed.

**Decision (2026-07-22, Arthur): DISCARD the +6 dB lift; do not integrate `006fda6`.**
The branch is left in place as the record of the original observation. The real complaint
it captured — the driven guitars sit under the mix — is now tracked here, and the M-CAL
panel independently agrees on the direction but a smaller magnitude (GM29 residual: SC-55
+4.3 dB, S-YXG50 +1.7 dB, spread 2.65 dB so the panel AGREES; GM30 has no reference datum
at all, both guards failed on all 6 keys). That residual was itself measured on the broken
decay, so it should shrink once the fix lands. **Re-derive after fixing, and only then ask
whether GM29/30 need any static trim.**

**Adopt 300 Hz as `DRIVE`'s anchor when fixing this bug**, and note that this contradicts
the "author `treble_hold_hz` at the NYLON/STEEL 500 Hz value" reading of Fix direction §1 —
the anchor is per-preset and must be fitted below each instrument's cliff.

**Open design question for Arthur, NOT part of this bug.** `DRIVE` sets `sustain: 0.0`
deliberately (round-3 U2, `voices.rs:2650-2656`): the default driven bank is a *decaying*
overdriven pluck, with the sustaining voice reserved for the CC0 alt bank `DRIVE_LEAD`
(`sustain: 0.6`). Both references render GM29/30 as sustaining, which is why ferro fails
the shape guard on 4/6 and 6/6 keys against both. Flattening the register tilt does not
resolve that divergence — it is a deliberate voicing choice against GM convention, and
changing it is a decision, not a defect fix.
