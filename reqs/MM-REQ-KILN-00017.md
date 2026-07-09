# MM-REQ-KILN-00017 — Bagpipe (109) and shanai (111) as reed voices (blocked on reed engine)

- **State:** Accepted
- **Priority:** Could
- **Area:** ferrosintesis / voices (reed)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test bagpipe_shanai_route_to_reed_engine_with_drone_or_double_reed --manifest-path crates/ferrosintesis/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
GM 109 (bagpipe) and 111 (shanai) must render as reed instruments — shanai a
double-reed voice; bagpipe a continuous chanter over a persistent drone — instead
of the steel-guitar catch-all.

## Rationale
Both are reed-family and are a natural fit for the v0.9 reed voice (pulse osc +
formant bank) the brass/reed effort is building. **Dependency:** blocked on that
reed engine landing (no pulse oscillator existed in the crate before the synth-
lead build's `BlepPulse`; a shared reed engine is still needed). Bagpipe also
needs a chanter+drone scheme. Byte-identical for existing albums (109/111
unused). 2026-07-08 GM gap audit (ethnic/reed).
