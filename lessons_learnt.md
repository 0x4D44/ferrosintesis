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
