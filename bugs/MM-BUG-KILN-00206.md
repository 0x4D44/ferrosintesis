# MM-BUG-KILN-00206 — Sample-crate Rust generator writes directly over lib.rs

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample crate generation / output durability
- **Raised:** 2026-08-16T08:41:07Z
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
- **State history:** Open (2026-08-16T08:41:07Z, raised via `deltic bugs new` model=gpt-5.6-sol@high) -> Fixed (2026-09-13T15:11:08Z, deltic:auto role=fix run=fix-20260913T150200Z-99fda007 branch=task/bug-MM-BUG-KILN-00206-run-fix-20260913T150200Z-99fda007 code=9a28305b82c66689effa1f06abd0677a0ebad0ea gate=manual) -> Closed (2026-09-13T21:00:07Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: writing straight over lib.rs again fails both write-failure and rustfmt-failure regressions)

## Observation

**Symptom.** The shared sample-crate Rust-table generator opens the final
tracked `src/lib.rs` with mode `"w"` before it knows that the generated source
can be written and formatted successfully.

At
`D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-092455\tools\ferrosintesis-samples\gen_crate_lib.py:240`,
`out` is the crate's final `src/lib.rs`. Lines 242–243 open that path directly
and write the generated text. `rustfmt` does not run until lines 250–257. A
process termination, disk/write exception, or formatting failure can therefore
leave the tracked Rust source empty, partial, or replaced by an output that the
generator itself has not accepted.

The current YDP `lib.rs` is complete; this is the destructive failure window in
the generator, not evidence of current file corruption. Compilation will catch
many damaged outputs, but it cannot restore the tracked source that the failed
command overwrote.

**Expected.** A failed generation or formatting attempt leaves the previous
`src/lib.rs` byte-identical. Only a complete, fmt-clean replacement becomes
visible at the final path.

**Actual.** The final path is truncated before the write and formatting steps
succeed.

**Concrete fix.** Write the generated source to a unique sibling temporary
file, run `rustfmt` on that temporary file, close and validate it, then publish
it with `os.replace()`. Remove the temporary file on every failure. Add injected
write-failure and rustfmt-failure regressions that prove the old destination is
preserved.

Static review only. No generator, test, build, app, render, package command, or
exploratory harness ran. Estimated effort: Small.

## Fix

<unfixed — raised only>

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `9a28305b`) by an agent other than the fixer.

Injected write and rustfmt failures leave the existing `lib.rs` byte-identical and remove the temp file.

**Fails-before (method B).** Making the generator write directly over `lib.rs` fails `test_write_failure_preserves_existing_lib_and_cleans_temp` (`b'' != b'previous lib bytes...'`) and `test_rustfmt_failure_preserves_existing_lib_and_cleans_temp`. Restored; both pass on HEAD. A hard kill can still leave a stray sibling temp file, but the tracked file survives.

**Gates.** Causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes

Closed `MM-BUG-KILN-00063` covers atomic replacement inside
`prepare.py::write_wav_mono`; it does not cover this separate generator or Rust
source output.
