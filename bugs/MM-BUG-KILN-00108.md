# MM-BUG-KILN-00108 — GM85 (Lead 6, voice) lost 16 dB: its new formant bandpass bank has no make-up gain, unlike GM84 in the same commit

- **State:** Fixed
- **Priority:** Must
- **Severity:** High
- **Area:** synth / voices
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5-1m@high)

## Observation

GM85 (Lead 6, voice) has lost 16.0 dB. It is now the quietest program in the
Lead family by a wide margin, and has dropped out of the M-CAL anchor cohort.

FOUR INDEPENDENT READINGS, from the 2026-07-25 closed-loop re-derive
(`wrk_docs/2026.07.25 - M-CAL closed-loop re-derive report.md`):

  SC-55 residual     +1.74  ->  +17.82 dB
  S-YXG50 residual   -1.87  ->  +14.08 dB     (the two references agree to 0.01 dB)
  ferro int_F        +7.1   ->   -8.5  dB     (self-referential, no reference used)
  pitch tilt          0.9   ->   10.6  dB

Independently corroborated by the balance diagnostic added the same day
(`crates/ferrosintesis/src/balance.rs::report_trim_effect_on_family_spread`),
which measures the Lead family spanning 16.16 dB with GM85 as its quietest
member, on a different metric (early-window RMS) and a different code path.

CAUSE. Commit ec8bfd7 ("give GM 84, 85 and 93 their defining characters",
2026-07-25) replaced GM85's velocity-tracked lowpass with a three-band vocal
formant bandpass bank, at crates/ferrosintesis/src/voices.rs:~7592. A bandpass
bank passes far less broadband energy than the lowpass it replaced, and no
make-up gain was added.

Its sibling in the SAME commit did get one. GM84 received
`LEAD84_NOMINAL = 0.46` and

    s.drive_norm = (spec.drive * LEAD84_NOMINAL).tanh() / LEAD84_NOMINAL

and drifted only +0.17 dB. GM93, also in that commit, moved +0.67 dB — inside
the dead-band. So the principle was applied to one voice of three and missed on
this one. The commit message even states it: "gain at the level the voice
actually runs at (LEAD84_NOMINAL)".

FIX AT THE VOICE, NOT IN THE TRIM TABLE. The loss is register-dependent — the
pitch tilt went from 0.9 to 10.6 dB — so no scalar in PROGRAM_TRIM_DB can
correct it. It needs a formant-bank make-up gain computed at the level the voice
actually runs at, in the same shape as GM84's.

WHY NOTHING CAUGHT IT. The M-CAL residual oracle skips guard-excluded programs,
and the regression is large enough to trip the pitch-tilt guard itself, so the
program excluded itself from the check that would have flagged it. Only the
cross-run drift comparison found it. Worth considering whether a guard-excluded
program should be reported rather than silently dropped.

## Fix

<unfixed — raised only>

## Notes

## Fix (2026-07-25)

Fixed in ff31237. `SawStack` gained a `formant_makeup` field (default 1.0, an
exact IEEE-754 identity so every non-formant render stays bit-identical), set
only by the GM85 spec via `LEAD85_FORMANT_MAKEUP_DB = 16.0`.

16.0 dB is the fall the two references measured independently (SC-55 16.08,
S-YXG50 15.95), so this restores the level both had blessed before the
re-voicing rather than aiming at a family median. Verified: GM85 moved
-38.27 -> -22.27 dB and now sits +1.48 dB against its family median, matching
its pre-regression SC-55 residual of +1.74 dB.

The register tilt is deliberately left in: vocal formants sit at absolute
frequencies and do not transpose, which is what makes a formant read as a voice.
Flattening it would need a pitch-tracking gain - a voicing decision, not part of
this regression fix.

Guarded by `balance::tests::gm85_formant_bank_keeps_its_make_up_gain`, which
pins GM85 within 6 dB of GM84 (post-fix +3.5; the regression was -12.6).

NOT closed by its own fixer - the ledger's two-eyes rule applies.
