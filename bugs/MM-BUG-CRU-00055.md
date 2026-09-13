# MM-BUG-CRU-00055 — MIDI resource-bound test helpers fail clippy manual_repeat_n, leaving the workspace clippy gate red

- **State:** Fixed
- **Priority:** Must
- **Severity:** Medium
- **Area:** ferrosintesis / MIDI parser tests
- **Raised:** 2026-09-13T19:19:46Z
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
- **State history:** Open (2026-09-13T19:19:46Z, raised via `deltic bugs new` model=claude-opus-5) -> Fixed (2026-09-13T22:10:20Z, deltic:auto role=fix run=fix-20260913T220245Z-abb143ec branch=task/bug-MM-BUG-CRU-00055-run-fix-20260913T220245Z-abb143ec code=e75867d65e07f6a04935acfa3dcc64c325d0bd58 gate=manual)

## Observation

Split from MM-BUG-KILN-00274 at independent verification (2026-09-13). Fix commit 4951e6ed added `events.extend(std::iter::repeat(b'x').take(marker_len))` in test helpers at crates/ferrosintesis/src/midi.rs:1068 and crates/ferrosintesis/src/parse_robustness.rs:173 (the only commit adding that text, per git log -S). On trunk 8b6a6f86 with rustc/clippy 1.95.0, `cargo clippy --workspace --all-targets --locked -- -D warnings` and `cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings` both fail with clippy::manual_repeat_n at those two lines. Expected: the required integration gate is clean. Actual: two lint errors in the fix's test helpers keep it red. std::iter::repeat_n is stable since Rust 1.82, inside the 1.87 MSRV. The oversized-marker builder is also duplicated between the two test files.

## Fix

<unfixed — raised only>

## Notes
