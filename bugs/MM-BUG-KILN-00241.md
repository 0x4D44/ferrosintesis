# MM-BUG-KILN-00241 — FLAC retarget left the sample-crate Rust generator syntactically invalid

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / generated crate inventories
- **Raised:** 2026-08-16T21:54:56Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** verify
- **Owner run:** verify-20260913T203206Z-460230e8
- **Owner host:** CRUCIBLE
- **Owner branch:** task/bug-MM-BUG-KILN-00241-run-verify-20260913T203206Z-460230e8
- **Owner base:** 87547a96efd6d45628a49829fd7fcc6eed63656c
- **Owner fingerprint:** sha256:d4c489e31d09c91cdc8ffe30b9b125b426584c306369c96182761599420fe687
- **Owner since:** 2026-09-13T20:32:06Z
- **Owner until:** 2026-09-13T22:32:06Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-16T21:54:56Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:54:02Z, deltic:auto role=fix run=fix-20260913T064440Z-fe335cba branch=task/bug-MM-BUG-KILN-00241-run-fix-20260913T064440Z-fe335cba code=5e648268 gate=manual)

## Observation

Observation: tools/ferrosintesis-samples/gen_crate_lib.py cannot be parsed. In main(), line 98 opens names = sorted( and line 99 begins the following if statement without supplying an iterable or closing the call. A second break at lines 164-165 opens lines.append( and immediately begins another lines.append call. Both fragments arrived in the FLAC conversion commit 9046cd1, whose intended retarget was to enumerate .wav and .flac assets and emit a matching Rust filter. Expected: the documented generator parses and regenerates sample-crate FILE_COUNT, SAMPLES, EXPECTED_BYTES, and inventory tests from the committed container set. Actual: every invocation stops at Python parse time, blocking generated inventory refreshes including the gong bank. Existing Open MM-BUG-KILN-00206 concerns non-atomic replacement after the generator starts and does not cover this parse failure. Concrete fix: restore the missing format-agnostic sorted enumeration and emitted extension filter, repair the truncated generated module prose at lines 106-108, and add a non-mutating syntax/import check plus a temporary mixed-WAV/FLAC generation golden. Static review only; the generator was not executed.

## Fix

<unfixed — raised only>

## Notes
