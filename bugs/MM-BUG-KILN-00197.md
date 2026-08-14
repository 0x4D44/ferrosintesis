# MM-BUG-KILN-00197 — Sample-crate rustdoc headers carry a dangling 'ferrosintesis.' sentence fragment left by the legal-header sync

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** samples crates / published rustdoc
- **Raised:** 2026-08-14T08:07:50Z
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
- **State history:** Open (2026-08-14T08:07:50Z, raised via `deltic bugs new`)

## Observation

**Symptom.** Twelve sample crates' crate-level rustdoc contains a stray sentence
fragment: a line reading `` //! `ferrosintesis`. Licence/provenance: see … `` sits
after a line whose sentence is already complete, so the rendered doc paragraph reads
"…Attribution obligations are in `NOTICE`. `ferrosintesis`. Licence/provenance: see
`NOTICE` / `PROVENANCE.md`." — a dangling "`ferrosintesis`." that belongs to no
sentence. Example: `crates/ferrosintesis-samples-sax/src/lib.rs:7-8`.

**Cause.** `tools/ferrosintesis-samples/gen_crate_lib.py:43` (`legal_doc_line`)
renders the required legal pointer as a *hard-wrapped continuation line* — it is
grammatical only when the preceding line ends "…consumers normally reach it through"
(`gen_crate_lib.py:94`). The sync pass `e121847` ("fix(samples): keep generated legal
headers in sync", 2026-07-29) had to satisfy the new oracle
`GeneratedCrateDocHeaderTest.test_every_sample_crate_header_matches_the_generator`
(`tools/ferrosintesis-samples/test_prepare.py:3040-3066`), which requires the exact
`legal_doc_line` output in every crate's `lib.rs`. Where the header was fully
regenerated or the old line replaced (`2 +-` in the commit stat), the result reads
fine; where the line was purely appended to a hand-written header whose sentence was
already complete (`1 +` in the commit stat), the fragment dangles.

**Affected (12 of 25, enumerated from the whole set per the derive-the-list rule —
the preceding line ends a sentence, so the appended line dangles):**
`ferrosintesis-samples-sax` (lib.rs:8), `-core` (:4), `-clavinet` (:7),
`-drumkit` (:22), `-drumkit2` (:18), `-gong` (:5), `-bottle` (:8),
`-fretnoise` (:8), `-grand` (:9), `-strings` (:14), `-musescore` (:12),
`-orchestral2` (:10). The other 13 crates integrate the line grammatically.

**Classification.** Cosmetic docs defect, but in the *published* crates.io rustdoc of
twelve packages, and self-inflicted by the oracle's line-shape assumption — the exact
"generated line pasted into hand prose" hazard the repo's derived-oracle doctrine
warns about.

Found by the 2026-08-14 code-review pass over `crates/ferrosintesis-samples-sax/`;
verified against source and the e121847 diff by the reviewing lead.

## Fix

<unfixed — raised only>

Suggested shape: for each of the 12 crates, rewrap the preceding hand-written prose so
it flows into the required line (e.g. end it "…consumers normally reach this crate
through"), keeping the `legal_doc_line` text byte-identical so
`test_every_sample_crate_header_matches_the_generator` stays green. For the sax crate
the rewrap must also keep the phrase "recorded attack plus looped recorded sustain"
and avoid the stale phrases asserted by
`sampler::tests::sax_published_docs_describe_the_looped_recording_voice`
(`crates/ferrosintesis/src/sampler.rs:5901`). Alternatively (deeper fix): split
`legal_doc_line` so the oracle-required marker starts at "Licence/provenance:" and the
"`ferrosintesis`. " prefix stays part of the generated-header wrap only — that removes
the trap for future hand-maintained headers at the cost of touching generator + oracle
+ 25 headers.

## Notes

- Sibling context: MM-BUG-KILN-00159 rewrote the sax header prose on 2026-07-28; the
  sync commit e121847 appended the generated line the day after, which is how the sax
  duplication ("through `ferrosintesis`. … `ferrosintesis`.") arose.
