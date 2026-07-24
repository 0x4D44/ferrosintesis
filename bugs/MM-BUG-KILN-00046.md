# MM-BUG-KILN-00046 — GM48/49 string-section LA onset is not level-matched to the model it hands over to (−2.5 .. +7.6 dB, zone-dependent): "Slow Strings" peaks in its first 400 ms

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler
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
  - Open (2026-07-22, raised by Claude Opus 4.8 (1M) — triage of M-CAL v3 reference-panel finding E)
  - Fixed (2026-07-23, Claude Opus 4.8 (1M) — `strings_seam_gain(program, key, vel)` in `crates/ferrosintesis/src/voices.rs`: a per-velocity-LAYER (strsec_p/strsec_f), per-key taper on the LA wrap gain, each table the inverse of the measured wrapped/model fade-window mismatch (3-SEED GEOMEAN over GM48/49 — the metric swings ~0.3 per seed). Seam excess cut from +1..+6 dB to a [0.75,1.30] parity band across the whole active-wrap range (keys ~28-96, edges + velocity extremes covered); GM49's swell handed back to the model. Program-aware cap: GM48 takes full parity (incl. the modest boosts that fix the −2.5 dB under-level zones); GM49 (a swell patch) caps at 1.0 so the sample never speaks over the still-swelling model. Two new oracles: `la_strings_seam_level_parity` (fail-first: untapered ratio 2.0-2.1× at vel≥80 low keys) and `la_strings_onset_preserves_model_swell` (relative, non-vacuous). Independently reviewed by gpt-5.6-sol (REQUEST-CHANGES → all three points addressed: under-level half, oracle honesty, edge/velocity coverage). render-diff: 104 GM48/49 tracks changed, **0 contamination**, 0 not-reached. ferrosintesis suite green, clippy + fmt clean. Found while fixing: KILN-00053 (the strings MODEL's low-key non-swell — out of this sampler seam's scope). GM48/49 mutual distinctness (KILN-00024, EarPending) unchanged — needs an ear A/B. Fixing commit on this task branch; awaits independent two-eyes closure.)
  - Closed (2026-07-24 — independent two-eyes verification by **Codex gpt-5.6-sol**,
    cross-family, on a clean worktree at post-fix trunk. Verdict: CLOSE+SPLIT. Verdict
    recorded by Claude Opus 4.8 (1M), which did NOT perform the verification and did not
    author the fix. Evidence the verifier produced:
    (a) **Fails-before proven properly** — it transplanted ONLY the new tests onto the
    fix's parent `e23def1` and observed both fail there: `la_strings_seam_level_parity`
    GM48 key33 vel40 ratio **1.55**, outside the [0.75, 1.30] band; and
    `la_strings_onset_preserves_model_swell` GM49 key68 vel72 wrapped/model **0.42**,
    below the 0.70 floor. Both pass on the fixed tree.
    (b) **Root cause addressed at the right layer** — the single wrap gain is replaced by
    velocity-layer/key tapers at `crates/ferrosintesis/src/voices.rs:8717`, which is the
    `strsec_p`/`strsec_f` split and zone-dependent mismatch the bug describes.
    (c) **Assertions are substantive, not vacuous** — parity covers 40 program/key/velocity
    combinations; the swell guard requires ≥6 genuinely swelling model cases before it will
    accept its 0.70 minimum. A calibration sweep measured every key 28-96 at vel 72/110
    landing in **0.88-1.22** (−1.1 to +1.7 dB).
    **Split residual:** GM49 still lacks an absolute low-register swell — key48 vel110
    measured wrapped body/onset 0.81 against model-only 1.01. That is the strings MODEL's
    envelope, not this sampler seam, and it is **already tracked Open as
    MM-BUG-KILN-00053**, so no new ID was minted.)

## Observation

### The reported observation, verbatim

> FINDING E - THE METRIC DISAGREES WITH EAR-VETTED TRIMS ON SLOW-ATTACK FAMILIES.
> For programs carrying a nonzero (ear-decided) PROGRAM_TRIM_DB entry we compute
> residual = anchor - g, i.e. how far the program's RENDERED output sits from the reference
> frame. Near zero means metric and ear agree. These disagree materially:
>   GM56 / GM57 brass   -6.7 / -6.3 dB
>   GM67               -4.8 dB
>   GM48 / GM50 / GM51 ensembles  +3.7 .. +4.3 dB
> Two competing explanations and I do not know which: (a) the probe is a SINGLE HELD NOTE,
> which may bias slow-attack voices (the body window is b2..b8 = 200-1200 ms), or (b) those
> shipped trims are stale ear judgments.

(Source: the residual-oracle block of `wrk_docs/2026.07.22 - M-CAL v3 certified derivation
report.md`; also parked at `scratchpad.md:10`.)

### What the evidence actually shows

Neither (a) nor (b). The ensemble half of that observation is a **symptom of a real synth
defect**, and this bug is that defect. (The brass/reed half is a separate matter — see
Notes.)

**Symptom.** GM48 String Ensemble 1 and GM49 Slow Strings are 1–7.6 dB louder in their
first ~400 ms than in the sustain they settle into, and the size — and even the *sign* —
of that step depends on which sample zone the key lands in. On GM49 this inverts the
envelope of a patch whose whole identity is a swell: ferro's Slow Strings is loudest at
note-on and then falls, while both references rise.

**Expected.** `LaVoice`'s documented onset-ownership contract
(`crates/ferrosintesis/src/sampler.rs:2544-2557`) is that the crossfade keeps "the sum
level-true through the seam", so the sampled onset should hand over to the model at
matched level, at every key.

**Actual.** Measured on the certified M-CAL v3 probe (single held note, 1.30 s, CC7=50,
keys 48/53/58/63/68/73, velocities 72/110), the shipped render minus its own
`--no-samples` twin — which isolates the wrap exactly, since the two renders are the same
seed and the same model:

```
LA-onset excess = (samples-on) − (model-only), dB, per BS.1770 momentary block
prog  key  vel      b0      b1      b2      b3    b4..b8
  49   48  110   +7.57   +6.08   +1.84   -0.27     0.00
  49   58  110   +6.18   +4.48   +2.07   -0.17     0.00
  49   73  110   +5.83   +3.34   +0.68   -0.13     0.00
  49   63  110   +5.29   +3.11   +0.82   +0.26     0.00
  49   68   72   +6.54   +3.48   +1.09   -0.24     0.00
  49   58   72   -0.86   -0.74   -0.81   -0.24     0.00   <-- zone with the opposite sign
  48   63   72   +5.25   +4.45   +2.07   +0.32     0.00
  48   68   72   +4.87   +3.77   +1.89   -0.01     0.00
  48   58   72   -2.49   -1.18   -0.87   -0.41     0.00   <-- same zone, other program
```

Two things to read off it. First, the excess is **exactly 0.00 dB from b4 onward on all 24
notes** — the defect is entirely inside the 0.10–0.40 s fade window, i.e. it is the wrap,
not the model. Second, 20 of the 24 notes are positive at b0 and 15 exceed +3 dB, but key
58 is negative in both programs at both velocities: the mismatch is **signed and
zone-dependent, spread about 10 dB** around one hard-coded wrap gain.

The resulting envelope, GM49 at v110 (BS.1770 momentary blocks b0..b8, 400 ms/100 ms hop):

```
ferro   k48   -37.82 -38.63 -42.62 -44.62 -44.06 -43.50 -43.06 -43.47 -44.26   falls 6.8 dB
SC-55   k48   -54.60 -51.78 -49.63 -48.26 -47.23 -46.70 -46.71 -46.74 -47.11   rises 7.9 dB
```

Every one of the six probe keys shows the same shape on ferro; the SC-55 swells on all six.

**Knock-on: it corrupts the M-CAL reading of the ensemble family.** ferro's median
peak-to-body crest is 3.52 dB (GM48) and 3.13 dB (GM49), against 0.55–1.56 dB for the same
programs on both references, ≤1.61 dB for *every other* sustained ferro voice, and 0.92/0.97
dB for GM50/51 (same family, no sample layer). Re-running `derive_trims.evaluate` with the
note-peak statistic substituted for the body median collapses GM48's residual from +3.70 →
**+0.07** on the SC-55 and +2.81 → **+0.06** on the S-YXG50 — i.e. against both references
independently, ferro's GM48 sits exactly on the frame once the seam overshoot is included.
GM49 collapses partially (+5.96 → +2.14 on the SC-55). So the "metric says the ear is ~4 dB
low on ensembles" flag is the metric and the ear measuring two different parts of one voice
whose onset and body are 4–7 dB apart. **GM48/49 must not be re-trimmed on that residual;
the seam is what needs fixing.**

### Reproduce

Measurement path actually used (all artefacts already on disk, git-ignored):

```
# shipped render, and its model-only twin, both already produced by the M-CAL v3 run
./target/release/examples/calmeter.exe _cal/ferro_ns_chunk1.f32.wav _cal/plan_chunk1.tsv ferro > ns.levels.tsv
# then difference the b0..b8 columns against _cal/ferro_full.levels.tsv for programs 48,49
```

Unit-level repro (suggested, not yet run): render `voices::make(49, 48, 110, sr, seed,
true)` against `voices::make(49, 48, 110, sr, seed, false)` for 1.2 s and compare 100 ms
window RMS — the samples-on render should be ~7 dB hotter over 0–0.4 s and identical
afterwards; and on the samples-on render the 0–0.4 s mean should NOT exceed the 0.8–1.2 s
mean for a swell patch.

## Root cause

`crates/ferrosintesis/src/voices.rs:8464`

```rust
const LA_STRINGS: (f32, (f32, f32)) = (0.40, (0.10, 0.40));
```

applied at `crates/ferrosintesis/src/voices.rs:12292-12307`:

```rust
48..=49 => {
    let model = Box::new(strings(program, key, vel, sr, seed));
    if samples {
        let (gain, fade) = LA_STRINGS;
        crate::sampler::LaVoice::wrap(model, crate::sampler::strings_bank(vel), key, vel, sr, gain, fade)
    } else { model }
}
```

One scalar wrap gain (0.40) is applied to the whole `strings_bank` — both velocity layers
(`strsec_f` for vel ≥ 80, `strsec_p` below, `sampler.rs:1927`) and every zone within them —
while the sampled onset's level *relative to the `strings()` SawStack model*
(`voices.rs:6176-6207`) varies by roughly 10 dB across zones and keys. Under the
onset-ownership contract (`sampler.rs:2544-2557`) the sample owns `[0, 0.10 s)`, a
sum-to-one crossfade runs `[0.10, 0.40 s)`, and the model owns `[0.40 s, ∞)` — so a
per-zone gain error surfaces as a monotone level step through the seam rather than a click.
GM49 is hit hardest because its model attack is `vel_attack(0.45, vel)` (the slow section):
the sampled onset is at full level while the model is still 450 ms from arriving.

**Why no oracle caught it.** `la_level_continuity` (`sampler.rs:5379`) *does* carry the
three relevant fixtures — `(48, 48, "string-ens-low")`, `(48, 76, "string-ens-high")`,
`(49, 55, "slow-strings")` — but its contract, `assert_wrap_seam`, bounds only the **rate of
change**: the wrap may not add more than a 2.4× step between adjacent 100 ms windows beyond
the model's own envelope shape. A 5 dB mismatch spread across the 300 ms fade is ~1.2× per
window and passes comfortably. The complementary check, `assert_attack_is_peak`
(`sampler.rs:5533`), is applied only when the fixture is flagged `struck` — all three
strings rows are `struck: false` — so an *inverted* envelope on a swell patch is unguarded
in both directions.

This is the same defect class as **MM-REQ-KILN-00027** (steel-guitar high-key LA seam level
parity: "the sample speaks ~12 dB over the now-ringing model at the seam"), which is already
`Implemented` — including the pattern for the fix (per-key wrap-gain taper calibrated
against the model's actual output) and for the oracle (`la_steel_high_key_level_parity`, a
0.8–2.2× parity band across keys × velocities). That precedent is directly reusable here.

## Fix

<unfixed — raised only>

Direction, following MM-REQ-KILN-00027's precedent:

1. Measure the sampled onset's level against the `strings()` model per zone (do not
   hand-tune — calibrate against the model's actual output, as the steel work did).
2. Replace the single `LA_STRINGS` gain with a per-zone / per-key taper so the seam holds
   parity across the sampled range and across both velocity layers.
3. Extend `la_level_continuity` with a strings **level-parity** row modelled on
   `la_steel_high_key_level_parity` — a parity band, not a slope bound — covering at least
   keys 48/58/76 × velocities 72/110 so the key-58 sign inversion is pinned.
4. Additionally guard the swell direction on GM49: assert its 0.8–1.2 s mean is not *below*
   its 0–0.4 s mean, which is the property both references satisfy and ferro does not.
5. Re-run the M-CAL v3 derivation afterwards and confirm GM48's residual moves toward the
   +0.07 that the note-peak statistic already reports.

Render-diff expected on every ensemble-bearing album; it is a level change confined to the
first 400 ms of GM48/49 notes, so nothing outside those two programs should move.

## Notes

**What this bug does NOT cover** (so it is not mistaken for a fix to all of finding E):

- **GM56/57 brass and GM67 reed (residuals −6.3/−6.7/−4.8 dB).** Not this defect and not a
  probe artefact. I re-ran the derivation under six body-window definitions (b2..b8 shipped,
  b2..b4, b6..b8, b8-only, whole note, note-peak); GM56/57's residual moves at most 0.9 dB
  across all six, and both independent references agree within the 3 dB panel gate. Their
  peak-to-body crest is 0.04/0.07 dB — dead flat, no onset artefact to blame. So for any
  note held past ~400 ms ferro's solo brass really does sit 3.5–6.7 dB above the reference
  frame with the −6 dB trim already applied. Note the structural blocker: GM56/57/58 are
  pinned at exactly −6.0 dB, which is `derive_trims.CLAMP`, so the implied −12.3/−12.7 dB
  can never be expressed as a trim — it is a voice-level question or an accepted deviation.
  Belongs with **MM-BUG-KILN-00019**, not here. One caveat for whoever picks it up: ferro's
  GM56 takes ~300 ms to reach plateau (b0 is 3.8 dB down) where the SC-55 is at full in b0,
  so on short articulated notes the gap is smaller than the held-note metric says.

- **GM50/51 (+4.3/+3.8 dB).** No metric claim exists. The finding quoted only the SC-55
  column; on the panel the two references disagree by 5.06 and 6.42 dB — over the 3 dB gate
  — and the panel report already routes both to "NO CONSENSUS: ears decide". They also carry
  no sample layer (`sampled=0` on every probe note; they are the `with_chorus` string-machine
  voices, `voices.rs:6217`) and their crest is a normal 0.92/0.97 dB, so this fix cannot
  touch them.

**Relationship to other ledger entries:**

- **MM-BUG-KILN-00030** — same class (LA onset vs model level), different voice and
  mechanism: there the mismatch is velocity-dependent on the one `vel_sense` + LA voice;
  here it is a flat, zone-dependent wrap-gain miscalibration. Both point at the same missing
  contract (the LA onset must land on the model's actual level), so whoever fixes one should
  read the other.
- **MM-BUG-KILN-00024** — same programs, orthogonal axis (48/49 mutual *distinctness*, not
  level). Sequencing note only: this fix changes both onsets, so take 00024's A/B
  adjudication afterwards.
- **MM-REQ-KILN-00027** — the solved precedent; reuse its calibration and oracle shape.

**Provenance.** Raised while triaging finding E of the M-CAL v3 reference-panel run
(`wrk_docs/2026.07.22 - M-CAL v3 reference-panel derivation report.md`,
`wrk_docs/2026.07.22 - M-CAL v3 certified derivation report.md`). The finding itself is
parked at `scratchpad.md:10`; that entry can be closed out by pointing at this bug for the
ensemble half and at MM-BUG-KILN-00019 for the brass/reed half.