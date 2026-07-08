# MM-REQ-KILN-00001 — Fiddle (GM 110) should render as a bowed string, not a guitar

- **State:** Accepted
- **Priority:** Should
- **Area:** hollowsynth / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test gm110_fiddle_routes_to_bowed_and_takes_mod_vibrato --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** codex-gpt5@KILN (2026-07-08T19:42:36.7641945+01:00)
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
A NoteOn on GM program 110 (Fiddle) must render through the bowed-string voice
(the `Bowed` model already used for GM 40–45, LA violin-bank included), not the
steel-guitar catch-all it currently falls through to.

## Rationale
110 is a lead voice on RIVERWAKE and is character-opposite to a plucked guitar.
`Bowed::new` takes no program parameter, so this is a one-arm dispatch change
(duplicate the 40..=45 arm) plus adding 110 to `vibrato_family` and the fiddle
`fx_profile` arm. Byte-identical for every existing hollowsynth album (110 is
unused by them). From the 2026-07-08 GM gap audit (ethnic family).
