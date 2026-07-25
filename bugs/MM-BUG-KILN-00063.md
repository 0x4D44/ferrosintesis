# MM-BUG-KILN-00063 — Sample regeneration can truncate tracked WAVs on interruption

- **State:** Fixed
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
- **State history:** Open (2026-07-24, raised by Codex during the coverage-ledger review of `crates/ferrosintesis-samples-bass/`) → Fixed (2026-07-25, Codex GPT-5.6-Sol; shared WAV generation now stages through a sibling `.part` and atomically replaces the destination after close; awaiting independent two-eyes verification)

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

## Notes

- A successful rerun repairs the file, and existing byte-count checks should detect many
  truncations. Those facts reduce the impact to Low; they do not preserve source state
  when the interrupted write occurs.
- The reliability and devil's-advocate passes confirmed the write window. No existing
  bug or requirement matched it.
- `write_wav_mono()` serves multiple generated asset families, so one helper fix covers
  the wider surface.

