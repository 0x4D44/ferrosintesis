# The Burning Meridian

Three orchestral film-epic instrumentals (3:14 + 3:19 + 3:03).  One
HORN THEME binds the outer tracks. The horn section is **built**: rock
organ + saw stack in octaves, fattened with a +6-cent fine-tune spread,
doubled by choir and strings at the summits, because the synth version
used for this album did not yet model brass.

This is original material using broad film-music vocabulary; it is
not a copy of any existing score.

## The machine-verified DNA (`material.py`)

- **One theme, two wars.** The horn theme's strong-beat skeleton
  `[1 3 3 4]` is a chord tone of both the 12/8 muster ground
  (Dm Bb F C) and the 5/4 battle ground (Dm Dm Bb C) — track 3
  restates track 1's call over new harmony and a new meter (the theme
  stretches ×1.5 into 12/8 and ×1.25 into 5/4, so its downbeats stay
  on the bar lines and the proof carries).
- **A snapped descant** (3rd up, checked at every half-bar) rides the
  stacked statements of both epics.
- **The elegy duet**: track 2's fiddle and flute lines are pairwise
  consonant at every 3/4 bar line and mid-bar, and both stay inside a
  5th of melodic motion.
- **Ostinati by construction**: the 12/8 and 5/4 low-string engines
  are all chord tones with full coverage.

## Shape

01 **The Muster** (D aeolian, 12/8): embers → the ostinato climbing
under taiko layers → the call, three growing statements + descant →
over the hill (solo fiddle echo, one last ringing hit).

02 **Lanterns on the Water** (A aeolian, 3/4): harp water → the duet
(twice, then voices swapped, then cello beneath) → the orchestra
takes it, bell and timpani → ashfall, rit.

03 **Meridian** (D aeolian → **D MAJOR**, 5/4 as 3+2): war footing →
cavalry (the theme rides the odd meter) → the 4/4 break (the elegy
remembered; cello portamento sighs) → the charge in four waves with a
held-breath bar and a two-semitone horn FALL into the grand pause →
**Daybreak**: the same theme in the major, over bells.

## Regenerate / verify / listen

```powershell
python build.py             # rebuild all three + manifest
python build.py --verify    # material + 12 structural oracles / track
```

Listen via [ferrosintesis](../../../crates/ferrosintesis/README.md) (v0.8) or the
committed `listening/Claude Fable 5/The Burning Meridian/*.opus`.
