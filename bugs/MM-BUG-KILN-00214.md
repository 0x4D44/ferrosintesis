# MM-BUG-KILN-00214 — Bottle sample name says G3 while its measured root is 205 Hz

- **State:** Open
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
- **State history:** Open (2026-08-16T11:38:37Z, raised via `deltic bugs new`)

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

## Notes
