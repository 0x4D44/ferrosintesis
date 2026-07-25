# MM-BUG-KILN-00104 — Piano damper release is a flat constant across the whole keyboard: no register dependence and no undamped top octaves

- **State:** Closed
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high) → Fixed (2026-07-25, Claude Opus 5; `70b7067` replaced the flat release with a bounded register-aware felt damper and undamped top register) → Closed (2026-07-25, Codex GPT-5.6-Sol; independently inspected the release law and reran the curve, anti-flat, rendered-tail, and register-release oracles on native Rust and 1.87)

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

Commit `70b7067` replaced the flat piano release with `PianoDamper::Felt`.
The release halves every two octaves, remains bounded from 0.18 to 0.95
seconds through the damped range, and stays anchored at the prior 0.45-second
middle-C value. Keys above F6 use a bounded 12-second release so their modal
body rings naturally without making voice reaping unbounded.

Independent closure verification confirmed the law reaches GM0, all GM0
alternates, and GM1, while the deliberately separate GM3 honky-tonk remains
outside it. The adversarial oracle rejects the old flat law. The rendered-path
oracle measured the damped tail at -162.8 dB and the undamped tail at -30.6 dB,
a 132.2 dB separation after key-up. The register sweep also matched the
derived 60 dB/T60 expectations at keys 36, 60, and 84 with samples both off
and on. All focused tests pass on native Rust; the four damper oracles also
pass on Rust 1.87.

## Notes
