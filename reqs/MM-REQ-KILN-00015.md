# MM-REQ-KILN-00015 — Electric pianos, harpsichord, clavinet (GM 4-7) need their own voices

- **State:** Draft
- **Priority:** Should
- **Area:** hollowsynth / voices (piano)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08)

## Statement
GM 4/5 (electric pianos — Rhodes tine, FM/DX bell), 6 (harpsichord) and 7
(clavinet) must render as their own instruments rather than all going through the
one acoustic-piano model (with its acoustic-piano velocity→brightness law and
sampled hammer strike). Harpsichord in particular is a plucked, near-constant-
loudness instrument and must not be a velocity-scaled struck-hammer piano.

## Rationale
`piano()` does not branch on program — 0–7 are byte-identical. 6/7 are
"absent in spirit"; harpsichord is the worst-fit (plucked → struck). Every
committed album uses only program 0, so 4–7 are unused → changing them is
byte-identical-safe (a rare heavy req that does NOT re-render). Options: route
6/7 to the Pluck engine, a bell-table voice for 4/5, and suppress the acoustic
PCM layer for 3/6/7. 2026-07-08 GM gap audit (piano).
