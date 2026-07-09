# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. Cap: 20.

- 2026.07.08 — **A synth "spread" oracle across instruments must fix pitch, or
  it measures pitch not timbre.** Four v0.9 verification oracles measured the
  wrong thing while the voice mechanism was fine: brass `centroid/f0` ordered
  tuba<trumpet but at E1-vs-C5 the 100 Hz `centroid` floor drops the tuba's
  fundamental and inverts it; reed anti-alias tested the bari (best case) not
  the soprano (worst); choir shimmer's ±3–7 Hz FM grid overlapped the static
  detune cluster; the crash-twin oracle measured a window where the twins were
  already −70 dB. Render at matched pitch / worst case / the feature's live
  window, and keep the measurement band clear of confounding static structure.
- 2026.07.08 — **Shared voice structs are where parallel designs collide.**
  ferrosintesis strings (48–51) and choir (52–54) are both `SawStack`; designed
  in parallel, one added a stack-level `vib_depth` the other deleted (moving it
  per-`Layer`). Per-family review passed both; only a cross-section critic
  caught it. When fanning out voice designs, add an explicit assembly/critic
  pass over shared structs (`SawStack`, `Layer`, `fx_profile`, the golden
  fixture) before trusting the union.
- 2026.07.07 — **Put untouched-family canaries in the golden fixture.** The
  ferrosintesis realism build's per-channel golden table included piano/strings
  channels no phase touched; they stayed bit-exact for six phases and caught
  the one real leak (a rebuilt Drive emitting tanh(bias) DC on SILENT
  channels) that every feature oracle missed. Level guards find drift;
  canaries find contamination.
- 2026.07.07 — **Zero-crossing pitch counters lie when a change legitimately
  brightens a voice.** Three separate "pitch broke" scares in the realism
  build were the 2nd harmonic leaking through the counter's lowpass
  (452.5 Hz for a true 440). Measure pitch with a Goertzel peak
  (`testutil::peak_locate`); keep crossings only for pure-sine calibration.
- 2026.07.07 — **Noise-fed resonator pairs only beat if they can remember a
  beat.** CYM-1's 6000/6055 Hz pair at the HLD's Q 120-150 has a ~7 ms ring
  time against an 18 ms beat period — decorrelated before one cycle, no beat
  survives. Ring time Q/(πf) must span the beat period (Q ≈ 800 here);
  Δf > f/Q alone is not sufficient.

- 2026.07.06 — **Write the musical oracle before the music.** The Signal
  Fire's themes were composed to pass a counterpoint oracle (chord tone on
  every ground downbeat, consonant pairwise intervals); the finale's
  three-theme stack then worked first try. Compose-to-pass beats
  verify-after-the-fact for generative music.
- 2026.07.06 — **A movement-verified render does not verify the album.**
  Engines with one seeded RNG stream (Hollow Hill / Signal Fire engine.py)
  re-roll every downstream jitter when any upstream movement changes an
  event count — per-movement click scans and velocity means shift on the
  final assembly. Always re-measure the assembled build.
- 2026.07.06 — **Same-pitch overlapping notes are a silent GM portability
  bug.** ferrosintesis matches note-offs oldest-first so overlaps render
  fine locally, but kill-newest GM synths chop the re-strike. The Signal
  Fire engine's `Score._resolve_overlaps()` (write-time clamp) is the fix;
  Hollow Hill's engine still has the issue if its files are regenerated.
- 2026.07.06 — **Interrupted composer agents leave salvageable drafts.**
  On session-limit deaths mid-fan-out, relaunch with an explicit
  "verify-and-complete the draft, don't rewrite" note — three of six
  Signal Fire drafts were kept nearly verbatim, saving a full re-run.
- 2026.07.06 — **Presence in the MIDI is not audibility in the render.**
  The CC1 Leslie ramp was tick-perfect in the file yet measured flat in
  audio (the organ's idle tremulant was already near LESLIE_FAST). Verify
  headline effects on rendered stems (ferrosintesis `--solo`), not just in
  the event data.
- 2026.07.07 — **On Opus, heavy compose/surgery subagents must return
  PLAIN TEXT, not a StructuredOutput schema.** Six Winter Guests composers
  each did full work then all failed the schema-emission retry cap; the
  files were fine. Light verify agents tolerate the schema. Reserve
  workflow `schema:` for short-output lenses; give big generative agents a
  free-text final report.
- 2026.07.07 — **ferrosintesis mono-collapse comes from the pan Haas
  micro-delay, not the chorus.** A choir-heavy, sparse, wet movement lost
  5.6 dB summed to mono because every off-centre CC10 pan adds a Haas delay
  that comb-filters sustained tonal voices in mono. Fix at the composition
  layer: centre sustained beds (pan 64) and get width from panning
  transient sources — don't touch the shared chorus bus (it's near
  mono-neutral and shared across all albums).
- 2026.07.07 — **New synth features must stay opt-in (the "authored
  channel" pattern).** Every ferrosintesis CC feature (v0.6 CC1, v0.7
  CC70/71/5/65/66/67/RPN/aftertouch) only engages once a channel authors
  it; prove it by rendering all prior albums byte-identical (build a
  baseline binary in a scratch `git worktree add HEAD` and `cmp`). Keeps
  old albums frozen while the synth grows.
- 2026.07.08 — **Encode the dramatic shape as an oracle, twice.** The
  Ninth Bell's "builds and drops" brief became `check_arc` — inequalities
  on per-bar velocity sums (ascent < ascent, void ≤ 0.25× processional,
  feint bar < 0.6× its neighbour, climax = global max, coda ≤ 0.2× climax)
  — plus an `analyze.py` mirror asserting the SAME contour in render RMS
  dB. Composer agents then compose *to the shape*, and the −60 dB void /
  −18 dB climax landed first assembly. A prose brief ("goes somewhere
  dramatic") is unfalsifiable; a contour of numbers is a target and a test.
- 2026.07.08 — **Reproduce a "verbatim" seed by recomputing it, not
  copying it.** The Veil had to be the demo's ch0 gesture exactly;
  `check_intro_fidelity` re-runs `pad_block`/`voice_lead`/`cc_curve` from
  the engine and pins ch0 note-for-note (sorting by jitter-rounded onset
  so ±4-tick humanisation can't scramble same-beat chords). Continuing the
  ground into movement II then needs the intro's FINAL voicing as the
  voice-lead seed, or bar 9 re-spreads and dents the seam.
- 2026.07.09 — **"Authored-channel" is not the same as old-album
  byte-identity.** MM-REQ-KILN-00008 made existing Modal/Organ pitch controls
  start working, but 13 committed MIDIs had already authored those controls
  while the synth ignored them. Scan `render_opus.py::ALBUMS` for authored
  controls before promising byte identity; then make the waiver set explicit.
- 2026.07.09 — **Full-mix audio deltas must follow the rendered signal, not the
  control's intuition.** The synth feature demos' first `analyze.py` pass failed
  because wah/Leslie/vowel checks guessed "darkens"/"louder" while the full mix
  measured HF-up or HF-down after other parts and normalization. For controller
  audibility, either isolate a solo stem or measure the rendered ratio first and
  assert that direction.
- 2026.07.09 — **Generated text-artifact freshness checks must normalize line
  endings.** The synth demo verifier compared `album_manifest.json` bytes, so a
  Windows CRLF checkout failed even though Git saw no diff and the builder emitted
  the same LF-normalized JSON. Compare text artifacts as text; keep byte-exact
  checks for binary `.mid` files.
- 2026.07.09 — **`render_opus.py::ALBUMS` is the listening blast radius, not just
  `albums/`.** MM-REQ-KILN-00017 left album MIDI byte-identical, but the newly
  committed Synth Feature Showcase listening track used GM109/111 and had to be
  refreshed. Scan every `ALBUMS` entry before declaring a synth change asset-free.
- 2026.07.09 — **Generated GM43 contrabass lanes need a floor and centered pan.**
  Spark and Hours After Rain both wrote `chord["bass"] - 12` into program 43,
  producing MIDI 12-23 sustained notes panned left; ferrosintesis turns that into
  sub-bass flatulence. Clamp/raise contrabass beds to at least C2 (MIDI 36) and
  keep sustained low strings centered unless the track has an explicit reason not to.
