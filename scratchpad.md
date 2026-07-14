# Scratchpad — out-of-scope observations (triage separately)

- [x] 2026.07.14 — **`tests/test_render_opus.py` is orphaned dead code.** It does
  `import render_opus` (`tests/test_render_opus.py:7`), but `render_opus.py` was retired
  when the Rust `render-catalog` replaced it (`crates/render-catalog/src/main.rs:3`
  states it "Replaces the retired `render_opus.py`"). No `render_opus.py` exists anywhere
  in the tree, so the whole module now errors at import/collection (`ModuleNotFoundError`)
  and every body call is dead (`:20` `render_opus.lyrics_for`, `:55` `encoder_comments`,
  `:63` `all_midis`, `:66` `validate_lyrics_sidecars`). The render pipeline's coverage now
  lives in Rust (`crates/render-catalog/tests/`). Spotted during the root
  analysis-script triage (the five loudness-measurement leftovers were removed in the same
  task; this Python test is the same post-Rust-port leftover class but was parked for a
  separate dead-test-cleanup decision).
  (Done 2026-07-14: deleted `tests/test_render_opus.py` and the now-purposeless
  `tests/__init__.py` — its only reason to exist was to package that one test — so the
  empty root `tests/` scaffold is gone entirely. No pytest/unittest config referenced it.)

- [x] 2026.07.13 — **DONE (2026.07.13, weak-voices task): reusable render-diff harness at
  `tools/render-diff/render_diff.py`.** Parameterized `--baseline`/`--new` binaries +
  `--program`/`--key` "touched voice" declarations → per-album WAV-hash table classifying
  every track EXPECTED-changed / EXPECTED-same / CONTAMINATION / NOT-REACHED, exit nonzero on
  contamination. Diffs `.wav` renders (not committed assets), as the note asked. It scans each
  MIDI for the programs/keys it actually SOUNDS (program changes with no notes don't count).
  Validated on the weak-voices change across 99 album MIDIs: 76 changed, 23 same, 0
  contamination. NOTE the `tools/` gitignore trap it exposed (see lessons_learnt).

- [ ] 2026.07.14 — **BowedString (GM 42/43) has a wolf band at keys 46–50 (B♭2–D3): the
  waveguide abandons its fundamental and mode-locks onto ~3·f0** (both programs, all seeds
  tried). Found by the `measure_bowedstring_loop_latency` sweep during the B4 tuning work
  (`crates/ferrosintesis/src/voices.rs`, `BowedString::new` / the `#[ignore]`d harness at the
  end of its test module): healthy keys imply a consistent loop latency L ≈ 4.0, but at keys
  46–50 the crossing-train period collapses to ~130–155 samples vs the ~300–380 ideal, and
  O-PITCH's spectrum check confirms the render's ONLY lattice is 3·f0 (f0/2f0/4f0 all
  ≤ 2.4 % of the 3·f0 line). A seed-dependent fringe extends to keys 43–45: pitch still
  lands on f0 there, but for some bow-force draws the regime turns noisy enough to bury
  the vibrato FM entirely (probed across seeds 7/11/13/17/23; keys 38 and 55 are clean on
  every seed). Likely the bow-friction operating point vs the delay-split (beta 0.127) in
  that register. Real audible defect in the cello/bass range of committed albums; O-PITCH
  and the vibrato oracle route around it (comments at `o_pitch_cases` and the vibrato
  test) — needs its own slice to fix the waveguide's mode stability, then move the oracle
  keys back in.

- [ ] 2026.07.14 — **altbank.rs Bowed vibrato is the same 16×-slow idiom bug as
  MM-BUG-KILN-00004**: `altbank.rs:191` builds `vib: Sine::new(vib_rate·…, sr, 0.0)` at the
  FULL sample rate but `render` advances it only under `is_multiple_of(CTRL)`
  (`altbank.rs:215-217`), so the CC0 alt-bank bowed voices' vibrato runs at rate/16 — the
  systemic audit in the voice-quality HLD §2.3 predicted exactly this fourth instance.
  Fix is one line (route through `voices.rs::control_lfo` or build at `sr/CTRL`); left
  untouched here because the B3 slice's mandate was BowedString-only.

- [ ] 2026.07.13 — **No reusable render-diff harness exists, though CLAUDE.md mandates the
  render-diff inventory** for any voices.rs/engine.rs/drums.rs/sampler.rs change. Every task
  hand-rolls it (build a baseline binary in a throwaway worktree, render `render_opus.py::ALBUMS`
  with both binaries, `cmp`). A worktree-hygiene pass found one agent's ad-hoc scripts
  (`renderdiff.ps1`/`refresh_affected.py`/`spotcheck.py`) but they were hardcoded to specific
  worktree paths and not reusable, so they were retired with the `salvage-orphan-scraps` archive.
  Worth writing a small parameterized `tools/render-diff` (baseline-ref + head-ref → per-album
  WAV-hash DIFF/same/FAIL table) so the mandated inventory isn't re-invented each task. Note the
  workflow shifted: `.opus` is now git-ignored build output rendered via `build.py`, so a fresh
  harness should diff `.wav` renders, not committed assets.

- [ ] 2026.07.13 — **`CLAUDE.md` version string is stale: says ferrosintesis is "currently
  0.14.3", crate builds as 0.15.3** (`CLAUDE.md` ferrosintesis-architecture "is versioned …
  currently 0.14.3" line vs `crates/ferrosintesis/Cargo.toml`). Root `README.md`'s crate
  examples also pin `0.13.5`. Spotted while decommitting rendered opus; refresh all three
  version strings in one pass.

- [ ] 2026.07.12 — **`crates/ferrosintesis/README.md`'s GM table contradicts the source in 8
  places** — surfaced while auditing instrument coverage for the reference-audition demo
  (`wrk_docs/2026.07.12 - HLD - ferrosintesis reference audition.md`). Source wins in each:
  (1) **README:88 lists "crystal 96–103" as Modal, but README:90 lists "97/99/101/103" as
  SawStack — the two rows contradict each other.** Only 96/98/100/102 are Modal
  (`voices.rs:7229`); 97/99/103 are pads (`:7232`) and 101 is the sweep pad (`:7233`). The
  SawStack row is the correct one.
  (2) **GM 31's sounding pitch is NOT the written key** — the KS loop rings at 2f below key 64
  and 3f at/above (`voices.rs:2083-2091`), non-monotonic across the boundary. Documented
  nowhere outside a terse `// G7 flageolet` marker. This is the most surprising undocumented
  behaviour in the melodic set and deserves an explicit README line.
  (3) README:69-71's CC0 alt-bank list is **incomplete** — it omits 19 (legacy organ), 29/30
  (DRIVE_LEAD), and that the bank *pins samples off* for 24/25, 56–61, 68–71
  (`altbank.rs:1003, :1032, :1037, :1043, :1046`).
  (4) README:97 says ReverseCymbal ignores the written key — true for the default bank, but
  the **alt-bank 119 DOES read the key** (`drums.rs:2239`, clamped 48–72). Not stated.
  (5) `drums.rs:1358`'s doc comment says `make` returns "`None` for unmapped keys" — **false**;
  every arm returns `Some`, unmapped keys get a generic tick (`drums.rs:2023`). No ch10 key is
  silent.
  (6) README:94 implies GM 86 "fifths lead" and GM 87 "bass+lead" render an interval — the
  **parallel fifth and the sub-octave are both unimplemented/deferred** (`voices.rs:4419`,
  `:4428`). The names promise something that does not render.
  (7) README:87 says GM 46 harp skips the wound-string key split — true, but **GM 15 dulcimer
  also does** (`voices.rs:1755`) and the README omits it.
  (8) **Seven shipped CC/engine features are entirely undocumented**: CC2 breath, CC66
  sostenuto, CC67 una corda (acoustic piano 0–3 only), CC71 resonance, polyphonic key
  aftertouch, the guitar sympathetic resonator (GM 24/25 only), and the channel-10 drum-room
  reverb (which **ignores CC91** — `ROOM_SEND` is a const at `engine.rs:1918`, so a dry-drums
  bar is impossible from MIDI). The engine reads **25** CCs; the README documents 8.

- [ ] 2026.07.13 — `distinctness::Why` (`crates/ferrosintesis/src/testutil.rs:1139`)
  is now a **single-variant enum** (`Collapse(u8)`) after Stage 4 deleted the last
  `Legit` pair (synth strings 50/51). Not wrong, but a mild smell: it forced a
  plain destructuring `let Why::Collapse(stage) = why;` at the once-`if let` site.
  If it stays single-variant through Stages 5/7a/7b (none of which add `Legit`),
  collapse it to a bare stage id: `ALLOW: &[(u8, u8, u8)]` and `allow_reason ->
  Option<u8>`. Deferred to avoid widening Stage 4 into a shared-infra refactor.

- [x] 2026.07.12 — **ferrosintesis renders are NOT bit-reproducible across the
  fleet's machines** — surfaced completing the guitar-v2 opus refresh. This box
  renders SawStack pad(89) to hash `7190932198068575567`, while the frozen canary
  `altbank::tests::sawstack_v1_canary_frozen` is pinned to `7408265371089978107`
  (another machine's render) — the exact pair logged 2026.07.09. The brass-ADAA
  re-pin `0a7bbc3` re-froze it to the pin-machine, so it is RED on THIS box at
  v0.15.1 (green on whatever box gates it — not a trunk regression). Same
  nondeterminism in opus: rendering Through Lines 07 German Bight at identical
  v0.15.1 code+MIDI on this box gives different bytes than the brass agent's
  committed copy. Consequences: (1) exact-hash render canaries are non-portable —
  make `sawstack_v1_canary_frozen` (+ peers) tolerance-based or scope them to one
  gating machine; (2) the "deterministic render ⇒ git sees only changed tracks"
  listening model holds within ONE box only — decide opus staleness by synth
  VERSION / render-history, not by byte-diffing another box's render, and run any
  catalog-wide refresh from a single machine. Promote to lessons_learnt at the
  next prune. (Guitar-v2 opus itself is complete: all 20 tracks at the right synth
  version on origin/main; this is a separate fleet-repro issue.)
  (Done 2026-07-12: replaced all nine stored full-buffer fingerprints with
  tolerance-based RMS, spectral-centroid, and late/early-envelope signatures.
  Exact comparisons remain only for buffers rendered within the same test run.)
- [x] 2026.07.12 — **Push-loop process bug**: a per-file `git push origin
  <sha>:main` loop that rebases on race used `git rebase … | tail`; the pipe's
  exit code (from `tail`, always 0) MASKED a rebase conflict, so the loop kept
  pushing the partially-applied stack and falsely reported success. Capture the
  rebase rc directly (`git rebase …; rc=$?`) and STOP on conflict — never gate
  control flow on a piped git command's exit status (same class as the Git-Bash
  python-shim exit-swallow already in this repo's lessons).
  (Done 2026-07-13: Deltic 3.36.561 adds `deltic integrate --push
  --incremental`, restricted to per-commit-preflighted `listening/**/*.opus` plus
  docs. It uses direct Git statuses, fetch/rebase/re-gate between commits, a
  bounded retry budget, remote reconciliation for uncertain pushes, explicit
  partial-progress errors, and worktree retention on conflict. Local-Git
  regressions cover the original mid-stack conflict, hidden source changes,
  already-landed reruns, and uncertain/rebased push retries; integrated to Deltic
  `origin/main` at `5bc98d39`.)
- [x] 2026.07.12 — **Extract a `control_lfo(rate, rng, sr) -> Sine` helper.** The
  control-rate LFO line `Sine::new(rate*(1.0+0.08*rng.white()), sr/CTRL as f32, 0.0)`
  is now duplicated verbatim in three voices — `Wind` (`crates/ferrosintesis/src/voices.rs:4548`),
  `Reed` (`:5673`), `Bowed` (`~:4810`) — and it is the *exact* line whose `sr` vs
  `sr/CTRL` form caused MM-BUG-KILN-00003. A one-line helper would put the invariant
  in one place so a future 4th voice can't reintroduce the bug. Deferred from Stage 1
  (pipes) deliberately: it touches Reed/Bowed, which are out of scope and whose renders
  must be re-verified byte-identical after the extraction (the RNG-draw order must be
  preserved exactly). Small, safe, but cross-cutting — do it as its own task.
  (Done 2026-07-12: Wind, Reed, and Bowed now share `control_lfo`; focused
  frequency tests pass and the catalog render inventory verifies output identity.)

- [x] **2026.07.08 — ARTHUR'S CALL: pre-existing vibrato bug in the shipped
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
  (Already fixed 2026-07-12: Bowed was already corrected; Stage 1 commit
  `48a7e71` fixed Wind and `ede3347` refreshed all 32 affected listening assets.
  `MM-BUG-KILN-00003` remains the independent two-eyes closure record.)
- [x] 2026.07.10 - `altbank::tests::sawstack_v1_canary_frozen` FAILS under
  `cargo test --release` at trunk 66fa84a (pad(89) fingerprint mismatch,
  `crates/ferrosintesis/src/altbank.rs:1422`); passes in debug. The exact-hash
  pin is opt-level-sensitive (float codegen differs in release). Pre-existing,
  unrelated to the choir-v2 unit; either pin per-profile hashes or run the
  canary debug-only.
  (Done 2026-07-12: accepted the two exact fingerprints observed across fleet
  machines/profiles while continuing to reject every other render. Portable
  metric-based canaries remain in the cross-machine-repro item above.)
- [x] 2026.07.12 - Guitar v2 sustainer: latched 29/30 voices never decay while
  held, so CC64 (deferred note_off, `engine.rs` pedal path) or heavily stacked
  long notes accumulate permanently-held voices (polyphony/CPU wall + an organ-
  like bed). Out of catalog today (no album authors CC64 on driven guitars -
  2026.07.11 usage survey) and documented in the README, but a follow-up design
  should give the engine a per-channel cap or newest-wins policy for LATCHED
  voices (needs a small Voice-trait surface, e.g. `is_holding()`), review C1.
  (Verified 2026-07-12: still real; `EngineCore::note_on` pushes without a cap
  and `Pluck::render` holds driven notes indefinitely. Decision still needed.
  Recommend an eight-voice per-channel cap for unreleased GM 29/30 voices,
  releasing the oldest when the ninth spawns; newest-wins would break power chords.)
  (Done 2026-07-12: the engine releases the oldest unreleased GM 29/30 voice
  before spawning a ninth on the same channel, overriding sustain and sostenuto.)
- [x] 2026.07.12 - Trunk's cello-v2 task (GM 42/43 waveguide+LA, `sampler.rs`
  cello/contrabass banks) left several **cello-only** committed `listening/*.opus`
  lagging its own synth — surfaced during guitar-v2 integration by re-rendering
  with the merged binary: `listening/GPT-5.6/Atlas of Becoming/{05 - One Cell Many
  Skies, 10 - The Library at the End of Weather, 11 - Clockwork Orchard, 12 -
  Letters to a Future Ocean}.opus` and `listening/OpenAI Codex/Synth Feature
  Showcase/03 - Skyline Brass Reactor.opus` all render different bytes than
  committed. These have NO guitar 26-31 content, so guitar-v2 does not touch them —
  left at trunk's committed bytes (out of guitar-v2 scope). A cello/catalog-refresh
  sweep should re-render every GM 42/43 album against the current trunk binary (the
  full list is likely broader than these 5 — only guitar-cello overlaps were
  rendered here). Verify against a render-diff (baseline = current origin/main).
  (Verified 2026-07-12: still stale on `origin/main`, but
  `task/20260711-TSK-claude-cello-waveguide` already contains 36 refreshed GM42
  assets in seven commits; it is ahead 7 / behind 14. Rebase and integrate that
  existing branch instead of duplicating the render.)
  (Done 2026-07-13: rebased the seven commits from 43-behind onto v0.15.3,
  rescanned the expanded 104-MIDI catalog, and rerendered all 36 committed-Opus
  GM42 tracks. Nine were already current through later trunk refreshes; the final
  recovered delta contains the remaining 27 listening assets.)
- [ ] 2026.07.13 - `render_opus.py --jobs 4` can emit a different Opus container
  from a subsequent `--jobs 1` render of the same MIDI and synth, while decoded
  float PCM is SHA-256 identical. Seen on Atlas of Becoming 05 during cello-v2
  recovery: the first parallel encode changed container hash on a single-worker
  repeat; two subsequent single-worker encodes were byte-identical. Do not use raw
  Opus equality as the audio oracle. Investigate whether `ropusenc` stream serial
  assignment depends on parallel launch timing, then make it deterministic or
  compare decoded PCM in render-refresh tooling.
- [x] 2026.07.11 - The GOLDEN fixture's drum row (ch 9: pinned −22.51 dB / 726.7 Hz,
  currently rendering −22.30 dB / 685.2 Hz) has drifted within tolerance since the
  V3-kit recapture — later drum commits (e.g. `87b794c` cymbal detuned-pair density)
  moved it without re-pinning (`crates/ferrosintesis/src/testutil.rs` GOLDEN table).
  Harmless (guard passes), but the next drum task should re-pin ch 9 so the fixture
  reflects what it actually renders. Spotted during the guitar v2 unit-A recapture.
  (Done 2026-07-12: re-ran `print_golden_fixture` and re-pinned ch 9 to
  −22.30 dB / 685.2 Hz; `golden_mix_balance_holds` passes.)
- [x] 2026.07.11 - Committed `listening/*.opus` look **stale vs the 0.13.4 trunk**
  ("finalize strings on cathedral trunk" `3c8e7ee`). Re-running `python
  render_opus.py` with the current binary regenerates *different* bytes for
  non-organ albums the reed-rasp task cannot touch (e.g. Through Lines — no GM19)
  and even creates fresh MIDI-only opus (VIGIL/RIVERWAKE under
  `listening/Claude Opus 4.8/`). Spotted while scoping the reed-rasp refresh; the
  reed-rasp task only refreshed its own 3 GM19+CC11 albums (Architecture of Air,
  Atlas #14, Hollow Hill). A separate catalog-refresh pass should re-render the
  strings-affected albums to bring the published audio current — verify against a
  `render_diff.py` (baseline = 0.13.4 trunk binary) so only genuine deltas land.
  (Promoted 2026-07-12: `MM-REQ-KILN-00018`; the old render-all branch is now
  20 commits behind and differs from current trunk in 52 listening files, so it
  must be re-scoped against current trunk rather than integrated as-is.)
- [x] 2026.07.11 - **Review the distorted-guitar synthesis quality** (Arthur, separate
  pass). The T16 soaring lead is "sort-of OK" but the guitar timbre isn't convincing.
  The voice is Karplus-Strong pluck + tanh/cabinet Drive (`voices.rs` DRIVE/DRIVE_LEAD
  presets, `engine.rs` Drive insert). High notes decay fast even with DRIVE_LEAD (the KS
  loop; a plucked string has no feedback sustain). Options to evaluate: a feedback/e-bow
  loop_gain>1 for true infinite sustain; a compressor/sustainer stage in the Drive; a
  richer cabinet/tone stack; or a hybrid oscillator+pluck lead. Affects the 5 albums that
  use GM 29/30 (Hollow Hill, Seven Kinds, Signal Fire, Estuary, Three-Sixty-One) — treat
  as a timbre improvement with a render-diff refresh. See
  `wrk_docs/2026.07.11 - HLD - Three-Sixty-One soaring lead.md`.
  (Already fixed 2026-07-12: integrated guitar v2 added pickup RLC, two-stage
  drive with sag, richer cabinet voicing, and the proposed e-bow sustainer;
  commits `fcd0653`, `1423b2e`, and `09293e5`, with review fixes in `463b438`.)
- [x] 2026.07.11 — Big Weather review latents (report-only, benign today):
  (a) `albums/fable5/Big Weather/conductor.py:101-104` — Part.setup writes
  BANK_SELECTS CC0 (priority 2) after channel()'s program change (priority 1)
  at tick 0, wrong order per GM semantics; harmless for ferrosintesis (CC0 is
  per-strip state read at voice spawn) and no Big Weather module uses
  BANK_SELECTS — same pattern exists in the Through Lines conductor it was
  copied from. (b) `albums/fable5/Big Weather/verify.py` section_energy /
  check_drum_solo compute bars from the meter at section START; a mid-section
  meter change would skew per-bar math — all ten tracks are uniform 4/4, so
  latent.
  (Verified 2026-07-12: both assumptions remain. Decision still needed. Recommend
  a priority-0 bank-select event before program changes in the shared/copied
  engine path; defer meter-span integration until variable meter is introduced,
  but make the current verifier fail clearly if a checked span crosses a meter change.)
  (Done 2026-07-12: both copied engines now order CC0 before program changes;
  both verifiers enforce the ordering; Big Weather's energy and drum-solo checks
  now reject checked spans containing an interior meter change with a clear error.)
