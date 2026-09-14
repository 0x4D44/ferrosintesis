# MM-BUG-KILN-00297 — CLI argument handling breaks conventions: --help to stderr with exit 2, no --version, unknown flags taken as the input path

- **State:** Closed
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
- **State history:** Open (2026-08-17T22:49:50Z, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-09-13T22:57:12Z, deltic:auto role=fix run=fix-20260913T224834Z-f41a6f70 branch=task/bug-MM-BUG-KILN-00297-run-fix-20260913T224834Z-f41a6f70 code=03e7af68c7d75415e6d542a22e1e375950309ee4 gate=manual) -> Closed (2026-09-14T22:01:21Z, independent verify by Claude Opus 5 on trunk 011738f6: --help prints to stdout and exits 0, --version exists, and an unknown option is named whatever its position; reversing each change fails its CLI test)

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

### Verification summary (2026-09-14, Claude Opus 5, independent)

Verified on trunks `258e957b` (verifier worker) and `011738f6` (lead) by agents other than the fixer (fix `03e7af68`).

**Original observation, re-run live by the lead.**
- `ferrosintesis --help` exits 0, with `usage: ferrosintesis <input.mid> ...` on stdout and nothing on stderr.
- `--version` exits 0 and prints `ferrosintesis 0.14.4`.
- `--bogus score.mid` and `score.mid --bogus` both exit 2 with 'error: unknown option `--bogus`' plus usage.
The worker also saw `-h` and `-V` behave the same, and `-- -x.mid` treat `-x.mid` as the input path.

**Root cause check.** Requested help (stdout, exit 0) and usage errors (stderr, exit 2) now have separate exits. A `--version`/`-V` arm exists. Any token starting with `-` that matches no flag is rejected by name before the input-path arm, and `--` ends option parsing. All three symptoms were fixed at their shared cause, the argument loop.

**Fails-before (method B).** `tests/cli_arguments.rs` has four tests, all passing. With help routed back to the usage error, the `--version` arm deleted and the unknown-option arm deleted:
- `help_is_successful_on_stdout` fails (exit 2, empty stdout);
- `version_is_successful_and_names_the_package` fails with the recorded symptom: exit 1, 'The system cannot find the file specified. (os error 2)';
- `unknown_option_is_named_regardless_of_position` fails.
`end_of_options_allows_a_dash_prefixed_input_path` stays green, as expected. Restored.

**Repo gate.** On `258e957b`: `cargo test -p ferrosintesis-cli --locked --all-targets` 32 passed, and the CLI no-default run 27 passed. On `1d87b00f`: fmt, all three clippy steps and `cargo test --workspace --all-targets` green. Still red on trunk, not caused by this fix: 4 `test_prepare.py` errors (MM-BUG-CRU-00068, reopened).

## Notes

- Symptom 2's opaque message is compounded by pre-load I/O errors dropping the file path;
  that is tracked separately.
- Deliberately grouped as one record: all three are the same missing concept (an unknown-flag
  / help-vs-error distinction in the arg loop) and one small pass fixes them together.
- Raised by an autonomous read-only code-review pass. Established by reading `main.rs` and
  `output.rs`; not reproduced by running the binary — this pass does not run the app.
