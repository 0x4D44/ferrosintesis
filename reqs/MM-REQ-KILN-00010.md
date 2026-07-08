# MM-REQ-KILN-00010 — CC70 vowel morph should extend beyond the choir

- **State:** Accepted
- **Priority:** Could
- **Area:** hollowsynth / engine
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test choir_pad_91_cc70_vowel_morph_opens_formants --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
The CC70 vowel-morph control must be available to the formant-capable SawStack
voices beyond the choir — at minimum the choir-pad (GM 91), and optionally
strings/pads given a formant filter — rather than being hard-gated to programs
52–54, since `SawStack::set_vowel` already exists.

## Rationale
The vowel machinery is built and gated to 52..=54 only; choir-pad 91 in
particular has zero vocal character today. Note: a voice must be built with the
`Formant` filter for `set_vowel` to act, so ungating alone is insufficient for
programs currently on a plain lowpass — the req includes giving 91 the formant
bank. Opt-in via CC70 authoring → byte-identical for existing albums. 2026-07-08
GM gap audit (cross-cutting engine gap; pads/choir).
