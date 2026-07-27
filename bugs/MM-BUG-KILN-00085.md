# MM-BUG-KILN-00085 — the LA bass crossfade SHAPE still costs the onset: a 50 ms model mute erases the kick thump and a 350 ms handover outlasts 90% of a bass line's notes

- **State:** Fixed
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-24
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
- **State history:** Open (2026-07-24 — split from MM-BUG-KILN-00075 on its Open → Fixed transition by Claude Opus 4.8 (1M), which landed that bug's gain items 1–2 and could not land items 3–4) → Blocked (2026-07-25, Codex GPT-5.6-Sol; the remaining fade shape, handover duration, and bass-onset repitch limit are audible product decisions Arthur must make, while extending the bank needs owner-recorded or approved licensed source material) → Open (2026-07-26, unblocked by Arthur; approved a bass-specific additive onset ending at approximately 150 ms, a five-semitone upward-repitch ceiling with model fallback, and retention as an alternate bank pending a later A/B) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260726T230602Z-p9812-n782377700-c18 branch=task/bug-MM-BUG-KILN-00085-run-fix-20260726T230602Z-p9812-n782377700-c18 code=a0bdbdc7335105591dc6dc4228b8baa1bb61d30a gate=focused+render-diff model=codex@xhigh)

## Observation

**Symptom.** Even with the GM 32–35 seam now level-matched (MM-BUG-KILN-00075), the LA bass
layer is still not fit to return to the default bank. Three things remain, and none is a
gain:

1. **The 50 ms model mute erases the `kick` thump.** `LaVoice`'s crossfade is sum-to-one:
   the model is muted outright until `fade.0` = 50 ms. The `BASS` preset's `kick` is a
   one-shot `Burst` with `KICK_T60_S` = 75 ms, so it fires almost entirely inside the muted
   window and never reaches the output. Level-matching the sample cannot restore it — the
   sample is a different recording and does not contain that thump.
2. **The 350 ms handover outlasts the music.** `fade.1` = 350 ms, but the bass part
   MM-BUG-KILN-00075 was raised from has a **146 ms median note** and **90% of notes shorter
   than the handover**, so the model is never sole owner. `LA_BANJO` already uses a 0.20 s
   tail, so a shorter bass handover has precedent in the codebase.
3. **GM32's onset stays ~3.7 dB under parity, and cannot be fixed by a gain.** The real
   pizzicato contrabass recording rings on while `Pluck(&UPRIGHT)`'s short `t60` has already
   decayed, so a taper that reaches onset parity overshoots `[50, 350] ms` by +6 to +10 dB.
   KILN-00075 therefore fitted GM32 on the whole handover instead, deliberately leaving the
   onset under. One scalar cannot fix both ends of a decay-**shape** mismatch.

**Also unresolved from KILN-00075's suggested fix (its item 4).** `finger_bass` covers
E1–D2 and `pick_bass` E1–E2, but 68% of that part's bass notes play above the top zone, so
notes are repitched up to +12 semitones — not a credible repitch for a bass onset. Either
the banks want upward extension, or the basses want a tighter repitch guard than the shared
`0.5..=2.05`.

## Measured context

From KILN-00075's calibration harness
(`sampler::tests::print_ebass_wrap_level_ratios`), post-taper, 187 engaged points:

| window | geomean | range |
|---|---|---|
| `[0, 50 ms]` | 0.866 (−1.2 dB) | 0.433 … 1.217 |
| `[50, 150]` | 1.025 (+0.2 dB) | 0.612 … 1.580 |
| `[150, 350]` | 0.900 (−0.9 dB) | 0.684 … 1.700 |

The remaining per-point spread — still ±4 dB at the edges — is the shape mismatch, not a
gain error. A gain moves the whole curve; it cannot change its slope.

## Fix

Needs **Arthur's ear**, which is why it is split rather than attempted:

- Shortening `fade` for the basses, or giving `LaVoice` an additive rather than sum-to-one
  option for the muted window, is an audible voicing decision on a part Arthur has already
  A/B'd once and reversed.
- Extending the sample banks upward requires new source recordings and licensing, not code.

The measurement infrastructure is in place: re-run the printer after any change and require
every window's geomean within ~1 dB of parity with a tightened per-point spread.

### Blocker (2026-07-25)

Blocking owner: **Arthur**. Unblock when Arthur supplies these two decisions:

1. Audition and choose the bass onset contract: keep the current sum-to-one 50–350 ms
   handover, shorten it, or preserve the modeled kick with an additive onset window. This
   must include an accepted handover endpoint because 90% of the motivating part's notes
   end before 350 ms and Arthur previously reversed the sampled-bass A/B.
2. Choose the out-of-zone policy above D2/E2: accept up to +12 semitones of sample repitch,
   disable the LA layer above its recorded range, or provide/approve higher owner-recorded
   or CC0/CC-BY bass-onset samples with retained provenance.

Those choices determine different audible behavior and asset scope. An unattended change
would guess at the product contract rather than fix a settled defect.

### Decision and autonomous implementation brief (2026-07-26)

Arthur approved a bass-specific additive LA contract:

1. Keep the modeled bass at full weight from time zero. Layer the sampled transient over
   it at full onset weight, then taper the sample smoothly to zero by approximately
   150 ms. Do not reuse the current sum-to-one 50–350 ms replacement crossfade for
   GM 32–35: the model's `kick` and decay must remain present throughout.
2. Limit upward sample repitch to **five semitones** from the selected zone root
   (`2^(5/12)`, approximately `1.33484×`). Above that ceiling, return the bare modeled
   voice. Do not stretch the existing recordings upward by an octave and do not add or
   source new audio in this fix.
3. Recalibrate `LA_PIZZBASS` and `LA_EBASS` sample gain for additive layering. The old
   seam gains describe a replacement crossfade and are not automatically valid.
4. Keep this sampled path on the CC0 alternate bank. Do not promote it back to the
   default in this bug; a representative musical A/B is required before that separate
   product decision.

Implement the additive shape as a narrowly selected `LaVoice` mode or bass wrapper so
every existing sum-to-one LA voice remains unchanged. Avoid duplicating the sample
reader or weakening its lifecycle rules.

The autonomous fix must add focused regression evidence:

- In the first 50 ms, the wrapped bass preserves the bare model's low-frequency kick
  energy within 1 dB while also retaining a measurable sample contribution.
- The sample contribution reaches zero smoothly by 150 ms, with no amplitude step at
  the endpoint; the model remains live on notes longer than the handover.
- The combined onset is gain-calibrated rather than allowed to jump arbitrarily from
  additive summing. Re-run the existing bass-window measurement across GM 32–35 and
  representative keys/velocities, adapting its windows to the new 0–150 ms contract.
- A zone engages at exactly the five-semitone ceiling and falls back to the bit-identical
  bare model immediately above it. Cover both the finger/pizzicato and pick banks.
- Note-off, end-of-sample handling and voice reaping remain correct, and a regression
  proves a non-bass `LaVoice` caller retains its existing sum-to-one behaviour.

Leave the bug **Fixed**, not Closed, after the code and regression tests land. Independent
verification should inspect the automated evidence and audition a short representative
GM 32–35 alternate-bank render before closure.

### Fix summary (2026-07-27, deltic:auto run=fix-20260726T230602Z-p9812-n782377700-c18 code=a0bdbdc7335105591dc6dc4228b8baa1bb61d30a gate=focused+render-diff)

Agent-reported summary: Fixed MM-BUG-KILN-00085 by making the GM32-35 alternate bass sampled layer additive instead of letting it replace the modeled bass onset. The modeled bass now plays at full level from sample zero, while the sampled overlay fades out by 150 ms. The bass alternate path also refuses upward sample repitching beyond five semitones and falls back to the bare model above that ceiling. Regression tests cover onset preservation, the 150 ms taper, the upward repitch ceiling, note-off/reaping, and the unchanged ordinary LA replacement wrapper. Focused tests, both clippy feature configurations, catalog render comparisons, and an explicit alternate-bank A/B are green.

Root cause: The shared LA sampled wrapper only implemented a sum-to-one replacement crossfade, so the bass alternate path inherited a 50 ms model mute and 350 ms handover. That envelope displaced the modeled kick/transient for bass notes that are often shorter than the handover, and the sample zone also remained eligible for overly broad upward repitching.

Changed:
- crates/ferrosintesis/src/sampler.rs: added explicit LA replacement/additive blend handling, a bass-only additive limited wrapper, and focused regression coverage.
- crates/ferrosintesis/src/voices.rs: routed GM32-35 alternate bass through the additive wrapper with a 150 ms fade and five-semitone upward repitch ceiling.

Tests:
- $null | deltic timeout 300 cargo test -p ferrosintesis la_bass_alt -- --nocapture
- $null | deltic timeout 300 cargo test -p ferrosintesis la_ebass_additive_level_parity -- --nocapture
- $null | deltic timeout 300 cargo test -p ferrosintesis ordinary_la_wrap_keeps_sum_to_one_onset_ownership -- --nocapture
- $null | deltic timeout 300 cargo test -p ferrosintesis print_ebass_wrap_level_ratios -- --ignored --nocapture
- $null | deltic timeout 300 cargo clippy -p ferrosintesis --all-targets -- -D warnings
- $null | deltic timeout 300 cargo clippy -p ferrosintesis --all-targets --no-default-features -- -D warnings
- deltic render-diff albums --baseline D:\worktrees\midi-music\BASELINE-00085\target\release\ferrosintesis.exe --candidate D:\worktrees\midi-music\bug-MM-BUG-KILN-00085-run-fix-20260726T230602Z-p9812-n782377700-c18\target\release\ferrosintesis.exe: 0 changed, 82 expected same, 0 contamination; 42 default-bank GM32-35 tracks reported not reached because the harness is not bank-aware.
- deltic render-diff demos --baseline D:\worktrees\midi-music\BASELINE-00085\target\release\ferrosintesis.exe --candidate D:\worktrees\midi-music\bug-MM-BUG-KILN-00085-run-fix-20260726T230602Z-p9812-n782377700-c18\target\release\ferrosintesis.exe: 0 changed, 12 expected same, 0 contamination; 5 default-bank GM32-35 tracks reported not reached for the same reason.
- Explicit CC0=1 GM32-35 audition: C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00085\before.wav and C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00085\after.wav have equal lengths and different SHA-256 hashes, proving the alternate-bank path changed while the default catalog did not.

Left alone:
- Cargo.toml and Cargo.lock

## Notes

- **Do NOT promote the LA bass back to the default bank** until this lands. That
  instruction originates in MM-BUG-KILN-00075 and survives its closure — KILN-00075 fixed
  the gain, not the shape.
- Related: **MM-BUG-KILN-00075** (the gain, Fixed), **MM-BUG-KILN-00045** (bass family
  level spread; GM32's `UPRIGHT` decay is the shared mechanism behind item 3),
  **MM-BUG-KILN-00046** (the GM48/49 precedent, Fixed), **MM-BUG-KILN-00016** (the bass
  family's missing sampled onset).
- Not verified: whether a shorter handover actually sounds better, and where the
  repitch-credibility limit for a bass onset really sits. Both are listening questions.
