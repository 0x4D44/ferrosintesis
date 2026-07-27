# MM-BUG-KILN-00156 — Bake-inventory oracle enumerates by _bake_ name prefix, not by packaged-write behaviour

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** testing / sample generation
- **Raised:** 2026-07-27
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
- **State history:** Open (2026-07-27, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** The MM-BUG-KILN-00145 oracle enumerates candidate bake helpers by NAME
prefix, so the identical unvalidated-write defect is invisible the moment a helper is
not called `_bake_*` / `bake_*`.

`unvalidated_bake_output_helpers` (`crates/ferrosintesis/src/inventory.rs:233`) filters
with `name.starts_with("_bake_") || name.starts_with("bake_")` before computing effects.
Everything downstream of that filter is sound: `python_bake_effects`
(`crates/ferrosintesis/src/inventory.rs:178`) already resolves packaged writes and
validation transitively, in call order, for ANY function. Only the enumeration is narrow.

**Reproduced.** Taking the oracle's own positive control
(`bake_output_inventory_oracle_rejects_an_unvalidated_writer`,
`crates/ferrosintesis/src/inventory.rs:750`) byte-for-byte and renaming its helper from
`_bake_newbank` to `prepare_newbank`, `unvalidated_bake_output_helpers` returns `[]` —
the defect is not flagged at all. The source is otherwise identical, including the
unvalidated `write_wav_mono` into a crate `samples/` directory.

**The three adversarial controls cannot catch this**, because all three name their helper
`_bake_newbank` and therefore satisfy the prefix. They exercise the effect resolver, never
the enumeration. This is the same shape as MM-BUG-KILN-00072, whose five self-tests all
used `"` and so never exercised `'`.

**Expected.** The set of guarded helpers is derived from what a function DOES — writing a
packaged WAV into a crate `samples/` directory — as MM-BUG-KILN-00145's own fix direction
proposed: *"derive the set of bake helpers that own an output family (for example, those
that call `sample_output_path`/`write_wav_mono` into a crate `samples/` directory)"*.

**Actual.** The set is derived from what a function is CALLED. A rename, or a new writer
following a different naming convention, silently leaves the guard green.

**No live defect today, and this is stated at the same evidential level as
MM-BUG-KILN-00145's own report.** An AST census of `tools/ferrosintesis-samples/prepare.py`
finds 12 top-level functions that call `write_wav_mono` directly. Eleven match the prefix
and are guarded. The twelfth is `main`, which is NOT guarded by the oracle but does call
`_validate_generated_output_inventory` at `tools/ferrosintesis-samples/prepare.py:3336`
before its own packaged writes at `:3564` and `:3572` — so it is correct today, purely by
its author's care rather than by enforcement. Remove or reorder that one call and no test
turns red.

**Concrete fix.** Replace the name filter with a behavioural one: enumerate every top-level
function whose transitive effects include a packaged write, and exclude only what is
deliberately exempt. Keep the existing effect resolver as-is. Add a control that renames a
flagged helper off the `_bake_` prefix and requires it to STILL be flagged, so the
enumeration itself is tested rather than assumed.

## Notes

Split out of MM-BUG-KILN-00145 during its independent two-eyes verification. That bug's own
report — that `_validate_generated_output_inventory` was an optional hand-placed call, so
each new bank had to be told to use it — is genuinely fixed and was closed. This is the
residual in the guard's enumeration predicate, which this repo's CLAUDE.md already names as
its recurring defect: *"a derived oracle is only as good as its enumeration predicate, and
the predicate is itself an assumption."*
