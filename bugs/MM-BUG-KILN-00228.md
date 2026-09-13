# MM-BUG-KILN-00228 — Packaged fret-noise README points to provenance data absent from the package

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** fret-noise package documentation / provenance
- **Raised:** 2026-08-16T16:53:13Z
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
- **State history:** Open (2026-08-16T16:53:13Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T16:20:57Z, deltic:auto role=fix run=fix-20260913T161451Z-b2335558 branch=task/bug-MM-BUG-KILN-00228-run-fix-20260913T161451Z-b2335558 code=80747f5953794f95878245ed50a6971d3d22cd64 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: packaged fret-noise PROVENANCE links the cut map at an immutable trunk commit; pre-fix PROVENANCE fails the crate test)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `80747f59`) by an agent other than the fixer.

**Original observation re-derived.** The packaged PROVENANCE says the detailed source record lives outside the crate and links it at commit `17804653`, which is on trunk; that commit's `samples/fret-noise-eastman-e1d/README.md` holds the level measurements and the 12-cut map. `cargo package --list` confirms README and PROVENANCE ship.

**Fails-before (method A).** With PROVENANCE.md from `80747f59^`, `tests::packaged_provenance_hands_off_to_the_immutable_source_record` fails. It passes on HEAD.

## Notes

The committed source record at
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-173412\samples\fret-noise-eastman-e1d\README.md:45` contains the complete twelve-row cut map. All fourteen source digests listed by packaged provenance match their current files.
