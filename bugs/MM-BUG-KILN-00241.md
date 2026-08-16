# MM-BUG-KILN-00241 — FLAC retarget left the sample-crate Rust generator syntactically invalid

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / generated crate inventories
- **Raised:** 2026-08-16T21:54:56Z
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
- **State history:** Open (2026-08-16T21:54:56Z, raised via `deltic bugs new`)

## Observation

Observation: tools/ferrosintesis-samples/gen_crate_lib.py cannot be parsed. In main(), line 98 opens names = sorted( and line 99 begins the following if statement without supplying an iterable or closing the call. A second break at lines 164-165 opens lines.append( and immediately begins another lines.append call. Both fragments arrived in the FLAC conversion commit 9046cd1, whose intended retarget was to enumerate .wav and .flac assets and emit a matching Rust filter. Expected: the documented generator parses and regenerates sample-crate FILE_COUNT, SAMPLES, EXPECTED_BYTES, and inventory tests from the committed container set. Actual: every invocation stops at Python parse time, blocking generated inventory refreshes including the gong bank. Existing Open MM-BUG-KILN-00206 concerns non-atomic replacement after the generator starts and does not cover this parse failure. Concrete fix: restore the missing format-agnostic sorted enumeration and emitted extension filter, repair the truncated generated module prose at lines 106-108, and add a non-mutating syntax/import check plus a temporary mixed-WAV/FLAC generation golden. Static review only; the generator was not executed.

## Fix

<unfixed — raised only>

## Notes
