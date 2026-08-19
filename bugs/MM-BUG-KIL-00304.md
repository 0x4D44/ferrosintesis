# MM-BUG-KIL-00304 — Drum-kit PROVENANCE files still describe pre-FLAC WAV payloads and byte totals

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** sample assets / provenance documentation
- **Raised:** 2026-08-19T09:33:14Z
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
- **State history:** Open (2026-08-19T09:33:14Z, raised via `deltic bugs new`)

## Observation

Both drum-kit crates' provenance records still describe the pre-FLAC payload. The
committed assets became FLAC on 2026-08-16; the PROVENANCE prose was not updated.

`crates/ferrosintesis-samples-drumkit2/PROVENANCE.md`:
- Line 11-12: "36 mono 16-bit 44.1 kHz WAVs (7,647,408 raw bytes)". The crate ships
  36 `.flac` totalling 4,301,372 bytes — the crate's own pin
  (`crates/ferrosintesis-samples-drumkit2/src/lib.rs:419`,
  `EXPECTED_BYTES: usize = 4301372`). 7,647,408 is the pre-migration WAV total.
- Line 13: "The WAVs under `samples/`…".
- Lines 80-82: "File naming: `<articulation>_vl{L}_rr{R}.wav` … e.g.
  `crash_vl2_rr3.wav`". The tree holds `crash_vl2_rr3.flac`;
  `Bank::file_name` formats `.flac`
  (`crates/ferrosintesis-samples-drumkit/src/lib.rs:708`), so the doc's own example
  name resolves to `None` through `get()`.
- Line 103: "Output: 16-bit mono WAV" — the published bank is FLAC
  (`tools/ferrosintesis-samples/prepare_drumkit.py:358-386` encodes at the crate
  boundary, bit-exact).

`crates/ferrosintesis-samples-drumkit/PROVENANCE.md` has the same drift: line 18-19
"128 mono 16-bit 44.1 kHz WAVs (9,632,990 raw bytes)" vs 128 `.flac` at 5,428,756
bytes (`crates/ferrosintesis-samples-drumkit/src/lib.rs:963`), and line 107
"Output: 16-bit mono WAV". `prepare_drumkit.py`'s module docstring carries the same
stale wording.

Provenance files are the licence/source evidence for shipped recordings, and the
byte figure is material context for the crates.io 10 MiB split this crate exists
for — a reader re-deriving the split from these numbers works from figures 78% high.

Deliberately NOT covered by open MM-BUG-CRUCIBLE-00044: that bug's enumerated fix
list covers the `get()` rustdoc lines (drumkit2 `src/lib.rs:215-217` among 12
crates) and README/PROVENANCE "N WAVs" prose in ten *other* crates; neither
drum-kit PROVENANCE file, nor any byte figure, is in its enumeration. Fixing 00044
by its list leaves everything above stale.

## Fix

Restate the payload as FLAC with the packaged byte totals (4,301,372 / 5,428,756),
fix the `.wav` naming examples to `.flac`, and reword "Output: 16-bit mono WAV" to
"16-bit mono PCM, published as FLAC (bit-exact)". Fix `prepare_drumkit.py`'s
docstring in the same pass. Prefer stating the byte figures as "see
`EXPECTED_BYTES` in `src/lib.rs`" so the document cannot disagree with the derived
oracle again; 00044's proposed container-word oracle would then cover the rest of
this class.

## Notes

Raised by the 2026-08-19 static review of `crates/ferrosintesis-samples-drumkit2/`
(worktree 20260819-REV-MM-CLA@KILN-code-review-101941). Confirmed by two
independent reviewers plus lead re-read. Estimated effort: Small.
