# MM-BUG-KILN-00168 — B1 source recordings evade the committed-input provenance oracle

- **State:** Open
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=gpt-5.6-sol@high)

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

Pin both exact hashes in the B1 crate's packaged `PROVENANCE.md`. Replace or
widen the `*-src` directory-name predicate with a source registry or
source-derived predicate that covers every committed bake input, including
repo-root first-party archives. Add an adversarial control shaped like
`samples/b1-upright/` so another committed-source root cannot evade the scan.

## Notes

Draft requirement `MM-REQ-KILN-00144` covers publishing known exact source
pins. This bug is the residual predicate failure that prevents these B1 inputs
from being known or checked at all; it is not a duplicate of that requirement.

Estimated effort: Small–Medium.
