# MM-BUG-KILN-00074 — GM 42/43 bowed strings PANIC at C1 when rendering at 96 kHz: BowedString's delay lines are sized in fixed samples, ignoring the sample rate

- **State:** Closed
- **Priority:** Should
- **Severity:** High
- **Area:** synth / sample-rate conversion
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
- **State history:** Open (2026-07-24, raised by Claude Opus 4.8 (1M) — found incidentally while building the all-program rate-sweep oracle for MM-BUG-KILN-00061, not by a hunt for it)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M), same author as the raise — **two-eyes closure
  is therefore owed to someone else**. Correction on investigation: the reported "exactly
  two panicking combinations" was an undercount of a **30-combination** defect that also
  breaks at **48 kHz** — see "Correction on investigation".)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

**Symptom.** Rendering GM 42 (cello) or GM 43 (contrabass) at key 24 (C1) with an output
rate of 96 kHz **panics**:

```
thread '…' panicked at crates\ferrosintesis\src\dsp.rs:375:26:
attempt to subtract with overflow
```

**Expected.** 96 kHz is an accepted output rate — the public offline and realtime
builders take it without a caveat — so every GM program should render at it. A low note
should sound, or at worst sound wrong; it must never crash the caller.

**Actual.** It aborts the render. In a debug build it is the panic above; the arithmetic
that overflows is `self.idx + self.buf.len() - i` at
`crates/ferrosintesis/src/dsp.rs:375` (`DelayLine::tap`), so a release build wraps the
index instead and reads the wrong sample — silent corruption rather than a crash.

**Repro.** Exhaustive scan of programs 0..=127 x keys {24, 28, 33, 40, 52, 64, 76, 88} x
rates {44100, 48000, 96000}, rendering 0.03 s of each through `voices::make`. **Exactly
two** combinations panic, both bowed, both at the lowest key, both only at 96 kHz:

```
GM 42 key 24 sr 96000
GM 43 key 24 sr 96000
```

44.1 kHz and 48 kHz are clean for every program and key in that grid.

## Root cause

`BowedString`'s two waveguide delay lines are allocated with **literal sample counts**
that do not scale with `sr` (`crates/ferrosintesis/src/voices.rs:8436-8437`):

```rust
bridge: DelayLine::new(320),
neck: DelayLine::new(1600),
```

Every other `DelayLine` allocation in the crate is derived from `sr` or from the target
delay — `(0.040 * sr)`, `(target * 2.2) as usize + 8`, `(d as usize + 8)`, and so on.
These two are the exceptions.

The waveguide needs about `sr / f` samples of round-trip delay. At C1 (32.70 Hz) that is
~1349 samples at 44.1 kHz — inside the 1600-sample neck line — but ~2936 samples at
96 kHz, which is not. `DelayLine::new` rounds up to the next power of two (2048 here), so
the line is still short and `tap` walks off the front.

The threshold is therefore roughly `sr / f > 1600`, i.e. it worsens as the rate rises and
the pitch falls. C1 at 96 kHz is simply the first grid point that crosses it; the true
boundary was not mapped.

## Fix

Size both lines from `sr` and the lowest supported pitch, exactly as every other call
site does — the required delay is a function of the sample rate, so a literal cannot be
correct at more than one rate.

Add a rate-sweep regression: render every GM program at the bottom of the keyboard across
the supported output rates and require none to panic. The scan above is the shape; it
belongs in the suite so a fixed-size line cannot be reintroduced.

Note `DelayLine::tap`'s own arithmetic is the reason this is a panic in debug and silent
corruption in release. Consider whether `tap` should clamp or debug-assert its delay
against the buffer length, so a future undersized line fails loudly at its source in both
profiles rather than only in debug.

## Correction on investigation (2026-07-24)

**The "exactly two panicking combinations" figure in the Observation above is an
undercount, and the severity framing there understates the reach.** It counted *panics*.
An over-long delay only panics when `self.idx + self.buf.len() - i` happens to underflow;
for other values of `idx` the expression stays non-negative, the `& self.mask` wraps the
index, and `tap` quietly returns an unrelated sample. Those cases were invisible to a
panic scan.

Re-measured with the new `debug_assert` in `DelayLine::tap`, which catches every
undersized read rather than only the ones that underflow — same grid extended to five
rates (programs 0..=127 x keys {0, 12, 21, 24, 36}):

| rate | undersized reads |
|---|---|
| 44 100 Hz | 0 |
| 48 000 Hz | **4** |
| 88 200 Hz | 8 |
| 96 000 Hz | 8 |
| 192 000 Hz | 10 |
| **total** | **30** |

So this was never a 96 kHz corner case: **it breaks at 48 kHz**, silently, in release.
44.1 kHz is clean, which is why no album render was ever affected — that is the CLI
default.

## Resolution

`crates/ferrosintesis/src/voices.rs`:

- New `bow_line_len(sr, share)` sizes each waveguide line from the **same arithmetic
  `set_freq` uses** — `sr / BOW_MIN_HZ * share` — so a rate change cannot outgrow it.
  `loop_comp` is deliberately not subtracted (it only shortens the delay, so ignoring it
  keeps the bound safe), and `+ 2` covers `tap`'s two-point interpolated read.
- `BOW_MIN_HZ` is now a named constant used by **both** `set_freq`'s pitch floor and the
  sizing, so the two cannot drift. Lowering the floor without regrowing the lines was the
  latent way to re-create this bug; now it is one edit.

`crates/ferrosintesis/src/dsp.rs`:

- `DelayLine::tap` gains a `debug_assert!` that the requested delay fits, naming both the
  reach and the line length. This is the guard the Fix section asked for, and it is the
  general one: it protects **every** `DelayLine` call site, not just the bowed string, and
  it converts the silent-wrap failure mode into a loud, self-explaining one. Debug-only —
  `tap` is a per-sample path.

Oracles, both proven red on the pre-fix tree:

- `voices::every_program_renders_at_every_common_rate` — all 128 programs x 5 low keys x
  {44.1, 48, 88.2, 96, 192} kHz, asserting finite output and no panic. Swept over every
  program rather than the two reported, because a fixed-size literal is a mistake any
  voice could carry and only a sweep says which do.
- `voices::bowed_string_survives_a_downward_bend_at_high_rate` — `set_freq` runs per
  sample off `base_f * bend * vib * drift`, so the loop grows *after* construction. A
  sweep that only renders at the written pitch would miss a line sized from
  `key_freq(key)` rather than from the floor.

The rate set is chosen because **nothing validates it**: `Options::with_sample_rate` and
`RealtimeOptions::with_sample_rate` accept any value, so every rate a caller can pick is a
rate we ship.

Also removed the two-entry skip list this bug had forced into
`sampler::la_engagement_never_depends_on_output_rate` (MM-BUG-KILN-00061); that sweep now
covers GM 42/43 at C1 like everything else, and passes.

Behaviour at 44.1 kHz is unchanged: the old buffers were large enough there, and
`DelayLine`'s reads are `& mask` into a circular history, so a larger power-of-two buffer
returns the identical sample for any delay that fitted in the smaller one.

## Notes

- **Found while fixing MM-BUG-KILN-00061**, and deliberately NOT fixed there — that bug
  is the LA sample-eligibility guard, a different mechanism in a different file. The
  KILN-00061 sweep oracle
  (`sampler::tests::la_engagement_never_depends_on_output_rate`) carries an explicit
  two-entry skip list naming **this** bug ID. **Delete that skip list as part of fixing
  this bug** — it is there only to keep an unrelated crash from reddening that oracle.
- Not a duplicate of MM-BUG-KILN-00061: that one changes which notes get a sampled onset
  and never crashes. The overlap is only that both are output-rate-dependence defects,
  which is itself worth noting — a sweep across supported rates was not part of this
  repo's standard coverage before today.
- Severity is High rather than Medium because it is a hard panic in a published library
  crate reachable from a documented-supported configuration, and because the release-build
  behaviour is silent wrong-sample reads rather than a clean failure.
- Not verified: whether any album or demo renders at 96 kHz (the CLI default is 44.1 kHz),
  and where exactly the `sr / f > 1600` boundary falls across the keyboard.
