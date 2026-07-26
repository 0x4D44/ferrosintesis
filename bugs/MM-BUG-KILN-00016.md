# MM-BUG-KILN-00016 — Bass family (GM 32–39) is model-only; the finger/pick/slap attack lives in the LA window and is left unsampled

- **State:** Blocked
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Blocked (2026-07-25, Codex GPT-5.6-Sol; GM32–35 are complete, but GM36/37 require a real slap-bass multisample with usable provenance; Arthur must provide an owner recording or approve a discovered CC0/CC-BY source)

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
therefore **stayed Open** on the slap sub-item until the blocker was recorded below.

### Blocker (2026-07-25)

The remaining GM36/37 work is an external asset-sourcing decision, not an unattended code
fix. The repository contains fingered, picked and acoustic-pizzicato bass recordings, but
no real slap-bass source. The approved sourcing design
`wrk_docs/2026.07.19 - HLD - LA sample sourcing plus model-to-alt (GM4-8-10-11-14-15, 32-37).md`
explicitly defers GM36/37 until a clean real-slap CC0 source is hand-curated.

Unblock when Arthur either supplies an owner-recorded slap/pop take suitable for a
multisample bank, or approves a discovered CC0/CC-BY source with retained provenance and
any required attribution. Reusing the existing finger/pick assets would not resolve the
recorded identity defect.

## Notes

- Enhancement filed as a bug per the maintainer routing decision (2026-07-18).
- Net-new CC0 sourcing → sequence with MM-BUG-KILN-00015 after the reuse-only
  fixes. Slap bass onset is the most identity-critical, worth prioritising within
  the family.

### Focused source search (2026-07-26)

Arthur authorised a focused search for a CC0/CC-BY source. No immediately
admissible live multisample was found:

- The strongest match is Jonpv's 2019 public-domain bank: real six-string bass,
  slap from B0–C#2, pop from D2–F3, sampled per fret with three round robins.
  The creator's post explicitly dedicates it to the public domain, but both
  Dropbox links now return an error and the Wayback Machine did not archive the
  asset. Source:
  <https://www.reddit.com/r/Bitwig/comments/e5jt15/slap_bass_multisample_96mb_3x_round_robin_sampled/>.
- JohnSlap is live and contains slap/pop samples across two octaves, but its
  repository and sample release contain no redistribution licence. It is not
  usable without an explicit licence from its author. Source:
  <https://github.com/johnmanjohnston/JohnSlap>.
- Karoryfer's CC0 Swagbass contains five real muted-slap noise round robins, but
  no pitched slap/pop multisample. It could add an unpitched transient but cannot
  establish distinct GM36 slap and GM37 pop identities. Source:
  <https://github.com/sfzinstruments/karoryfer.swagbass>.
- The live CC0 Freesound candidates are single riffs/noises, or a synthesized
  two-note imitation, rather than an isolated real multisample bank.

The bug remains Blocked. It can be unblocked by recovering the Jonpv archive,
obtaining an explicit redistributable licence for JohnSlap, finding another
live CC0/CC-BY bank, or supplying an owner recording.
