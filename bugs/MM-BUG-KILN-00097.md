# MM-BUG-KILN-00097 — CLI output alias can replace the input MIDI with WAV data

- **State:** Fixed
- **Priority:** Must
- **Severity:** High
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; same-file identity rejection and atomic output replacement landed with regression coverage; awaiting independent two-eyes verification)

## Observation

Source-level reproduction at `2d90376` (not executed because the review pass is
read-only):

```text
ferrosintesis score.mid -o score.mid
```

`crates/ferrosintesis-cli/src/main.rs:102-105` accepts the same path as input
and output and loads the complete MIDI. After rendering,
`crates/ferrosintesis-cli/src/main.rs:161` calls `offline::write_wav` on that
same path. `crates/ferrosintesis/src/wav.rs:15-16` opens it with
`std::fs::File::create`, which truncates it before writing WAV bytes.

The same collision can happen without an explicit `-o` when a valid MIDI input
is named with a `.wav` extension, because `input.with_extension("wav")` returns
the input path.

Expected: reject an output that aliases the input before rendering or writing.

Actual: the command can complete successfully after replacing the source MIDI
with a WAV file. Textually different symlink or hard-link aliases are also
unchecked.

## Fix

The CLI now rejects an output that resolves to the input before loading or
rendering. Canonical paths cover exact, normalized, and symbolic-link aliases;
Unix device/inode identity and a Windows kernel sharing probe cover hard links
without adding a dependency or weakening the crate's `forbid(unsafe_code)`.

Normal output is written to a unique temporary file beside the destination,
flushed to stable storage, then atomically renamed over the destination. A
failed temporary write leaves any prior output intact.

The two command-level collision regressions failed before the fix because the
CLI returned success after replacing the source MIDI. They pass after the fix,
alongside normalized-path, symbolic-link, hard-link, distinct-file, failed-write
preservation, and successful-replacement unit coverage. The focused
`ferrosintesis-cli` suite passes on Rust 1.87, and focused clippy is
warning-free.

## Notes

The devil's-advocate pass rejected the claim that ordinary `-o` overwrite
semantics make this harmless: replacing an existing output may be intentional,
but replacing the input artifact is irreversible data loss and has no
`--force` guard or warning.
