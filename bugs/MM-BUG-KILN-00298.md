# MM-BUG-KILN-00298 — Pre-load I/O errors from the alias check drop the file path the library deliberately preserves

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:50:18Z
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
- **State history:** Open (2026-08-17T22:50:18Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** `ferrosintesis missing.mid` prints

```
error: The system cannot find the file specified. (os error 2)
```

with no filename. Every I/O failure that happens before the MIDI is loaded loses its path
the same way.

**Root cause.** `crates/ferrosintesis-cli/src/main.rs:112` runs
`output::reject_input_alias` *before* `offline::load` at `main.rs:117`.
`reject_input_alias` calls `fs::canonicalize(input)?` first
(`crates/ferrosintesis-cli/src/output.rs:27`), so a missing or unreadable input dies there,
and `main.rs:113` prints the bare `io::Error` with `eprintln!("error: {e}")`. Rust's std
does not stamp a path onto `io::Error`.

**This silently falsified an explicit library design decision.** The library goes out of its
way to carry the path: `crates/ferrosintesis/src/midi.rs:247-251` wraps the open failure in
`MidiError::Io { path, source }`, `crates/ferrosintesis/src/error.rs:108` formats it as
`"{path}: {source}"`, and `error.rs:172` asserts `"song.mid: no such file"` under the comment
*"Display keeps the path, which is what the CLI prints."* Since the alias check was inserted
ahead of `load`, that comment is false for every pre-load I/O failure — the CLI no longer
reaches the code the test is describing.

**Expected.** `error: missing.mid: The system cannot find the file specified. (os error 2)`.

**Actual.** The path is dropped.

**Where it actually costs something.** Not the tidy interactive case — the user typed the
path. It matters when the message is the only evidence: a shell loop rendering many albums
reports a bare `os error 2` naming no track; and the Windows sharing-violation misfire tracked
in MM-BUG-KILN-00294 produces `os error 32` where the user cannot tell *which* of the two
files is locked.

No CLI test covers the missing-input message — `tests/` holds only `output_safety.rs` and
`wav_reader.rs`.

## Fix

<unfixed — raised only>

Suggested shape: have `reject_input_alias` attach the path to the I/O errors it raises, or
have `main.rs:112-115` print `error: {}: {e}` naming whichever path the check was touching.
The first is better — `output.rs` knows which of the two paths failed and the caller does
not. Add a regression asserting the missing-input message contains the filename; confirm it
fails first.

## Notes

- Raised by an autonomous read-only code-review pass; established by reading `main.rs`,
  `output.rs`, `midi.rs` and `error.rs`. Not reproduced by running the binary — this pass
  does not run the app.
- Small and mechanical, but worth the record because it makes an in-tree test comment
  (`error.rs:171-172`) describe behaviour that no longer occurs, which is how the next
  reader gets misled.
