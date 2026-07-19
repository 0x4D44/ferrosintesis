# The Causeway — track notes

An album by **Claude Fable 5** (2026). Five crossings between a tidal island
and a mainland village joined by a causeway that only shows at low water —
two players sending music instead of letters across a winter. The **island**
writes in late-ABBA ice (incantatory repeated notes, off-beat pushes,
sequenced chill) wrapped in Enigma/Delerium weather — breath flutes, vowel
choirs, echo throws; the **mainland** writes in McCartney warmth — melodic
protagonist bass, piano pump, clavinet strut, suite-form pivots — layered
with Oldfield patience. Original material throughout; the album writes in
the *vocabulary* of those idioms and quotes nothing. Five tracks, ~27:33.

The story arc is machine-verified: the two shore themes begin a tritone
apart and converge track by track — **6 → 4 → 3 → 2 → 0 semitones** — while
every cadence is modally withheld (no leading-tone V–I anywhere in tracks
1–4) and the themes are never allowed to sound at the same time. The finale
crosses at dawn: both themes together in D, invertible counterpoint, a
medley of the album's four hooks, and a fusion phrase that lands the
record's only melodic tonic. The devices that bind the record, all pinned in
`material.py` and proven by the oracles in each track's module:

- **THE TWO SHORE THEMES** — the island's ten-note incantation always hangs
  on degree 2; the mainland's tune leaps a major sixth and settles on
  degree 6. Neither may end on its tonic until the end.
- **THE CONVERGENCE** — the keys close 6-4-3-2-0 semitones; T3 escalates to
  call-and-answer (statements adjacent within a beat, still disjoint); T5
  requires overlap, downbeat-consonant, inverted both ways.
- **THE HOOK LEDGER** — one riff cell per track (heartbeat, ferry riff,
  lattice, ice-arp, pump call), stated ≥ 6 times in its own track and sung
  by the bass in every chorus; the finale restates hooks 1–4 over the pump
  (the side-two medley, made checkable).
- **THE WEATHER** — a breath-flute herald primes each groove out of
  silence; morse tide-words (NEAP, WAIT, TURN, EBB, HOME) rotate through
  five timbres; the stereo field is the strait itself, island channels
  seated left and mainland right, the seats narrowing with the keys
  (40/88 → 60/68); a bell buoy ends track N with exactly N tolls.

| # | Track | Time | |
|---|-------|------|---|
| 1 | **Neap Light** | 5:31 | The island alone; the far shore only a rumour. Piano states the incantation over open-fifth drones while a sealed choir hums and a celesta taps `NEAP`; a pan flute inhales and the Delerium heartbeat locks — synth-bass ostinato, FM-EP ice arps, the bass singing above the pulse, choruses thickened at the octave. Then the album's only mainland glimpse: its theme once, in B♭ a tritone away, on a french horn drenched in reverb (send 112 against ≤ 48 everywhere else — distance coded in the wet). One bell toll. E minor, tide-breath ≈76→92. |
| 2 | **The Winter Ferry** | 5:55 | The failed crossing — a Band-on-the-Run three-act storm on a Mrs-Vandebilt engine. Brush-kit harbour, woodblock tapping `WAIT`; then the strut: sampled clavinet with hammer-on slurs, wah-filtered octave chops, brass stabs snapping with aftertouch rasp, fretless portamento scoops, E mixolydian false hope, an authored accelerando 112→138 — until the wave (orchestra hit and tam-tam) turns the ferry back. The mainland theme arrives complete but alone, in C, over the wreckage; a harmonica laments; the brushes return hollow at half tempo. Two tolls. |
| 3 | **Spring Tide** | 5:00 | The turn of the year. A marimba cycles a 3-quaver cell against a kalimba's 4-grid — the lattice realigns every 12 quavers and that click is the reward beat — while the choir's vowels begin to open and a muted guitar taps `TURN`. The spring groove blooms in C major: brass punches the mainland theme and the island answers within a single beat — close enough to talk, still forbidden to touch. Leslie spin-ups, steelpan colour, an autopan shimmer; then slack water, kalimba alone, three tolls. A minor → C major, 96→108. |
| 4 | **The Ebb Letter** | 4:40 | The darkest hour — ice outside, one candle inside. A 6/8 candle scene under una corda with fermata rubato dipping to 48, cello sighing bend-appoggiaturas; then the ice: exactly one tempo event, a 16th-note arp mutating one pitch per cycle over a static drone, kalimba tapping `EBB` — and the mainland *reaching* on french horn in G: 4 notes, then 7, then 9 of its 10, never completing. Wax closes at 56, the island's last pre-dawn reading, four tolls. A minor. |
| 5 | **Low Water Crossing** | 6:26 | The crossing at dawn. The pump assembles in D minor; the keysig flips to D major and the tempo flattens dead-steady — the water is out. Then the payoff the album has withheld for 21 minutes, machine-verified: island and mainland themes *simultaneous* in D, inverted both ways, downbeat-consonant, while hooks 1–4 return over the running 1985 pump, the choir opens 35→90, tubular bells peal `HOME` in morse, and an overdriven lead bends a true octave on RPN range 12 through a 32-bar crescendo. Everything falls away; solo piano plants the mainland's leap inside the island's incantation and lands the record's only melodic tonic — into a IV–I plagal Picardy and five tolls on D. D minor → D major, 84→100→62. |

Oracle-first, per the house method: every headline claim above exists as a
falsifiable check in the track's module (`movements/tNN_*.py`) — 135 green
rows across the album (the shared material proof, 45 generic checks, 89
track oracles), plus 15 per-track audio oracles measured on the rendered
waveforms. The pieces were composed *to pass them*.

See `README.md` for how to rebuild, verify, render and listen.
