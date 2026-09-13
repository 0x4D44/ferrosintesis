# MM-BUG-CRUCIBLE-00027 — offline::load reads unbounded MIDI files before parser limits apply

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** ferrosintesis / MIDI loading
- **Raised:** 2026-08-14T11:47:21Z
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
- **State history:** Open (2026-08-14T11:47:21Z, raised via `deltic bugs new` model=gpt-5.6-sol@xhigh) -> Fixed (2026-08-15T07:27:34Z, deltic:auto role=fix run=fix-20260815T071503Z-p19272-n598691600-c1 branch=task/bug-MM-BUG-CRUCIBLE-00027-run-fix-20260815T071503Z-p19272-n598691600-c1 code=ccf2cdf gate=manual) -> Closed (2026-09-13T19:21:20Z, independent verify by Claude Opus 5 on trunk 8b6a6f86: 5 GiB file refused instantly as TooLarge; oversized-file test fails with plain fs::read restored)

## Observation

The parser treats MIDI bytes as attacker-controlled and caps decoded duration to prevent an
allocator abort. The path-based entry point bypasses that protection until after it has
allocated for the whole input: `offline::load` calls `std::fs::read` at
`D:\worktrees\ferrosintesis\20260814-REV-MM-CDX@CRUCIBLE-code-review-121801\crates\ferrosintesis\src\midi.rs:210`,
then calls `parse`.

A multi-gigabyte regular or sparse file is therefore materialized before the header,
track lengths, or `MAX_SONG_SECONDS` are checked. SMF track lengths are `u32`, so a file
can also present an almost-4-GiB declared track while remaining structurally plausible.
The duration guard at `midi.rs:433-439` limits render length, not input bytes or event
allocation.

Expected: the convenience loader applies a resource bound before reading untrusted input.
Actual: opening one hostile file can exhaust process memory before `MidiError` is returned.
This is a resource-exhaustion defect on the crate's documented untrusted-input surface.

## Fix

Preflight `metadata.len()` against a documented maximum and return a dedicated
`MidiError`, or parse through a bounded/streaming reader so memory does not scale with the
entire file. Cover both a sparse oversized file and a declared near-4-GiB track with tests
that reject before allocation. Estimated effort: Small with an explicit cap; Medium/Large
for streaming.

### Verification summary (2026-09-13, Claude Opus 5, independent)

Verified on trunk `8b6a6f86` (fix `ccf2cdf8`) by an agent other than the fixer.

**Original observation re-run.** A 5 GiB file through the CLI fails immediately with "MIDI file is 5368709120 bytes, which exceeds the 67108864 byte limit"; a track declaring 0xFFFFFF00 bytes fails with `UnexpectedEof` without allocating.

**Fails-before (method B).** Replacing `read_bounded` with `std::fs::read` makes `load_rejects_an_oversized_file` fail ("`load` has no size limit"). The boundary and declared-4-GiB tests stay green, as the fix commit says that case already held. Restored; `git diff` empty; three regressions pass on HEAD.

**Gates.** This fix causes no gate failure; trunk `8b6a6f86` is red for unrelated recorded reasons.


## Notes
