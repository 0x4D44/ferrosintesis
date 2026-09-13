# MM-BUG-KILN-00209 — Bass regeneration can publish a mixed bank after a late failure

- **State:** Closed
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
- **State history:** Open (2026-08-16T09:39:44Z, raised via `deltic bugs new`) -> Fixed (2026-09-13T05:10:23Z, deltic:auto role=fix run=fix-20260913T044533Z-298b1291 branch=task/bug-MM-BUG-KILN-00209-run-fix-20260913T044533Z-298b1291 code=fd8cead81ec76a070a9300ce13a5e097003177fb gate=manual) -> Closed (2026-09-13T20:22:13Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: staging and rollback reversals each redden the bass old-bank snapshot tests; main routing pinned)

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

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `fd8cead8`, later consolidated into `_publish_staged_flac_bank`) by an agent other than the fixer.

`BassWholeBankPublicationTest` injects failures on the 5th transform and a late replacement; on HEAD the old bank is preserved, and `test_main_routes_selected_bass_through_the_whole_bank_baker` pins the routing.

**Fails-before (method B).** The staging redirect fails the late-transform test (`fingerbass_A#1.wav` published into the live bank); the rollback reversal fails the publication test on the snapshot. Restored; all three pass on HEAD.

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
