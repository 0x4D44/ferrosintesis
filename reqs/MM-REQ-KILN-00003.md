# MM-REQ-KILN-00003 — Sustaining synth-FX programs (97/99/101/103) should sustain

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
GM 97 (soundtrack), 99 (atmosphere), 103 (sci-fi) must render as sustaining pad
textures (route to `pad()`), and 101 (goblins) to the LFO-swept sweep-pad path,
rather than the one decaying `bell(CRYSTAL)` chime that all eight FX programs
currently share and which fades to silence in ~3 s on a held note.

## Rationale
These are sustained-texture programs; a struck chime is structurally wrong. The
SawStack pad voice already provides the right character; this is dispatch-arm
work. Byte-identical for existing albums (only FX 98/crystal is used, and it
stays on the bell path). 2026-07-08 GM gap audit (synth FX).
