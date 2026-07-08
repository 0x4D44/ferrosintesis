# MM-REQ-KILN-00013 — Timpani (GM 47) needs strike dynamics and pitch glide

- **State:** Accepted
- **Priority:** Should
- **Area:** hollowsynth / voices (timpani)
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** heavy
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
The timpani (GM 47) must model a real kettle strike: a short post-strike pitch
glide (head settling), a velocity→brightness law on the upper modes, per-strike
jitter, and a note-off release long enough that staccato hits ring rather than
choke.

## Rationale
Today timpani is fixed-frequency modes scaled by velocity only — no glide, no
harder-is-brighter, no jitter, and staccato notes choke on a 0.25 s release
against a 1 s mode ring. The channel-10 membranes already model the glide pattern
to reuse. GM 47 is used (Hollow Hill), so re-renders — needs sign-off. 2026-07-08
GM gap audit (low-strings/percussion).
