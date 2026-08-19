# MM-BUG-KIL-00303 — regen_samples_table.py rejects FLAC banks, stranding the documented drum-kit table-refresh recipe

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / regeneration tooling
- **Raised:** 2026-08-19T09:33:06Z
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
- **State history:** Open (2026-08-19T09:33:06Z, raised via `deltic bugs new`)

## Observation

The documented drum-kit regeneration recipe cannot complete on the current tree: the
table-refresh tool only accepts `.wav` files, and both drum-kit crates' `samples/`
directories have been all-FLAC since the 2026-08-16 container migration.

`tools/ferrosintesis-samples/regen_samples_table.py:155` selects inputs with
`f.endswith(".wav")`, and lines 156-157 `raise SystemExit(f"no .wav files in …")`
when none match. `crates/ferrosintesis-samples-drumkit2/samples/` holds 36 `.flac`
and 0 `.wav`; `crates/ferrosintesis-samples-drumkit/samples/` holds 128 `.flac` and
0 `.wav`. So both commands in the documented recipe
(`crates/ferrosintesis-samples-drumkit2/PROVENANCE.md:111-115`) exit with
"no .wav files" and never refresh `SAMPLES`, `FILE_COUNT`, or `EXPECTED_BYTES`.

The producing half of the pipeline was migrated: `prepare_drumkit.py`'s
`publish_staged` (`tools/ferrosintesis-samples/prepare_drumkit.py:358-386`) encodes
staged WAVs to FLAC at the crate boundary and verifies the encode is bit-exact. It
never touches `lib.rs` (no reference to `lib.rs`, `FILE_COUNT`, or `EXPECTED_BYTES`
anywhere in it), so `regen_samples_table.py` is the only table-refresh path — and it
is stranded. The tool's own docstring (lines 2 and 7) still says `samples/*.wav`.

Expected: the documented recipe regenerates a drum-kit crate's embedded table after
a bake. Actual: it exits with an error, silently inviting the exact hand-editing of
derived tables that CLAUDE.md's "hand-maintained lists" section warns about.

Classification: dev-tooling defect, exposed only when regenerating; no shipped
audio or committed table is currently wrong. Related but distinct:
MM-BUG-KILN-00224 (the *core* crate documents no safe regen path at all) and
MM-BUG-KIL-00304 (the surrounding PROVENANCE prose is stale the same way).

## Fix

Widen the filter at `regen_samples_table.py:155` to
`f.endswith((".wav", ".flac"))` — matching `prepare_drumkit.py:372` and the crate
test's own filter (`crates/ferrosintesis-samples-drumkit2/src/lib.rs:364-368`,
which accepts `Some("wav" | "flac")`) — and update the docstring and the
`SystemExit` message. Prove it by running the documented recipe on the unchanged
drumkit2 crate and confirming the idempotence claim: the rewrite must be a no-op
(same `SAMPLES`, `FILE_COUNT=36`, `EXPECTED_BYTES=4301372`). Regression: a
FLAC-only samples directory must no longer raise `SystemExit`.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Estimated effort: Small.
