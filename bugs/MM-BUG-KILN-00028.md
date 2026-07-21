# MM-BUG-KILN-00028 — Channel-10 room-reverb send ignores authored CC91; a dry kit is unreachable from MIDI

- **State:** Blocked
- **Priority:** Could
- **Severity:** Low
- **Area:** engine
- **Raised:** 2026-07-20
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
- **State history:** Open (2026-07-20, raised from the GM instrument sweep audit — Claude Fable 5) → Blocked (2026-07-21, Claude Opus 4.8 — the sketch's premise is false: 86 catalog tracks author ch-10 CC91, so coupling the room send to it re-mixes established albums by 0.5×–2.9×, failing the controller-feature render-diff rule. Needs a design/ears decision from Arthur.)

## Observation

The channel-10 drum room-reverb send is a fixed constant (`ROOM_SEND`,
`crates/ferrosintesis/src/engine.rs`, grep `ROOM_SEND`) applied unconditionally at
the drum mix points. An authored CC91 on channel 10 therefore cannot dry the kit —
a dry-drums bar is impossible from MIDI.

This runs against the crate's own controller doctrine ("an unauthored controller
is inert" — with the implied converse that an authored one works), which every
melodic channel honours via its CC91 reverb send. It also contradicts the
README's Controllers table, which documents CC91 as the reverb send with no
channel-10 carve-out.

## Fix

<blocked — needs a design/ears decision, see Blocking analysis below>

Sketch (as raised): scale the room send by the channel's CC91 only when the channel
has authored CC91 (unauthored keeps today's fixed default — exact-render-preserving
for every existing file, per the opt-in controller policy). Any diff at all on
albums that never author ch-10 CC91 would be a bug (controller-feature rule).

## Blocking analysis (2026-07-21, Claude Opus 4.8)

The sketch was prototyped and worked mechanically (a `reverb_authored` flag gating
`ROOM_SEND * (reverb_send / DEFAULT_REVERB_SEND)` at the two drum-mix sites, with
unit + isolated-render regression tests green). But its stated premise — "exact-
render-preserving for every existing file" — is **false**:

- A stdlib MIDI scan of the whole catalog finds **86 of 124 album tracks author
  CC91 on channel 10** (drum channel). They span the fable5, gpt5-5, gpt5-6 and
  gpt5-3-spark albums.
- Their authored CC91 values range **20–110**, which under the coupling would scale
  the drum-room send by **0.5× to 2.9×** vs today's fixed `ROOM_SEND` (value
  histogram: 25→0.66×, 40→1.05×, 58→1.52×, 110→2.89×, etc.). So the fix retroactively
  **re-mixes the drum-room ambience of 86 established album tracks**, most of which
  were hand-tuned against the old fixed room.

This fails the crate's controller-feature render-diff rule ("for a pure controller
feature, any diff at all is a bug" — the feature must be **inert on existing
content**). CC91 is *the* documented reverb controller and is broadly authored, so
there is **no inert-on-existing-content fix**: any CC91→room coupling changes the
catalog. Making the dry-kit capability reachable safely is therefore a design/ears
call for the maintainer — e.g. a *new dedicated* controller for the drum-room dry/wet
(leaving CC91's hall coupling as-is), or an explicit decision to accept and re-tune
the catalog re-mix. Same class as MM-BUG-KILN-00019 (ear-in-the-loop mix change).

**Missing input to unblock:** Arthur's decision on the mechanism (new controller vs
accept catalog re-mix) and, if the latter, an ears pass over the affected 86 tracks.

## Notes

- Surfaced by the 2026-07-20 GM instrument sweep (drums auditor); also flagged as
  item 8 of the scratchpad README-contradiction entry (2026.07.12).
- The docs sweep of 2026-07-20 documents the current behaviour honestly in the
  README Controllers table; this bug tracks making the behaviour match the
  doctrine instead.
