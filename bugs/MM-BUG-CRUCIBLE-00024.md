# MM-BUG-CRUCIBLE-00024 — Soft gong starts with an unfaded NoteOn step

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample assets / gong onset conditioning
- **Raised:** 2026-08-12T08:47:34Z
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
- **State history:** Open (2026-08-12T08:47:34Z, raised via `deltic bugs new`) -> Fixed (2026-08-15T03:37:28Z, deltic:auto role=fix run=fix-20260815T032051Z-p42576-n588484800-c1 branch=task/bug-MM-BUG-CRUCIBLE-00024-run-fix-20260815T032051Z-p42576-n588484800-c1 code=1c2fc723be08c9ab74671e39489c3f7ed64bf19c gate=manual)

## Observation

The packaged soft gong begins at PCM -2769 (8.45% full scale) instead of
silence. Its initial jump is 12.7 times the 95th-percentile adjacent step in
the first 2 ms. The generator's `trim_lead_and_ring` computes a zero-length
fade when the detected onset is frame zero, while `GongOneShot` emits sample
zero directly. Every soft-layer strike therefore begins with a discontinuity.

Static reproduction on the 2026-08-12 review baseline
`cc3f3b4fdbe9c916566b734c6864fe6c7bc999a1`:

1. Read signed little-endian PCM16 from
   `crates/ferrosintesis-samples-gong/samples/gong_ageng_soft.wav`.
2. Observe the first sample `-2769`; the file peak is `29490`.
3. Compute absolute adjacent steps over the following 88 frames. Their 95th
   percentile is `218`, so the silence-to-first-frame step is `12.7x` that
   local motion.

Expected: the committed soft layer starts with a slope-bounded de-click
transition while preserving its attack, matching the processing contract in
`PROVENANCE.md`.

## Fix

<unfixed — raised only>

## Notes

- Root cause: `tools/ferrosintesis-samples/prepare.py:4173-4177` sets
  `fin = min(int(0.002 * sr), lead)`. For this source `onset == start == 0`,
  so `fin == 0` and the loop applies no fade.
- Shipped path: `crates/ferrosintesis/src/sampler.rs:5297-5316` reads and adds
  the first PCM value without a note-on envelope.
- The same generator already contains the correct zero-lead treatment in
  `trim_to_onset` at `tools/ferrosintesis-samples/prepare.py:2111-2130`.
- Fix direction: share or port that slope-bounded zero-lead micro-fade into
  `trim_lead_and_ring`, regenerate the two gong outputs, refresh derived pins,
  and add an adversarial regression for a nonzero frame-zero source. The oracle
  must bound the silence-to-first-frame step against ordinary first-window
  motion without imposing a fixed fade that crushes tight attacks.
- Estimated effort: Small.
