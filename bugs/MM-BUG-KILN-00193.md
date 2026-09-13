# MM-BUG-KILN-00193 — Published orchestral2 provenance links licence evidence outside the package

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / orchestral2 licence evidence
- **Raised:** 2026-08-13T22:54:39Z
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
- **State history:** Open (2026-08-13T22:54:39Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-08-15T15:43:57Z, deltic:auto role=fix run=fix-20260815T153642Z-p13472-n987109500-c1 branch=task/bug-MM-BUG-KILN-00193-run-fix-20260815T153642Z-p13472-n987109500-c1 code=a6abb0c gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: licence evidence packaged and linked crate-locally; its link oracle's #fragment false positive (triggered by KILN-00258) split to MM-BUG-CRU-00057)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `a6abb0c7`) by an agent other than the fixer.

**Original observation re-derived.** The orchestral2 and ccby PROVENANCE link `licence-evidence/...` inside the crate, `include` lists `licence-evidence/**`, `cargo package --list --offline` shows the evidence in both archives, and the hashes match their pins.

**Fails-before (method A).** At `a6abb0c7^` the link was `../../tools/...`, which the new oracle's escape arm rejects.

**Residual split to MM-BUG-CRU-00057 (Must).** The oracle added here, `inventory::tests::packaged_documents_never_link_outside_their_own_package`, joins a link target onto the crate directory without stripping `#fragment`. The valid link `README.md#lookup-keys` added by `5f4e6083` (KILN-00258) therefore fails it, turning `cargo test -p ferrosintesis` red on trunk.

## Notes

The current retained repository file exists, is tracked, and its documented
SHA-256 matches. This defect is distribution completeness, not a challenge to
the current CC0 classification.
