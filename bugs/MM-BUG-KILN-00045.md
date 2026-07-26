# MM-BUG-KILN-00045 — Bass family (GM 32–39) spans 21–25 dB internally where both reference synths span ~9 dB: the plucked basses' held body collapses while SynthBass 38 holds flat and hot

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** synth
- **Raised:** 2026-07-22
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260726T213802Z-p9812-n009629600-c2
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00045-run-fix-20260726T213802Z-p9812-n009629600-c2
- **Owner base:** 964ed7a1a92945e9d2f334eef9df99a014b36741
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T21:38:02Z
- **Owner until:** 2026-07-26T22:33:24Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) from the M-CAL v3 certified reference-panel run; measured against two independent references, code-confirmed)
  → Blocked (2026-07-24, Claude Opus 4.8 (1M) during an autonomous fixing pass. **Needs
  Arthur's listening call** — see "Why this is Blocked". Not a judgement on the bug, which
  is well-evidenced and still real; it cannot be finished unattended because the target
  numbers are not derivable.)
  → Open (2026-07-26, unblocked by Arthur. Preserve the upright/fingered articulation
  contrast while constraining the held-level family spread to about 9 dB; keep GM38
  Synth Bass 1 moderately prominent rather than matching the quieter Roland reference.
  Re-measure after the closed KILN-00042 decay-law fix, then implement and validate this
  direction with the within-family oracle, render-diff inventory, and listening candidates.)

## Observation

**Symptom.** ferrosintesis places its eight bass programs more than twice as far apart from
each other as either reference synth does. Measuring each engine against ITS OWN
128-program median (so absolute gain differences cancel), the within-family spread over
GM 32–39 is:

| engine | spread over GM 32–39 | spread excl. GM37 |
|---|---|---|
| **ferro** | **25.02 dB** | **20.91 dB** |
| Roland SC-55mkII | 8.88 dB | 8.88 dB |
| Yamaha S-YXG50 | 9.21 dB | 9.21 dB |

The two references were chosen because their patch quirks are uncorrelated (different
vendor, era and synthesis). They agree with each other here, so ferro is the outlier.

Per program, in each engine's own balance:

| GM | voice | ferro int_F | SC-55 | S-YXG50 | ferro vs SC-55 | ferro vs YXG |
|---|---|---|---|---|---|---|
| 32 | acoustic bass | −12.01 | −1.41 | +0.59 | **−10.60** | **−12.60** |
| 33 | fingered electric | +2.69 | +0.01 | +2.28 | +2.68 | +0.41 |
| 34 | picked electric | −11.41 | +0.70 | +3.20 | **−12.11** | **−14.61** |
| 35 | fretless | −6.01 | +3.62 | +2.57 | **−9.63** | **−8.58** |
| 36 | slap 1 | −10.29 | −3.71 | −3.12 | **−6.58** | **−7.17** |
| 37 | slap 2 | −16.13 | −1.40 | −0.28 | **−14.73** | **−15.85** |
| 38 | synth bass 1 | **+8.89** | −5.26 | +3.98 | **+14.15** | **+4.91** |
| 39 | synth bass 2 | +3.59 | −1.18 | +6.09 | +4.77 | −2.50 |

Both references agree on the **sign** for every member: GM 32/34/35/36/37 are 6.6–15.9 dB
too quiet in ferro's own balance, GM38 is 4.9–14.2 dB too loud, and only GM33 and GM39
land near correct. The sharpest single instance: **ferro puts GM32 14.70 dB below GM33;
the SC-55 separates its own by 1.42 dB and the S-YXG50 by 1.69 dB.**

**Expected.** A generic GM player's bass family should hold together within a few dB, as
both references do — swapping GM32 for GM38 in a foreign MIDI file should not move the
bass by ~21 dB.

**Actual.** It moves by 20.9 dB (25.0 dB if GM37 is included).

**Repro.**

    python tools/instrument-balance/mkprobe.py chunkN
    ./target/release/examples/raw_dump _cal/probe_chunkN.mid _cal/ferro_chunkN.f32.wav
    ./target/release/examples/calmeter.exe _cal/ferro_chunkN.f32.wav _cal/plan_chunkN.tsv ferro
    # references
    /c/apps/mdmidiemu.exe _cal/probe_chunkN.mid --wav _cal/sc55_chunkN.wav --synth sc55mk2
    /c/apps/mdmidiemu.exe _cal/probe_chunkN.mid --wav _cal/yxg_chunkN.wav --synth syxg50 \
        --dll /d/language/mdsc55/mdmu80-syxg50-helper/assets/syxg50.dll
    python tools/instrument-balance/derive_trims.py _cal/ferro_full.levels.tsv \
        _cal/sc55_full.levels.tsv _cal/yxg_full.levels.tsv

Then read the `int_F` column for GM 32–39, and compute the same self-referential
placement on each reference table (`prog_body(p) − median over all programs`).

**Measurement is clean.** 6 keys (24, 29, 34, 39, 44, 49) x 2 velocities (72, 110), every
note `sounded` on all three engines; the probe holds each note 1.30 s against a 1.2 s
analysis window, so the whole b0..b8 trajectory is key-down (no release artifact);
`glue_ok = 1` on every bass note (the master bus compressor is proven inert); raw
un-normalized renders; and `int_F`/`int_S` are each self-referential, so the reference
DLLs' absolute gains cancel.

## Root cause

Two independent mechanisms, neither reconciled against the other, because nothing in
ferrosintesis compares programs **within** a family.

**(1) Sustain — the dominant term.** Six of the eight bass programs are Karplus-Strong
`Pluck` voices whose held body decays away inside the window; GM 38/39 are `SynthBass`, an
ADSR voice that *holds*. `SynthBass::new` sets `amp_env: Adsr::new(0.004, 0.18, 0.75,
0.08, sr)` — sustain 0.75 held indefinitely — with `amp: 0.62 * vel_amp(vel)`
(`crates/ferrosintesis/src/voices.rs:4633` and `:4639`). Measured peak → held-body drop
over the probe window:

| GM | ferro | SC-55 | S-YXG50 |
|---|---|---|---|
| 32 | 11.37 | 6.10 | 3.82 |
| 33 | 2.17 | 3.28 | 2.60 |
| 34 | 9.03 | 2.58 | 4.29 |
| 35 | 6.73 | 0.34 | 1.42 |
| 36 | 13.09 | 3.22 | 4.09 |
| 37 | **18.48** | 2.30 | 1.34 |
| 38 | **−0.30** | 6.66 | 2.57 |
| 39 | 2.38 | 3.12 | −0.08 |

Both references stay inside 0.3–6.7 dB for every member; ferro ranges −0.3 to 18.5. The
`Pluck` presets' `t60` values were each authored in isolation and never cross-checked:
UPRIGHT 1.8 s (`voices.rs:2966`), SLAP_POP 1.8 (`:2923`), FRETLESS 2.6 (`:2868`), SLAP 2.8
(`:2897`), BASS 3.2 (`:2826`), PICK 3.2 (`:2940`).

**(2) Steady low-end gain — the secondary term, and why GM33 alone sits right.** `BASS`
(GM33) carries `sub: 0.72` (`voices.rs:2843`) and `kick: 3.9` (`voices.rs:2844`), a strong
steady fundamental added in the 2026.07 "muffled flatwound" re-voicing. Every sibling has
`sub` an order of magnitude smaller: UPRIGHT 0.15 (`:2976`), PICK 0.16 (`:2949`), SLAP
0.15 (`:2906`), SLAP_POP 0.08 (`:2924`), FRETLESS 0.26 (`:2877`). Hence the 14.70 dB
GM32→GM33 step against the references' ~1.5 dB.

**(3) Why it is stuck.** `PROGRAM_TRIM_DB[32..=39]` is all `0.0`
(`crates/ferrosintesis/src/engine.rs:665`), and the M-CAL pipeline structurally cannot
reach the family: `tools/instrument-balance/derive_trims.py:163` classifies Bass as
`"percussive"` (trimmable), but the envelope guards exclude GM 32, 33, 34, 35, 36, 37 and
39 on shape/short or pitch-tilt on at least one reference, and GM38 fails the
panel-agreement gate (7.63 dB reference disagreement). **Zero** bass programs are
auto-shippable. And a static per-program trim could not fix mechanism (1) in any case —
that is a decay-shape mismatch, not a gain error.

**The gain term is not explained away by the decay artifact.** The peak-only cross-check
is envelope-independent, and ferro's bass **peaks** still span 10.97 dB against 5.17
(SC-55) and 6.52 (S-YXG50) — about twice either reference. Decomposed: GM 36/37's peaks
are fine or hot and their *bodies* collapse (pure decay defect); GM 32/34 are down ~5 dB
at the peak *and* decay too fast (both terms); GM38 is ~7 dB hot at the peak *and* never
decays (hot everywhere).

## Fix direction

Ears-in-the-loop, and it must land with a render-diff inventory (this touches `voices.rs`
so every album with a bass part will move).

1. **Cross-calibrate the family against itself, not just against a reference.** The
   missing artefact is a *within-family* oracle: no test asserts that GM 32–39 hold
   together in level. Add one (a family-spread bound derived from the reference panel,
   e.g. "no two bass programs differ by more than ~9 dB at equal key/velocity on a held
   body") — that is the durable guard, and it generalises to every other family.
2. **Lengthen the plucked basses' effective sustain** toward the references. Both
   references hold a bass note far longer than ferro does (SC-55 GM34 loses 3.6 dB over
   1.2 s where ferro loses 15 dB). Note the honest tension: UPRIGHT's short `t60` and
   BASS's flatwound voicing are **authored** choices (`voices.rs:2966`, `:2822` comments),
   so this needs Arthur's ear, not a blind number change.
3. **Bring GM38's `SynthBass` down and/or give its ADSR a decay** so a held synth bass
   does not sit +8.9 dB in ferro's own balance where both references put theirs at or
   below their median. Magnitude is a listening call — the panel disagrees on how hot it
   is (SC-55 implies −13.3, S-YXG50 −5.6).
4. Equalise the steady `sub`/`kick` weight across the plucked basses, or accept GM33's
   weight as the family target and lift the others toward it.

`PROGRAM_TRIM_DB` is the wrong lever for all of this — it is a static per-program gain and
the dominant term is a decay-shape mismatch.

## Why this is Blocked (2026-07-24)

Blocked on **Arthur's ear**, not on analysis. Every one of the four fix items resolves to
a judgement this bug's own evidence says cannot be derived:

- **The target magnitude is not derivable from the panel.** The two references disagree on
  GM38 by 9 dB (SC-55 implies −13.3, S-YXG50 −5.6), and this entry already warns "do not
  treat the SC-55's −13.3 dB implied trim as the target". There is no number to compute.
- **Two of the offending values are authored choices, not accidents.** UPRIGHT's short
  `t60` and BASS's flatwound voicing are deliberate (`voices.rs:2966`, `:2822`), and the
  Fix direction says so: "this needs Arthur's ear, not a blind number change".
- **An existing oracle pins the disparity.** `bass_articulations_distinct`
  (`voices.rs:17547`) asserts `UPRIGHT.t60 < BASS.t60`. Any fix must consciously reconcile
  with it — a decision about intended voicing, not a mechanical edit.
- It touches `voices.rs`, so it moves every album with a bass part, and the fix direction
  requires a full render-diff inventory plus listening.

**What unblocks it, in order:**

1. **The prerequisite is now clear.** This entry says "fix MM-BUG-KILN-00042 first, then
   re-measure" — and **00042 is Closed** as of 2026-07-24. So the next concrete step is a
   re-measure, which is unattended-doable: the reference-panel tooling is present on KILN
   (`/c/apps/mdmidiemu.exe`, `mdsc55/mdmu80-syxg50-helper/assets/syxg50.dll`,
   `tools/instrument-balance/`). Re-run the Repro section and restate the residual.
2. **Then Arthur decides** the family target: how hot GM38 should sit, and whether
   UPRIGHT/BASS keep their authored decay contrast.

### Arthur's decision (2026-07-26)

Arthur approved the recommended calibration direction:

- Preserve the audible articulation difference: upright bass should remain shorter-lived
  than fingered bass.
- Constrain the held-level spread across GM 32–39 to about 9 dB.
- Keep GM38 Synth Bass 1 moderately prominent rather than targeting the quieter Roland
  reference.

This supplies the missing listening judgement. The bug is Open for an autonomous fixer to
re-measure the post-KILN-00042 tree and implement that direction.

Item 1 of the Fix direction — the **within-family spread oracle** — is the durable,
generalisable piece and needs no ear. It cannot land alone, though: written honestly it
fails on today's tree, and a knowingly-red test is not a landable change. It should land
together with whatever calibration Arthur signs off.

## Notes

- **Not a duplicate of MM-BUG-KILN-00016** (Open, same family). 00016 is the missing
  sampled *onset* — an attack-timbre defect whose only open remainder is the GM 36/37 slap
  onset. This is *level and sustain*. The LA onset wrap covers 0.05–0.35 s
  (`LA_EBASS`/`LA_PIZZBASS`, `voices.rs:8333`/`:8336`) and cannot move the b2..b8 held
  body, so landing 00016's slap onset would leave GM 36/37 exactly as far out of family as
  they are now. Confirmed empirically: GM 32–35 already carry the sample layer
  (`sampled = 1` in the TSV) and are still 8.6–14.6 dB under both references.
- **Not a duplicate of MM-BUG-KILN-00019** (Open). 00019 is the 0.70x damping leaving
  ~1–2.5 dB residuals in the families that *did* get a trim. Bass was never trimmed
  (`engine.rs:665` is all 0.0) and the discrepancy here is 21–25 dB.
- **Partial overlap with MM-BUG-KILN-00039** on a sub-observation only: the bass family
  also shows per-**key** pitch tilt (GM33 7.5/7.9 dB, GM34 7.8/7.0, GM37 12.3/17.4, GM39
  6.3/12.0 on sc55/yxg). That is 00039's defect class and its fix direction already asks
  for an audit of other long-ring plucks. The per-**program** family-spread claim filed
  here is new.
- **The GM38 magnitude is contested by the panel's own gate.** Both references agree ferro's
  GM38 is hot, but by 5–14 dB, and the S-YXG50 puts its own GM38 at +3.98 (above its
  median) where the SC-55 puts its own at −5.26. Do not treat the SC-55's −13.3 dB implied
  trim as the target.
- Evidence: `wrk_docs/2026.07.22 - M-CAL v3 reference-panel derivation report.md`
  (lines 72–79 for `int_F`, 217–224 for the guard exclusions); raw tables
  `_cal/ferro_full.levels.tsv`, `_cal/sc55_full.levels.tsv`, `_cal/yxg_full.levels.tsv`
  (git-ignored).

## Independent review corrections (2026-07-22)

A second agent reproduced the measurement exactly and confirmed this is REAL and NEW, but
found the root cause only half right. **Mechanism (1), SUSTAIN, is correct and well-evidenced**
(`SynthBass::new` sets `amp_env: Adsr::new(0.004, 0.18, 0.75, 0.08, sr)`, `voices.rs:4633`,
and GM38/39 dispatch to it at `voices.rs:12152`, while 32/34/35/36/37 are `Pluck`). Measured
peak->body drop: ferro GM37 18.23 dB, GM36 13.37, GM32 10.50, GM34 7.96, GM35 7.13, GM33 4.13,
GM39 1.41, GM38 0.87; SC-55 1.03-7.20, S-YXG50 1.40-4.66.

**Mechanism (2) as written is wrong - do not act on it:**

1. **`kick: 3.9` (`voices.rs:2844`) CANNOT drive this symptom.** It is a one-shot `Burst` with
   `KICK_T60_S = 0.075` (`voices.rs:3476`), so by b2 (t = 0.2 s) it is ~160 dB down, and int_F
   is the median of b2..b8 only. It is also not censoring tail blocks via the presence test
   (GM33 key 34 v110 runs -32.90 .. -40.22, every block far inside peak-40 dB). A fixer acting
   on this would spend effort on a 75 ms transient that cannot move the measured number.
2. **The dominant held-body term is MISSING:** BASS's body peak-EQ
   `body: &[(50.0, 0.8, 9.0), (100.0, 1.0, 6.2), (320.0, 0.9, 1.2)]` (`voices.rs:2839`;
   fields are freq/q/gain-dB) applies +9.0 dB at 50 Hz and +6.2 dB at 100 Hz to the whole
   ringing string - against FRETLESS +4.0/+2.2, SLAP +3.0, PICK +3.5, UPRIGHT +4.5/+3.5. That
   is +3 to +6 dB of extra body gain sitting exactly where int_F reads. (`sub: 0.72` is
   correctly cited but is not "steady": it decays at `t60 * 0.8`, `voices.rs:4054`.)
3. **"Nothing compares programs WITHIN a family" is false.** `bass_articulations_distinct`
   (`voices.rs:17547`) does exactly that, asserting `cent(&PICK) > 1.1 * cent(&BASS)` and
   `UPRIGHT.t60 < BASS.t60` - so the GM32-vs-GM33 decay disparity is not an unchecked accident,
   it is PINNED BY A TEST. Any fix must reconcile with that oracle rather than silently
   contradict it.

**Relationship to MM-BUG-KILN-00042:** the plucked half of this spread is a symptom of the
shared Karplus-Strong decay law tracked there. Fix 00042 first, then re-measure - this entry
covers what remains, principally the SynthBass 38/39 vs plucked-bass level mismatch and the
family-level reconciliation.
