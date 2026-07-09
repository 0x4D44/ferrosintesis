# MM-REQ-KILN-00011 — Fretless bass (GM 35) should have a "mwah"

- **State:** Implemented
- **Priority:** Should
- **Area:** hollowsynth / voices (Pluck bass)
- **Raised:** 2026-07-08
- **Implemented-by:** `fable5/hollowsynth/src/voices.rs::Mwah`, `fable5/hollowsynth/src/voices.rs::FRETLESS`, `fable5/hollowsynth/src/voices.rs::tests::fretless_bass_35_mwah_blooms`, `fable5/hollowsynth/src/testutil.rs::guards::golden_mix_balance_holds`, `fable5/hollowsynth/README.md`
- **Satisfied-by:** `$null | deltic timeout 240 cargo test fretless_bass_35_mwah_blooms --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-09)

## Statement
The fretless bass (GM 35) must have its signature vocal onset — an
envelope-following mid formant that blooms open over the first ~120 ms — rather
than differing from the fingered bass only in static damping/tone-table values.

## Rationale
Fretless character is the "mwah"; today GM 35 is just a darker fingered bass with
no dynamic mid resonance. Could be done default-on (re-renders 35's album tracks
— needs sign-off) or gated behind CC70 on bass channels (byte-identical); the
design chooses. GM 35 is used by albums, so treat as re-rendering unless gated.
2026-07-08 GM gap audit (bass).
