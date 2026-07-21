# MM-BUG-KILN-00027 — `--solo 8` render of Hollow Hill Pt 1 hangs (>400 s vs ~2 min full mix)

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine / sampler
- **Raised:** 2026-07-20
- **Owner:** -
- **Owner role:** -
- **Owner run:** -
- **Owner host:** -
- **Owner branch:** -
- **Owner base:** -
- **Owner fingerprint:** -
- **Owner since:** -
- **Owner until:** -
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=1, indeterminate=0
- **State history:** Open (2026-07-20, promoted from the 2026-07-19 scratchpad entry — Claude Fable 5, GM sweep audit) → Open/parked (2026-07-21, Claude Opus 4.8 — investigated on current HEAD; the described stuck-voice/>200× slowdown does NOT reproduce, see Investigation. Left Open with evidence rather than guessed at.)

## Observation

`ferrosintesis "<Hollow Hill Pt 1>.mid" --solo 8 -o x.wav` (channel 8 = nylon,
program 24) runs >400 s and had to be killed, while the FULL-mix render of the
same file finishes in ~2 min and `--solo 7/10/14` also finish in ~2 min. Only
`--solo 8` is pathologically slow.

Reproduces on BOTH the pre-Phase-1 pluck baseline binary AND with
`--peak-normalize` — so it is not the LUFS normalizer and not the pluck redesign.
A >200× slowdown on a solo path is a real engine/sampler defect even though
full-mix renders are unaffected.

Suspect a stuck / never-reaping voice or an LA-sample loop interaction specific to
that channel: `crates/ferrosintesis/src/engine.rs` (solo path / voice reap) +
`crates/ferrosintesis/src/sampler.rs`.

Repro: Hollow Hill Pt 1, `--solo 8`.

## Fix

<parked — does not reproduce on current HEAD; see Investigation>

## Investigation (2026-07-21, Claude Opus 4.8 — bug-drain pass)

Reproduced the exact command on current HEAD (`origin/main` @ `4ff4e87`), release build,
default LUFS-normalized render, `albums/fable5/Hollow Hill/midi/01 - Hollow Hill, Part
One.mid --solo 8`. **The pathology does not reproduce.**

- Instrumented the offline render loop (`render_block_add`) to log the active-voice count
  every 2000 blocks over the WHOLE render. Across the entire solo-8 render the active set
  peaks at **3 voices** (max unreleased = 2) — there is no stuck/never-reaping voice and no
  O(n²) voice accumulation. `LaVoice::render` self-terminates (`sample_live` clears at
  `fade_end`; the wrapped Pluck decays), so the nylon voices reap normally.
- Confirmed the offline path has unbounded polyphony (`enforce_voice_cap` is realtime-only)
  — so if voices *had* leaked it would show as runaway `active`, and it does not.
- Channel 8's music ends ~145 s, but the song length (set by other channels' last events,
  ~500 s) makes solo-8 render a long **silent** tail (0 active voices — trivially cheap).
  A solo therefore renders FEWER voices per block than the full mix, so it should be — and
  in an isolated run is — **faster** than the full mix, the opposite of the report.
- The one-off "solo-8 slower than full-mix" reading during triage was an artifact of running
  several renders concurrently on a 4-core box (CPU contention between my own test jobs); a
  single isolated solo-8 render completes in well under the full-mix time.

Root cause not found because the symptom is absent here. Per the bug-tracking method, a
non-reproducing bug is parked with evidence rather than guessed at. Likely already addressed
by a change between the 2026-07-20 raise and current HEAD, or specific to the reporter's
environment/binary. **To advance:** the reporter should confirm the repro on current HEAD
(exact binary/commit, `--peak-normalize` vs LUFS, machine), ideally with a voice-count trace;
if it still reproduces there, that trace pinpoints the leaking voice.

## Notes

- Promoted from scratchpad.md (2026-07-19 entry) during the 2026-07-20 GM
  instrument sweep so it is tracked as a defect rather than parked; diagnosis
  session planned.
- Player-correctness issue (the solo path is the documented verification-stem
  workflow), not a voicing issue.
