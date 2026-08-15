# MM-BUG-KILN-00201 — Steinway/piano-family zone-root pins have no oracle; equal-size payloads make a swapped include_bytes silently mispitch

- **State:** Fixed
- **Priority:** Could
- **Severity:** Medium
- **Area:** sampler zone tables / oracles
- **Raised:** 2026-08-14T10:21:10Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-14T10:21:10Z, raised via `deltic bugs new` model=claude-fable-5) -> Fixed (2026-08-15T16:56:38Z, deltic:auto role=fix run=fix-20260815T164408Z-p20132-n151918200-c1 branch=task/bug-MM-BUG-KILN-00201-run-fix-20260815T164408Z-p20132-n151918200-c1 code=8bb77f8 gate=manual)

## Observation

**Symptom.** The 27 `steinwayb_*` zone roots in
`crates/ferrosintesis/src/sampler.rs:1248-1301` are hand-transcribed f0 literals
(measured at bake time by `prepare.py`'s `measure_f0`, then copied into the zone
tables — `crates/ferrosintesis-samples-vcsl-steinway/PROVENANCE.md:56-58` documents
the flow). **No oracle checks them**: not a structural interval check, not a
measured-pitch check. The mandolin bank got exactly this guard
(`mandolin_zone_roots_match_the_fretboard`, `sampler.rs:6721` — pinned roots must
step 5-2-5-2… semitones within 0.6), after its own transcription scare; the
steinway bank's C/F# ladder (uniform 6-semitone steps) has no equivalent, and the
crate side cannot compensate: its tests check the name set, RIFF magic, and one
**aggregate** byte size (`ferrosintesis-samples-vcsl-steinway/src/lib.rs:177-208`),
and all 27 payloads are exactly 133 048 bytes, so payloads are fully interchangeable
as far as every existing test can see.

**Failure scenarios, all suites green (Rust workspace + Python gate):**

1. A transposed digit or row-vs-filename mismatch introduced while hand-updating the
   pins after a re-bake — the zone repitches by the transcription error; silently
   flat/sharp on a box that "has no ears".
2. Two `include_bytes!` paths swapped in a regenerated/hand-merged `lib.rs` — every
   name still present, aggregate size unchanged, duplicate-payload check still green
   (the payloads are distinct, just misassigned); C3 plays the C5 recording repitched
   ~2 octaves down.

This is the repo's self-declared recurring defect class (CLAUDE.md: "hand-maintained
lists are the recurring defect here — derive them"), on the audio path where the
symptom is inaudible to CI.

**Scope.** Not steinway-specific: the piano-family banks (`piano`/`grand`/`kawai`/
`headroom`/`musescoregrand`/`darkgrand`/`ydpgrand`/`honkytonk`/`b1upright`) pin
zone roots the same hand-transcribed way with no root oracle (spot-verified: the only
`*_zone_roots_*` test in `sampler.rs` is the mandolin's). Whoever fixes this should
enumerate every zone table carrying literal roots before fixing one (CLAUDE.md: the
reported item is evidence the list class is unmaintained, not the spec of the work).

Found by the 2026-08-14 review pass over `crates/ferrosintesis-samples-vcsl-steinway/`
(adversarial verify stage); pin-list shape and test absence re-verified against
`sampler.rs` by the reviewing lead.

## Fix

<unfixed — raised only>

Suggested shape, two independent layers (either alone catches scenario 1; only the
second catches scenario 2):

1. **Structural**: assert each bank's pinned roots step the documented ladder (6.0
   semitones ±0.6 for the steinway C/F# grid), mandolin-style — cheap, no decode.
2. **Measured**: for each zone, run the existing autocorrelation/Goertzel tooling
   (`testutil.rs`) over the decoded `z.data` and assert the measured f0 is within a
   few cents of `z.root` — this binds pin to payload and kills the swapped-bytes case.

Prove both the KILN-00073 way: transpose one pin / swap two `include_bytes!` paths in
a scratch build and watch the new oracle go red.

## Notes

- The bake side already measures f0 per file; the defect is only that the number's
  hand-carried copy into `sampler.rs` is trusted forever after.
- The voice-level pattern to copy also already exists: `la_brass_pitch_integrity` /
  `la_reed_pitch_integrity` / `la_sax_pitch_integrity` / `la_guitar_pitch_integrity` /
  `la_strings_pitch_integrity` (`sampler.rs:7508-8565`) render voices and Goertzel the
  crossfade window — none covers a piano program, and none reaches the CC0 alternate
  grands (steinway is CC0=3) at all.
