# MM-REQ-KILN-00286 — Core drum-kit assets and runtime takes must be independently verifiable

- **State:** Draft
- **Priority:** Could
- **Area:** core drum-kit sample assets / deterministic verification
- **Raised:** 2026-08-17T11:40:19Z
- **Discovery source:** Agent
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Depends-on:** —
- **Design:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-08-17T11:40:19Z, raised via `deltic reqs new`)

## Statement

The core drum-kit bank must be independently verifiable from its pinned source
selection and deterministic bake through the final FLAC payloads, `SAMPLES`
labels, bank descriptors, and runtime take selection. A non-mutating oracle must
bind each packaged filename to the exact bytes included under that label, prove
every registered bank/take is covered once, and validate the expected decoded
audio properties. Negative controls must include a same-family `include_bytes!`
path swap, a duplicate payload under two labels, an unembedded packaged file, a
stale velocity or first-index descriptor, and a valid but silent FLAC.

## Notes

Current static inspection found 128 FLAC names, table entries, and bank-derived
names in agreement; no current payload swap or corruption was established.
`crates/ferrosintesis-samples-drumkit/src/lib.rs:904-923` compares labels and two
views of the same cache, while `:947-960` checks an aggregate size, magic, and
self-lookup. Swapping two same-family `include_bytes!` paths can preserve all of
those assertions. Open `MM-BUG-KILN-00284` covers the narrower omission of 33
takes from the current audio-quality loop. Draft `MM-REQ-KILN-00176` covers
accent-bank descriptor parity only, and Draft `MM-REQ-KILN-00237` covers decoder
conformance; neither binds this package's payload identities end to end.

Proposed effort: Medium. Proposed flow: heavy.
