# MM-BUG-CRU-00052 — Realtime prewarm memory guidance still assumes uncompressed sample payloads after the FLAC migration

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** realtime API / sample prewarm documentation
- **Raised:** 2026-08-20T15:01:11Z
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
- **State history:** Open (2026-08-20T15:01:11Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:20:50Z, deltic:auto role=fix run=fix-20260913T151752Z-de616c4c branch=task/bug-MM-BUG-CRU-00052-run-fix-20260913T151752Z-de616c4c code=dc6aa28a93c3cab614cd6579157bc5ce74bed8c6 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: prewarm guidance now says four bytes per decoded mono frame, matching the f32 decode; reversing the hunk fails the wording test)

## Observation

The public realtime API still sizes prewarm memory as though the embedded banks were
uncompressed PCM16. `D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\crates\ferrosintesis\src\live.rs:301-308`
says prewarming holds decoded PCM for the process lifetime and that “Ordinary PCM16 banks
expand to roughly twice their embedded bytes.” Since the 2026-08-17 release, ordinary
sample-bank bytes are compressed FLAC, while
`D:\worktrees\ferrosintesis\20260820-REV-MM-CDX@CRUCIBLE-code-review-153056\crates\ferrosintesis\src\sampler.rs:71-79`
decodes them into `Vec<f32>`.

Kawai is a concrete counterexample from this review. Its 32 embedded FLACs total 1,733,440
bytes. Static STREAMINFO inspection found 66,502 mono frames per file, so their retained
f32 samples occupy `32 * 66,502 * 4 = 8,512,256` bytes: 4.91 times the embedded bytes, not
roughly twice. A caller using the stated ratio budgets 3,466,880 bytes and is low by
5,045,376 bytes for Kawai alone. The STREAMINFO facts were read directly from the
committed files; no decoder, app, build, test, render, or exploratory harness ran.

Expected: setup documentation gives a container-aware memory rule suitable for capacity
planning. Actual: it applies the old WAV-era ratio to compressed FLAC payloads. The B1
exception remains separately and correctly quantified. Static review found no existing
Open bug or Draft requirement for this stale prewarm claim. Estimated effort: Small.

## Fix

<unfixed — raised only>

Replace the embedded-byte multiplier with the real invariant: decoded mono storage is
four bytes per PCM frame, while the ratio to compressed FLAC bytes varies by material.
Either state that formula without promising one ratio, or derive and publish a current
whole-bank estimate from the packaged STREAMINFO metadata. Keep the B1 custom-tail figure
separate. If a numeric estimate remains, bind it to a source-derived oracle so a future
container or inventory change cannot leave the public guidance stale again.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `dc6aa28a`) by an agent other than the fixer.

**Original observation re-derived.** The "roughly twice their embedded bytes" sentence is gone from the `live.rs` prewarm docs. Checked against code: `sampler.rs parse_wav` decodes FLAC with `decode_mono16` into a mono `Vec<f32>` (4 bytes per frame); the drum-kit caches hold `Vec<i16>`, so the rule over-budgets them, which is safe.

**Fails-before (method B).** Reversing the hunk fails `RealtimePrewarmMemoryDocumentationTest` ("'four bytes per decoded mono PCM frame' not found"). Restored; passes on HEAD.

## Notes
