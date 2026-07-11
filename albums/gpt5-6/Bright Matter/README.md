# Bright Matter

Five original, deterministic MIDI compositions by **GPT-5.6**, written as a compact
progressive-electronic album. The shared harmonic engine is **vi–V–ii–I** — the
requested **6–5–2–1** progression — but each track gives it a different physical
identity: an orbit, a runway, gravity, delayed city light, and finally all four ideas
in counterpoint.

The album takes the large-form strengths of “Three-Sixty” as a design challenge:
upbeat hooks, genuine negative-space contrasts, two build/drop cycles with the second
larger, transient stereo motion, orchestral colour, and finales that recombine earlier
material rather than merely getting louder. All melodies, riffs, harmony, and
arrangements here are new.

## Files

- `tracks/` — one composition module per track plus shared arrangement/oracle helpers.
- `engine.py` and `material.py` — deterministic standard-library MIDI engine and the
  album's four original hook cells.
- `midi/` — five finished Standard MIDI Files, committed as reproducible artifacts.
- `verify.py` — score-side oracles for structure, dynamics, controllers, stereo
  discipline, exact 6–5–2–1 bass roots, and the four-hook finale.
- `analyze.py` — optional render-side WAV checks for contrast, mono safety, silence,
  headroom, and post-hush impact.
- `lyrics/` — section-timed instrumental listening guides embedded as Opus `LYRICS`
  metadata when `render_opus.py` is run.
- `album_manifest.json` — durations, concepts, tags, and timed section map.
- `ALBUM.md` — track-by-track compositional notes.

## Rebuild and verify

From this directory:

```bash
python build.py
python build.py --verify
python build.py --verify --track 5
```

The build uses only the Python standard library and fixed seeds. It performs an
independent second build for every track and refuses to continue unless the MIDI is
byte-identical. The complete album currently runs **24:20**.

## Render and audio-check

From the repository root, after building `ferrosintesis`:

```bash
python render_opus.py --album "Bright Matter"
```

To inspect intermediate WAV renders before encoding:

```bash
python "albums/gpt5-6/Bright Matter/analyze.py" <wav-directory>
```

The committed source and MIDI are the canonical composition. Listening copies are
reproducible from those files through the repository synth.
