# MM-REQ-KILN-00188 — MuseScore grand assets and zone mappings must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** MuseScore grand sample assets / deterministic verification
- **Raised:** 2026-08-13T21:20:11Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T21:20:11Z, raised via `deltic reqs new` model=gpt-5.6-sol@high)

## Statement

The MuseScore grand sample assets must be independently verifiable against the pinned MuseScore_General SF3 and their runtime zone mappings. A non-mutating oracle must bind each packaged filename to its baked payload identity and measured root, validate complete RIFF/PCM16 mono 44.1 kHz structure and extents, and prove the 25 filename-to-zone mappings consumed by ferrosintesis. Negative controls must include an equal-sized cross-note payload swap, duplicate payload, malformed RIFF or data extent, changed PCM format, and changed root mapping. The current crate-local tests derive names and aggregate size from the same output directory, so all current 133048-byte WAVs can be swapped without tripping those checks. Current static inventory is internally consistent; this requirement prevents future silent drift. Draft MM-REQ-KILN-00144 separately covers publishing the exact upstream source digest and does not duplicate output or zone identity.

## Notes
