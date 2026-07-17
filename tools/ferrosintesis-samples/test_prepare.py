import math
import os
import struct
import tempfile
import unittest
import urllib.error
import wave

import prepare


def old_trim(x, sr, keep_s, fade_s):
    """The pre-2026.07.16 trim, kept as a reference implementation.

    Its fade-in is a fixed 2 ms regardless of how much lead-in the source
    actually has — the defect the `lead` cap fixes. Retained here so both the
    inertness oracle and the bites-on-tight-trims oracle can compare against
    the real thing rather than an approximation of it.
    """
    peak = max(abs(v) for v in x)
    thr = 0.03 * peak
    onset = next(i for i, v in enumerate(x) if abs(v) > thr)
    start = max(0, onset - int(prepare.PRE_S * sr))
    seg = x[start:start + int((prepare.PRE_S + keep_s) * sr)]
    fin = int(0.002 * sr)
    for i in range(min(fin, len(seg))):
        seg[i] *= i / fin
    fout = int(fade_s * sr)
    for i in range(fout):
        j = len(seg) - fout + i
        if 0 <= j < len(seg):
            t = 1.0 - i / fout
            seg[j] *= t * t
    pk = max(abs(v) for v in seg)
    g = 0.9 / pk if pk > 0 else 1.0
    return [v * g for v in seg]


def write_wav(path, sample_width, channels):
    frames = 128
    raw = bytearray()
    for i in range(frames):
        for ch in range(channels):
            v = ((i + ch) % 17) / 16.0 - 0.5
            if sample_width == 2:
                raw.extend(struct.pack("<h", int(v * 32767)))
            else:
                raw.extend(int(v * 8388607).to_bytes(3, "little", signed=True))
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(44100)
        w.writeframes(bytes(raw))


class PrepareSampleBankTests(unittest.TestCase):
    def test_all_samples_route_to_the_expected_package(self):
        filenames = (
            set(prepare.SOURCES)
            | set(prepare.GUITAR_SOURCES)
            | set(prepare.STEEL_URLS)
        )
        core = set()
        orchestral = set()

        with tempfile.TemporaryDirectory() as repo_root:
            for filename in filenames:
                path = prepare.sample_output_path(filename, repo_root)
                relative = os.path.relpath(path, repo_root).split(os.sep)
                self.assertEqual(relative[0], "crates")
                self.assertEqual(relative[-2:], ["samples", filename])

                if relative[1] == "ferrosintesis-samples-core":
                    core.add(filename)
                elif relative[1] == "ferrosintesis-samples-orchestral":
                    orchestral.add(filename)
                else:
                    self.fail(f"unexpected sample package for {filename}: {relative[1]}")

        self.assertEqual(len(filenames), 210)
        self.assertEqual(len(core), 71)
        self.assertEqual(len(orchestral), 139)
        self.assertTrue(
            all(name.startswith(("piano_", "violin_", "flute_")) for name in core)
        )
        self.assertFalse(
            any(name.startswith(("piano_", "violin_", "flute_")) for name in orchestral)
        )

    def test_fade_in_is_inert_when_lead_in_exceeds_the_window(self):
        """A source with >= 2 ms of lead-in must be cut exactly as before.

        Differential oracle against the pre-fix algorithm. This is the claim the
        already-committed WAVs rest on, and it is deliberately narrow: the fade
        cap only bites when the onset sits INSIDE the 2 ms window, so the 136
        sources with more lead-in than that must come out bit-identical.

        Note the sizing. An earlier attempt at this fix padded up to PRE_S
        (8 ms) and asserted inertness with test inputs that had 8-300 ms of
        lead-in — which passed, and was wrong: the real bank is trimmed far
        tighter than that (median onset 120 samples on piano, 8 on steel), so
        the pad silently re-cut 131 committed files. The lesson is in the
        parameters below: they are the MEASURED population, not a convenient
        assumption.
        """

        sr = prepare.OUT_SR
        fin = int(0.002 * sr)  # 88 samples — the de-click window
        # lead-ins at and above the window, including the exact boundary, and
        # the 31 ms real-world case (vlnens, the most generously padded family)
        for lead in (fin, fin + 1, 127, 352, 1374):
            with self.subTest(lead_samples=lead):
                body = [math.sin(2 * math.pi * 440.0 * i / sr) for i in range(sr)]
                x = [0.0] * lead + body
                new = prepare.trim_to_onset(list(x), sr, keep_s=0.62, fade_s=0.20)
                ref = old_trim(list(x), sr, keep_s=0.62, fade_s=0.20)
                self.assertEqual(len(new), len(ref))
                self.assertEqual(new, ref)

    def test_fade_in_never_exceeds_available_lead_in(self):
        """A tightly-trimmed source must keep its attack.

        Uses the MEASURED steel geometry: onset within a handful of samples,
        first sample at near-silence (so there is no step to de-click). The old
        fixed 2 ms fade attenuated the whole pick transient; the cap must leave
        it essentially untouched.
        """
        sr = prepare.OUT_SR
        for onset in (0, 1, 8, 41):  # measured steel onsets across the bank
            with self.subTest(onset=onset):
                body = [math.sin(2 * math.pi * 220.0 * i / sr) for i in range(sr)]
                x = [0.0] * onset + body

                seg = prepare.trim_to_onset(list(x), sr, keep_s=0.9, fade_s=0.30)

                # The transient must survive: peak within the first 2 ms should
                # reach essentially the normalized ceiling, not a fraction of it.
                early_peak = max(abs(v) for v in seg[: int(0.002 * sr)])
                self.assertGreater(
                    early_peak,
                    0.85,
                    f"onset={onset}: de-click fade crushed the attack "
                    f"(early peak {early_peak:.3f})",
                )

    def test_fade_in_cap_actually_bites_on_the_measured_steel_geometry(self):
        """Guard against the cap silently regressing to a no-op.

        True differential against `old_trim`: at the median measured steel
        onset the new cut must deliver a materially stronger attack than the
        old fixed-fade cut. Measured ratio is ~1.35x; asserted at 1.2x so
        harmless numerical drift does not flake it.
        """
        sr = prepare.OUT_SR
        body = [math.sin(2 * math.pi * 220.0 * i / sr) for i in range(sr)]
        x = [0.0] * 8 + body  # median measured steel onset

        fin = int(0.002 * sr)
        new_peak = max(abs(v) for v in prepare.trim_to_onset(
            list(x), sr, keep_s=0.9, fade_s=0.30)[:fin])
        old_peak = max(abs(v) for v in old_trim(
            list(x), sr, keep_s=0.9, fade_s=0.30)[:fin])
        self.assertGreater(
            new_peak,
            old_peak * 1.2,
            f"fade cap is not biting: new {new_peak:.4f} vs old {old_peak:.4f}",
        )

    def test_fetch_is_atomic_on_short_transfer(self):
        with tempfile.TemporaryDirectory() as td:
            final = os.path.join(td, "sample.wav")
            real_urlretrieve = prepare.urllib.request.urlretrieve

            def short_transfer(_url, filename):
                with open(filename, "wb") as f:
                    f.write(b"partial")
                raise urllib.error.ContentTooShortError("short", b"partial")

            prepare.urllib.request.urlretrieve = short_transfer
            try:
                with self.assertRaises(urllib.error.ContentTooShortError):
                    prepare.fetch("https://example.invalid/sample.wav", final)
            finally:
                prepare.urllib.request.urlretrieve = real_urlretrieve

            self.assertFalse(os.path.exists(final))
            self.assertFalse(os.path.exists(final + ".part"))

    def test_ensure_source_refetches_poisoned_cache_once(self):
        with tempfile.TemporaryDirectory() as td:
            final = os.path.join(td, "sample.wav")
            write_wav(final, 2, 2)
            os.truncate(final, os.path.getsize(final) - 17)
            calls = []
            real_urlretrieve = prepare.urllib.request.urlretrieve

            def good_transfer(_url, filename):
                calls.append(filename)
                write_wav(filename, 2, 2)

            prepare.urllib.request.urlretrieve = good_transfer
            try:
                prepare.ensure_source("sample.wav", "https://example.invalid/sample.wav", td)
            finally:
                prepare.urllib.request.urlretrieve = real_urlretrieve

            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.exists(final))
            self.assertFalse(os.path.exists(final + ".part"))
            samples, sr = prepare.read_wav(final)
            self.assertEqual(sr, 44100)
            self.assertEqual(len(samples), 128)

    def test_read_wav_rejects_truncated_16_and_24_bit_inputs(self):
        for sample_width in (2, 3):
            for channels in (1, 2):
                with self.subTest(sample_width=sample_width, channels=channels):
                    with tempfile.TemporaryDirectory() as td:
                        path = os.path.join(td, "sample.wav")
                        write_wav(path, sample_width, channels)
                        samples, sr = prepare.read_wav(path)
                        self.assertEqual(sr, 44100)
                        self.assertEqual(len(samples), 128)
                        os.truncate(path, os.path.getsize(path) - 17)
                        with self.assertRaises(ValueError):
                            prepare.read_wav(path)


class BagpipeLoopTests(unittest.TestCase):
    """The looped-sustain path (HLD 2026.07.17) — extract_loop and the SFZ parse.

    These test the pure transforms without any network or the real WAVs, so the
    prepare.py bagpipe capability is committable green before the samples exist.
    """

    def test_parse_sfz_loops_reads_points_per_region(self):
        sfz = (
            "// header\n"
            "<region> sample=samples/drone_G2_1.wav lokey=36 hikey=47 "
            "loop_start=1858 loop_end=106496\n"
            "<region> sample=samples/F4_31.wav pitch_keycenter=65 "
            "loop_start=52224 loop_end=166144 tune=40\n"
            "<region> sample=samples/no_loop.wav lokey=1\n"  # no loop -> skipped
        )
        loops = prepare.parse_sfz_loops(sfz)
        self.assertEqual(loops["drone_G2_1.wav"], (1858, 106496))
        self.assertEqual(loops["F4_31.wav"], (52224, 166144))
        self.assertNotIn("no_loop.wav", loops)

    def _tone(self, sr, f0, n):
        return [math.sin(2 * math.pi * f0 * i / sr) for i in range(n)]

    def test_extract_loop_emits_a_seamless_wrap(self):
        # a stable tone -> the endpoint search finds a near-whole-period loop
        # whose modulo wrap is seamless, at ~target length.
        sr = 44100
        x = self._tone(sr, 441.0, 2 * sr)  # 2 s, period 100 samples
        seg = prepare.extract_loop(x, sr, 8800, 441.0, target_s=0.4)
        click = prepare._seam_click(seg)
        self.assertLess(click, 2.0, f"wrap step x{click:.2f} of the p95 body step")
        self.assertAlmostEqual(len(seg) / sr, 0.4, delta=0.01)  # ~target length

    def test_extract_loop_removes_dc(self):
        sr = 44100
        x = [0.3 + v for v in self._tone(sr, 196.0, 2 * sr)]  # +0.3 DC like a drone
        seg = prepare.extract_loop(x, sr, int(0.2 * sr), 196.0, target_s=0.5)
        self.assertAlmostEqual(sum(seg) / len(seg), 0.0, places=6)

    def test_extract_loop_normalizes_to_common_rms(self):
        sr = 44100
        quiet = self._tone(sr, 300.0, 2 * sr)
        loud = [4.0 * v for v in quiet]

        def rms(s):
            return math.sqrt(sum(v * v for v in s) / len(s))

        a = prepare.extract_loop(quiet, sr, int(0.2 * sr), 300.0, target_s=0.4)
        b = prepare.extract_loop(loud, sr, int(0.2 * sr), 300.0, target_s=0.4)
        self.assertAlmostEqual(rms(a), prepare.BAGPIPE_TARGET_RMS, places=4)
        self.assertAlmostEqual(rms(b), prepare.BAGPIPE_TARGET_RMS, places=4)

    def test_extract_loop_rejects_a_source_too_short(self):
        with self.assertRaises(ValueError):
            prepare.extract_loop([0.0] * 100, 44100, 10, 200.0, target_s=0.4)


if __name__ == "__main__":
    unittest.main()
