# MM-BUG-KILN-00298 — Pre-load I/O errors from the alias check drop the file path the library deliberately preserves

- **State:** Closed
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
- **State history:** Open (2026-08-17T22:50:18Z, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-09-13T23:06:18Z, deltic:auto role=fix run=fix-20260913T225802Z-54eaf8ae branch=task/bug-MM-BUG-KILN-00298-run-fix-20260913T225802Z-54eaf8ae code=f77f24488512b6f5296bde611018a8dd3f963c19 gate=manual) -> Closed (2026-09-14T22:04:11Z, independent verify by Claude Opus 5 on trunk 011738f6: pre-load I/O errors from the alias check now carry the path; ferrosintesis missing.mid names missing.mid, and dropping the wrap fails the regression test)

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

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `258e957b` (verifier worker) and `011738f6` (lead) by agents other than the fixer (fix `f77f2448`).

**Original observation, re-run live by the lead.** `ferrosintesis missing.mid` exits 1 with `error: missing.mid: The system cannot find the file specified. (os error 2)`, the exact message the record expected. On Windows the MM-BUG-KILN-00294 sharing violation now names `...\score.mid` too.

**Root cause check.** `output.rs` wraps every I/O error the alias check can raise with `path_error`: input and output `canonicalize`, the unix metadata calls, and the Windows input guard and output probe. The library's comment 'Display keeps the path, which is what the CLI prints' is true again for failures before load.

**Fails-before (method B).** `output_safety::missing_input_error_names_the_input_path` passes. Reverting `fs::canonicalize(input).map_err(|error| path_error(input, error))?` to `fs::canonicalize(input)?` fails it: 'missing input path was dropped: error: The system cannot find the file specified. (os error 2)'. Restored.

**Not split.** Only the input-canonicalize wrap has a test; the output and Windows-probe wraps are correct by reading. The Windows input-guard wrap was also observed in the MM-BUG-KILN-00294 live probe.

**Repo gate.** On `258e957b`: `cargo test -p ferrosintesis-cli --locked --all-targets` 32 passed, and the CLI no-default run 27 passed. On `1d87b00f`: fmt, all three clippy steps and `cargo test --workspace --all-targets` green. Still red on trunk, not caused by this fix: 4 `test_prepare.py` errors (MM-BUG-CRU-00068, reopened).

## Notes

- Raised by an autonomous read-only code-review pass; established by reading `main.rs`,
  `output.rs`, `midi.rs` and `error.rs`. Not reproduced by running the binary — this pass
  does not run the app.
- Small and mechanical, but worth the record because it makes an in-tree test comment
  (`error.rs:171-172`) describe behaviour that no longer occurs, which is how the next
  reader gets misled.
