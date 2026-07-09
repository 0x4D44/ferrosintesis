# MM-REQ-KILN-00016 — Harp (GM 46) should have a soundboard

- **State:** Implemented
- **Priority:** Could
- **Area:** ferrosintesis / voices (Pluck)
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::HARP`, `crates/ferrosintesis/src/voices.rs::wound_factor`, `crates/ferrosintesis/src/voices.rs::tests::harp_46_has_soundboard_and_harp_wound_law`, `crates/ferrosintesis/README.md`
- **Satisfied-by:** `$null | deltic timeout 120 cargo test harp_46_has_soundboard_and_harp_wound_law --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09)

## Statement
The harp (GM 46) must have a body/soundboard resonance (a small peak-EQ set, e.g.
broad ~90 Hz plus 180/400 Hz warmth) and must be exempt from the guitar
wound-string key-split law that currently darkens its bass register on a
guitar-scale crossover.

## Rationale
The HARP preset has an empty body EQ (a boxless string, thin next to a real harp)
and runs its low register through a guitar-tuned wound key-split. GM 46 is used
(Hollow Hill), so re-renders — needs sign-off. 2026-07-08 GM gap audit
(low-strings).
