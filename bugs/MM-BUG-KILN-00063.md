# MM-BUG-KILN-00063 — Sample regeneration can truncate tracked WAVs on interruption

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample generation / output durability
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
- **State history:** Open (2026-07-24, raised by Codex during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; shared WAV generation now stages through a sibling `.part` and atomically replaces the destination after close; awaiting independent two-eyes verification) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded 44-byte truncation reproduced by reverting only write_wav_mono)

## Observation

**Symptom.** The sample generator writes directly to the final tracked WAV path. A
process termination, disk error, or write exception after the file is opened can leave
the repository's source asset empty or partial.

**Expected.** A failed regeneration should preserve the previously valid tracked WAV.
Only a fully closed replacement should become visible at the final path.

**Actual.** `tools/ferrosintesis-samples/prepare.py:1802-1811` calls
`wave.open(path, "wb")`, which truncates the final file before its header and PCM are
fully written. Electric-bass regeneration reaches this helper at line 2680. The same
tool already uses the durable pattern for downloads at lines 1067-1077: write a
`.part`, then `os.replace()` only after success.

This review did not inject a mid-write failure. The destructive window follows directly
from opening the final path in `wb` mode and writing it in place.

## Fix

Implemented in `tools/ferrosintesis-samples/prepare.py`. `write_wav_mono()` now
writes and closes a sibling `.part`, then publishes it with `os.replace()`. Any
exception removes the staged file and leaves the tracked destination unchanged.
This follows the tool's existing durable-download pattern.

The focused regression patches `Wave_write.writeframes()` to raise after the
destination is known to exist. Before the fix, it failed because the known bytes
became a partial 44-byte WAV. It now proves the destination remains byte-identical
and no `.part` survives.

Validation on 2026-07-25:

- Focused injected-write-failure regression: 1 passed.
- Full `tools/ferrosintesis-samples/test_prepare.py` suite: 32 passed.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Red-before: reverting **only** `write_wav_mono` to the pre-fix in-place `wave.open(path,
"wb")` fails `test_failed_wav_write_preserves_the_existing_destination`. The injected write
failure leaves the destination as a header-only WAV — the bytes begin `RIFF$\x00\x00\x00`
(declared size 36, zero data frames) where the original held 1,024 data bytes. That is the
recorded destructive window, observed rather than inferred.

Green after: the full `tools/ferrosintesis-samples/test_prepare.py` suite passes, 32/32, and
no `.part` file survives the failure.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

- A successful rerun repairs the file, and existing byte-count checks should detect many
  truncations. Those facts reduce the impact to Low; they do not preserve source state
  when the interrupted write occurs.
- The reliability and devil's-advocate passes confirmed the write window. No existing
  bug or requirement matched it.
- `write_wav_mono()` serves multiple generated asset families, so one helper fix covers
  the wider surface.

