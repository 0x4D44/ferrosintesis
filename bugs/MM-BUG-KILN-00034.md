# MM-BUG-KILN-00034 — NRPN select (CC98/99) does not invalidate the RPN latch, so a later Data-Entry corrupts the RPN-set value (e.g. pitch-bend range → 24 semitones)

- **State:** Fixed
- **Priority:** Should
- **Severity:** High
- **Area:** engine
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the cross-agent MIDI/GM support audit — severity re-framed from "harmless absence" to active corruption by Fable 5) → Fixed (2026-07-21, `663752a`)

## Observation

The CC dispatch `fn cc` (`crates/ferrosintesis/src/engine.rs`) sets the RPN latch only on
CC100/CC101 (engine.rs:2284-2285); there is **no CC98/CC99 (NRPN LSB/MSB) arm** — both fall
through `_ => {}` (engine.rs:2289). Data-Entry CC6/CC38 (engine.rs:2162-2187) is applied to
whatever `(rpn_msb, rpn_lsb)` currently holds. Because an NRPN select never touches that
latch, this sequence corrupts an RPN-set parameter:

1. File sets RPN 0,0 pitch-bend range (near-universal in GM/GS files) → latch = (0,0).
2. File does **not** send RPN-Null (127,127) afterwards (many GS/XG files don't).
3. File selects an NRPN (CC99/CC98 — common in GS content for vibrato rate, TVF cutoff,
   drum params) then sends Data-Entry CC6 = v.

Step 3's CC6 writes `bend_range = v.clamp(1,24)` against the **stale** RPN 0,0 latch. A GS
vibrato-rate NRPN with CC6 = 80 sets the bend range to 24 semitones, so every subsequent
pitch bend renders ~12× too wide — a loud, obvious pitch error. Only files that dutifully
send RPN-Null after using an RPN are safe. No in-repo album authors NRPN (unaffected); the
corruption is real and audible on foreign GS/XG files.

Repro (unit): CC101=0, CC100=0, CC6=2 (bend range 2) → NRPN select CC99=1, CC98=8 → CC6=80;
assert the channel bend range is still 2, not 24.

## Fix

Fix (`663752a`): add a `98 | 99 => { s.rpn_msb = 127; s.rpn_lsb = 127; }` arm to the CC
dispatch (`engine.rs`, beside the CC100/101 RPN-select arms). An NRPN select now parks the RPN
latch at null — the same inert state as an RPN-Null — so a following Data-Entry (CC6/38) matches
neither `(0,0)` nor `(0,1)` in the data-entry handler (`engine.rs:2171`) and is dropped. This is
the defensive guard only (correct MIDI semantics: an NRPN select must not leave a following
Data-Entry writing into the previously-selected RPN); it is NOT NRPN parameter support (out of
scope — large surface, no demonstrated demand).

Verification:
- Regression `engine::tests::nrpn_select_does_not_corrupt_the_rpn_bend_range` — observed RED
  without the arm (bend range corrupted to 24 after RPN 0,0 → NRPN select → CC6=80) → GREEN with
  it (bend range stays 2). Fails-before/passes-after both confirmed by reverting and re-applying
  the arm.
- Full `cargo test -p ferrosintesis --lib` suite 600/600 (0 failed); `cargo clippy -p
  ferrosintesis --all-targets -- -D warnings` clean; `cargo fmt --check` clean.
- Pure controller guard: no in-repo composition engine emits CC98/99 (census of `albums/**/*.py`
  clean), so album renders are unchanged by construction — the render-diff is zero and was not run
  for that reason.

Awaiting independent two-eyes verification before Closed (the fixer must not close their own bug).

## Notes

- My own first-pass audit spotted this mechanism but wrongly filed it "inert" because no
  in-repo album authors NRPN; the Fable 5 review correctly re-scoped it to the foreign-file
  fidelity question, where it is the single worst controller hazard found.
- gpt-5.6-sol-xhigh agreed CC98/99 fall through but deprioritised *broad* NRPN work — which
  is a different scope from this cheap latch guard; both positions are compatible.
