# MM-REQ-KILN-00004 — Marimba (12) and xylophone (13) need wood voices, not the vibes preset

- **State:** Accepted
- **Priority:** Should
- **Area:** hollowsynth / voices
- **Raised:** 2026-07-08
- **Implemented-by:** —
- **Satisfied-by:** —
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08)

## Statement
GM 12 (Marimba) and 13 (Xylophone) must render with wood-bar character — a fast,
key-scaled decay and a band-passed wood-click attack, xylophone with its 1:3
quint tuning — via dedicated `bell()` preset tables, instead of sharing the metal
VIBES table (T60 ~3 s, no click) with GM 11 vibraphone.

## Rationale
One VIBES preset currently serves vibraphone+marimba+xylophone; marimba/xylophone
ring like metal with no mallet click — the defining wood transient is absent. 12
is used by RIVERWAKE. `bell()` is table-driven, so this is data + two match arms.
Byte-identical for existing hollowsynth albums (12/13 unused by them). 2026-07-08
GM gap audit (chromatic percussion).
