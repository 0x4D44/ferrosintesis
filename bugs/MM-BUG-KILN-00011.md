# MM-BUG-KILN-00011 — CC7 volume and CC10 pan bypass the controller slew that CC11 gets, so a fade or pan sweep steps at block boundaries

- **State:** Fixed (awaiting close)
- **Priority:** Should
- **Severity:** Medium
- **Area:** engine
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
- **State history:** Open (2026-07-18, raised by Claude Opus 4.8 (1M) — ferrosintesis subsystem audit); Fixed (2026-07-18, Claude Opus 4.8 (1M) — CC7/CC10 routed through a prime-on-first-block slew like CC11; render-diff 20 changed/89 same reconciles exactly to the multi-tick CC7/CC10 set, 0 contamination. NOTE: the bug's "catalog sets CC7/CC10 once, any diff is a bug" premise was false — 24 album MIDIs automate CC10 pan; Arthur chose to slew both, accepting the pan-automation albums re-render as a spatial-smoothing improvement.)

## Observation

CC11 (expression) is smoothed through `expr_smooth` (`engine.rs:~2269`), but CC7
volume (`engine.rs:~1652`, `s.volume = v*v`, no smoothing) and CC10 pan
(`engine.rs:~1653`, set directly) are not. Strip gain `g` and pan angle `theta`
are recomputed once per 64-sample block from the un-slewed values, so a CC7 fade
or CC10 pan sweep steps hard at block boundaries (~1.45 ms grid) instead of
ramping — a zipper/stepping artefact.

It is an inconsistency the "faithful GM player" claim exposes: expression is
smoothed, but volume — which arbitrary GM files use for fades — is not. The
fable5 albums dodge it by doing dynamics on CC11 and setting CC7 once (e.g.
`albums/fable5/.../build ... engine.py`), so it stays latent in-repo but bites
foreign GM input.

## Fix

Route CC7 volume and CC10 pan through the existing `expr_smooth` (or a dedicated
per-strip slew) so their gain/pan ramp per-sample like CC11. Trivial reuse of
machinery already present.

## Notes

- Pure controller change: on the fable5 albums (CC7 set once) *any* render-diff
  would be a bug, so it is cheaply verifiable against the catalog.
- Related mono-compat concern (pan-authored Haas widening) is a separate, lower
  item parked in scratchpad.
