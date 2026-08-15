# MM-BUG-NMI-00002 — the core piano bank was stale: a whole-bank conditioner re-levels all 48 takes after any onset change

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample tooling / core piano bake reproducibility
- **Raised:** 2026-08-15T11:56:51Z
- **Discovery source:** Agent
- **Owner:** deltic:manual
- **Owner role:** fix
- **Owner run:** fix-20260815T161214Z-p18772-n712089000-c1
- **Owner host:** NMI
- **Owner branch:** task/bug-MM-BUG-NMI-00002-run-fix-20260815T161214Z-p18772-n712089000-c1
- **Owner base:** 65cb7f7eca21dcce40f37645c2dc4224bc62c12f
- **Owner fingerprint:** -
- **Owner since:** 2026-08-15T16:12:14Z
- **Owner until:** 2026-08-15T18:12:14Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-08-15T11:56:51Z, raised via `deltic bugs new`)

## Correction (2026-08-15, while fixing)

**The title and diagnosis below are wrong. The bake is deterministic and does
reproduce the committed bank — under the code that produced it.** I raised this from
a single observation (48 files rewritten) and inferred non-determinism without
testing for it.

Measured on 2026-08-15:

- Running `--only=piano` twice gives byte-identical output both times. The bake is
  deterministic.
- Disabling the zero-lead de-click branch in `declick_fade_in` and re-baking
  reproduces the committed bank **exactly — 0 of 48 files differ**.

So the 48-file delta has a single cause, and it is not a defect in the bake.
`condition_piano_bank` fits a minimax line across the WHOLE 52-take bank and derives
every take's correction from it. MM-BUG-CRUCIBLE-00021 (2026-08-01) changed 5 takes'
onsets, which moved their `piano_envelope_stats`, which moved the fit, which changed
the correction for all 48. The bank was simply never regenerated after that fix — it
was stale, not irreproducible.

The regeneration is safe, measured rather than assumed: the level change is at most
0.062 dB and averages -0.003 dB, and the largest changes land on exactly the five
defective takes. Rendering a GM 0 CC0=1 probe across all three dynamic layers gives
a maximum sample delta of -47.7 dBFS and an overall RMS change of +0.0002 dB — the
onset clicks removed and nothing else audible.

**Resolution: the bank is regenerated.** That also unblocks the remaining half of
MM-BUG-NMI-00001.

## Observation

`python tools/ferrosintesis-samples/prepare.py --only=piano` does not reproduce the
committed `ferrosintesis-samples-core` piano bank. On trunk it rewrites **48 of the
48** packaged `piano_*.wav` files, and the differences are not confined to the 5 that
have a known onset defect (MM-BUG-NMI-00001).

Measured on 2026-08-15 from a clean worktree at `fe1fb49`, comparing the regenerated
files against `HEAD`:

| File | Length | Differing samples | Start before | Start after |
|---|---:|---:|---:|---:|
| `piano_C2_f.wav` | 79732 | 6440 (idx 223..78635) | 0.00000 | 0.00000 |
| `piano_C4_mf.wav` | 79732 | 4429 (idx 177..74835) | 0.00000 | 0.00000 |
| `piano_G5_pp.wav` | 79732 | 7135 (idx 4..76155) | 0.00000 | 0.00000 |
| `piano_C3_pp.wav` | 79732 | 59667 (idx 0..78172) | 0.01031 | 0.00000 |

The first three already started at exactly zero, so the de-click branch cannot be
what moved them: thousands of samples changed scattered through the body of each
file. Lengths are unchanged, so this is drift in the sample VALUES, not a
re-segmentation.

Expected: a bake is deterministic, so re-running it on unchanged sources reproduces
the committed bytes, and a fix that should touch 5 files touches 5 files.
Actual: it rewrites the whole family, which makes it impossible to land a targeted
onset fix without also replacing the flagship piano's sound.

Contrast: the same command shape IS reproducible for other families. `--only=b1upright`
changed exactly the 2 files with the defect; `--only=pizzbass` exactly 1;
`--only=eastpick,eastpluck` exactly 3. So this is specific to the piano path, not to
`prepare.py` in general.

## Fix

<unfixed — raised only>

## Notes

- Blocks the remaining half of MM-BUG-NMI-00001. Those 5 files are pinned in
  `KNOWN_DISCONTINUOUS_ONSETS` in `tools/ferrosintesis-samples/test_prepare.py`, whose
  sweep asserts they are STILL failing — so when this is fixed and they are
  regenerated, that assertion goes red and forces the pin out.
- First thing to establish is which input differs: the fetched archive (a changed
  upstream download, or a cache built by a different code version), the decode path,
  or the resampler. The archive cache is the prime suspect — MM-BUG-KILN-00181 and
  MM-BUG-KILN-00182 are both open against archive-cache and stale-output handling in
  the same tool.
- A useful oracle once diagnosed: bake twice into scratch dirs and require the two
  runs byte-identical, then require a run against the committed bank to be a no-op.
  The second is the property that actually failed here and nothing checks it.
- Estimated effort: Medium — the diagnosis is the work; the repair may be small.


