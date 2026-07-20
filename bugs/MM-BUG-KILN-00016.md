# MM-BUG-KILN-00016 — Bass family (GM 32–39) is model-only; the finger/pick/slap attack lives in the LA window and is left unsampled

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sampler
- **Raised:** 2026-07-18
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit)

## Observation

The bass arms (`crates/ferrosintesis/src/voices.rs:~10858`) are bare `Pluck::new`
(upright/fingered/picked/slap/fretless) plus `SynthBass` for 38/39 — no LA wrap.
The finger/pick/slap attack is the defining cue of an acoustic or electric bass
and sits squarely in the onset window the LA layer owns. Leaving it modeled is
inconsistent with the already-sampled nylon/steel/sitar/banjo plucks that use the
identical wrap (`voices.rs:~10817`).

## Fix

Add a sampled pluck onset for GM 32–39 (acoustic/fingered/picked/slap) using the
proven `LaVoice::wrap` — mostly a sourcing + root-measurement task, not new DSP,
since the wrap is already validated for the other plucks.

### Progress (2026-07-20) — 32–35 LANDED; slap 36/37 deferred (bug STAYS OPEN)

Acoustic pizz bass 32 (VSCO Solo Contrabass Pizz, CC0, `1a033e3`) and electric bass fingered 33 /
picked 34 / fretless 35 (FreePats RBX, CC0, new `-bass` crate, `dbef98a`) landed — real onset as
default, pure model as the CC0!=0 alt, oracle + render-diff (0 contamination) green. GM 38/39 synth
bass stay model-only (they are *synth*). **Slap 36/37 is deferred** (2026-07-19 sourcing HLD,
decision 4): no clean real-slap CC0/CC-BY multisample exists — its own future mini-hunt. This bug
therefore **stays Open** on the slap sub-item.

## Notes

- Enhancement filed as a bug per the maintainer routing decision (2026-07-18).
- Net-new CC0 sourcing → sequence with MM-BUG-KILN-00015 after the reuse-only
  fixes. Slap bass onset is the most identity-critical, worth prioritising within
  the family.
