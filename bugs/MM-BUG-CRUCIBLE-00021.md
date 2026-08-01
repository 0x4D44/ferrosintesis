# MM-BUG-CRUCIBLE-00021 — Six bass samples inject a note-on discontinuity

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** electric-bass samples / onset de-click
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T061614Z-p88600-n294560700-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00021-run-fix-20260801T061614Z-p88600-n294560700-c1
- **Owner base:** 3e98f7cf9b347aed150c660a502104c44dc4a40b
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T06:16:14Z
- **Owner until:** 2026-08-01T08:16:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`)

## Observation

`trim_to_onset()` promises to de-click generated attacks at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:2052`,
but an onset at source frame zero makes both `lead` and `fin` zero at lines 2078–2081,
so no fade is applied. Six of the thirteen committed bass WAVs have a nonzero first PCM
frame: finger E1 `-1248`, finger F#1 `+1647`, pick E1 `-1053`, pick E2 `-932`, pick F#1
`-7471`, and pick G#1 `-1072`.

The worst file,
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\crates\ferrosintesis-samples-bass\samples\pickbass_F#1.wav`
(PCM data frame 0), begins at `-0.227997` full scale. `LaVoice` starts at source position
zero and full additive sample weight at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\crates\ferrosintesis\src\sampler.rs:3814`
and `:3862`; the cubic reader returns that exact frame at fraction zero, then line 3957
adds it immediately. For GM 34 keys 30–31 at velocity 127, the gain table at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\crates\ferrosintesis\src\voices.rs:10499`
raises the first-frame contribution to about `-0.104` to `-0.114` full scale before model
summation.

Expected: a generated attack enters continuously from silence or within a bounded initial
slope. Actual: the sample overlay injects a one-sample step at NoteOn. Audibility was not
tested; the waveform discontinuity and output magnitude are source-confirmed.

## Fix

When no usable lead-in exists, apply a very short, data-aware micro-fade or zero-crossing
strategy that preserves the attack. Add an adversarial `trim_to_onset` fixture whose onset
is nonzero at frame zero, plus a bank-wide oracle that bounds silence-to-first-frame change
against ordinary adjacent steps. Retain the existing early-peak assertion so de-clicking
cannot erase the transient.

## Notes

Static review only. No application, generator, test, build, render, listening check, or
exploratory harness ran. Estimated effort: Small.
