# MM-BUG-CRUCIBLE-00031 — Loudness normalization skips the true-peak ceiling when loudness is already on target

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / loudness normalization
- **Raised:** 2026-08-14T11:47:25Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T191114Z-42ab7cac
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00031-run-verify-20260913T191114Z-42ab7cac
- **Owner base:** 8cfd384974b3f283bf5e484f5b74f71c66b38f4e
- **Owner fingerprint:** sha256:16df9d7833cbd97b074f882ac03e04b0535d88655765d4669a6450f49ab3ce40
- **Owner since:** 2026-09-13T19:11:14Z
- **Owner until:** 2026-09-13T21:11:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-14T11:47:25Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T10:58:37Z, deltic:auto role=fix run=fix-20260815T104337Z-p42868-n011065400-c1 branch=task/bug-MM-BUG-CRUCIBLE-00031-run-fix-20260815T104337Z-p42868-n011065400-c1 code=e58a7bb gate=manual)

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

## Notes
