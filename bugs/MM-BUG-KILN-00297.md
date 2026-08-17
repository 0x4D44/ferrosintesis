# MM-BUG-KILN-00297 — CLI argument handling breaks conventions: --help to stderr with exit 2, no --version, unknown flags taken as the input path

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:49:50Z
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
- **State history:** Open (2026-08-17T22:49:50Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

`ferrosintesis-cli` is published on crates.io and is the only installable entry point to the
synthesizer (`cargo install ferrosintesis` installs nothing). Its hand-rolled argument loop
(`crates/ferrosintesis-cli/src/main.rs:46-109`) breaks three conventions a user or script
will rely on. One root cause: the loop has no notion of an unknown flag, and `usage()` does
double duty as both the help output and the error output.

**1 — `--help` writes to stderr and exits 2.** `usage()` (`main.rs:20-25`) is
`eprintln!` + `std::process::exit(2)`, and `-h` / `--help` calls it (`main.rs:104`). So
`ferrosintesis --help` writes **zero bytes to stdout** and returns a failure status.
`ferrosintesis --help | less`, `ferrosintesis --help > usage.txt`, and any
`if ferrosintesis --help; then` probe all break. GNU/POSIX convention is that *requested*
help goes to stdout with exit 0. The same function is correct as the *error* path
(`main.rs:49, 54, 60, 66, 73, 81, 87, 91, 99, 106, 109`), where stderr + exit 2 is right —
the defect is the single shared exit for two different outcomes.

**2 — there is no `--version`.** No `--version` / `-V` arm exists in the match
(`main.rs:48-107`) and `CARGO_PKG_VERSION` is never referenced anywhere in the crate.
`ferrosintesis --version` therefore falls through to `_ if input.is_none()`
(`main.rs:105`), becomes the *input path*, and dies at `main.rs:112` inside
`reject_input_alias` → `output.rs:27` `fs::canonicalize(input)?`. The user sees
`error: The system cannot find the file specified. (os error 2)` (Windows) or
`No such file or directory (os error 2)` (unix), exit 1 — no version, no mention of
`--version`, no hint the flag was unknown. For a published binary this is the first thing a
bug reporter tries.

**3 — an unknown flag is silently accepted as the filename.** `main.rs:105` has no
leading-`-` guard, so the first unrecognised token becomes the input path unconditionally.
`ferrosintesis --bogus song.mid` sets input to `--bogus`, then `song.mid` hits `_ => usage()`
at `main.rs:106` and exits 2 with a usage dump that never names the offending token;
`ferrosintesis --bogus` alone produces the bare `os error 2` above. The same unknown flag
placed *after* the input is correctly rejected — so whether the CLI notices a typo depends
purely on argument order.

**Expected.** `--help` on stdout, exit 0. `--version` prints the crate version, exit 0. A
token starting with `-` that matches no flag is reported by name as an unknown option,
whatever its position.

**Actual.** As above.

None of this is documented in `crates/ferrosintesis-cli/README.md` or the module
doc-comment.

## Fix

<unfixed — raised only>

Suggested shape, no new dependency (the workspace forbids registry deps):

1. Split `usage()` into `help() -> !` (stdout, exit 0) and `usage_error(msg: &str) -> !`
   (stderr, names the offending token, exit 2). Point `-h`/`--help` at the first and every
   existing error site at the second.
2. Add `--version` / `-V` printing `concat!("ferrosintesis ", env!("CARGO_PKG_VERSION"))`,
   exit 0.
3. Change the catch-all at `main.rs:105-106` to reject a token starting with `-` as an
   unknown option *before* the `input.is_none()` arm. Add `--` as the end-of-options
   separator so a file legitimately named `-x.mid` stays reachable.
4. Regressions: `--help` exits 0 with non-empty stdout; `--version` exits 0 and its stdout
   contains `CARGO_PKG_VERSION`; `--bogus song.mid` exits 2 and stderr names `--bogus`.
   Confirm each fails before the fix. The crate has **no** argument-parsing test today —
   `src/main.rs` holds a single test, about the `embedded-samples` feature flag
   (`main.rs:191-200`).

## Notes

- Symptom 2's opaque message is compounded by pre-load I/O errors dropping the file path;
  that is tracked separately.
- Deliberately grouped as one record: all three are the same missing concept (an unknown-flag
  / help-vs-error distinction in the arg loop) and one small pass fixes them together.
- Raised by an autonomous read-only code-review pass. Established by reading `main.rs` and
  `output.rs`; not reproduced by running the binary — this pass does not run the app.
