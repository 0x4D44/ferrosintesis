# MM-REQ-KILN-00007 — Sitar/shamisen/koto (104/106/107) need their own plucked voices

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test sitar_shamisen_koto_have_distinct_pluck_presets --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** codex-gpt5@KILN (2026-07-08T21:22:21.7376460+01:00)
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
GM 104 (sitar), 106 (shamisen) and 107 (koto) must render with distinct plucked
character — koto long and mellow (harp-like preset), sitar with a buzzing
jawari/sympathetic quality, shamisen a lightened banjo — instead of all sharing
the single bright/short BANJO preset with GM 105.

## Rationale
104/106/107 are byte-identical to the banjo today; sitar and koto are
character-opposite (koto rings short and bright, opposite of its long mellow
decay). GM 105 (banjo, used by Hollow Hill/RIVERWAKE) stays untouched.
Byte-identical for existing albums (104/106/107 unused). 2026-07-08 GM gap audit
(ethnic).
