# MM-BUG-KILN-00044 — GM6 harpsichord's held body rises only +0.9 dB from v72 to v110 where both reference modules rise +6.6 / +8.3 dB — a ~7 dB velocity-response gap that is `vel_sense` 0.15 itself: physical realism vs GM convention, an ears/design call

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
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
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) from the M-CAL v3 certified/panel derivation runs; triaged and root-caused against the source and the raw measurement TSVs) → Fixed (2026-07-25, Claude Opus 5 (1M) @ xhigh in `d1245e9`; removed the stale GM6 exponent correction so the body rises monotonically, while Arthur accepted the remaining weak `vel_sense: 0.15` response after A/B listening) → Closed (2026-07-25, independent verification by Codex GPT-5.6-Sol; current source preserves the accepted physical-harpsichord exception, the positive sub-3 dB velocity span, and the no-compensation invariant, with all focused guards green)

## Narrowed (2026-07-25) — the inversion half is FIXED; only the design question remains

This bug originally carried two defects. **The inversion is gone.**

`VEL_LEVEL_EXP[6] = 1.500` — root-cause item 3 below, worth −1.837 dB over v72→v110 — has been
**deleted**, along with the reason it existed. Its comment justified it as compensation for the
LA layer "not inheriting that compression", i.e. for MM-BUG-KILN-00030; that bug is now fixed at
its own layer (`LaFx::vel_sense`, so the sampled onset applies the same `vel_sense` compression
the model does), leaving the compensation nothing to compensate. Measured at key 60:

| | v40 | v72 | v110 | v127 | span |
|---|---|---|---|---|---|
| body, before | −16.42 | −18.20 | −19.16 | −19.44 | **−3.02 dB** |
| body, after | −21.44 | −20.67 | −19.78 | −19.44 | **+2.00 dB** |

So the two claims in this record that rested on the inversion no longer hold:
- *"A composed crescendo on a GM6 channel renders flat, and marginally backwards"* — it now
  renders **forwards**, at the `vn²` law's predicted slope.
- *"fails the repo's own documented contract regardless … it responds negatively"* — it now
  responds positively. `velocity_law.rs`'s "GM6 must still respond to velocity, just weakly"
  passes on merit rather than on the wrong window.

Root-cause item 4 ("why no oracle caught it") is also addressed: the new derived guard
`velocity_law::corrected_programs_still_rise_with_velocity` fails on any program that carries a
`VEL_LEVEL_EXP` correction while rendering backwards. Verified adversarially against
`t[6] = 1.500`.

**What is left, and is now the whole of this bug:** the reference-fidelity gap. ferrosintesis
gives GM6 **+0.89 dB** over v72→v110 (was −0.96); the SC-55mkII gives +8.33 and the S-YXG50
+6.61. That residual is `vel_sense: 0.15` itself, exactly as root-cause item 1 says — and per
Arthur (2026-07-25, after A/B listening) **`vel_sense: 0.15` stays**: a real jack plectrum
displaces the string the same distance however hard the key falls, and physical realism wins
over GM convention here. This bug therefore remains open as the standing record of a *known,
deliberate* divergence from the reference panel, not as a defect to be silently fixed.

Anyone re-opening the question must still re-decide root-cause item 5's three guards together
(the GM6 square-law exclusion, the `< 3.0` contract, and the `<= 1.5` spread pin) — all three
pass unmodified today, and none was weakened to land the inversion fix.

## Observation

### As reported (verbatim)

> FINDING C - GM6 HARPSICHORD FAILS THE VELOCITY GUARD AT 9.6 dB.
> The ferro-vs-reference level difference for GM6 changes by 9.6 dB between velocity 72 and
> velocity 110 - i.e. a velocity-RESPONSE mismatch, not a level offset, so the static
> PROGRAM_TRIM_DB entry (currently +6.0 dB, the one documented plucked exception) cannot fix
> it.

### Symptom

ferrosintesis renders GM6 with **no usable velocity response in the sustained body**, and the
residual response is slightly **negative**. Both independent GM reference modules render it
with a near-textbook square-law rise.

Body level = median of the held BS.1770 momentary blocks b2..b8 within 40 dB of the note peak
(the M-CAL v3 metric). Median over the three shape-clean keys the SC-55 pairing uses (48, 53, 58):

| engine | v72 | v110 | v72 → v110 |
|---|---|---|---|
| **ferrosintesis** | −43.58 | −44.82 | **−1.24 dB** |
| Roland SC-55mkII | −62.07 | −53.74 | **+8.33 dB** |
| Yamaha S-YXG50 | −52.49 | −45.88 | **+6.61 dB** |
| square law `(v/127)²` | — | — | +7.37 dB |

`vel_guard = |ferro span − reference span|` = **9.57 dB** vs SC-55 (VEL_GUARD is 3.0), which is
the reported 9.6. The S-YXG50 pairing has a different clean-key set (48, 53, 58, 63) and gives
**6.3 dB** — reproduced exactly, both numbers.

The references are not merely "louder"; they are **uniformly** louder — v110 is a clean gain
copy of v72:

| per-key delta v72→v110 | 48 | 53 | 58 | 63 | 68 | 73 | spread |
|---|---|---|---|---|---|---|---|
| ferro | −1.24 | −2.00 | +1.94 | −2.76 | +1.59 | −4.03 | 6.0 dB |
| SC-55 | +8.21 | +8.33 | +8.28 | +8.33 | +8.59 | +8.47 | 0.4 dB |
| S-YXG50 | +6.62 | +6.61 | +6.63 | +6.14 | +6.67 | +6.57 | 0.5 dB |

ferro's mean is **−1.08 dB** and its sign flips key to key — there is no reproducible
velocity→level mapping in the body at all. The ±3 dB scatter is per-note jitter, not signal:
`t60` carries ±10% (`voices.rs:3891`), which at key 73 (t60 ≈ 1.75 s) is ±2.7 dB by block b8.
The jitter is **larger than the entire intended velocity signal**.

### Reproduce

From the M-CAL v3 raw measurements (`_cal/*.levels.tsv`, git-ignored, regenerated per the
recipe at the top of `wrk_docs/2026.07.22 - M-CAL v3 certified derivation report.md`):

```
python tools/instrument-balance/derive_trims.py _cal/ferro_full.levels.tsv \
    _cal/sc55_full.levels.tsv _cal/yxg_full.levels.tsv
```

GM6 reports `shape/short (3 keys: [63, 68, 73]); velocity 9.6dB` in the certified report
(line 44) and `sc55: … velocity 9.6dB | yxg: … velocity 6.3dB` in the panel report (line 204).

Code-only cross-check, no emulator needed — the arithmetic in the source predicts the
measurement to 0.06 dB (see Root cause).

### Expected vs actual

- **Expected:** GM6's held body rises ~+7 dB from v72 to v110, as it does on both references
  (+8.33 SC-55, +6.62 S-YXG50, within the panel's 3 dB agreement gate) and as `(v/127)²`
  predicts (+7.37). Two independent implementations agreeing this closely is the same standard
  `velocity_law.rs` already elevated to a specification when it fitted k=1.997 (SC-55) and
  1.981 (S-YXG50).
- **Actual:** −1.02 dB by construction, −1.08 dB measured. A composed crescendo on a GM6
  channel renders flat, and marginally *backwards*.

### This is a defect on the repo's own terms, not only against the panel

Whether a modelled harpsichord *should* be velocity-flat is a legitimate design argument
(a real jack plectrum displaces the string the same distance however hard the key falls) and
resolving it against two disagreeing references is an Arthur/ears call. But the current
behaviour fails the repo's own documented contract regardless: `velocity_law.rs:519` asserts
"GM6 must still respond to velocity, just weakly", and in the sustained body it does not — it
responds negatively. That assertion passes only because it is measured on the wrong window
(see Root cause §4).

## Root cause

Three sites compound; a fourth hides the result; a fifth will block the fix.

**1. `crates/ferrosintesis/src/voices.rs:2761`** — `HARPSICHORD.vel_sense = 0.15`.

**2. `crates/ferrosintesis/src/voices.rs:3873-3879`** — `Pluck::new` compresses velocity before
the square law:

```rust
let vn = 1.0 - p.vel_sense * (1.0 - vel as f32 / 127.0);
(vn, vn * vn)
```

v72 → vn 0.93504, v110 → vn 0.97992, so the excitation amplitude rises **+0.815 dB** where the
law wants +7.37. Across the whole range v1→v127 the model spans just 2.82 dB. `bright`
(`:3890`) and `pick_lp` (`:3892`) ride the same compressed `vn`, so the velocity→timbre law is
compressed identically.

**3. ~~`VEL_LEVEL_EXP[6] = 1.500`~~ — FIXED 2026-07-25, entry deleted (see "Narrowed" above).**
The analysis below remains correct and is kept as the record of why it was wrong; the arithmetic
it predicts no longer applies to the shipped synth. Historic text:

**3. `crates/ferrosintesis/src/voices.rs:11571`** — `VEL_LEVEL_EXP[6] = 1.500`, applied to the
COMPOSITE by `voices::make` (`:11683`) through `ScaledVoice::gain` (`:11612`) as
`(v/127)^(exp − 2)` = `(v/127)^-0.5`. Its stated job (comment at `:11568-11570`) is to pull the
LA sample layer's *uncompressed* rise back inside the "<3 dB contract". Cost over v72→v110:
**−1.837 dB**.

**Net on the held body** — where the sample is gone, because the `LaVoice` crossfade completes
at `fade_end = 0.20 s` (`LA_HARPSICHORD` at `voices.rs:8425`; sum-to-one crossfade at
`sampler.rs:2759-2762`), and block b2 starts at 200 ms:

```
+0.815  (vel_sense-compressed model)
−1.837  (VEL_LEVEL_EXP[6] = 1.5 composite compensation)
───────
−1.022 dB predicted     vs   −1.08 dB measured (6-key mean)
```

**4. Why no oracle caught it.** GM6 is excluded from the full square-law sweep
(`velocity_law.rs:379`), leaving `exempt_voices_keep_their_documented_velocity_behaviour`
(`velocity_law.rs:508-523`) as its only velocity guard. That test measures `melodic_level` =
the **max momentary block** of a 1.2 s render — the attack — and the LA sample onset there uses
`vel_gain = vel_amp(vel)`, the full square law (`sampler.rs:2715`). Measured attack deltas
v72→v110: +0.78, +0.47, +2.75, +2.39, +3.44, +3.70 dB (keys 48…73, rising with key as the
sample owns more of the peak). So `loud > soft` passes on the attack while the body inverts,
and the `< 3.0` bound is a *ceiling* that a near-zero span trivially satisfies. The guard has
no lower bound and never looks at the sustain.

**5. A second oracle actively pins the defect.**
`crates/ferrosintesis/src/voices.rs:14420-14423` (inside
`keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice`, `:14321`) asserts
`harpsi_hi / harpsi_lo <= 1.5` on the 0.05–0.35 s body RMS over v32→v116 — 3.5 dB, where both
references give ~+18–22 dB. Any GM-conformant fix fails it. It must be re-decided deliberately,
not quietly relaxed.

**Not fixable by the shipped trim.** `PROGRAM_TRIM_DB[6] = 6.0`
(`crates/ferrosintesis/src/engine.rs:661`, applied at `:683`) is a per-program constant on the
strip gain — velocity-independent by construction, exactly as the finding states.

## Fix

Not fixed. Direction, for whoever picks it up:

- The panel's implied `vel_sense` for GM6 is ≈1.0 — neither reference compresses GM6 at all.
  Raising `vel_sense` toward 1.0 and deleting `VEL_LEVEL_EXP[6]` puts GM6 on the same square law
  as every other program, and removes the only `vel_sense` + LA-layer pairing in the synth —
  which dissolves **MM-BUG-KILN-00030** as a side effect (read that bug first; do not fix it
  separately before this is decided).
- That is a re-voicing, so it needs ears plus the render-diff inventory. No committed album
  authors GM6 (`grep -i harpsichord albums/**/*.py` is empty), so the album-render blast radius
  is nil; the impact is on foreign GM files, which is exactly the "generic GM player" contract
  in CLAUDE.md.
- Three guards must be re-decided together, not weakened one at a time: the GM6 exclusion
  (`velocity_law.rs:379`), the `< 3.0` contract (`velocity_law.rs:508-523` — replace the
  attack-peak measurement with a **held-body** measurement whichever way the design goes), and
  the `<= 1.5` spread pin (`voices.rs:14420-14423`).
- If Arthur decides physical realism wins over GM convention, the flat body is still wrong:
  `velocity_law.rs:519` requires a positive response and the composite currently delivers a
  negative one. At minimum the compensation must stop out-running the model.

## Exit condition (rewritten 2026-07-25 — the inversion half is done)

This is now a **design question, not a defect to fix silently**. It closes one of two ways, and
either way needs Arthur and ears, not a unilateral agent change:

- **Accept the divergence (current standing decision, 2026-07-25).** `vel_sense: 0.15` stays;
  GM6 is deliberately near-velocity-flat because a real jack plectrum is, and we knowingly
  differ from both reference modules on this one program. Closing on this basis means recording
  it as a documented exception — ideally an oracle that PINS the ~7 dB divergence so it cannot
  drift unnoticed in either direction, the way `looped_recording_voices_keep_their_documented_
  velocity_behaviour` pins the bottle and bagpipe.
- **Adopt GM convention.** `vel_sense` → ~1.0, putting GM6 on the plain square law and matching
  the panel (`vel_guard` < 3.0 dB against both). That is a re-voicing: it needs a listening pass
  plus the render-diff inventory, and root-cause item 5's three guards must be re-decided
  **together** — the GM6 square-law exclusion (`velocity_law.rs`), the `< 3.0` contract, and the
  `<= 1.5` body-spread pin. Note the LA onset now inherits whatever `vel_sense` becomes, so this
  no longer requires touching the crossfade.

Superseded: the original exit condition also demanded the velocity guard move from the attack
peak to the held body with a lower bound. Partly moot — the composite and body now track each
other (+1.85 vs +2.00 dB span), so the attack-window measurement is no longer masking a
different body behaviour. Still worth doing on its own merits if this bug is picked up.

## Verification (2026-07-25)

Independent verification on current trunk confirmed:

- Arthur's standing A/B decision is recorded in the landed `d1245e9` fix: physical
  harpsichord behavior wins here, so `HARPSICHORD.vel_sense` remains `0.15`.
- `velocity_law::tests::corrected_programs_still_rise_with_velocity`: passed. GM6 has no
  `VEL_LEVEL_EXP` correction that can reintroduce the former inversion.
- `velocity_law::tests::exempt_voices_keep_their_documented_velocity_behaviour`: passed.
  The rendered GM6 response remains positive and below the documented 3 dB ceiling.
- `voices::tests::keyboard_voices_programs_4_7_do_not_use_acoustic_piano_voice`: passed.
  Its held-body ratio guard remains below 1.5, preserving the deliberately compressed
  harpsichord response.

The remaining reference-panel gap is therefore a documented product choice, not an
unresolved defect.

## Notes

- Verified against the raw measurement TSVs (`_cal/ferro_full.levels.tsv`,
  `_cal/sc55_full.levels.tsv`, `_cal/yxg_full.levels.tsv`). Both reported guard values (9.6 dB
  SC-55, 6.3 dB S-YXG50) reproduce exactly, including the differing clean-key sets the shape
  guard hands each pairing.
- The certified run's glue-inertness certificate covers GM6 (probe at CC7=50, master bus
  compressor proven inert), so the differential is linear where it was measured.
- Relationship to **MM-BUG-KILN-00030**: same voice, disjoint region and opposite premise. 00030
  is the sampled quill ONSET (first 200 ms) not tracking the compressed model; this is the model
  BODY after the crossfade has completed. 00030's exit condition preserves `vel_sense`; this bug
  questions it. Fixing this one dissolves that one.
- Relationship to **MM-BUG-KILN-00029**: different programs (GM42/43, GM4) and a different
  failure (non-monotonic turnover near v127 from waveguide instability / a tanh shaper). GM6 is
  not a turnover — it is a near-zero slope by construction.
- Relationship to **MM-BUG-KILN-00019**: that bug is static per-program level offsets;
  `PROGRAM_TRIM_DB` cannot express a velocity-response error.
- Secondary observation, not filed separately: GM6's per-note jitter (`pos` ±15% `voices.rs:3881`,
  `bright` ±8% `:3890`, `t60` ±10% `:3891`) produces ±3 dB of body-level scatter — larger than the
  0.8 dB of velocity signal the design intends. Whatever `vel_sense` ends up being, the jitter
  budget should be checked against it.
