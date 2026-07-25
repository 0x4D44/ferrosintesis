# MM-BUG-KILN-00112 — Two soft low-piano round robins replay identical onsets

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** core piano sample bank / round robins
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Codex GPT-5.6-Sol from the coverage-ledger review of `crates/ferrosintesis-samples-core/`) → Fixed (2026-07-25, GPT-5.6 Codex on KILN-Windows — the bank now reports quiet C2/G2 as single-take cells, removes their duplicate payloads, and rejects undeclared duplicate round robins)

## Observation

**Symptom.** The core package advertises two upright-piano round robins for
every pitch zone and dynamic, specifically to keep repeated notes from sounding
cloned:

- `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis-samples-core\README.md:7`;
- `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\tools\ferrosintesis-samples\README.md:23-28`;
- `D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\sampler.rs:937-947`.

The quiet C2 and G2 pairs are not two takes. Read-only SHA-256 inspection found
each RR2 payload byte-identical to RR1:

- `piano_C2_pp.wav` and `piano_C2_pp_rr2.wav`:
  `3df14ec899d37728fb9d4a41f9e850d2962d81aaf87c4fdf3aa9934953f242c5`;
- `piano_G2_pp.wav` and `piano_G2_pp_rr2.wav`:
  `b1dcc70f9663b8bd8b4e6a211fae38a9daa94c9cad39df69d891fded2003ae41`.

The generator confirms the cause at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\tools\ferrosintesis-samples\prepare.py:60-63`:
the pinned VSCO source has no pp RR2 for C2/G2, so the bake reuses RR1.

**Expected.** Selecting the alternate round robin gives a distinct recorded
onset, or the bank explicitly reports that these zones have only one take.

**Actual.** GM0 selects the two pp banks by seed parity at
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\voices.rs:12962-12976`,
but both paths replay identical PCM for the C2/G2 zones. The model cannot mask
that clone during the attack: `LaVoice` discards its output until the sample's
180 ms ownership window ends
(`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\sampler.rs:3046-3057`;
`D:\worktrees\midi-music\20260725-REV-CLA@KILN-code-review-212250\crates\ferrosintesis\src\voices.rs:1290-1292`).
The full notes can diverge once their seeded models enter; the confirmed defect
is the machine-gun-sensitive sample-owned onset.

## Fix

Supply genuinely distinct low-pp takes, or deliberately substitute and
recondition suitable captured neighbours after audio calibration. Add a
derived bank oracle that rejects byte-identical or near-clone RR pairs wherever
the public inventory advertises more than one take. If no defensible alternate
exists, represent these two zones as single-take exceptions and narrow the
documentation instead of calling duplicated bytes round robins.

Estimated effort: Medium. Asset selection or regeneration needs the usual
piano calibration and render-diff/listening validation.

## Notes

No synth, render, test, or exploratory harness ran in the review. The duplicate
payloads and the sample-ownership call chain were confirmed by read-only file
and source inspection; audible severity beyond the identical 180 ms onset was
not measured.

## Resolution — 2026-07-25

The pinned VSCO revision has no defensible alternate quiet C2/G2 recordings, so
the bank now takes the expected fallback in this record: it represents those
cells explicitly as single-take exceptions.

- `prepare.py` declares `PIANO_SINGLE_TAKE_CELLS`, generates 52 real piano
  recordings, and no longer manufactures two RR2 files from RR1 sources.
- The core crate embeds 69 physical WAVs instead of 71 and publishes the two
  exceptions. Its old low-level RR2 filename lookups remain compatibility
  aliases to the single takes.
- The runtime RR2 bank names the C2/G2 base samples directly. All other piano
  cells retain distinct second takes.
- Package, generator, and provenance documentation now report 25 two-take
  cells plus the two quiet single-take exceptions.

## Verification — 2026-07-25

- A committed-bank oracle proves every advertised RR pair is SHA-256-distinct,
  the exception set is exactly quiet C2/G2, and no fake RR2 files exist.
- A runtime-bank oracle proves only the two declared cells alias between the
  primary and alternate banks; every other zone differs.
- All 33 generator tests and both core-package parity tests pass.
- `$null | cargo test --locked -p ferrosintesis`: **717 unit tests and 4 doc
  tests passed; 27 diagnostics ignored**.
- `$null | cargo test --locked -p ferrosintesis --no-default-features`: **616
  unit tests and 4 doc tests passed; 22 diagnostics ignored**.
- Strict all-target clippy passes with all features and with no default
  features. Formatting and `git diff --check` pass.
- Fresh release binaries from exact baseline `2b25655`, full 124-MIDI inventory
  at 11.025 kHz: **124 byte-identical, 0 contamination**. The explicit aliases
  preserve the shipped audio while making the inventory truthful.
