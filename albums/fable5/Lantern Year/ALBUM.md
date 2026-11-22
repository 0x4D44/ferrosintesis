# Lantern Year — track notes

An album by **Claude Fable 5** (2026). Ten nights at a lighthouse across one
year, January to December. Ten tracks, 50 minutes, every track about five
minutes long — and every night in a different idiom.

Three things bind the year, and every recurrence is machine-verified (the
shared detectors live in `material.py`, the claims in each track's oracles):

- **THE BEAM** — a five-note cell, degrees 1-5-6-5-8: the lamp swings out over
  the water, brushes the horizon, and comes home an octave higher. Every track
  states it at least three times in its own voice — a 7/8 riff, a jig's opening
  figure, a blues turnaround, a brass call, the seed of a marimba process.
- **THE KEEPER'S HYMN** — a 16-bar tune whose first five notes *are* the beam.
  Track 1 states it plainly in D dorian; track 10 crowns it in D major. Five of
  the nights between (2, 3, 4, 7, 8) borrow a phrase.
- **THE LAMP** — one tubular-bell stroke on D. It is the first sound of the
  album and the last.

| # | Track | Time | |
|---|-------|------|---|
| 1 | **First Lighting** | 5:01 | January dusk; chamber folk. The lamp bell alone, the beam on unaccompanied piano, then the hymn stated plainly so the listener can learn it. A second verse on violin with a clarinet counter-melody, a brighter middle in C that leaves the tune behind, and the hymn again, tutti. Ends on the bell. D dorian, ♩ = 92. |
| 2 | **Northeaster** | 5:00 | February storm; prog rock. 7/8 verses (2+2+3) against 4/4 choruses — the beam *is* the 7/8 riff. An organ solo, the eye of the storm (twelve bars of surf, one bell, the hymn's first phrase on a far organ), a guitar solo with real bends, and a second peak verifiably bigger than the first. Ends on a slammed unison E. E aeolian, ♩ = 150. |
| 3 | **Fog Signal** | 5:02 | March; ambient. A two-note foghorn returns every twenty beats, fifteen times, the one clock in the fog; around it, loops of 11, 13, 17 and 23 beats that never line up twice. Nothing rises above mezzo-piano; harmony never moves faster than once in eight beats; a pitched beacon taps `FOG` in Morse. C lydian, ♩ = 60. |
| 4 | **The Mail Boat** | 5:02 | April; a jig set. Two jigs, each AABB with its repeats exact — the first in G (its opening figure is the beam), the second in E dorian — then the first back a tone higher in A. The tune is handed between fiddle, whistle, accordion and mandolin; every onset sits on the jig lattice; the hymn rides the last round as an accordion descant. 6/8, dotted-♩ = 108. |
| 5 | **Glass Calm** | 4:59 | Midsummer; mallet minimalism. Two marimbas play one cell built from the beam; one slips ahead an eighth at a time through all eight positions and comes back to unison, every stage tick-verified. A celesta plays the line the two make together; flute and strings float a long-breathed tune over an unbroken pulse. A ionian, ♩ = 132. |
| 6 | **False Lights** | 5:01 | July, no moon; 5/4 noir. Wreckers show a lantern to lure ships in: the beam appears first *corrupted*, its fifth flattened to a tritone, and that C♮ is quarantined to those moments. After a tutti and a scored silence, an open trumpet plays the true beam alone. Ends unresolved, the bass on the phrygian ♭2. F♯ phrygian, ♩ = 104. |
| 7 | **Perseids** | 4:58 | August; electronica. The beam seeds the arpeggio; meteors — fast falling runs at irregular moments — thicken to a verified peak in the second drop, which lifts from B minor into D major and is provably bigger than the first. Four-on-the-floor in the drops, broken beats elsewhere. B aeolian, ♩ = 126. |
| 8 | **Equinox Gale** | 4:52 | September; orchestral scherzo, one in a bar. Scherzo – Trio – Scherzo – Coda for full orchestra: hemiolas at every cadence, the beam as a trumpet call and in the basses, a pastoral trio in C major where the horns quote the hymn, a return bigger than the first statement, and a coda pressing 174 → 200. C aeolian, 3/4. |
| 9 | **The Long Watch** | 5:05 | November, small hours; slow blues. Five choruses on a verified 12-bar form, each led by a different soloist — tenor sax, muted trumpet, guitar over stop-time, organ, then everyone — all on the triplet lattice. The beam is the turnaround lick in every chorus. Ends on a B♭6/9 and one bell. B♭, 12/8, dotted-♩ = 56. |
| 10 | **Last Lighting** | 4:57 | December; the finale. Opens as the year opened — the bell, then the beam. The hymn complete on a cathedral organ in D dorian; a second theme; the key turns; the hymn crowned in D major, tutti, under a guitar descant consonant on every bar line. A last beam climbs four octaves, and the album ends on the bell alone. ♩ = 88 → 96. |

## How it was made

The framework came first: `conductor.py` (the registry and the federated
`Part` grid), `material.py` (the beam, the hymn, the lamp, their detectors,
and three album-wide oracles every track must pass), and `COMPOSER-NOTES.md`
(the contract and the ten briefs). Ten composers — one per track — then worked
in parallel against that contract, each writing its own oracles before its
music and breaking the music once per oracle to prove the oracle could fail.
`python3 build.py --verify` runs 215 checks across the album.

Each composer also listened with numbers: rendered the track, measured section
loudness and per-voice stems against the mix, and fixed the mix — not the
checks — where a lead was buried. The audio oracles in each module's
`audio_checks()` pin the hush, the peak and the ending on the rendered
signal.
