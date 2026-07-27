# MM-BUG-KILN-00145 — No oracle asserts bake helpers validate their output inventory, so the class recurs per bank

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** testing / sample generation
- **Raised:** 2026-07-26
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260727T033403Z-p9812-n749513500-c45
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00145-run-fix-20260727T033403Z-p9812-n749513500-c45
- **Owner base:** 6d9a568872af153f75f17fa5cee40c2b6ce73410
- **Owner fingerprint:** -
- **Owner since:** 2026-07-27T03:34:03Z
- **Owner until:** 2026-07-27T04:19:03Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised via `deltic bugs new` model=claude-opus-5@high)

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

## Notes
