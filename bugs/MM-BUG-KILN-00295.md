# MM-BUG-KILN-00295 — the_cli_help_text_states_the_real_defaults never binds a default to its flag, and does not read the help text

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** crates/ferrosintesis
- **Raised:** 2026-08-17T22:48:36Z
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
- **State history:** Open (2026-08-17T22:48:36Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** The oracle `the_cli_help_text_states_the_real_defaults`
(`crates/ferrosintesis/src/render_profile.rs:379-405`) passes on documentation that states
every default against the **wrong flag**, on documentation that names no flags at all, and
on a `--help` text that states no defaults whatsoever. It does not check what its name
claims.

**Two independent holes.**

*1 — no value is bound to its flag.* Lines 383-387 flatten every `//!` line plus every line
containing `usage:` into one blob. Lines 393-397 then ask only whether *some*
whitespace-separated token anywhere in that blob parses to `want`. The `flag` binding is
used solely in the panic message at line 400. Adversarial counterexample — replace
`crates/ferrosintesis-cli/src/main.rs:4-5` with every default attached to the wrong flag:

```
//!     ferrosintesis input.mid [-o out.wav] [--rate 0.32] [--wet 44100]
//!                 [--delay MS] [--tail 6] [--solo CH[,CH...]] [-q]
```

Authority values are `sr: 44_100.0`, `wet: 0.32`, `tail: 6.0`
(`crates/ferrosintesis/src/engine.rs:1826-1828`). `split_whitespace` yields `0.32]`,
`44100]`, `6]`; the `trim_matches` closure at line 394 keeps alphanumerics, `.` and `-`, so
they reduce to `0.32`, `44100`, `6`; `num` (lines 71-81) parses all three. The `--rate`
iteration wants 44100 and finds it — sitting in the `--wet` slot. The `--wet` iteration
wants 0.32 and finds it in the `--rate` slot. **All three assertions pass.** So does a
doc-comment mentioning no flags at all, e.g. `//! Released 2026; 44100 lines, 0.32 s, 6
movements`.

*2 — it does not read the help text.* `--help` prints only `usage()`
(`crates/ferrosintesis-cli/src/main.rs:20-25`), whose text is `[--rate N] [--wet X]
[--tail S]` — it states **no** defaults for those three flags at all. The oracle is
satisfied entirely by the crate-level `//!` comment, which no user ever sees. The actual
help text could state every default wrongly, or omit them, and the test stays green.

**Why this matters here.** `render_profile.rs:1-46` exists precisely to stop restated
defaults drifting (MM-REQ-KILN-00032), and its own module doc says "a stale one misleads
exactly the reader who cannot check". This assertion is the one in the module that does not
deliver that. CLAUDE.md's standing lesson names this failure mode directly: "write the
adversarial document that *should* fail your oracle, and check that it does" — that was
never done for this one.

**Expected.** The oracle finds each flag in the user-visible help text and checks the token
that follows it against the library default.

**Actual.** It checks that the flag's default value appears *somewhere* in a blob that
includes a non-user-visible comment.

**The correct shape already exists in the same file.** `the_readme_options_table_states_the_
real_defaults` (`render_profile.rs:328-377`) locates the row starting `` | `{builder}` `` and
reads cell 3 — value bound to key. Copy that discipline.

## Fix

<unfixed — raised only>

Suggested shape:

1. Build the blob from the `usage()` string only, not from `//!` lines — that is the text
   a user actually reads. Update `usage()` to state the defaults it currently omits (it
   already states the `-18 LUFS` / `-1 dBTP` ones, so this is consistent with its style).
2. For each flag, locate the flag token in that text and parse the token that follows it;
   assert *that* token equals the library default. A flag absent from the text is a
   failure, not a silent pass.
3. Before landing, verify the fixed oracle **fails** on the swapped-flag counterexample
   above and on a help text with the defaults removed, then restore.

## Notes

- Found by adversarially attacking the oracle rather than confirming it — the method
  CLAUDE.md prescribes after KILN-00071/00072/00073.
- Filed against `crates/ferrosintesis` because the test lives there, though its subject is
  `crates/ferrosintesis-cli/src/main.rs`.
- Not a present mismatch: the CLI's current doc-comment does state the right values against
  the right flags. This is drift *risk* plus a mis-scoped subject, the same classification
  MM-REQ-KILN-00032 carried.
