# MM-BUG-KILN-00296 — CLI prints and silently accepts option values the render did not use

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** crates/ferrosintesis-cli
- **Raised:** 2026-08-17T22:49:17Z
- **Discovery source:** Agent
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
- **State history:** Open (2026-08-17T22:49:17Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom 1 — the printed echo time contradicts the render.** `ferrosintesis song.mid
--delay 60000` prints

```
song: 3.21 min, 4812 events, 9 markers, 96 bpm at open (echo 60000 ms)
```

while the render actually uses **10000 ms**. `--delay nan` prints `echo NaN ms` and renders
375 ms. This is a wrong number, not merely a missing warning.

**Symptom 2 — every other knob is clamped in silence.** `--rate 500000` renders at 384000,
`--rate 100` at 8000, `--wet 5` at 1.0, `--tail 99999` at 3600, and `--wet nan` at the
default 0.32. Nothing is printed on any of these paths, and no exit code changes. A user
who mistypes a knob gets a plausible-looking render at settings they did not ask for and
cannot discover.

**Root cause.** Every `Options` builder sanitizes its argument:
`with_sample_rate` → `sanitize_sample_rate`, clamped to `MIN_SAMPLE_RATE..=MAX_SAMPLE_RATE`
(8000..=384000) at `crates/ferrosintesis/src/engine.rs:1838-1841`, `1775-1777`, `1741-1743`;
`with_reverb` clamped 0..=1 at `engine.rs:1845-1848`; `with_tail` clamped 0..=`MAX_TAIL_S`
(3600) at `engine.rs:1853-1856`; `with_echo` clamped 0..=`MAX_ECHO_S` (10) at
`engine.rs:1869-1872`. All four route through `sanitize_knob` (`engine.rs:1766-1772`), which
additionally substitutes the **default** for a non-finite value — and both `"nan"` and
`"inf"` parse successfully as `f32` in the CLI's `.parse()` at
`crates/ferrosintesis-cli/src/main.rs:56-88`.

The library states plainly that reporting is the caller's job — `engine.rs:1760-1761`: "The
accessors report the clamped value, so a caller that cares can see what it actually got."
The CLI builds `opt` at `main.rs:146-152` and then never calls `opt.sample_rate()`,
`opt.reverb()`, `opt.tail()` or `opt.echo()` anywhere. Its two verbose blocks
(`main.rs:129-142` and `main.rs:175-188`) report song stats and render stats only.

For symptom 1 specifically, `delay_s` is computed at `main.rs:125-128`, printed as
`delay_s * 1000.0` at `main.rs:141`, and only afterwards clamped inside `with_echo` at
`main.rs:150`. The default branch (`main.rs:127`) pre-clamps to 0.20..0.62, so the *default*
print is always truthful — the divergence exists only for user-supplied values, which is
exactly the case where the user needs the number to be right.

**Expected.** The CLI reports the values the render used, and says so when a requested value
was changed.

**Actual.** It prints a pre-clamp value for the echo and prints nothing at all for the other
four knobs.

**Not documented anywhere the user looks.** `crates/ferrosintesis-cli/README.md:31-34` gives
a bare range for `--wet` only and nothing for `--rate` / `--tail` / `--delay`; the clamps are
absent from the module doc-comment (`main.rs:1-10`) and from `usage()` (`main.rs:21-23`). The
library documents them (`engine.rs:1785-1791`), but that is the library's API contract, not a
CLI diagnostic.

## Fix

<unfixed — raised only>

Suggested shape — read the knobs back from `opt` after it is built, which is what the
library's own doc-comment tells callers to do:

1. Move the verbose header (`main.rs:129-142`) to *after* `opt` is constructed
   (`main.rs:146-152`) and print `opt.echo() * 1000.0` instead of the raw `delay_s`. That
   alone fixes symptom 1 and cannot regress the default path, whose value is already inside
   the clamp.
2. Keep the four requested values, compare each against its accessor, and emit one
   `warning: --<flag> <requested> is out of range; using <effective>` line per changed knob.
   Emit it regardless of `-q`, or the quiet catalog path hides exactly the mistakes it
   should surface — decide deliberately and state which.
3. Regression: assert that `--delay 60000` reports `echo 10000 ms`, and that `--rate 500000`
   warns. Confirm both fail before the fix. The crate currently has **no** test of argument
   handling at all — `src/main.rs` holds one test and it is about the `embedded-samples`
   feature flag (`main.rs:191-200`).

## Notes

- `--wet nan` / `--tail inf` are worth a test of their own: `f32::from_str` accepts both, so
  they reach `sanitize_knob`'s non-finite branch and silently become the default rather than
  being rejected at parse time. Rejecting non-finite input in the CLI's parse step is a
  reasonable alternative fix for that half.
- Raised by an autonomous read-only code-review pass; established by reading the CLI and the
  library builders. The clamping behaviour is proven by the library source and its own
  tests; the printed-value divergence is proven by statement order in `main.rs`. Neither was
  reproduced by running the binary — this pass does not run the app.
