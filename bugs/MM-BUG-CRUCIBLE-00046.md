# MM-BUG-CRUCIBLE-00046 — Core and orchestral crates.io READMEs ship panicking get() examples and WAV container claims missed by MM-BUG-CRUCIBLE-00044

- **State:** Open
- **Priority:** Should
- **Severity:** Low
- **Area:** crates/ferrosintesis-samples-core
- **Raised:** 2026-08-18T22:27:49Z
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
- **State history:** Open (2026-08-18T22:27:49Z, raised via `deltic bugs new` model=claude-fable-5)

## Observation

Two published asset-crate READMEs — the crates.io front pages (`readme = "README.md"` in both
manifests) — still document the pre-FLAC WAV contract, including example code that panics as
written. MM-BUG-CRUCIBLE-00044 covers the stale `get()` rustdoc across twelve crates and lists
the crates whose README/PROVENANCE prose says "WAVs", but its enumeration names neither of these
two READMEs, and they are the only two sample-crate READMEs in the workspace that carry runnable
```rust example blocks. Both examples are broken:

- `crates/ferrosintesis-samples-core/README.md:22-23` —
  `get("flute_A4.wav").unwrap()` then `assert_eq!(&wav[..4], b"RIFF")`. The only `.wav`
  spellings `get()` still accepts are the two piano aliases
  (`crates/ferrosintesis-samples-core/src/lib.rs:284-288`); `"flute_A4.wav"` matches nothing,
  so the published example returns `None` and panics — and the RIFF assert would fail anyway
  on FLAC bytes (`fLaC`, per the crate's own test at `src/lib.rs:347`).
- `crates/ferrosintesis-samples-orchestral/README.md:22-25` — same shape:
  `get("trumpet_C3_f.wav").unwrap()` + RIFF assert; orchestral's `lib.rs` has zero `.wav`
  names (only the `missing.wav` negative test at `src/lib.rs:656`), so it also panics.

Supporting stale prose in the same files: core README:4-5 "69 mono, 16-bit, 44.1 kHz WAV attack
transients", :15 "`include_bytes!` places the selected WAV data", :41 "conversion to mono 16-bit
44.1 kHz WAV" (the tool now packages FLAC — `tools/ferrosintesis-samples/prepare.py:1225`
`PACKAGED_EXT = ".flac"`); orchestral README:5, :17, :30, :41, :51, :76, :94 repeat "WAV(s)".
Orchestral README:76 additionally miscounts its own bank independent of the container: "The two
`drone_*` and six `chanter_*` WAVs" vs line 13's correct "2 drones, 15 chanter takes" (disk
holds 15 `chanter_*.flac`).

The banks became FLAC at 0.2.0 (release 0.21.58, 2026-08-17 —
`crates/ferrosintesis/CHANGELOG.md:14-18,37-38`), so these panicking examples are live on the
published crates' front pages (published-state inferred from the changelog; registry not queried
from this session). No current check can catch this: neither crate wires its README into module
docs, so the example blocks are never doctested, and the inventory oracles
(`crates/ferrosintesis/src/inventory.rs`) validate family tables and counts, not container
wording or examples.

Classification: shipped-documentation defect on published crates' public contract, same root
cause as MM-BUG-CRUCIBLE-00044 (FLAC migration doc sweep), distinct surfaces its enumeration
missed — per the repo doctrine, the miss is itself evidence the 00044 list was hand-maintained.

## Fix

Fold into the MM-BUG-CRUCIBLE-00044 sweep, extending its list with these two READMEs:

1. Rewrite both examples against the real API (`get("flute_A4.flac")` / `b"fLaC"`), and make
   the prose container-neutral ("recordings", "sample bytes") or say FLAC explicitly; fix
   orchestral README:76's chanter count (15, not six).
2. Make the examples self-checking so this cannot recur: add
   `#![doc = include_str!("../README.md")]` to both crates' `lib.rs` so the README blocks run
   as doctests (they would have failed the day the names changed), or extend 00044's planned
   container-claim oracle to also flag `get("….wav")` calls inside README code fences.

Effort: ~30 min alongside the 00044 sweep.

## Notes

Found by the 2026-08-18 CRUCIBLE review pass over `crates/ferrosintesis-samples-core/`
(report: `wrk_docs/2026.08.18 - CR - 20260818-REV-MM-CLA@CRUCIBLE-code-review-225905.md`).
Confirmed by an adversarial verifier briefed to refute it; the "logical WAV name" defence in
`prepare.py:1228-1246` covers prose about decoded PCM but cannot defend a panicking example or
the `include_bytes!` claim.
