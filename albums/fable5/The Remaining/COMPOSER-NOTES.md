# The Remaining — composer notes (the compact exemplar digest)

Read THIS plus the HLD ("wrk_docs/2026.07.18 - HLD - The Remaining album
(five elegies).md" — the globals in §1 and YOUR track's section in §2) and
`material.py` (the album DNA — import it, never re-type its data).  Skim
`engine.py`'s docstring index, then only the helpers you use.  Do NOT
re-derive any of this by exploring the repo — it is authoritative here.
Budget your iterations: aim for green in ≤ ~12 runs of
`python3 build.py --track N --check`.

**The idiom is Max Richter (The Leftovers score): slow, patient, devastating.**
Restraint IS the wow here: velocities mostly 35-75, silence is scored, builds
are additive (add a voice per cycle, never a drum fill), and every sustained
line breathes with CC11.  No drums anywhere on this album (T3's pulse is
synth bass; its "percussion" is one woodblock morse lane).  Rubato is
mandatory: a flat tempo map is a bug (except T3, which is deliberately
metronomic — the machine searching).

## 1. Module contract (build.py/verify.py consume exactly these symbols)

```python
NUMBER = <int>; TITLE = "<registry>"; FILE = "<NN - Title.mid>"; SEED = <int>
COMMENT = "one-paragraph track description (goes in the MIDI file)"

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Name", t0, t1), ...],       # contiguous; last t1 = END
    tempo_map=[(0.0, BPM), ...],
    time_signatures=[(0.0, 4, 4), ...],
    keysigs=[(0.0, sharps, minor)],             # D minor = (0.0, -1, 1)
    channels=[(ch, "name", program, volume, pan, reverb), ...],
    program_changes=[(ch, beat, prog), ...],    # optional mid-track swaps
    extra_markers=[(beat, "text"), ...],        # optional
    bank_selects=[],                            # default voices only here
)

BUILDERS = [_b_one_per_movement, ...]           # len == len(movements)

PROGRAM_WHITELIST: set[int]      # exactly the programs you use
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
movement markers), programs (whitelist), bank-select-before-program, pan
(CENTERED_CHANNELS emit only 64), ranges, gaps (> 1.5 beats unscored fails),
same-pitch overlaps, bend hygiene (recentred ±0.02 at every movement boundary),
movement bounds (each builder's note-ons inside its own movement; CC exempt).

## 2. Oracle helpers (copy these into your module; proven on Slipstream)

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

(For 3/4 tracks change `_bar_sums`' `4 * _PPQ` to `3 * _PPQ`.)

## 3. Emitter patterns (adapt freely; keep jt=0 on oracle-pinned lanes)

**The ground with sighs** (block-chord guise; one chord per 4-beat bar):
```python
def _ground_bar(sc, ch, bar_t0, base, i, vel, major=False):
    sus_tab = material.MAJOR_SUSPENSIONS if major else material.SUSPENSIONS
    root = material.ground_roots(base, major)[i]      # re-octave as needed
    triad = material.ground_triad(base, i, major)
    s, r = sus_tab[i]
    sc.note(ch, root + s, bar_t0, 1.0, vel + 6, jt=0, jv=2)       # the sigh
    sc.note(ch, root + r, bar_t0 + 1.0, 3.0, vel, jt=0, jv=2)     # resolves
    for p in triad:                                                # the body
        if p % 12 not in ((root + s) % 12, (root + r) % 12):
            sc.note(ch, p, bar_t0, 4.0, vel - 8, jt=0, jv=2)
```
(Voice it yourself per register — the pattern that matters: suspension ON the
barline, resolution on beat 2, held body underneath.)

**The departure figure**: `material.play_figure(sc, 0, bar, root, minor=True,
vel=52, holes=material.HOLES or frozenset())` — one call per bar, roots from
the ground walk.  Piano pedals per bar: `en.sustain(sc, 0, bar, bar + 3.9)`;
una corda for intimate movements: `en.soft_pedal(sc, 0, t0, t1)`.

**The theme**: `material.play_theme(sc, ch, t0, base, stretch=..., jt=0)` —
jt=0 ALWAYS (every statement is oracle-pinned).  `arrival=True` is T5-only.

**String lines**: long notes + `en.expr_curve(sc, ch, [(on, 40), (peak_t, 96),
(off, 30)], step=0.5)` per phrase; `en.vibrato(sc, ch, on + dur*0.3,
dur*0.7, depth=0.15..0.35)` on notes >= 2 beats (depth grows across the
track); bend appoggiatura = `en.bend_ramp` from -0.5 semis into the note over
~0.15 beats, then recentre (`sc.bend(ch, t, 0.0)`) BEFORE the movement ends.
Aftertouch swell on held cello notes: `en.at_curve(sc, ch, [(on, 0),
(on + dur*0.6, 70), (off, 0)])`.

**Choir**: `en.vowel(sc, ch, val, beat)` / `en.vowel_curve` — 0=mm, ~45=oo,
>=80=ah.  T4 must stay < 60; T5 III opens to >= 80.

**Sub drone / organ pedal**: very long low notes (8-16 beats), vel 30-45,
re-struck with overlap-safe re-onsets at phrase starts, CC11 arcs so it
breathes.

**Rubato**: tempo_map with phrase-end dips, e.g. 8-bar phrases at 66 with
`(phrase_end - 2, 62), (phrase_end, 66)` pairs.  3-6 bpm dips; deeper
(8-10) at movement seams.  T3: exactly one tempo event (the point).

## 4. Trip-wires (Slipstream's five cost debug cycles; +3 are this album's)

1. **RNG stream**: every `sc.note` call with jt/jv advances the shared seeded
   RNG. Emit in a deterministic order (tables, then loops); jt=0 lanes are
   immune. Never interleave emission order conditionally.
2. **Jitter leaks across boundaries**: a jt>0 note at a movement edge can land
   outside the builder's window → check_movement_bounds fails. Use jt=0 near
   edges or start >= 0.05 beats inside.
3. **Same-pitch knife edges**: back-to-back same-pitch notes where off == next
   on are fine (the engine clamps), but overlaps beyond that fail
   check_overlaps. Shave the first note's duration (0.45-quaver gate on the
   figure already does this).
4. **DURATION_WINDOW includes the 2-beat end pad** at the final tempo.
5. **check_gaps** measures *global* silence: any moment with zero sounding
   notes anywhere for > 1.5 beats must be in GAP_WHITELIST.  On THIS album
   silences are scored on purpose — whitelist them deliberately, and T1's
   departure silence is REQUIRED to be exactly one whitelisted 2.5-beat hole.
6. **Pedal is not sound**: CC64 does not extend a note for check_gaps —
   the *note events* must cover the bar.  Keep piano note durations honest
   (3.5-4.0 beats under pedal), don't rely on the pedal to fill silence.
7. **Low velocities disappear in render**: below vel ~30 a solo string is
   inaudible under the bus.  pp = 35-45, not 20.  (analyze.py checks will
   catch you; don't compose inaudible.)
8. **The waiting-tone discipline**: tracks 1-4 may NEVER sound degree 1 as a
   theme ending — if you quote the theme, it ends on degree 2.  Cadences on
   a bare D in the BASS are fine (the drone is not the theme); the theme's
   melodic voice landing on D is T5's single privilege.

## 5. Voice palette (catalog-proven; prefer these)

- Core: 0 piano (Salamander LA layer — the album's centre), 40 violin,
  41 viola, 42 cello, 43 contrabass, 48/49 string ensembles.
- Colour: 8 celesta (the music box), 46 harp, 14 tubular bells,
  9 glockenspiel, 52 choir aah / 53 ooh (vowel-morphable), 19 church organ.
- Electronics: 89 warm pad, 95 sweep pad, 98 crystal, 38/39 synth bass.
- Utility: 47 timpani, 115 woodblock (the morse lane), 45 pizzicato.
- NO guitars, NO drum kit, NO brass on this album.

## 6. Workflow

```
cd "albums/fable5/The Remaining"
python3 build.py --track N --check     # in-memory oracles (fast loop)
python3 build.py --track N             # writes midi/<FILE>
python3 build.py --track N --verify    # file-backed + all oracles
```
Never plain `python3 build.py` (other modules may not exist). Green means:
the nine generic checks + material + every one of your oracles PASS.
