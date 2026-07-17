# test-corpus/

Local, **gitignored** scratch space for third-party reference MIDI files used to
stress-test `ferrosintesis` against real-world content (varied instrumentation,
controller usage, GM program ranges) beyond this repo's own generative albums.

`reference-midi/` holds fan-transcribed MIDI files of copyrighted commercial works
(pop/rock songs, electronic albums, game soundtracks) pulled from public MIDI
archives for local playback testing only. **Never commit or push the contents of
this directory** — this repo's remote (`github.com/0x4D44/ferrosintesis`) is
public, and these files are not licensed for redistribution. `.gitignore` enforces
this (`test-corpus/*`, with only this README re-included).

The tracked index below is the source of truth for rebuilding the local corpus.
Filenames are stable local names; the links point to the archive or download page
where each fan transcription was found. Availability and archive filenames may
change. Downloads have no redistribution licence unless the linked source says
otherwise, so keep them local.

## Reference index

### Mike Oldfield

| Local filename | Work / arrangement | Source |
|---|---|---|
| `mike-oldfield/01-tubular-bells-part-one.mid` | Tubular Bells, Part One | [Midis101](https://www.midis101.com/free-midi/53432-mike-oldfield-mike-oldfield-tubular-bells) |
| `mike-oldfield/02-moonlight-shadow.mid` | Moonlight Shadow | [Midis101 Mike Oldfield archive](https://www.midis101.com/search/mike-oldfield) |
| `mike-oldfield/03-ommadawn.mid` | Ommadawn | [Midis101 Mike Oldfield archive](https://www.midis101.com/search/mike-oldfield) |
| `mike-oldfield/04-incantations-part-iv-xg.mid` | Incantations Part IV: Intro / Vibes / Guilty / Ode to Cynthia (Yamaha XG, Ferran Perez Torres, 6:56) | [Tubular.net](https://tubular.net/midi/Incantations4XG.mid) |
| `mike-oldfield/05-tubular-bells-ii-early-stages.mid` | Tubular Bells II Early Stages, the early standalone form of “Sentinel” (4:11) | [Tubular.net](https://tubular.net/midi/EarlyStages.mid) |
| `mike-oldfield/06-amarok.mid` | Amarok arrangement (Rene de Vreng, 5:24) | [Tubular.net](https://tubular.net/midi/Amarok.mid) |
| `mike-oldfield/07-amarok-happy.mid` | Amarok “Happy?” section (Carsten Kuss, 6:23) | [Tubular.net](https://tubular.net/midi/Happy.mid) |
| `mike-oldfield/08-amarok-busy.mid` | Amarok “Busy” section (Carsten Kuss, 9:38) | [Tubular.net](https://tubular.net/midi/Busy.mid) |
| `mike-oldfield/09-amarok-roses.mid` | Amarok “Roses” section (Daniel Acedo, 5:57) | [Tubular.net](https://tubular.net/midi/Roses.mid) |
| `mike-oldfield/10-the-bell-steve-farrell.mid` | The Bell (Steve Farrell, 7:00) | [Tubular.net](https://tubular.net/midi/TheBell%28SF%29.mid) |

The current Tubular.net copies of `05-tubular-bells-ii-early-stages.mid` and
`09-amarok-roses.mid` have valid MIDI headers but malformed track data;
`ferrosintesis` rejects both with `unexpected end of file`. They remain indexed
because the references are useful, but need complete replacement files before
they can join the rendered listening set.

### The Beatles

| Local filename | Work | Source |
|---|---|---|
| `beatles/01-hey-jude.mid` | Hey Jude | [BitMidi](https://bitmidi.com/search?q=hey+jude) |
| `beatles/02-let-it-be.mid` | Let It Be | [BitMidi](https://bitmidi.com/search?q=let+it+be) |
| `beatles/03-yesterday.mid` | Yesterday | [BitMidi](https://bitmidi.com/search?q=beatles+yesterday) |
| `beatles/04-while-my-guitar-gently-weeps.mid` | While My Guitar Gently Weeps | [BitMidi](https://bitmidi.com/search?q=while+my+guitar+gently+weeps) |

### Jean-Michel Jarre

| Local filename | Work | Source |
|---|---|---|
| `jean-michel-jarre/01-oxygene-part-4.mid` | Oxygene Part IV | [BitMidi](https://bitmidi.com/search?q=oxygene+part+4) |
| `jean-michel-jarre/02-oxygene-part-2.mid` | Oxygene Part II | [BitMidi](https://bitmidi.com/search?q=oxygene+part+2) |
| `jean-michel-jarre/03-equinoxe-part-5.mid` | Equinoxe Part V | [BitMidi](https://bitmidi.com/equinoxepart5-mid) |

### The Secret of Monkey Island / Monkey Island 2

| Local filename | Work | Source |
|---|---|---|
| `monkey-island/01-secret-of-monkey-island-main-theme.mid` | The Secret of Monkey Island main theme | [The Legend of Monkey Island music archive](https://legendofmi.com/downloads/music/) |
| `monkey-island/02-lechucks-theme-mi1.mid` | LeChuck's Theme | [The Legend of Monkey Island music archive](https://legendofmi.com/downloads/music/) |
| `monkey-island/03-woodtick-theme-mi2.mid` | Woodtick Theme | [The Legend of Monkey Island music archive](https://legendofmi.com/downloads/music/) |
| `monkey-island/04-voodoo-lady-mi2.mid` | Voodoo Lady's Swamp | [The Legend of Monkey Island music archive](https://legendofmi.com/downloads/music/) |

### Gabriel Knight: Sins of the Fathers

Robert Holmes composed the score; these are General MIDI sequences distributed by
Quest Studios.

| Local filename | Work | Source |
|---|---|---|
| `gabriel-knight/01-main-theme.mid` | Main Theme | [Gabriel Knight Mysteries music archive](https://gkmysteries.nfo.sk/) |
| `gabriel-knight/02-voodoo-shop-dr-john.mid` | The Voodoo Shop (Dr. John) | [Gabriel Knight Mysteries music archive](https://gkmysteries.nfo.sk/) |
| `gabriel-knight/03-new-orleans-map-theme.mid` | New Orleans Map Music | [Gabriel Knight Mysteries music archive](https://gkmysteries.nfo.sk/) |

## Local layout

Put downloaded files under `test-corpus/reference-midi/` using the indexed paths.
Rendered listening copies belong under `test-corpus/reference-midi-opus/`. Both
trees remain ignored by Git.
