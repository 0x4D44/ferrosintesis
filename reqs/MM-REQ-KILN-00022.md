# MM-REQ-KILN-00022 — GM 85 (Lead 6, voice) must have a vocal formant character

- **State:** Satisfied
- **Priority:** Could
- **Area:** voices / synth leads
- **Raised:** 2026-07-20
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::LEADS` (GM 85 `vowel_cc`), `crates/ferrosintesis/src/voices.rs::LEAD85_VOWEL_CC`, `crates/ferrosintesis/src/voices.rs::lead`, `crates/ferrosintesis/src/engine.rs::vowel_family`
- **Satisfied-by:** `voices::tests::ld_o1_voice_lead_85_speaks_through_formants`
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

GM program 85 ("Lead 6 (voice)") must shape its spectrum with vocal formants so it
reads as a voice-like lead, not another filtered saw.

## Notes

- "Lost" requirement: deferred "to reqs" in the `voices.rs` LeadSpec comment
  block; never filed.
- The machinery exists in-repo: `StackFilter::Formant` (the vowel formant bank) is
  already the default on choir-pad 91 and answers CC70 elsewhere — routing it
  under a lead envelope is the work.
- Oracle sketch: formant-peak presence (e.g. energy concentration near the bank's
  F1/F2) on GM 85 vs the plain-saw leads.
- Surfaced by the 2026-07-20 GM instrument sweep (rated "adequate": defining
  character unimplemented).

## Implementation (2026-07-25)

GM 85 now builds `StackFilter::Formant` instead of the lowpass, using the
existing three-band bank (the machinery the note identified). Two decisions
worth recording:

- **The formants are DERIVED, not copied.** `LEAD85_VOWEL_CC = 84.0` is a
  position in the shared CC70 vowel bank (`engine::VOWEL_ANCHORS`, the "ah"
  anchor), and `lead()` calls `engine::vowel_at` to get the numbers. A second
  hand-written formant table is exactly the drift this repo keeps paying for, so
  a retune of the vowel bank now moves the choir and the voice lead together.
- **GM 85 joined `vowel_family`**, so CC70 can morph its vowel. Opt-in as
  always: the arms it guards run only once a channel has AUTHORED CC70, so a
  lead that never sends it renders exactly as before.

The bank is static (`cur == tgt`), the way choir 91 does it — the "mm-ah" onset
morph belongs to a sung entry, and a lead has to speak immediately.

**Oracle: `ld_o1_voice_lead_85_speaks_through_formants`.** The measurement is the
contrast between the three formant bands and the VALLEYS between them: a
three-band resonant bank digs notches at fixed absolute frequencies that a
lowpass, however tuned, cannot make.

The statistic is that contrast's **minimum across keys**, and that choice is the
oracle's whole robustness argument. The square-lead pulse waves (80, 82) have no
even harmonics, and at key 55 their missing 4th and 8th land in both valley
bands — reading a spurious **+97.6 dB** that a single-key threshold would have
mistaken for formants. Their minima across keys are -8.8 and -14.2 dB, so the
minimum sees through the coincidence. Measured: GM 85 +11.8 dB; the largest
control minimum -2.6 dB.

A guard on the derivation is included: if the shared vowel bank is retuned so a
formant leaves the measurement band, the oracle fails loudly rather than
silently measuring empty spectrum. Proven by retuning ah's F1 600 -> 900 Hz.

Honest scope: formants are only observable where the harmonic comb is dense
enough to sample the filter's envelope. By key 72 the valleys have no harmonic
in them at all, so the contrast stops being diagnostic for any voice — a limit
of what a spectrum can show, not of the feature (the bank is key-independent by
construction). The oracle therefore runs on keys 40-60 and says so.

Refutations (each applied, each RED): 85 reverted to the plain lowpass
(+11.8 -> -4.8 dB); shared vowel bank retuned out of band (bracket guard fires).
