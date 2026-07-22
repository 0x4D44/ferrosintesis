# MM-BUG-KILN-00039 — GM107 Koto has a ~13 dB low-register level explosion (pitch-dependent gain, no per-key compensation)

- **State:** Open
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the M-CAL
  instrument-audition review; measured pitch tilt, code-confirmed)

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
