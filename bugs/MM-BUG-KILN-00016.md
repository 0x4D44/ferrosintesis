# MM-BUG-KILN-00016 — GM36/37 slap and pop lack modeled string–fret collision identity

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** synth
- **Raised:** 2026-07-18
- **Owner:** deltic:gpt-5.5
- **Owner role:** fix
- **Owner run:** fix-20260727T121001Z-p9812-n920194600-c80
- **Owner host:** KILN
- **Owner branch:** task/bug-MM-BUG-KILN-00016-run-fix-20260727T121001Z-p9812-n920194600-c80
- **Owner base:** e9cfdd99df431399340ce16c47976dda3c3fa236
- **Owner fingerprint:** -
- **Owner since:** 2026-07-27T12:10:01Z
- **Owner until:** 2026-07-27T13:05:34Z
- **Verify retry after:** -
- **Held branch:** -
- **Legacy fixed run:** -
- **Attempts:** fix=0, doubt=1, indeterminate=0
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit) → Blocked (2026-07-25, Codex GPT-5.6-Sol; GM32–35 are complete, but GM36/37 require a real slap-bass multisample with usable provenance; Arthur must provide an owner recording or approve a discovered CC0/CC-BY source) → Open (2026-07-26, Arthur approved replacing the unavailable GM36/37 sample requirement with researched string–fret collision synthesis) → Fixed (2026-07-27, deltic:auto role=fix run=fix-20260726T223701Z-p9812-n951988700-c12 branch=task/bug-MM-BUG-KILN-00016-run-fix-20260726T223701Z-p9812-n951988700-c12 code=43fab4a47298c7938fcbfa7fa6e2b00798677827 gate=focused+render-diff model=codex@xhigh; held branch recovered by Codex) → Open (2026-07-27, deltic:auto role=verify run=verify-20260727T115901Z-p9812-n535270700-c79 verified_fix_run=fix-20260726T223701Z-p9812-n951988700-c12 verdict=doubt reason=gates-green-and-the-new-string-fret-collision-is-real-contained-and-well-tested model=claude)

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

### Fix summary (2026-07-27, deltic:auto run=fix-20260726T223701Z-p9812-n951988700-c12 code=43fab4a47298c7938fcbfa7fa6e2b00798677827 gate=focused+render-diff)

Agent-reported summary: Fixed MM-BUG-KILN-00016 by adding a modeled, attack-bounded string-fret collision path for GM36 slap bass and GM37 slap-pop bass. The original observation reproduced: those programs were direct Pluck routes whose identity was carried by a post-output click burst, so the old slap oracle passed without any modeled fret collision. The new contact stage is deterministic, velocity-thresholded, passive sample-by-sample, and inserted inside the KS loop before pickup/body/output filtering. The regression keeps the legacy burst enabled in a contact-disabled lesion and proves the lesion no longer satisfies the slap/pop identity checks. Recovery expanded the acceptance grid across three registers and velocities, retired the contact runtime after its attack window, and confirmed catalog isolation, lifecycle behaviour, render cost, and A/B reachability.

Root cause: GM36/37 authored only the legacy post-output click_post burst and had no string-path contact mechanism. The existing oracle measured the first 3 ms high-frequency transient, which the output burst could satisfy even though the modeled string never collided with the fretboard.

Changed:
- crates/ferrosintesis/src/voices.rs: added FretContactSpec, FretContact runtime, SLAP/SLAP_POP contact voicing, KS-loop wiring, and regression tests
- crates/ferrosintesis/src/voices.rs: added SLAP_POP to the shared pluck preset stability sweep
- crates/ferrosintesis/src/voices.rs: added low/mid/high-register identity, determinism, pitch, finite-output, runtime-retirement, note-off, and reaping coverage
- crates/ferrosintesis/src/altbank.rs: set the frozen PIZZ PluckPreset to fret_contact None

Tests:
- FAIL-FIRST observed: cargo test -p ferrosintesis voices::tests::slap_pop_ -- --nocapture failed with zero contact residual before wiring
- `cargo test -p ferrosintesis voices::tests::slap -- --nocapture` passed: 5 tests.
- `cargo test -p ferrosintesis --no-default-features voices::tests::slap -- --nocapture` passed: 5 tests.
- `cargo test -p ferrosintesis voices::tests::coupled_loop_margin_holds -- --nocapture` passed.
- `cargo test -p ferrosintesis voices::tests::v2_untouched_pluck_signatures_are_stable -- --nocapture` passed.
- `cargo test -p ferrosintesis voices::tests::default_bass_family_held_levels_stay_together -- --nocapture` passed; GM32–39 span stayed within the 9.25 dB gate.
- Full `albums/**/*.mid` render diff at 11,025 Hz: 124 expected same, 0 contamination, 0 not reached; the catalog contains no GM36/37 events.
- Full `demos/**/*.mid` render diff at 11,025 Hz: 4 expected changed, 13 expected same, 0 contamination, 0 not reached.
- The loudness-normalized 18-note low/mid/high × soft/medium/hard audition matrix is in `C:\Users\marti\AppData\Local\Temp\MM-BUG-KILN-00016\before.wav` and `after.wav`.
- Three alternating 44.1 kHz renders of that matrix averaged 6.872 s baseline and 6.772 s candidate (0.986×).
- `cargo fmt --package ferrosintesis` and `git diff --check` passed.

No Cargo manifest, lockfile, journal, scratchpad, or lesson file changed.

### Verification summary (2026-07-27, deltic:auto run=verify-20260727T115901Z-p9812-n535270700-c79 verified_fix_run=fix-20260726T223701Z-p9812-n951988700-c12 verdict=doubt)

Verifier note: Gates green and the new string-fret collision is real, contained and well-tested, but acceptance-contract item 6 is unevidenced: the retained post-output click burst was never lesioned, and the new identity oracle measures 6-30 ms, excluding the 0-3 ms window the burst occupies. — HEAD abbfbf3 on trunk worktree. GATES (all green, observed): `cargo fmt --all -- --check` clean; `cargo clippy --workspace --all-targets -- -D warnings` clean (Finished dev profile); `cargo test --workspace` exit 0 (ferrosintesis 773 passed/0 failed/36 ignored, every other crate 0 failed); `cargo test -p ferrosintesi...

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

At the end of that source search, the bug remained Blocked pending recovery of
the Jonpv archive, an explicit redistributable JohnSlap licence, another live
CC0/CC-BY bank, or an owner recording. The modeled decision below supersedes
that asset requirement for GM36/37.

### Decision and researched implementation contract — 2026-07-26

Arthur approved a **modeled string–fret collision** route for the remaining
GM36/37 scope. Do not continue asset sourcing or add a sample dependency for
this bug. GM32–35's already-landed sample layers remain unchanged, GM38/39
remain synthesized basses, and MM-BUG-KILN-00085 independently owns the
alternate-bank additive crossfade.

Relevant prior art:

- Kramer et al. model finger, pick, muted, slap-thumb, and slap-pluck within one
  electric-bass digital waveguide. Thumb slap uses initial velocity with zero
  displacement; slap-pluck uses a plucked displacement; both enable fret
  collision:
  <https://dihana.cps.unizar.es/proceedings/ICASSP/2012/pdfs/0000353.pdf>.
- Fraunhofer's project summary and listening study confirm that those distinct
  physical playing-technique configurations can produce accepted synthesized
  bass:
  <https://www.idmt.fraunhofer.de/en/publications/datasets/bass_synthesis.html>.
- Issanchou et al. experimentally validate that slap/pop's percussive transient
  comes from nonlinear string–fret contact. Gesture, plucking position, fret
  clearance, and contact stiffness affect the number, duration, and spectrum of
  collisions:
  <https://perso.ensta.fr/~doare/files/issanchou_apac2018.pdf>.
- Edinburgh's NESS work demonstrates the missing amplitude-dependent timbral
  change in a linear plucked string and the fretboard collision mechanism that
  restores it:
  <https://www.ness.music.ed.ac.uk/archives/systems/guitarfretboard-interactions.html>.

Apply those principles at the existing `Pluck` model's scale:

1. Add a bounded, deterministic contact stage to the existing waveguide/string
   path for `SLAP` and `SLAP_POP` only. The contact must modify or re-excite the
   string before pickup, body, and output filtering; another output-only noise
   burst does not resolve the defect.
2. First identify what physical quantity the current travelling-wave state
   represents. Implement a stable conditional reflection/contact law at a
   small number of fretboard locations, or an equivalent displacement-derived
   junction. Do not assume a delay-line sample is displacement without proving
   the representation, and do not import a full modal/FDTD solver.
3. Voice GM36 thumb slap as a predominantly initial-velocity gesture toward the
   fretboard, with little initial displacement and an early, weighty collision
   response.
4. Voice GM37 pop as a large near-bridge displacement/release that rebounds
   into the frets, producing a brighter, thinner, multi-contact transient.
   Preserve the existing settled pitch and shorter ring.
5. Make collision strength and duration respond naturally to velocity. Gentle
   notes must not chatter; harder notes should produce more contact energy and
   spectral enrichment. Bound reflection/energy injection so no contact can
   create runaway gain, persistent buzz, aliasing, or unstable pitch.
6. Retain the existing post-filter burst only if a level-matched lesion proves
   it contributes a small acoustic contact detail after the string collision
   exists. It must no longer carry the slap/pop identity by itself.
7. Keep every non-slap `PluckPreset`, all existing controls, note-off/reaping,
   seeded determinism, and the GM32–35 and GM38/39 routes unchanged.

The fail-first regression evidence must prove:

- a contact-disabled lesion no longer satisfies the complete slap/pop identity
  oracle, even if the old output burst remains;
- collision energy grows superlinearly with velocity, occurs only during a
  bounded attack interval, and is negligible below the intended contact
  threshold;
- GM36 and GM37 remain distinct from fingered bass and from each other across
  representative low, middle, and high keys and soft, medium, and hard
  velocities;
- settled fundamental pitch, decay ordering, finite output, deterministic
  rendering, note-off, and voice reaping remain correct;
- the collision path has a measured render-cost ceiling and does not alter a
  non-slap preset bitwise.

After focused tests pass, run the required full catalog render diff and create
level-matched current-versus-candidate GM36/37 A/B renders across the tested
register and velocity range. Land the implementation as **Fixed**, not Closed,
for independent verification and final listening.
