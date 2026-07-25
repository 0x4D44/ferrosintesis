# MM-REQ-KILN-00031 — Fret-noise inventory must have one generated source of truth

- **State:** Implemented
- **Priority:** Could
- **Area:** fret-noise sample generation / package inventory
- **Raised:** 2026-07-24
- **Implemented-by:** `tools/ferrosintesis-samples/fretnoise_bake.py::discover_cuts` (replaces the `N = 12` literal), `crates/ferrosintesis-samples-fretnoise/src/lib.rs::SAMPLES` (now a slice) and `::FILE_COUNT` (now `SAMPLES.len()`)
- **Satisfied-by:** `crates/ferrosintesis-samples-fretnoise/src/lib.rs::tests::samples_are_in_canonical_round_robin_order`, `::tests::embedded_bytes_match_the_committed_files`, `::tests::inventory_matches_packaged_wavs`; the bake-side contiguity guard raises `SystemExit` from `discover_cuts` (manual: `python tools/ferrosintesis-samples/fretnoise_bake.py`)
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **Owner:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner since:** -
- **Owner until:** -
- **Auto attempts:** 0
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-fretnoise/`) → Implemented (2026-07-25, scope shrunk to the four real gaps by Arthur's decision — see Resolution)

## Statement

The fret-noise bake and asset crate must derive their contiguous source-cut set,
packaged filenames, file count, lookup table, round-robin count, and generated
inventory assertions from one authoritative inventory. A non-mutating check must
fail when committed outputs or generated Rust drift from that inventory.

## Notes

- `tools/ferrosintesis-samples/fretnoise_bake.py:32,123-137` owns `N = 12` and
  the source/output filename loops.
- `crates/ferrosintesis-samples-fretnoise/src/lib.rs:10-66,90-120` independently
  owns the same count, twelve include rows, round-robin alias, and byte total.
- `tools/ferrosintesis-samples/gen_crate_lib.py` already derives ordinary sample
  crate inventories. It needs a round-robin mode or a custom-tail template so it
  preserves `ROUND_ROBINS` and `take_name`.
- Atomic replacement of generated WAVs is already tracked by
  `MM-BUG-KILN-00063`. Generator-environment byte reproducibility is tracked by
  `MM-BUG-KILN-00095`; neither is duplicated by this inventory requirement.
- Proposed Gate-1 flow is light: the behavior and a source-derived drift oracle
  are bounded, despite touching both Python generation and generated Rust.

## Resolution (2026-07-25)

Implemented at a **deliberately shrunk scope**, chosen by Arthur after an
investigation found most of the Statement already satisfied and one Note
factually wrong. What follows records exactly what was and was not done.

### Clauses implemented

1. **"contiguous source-cut set"** — `fretnoise_bake.py` no longer carries
   `N = 12`. `discover_cuts()` enumerates
   `samples/fret-noise-eastman-e1d/cuts/fret_rrNN.wav`, requires the ordinals to
   run contiguously from 01, and rejects a non-conforming name. Previously a
   13th cut was silently ignored. The change is pure control flow: the
   discovered ordinal sequence is identical to the old `range(1, N + 1)`, which
   matters because the bake's single shared RNG is consumed sequentially, so any
   change to enumeration order or membership would rewrite every subsequent
   file's dither bytes. **No committed WAV was re-baked or touched.**
2. **"file count"** — `FILE_COUNT` is now `SAMPLES.len()`, and `SAMPLES` is a
   slice rather than a fixed-size array (the shape already used by
   `-musescore`, `-orchestral2` and `-strings`). The `ROUND_ROBINS` → `FILE_COUNT`
   → `SAMPLES` chain now bottoms out on the `include_bytes!` rows.
3. **"generated inventory assertions"** — the row ORDER was an unoracled but
   explicitly documented contract, and is now pinned by
   `samples_are_in_canonical_round_robin_order`. See the correction below for why
   the pre-existing test could not cover it.
4. `embedded_bytes_match_the_committed_files` was added so the
   embedded-bytes-are-the-committed-files property is machine-checked without a
   hand-maintained number.

### Clause deliberately NOT implemented

**"`gen_crate_lib.py` needs a round-robin mode or a custom-tail template."**
Rejected, on three findings from disk:

- `tools/ferrosintesis-samples/regen_samples_table.py` **already exists** and
  already does exactly what the Note asks for — it rewrites only the generated
  `SAMPLES`/`FILE_COUNT` region, preserves a hand-written tail, and re-runs
  rustfmt. The clause is therefore moot as written.
- fretnoise is **1 of 12 hand-written crates out of 25**, not an outlier that
  needs normalising.
- `gen_crate_lib.py` emits a **literal** `FILE_COUNT` (`gen_crate_lib.py:44`),
  which is *worse* than what the slice-shaped hand-written crates already do.
  Converting fretnoise to it would have re-introduced the very literal this
  requirement exists to remove, and replaced working oracled code.

`EXPECTED_BYTES` was examined and **deliberately left as a pinned literal**.
Deriving it from `SAMPLES` would assert `sum == sum` — vacuous. Deriving it from
the files on disk would merely mirror whatever was last baked, destroying its
only real value: it is a canary that turns red if a re-bake changes the committed
bank, which is precisely the event this repo wants a human to see. The derived
half of that property is the new
`embedded_bytes_match_the_committed_files`, which needs no re-pinning.

### Corrections to the Notes above

- **"`lib.rs` … independently owns … the round-robin alias" is wrong.**
  `ROUND_ROBINS` was already `= FILE_COUNT` (lib.rs:66 at the time of writing) —
  already derived, never independently owned.
- **"`lib.rs:10-66,90-120` independently owns the same count" overstates it.**
  The old declaration was `static SAMPLES: [(&str, &[u8]); FILE_COUNT]`, whose
  array length the compiler pins to the row count (verified with `rustc`), so
  `FILE_COUNT` could not silently disagree with the table. The literal was a
  genuine maintenance burden — a human had to update it — but not a live
  correctness hole. That distinction is why this requirement is `Could`, not
  `Must`.
- The Notes did **not** name the one real correctness gap in `lib.rs`: the
  positional row ORDER. `take_name(rr)` indexes `SAMPLES[rr % ROUND_ROBINS]`
  positionally and `sampler.rs:fret_noise_takes` caches the decoded takes in
  that order, but `inventory_matches_packaged_wavs` **sorts both sides** before
  comparing and only `take_name(0)` was pinned — so rows 2..N could be permuted
  freely with the whole suite green. That test is the sorted shape
  `gen_crate_lib.py:79-86` emits for the 13 generated crates where `get(name)` is
  the only accessor and order genuinely does not matter; fretnoise is the one
  crate with a positional accessor, so it inherited a test strictly too weak for
  it. Verified by refutation: permuting rows 2 and 3 leaves all four
  pre-existing tests green and fails only the new oracle.

### Coverage that already existed and was not rebuilt

`inventory_matches_packaged_wavs` already read `samples/*.wav` off disk and
asserted names and `FILE_COUNT` against `SAMPLES`; round-robin wrap semantics,
the lookup table's exhaustiveness and the `get("missing.wav") == None` negative
case were all already oracled; and `crates/ferrosintesis/src/inventory.rs`,
`payload.rs` and `licensing.rs` already cover this crate at the repo level by
globbing `ferrosintesis-samples-*` (licensing correctly exempts it as CC0).

MM-BUG-KILN-00063 (atomic replacement of generated WAVs) and MM-BUG-KILN-00095
(generator byte reproducibility) remain untouched and unblocked by this change.
