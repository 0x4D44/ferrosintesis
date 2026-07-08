# MM-REQ-KILN-00012 — Vibraphone (GM 11) should have its motor tremolo

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / voices (Modal / bell)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
The vibraphone (GM 11) must carry the amplitude-modulation tremolo that defines
it — the motor-fan pulse — rather than being a static metal-bar ring identical to
marimba/xylophone on the shared VIBES preset.

## Rationale
The Modal family ignores `set_trem` (only organs implement it) and 11 is outside
`vibrato_family`, so a vibraphone tremolo can never occur today. Implement as an
amplitude LFO on Modal, ideally CC1-routable and opt-in (byte-identical when CC1
absent) or default-on (re-renders — sign-off). Pairs with MM-REQ-KILN-00004
(splitting 11–13). 2026-07-08 GM gap audit (chromatic percussion).
