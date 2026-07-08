# MM-REQ-KILN-00005 — Orchestra hit (GM 55) should be a real stab, not a guitar note

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test orchestra_hit_55_is_short_layered_stab --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
A NoteOn on GM program 55 (Orchestra Hit) must render as a short, layered
stab — octave-stacked ensemble chord with a percussive thump and a fast decay —
plus the appropriate engine wiring, not the steel-guitar catch-all.

## Rationale
55 falls in the 55–71 seam: the brass/reed effort wires 55–71 into the
expressive features but designs no voice for 55 itself. 55 is unused by every
committed album, so a new voice here is byte-identical-safe. 2026-07-08 GM gap
audit (low-strings/hit). Note: coordinate with the brass/reed agent on the
55–71 engine wiring to avoid a collision.
