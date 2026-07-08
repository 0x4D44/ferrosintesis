# MM-REQ-KILN-00003 — Sustaining synth-FX programs (97/99/101/103) should sustain

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** codex-gpt5@KILN (2026-07-08T20:28:17.3073443+01:00)
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
GM 97 (soundtrack), 99 (atmosphere), 103 (sci-fi) must render as sustaining pad
textures (route to `pad()`), and 101 (goblins) to the LFO-swept sweep-pad path,
rather than the one decaying `bell(CRYSTAL)` chime that all eight FX programs
currently share and which fades to silence in ~3 s on a held note.

## Rationale
These are sustained-texture programs; a struck chime is structurally wrong. The
SawStack pad voice already provides the right character; this is dispatch-arm
work. Byte-identical for existing albums (only FX 98/crystal is used, and it
stays on the bell path). 2026-07-08 GM gap audit (synth FX).
