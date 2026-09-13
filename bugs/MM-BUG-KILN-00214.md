# MM-BUG-KILN-00214 — Bottle sample name says G3 while its measured root is 205 Hz

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** sample package / bottle pitch metadata
- **Raised:** 2026-08-16T11:38:37Z
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
- **State history:** Open (2026-08-16T11:38:37Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T15:41:57Z, deltic:auto role=fix run=fix-20260913T153622Z-8d72e8db branch=task/bug-MM-BUG-KILN-00214-run-fix-20260913T153622Z-8d72e8db code=1f1892c98b12eb5270d5d4b7adbe978afbecd5b3 gate=manual) -> Closed (2026-09-13T19:59:17Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: bottle crate exports MEASURED_ROOT_HZ 205.0 used by the sampler; pre-fix docs fail the metadata contract test)

## Observation

The crate's only public lookup key is `bottleloop_G3.wav`
(`crates/ferrosintesis-samples-bottle/src/lib.rs:15-17`), and the README and provenance
repeat the G3 label. Those same documents and the runtime mapping state that the
recording's measured root is 205.0 Hz
(`crates/ferrosintesis-samples-bottle/README.md:8`,
`crates/ferrosintesis-samples-bottle/PROVENANCE.md:27-28`,
`crates/ferrosintesis/src/sampler.rs:4572-4579`). Equal-tempered G3 is about 196.00 Hz,
so 205.0 Hz is 77.7 cents sharp of G3 and only about 22 cents flat of G-sharp 3.

The synth is correct because it repitches from 205.0 Hz and its pitch-integrity oracle
uses that runtime root. The defect is the public filename/API metadata: a direct crate
consumer or maintainer can reasonably infer 196 Hz from `G3` and apply the wrong
repitch. Static review and WAV-header inspection only; acoustic root measurement and
the app/tests were not run.

## Fix

<unfixed — raised only>

Prefer the non-breaking correction: keep the established lookup key but explicitly
label it as a historical/source filename and state that consumers must use the measured
205.0 Hz root (approximately G-sharp 3). If a breaking rename is acceptable in a future
release, rename the asset and every generator/runtime key together. Add measured-root
metadata or a documented accessor so direct consumers do not infer pitch from the
filename.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `1f1892c9`) by an agent other than the fixer.

**Original observation re-derived.** The bottle crate exports `MEASURED_ROOT_HZ: f32 = 205.0`, and `sampler.rs` builds the zone from it (a matching constant without default features). README, PROVENANCE and rustdoc call `bottleloop_G3.flac` a historical filename and give 205.0 Hz (about 22 cents flat of G#3). The constant equals the root the synth already used, so renders are unchanged.

**Fails-before (method A).** With the README and PROVENANCE from `1f1892c9^`, `BottleMeasuredRootMetadataTest` fails in two subtests. It passes on HEAD, as do `bottle_loop_pitch_integrity`, `bottle_loop_level_parity_and_flat` and `wd_o13_bottle_level_pitch_and_bend_across_keys`.

## Notes
