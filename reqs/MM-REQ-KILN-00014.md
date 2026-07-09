# MM-REQ-KILN-00014 — Reed organ, accordion, harmonica (GM 20-23) need reed character

- **State:** Accepted
- **Priority:** Should
- **Area:** ferrosintesis / voices (Organ)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test reed_organ_accordion_harmonica_have_free_reed_character --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
GM 20 (reed organ), 21/23 (accordion, tango accordion) and 22 (harmonica) must
render with free-reed character — detuned musette ranks and a bellows-noise floor
for the accordions, a breathy sustained-noise + onset scoop for the harmonica —
and must drop the unconditional Hammond key-click. For 22, CC1 should give
vibrato rather than the organ Leslie ramp.

## Rationale
All four render the shared church-pipe-organ registration with zero reed/bellows
adaptation today (21–23 are borderline absent-in-spirit). GM 20 is used (Winter
Guests), so re-renders — needs sign-off. 2026-07-08 GM gap audit (organ).
