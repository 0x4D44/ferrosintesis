# MM-REQ-KILN-00013 — Timpani (GM 47) needs strike dynamics and pitch glide

- **State:** Implemented
- **Priority:** Should
- **Area:** ferrosintesis / voices (timpani)
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::Modal::with_strike_glide`, `crates/ferrosintesis/src/voices.rs::timpani_partials`, `crates/ferrosintesis/src/voices.rs::timpani`, `crates/ferrosintesis/src/voices.rs::tests::timpani_47_glides_brightens_and_rings_after_noteoff`, `crates/ferrosintesis/README.md`
- **Satisfied-by:** `$null | deltic timeout 240 cargo test timpani_47_glides_brightens_and_rings_after_noteoff --manifest-path crates/ferrosintesis/Cargo.toml -- --nocapture`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09)

## Statement
The timpani (GM 47) must model a real kettle strike: a short post-strike pitch
glide (head settling), a velocity→brightness law on the upper modes, per-strike
jitter, and a note-off release long enough that staccato hits ring rather than
choke.

## Rationale
Today timpani is fixed-frequency modes scaled by velocity only — no glide, no
harder-is-brighter, no jitter, and staccato notes choke on a 0.25 s release
against a 1 s mode ring. The channel-10 membranes already model the glide pattern
to reuse. GM 47 is used (Hollow Hill), so re-renders — needs sign-off. 2026-07-08
GM gap audit (low-strings/percussion).
