# MM-BUG-KILN-00228 — Packaged fret-noise README points to provenance data absent from the package

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise package documentation / provenance
- **Raised:** 2026-08-16T16:53:13Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T195712Z-ac780954
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00228-run-verify-20260913T195712Z-ac780954
- **Owner base:** dee9a7f63d86ea6d1abb00423300519a75abe4bd
- **Owner fingerprint:** sha256:72f7d026a84a4e24e882fb0fe1085e320f93e5e7b2c44ebcdd2b1b7dc5c71e2a
- **Owner since:** 2026-09-13T19:57:12Z
- **Owner until:** 2026-09-13T21:57:12Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T16:53:13Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T16:20:57Z, deltic:auto role=fix run=fix-20260913T161451Z-b2335558 branch=task/bug-MM-BUG-KILN-00228-run-fix-20260913T161451Z-b2335558 code=80747f5953794f95878245ed50a6971d3d22cd64 gate=manual)

## Observation

`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\README.md:22` tells package users that the take measurements and cut map are in the packaged `PROVENANCE.md`.

`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\PROVENANCE.md:18` instead says those details live in the repo-root
`samples/fret-noise-eastman-e1d/README.md`. The package allowlist at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\crates\ferrosintesis-samples-fretnoise\Cargo.toml:10` includes the crate README and provenance file, but not that repo-root source record. Cargo packages cannot include a file above the crate root.

**Expected.** A published-crate consumer can follow the README to the promised
measurements and cut-selection evidence.

**Actual.** The promised packaged document redirects to a file absent from the
package and gives no stable repository link. The source record exists and is
correct in this repository, so runtime audio and licensing are unaffected. The
defect is Low-severity published documentation.

## Fix

Unfixed. Either copy the promised measurements and cut map into the packaged
`PROVENANCE.md`, or state clearly that the detailed source record is external
to the crate package and provide a stable repository or commit link to it.

## Notes

The committed source record at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\samples\fret-noise-eastman-e1d\README.md:45` contains the complete twelve-row cut map. All fourteen source digests listed by packaged provenance match their current files.
