# Listening Library

This tree holds the tagged Opus listening copies. They are **git-ignored build
output**, not committed — a fresh clone has none, so you generate them.

Build them from the repo root with one command, then drag `listening/` into an
audio player to browse the rendered albums by artist and album:

```powershell
cargo run --release -p render-catalog                        # every album
cargo run --release -p render-catalog -- --album "Sub Rosa"  # just one album
```

The source albums, MIDI files, manifests, and composition engines live under
`albums/`; synth showcase demos live under `demos/`. Rendering needs a Rust
toolchain and `ropusenc` on PATH (from the sibling `ropus` project).
