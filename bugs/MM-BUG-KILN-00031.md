# MM-BUG-KILN-00031 — removing VEL_LEVEL_EXP[76] left the modeled GM76 bottle (--no-samples / repitch-fallback) un-compensated and off-law (k≈2.5), uncaught by the samples-on-only velocity sweep

- **State:** Closed
- **Priority:** Should
- **Severity:** Low
- **Area:** synth
- **Raised:** 2026-07-21
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
- **State history:** Open (2026-07-21, raised by Claude Opus 4.8 during the velocity-law loose-ends investigation; a regression introduced by `f7d585a`) → Fixed (2026-07-21, `4569855`, bumped `7caec4c`) → Closed (2026-07-21, independently verified by Codex GPT-5: modeled GM76 k=2.421/2.555 red-before, all routing and velocity guards green-after; workspace tests and clippy green)

## Observation

The GM76 exemption commit (`f7d585a`) removed `VEL_LEVEL_EXP[76] = 1.450` because that
entry was double-correcting the new self-compensating `BottleLoopVoice` (samples-on).
Correct for the loop — but that same 1.450 was **also** the compensation the **modeled**
Wind bottle still needs, and `VEL_LEVEL_EXP` is program-indexed (not samples-aware). So
the entry's removal set GM76 to the table default 2.0, and `make()` early-returns without a
`ScaledVoice` wrap at exponent 2.0 — leaving the modeled bottle rendering its raw curve.

Measured (modeled path, `samples=false`, same `level_db`/`fit_k`/`FIT_VELS` harness the
velocity oracles use):

| key | fitted k | want |
|---|---|---|
| 48 | 2.421 | 2.0 |
| 60 | 2.555 | 2.0 |

Controls GM73/GM75 (no table entry) fit 2.04/2.09, so the harness is sound. k≈2.5 means the
modeled bottle renders **~6.6 dB too quiet at v32** relative to fortissimo.

**Blast radius is not only `--no-samples`.** The `76 =>` arm falls back to the model via
`bottle_loop_voice(...).unwrap_or(model)` for any GM76 note more than ~1 octave from the
bottle sample's zone root (below ~C#5), in **any** build — so low GM76 notes were off-law
even with samples on. The samples-on velocity sweep never caught it: there GM76 is the
exempted loop (`every_gm_program_follows_the_square_law` runs `samples=true`, HLD §5).

**No in-repo album is affected** — a program census over all 124 committed album MIDIs shows
GM76 authored by zero of them. The defect is audible only on foreign GM files using program
76, and in `--no-samples` renders. Severity Low for that reason; filed because it is a real
regression and ferrosintesis is a faithful generic GM player, not only an album engine.

## Fix

Wrap the model — and only the model — in `ScaledVoice(1.512)` inside the `76 =>` arm, so the
compensation tracks the **voice** (model vs loop), not the `samples` flag. The
`BottleLoopVoice` (a real recording carrying its own dynamic) stays bare. A note that falls
back to the model in a samples-on build (e.g. C5) is now compensated identically to
`--no-samples`. GM76 keeps **no** `VEL_LEVEL_EXP` entry — the program-indexed table cannot
express "compensate the model, not the loop"; the compensation is voice-intrinsic, like the
loop's own taper. `1.512` is the census-derived midpoint of the valid compensation range
`[1.379, 1.645]` measured at the two probe keys.

Verification (on the fixed tree, integrated at `4569855`):
- `velocity_law::modeled_gm76_follows_the_square_law_in_no_samples_builds` — the
  fails-before guard, observed red (k=2.421/2.555) → green (within 2.0 ± 0.2). The first
  samples-off velocity oracle.
- `velocity_law::looped_recording_voices_keep_their_documented_velocity_behaviour` — pins the
  loop voices' deliberate laws (GM76 compressed span, GM109 velocity-flat), turning the silent
  sweep exemptions into positive contracts.
- `voices::tests::wd_o10_routing_sample_policy_and_lifecycle` — pins that GM76 renders
  identically samples on/off at C5 (both fall back to the compensated model). It red-flagged
  an earlier flag-keyed attempt; the voice-keyed fix passes it.
- Full ferrosintesis lib suite 598/598, clippy `-D warnings` clean, fmt clean. Render-diff
  clean by construction (change confined to the `76 =>` arm; GM76 unauthored by any album).

### Verification summary (2026-07-21 — Codex GPT-5)

Independent of the Claude Opus 4.8 fixer. On `4569855^`, the transplanted modeled-path
oracle reproduced both recorded exponents: k=2.421 at key 48 and k=2.555 at key 60. Current
trunk passed `modeled_gm76_follows_the_square_law_in_no_samples_builds`,
`looped_recording_voices_keep_their_documented_velocity_behaviour`, and
`wd_o10_routing_sample_policy_and_lifecycle`. Source review confirmed `ScaledVoice(1.512)`
wraps only the modeled bottle before the sample/fallback decision, so both `--no-samples`
and samples-on repitch fallback are corrected without double-scaling `BottleLoopVoice`.
Workspace tests and clippy were green. No residual path gap.

## Notes

- Distinct from MM-BUG-KILN-00029 (GM42/43 bowed turnover) and MM-BUG-KILN-00030 (harpsichord
  LA onset): this is a monotonic power-law slope error a scalar exponent corrects exactly, not
  a non-monotonic model defect.
- Durable lesson captured in `lessons_learnt.md` (2026.07.21): a program whose samples-on and
  samples-off voices have different raw velocity laws needs voice-level compensation, and the
  samples-on-only sweep will not catch a samples-off regression.
