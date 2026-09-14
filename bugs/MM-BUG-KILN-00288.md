# MM-BUG-KILN-00288 — Sample inventory guard skips multi-family aggregation crates

- **State:** Closed
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
- **State history:** Open (2026-08-17T13:41:00Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T19:31:31Z, deltic:auto role=fix run=fix-20260913T190749Z-15df7645 branch=task/bug-MM-BUG-KILN-00288-run-fix-20260913T190749Z-15df7645 code=fd4768c77ca50a8d14b8b84ead17057767b8980d gate=manual) -> Closed (2026-09-14T21:50:03Z, independent verify by Claude Opus 5 on trunk 1d87b00f: the eight-family bail is gone; restoring it fails both 15-family adversarial tests, and the live orchestral crate is now checked)

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

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunk `1d87b00f` (fix `fd4768c7`) by an agent other than the fixer.

**Original observation.** `partial_summary_error` no longer returns `None` for packages with more than eight families, and an empty mention set on such a package is an error unless that surface delegates to `PROVENANCE.md`. The new `public_inventory_oracle_rejects_partial_large_summary` (4 of 15 families named) and `public_inventory_oracle_rejects_empty_large_summary` pass, as does the delegation control.

**Fails-before (method B).** Re-inserting `if packaged.len() > 8 { return None; }` fails both adversarial tests. Restored.

**Live coverage (the crate the observation named).** While verifying MM-BUG-CRU-00074, reverting the orchestral manifest description and README delegation produced 'ferrosintesis-samples-orchestral: manifest description summary names no packaged families (omits ... 15 families)' and a partial-family README error. Those errors come only from the path this fix opened, so the 15-family crate is now genuinely checked.

**Repo gate on `1d87b00f`.** Green: fmt, all three clippy steps, `cargo test -p ferrosintesis-cli --no-default-features`, and `cargo test --workspace --all-targets`. Red, not caused by this fix: `cargo test -p ferrosintesis --no-default-features` fails `no_default_gate_is_paired_with_embedded_sample_coverage` (MM-BUG-KILN-00301 reopened), and 4 `test_prepare.py` tests error (MM-BUG-CRU-00068 reopened).

## Notes

The same predicate also affects `ferrosintesis-samples-orchestral2`; no open bug
in the current queue covers this `> 8` exemption.
