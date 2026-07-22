# MM-BUG-KILN-00033 — Authored effect sends (CC93 chorus / CC94 delay) are discarded on Program Change and Reset-All-Controllers; CC121 additionally over-resets RPN-set values and sound controllers (RP-015)

- **State:** Fixed
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — Program-Change facet found independently by Fable 5 and gpt-5.6-sol-xhigh; CC121 RP-015 scope from Fable 5) -> Fixed (2026-07-22, Claude Opus 4.8, `eae24cc` on `task/20260722-FIX-HUM-effect-send-persistence-across-program-c`; **integration held pending Arthur's audio review** — see Notes)

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

`eae24cc` — one controller-persistence semantics pass over
`crates/ferrosintesis/src/engine.rs`.

- **`program_change`** — the program's `fx_profile` is now a *default* that fills an
  UNauthored send only, guarding on `chorus_authored`/`delay_authored` exactly as the CC0
  bank arm already did. The flags are no longer cleared (the mix reads them to pick the
  legacy/cathedral bus feeds).
- **`reset_all_controllers`** — reduced to RP-015's actual reset list. It no longer resets
  the CC93/CC94 sends, the RPN-set bend range (RPN 0,0) and fine tuning (RPN 0,1), the CC5
  portamento TIME (only the CC65 switch resets), or the CC70 vowel / CC71 resonance / CC74
  cutoff sound controllers and the wah filters that realise them. Two knock-ons: centre bend
  is now `s.fine`, not a hardcoded `1.0` (the old line was correct only because `fine` was
  clobbered on the next one), and the choir re-vowel applies the preserved vowel rather than
  `0.0`. `rederive_program_defaults` lost its send-resetting half and is renamed
  `rederive_program_drive`.
- **Deliberately out of scope**, as defensible internal state rather than spec violations:
  `legato` (CC68), `breath_*` (CC2), `expr_authored`, `mod_authored`. `expr_authored` is
  notably *not* inert — the cathedral-organ reed-rasp swell reads it — so flipping it would
  be an audio change with no spec mandate behind it.

**Regressions.** `program_change_preserves_authored_effect_sends` (authored sends survive a
PC; an unauthored channel still tracks the program default; authoring one of the pair leaves
the other on the default). `cc121_resets_controllers_but_preserves_mix_state` rewritten to
assert both halves of RP-015 — what resets *and* what survives (sends, bend range, fine, CC74
cutoff + filter, CC5 time).

**One pre-existing test needed its oracle corrected**, and it is worth reading before
touching this area: `gm22_cc1_is_harmonica_vibrato_not_leslie` authors `CC93=0` to kill
chorus for a clean measurement, and the old engine discarded that at the following Program
Change, restoring chorus 0.20 — whose wash suppressed the AM detector. Measured against the
right control, the post-reset channel is *identical* to a GM22 that never received CC1 (AM
`0.00->6.00` and spread `3.11` for both): the 6 Hz AM is GM22's own delayed-onset vibrato,
not a Leslie leak. The absolute bound `reset_late <= reset_early + 2.0` was passing for the
wrong reason; it is replaced by a comparison against that never-modulated control, which is
*stricter* — it pins reset TO the un-modulated voice instead of to a range.

## Notes

- The Program-Change facet is broader and bites more often than the CC121 facet (mid-song PC
  is common; mid-song Reset-All is rare) — prioritise the PC fix.
- Distinct from MM-BUG-KILN-00035 (GM System On / live-vs-offline reset semantics): this is
  ordinary per-channel controller persistence, not a System-On/SysEx reset.
- **The Observation's claim that "no in-repo album is affected" was WRONG.** A census of every
  committed MIDI for the exact changed pattern (a PC or CC121 landing on a channel that has
  already authored CC93/CC94) finds four album tracks. Corrected facts below.

### Render impact (measured, not predicted)

Render-diff over all 140 committed MIDIs against the branch base `a20f0b3`: **10 changed,
130 identical**, every diff predicted by the census and every non-diff explained.

Four album tracks move, **all on the echo/delay bus only** — no album MIDI authors CC93
before a Program Change, so the chorus delta is exactly zero everywhere:

| track | change |
|---|---|
| Big Weather 01 - First Light Freeway | ch2 lead guitar echo 0.30 -> 0.00, 3:02.9-3:55.2 (52 s) |
| Big Weather 03 - Run the Rooftops | ch2 lead guitar echo 0.30 -> 0.00, 3:09.1-4:25.7 (77 s) |
| Big Weather 05 - Static & Sparks | ch2 lead guitar echo 0.30 -> 0.00, 0:15.0 to end (3 m 34 s, ~93%) |
| The Signal Fire 01 | ch14 violin +3.9 dB echo, flute/whistle -2.9 dB; ch2 glockenspiel +5.3 dB |

Plus six demo tracks, which is the demos doing their job: `synth_feature_showcase` 01-05
(they author sends then walk the GM program list) and `ferrosintesis_reference` 06 -
Controllers and Effects, the **only** file in the repo containing a CC121 (19 events, ch0).
Zero CC121 events exist across all 124 album MIDIs, so the Reset-All-Controllers half of this
fix cannot reach any album render.

In all three Big Weather tracks the composer **ramps CC94 down to zero** and the Program
Change was silently restoring 0.30 moments later — in Static & Sparks the ramp completes at
0:14.91 and the PC lands 0.09 s afterwards. The fix therefore *honours* authored intent the
engine had been undoing. That is an argument for it, not proof it sounds better: these albums
were auditioned against the old engine, so **integration is held pending Arthur's listen**.

### For whoever runs the next render-diff here

`render-catalog`'s `ALBUMS` table includes the two **demo** directories, so a catalogue-wide
inventory is never "albums only". And `render_diff.py` classifies by touched GM program /
drum key — a change like this one is not a voice change, so with no `--program`/`--key`
declared, everything that moves is reported as "CONTAMINATION". That label is a harness
artifact here, not a finding.
