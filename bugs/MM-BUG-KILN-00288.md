# MM-BUG-KILN-00288 — Sample inventory guard skips multi-family aggregation crates

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample inventory / public package surfaces
- **Raised:** 2026-08-17T13:41:00Z
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
- **State history:** Open (2026-08-17T13:41:00Z, raised via `deltic bugs new`)

## Observation

The repository test that claims to check every sample crate's public inventory
silently disables its summary checks for aggregation crates. At
`D:\worktrees\ferrosintesis\20260817-REV-MM-CDX@KILN-code-review-141930\crates\ferrosintesis\src\inventory.rs:950`,
`partial_summary_error` returns `None` whenever a package has more than eight
families; line 966 also treats a summary that mentions no family as valid.

`ferrosintesis-samples-orchestral` has 15 packaged families, derived from the
filename prefixes in its 158-entry table. Its README uses bullets rather than the
family-table syntax the alternate branch recognizes, its prose does not trigger
the delegation fallback, and its documented `--only=<family>` placeholder is
discarded as non-concrete at line 896. The manifest description,
README introduction, and module docs are therefore unchecked. The live stale
claims recorded in `MM-BUG-KILN-00289` demonstrate the blind spot: the guard
counts this crate toward its anti-vacuity total while asserting nothing about
those surfaces.

Expected: aggregation crates receive at least as much inventory coverage as
small crates. Concrete fix: replace the size bail with a scalable rule, such as
requiring a complete family table or explicit delegation above eight families;
treat an empty mention set as an error for multi-family summaries. Add adversarial
fixtures for a 15-family package that names four families and one that names
none. Static source review only; the repository test was not run.

## Fix

<unfixed — raised only>

## Notes

The same predicate also affects `ferrosintesis-samples-orchestral2`; no open bug
in the current queue covers this `> 8` exemption.
