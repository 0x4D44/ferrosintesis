#!/usr/bin/env bash
# Render the GM0 alternate-bank audition matrix: each bank x {torture-test, the
# opening of Tubular Bells (piano soloed)}, plus the pure model (--no-samples) as
# the source-vs-blend reference. Outputs are git-ignored WAVs under renders/.
#
# Bank 0 = the default B1 upright (Arthur's own Yamaha B1, no CC0 injected). Banks
# 1.. select the alternate sample crates via CC0 on the piano channel
# (altbank::make). Add a bank to BANKS as each candidate lands.
#
#   bash tools/gm0-audition/render_audition.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
BIN="$ROOT/target/release/ferrosintesis"
[ -x "$BIN" ] || BIN="$BIN.exe"
# Reference MIDIs live only in the (untracked) main-clone test-corpus.
TB="${TB_MIDI:-/d/language/midi-music/test-corpus/reference-midi/mike-oldfield/01-tubular-bells-part-one.mid}"
OUT="$HERE/renders"; mkdir -p "$OUT"
TRIM="${TRIM_SECONDS:-30}"

# "bank:label" = the CC0 value injected on the piano channel and its label. These
# are the GM 0 CC0 alternates the program-0 torture MIDI can reach via altbank::make
# (raw CC0, no tens-digit encoding): 0 injects nothing (the GM0 default voice, the
# B1 upright), 1.. select the alternate sample crates. Extend as candidates land.
#   (Refreshed 2026.07.24 to the real altbank map — the old array + the tens-digit
#    "lever B/C" set encoded a CC0 scheme the code no longer has.)
#   (Renumbered 2026.07.26 when the B1 upright became the CC0=0 GM0 default; the
#    old default-Salamander voice moved to CC0=2.)
BANKS=(
  "0:b1-upright-default"
  "1:vsco-upright"
  "2:salamander"
  "3:vcsl-steinwayb"
  "4:headroom"
  "5:dark-salamander"
)

echo "binary: $BIN"
python "$HERE/make_torture_midi.py" -o "$OUT/torture.mid" >/dev/null

render_bank () { # <bank-num> <label>
  local num="$1" lbl="$2"
  python "$HERE/prep_audition.py" "$OUT/torture.mid" -o "$OUT/_t${num}.mid" --bank "$num" --channel 0 >/dev/null
  "$BIN" "$OUT/_t${num}.mid" -o "$OUT/torture_${num}_${lbl}.wav" -q
  python "$HERE/prep_audition.py" "$TB" -o "$OUT/_tb${num}.mid" --bank "$num" --channel 0 --max-seconds "$TRIM" >/dev/null
  "$BIN" "$OUT/_tb${num}.mid" -o "$OUT/tubularbells_${num}_${lbl}.wav" --solo 0 -q
  echo "rendered bank $num ($lbl)"
}

for b in "${BANKS[@]}"; do render_bank "${b%%:*}" "${b#*:}"; done

# Model-only reference (--no-samples): the pure GM0 model, as the source-vs-blend A/B.
"$BIN" "$OUT/torture.mid" -o "$OUT/torture_model.wav" --no-samples -q
python "$HERE/prep_audition.py" "$TB" -o "$OUT/_tbm.mid" --bank 0 --channel 0 --max-seconds "$TRIM" >/dev/null
"$BIN" "$OUT/_tbm.mid" -o "$OUT/tubularbells_model.wav" --no-samples --solo 0 -q
echo "rendered model ref"

rm -f "$OUT"/_*.mid
echo "done -> $OUT"
ls -la "$OUT"/*.wav
