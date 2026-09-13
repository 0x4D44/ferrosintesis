# MM-BUG-KILN-00246 — Dark-Salamander regeneration ignores the migrated FLAC grand sources

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** dark-Salamander sample generation / FLAC source migration
- **Raised:** 2026-08-16T22:56:45Z
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
- **State history:** Open (2026-08-16T22:56:45Z, raised via `deltic bugs new`)

## Observation

The supported dark-Salamander recipe derives its source inventory by selecting only
`grand_dir` names ending in `.wav` at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-234326\tools\ferrosintesis-samples\prepare.py:5032-5047`.
The source grand crate now contains 54 `.flac` files and zero WAVs. On the current
tree `source_names` is therefore empty, `expected_outputs` is empty, and the loop at
`prepare.py:5051-5069` transforms nothing.

Expected: `prepare.py --only=darkgrand` rebuilds all 54 dark-Salamander outputs from
the current raw-grand bank. Actual: after the grand FLAC migration it silently does
no source work and leaves the existing derived FLAC bank stale. This is a distinct
current symptom from `MM-BUG-KILN-00226`, which covers late-failure atomicity in the
former working WAV path. Static review only; the generator was not run.

## Fix

<unfixed — raised only. Decode the current FLAC grand sources through the shared
first-party decoder or a verified tool-time path, require the exact non-empty 54-file
source inventory before writing, emit the chosen final format, and add a clean-tree
negative control proving an empty source selection fails rather than succeeding.>

## Notes

The grand crate was the primary review area; this direct dependent was inspected
only to verify the regeneration contract broken by its format migration.
