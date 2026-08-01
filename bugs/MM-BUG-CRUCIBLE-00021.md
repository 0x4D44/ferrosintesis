# MM-BUG-CRUCIBLE-00021 — Six bass samples inject a note-on discontinuity

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** electric-bass samples / onset de-click
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:25:42Z, deltic:auto role=fix run=fix-20260801T061614Z-p88600-n294560700-c1 branch=task/bug-MM-BUG-CRUCIBLE-00021-run-fix-20260801T061614Z-p88600-n294560700-c1 code=bea209f04e9d5980d495fda2b01d950250c8fb2a gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 9b325c9; fixer was OpenAI GPT-5 Codex)

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

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `9b325c9` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-15-21`.

**Original observation reproduced verbatim on the shipped assets.** Reading the
first PCM frame of all 13 committed bass WAVs at `bea209f^` and at trunk:

| sample | pre-fix frame 0 | post-fix |
|---|---|---|
| fingerbass_E1 | -1248 | 0 |
| fingerbass_F#1 | +1647 | 0 |
| pickbass_E1 | -1053 | 0 |
| pickbass_E2 | -932 | 0 |
| pickbass_F#1 | -7471 | 0 |
| pickbass_G#1 | -1072 | 0 |

Exactly the six files and the six values the report names, and the worst
(-7471/32768 = -0.22800) matches its "-0.227997 full scale". The other seven were
already 0 and still are.

**The attack survives — measured, not assumed.** Peak amplitude is unchanged at
29490 in all six, and only 3-84 frames differ per file (<= 1.9 ms at 44.1 kHz), so
the micro-fade is confined to the window it targets and leaves the transient
untouched. The 849-test `ferrosintesis` suite (which carries the sampler onset and
perceptual oracles over this bank) is green on the regenerated assets.

**Fails-before proved twice, for both halves of the regression.**
- Copying the pre-fix WAVs back in made `test_committed_bass_bank_starts_with_
  continuous_pcm` fail on 6 of 13 subtests -- the same six files.
- Disabling only the new zero-lead micro-fade in `trim_to_onset` made
  `test_frame_zero_onset_is_declicked_without_erasing_the_attack` fail with a
  first-frame step of 0.360 against an ordinary step of 0.017 -- a 21x
  discontinuity.
Restoring `prepare.py` (md5 `9a89dc4b…`) and the WAVs turned both green;
`git status` clean.

**Gates.** `python3 -m unittest test_prepare`: 139 pass. `cargo test -p
ferrosintesis`: 849 pass / 0 fail / 44 ignored (pre-existing), plus 4 doc-tests.
I did not re-bake the bank from its source archive — that needs a network fetch of
the pinned 7z — so reproducibility of the regenerated WAVs from `prepare.py` is
inferred from the unit tests, not observed.

## Notes

Static review only. No application, generator, test, build, render, listening check, or
exploratory harness ran. Estimated effort: Small.
