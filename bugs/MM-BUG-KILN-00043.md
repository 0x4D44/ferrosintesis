# MM-BUG-KILN-00043 — GM7 clavinet's baked decay is ~3x too fast: its body level reads 13.4 dB under both references while its attack level is correctly placed (a 1.6 s sample wall also exists, but measures inaudible)

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler
- **Raised:** 2026-07-22
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260726T221402Z-p9812-n155597100-c8
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00043-run-fix-20260726T221402Z-p9812-n155597100-c8
- **Owner base:** dcc6db48b10d4eeb34abd8e9c5b9afa3e3a44266
- **Owner fingerprint:** -
- **Owner since:** 2026-07-26T22:14:02Z
- **Owner until:** 2026-07-26T22:59:02Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) during M-CAL v3 reference-panel triage; measured on both references and code-confirmed to the bake constant) → Blocked (2026-07-25, Codex GPT-5.6-Sol; removing the 1.6 s wall must be coupled to a new GM7 decay law, whose GM-reference-versus-physical target and runtime-loop design require Arthur's audition decision) → Open (2026-07-26, unblocked by Arthur; approved the GM-reference decay idiom, a runtime-looped sampled sustain with an output-time decay envelope, roughly 5 s low/mid tapering to 3.3 s at the top, and fallback alignment)

## Observation

### Symptom

In the M-CAL v3 two-reference run (Roland SC-55mkII and Yamaha S-YXG50, both via
`mdmidiemu`), GM7 Clavinet is the most emphatic and best-agreed outlier of the whole
128-program sweep. Where each engine places its own clavinet in its own balance
(program body level minus that engine's median body level over all 128 programs):

| | int (own balance) |
|---|---|
| ferrosintesis | **-18.30 dB** |
| SC-55mkII | -4.95 dB |
| S-YXG50 | -4.79 dB |

The two references agree to **0.16 dB**; ferro sits **13.35 / 13.51 dB** below them.

**But ferro's clavinet is not quiet — it is short.** Recomputing the identical
self-referential statistic on note **peak** instead of body-median:

| | int on PEAK (own balance) |
|---|---|
| ferrosintesis | **-0.15 dB** |
| SC-55mkII | -3.24 dB |
| S-YXG50 | +0.48 dB |

Ferro's clavinet *attack* is right where both references put theirs, to about a
decibel. The entire 13.4 dB body gap is **decay rate**. Over the 0.8 s from block
b0 to b8 of a held note (v110):

| probe key | ferro drop | SC-55 drop | S-YXG50 drop | ferro t60 | SC-55 t60 | S-YXG50 t60 |
|---|---|---|---|---|---|---|
| 48 (C3)  | 25.2 dB | 4.5 dB  | 9.2 dB  | 1.90 s | 10.7 s | 5.2 s |
| 53 (F3)  | 25.2 dB | 5.0 dB  | 13.4 dB | 1.91 s | 9.7 s  | 3.6 s |
| 58 (A#3) | 26.2 dB | 5.4 dB  | 12.1 dB | 1.83 s | 8.9 s  | 4.0 s |
| 63 (D#4) | 34.8 dB | 6.9 dB  | 11.4 dB | 1.38 s | 7.0 s  | 4.2 s |
| 68 (G#4) | 34.6 dB | 9.8 dB  | 11.3 dB | 1.39 s | 4.9 s  | 4.2 s |
| 73 (C#5) | 36.9 dB | 14.0 dB | 14.7 dB | 1.30 s | 3.4 s  | 3.3 s |

Median **3.0x too fast**, worst 5.7x. The body-median metric is measuring duration
as level — precisely the failure mode `derive_trims.py`'s own `note_body` docstring
warns about ("a static trim would mistake duration for level"). The derivation
tooling already refuses to trim GM7 on that basis: it is **guard-excluded on BOTH
references** (`shape/short`, 6 keys on SC-55 and 5 on S-YXG50; measured shape_dev
10.8-27.9 dB against `SHAPE_DB = 12.0`), i.e. already routed to voice work.

**Second, independent defect found while root-causing this.** Every baked clavinet
zone is exactly 1.6 s long and ends on a 50 ms fade to zero, and `ClavinetSampled`
reaps the voice when the buffer runs out. A GM7 note held longer than ~1.6 s
therefore goes **silent while the key is still down**. Both references sustain (while
decaying) for as long as the note is held. The M-CAL probe holds notes for 1.30 s, so
this run does not see it — it was found by code read and is stated here as such.

### How to reproduce

The measurement, from the M-CAL v3 run (raw, un-normalized renders; CC7=50 so the
master bus compressor is proven inert):

```
cargo build --release -p ferrosintesis-cli --example raw_dump --example calmeter
python tools/instrument-balance/mkprobe.py chunk0
./target/release/examples/raw_dump.exe _cal/probe_chunk0.mid _cal/ferro_chunk0.f32.wav
/c/apps/mdmidiemu.exe _cal/probe_chunk0.mid --wav _cal/sc55_chunk0.wav --synth sc55 --roms <sc55 roms>
/c/apps/mdmidiemu.exe _cal/probe_chunk0.mid --wav _cal/yxg_chunk0.wav  --synth syxg50 \
    --dll /d/language/mdsc55/mdmu80-syxg50-helper/assets/syxg50.dll
./target/release/examples/calmeter.exe <each wav> _cal/plan_chunk0.tsv <label>
```

Then, over the resulting `_cal/*_full.levels.tsv`, using `derive_trims.py`'s own
primitives:

```python
import statistics, derive_trims as dt
data, _ = dt.load(path)
bodies = {p: dt.prog_body(data[p], sorted(data[p])) for p in data}
med = statistics.median([b for b in bodies.values() if b is not None])
print(bodies[7] - med)          # ferro -18.30 | sc55 -4.95 | yxg -4.79
```

Swap `dt.prog_body` for a median-of-`dt.note_peak` and the same three engines give
-0.15 / -3.24 / +0.48. The per-key b0->b8 drops above are read straight from the
`b0` and `b8` columns of the `program == 7` rows of each TSV.

### Expected vs actual

**Expected.** A held GM7 note sustains at a decay rate in the region both references
agree on (t60 roughly 3-10 s across C3-C#5), so its body level lands near its
engine's own median-relative placement of about -5 dB, and it keeps sounding for as
long as the key is held.

**Actual.** The note decays with an effective t60 of 1.3-1.9 s, putting its body
13.4 dB below where both references put theirs, and it stops dead at 1.6 s.

## Root cause

The decay is **baked into the committed asset**, not applied at runtime.

- `tools/ferrosintesis-samples/prepare.py:794-797` — `clavinet_t60(root_midi)`,
  "Register-scaled clavinet decay t60 (EAR-tunable): 2.4 s low -> 0.9 s high",
  linear in MIDI root from 31 to 91.
- `tools/ferrosintesis-samples/prepare.py:1762-1766` — `_bake_clavinet_note` applies
  that as an exponential envelope (`dec = 10 ** (-3.0 / (t60 * sr))`) over the looped
  sustain, from `loop_start` to the end of the buffer.
- `tools/ferrosintesis-samples/prepare.py:1799` — `_bake_clavinet` calls it per zone.
- The 11 resulting WAVs in `crates/ferrosintesis-samples-clavinet/samples/` carry the
  envelope. `sampler.rs:3947-4061` (`clavinet_bank`, `ClavinetSampled`) faithfully
  replays what was baked; there is **no runtime decay knob** to turn.

The mechanism is confirmed numerically. Effective t60 =
`clavinet_t60(nearest_root) / repitch_ratio` (repitching a decaying sample upward
shortens its decay proportionally):

| probe key | nearest zone root | repitch | predicted t60 | measured t60 |
|---|---|---|---|---|
| 48 | 48 (C3) | 1.000 | 1.98 s | 1.90 s |
| 63 | 60 (C4) | 1.189 | 1.41 s | 1.38 s |
| 68 | 67 (G4) | 1.059 | 1.42 s | 1.39 s |
| 73 | 72 (C5) | 1.059 | 1.30 s | 1.30 s |

The 1.6 s cutoff is `CLAVINET_KEEP_S = 1.6` (`prepare.py:789`) plus the reap in
`ClavinetSampled::render` (`sampler.rs:4020`, `if j + 1 >= n { return false }`).

**Provenance.** `wrk_journals/2026.07.17 - JRN - clavinet sampled default (MuseScore
MIT).md` lists `clavinet_t60` explicitly under "Ear-tuning left to Arthur (no ears on
this box) ... expect to nudge after listening". `git log --oneline --
crates/ferrosintesis-samples-clavinet` shows a single commit (`0a9636f`), so the
unheard guess is still shipping.

**Not the cause.** `CLAVINET_LEVEL = 0.80` (`sampler.rs:3939`) and
`PROGRAM_TRIM_DB[7] = 0.0` (`engine.rs:661`) govern the attack level, which the peak
measurement shows is already correct.

**Same class in the fallback.** The `--no-samples` / CC0-nonzero alt-bank voice is
`Pluck(&CLAVINET)` (`voices.rs:11822`), whose preset carries `t60: 0.78`
(`voices.rs:2781`) — shorter still. Code-read; not measured in this run.

## Fix direction

Not a trim. `PROGRAM_TRIM_DB[7]` must stay 0.0 — raising it would leave the attack
13 dB too loud in order to prop up a sustain that has already died, and GM7 is
guard-excluded from the trim derivation on both references precisely because a static
scalar cannot represent an envelope mismatch.

Two things need to change together:

1. **Lengthen the baked decay** (`clavinet_t60`) toward the references' consensus —
   roughly 4-6 s in the low register tapering to ~3.3 s at the top, versus today's
   2.4 -> 0.9 s. Re-bake and re-commit the 11 zones (needs `prepare.py`, the pinned
   MS Basic `.sf3` and `ffmpeg`).
2. **Remove the 1.6 s wall.** Raising t60 alone makes it worse: at t60 = 5 s the note
   would be cut off ~19 dB down instead of ~48 dB down, turning a natural fade into an
   audible chop. Either extend `CLAVINET_KEEP_S`, or — better — give `ClavinetSampled`
   a loop point and a runtime decay envelope so held-note length is unbounded and the
   decay becomes an ear-tunable constant instead of a baked one.

Then re-run the M-CAL probe and confirm GM7 clears the `shape/short` guard on both
references and its `int_F` lands near -5 dB. Consider the same audit for the modeled
`CLAVINET` preset (`t60: 0.78`) so `--no-samples` and the CC0 alt bank do not diverge
from the default voice.

## Notes

- **The direction of the fix is an ear call, and this box has none.** A real Hohner
  Clavinet D6 does decay briskly, so "match the references" is a judgement about
  matching the GM idiom, not about physics. What is *not* a judgement call: two
  independent references (different vendor, era and synthesis method) agree to 0.16 dB
  against us, and the 1.6 s hard cutoff is wrong under any reading.
- No committed album authors GM7 today. Per `CLAUDE.md`, that is not evidence the
  voice is dead — ferrosintesis is a generic GM player and GM7 is a mainstream
  keyboard program that any foreign MIDI file will reach.
- Related but distinct: MM-BUG-KILN-00039 (GM107 koto) shares the insight that a
  static `PROGRAM_TRIM` cannot fix a voice-model defect, but its mechanism is a
  pitch-dependent gain, not a decay rate. MM-BUG-KILN-00019 (0.70x trim damping) is
  about 1-2.5 dB residuals inside the +/-6 dB clamp and cannot reach a guard-excluded,
  untrimmed program.
- There is no oracle guarding GM7's sustain length. The two existing clavinet tests
  (`voices.rs:17272` tangent scrape, `voices.rs:17329` buzz-into-sustain) cover the
  *modeled* voice's timbre only, and `sampler.rs:5576` only asserts the
  default/alt-bank routing. A held-note decay-rate oracle would have caught this and
  would make the fix self-verifying.
- The M-CAL v3 certified report already states the general shape of this at the family
  level ("the plucked families fail on ENVELOPE, not level — that is voice work");
  this entry pins the specific program, the specific constant and the specific
  truncation.

## Blocker (2026-07-25)

The hard 1.6-second wall is objectively wrong, but it cannot be removed safely in
isolation: exposing more of the current baked 2.4→0.9-second decay would preserve the
measured 13.4 dB body deficit, while lengthening only the bake would make the existing wall
an audible chop. The replacement therefore couples an ear-tuned decay target to a longer
asset or a runtime loop/envelope.

Unblock when Arthur auditions and chooses the GM7 target—physical Clavinet brevity versus
the 3–10-second GM-reference idiom—and approves whether the source should be re-baked
longer or looped under a runtime decay envelope. The existing reference panel and pinned
MS Basic source can then drive the implementation and render-diff validation.

## Decision and autonomous implementation brief (2026-07-26)

Arthur approved the GM-reference idiom. Ferrosintesis is a General MIDI player, and the
independent SC-55 and S-YXG50 measurements agree that GM7 should retain substantially more
body than the physically brief interpretation. The sampled voice should target approximately
5.0 seconds t60 through the low and middle register, tapering smoothly to approximately
3.3 seconds at the top. These are calibration anchors, not a demand for one exact curve:
the implementation may fit the per-zone law within the references' 4–6-second low/mid and
3.0–3.8-second top envelope.

Implement this as a click-free runtime loop plus decay envelope, rather than by committing
several seconds of redundant audio per zone. Remove the 1.6-second held-note reap. Choose a
stable loop segment and use a zero-crossing or short crossfade so the loop boundary does not
click. Measure the decay envelope in output seconds, independent of sample playback rate,
so repitching a zone cannot silently shorten or lengthen t60. Keep note-off release and voice
reaping independent from the held-note decay.

Preserve the already-correct attack: `CLAVINET_LEVEL` and `PROGRAM_TRIM_DB[7] = 0.0` are not
calibration levers for this fix. Align the modeled `CLAVINET` fallback's broad decay curve
with the sampled voice so `--no-samples` and the CC0 alt bank no longer die in under one
second; exact timbral identity is not required.

The implementation is autonomously decidable when it carries these focused regression
oracles:

1. A held GM7 note remains live and non-silent beyond 1.6 seconds, then reaches the
   key-dependent decay target without an end-of-sample discontinuity.
2. Representative MIDI keys 48, 53, 58, 63, 68 and 73 follow a smooth curve through the
   target envelope above. The test should measure rendered output time, not infer it from
   source-frame counts.
3. The attack peak remains within the existing calibration tolerance, note-off release
   still terminates the voice, and no permanently live voice remains after silence.
4. The modeled fallback receives an equivalent held-note decay oracle.
5. Re-run the focused M-CAL GM7 probe when the reference setup is available. The expected
   external result is removal of the `shape/short` guard on both references and `int_F`
   near -5 dB; lack of ROM access must not block the in-tree timing and lifecycle tests.

Re-bake the existing sample bank only if stable loop material or loop metadata requires it.
Do not add a dependency. Leave the bug **Fixed**, not Closed, after implementation so a
fresh verifier can inspect a representative low/mid/high render and the automated evidence.
