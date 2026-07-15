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

To regenerate the corpus, see the sourcing notes in
`reference-midi/SOURCES.md` (local-only, not committed) or ask an agent to
re-fetch a curated flagship set per artist/soundtrack.
