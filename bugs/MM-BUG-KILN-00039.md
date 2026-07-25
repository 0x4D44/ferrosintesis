# MM-BUG-KILN-00039 — GM107 Koto has a ~13 dB low-register level explosion (pitch-dependent gain, no per-key compensation)

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL instrument-audition review; measured pitch tilt, code-confirmed) → Fixed (2026-07-23, Claude Opus 4.8; superseded by MM-BUG-KILN-00042's shared damper-law fix in `8e1da29` and the reference-matched plucked-family re-fit in `aadcd57`, which measured koto register tilt improving from 14.1× to 1.0×) → Closed (2026-07-25, independent verification by Codex GPT-5.6-Sol; current source uses the derived damper law and reference-matched koto t60, while the register-law, rendered-identity, and koto-family distinctness oracles all pass)

## Observation

GM107 (Koto) reads "slightly loud" in the per-program median, but the **low register is
conspicuously loud** — a pitch-dependent level explosion of ~13 dB across the range, which a
static `PROGRAM_TRIM_DB` entry cannot correct.

## Root cause / measurement

`KOTO` PluckPreset (`crates/ferrosintesis/src/voices.rs:3169`), t60 = 7.0 s long ring, has
**no per-key level compensation**; the Pluck / KsLoop key-gain over-weights the low register.
Measured on the calibration probe: ferro key48 = −27.1 dBm, key53 = −24.5 dBm vs ~−37.5 at
key68/73 — a ~13 dB tilt — while the SC-55 is flat within ~1 dB (~−30.5 across all keys). The
per-program median hides the tilt (it sits in the middle and discards the loud low notes).

## Fix direction

Add per-key (or per-frequency) level compensation to the koto so its output is register-flat
like the reference. Audit other long-ring plucks (shamisen, sitar, banjo) for the same tilt.
A flat PROGRAM_TRIM cannot fix a pitch-dependent gain — this is a model bug, not a calibration
input. Feeds the M-CAL v2 per-key envelope guard (a program with a >3 dB per-key spread is
guard-excluded from a static trim).

## Correction: the stated mechanism is wrong (2026-07-22, M-CAL v3 run)

**Do not implement this bug's proposed per-key level compensation.** The M-CAL v3 certified
derivation, independently cross-checked, shows the koto's register tilt is a *decay-rate*
symptom of the shared Karplus-Strong loss law now tracked as **MM-BUG-KILN-00042**, not a
missing per-key gain:

- KOTO's low `bright` (1900 Hz) against the in-loop damper's ~f^3 law predicts -203.5 dB/s at
  key 73 from the damper alone; measured early decay is -213 dB/s (within 5%). At key 48 the
  same term predicts only -2.4 dB/s.
- The koto is **not "too loud low"**: GM107 at key 48 (-21.0 dB/s) sits BETWEEN the two
  reference modules (SC-55 -17.3, S-YXG50 -26.2), and at key 53 it decays slower than both.
  It is **dead high** - b2 is already -90.3 dBm at key 73 - and that is what tilts the median
  a level-based reading sees.

A per-key gain curve would therefore compensate a symptom and bake the decay defect in
permanently, on top of a voice whose upper register has already stopped ringing. Fix 00042
(generalise `treble_hold_hz` beyond NYLON/STEEL), then re-measure GM107; this bug should close
or reduce to whatever residual tilt survives that fix.

## Verification (2026-07-25)

MM-BUG-KILN-00042 fixed the actual shared Karplus-Strong decay law and independently
recorded GM107's register tilt improving from 14.1× to 1.0×. The subsequent
reference-matched family pass shortened koto's authored `t60` from 7.0 to 4.1 seconds
without restoring the dead-high-register failure.

Independent verification on current trunk confirmed:

- `KOTO` inherits the derived `DamperHold` path and carries the reference-matched
  `t60: 4.1`.
- `voices::tests::ks_decay_law_holds_across_register`: passed.
- `voices::tests::damper_hold_preserves_instrument_identity`: passed.
- `voices::tests::sitar_shamisen_koto_have_distinct_pluck_presets`: passed.

No per-key gain compensation was added; the correction remains at the diagnosed decay-law
layer.

