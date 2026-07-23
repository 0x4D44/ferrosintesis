"""Tests for the B1 ladder slicer.

Run from anywhere, with stdin closed:
    python -m unittest discover -s tools/b1-slice -v < /dev/null

The four things most likely to be silently wrong are covered directly:

  * the 24-bit decode, against a fixture whose sample values are known by
    construction (reading 24-bit data as 16-bit produces plausible noise, so
    "the numbers looked sensible" proves nothing);
  * the onset detector, on a synthetic multi-note signal whose notes differ by
    25 dB — the level spread that defeats a fixed threshold;
  * the inharmonic pitch fit, on a synthesised stiff string with a KNOWN f0 and
    B. The test tone is harmonically RICH: a pure sine can be identified from
    its value and slope alone, so a sine test would pass a broken estimator;
  * the ladder matcher, including its missing / extra / mismatch reporting.
"""

import math
import os
import struct
import sys
import tempfile
import unittest
from array import array

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import slice as b1  # noqa: E402


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

def pack24(values):
    """Signed ints -> 24-bit little-endian bytes."""
    out = bytearray()
    for v in values:
        out += int(v).to_bytes(3, "little", signed=True)
    return bytes(out)


def write_wav24(path, left, right, sample_rate=48000, bext=636):
    """Write a 24-bit stereo WAV with a bext chunk, like the DR-05 does."""
    assert len(left) == len(right)
    data = bytearray()
    for a, b in zip(left, right):
        data += int(a).to_bytes(3, "little", signed=True)
        data += int(b).to_bytes(3, "little", signed=True)
    fmt = struct.pack("<4sIHHIIHH", b"fmt ", 16, 1, 2, sample_rate,
                      sample_rate * 6, 6, 24)
    chunks = bytearray(fmt)
    if bext:
        chunks += struct.pack("<4sI", b"bext", bext) + bytes(bext)
    chunks += struct.pack("<4sI", b"data", len(data)) + data
    with open(path, "wb") as f:
        f.write(struct.pack("<4sI4s", b"RIFF", 4 + len(chunks), b"WAVE"))
        f.write(chunks)


def stiff_string(n, sr, f0, b, partials=16, decay=2.0, seed=1):
    """A synthesised stiff string: partials at k*f0*sqrt(1+B k^2).

    Harmonically rich by construction, with the 1/k amplitude roll-off and
    per-partial decay of a real string, plus scrambled phases so no partial
    can be recovered from waveform slope alone. Higher partials damp faster,
    as ~1/sqrt(k) — a piano's measured trend, and slow enough that a real note
    still shows a dozen partials a second after the strike.
    """
    out = [0.0] * n
    rnd = seed
    for k in range(1, partials + 1):
        fk = k * f0 * math.sqrt(1.0 + b * k * k)
        if fk >= sr / 2.0:
            break
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        phase = 2.0 * math.pi * (rnd / 0x7FFFFFFF)
        amp = 1.0 / k
        tau = decay / math.sqrt(k)
        w = 2.0 * math.pi * fk / sr
        for i in range(n):
            out[i] += amp * math.exp(-i / (tau * sr)) * math.sin(w * i + phase)
    peak = max(abs(v) for v in out) or 1.0
    return [v / peak for v in out]


def noise(n, seed=7):
    rnd = seed
    out = []
    for _ in range(n):
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        out.append((rnd / 0x3FFFFFFF) - 1.0)
    return out


# ---------------------------------------------------------------------------
# 24-bit decode  (highest-risk step)
# ---------------------------------------------------------------------------

class TestDecode24(unittest.TestCase):
    KNOWN = [0, 1, -1, 127, -128, 32767, -32768, 8388607, -8388608,
             4194304, -4194304, 65536, -65536, 3, -3]

    def test_known_values_round_trip_exactly(self):
        buf = pack24(self.KNOWN)
        got = b1.decode_pcm(buf, 24)
        self.assertEqual(len(got), len(self.KNOWN))
        for want, have in zip(self.KNOWN, got):
            self.assertAlmostEqual(have, want / 8388608.0, places=6,
                                   msg=f"sample {want} decoded as {have}")

    def test_full_scale_endpoints(self):
        got = b1.decode_pcm(pack24([8388607, -8388608]), 24)
        self.assertAlmostEqual(got[0], 8388607 / 8388608.0, places=7)
        self.assertAlmostEqual(got[1], -1.0, places=7)

    def test_sign_extension_is_not_a_16_bit_read(self):
        # 0x800000 is -8388608 as 24-bit; its low two bytes are 0x0000, so a
        # 16-bit reader sees 0 and a 24-bit reader sees full-scale negative.
        got = b1.decode_pcm(pack24([-8388608]), 24)
        self.assertLess(got[0], -0.99)

    def test_all_three_bytes_are_used(self):
        # differs from 0 only in the MIDDLE byte
        got = b1.decode_pcm(pack24([0x000100]), 24)
        self.assertAlmostEqual(got[0], 256 / 8388608.0, places=9)
        # differs from 0 only in the LOW byte
        got = b1.decode_pcm(pack24([0x000001]), 24)
        self.assertAlmostEqual(got[0], 1 / 8388608.0, places=9)

    def test_decode_is_chunk_boundary_safe(self):
        vals = [((i * 7919) % 16777216) - 8388608 for i in range((1 << 20) + 5)]
        got = b1.decode_pcm(pack24(vals), 24)
        self.assertEqual(len(got), len(vals))
        for i in (0, 1, (1 << 20) - 1, 1 << 20, len(vals) - 1):
            self.assertAlmostEqual(got[i], vals[i] / 8388608.0, places=6)


class TestRiff(unittest.TestCase):
    def test_header_walk_finds_data_past_a_bext_chunk(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.wav")
            left = [1000, 2000, 3000, 4000]
            right = [-1000, -2000, -3000, -4000]
            write_wav24(p, left, right)
            info = b1.read_wav_info(p)
            self.assertEqual(info.channels, 2)
            self.assertEqual(info.bits, 24)
            self.assertEqual(info.sample_rate, 48000)
            self.assertEqual(info.frames, 4)
            # 12 RIFF + 24 fmt + 8+636 bext + 8 data header
            self.assertEqual(info.data_offset, 12 + 24 + 8 + 636 + 8)

    def test_channel_extraction_takes_l_and_never_sums(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.wav")
            left = [1000, 2000, 3000, 4000]
            right = [-7777, -8888, -9999, -11111]
            write_wav24(p, left, right)
            info = b1.read_wav_info(p)
            raw = b1.read_frames(info, 0, info.frames)
            lb = b1.channel_bytes(raw, info, 0)
            self.assertEqual(lb, pack24(left))
            rb = b1.channel_bytes(raw, info, 1)
            self.assertEqual(rb, pack24(right))
            got = b1.decode_pcm(lb, 24)
            for want, have in zip(left, got):
                self.assertAlmostEqual(have, want / 8388608.0, places=7)

    def test_slice_bytes_are_bit_exact(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.wav")
            left = [((i * 104729) % 16777216) - 8388608 for i in range(500)]
            right = [0] * 500
            write_wav24(p, left, right)
            info = b1.read_wav_info(p)
            raw = b1.read_frames(info, 100, 200)
            pcm = b1.channel_bytes(raw, info, 0)
            self.assertEqual(pcm, pack24(left[100:300]))

    def test_written_wav_reads_back_identically(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "out.wav")
            vals = [((i * 7717) % 16777216) - 8388608 for i in range(333)]
            b1.write_wav_mono(p, pack24(vals), 24, 48000)
            info = b1.read_wav_info(p)
            self.assertEqual(info.channels, 1)
            self.assertEqual(info.bits, 24)
            self.assertEqual(info.frames, 333)
            raw = b1.read_frames(info, 0, info.frames)
            self.assertEqual(b1.channel_bytes(raw, info, 0), pack24(vals))


# ---------------------------------------------------------------------------
# FFT
# ---------------------------------------------------------------------------

def direct_dft_mag(x):
    n = len(x)
    out = []
    for k in range(n // 2 + 1):
        re = im = 0.0
        for i, v in enumerate(x):
            ang = -2.0 * math.pi * k * i / n
            re += v * math.cos(ang)
            im += v * math.sin(ang)
        out.append(math.hypot(re, im))
    return out


class TestFft(unittest.TestCase):
    def test_matches_a_direct_dft(self):
        x = noise(64, seed=11)
        want = direct_dft_mag(x)
        got = b1.rfft_mag(x)
        self.assertEqual(len(got), len(want))
        for a, b in zip(want, got):
            self.assertAlmostEqual(a, b, places=8)

    def test_locates_a_known_tone(self):
        n, sr, f = 4096, 48000.0, 1000.0
        x = [math.sin(2 * math.pi * f * i / sr) for i in range(n)]
        mag = b1.rfft_mag(x)
        peak = max(range(len(mag)), key=lambda i: mag[i])
        self.assertEqual(peak, round(f * n / sr))

    def test_rejects_non_power_of_two(self):
        with self.assertRaises(ValueError):
            b1.rfft_mag([0.0] * 100)


# ---------------------------------------------------------------------------
# onset detection
# ---------------------------------------------------------------------------

class TestOnsets(unittest.TestCase):
    SR = 48000

    def build(self, events, seconds=40.0, floor_db=-90.0):
        """events = [(time_s, f0, peak_dbfs)] -> a float signal."""
        n = int(seconds * self.SR)
        x = [v * (10 ** (floor_db / 20.0)) for v in noise(n, seed=5)]
        for t, f0, db in events:
            start = int(t * self.SR)
            body = stiff_string(min(int(6.0 * self.SR), n - start),
                                self.SR, f0, 2e-4, partials=14, decay=2.5,
                                seed=int(f0) + 1)
            g = 10 ** (db / 20.0)
            for i, v in enumerate(body):
                x[start + i] += v * g
        return x

    def detect(self, x):
        env, _fs, hop = b1.band_envelope(array("f", x), self.SR)
        onsets = b1.detect_onsets(env, hop)
        lv = b1.onset_levels(onsets, array("f", x), self.SR)
        keep = b1.suppress_shadowed(onsets, lv)
        return [onsets[i] for i in keep]

    def test_finds_notes_25_db_apart(self):
        """The pass-to-pass level spread is ~25 dB; one global threshold cannot
        cover it, and a rise-based detector must not care."""
        events = [(2.0, 55.0, -8.0), (10.0, 110.0, -33.0),
                  (18.0, 220.0, -10.0), (26.0, 440.0, -32.0),
                  (33.0, 880.0, -12.0)]
        got = self.detect(self.build(events))
        self.assertEqual(len(got), len(events),
                         msg=f"onsets at {[round(t, 3) for t in got]}")
        for (want, _, _), have in zip(events, got):
            self.assertLess(abs(have - want), 0.05,
                            msg=f"onset {have:.3f} vs expected {want}")

    def test_onset_lands_at_or_before_the_attack(self):
        got = self.detect(self.build([(5.0, 130.0, -12.0)], seconds=15.0))
        self.assertEqual(len(got), 1)
        self.assertLessEqual(got[0], 5.0 + 1e-9)
        self.assertGreater(got[0], 4.9)

    def test_a_quiet_note_during_a_loud_ring_out_is_still_found(self):
        """Bass notes ring for ~16 s; the treble notes played over the tail of
        one must not be masked."""
        events = [(2.0, 55.0, -6.0), (6.0, 1046.5, -26.0), (11.0, 1318.5, -26.0)]
        got = self.detect(self.build(events, seconds=20.0))
        self.assertEqual(len(got), 3, msg=f"got {[round(t, 3) for t in got]}")

    def test_key_noise_before_a_strike_is_suppressed(self):
        """A soft key press thumps ~0.6 s before the hammer throws; that thump
        is a real transient but not a note."""
        x = self.build([(8.0, 196.0, -14.0)], seconds=20.0)
        thump = stiff_string(int(0.25 * self.SR), self.SR, 500.0, 1e-3,
                             partials=6, decay=0.2, seed=99)
        at = int(7.4 * self.SR)
        for i, v in enumerate(thump):
            x[at + i] += v * (10 ** (-40.0 / 20.0))
        got = self.detect(x)
        self.assertEqual(len(got), 1, msg=f"got {[round(t, 3) for t in got]}")
        self.assertLess(abs(got[0] - 8.0), 0.05)

    def test_silence_yields_no_onsets(self):
        x = [v * 1e-4 for v in noise(int(5 * self.SR), seed=3)]
        self.assertEqual(self.detect(x), [])


# ---------------------------------------------------------------------------
# inharmonic pitch fit
# ---------------------------------------------------------------------------

class TestPitchFit(unittest.TestCase):
    SR = 48000

    def fit(self, f0, b, partials=16, n=None, decay=2.5):
        n = n or int(2.0 * self.SR)
        body = stiff_string(n, self.SR, f0, b, partials=partials, decay=decay,
                            seed=int(f0) + 3)
        x = array("f", [v * 0.5 + 1e-5 * w
                        for v, w in zip(body, noise(len(body), seed=21))])
        return b1.estimate_pitch(x, self.SR, 0)

    def assert_recovers(self, f0, b, f0_tol_cents=12.0, b_tol=0.35, **kw):
        r = self.fit(f0, b, **kw)
        self.assertIsNotNone(r, f"no fit for f0={f0} B={b}")
        cents = abs(1200 * math.log2(r["f0_hz"] / f0))
        self.assertLess(cents, f0_tol_cents,
                        f"f0 {r['f0_hz']:.3f} vs {f0} ({cents:.1f} cents off)")
        if b > 0 and r["b_is_fitted"]:
            rel = abs(r["inharmonicity_b"] - b) / b
            self.assertLess(rel, b_tol,
                            f"B {r['inharmonicity_b']:.3e} vs {b:.3e}")
        return r

    def test_recovers_f0_and_b_mid_register(self):
        """C3-ish with the B this instrument actually measures there."""
        r = self.assert_recovers(130.5, 1.7e-4)
        self.assertGreaterEqual(r["partials_used"], 6)
        self.assertTrue(r["b_is_fitted"])

    def test_recovers_a_bass_note_with_strong_inharmonicity(self):
        """A0: B ~5e-4, and the fundamental is far from the loudest partial."""
        self.assert_recovers(26.9, 4.9e-4, partials=30, decay=4.0)

    def test_recovers_when_the_fundamental_is_missing(self):
        """Real bass notes radiate almost nothing at f0; the fit must come from
        the series, not from a peak at f0."""
        n = int(2.0 * self.SR)
        full = stiff_string(n, self.SR, 30.0, 4.0e-4, partials=24, decay=3.0, seed=8)
        # subtract partials 1-3 so the series starts at k=4
        low = stiff_string(n, self.SR, 30.0, 4.0e-4, partials=3, decay=3.0, seed=8)
        pk = max(abs(v) for v in stiff_string(n, self.SR, 30.0, 4.0e-4,
                                              partials=24, decay=3.0, seed=8))
        del pk
        x = array("f", [a - b for a, b in zip(full, low)])
        r = b1.estimate_pitch(x, self.SR, 0)
        self.assertIsNotNone(r)
        cents = abs(1200 * math.log2(r["f0_hz"] / 30.0))
        self.assertLess(cents, 20.0, f"f0 read {r['f0_hz']:.3f}, wanted 30.0")

    def test_recovers_treble_with_large_inharmonicity(self):
        """Top octave: B runs to ~1e-2 and only a few partials fit below
        Nyquist."""
        self.assert_recovers(2100.0, 5e-3, partials=8, decay=0.8, b_tol=0.6)

    def test_does_not_octave_error_on_a_2f_dominant_tone(self):
        """The classic failure: partial 2 louder than partial 1."""
        n = int(1.5 * self.SR)
        base = stiff_string(n, self.SR, 220.0, 3e-4, partials=12, decay=2.0, seed=4)
        second = [math.sin(2 * math.pi * 220.0 * 2 *
                           math.sqrt(1 + 3e-4 * 4) * i / self.SR)
                  for i in range(n)]
        x = array("f", [0.4 * a + 0.9 * b for a, b in zip(base, second)])
        r = b1.estimate_pitch(x, self.SR, 0)
        self.assertIsNotNone(r)
        cents = abs(1200 * math.log2(r["f0_hz"] / 220.0))
        self.assertLess(cents, 25.0, f"read {r['f0_hz']:.2f}, wanted ~220")

    def test_b_is_flagged_unfitted_when_too_few_partials(self):
        n = int(0.5 * self.SR)
        x = array("f", [0.5 * math.sin(2 * math.pi * 3500.0 * i / self.SR)
                        for i in range(n)])
        r = b1.estimate_pitch(x, self.SR, 0)
        self.assertIsNotNone(r)
        self.assertLess(r["partials_used"], 3)
        self.assertFalse(r["b_is_fitted"])

    def test_reports_f1_above_f0_for_a_stiff_string(self):
        r = self.fit(200.0, 2e-3)
        self.assertIsNotNone(r)
        self.assertGreater(r["f1_hz"], r["f0_hz"])
        self.assertAlmostEqual(
            r["f1_hz"], r["f0_hz"] * math.sqrt(1 + r["inharmonicity_b"]),
            places=6)


# ---------------------------------------------------------------------------
# note names / cents
# ---------------------------------------------------------------------------

class TestNotes(unittest.TestCase):
    def test_note_to_midi(self):
        self.assertEqual(b1.note_to_midi("A0"), 21)
        self.assertEqual(b1.note_to_midi("C1"), 24)
        self.assertEqual(b1.note_to_midi("A4"), 69)
        self.assertEqual(b1.note_to_midi("C8"), 108)
        self.assertEqual(b1.note_to_midi("F#3"), 54)
        self.assertEqual(b1.note_to_midi("Gb3"), 54)

    def test_round_trip(self):
        for m in range(21, 109):
            self.assertEqual(b1.note_to_midi(b1.midi_to_note(m)), m)

    def test_bad_names_raise(self):
        for bad in ("", "H4", "A", "4A", "C#x"):
            with self.assertRaises(ValueError):
                b1.note_to_midi(bad)

    def test_et_reference(self):
        self.assertAlmostEqual(b1.et_hz(69), 440.0, places=9)
        self.assertAlmostEqual(b1.et_hz(21), 27.5, places=6)

    def test_cents_matches_the_measured_a4(self):
        # the instrument reads A4 = 437.45 Hz, i.e. ~10 cents flat of A440
        self.assertAlmostEqual(b1.cents_vs(437.45, 69), -10.06, places=1)

    def test_every_ladder_note_parses_and_ascends(self):
        for name, ladder in b1.LADDERS.items():
            midi = [b1.note_to_midi(n) for n in ladder]
            self.assertEqual(midi[0], 21, f"{name} must start on A0")
            self.assertEqual(midi, sorted(midi), f"{name} must ascend")
            self.assertEqual(len(midi), len(set(midi)), f"{name} has a repeat")


# ---------------------------------------------------------------------------
# ladder matching
# ---------------------------------------------------------------------------

class TestLadderMatch(unittest.TestCase):
    LADDER = [b1.note_to_midi(n) for n in "A0 C1 E1 G1 B1 D2".split()]

    def pairs(self, detected):
        return b1.align_to_ladder(detected, self.LADDER)

    def test_perfect_run_maps_one_to_one(self):
        det = [float(m) for m in self.LADDER]
        got = self.pairs(det)
        self.assertEqual(got, [(i, i) for i in range(len(self.LADDER))])

    def test_detuning_within_a_semitone_still_matches(self):
        """The bass is ~50 cents flat, so 'C1' reads nearly halfway to B0."""
        det = [m - 0.53 for m in self.LADDER]
        got = self.pairs(det)
        self.assertEqual(got, [(i, i) for i in range(len(self.LADDER))])

    def test_an_extra_event_is_reported_not_absorbed(self):
        det = [float(self.LADDER[0]), float(self.LADDER[1]),
               float(self.LADDER[1]),                       # re-strike
               float(self.LADDER[2]), float(self.LADDER[3]),
               float(self.LADDER[4]), float(self.LADDER[5])]
        got = self.pairs(det)
        extras = [ei for ei, li in got if li is None]
        self.assertEqual(len(extras), 1)
        matched = {li: ei for ei, li in got if li is not None and ei is not None}
        self.assertEqual(len(matched), len(self.LADDER))
        # the notes AFTER the extra keep their correct rung
        self.assertEqual(matched[5], 6)

    def test_a_missing_rung_is_reported(self):
        det = [float(m) for m in self.LADDER[:3] + self.LADDER[4:]]
        got = self.pairs(det)
        missing = [li for ei, li in got if ei is None]
        self.assertEqual(missing, [3])

    def test_a_wrong_pitch_is_matched_but_flaggable(self):
        det = [float(m) for m in self.LADDER]
        det[3] += 2.0                       # two semitones off its rung
        got = self.pairs(det)
        pair = [(ei, li) for ei, li in got if li == 3][0]
        self.assertEqual(pair, (3, 3))
        delta = abs(det[3] - self.LADDER[3])
        self.assertGreater(delta, b1.FLAG_WINDOW)

    def test_a_wildly_wrong_pitch_becomes_extra_plus_missing(self):
        det = [float(m) for m in self.LADDER]
        det[2] += 24.0                      # two octaves off: not a match
        got = self.pairs(det)
        self.assertIn((2, None), got)
        self.assertIn((None, 2), got)

    def test_an_empty_detection_list_reports_every_rung_missing(self):
        got = b1.align_to_ladder([], self.LADDER)
        self.assertEqual(got, [(None, j) for j in range(len(self.LADDER))])

    def test_none_pitches_do_not_crash_the_matcher(self):
        det = [float(self.LADDER[0]), None, float(self.LADDER[2])]
        got = b1.align_to_ladder(det, self.LADDER)
        self.assertTrue(any(ei == 0 and li == 0 for ei, li in got))


# ---------------------------------------------------------------------------
# CLI plumbing
# ---------------------------------------------------------------------------

class TestOverrides(unittest.TestCase):
    def test_assign_parsing(self):
        got = b1.parse_overrides(
            ["--assign=hard:12:C8", "--assign=hard:3:A0", "--assign=soft:1:F#3"],
            "--assign")
        self.assertEqual(got, {"hard": {12: "C8", 3: "A0"}, "soft": {1: "F#3"}})

    def test_drop_parsing(self):
        got = b1.parse_overrides(["--drop=hard:4", "--drop=hard:9"], "--drop")
        self.assertEqual(got, {"hard": {4, 9}})

    def test_bad_note_in_assign_is_rejected_up_front(self):
        with self.assertRaises(ValueError):
            b1.parse_overrides(["--assign=hard:1:Q9"], "--assign")

    def test_malformed_assign_is_rejected(self):
        with self.assertRaises(SystemExit):
            b1.parse_overrides(["--assign=hard:1"], "--assign")

    def test_main_requires_an_output_directory(self):
        self.assertEqual(b1.main(["--all"]), 2)

    def test_help_exits_clean(self):
        self.assertEqual(b1.main(["--help"]), 0)


class TestTakesTable(unittest.TestCase):
    def test_every_pass_names_a_real_ladder_and_a_sane_window(self):
        for name, spec in b1.TAKES.items():
            self.assertIn("passes", spec, name)
            for pass_name, t0, t1, ladder in spec["passes"]:
                self.assertIn(ladder, b1.LADDERS, f"{name}/{pass_name}")
                self.assertLess(t0, t1, f"{name}/{pass_name}")

    def test_pass_windows_within_a_take_do_not_overlap(self):
        for name, spec in b1.TAKES.items():
            spans = sorted((t0, t1) for _, t0, t1, _ in spec["passes"])
            for (a0, a1), (b0, b1_) in zip(spans, spans[1:]):
                self.assertLessEqual(a1, b0, f"{name}: {a0}-{a1} overlaps {b0}-{b1_}")


# ---------------------------------------------------------------------------
# end-to-end
# ---------------------------------------------------------------------------

class TestEndToEnd(unittest.TestCase):
    SR = 48000

    def test_synthetic_take_slices_and_manifests(self):
        """Three notes of a ladder, written as a real 24-bit stereo WAV with a
        bext chunk, sliced through the whole pipeline."""
        notes = [("A0", 26.9, 4.9e-4, -10.0), ("C1", 31.9, 3.0e-4, -12.0),
                 ("E1", 40.3, 2.4e-4, -11.0)]
        seconds = 32.0
        n = int(seconds * self.SR)
        x = [v * 1e-4 for v in noise(n, seed=13)]
        for i, (_, f0, b, db) in enumerate(notes):
            at = int((2.0 + 9.0 * i) * self.SR)
            body = stiff_string(int(7.0 * self.SR), self.SR, f0, b,
                                partials=26, decay=4.0, seed=int(f0))
            g = 10 ** (db / 20.0)
            for j, v in enumerate(body):
                x[at + j] += v * g
        ints = [max(-8388608, min(8388607, int(v * 8388607))) for v in x]

        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "SYNTH.wav")
            write_wav24(src, ints, [0] * n)
            out = os.path.join(d, "slices")
            spec = {"gain_group": "T", "note": "synthetic",
                    "passes": [("test", 0.0, seconds, "thirds_a0")]}
            opts = {"channel": 0, "pre_roll": 0.005, "slice_s": 4.0,
                    "guard": 0.15, "extras": True, "opus": False,
                    "ropusenc": "ropusenc", "opus_bitrate": 128000,
                    "no_hash": False, "assigns": {}, "drops": {},
                    "ladder": {"test": [n for n, _, _, _ in notes]}}
            man = b1.analyse_take(src, spec, out, opts)

        self.assertEqual(len(man["slices"]), 3)
        got = [s["assigned_note"] for s in man["slices"]]
        self.assertEqual(got, ["A0", "C1", "E1"])
        self.assertEqual(man["passes"][0]["missing"], [])
        self.assertEqual(man["passes"][0]["extras"], 0)
        for s in man["slices"]:
            self.assertEqual(s["status"], "assigned")
            self.assertEqual(s["pitch_source"], "auto")
            self.assertEqual(s["source_sample_rate"], self.SR)
            self.assertGreater(s["frames"], 0)
            self.assertIsNotNone(s["f0_hz"])
            self.assertIsNotNone(s["peak_dbfs"])
            self.assertIsNotNone(s["rms200_dbfs"])
            self.assertLess(abs(s["cents_vs_et"]), 100.0)
        # the pre-roll must not swallow the attack
        self.assertLessEqual(man["slices"][0]["source_offset"],
                             man["slices"][0]["onset_sample"])

    def test_override_forces_an_assignment_and_is_recorded(self):
        seconds = 14.0
        n = int(seconds * self.SR)
        x = [v * 1e-4 for v in noise(n, seed=17)]
        body = stiff_string(int(6.0 * self.SR), self.SR, 262.0, 2e-4,
                            partials=16, decay=2.0, seed=5)
        at = int(2.0 * self.SR)
        for j, v in enumerate(body):
            x[at + j] += v * 0.3
        ints = [max(-8388608, min(8388607, int(v * 8388607))) for v in x]
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "SYNTH2.wav")
            write_wav24(src, ints, [0] * n)
            out = os.path.join(d, "slices")
            spec = {"gain_group": "T", "note": "synthetic",
                    "passes": [("p", 0.0, seconds, "thirds_a0")]}
            opts = {"channel": 0, "pre_roll": 0.005, "slice_s": 3.0,
                    "guard": 0.15, "extras": True, "opus": False,
                    "ropusenc": "ropusenc", "opus_bitrate": 128000,
                    "no_hash": True, "assigns": {"p": {0: "C8"}}, "drops": {},
                    "ladder": {"p": ["C8"]}}
            man = b1.analyse_take(src, spec, out, opts)
        self.assertEqual(len(man["slices"]), 1)
        s = man["slices"][0]
        self.assertEqual(s["assigned_note"], "C8")
        self.assertEqual(s["pitch_source"], "override")
        self.assertEqual(s["status"], "assigned")
        # the auto-detected pitch is still reported, so the override is auditable
        self.assertIsNotNone(s["f0_hz"])

    def test_drop_removes_an_event(self):
        seconds = 20.0
        n = int(seconds * self.SR)
        x = [v * 1e-4 for v in noise(n, seed=19)]
        for i, f0 in enumerate((262.0, 330.0)):
            at = int((2.0 + 8.0 * i) * self.SR)
            body = stiff_string(int(6.0 * self.SR), self.SR, f0, 2e-4,
                                partials=16, decay=2.0, seed=int(f0))
            for j, v in enumerate(body):
                x[at + j] += v * 0.3
        ints = [max(-8388608, min(8388607, int(v * 8388607))) for v in x]
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "SYNTH3.wav")
            write_wav24(src, ints, [0] * n)
            out = os.path.join(d, "slices")
            spec = {"gain_group": "T", "note": "synthetic",
                    "passes": [("p", 0.0, seconds, "thirds_a0")]}
            opts = {"channel": 0, "pre_roll": 0.005, "slice_s": 3.0,
                    "guard": 0.15, "extras": True, "opus": False,
                    "ropusenc": "ropusenc", "opus_bitrate": 128000,
                    "no_hash": True, "assigns": {}, "drops": {"p": {0}},
                    "ladder": {"p": ["E4"]}}
            man = b1.analyse_take(src, spec, out, opts)
        self.assertEqual(len(man["slices"]), 1)
        self.assertEqual(man["slices"][0]["assigned_note"], "E4")


if __name__ == "__main__":
    unittest.main()
