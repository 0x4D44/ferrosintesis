# MM-BUG-KILN-00085 — the LA bass crossfade SHAPE still costs the onset: a 50 ms model mute erases the kick thump and a 350 ms handover outlasts 90% of a bass line's notes

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24 — split from MM-BUG-KILN-00075 on its Open → Fixed transition by Claude Opus 4.8 (1M), which landed that bug's gain items 1–2 and could not land items 3–4)

## Observation

**Symptom.** Even with the GM 32–35 seam now level-matched (MM-BUG-KILN-00075), the LA bass
layer is still not fit to return to the default bank. Three things remain, and none is a
gain:

1. **The 50 ms model mute erases the `kick` thump.** `LaVoice`'s crossfade is sum-to-one:
   the model is muted outright until `fade.0` = 50 ms. The `BASS` preset's `kick` is a
   one-shot `Burst` with `KICK_T60_S` = 75 ms, so it fires almost entirely inside the muted
   window and never reaches the output. Level-matching the sample cannot restore it — the
   sample is a different recording and does not contain that thump.
2. **The 350 ms handover outlasts the music.** `fade.1` = 350 ms, but the bass part
   MM-BUG-KILN-00075 was raised from has a **146 ms median note** and **90% of notes shorter
   than the handover**, so the model is never sole owner. `LA_BANJO` already uses a 0.20 s
   tail, so a shorter bass handover has precedent in the codebase.
3. **GM32's onset stays ~3.7 dB under parity, and cannot be fixed by a gain.** The real
   pizzicato contrabass recording rings on while `Pluck(&UPRIGHT)`'s short `t60` has already
   decayed, so a taper that reaches onset parity overshoots `[50, 350] ms` by +6 to +10 dB.
   KILN-00075 therefore fitted GM32 on the whole handover instead, deliberately leaving the
   onset under. One scalar cannot fix both ends of a decay-**shape** mismatch.

**Also unresolved from KILN-00075's suggested fix (its item 4).** `finger_bass` covers
E1–D2 and `pick_bass` E1–E2, but 68% of that part's bass notes play above the top zone, so
notes are repitched up to +12 semitones — not a credible repitch for a bass onset. Either
the banks want upward extension, or the basses want a tighter repitch guard than the shared
`0.5..=2.05`.

## Measured context

From KILN-00075's calibration harness
(`sampler::tests::print_ebass_wrap_level_ratios`), post-taper, 187 engaged points:

| window | geomean | range |
|---|---|---|
| `[0, 50 ms]` | 0.866 (−1.2 dB) | 0.433 … 1.217 |
| `[50, 150]` | 1.025 (+0.2 dB) | 0.612 … 1.580 |
| `[150, 350]` | 0.900 (−0.9 dB) | 0.684 … 1.700 |

The remaining per-point spread — still ±4 dB at the edges — is the shape mismatch, not a
gain error. A gain moves the whole curve; it cannot change its slope.

## Fix

Needs **Arthur's ear**, which is why it is split rather than attempted:

- Shortening `fade` for the basses, or giving `LaVoice` an additive rather than sum-to-one
  option for the muted window, is an audible voicing decision on a part Arthur has already
  A/B'd once and reversed.
- Extending the sample banks upward requires new source recordings and licensing, not code.

The measurement infrastructure is in place: re-run the printer after any change and require
every window's geomean within ~1 dB of parity with a tightened per-point spread.

## Notes

- **Do NOT promote the LA bass back to the default bank** until this lands. That
  instruction originates in MM-BUG-KILN-00075 and survives its closure — KILN-00075 fixed
  the gain, not the shape.
- Related: **MM-BUG-KILN-00075** (the gain, Fixed), **MM-BUG-KILN-00045** (bass family
  level spread; GM32's `UPRIGHT` decay is the shared mechanism behind item 3),
  **MM-BUG-KILN-00046** (the GM48/49 precedent, Fixed), **MM-BUG-KILN-00016** (the bass
  family's missing sampled onset).
- Not verified: whether a shorter handover actually sounds better, and where the
  repitch-credibility limit for a bass onset really sits. Both are listening questions.
