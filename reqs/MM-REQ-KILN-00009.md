# MM-REQ-KILN-00009 — Strings & choir (SawStack) must answer CC1 vibrato and CC68 legato

- **State:** Accepted
- **Priority:** Should
- **Area:** hollowsynth / engine + voices (SawStack)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** `$null | cargo test strings_choir_cc1_vibrato_and_cc68_legato_are_opt_in --manifest-path fable5/hollowsynth/Cargo.toml`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
The string-ensemble (48–51) and choir (52–54) SawStack voices must answer the
CC1 mod-wheel vibrato (add them to `vibrato_family`) and CC68 legato slurs
(extend the lead-gated `SawStack::legato_to`), engaging only on channels that
author those controllers.

## Rationale
The synth-lead build (MM lead voice, GM 80–87) already wired CC1/CC68 into the
SawStack engine and gated legato to leads; extending it to strings/choir is a
small follow-on. Opt-in via the authored-channel pattern → byte-identical for
albums that don't send CC1/CC68 on those channels (none do today). Coordinate
with the brass/reed agent, who owns the strings/choir polish. 2026-07-08 GM gap
audit (cross-cutting engine gap #2).
