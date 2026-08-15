# MM-BUG-NMI-00001 — Ten packaged WAVs across four banks still open on a frame-zero PCM step

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample assets / onset de-click coverage
- **Raised:** 2026-08-15T03:38:52Z
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
- **State history:** Open (2026-08-15T03:38:52Z, raised via `deltic bugs new`) -> Blocked (2026-08-15, six of the ten fixed in 3d186d0; the remaining five are all `-core` piano and cannot be regenerated until MM-BUG-NMI-00002 is fixed — `prepare.py --only=piano` rewrites all 48 files in the family rather than reproducing the committed bank. Blocked on that bug, not on a decision.) -> Open (2026-08-15T16:25:34Z, deltic:manual host=NMI verdict=reopen) -> Fixed (2026-08-15T16:27:44Z, deltic:auto role=fix run=fix-20260815T162554Z-p14984-n995209800-c1 branch=task/bug-MM-BUG-NMI-00001-run-fix-20260815T162554Z-p14984-n995209800-c1 code=e4272da gate=manual) -> Closed (2026-08-15T22:50:00Z, independent verify: extracted piano_C3_pp/_rr2/G3_pp/G4_pp/G5_f.wav at e4272da^ and e4272da via `git show`, re-ran the census predicate from this bug's own Correction section directly on the PCM — all 5 DISCONTINUOUS before, all 5 `ok` (first=0.0) after; also confirmed the other 5 (b1_normal_C1/C3, eastpick_E2, eastpluck_E2, pizzbass_E1) are `ok` at HEAD. Ran `python -m unittest discover -s tools/ferrosintesis-samples`: 155 tests, only the 2 pre-existing environment failures (b1_sustain_pilot vs. $env:TEMP inside a git tree) matching the fixer's own report — now separately tracked as MM-BUG-NMI-00004.)

## Correction (2026-08-15, while fixing)

**The count in the original observation below is wrong: 10, not 15.** The census
predicate treated every packaged WAV as a one-shot, and five of the fifteen are not.
`chanter_A#4`, `chanter_A#4_rr2`, `chanter_A4`, `chanter_D5_rr2` and `drone_G3` are
**seamless loops** produced by `extract_loop`, whose returned window deliberately
begins mid-waveform; the discontinuity that matters for a loop is the WRAP, and
`find_loop` already optimises it. Measured on those five, the wrap step (0.008-0.046)
sits far BELOW their own ordinary first-window motion (0.048-0.186) — they are
correctly formed. De-clicking their starts would have destroyed the seam that search
bought, converting one click at note-on into one per repetition.

This is the failure CLAUDE.md warns about directly: a derived oracle is only as good
as its enumeration predicate, and the predicate is itself an assumption. The corrected
predicate decides from the DATA which kind of sample it is looking at — a file that
ends at silence is a one-shot and is judged on its start; one that ends mid-waveform
is a loop and is judged on its seam.

Under the corrected predicate, a sweep of all 1,089 packaged WAVs finds 1,068
one-shots and 21 loops, with **zero** failing loop seams.

**Status: 6 of the 10 fixed; 5 remain** (b1_normal_C1/C3, eastpick_E2, eastpluck_E2,
pizzbass_E1 regenerated, plus the sub-threshold eastpick_E3). The remaining five are
all `-core` piano and are **blocked on MM-BUG-NMI-00002**: `prepare.py --only=piano`
no longer reproduces the committed bank, rewriting 48 WAVs — including files that
already start at zero — so regenerating them would replace the flagship piano's sound
under an onset fix. They are pinned in `KNOWN_DISCONTINUOUS_ONSETS` in
`tools/ferrosintesis-samples/test_prepare.py`, which asserts they are still failing
so the entry cannot outlive the defect.

## Observation

The zero-lead de-click was fixed twice, one bank at a time, and the rest of the
catalogue was never re-measured. MM-BUG-CRUCIBLE-00021 (2026-08-01) added the
zero-lead micro-fade branch to `trim_to_onset` and regenerated only
`ferrosintesis-samples-bass`; MM-BUG-CRUCIBLE-00024 (2026-08-15) ported it to
`trim_lead_and_ring` and regenerated only `ferrosintesis-samples-gong`. **15
committed WAVs across five other packaged banks still open on a frame-zero PCM
step** — they were baked before the fix and never rebuilt.

Census on trunk `1b0102a`, run from `tools/ferrosintesis-samples/`. A file is
listed when its first sample exceeds the largest adjacent step in its own first
10 ms (the same predicate as the existing
`test_committed_bass_bank_starts_with_continuous_pcm` and
`test_committed_gong_bank_starts_with_continuous_pcm` oracles):

| Crate | File | First PCM | Ratio to ordinary step |
|---|---|---:|---:|
| `-b1-upright` | `b1_normal_C1.wav` | 933 | 28.3x |
| `-b1-upright` | `b1_normal_C3.wav` | 1485 | 13.3x |
| `-core` | `piano_C3_pp.wav` | 338 | 2.5x |
| `-core` | `piano_C3_pp_rr2.wav` | -269 | 2.2x |
| `-core` | `piano_G3_pp.wav` | 485 | 5.0x |
| `-core` | `piano_G4_pp.wav` | 452 | 1.2x |
| `-core` | `piano_G5_f.wav` | -352 | 1.8x |
| `-orchestral` | `chanter_A#4.wav` | -7979 | 1.3x |
| `-orchestral` | `chanter_A#4_rr2.wav` | -8944 | 1.2x |
| `-orchestral` | `chanter_A4.wav` | -12083 | 2.1x |
| `-orchestral` | `chanter_D5_rr2.wav` | -6073 | 1.3x |
| `-orchestral` | `drone_G3.wav` | 4628 | 3.0x |
| `-orchestral2` | `eastpick_E2.wav` | -5427 | 1.8x |
| `-orchestral2` | `eastpluck_E2.wav` | 5903 | 12.1x |
| `-strings` | `pizzbass_E1.wav` | -2188 | 8.0x |

Reproduction (read-only, no network):

```powershell
cd tools/ferrosintesis-samples
python -c "import prepare,os; root=prepare.REPO_ROOT; [print(c,n,round(x[0]*32768)) for c in sorted(os.listdir(os.path.join(root,'crates'))) if os.path.isdir(os.path.join(root,'crates',c,'samples')) for n in sorted(os.listdir(os.path.join(root,'crates',c,'samples'))) if n.endswith('.wav') for x,sr in [prepare.read_wav(os.path.join(root,'crates',c,'samples',n))] if len(x)>900 and abs(x[0])>max(abs(x[i]-x[i-1]) for i in range(1,min(len(x),int(0.010*sr))))]"
```

Expected: every packaged bank starts on a slope-bounded transition, as the two
already-pinned banks do.

## Fix

<unfixed — raised only>

## Notes

- This is the repo's documented "hand-maintained list drifted" pattern
  (`CLAUDE.md`, *Hand-maintained lists are the recurring defect here*): the
  reported item each time was the newest bank, never the whole set. Two oracles
  now exist, one per already-fixed bank
  (`test_committed_bass_bank_starts_with_continuous_pcm`,
  `test_committed_gong_bank_starts_with_continuous_pcm`), and a third
  hand-written copy per bank is the wrong answer.
- **The oracle should be derived, not enumerated**: scan every
  `crates/ferrosintesis-samples-*/samples/*.wav` and assert the predicate, so a
  new bank cannot land outside the sweep. Then delete the two per-bank copies.
- Not all 15 come from `trim_to_onset`. The chanter/drone files are baked by
  `_bake_bagpipe` and `eastpick`/`eastpluck` by their own recipe, so the fix is
  likely "route every bake through the shared `declick_fade_in`", not "rerun
  `prepare.py`". Confirm per family before regenerating.
- Regeneration cost differs per bank: `-core`, `-orchestral`, `-orchestral2`
  and `-strings` are fetched-source banks (network), `-b1-upright` is an
  owner-recording bake. Byte counts may move, so `EXPECTED_BYTES`, the inventory
  parity tests and each `PROVENANCE.md` inventory table need refreshing with them.
- Audibility is unmeasured: a step at 1.2x ordinary motion is unlikely to be
  heard, one at 28x on a piano `pp` attack plausibly is. Sizing the work should
  start with the worst three (`b1_normal_C1`, `b1_normal_C3`, `eastpluck_E2`).
- Estimated effort: Medium — the derived oracle is small, the per-family
  regeneration and pin refresh is the bulk.

### Reopen note (2026-08-15T16:25:34Z, deltic:manual host=NMI verdict=reopen)

Reopen reason: The blocker (MM-BUG-NMI-00002) is resolved: the core piano bank was stale, not irreproducible, and regenerating it fixes the remaining five onsets.
