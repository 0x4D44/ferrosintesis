# MM-BUG-KILN-00040 — GM120 Guitar Fret Noise is pinned near-silent (~18 dB under the SC-55 reference)

- **State:** Open
- **Priority:** Could
- **Severity:** Low
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
  instrument-audition review; effectively inaudible vs SC-55, code-confirmed)

## Observation

GM120 (Guitar Fret Noise) is effectively **silent** in the reference audition — measured
~18 dB under the SC-55 for the same event. `CLAUDE.md` documents 120 as the remaining
intentional "toneless squeak transient", but the audition shows it inaudible where the
reference is clearly present.

## Root cause

`SfxNoise` for 120 uses gain **0.09** (`crates/ferrosintesis/src/voices.rs:174`) with a
~0.12 s decay — a deliberately short, quiet noise transient (`voices.rs:220` frames it as
such). The model shape is fine; it is pinned near-silent. This is a **level** issue, not
timbre, and the PROGRAM_TRIM table cannot touch it: 120 is in the never-trim SoundFX class,
and −18 dB exceeds the ±6 dB clamp anyway.

## Fix direction

Raise the SfxNoise 120 voice gain (and/or lengthen the decay) so the squeak is audible at a
level comparable to the reference. A voice-level fix, not a strip trim. Low priority (a niche
SFX voice, no in-repo album authors it), but the audition makes the gap plain.
