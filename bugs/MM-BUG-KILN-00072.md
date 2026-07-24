# MM-BUG-KILN-00072 — manifest.rs comment-stripping ignores TOML literal strings and braces in strings

- **State:** Open
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
- **State history:** Open (2026-07-24 — split from MM-BUG-KILN-00067 on its independent
  two-eyes closure. Found by Codex gpt-5.6-sol; recorded by Claude Opus 4.8 (1M), who
  wrote the oracle.)

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

Track both string forms in `strip_comment` and in the brace counter: on `'` enter a
literal string (no escapes, terminated by the next `'`); on `"` enter a basic string
(backslash escapes apply). Ignore `#`, `{` and `}` inside either.

Multi-line basic (`"""`) and literal (`'''`) strings are also legal TOML and would need
state across lines if this is ever pointed at a manifest that uses them; note the
limitation explicitly if not handled, rather than leaving it silent.

Extend `the_oracle_detects_the_shape_it_is_meant_to_catch` with the cases that exposed
this: `foo = { path = 'vendor/a#b' }` must pass, and a malformed table following a
literal string containing `"` must still fail.

## Notes

- The KILN-00067 fix itself is sound: `cargo +1.87 check --workspace --exclude amp-lab`
  exits 0 and the oracle does catch the two original malformed tables. This concerns
  only the parser's edge cases.
- A cheaper alternative worth weighing: run `cargo +1.87 metadata --no-deps` in the gate
  and delete the text oracle entirely. Rejected for KILN-00067 because it needs a second
  toolchain installed on every machine, which the text check deliberately avoids — but if
  the fleet standardises on having 1.87 present, the real parser beats an approximation.
