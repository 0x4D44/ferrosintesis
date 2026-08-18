# MM-BUG-CRUCIBLE-00039 — Packaged FLAC banks pin EXPECTED_BYTES to one ffmpeg build, so a documented re-bake fails the crate size oracle

- **State:** Open
- **Priority:** Should
- **Severity:** Medium
- **Area:** sample generation / bank reproducibility
- **Raised:** 2026-08-18T00:08:02Z
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
- **State history:** Open (2026-08-18T00:08:02Z, raised via `deltic bugs new` model=claude-opus-5@high)

## Observation

**Symptom.** Every packaged FLAC bank carries the version string of the exact ffmpeg build
that encoded it, and each crate pins the aggregate byte total of its bank. Re-baking on a
box with a different ffmpeg therefore produces a byte-different bank and fails the crate's
own size oracle — with a message that names neither ffmpeg nor a version.

**Expected.** The documented regeneration recipe reproduces the committed bank, or the
byte pin states the encoder it is pinned to so the failure is self-explaining.

**Actual — measured, not inferred.** The committed FLACs embed a VORBIS_COMMENT block
holding the libavformat version twice. Hex dump of the metadata block following STREAMINFO
in `crates/ferrosintesis-samples-bass/samples/fingerbass_E1.flac` (offset 42, 96 bytes):

```
0000042 004  \0  \0   .  \r  \0  \0  \0   L   a   v   f   6   2   .   1
0000058   2   .   1   0   1 001  \0  \0  \0 025  \0  \0  \0   e   n   c
0000074   o   d   e   r   =   L   a   v   f   6   2   .   1   2   .   1
0000090   0   1 201  \0      \0  \0  \0  \0  \0  \0  \0  \0  \0  \0  \0
```

That is block type 4 (VORBIS_COMMENT), a 13-byte vendor string `Lavf62.12.101`, and a
21-byte `encoder=Lavf62.12.101` tag. Confirmed identical in
`crates/ferrosintesis-samples-bass/samples/pickbass_E2.flac`.

The chain that turns this into a red test:

- `tools/ferrosintesis-samples/prepare.py:4335-4341` — `_encode_flac` shells out to
  whatever `ffmpeg` is on `PATH` (`-c:a flac -compression_level 12`). No version is pinned,
  recorded, or checked; `_require_ffmpeg` (`prepare.py:4324-4332`) only tests presence.
- `tools/ferrosintesis-samples/gen_crate_lib.py:113` computes `EXPECTED_BYTES` as
  `sum(os.path.getsize(...))` over the on-disk bank, emitted at `:172`.
- `crates/ferrosintesis-samples-bass/src/lib.rs:84` holds the result,
  `EXPECTED_BYTES = 365281`, asserted at `:104-107` as
  `"every_sample_is_a_nonempty_bank_file_with_the_expected_size"`.

A vendor string of a different length changes each file's size, twice over. A move from
`Lavf62.12.101` (13 bytes) to a 12-byte or 14-byte version shifts every one of the 13 files
and the aggregate by tens of bytes — far outside any tolerance, since the assertion is
exact equality.

**Why the bit-exactness check does not cover this.** `prepare.py:4442` verifies
`_decode_flac_pcm(part) == _read_wav_pcm(wav_path)` and raises `"FLAC encode was not
bit-exact"` otherwise. That is a real and valuable guarantee, but it is about the *decoded
PCM*, not the *container bytes*. A different ffmpeg passes that check and still produces a
different file.

**Concrete failure.** An agent on a fleet box whose ffmpeg is not 62.12.101 follows
`crates/ferrosintesis-samples-bass/README.md:11-12` and runs
`python3 tools/ferrosintesis-samples/prepare.py --only=fingerbass,pickbass`. The bake
succeeds, every PCM check passes, the audio is identical. `cargo test -p
ferrosintesis-samples-bass` then fails with `assertion left == right` on two integers, one
of which is named `EXPECTED_BYTES`. Nothing in the message, the test name, the crate README
or `PROVENANCE.md` points at the encoder. The obvious next move — re-pinning
`EXPECTED_BYTES` to make the test pass — silently replaces the published bank's bytes on
that agent's box and moves the pin to *its* ffmpeg, so the next box with the original
ffmpeg hits the same wall in reverse.

**Scope.** Not bass-specific. `publish_pending_banks` (`prepare.py:4412-4452`) is the one
publication path for every FLAC bank, and `PACKAGED_EXT = ".flac"` (`prepare.py:1225`)
since 2026.08.16, so all 24 sample crates carry an encoder-pinned byte total. Bass is
simply where this pass looked.

Static review only. No bake, build, test, or ffmpeg invocation ran. The vendor strings are
read directly from the committed bytes; that a *different* ffmpeg emits a different vendor
string is inference from the FLAC format and from ffmpeg writing its own version there,
not something observed on a second toolchain here.

## Fix

Unfixed. Raised for the fix-open-bugs loop; this review did not change code.

Pick one reproducibility contract and write it down, in the spirit of closed
`MM-BUG-KILN-00095`:

1. **Make the bytes encoder-independent.** Pass `-fflags +bitexact` (or strip the
   VORBIS_COMMENT block after encode) so no vendor string is embedded. Cheapest, and it
   makes the byte pin mean what the crate implies it means. Verify by re-baking one bank on
   two ffmpeg versions and `cmp`-ing.
2. **Pin the encoder explicitly.** Record the required ffmpeg version alongside the bank,
   check it in `_require_ffmpeg`, and name it in each `PROVENANCE.md`. Honest, but it makes
   every fleet box's ffmpeg load-bearing.
3. **Stop pinning container bytes.** Replace `EXPECTED_BYTES` with a per-file decoded-PCM
   assertion — which also closes MM-BUG-CRUCIBLE-00040 — and drop the aggregate.

Whichever is chosen, the failure message must name ffmpeg. Add a negative control that
mutates a vendor string and proves the new check reports the encoder rather than an
unexplained integer mismatch.

## Notes

- Related but distinct: `MM-BUG-KILN-00292` (fret-noise recipe omits the required ffmpeg
  executable) is about ffmpeg's *presence*; this is about its *version*. The bass README
  has the -00292 defect too — `README.md:11-12` presents the recipe as self-contained
  though `prepare.py:5671` now hard-requires ffmpeg — recorded here rather than filed
  separately because the per-crate instances of that class are already being tracked.
- Option 1 is the only one that leaves a re-bake byte-reproducible across the fleet, which
  is the property CLAUDE.md's offline/first-party build story depends on.
- Estimated effort: Small for option 1 plus its two-toolchain proof; Medium for option 3.
