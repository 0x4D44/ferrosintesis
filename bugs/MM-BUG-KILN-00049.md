# MM-BUG-KILN-00049 — the e-bow sustainer pins its hold level in the LOOP domain but is calibrated against an OUTPUT measurement, so any damper change breaks its pitch invariance (+12.9 dB at key 88)

- **State:** Closed
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
- **State history:** Open (2026-07-22, raised by Claude Opus 4.8 (1M) — surfaced while fixing KILN-00042; it is the reason DRIVE_LEAD had to be excluded from that fix) → Fixed (2026-07-25, Codex GPT-5.6-Sol; closed the hold-level invariant on DRIVE_LEAD's audible post-pickup/body output, restored the derived damper law, and added a two-seed five-key register-spread oracle) → Closed (2026-07-25, Claude Opus 5, independent two-eyes — did not author the fix; the recorded key-88 failure reproduced digit-for-digit on a pre-fix build, and the controller is load-bearing on trunk)

## Observation

**Symptom.** `DRIVE_LEAD` is the only preset carrying the e-bow sustainer (`sustain > 0`).
Its design claim, stated in `sus_headroom` (`crates/ferrosintesis/src/voices.rs`), is that
the hold level is **pitch-invariant by construction**:

> "PROPORTIONALLY supercritical — k = SUS_K_OVER × the loop's per-trip deficit at the
> fundamental… Keeping k/deficit constant pins the saturator's equilibrium amplitude at the
> SAME multiple of the knee L at every pitch — the hold level is calibrated by construction
> instead of trimmed at runtime."

The algebra holds in the loop domain. Loss per trip is `deficit·A`; the driver contributes
`k·l·tanh(A/l) → k·l` once saturated; equilibrium is therefore

```
deficit·A = k·l = SUS_K_OVER·deficit·l   ⟹   A_eq = SUS_K_OVER·l
```

— independent of `deficit`, hence of pitch. **But the oracles measure the rendered OUTPUT,
and the loop→output mapping is itself pitch-dependent** (body resonators, `out_lp`, pickup
RLC, and how many partials the loop is currently carrying). Nothing pins that half.

**Measured**, with the KILN-00042 damper hold enabled on `DRIVE_LEAD` (velocity 100,
seed 0xD8, held 8 s), held level relative to the note's own spoken reference:

| key | f | fc | deficit | knee `l` | held level rel-ref |
|---|---|---|---|---|---|
| 64 | 329.6 | 10734 | 0.00387 | 0.1129 | **−6.1 dB** |
| 70 | 466.2 | 16713 | 0.00323 | 0.1277 | −3.3 dB |
| 76 | 659.3 | 19845 | 0.00284 | 0.1137 | −1.6 dB |
| 82 | 932.3 | 19845 | 0.00277 | 0.1227 | +4.4 dB |
| 88 | 1318.5 | 19845 | 0.00304 | 0.0891 | **+12.9 dB** |

`deficit`, `k` and `l` are all near-constant across the register exactly as the design
intends — and the audible hold level still climbs **19 dB**. The design's invariant is real
but it is the wrong invariant, because it is not the quantity anyone hears.

**Expected.** Held level within the oracle's ±5 dB band at every pitch, per the design claim.

**Actual.** A 19 dB spread across two octaves; `sustain_holds_high_notes` fails at key 88.

**Reproduce.** On a build where `DRIVE_LEAD` is `DamperHold::Derived` (remove its opt-out
in `voices.rs`):

```
cargo test -p ferrosintesis --release -- sustain_holds_high_notes </dev/null
```

```
key 88: windows outside [-13.3, -3.3]: [(2, 8.03), (3, 9.79), (4, 10.79), (5, 11.40), (6, 11.78), (7, 12.02)]
```

## Root cause

Two halves of one calibration live in different domains and only one is pinned:

1. `sus_headroom` pins the **loop** equilibrium at `SUS_K_OVER × knee`, correctly and
   pitch-independently.
2. `SUS_HOLD_REF_OFFSET_DB` (in the test module) absorbs the **loop → output** mapping as a
   single measured scalar — "the crest-vs-RMS, the smoothed window-max envelope statistic,
   and the saturator equilibrium multiple" — with the tacit assumption that the mapping is
   flat enough in pitch for one number to cover it.

That assumption held while the damper's corner sat a fixed multiple above the fundamental.
Once the corner moves (as KILN-00042 makes it), the loop carries a different partial
structure at each pitch, the mapping tilts, and no single scalar can absorb it. The comment
on `SUS_HOLD_REF_OFFSET_DB` already records the constant being re-captured twice for exactly
this class of change ("the brighter damper shrinks the high-key loop deficit so the
SUS_K_MAX clamp no longer caps E6…") — but a re-capture only re-centres a spread, it cannot
remove one.

## Fix direction

Pin the invariant in the domain where it is claimed. Options, in preference order:

1. **Close the loop on the output.** Derive the knee `l` (or a per-note correction to it)
   from a measurement that already includes the loop→output mapping, rather than from the
   spoken-level reference alone.
2. **Model the mapping.** Make `SUS_HOLD_REF_OFFSET_DB` a function of pitch fitted against
   the same probe harness KILN-00042 uses, instead of a scalar. Cheaper, but it re-fits
   every time the damper law changes — which is what just went wrong.
3. **Bound the regime.** Cap how far the damper corner may sit above the fundamental so the
   loop's partial structure stays in the band the sustainer was calibrated for. Interacts
   with 00042's ceiling and would partly undo it.

**Oracle to add:** the existing `sustain_holds_high_notes` asserts a band per key; add an
explicit assertion that the *spread across keys* is small, so a future change that tilts the
mapping fails on the invariant itself rather than on whichever key happens to leave the band
first.

## Fix (2026-07-25)

`DRIVE_LEAD` now uses `DamperHold::Derived`, removing KILN-00042's sole
e-bow exclusion. The string-loop driver remains unchanged and bounded by
`sus_headroom`; its one-way energy injection still owns sustain and release.

The correction is at the layer that was uncalibrated:

- `Pluck::apply_sustainer_output_gain` measures the main string signal after
  pickup, body, cabinet, output filter, amplitude, and attack/release envelopes.
- Once the existing e-bow latch engages, a 50 ms log-amplitude slew tracks the
  audible target `sustain × captured output reference`.
- Make-up is bounded to `[0.05, 4.0]`. The lower bound covers the reported
  key-88 overshoot with margin; the upper bound prevents a silent or broken
  projection from becoming unbounded gain.
- The path is constructed only for a preset that has both an authored e-bow
  (`sustain > 0`) and a derived damper. Tremolo-installed holds and every other
  `Pluck` keep their prior render path.
- Release freezes the last scalar while the bounded driver drops immediately,
  preserving the existing natural-release contract.

The first attempted output-to-knee feedback was rejected: the driver can add
energy but cannot remove overshoot, so it pumped against the string's eight-second
decay. A post-projection scalar can correct both directions without changing loop
stability or timbre.

## Verification (2026-07-25)

- Red before: changing only `DRIVE_LEAD.damper_hold` to `Derived` reproduced the
  reported failure. Key 88 rose from `+8.0` to `+12.0 dB` relative to its spoken
  reference across seconds 2–8, outside the expected `[-13.3, -3.3] dB` band.
- Green after: `voices::tests::sustain_holds_high_notes` now covers keys
  64/70/76/82/88 and seeds `0xD6`/`0xD8`. Every one-second window passes the
  existing level and flatness bounds; worst cross-register spread is `2.4 dB`,
  down from the reported `19 dB`.
- The four `voices::tests::sustain_*` oracles pass with default features and
  `--no-default-features`, natively and on Rust 1.87. Bends, slurs, release, and
  self-oscillation behavior remain green.
- `voices::tests::treble_hold_authoring_pins`,
  `voices::tests::ks_decay_law_holds_across_register`,
  `voices::tests::driven_main_and_alt_banks_diverge`, and
  `voices::tests::feedback_gtr2_variation_sustains_longer_than_base_drive` pass.
- Strict clippy passes for all targets with all features and with no default
  features; `cargo fmt --all --check` passes.
- Exact baseline `b2a7000`, full 124-MIDI render inventory at 11,025 Hz:
  11 changed and 113 byte-identical. A bank-aware MIDI census proves the 11
  changed tracks are exactly the complete CC0-nonzero GM29/30 set (all ten
  Slipstream tracks plus Through Lines 16), so there is no contamination.
  `render-diff` itself labels them contamination because its scanner ignores
  bank selectors; that separate tooling limitation is parked in `scratchpad.md`.

### Verification summary (2026-07-25, Claude Opus 5, independent — did not author the fix)

Reproduced the **original recorded observation verbatim**. A throwaway worktree at
`620e5b6^` (`b2a7000`) with DRIVE_LEAD's opt-out removed exactly as the Reproduce block
specifies (`damper_hold: DamperHold::Derived`, nothing else changed) fails with:

```
key 88: windows outside [-13.3, -3.3]: [(2, 8.027917), (3, 9.786356), (4, 10.788551),
 (5, 11.396221), (6, 11.777503), (7, 12.02174)]
```

Every digit the ledger quotes — `(2, 8.03) (3, 9.79) (4, 10.79) (5, 11.40) (6, 11.78)
(7, 12.02)` — matches. The register climb reproduced too: key 76 held at −9.3 dB while key 88
sat at +12.0 dB rel-ref.

Green on trunk: `voices::tests::sustain_holds_high_notes` passes across keys 64/70/76/82/88
and seeds `0xD6`/`0xD8`.

The fix is load-bearing, not incidental: on trunk, setting **only** `sus_out_control: false`
(keeping `DamperHold::Derived`) turns the oracle red again — so the output-domain controller,
not the damper flip, is what closes the invariant.
Repo gates on the verification worktree: `cargo fmt --all --check` clean;
`cargo clippy --workspace --exclude amp-lab --all-targets --locked -- -D warnings` clean;
`cargo clippy -p ferrosintesis --no-default-features --all-targets --locked -- -D warnings`
clean; `cargo test -p ferrosintesis --no-default-features --locked` 614 passed / 0 failed;
`cargo test --workspace --exclude amp-lab --locked` all suites ok, 714 passed / 0 failed /
27 ignored in the ferrosintesis lib suite and no failures anywhere; `cargo test -p amp-lab` 26/26;
`python tools/ferrosintesis-samples/test_prepare.py` 32/32.

## Notes

- **Resolved the MM-BUG-KILN-00042 block for DRIVE_LEAD.** Before this fix the
  preset was `DamperHold::Off` purely because the derived law exposed this
  output-domain tilt. It now rejoins `Derived` with the audible invariant closed.
- Above key ~76 the derived corner saturates the `sr * 0.45` clamp, so the loop is nearly
  undamped; that is where the mapping tilts hardest.
- Same underlying habit as MM-BUG-KILN-00048: a loop-internal quantity calibrated against an
  output-domain measurement. Worth fixing them with one another in mind.
