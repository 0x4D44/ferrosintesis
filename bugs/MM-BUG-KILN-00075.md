# MM-BUG-KILN-00075 — the LA bass onset (GM 32–35) sits ~15–18 dB under the model its sum-to-one crossfade mutes, costing a real bass line 13–18 dB

- **State:** Open
- **Priority:** Should
- **Severity:** High
- **Area:** synth
- **Raised:** 2026-07-24
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
- **Attempts:** fix=0, doubt=0, indeterminate=0
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 (1M) from Arthur's A/B of a Tubular Bells render against one made 2026-07-19 07:07; measured, code-confirmed)

## Observation

**Symptom.** Arthur compared a *Tubular Bells (Part One)* render at HEAD against one from
2026-07-19 07:07 and reported the bass guitar was both quieter and worse-sounding. The
bass is channel index 3 (GM 33 fingered + GM 34 picked, 4604 note-ons).

**Cause.** On 2026-07-20 (`dbef98a`) the LA sampled onset became the DEFAULT bank for
GM 32/33/34/35. `LaVoice::render` (`crates/ferrosintesis/src/sampler.rs`) is a *sum-to-one*
crossfade, not an additive layer:

```rust
let u = smooth((t - fade_start) / fade_len);   // 0 until fade.0, 1 at fade.1
let mut s = self.buf[i] * u;                   // the MODEL, faded IN
s += v * (1.0 - u) * self.gain * self.rel_gain; // the SAMPLE, faded OUT
```

With `LA_EBASS = (0.42, (0.05, 0.35))` and `LA_PIZZBASS = (0.40, (0.05, 0.35))` the modeled
bass is **fully muted for the first 50 ms** and only sole owner at **350 ms**. The flat wrap
gain sits the sampled onset **~15–18 dB under** the model it displaces, and because the
crossfade is sum-to-one nothing fills the deficit.

That is survivable on sustained notes and ruinous on a real bass line. On this MIDI the
median ch-3 note is **146 ms** and **90% of notes are shorter than the 350 ms handover**, so
the model never speaks. The `BASS` preset's `kick: 3.9` low thump (`KICK_T60_S` 75 ms) fires
entirely inside the muted window and is erased.

## Evidence (measured; `--peak-normalize` raw-recovered via the printed peak)

Controlled probe, 146 ms notes (the song's median), keys E1/A1/E2/A2/D3, 2026-07-19
baseline `196e552` vs HEAD:

| | GM33 @ vel 64 | whole probe |
|---|---|---|
| total loss vs baseline | **−18.2 dB** | −13.2 dB |
| …the LA sample layer | −14.8 dB | −12.0 dB |
| …the k=2 velocity law | −3.4 dB | −1.2 dB |

Band deltas, GM33 short notes vel 48–80: **−18.2 dB @ 20–60 Hz** (the `kick` thump),
**−15.0 dB @ 60–120 Hz** (the fundamental), −11…−14 dB in every band above.

Envelope at A1 v64 (key **inside** the bank, so no repitch penalty), 25 ms slices, dBFS —
the sample-owned window is ~15–18 dB low and the whole note never recovers:

| t (ms) | baseline | HEAD `--no-samples` | HEAD (shipped) |
|---|---|---|---|
| 0 | −20.0 | −23.7 | −35.6 |
| 25 | −17.2 | −20.6 | −37.5 |
| 100 | −18.6 | −21.6 | −37.4 |
| 125 | −19.7 | −22.8 | −34.7 |

Running HEAD with `--no-samples` returns to within **1.4–3.0 dB of baseline in every band**,
which isolates the sample layer as the cause. Raw peaks, 146 ms probe: GM32 0.52→0.18,
GM33 0.73→0.18, GM34 0.76→0.18, GM35 0.48→0.18; `--no-samples` restores GM32 and GM35 to the
baseline peak **exactly**.

**Aggravating factor — repitch reach.** `finger_bass` covers E1–D2 (6 zones) and `pick_bass`
E1–E2 (7 zones), but **68% of this part's bass notes play above the top zone**. The
`build()` guard admits `step` in `0.5..=2.05`, i.e. up to ~+13.8 semitones at 48 kHz, so
notes are repitched up to **+12 semitones**; the 2.7% that exceed the guard fall back to the
**full-level bare model**, so level jumps note to note.

## Why no oracle caught it

`la_level_continuity` (`sampler.rs`) lists fiddle, flute, piano, brass, reeds, guitars,
harpsichord, dulcimer, strings, cello and contrabass — **no bass program at all**. It also
measures *continuity between adjacent windows*, not parity against the model, so a uniform
under-level would pass even if a bass row existed. The two oracles that do test parity,
`la_steel_high_key_level_parity` and `la_strings_seam_level_parity`, cover only GM25 and
GM48/49. `LA_EBASS` / `LA_PIZZBASS` are commented "Ear-tunable" and were never calibrated.

This is the same defect class as **MM-BUG-KILN-00046** (GM48/49 string seam, fixed
2026-07-23), with the sign reversed: there the sample sat +1..+6 dB *over* the model, here it
sits ~15–18 dB *under*.

## Partial mitigation already shipped

Arthur's call, 2026-07-24: the modeled bass was restored as the DEFAULT bank for GM 32–35 and
the sampled onset moved to the CC0!=0 alt (`voices::bass_la_alt`). That recovers the audible
regression across the 42 album MIDIs (35,831 notes, 11 albums) that author these programs.

**This bug remains open** because the seam mismatch itself is unfixed — it now lives on the
alt bank. Do **not** promote the LA bass layer back to the default bank until it is
level-matched and guarded.

## Suggested fix

1. An `ebass_seam_gain(program, key, vel)` per-key/velocity taper on the wrap gain, fitted as
   the inverse of the measured wrapped/model fade-window ratio — the `strings_seam_gain`
   treatment from KILN-00046, including its 3-seed geomean (the model's per-note jitter makes
   a single-seed ratio unreliable).
2. Add bass rows to `la_level_continuity`, and a dedicated `la_ebass_seam_level_parity`
   oracle with a fail-first bar (the un-tapered ratio is ~0.13–0.18×, i.e. 15–18 dB under).
3. Reconsider the `(0.05, 0.35)` window independently of gain. Even level-matched, muting the
   model for 50 ms erases the `kick` thump, and a 350 ms handover is longer than 90% of a
   typical bass line's notes. The banjo already uses a 0.20 s tail (`LA_BANJO`).
4. Extend the sample banks upward, or tighten the repitch guard for the basses — +12
   semitones on a bass onset is not a credible repitch, and the guard's `44100.0/sr` factor
   makes eligibility rate-dependent (see MM-BUG-KILN-00061).

## Related

- **MM-BUG-KILN-00046** — same defect class, GM48/49 strings (Fixed 2026-07-23).
- **MM-BUG-KILN-00045** — bass family spans 21–25 dB internally where the references span
  ~9 dB. This is a mechanism behind the plucked basses' collapsed held body.
- **MM-BUG-KILN-00061** — LA sample eligibility changes with output rate, dropping bass
  onsets at 96 kHz; same `build()` guard.
