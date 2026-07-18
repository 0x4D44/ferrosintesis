# MM-BUG-KILN-00004 — BowedString waveguide vibrato runs at 1/16 speed (default GM 42 cello / 43 contrabass); the guarding oracle tests the wrong voice

- **State:** Closed
- **Priority:** Should
- **Severity:** High
- **Area:** synth
- **Raised:** 2026-07-12
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
- **State history:** Open (2026-07-12, raised by Claude Opus 4.8) → Fixed (2026-07-14, voice-quality overhaul slice 1 / B3, Claude Opus 4.8) → Closed (2026-07-18, independently verified by OpenAI Codex on `55c829e`)

## Fix (2026-07-14, voice-quality overhaul, HLD §2.3 / B3)

Both halves of the defect are resolved:

1. **The 16×-slow vibrato.** `BowedString::new` now builds its vibrato LFO through
   `control_lfo(vib_rate, jitter, &mut rng, sr)` (which constructs the `Sine` at
   `sr / CTRL`), so the `is_multiple_of(CTRL)`-gated `.next()` in `render` advances it at
   the intended rate. Per-program base rates match the demoted `Bowed` presets the oracle
   names: **cello (42) 4.8 Hz, contrabass (43) 4.2 Hz**. This is the 4th instance of the
   same idiom (Wind = KILN-00003; a 5th was found in `altbank.rs` and fixed in the same
   task).
2. **"The guarding oracle tests the wrong voice."** `default_bowed_natural_vibrato_runs_at_named_rate`
   was constructing `Bowed::new` directly, but `make()` routes 42/43 to `BowedString` — so it
   was green while the shipped voice was broken. Rewritten to exercise the SHIPPED voice
   through `make()` and measure the rendered FM rate. It is **red on the un-fixed trunk**
   (GM 42 autocorrelation 0.29 Hz) and **green after** (≈ 4.6/5.2 Hz, the seeds' jittered
   rates) — regression-first, so it cannot silently pass a future recurrence.

**Verification (independent oracle, red-before/green-after — the two-eyes standard for this
autonomous session):** the rewritten oracle fails on trunk and passes after the fix; confirmed
by the lead re-running `cargo test -p ferrosintesis` (green). Landed in the squashed overhaul
commit; a render-diff over the GM 42/43 albums (46 + 42 committed MIDIs) confirms the cello/bass
material changed and unrelated albums did not.

> A **separate** defect on the same voice — GM 43 contrabass *tuning* (progressively flat, a
> different mechanism) — was fixed in parallel on trunk (`ff88e98`) AND independently in this
> task (measured `loop_comp` 4.03); reconciled at integration. That tuning issue is NOT this
> bug (this is vibrato); noted only to avoid confusion.

### Independent closure verification (2026-07-18, OpenAI Codex)

- Re-ran the shipped-voice observation on trunk build `55c829e` through
  `voices::tests::default_bowed_natural_vibrato_runs_at_named_rate`: GM 42 measured
  5.21 Hz and GM 43 measured 4.59 Hz with strong periodic autocorrelation.
- Confirmed both red-before halves at pre-fix `0d147c0`: `BowedString` constructed
  `Sine::new(vib_rate, sr, ...)`, yielding 0.300/0.2625 Hz after `CTRL = 16`, while
  the old oracle directly constructed `Bowed` and bypassed the shipped 42/43 route.
  Those rates fail the rewritten oracle's ±20% bands; the exact focused test passes
  after the fix and now goes through `make()` for GM 42/43.
- The independent workspace gate on the same build passed: `cargo test --workspace`,
  `cargo clippy --workspace --all-targets -- -D warnings`, and `cargo fmt --all -- --check`.
  The vibrato defect and the false-green oracle are both corrected; the separately
  tracked contrabass-tuning issue is outside this bug, so no residual split is needed.

## Observation

The `BowedString` waveguide voice — the **default bank for GM 42 (cello) and
GM 43 (contrabass)** since the waveguide+arco-LA cello landed (`5611a62`) — has
an always-on internal pitch vibrato that renders **~16× too slow**, i.e.
effectively inert. Sustained cello and contrabass notes sit dead-flat unless the
channel also authors CC1.

This is the same defect class as MM-BUG-KILN-00003 (the `Wind` voice), reproduced
in a voice written afterwards.

**Repro (by inspection of `crates/ferrosintesis/src/voices.rs` at `5163fe2`,
v0.15.2):**

1. `BowedString::new` picks a nominal rate of ~4.6 Hz:
   `voices.rs:5264` — `let vib_rate = 4.6 * (1.0 + 0.16 * rng.white());`
2. It builds the LFO at the **full sample rate**:
   `voices.rs:5292` — `vib: Sine::new(vib_rate, sr, u(&mut rng)),`
3. But `BowedString::render` advances that LFO **only once per `CTRL` (=16)
   samples**, inside the control-rate gate:
   `voices.rs:5336` — `if self.t.is_multiple_of(CTRL) {`
   `voices.rs:5339` / `:5341` — `self.vib.next()`

So the oscillator advances one control tick per 16 audio samples while its phase
increment was computed for one *audio* sample.

- **Expected:** a ~4.6 Hz pitch vibrato on sustained arco notes.
- **Actual:** ~4.6 / 16 ≈ **0.29 Hz** — a slow drift, below the rate the ear reads
  as vibrato at all.

The neighbouring, now-demoted `Bowed` voice does it **correctly** —
`voices.rs:5055-5057` builds its LFO at `sr / CTRL as f32` and ticks it in the same
control-rate gate. `Reed` and (since Stage 1, `48a7e71`) `Wind` are also correct.
`BowedString` is the lone holdout.

### Why no test caught it (the important half)

`voices.rs:10284` — `default_bowed_natural_vibrato_runs_at_named_rate` — looks
like exactly the guard for this. It even asserts the right numbers for the right
programs (`(42, 4.8)`, `(43, 4.2)`) and its doc-comment states the exact invariant
being violated: *"The nominal natural-vibrato rates are control-rate values, not
full-rate oscillators sampled once every CTRL frames."*

But at `voices.rs:10287` it constructs the voice **directly**:

```rust
let mut v = Bowed::new(program, 69, 100, sr, 17);
```

…bypassing the `make()` dispatch, which at `voices.rs:7123` routes GM `42 | 43` to
`BowedString`, not `Bowed`. The oracle therefore measures a voice that GM 42/43 no
longer render through. **It is green, and it is measuring the wrong thing.** That
false green is why the defect shipped as the default bowed voice and survived the
guitar-v2, brass-ADAA and Stage-1 gates.

Same root shape as the 2026.07.08 lesson (an oracle that measures the wrong thing
while the mechanism is broken), and it is the reason this is filed as High rather
than Medium: the audible defect is modest, but the *guard* is actively misleading.

## Fix

Not yet fixed. Suggested shape (for whoever picks it up — verify, don't take on
faith):

1. **The one-line correction:** build the LFO at control rate, matching
   `Bowed`/`Reed`/`Wind` — `voices.rs:5292` becomes
   `vib: Sine::new(vib_rate, sr / CTRL as f32, u(&mut rng)),`.
2. **Fix the oracle, or the fix is unguarded.** `default_bowed_natural_vibrato_runs_at_named_rate`
   must exercise the voice that actually ships — go through `make(program, …)` (or
   construct `BowedString` for 42/43 explicitly) rather than hard-coding
   `Bowed::new`. Note the two voices disagree on nominal rate: the `Bowed` presets
   name 4.8 / 4.2 Hz for 42/43, while `BowedString` hardcodes a single ~4.6 Hz base
   (`voices.rs:5264`) with no per-program term — decide which is intended and assert
   *that*. A regression test must fail on the current trunk before it passes.
3. **Audit the sibling risk:** any other voice whose LFO/`Drift` is built at `sr`
   but ticked in a `is_multiple_of(CTRL)` gate. This is now the third instance
   (Reed, Wind, BowedString) of one recurring mistake — consider a shared
   constructor or a debug assertion that makes it impossible to get wrong, rather
   than a fourth point-fix.

**Cost note (do not under-scope):** this is a **default-on timbre change** to GM
42/43, so per the repo's synth-change policy it owes a render-diff inventory, an
opus refresh of every album using cello/contrabass, and one version bump. Cheap
diagnosis, non-trivial delivery.

## Notes

- Sibling defect: **MM-BUG-KILN-00003** (`Wind`, GM 72–79) — same CTRL-rate LFO
  mistake, fixed inside Stage 1 (`48a7e71`), though that bug's own ledger entry is
  still `Open` at the time of writing.
- The 2026-07-08 scratchpad "ARTHUR'S CALL" item flagged this bug class as latent in
  `Wind` **and** `Bowed`. `Bowed` was subsequently fixed — but `BowedString`, written
  later as its replacement for 42/43, reintroduced it. The class was closed on the
  old voice and reopened on the new one.
- Found on 2026-07-12 during a read-only audit of the woodwind/synth-wide LA HLD's
  continued validity (no code changed by that audit). Confirmed by direct reading of
  `voices.rs` at `5163fe2`; not yet confirmed by ear or by a rendered-audio
  measurement — the render-side confirmation is part of the fix's regression
  coverage, not a precondition for raising this.
- GM 42/43 are the voice Arthur chose in the waveguide-vs-subtractive A/B. The
  waveguide won for its living, fused sustain; the inert vibrato means it is not
  yet delivering all of the life it was picked for.
