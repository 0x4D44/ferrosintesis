# MM-BUG-KILN-00033 — Authored effect sends (CC93 chorus / CC94 delay) are discarded on Program Change and Reset-All-Controllers; CC121 additionally over-resets RPN-set values and sound controllers (RP-015)

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine
- **Raised:** 2026-07-21
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — Program-Change facet found independently by Fable 5 and gpt-5.6-sol-xhigh; CC121 RP-015 scope from Fable 5)

## Observation

MIDI effect send levels are persistent **channel** state; GM / MMA RP-015 keeps them across
a Program Change and does not reset them on Reset-All-Controllers. ferrosintesis violates
this in two places, both in `crates/ferrosintesis/src/engine.rs`:

- **Program Change discards authored sends.** `program_change` (engine.rs:2332-2335)
  unconditionally sets `chorus_send`/`delay_send` from `fx_profile(prog, …)` and clears
  `chorus_authored`/`delay_authored`. A foreign file that authors CC93 and/or CC94 then
  changes program mid-song loses its authored sends. Mid-song Program Change is common. Note
  the inconsistency: a CC0 **bank** change correctly guards on the authored flags
  (engine.rs:2137-2143) — Program Change does not.

- **Reset-All-Controllers resets the sends and more than RP-015 allows.** CC121 →
  `reset_all_controllers` → `rederive_program_defaults` (engine.rs:2448, 2360-2363) resets
  the same two sends. Per RP-015 the *only* controllers reset by Reset-All-Controllers are
  modulation, expression, hold/sostenuto/soft pedals, RPN/NRPN latch (→ null), pitch-bend
  value, and channel/poly pressure. `reset_all_controllers` additionally resets values that
  RP-015 says to preserve: the RPN-set pitch-bend range → 2.0 (engine.rs:2408), channel fine
  tune → 1.0 (engine.rs:2409), and the sound-controller state CC70 vowel / CC71 resonance /
  CC74 cutoff plus the wah filters (engine.rs:2421-2447).

Correctly preserved today: CC91 reverb send, CC7 volume, CC10 pan, program, and both bank
selects. No in-repo album is affected (albums do not re-program or Reset-All mid-song with
authored sends); foreign-file fidelity is the beneficiary.

## Fix

<to be filled by the fixer>

Sketch (one "controller-persistence semantics" pass): in `program_change`, preserve authored
sends the way the CC0 arm already does (respect `chorus_authored`/`delay_authored`); in
`reset_all_controllers`, stop resetting the effect sends, the RPN-set bend range / fine tune,
and the CC70/71/74 sound-controller state — reset only the RP-015 controller set. Regression:
author CC93 then send a Program Change → send preserved; send CC121 → bend range / sound
controllers preserved.

## Notes

- The Program-Change facet is broader and bites more often than the CC121 facet (mid-song PC
  is common; mid-song Reset-All is rare) — prioritise the PC fix.
- Distinct from MM-BUG-KILN-00035 (GM System On / live-vs-offline reset semantics): this is
  ordinary per-channel controller persistence, not a System-On/SysEx reset.
