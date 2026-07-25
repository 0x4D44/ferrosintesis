# MM-REQ-KILN-00003 — Each synth-FX program (96–103) must have a distinct identity

- **State:** Satisfied
- **Priority:** Could
- **Area:** ferrosintesis / voices dispatch
- **Raised:** 2026-07-08
- **Implemented-by:** `crates/ferrosintesis/src/voices.rs::make`, `crates/ferrosintesis/src/voices.rs::fx`, the eight `FxSpec` presets, `crates/ferrosintesis/src/testutil.rs::guards::gm_routing_pins_voice_kinds`
- **Satisfied-by:** `voices::tests::synth_fx_96_103_route_to_fx_voice`, `voices::tests::fx_o2_rain_96_is_a_fused_aperiodic_wash` (96), `voices::tests::fx_o9_soundtrack_97_opens_and_swells` (97), `voices::tests::fx_o5_crystal_98_is_frozen_bit_for_bit` (98), `voices::tests::fx_o10_atmosphere_99_closes_and_plucks` (99), `voices::tests::fx_o3_brightness_100_blooms_late` (100), `voices::tests::fx_o4_goblins_101_pitch_is_unstable` (101), `voices::tests::fx_o1_echoes_102_repeat_at_the_delay` (102), `voices::tests::fx_o11_scifi_103_falls_an_octave_onto_pitch` (103)
- **Violated-by:** —
- **Flow:** light
- **Claimed-by:** —
- **State history:** Draft (2026-07-08) → Accepted (2026-07-08) → Implemented (2026-07-08, `a3eecb96c93646fb382867f14d250ac3f9eadb81`) → re-stated (2026-07-25, see below) → Satisfied (2026-07-25, verified)

## Statement
Each of the eight GM synth-FX programs (96–103) must render a DISTINCT identity,
not the single decaying `bell(CRYSTAL)` chime that all eight shared and which
faded to silence in ~3 s on a held note. Each identity is separated from its
neighbours on a different axis: 96 aperiodic, 97 opens, 98 static, 99 closes,
100 blooms late, 101 never settles, 102 periodic, 103 falls.

Every one of the eight must be pinned by an oracle that goes RED when its
identity is removed — a routing assertion alone is not acceptance.

## Rationale
These are texture programs; one shared struck chime is structurally wrong.
2026-07-08 GM gap audit (synth FX).

The original Statement named the fix ("route to `pad()`") rather than the
requirement, and the shipped Stage-3 design is better than the one it prescribed:
all eight programs route to an `Fx` wrapper carrying a per-program preset, so 99
is "a percussive pluck decaying into a soft dark wash" and 103 "a falling
resonant zap" — neither of which is a pad. Re-stated on 2026-07-25 to the intent
the code actually serves. See "Acceptance blocked" below for the full history.

## Notes

Manual reqs-loop implementation branch:
`task/20260708-TSK-HUM-reqs-loop-mm-req-00003`.

The named oracle was added before implementation and failed red on the old shared
crystal route:

```text
$null | deltic timeout 180 cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::synth_fx_97_99_101_103_sustain_as_pads ... FAILED
assertion `left == right` failed: program 97 should route to pad
  left: "modal"
 right: "sawstack"
```

Passing oracle for Gate 2:

```text
$null | deltic timeout 180 cargo test synth_fx_97_99_101_103_sustain_as_pads --manifest-path fable5/hollowsynth/Cargo.toml
test voices::tests::synth_fx_97_99_101_103_sustain_as_pads ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 109 filtered out; finished in 0.05s

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

Additional local gates after rebasing onto `origin/main` at `112d3b9`:

```text
$null | deltic timeout 180 cargo test gm_routing_pins_voice_kinds --manifest-path fable5/hollowsynth/Cargo.toml
test testutil::guards::gm_routing_pins_voice_kinds ... ok
test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 109 filtered out; finished in 0.00s

deltic timeout 120 cargo fmt --check --manifest-path fable5/hollowsynth/Cargo.toml
passed (no output)

$null | deltic timeout 300 cargo test --manifest-path fable5/hollowsynth/Cargo.toml
test result: ok. 108 passed; 0 failed; 2 ignored; 0 measured; 0 filtered out; finished in 8.80s

$null | deltic timeout 300 cargo clippy --manifest-path fable5/hollowsynth/Cargo.toml --all-targets -- -D warnings
Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.89s

deltic timeout 300 cargo build --release --manifest-path fable5/hollowsynth/Cargo.toml
Finished `release` profile [optimized] target(s) in 3.55s
```

MIDI scan:

```text
changed_fx_files=0
unchanged_crystal_fx_files=6
```

Unaffected GM-98 material stayed byte-identical:

```text
baseline_sha256=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
current_sha256=C297E540885FA9FE5F8A24A452AB3FCA1C48110AB0A3A544A6B775323E3FB847
byte_identity=pass
```

Three read-only adversarial reviewers ran concrete refutation checks. The oracle
and regression reviewers found no defects. The remaining dirty-tree/Accepted
state finding was the expected pre-landing state and is addressed by this
commit.

Post-integration rebase note: rebased onto `origin/main` at `112d3b9` after
`MM-REQ-KILN-00002` landed. The implementation commit became
`a3eecb96c93646fb382867f14d250ac3f9eadb81`; the package version was advanced to
`0.8.8` because trunk already carried `0.8.7`.


## Acceptance blocked (2026-07-25) — stale oracle, superseded Statement

Held at `Implemented` during the batch acceptance of the other 23 reqs. Two
problems, both needing a human spec decision before this can move to `Satisfied`:

1. **The recorded oracle no longer exists and fails silently.** The
   `Satisfied-by` command filters on `synth_fx_97_99_101_103_sustain_as_pads`,
   which was renamed to `voices::tests::synth_fx_96_103_route_to_fx_voice` and
   had its assertion deliberately changed. Run verbatim today it reports
   `test result: ok. 0 passed; 0 failed; ... 700 filtered out` and **exits 0** —
   it looks green while asserting nothing. A cargo name filter that matches
   nothing is not a failure, so this cannot be caught by running the command.

2. **The Statement is contradicted by the shipped design.** It requires 97/99/103
   to "render as sustaining pad textures (route to `pad()`)". Stage 3 routes all
   of 96-103 to the `Fx` wrapper with per-program identities; the retired oracle's
   replacement comment states "the eight presets are no longer pads". Two current
   identities directly contradict the wording: 99 is "a percussive pluck DECAYING
   into a soft dark wash" (`voices.rs:11536`) and 103 "a falling resonant ZAP"
   (`voices.rs:11681`).

The code did not regress -- the requirement's wording went stale when a better
design landed. Two dispositions, for Arthur:

- **Re-state** to the shipped intent ("each of the eight synth-FX programs must
  have a distinct sustained identity, not one shared decaying chime") and point
  `Satisfied-by` at the `fx_o1`-`fx_o8` oracles, keeping the regression alarm.
- **Retire** as superseded by the Stage-3 FX work, accepting that the FX-O
  oracles carry the spec from here.

## Resolution (2026-07-25) — re-stated, oracle gap closed, Satisfied

Arthur chose **re-state**. Mapping the existing FX-O oracles to programs first
exposed a hole that would have made a re-stated `Satisfied` dishonest:

| program | 96 | 97 | 98 | 99 | 100 | 101 | 102 | 103 |
|---------|----|----|----|----|-----|-----|-----|-----|
| before  | O2/O7/O8 | **none** | O5 | **none** | O3 | O4 | O1/O6 | **none** |

The three unoracled programs were **exactly the three the requirement was
originally about**. `synth_fx_96_103_route_to_fx_voice` proves only that all
eight reach the `Fx` wrapper — it says nothing about their identities being
distinct, so 97/99/103 could have collapsed into one another undetected.

Three new oracles close the gap:

- **FX-O9** `fx_o9_soundtrack_97_opens_and_swells` — 97 opens spectrally
  (+15.9 dB worst case over a key/vel/seed grid) and swells in amplitude
  (≥3.2×, peaking ≥1.10 s in), against the static-filter control 101 (≤|4.0| dB,
  ~1.0× growth).
- **FX-O10** `fx_o10_atmosphere_99_closes_and_plucks` — 99 is 97's mirror:
  brightness falls (≤ −25.9 dB) where 97's rises, and it peaks in the first
  300 ms and decays where 97 peaks past a second and grows. A two-sided
  contrast, because 97 and 99 are both saw stacks under the same wrapper and
  nothing but the direction of their motion separates them.
- **FX-O11** `fx_o11_scifi_103_falls_an_octave_onto_pitch` — 103 is the only
  preset with a pitch scoop: at onset it has +38.9 dB or more energy an octave
  above written pitch versus at it, settling back into the non-scooped
  population (≤ +6 dB) by 0.34 s.

**Each oracle was proven to go RED** by removing the identity it guards, which
is the acceptance evidence the honesty rule asks for (repo doctrine: write the
adversarial change that *should* fail your oracle and check that it does):

| adversarial change | result |
|---|---|
| 97 `lp_fc0` 420 → 4600 (filter no longer opens) | FX-O9 red |
| 97 attack 2.2 s → 0.02 s (no swell) | FX-O9 red |
| 99 `lp_fc0` 3600 → 520 (filter no longer closes) | FX-O10 red |
| 99 attack 0.02 s → 2.2 s, sustain → 1.0 (no pluck) | FX-O10 red |
| 103 `scoop0` 2.0 → 1.0 (scoop removed) | FX-O11 red |

Two measurement traps were found and avoided while calibrating, both recorded in
the oracle doc comments:

1. **A key-relative brightness band goes blind at low keys.** The one-shot LP's
   cutoff travels in absolute Hz, so the measurement band has to straddle *that*,
   not the note. A `f0*5.5 .. f0*15` band read 97's entire opening as +1.2 dB at
   key 48, where the absolute 1.8–4.2 kHz band reads +15.9 dB.
2. **The obvious pitch reader would have made FX-O11 a false green.**
   `peak_locate` over `[0.8·f0, 2.6·f0]` is fooled by a plain detuned saw stack —
   its beating 2nd harmonic wins the argmax in short windows, so the NON-scooped
   99 and 101 both read a phantom ~1200-cent "scoop" that decays like a real one.
   The shipped oracle compares band ENERGY at the octave against band energy at
   the fundamental instead, which a harmonic-balance accident cannot imitate.

The stale `Satisfied-by` command (a cargo name filter matching nothing, exiting 0
while running zero tests) is replaced by an explicit list of oracle symbols.
