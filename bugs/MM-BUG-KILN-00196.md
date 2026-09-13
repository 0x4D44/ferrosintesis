# MM-BUG-KILN-00196 — b1-upright packages samples/** but its inventory oracle counts only lowercase top-level .wav, so junk ships unvetted

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** samples-b1-upright / packaging
- **Raised:** 2026-08-14T07:06:14Z
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
- **State history:** Open (2026-08-14T07:06:14Z, raised via `deltic bugs new` model=claude-fable-5) -> Fixed (2026-08-15T15:49:24Z, deltic:auto role=fix run=fix-20260815T154441Z-p20220-n322888900-c1 branch=task/bug-MM-BUG-KILN-00196-run-fix-20260815T154441Z-p20220-n322888900-c1 code=5ca3a8f gate=manual) -> Closed (2026-09-13T21:00:07Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: planted junk.txt, EXTRA.WAV and a raw/ subdirectory in the gong crate were each named by the oracle)

## Observation

**Symptom.** The published crate's contents and its inventory oracle enumerate
different sets. `crates/ferrosintesis-samples-b1-upright/Cargo.toml:10` packages
`samples/**` — everything, recursively. The oracle
`inventory_matches_packaged_wavs` (`crates/ferrosintesis-samples-b1-upright/src/lib.rs:288-301`)
enumerates with a non-recursive `read_dir` filtered by a case-sensitive
`extension() == "wav"` (`lib.rs:293`), and the regen tool uses the same shape —
case-sensitive `f.endswith(".wav")` over `os.listdir`
(`tools/ferrosintesis-samples/regen_samples_table.py:106`).

**Failure scenario.** Any of `samples/extra.WAV` (wrong case), `samples/notes.txt`, or
a `samples/raw/` subdirectory holding anything at all is invisible to both the test and
the tool, yet ships in the published `.crate`. For a CC0-declared crate that means
package bloat at best and unvetted/unlicensed content at worst, with zero oracle
coverage. (A lowercase top-level `.wav` that is packaged but not embedded IS caught —
`packaged.len() != FILE_COUNT`, `lib.rs:299` — the gap is exactly the
non-`.wav`-named / nested set.)

**Current state is clean** — the directory holds exactly the 52 embedded WAVs (verified
2026-08-14) — so this is a latent gate gap, not shipped junk today. Classified a defect
because the crate's stated invariant ("every packaged sample is documented/embedded")
is enforced against a narrower set than what `include` actually packages.

Likely shared by sibling `ferrosintesis-samples-*` crates whose manifests use the same
`samples/**` include with the same generated-test shape; whoever fixes this should
enumerate all of them first (CLAUDE.md: when a list item is reported missing, re-read
the whole list).

Found by an adversarial defeat-the-oracle review pass (2026-08-14 code review,
`crates/ferrosintesis-samples-b1-upright/`); verified against source by the reviewing
lead.

## Fix

<unfixed — raised only>

Suggested shape: make the oracle enumerate what `include` packages — walk
`samples/` recursively and assert every entry is a top-level lowercase `.wav` in the
embedded set (fail on anything else) — or narrow the manifest include to
`samples/*.wav`. Either closes the set difference; doing both is cheapest to reason
about. Prove it by dropping a `samples/junk.txt` into a scratch copy and watching the
strengthened test go red.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `5ca3a8fe`, later extended for FLAC) by an agent other than the fixer.

**Adversarial check (as the record asks).** Planting `junk.txt`, `EXTRA.WAV` and a `raw/` subdirectory under `crates/ferrosintesis-samples-gong/samples/` makes `inventory::tests::packaged_sample_directories_hold_only_top_level_lowercase_wavs` fail, naming all three. Removed; the tree is clean and the oracle passes.

One workspace sweep now enumerates what every sample crate's `samples/**` packages, not only what it embeds.

**Gates.** Causes no gate failure; trunk `8b6a6f86` is red for other recorded reasons.

## Notes

- Found together with MM-BUG-KILN-00195 (the tail-only validator gap in the same
  crate); they are separable fixes.
