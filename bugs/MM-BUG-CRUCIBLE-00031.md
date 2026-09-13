# MM-BUG-CRUCIBLE-00031 — Loudness normalization skips the true-peak ceiling when loudness is already on target

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / loudness normalization
- **Raised:** 2026-08-14T11:47:25Z
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
- **State history:** Open (2026-08-14T11:47:25Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T10:58:37Z, deltic:auto role=fix run=fix-20260815T104337Z-p42868-n011065400-c1 branch=task/bug-MM-BUG-CRUCIBLE-00031-run-fix-20260815T104337Z-p42868-n011065400-c1 code=e58a7bb gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: both normalizers fail at -0.92 dBTP against a -6 dBTP ceiling with the early on-target break restored)

## Observation

Both loudness-normalization implementations exit as soon as integrated loudness is within
0.3 LU of the target. The exit occurs before the required true-peak limiter at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:4259`
and
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\scratch.rs:124`.

A high-crest signal scaled so its loudness already equals the requested target, but whose
intersample peak exceeds the requested ceiling, takes the early `break` and is returned
unlimited. That contradicts the public promise at `engine.rs:4234-4245` and
`offline.rs:35-44` to hit the loudness target and constrain transients.

Existing tests exercise the limiter itself and signals that first need loudness gain. The
unity-gain normalizer test uses a ceiling above its signal. The scratch parity test compares
against the buffered implementation with the same control-flow bug, so it is not an
independent oracle.

## Fix

Apply the true-peak ceiling even when loudness starts inside tolerance. If limiting changes
the signal, remeasure and apply bounded makeup before limiting again. Add independent
buffered and scratch tests whose input is already on target but above a low ceiling; assert
both loudness and measured true peak, not parity between the two implementations alone.
Estimated effort: Small/Medium.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `e58a7bbb`) by an agent other than the fixer.

Both new tests are the reproducer: a 997 Hz tone above a -6 dBTP ceiling, with the target set to its own measured loudness so normalization starts on target; they measure true peak and loudness of the output directly.

**Fails-before (method B).** Restoring the early on-target `break` in `engine.rs` and `scratch.rs` fails both ("-0.92 dBTP against a -6.0 dBTP ceiling"). Restored; `git diff` empty; both pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
