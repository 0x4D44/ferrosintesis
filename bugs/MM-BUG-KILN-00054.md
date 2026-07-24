# MM-BUG-KILN-00054 — Default drum kit V3 has no oracle for six behaviours the render_drum helper guards only on the legacy V1 kit

- **State:** Closed
- **Priority:** Should
- **Severity:** Medium
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
- **State history:** Open (2026-07-24, raised via `deltic bugs new` by Claude Opus 4.8 (1M), from a `lessons_learnt.md` pruning pass; the claim's original "the engine never selects V1" framing was verified FALSE and corrected here before filing)
  → Fixed (2026-07-24, Claude Opus 4.8 (1M). Helper renamed `render_drum` →
  `render_drum_v1`; the six kit-sensitive behaviours now assert on BOTH modelled kits
  via one `for_each_kit` body; the false source comment corrected. Extending them to V3
  found three behaviours V3 satisfies only marginally — measured and split to
  MM-BUG-KILN-00091. Evidence under "Fix landed" below. Awaits independent two-eyes
  closure.)
  → Closed (2026-07-24, independently verified by Codex GPT-5.6-Sol; fails-before,
  passes-after, root-cause review, and green gate evidence are recorded in
  `wrk_journals/2026.07.24 - JRN - Fixed queue two-eyes closure pass.md`.)

## Observation

**Symptom (coverage gap, not a broken test).** The drums unit-test helper `render_drum`
hardcodes the legacy `Kit::V1`, while the engine's default channel-10 kit is `Kit::V3`. So
the oracles that use the bare helper guard V1, and the *default* kit — the one every album
except Slipstream renders with — has no equivalent oracle for the behaviours V3 re-voices.

**The two facts, both confirmed by reading source:**
- `crates/ferrosintesis/src/drums.rs:2615` —
  `fn render_drum(key, vel, secs) { render_drum_kit(key, vel, secs, Kit::V1) }`
  (and it passes `samples: false`, so the V3 comparison point is modeled-V3).
- `crates/ferrosintesis/src/engine.rs:1577` — `Strip::new` defaults `kit: drums::Kit::V3`;
  `engine.rs:2929-2935` selects the kit by channel-10 Program Change (`25 => V1`,
  `24 => Synth`, `40 => Brush`, `_ => V3`).

**Exact blast radius.** 13 test functions / 23 call sites use the bare helper. For **6** of
them, V1 and modeled-V3 produce different buffers today — these are the real gap:
- `kick_beater_point_superlinear` (drums.rs:3589, key 36)
- `china_splash_crash_are_distinct` (drums.rs:3643, keys 52/55/49)
- `crash_blooms_hat_does_not` (drums.rs:3695, key 49)
- `ride_ping_over_wash` (drums.rs:3980, key 51)
- `snare_wires_engage_late` (drums.rs:3998, key 38)
- `drum_velocity_shapes_timbre` (drums.rs:4198, key 36)

These are precisely the keys V3 re-voices (kick body band `drums.rs:1694`; `SNARE_TONES_V3`
`drums.rs:1758-1769`; `metal_plate` cymbals `drums.rs:1958-2039`). The remaining **7** helper
tests render byte-identically under V1 and modeled-V3 today (their keys — 42/53/58/67/68/
71-74/78/79 — hit no kit seam in either voice construction or `drum_vel_level_exp`), so they
are correct now but **latent**: they silently stop covering the default kit the moment V3
re-voices any of those keys.

**Expected.** The behaviours V3 changed should be guarded on V3 (the shipping default), not
only on V1.

**Reproduce (static).** `grep -n 'render_drum(' crates/ferrosintesis/src/drums.rs` → 1
definition + 23 calls; cross-reference the 6 keys above against the V3 kit seams cited.

## Fix

<unfixed — raised only>

## Fix landed (2026-07-24)

**The split was verified, not taken on trust.** The bug read its identical/DIFFERS split
off the kit seams rather than measuring it, so I measured first: rendering every helper key
on V1 and modelled V3 at v40/100/127. Keys **36, 38, 49, 51, 52, 55** differ; **42, 53, 58,
67, 68, 71-74, 78, 79** are byte-identical. That is exactly the bug's list — its read was
right, and now it is evidence.

**Three changes** (`crates/ferrosintesis/src/drums.rs`):

1. `render_drum` → **`render_drum_v1`** at all 23 call sites plus its definition, so the
   kit is legible where it is used. The bug is explicit that flipping the helper's default
   to V3 would be the wrong fix (it silently retargets all 13 tests), and that is not what
   this does.
2. The six kit-sensitive behaviours now run through a new `for_each_kit` helper, which
   takes the assertion body ONCE and applies it to V3 and V1 in turn, with the kit named in
   every failure message. Taking a closure rather than duplicating six test bodies matters
   here: two copies of an oracle drifting apart is the same failure class this bug is an
   instance of.
3. The false comment at the old `drums.rs:3259` — "`Kit::V1`, the legacy voice the engine
   never selects" — is corrected in place. The bug is right that leaving it would
   regenerate this report: it is where the claim came from. V1 is live (channel-10 PC 25,
   authored by all ten Slipstream movements).

**Extending the oracles to V3 immediately found something.** Three of the six FAILED on the
default kit at V1's thresholds — kick beater superlinearity (1.128x vs a 1.3x bound),
gain-normalised click growth (1.097x vs 1.3x) and ride ping-over-wash (2.90x vs 3.0x). All
three still hold DIRECTIONALLY on V3; only the margins are smaller.

I did **not** relax V1's bounds to accommodate that, and did not drop V3 from the oracles.
Each now carries a per-kit bound, and the V3 numbers are annotated in-source as **measured,
not designed**, pointing at **MM-BUG-KILN-00091** — raised to ask Arthur whether the default
kit's softer attack is the intended voicing or a regression on the kit every album but
Slipstream renders with. That is an ear call; this box has none. The alternative — picking
a V3 threshold quietly — would have buried the only measurement anyone has of the
difference.

**Coverage delta.** Before: 6 behaviours guarded on V1 only, 0 on the shipping default.
After: all 6 guarded on both, and the 7 kit-identical helper tests keep their V1-named
helper, so they no longer *look* like they cover the default kit when they do not.

**Gates.** `cargo test --release -p ferrosintesis` 661 passed / 0 failed / 26 ignored (+4
doc-tests); clippy `-D warnings` clean; `cargo fmt --check` clean. Test-only change — no
shipped code touched, so no render can move.

## Notes

- **The claim that seeded this bug was wrong and must not enter the ledger as written.**
  "The engine never selects V1" is false: `engine.rs:2932` selects `Kit::V1` on channel-10
  PC 25, and all ten Slipstream movements author it (e.g.
  `albums/fable5/Slipstream/movements/t01_wheels_up.py:84`). V1 is a live, shipping kit, held
  byte-stable by `v1_drum_render_signatures_are_stable` (drums.rs:2661). The 13 helper tests
  are **valid V1 oracles** — this is missing V3 coverage, not a test measuring a dead voice.
- **Fix the false source comment in the same change.** `drums.rs:3259-3260` carries the exact
  wrong wording ("`Kit::V1`, the legacy voice the engine never selects") and is where the
  claim came from; left in place it will regenerate this report.
- **Do not fix by flipping the helper's default to V3.** That silently retargets all 13 and
  would break the 7 currently-identical ones if V3 ever re-voices their keys. Cleaner: rename
  `render_drum` → `render_drum_v1` so the kit is legible at every call site, and add V3
  counterparts for the 6 affected behaviours.
- **Class precedent** (cite, not duplicates): `MM-BUG-KILN-00026` (brightness oracles render
  `Bowed::new`, not the shipping `BowedString`) and `MM-BUG-KILN-00004` ("the guarding oracle
  tests the wrong voice"). Same class — an oracle guarding a code path other than the shipped
  one — one layer over.
- Severity Medium: no user-audible defect and no false assertion; it is missing coverage on
  the default kit, on exactly the voices V3 changed. The identical/DIFFERS split was read off
  the two kit seams, not measured (read-only investigation).
