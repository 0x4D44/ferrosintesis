# MM-REQ-KILN-00011 — Fretless bass (GM 35) should have a "mwah"

- **State:** Draft
- **Priority:** Should
- **Area:** hollowsynth / voices (Pluck bass)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08)

## Statement
The fretless bass (GM 35) must have its signature vocal onset — an
envelope-following mid formant that blooms open over the first ~120 ms — rather
than differing from the fingered bass only in static damping/tone-table values.

## Rationale
Fretless character is the "mwah"; today GM 35 is just a darker fingered bass with
no dynamic mid resonance. Could be done default-on (re-renders 35's album tracks
— needs sign-off) or gated behind CC70 on bass channels (byte-identical); the
design chooses. GM 35 is used by albums, so treat as re-rendering unless gated.
2026-07-08 GM gap audit (bass).
