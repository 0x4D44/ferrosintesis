# MM-REQ-KILN-00028 — A MIDI file must be able to author the driven-guitar amp and cabinet per channel

- **State:** Satisfied
- **Priority:** Should
- **Area:** engine / Drive
- **Raised:** 2026-07-23
- **Implemented-by:** crates/ferrosintesis/src/engine.rs (Strip amp_params/amp_cur/amp_primed + NRPN latch; Drive::apply_params + DriveBase; the three rebuild reseed sites; CC 6/38/98/99/100/101 arms) — on branch, pending integration
- **Satisfied-by:** engine::tests::amp_neutral_is_bit_identical (inertness), amp_each_knob_moves_its_axis, amp_drive_knob_holds_alias_floor, amp_drive_level_residual_bounded, amp_sweep_has_no_block_rate_zipper, amp_single_step_does_not_click, amp_params_follow_the_state_table (state table + rebuild timing), amp_nrpn_never_corrupts_the_rpn_bend_range (KILN-00034 all directions)
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-23, Arthur asked for authorable amp/distortion knobs so GM29 and GM30 can be built into genuinely different rigs — Claude Opus 4.8) → Accepted (2026-07-23, HLD Part A self-approved: 3-lens adversarial + Codex cross-family review) → Implemented (2026-07-23, on branch — 8 oracles green, render-diff clean, awaiting integration) → Satisfied (2026-07-25, verified)

## Statement

A MIDI file must be able to author the driven-guitar amp and cabinet (GM programs 29 and 30) as
per-channel parameters, so that two channels playing driven guitar can present two distinguishably
different rigs from the score alone.

The control surface must satisfy three invariants:

1. **Inert when unauthored.** A file that authors none of these parameters must render
   bit-identically to a build without the feature. This follows the repo's standing
   controller-feature rule: an unauthored controller must have no effect.
2. **Authored values are channel state, not program state.** They must survive Program Change,
   CC0 bank select and CC121 Reset All Controllers, and must be cleared only by GM System On.
   This is MM-BUG-KILN-00033's rule — program-derived values are defaults; authored values
   outrank them.
3. **Click-free and allocation-free.** Changing a parameter mid-note must not rebuild the `Drive`
   insert, must not discard filter state, and must not allocate on the audio path.

## Notes

- Design: `wrk_docs/2026.07.23 - HLD - score-authored amp parameters (part A, control surface and
  state).md`. Part A ships the control surface and state semantics; **Part B** sets what the GM29
  and GM30 defaults should actually be, after Arthur has auditioned the knobs.
- Addressed by NRPN (MSB `0x30`, LSB = parameter index), chosen over undefined CCs because
  ferrosintesis is a generic GM player and must not silently reinterpret a foreign file's
  controllers; and over SysEx because the existing XG variation insert is one global amp on one
  part, structurally incapable of giving two channels two different rigs.
- Values are **offsets** from the shipped program voicing, `64` = unchanged — so the oracle-tuned
  29/30 × main/alt matrix from `e2a78c1` composes with authoring rather than being discarded by it.
- This change edits the CC98/99 arm added for **MM-BUG-KILN-00034**. The guard must survive, and
  is strengthened to null the latch in both directions (an RPN select now also nulls the NRPN
  latch), which is the correct MIDI semantics — most recent select wins.
- Origin: Arthur, 2026-07-23 — *"An Epiphone going through X pedal to a Marshall cab can sound
  quite different from a Les Paul going through Y pedal to a different cab... Has to be author —
  that's where the real magic will happen."*
