# MM-REQ-KILN-00189 — MuseScore MS Basic assets and zone mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** MuseScore MS Basic sample assets / deterministic verification
- **Raised:** 2026-08-13T22:30:20Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T22:30:20Z, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The MuseScore MS Basic sample assets must be independently verifiable against the pinned MS Basic SF3, the bake recipe, and their runtime zone mappings. A non-mutating oracle must bind every packaged filename to its baked payload identity and measured root, validate complete RIFF and PCM16 mono 44.1 kHz structure and extents, and prove all 36 filename-to-zone mappings consumed by ferrosintesis. Negative controls must include an equal-sized cross-note payload swap, duplicate payload, malformed RIFF or data extent, changed PCM format, changed regeneration selector, and changed root mapping. Current crate-local checks establish name parity and RIFF/WAVE magic but do not authenticate payload identity or bind it to the independently maintained runtime roots. Current static inventory is internally consistent; this requirement prevents future silent audio drift. Draft MM-REQ-KILN-00144 separately covers exact published upstream source pins, and MM-REQ-KILN-00188 covers the distinct MuseScore_General grand bank.

## Notes
