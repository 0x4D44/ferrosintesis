# MM-BUG-CRU-00052 — Realtime prewarm memory guidance still assumes uncompressed sample payloads after the FLAC migration

- **State:** Open
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
- **State history:** Open (2026-08-20T15:01:11Z, raised via `deltic bugs new`)

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

## Notes
