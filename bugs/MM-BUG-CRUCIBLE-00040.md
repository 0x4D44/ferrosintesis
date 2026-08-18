# MM-BUG-CRUCIBLE-00040 — Generated sample-crate payload test is self-referential: nothing binds an embedded payload to its packaged file

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample asset crates / generated oracles
- **Raised:** 2026-08-18T00:08:18Z
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
- **State history:** Open (2026-08-18T00:08:18Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** Each sample crate ships two tests that together look like a payload check.
Neither ever compares an embedded payload against the file it claims to embed. One of the
two assertions cannot fail at all.

**Expected.** `SAMPLES[i] == (name, bytes of samples/<name>)` for every entry — the
property the crate's public `get(name)` contract rests on.

**Actual**, in `crates/ferrosintesis-samples-bass/src/lib.rs`:

- `inventory_matches_packaged_samples` (`:87-100`) compares the *sorted name list* against
  `read_dir("samples")`. It never opens a file.
- `every_sample_is_a_nonempty_bank_file_with_the_expected_size` (`:103-116`) asserts the
  **aggregate** byte total (`:104-107`), a ≥12-byte floor (`:109`), `RIFF`/`fLaC` magic
  (`:110-112`), and then `:113`:

```rust
for (name, bytes) in SAMPLES {
    ...
    assert_eq!(get(name), Some(bytes));
}
```

`get` (`:68-73`) searches `SAMPLES` for `name` and returns that entry's bytes. The loop
therefore hands `get` a name taken from `SAMPLES` and compares the result to the bytes from
that same tuple. **It can only agree with itself.** The sole way to make it fail is a
duplicate name — which `inventory_matches_packaged_samples` already excludes. This is
exactly the shape CLAUDE.md names as proving nothing: "an assertion checked against a
constant the code under test also derives".

**The aggregate is permutation-invariant, and here that is not theoretical.** I measured
the STREAMINFO of all 13 committed bass FLACs: every one is 44.1 kHz, mono, 16-bit, and
**exactly 40042 frames** — an identical decoded length across the whole bank (the sibling
`-strings` `pizzbass_E1.flac` is also 40042, so the fixed length is a repo-wide bake
constant, not a bass coincidence). Compressed sizes differ (26–30 KB), but a *swap*
preserves the multiset of sizes and so preserves the sum exactly.

**Concrete defeat.** Transpose the `include_bytes!` targets of two entries — leave the name
`"fingerbass_E1.flac"` at `:14` but point `:15` at `../samples/fingerbass_D2.flac`, and
vice versa. Then:

| Guard | Result |
|---|---|
| `inventory_matches_packaged_samples` (`:87-100`) | green — names unchanged |
| aggregate `EXPECTED_BYTES` (`:104-107`) | green — sum unchanged |
| `RIFF`/`fLaC` magic (`:110-112`) | green — both are valid FLAC |
| `assert_eq!(get(name), Some(bytes))` (`:113`) | green — tautology |
| `ferrosintesis-flac` STREAMINFO MD5 (`crates/ferrosintesis-flac/src/lib.rs:374-382`) | green — each file still matches *its own* embedded hash |
| `every_note_named_zone_root_matches_its_filename` (`crates/ferrosintesis/src/sampler.rs:6639-6707`) | green — a source-text scan; never touches PCM |
| `banks_parse` (`sampler.rs:7420-7478`) | not applicable — does not chain `finger_bass`/`pick_bass` (MM-BUG-CRUCIBLE-00041) |

`crates/ferrosintesis/src/sampler.rs:967` then pairs a D2 recording with a 41.22 Hz root
claim: GM 33 and GM 35 play E1 with a body repitched a whole tone, and GM 33 D2 likewise —
silently, on a box with no ears. The same holds if the two *files on disk* are swapped
rather than the tuples, since `include_bytes!` follows the path.

**Scope — assume all 24 crates.** `src/lib.rs` in every sample crate is emitted by
`tools/ferrosintesis-samples/gen_crate_lib.py`;
`crates/ferrosintesis-samples-sax/src/lib.rs:369-382` is identical in shape. Per CLAUDE.md
("when a bug reports X is missing from list L, enumerate all of L before fixing"), the unit
of work is the generator, not the bass crate.

Static review only. No build or test ran; the defeat above is traced from source, and the
STREAMINFO measurements were read directly from the committed bytes.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

In `gen_crate_lib.py`, emit a check that compares each embedded payload to the file it
names, rather than to itself. The whole of it:

```rust
for (name, bytes) in SAMPLES {
    assert_eq!(fs::read(samples_dir.join(name)).unwrap(), bytes, "{name}");
}
```

`samples_dir` is already in scope in `inventory_matches_packaged_samples` (`:88`). This
closes both halves at once: the tautology, and the cancel-out case the aggregate misses
(one file shrinking by N bytes while another grows by N is green today, despite the test
being named `..._with_the_expected_size`).

Note this test is compiled into the published archive and `samples/**` is packaged
(`Cargo.toml:10`), so it still works from a `.crate` unpack — unlike the parent-crate
oracles, which are gated behind `ferrosintesis_repository_tests`.

**Prove it fails first.** Regenerate one crate with two `include_bytes!` targets
transposed, watch the new assertion go red and the four existing ones stay green, then
restore. A fix landed without that demonstration repeats the defect being reported.

## Notes

- Draft `MM-REQ-KILN-00211` records the same undetectable-swap consequence for bass and
  asks for a heavyweight verifier binding packaged files to source-archive members and
  measured roots. This bug is the narrow, one-line half of that: it does not authenticate
  provenance, it just makes the crate's existing payload assertion non-vacuous. Its Notes
  are also now stale — they describe the bank as "13 WAVs, 80,128 bytes each"; the bank has
  been FLAC since 2026.08.16 and the files are 26–30 KB, though the equal *decoded* length
  that makes a swap invisible still holds.
- What remains uncovered after this fix: the roots in `sampler.rs:967-972` and `:989-995`
  are still hand-copied literals with no derivation link to the audio — the bake measures
  each root (`prepare.py:5933`) but only prints it (`_print_sample_rows`,
  `prepare.py:5420-5426`), persisting nothing machine-readable. That is REQ-00211's
  territory, not this bug's.
- Estimated effort: Small.
