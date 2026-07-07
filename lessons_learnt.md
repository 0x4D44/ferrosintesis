# Lessons learnt

Distilled, non-obvious gotchas for future sessions in this repo. Cap: 20.

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
  bug.** hollowsynth matches note-offs oldest-first so overlaps render
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
  headline effects on rendered stems (hollowsynth `--solo`), not just in
  the event data.
- 2026.07.07 — **On Opus, heavy compose/surgery subagents must return
  PLAIN TEXT, not a StructuredOutput schema.** Six Winter Guests composers
  each did full work then all failed the schema-emission retry cap; the
  files were fine. Light verify agents tolerate the schema. Reserve
  workflow `schema:` for short-output lenses; give big generative agents a
  free-text final report.
- 2026.07.07 — **hollowsynth mono-collapse comes from the pan Haas
  micro-delay, not the chorus.** A choir-heavy, sparse, wet movement lost
  5.6 dB summed to mono because every off-centre CC10 pan adds a Haas delay
  that comb-filters sustained tonal voices in mono. Fix at the composition
  layer: centre sustained beds (pan 64) and get width from panning
  transient sources — don't touch the shared chorus bus (it's near
  mono-neutral and shared across all albums).
- 2026.07.07 — **New synth features must stay opt-in (the "authored
  channel" pattern).** Every hollowsynth CC feature (v0.6 CC1, v0.7
  CC70/71/5/65/66/67/RPN/aftertouch) only engages once a channel authors
  it; prove it by rendering all prior albums byte-identical (build a
  baseline binary in a scratch `git worktree add HEAD` and `cmp`). Keeps
  old albums frozen while the synth grows.
