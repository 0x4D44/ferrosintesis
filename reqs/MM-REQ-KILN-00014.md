# MM-REQ-KILN-00014 — Reed organ, accordion, harmonica (GM 20-23) need reed character

- **State:** Satisfied
- **Priority:** Should
- **Area:** ferrosintesis / voices (Organ)
- **Raised:** 2026-07-08
- **Implemented-by:** task/20260709-TSK-HUM-reqs-heavy-00014-reed-organ-accordion-ha
- **Satisfied-by:** `voices::tests::reed_organ_accordion_harmonica_have_free_reed_character`, `voices::tests::accordion_musette_beats_across_harmonics`, `voices::tests::bandoneon_is_drier_than_accordion`, `voices::tests::reed_organ_gm20_has_no_parallel_fifth`, `engine::tests::gm22_cc1_is_harmonica_vibrato_not_leslie`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09) → Satisfied (2026-07-25, verified)

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

## Notes

- 2026-07-09 implementation gate: `$null | cargo test --manifest-path crates/ferrosintesis/Cargo.toml` passed (`178 passed; 0 failed; 4 ignored`).
- 2026-07-09 integration gate: `cargo fmt --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, and `cargo build --release -p ferrosintesis-cli` passed.
- 2026-07-09 render containment: Winter Guests Part One GM20 harmonium channel changed while channel 0 stayed byte-identical to latest trunk; RIVERWAKE GM21 accordion channel changed while channel 0 stayed byte-identical to latest trunk.
