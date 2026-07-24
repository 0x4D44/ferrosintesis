import hashlib
import math
import os
import random
import shutil
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

    @staticmethod
    def _synthetic_piano_bank(sr=1000):
        bank = {}
        for dyn_i, dyn in enumerate(("pp", "mf", "f")):
            for note_i, note in enumerate(prepare.PIANO_ZONE_NOTES):
                for rr_i, suffix in enumerate(("", "_rr2")):
                    body_db = -22.0 + 0.35 * note_i + (rr_i * 2.0 - 1.0)
                    ratio_db = (
                        -4.0
                        + 1.7 * note_i
                        + 1.5 * dyn_i
                        + (rr_i * 4.0 - 2.0)
                    )
                    body = 10 ** (body_db / 20.0)
                    attack = body * 10 ** (ratio_db / 20.0)
                    x = [0.0] * 5
                    for i in range(int(0.40 * sr)):
                        t = i / sr
                        if t < 0.03:
                            amp = attack
                        elif t < 0.12:
                            u = (t - 0.03) / 0.09
                            u = u * u * (3.0 - 2.0 * u)
                            amp = attack + (body - attack) * u
                        else:
                            amp = body
                        x.append(amp * math.sin(2.0 * math.pi * 50.0 * t))
                    bank[f"piano_{note}_{dyn}{suffix}.wav"] = x
        return bank

    def test_piano_conditioner_matches_shape_and_absolute_level_trends(self):
        sr = 1000
        source = self._synthetic_piano_bank(sr)

        conditioned = prepare.condition_piano_bank(source, sr)
        stats = prepare.piano_envelope_stats(conditioned, sr)

        self.assertEqual(set(conditioned), set(source))
        self.assertEqual(
            conditioned,
            prepare.condition_piano_bank(source, sr),
            "bank conditioning must be deterministic",
        )
        for name, before in source.items():
            after = conditioned[name]
            self.assertEqual(len(after), len(before))
            self.assertLessEqual(max(abs(v) for v in after), 0.900001)
            onset = prepare.piano_envelope_stats({name: before}, sr)[name][2]
            scales = [
                after[i] / before[i]
                for i in range(onset, onset + int(0.035 * sr))
                if abs(before[i]) > 1e-6
            ]
            self.assertLess(
                max(scales) - min(scales),
                1e-9,
                f"{name}: hammer window received time-varying gain",
            )

        for dyn in ("pp", "mf", "f"):
            for note in prepare.PIANO_ZONE_NOTES:
                a = stats[f"piano_{note}_{dyn}.wav"]
                b = stats[f"piano_{note}_{dyn}_rr2.wav"]
                self.assertLess(abs(a[0] - b[0]), 0.05)
                self.assertLess(abs(a[1] - b[1]), 0.05)

        for note in prepare.PIANO_ZONE_NOTES:
            shape_ratios = [
                stats[f"piano_{note}_{dyn}{suffix}.wav"][0]
                for dyn in ("pp", "mf", "f")
                for suffix in ("", "_rr2")
            ]
            self.assertLess(max(shape_ratios) - min(shape_ratios), 0.05)
            body_levels = [
                stats[f"piano_{note}_{dyn}{suffix}.wav"][1]
                for dyn in ("pp", "mf", "f")
                for suffix in ("", "_rr2")
            ]
            self.assertLess(max(body_levels) - min(body_levels), 0.05)

    def test_committed_piano_bank_has_conditioned_macro_envelopes(self):
        sample_dir = os.path.join(
            prepare.REPO_ROOT, "crates", "ferrosintesis-samples-core", "samples"
        )
        bank = {}
        for name in sorted(prepare.SOURCES):
            if not name.startswith("piano_"):
                continue
            x, sr = prepare.read_wav(os.path.join(sample_dir, name))
            self.assertEqual(sr, prepare.OUT_SR)
            bank[name] = x

        self.assertEqual(len(bank), 54)
        stats = prepare.piano_envelope_stats(bank, prepare.OUT_SR)
        ratio_points = []
        for dyn in ("pp", "mf", "f"):
            for note in prepare.PIANO_ZONE_NOTES:
                a = stats[f"piano_{note}_{dyn}.wav"]
                b = stats[f"piano_{note}_{dyn}_rr2.wav"]
                ratio_points.extend([
                    (prepare.PIANO_ZONE_MIDI[note], a[0]),
                    (prepare.PIANO_ZONE_MIDI[note], b[0]),
                ])
                self.assertLess(
                    abs(a[0] - b[0]),
                    0.35,
                    f"{note} {dyn}: round-robin shape mismatch",
                )
                self.assertLess(
                    abs(a[1] - b[1]),
                    0.35,
                    f"{note} {dyn}: round-robin body-level mismatch",
                )
        ratio_slope, ratio_intercept = prepare._minimax_line(ratio_points)
        for note in prepare.PIANO_ZONE_NOTES:
            target = (
                ratio_slope * prepare.PIANO_ZONE_MIDI[note]
                + ratio_intercept
            )
            ratios = []
            for dyn in ("pp", "mf", "f"):
                for suffix in ("", "_rr2"):
                    ratio = stats[f"piano_{note}_{dyn}{suffix}.wav"][0]
                    ratios.append(ratio)
                    self.assertLess(
                        abs(ratio - target),
                        0.35,
                        f"{note} {dyn}{suffix}: shape misses register trend",
                    )
            self.assertLess(
                max(ratios) - min(ratios),
                0.35,
                f"{note}: velocity layers do not share one macro envelope",
            )

        level_points = []
        for note in prepare.PIANO_ZONE_NOTES:
            levels = [
                stats[f"piano_{note}_{dyn}{suffix}.wav"][1]
                for dyn in ("pp", "mf", "f")
                for suffix in ("", "_rr2")
            ]
            level_points.append(
                (prepare.PIANO_ZONE_MIDI[note], sum(levels) / len(levels))
            )
        level_slope, level_intercept = prepare._robust_line(level_points)
        for note in prepare.PIANO_ZONE_NOTES:
            target = (
                level_slope * prepare.PIANO_ZONE_MIDI[note] + level_intercept
            )
            for dyn in ("pp", "mf", "f"):
                for suffix in ("", "_rr2"):
                    body_db = stats[f"piano_{note}_{dyn}{suffix}.wav"][1]
                    self.assertLess(
                        abs(body_db - target),
                        0.35,
                        f"{note} {dyn}{suffix}: body level misses register trend",
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

    def _tone(self, sr, f0, n, harmonics=4):
        """A harmonically rich tone — a single sine is too easy: its value+slope
        pair identifies the phase uniquely, so even the old broken search passed."""
        return [sum(math.sin(2 * math.pi * f0 * k * i / sr) / k
                    for k in range(1, harmonics + 1))
                for i in range(n)]

    def test_extract_loop_emits_a_seamless_wrap(self):
        sr = 44100
        x = self._tone(sr, 441.0, 3 * sr)  # 3 s, period 100 samples
        seg, wrap_db = prepare.extract_loop(x, sr, 8800, 441.0,
                                            target_s=(0.06, 0.14))
        self.assertLess(wrap_db, -40.0, f"wrap error {wrap_db:.1f} dB on a steady tone")
        click = prepare._seam_click(seg)
        self.assertLess(click, 2.0, f"wrap step x{click:.2f} of the p95 body step")
        self.assertGreaterEqual(len(seg) / sr, 0.06)
        self.assertLessEqual(len(seg) / sr, 0.14)

    def test_extract_loop_picks_a_whole_number_of_periods(self):
        """The defect that shipped: a loop of non-integer period count wraps with
        every harmonic out of phase. A single sine hides it; a rich tone does not."""
        sr = 44100
        f0 = 441.0
        x = self._tone(sr, f0, 3 * sr)
        seg, _ = prepare.extract_loop(x, sr, 8800, f0, target_s=(0.06, 0.14))
        cycles = len(seg) / (sr / f0)
        self.assertLess(abs(cycles - round(cycles)), 0.02,
                        f"loop spans {cycles:.3f} periods, not a whole number")

    def test_extract_loop_avoids_a_window_that_spans_a_swell(self):
        """`chanter_G4`/`chanter_D5` shipped a 4 dB ramp inside the loop, so the
        wrap stepped 4 dB every 0.39 s. The search must reject such a window even
        though its SEAM SAMPLES match — the old cost function could not see it."""
        sr = 44100
        f0 = 441.0
        n = 3 * sr
        base = self._tone(sr, f0, n)
        # a loud ramp early, flat later: only the later region can loop cleanly
        ramp_end = int(1.2 * sr)
        x = [v * (1.0 + 3.0 * i / ramp_end) if i < ramp_end else v * 4.0
             for i, v in enumerate(base)]
        seg, _ = prepare.extract_loop(x, sr, int(0.1 * sr), f0,
                                      target_s=(0.06, 0.14))
        h = len(seg) // 2

        def rms(s):
            return math.sqrt(sum(v * v for v in s) / len(s))

        imbalance = abs(20 * math.log10(rms(seg[:h]) / rms(seg[h:])))
        self.assertLess(imbalance, 0.5,
                        f"loop halves differ by {imbalance:.2f} dB — it spans the ramp")

    def test_wrap_error_db_scores_a_phase_jump_far_worse_than_a_clean_wrap(self):
        sr = 44100
        f0 = 441.0
        per = sr / f0
        x = self._tone(sr, f0, sr)
        start = 4410
        clean = prepare.wrap_error_db(x, start, int(round(20 * per)), int(4 * per))
        # half a period short -> every harmonic wraps out of phase
        jump = prepare.wrap_error_db(x, start, int(round(19.5 * per)), int(4 * per))
        self.assertLess(clean, -40.0, f"clean wrap scored {clean:.1f} dB")
        self.assertGreater(jump, clean + 30.0,
                           f"phase jump {jump:.1f} dB vs clean {clean:.1f} dB")

    def test_extract_loop_removes_dc(self):
        sr = 44100
        x = [0.3 + v for v in self._tone(sr, 196.0, 3 * sr)]  # +0.3 DC like a drone
        seg, _ = prepare.extract_loop(x, sr, int(0.2 * sr), 196.0,
                                      target_s=(0.08, 0.20))
        self.assertAlmostEqual(sum(seg) / len(seg), 0.0, places=6)

    def test_extract_loop_normalizes_to_common_rms(self):
        sr = 44100
        quiet = self._tone(sr, 300.0, 3 * sr)
        loud = [4.0 * v for v in quiet]

        def rms(s):
            return math.sqrt(sum(v * v for v in s) / len(s))

        a, _ = prepare.extract_loop(quiet, sr, int(0.2 * sr), 300.0,
                                    target_s=(0.06, 0.14))
        b, _ = prepare.extract_loop(loud, sr, int(0.2 * sr), 300.0,
                                    target_s=(0.06, 0.14))
        self.assertAlmostEqual(rms(a), prepare.BAGPIPE_TARGET_RMS, places=4)
        self.assertAlmostEqual(rms(b), prepare.BAGPIPE_TARGET_RMS, places=4)

    def test_extract_loop_rejects_a_source_too_short(self):
        with self.assertRaises(ValueError):
            prepare.extract_loop([0.0] * 100, 44100, 10, 200.0,
                                 target_s=(0.06, 0.14))

    def test_extract_loop_enforces_the_wrap_gate(self):
        """Noise cannot loop; the gate must refuse rather than ship a click."""
        rng = random.Random(7)
        x = [rng.uniform(-1.0, 1.0) for _ in range(3 * 44100)]
        with self.assertRaises(ValueError):
            prepare.extract_loop(x, 44100, 4410, 441.0, target_s=(0.06, 0.14),
                                 max_wrap_db=prepare.BAGPIPE_MAX_WRAP_DB)


class ArchiveCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00062: a warm cache must PROVE it came from the pinned archive.

    The old `ensure_archive_sources` returned as soon as every destination path
    existed, which made the SHA-256 check below it unreachable: an altered,
    truncated or superseded cached member was rebaked into the tracked asset crate
    as if it had come from the pinned archive.

    Each case here drives the real `ensure_archive_sources` with the fetch/extract
    step stubbed, so it tests the cache DECISION — the part that was wrong — with
    no network and no 7z. `rebuilt` counts how often the stub ran: 0 means the warm
    cache was trusted, 1 means it was rejected and rebuilt.
    """

    PIN = "a" * 64
    MEMBERS = {"one.wav": "pack/one.wav", "two.wav": "pack/two.wav"}

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.url = "https://example.invalid/pack.7z"
        self.rebuilt = 0
        self.real_rebuild = prepare.rebuild_archive_cache
        prepare.rebuild_archive_cache = self.fake_rebuild
        self.addCleanup(setattr, prepare, "rebuild_archive_cache", self.real_rebuild)

    def fake_rebuild(self, *_args, **_kwargs):
        """Stand in for fetch + verify + 7z extract: write the pinned member bytes."""
        self.rebuilt += 1
        for fn in self.MEMBERS:
            with open(os.path.join(self.src, fn), "wb") as f:
                f.write(b"PINNED-" + fn.encode())

    def warm(self, pin=None):
        """Populate a cache the way a successful run leaves it."""
        prepare.ensure_archive_sources(self.src, self.url, pin or self.PIN,
                                       self.MEMBERS, "ext")

    def member(self, fn):
        with open(os.path.join(self.src, fn), "rb") as f:
            return f.read()

    def test_a_valid_warm_cache_is_reused(self):
        self.warm()
        self.assertEqual(self.rebuilt, 1, "cold cache must build once")
        self.warm()
        self.assertEqual(self.rebuilt, 1, "a verified warm cache must not refetch")

    def test_an_altered_member_is_rejected_and_restored(self):
        """Wave-valid but altered: the old code could not see this at all."""
        self.warm()
        with open(os.path.join(self.src, "one.wav"), "wb") as f:
            f.write(b"ALTERED-BUT-STILL-A-FILE")
        self.warm()
        self.assertEqual(self.rebuilt, 2, "an altered member must force a rebuild")
        self.assertEqual(self.member("one.wav"), b"PINNED-one.wav")

    def test_a_truncated_member_is_rejected_and_restored(self):
        self.warm()
        with open(os.path.join(self.src, "two.wav"), "wb") as f:
            f.write(b"PIN")
        self.warm()
        self.assertEqual(self.rebuilt, 2, "a truncated member must force a rebuild")
        self.assertEqual(self.member("two.wav"), b"PINNED-two.wav")

    def test_a_changed_pin_with_unchanged_member_names_is_rejected(self):
        """The nastiest case: nothing about the FILENAMES says the source moved."""
        self.warm()
        self.warm(pin="b" * 64)
        self.assertEqual(self.rebuilt, 2, "a new archive pin must force a rebuild")

    def test_a_missing_member_is_rejected(self):
        self.warm()
        os.remove(os.path.join(self.src, "one.wav"))
        self.warm()
        self.assertEqual(self.rebuilt, 2, "a missing member must force a rebuild")

    def test_a_legacy_cache_without_a_manifest_is_not_trusted(self):
        """Every cache on every machine predates the manifest — none may be trusted."""
        for fn in self.MEMBERS:
            with open(os.path.join(self.src, fn), "wb") as f:
                f.write(b"WHO-KNOWS")
        self.warm()
        self.assertEqual(self.rebuilt, 1, "an unmanifested cache must be rebuilt")
        self.assertEqual(self.member("one.wav"), b"PINNED-one.wav")

    def test_a_corrupt_manifest_is_not_trusted(self):
        self.warm()
        with open(prepare.member_manifest_path(self.src, self.url), "w",
                  encoding="utf-8") as f:
            f.write("{not json")
        self.warm()
        self.assertEqual(self.rebuilt, 2, "an unreadable manifest must force a rebuild")


class ArchiveRefetchTest(unittest.TestCase):
    """A local archive that does not match the pin self-heals once, then raises."""

    PIN = hashlib.sha256(b"GOOD").hexdigest()
    MEMBERS = {"one.wav": "pack/one.wav"}

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.url = "https://example.invalid/pack.7z"
        self.arc = os.path.join(self.src, "pack.7z")
        self.fetches = 0
        self.real_fetch = prepare.fetch
        self.real_run = prepare.subprocess.run
        self.addCleanup(setattr, prepare, "fetch", self.real_fetch)
        self.addCleanup(setattr, prepare.subprocess, "run", self.real_run)
        prepare.subprocess.run = self.fake_extract

    def fake_extract(self, *_args, **_kwargs):
        ext = os.path.join(self.src, "ext", "pack")
        os.makedirs(ext, exist_ok=True)
        with open(os.path.join(ext, "one.wav"), "wb") as f:
            f.write(b"MEMBER")

    def fetch_good(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as f:
            f.write(b"GOOD")

    def fetch_bad(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as f:
            f.write(b"BAD")

    def test_a_corrupt_local_archive_is_refetched_once(self):
        prepare.fetch = self.fetch_good
        with open(self.arc, "wb") as f:
            f.write(b"STALE")
        prepare.ensure_archive_sources(self.src, self.url, self.PIN,
                                       self.MEMBERS, "ext")
        self.assertEqual(self.fetches, 1, "the mismatched archive must be refetched once")
        self.assertTrue(prepare.cached_members_match(self.src, self.url, self.PIN,
                                                     self.MEMBERS))

    def test_a_served_archive_that_still_mismatches_raises(self):
        """Self-healing stops at one attempt: disagreeing bytes are not ours to accept."""
        prepare.fetch = self.fetch_bad
        with self.assertRaises(ValueError):
            prepare.ensure_archive_sources(self.src, self.url, self.PIN,
                                           self.MEMBERS, "ext")
        self.assertEqual(self.fetches, 2, "one initial fetch plus exactly one refetch")


if __name__ == "__main__":
    unittest.main()
