# MM-BUG-CRUCIBLE-00020 — Archive rebuilds can attest stale extraction leftovers

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / archive provenance
- **Raised:** 2026-08-01
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260801T060800Z-p83800-n615076000-c1
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-CRUCIBLE-00020-run-fix-20260801T060800Z-p83800-n615076000-c1
- **Owner base:** e4dd159b77baeed535b737e395b0a384c39212a9
- **Owner fingerprint:** -
- **Owner since:** 2026-08-01T06:08:00Z
- **Owner until:** 2026-08-01T08:08:00Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-01, raised by Codex GPT-5.6-Sol from a static multi-lens review; ID allocated per `bugs/README.md`)

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

## Notes

Static review only. No generator, application, test, build, render, or exploratory harness
ran. Estimated effort: Small–Medium.
