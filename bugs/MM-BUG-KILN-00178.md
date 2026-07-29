# MM-BUG-KILN-00178 — GM67 key 58 'fartiness' from Arthur's audition is still undiagnosed: the other half of MM-BUG-KILN-00176's observation

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** audio / sampled sax sustain
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

Residual split from MM-BUG-KILN-00176 during its independent two-eyes closure.
Carried forward so the report is not lost when that bug closes.

Arthur's original report named TWO distinct artifacts on the GM67 channel, verbatim:

> What I did notice is that there are some artifacts on the GM67 channel - a
> combo of "fartiness" on some notes and a noticeable looping on some high
> notes.

His direct left/right comparison localized the **fartiness to notes 5 and 6, MIDI
key 58 at velocities 72 and 110**, and the sustain oscillation to keys 68 and 73.
Ferrosintesis was the left channel in both comparisons; channel extraction was
hash-verified against the source renders.

MM-BUG-KILN-00176 resolved and verified only the **looping** half. Its own Observation
says of this one: "Arthur has localized the separate 'fartiness' description to key 58,
but the current probe has not yet objectively defined or diagnosed it."

The landed fix (0798a78) cannot have affected key 58. Its multi-slice grain motion is
gated on `program == 67 && key >= 68` at `crates/ferrosintesis/src/sampler.rs`
`sax_loop_voice`, so key 58 takes `grain_motion == false`. This was confirmed two
independent ways during closure: by tracing every new mutation (all guarded by
`if self.grain_motion`, `grain_gain` stays 1.0, and `choose_next_grain` - the only new
`rng.white()` consumer - is never reached so the RNG stream is untouched), and
empirically by render-diff, where the one demo authoring GM67 below the gate
(`demos/ferrosintesis_reference/midi/03 - Reed, Pipe, Lead, Pad.mid`, GM67 keys
49/53/56) rendered bit-identically.

Reproduction, per the original:

1. Render default-bank GM67 with samples enabled, sends disabled, and the M-CAL
   sustained sequence: MIDI keys 48, 53, 58, 63, 68 and 73, each at velocities 72
   and 110.
2. Hold each note for 1.3 seconds. Listen to key 58 at both velocities.
3. Compare against the SC-55 and S-YXG50 reference renders.

**Expected.** A held baritone-sax note at key 58 does not read as "farty" against
the reference modules.

**Actual.** Arthur hears it; no objective metric has yet been defined for it, so
there is no numeric evidence in this record and no regression is possible yet.

**First work item is therefore diagnostic, not corrective:** define a measurement
that separates this from the loop-exposure artifact (which at key 58 measures
differently from the reported high notes) before proposing a fix. Note the ledger
precedent at `bugs/MM-BUG-KILN-00038.md`, where an Arthur audition described an
aftertouch passage as "farty" - check whether the mechanism is shared before
treating this as new.

Searched during closure: no other bug or requirement covers this.
`reqs/MM-REQ-KILN-00176.md` is an unrelated accent-drum-bank Draft that merely
shares the number.

## Fix

<unfixed — raised only>

## Notes
