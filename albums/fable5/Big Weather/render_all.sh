#!/usr/bin/env bash
# Render every album MIDI to audio/*.wav, 4 renders in parallel.
# Dev-only helper; audio/ and *.wav are gitignored repo-wide.
set -u
BIN="D:/worktrees/midi-music/20260711-DEV-HUM-rockpop-ten-track-album/target/release/ferrosintesis.exe"
cd "$(dirname "$0")" || exit 1
mkdir -p audio
render() {
    local f="$1"
    local b
    b=$(basename "${f%.mid}")
    if "$BIN" "$f" -o "audio/$b.wav" -q; then
        echo "done: $b"
    else
        echo "FAIL: $b"
    fi
}
export -f render
export BIN
ls midi/*.mid | xargs -P 4 -I{} bash -c 'render "$@"' _ {}
