# MM-REQ-KILN-00015 — Electric pianos, harpsichord, clavinet (GM 4-7) need their own voices

- **State:** Satisfied
- **Priority:** Should
- **Area:** ferrosintesis / voices (piano)
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::is_acoustic_piano`, `crates/ferrosintesis/src/voices.rs::electric_piano_1`, `crates/ferrosintesis/src/voices.rs::electric_piano_2`, `crates/ferrosintesis/src/voices.rs::harpsichord`, `crates/ferrosintesis/src/voices.rs::CLAVINET`, `crates/ferrosintesis/src/engine.rs::EngineCore::note_on`
- **Satisfied-by:** `$null | cargo test keyboard_voices_ --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09) → Satisfied (2026-07-25, verified)

## Statement
GM 4/5 (electric pianos — Rhodes tine, FM/DX bell), 6 (harpsichord) and 7
(clavinet) must render as their own instruments rather than all going through the
one acoustic-piano model (with its acoustic-piano velocity→brightness law and
sampled hammer strike). Harpsichord in particular is a plucked, near-constant-
loudness instrument and must not be a velocity-scaled struck-hammer piano.

## Rationale
`piano()` does not branch on program — 0–7 are byte-identical. 6/7 are
"absent in spirit"; harpsichord is the worst-fit (plucked → struck). Every
committed album uses only program 0, so 4–7 are unused → changing them is
byte-identical-safe (a rare heavy req that does NOT re-render). Options: route
6/7 to the Pluck engine, a bell-table voice for 4/5, and suppress the acoustic
PCM layer for 3/6/7. 2026-07-08 GM gap audit (piano).

## Notes

- 2026-07-09 implementation found the original "GM4-7 unused" rationale was false: both committed Heliopause MIDI files use GM4 on channel 0. No other GM4-7 committed MIDI use was found in a 53-file scan.
- 2026-07-09 focused oracle: `$null | cargo test keyboard_voices_ --manifest-path crates/ferrosintesis/Cargo.toml` passed. It covers GM4-7 distinct routing, GM0-3 acoustic hash canaries, GM0 sample-layer positive control, GM4-7 no acoustic sample layer, GM6 narrow velocity law, GM7 clavinet pluck routing, and CC67 acoustic-only behavior.
- 2026-07-09 full gate: `cargo fmt --check`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo test --workspace`, and `cargo build --release -p ferrosintesis-cli` passed at `0.10.4`.
- 2026-07-09 Heliopause containment: Part One and Part Two channel 0 stems changed, while channel 1 stems stayed byte-identical to baseline. Refreshed the two committed Heliopause `.opus` listening copies with `python render_opus.py --album "Heliopause"`.
