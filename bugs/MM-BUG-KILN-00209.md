# MM-BUG-KILN-00209 — Bass regeneration can publish a mixed bank after a late failure

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** electric-bass sample generation / failure atomicity
- **Raised:** 2026-08-16T09:39:44Z
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
- **State history:** Open (2026-08-16T09:39:44Z, raised via `deltic bugs new`)

## Observation

The generic bass bake processes each selected WAV and immediately writes its final
tracked destination (`tools/ferrosintesis-samples/prepare.py:5733-5779`).
`write_wav_mono()` uses a `.part` file and `os.replace`, so one WAV is atomic, but
the bank is not (`prepare.py:4247-4263`).

If a later source read, transform, root measurement, allocation, or destination
replacement fails, the already-written prefix remains from the new bake while the
unwritten suffix remains from the old bake. The mixed bank can retain the right
names and valid RIFF files, so the crate's inventory and RIFF-magic tests need not
reject it.

Expected: a failed bass regeneration leaves the previous selected bank
byte-identical. Actual: generation, validation, and publication are interleaved per
file, so a late failure can publish a mixed-generation bank. The current committed
bank is coherent; this is the live failure path, not a claim of current corruption.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

## Notes

Generate every selected output in an empty staging directory, validate the complete
inventory and WAV/root contracts, then publish with rollback if any replacement
fails. Add negative controls for a late transform failure and an injected publish
failure after several staged files; both must preserve the old bank byte-for-byte.
This is the bass instance of the failure shape tracked for YDP by open
`MM-BUG-KILN-00205`; the code paths and acceptance fixtures are distinct.
Estimated effort: Small–Medium.

Static review only. No generator, app, build, test, render, package, or exploratory
harness ran.
