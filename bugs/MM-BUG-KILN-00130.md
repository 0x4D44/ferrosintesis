# MM-BUG-KILN-00130 — B1 upright bass notes dip ~5 dB then swell back across the LA crossfade

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** GM0 piano voicing / LA sample-to-model crossfade
- **Raised:** 2026-07-26
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
- **State history:** Open (2026-07-26, raised while promoting the B1 upright to the GM0 default) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T092559Z-p45536-n826874200-c1 branch=task/bug-MM-BUG-KILN-00130-run-fix-20260726T092559Z-p45536-n826874200-c1 code=248de621baa8c8a42db3884a7e610e6c114852f0 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (635 passed) and `test --workspace --exclude amp-lab --locked` (742 passed) - 1480 tests, 0 failures. Original observation re-run at BOTH layers, and the fix holds where the bug measured it. At voice level - the layer the bug's own repro names, `voices::make(0, key, 100, 44100.0, 5, true)` - I forced `b1_upright_handoff_does_not_rebound` to print its measurement rather than trusting a green tick: key 72 now rebounds **0.14 dB** against the ~9 dB the bug recorded, and key 36 passes the same 1.5 dB bar. Constant restored afterwards; `git status --porcelain` clean. The regression is well built: it renders both keys the bug measured, held for 700 ms at 50 ms RMS windows - the bug's exact method - and for every window in the 150-450 ms handoff it takes the loudest LATER window, so it tests the actual property ("a real piano cannot recover from a handoff trough") rather than a proxy. Both bars the bug required held are green: `la_level_continuity` and `gm0_fra_phrase_keeps_energy_through_short_key_up_gaps`. I also re-ran the bug's CLI claim end to end with my own probe (release binary, `--wet 0`, one held note per render so the -18 LUFS normalization cancels, 50 ms windows): at key 36 - the bass register the bug's title and its "any sustained bass piano line" claim are about - the envelope is monotone with a max rebound of **+0.28 dB**, against the ~5 dB the bug recorded there. CLOSED WITH A RESIDUAL SPLIT OUT AS MM-BUG-KILN-00133. The same end-to-end sweep showed that from about key 72 up the engine still rebounds 2.9-4.0 dB (key 72 +4.00, key 78 +3.04, key 84 +2.88), while a `--no-samples` render of the same notes stays monotone within 0.4 dB - so the effect is real and sample-layer-dependent. It is a residual rather than a persistence of this bug: the layer this bug names is measurably fixed, its guard is sound and passes honestly, its register is clean, and the surviving effect is at the engine rather than the voice, which is why a voice-level oracle cannot see it. Evidence, the key sweep, and a suspected (explicitly unconfirmed) sympathetic-resonance mechanism are recorded on 00133.)

## Observation

A held B1 upright note in the bass does not decay monotonically. It peaks at the
hammer, falls into a trough around 400 ms, then **rises again** as the LA sampled
onset hands over to the modelled body. A real piano decays monotonically from the
strike.

Measured on a held note (no note-off), 50 ms RMS windows, dB relative to the
attack peak, with the shipped calibration
(`voices::PianoSampleCal::B1Upright`, gain 1.30, crossfade 0.18–0.45 s):

- key 36, vel 100: trough about −5 dB near 400 ms, recovering to roughly the
  attack level by ~600 ms — a re-rise of about 5 dB above the trough.
- key 72, vel 100: a deeper notch, about −16 dB near 250 ms recovering to −9 dB,
  a re-rise of about 9 dB.

Reproduce with a held note through `voices::make(0, 36, 100, 44100.0, 5, true)`
and an RMS window sweep; the same shape appears through the CLI on any sustained
bass piano line.

## Analysis

This is **not** a level problem, and gain cannot fix it. Make-up gain was swept
over 0.90–2.40 while promoting the bank to the default
(`crates/ferrosintesis/src/voices.rs`, `PianoSampleCal::B1Upright`). Gain trades
two properties against each other and the usable window is only ~1.2–1.3 wide:

- below ~1.2 the modelled body outruns the recorded hammer and the envelope peak
  leaves the attack window entirely;
- above ~1.3 fast repeated notes stop damping cleanly — the 62.5 ms key-up gap
  drop grows from 9.99 dB at gain 1.30 to 10.45 at 2.00 and 10.78 at 2.40
  (engine level, key 66).

Lengthening the crossfade end (0.55 / 0.65 / 0.75 s was swept) makes both
properties worse, not better.

The residual is therefore the sampled layer's **decay shape** through the
crossfade, not its level: the B1 recording's own body falls faster over
0.18–0.45 s than the model underneath it rises, so the sum notches. Fixing it
needs the handoff to be shaped — for example an equal-power or
decay-rate-matched crossfade, or a per-zone body-decay match at bake time —
rather than a scalar gain.

## Impact

GM 0 is the default piano and the B1 is now its default recording, so this
reaches every album with a sustained piano bass line. It is audible as a slight
"breathing" on long held notes. It is not a regression introduced by the
promotion: the B1 behaved this way as the CC0=5 alternate too, and was worse
there (the pre-calibration swell rose ABOVE the attack). The promotion is what
brought it under test.

## Fix

Shape the sample-to-model handoff rather than scaling it. Candidates, cheapest
first:

1. Match the crossfade law to the two layers' measured decay rates per zone
   instead of using one fixed smoothstep.
2. Give `LaVoice` an equal-power (rather than sum-to-one amplitude) crossfade
   option and measure whether the notch closes.
3. Condition the B1 bank at bake time the way the VSCO upright is conditioned,
   so its cross-zone body trend matches the model it sits on.

Any fix needs the same held-note envelope sweep used above as its regression
oracle, plus the existing `la_level_continuity` and
`gm0_fra_phrase_keeps_energy_through_short_key_up_gaps` bars held.

Estimated effort: Medium.

## Notes

Related but distinct from MM-BUG-KILN-00103, which separated damper physics from
sample calibration. That fix made the two independent; this bug is about the
third thing neither controls — the crossfade's *shape*.
