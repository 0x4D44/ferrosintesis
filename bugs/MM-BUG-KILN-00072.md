# MM-BUG-KILN-00072 — manifest.rs comment-stripping ignores TOML literal strings and braces in strings

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** packaging / build
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
- **State history:** Open (2026-07-24, split from MM-BUG-KILN-00067 on independent two-eyes closure; found by Codex GPT-5.6-Sol; recorded by Claude Opus 4.8 (1M)) → Fixed (2026-07-25, Codex GPT-5.6-Sol; TOML basic/literal string scanner and regressions landed; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded literal-string false positive reproduced by reverting only the scanner)

## Observation

**Symptom.** `no_manifest_uses_a_multi_line_inline_table`
(`crates/ferrosintesis/src/manifest.rs`) can both miss an invalid manifest and reject a
valid one, because its comment-stripping models only *one* of TOML's two string forms.

**Root cause.** `strip_comment` tracks `"` (basic strings) and treats any `#` outside
them as the start of a comment. TOML also has **literal strings** delimited by `'`, in
which `#` and `"` are ordinary characters and backslash is not an escape. Two consequences:

- **False positive** — a valid line whose literal string contains `#` is truncated at
  that `#`, discarding the closing brace, so the oracle reports an unclosed inline
  table that is not there. Example: `foo = { path = 'vendor/a#b' }`.
- **False negative** — a `"` inside a literal string flips the in-string state, so a
  genuinely malformed line afterwards can be mis-parsed and slip through.

The brace counting inherits the same weakness: braces inside strings are counted as
structure.

**Why it was not caught.** The companion test
`the_oracle_detects_the_shape_it_is_meant_to_catch` pins five shapes — the broken form,
the corrected form, a `#` inside a *basic* string, a commented-out brace and a
multi-line array. Every one of them uses `"`. The literal-string form was never
exercised, so the gap was invisible.

**Real-world likelihood is low**, which is why this is Low/Could: no manifest in this
workspace currently uses literal strings, and the entries are machine-uniform. It
matters because the oracle's whole justification is that it catches what the compiler
cannot — a guard with a parser hole is worth less than its docstring claims.

## Fix

Implemented in `crates/ferrosintesis/src/manifest.rs`. `structural_braces` now scans
comments and braces in one pass while tracking both TOML string forms. Basic strings
honour backslash escapes; literal strings do not. `#`, `{`, and `}` are data inside
either form.

The oracle documents its deliberate single-line limit. Multi-line basic (`"""`) and
literal (`'''`) strings need state across lines; no workspace manifest uses either.
If that changes, the narrow oracle must be replaced with a stateful TOML lexer.

The focused regression first failed on valid
`foo = { path = 'vendor/a#b' }`, proving the historical false positive. It now covers
that line, braces inside a literal string, and a literal `"` that previously hid a real
comment and malformed inline table.

Validation on 2026-07-25:

- Native focused manifest suite: 2 passed.
- Rust 1.87 focused manifest suite: 2 passed.
- `cargo clippy -p ferrosintesis --lib --tests -- -D warnings`: passed.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before: reverting **only** `structural_braces` to the pre-fix basic-string-only
comment stripper fails `the_oracle_detects_the_shape_it_is_meant_to_catch` at the assertion on
`foo = { path = 'vendor/a#b' }` — the recorded false positive, where the `#` inside a TOML
literal string truncates the line and discards its closing brace.

Green after: passes on trunk, including the two further literal-string shapes the fix added
(braces inside a literal string, and a literal `"` that previously hid a real comment).
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

- The KILN-00067 fix itself is sound: `cargo +1.87 check --workspace --exclude amp-lab`
  exits 0 and the oracle does catch the two original malformed tables. This concerns
  only the parser's edge cases.
- A cheaper alternative worth weighing: run `cargo +1.87 metadata --no-deps` in the gate
  and delete the text oracle entirely. Rejected for KILN-00067 because it needs a second
  toolchain installed on every machine, which the text check deliberately avoids — but if
  the fleet standardises on having 1.87 present, the real parser beats an approximation.
