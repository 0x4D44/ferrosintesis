# MM-BUG-KILN-00241 — FLAC retarget left the sample-crate Rust generator syntactically invalid

- **State:** Closed
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
- **State history:** Open (2026-08-16T21:54:56Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T06:54:02Z, deltic:auto role=fix run=fix-20260913T064440Z-fe335cba branch=task/bug-MM-BUG-KILN-00241-run-fix-20260913T064440Z-fe335cba code=5e648268 gate=manual) -> Closed (2026-09-13T20:44:18Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: bug-time gen_crate_lib.py raises SyntaxError at line 99; removing the FLAC enumeration fails the mixed-inventory test)

## Observation

Observation: tools/ferrosintesis-samples/gen_crate_lib.py cannot be parsed. In main(), line 98 opens names = sorted( and line 99 begins the following if statement without supplying an iterable or closing the call. A second break at lines 164-165 opens lines.append( and immediately begins another lines.append call. Both fragments arrived in the FLAC conversion commit 9046cd1, whose intended retarget was to enumerate .wav and .flac assets and emit a matching Rust filter. Expected: the documented generator parses and regenerates sample-crate FILE_COUNT, SAMPLES, EXPECTED_BYTES, and inventory tests from the committed container set. Actual: every invocation stops at Python parse time, blocking generated inventory refreshes including the gong bank. Existing Open MM-BUG-KILN-00206 concerns non-atomic replacement after the generator starts and does not cover this parse failure. Concrete fix: restore the missing format-agnostic sorted enumeration and emitted extension filter, repair the truncated generated module prose at lines 106-108, and add a non-mutating syntax/import check plus a temporary mixed-WAV/FLAC generation golden. Static review only; the generator was not executed.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (test `5e648268`; root cause `82ccd84a`) by an agent other than the fixer.

**Original observation re-run (method A).** `ast.parse` on `gen_crate_lib.py` from `82ccd84a^` raises `SyntaxError: invalid syntax` at line 99; the HEAD file parses.

**Fails-before (method B).** Narrowing the restored enumeration and emitted filter back to `.wav` fails the mixed-inventory test (`'pub const FILE_COUNT: usize = 2;' not found`). Restored; all 5 `GenCrateLibMixedContainerTest` tests pass on HEAD. The parse test cannot go red on a real syntax error because `test_prepare` imports the module at load, which is why method A proves that half.

## Notes
