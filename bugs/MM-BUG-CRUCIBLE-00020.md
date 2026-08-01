# MM-BUG-CRUCIBLE-00020 — Archive rebuilds can attest stale extraction leftovers

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / archive provenance
- **Raised:** 2026-08-01
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
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`) -> Fixed (2026-08-01T06:15:08Z, deltic:auto role=fix run=fix-20260801T060800Z-p83800-n615076000-c1 branch=task/bug-MM-BUG-CRUCIBLE-00020-run-fix-20260801T060800Z-p83800-n615076000-c1 code=86b23cca7bba88b9f5b78cd536c5664c733bd305 gate=manual) -> Closed (2026-08-01, independently verified by Claude Opus 5 on trunk 9b325c9; fixer was OpenAI GPT-5 Codex)

## Observation

`rebuild_archive_cache()` extracts a verified 7z archive into the persistent
`src/<extract_subdir>` directory at
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\tools\ferrosintesis-samples\prepare.py:1431`.
The `7z x -y` call at line 1446 overwrites present members but does not remove paths left
by an older extraction. Lines 1454–1456 then copy requested paths from that mixed directory,
and lines 1486–1487 write a fresh manifest under the new archive pin.

Static reproduction: retain an extracted bass member from the old archive, advance to a
valid new pinned archive that omits or renames that member, and rebuild. The old path remains,
the copy succeeds, and the new manifest positively attests stale bytes as originating from
an archive that never contained them.

Expected: a missing selected member in the pinned archive fails closed without changing
the cache or manifest. Actual: persistent extraction state can satisfy the copy.

The separate Salamander path was staged under closed `MM-BUG-KILN-00134`; the shared 7z
helper remains persistent. This defect was previously confirmed in
`D:\worktrees\ferrosintesis\20260801-REV-CLA@CRUCIBLE-code-review-033412\wrk_docs\2026.07.27 - CR - 20260727-REV-CLA@KILN-code-review-074202.md:77`,
but no bug file was created.

## Fix

Extract each rebuild into a fresh temporary directory. Validate that every selected member
exists there, stage the complete destination set, and only then publish cache files and the
manifest. Add a regression that pre-seeds an old extracted member, omits it from the new
extraction, and requires failure with no destination or manifest update.

### Verification summary (2026-08-01, Claude Opus 5, independent)

Verified on trunk `9b325c9` in worktree
`D:\worktrees\ferrosintesis\20260801-TSK-HUM-bug-verify-crucible-15-21`.

**Root cause addressed, and in the right order.** `rebuild_archive_cache` now
extracts into a fresh `tempfile.TemporaryDirectory` under `src`, checks every
selected member exists there (raising `ValueError` naming the missing member),
stages the complete destination set, and only then publishes with
`atomic_replace`. Validate-all-then-publish is what makes the failure leave the
old cache *and* its manifest untouched rather than half-updated.

**Fails-before proved by reverting only the extraction body.** Restoring the
pre-fix persistent `src/<extract_subdir>` extraction (test untouched) made
`ArchiveExtractionIsolationTest::test_missing_new_archive_member_cannot_be_attested_from_an_old_extraction`
fail with `ValueError not raised` — the stale extracted member satisfied the copy
and the run would have written a fresh manifest attesting bytes the new archive
never contained, exactly as reported. Restoring `prepare.py` (md5 `9a89dc4b…`)
turned it green.

**Gates.** `python3 -m unittest test_prepare` from `tools/ferrosintesis-samples/`:
139 tests, all pass.

## Notes

Static review only. No generator, application, test, build, render, or exploratory harness
ran. Estimated effort: Small–Medium.
