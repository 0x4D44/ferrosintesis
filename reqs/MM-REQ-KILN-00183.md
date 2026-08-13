# MM-REQ-KILN-00183 — Salamander grand assets and selectors must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** Salamander grand sample assets / deterministic verification
- **Raised:** 2026-08-13T17:58:33Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-13T17:58:33Z, raised via `deltic reqs new`)

## Statement

The system must provide a non-mutating verification that authenticates or rebuilds every Salamander grand zone from the pinned archive and recipe, then compares the committed outputs per filename for exact inventory, payload identity, canonical RIFF/PCM structure, declared duration, measured-root agreement, and deterministic output bytes. It must also independently assert the pp/mf/f velocity boundaries and both round-robin selections used by grand_bank. The current crate checks names, count, aggregate bytes, RIFF/WAVE magic, and get lookup while deriving its table and byte pin from the same output directory. All 54 files are exactly 133,048 bytes, so swapping C2 and C6 payloads preserves every crate-local assertion while the unchanged consumer root table routes both notes incorrectly. A suitable negative control must perform that same-sized swap; additional controls should corrupt RIFF extent or data length and shift the 51/52 or 95/96 selector boundary. Current assets were statically inspected and are structurally valid and unique; this records prevention debt, not present corruption. Share verifier architecture with Draft MM-REQ-KILN-00164, MM-REQ-KILN-00167, and MM-REQ-KILN-00170 while retaining the Salamander archive, recipe, dynamic-layer, and round-robin rules. Proposed priority: Could. Proposed flow: heavy. Estimated effort: Medium.

## Notes
