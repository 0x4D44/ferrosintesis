#!/usr/bin/env bash
# Render the GM0 alternate-bank audition matrix: each bank x {torture-test, the
# opening of Tubular Bells (piano soloed)}, plus the pure model (--no-samples) as
# the source-vs-blend reference. Outputs are git-ignored WAVs under renders/.
#
# Bank 0 = the default Salamander grand (no CC0 injected). Banks 1.. select the
# alternate sample crates via CC0 on the piano channel (altbank::make). Add a bank
# to BANKS as each candidate lands.
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

# "bank:label" — extend as candidates land.
BANKS=(
  "0:salamander"
  "1:vcsl-steinwayb"
  "2:vcsl-kawai"
  "3:headroom"
  "4:musescore-grand"
  "5:dark-salamander"
  "6:vsco-upright-old-gm0"
  "7:ydp-bright-grand"
  "8:honkytonk"
)

# Lever B/C demo (CC0 tens digit: 1=wide blend, 2=bright model). A focused set on a
# warm source (upright, 6) and the bright grand (ydp, 7) so the levers are audible.
BC_BANKS=(
  "16:upright+wideblend"
  "26:upright+brightmodel"
  "17:ydp+wideblend"
  "27:ydp+brightmodel"
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

for b in "${BANKS[@]}";    do render_bank "${b%%:*}" "${b#*:}"; done
for b in "${BC_BANKS[@]}"; do render_bank "${b%%:*}" "${b#*:}"; done

# Model-only references (--no-samples): normal model, and the C bright model (tens=2).
"$BIN" "$OUT/torture.mid" -o "$OUT/torture_model.wav" --no-samples -q
python "$HERE/prep_audition.py" "$TB" -o "$OUT/_tbm.mid" --bank 0 --channel 0 --max-seconds "$TRIM" >/dev/null
"$BIN" "$OUT/_tbm.mid" -o "$OUT/tubularbells_model.wav" --no-samples --solo 0 -q
# bright model alone: CC0=20 (tens=2 bright, ones=0) + --no-samples
python "$HERE/prep_audition.py" "$OUT/torture.mid" -o "$OUT/_tmb.mid" --bank 20 --channel 0 >/dev/null
"$BIN" "$OUT/_tmb.mid" -o "$OUT/torture_model-bright.wav" --no-samples -q
python "$HERE/prep_audition.py" "$TB" -o "$OUT/_tbmb.mid" --bank 20 --channel 0 --max-seconds "$TRIM" >/dev/null
"$BIN" "$OUT/_tbmb.mid" -o "$OUT/tubularbells_model-bright.wav" --no-samples --solo 0 -q
echo "rendered model refs (normal + bright)"

rm -f "$OUT"/_*.mid
echo "done -> $OUT"
ls -la "$OUT"/*.wav
