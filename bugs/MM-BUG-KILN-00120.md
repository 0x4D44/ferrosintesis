# MM-BUG-KILN-00120 — Windows identity probe reports aliasing for ANY sharing violation on the output path

- **State:** Fixed
- **Priority:** Could
- **Severity:** Low
- **Area:** crates/ferrosintesis-cli
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
- **State history:** Open (2026-07-25, raised via `deltic bugs new` model=claude-opus-5@high) → Fixed (2026-07-26, GPT-5.6 Codex on KILN-Windows — disambiguated self-induced and third-party Windows sharing violations)

## Observation

**Symptom.** `ferrosintesis <in.mid> -o <out.wav>` refuses to write, claiming the output
aliases the input, when the two are **entirely different files** — if any other process holds
the output path with a share mode that excludes read.

**Root cause.** `crates/ferrosintesis-cli/src/output.rs:59-65` establishes file identity on
Windows by holding the input with `share_mode(0)` and then probing the output:

```rust
let _input_guard = OpenOptions::new().read(true).share_mode(0).open(input)?;
match File::open(output) {
    Ok(_) => Ok(false),
    Err(error) if error.raw_os_error() == Some(ERROR_SHARING_VIOLATION) => Ok(true),
    Err(error) => Err(error),
}
```

Raw OS error 32 means "this name is not openable for reading right now" — which is strictly
weaker than "this name is the input". Any third-party handle that excludes `FILE_SHARE_READ`
produces the same error, so the probe attributes someone else's lock to our own guard. The
comment above it at `output.rs:57-59` overstates the guarantee, claiming the probe "asks the
kernel whether both names resolve to the same file object".

Nothing shields the misfire earlier: `fs::canonicalize` on Windows opens with `access_mode(0)`
precisely so metadata queries work on exclusively-held files, so the canonical-path comparison
at `output.rs:29-33` succeeds, finds the two paths different, and hands off to
`platform_same_file`.

**Expected.** A sharing violation caused by a third party is reported as a sharing violation,
or ignored; only genuine identity yields the alias refusal.

**Actual — reproduced on Windows, not inferred.** With `in.mid` (4,131 bytes) and a distinct
pre-existing `out.wav`:

- control, no third-party holder → `wrote …\out.wav (10.6 MB) in 10.7 s` (correct);
- with `[System.IO.File]::Open(out, Open, ReadWrite, FileShare::None)` held by a separate
  process →

```
error: output C:\…\out.wav aliases the input C:\…\in.mid; refusing to overwrite the source MIDI
exit code: 1
```

Two different files, and the tool says one aliases the other.

**Reproduce.** Hold the output path with `FileShare::None` from PowerShell, then run
`ferrosintesis <a.mid> -o <held.wav>` with a genuinely distinct input. Observed at `6c4c21e`.

## Fix

The Windows identity probe now treats its first sharing violation as
provisional. It releases the no-sharing input handle and retries the output
open. A successful retry means our input guard caused the conflict, so the
paths are aliases; a second failure is returned as the real output-access error
instead of being relabelled as aliasing.

The probe's comment now states that evidence boundary. No dependency or unsafe
Windows API was added.

## Verification — 2026-07-26

- The new command-level regression failed before the fix with the false
  `aliases the input` message. It now passes while holding a distinct output
  with `share_mode(0)`, and proves the rejected command preserves both files.
- All four output-safety integration tests pass.
- All six `output.rs` unit tests pass, including normalized-path, symbolic-link,
  and hard-link alias rejection.
- Targeted strict clippy, the full `ferrosintesis-cli` test suite, Rust 1.87
  compatibility, formatting, and `git diff --check` passed.

## Notes

- **This does NOT reopen MM-BUG-KILN-00097, and that bug is correctly Closed.** The misfire
  is **fail-safe**: it refuses to write. It cannot reintroduce 00097's actual harm — the input
  MIDI being truncated and replaced with WAV bytes — which was re-verified end-to-end on
  2026-07-25 (pre-fix path really did replace a 4,131-byte MIDI with 10,607,052 bytes of
  `RIFF`; the fixed path refuses exact, `.wav`-named and hard-link aliases and leaves the MIDI
  byte-identical).
- **Narrow blast radius.** The holder must exclude `FILE_SHARE_READ`; ordinary players and
  editors share read. In most triggering cases the fix's own `fs::rename` would have failed
  anyway, so the practical cost is usually a *wrong message* replacing an accurate
  sharing-violation one. Capability is genuinely lost only for a holder that grants
  `FILE_SHARE_DELETE` but not `FILE_SHARE_READ`. Hence Low / Could.
- **The probe approach is right; only its reading of failure is too broad.** Stable Rust does
  not expose volume-serial/file-index identity (`windows_by_handle` is unstable) and the crate
  is `#![forbid(unsafe_code)]`, so the sharing probe is a reasonable stand-in.
- **Proposed fix (cheap, no dependency, no unsafe):** on error 32, drop `_input_guard` and
  retry `File::open(output)`. If it now succeeds, our own guard caused the violation, so the
  paths are the same file → aliased. If it still fails, a third party holds the name and the
  probe has proved nothing → not aliased (or surface the real sharing error). Correct the
  overstated comment at `output.rs:57-59` in the same change, and add a regression that holds
  the output with an exclusive share mode and asserts the command does *not* report aliasing.
- **Unix is unaffected** — `platform_same_file` there compares `dev`/`ino`, which is real
  identity.
- **Provenance.** Surfaced by the independent two-eyes verification of MM-BUG-KILN-00097 on
  2026-07-25 and confirmed by direct execution on Windows.
