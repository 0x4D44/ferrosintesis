# MM-BUG-KILN-00067 — Multi-line inline tables in ferrosintesis Cargo.toml break the declared MSRV 1.87

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 while fixing
  KILN-00060 in the same manifest; reproduced against the 1.87 toolchain)

## Observation

**Symptom.** The workspace does not build on the toolchain every crate declares as its
MSRV. `cargo +1.87` cannot parse `crates/ferrosintesis/Cargo.toml` at all, so it fails
before compiling a single line.

**Repro** (from a worktree root, with the 1.87 toolchain installed):

```
$ cargo +1.87 metadata --no-deps --format-version 1
error: invalid inline table
expected `}`
  --> crates\ferrosintesis\Cargo.toml:47:34
   |
47 | ferrosintesis-samples-drumkit = {
   |                                  ^
   |
error: failed to load manifest for workspace member `...\crates\ferrosintesis`
$ echo $?
101
```

**Expected.** `cargo +1.87 check --workspace` is the command `CLAUDE.md` names as the
proof that the declared MSRV is real. It should parse and build.

**Actual.** Exit 101 at manifest-parse time. Nothing is compiled, so the MSRV is
currently unproven and, as declared, false.

**Root cause.** Two dependencies are written as **multi-line inline tables**:

- `crates/ferrosintesis/Cargo.toml:47-51` — `ferrosintesis-samples-drumkit`
- `crates/ferrosintesis/Cargo.toml:64-68` — `ferrosintesis-samples-orchestral`

TOML 1.0 requires an inline table to be on one line ("no newlines are allowed between
the curly braces"). Newer cargo accepts the multi-line form leniently; cargo 1.87 does
not. The manifest carries a comment at lines 43-45 warning against exactly this, so both
entries were written in violation of a rule the file itself states.

**Introduced by** `0d147c0` (2026-07-14, drumkit) and `b6598c9` (2026-07-18,
orchestral) — so the declared MSRV has been broken on trunk for ~10 days. Neither is
another agent's in-flight work.

## Fix

Put both dependency declarations back on one line each, matching the other 19. Then add
a regression oracle: the existing gate cannot catch this, because the toolchain the
fleet builds with parses the bad form happily. Prefer a test that reads the manifest
text and asserts every `[dependencies]` entry opening an inline table closes it on the
same line — that fails on the current tree and needs no second toolchain to run.

Prove the fix with `cargo +1.87 check --workspace` (an MSRV is only real once a
toolchain at that version has compiled it).

## Notes

- Found while fixing KILN-00060 in the same file; the two defects are independent and
  are being landed as separate changes.
- The lenient parse means every `cargo` invocation on a current toolchain succeeds, which
  is why this survived ten days and two code reviews unnoticed.
