# MM-BUG-KILN-00126 — Published drum-kit inventory and kick provenance are stale

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** drum-kit package documentation / provenance
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
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-26, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-drumkit/`) -> Fixed (2026-07-26, deltic:auto role=fix run=fix-20260726T083911Z-p34720-n358957300-c1 branch=task/bug-MM-BUG-KILN-00126-run-fix-20260726T083911Z-p34720-n358957300-c1 code=378167ab3245b4a6628e49bfb8227cf5d98734a3 gate=manual) -> Closed (2026-07-26, verified by Claude Opus 5 @ high, fresh context - I did not author this fix (fixer: deltic:auto role=fix), so I am eligible as the second pair of eyes. Repo gate green on the fix-bearing tree: `cargo fmt --all --check`, both clippy configurations with `-D warnings`, `test -p ferrosintesis --no-default-features --locked` (635 passed) and `test --workspace --exclude amp-lab --locked` (740 passed) - 1478 tests, 0 failures; the sample-tool Python suite passes 44. Original observation re-run at source across every surface the bug named. The core README now states 140 WAVs and explicitly attributes crash, sizzle crash, splash and china to the sibling `ferrosintesis-samples-drumkit2`; the stale "109" claim is gone. `tools/ferrosintesis-samples/README.md` now describes the correct two-package ownership (140 core, 48 companion) including the kick's `kickmic` exception. The core `PROVENANCE.md` no longer says every family uses the `mid` mic set - it reads "`mid` for every family except the kick; `kickmic` for the kick" - and its kick row names `kickmic_kick_snon`, matching the generator's actual source URL at `prepare_drumkit.py:105-109`. The new guard `test_core_provenance_source_stems_match_the_generator_manifest` is properly derived: it reconstructs each core family's expected source stem from the generator's own `BANKS`/`PSEUDO_RR_BANKS` manifest rather than from a second hand-written list. CLOSED WITH A RESIDUAL SPLIT OUT AS MM-BUG-KILN-00131. Following this repo's own "enumerate all of L before fixing" rule, I swept the whole class repo-wide instead of only re-reading the cited lines, and found one surviving instance the fix did not sweep: `crates/ferrosintesis-samples-drumkit/src/lib.rs:682` still documents the kick as `mid_kick_snon`. That surface is PACKAGED - `Cargo.toml:13` includes `src/**` - so the wrong stem ships to crates.io and renders on docs.rs. It is a residual rather than a persistence of this bug: every line 00126 actually cited (`PROVENANCE.md:36-52,60-72`, `README.md:3-10`, the tooling overview) is correctly fixed, and the new oracle reads only `PROVENANCE.md`, never `src/lib.rs`, which is both why the instance survived and why it can drift again. Recorded in full on 00131.)

## Observation

The core crate's published README still describes the pre-split cymbal bank.

`crates/ferrosintesis-samples-drumkit/README.md:3-10` claims 109 WAVs and lists
crash, sizzle crash, splash, and china as core contents sourced partly from Big Rusty
Drums. The core crate actually embeds 140 ride/hat/kick/snare/tom WAVs
(`crates/ferrosintesis-samples-drumkit/src/lib.rs:27-33`), while those four accent
banks moved to the companion crate
(`crates/ferrosintesis-samples-drumkit/PROVENANCE.md:19-32`).

The tooling overview repeats the old ownership at
`tools/ferrosintesis-samples/README.md:3-7`.

The core provenance has a second, independent factual error. It says every bank uses
the `mid` mic set and names the kick source stem `mid_kick_snon` at
`crates/ferrosintesis-samples-drumkit/PROVENANCE.md:36-52,60-72`. The generator
intentionally sources all sixteen kick takes from the `kickmic` close-mic set at
`tools/ferrosintesis-samples/prepare_drumkit.py:97-101`. Commit history confirms the
kick payloads and generator changed together when the kick was re-sourced.

Expected: packaged documentation accurately identifies the crate's contents and the
recording source behind each shipped family.

Actual: crates.io consumers and provenance auditors receive the old package boundary
and the wrong kick microphone. The sources are CC0, so this is not an attribution
breach; it is inaccurate published inventory and provenance.

## Fix

Update the core crate description and README to describe its 140-file core-kit
inventory and point to `ferrosintesis-samples-drumkit2` for the 48 accent WAVs.
Update the tooling overview to describe both destinations.

In core `PROVENANCE.md`, document `mid` for every family except the kick, and record
the kick's `kickmic_kick_snon` source stem and close-mic rationale.

Add an adversarial documentation oracle only if this drift recurs: derive crate
ownership and source stems from one generator manifest rather than maintaining the
same facts in several prose files.

Estimated effort: Small.

## Notes

No existing bug or open requirement covered these current drum-kit documentation
errors.
