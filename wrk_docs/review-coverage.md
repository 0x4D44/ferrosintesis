# Review coverage ledger

Tracks the overnight/continuous code-review coverage of this repo's code areas so
review passes converge across the whole codebase instead of circling hot spots.

- **Area** — a repo-relative directory path, used verbatim as the key (forward
  slashes, trailing slash, no glob characters). One row per Cargo workspace-member
  crate under `crates/`. deltic's continuous review reads this cell verbatim as a
  `git log` pathspec, so it must match the on-disk path exactly.
- **Last reviewed** — ISO `YYYY-MM-DD`, or the literal `(never)`.

Reconcile additively: every current area has a row; a vanished area's row is
harmless. Never reorder columns or re-flow untouched rows.

| Area | Last reviewed |
|------|---------------|
| crates/ferrosintesis/ | 2026-07-18 |
| crates/ferrosintesis-cli/ | 2026-07-18 |
| crates/render-catalog/ | 2026-07-18 |
| crates/ferrosintesis-samples-clavinet/ | (never) |
| crates/ferrosintesis-samples-core/ | (never) |
| crates/ferrosintesis-samples-dark-salamander/ | (never) |
| crates/ferrosintesis-samples-drumkit/ | 2026-07-18 |
| crates/ferrosintesis-samples-gong/ | (never) |
| crates/ferrosintesis-samples-grand/ | (never) |
| crates/ferrosintesis-samples-headroom/ | (never) |
| crates/ferrosintesis-samples-honkytonk/ | (never) |
| crates/ferrosintesis-samples-musescore/ | (never) |
| crates/ferrosintesis-samples-musescore-grand/ | (never) |
| crates/ferrosintesis-samples-orchestral/ | (never) |
| crates/ferrosintesis-samples-orchestral2/ | (never) |
| crates/ferrosintesis-samples-sax/ | (never) |
| crates/ferrosintesis-samples-strings/ | (never) |
| crates/ferrosintesis-samples-vcsl-kawai/ | (never) |
| crates/ferrosintesis-samples-vcsl-steinway/ | (never) |
| crates/ferrosintesis-samples-ydp-grand/ | (never) |
