# MM-BUG-KILN-00097 — CLI output alias can replace the input MIDI with WAV data

- **State:** Open
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review)

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

Not fixed in this review. Before rendering, reject input/output same-file
identity using canonical paths and platform file identity where available.
Write normal output through a unique same-directory temporary file and
atomically replace the destination only after a successful flush, so a failed
write does not leave a prior output truncated.

Add regression coverage for exact-path, normalized-path, and supported
symlink/hard-link aliases, including the default-output collision.

## Notes

The devil's-advocate pass rejected the claim that ordinary `-o` overwrite
semantics make this harmless: replacing an existing output may be intentional,
but replacing the input artifact is irreversible data loss and has no
`--force` guard or warning.
