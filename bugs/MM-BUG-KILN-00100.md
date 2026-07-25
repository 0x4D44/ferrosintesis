# MM-BUG-KILN-00100 — Sympathetic comb tap still flushes at 1e-20, the floor KILN-00027 proved wrong

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** engine / dsp
- **Raised:** 2026-07-25
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
- **Attempts:** fix=1, doubt=0, indeterminate=0
- **State history:** Open (2026-07-25, raised by Claude Opus 4.5 during the ferrosintesis review-remediation build; found by reading `dsp::flush_denormal`'s own doc comment against the call sites it was written to govern) → Fixed (2026-07-25, Claude Opus 4.5; routed through `dsp::flush_denormal`. Render-diff over 124 catalog MIDIs: 0 changed / 124 identical / 0 contamination — byte-neutral, which contradicted the raising prediction of audible diffs; the "Suggested fix" section records why. Awaits independent two-eyes closure.) → Closed (2026-07-25, Codex GPT-5; independently proved the pre-fix Sympathetic path discards a normal `1e-25` tap and the fixed path preserves it bit-exactly through the shared `1e-34` floor; the persistent floor and sympathetic-bus tests plus the complete repository gate passed.)

## Observation

`Sympathetic::process` (`crates/ferrosintesis/src/engine.rs:1381`) flushes the comb
delay-line tap with a hand-rolled threshold:

```rust
let mut y = dl.tap(*d);
if y.abs() < 1e-20 {
    y = 0.0; // denormal flush
}
```

**`1e-20` is the exact value `crates/ferrosintesis/src/dsp.rs:313-328` argues at length
is wrong**, in a 24-line comment written when MM-BUG-KILN-00027 was fixed:

> The floor is `1e-34`, NOT the `1e-20` this shipped with first. `1e-20` is a perfectly
> normal f32 (subnormals only start ~1.18e-38), so flushing there zeroed ~14 orders of
> legitimate, if tiny, state — and that is NOT byte-transparent, however small it looks.

That comment names **this very code path** as where the audible artefact was measured:

> measured on "Wire and Wake": the piano `Sympathetic` per-block flush seeded δ≈1e-19
> every staccato gap, one tie surfaced at t=123.65 s, and `BusGlue`'s transient-displaced
> atk/rel branch amplified it to a 4.8 s, ≤6.5e-5 burst before it self-healed

So KILN-00027 fixed the **per-block** flush in this function — `self.hp.flush()` and the
`damp.flush()` loop at `engine.rs:1372-1375` both route through `dsp::flush_denormal`
and use `1e-34`. The **per-sample tap flush eight lines below** was missed, and still
carries the rejected threshold. Two flushes, two different floors, in one function.

## Why it matters (and why it is only Low)

`y` is not merely feedback state: it is both pushed back into the comb *and* summed into
`sum`, which becomes the wet return added to `l[i]`/`r[i]`. So the flush truncates signal
on the output path, not just internal state.

Severity is Low, not Medium, because the residual is genuinely tiny and self-healing —
KILN-00027 measured the amplified burst at ≤6.5e-5. It is a correctness-of-reasoning
defect more than an audible one: the codebase has a documented, argued floor and one site
silently disagrees with it.

Three `Sympathetic` instances are affected (`engine.rs:2001-2003`): `symp` (piano),
`gtr_symp` (guitar) and `sitar_symp`.

## Fix

Replaced the inline test with `crate::dsp::flush_denormal(dl.tap(*d))`, so the threshold
lives in exactly one place and the argument for it cannot drift away from the code again.

**MEASURED: the fix is byte-neutral on the current catalog — 0 of 124 tracks changed.**
That was NOT the prediction. This bug was raised expecting audible-scale diffs on piano,
guitar and sitar tracks, on the strength of `dsp.rs`'s account of MM-BUG-KILN-00027.

Why the prediction was wrong, and why the fix is still right:

The two floors differ only in the band `[1e-34, 1e-20)`. Old code zeroed a tap there; new
code keeps it. The residual therefore enters the comb at ~1e-20 scale, and the comb
feedback is < 1, so it decays rather than accumulating. Against a normalised signal
quantised to 16-bit (LSB ≈ 3e-5 after −18 LUFS), a 1e-20 perturbation is ~15 orders below
the quantiser and cannot move a sample on its own.

KILN-00027's measured artefact needed something this site does not do: the **per-block**
flush re-seeded δ≈1e-19 at *every staccato gap*, and `BusGlue`'s transient-displaced
atk/rel branch amplified one ULP tie into a 4.8 s, ≤6.5e-5 burst. That is a resonance, not
a general mechanism — it needs repeated re-seeding plus a compressor transient landing on
a tie. The per-sample tap flush seeds once per decay and never hit that resonance across
124 tracks.

So this is a correctness-of-reasoning fix with a measured zero blast radius: the codebase
now has exactly one denormal floor, in one place, with the argument for it attached. The
value of the fix is that the next person cannot reintroduce the divergence by reading the
wrong site.

Keep `reverb::tests::tanks_do_not_park_below_the_flush_floor` in lockstep, as
`dsp.rs:327` instructs.

### Independent closure verification (2026-07-25 — Codex GPT-5)

- Inspected the fixed path and confirmed `Sympathetic::process` now passes every comb tap
  through `dsp::flush_denormal`; the only threshold is the shared `1e-34` floor.
- Added the same temporary behavioral verifier to the pre-fix parent
  `dba058983f9fb4dc8e9211d235c2dc363a0fe859` and the fixed tree. It seeded a
  `Sympathetic` comb so its next tap was exactly `1e-25`, then processed one silent frame.
  The pre-fix path failed because the output was zero, directly reproducing the hand-rolled
  `1e-20` truncation.
- The fixed tree passed the same verifier bit-for-bit: both wet channels retained the
  `1e-25` tap. The temporary verifier was then removed cleanly from both worktrees.
- The persistent `reverb::tests::tanks_do_not_park_below_the_flush_floor` shared-floor
  guard and `engine::tests::guitar_sympathetic_rings_open_strings` functional oracle passed.
- The repository gate passed: formatting, workspace Clippy excluding `amp-lab`, modeled-only
  `ferrosintesis` Clippy, and workspace tests excluding `amp-lab`.
