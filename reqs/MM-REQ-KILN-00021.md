# MM-REQ-KILN-00021 — GM 84 (Lead 5, charang) must have its distortion character

- **State:** Satisfied
- **Priority:** Could
- **Area:** voices / synth leads
- **Raised:** 2026-07-20
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::LEADS` (GM 84 `drive`), `crates/ferrosintesis/src/voices.rs::LEAD84_DRIVE`, `crates/ferrosintesis/src/voices.rs::LEAD84_NOMINAL`, `SawStack::render` drive stage
- **Satisfied-by:** `voices::tests::ld_o2_charang_84_is_driven_not_merely_bright`
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-20, captured from the GM instrument sweep audit — Claude Fable 5) → Accepted (2026-07-25) → Implemented (2026-07-25) → Satisfied (2026-07-25, verified)

## Statement

GM program 84 ("Lead 5 (charang)") must carry the driven/distorted edge that
defines the charang patch, not render as another clean saw variant.

## Notes

- "Lost" requirement: bespoke per-program DSP for leads 84–87 was deferred "to
  reqs" in a `voices.rs` comment near the LeadSpec table; no req was ever filed.
- The repo already owns a Drive insert (guitar v2, used by GM 29/30) that could
  supply the nonlinearity — plumbing, not new DSP.
- Oracle sketch: harmonic-distortion ratio (odd-harmonic energy above the saw
  baseline) on GM 84 vs GM 80/81.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate": defining
  character unimplemented).

## Implementation (2026-07-25)

A post-filter `tanh` drive stage inside the lead voice, not the engine's guitar
Drive insert. The insert was the note's suggestion, but it is a channel effect
carrying a whole amp and cabinet — wrong tone for a synth lead, and adding 84 to
`engine::needs_drive` would have meant editing a currently-green guard that
deliberately pins the insert to GM 29/30. A charang's distortion belongs to the
patch, so it lives in the voice.

Placed AFTER the filter deliberately: a shaper before the tone control has its
new harmonics filtered straight back off.

**Oracle: `ld_o2_charang_84_is_driven_not_merely_bright`.** The control is an
exact LINEAR TWIN — the same voice, key, velocity and seed with only `drive`
zeroed — because comparing against GM 80/81 (the note's sketch) would confound
the drive with those programs' own cutoffs. Three claims, measured over a
key/velocity grid:

| claim | measured | threshold |
|---|---|---|
| (a) driven — HF above the twin | +5.2 .. +9.3 dB | >= +4 dB |
| (b) no aliasing — on/off-lattice contrast | 37.9 .. 51.9 dB (twin 36.5 .. 52.7) | >= 30 dB, and >= twin - 6 |
| (c) timbre not level — RMS vs twin | -0.44 .. +0.01 dB | within 1 dB |

**(c) is the claim that made this honest.** The first normalisation
(`tanh(drive)`, mapping full scale to full scale) passed (a) handsomely while
making the patch **5.7 dB louder** — brightness bought with loudness, which
would also have unbalanced the five album tracks that play GM 84. Dividing by
`drive` instead overshot to -3.8 dB. `LEAD84_NOMINAL` is the solved root of
`tanh(LEAD84_DRIVE·x)/x = 1.918` (the stage's measured RMS gain on this voice),
which puts unity gain at the level the voice really runs at.

Refutations (each applied, each RED):

- drive removed -> the derived table check fires;
- naive `tanh(drive)` normalisation restored -> (c) fires at +5.70 dB;
- drive cranked to 40 -> (c) fires;
- drive cranked to 40 **with the level re-solved**, isolating the alias guard ->
  (b) fires (lattice 52.7 -> 45.0 dB). Worth doing separately: without it, (b)
  would have been an assertion no test had ever shown could fail.

## Render-diff inventory (2026-07-25) — complete, no unexpected diffs

Baseline `3d64dc2` vs the change, all **141** committed MIDI files rendered by
both release binaries and compared byte-for-byte: **132 identical, 10 changed,
0 failures.** Every changed file is in the predicted set and nothing else moved.

| changed file | why |
|---|---|
| `albums/fable5/Big Weather/midi/03 - Run the Rooftops.mid` | GM 84 |
| `albums/fable5/The Burning Meridian/midi/01 - The Muster.mid` | GM 84 |
| `albums/fable5/The Burning Meridian/midi/03 - Meridian.mid` | GM 84 |
| `albums/fable5/Tuxedo Noir/midi/01 - Tuxedo Noir.mid` | GM 84 |
| `albums/fable5/Big Weather/midi/04 - Glass Anthem.mid` | GM 85 |
| `albums/fable5/Heliopause/midi/01 - Heliopause, Part One.mid` | GM 85 |
| `albums/fable5/Heliopause/midi/02 - Heliopause, Part Two.mid` | GM 85 |
| `demos/ferrosintesis_reference/midi/03 - Reed, Pipe, Lead, Pad.mid` | GM 84 + 85 + 93 |
| `demos/synth_feature_showcase/midi/01 - Ignition Court.mid` | GM 84 + 85 |
| `demos/synth_feature_showcase/midi/04 - Choir of Circuitry.mid` | GM 93 |

One PREDICTED file did not change, and the reason is worth keeping:
`albums/fable5/The Burning Meridian/midi/02 - Lanterns on the Water.mid` selects
GM 84 but plays **zero note-ons** while that program is current — verified by
counting note-ons per (channel, active program). Presence of a program-change
event is not evidence a program sounds; only notes under it are. An inventory
predicted from program changes alone will over-count.

No album plays GM 93 — its two diffs are both demos.
