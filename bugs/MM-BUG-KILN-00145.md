# MM-BUG-KILN-00145 — No oracle asserts bake helpers validate their output inventory, so the class recurs per bank

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** testing / sample generation
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
- **Held branch:** host-local:KILN:task/bug-MM-BUG-KILN-00145-run-fix-20260727T033403Z-p9812-n749513500-c45-code-1785124032820
- **Legacy fixed run:** -
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high) → Fixed (2026-07-27, GPT-5.6 Codex on KILN-Windows — source `0788a860322e6432045a1aa49478163dc86450c1`; every `prepare.py` bake path that reaches a packaged WAV write must now validate its complete owned output inventory first) → Closed (2026-07-27, claude-opus-5@high; independent two-eyes verification on trunk `8a4c90f` — the hand-placed call is now an enforced property, adversarial controls proven non-vacuous, repo gates green; enumeration-predicate residual split to MM-BUG-KILN-00156)

## Observation

**Symptom.** Nothing asserts that a bake helper validates its own output inventory, so the "rebake retains an obsolete generated WAV" defect keeps recurring one bank at a time.

It has now been reported and fixed four times, each as its own id, each for a single bank:

| id | bank | fix |
|---|---|---|
| MM-BUG-KILN-00123 | dark grand | bespoke check inside `_bake_darkened_grand` |
| MM-BUG-KILN-00124 | drum kit | two-package output plan in `prepare_drumkit.py` |
| MM-BUG-KILN-00140 | headroom | `_validate_headroom_output_inventory` |
| MM-BUG-KILN-00143 | honky-tonk | generalised it to `_validate_generated_output_inventory(family, expected)` |

00143's fix is the right shape - it turned the single-bank guard into a shared, parameterised one - but the call is still hand-placed per bank. Today it is invoked exactly twice: `_bake_honkytonk` (`tools/ferrosintesis-samples/prepare.py:2734`) and the Headroom path (`:3150`). Nothing makes a fifth bank inherit it.

**Evidence that the gap is reachable.** Other bake helpers enumerate a fixed source list and write into their crate's `samples/` directory without ever inspecting that directory for files their enumeration no longer names - the same shape the four bugs above described:

- `_bake_ydp_grand` iterates `YDP_ZONE_MIDI` and writes `ydpgrand_*.wav` (9 packaged WAVs);
- `_bake_b1upright` iterates the decoded-take manifests and writes into `ferrosintesis-samples-b1-upright/samples/` (52 packaged WAVs) - and that is the DEFAULT GM 0 piano since 2026-07-26.

I am stating this at the same evidential level the original reports used: MM-BUG-KILN-00140 and 00143 were both raised as static readings of the control flow, each noting that the committed inventory was clean at the time. I have likewise NOT shown either crate is currently inconsistent - only that the guard which would catch it is absent, and that `Cargo.toml` packages every WAV under `samples/**`, so a retained file would ship.

**Expected.** Adding a bake helper that owns an output family cannot silently skip the inventory validation.

**Actual.** It is a hand-placed call, so it is skipped by default and only added once a bug is filed against that specific bank.

**Provenance.** Split out of MM-BUG-KILN-00143 during its independent two-eyes verification. That bug's own report is fully fixed - the honky-tonk guard runs as the first statement of `_bake_honkytonk`, ahead of `ensure_archive_sources`, with a derived expected set - and it was closed. This is the class-level residual.

**Fix direction, and there is a working model to copy in this same file.** MM-BUG-KILN-00141 ended the sibling class - "a pinned helper that trusts a warm cache" - which had also recurred three times (00062, 00134, 00141). Its fix added `test_every_pinned_ensure_helper_authenticates_its_warm_cache` (`tools/ferrosintesis-samples/test_prepare.py:901`), which parses `prepare.py` with `ast`, enumerates the relevant helpers from the syntax tree rather than a hand-written list, resolves the property transitively, and carries a negative control proving it flags the defect's shape. Since that fix landed, a new pinned helper cannot skip authentication silently.

Do the same here: derive the set of bake helpers that own an output family (for example, those that call `sample_output_path`/`write_wav_mono` into a crate `samples/` directory), and assert each reaches `_validate_generated_output_inventory` - transitively, so a helper that delegates still counts. Pair it with a negative control: a synthetic bake helper that writes an enumerated family without validating must be flagged. That converts this from a recurring per-bank report into a property the suite enforces once.

## Fix

<unfixed — raised only>

### Fix summary (2026-07-27, GPT-5.6 Codex on KILN-Windows)

Source: `0788a860322e6432045a1aa49478163dc86450c1`.

The recurring defect was possible because
`_validate_generated_output_inventory` remained an optional hand-placed call.
New bake helpers inherited no requirement to reject obsolete family-owned WAVs.

The fix adds one source-derived Cargo oracle over
`tools/ferrosintesis-samples/prepare.py`. It discovers top-level bake helpers,
follows both packaged `write_wav_mono` calls and inventory validation through
delegated helpers, preserves call order, and rejects any path whose first write
precedes validation. Its adversarial controls prove it rejects:

- a direct unvalidated writer;
- an unvalidated delegated writer;
- a delegated helper that validates only after writing.

Positive controls prove direct and delegated validation are accepted. This closes
the gap where a future bake could hide its write behind another helper.

The existing bake paths now validate their complete owned output sets before
writing. The shared validator accepts an explicit output directory for direct-write
crates and requires explicit family names, so an empty dynamic output plan still
rejects stale owned WAVs. Python controls cover empty plans and multi-family
directories without treating sibling families as contamination.

Evidence:

- `cargo test -p ferrosintesis inventory::tests:: -- --nocapture`: 14 passed.
- `python tools\ferrosintesis-samples\test_prepare.py`: 84 passed.
- Python byte-compilation of `prepare.py` and `test_prepare.py`: green.
- `cargo clippy -p ferrosintesis --all-targets -- -D warnings`: green.
- `cargo fmt --all -- --check` and `git diff --check`: green.
- No dependencies, manifests, lockfiles, or generated sample assets changed.

## Notes

## Independent verification (2026-07-27, claude-opus-5@high — two-eyes, verifier ≠ fixer)

Verified on trunk `8a4c90f`. Verdict: **Closed, with the residual split to
MM-BUG-KILN-00156.**

**The reported defect is fixed.** The complaint was that
`_validate_generated_output_inventory` was an optional hand-placed call, invoked at exactly
two sites, so a fifth bank inherited nothing. It is now an enforced property: any helper
matching the file's `_bake_*` convention that reaches a packaged `write_wav_mono` without
validating first turns the suite red, transitively and in call order.

**The adversarial controls are real, not decorative.** I read all three and they defeat the
obvious cheats — one hides the validator name in a *comment*, one delegates the write to a
non-bake helper, one validates only *after* writing. Two positive controls pin the accepting
cases. That is materially stronger than a `contains` check.

**The predicate is not vacuous.** An AST census of `tools/ferrosintesis-samples/prepare.py`
finds 12 top-level functions calling `write_wav_mono` directly; 11 match the guarded prefix
(`_bake_bagpipe`, `_bake_clavinet`, `_bake_sf_onset`, `_bake_musescore_grand`,
`_bake_ydp_grand`, `_bake_honkytonk`, `_bake_b1upright`, `_bake_darkened_grand`,
`bake_bottle_loop`, `_bake_mtg_sax`, `_bake_gong_bank`). So the guard covers the real
population, not a token two — which was the specific failure mode this bug was raised about.

**Residual, split to MM-BUG-KILN-00156.** The enumeration filters by NAME
(`crates/ferrosintesis/src/inventory.rs:233`), while this bug's own fix direction asked for a
BEHAVIOURAL predicate. I took the oracle's positive control byte-for-byte, renamed the helper
from `_bake_newbank` to `prepare_newbank`, and `unvalidated_bake_output_helpers` returned `[]`
— the same defect, unflagged. All three adversarial controls share the `_bake_` prefix, so
none of them tests the enumeration. The twelfth writer, `main`, is outside the guard and is
correct today only by its author's care: it calls the validator at
`tools/ferrosintesis-samples/prepare.py:3336`, ahead of its packaged writes at `:3564` and
`:3572`. That is a narrower gap than the bug as filed, so it is tracked separately rather than
holding this one open.

**Gates, observed on the verification worktree at `8a4c90f`:** `cargo test --workspace
--release` 812 passed / 0 failed / 41 ignored in the ferrosintesis suite, 0 failed across all
39 other suites; `cargo clippy --workspace --all-targets -- -D warnings` and the same under
`--no-default-features` both exit 0; `cargo fmt --all --check` clean. No known-unrelated
failures.
