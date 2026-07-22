# MM-BUG-KILN-00048 — the Karplus-Strong loop damper's corner scales with VELOCITY, so a plucked string's decay RATE depends on how hard you pluck it; today it is masked by the f³ collapse, and it blocks KILN-00042 on the dark basses

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-22
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
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) — surfaced while fixing KILN-00042; it is the reason GM33/GM35 had to be excluded from that fix)

## Observation

**Symptom.** In `Pluck::new` the in-loop damper cutoff is scaled by velocity:

```rust
let bright = (p.bright * (0.22 + 0.98 * vn) * (1.0 + 0.08 * rng.white())).min(sr * 0.45);
```

That damper sits **inside** the KS feedback loop, so it does not only shape the attack
timbre — it sets how fast the string loses energy. Its loss per round trip is ≈ ½(f/fc)²
and the loop makes f trips per second, so scaling `fc` with velocity scales the **decay
rate** with velocity: a note struck at velocity 32 decays roughly `1/0.467² ≈ 4.6x` faster
than the same note struck at 127.

On a real string that is wrong. Damping is a property of the string, the bridge and the
air — not of how hard the player plucks. A harder pluck should be **louder and brighter**,
and then decay at essentially the same rate. Velocity→brightness belongs in the excitation,
where `pick_lp` (`p.pick_lp * (0.10 + 1.30 * vn)`) already implements it correctly.

**Why nobody has noticed.** On the dark presets it is invisible because the f³ damper
collapse of MM-BUG-KILN-00042 dominates: every note dies almost instantly at every
velocity, so only the onset is measurable and the level law reads clean. Measured on
GM35 fretless, key 60, **before** the 00042 fix:

| velocity | decay rate |
|---|---|
| 32 | 661 dB/s |
| 127 | 144 dB/s |

Both are so fast that the 400 ms measurement block contains only a transient.

**How it surfaced.** Fixing 00042 holds the damper open, so those notes finally sustain —
at which point their velocity-dependent decay starts contributing slope to the measured
level, and `every_gm_program_follows_the_square_law` fails:

```
programs off the square law (k, want 2.0 +/- 0.25): GM33=2.38, GM35=2.62
```

Both are the darkest wound bass presets (`BASS` bright 1100, `FRETLESS` bright 1050),
where the damper's share of the decay is largest and the velocity scaling therefore bites
hardest. The square law is not a nicety: it is calibrated against both reference synths
(k = 1.997 on the SC-55, 1.981 on the S-YXG50).

**Expected.** A preset's decay rate should be a function of pitch and the authored `t60`,
not of velocity. Level should follow `vel²`; timbre should open with velocity.

**Actual.** Decay rate varies ≈ 4.6x across the velocity range, and once notes sustain
long enough to measure, that leaks into the level law.

**Reproduce.** On a build with `DamperHold::Derived` enabled for `BASS` and `FRETLESS`
(i.e. remove their opt-outs, `voices.rs`):

```
cargo test -p ferrosintesis --release -- every_gm_program_follows_the_square_law </dev/null
```

Fails with GM33 = 2.38, GM35 = 2.62. With the opt-outs in place it passes.

## Root cause

`crates/ferrosintesis/src/voices.rs`, the per-note derivation in `Pluck::new`: one
parameter, `bright`, is doing two unrelated jobs — the **timbre** of the string's tone and
the **damping** of its loop — and velocity is applied to both because they share the
variable. The excitation-side lever (`pick_lp`) is the correct home for velocity→brightness
and already exists.

## Fix direction

Decouple the two roles: apply the velocity scale to the excitation path only, and give the
loop damper a velocity-independent corner (still key- and wound-dependent). Then decay rate
becomes a function of pitch and `t60` alone, and the square law holds by construction.

That is a **re-voicing**, not a mechanical change — every plucked preset's velocity→timbre
behaviour is authored against the current coupling, and `velocity_opens_the_timbre`
(the ff/pp centroid-contrast oracle) pins a 1.25x contrast that today is partly supplied by
the loop damper. Expect to compensate in `pick_lp` and to re-listen. Needs the render-diff
inventory and an ear pass.

**Oracle to add:** decay rate at a fixed key must be invariant across velocity to within a
small tolerance — the property that is silently false today.

## Notes

- **Blocks MM-BUG-KILN-00042 for GM33 and GM35.** Those two presets are `DamperHold::Off`
  purely because of this; lifting the exclusion is the acceptance test for this bug.
- No global damper ceiling escapes it: sweeping `KS_DAMP_DBPS_MAX` restores the square law
  only at ~24 dB/s, which is more decay than either reference shows in total — i.e. only by
  abandoning the 00042 fix entirely.
- Related but distinct: MM-BUG-KILN-00049 (the sustainer's hold level is pinned in the loop
  domain but measured in the output domain). Both are consequences of the same underlying
  habit — calibrating a loop-internal quantity against an output-domain measurement.
