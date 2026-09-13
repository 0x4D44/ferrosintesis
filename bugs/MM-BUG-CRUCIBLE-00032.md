# MM-BUG-CRUCIBLE-00032 — Non-finite normalization settings silently produce clipped or silent WAV output

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / normalization validation
- **Raised:** 2026-08-14T11:47:26Z
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
- **State history:** Open (2026-08-14T11:47:26Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T11:06:35Z, deltic:auto role=fix run=fix-20260815T105918Z-p8844-n753669700-c1 branch=task/bug-MM-BUG-CRUCIBLE-00032-run-fix-20260815T105918Z-p8844-n753669700-c1 code=236e96d gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: NaN and Inf LUFS and ceiling CLI runs exit 1 leaving prior output intact; both tests fail with validation removed)

## Observation

The public normalization constructors accept arbitrary `f32` values at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\offline.rs:35`.
No validation occurs before scratch files are created or audio is processed.

`Normalization::loudness(f32::NAN, -1.0)` produces a NaN gain; the i16 quantizer at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:4216`
casts the resulting NaNs to zero, silently writing a near-silent WAV. A finite target with
a NaN ceiling reaches `limiter_config` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\loudness.rs:484`;
comparisons against the NaN ceiling never apply gain reduction, silently disabling the
promised limit. `Normalization::peak(NaN)` has the same silent-output class.

Expected: the fallible file-rendering API rejects non-finite normalization settings before
touching output. Actual: it succeeds with clipped or silent audio and no diagnostic.

## Fix

Validate every normalization target and ceiling as finite and within documented ranges at
the start of `render_to_wav`, before reserving scratch or changing the destination. Return
`InvalidInput`. Define explicit behavior for the infallible in-memory helpers or add
fallible variants. Add NaN and ±Inf tests for peak, loudness target, and ceiling that also
prove an existing destination remains unchanged. Estimated effort: Small/Medium.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `236e96d3`) by an agent other than the fixer.

**Original observation re-run.** CLI runs with `--lufs NaN`, `--lufs inf`, `--tp-ceiling NaN` and `--tp-ceiling -inf` each exit 1 with "not a finite value", and the existing destination still holds its prior content.

**Fails-before (method B).** Removing `validate_normalization` and the non-finite guard in `normalize_loudness` fails both regressions ("loudness target NaN was accepted"; "a non-finite setting produced silence"). Restored; `git diff` empty; both pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
