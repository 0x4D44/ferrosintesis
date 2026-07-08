# MM-REQ-KILN-00006 — SFX programs (GM 120-127) should not emit a pitched guitar note

- **State:** Draft
- **Priority:** Could
- **Area:** hollowsynth / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08)

## Statement
GM 120–127 (fret noise, breath, seashore, bird, telephone, helicopter, applause,
gunshot) must render as a safe, toneless noise/near-silence fallback rather than
the current in-key steel-guitar pluck, so a composer who hits an SFX program does
not get a wrong pitched note.

## Rationale
These sound-effect programs are rare but currently produce a melodic guitar note
at the written pitch — the loudest possible wrongness. A band-filtered noise
burst (or near silence) is a safer default. Byte-identical for existing albums
(none use 120–127). Lowest-priority family; keep the change proportionate.
2026-07-08 GM gap audit (percussive/SFX).
