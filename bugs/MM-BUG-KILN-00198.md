# MM-BUG-KILN-00198 — Sax PROVENANCE says every packaged root is pinned in the sampler zone tables, but the two baritone G#3 takes are not

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** samples-sax / published provenance
- **Raised:** 2026-08-14T08:07:54Z
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
- **State history:** Open (2026-08-14T08:07:54Z, raised via `deltic bugs new`)

## Observation

**Expected.** The packaged provenance document describes the packaged bank
accurately: which takes are runtime zones, and where their roots are pinned.

**Actual.** `crates/ferrosintesis-samples-sax/PROVENANCE.md:49-50` states "The
measured roots are pinned in the `sax_*` zone tables in
`crates/ferrosintesis/src/sampler.rs`", and the surrounding prose presents all 74
packaged WAVs as supplying the default voice. But two packaged takes —
`sax_bar_G#3_p.wav` and `sax_bar_G#3_f.wav` — were deliberately removed from the
runtime zone tables by MM-BUG-KILN-00178 (forte breakup; the soft layer removed with
it for p/f symmetry) and kept packaged for provenance only. Their measured roots
(208.95 / 209.52 Hz) live solely inside the guarding test
`baritone_sax_bank_rejects_the_rough_source_population_outlier`
(`crates/ferrosintesis/src/sampler.rs:7909`), not in any zone table. The exclusion is
documented in a `sax_bar_p` code comment (`sampler.rs:2389`) and the bug record, but
not in the shipped PROVENANCE.md — the one document a crates.io consumer of the 4.1 MB
package actually receives.

**Classification.** Docs drift in a shipped provenance document: a consumer auditing
the package against its own provenance finds two WAVs whose stated pinning location
does not contain them, and no explanation why. Same defect family as
MM-BUG-KILN-00069/00159 (published sample docs falling behind the code).

Found by the 2026-08-14 code-review pass over `crates/ferrosintesis-samples-sax/`;
verified by reading the zone tables (`sampler.rs:2386-2419` — 9 baritone zones per
dynamic, no G#3) against the 74-file packaged set (10 baritone notes × 2 dynamics).

## Fix

<unfixed — raised only>

Suggested shape: add two or three sentences to
`crates/ferrosintesis-samples-sax/PROVENANCE.md` (Selection or Inventory section)
recording that the baritone G#3 takes are packaged for provenance but excluded from
the runtime zone tables per MM-BUG-KILN-00178, with the forte take being the measured
rough outlier and the population-relative oracle that enforces the exclusion. Keep the
phrases asserted by
`sampler::tests::sax_published_docs_describe_the_looped_recording_voice`
(`crates/ferrosintesis/src/sampler.rs:5901`) intact — it checks for required and
stale-phrase text in this exact file.

## Notes

- The exclusion itself is correct and well-oracled (this is NOT a request to restore
  the zones); only the shipped document misdescribes it.
