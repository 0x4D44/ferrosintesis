# MM-BUG-KILN-00215 — Two dulcimer onsets jump from silence

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** CC-BY dulcimer samples / onset continuity
- **Raised:** 2026-08-16T12:38:51Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-16T12:38:51Z, raised via `deltic bugs new`)

## Observation

Two packaged GM 15 onset assets begin away from silence:

- `D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-131612\crates\ferrosintesis-samples-ccby\samples\dulcimer_D5.wav` starts at signed PCM16 sample `-1272`.
- `D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-131612\crates\ferrosintesis-samples-ccby\samples\dulcimer_F#4.wav` starts at signed PCM16 sample `+2120`.

Both files peak at `29490`, so their first frames are 4.31% and 7.19% of the
sample peak. The GM 15 route wraps the modeled dulcimer in `LaVoice` at
`crates/ferrosintesis/src/voices.rs:14688`. `LaVoice::build` starts the source
at position zero (`crates/ferrosintesis/src/sampler.rs:3815-3832`), and
`LaVoice::render` reads frame zero immediately while the sample owns the onset
(`crates/ferrosintesis/src/sampler.rs:3851-3958`). A NoteOn therefore introduces
a deterministic nonzero edge from the preceding silence.

Expected: every one-shot onset enters from silence with a slope-bounded fade.
Actual: these two assets inject the nonzero frame directly. Audible click
perception is unverified because this was a static review and ran no render.

## Fix

Unfixed; raised only.

## Notes

Rebake the dulcimer family with the current `trim_to_onset` de-click path. Add
an adversarial opening-continuity oracle that rejects these files; the current
derived sweep compares frame zero with the largest motion in the first 10 ms,
so the larger attack motion lets both discontinuities pass. Estimated effort:
Small.

Static review only. No generator, app, test, build, render, package command, or
exploratory harness ran.
