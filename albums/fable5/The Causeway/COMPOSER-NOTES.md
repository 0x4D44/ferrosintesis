# The Causeway — composer notes (the compact exemplar digest)

Read THIS plus the HLD ("wrk_docs/2026.07.18 - HLD - The Causeway album
(five crossings).md" — the globals in §1 and YOUR track's section in §2) and
`material.py` (the album DNA — import it, never re-type its data).  Skim
`engine.py`'s docstring index, then only the helpers you use.  Do NOT
re-derive any of this by exploring the repo — it is authoritative here.
Budget your iterations: aim for green in <= ~12 runs of
`python build.py --track N --check`.

**The idiom is a duet of shores.** The ISLAND writes late-ABBA ice — 
incantatory repeated notes, off-beat pushes, sequenced chill — inside
Enigma/Delerium weather (breath flutes, vowel choirs, echo throws).  The
MAINLAND writes McCartney warmth — the bass is a lead singer, piano pump,
clavinet strut, suite-form pivots that CHANGE mid-track — with Oldfield
patience (additive builds, tubular bells).  Hooks are the point: your track's
HOOKS[n] cell should be stated often enough to earworm (>= 6 times), varied
in register and instrument, never varied in interval or rhythm (only
transposition and uniform stretch are legal — `material.find_statements`
must FIND every statement).  Grooves are tight (jt=0 or jt<=6 on drums/bass),
melodies breathe (CC11 arcs), and the tempo map carries the tide.

## 1. Module contract (build.py/verify.py consume exactly these symbols)

```python
NUMBER = <int>; TITLE = "<registry>"; FILE = "<NN - Title.mid>"; SEED = <int>
COMMENT = "one-paragraph track description (goes in the MIDI file)"

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Name", t0, t1), ...],       # contiguous; last t1 = END
    tempo_map=[(0.0, BPM), ...],
    time_signatures=[(0.0, 4, 4), ...],
    keysigs=[(0.0, sharps, minor)],             # E minor = (0.0, 1, 1)
    channels=[(ch, "name", program, volume, pan, reverb), ...],
    program_changes=[(ch, beat, prog), ...],    # optional mid-track swaps
    extra_markers=[(beat, "text"), ...],        # optional
    bank_selects=[(ch, val), ...],              # CC0 alt-bank opt-ins
)

BUILDERS = [_b_one_per_movement, ...]           # len == len(movements)

PROGRAM_WHITELIST: set[int]      # exactly the programs you use (ch9 exempt)
CENTERED_CHANNELS: set[int]      # every channel that must hold CC10 64
NOTE_RANGES: dict[int, tuple[int, int]]   # per-channel [lo, hi] pitch bounds
GAP_WHITELIST: list[tuple[float, float]]  # scored silences (unscored cap 1.5 beats)
BEND_EXEMPT: set[int]            # channels with STATIC bend offsets (usually empty)
DURATION_WINDOW: tuple[float, float]      # FILE seconds (write() pads 2 beats)
BOUNDS_WHITELIST: list[tuple[int, float, float]]  # (ch, lo, hi) seam carry-overs

def oracles(sc, info, spans) -> list[tuple[str, list[str]]]: ...
def audio_checks(ctx) -> list[tuple[str, list[str]]]: ...   # optional, 2-4 checks
```

Generic checks that run automatically (verify.py): structure (duration window,
track count = 1 + len(channels), file-vs-Score note parity, tempo/keysig grids,
movement markers), programs (whitelist; ch9 drums exempt), bank-select-before-
program, pan (CENTERED_CHANNELS emit only 64), ranges, gaps (> 1.5 beats
unscored fails), same-pitch overlaps, bend hygiene (recentred +-0.02 at every
movement boundary), movement bounds (each builder's note-ons inside its own
movement; CC exempt).

## 2. The album laws (every track must encode these as oracles)

Import material; use its searchers — never hand-roll pattern matching.

1. **Convergence** — your theme statements' implied tonics must match
   `material.convergence_pcs(NUMBER)`:
   `material.island_tonic_pc(first_pitch)` / `mainland_tonic_pc(first_pitch)`.
2. **No overlap** (T1-T4) — 
   `material.overlapping_pairs(theme_statements(sc,'island'),
   theme_statements(sc,'mainland')) == []`.  T3 additionally requires
   call-and-answer adjacency (gap <= 2 beats between paired statements).
   T5 III REQUIRES overlap, downbeat-consonant, plus the inversion windows.
3. **End-degree discipline** — every island statement hangs (its last note is
   theme-final by construction: use `material.play_island`, never a hand
   copy); NOTHING in T1-T4 may state the FUSION phrase, and no theme-family
   line may end on the local tonic.  T5 IV states FUSION exactly once — the
   album's only melodic tonic landing.
4. **Hook density** — HOOKS[NUMBER] found >= 6 times across the track
   (`material.find_statements` per channel, any transposition/stretch).
   T5 III also restates HOOKS[1..4] (>= 1 each inside its window).
5. **Protagonist bass** — on your named bass channel: stepwise ratio >= your
   pinned floor (default 0.50; T2 may pin 0.42), range >= 19 semitones, and
   your hook stated >= 2 times IN THE BASS inside CHORUS_SPANS.  T4 exempt.
6. **Doubled thumb** — inside CHORUS_SPANS every bass note-on shadowed at
   +12 on your partner channel (+-10 ticks), coverage >= 0.80; outside the
   spans coverage < 0.30.  T4 exempt.
7. **Breath herald** — before your pinned groove movement: >= 2 bars where
   ONLY the herald channel (pan flute 75 / shakuhachi 77) sounds, playing
   your hook's first 3 notes under a strictly-rising CC11 swell.  T4 exempt.
8. **Morse** — `material.play_morse(sc, ch, t0, NUMBER, pitch)` on your
   track's rotating timbre (MORSE_PROGRAMS[NUMBER]) >= 1 full statement;
   oracle re-derives the expected (onset, dur) grid from material.
9. **Tide-breath** — build rubato from `material.tide_breath(...)`; oracle
   asserts the movement's tempo events swell (>= 2 cycles) — EXCEPT the two
   still points (T4 II exactly one tempo event in its window; T5 II-III
   wiggle <= 1 bpm).  A flat map elsewhere is a bug.
10. **Cadence law** — pin your cadence windows and run
    `material.cadence_failures(sc, bass_ch, lo, hi, downbeat, tonic_pc)`
    on each (T1-T4).  T5's final cadence is IV-I plagal + Picardy (own
    oracle: bass G->D, F# present, no C-natural in the final window).
11. **Shore pans** — island-pole channels at SHORE_PANS[N][0], mainland-pole
    at SHORE_PANS[N][1], neutral channels centered (64).  Declare every
    non-shore channel in CENTERED_CHANNELS; shore channels get their seat in
    the channels table (one CC10 at setup — do NOT also list them centered).
12. **Tolls** — end with `material.play_tolls(sc, bells_ch, t0, NUMBER,
    pitch)` (pitch pc = your island tonic); after toll 1's onset the only
    note-ons anywhere are the remaining tolls.  Whitelist the toll tail in
    GAP_WHITELIST if gaps between tolls exceed 1.5 beats.
13. **Vowel clock** — choir CC70 <= VOWEL_CAPS[NUMBER] everywhere; T3 must
    also RISE (8-bar-window means non-decreasing); T5's final movements rise
    monotonically and reach >= VOWEL_FLOOR_T5.

## 3. Oracle helpers (copy these into your module; proven on Slipstream)

```python
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_PPQ = en.PPQ

def _tick(beat): return max(0, int(round(beat * _PPQ)))

def _note_ons(sc, ch):
    out = []
    for tick, _prio, data in sc.events.get(ch, []):
        if (data[0] & 0xF0) == 0x90 and data[2] > 0:
            out.append((tick, data[1], data[2]))
    return sorted(out)

def _note_spans(sc, ch):
    pending, out = {}, []
    for tick, _prio, data in sorted(sc.events.get(ch, []), key=lambda e: (e[0], e[1])):
        s = data[0] & 0xF0
        if s == 0x90 and data[2] > 0:
            pending.setdefault(data[1], []).append(tick)
        elif s == 0x80 or (s == 0x90 and data[2] == 0):
            q = pending.get(data[1])
            if q:
                out.append((q.pop(0), tick, data[1]))
    return sorted(out)

def _cc_lane(sc, ch, num):
    return sorted((t, d[2]) for t, _p, d in sc.events.get(ch, [])
                  if (d[0] & 0xF0) == 0xB0 and d[1] == num)

def _bar_sums(sc):
    out = {}
    for ch in sc.events:
        for tick, p, v in _note_ons(sc, ch):
            out[tick // (4 * _PPQ)] = out.get(tick // (4 * _PPQ), 0.0) + v
    return out

def _mean_barsum(sums, lo, hi):
    bars = range(int(lo // 4), int(hi // 4))
    return sum(sums.get(b, 0.0) for b in bars) / max(1, len(bars))

def _sounding(sc, ch, tick, eps=24):
    return [p for on, off, p in _note_spans(sc, ch)
            if on <= tick - eps and off >= tick + eps]
```

(For 6/8 movements convert with the movement's own bar length, and remember
`material.find_statements` works in ticks via `material.note_ons(sc, ch)`.)

## 4. Emitter patterns (adapt freely; keep jt=0 on oracle-pinned lanes)

**Themes / hooks / morse / tolls**: ONLY via material.play_island /
play_mainland / play_fusion / play_hook / play_morse / play_tolls — jt=0
always; a hand-typed copy that drifts by one quaver will not be FOUND by the
searcher and your own oracle will fail.  Keep the statement channel
monophonic while a statement sounds (the searcher matches consecutive runs).

**The pump** (1985 engine): piano left hand octave quavers, jt=0, vel 66-84
with accents on 1 and the and-of-2; `en.sustain(sc, ch, bar, bar+3.9)` per
bar; right hand answers off-beats.

**The strut** (Vandebilt engine): clavinet HOOK cell + CC68 hammer-on pairs
(`sc.cc(ch, 68, 127, t)` before the slurred note, 0 after), muted-guitar
chops with `en.wah(...)` (CC74 LFO), fretless bass with
`en.portamento_on/off` + short `en.bend_ramp` scoops recentred by movement
end, brass stabs vel 90+ with `en.at_curve` rasp.

**String/choir lines**: long notes + `en.expr_curve(sc, ch, [(on, 40),
(peak_t, 96), (off, 30)], step=0.5)` per phrase; `en.vibrato(sc, ch,
on + dur*0.3, dur*0.7, depth=0.15..0.35)` on notes >= 2 beats (depth grows
across the track); choir vowels via `en.vowel` / `en.vowel_curve` (0=mm,
~45=oo, >=80=ah) under YOUR track's cap.

**Sequencers** (the ice): synth bass 38/39, jt=0, 16ths or 8ths; CC74 arcs
on pads; crystal 98 shimmer may `en.autopan` ONLY if the module names it
(exclude from CENTERED_CHANNELS, keep its volume low — mono-collapse).

**Echo throws**: `en.echo_throw(sc, ch, t)` (CC94 spike) on phrase tails —
Enigma punctuation, use sparingly (2-6 per track).

**Drums** (ch9): GM keys 35/36 kick, 38/40 snare, 42/44/46 hats, 49/57
crashes, 51/53 ride; brush kit = Program Change 40 on ch9 (a
`program_changes` entry), swap back with another entry.  Grooves jt<=6,
fills jt<=10.  Drum notes need no PROGRAM_WHITELIST entry.

**Rubato**: movement maps from `material.tide_breath(base, t0, t1)`;
deepen seams by appending explicit dips.  Still points per the law table.

## 5. Trip-wires (Slipstream/Remaining's five cost debug cycles; +4 ours)

1. **RNG stream**: every `sc.note` call with jt/jv advances the shared seeded
   RNG. Emit in a deterministic order (tables, then loops); jt=0 lanes are
   immune. Never interleave emission order conditionally.
2. **Jitter leaks across boundaries**: a jt>0 note at a movement edge can land
   outside the builder's window -> check_movement_bounds fails. Use jt=0 near
   edges or start >= 0.05 beats inside.
3. **Same-pitch knife edges**: back-to-back same-pitch notes where off == next
   on are fine (the engine clamps), but overlaps beyond that fail
   check_overlaps. Shave gate to 0.9-0.95 on repeated-note lanes (the island
   incantation and the pump are full of them).
4. **DURATION_WINDOW includes the 2-beat end pad** at the final tempo.
5. **check_gaps** measures *global* silence: any moment with zero sounding
   notes anywhere for > 1.5 beats must be in GAP_WHITELIST — including
   between your tolls and before a breath herald.
6. **Statement findability**: an accompaniment note interleaved on a channel
   DURING a theme/hook statement breaks the consecutive-run searcher — keep
   statement channels clean while stating (put pads on another channel).
7. **Low velocities disappear in render**: below vel ~30 a line is inaudible
   under the bus. pp = 35-45, not 20. Morse lanes: vel >= 50.
8. **The leading-tone ban is global on T1-T4 cadence windows** — including
   passing tones on ANY channel inside the pinned window. Place windows
   where your counterpoint truly avoids the pc, or move the window.
9. **Bank-select order**: any CC0 entry must precede the program change at
   the same tick — use PART.bank_selects + channels, never a late sc.cc(0).

## 6. Voice palette (catalog-proven; prefer these)

- Songcraft core: 0 piano (Salamander LA), 4 Rhodes, 5 FM EP, 7 clavinet
  (sampled; CC0 alt = modeled contrast), 33 fingered bass, 35 fretless
  ("mwah"), guitars 24/25/27/28/29/30 (28 = palm mute).
- Weather: 52/53 choir (vowel-morphable), 73 flute, 75 pan flute,
  77 shakuhachi, 89 warm pad, 95 sweep pad, 98 crystal, 38/39 synth bass.
- Colour: 8 celesta, 10 music box, 11 vibraphone, 12 marimba, 14 tubular
  bells, 16-19 organs (CC1 Leslie on drawbars), 22 harmonica, 46 harp,
  47 timpani, 55 orchestra hit, 108 kalimba, 115 woodblock.
- Sections: 48/49 strings, 40/42 solo strings, 56/57/60/61 brass, 65/66 sax.
- ch9: GM kit (sampled) + brush kit via Program 40.  CC0 banks: tam-tam at
  14, second percussion set at 112-119, legacy drawbar 19.

## 7. Workflow

```
cd "albums/fable5/The Causeway"
python build.py --track N --check     # in-memory oracles (fast loop)
python build.py --track N             # writes midi/<FILE>
python build.py --track N --verify    # file-backed + all oracles
```
Never plain `python build.py` (other modules may not exist). Green means:
the nine generic checks + material + every one of your oracles PASS.
Write your module in SEVERAL SMALL Write/Edit chunks (a single giant write
dies on the output cap — repo lesson), and keep the movements/ file total
under ~950 lines.
