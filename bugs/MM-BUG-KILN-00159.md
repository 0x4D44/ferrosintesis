# MM-BUG-KILN-00159 — Published sax provenance describes the retired onset-only voice

- **State:** Open
- **Priority:** Could
- **Severity:** Low
- **Area:** sample assets / sax documentation
- **Raised:** 2026-07-28
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260728T040109Z-p57192-n646860400-c93
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00159-run-fix-20260728T040109Z-p57192-n646860400-c93
- **Owner base:** 4bd6a5691900ed63e620eae8a13345a3e6167eae
- **Owner fingerprint:** -
- **Owner since:** 2026-07-28T04:01:09Z
- **Owner until:** 2026-07-28T04:46:09Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-28, raised via `deltic bugs new` model=gpt-5.6-sol@high)

## Observation

**Symptom.** The published sax crate documents the retired onset-only architecture. `crates/ferrosintesis-samples-sax/PROVENANCE.md:9-14` calls the bank attack/body material, and `:56-62` says the model carries sustain. Crate rustdoc at `src/lib.rs:3-6` says the samples layer over the modeled reed.

**Expected.** Published docs describe the current default voice: the recorded attack plays through into a pitch-synchronous loop of the recorded sustain; the modeled reed is used only with `--no-samples` or when the loop/repitch is unusable.

**Actual.** Current routing says the whole default voice is the recording and explicitly records that this replaced the onset-only layer (`crates/ferrosintesis/src/voices.rs:14926-14945`). `SaxLoopVoice` renders the recorded loop (`crates/ferrosintesis/src/sampler.rs:4061-4064,4133-4178`). The package docs therefore give consumers and maintainers an obsolete architecture and processing claim. No existing bug or requirement covers this documentation drift.

**Concrete fix.** Update crate rustdoc, README/provenance language, and the corresponding generator comments to describe recorded attack plus looped recorded sustain, with the modeled reed only as the documented fallback. Keep the 0.62-second source processing facts, but remove the claim that the model carries the default hold.

**Effort:** Extra small.

## Fix

<unfixed — raised only>

## Notes
