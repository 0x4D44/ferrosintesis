# MM-BUG-KILN-00193 — Published orchestral2 provenance links licence evidence outside the package

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / orchestral2 licence evidence
- **Raised:** 2026-08-13T22:54:39Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T195332Z-398564c1
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00193-run-verify-20260913T195332Z-398564c1
- **Owner base:** 1652216c88848015d8c0d90429123a67f91f0e41
- **Owner fingerprint:** sha256:adb0a2031bfe65af3d313d11300513cc76e689d5ccb5f7e393b1981534d1fbcb
- **Owner since:** 2026-09-13T19:53:32Z
- **Owner until:** 2026-09-13T21:53:32Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-13T22:54:39Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-08-15T15:43:57Z, deltic:auto role=fix run=fix-20260815T153642Z-p13472-n987109500-c1 branch=task/bug-MM-BUG-KILN-00193-run-fix-20260815T153642Z-p13472-n987109500-c1 code=a6abb0c gate=manual)

## Observation

`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\PROVENANCE.md:70` says the music-box
CC0 check is backed by the bundled Freesound manifest and links to
`../../tools/ferrosintesis-samples/freesound-src/_readme_and_license_44539.txt`.
The crate manifest at
`D:\worktrees\ferrosintesis\20260813-REV-MM-CDX@KILN-code-review-233709\crates\ferrosintesis-samples-orchestral2\Cargo.toml:10` packages only `src/**`,
`samples/**`, `README.md`, `PROVENANCE.md`, and `LICENSE-CC0`. The linked target
is outside the crate and is absent from the published archive, so the relative
link is broken for a crates.io consumer. The prose and SHA-256 travel; the
cited upstream evidence does not.

Expected: a packaged provenance link resolves inside the published package,
especially where the document promises retained offline licence evidence.
Actual: the only linked evidence file remains repository-only. Package a local
copy of the retained manifest (or an equivalent immutable evidence snapshot),
link to that package-local path, and include it in Cargo's package file set.
Add a package-path oracle that rejects provenance links escaping or missing
from the archive. Static review only; no package command or network access ran.

## Fix

<unfixed — raised only>

## Notes

The current retained repository file exists, is tracked, and its documented
SHA-256 matches. This defect is distribution completeness, not a challenge to
the current CC0 classification.
