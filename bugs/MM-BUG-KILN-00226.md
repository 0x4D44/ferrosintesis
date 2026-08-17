# MM-BUG-KILN-00226 — Dark-Salamander regeneration can publish a mixed bank after a late failure

- **State:** Closed
- **Priority:** Could
- **Severity:** Low
- **Area:** dark-Salamander sample generation / failure atomicity
- **Raised:** 2026-08-16T16:08:50Z
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
- **State history:** Open (2026-08-16T16:08:50Z, raised via `deltic bugs new` model=gpt-5.6-sol@high); Closed (2026-08-17T20:21:52Z, moot — subject code removed in 04d841ba, closed on Arthur's decision)

## Observation

Static review found that the documented dark-Salamander regeneration path publishes its 54 tracked WAVs one at a time. `D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-162512\tools\ferrosintesis-samples\prepare.py:5053` reads, transforms, and immediately calls `write_wav_mono` for each raw-grand source. `write_wav_mono` at `D:\worktrees\ferrosintesis\20260816-REV-MM-CDX@KILN-code-review-162512\tools\ferrosintesis-samples\prepare.py:4247` makes one destination atomic, but the bank has no staging or rollback.

A failure while reading, transforming, measuring, allocating, or writing a later file therefore leaves the already-replaced prefix from the new bake beside the untouched suffix from the old bake. Every file can remain present and structurally valid, so the crate inventory and RIFF-magic tests need not reject the mixed generation. The current committed bank is coherent; this is the live failure path in the documented `python3 tools/ferrosintesis-samples/prepare.py --only=darkgrand` command.

Expected: a failed darkgrand regeneration leaves the previous bank byte-identical. Actual: generation and publication are interleaved, so a late failure can expose a mixed old/new bank.

Concrete fix: validate the complete raw-grand source plan first, generate all dark outputs in an empty staging directory, verify the exact 54-file inventory and WAV contracts, then publish with rollback if any replacement fails. Add negative controls for a late source/transform failure and an injected replacement failure; both must preserve every prior destination byte-for-byte.

Existing records do not cover this path: MM-BUG-KILN-00123 covers stale dark destination names, MM-BUG-KILN-00182 covers selected raw-grand regeneration, and MM-REQ-KILN-00033 covers deterministic projection/output verification. Sibling failure-atomicity bugs MM-BUG-KILN-00205, 00209, and 00220 cover different bank generators. Estimated effort: Small-Medium. Static review only; no app, build, test, generator, render, package command, or exploratory harness ran.

## Fix

Not fixed — **closed as moot**. The failure path described here belongs to the
dark-Salamander regeneration recipe, and that bank was removed in `04d841ba`
("samples: remove the dark-Salamander alternate (GM 0 CC0=5)"). There is no
`--only=darkgrand` recipe left to run, so the interleaved generate-and-publish
sequence it describes no longer exists.

Closed on Arthur's explicit decision (2026-08-17), which is the second pair of
eyes the ledger's two-eyes rule requires. Note the rule is written for verifying
a *fix*; there is no fix to verify here, and the check that matters instead is
that the subject code is genuinely gone — `crates/ferrosintesis-samples-dark-salamander/`
is absent from trunk and the sample-crate census is now 24, pinned by
`test_every_sample_crate_header_matches_the_generator`.

## Notes

The general lesson outlived the bank, and the surviving generators now satisfy
it. `55298fb1` ("Bake sample banks as FLAC end to end") gave every publication
path the staging-then-publish shape this record asked for: `prepare.py` writes
WAVs and converts a finished bank in one pass, `prepare_drumkit.py` and
`banjo_extract.py` encode every take before any tracked file is replaced, and
both carry negative controls for an injected mid-publication failure
(`test_publish_encode_failure_preserves_both_packages`,
`test_mid_publish_write_failure_rolls_back_every_file`). So the fix this bug
proposed exists — for the banks that still ship.
