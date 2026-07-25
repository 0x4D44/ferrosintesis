# MM-BUG-KILN-00116 — derive_trims.py's SHIPPED parser is unanchored and unchecked for uniqueness, so a sibling declaration silently yields a wrong table

- **State:** Open
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 5 (1M) @ high during the independent two-eyes verification of MM-BUG-KILN-00109; found by adversarially perturbing the parser the 00109 fix introduced)

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

## Notes
