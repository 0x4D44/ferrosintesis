# Scratchpad — out-of-scope observations (triage separately)

- [x] 2026.07.10 — The synth showcase's full audio runner has four pre-existing
  oracle failures that reproduce byte-for-byte with the 0.11 baseline binary:
  track 1 `wah resonance bite` HF delta, track 4 `vowel shifts` HF direction,
  and track 5's flat dynamic arc plus `shanai pressure` RMS delta
  (`demos/synth_feature_showcase/analyze.py:106-124`). The cathedral-organ
  track 2 passes. Recalibrate or fix the three untouched tracks in a focused
  audio-oracle task; do not attribute these failures to the 0.12 organ change.
  (Promoted 2026-07-10: `MM-BUG-KILN-00002` after all four failures reproduced on v0.13.1.)
- [x] 2026.07.09 — A repo-wide GM43 contrabass scan after the Spark/Hours bass-floor
  fix still found below-C2 notes outside that task: `albums/fable5/The Ninth Bell/midi/01 - The Ninth Bell.mid`
  (`contrabass`, ch13, min MIDI 28, centered), plus VIGIL MIDI-only files
  `albums/opus4-8/midi/02 - First Light.mid`, `04 - Undertow.mid`, and
  `11 - What Remains.mid` (min MIDI 31-34). Triage by listening before changing;
  they are not the same left-panned Spark/Hours pattern.
  (Already fixed: `5b752e6` raised every listed GM43 lane to MIDI 36 or above.)
- [x] 2026.07.09 — `origin/main` `8048a64` is red on
  `altbank::tests::sawstack_v1_canary_frozen`: clean trunk and
  `MM-REQ-KILN-00013` both report `pad(89) SawStack drifted`, observed hash
  `7190932198068575567` vs expected `7408265371089978107`
  (`fable5/hollowsynth/src/altbank.rs:1387`). Out of scope for the GM47 timpani
  change; likely needs an alt-bank canary recapture or root-cause fix.
  (Already fixed: the repinned current-path canary passes on v0.13.1.)
- [x] 2026.07.08 — drums review: `impl Default for CymSpec` would remove the
  `v2: None, noise2: None, shimmer: None` boilerplate from ~5 simple cymbal call
  sites (`fable5/hollowsynth/src/drums.rs` china 52 / splash 55 / ride 51|59 /
  closed-hat 42|44 / ride-bell). Deferred as low-value cosmetic (crash_spec
  already removed the worst dup; a little duplication is fine).
  (Refuted 2026-07-10: a blanket default would hide required acoustic parameters and permit invalid specs for little gain.)
- [x] 2026.07.08 — drums review: `Drum::render` computes `head_amp_now` and a
  `tones[0].phase.sin()` every sample for EVERY drum voice
  (`fable5/hollowsynth/src/drums.rs:271-272`), used only when `wire.is_some()`
  (snare v2). Guard with `if self.wire.is_some()` to skip the per-sample `sin()`
  on non-wire voices. Minor perf; correct as-is.
  (Done 2026-07-10: `27dad7a` moved both head reads inside the wire-only branch.)
- [x] 2026.07.08 — drums review: the DR3 `noise2` band pushes its index into
  `swelled` (`fable5/hollowsynth/src/drums.rs` in `cymbal`), but the only
  `noise2` spec (open-hat 46) has `swell:false`, so it is inert. Latent-wrong if
  a future spec set both `noise2` + `swell` (sizzle should be instant, not
  swelled). Drop the `swelled.push` for noise2 or comment it.
  (Done 2026-07-10: `27dad7a` keeps `noise2` instant and adds an exact differential oracle.)
- [ ] **2026.07.08 — ARTHUR'S CALL: pre-existing vibrato bug in the shipped
  Wind + Bowed voices.** The 55-71 review found the reed vibrato ran 16x too slow
  (fixed); the SAME bug is latent in Wind (`voices.rs` ~1730/1747) and Bowed
  (~1841/1860) — an LFO `Sine` built at full `sr` but ticked once per `CTRL`
  samples, so the labelled ~5 Hz flute/whistle/fiddle vibrato is actually a
  ~0.3 Hz drift. It is a genuine quality bug. Fixing it (build at `sr/CTRL`, like
  the corrected reed/brass) CHANGES committed renders — Hollow Hill P1/P2
  (flute 73, whistle 78, fiddle 40), The Signal Fire, Winter Guests, Sub Rosa.
  Left OUT of v0.9 (scope = brass/reeds/orchestral) and flagged for Arthur: fix
  in a follow-up (its own listen), or fold into v0.9 under the relaxed policy.
  (Verified 2026-07-10 at `voices.rs:3726` and `voices.rs:3837`; decision still needed.)
- [x] 2026.07.08 — reeds review: `ReedPreset`'s 8 presets each spell out ~13
  fields; a `RD_DEFAULTS` base + struct-update (like `BR_DEFAULTS`) would cut
  ~40 lines (`voices.rs`). Low-value altitude nit; deferred.
  (Refuted 2026-07-10: the now-ten explicit preset tables are easier to audit; most fields genuinely vary.)

- [x] 2026.07.10 ferrosintesis v0.11 review minors (from 216da4a adversarial pass):
  (a) crates/ferrosintesis/src/drums.rs:1015 open-hat arm still `== Kit::V2` — use
  `!= Kit::V1` like crash_spec:570 (latent trap if the Brush intercept narrows);
  (b) crates/ferrosintesis/src/altbank.rs:61 PIZZ hardcodes course_couple 0.02 dup
  of private voices::K_COUPLE — make K_COUPLE pub(crate), reference it;
  (c) voices.rs:4647/:4658/:4669 per-site fold_key bounds never exercised by tests;
  (d) drums.rs:671 brush-slap re-excitation burst amp is absolute 0.50 — ghost-note
  slaps (vel~30) render the 12ms second contact louder than the first (touching it
  breaks brush_render_is_frozen pins — recalibrate deliberately);
  (e) drums.rs:1442 RevCym honours note_off (8ms stop) — deliberate, but foreign GM
  files with staccato 119 get near-silence; consider README note only.
  (Done 2026-07-10: (a) was already exhaustive in v0.12; (b)/(c) landed in `27dad7a`; (d) promoted to `MM-BUG-KILN-00001`; (e) is already documented in `crates/ferrosintesis/README.md`.)
- [x] 2026.07.10 ferrosintesis percussion ignores note-off (crates/ferrosintesis/src/drums.rs:308;
  choke() covers only the hat group, engine.rs:884-889) — the "cymbal choke" idiom
  authored in Through Lines T08/T11 rings instead of choking. NOT opt-in-safe to
  change (every existing file sends drum note-offs) — needs a design decision
  (e.g. choke only when note duration < some threshold AND a new opt-in signal).
  (Done 2026-07-10: Through Lines T11 now authors standard CC120 explicitly in `0146ba7`; T08's alt-bank reverse cymbal already honours NoteOff. The refreshed T11 stem drops 33.76 dB after the choke.)
- [ ] 2026.07.10 - `altbank::tests::sawstack_v1_canary_frozen` FAILS under
  `cargo test --release` at trunk 66fa84a (pad(89) fingerprint mismatch,
  `crates/ferrosintesis/src/altbank.rs:1422`); passes in debug. The exact-hash
  pin is opt-level-sensitive (float codegen differs in release). Pre-existing,
  unrelated to the choir-v2 unit; either pin per-profile hashes or run the
  canary debug-only.
