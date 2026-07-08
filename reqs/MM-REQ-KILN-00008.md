# MM-REQ-KILN-00008 — Modal & Organ voices must respond to pitch bend and portamento

- **State:** Accepted
- **Priority:** Should
- **Area:** hollowsynth / voices (Modal, Organ)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
The Modal and Organ voice families must honour channel pitch multipliers
(`set_pitch`): pitch bend, RPN bend-range/fine-tune, CC5/CC65 portamento, and
aftertouch vibrato must audibly move their pitch. This covers pianos 0–7, bells
8–15, timpani 47, crystal 96–103 and organs 16–23 — roughly 40 programs that
currently ignore all of them (their `set_pitch` is the no-op trait default while
the engine dutifully calls it).

## Rationale
Highest-leverage expression gap: one capability unlocks ~40 programs. Needs care
(retuning modal partials / organ pipes while a note rings) and per-family design,
hence heavy. Opt-in-safe in principle (a channel that never bends is unchanged),
but must be proven byte-identical for existing albums. 2026-07-08 GM gap audit
(cross-cutting engine gap #1).
