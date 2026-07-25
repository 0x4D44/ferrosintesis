# MM-REQ-KILN-00023 — GM 93 (Pad 6, metallic) must be inharmonic

- **State:** Satisfied
- **Priority:** Could
- **Area:** voices / synth pads
- **Raised:** 2026-07-20
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::pad` (GM 93 arm), `crates/ferrosintesis/src/voices.rs::PAD93_BAR_MODE_2`, `crates/ferrosintesis/src/voices.rs::PAD93_BAR_MODE_3`
- **Satisfied-by:** `voices::tests::pd_o1_metallic_93_carries_inharmonic_bar_modes`
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

GM program 93 ("Pad 6 (metallic)") must carry genuinely inharmonic partials — a
metallic clang, not the harmonic stack it renders today.

## Notes

- "Lost" requirement: the code and the Stage-2 journal both flag the
  harmonic-clang limit and promise "a separate req" (grep "metallic" in
  `crates/ferrosintesis/src/voices.rs`); the req was never filed.
- The Modal partial-bank machinery (bells, tubular bells' hand-tuned ≈2:3:4.2
  ratios) shows how to put an inharmonic table under a pad-shaped envelope.
- Oracle sketch: partial-frequency ratios deviate from integer multiples by a
  floor (inharmonicity measure), on GM 93 only within 88–95.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate").

## Implementation (2026-07-25)

Two `push_interval_layer` layers at the transverse mode ratios of an ideal
free-free BAR — 1 : 2.756 : 5.404, the glockenspiel / tubular-bell series. The
ratios are physics, not taste; that series is why struck metal reads as metal
rather than as a pitched pipe.

The note proposed a `Modal` voice, and the `voices.rs` comment here said the
same ("a true *inharmonic* metallic needs a Modal voice"). That route was NOT
taken: a Modal rings and decays, and GM 93 has to hold under a held key. Interval
layers — the machinery the 86 fifth and 87 sub-octave already use — put genuinely
inharmonic partials into a SUSTAINING pad. The layers ride under the harmonic
body so the written pitch stays the tonal centre; a metallic PAD, not a bell.

**Oracle: `pd_o1_metallic_93_carries_inharmonic_bar_modes`.** Four claims:
present at each bar mode; SPECIFIC (nothing at 2.50·f0, an inharmonic ratio
nothing is designed at, so a voice that merely got noisier cannot pass); the
ratios are >= 0.15 from every integer, asserted directly; and the harmonic body
survives at 3·f0.

**Two measurement dead ends worth recording**, both caught by measuring rather
than assuming:

1. A harmonic-comb metric (energy at half-integer midpoints vs at harmonics)
   **barely saw the change** — 2.756 is 0.256 from the 2.5 midpoint, so the very
   partials being added fell in the gap between the metric's bands. It moved
   GM 93 from -10.9 to -6.7 dB while the noise pad 94 sat at -11.4: no usable
   separation.
2. Peak-picking then found the designed partials cleanly, but **noise pad 94
   produced 15 false "inharmonic partials"** from its first-class noise bed's
   ripple, up to -18 dB below the strongest peak — overlapping GM 93's own
   weakest.

The shipped metric is PROMINENCE (peak over the median of its neighbourhood),
which a noise floor cannot fake however tall it looks against the global peak:
GM 93 reads +22.0 dB or better at every key; the loudest of the seven control
pads reads +5.9 dB.

Refutations (each applied, each RED): both layers removed (+22.0 -> -1.0 dB);
ratios rounded to integers (the inharmonicity assertion fires); layer gains cut
to 0.02 (+1.7 dB).

Blast radius: GM 93 appears in **no album** — only two demo files
(`demos/ferrosintesis_reference/midi/03`, `demos/synth_feature_showcase/midi/04`),
confirmed by scanning program-change events in all 141 committed MIDI files.
