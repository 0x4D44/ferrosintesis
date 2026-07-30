# MM-BUG-KILN-00178 — GM67 key 58 'fartiness' from Arthur's audition is still undiagnosed: the other half of MM-BUG-KILN-00176's observation

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
- **Area:** audio / sampled sax sustain
- **Raised:** 2026-07-29
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
- **State history:** Open (2026-07-29, raised via `deltic bugs new` model=claude-opus-5@high) -> Fixed (2026-07-30, deltic:auto role=fix run=fix-20260729T232125Z-p54804-n080502500-c1 branch=task/bug-MM-BUG-KILN-00178-run-fix-20260729T232125Z-p54804-n080502500-c1 code=190b8c66e4d754ef6ddf3c299e652a7e4d8370fc gate=manual) -> Closed (2026-07-30, independently verified by claude-opus-5@high on trunk 73ec2f2; fix authored by GPT-5.6, so two-eyes holds; oracle-design residual split to MM-BUG-KILN-00180)

## Observation

Residual split from MM-BUG-KILN-00176 during its independent two-eyes closure.
Carried forward so the report is not lost when that bug closes.

Arthur's original report named TWO distinct artifacts on the GM67 channel, verbatim:

> What I did notice is that there are some artifacts on the GM67 channel - a
> combo of "fartiness" on some notes and a noticeable looping on some high
> notes.

His direct left/right comparison localized the **fartiness to notes 5 and 6, MIDI
key 58 at velocities 72 and 110**, and the sustain oscillation to keys 68 and 73.
Ferrosintesis was the left channel in both comparisons; channel extraction was
hash-verified against the source renders.

MM-BUG-KILN-00176 resolved and verified only the **looping** half. Its own Observation
says of this one: "Arthur has localized the separate 'fartiness' description to key 58,
but the current probe has not yet objectively defined or diagnosed it."

The landed fix (0798a78) cannot have affected key 58. Its multi-slice grain motion is
gated on `program == 67 && key >= 68` at `crates/ferrosintesis/src/sampler.rs`
`sax_loop_voice`, so key 58 takes `grain_motion == false`. This was confirmed two
independent ways during closure: by tracing every new mutation (all guarded by
`if self.grain_motion`, `grain_gain` stays 1.0, and `choose_next_grain` - the only new
`rng.white()` consumer - is never reached so the RNG stream is untouched), and
empirically by render-diff, where the one demo authoring GM67 below the gate
(`demos/ferrosintesis_reference/midi/03 - Reed, Pipe, Lead, Pad.mid`, GM67 keys
49/53/56) rendered bit-identically.

Reproduction, per the original:

1. Render default-bank GM67 with samples enabled, sends disabled, and the M-CAL
   sustained sequence: MIDI keys 48, 53, 58, 63, 68 and 73, each at velocities 72
   and 110.
2. Hold each note for 1.3 seconds. Listen to key 58 at both velocities.
3. Compare against the SC-55 and S-YXG50 reference renders.

**Expected.** A held baritone-sax note at key 58 does not read as "farty" against
the reference modules.

**Actual.** Arthur hears it; no objective metric has yet been defined for it, so
there is no numeric evidence in this record and no regression is possible yet.

**First work item is therefore diagnostic, not corrective:** define a measurement
that separates this from the loop-exposure artifact (which at key 58 measures
differently from the reported high notes) before proposing a fix. Note the ledger
precedent at `bugs/MM-BUG-KILN-00038.md`, where an Arthur audition described an
aftertouch passage as "farty" - check whether the mechanism is shared before
treating this as new.

Searched during closure: no other bug or requirement covers this.
`reqs/MM-REQ-KILN-00176.md` is an unrelated accent-drum-bank Draft that merely
shares the number.

## Fix

`190b8c66` (GPT-5.6) at `crates/ferrosintesis/src/sampler.rs`:

- Dropped `"sax_bar_G#3_p.wav" => 208.95` from `sax_bar_p()` and
  `"sax_bar_G#3_f.wav" => 209.52` from `sax_bar_f()`, so key 58 no longer selects
  them. Both WAVs stay packaged for provenance.
- Added `baritone_sax_key58_avoids_a_rough_source_zone`, which defines the missing
  metric the Observation asked for: best adjacent-pitch-cycle correlation inside
  the unlooped source body (0.30–0.50 s), swept ±5 samples around the period.
  Deliberately distinct from the sustain-loop oracle — it measures 4–5 ms cycles
  in the *source*, not a 50–130 ms envelope repeat in the *render*.

## Notes

**Independent verification, 2026-07-30, claude-opus-5@high on trunk 73ec2f2**
(worktree `D:\worktrees\midi-music\20260730-TSK-HUM-verify-close-sax-bugs`).
Fix authored by GPT-5.6 — a different actor, so two-eyes holds.

**The diagnostic first work item this bug asked for is done, and the answer is
decisive.** Restoring the two G#3 zones and applying the new metric to every zone
in both baritone banks: `sax_bar_G#3_f.wav` measures **0.77865** adjacent-cycle
correlation. Every other zone in either bank spans 0.99296–0.99967. That take is
genuinely broken up cycle-to-cycle — an objective correlate for Arthur's
"fartiness", localized to exactly the key he named.

**The original observation is addressed at the reported key.** Key 58 (f0 233.08
Hz) selected root 208.95 Hz at velocity 72 and 209.52 Hz at velocity 110 — the
rough take at both. With the zones removed it selects 263.75 Hz (0.99753) and
261.13 Hz (0.99821). The reported velocities 72 and 110 are both covered by the
new test.

**Regression genuinely fails before / passes after.** Restoring only the two zone
lines fails the test: "GM67 key 58 velocity 72: selected 208.95 Hz source has only
0.9948 adjacent-cycle correlation". Removed again, it passes.

**Sequencing note (not a defect).** This bug's Observation reasoned that the
MM-BUG-KILN-00176 fix "cannot have affected key 58" because grain motion was gated
on `key >= 68`. MM-BUG-KILN-00177's fix landed first and removed that key gate, so
key 58 now *does* render with grain motion. Verified directly by buffer
comparison. That does not disturb this diagnosis — the roughness is in the source
recording, upstream of any loop-reading strategy — but the Observation's reasoning
is stale as written.

**Residual, split to MM-BUG-KILN-00180.** The new test's 0.996 bar is fitted, not
derived: five *healthy* shipping zones already sit below it (bar_p 82.52 / 103.47
/ 130.04, bar_f 82.38 / 130.22), while the real defect was 0.779. The test passes
only because it checks one key that happens to land above the bar. Also recorded
there: removing both G#3 zones opens an 8.3-semitone gap (163.27 → 263.75 Hz) that
nothing guards. Neither is what this bug was raised for, and neither is a shipped
audio defect, so this ID closes and the residual stays tracked.

**Gates green on the exact tree:** `cargo test --workspace --release` 842 passed
/ 0 failed in `ferrosintesis` plus every sample crate green;
`cargo clippy --workspace --all-targets -- -D warnings` clean;
`cargo fmt --all -- --check` clean.

Verification probes were temporary and are not committed; the tree was restored
to 73ec2f2 and confirmed clean before the gate run.
