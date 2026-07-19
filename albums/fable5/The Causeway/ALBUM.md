# The Causeway — track notes

An album by **Claude Fable 5** (2026). Ten crossings in two acts (~55:35)
between a tidal island and a mainland village joined by a causeway that only
shows at low water — two players sending music instead of letters across a
winter, and then across the year that follows. The **island** writes in
late-ABBA ice (incantatory repeated notes, off-beat pushes, sequenced chill)
wrapped in Enigma/Delerium weather — breath flutes, vowel choirs, echo
throws; the **mainland** writes in McCartney warmth — melodic protagonist
bass, piano pump, clavinet strut, suite-form pivots — layered with Oldfield
patience. Original material throughout; the album writes in the *vocabulary*
of those idioms and quotes nothing.

**Act One (1–5): the winter apart.** The two shore themes begin a tritone
apart and converge track by track — **6 → 4 → 3 → 2 → 0 semitones** — while
every cadence is modally withheld (no leading-tone V–I anywhere in tracks
1–4) and the themes are never allowed to sound at the same time. Track 5
crosses at dawn: both themes together in D, invertible counterpoint, a
medley of the act's four hooks, and a fusion phrase that lands Act One's
only melodic tonic on a plagal Picardy.

**Act Two (6–10): the tide returns.** The water re-drowns the road — the
stereo strait re-opens (16 → 20 → 44 → 36 wide, never again as wide as the
first winter) — but the voices never part again: distance 0 on every track,
overlap *required*, the leading-tone ban lifted. Everything new grows from
the fusion phrase (each hook carries a machine-checked derivation), and the
act runs on a new audible engine: **the road home** — the fusion phrase's
exact retrograde — assembles 3 → 5 → 6 → 8 notes across the tracks, each
reach stopping short, until the finale walks it whole. Tracks 6/7/9/10 end
on the plagal signature the crossing taught them; the gale alone is refused
its cadence. In track 10 the island's theme finally turns **major** (still
hanging on its second degree), the forward fusion and its retrograde sound
as one palindrome — the road out and the road back — and ten bell tolls
widen into a seashore that sounds last.

The recurring devices, all pinned in `material.py` and proven by the oracles
in each track's module: the hook ledger (one earworm per track, sung by the
protagonist bass in every chorus; two medleys — Act One's in T5, Act Two's
in T10); breath-flute heralds priming each groove out of silence; morse
tide-words (NEAP, WAIT, TURN, EBB, HOME / FLOOD, NOON, GALE, WANE, SAIL) on
ten distinct rotating timbres; tide-breath tempo maps with pinned still
points (and T10 breathing everywhere — they are ON the water); a bell buoy
ending track N with exactly N tolls; and a choir vowel clock that seals in
winter, opens through summer, and reaches its widest voice (≥ 100) as they
sail.

| # | Track | Time | |
|---|-------|------|---|
| 1 | **Neap Light** | 5:31 | The island alone; the far shore only a rumour. The incantation over open-fifth drones, a sealed choir, celesta tapping `NEAP`; a pan-flute inhale into the Delerium heartbeat; the mainland theme once, in B♭ a tritone away, on a horn drenched in reverb — distance coded in the wet. One toll. E minor. |
| 2 | **The Winter Ferry** | 5:55 | The failed crossing — a Band-on-the-Run three-act storm on a Mrs-Vandebilt engine: clavinet hammer-ons, wah chops, brass aftertouch rasp, brush→full→brush kit swaps, accelerando 112→138 — until the wave turns the ferry back. The mainland theme complete but alone, in C; harmonica lament; two tolls. |
| 3 | **Spring Tide** | 5:00 | The turn of the year: a marimba/kalimba 3-against-4 lattice whose realignment click is the reward beat; the shores close enough to CALL AND ANSWER within a beat — never touching; Leslie spin-ups, steelpan colour, opening vowels. Three tolls. A minor → C major. |
| 4 | **The Ebb Letter** | 4:40 | The darkest hour: a 6/8 candle under una corda with fermata rubato; a metronomic ice-arp mutating one pitch per cycle; the mainland *reaching* on horn — 4, then 7, then 9 of its 10 notes, never completing; kalimba taps `EBB`. Four tolls. A minor. |
| 5 | **Low Water Crossing** | 6:26 | The dawn crossing: the keysig flips to D major, the tempo flattens (the water is out), and every Act One promise lands — themes simultaneous and inverted both ways, the four hooks over a 1985 pump, `HOME` pealed in morse, an RPN-12 octave-bend solo, the fusion phrase's only Act One tonic landing, a plagal Picardy, five tolls. |
| 6 | **The Flood** | 5:13 | Act Two inhales (pan flute at the very top) and the tide chases them back across — the Another Day gait into a stacked Super Trouper chorus, accelerando with a rising CC74 waterline, the themes' first EASY overlap, the road home's first three notes left hanging. Six tolls. G major. |
| 7 | **Noon Water** | 5:29 | High summer — Delerium Karma warmth in C: shakuhachi haze, steel drums tapping `NOON`, a downtempo groove with the noon fall (the fusion's own tail) on bass, echo throws, a lazy harmonica; the reach at five notes, stopped. Seven tolls. |
| 8 | **The Equinox Gale** | 5:45 | The album's heaviest track: the gale riff (the fusion head slammed down a sixth) on driven guitars, Stranglehold horns, fast Leslie, timpani thundering `GALE` in morse, an authored lurching storm map — and the thesis, machine-verified: the storm cannot part them (two overlaps inside the gale). The eye holds one fusion alone; the reach hits six and is snatched away; the final cadence REFUSES the tonic, and the buoy tolls the D the music would not — eight times. D minor. |
| 9 | **The Wane** | 5:18 | The autumn letters — Distractions tenderness with Footprints fingerpicking: nylon and steel guitars, bossa brushes, a marquee cello; THE MEMORY: Act One's heartbeat quoted at half speed and the island theme once in its original E minor — the record's only off-key statement, whitelisted by name; the reach at eight of nine. Music box taps `WANE`; nine tolls. F major. |
| 10 | **Out on the Tide** | 6:15 | The second crossing: both leave together at low water. Eight ship's bells and a `SAIL` in morse; the gallop carries the Act Two medley; the slack clears the stage and the island theme finally turns MAJOR; the crest breaks into the palindrome — the fusion phrase forward, then its exact retrograde, the road out and the road back as one mirror — a plagal IV–I, the choir at 104, a seashore swelling beneath, and TEN tolls widening into the wash as CC11 carries the band below the horizon. The sea sounds last. D major. |

Oracle-first, per the house method: every headline claim above exists as a
falsifiable check in the track's module (`movements/tNN_*.py`) — **265 green
rows** across the album (the shared material proof with its round-trip and
derivation matrix, 90 generic checks, 174 track oracles), plus 30 per-track
audio oracles measured on the rendered waveforms. The pieces were composed
*to pass them*.

See `README.md` for how to rebuild, verify, render and listen.
