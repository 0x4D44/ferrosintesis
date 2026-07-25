# MM-BUG-KILN-00097 — CLI output alias can replace the input MIDI with WAV data

- **State:** Closed
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
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol during the `crates/ferrosintesis-cli/` coverage review) → Fixed (2026-07-25, Codex GPT-5.6-Sol; same-file identity rejection and atomic output replacement landed with regression coverage; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the observation re-run end-to-end: trunk refuses and preserves; the pre-fix path destroys)

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

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Re-ran the **original observation end-to-end** against a trunk build, not a unit test.

Green after — `ferrosintesis score.mid -o score.mid` exits 1 with
`error: output …/score.mid aliases the input …/score.mid; refusing to overwrite the source
MIDI`, and the MIDI's md5 is unchanged. The observation's second half — a valid MIDI *named*
`.wav` with no `-o`, where `with_extension("wav")` returns the input path — is rejected the
same way. A **hard-link** alias (a textually different path, same file) is rejected too, which
is the case a naive path comparison would miss.

Red-before — with only the guard call removed and `offline::write_wav` restored, the same
command **succeeded**: it printed `wrote … (10.6 MB)` and replaced a 4,131-byte MIDI with
10,607,052 bytes beginning `RIFF`. Irreversible loss of the source artifact, observed.

The `ferrosintesis-cli` suite is green, 16/16 across `output`, `output_safety` and
`wav_reader`.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

The devil's-advocate pass rejected the claim that ordinary `-o` overwrite
semantics make this harmless: replacing an existing output may be intentional,
but replacing the input artifact is irreversible data loss and has no
`--force` guard or warning.
