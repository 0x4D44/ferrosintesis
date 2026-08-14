# MM-REQ-CRUCIBLE-00033 — Define explicit reset scopes and derived-state rehydration for channel strips

- **State:** Draft
- **Priority:** Should
- **Area:** ferrosintesis / engine reset policy
- **Raised:** 2026-08-14T11:47:27Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-14T11:47:27Z, raised via `deltic reqs new` model=gpt-5.6-sol@xhigh)

## Statement

Channel-strip reset and routing transitions must use explicit reset scopes and one shared
derived-state rehydration path. GM System On, XG System On, GS rhythm-part changes/Reset,
Reset All Controllers, bank changes, and Program Change each preserve different authored
state; adding a strip field must not rely on remembering several unrelated manual field
lists.

The implementation should name each scope, document the fields it preserves, and derive
kit selection, unauthored FX defaults, and program `Drive` from the final logical strip
state. A table-driven oracle must put a strip into non-default authored and derived states,
apply each reset/transition, and compare the result with a freshly constructed strip driven
to the same logical final state. Negative controls must show that an omitted derived field
or an incorrectly cleared authored field fails.

The current drift is visible across
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\engine.rs:1549-1665`,
`engine.rs:2441-2478`, `engine.rs:3121-3198`, and `engine.rs:3261-3336`. The concrete GS
state failure is tracked separately as MM-BUG-CRUCIBLE-00030; this requirement captures the
broader structural guard, not a second copy of that defect.

## Notes
