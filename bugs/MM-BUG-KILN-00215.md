# MM-BUG-KILN-00215 — Two dulcimer onsets jump from silence

- **State:** Closed
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
- **State history:** Open (2026-08-16T12:38:51Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T05:00:53Z, deltic:auto role=fix run=fix-20260913T045256Z-6fa24f72 branch=task/bug-MM-BUG-KILN-00215-run-fix-20260913T045256Z-6fa24f72 code=248076795ef6b043001f73dfe7d70936a80be737 gate=manual) -> Closed (2026-09-13T21:00:07Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: dulcimer D5 and F#4 frame0 were -1272 and +2120 and are 0 now; a census found five more such one-shots, split to MM-BUG-CRU-00066)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `24807679`) by an agent other than the fixer.

**Original observation re-run.** Decoding the committed FLACs: before the fix `dulcimer_D5` frame0 = -1272 and `dulcimer_F#4` = +2120 (peak 29490), exactly as recorded, and the old 10 ms sweep predicate passed them; at HEAD both are 0.

**Fails-before (method A).** The `24807679^` blobs fail `test_dulcimer_assets_enter_from_silence`'s own predicate (|frame0| <= 1 LSB). It passes on HEAD.

**Residual split to MM-BUG-CRU-00066.** The new oracle covers only dulcimer, and the general sweep still lets a large attack mask a frame-zero step. A census of 1015 packaged one-shots found five more starting far from silence (headroom C4/F#3 pp, orchestral steel_E4, strings cellosolo A3/C4 f).

## Notes

Rebake the dulcimer family with the current `trim_to_onset` de-click path. Add
an adversarial opening-continuity oracle that rejects these files; the current
derived sweep compares frame zero with the largest motion in the first 10 ms,
so the larger attack motion lets both discontinuities pass. Estimated effort:
Small.

Static review only. No generator, app, test, build, render, package command, or
exploratory harness ran.
