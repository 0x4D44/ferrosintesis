#!/usr/bin/env bash
# Render every album MIDI to audio/*.wav, 4 renders in parallel.
# Dev-only helper; audio/ and *.wav are gitignored repo-wide.
set -u
BIN="${FERRO_BIN:-$(cd "$(dirname "$0")/../../.." && pwd)/target/release/ferrosintesis}"
# Windows builds carry the .exe suffix; POSIX builds do not. Probe rather than
# hardcode, so one script serves both. FERRO_BIN still overrides either way.
[ -x "$BIN" ] || BIN="$BIN.exe"
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
        return 1
    fi
}
export -f render
export BIN
ls midi/*.mid | xargs -P 4 -I{} bash -c 'render "$@"' _ {}
