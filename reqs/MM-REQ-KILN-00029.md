# MM-REQ-KILN-00029 — Retain offline-auditable licence evidence for login-gated CC-BY samples

- **State:** Implemented
- **Priority:** Should
- **Area:** sample assets / licence provenance
- **Raised:** 2026-07-24
- **Implemented-by:** `tools/ferrosintesis-samples/freesound-src/_readme_and_license_{3957,19445,44539}.txt`; `crates/ferrosintesis-samples-ccby/PROVENANCE.md`; `crates/ferrosintesis-samples-gong/PROVENANCE.md`; `crates/ferrosintesis-samples-orchestral2/PROVENANCE.md`; `crates/ferrosintesis-samples-mandolin/PROVENANCE.md`
- **Satisfied-by:** `crates/ferrosintesis/src/provenance.rs::every_committed_source_is_pinned_by_a_packaged_document`; `::the_retained_freesound_licence_manifests_are_present`; `::the_coverage_check_rejects_an_unpinned_source`; `::sha256_matches_known_vectors`
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
- **State history:** Draft (2026-07-24, captured by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-ccby/`) → Implemented (2026-07-25, scope widened to all four login-gated crates at Arthur's direction; the oracle is complete, so this is awaiting a second pair of eyes rather than missing coverage)

## Statement

The repository must retain immutable, offline-auditable upstream licence evidence for
each login-gated CC-BY Freesound source embedded by
`ferrosintesis-samples-ccby`.

## Notes

- `crates/ferrosintesis-samples-ccby/PROVENANCE.md:3-4` cites each pack's bundled
  `_readme_and_license.txt` as the evidence for CC-BY 4.0.
- The same document says Freesound downloads are login-gated. No cited licence
  manifest is tracked in the repository; `tools/ferrosintesis-samples/freesound-src/`
  contains only WAVs.
- Acceptable evidence could be the original two manifests, or immutable metadata
  snapshots containing source/pack IDs, author, licence, source URL, and content hash.
- This does not challenge the current `NOTICE`; it preserves the evidence needed to
  audit that notice without a Freesound account or mutable upstream page.

## Resolution (2026-07-25)

The original pack downloads were still on Arthur's machine, so the first acceptable form
in the Notes above was achievable: **the upstream manifests are now committed verbatim**,
not transcribed.

What landed:

1. **Three retained manifests** under `tools/ferrosintesis-samples/freesound-src/` —
   packs 3957 (Rhodes), 19445 (dulcimer) and 44539 (music box), each the
   `_readme_and_license.txt` Freesound bundles with a pack download, byte-for-byte. They
   settle two things nothing in the repo could settle before: the per-sound licence
   (53/53 and 15/15 "Attribution 4.0"; 11/11 "Creative Commons 0"), and the licence
   **version** — both CC-BY pack IDs predate CC BY 4.0, so 4.0 was previously an
   unverifiable claim.
2. **The per-sound mapping, recovered.** The 20 ccby sources had been renamed to measured
   pitch before first commit, severing the link to the individual sound. Each committed
   clip was cross-correlated against the decoded pack originals; all 31 clips (ccby +
   music box) matched at 1.0000 with the runner-up never above 0.62. `PROVENANCE.md` now
   carries the file → sound-ID → source-URL table.
3. **Scope widened from `-ccby` to all four login-gated crates** at Arthur's direction —
   `-ccby`, `-gong`, `-orchestral2`, `-bottle`. Fixing only the crate that was reported
   would have repeated the drift pattern the repo already documents.
4. **Every committed source is now hashed** — 77 files across the three `*-src/`
   directories, up from 21. This includes the 40 owner-recorded mandolin cuts, which carry
   no licence obligation but *are* an irreplaceable master (the raw take is not committed).
5. **A derived oracle**, `crates/ferrosintesis/src/provenance.rs`, keyed off the glob
   `tools/ferrosintesis-samples/*-src` rather than a list of directory names, requiring
   every committed source to be pinned by a hash in a **packaged** `PROVENANCE.md`. It was
   verified by refutation: dropping one recorded hash turns it red naming exactly that file.

**What is still open, and cannot be closed by this work.** `-gong`'s two sounds were fetched
individually, not as a pack, and Freesound bundles a manifest only with a pack download. The
committed gong WAVs are byte-identical to the Freesound originals — so the *audio* is fully
auditable — but the CC BY 3.0 line still rests on a human having read two sound pages. Closing
that needs either a pack download containing 261890/261893, or a snapshot of the two sound
pages. Recorded here rather than papered over.

