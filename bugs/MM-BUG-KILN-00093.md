# MM-BUG-KILN-00093 — The fret-noise asset crate declares a README that does not exist

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** fret-noise sample package / publication
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; `4ad6947` supplied the missing README, then its API/bake contract and a source-derived package-path oracle completed the fix; awaiting independent two-eyes verification)

## Observation

`crates/ferrosintesis-samples-fretnoise/Cargo.toml:9` declares
`readme = "README.md"`, and line 10 explicitly includes that path in the package.
No `README.md` exists or is tracked under the crate. The tracked root contains only
`Cargo.toml`, `PROVENANCE.md`, `src/`, and `samples/`; every other current
`ferrosintesis-samples-*` crate has its declared README.

**Expected.** The publishable asset crate contains the README named by its manifest,
so its package archive is complete and its bank, format, provenance, and regeneration
contract are visible to package users.

**Actual.** Local path builds can consume the crate without reading its package
README, but the normal Cargo packaging/publication path cannot supply the
manifest-declared file. This asset crate must be published before `ferrosintesis`,
which exact-pins it at `=0.1.0`, so the omission also blocks that release sequence.

No package dry-run was run in this read-only review. The failure follows directly
from the manifest naming an absent file; exact Cargo failure text remains unverified.

## Fix

Commit `4ad6947` added the missing README after this bug was raised and before
this fixing pass began. `cargo package -p ferrosintesis-samples-fretnoise
--list --allow-dirty --locked` now succeeds and lists the README, provenance,
source, and all twelve WAVs.

This pass completed the README contract with the public `get`, `take_name`, and
`ROUND_ROBINS` API plus the exact bake command. It also added a source-derived
oracle over all 25 `ferrosintesis-samples-*` crates: every explicit `readme` and
literal `include` path must exist. An adversarial multi-line manifest proves a
missing README is reported while glob entries remain Cargo's responsibility.

The complete inventory module and focused clippy pass. The new package-path
checks also pass on Rust 1.87.

## Notes

The crate also omits the repository-required packaged `LICENSE-CC0`. That broader
legal-text omission is already covered by open `MM-BUG-KILN-00089`, whose fix calls
for a derived package-content check across every CC0 asset crate; it is not duplicated
here.
