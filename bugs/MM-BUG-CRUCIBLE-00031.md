# MM-BUG-CRUCIBLE-00031 — Loudness normalization skips the true-peak ceiling when loudness is already on target

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / loudness normalization
- **Raised:** 2026-08-14T11:47:25Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T104337Z-p42868-n011065400-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00031-run-fix-20260815T104337Z-p42868-n011065400-c1
- **Owner base:** 8923ffcbc0e2fa004fecc79f0eee5ee6a55cc63e
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T10:43:37Z
- **Owner until:** 2026-08-15T12:43:37Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-14T11:47:25Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh)

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
