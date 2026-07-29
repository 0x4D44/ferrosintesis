# MM-BUG-KILN-00168 — B1 source recordings evade the committed-input provenance oracle

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** B1 sample provenance / source integrity
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-07-29, deltic:auto role=fix run=fix-20260728T232959Z-p58892-n493739700-c1 branch=task/bug-MM-BUG-KILN-00168-run-fix-20260728T232959Z-p58892-n493739700-c1 code=9df73cb gate=manual) -> Closed (2026-07-29, independently verified by Claude Opus 5 on trunk `be161eb`; original observation re-run, regression proven to fail without the fix, repo gates green; residual split to MM-BUG-KILN-00170)

## Observation

The published B1 provenance identifies two committed Opus files as the
reproducible source of record:

- `samples/b1-upright/DR0000_0195_normal_soft.opus`
- `samples/b1-upright/DR0000_0200_hard.opus`

Their current SHA-256 values are respectively:

- `a3f8fa906cbfb2706836ad6dd648e3267fad2dd0dadfd6c64fac06a2b3e5b602`
- `fa4b89c9b78db1b0a53c67a826cd8edac6e8d39c3f8765f3861d12ffaf0eb2d0`

Neither digest appears in the repository. The owning packaged provenance at
`D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-235149\crates\ferrosintesis-samples-b1-upright\PROVENANCE.md:27`
names the files but carries no immutable identity.

The provenance oracle says it covers every committed upstream source at
`D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-235149\crates\ferrosintesis\src\provenance.rs:1`,
but `source_dirs()` at
`D:\worktrees\midi-music\20260728-REV-CLA@KILN-code-review-235149\crates\ferrosintesis\src\provenance.rs:164`
enumerates only immediate directories matching
`tools/ferrosintesis-samples/*-src/`. The B1 sources live under the repo-root
`samples/` tree, so both are invisible to the oracle.

**Expected.** Every committed recording used as a published bank's source of
record is bound to an exact digest in that bank's packaged provenance, and a
source-derived oracle fails if the recording changes without the provenance
changing with it.

**Actual.** Either B1 source recording can change and the "every committed
source" oracle still passes because the directory predicate never enumerates
it. Git preserves each commit's bytes, but the separately published sample
crate cannot identify which source bytes its provenance and processing claims
describe.

No current tampering or output corruption was observed. This is a Low-severity
integrity and reproducibility defect in the oracle's enumeration predicate.

## Fix

### Proposed (at raise time)

Pin both exact hashes in the B1 crate's packaged `PROVENANCE.md`. Replace or
widen the `*-src` directory-name predicate with a source registry or
source-derived predicate that covers every committed bake input, including
repo-root first-party archives. Add an adversarial control shaped like
`samples/b1-upright/` so another committed-source root cannot evade the scan.

### As landed

Code commit `9df73cb`. Pins both committed B1 Opus digests in the crate's
packaged `PROVENANCE.md`, and extends committed-source discovery with an
explicit repo-root registry (`REPO_SOURCE_DIRS`) alongside the existing
`tools/ferrosintesis-samples/*-src` glob, so the B1 archives are scanned.

## Notes

Draft requirement `MM-REQ-KILN-00144` covers publishing known exact source
pins. This bug is the residual predicate failure that prevents these B1 inputs
from being known or checked at all; it is not a duplicate of that requirement.

Estimated effort: Small–Medium.

## Verification (2026-07-29, independent two-eyes, Claude Opus 5)

Re-ran the recorded observation. Recomputed both digests from the committed
files: `a3f8fa90...b602` and `fa4b89c9...b2d0`. Both now appear in
`crates/ferrosintesis-samples-b1-upright/PROVENANCE.md` bound to their exact
file paths, and both match the bytes on disk. The reported "neither digest
appears in the repository" no longer holds.

Enumeration widened: `samples/b1-upright` is in `source_dirs()`, and
`source_registry_covers_repo_root_b1_recordings` asserts both archives are
scanned and that a document naming them without hashes does not satisfy the
check.

Fails-before proven two ways. Emptying `REPO_SOURCE_DIRS` fails both
`every_committed_source_is_pinned_by_a_packaged_document` and
`source_registry_covers_repo_root_b1_recordings`. Falsifying one pinned digest
in the packaged `PROVENANCE.md` fails the former, naming
`samples/b1-upright/DR0000_0195_normal_soft.opus` exactly. Tree restored clean
after each.

Residual found and split, not left silent. The bug's own fix note asked for a
control "so another committed-source root cannot evade the scan". The delivered
control proves B1 names-without-hashes fail; it does not prevent a new root from
evading, because `REPO_SOURCE_DIRS` is a hand-maintained list. Enumerating the
whole set -- the repo's standing rule when a list is implicated -- shows three of
the four first-party roots under `samples/` are still uncovered and entirely
unpinned. That is a distinct defect from the recorded observation, so the
original closes and the gap is tracked as MM-BUG-KILN-00170.

Repo gates on the exact verified tree (trunk `be161eb`, worktree clean): `cargo test --workspace` exit 0 (no failures), `cargo clippy --workspace --all-targets -- -D warnings` exit 0, `cargo fmt --check` exit 0, and `python3 -m pytest tools/ferrosintesis-samples/test_prepare.py` 129 passed / 35 subtests.
