# MM-BUG-KILN-00149 — Parent sample inventory mislabels MuseScore grand as GM0 instead of GM1 CC0=2

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample routing documentation
- **Raised:** 2026-07-26
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00149-run-fix-20260727T040306Z-p9812-n941510300-c51-code-1785125475274
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=gpt-5.6-sol@high) → Fixed (2026-07-27, GPT-5.6 Codex on KILN-Windows — source `30c9ed5e1ce72dcde2ec88f7db6e51e26934a59b`; parent inventory labels and derived GM1 selector oracle now agree with the shipped CC0 routing) → Closed (2026-07-27, claude-opus-5@high; independent two-eyes verification — both original parent references corrected on trunk `8a4c90f`, and the new derived oracle proven two-sided by restoring the exact original wording, which fails it on the README row and, separately, on the NOTICE line; repo gates green)

## Observation

Static reproduction:

1. The parent distribution table calls `ferrosintesis-samples-musescore-grand` a `GM 0 grand` at `crates/ferrosintesis/README.md:233`; the parent notice repeats `GM 0 grand piano` at `crates/ferrosintesis/NOTICE:26`.
2. The routing source accepts this bank only inside the program `1` arm and only for CC0=2 at `crates/ferrosintesis/src/altbank.rs:1046-1075`.
3. The crate module docs, manifest, README, provenance, generator, and sampler all correctly identify it as GM 1 Bright Acoustic alternate CC0=2.

Expected: parent documentation identifies the embedded bank as GM 1 Bright Acoustic, CC0=2, matching the shipped selector.

Actual: both parent-facing references classify it as GM0. A maintainer or MIDI author relying on the parent inventory associates the asset and its attribution with the wrong program; GM0 CC0=2 routes to the Salamander bank instead.

The existing derived selector/documentation oracle covers only `voices::GM0_SOURCES` (`crates/ferrosintesis/src/altbank.rs:1317-1363`), so this non-GM0 parent drift is unguarded. No application, build, test, render, generator, or exploratory harness ran.

## Fix

Correct both parent references to identify the bank as GM 1 Bright Acoustic,
CC0=2. Add a derived GM1 alternate-bank documentation regression rather than a
new hand-maintained list: cover the YDP bank at CC0=1 and MuseScore grand at
CC0=2, including the parent README/NOTICE claims, and prove an unknown GM1 bank
falls back to the model.

Estimated effort: Small.

### Fix summary (2026-07-27, GPT-5.6 Codex on KILN-Windows)

Source: `30c9ed5e1ce72dcde2ec88f7db6e51e26934a59b`.

The parent README and NOTICE independently called both GM1 alternate piano banks
GM0 recordings. The existing derived selector/documentation oracle covered only
GM0, so those parent-facing labels could drift without failing a test.

The fix:

- labels YDP Grand as GM1 Bright Acoustic CC0=1;
- labels MuseScore Grand as GM1 Bright Acoustic CC0=2;
- makes one ordered `GM1_ALT_SOURCES` table drive the program-1 alternate router
  and the documentation regression;
- verifies each bank's crate-local module docs, manifest, README, and provenance
  agree with its derived CC0 selector;
- verifies the parent README and NOTICE identify the same program and selector;
- proves an unknown GM1 CC0 value still falls back byte-identically to the model.

The routing table is a behavior-preserving refactor. GM0 selection is unchanged,
and the known GM1 entries still call the same YDP and MuseScore bank functions
with `GM1_VOICING`.

Evidence:

- `cargo test -p ferrosintesis altbank::tests::`: 60 passed.
- `cargo test -p ferrosintesis licensing::tests::`: 11 passed.
- GM1 alternate tests with `--no-default-features`: 2 passed.
- `cargo clippy -p ferrosintesis --all-targets -- -D warnings`: green.
- `cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings`:
  green.
- `cargo fmt --check` and `git diff --check`: green.
- Full 124-MIDI render-diff against exact base
  `149750d35be0c91e7179f85dcf8de5706a10b3c4`, at the tool-supported
  11.025 kHz rate: 124 byte-identical, 0 changed, 0 contamination, and
  0 not reached.

## Notes

Closed `MM-BUG-KILN-00122` fixed stale selector claims inside individual sample
crates and added a GM0-only guard. This is a residual on parent documentation
outside that guard, not a duplicate of the corrected crate-local claims.

## Independent verification (2026-07-27, claude-opus-5@high — two-eyes, verifier ≠ fixer)

Verified on trunk `8a4c90f` in a dedicated verification worktree. Verdict: **Closed**.

**Original observation is corrected.** Both parent-facing references the report named now
match the router:

- `crates/ferrosintesis/README.md:233` — `GM 1 Bright Acoustic alternate (CC0=2, MF velocity tier)`
  (was `GM 0 grand`).
- `crates/ferrosintesis/NOTICE:26` — `GM 1 Bright Acoustic alternate, CC0=2 (MF velocity tier)`
  (was `GM 0 grand piano`).

**The new oracle is genuinely two-sided, and covers BOTH halves of the report.** Rather than
take the guard on faith I restored the exact defect wording from the observation and re-ran it:

- with both references reverted, `every_gm1_alternate_parent_claim_matches_the_router` fails at
  `crates/ferrosintesis/src/altbank.rs:1528` — *"parent README row for
  ferrosintesis-samples-musescore-grand does not name GM 1 Bright Acoustic alternate CC0=2"*;
- with only the README restored and the NOTICE still reverted, it fails independently at
  `crates/ferrosintesis/src/altbank.rs:1544` on the NOTICE line.

So neither half is carried by the other, which matters because the report cited them as two
separate drifts.

**It is derived, not hand-maintained.** The oracle iterates `GM1_ALT_SOURCES`, the same table
that drives the program-1 router at `crates/ferrosintesis/src/altbank.rs:1063`, so a label
cannot drift from behaviour. It also carries explicit negative assertions (`!contains("GM 0")`)
on both the README row and the NOTICE line — the hardening this repo's KILN-00071 lesson
requires, since a `contains`-only predicate passes on gutted documentation.

**Gates, observed on the verification worktree at `8a4c90f`:** `cargo test --workspace --release`
812 passed / 0 failed / 41 ignored in the ferrosintesis suite and 0 failed across all 39 other
suites; `cargo clippy --workspace --all-targets -- -D warnings` and the same under
`--no-default-features` both exit 0 with no diagnostics; `cargo fmt --all --check` clean. The
`altbank::` suite specifically is 60 passed / 0 failed. No known-unrelated failures.

**Not re-run here:** the 124-MIDI render-diff. This fix changes documentation text plus a
behaviour-preserving router-table refactor, and the fixer recorded 124 byte-identical renders;
the `unknown_gm1_alternate_bank_falls_back_to_the_model` oracle independently pins the refactor's
one behavioural risk (an unlisted CC0 must stay pure-model), and it passes.
