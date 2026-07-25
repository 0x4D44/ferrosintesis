# MM-BUG-KILN-00104 — Piano damper release is a flat constant across the whole keyboard: no register dependence and no undamped top octaves

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** synth / piano voicing
- **Raised:** 2026-07-25
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high)

## Observation

Follow-on from MM-BUG-KILN-00103, raised by Arthur: "we should be consistent
between our pianos - there must be established practice about what a GM piano
should do here."
There is no GM answer. General MIDI specifies programs, channel 10, polyphony
and required controllers; it says NOTHING about envelope or release times. So
this is a voicing question, not a compliance one.
The established practice is physical. A felt damper takes time proportional to
the string's energy, so bass damps slowly and treble quickly; and the top ~1.5
octaves of a standard 88-key piano have NO dampers at all (the assembly stops
around F6), so those strings ring on after key-up until they decay naturally.
Sample formats are built for this: SoundFont 2 carries keynumToVolEnvDecay and
keynumToVolEnvHold precisely so envelope times scale with key number.
ferrosintesis applied ONE flat release to every key, A0 to C8, via
`acoustic_piano`/`grand_piano_variant` -> `Modal::new`. 0.45 s is defensible in
the mid register but too long in the treble, and wrong in kind above the damper
cutoff where it should be absent. The pre-00097 alternates were worse still at
0.10 s flat.
Tubular Bells makes it concrete: its piano spans keys 30-100, and 13.4% of its
notes sit above key 84 - the register a real piano does not damp at all.

## Fix

<unfixed — raised only>

## Notes
