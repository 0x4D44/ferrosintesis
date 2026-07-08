# MM-REQ-KILN-00002 — Kalimba (GM 108) should have a tine voice, not a guitar

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test kalimba_108_has_tine_decay_not_pluck --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
A NoteOn on GM program 108 (Kalimba) must render as a plucked-tine timbre — a
short-decay inharmonic partial set with a soft thumb-contact transient — via a
new `bell()` preset table, not the steel-guitar catch-all.

## Rationale
The `bell()` modal primitive is fully table-driven, so a KALIMBA partial table
(~2.8x/5.4x overtones, short T60, low-level contact noise) plus one match arm
suffices. Byte-identical for existing albums (108 unused). 2026-07-08 GM gap
audit (percussive/ethnic).
