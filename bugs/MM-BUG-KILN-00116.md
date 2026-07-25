# MM-BUG-KILN-00116 — derive_trims.py's SHIPPED parser is unanchored and unchecked for uniqueness, so a sibling declaration silently yields a wrong table

- **State:** Closed
- **Priority:** Must
- **Severity:** High
- **Area:** tooling / instrument balance
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00109; found by adversarially perturbing the parser the 00109 fix introduced) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — the parser now accepts one exact declaration, rejects missing/duplicate tables, and the ordinary Rust gate pins its derivation invariant) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded SC55_ sibling repro returns all -9.9 with no raise pre-fix and the real table after; the new Rust oracle is load-bearing)

## Observation

`load_shipped()` at `tools/instrument-balance/derive_trims.py:140` finds the
shipped trim table with:

    re.search(r"PROGRAM_TRIM_DB\s*:\s*\[\s*f32\s*;\s*128\s*\]\s*=\s*\[(.*?)\]\s*;", text, re.S)

There is no `\bconst\s+` anchor, first match wins, and there is no check that the
declaration is unique. So any earlier-appearing declaration whose name merely
ENDS with `PROGRAM_TRIM_DB` is picked up instead of the real one.

EXECUTED REPRO. Inserting

    pub const SC55_PROGRAM_TRIM_DB: [f32; 128] = [-9.9; 128];  // expanded to 128 literals

above the real declaration in `crates/ferrosintesis/src/engine.rs` makes
`load_shipped()` return 128 values of -9.9 **with no raise**. The tool then
derives every proposal against a table that is not the shipped one.

This is the SAME failure mode as MM-BUG-KILN-00109 — the tool reasoning against a
trim table that is not what the synth ships — reached by a different route, and it
is a defect INTRODUCED BY 00109's FIX rather than a pre-existing one.

Latent today, not live: `re.findall` returns exactly one match on the current
`engine.rs`, and Rust forbids a same-name duplicate. But the tool builds a
two-reference panel (SC-55 and S-YXG50), so an `SC55_`- or `SYXG50_`-prefixed
sibling table is a plausible next edit, and the harm is identical to the bug this
parser was written to fix.

The 20-case perturbation suite run during 00109's verification found no OTHER
silent drop — whitespace, integer literals, `-0.0`, `-6.`, `1e0`, missing trailing
comma, split entries, one-per-line rustfmt style, `//`-commented entries and a
`]`-bearing comment all parsed correctly or raised loudly. A `#[cfg(feature=...)]`
-gated alternate table was the one other silent-wrong-table case, and it is the
same root cause as this entry.

This is the repo's recurring defect class in a new place — see CLAUDE.md,
"Hand-maintained lists are the recurring defect here — derive them", and the
KILN-00071..00073 lesson that a derived oracle gets holed by its own enumeration
predicate. `PROGRAM_TRIM_DB` was a hand-maintained assumption wearing a
source-scan's clothing.

## Suggested fix

Anchor the pattern with `\bconst\s+PROGRAM_TRIM_DB\b` and assert
`len(re.findall(...)) == 1`, raising on 0 or 2+ the same way the existing
failure paths already raise. Both are one-line changes to `load_shipped()`.

Note that nothing in the repo executes `derive_trims.py` — `.deltic-integrate.toml`
is cargo-only and `--selftest` never touches `SHIPPED` — so a Python-side test
would not run in any gate. The guard that would actually run is a Rust source-scan
oracle beside `crates/ferrosintesis/src/licensing.rs` and `manifest.rs`, asserting
that `derive_trims.py` assigns `SHIPPED` only from `load_shipped()`. That is the
pattern CLAUDE.md already prescribes for this defect class.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Raised by this model during the two-eyes verification of MM-BUG-KILN-00109 but **fixed by
GPT-5.6 Codex** in `3c7829c`, so verifying it here is the reporter's normal role, not a
self-closure.

**The recorded repro, executed on both sides.** Inserting
`pub const SC55_PROGRAM_TRIM_DB: [f32; 128] = [-9.9; 128]` (expanded to 128 literals) above the
real declaration in a scratch copy of `engine.rs`, then calling `load_shipped()` from each
version of the tool:

| perturbation | pre-fix (`3c7829c^`) | post-fix (trunk) |
|---|---|---|
| `SC55_`-prefixed sibling above the real table | **no raise, 128 values all `-9.9`** | no raise, **the real table** |
| a second, duplicate real declaration | no raise, first match wins | **raises loudly** |

The first row is the Observation's "EXECUTED REPRO" reproduced exactly — silently deriving
against a table that is not the shipped one. The second row is the uniqueness hole the
Suggested-fix section asked for; pre-fix it was silently accepted, and post-fix it fails with
*"expected exactly one `const PROGRAM_TRIM_DB: [f32; 128] = [...]` … found 2"*. The real table
parsed by the fixed tool is 128 values with 54 non-zero, matching the shipped `engine.rs`.

**The guard runs where the bug said it had to.** The Observation was explicit that a
Python-side test would not run in any gate, and that the guard needed to be a Rust source
oracle beside `licensing.rs` and `manifest.rs`. That is what landed:
`balance::tests::trim_derivation_reads_one_exact_shipped_table` pins the `\bconst\s+PROGRAM_TRIM_DB\b`
anchor, the `findall` + `len(matches) != 1` uniqueness check, and that `SHIPPED` has exactly one
derived assignment.

**And that oracle is load-bearing.** It reads `derive_trims.py` at run time, so restoring the
pre-fix tool under the *same* test binary is a clean red-before: it fails immediately with
*"derive_trims.py must define parse_shipped before load_shipped"*. `python
tools/instrument-balance/derive_trims.py --selftest` also passes, reporting the exact/unique
shipped parser.

Gates on the verification worktree at `902a808`: `cargo fmt --all --check` clean; `cargo clippy
--workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean; the same clippy with
`--no-default-features` clean; `cargo test -p ferrosintesis --no-default-features --locked` 617 passed / 0 failed / 22 ignored plus 4 doc-tests;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 718 passed / 0 failed / 27 ignored in the ferrosintesis lib suite and no failures anywhere; `python
tools/ferrosintesis-samples/test_prepare.py` 33/33.

## Notes

## Resolution — 2026-07-25

`derive_trims.py` now separates source loading from a testable
`parse_shipped()` function. Its pattern is line-anchored to the exact Rust
`const PROGRAM_TRIM_DB` declaration, so prefixed siblings and commented-out
declarations do not match. It uses `findall` and requires exactly one match;
zero, duplicate, and cfg-gated alternate declarations fail loudly.

`SHIPPED` remains assigned exactly once from `load_shipped()`. A test-only Rust
source oracle in `balance.rs` runs in the normal repository gate and pins the
anchor, uniqueness check, and one derived assignment. This prevents the Python
self-test from being the only guard.

## Verification — 2026-07-25

- `python tools/instrument-balance/derive_trims.py --selftest` passes. Its new
  fixtures prove a preceding `SC55_PROGRAM_TRIM_DB` sibling is ignored and
  missing, commented, duplicate, and cfg-gated exact declarations are rejected.
- The new Rust source oracle passes with default and no default features.
- `$null | cargo test --locked -p ferrosintesis`: **718 unit tests and 4 doc
  tests passed; 27 diagnostics ignored**.
- `$null | cargo test --locked -p ferrosintesis --no-default-features`: **617
  unit tests and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes with all features and with no default
  features. Formatting and `git diff --check` pass.
- No audio render inventory is required: the changed Rust module is
  `#[cfg(test)]`, and the Python derivation tool does not ship in the synth.
