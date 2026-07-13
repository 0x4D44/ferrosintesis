# Tuxedo Noir

A spy-idiom instrumental single (3:05).  Swung walking vamp,
twang-guitar theme against a built horn-stab counterline, a 12/8
velvet middle, a 7/8 chase, and the genre's signature colour — the
minor-major-9 chord — saved for the final ring.  E aeolian, swung at
128.

**This is original material in the spy-score idiom; it quotes no
existing piece** (the famous theme it tips its hat to is only an
influence — every riff, vamp and stab here is newly composed, and the
one chromatic note in the piece, the D# of the closing E-minor-major-9,
is written raw and used once).

## The machine-verified DNA (`material.py`)

- **The vamp is swung by proof**: every on-beat 8th pair in the bass
  cell is long-short 2:1, oracle-checked, with five distinct pitches
  a bar and chord tones under the strong beats.
- **Theme vs stabs**: the twang theme (skeleton `5 3 1 2`, hanging on
  the 9th) and the horn-stab line are pairwise consonant on every
  strong beat — the Showdown plays them together, plus choir.
- **The 7/8 chase cell** covers its 3+2+2 bar with chord tones on
  every group start.
- The final chord's pitch classes are proven to spell min-maj9 on E.

## Shape

Cold Open (vibes shimmer, low piano, rim clicks) → The Vamp (the
walking bass; the theme at 0:22 with echo throws and fall-off bends) →
Stabs (the built horn section answers; +5-cent saw spread) →
**Velvet (12/8)**: flute takes the theme, fiddle slides on portamento,
bongos and brushes → **The Chase (7/8)**: palm-mute chug, overdrive
runs, stab hits → Showdown: theme + stabs stacked, one held-breath
bar, and an RPN-12 whammy dive → Last Cigarette: the reprise and the
min-maj9 ring.

## Regenerate / verify / listen

```powershell
python build.py             # rebuild + manifest
python build.py --verify    # material + 12 structural oracles
```

Listen by rendering with `python build.py` (or [ferrosintesis](../../../crates/ferrosintesis/README.md)
directly); the tagged, git-ignored `.opus` lands at
`listening/Claude Fable 5/Tuxedo Noir/01 - Tuxedo Noir.opus`.
