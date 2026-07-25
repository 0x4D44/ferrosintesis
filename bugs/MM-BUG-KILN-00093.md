# MM-BUG-KILN-00093 — The fret-noise asset crate declares a README that does not exist

- **State:** Closed
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
- **State history:** Open (2026-07-24, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; `4ad6947` supplied the missing README, then its API/bake contract and a source-derived package-path oracle completed the fix; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 4.6, independent two-eyes on `d3ac026`; ran `cargo package -p ferrosintesis-samples-fretnoise --list --allow-dirty --locked` — exit 0, 19 entries including `README.md`, `PROVENANCE.md`, `src/lib.rs` and all twelve `fretnoise_rrNN.wav`; deleted the real README and re-ran it to observe the failure this bug predicted — exit 101, "readme `README.md` does not appear to exist"; `inventory::tests::every_sample_crate_package_path_exists` went red naming the missing path and green again once restored)

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

### Verification summary (2026-07-25, Claude Opus 4.6, independent — did not author the fix)

Verified against `d3ac026`, which already contains `4ad6947`. Every Fix claim held:

- `README.md` is tracked under the crate (`git ls-files`), alongside `Cargo.toml`,
  `PROVENANCE.md`, `src/lib.rs` and twelve WAVs.
- `cargo package -p ferrosintesis-samples-fretnoise --list --allow-dirty --locked`
  exits 0 and lists exactly what the Fix claims.
- The README names `get`, `take_name` and `ROUND_ROBINS` — all three are public in
  `src/lib.rs` — and its bake command resolves to the real
  `tools/ferrosintesis-samples/fretnoise_bake.py`.
- `crates/ferrosintesis/src/inventory.rs:289` `every_sample_crate_package_path_exists`
  enumerates the 25 sample crates from the filesystem. All 25 declare `readme` and
  `include` and have a `samples/` dir, and the test's own `malformed.is_empty()`
  assertion passes, so the scan really does check 25. Green on stable and on
  `cargo +1.87`; focused clippy clean.

The original Observation's unverified premise is now verified: with the README removed,
Cargo fails hard — exit 101, ``readme `README.md` does not appear to exist``.

**Adversarial probes against the new oracle** (all mutations reverted; tree confirmed
clean by `git status --porcelain`):

- Deleting the real README turned it **red**, naming `ferrosintesis-samples-fretnoise/README.md`.
  This matters because the sibling self-test injects its own `exists` closure and never
  touches disk — only this proves the guard is live.
- A synthetic 26th crate (`ferrosintesis-samples-advtest`, declaring an absent README)
  turned it **red** with no list edit anywhere. The enumeration genuinely auto-enrols
  new asset crates, which is the anti-drift property the fix claims.

**Two limits found, neither falsifying this fix — both are existence checks by design:**

- An **empty** `README.md` (0 bytes) passes all four inventory oracles. The oracle asserts
  existence, not substance — the same "mentioned is not credited" gap KILN-00071 found in
  the licensing oracles. A stub README would satisfy it.
- `readme` pointing outside the package (`../ferrosintesis-samples-core/README.md`) also
  passes, but so does Cargo: it warns and falls back to the in-root `README.md`, exit 0.
  No divergence from Cargo, so not a hole.
- The scan guards are floors (`out.len() > 15`, `checked > 20`), not equalities, so up to
  four crates could silently drop out and it would stay green — most plausibly a crate
  losing its `samples/` dir, which the `samples.is_dir()` predicate skips entirely.
  Worth tightening to an exact count if a future crate ever ships without `samples/`.

## Notes

The crate also omits the repository-required packaged `LICENSE-CC0`. That broader
legal-text omission is already covered by open `MM-BUG-KILN-00089`, whose fix calls
for a derived package-content check across every CC0 asset crate; it is not duplicated
here.

Confirmed still true at closure (2026-07-25): the crate root holds no `LICENSE-CC0`, and
`MM-BUG-KILN-00089` is still `Open`. Closing this bug does not close that gap.
