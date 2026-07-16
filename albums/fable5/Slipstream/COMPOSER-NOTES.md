# Slipstream — composer notes (the compact exemplar digest)

Read THIS instead of re-reading Three-Sixty-One's 1,733-line module. It carries
the full module contract, the proven emitter patterns, and the trip-wires.
Your other reads: the HLD (globals + your track section), `engine.py` (the
toolkit — skim the docstring index then the helpers you use), `material.py`
(the album DNA). Do NOT re-derive any of this by exploring the repo — it is
authoritative here. Budget your iterations: aim for green in ≤ ~12 runs of
`python build.py --track N --check`.

## 1. Module contract (build.py/verify.py consume exactly these symbols)

```python
NUMBER = <int>; TITLE = "<registry>"; FILE = "<NN - Title.mid>"; SEED = <int>
COMMENT = "one-paragraph track description (goes in the MIDI file)"

PART = conductor.Part(
    NUMBER, TITLE, FILE,
    movements=[("I. Name", t0, t1), ...],       # contiguous; last t1 = END
    tempo_map=[(0.0, BPM), ...],
    time_signatures=[(0.0, 4, 4), ...],
    keysigs=[(0.0, sharps, minor)],             # e.g. (0.0, 1, 1) = E minor
    channels=[(ch, "name", program, volume, pan, reverb), ...],
    program_changes=[(9, 0.0, 1)],              # the V3 kit (keep)
    extra_markers=[(beat, "text"), ...],        # optional
    bank_selects=[(10,1),(11,1),(13,1),(14,1)], # toms/syn/riser set B + DRIVE_LEAD
)

BUILDERS = [_b_one_per_movement, ...]           # len == len(movements)

PROGRAM_WHITELIST: set[int]      # exactly the programs you use (setup + changes)
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

## 2. Oracle helpers (copy these into your module; they are t16's, proven)

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

def _phrases(ons, gap_ticks=_PPQ):
    starts, last = [], None
    for tick, _p, _v in ons:
        if last is None or tick - last > gap_ticks:
            starts.append(tick)
        last = tick
    return starts

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

Bend-aware consonance (only if your track bends over pinned downbeats):
`_bend_events`/`_frac_at`/`_eff` — see t16 lines 569-607 if truly needed.

## 3. Emitter patterns (adapt freely; keep jt=0 on pinned lanes)

```python
def _four_floor(sc, t0, t1, kick, clap, hat, open_hat, hat16=0):
    for b in range(int(round((t1 - t0) / 4.0))):
        bar = t0 + 4.0 * b
        for k in range(4):
            t = bar + k
            sc.note(9, 36, t, 0.25, kick, jt=0, jv=4)
            sc.note(9, 42, t, 0.2, hat, jt=0, jv=4)
            sc.note(9, 46, t + 0.5, 0.4, open_hat, jt=0, jv=4)
            if hat16:
                sc.note(9, 42, t + 0.25, 0.15, hat16, jt=0, jv=4)
                sc.note(9, 42, t + 0.75, 0.15, hat16, jt=0, jv=4)
        sc.note(9, 39, bar + 1.0, 0.3, clap, jt=0, jv=4)
        sc.note(9, 39, bar + 3.0, 0.3, clap, jt=0, jv=4)

def _snare_roll(sc, t0, t1, v0, v1):
    n = int(round((t1 - t0) / 0.25))
    for i in range(n):
        sc.note(9, 38, t0 + 0.25 * i, 0.2,
                int(en.lerp(v0, v1, i / max(1, n - 1))), jt=0, jv=3)

# Escalating fill schedule (velocity counts verified per 8-bar window):
FILL_SCHEDULE = [(beat, "A"), (beat, "D"), ...]   # shapes from material.FILL_LIB
def _build_fills(sc, t0, t1, vbump=0):
    for start, shape in FILL_SCHEDULE:
        if t0 <= start < t1:
            material.play_fill(sc, shape, start, vbump=vbump)

def _riser(sc, beat, dur, vel):          # ch13, GM119; window-pin in an oracle
    sc.note(13, 62, beat, dur, vel, jt=0, jv=0)

def _hits(sc, t0, t1, step, vel, root_of):   # ch12 GM55 orchestra hits
    t = t0
    while t < t1 - 1e-9:
        sc.note(12, root_of(t), t, 0.9, vel, jt=0, jv=3)
        t += step
```

Pads: `en.pad_block(sc, 1, t0, [en.triad(base, MODE, d) for d in degs],
span=8.0, size=4, lo=52, hi=76, vel=..., vel_end=...)`.
Bass 8ths: loop `sc.note(2, root, t0+0.5*i, 0.4, vel, jt=0, jv=3)`.
Antiphonal posts (ch3 L / ch4 R): short 3-note call at t, answer at t+2 —
see the HLD; keep notes ≤ 0.75 beats.

**Guitar lead (ch14, GM29 + CC0 bank 1 — the sustaining DRIVE_LEAD voice):**
- Note table `LEAD = [(onset, pitch, dur, vel), ...]`, emitted with jt=0.
- CC1 bloom over every held (≥ 2-beat) note:
  `en.cc_curve(sc, 14, 1, [(on, 0), (on + 0.35*dur, peak), (on + dur - 0.1, 0)], step=0.25)`
  with `peak = min(90, 34 + int(round(dur * 9)))`.
- CC68 legato pairs bracketing hammer-on runs: `sc.cc(14, 68, 90, on)` /
  `sc.cc(14, 68, 0, off)`.
- Marked bends as linear ramps of `sc.bend`, integer plateaus, zeroed before
  each movement boundary.
- Mix: volume ~118, reverb ~20, velocities 85+ in drops (T361 audibility fix).
Wing guitar (ch15): GM30 chugs (short low stabs, strictly under the lead) or
GM29+bank1 when it must sing. Both guitars centred (CC10 64).

**Choir (ch8):** vowel morphs `en.vowel_curve(sc, 8, [(beat, val), ...])` —
0=mm, ~45=oo, ≥80=ah. **Pad brightness:** `en.cc_curve(sc, 1, 74, [...])`
authored once for the whole timeline in your first builder.

## 4. Trip-wires (each cost a debug cycle on T361 — don't repeat them)

1. **RNG stream**: every `sc.note` call with jt/jv advances the shared seeded
   RNG. Emit in a deterministic order (tables, then loops); jt=0 lanes are
   immune. Never interleave emission order conditionally.
2. **Jitter leaks across boundaries**: a jt>0 note at a movement edge can land
   outside the builder's window → check_movement_bounds fails. Use jt=0 near
   edges or start ≥ 0.05 beats inside.
3. **Same-pitch knife edges**: back-to-back same-pitch notes where off == next
   on are fine (the engine clamps), but overlaps beyond that fail
   check_overlaps. Shave the first note's duration.
4. **DURATION_WINDOW includes the 2-beat end pad** at the final tempo.
5. **Average-RMS audio thresholds lie for sparse-but-loud sections** — in
   audio_checks compare dB over *trimmed inner windows* and keep margins ≥ 3 dB
   (see t16's audio_checks for shape; 4 checks max).
6. **CC0 bank select must precede the program change at the same tick** —
   PART.setup already orders this; don't author your own CC0 at tick 0.
7. **check_gaps** measures *global* silence: any moment with zero sounding
   notes anywhere for > 1.5 beats must be in GAP_WHITELIST.

## 5. Voice palette (all GM 0–119 are modeled in ferrosintesis v0.21; these
are the catalog-proven colors — prefer them)

- Leads: 81 saw (the soar), 80 square, 29/30 guitars (the duo), 61 brass
  section, 56 trumpet, 73 flute, 71 clarinet, 40 violin.
- Beds: 89 warm pad, 88 new-age, 91 choir pad, 95 sweep pad, 48/49 strings,
  52 choir aahs / 53 oohs.
- Motion/color: 114 steel drums, 46 harp, 11 vibes, 9 glockenspiel,
  8 celesta, 98 crystal, 4 e-piano, 0 piano, 45 pizzicato, 104 sitar.
- Low: 38/39 synth bass, 33 fingered bass, 35 fretless.
- Percussion melodics: 117 melodic toms, 118 synth drum, 119 reverse cymbal,
  116 taiko, 47 timpani, 115 woodblock, 55 orchestra hit.
- Alt banks (CC0=1): DRIVE_LEAD on 29; percussion set B on 114/117/118/119.

## 6. Workflow

```
cd "<album dir>"
python build.py --track N --check     # in-memory oracles (fast loop)
python build.py --track N             # writes midi/<FILE>
python build.py --track N --verify    # file-backed + all oracles
```
Never plain `python build.py` (other modules may not exist). Green means:
the nine generic checks + material + every one of your oracles PASS.
