import ast
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import struct
import tarfile
import tempfile
import unittest
import urllib.error
import wave
from unittest import mock

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
    def test_failed_wav_write_preserves_the_existing_destination(self):
        with tempfile.TemporaryDirectory() as output_dir:
            destination = os.path.join(output_dir, "tracked.wav")
            write_wav(destination, sample_width=2, channels=1)
            with open(destination, "rb") as f:
                original = f.read()

            with mock.patch.object(
                wave.Wave_write,
                "writeframes",
                side_effect=OSError("injected write failure"),
            ):
                with self.assertRaisesRegex(OSError, "injected write failure"):
                    prepare.write_wav_mono(destination, [0.25, -0.25], 44100)

            with open(destination, "rb") as f:
                self.assertEqual(f.read(), original)
            self.assertEqual(os.listdir(output_dir), ["tracked.wav"])

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

        # 208 -> 200 / orchestral 139 -> 131 on 2026.07.26: the eight retired VSCO
        # drum overlays left SOURCES (and the published crate) for
        # tools/ferrosintesis-samples/retired-drum-overlays/.
        self.assertEqual(len(filenames), 200)
        self.assertEqual(len(core), 69)
        self.assertEqual(len(orchestral), 131)
        self.assertNotIn(
            "drum",
            {name.split("_", 1)[0] for name in filenames},
            "the retired drum overlays must not be baked back into a crate",
        )
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
                for rr_i, name in enumerate(prepare.piano_take_names(note, dyn)):
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
                    bank[name] = x
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
                names = prepare.piano_take_names(note, dyn)
                if len(names) == 2:
                    a, b = (stats[name] for name in names)
                    self.assertLess(abs(a[0] - b[0]), 0.05)
                    self.assertLess(abs(a[1] - b[1]), 0.05)

        for note in prepare.PIANO_ZONE_NOTES:
            shape_ratios = [
                stats[name][0]
                for dyn in ("pp", "mf", "f")
                for name in prepare.piano_take_names(note, dyn)
            ]
            self.assertLess(max(shape_ratios) - min(shape_ratios), 0.05)
            body_levels = [
                stats[name][1]
                for dyn in ("pp", "mf", "f")
                for name in prepare.piano_take_names(note, dyn)
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

        self.assertEqual(len(bank), 52)
        stats = prepare.piano_envelope_stats(bank, prepare.OUT_SR)
        ratio_points = []
        for dyn in ("pp", "mf", "f"):
            for note in prepare.PIANO_ZONE_NOTES:
                names = prepare.piano_take_names(note, dyn)
                ratio_points.extend(
                    (prepare.PIANO_ZONE_MIDI[note], stats[name][0])
                    for name in names
                )
                if len(names) == 2:
                    a, b = (stats[name] for name in names)
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
                for name in prepare.piano_take_names(note, dyn):
                    ratio = stats[name][0]
                    ratios.append(ratio)
                    self.assertLess(
                        abs(ratio - target),
                        0.35,
                        f"{name}: shape misses register trend",
                    )
            self.assertLess(
                max(ratios) - min(ratios),
                0.35,
                f"{note}: velocity layers do not share one macro envelope",
            )

        level_points = []
        for note in prepare.PIANO_ZONE_NOTES:
            levels = [
                stats[name][1]
                for dyn in ("pp", "mf", "f")
                for name in prepare.piano_take_names(note, dyn)
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
                for name in prepare.piano_take_names(note, dyn):
                    body_db = stats[name][1]
                    self.assertLess(
                        abs(body_db - target),
                        0.35,
                        f"{name}: body level misses register trend",
                    )

    def test_b1_output_inventory_rejects_retired_or_incomplete_layers(self):
        sample_dir = os.path.join(
            prepare.REPO_ROOT,
            "crates",
            "ferrosintesis-samples-b1-upright",
            "samples",
        )
        expected = {
            name for name in os.listdir(sample_dir)
            if name.startswith("b1_") and name.endswith(".wav")
        }
        self.assertEqual(prepare.validate_b1_output_inventory(expected), expected)
        self.assertEqual(
            prepare.validate_b1_generated_inventory(expected, expected),
            expected,
        )

        with self.assertRaisesRegex(ValueError, "25 normal and 27 hard"):
            prepare.validate_b1_generated_inventory(expected, expected - {"b1_normal_A2.wav"})
        with self.assertRaisesRegex(ValueError, "retired or unknown"):
            prepare.validate_b1_generated_inventory(expected, expected | {"b1_soft_C4.wav"})
        substituted = (expected - {"b1_normal_A2.wav"}) | {"b1_normal_C#0.wav"}
        with self.assertRaisesRegex(ValueError, "differs from the committed bank"):
            prepare.validate_b1_generated_inventory(expected, substituted)

    def test_b1_body_is_the_ordinary_onset_trim_with_only_a_short_end_taper(self):
        sr = 4000
        source = [0.0] * 40 + [
            0.42
            * math.exp(-0.30 * i / sr)
            * math.sin(2.0 * math.pi * 220.0 * i / sr + 0.3)
            for i in range(int(2.0 * sr))
        ]

        expected = prepare.trim_to_onset(source, sr, 1.5, 0.010)
        untapered = prepare.trim_to_onset(source, sr, 1.5, 0.0)
        first = prepare.prepare_b1_body(source, sr)
        second = prepare.prepare_b1_body(source, sr)

        self.assertEqual(first, expected)
        self.assertEqual(second, expected)
        self.assertEqual(len(first), int((prepare.PRE_S + 1.5) * sr))
        self.assertLessEqual(max(abs(value) for value in first), 0.900001)

        # The retired 600 ms taper began around 0.9 s. The experiment must retain
        # the untapered body there and differ only inside the terminal 10 ms.
        fade_start = len(first) - int(0.010 * sr)
        self.assertEqual(first[:fade_start], untapered[:fade_start])
        self.assertNotEqual(first[fade_start:], untapered[fade_start:])
        self.assertLess(abs(first[-1]), 1e-3)

    def test_b1_tail_compander_is_the_accepted_mu255_mapping(self):
        controls = [-1.0, -0.25, -0.01, 0.0, 0.01, 0.25, 1.0]
        expected_codes = bytes([0, 32, 98, 128, 157, 223, 255])
        encoded = prepare.compand_b1_tail(controls)
        self.assertEqual(encoded, expected_codes)

        decoded = prepare.decode_b1_tail(encoded)
        expected_decoded = [
            -1.0,
            -0.2456980837065721,
            -0.010225303858321285,
            8.621159565072071e-05,
            0.010225303858321294,
            0.2456980837065721,
            1.0,
        ]
        for got, want in zip(decoded, expected_decoded):
            self.assertAlmostEqual(got, want, places=14)
        self.assertTrue(all(a < b for a, b in zip(decoded, decoded[1:])))
        self.assertEqual(
            prepare.compand_b1_tail(prepare.decode_b1_tail(bytes(range(256)))),
            bytes(range(256)),
        )

    def test_b1_tail_decimator_pins_phase_length_and_stopband(self):
        self.assertEqual(
            len(prepare.decimate_b1_tail([0.25] * 1025)),
            math.ceil(1025 / prepare.B1_TAIL_RATE_DIVISOR),
        )
        dc = prepare.decimate_b1_tail([0.25] * 8192)
        self.assertAlmostEqual(sum(dc[32:-32]) / len(dc[32:-32]), 0.25, places=12)

        def tone_rms(frequency):
            signal = [
                math.sin(2.0 * math.pi * frequency * i / prepare.OUT_SR)
                for i in range(prepare.OUT_SR)
            ]
            result = prepare.decimate_b1_tail(signal)[100:-100]
            return math.sqrt(sum(v * v for v in result) / len(result))

        reference = tone_rms(2000.0)
        at_5600 = 20.0 * math.log10(tone_rms(5600.0) / reference)
        at_6000 = 20.0 * math.log10(tone_rms(6000.0) / reference)
        self.assertLessEqual(at_5600, -20.0)
        self.assertLessEqual(at_6000, -45.0)

        impulse = [1.0] + [0.0] * 127
        first = prepare.decimate_b1_tail(impulse)
        second = prepare.decimate_b1_tail(impulse)
        self.assertEqual(first, second)
        expected_prefix = [
            0.2172666306994329,
            0.0302020278725563,
            -0.024697074581141825,
            0.017385945063066392,
            -0.010244953477404076,
            0.004803899643777737,
            -0.001638684494291428,
            0.00033810192489805674,
        ]
        for got, want in zip(first, expected_prefix):
            self.assertAlmostEqual(got, want, places=15)

    def test_b1_natural_tail_audit_accepts_identity_and_rejects_coloration(self):
        entry = prepare.B1_TAIL_ENTRY_FRAME
        body_frames = entry + 4096
        source_frames = 16_384
        archival = [
            0.15 * math.sin(2.0 * math.pi * 220.0 * i / prepare.OUT_SR)
            + 0.05 * math.sin(2.0 * math.pi * 1760.0 * i / prepare.OUT_SR)
            for i in range(entry + source_frames)
        ]
        body = list(archival[:body_frames])
        payload = prepare.compand_b1_tail(
            prepare.decimate_b1_tail(archival[entry:])
        )

        accepted = prepare.audit_b1_natural_tail(
            body, archival, payload, source_frames
        )
        self.assertGreaterEqual(accepted["waveform_snr_db"], 16.0)
        self.assertLessEqual(accepted["max_band_delta_db"], 6.0)
        self.assertLessEqual(accepted["centroid_delta_ratio"], 0.16)
        self.assertGreaterEqual(accepted["late_min_waveform_snr_db"], 2.0)
        self.assertLessEqual(accepted["late_max_band_delta_db"], 8.0)
        self.assertLessEqual(accepted["late_max_centroid_delta_ratio"], 0.40)
        self.assertLessEqual(accepted["max_seam_rms_delta_db"], 1.0)
        self.assertLessEqual(accepted["final_100ms_dc_error"], 1e-4)

        # A deliberately dark, half-amplitude tail is not the same recording.
        coloured = prepare.compand_b1_tail(
            [0.5 * value for value in prepare.decimate_b1_tail(archival[entry:])]
        )
        rejected = prepare.audit_b1_natural_tail(
            body, archival, coloured, source_frames
        )
        self.assertTrue(rejected["failures"])

    def test_b1_tail_chunk_is_strict_and_standard_wave_compatible(self):
        with tempfile.TemporaryDirectory() as output_dir:
            plain = os.path.join(output_dir, "plain.wav")
            write_wav(plain, sample_width=2, channels=1)
            with open(plain, "rb") as handle:
                original = handle.read()

            payload = bytes(range(17))
            extended = prepare.attach_b1_tail_chunk(
                original,
                payload,
                entry_frame=64,
                source_tail_frames=65,
            )
            info = prepare.inspect_b1_wav(extended)
            self.assertEqual(info["entry_frame"], 64)
            self.assertEqual(info["rate_divisor"], 4)
            self.assertEqual(info["source_tail_frames"], 65)
            self.assertEqual(info["payload"], payload)
            self.assertEqual(info["pcm_data"], original[44:])
            self.assertEqual(len(extended) % 2, 0)
            self.assertEqual(
                struct.unpack_from("<I", extended, 4)[0],
                len(extended) - 8,
            )

            # Python's standard reader must ignore the custom terminal chunk.
            with wave.open(io.BytesIO(extended), "rb") as reader:
                self.assertEqual(reader.getnframes(), 128)
                self.assertEqual(reader.readframes(128), original[44:])

            with self.assertRaisesRegex(ValueError, "duplicate"):
                prepare.inspect_b1_wav(
                    prepare.attach_b1_tail_chunk(
                        extended,
                        b"\x80",
                        entry_frame=64,
                        source_tail_frames=1,
                    )
                )
            truncated = bytearray(extended)
            truncated.pop()
            with self.assertRaisesRegex(ValueError, "RIFF|truncated"):
                prepare.inspect_b1_wav(bytes(truncated))
            outside_riff = extended + b"x"
            with self.assertRaisesRegex(ValueError, "beyond RIFF"):
                prepare.inspect_b1_wav(outside_riff)
            unsupported = bytearray(extended)
            tail = unsupported.index(b"b1t ")
            unsupported[tail + 8] = 2
            with self.assertRaisesRegex(ValueError, "version"):
                prepare.inspect_b1_wav(bytes(unsupported))
            wrong_length = bytearray(extended)
            struct.pack_into("<I", wrong_length, tail + 16, 69)
            with self.assertRaisesRegex(ValueError, "payload length"):
                prepare.inspect_b1_wav(bytes(wrong_length))

    def test_b1_bank_publication_stages_every_file_before_replace(self):
        with tempfile.TemporaryDirectory() as output_dir:
            destinations = {
                "b1_hard_A0.wav": ([0.0] * 60_000, b"\x80\x81", 8),
                "b1_normal_C1.wav": ([0.0] * 60_000, b"\x82\x83", 8),
            }
            originals = {}
            for name in destinations:
                path = os.path.join(output_dir, name)
                write_wav(path, sample_width=2, channels=1)
                with open(path, "rb") as handle:
                    originals[name] = handle.read()

            real_stage = prepare._stage_b1_wav
            calls = 0

            def fail_second(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected staging failure")
                return real_stage(*args, **kwargs)

            with mock.patch.object(
                prepare,
                "_stage_b1_wav",
                side_effect=fail_second,
            ):
                with self.assertRaisesRegex(OSError, "injected staging failure"):
                    prepare.publish_b1_bank(output_dir, destinations, sample_rate=44100)

            for name, expected in originals.items():
                with open(os.path.join(output_dir, name), "rb") as handle:
                    self.assertEqual(handle.read(), expected)
            self.assertFalse(any(".b1-stage-" in name for name in os.listdir(output_dir)))

    def test_b1_sustain_pilot_output_is_outside_every_git_tree_and_empty(self):
        with tempfile.TemporaryDirectory() as root:
            accepted = os.path.join(root, "new-output")
            self.assertEqual(
                prepare.validate_b1_pilot_output_dir(accepted, repo_root=prepare.REPO_ROOT),
                os.path.realpath(accepted),
            )

            os.makedirs(accepted)
            open(os.path.join(accepted, "old.wav"), "wb").close()
            with self.assertRaisesRegex(ValueError, "new or empty"):
                prepare.validate_b1_pilot_output_dir(
                    accepted, repo_root=prepare.REPO_ROOT
                )

        with tempfile.TemporaryDirectory() as git_root:
            os.makedirs(os.path.join(git_root, ".git"))
            nested = os.path.join(git_root, "untracked", "pilot")
            with self.assertRaisesRegex(ValueError, "Git working tree"):
                prepare.validate_b1_pilot_output_dir(
                    nested, repo_root=prepare.REPO_ROOT
                )

        with self.assertRaisesRegex(ValueError, "repository"):
            prepare.validate_b1_pilot_output_dir(
                os.path.join(prepare.REPO_ROOT, "pilot-output"),
                repo_root=prepare.REPO_ROOT,
            )

    def test_b1_sustain_pilot_dispatches_before_the_ordinary_baker(self):
        with tempfile.TemporaryDirectory() as root:
            output = os.path.join(root, "pilot")
            with (
                mock.patch.object(
                    prepare, "run_b1_sustain_pilot", return_value={"ok": True}
                ) as pilot,
                mock.patch.object(
                    prepare,
                    "_family_selection",
                    side_effect=AssertionError("ordinary baker was reached"),
                ),
                mock.patch.object(
                    prepare.sys,
                    "argv",
                    ["prepare.py", f"--b1-sustain-pilot={output}"],
                ),
            ):
                prepare.main()
            pilot.assert_called_once_with(output)

    def test_b1_sustain_pilot_preserves_assets_and_cleans_decode_temp(self):
        before = prepare.b1_asset_hashes()
        decode_dirs = []

        def successful_worker(_output, decode_dir):
            decode_dirs.append(decode_dir)
            open(os.path.join(decode_dir, "sentinel"), "wb").close()
            return {"ok": True}

        with tempfile.TemporaryDirectory() as root:
            output = os.path.join(root, "success")
            with mock.patch.object(
                prepare, "_build_b1_sustain_pilot", side_effect=successful_worker
            ):
                self.assertEqual(
                    prepare.run_b1_sustain_pilot(output),
                    {"ok": True},
                )
            self.assertFalse(os.path.exists(decode_dirs[-1]))

            failed = os.path.join(root, "failed")
            with mock.patch.object(
                prepare,
                "_build_b1_sustain_pilot",
                side_effect=RuntimeError("deliberate failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "deliberate failure"):
                    prepare.run_b1_sustain_pilot(failed)
            self.assertFalse(os.path.exists(failed))

        self.assertEqual(prepare.b1_asset_hashes(), before)

    def test_b1_sustain_budget_is_register_weighted_and_has_raw_headroom(self):
        self.assertEqual(prepare.b1_pilot_append_s(35), 1.25)
        self.assertEqual(prepare.b1_pilot_append_s(36), 0.75)
        self.assertEqual(prepare.b1_pilot_append_s(59), 0.75)
        self.assertEqual(prepare.b1_pilot_append_s(60), 0.50)
        self.assertEqual(prepare.b1_pilot_append_s(83), 0.50)
        self.assertEqual(prepare.b1_pilot_append_s(84), 0.0)

        sample_dir = os.path.join(
            prepare.REPO_ROOT,
            "crates",
            "ferrosintesis-samples-b1-upright",
            "samples",
        )
        projection = prepare.b1_pilot_size_projection(sample_dir)
        self.assertEqual(projection["zones"], 52)
        self.assertEqual(projection["append_frames"], 1267875)
        self.assertLessEqual(projection["projected_raw_bytes"], 9_500_000)
        self.assertGreaterEqual(projection["raw_headroom_ratio"], 0.05)

    def test_b1_pilot_felt_damper_matches_the_rust_curve(self):
        # Captured from voices.rs:PianoDamper::t60_for. Key 88 is the last
        # damped string; key 89 (F6) takes the 12-second undamped branch.
        expected = {
            21: 0.95,
            48: 0.6363961,
            65: 0.38949145,
            88: 0.20045221,
            89: 12.0,
        }
        for key, want in expected.items():
            self.assertAlmostEqual(prepare.b1_pilot_felt_t60(key), want, places=6)

        sr = 44100
        t60 = prepare.b1_pilot_felt_t60(65)
        mul = prepare.b1_pilot_release_mul(65, sr)
        self.assertAlmostEqual(mul ** round(t60 * sr), 1e-3, places=5)
        self.assertEqual(prepare.B1_PILOT_REAP_ENV, 1e-4)

    def test_b1_decay_fit_recovers_slow_shape_without_erasing_beats(self):
        hop_s = 0.025
        times = [1.5 + i * hop_s for i in range(261)]
        floor = 10 ** (-70.0 / 20.0)

        def slow_db(t):
            return -8.0 - 3.4 * (t - 1.5) - 3.0 * (1.0 - math.exp(-(t - 1.5)))

        observed = []
        for t in times:
            ripple_db = 0.7 * math.sin(2.0 * math.pi * 1.7 * t)
            signal = 10 ** ((slow_db(t) + ripple_db) / 20.0)
            observed.append(math.sqrt(signal * signal + floor * floor))

        fit = prepare.fit_b1_decay(
            times,
            observed,
            floor,
            knot_times=(1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.5, 8.0),
            median_radius_s=0.25,
        )
        self.assertGreaterEqual(len(fit), 6)
        self.assertTrue(
            all(a[1] >= b[1] for a, b in zip(fit, fit[1:])),
            f"fitted dB knots are not monotone: {fit}",
        )
        for t, got_db in fit:
            self.assertLess(abs(got_db - slow_db(t)), 1.0)

        residual = []
        for t, value in zip(times, observed):
            fitted_db = prepare.b1_decay_db_at(fit, t)
            clean = math.sqrt(max(0.0, value * value - floor * floor))
            residual.append(20.0 * math.log10(max(clean, 1e-12)) - fitted_db)
        self.assertGreater(max(residual) - min(residual), 1.0)

    def test_b1_loop_search_uses_the_same_decaying_beating_recording(self):
        sr = 4000
        f0 = 200.0
        duration_s = 4.0
        source = []
        for i in range(round(duration_s * sr)):
            t = i / sr
            decay = 10 ** (-3.0 * t / 20.0)
            tone = (
                math.sin(2.0 * math.pi * f0 * t)
                + 0.55 * math.sin(2.0 * math.pi * (f0 + 0.8) * t + 0.3)
                + 0.25 * math.sin(2.0 * math.pi * 2.03 * f0 * t + 0.7)
            )
            source.append(0.35 * decay * tone)

        knots = [(1.5, -4.5), (2.0, -6.0), (2.5, -7.5), (3.0, -9.0)]
        loop = prepare.find_b1_piano_loop(
            source,
            sr,
            search_start=round(1.5 * sr),
            search_end=round(2.5 * sr),
            f0=f0,
            decay_knots=knots,
        )
        self.assertGreaterEqual(loop["end"] - loop["start"], round(0.5 * sr))
        self.assertGreaterEqual(loop["start"], round(1.5 * sr))
        self.assertLessEqual(loop["end"], round(2.5 * sr))
        self.assertGreaterEqual(loop["crossfade"], round(0.020 * sr))
        self.assertLessEqual(loop["crossfade"], round(0.080 * sr))
        self.assertGreaterEqual(loop["crossfade_step_ratio"], 0.0)
        self.assertLess(loop["wrap_db"], -10.0)

        clean = prepare.b1_piano_loop_wrap_db(
            source, sr, loop["start"], loop["end"], knots
        )
        broken = prepare.b1_piano_loop_wrap_db(
            source, sr, loop["start"], loop["end"] - 37, knots
        )
        self.assertGreater(
            broken,
            clean + 3.0,
            f"37-frame endpoint displacement was not caught: {clean:.1f} vs {broken:.1f} dB",
        )

        rendered = prepare.render_b1_piano_loop(
            source,
            sr,
            loop,
            knots,
            duration_s=3.5,
            bend=2 ** (2.0 / 12.0),
        )
        self.assertEqual(len(rendered), round(3.5 * sr))
        self.assertTrue(all(math.isfinite(v) for v in rendered))
        self.assertLessEqual(max(abs(v) for v in rendered), 1.2)

        bend = 2 ** (2.0 / 12.0)
        flat = prepare._b1_decay_flattened(source, sr, knots)
        flat_reference_db = prepare.b1_decay_db_at(knots, knots[0][0])
        stride = loop["end"] - loop["start"] - loop["crossfade"]
        checked_fractional_loop = False
        for frame in range(math.ceil(
                (loop["end"] + loop["crossfade"]) / bend), len(rendered)):
            source_time = frame * bend
            pos = loop["start"] + loop["crossfade"] + (
                (source_time - loop["end"] - loop["crossfade"]) % stride
            )
            if pos >= loop["end"] - loop["crossfade"] or pos + 2 >= len(source):
                continue
            frac = pos - int(pos)
            if not 0.1 < frac < 0.9:
                continue
            expected = prepare._b1_cubic_loop(
                flat, pos, loop["start"], loop["end"]
            )
            target_db = prepare.b1_decay_db_at(knots, frame / sr)
            expected *= 10 ** ((target_db - flat_reference_db) / 20.0)
            self.assertAlmostEqual(rendered[frame], expected, places=12)
            checked_fractional_loop = True
            break
        self.assertTrue(checked_fractional_loop)

        unbent = prepare.render_b1_piano_loop(
            source, sr, loop, knots, duration_s=3.5
        )
        self.assertEqual(unbent[:loop["end"]], source[:loop["end"]])
        beat = prepare.b1_beat_diagnostic(source, sr, knots, floor_rms=1e-6)
        self.assertTrue(beat["supported"])
        self.assertGreater(beat["residual_depth_db_p90_p10"], 0.1)

    def test_b1_background_discards_handling_noise_but_keeps_note_free_room(self):
        sr = 8000
        rng = random.Random(119)
        samples = []
        for i in range(round(1.5 * sr)):
            time_s = i / sr
            scale = 0.025 if time_s < 0.60 else 0.003
            samples.append(scale * rng.uniform(-1.0, 1.0))
        pcm = struct.pack(
            f"<{len(samples)}h",
            *[int(value * 32767) for value in samples],
        )
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "take.wav")
            with wave.open(path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sr)
                wav.writeframes(pcm)
            floor = prepare.measure_b1_take_background(
                path, first_onset_sample=round(1.45 * sr)
            )
        self.assertGreaterEqual(floor["discarded_lead_s"], 0.20)
        self.assertLessEqual(floor["trend_db"], 3.0)
        self.assertLessEqual(floor["spread_db"], 6.0)

    def test_b1_background_rejects_a_stable_pitched_floor(self):
        sr = 8000
        samples = [
            0.01 * math.sin(2.0 * math.pi * 120.0 * i / sr)
            for i in range(round(1.5 * sr))
        ]
        pcm = struct.pack(
            f"<{len(samples)}h",
            *[int(value * 32767) for value in samples],
        )
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "pitched-take.wav")
            with wave.open(path, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sr)
                wav.writeframes(pcm)
            with self.assertRaisesRegex(ValueError, "coherent pitched energy"):
                prepare.measure_b1_take_background(
                    path, first_onset_sample=round(1.45 * sr)
                )

    def test_committed_piano_round_robins_are_distinct_or_declared_single_take(self):
        sample_dir = os.path.join(
            prepare.REPO_ROOT, "crates", "ferrosintesis-samples-core", "samples"
        )
        self.assertEqual(
            prepare.PIANO_SINGLE_TAKE_CELLS,
            frozenset({("C2", "pp"), ("G2", "pp")}),
        )
        for dyn in ("pp", "mf", "f"):
            for note in prepare.PIANO_ZONE_NOTES:
                names = prepare.piano_take_names(note, dyn)
                payloads = []
                for name in names:
                    with open(os.path.join(sample_dir, name), "rb") as sample:
                        payloads.append(sample.read())
                if len(names) == 1:
                    missing_rr2 = f"piano_{note}_{dyn}_rr2.wav"
                    self.assertFalse(os.path.exists(os.path.join(sample_dir, missing_rr2)))
                else:
                    self.assertNotEqual(
                        hashlib.sha256(payloads[0]).digest(),
                        hashlib.sha256(payloads[1]).digest(),
                        f"{note} {dyn}: advertised round robins are byte-identical",
                    )

    def test_fade_in_is_inert_when_lead_in_exceeds_the_window(self):
        """A source with >= 2 ms of lead-in must be cut exactly as before.

        Differential oracle against the pre-fix algorithm. This is the claim the
        already-committed WAVs rest on, and it is deliberately narrow: the fade
        cap only bites when the onset sits INSIDE the 2 ms window, so sources
        with more lead-in than that must come out bit-identical.

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


class DirectSourceCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00151: direct WAV caches must be bound to source URL + bytes."""

    URL_A = "https://example.invalid/rev-a/sample.wav"
    URL_B = "https://example.invalid/rev-b/sample.wav"

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.served_sample = 1000
        self.fetches = []
        self.fetch_patch = mock.patch.object(
            prepare, "fetch", side_effect=self.fake_fetch)
        self.fetch_patch.start()
        self.addCleanup(self.fetch_patch.stop)

    @property
    def wav(self):
        return os.path.join(self.src, "sample.wav")

    @staticmethod
    def write_constant_wav(path, sample):
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(struct.pack("<32h", *([sample] * 32)))

    def fake_fetch(self, url, path):
        self.fetches.append(url)
        self.write_constant_wav(path, self.served_sample)

    def ensure(self, url=URL_A):
        prepare.ensure_source("sample.wav", url, self.src)

    def cached_sample(self):
        samples, _sr = prepare.read_wav(self.wav)
        return round(samples[0] * 32768)

    def test_valid_warm_cache_is_reused_without_refetch(self):
        self.ensure()
        self.ensure()
        self.assertEqual(self.fetches, [self.URL_A])
        self.assertEqual(self.cached_sample(), 1000)

    def test_source_manifest_records_url_and_cached_sha256(self):
        self.ensure()
        with open(self.wav + ".source.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)
        self.assertEqual(
            manifest,
            {
                "schema": 1,
                "sha256": prepare.sha256_file(self.wav),
                "url": self.URL_A,
            },
        )

    def test_legacy_warm_wav_without_source_manifest_is_refetched(self):
        self.write_constant_wav(self.wav, 2222)
        self.ensure()
        self.assertEqual(self.fetches, [self.URL_A])
        self.assertEqual(self.cached_sample(), 1000)

    def test_valid_local_substitution_is_refetched(self):
        self.ensure()
        self.write_constant_wav(self.wav, 2222)
        self.ensure()
        self.assertEqual(self.fetches, [self.URL_A, self.URL_A])
        self.assertEqual(self.cached_sample(), 1000)

    def test_url_revision_change_with_stable_destination_refetches(self):
        self.ensure()
        self.served_sample = 3333
        self.ensure(self.URL_B)
        self.assertEqual(self.fetches, [self.URL_A, self.URL_B])
        self.assertEqual(self.cached_sample(), 3333)

    def test_ensure_direct_sources_uses_the_authenticated_cache(self):
        source_map = {"sample.wav": self.URL_A}
        prepare.ensure_direct_sources(self.src, source_map, "demo")
        self.write_constant_wav(self.wav, 2222)
        prepare.ensure_direct_sources(self.src, source_map, "demo")
        self.assertEqual(self.fetches, [self.URL_A, self.URL_A])
        self.assertEqual(self.cached_sample(), 1000)

    def test_ensure_direct_sources_refetches_changed_source_url(self):
        prepare.ensure_direct_sources(
            self.src, {"sample.wav": self.URL_A}, "demo")
        self.served_sample = 3333
        prepare.ensure_direct_sources(
            self.src, {"sample.wav": self.URL_B}, "demo")
        self.assertEqual(self.fetches, [self.URL_A, self.URL_B])
        self.assertEqual(self.cached_sample(), 3333)


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


class YdpArchiveCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00141: YDP warm caches remain bound to the archive pin."""

    MEMBER = "pack/YDP-GrandPiano.sf2"

    @staticmethod
    def archive_bytes(payload):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:bz2") as tf:
            info = tarfile.TarInfo(YdpArchiveCacheTest.MEMBER)
            info.size = len(payload)
            tf.addfile(info, io.BytesIO(payload))
        return stream.getvalue()

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.url = "https://example.invalid/ydp.tar.bz2"
        self.payload = b"PINNED-SF2"
        self.served = self.archive_bytes(self.payload)
        self.pin = hashlib.sha256(self.served).hexdigest()
        self.fetches = 0
        patches = [
            mock.patch.object(prepare, "YDP_URL", self.url),
            mock.patch.object(prepare, "YDP_SHA256", self.pin),
            mock.patch.object(prepare, "fetch", side_effect=self.fake_fetch),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    @property
    def sf2(self):
        return os.path.join(self.src, "YDP-GrandPiano.sf2")

    @property
    def archive(self):
        return os.path.join(self.src, os.path.basename(self.url))

    @property
    def manifest(self):
        return prepare.member_manifest_path(self.src, self.url)

    def fake_fetch(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as f:
            f.write(self.served)

    def ensure(self):
        return prepare.ensure_ydp_sf2(self.src)

    def cached_payload(self):
        with open(self.sf2, "rb") as f:
            return f.read()

    def test_valid_manifested_warm_cache_is_reused_without_archive(self):
        self.ensure()
        os.remove(self.archive)
        self.ensure()
        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.cached_payload(), self.payload)

    def test_altered_warm_sf2_is_rebuilt(self):
        self.ensure()
        with open(self.sf2, "wb") as f:
            f.write(b"ALTERED")
        self.ensure()
        self.assertEqual(self.cached_payload(), self.payload)

    def test_legacy_sf2_without_a_manifest_is_not_trusted(self):
        with open(self.sf2, "wb") as f:
            f.write(b"UNPROVEN")
        self.ensure()
        self.assertEqual(self.cached_payload(), self.payload)
        self.assertTrue(os.path.exists(self.manifest))

    def test_changed_pin_replaces_the_archive_and_sf2(self):
        self.ensure()
        self.payload = b"NEW-PINNED-SF2"
        self.served = self.archive_bytes(self.payload)
        new_pin = hashlib.sha256(self.served).hexdigest()
        with mock.patch.object(prepare, "YDP_SHA256", new_pin):
            self.ensure()
        self.assertEqual(self.cached_payload(), self.payload)
        self.assertEqual(self.fetches, 2)


class PinnedWarmCacheAuthenticationTest(unittest.TestCase):
    """Every pinned ensure helper must authenticate an already-present cache."""

    AUTHENTICATORS = {"cached_members_match", "sha256_file"}
    GUARDED_FETCH_AUTHENTICATORS = AUTHENTICATORS | {
        "decoded_wav_matches",
        "direct_source_matches",
    }

    @classmethod
    def unauthenticated_helpers(cls, source):
        tree = ast.parse(source)
        functions = {
            node.name: node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        def call_name(call):
            if isinstance(call.func, ast.Name):
                return call.func.id
            if isinstance(call.func, ast.Attribute):
                return call.func.attr
            return None

        def is_missing_guard(test):
            return (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and any(
                    isinstance(node, ast.Call) and call_name(node) == "exists"
                    for node in ast.walk(test)
                )
            )

        calls = {}
        direct_auth = set()
        for name, function in functions.items():
            calls[name] = set()

            def walk(node, behind_missing_guard=False):
                if isinstance(node, ast.If):
                    guarded = behind_missing_guard or is_missing_guard(node.test)
                    walk(node.test, behind_missing_guard)
                    for child in node.body:
                        walk(child, guarded)
                    for child in node.orelse:
                        walk(child, behind_missing_guard)
                    return
                if isinstance(node, ast.Call):
                    called = call_name(node)
                    if called:
                        calls[name].add((called, behind_missing_guard))
                        if not behind_missing_guard and (
                            called in cls.AUTHENTICATORS
                            or (
                                called == "sha256"
                                and isinstance(node.func, ast.Attribute)
                                and isinstance(node.func.value, ast.Name)
                                and node.func.value.id == "hashlib"
                            )
                        ):
                            direct_auth.add(name)
                for child in ast.iter_child_nodes(node):
                    walk(child, behind_missing_guard)

            for statement in function.body:
                walk(statement)

        pinned = set()
        for name, function in functions.items():
            if not name.startswith("ensure_"):
                continue
            referenced_names = {
                node.id for node in ast.walk(function) if isinstance(node, ast.Name)
            }
            parameter_names = {
                arg.arg for arg in function.args.args + function.args.kwonlyargs
            }
            if (
                any(ref.endswith("SHA256") for ref in referenced_names)
                or any("sha256" in param.lower() for param in parameter_names)
            ):
                pinned.add(name)

        authenticated = set(direct_auth)
        changed = True
        while changed:
            changed = False
            for name, edges in calls.items():
                if name in authenticated:
                    continue
                if any(
                    not guarded and called in authenticated
                    for called, guarded in edges
                ):
                    authenticated.add(name)
                    changed = True
        return sorted(pinned - authenticated)

    def test_every_pinned_ensure_helper_authenticates_its_warm_cache(self):
        with open(prepare.__file__, encoding="utf-8") as f:
            source = f.read()
        self.assertEqual(self.unauthenticated_helpers(source), [])

    def test_oracle_rejects_hashing_hidden_behind_a_missing_file_guard(self):
        source = """
PIN_SHA256 = "00"
def ensure_bad(src):
    path = src + "/cached"
    if not os.path.exists(path):
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        if digest != PIN_SHA256:
            raise ValueError
    return path
"""
        self.assertEqual(self.unauthenticated_helpers(source), ["ensure_bad"])

    @classmethod
    def guarded_fetches_without_authentication(cls, source):
        tree = ast.parse(source)
        functions = [
            node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

        def call_name(call):
            if isinstance(call.func, ast.Name):
                return call.func.id
            if isinstance(call.func, ast.Attribute):
                return call.func.attr
            return None

        def is_missing_guard(test):
            return (
                isinstance(test, ast.UnaryOp)
                and isinstance(test.op, ast.Not)
                and any(
                    isinstance(node, ast.Call) and call_name(node) == "exists"
                    for node in ast.walk(test)
                )
            )

        def is_hashlib_sha256(call):
            return (
                call_name(call) == "sha256"
                and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "hashlib"
            )

        offenders = []
        for function in functions:
            guarded_fetch = False
            direct_auth = False

            def walk(node, behind_missing_guard=False):
                nonlocal guarded_fetch, direct_auth
                if isinstance(node, ast.If):
                    guarded = behind_missing_guard or is_missing_guard(node.test)
                    walk(node.test, behind_missing_guard)
                    for child in node.body:
                        walk(child, guarded)
                    for child in node.orelse:
                        walk(child, behind_missing_guard)
                    return
                if isinstance(node, ast.Call):
                    called = call_name(node)
                    if called == "fetch" and behind_missing_guard:
                        guarded_fetch = True
                    if not behind_missing_guard and (
                        called in cls.GUARDED_FETCH_AUTHENTICATORS
                        or is_hashlib_sha256(node)
                    ):
                        direct_auth = True
                for child in ast.iter_child_nodes(node):
                    walk(child, behind_missing_guard)

            for statement in function.body:
                walk(statement)
            if guarded_fetch and not direct_auth:
                offenders.append(function.name)
        return sorted(offenders)

    def test_raw_fetch_behind_missing_file_guard_authenticates_warm_cache(self):
        with open(prepare.__file__, encoding="utf-8") as f:
            source = f.read()
        self.assertEqual(self.guarded_fetches_without_authentication(source), [])

    def test_oracle_rejects_bespoke_fetch_guard_without_digest(self):
        source = """
def _bake_bad(src):
    path = src + "/cached"
    if not os.path.exists(path):
        fetch("https://example.invalid/cached", path)
    return path
"""
        self.assertEqual(
            self.guarded_fetches_without_authentication(source), ["_bake_bad"])


class SalamanderArchiveCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00134: Salamander warm caches remain bound to the archive pin."""

    MEMBERS = {
        "grand_A.wav": "pack/A.wav",
        "grand_B.wav": "pack/B.wav",
    }

    @staticmethod
    def archive_bytes(contents):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w:bz2") as tf:
            for member, data in contents.items():
                info = tarfile.TarInfo(member)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        return stream.getvalue()

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.url = "https://example.invalid/salamander.tar.bz2"
        self.contents = {"pack/A.wav": b"PINNED-A", "pack/B.wav": b"PINNED-B"}
        self.served = self.archive_bytes(self.contents)
        self.pin = hashlib.sha256(self.served).hexdigest()
        self.fetches = 0

        patches = [
            mock.patch.object(prepare, "SALAMANDER_ARCHIVE_URL", self.url),
            mock.patch.object(prepare, "SALAMANDER_ARCHIVE_SHA256", self.pin),
            mock.patch.object(prepare, "GRAND_SOURCES", self.MEMBERS),
            mock.patch.object(prepare, "fetch", side_effect=self.fake_fetch),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    @property
    def archive(self):
        return os.path.join(self.src, os.path.basename(self.url))

    @property
    def manifest(self):
        return prepare.member_manifest_path(self.src, self.url)

    def fake_fetch(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as f:
            f.write(self.served)

    def ensure(self):
        prepare.ensure_salamander_sources(self.src)

    def member(self, fn):
        with open(os.path.join(self.src, fn), "rb") as f:
            return f.read()

    def test_valid_manifested_warm_cache_is_reused_without_archive(self):
        self.ensure()
        self.assertTrue(prepare.cached_members_match(
            self.src, self.url, self.pin, self.MEMBERS))
        os.remove(self.archive)
        self.ensure()
        self.assertEqual(self.fetches, 1)

    def test_altered_member_is_rebuilt(self):
        self.ensure()
        with open(os.path.join(self.src, "grand_A.wav"), "wb") as f:
            f.write(b"ALTERED")
        self.ensure()
        self.assertEqual(self.member("grand_A.wav"), b"PINNED-A")

    def test_truncated_member_is_rebuilt(self):
        self.ensure()
        with open(os.path.join(self.src, "grand_B.wav"), "wb") as f:
            f.write(b"")
        self.ensure()
        self.assertEqual(self.member("grand_B.wav"), b"PINNED-B")

    def test_missing_member_is_rebuilt(self):
        self.ensure()
        os.remove(os.path.join(self.src, "grand_A.wav"))
        self.ensure()
        self.assertEqual(self.member("grand_A.wav"), b"PINNED-A")

    def test_changed_pin_replaces_archive_and_members(self):
        self.ensure()
        self.contents = {"pack/A.wav": b"NEW-A", "pack/B.wav": b"NEW-B"}
        self.served = self.archive_bytes(self.contents)
        new_pin = hashlib.sha256(self.served).hexdigest()
        with mock.patch.object(prepare, "SALAMANDER_ARCHIVE_SHA256", new_pin):
            self.ensure()
            self.assertTrue(prepare.cached_members_match(
                self.src, self.url, new_pin, self.MEMBERS))
        self.assertEqual(self.member("grand_A.wav"), b"NEW-A")
        self.assertEqual(self.fetches, 2)

    def test_missing_manifest_is_not_trusted(self):
        self.ensure()
        os.remove(self.manifest)
        with open(os.path.join(self.src, "grand_A.wav"), "wb") as f:
            f.write(b"UNMANIFESTED")
        self.ensure()
        self.assertEqual(self.member("grand_A.wav"), b"PINNED-A")

    def test_corrupt_manifest_is_not_trusted(self):
        self.ensure()
        with open(self.manifest, "w", encoding="utf-8") as f:
            f.write("{not json")
        with open(os.path.join(self.src, "grand_A.wav"), "wb") as f:
            f.write(b"UNTRUSTED")
        self.ensure()
        self.assertEqual(self.member("grand_A.wav"), b"PINNED-A")

    def test_corrupt_cached_archive_is_refetched_once(self):
        with open(self.archive, "wb") as f:
            f.write(b"STALE")
        self.ensure()
        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.member("grand_A.wav"), b"PINNED-A")

    def test_served_archive_that_still_mismatches_fails_closed(self):
        self.served = b"BAD"
        with self.assertRaises(ValueError):
            self.ensure()
        self.assertEqual(self.fetches, 2)
        self.assertFalse(os.path.exists(self.manifest))

    def test_incomplete_archive_does_not_partially_replace_members(self):
        for fn in self.MEMBERS:
            with open(os.path.join(self.src, fn), "wb") as f:
                f.write(b"ORIGINAL-" + fn.encode())
        self.served = self.archive_bytes({"pack/A.wav": b"NEW-A"})
        new_pin = hashlib.sha256(self.served).hexdigest()
        with mock.patch.object(prepare, "SALAMANDER_ARCHIVE_SHA256", new_pin):
            with self.assertRaises(ValueError):
                self.ensure()
        self.assertEqual(self.member("grand_A.wav"), b"ORIGINAL-grand_A.wav")
        self.assertEqual(self.member("grand_B.wav"), b"ORIGINAL-grand_B.wav")
        self.assertFalse(os.path.exists(self.manifest))


class PinnedFlacCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00139: direct FLAC caches prove source and decoded identity."""

    URL = "https://example.invalid/rev/Samples/source.flac"
    SOURCES = {"headroom_C4_mf.wav": URL}

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.served = b"PINNED-FLAC"
        self.pin = hashlib.sha256(self.served).hexdigest()
        self.hashes = {"source.flac": self.pin}
        self.fetches = 0
        self.decodes = 0
        self.decoded_sample = 1000
        self.run_error = None
        self.fetch_patch = mock.patch.object(
            prepare, "fetch", side_effect=self.fake_fetch)
        self.run_patch = mock.patch.object(
            prepare.subprocess, "run", side_effect=self.fake_run)
        self.fetch_patch.start()
        self.run_patch.start()
        self.addCleanup(self.fetch_patch.stop)
        self.addCleanup(self.run_patch.stop)

    @property
    def wav(self):
        return os.path.join(self.src, "headroom_C4_mf.wav")

    @property
    def flac(self):
        return os.path.join(self.src, "source.flac")

    @property
    def manifest(self):
        return self.wav + ".source.json"

    def fake_fetch(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as f:
            f.write(self.served)

    def fake_run(self, args, **_kwargs):
        self.decodes += 1
        output = args[-1]
        with wave.open(output, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(struct.pack("<32h", *([self.decoded_sample] * 32)))
        if self.run_error is not None:
            raise self.run_error

    def ensure(self, recipe="pcm16le-v1", hashes=None):
        prepare.ensure_flac_sources(
            self.src, self.SOURCES, hashes or self.hashes, "headroom", recipe)

    def test_valid_manifested_warm_cache_is_reused(self):
        self.ensure()
        self.ensure()
        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.decodes, 1)

    def test_changed_upstream_bytes_fail_closed(self):
        self.served = b"UNPINNED"
        with self.assertRaises(ValueError):
            self.ensure()
        self.assertFalse(os.path.exists(self.flac))
        self.assertFalse(os.path.exists(self.wav))

    def test_altered_cached_flac_is_refetched(self):
        self.ensure()
        with open(self.flac, "wb") as f:
            f.write(b"ALTERED")
        self.ensure()
        self.assertEqual(self.fetches, 2)
        self.assertEqual(self.decodes, 1)
        self.assertEqual(prepare.sha256_file(self.flac), self.pin)

    def test_truncated_cached_wav_is_rebuilt(self):
        self.ensure()
        with open(self.wav, "wb") as f:
            f.write(b"RIFF")
        self.ensure()
        self.assertEqual(self.decodes, 2)
        samples, sr = prepare.read_wav(self.wav)
        self.assertEqual((len(samples), sr), (32, 44100))

    def test_altered_valid_cached_wav_is_rebuilt(self):
        self.ensure()
        with wave.open(self.wav, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(44100)
            w.writeframes(struct.pack("<32h", *([2000] * 32)))
        self.ensure()
        self.assertEqual(self.decodes, 2)
        samples, _sr = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 1000 / 32768.0)

    def test_source_revision_change_with_stable_names_rebuilds(self):
        self.ensure(recipe="rev-a")
        self.served = b"NEW-PINNED-FLAC"
        new_pin = hashlib.sha256(self.served).hexdigest()
        self.decoded_sample = 2000
        self.ensure(recipe="rev-b", hashes={"source.flac": new_pin})
        self.assertEqual(self.fetches, 2)
        self.assertEqual(self.decodes, 2)
        samples, _sr = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 2000 / 32768.0)

    def test_interrupted_decode_leaves_no_partial_cache_entry(self):
        self.run_error = RuntimeError("simulated ffmpeg interruption")
        with self.assertRaises(RuntimeError):
            self.ensure()
        self.assertFalse(os.path.exists(self.wav))
        self.assertFalse(os.path.exists(self.manifest))
        leftovers = [
            name for name in os.listdir(self.src)
            if name.startswith("headroom_C4_mf.wav.") and name.endswith(".wav")
        ]
        self.assertEqual(leftovers, [])

    def test_legacy_wav_without_manifest_is_rebuilt(self):
        self.ensure()
        os.remove(self.manifest)
        self.ensure()
        self.assertEqual(self.decodes, 2)

    def test_malformed_manifest_is_rebuilt(self):
        self.ensure()
        with open(self.manifest, "w", encoding="utf-8") as f:
            f.write("[]")
        self.ensure()
        self.assertEqual(self.decodes, 2)

    def test_headroom_urls_and_all_unique_payloads_are_pinned(self):
        source_names = {
            prepare.urllib.parse.unquote(os.path.basename(url))
            for url in prepare.HEADROOM_SOURCES.values()
        }
        self.assertEqual(len(source_names), 45)
        self.assertEqual(source_names, set(prepare.HEADROOM_FLAC_SHA256))
        self.assertTrue(all(
            f"/{prepare.HEADROOM_REV}/Samples/" in url
            for url in prepare.HEADROOM_SOURCES.values()
        ))

    def test_headroom_cache_identity_tracks_source_and_recipe_revisions(self):
        first = prepare.headroom_cache_path(self.src, "source-a", "recipe-a")
        changed_source = prepare.headroom_cache_path(
            self.src, "source-b", "recipe-a")
        changed_recipe = prepare.headroom_cache_path(
            self.src, "source-a", "recipe-b")
        self.assertNotEqual(first, changed_source)
        self.assertNotEqual(first, changed_recipe)


class MtgSaxCacheTest(unittest.TestCase):
    """MM-BUG-KILN-00157: sax warm inputs must prove their source identity."""

    BASE = "source"

    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.repo_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src, True)
        self.addCleanup(shutil.rmtree, self.repo_root, True)
        os.makedirs(os.path.join(
            self.repo_root, "crates", "ferrosintesis-samples-sax", "samples"))
        self.served_flac = b"PINNED-SAX-FLAC"
        self.decoded_sample = 1000
        self.fetches = []
        self.decodes = 0
        self.run_error = None

    @property
    def flac(self):
        return os.path.join(self.src, self.BASE + ".flac")

    @property
    def wav(self):
        return os.path.join(self.src, self.BASE + ".wav")

    @property
    def wav_manifest(self):
        return self.wav + ".source.json"

    def write_constant_wav(self, path, sample, sample_width=3):
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(sample_width)
            w.setframerate(48000)
            if sample_width == 2:
                frame = struct.pack("<h", sample)
                w.writeframes(frame * 64)
            else:
                frame = int(sample).to_bytes(3, "little", signed=True)
                w.writeframes(frame * 64)

    def write_region(self, dyn, sample_base=BASE):
        with open(os.path.join(self.src, f"sop_{dyn}_rr1.txt"),
                  "w", encoding="utf-8") as f:
            f.write(f"<region> key=60 sample={sample_base}.$EXT\n")

    def fake_fetch(self, _url, path):
        self.fetches.append(os.path.basename(path))
        if path.endswith(".txt"):
            self.write_region("f" if "_f_" in path else "p")
        elif path.endswith(".flac"):
            with open(path, "wb") as f:
                f.write(self.served_flac)
        else:
            raise AssertionError(f"unexpected sax fetch target {path}")

    def fake_run(self, args, **_kwargs):
        self.decodes += 1
        self.write_constant_wav(args[-1], self.decoded_sample)
        if self.run_error is not None:
            raise self.run_error

    def fake_measure(self, _x, _sr, nominal):
        return nominal, 1.0

    def fake_trim(self, x, _sr, _keep_s, _fade_s):
        return x[:16]

    def bake(self, recipe="mtg-sax-pcm24-v1"):
        with mock.patch.object(prepare, "MTG_SAX_INSTR", [("sop", "sop")]), \
             mock.patch.object(prepare, "MTG_SAX_ZONE_STEP", 99), \
             mock.patch.object(prepare, "MTG_SAX_DECODE_RECIPE_REV", recipe,
                               create=True), \
             mock.patch.object(prepare, "REPO_ROOT", self.repo_root), \
             mock.patch.object(prepare, "fetch", side_effect=self.fake_fetch), \
             mock.patch.object(prepare.subprocess, "run",
                               side_effect=self.fake_run), \
             mock.patch.object(prepare, "measure_f0_robust",
                               side_effect=self.fake_measure), \
             mock.patch.object(prepare, "trim_to_onset",
                               side_effect=self.fake_trim):
            return prepare._bake_mtg_sax(self.src)

    def fetch_count(self, suffix):
        return sum(1 for name in self.fetches if name.endswith(suffix))

    def test_legacy_unmanifested_warm_cache_is_not_trusted(self):
        for dyn in ("f", "p"):
            self.write_region(dyn)
        with open(self.flac, "wb") as f:
            f.write(b"ALTERED")
        self.write_constant_wav(self.wav, 2222)

        self.bake()

        self.assertGreater(self.fetch_count("_rr1.txt"), 0)
        self.assertGreater(self.fetch_count(".flac"), 0)
        self.assertGreater(self.decodes, 0)
        self.assertEqual(prepare.sha256_file(self.flac),
                         hashlib.sha256(self.served_flac).hexdigest())
        samples, _sr = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 1000 / 8388608.0)

    def test_valid_manifested_warm_cache_is_reused_without_refetch_or_decode(self):
        self.bake()
        fetches = list(self.fetches)
        decodes = self.decodes
        self.bake()
        self.assertEqual(self.fetches, fetches)
        self.assertEqual(self.decodes, decodes)

    def test_altered_sfz_region_is_refetched(self):
        self.bake()
        region_fetches = self.fetch_count("_rr1.txt")
        for dyn in ("f", "p"):
            self.write_region(dyn, "poison")
        self.bake()
        self.assertGreater(self.fetch_count("_rr1.txt"), region_fetches)
        self.assertEqual(self.fetch_count("poison.flac"), 0)

    def test_altered_cached_flac_is_refetched(self):
        self.bake()
        flac_fetches = self.fetch_count(".flac")
        with open(self.flac, "wb") as f:
            f.write(b"ALTERED")
        self.bake()
        self.assertGreater(self.fetch_count(".flac"), flac_fetches)
        self.assertEqual(prepare.sha256_file(self.flac),
                         hashlib.sha256(self.served_flac).hexdigest())

    def test_altered_cached_decoded_wav_is_rebuilt(self):
        self.bake()
        decodes = self.decodes
        self.write_constant_wav(self.wav, 2222)
        self.bake()
        self.assertGreater(self.decodes, decodes)
        samples, _sr = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 1000 / 8388608.0)

    def test_decode_recipe_change_rebuilds_cached_wav(self):
        self.bake(recipe="recipe-a")
        decodes = self.decodes
        self.decoded_sample = 2000
        self.bake(recipe="recipe-b")
        self.assertGreater(self.decodes, decodes)
        samples, _sr = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 2000 / 8388608.0)

    def test_interrupted_decode_leaves_no_partial_cache_entry(self):
        self.run_error = RuntimeError("simulated ffmpeg interruption")
        with self.assertRaises(RuntimeError):
            self.bake()
        self.assertFalse(os.path.exists(self.wav))
        self.assertFalse(os.path.exists(self.wav_manifest))
        leftovers = [
            name for name in os.listdir(self.src)
            if name.startswith(self.BASE + ".wav.") and name.endswith(".wav")
        ]
        self.assertEqual(leftovers, [])


#: URL ref position in a GitHub fetch: raw.githubusercontent.com/<owner>/<repo>/<REF>/…
#: and github.com/<owner>/<repo>/(archive|raw)/<REF>/…. Stops at the quote/brace that
#: ends the ref so an f-string interpolation is captured whole, as `{VCSL_REV}`.
_GH_REF_RE = re.compile(
    r"""raw\.githubusercontent\.com/[^/"'\s]+/[^/"'\s]+/([^/"'\s]+)/"""
    r"""|github\.com/[^/"'\s]+/[^/"'\s]+/(?:archive|raw)/([^/"'\s]+)/"""
)
_SHA1_RE = re.compile(r"\A[0-9a-f]{40}\Z")
_INTERPOLATION_RE = re.compile(r"\A\{[A-Za-z_][A-Za-z0-9_]*\}\Z")


def unpinned_github_refs(text):
    """Return every GitHub URL ref in `text` that is not immutable.

    Immutable means a literal 40-hex commit SHA, or an f-string interpolation of a
    single name (`{VCSL_REV}`) whose value is checked separately. A branch (`master`,
    `main`) or a tag is mutable: the bytes it serves can change under us, which for a
    sample bake means a silent re-voicing of a shipped bank.

    Text-based on purpose. The point is to catch a URL family added LATER, and a
    check that imported the constants could only see the families that already exist.
    """
    bad = []
    for m in _GH_REF_RE.finditer(text):
        ref = m.group(1) or m.group(2)
        if _SHA1_RE.match(ref) or _INTERPOLATION_RE.match(ref):
            continue
        bad.append(ref)
    return bad


class UpstreamRefsArePinnedTest(unittest.TestCase):
    """Every upstream GitHub fetch must name an immutable commit.

    Written after two of the ten VCSL URLs were found interpolating the literal
    `master` while the other eight used `VCSL_REV` — 102 WAVs off a moving branch in a
    tool where everything else is SHA-pinned. The per-family
    `test_headroom_urls_and_all_unique_payloads_are_pinned` could not catch it: it
    asserts about headroom and nothing else, so each new family arrived unguarded.
    This derives the set of URLs from the source text instead.
    """

    def bake_scripts(self):
        here = os.path.dirname(os.path.abspath(prepare.__file__))
        found = {}
        for name in sorted(os.listdir(here)):
            if name.endswith(".py") and not name.startswith("test_"):
                with open(os.path.join(here, name), encoding="utf-8") as f:
                    found[name] = f.read()
        self.assertIn("prepare.py", found)
        return found

    def test_no_bake_script_fetches_from_a_mutable_ref(self):
        offenders = {
            name: unpinned_github_refs(text)
            for name, text in self.bake_scripts().items()
        }
        offenders = {k: v for k, v in offenders.items() if v}
        self.assertEqual(offenders, {}, f"unpinned GitHub refs: {offenders}")

    def test_every_rev_constant_used_in_a_url_is_a_commit_sha(self):
        """The interpolation escape hatch must not smuggle in a branch name."""
        names = set()
        for text in self.bake_scripts().values():
            for m in _GH_REF_RE.finditer(text):
                ref = m.group(1) or m.group(2)
                if _INTERPOLATION_RE.match(ref):
                    names.add(ref[1:-1])
        self.assertIn("VCSL_REV", names, "expected the VCSL pin among the URL refs")
        for name in sorted(names):
            value = getattr(prepare, name, None)
            self.assertIsNotNone(value, f"{name} interpolated but not defined")
            self.assertRegex(
                value, _SHA1_RE, f"{name} = {value!r} is not a 40-hex commit SHA")

    def test_the_scan_rejects_the_refs_it_is_meant_to_reject(self):
        """The adversarial half: a scan nobody has seen fail proves nothing.

        Each case below is a URL this tool would plausibly grow, written the wrong
        way. If any stops being reported, the predicate has a hole.
        """
        owner = "raw.githubusercontent.com/sgossner/VCSL"
        cases = {
            f'"https://{owner}/master/Chordophones/x.wav"': ["master"],
            f'"https://{owner}/main/Chordophones/x.wav"': ["main"],
            f'"https://{owner}/HEAD/Chordophones/x.wav"': ["HEAD"],
            f'"https://{owner}/v1.2.0/Chordophones/x.wav"': ["v1.2.0"],
            # A tag looks pinned but GitHub lets it move; treat it as mutable.
            '"https://github.com/freepats/x/archive/refs.tar.gz/"': ["refs.tar.gz"],
            # f-string form, the shape the real bug took.
            f'f"https://{owner}/master/{{d}}/x.wav"': ["master"],
            # Short SHA: not 40 hex, so not accepted.
            f'"https://{owner}/c1ea7bc/Chordophones/x.wav"': ["c1ea7bc"],
            # Two offenders in one file must both surface, not just the first.
            f'"https://{owner}/master/a.wav" "https://{owner}/main/b.wav"':
                ["master", "main"],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(unpinned_github_refs(text), expected)

    def test_the_scan_accepts_the_real_pinned_forms(self):
        """The converse: it must not cry wolf on correctly-pinned URLs."""
        owner = "raw.githubusercontent.com/sgossner/VCSL"
        for text in (
            f'"https://{owner}/{prepare.VCSL_REV}/Chordophones/x.wav"',
            f'f"https://{owner}/{{VCSL_REV}}/Chordophones/x.wav"',
            'f"https://raw.githubusercontent.com/a/b/{SOME_REV}/p/x.wav"',
        ):
            with self.subTest(text=text):
                self.assertEqual(unpinned_github_refs(text), [])


class GeneratedOutputFamiliesTest(unittest.TestCase):
    """The shared validator fails closed for empty and multi-family plans."""

    def test_complete_directory_rejects_an_unexpected_generated_wav(self):
        with tempfile.TemporaryDirectory() as out_dir:
            open(os.path.join(out_dir, "accepted.wav"), "wb").close()
            open(os.path.join(out_dir, "stale.wav"), "wb").close()
            open(os.path.join(out_dir, "report.json"), "wb").close()
            with self.assertRaisesRegex(ValueError, r"stale\.wav"):
                prepare._validate_generated_output_inventory(
                    None, {"accepted.wav"}, output_dir=out_dir)

    def test_empty_expected_set_still_rejects_a_stale_owned_output(self):
        with tempfile.TemporaryDirectory() as out_dir:
            open(os.path.join(out_dir, "sax_old.wav"), "wb").close()
            with self.assertRaisesRegex(ValueError, r"sax_old\.wav"):
                prepare._validate_generated_output_families(
                    {"sax"}, set(), output_dir=out_dir)

    def test_each_named_family_is_checked_without_touching_siblings(self):
        with tempfile.TemporaryDirectory() as out_dir:
            for name in ("chanter_C4.wav", "drone_G2.wav", "other_old.wav"):
                open(os.path.join(out_dir, name), "wb").close()
            prepare._validate_generated_output_families(
                {"chanter", "drone"},
                {"chanter_C4.wav", "drone_G2.wav"},
                output_dir=out_dir,
            )


class HeadroomOutputInventoryTest(unittest.TestCase):
    """MM-BUG-KILN-00140: rebakes must reject obsolete owned outputs."""

    def assert_rebake_rejects_before_writing(self, sources, existing, unexpected):
        with tempfile.TemporaryDirectory() as repo_root:
            out_dir = os.path.join(
                repo_root, "crates", "ferrosintesis-samples-headroom", "samples")
            os.makedirs(out_dir)
            for name in existing:
                open(os.path.join(out_dir, name), "wb").close()

            with mock.patch.object(prepare, "REPO_ROOT", repo_root), mock.patch.object(
                prepare, "HEADROOM_SOURCES", sources
            ), mock.patch.object(
                prepare, "ensure_flac_sources"
            ) as ensure_sources, mock.patch.object(
                prepare, "write_wav_mono"
            ) as write_output, mock.patch.object(
                prepare.sys, "argv", ["prepare.py", "--only=headroom"]
            ):
                with self.assertRaisesRegex(ValueError, unexpected):
                    prepare.main()

            ensure_sources.assert_not_called()
            write_output.assert_not_called()

    def test_extra_output_is_rejected_before_the_first_write(self):
        self.assert_rebake_rejects_before_writing(
            {"headroom_C4_mf.wav": "https://example.invalid/C4.flac"},
            ["headroom_C4_mf.wav", "headroom_old.wav"],
            r"headroom_old\.wav",
        )

    def test_renamed_mapping_rejects_the_old_name_before_the_first_write(self):
        self.assert_rebake_rejects_before_writing(
            {"headroom_C4_medium.wav": "https://example.invalid/C4.flac"},
            ["headroom_C4_mf.wav"],
            r"headroom_C4_mf\.wav",
        )


class HonkytonkOutputInventoryTest(unittest.TestCase):
    """MM-BUG-KILN-00143: rebakes must reject obsolete owned outputs."""

    def assert_rebake_rejects_before_writing(self, notes, existing, unexpected):
        with tempfile.TemporaryDirectory() as repo_root:
            out_dir = os.path.join(
                repo_root, "crates", "ferrosintesis-samples-honkytonk", "samples")
            os.makedirs(out_dir)
            for name in existing:
                open(os.path.join(out_dir, name), "wb").close()

            with mock.patch.object(prepare, "REPO_ROOT", repo_root), mock.patch.object(
                prepare, "HONKYTONK_NOTES", notes
            ), mock.patch.object(
                prepare, "ensure_archive_sources"
            ) as ensure_sources, mock.patch.object(
                prepare.subprocess, "run"
            ) as decode, mock.patch.object(
                prepare, "write_wav_mono"
            ) as write_output:
                with self.assertRaisesRegex(ValueError, unexpected):
                    prepare._bake_honkytonk("unused-source-cache")

            ensure_sources.assert_not_called()
            decode.assert_not_called()
            write_output.assert_not_called()

    def test_extra_output_is_rejected_before_the_first_write(self):
        self.assert_rebake_rejects_before_writing(
            ["C4"],
            ["honkytonk_C4.wav", "honkytonk_old.wav"],
            r"honkytonk_old\.wav",
        )

    def test_renamed_note_rejects_the_old_name_before_the_first_write(self):
        self.assert_rebake_rejects_before_writing(
            ["D4"],
            ["honkytonk_C4.wav"],
            r"honkytonk_C4\.wav",
        )


class LocalBankSelectionTest(unittest.TestCase):
    """MM-BUG-KILN-00128: command modes must not rewrite an unrelated local bank."""

    def test_command_modes_select_only_the_intended_local_banks(self):
        cases = [
            (["--local-only"], ["gong"]),
            (["--only=bottle"], ["bottle"]),
            ([], ["gong", "bottle"]),
        ]
        for args, expected in cases:
            with self.subTest(args=args):
                calls = []
                with mock.patch.object(
                    prepare,
                    "_bake_gong_bank",
                    side_effect=lambda: calls.append("gong") or [],
                ), mock.patch.object(
                    prepare,
                    "bake_bottle_loop",
                    side_effect=lambda: calls.append("bottle") or [],
                ):
                    _local_only, only = prepare._family_selection(args)
                    prepare._bake_selected_local_banks(only)
                self.assertEqual(calls, expected)


class PrepareOnlySelectionContractTest(unittest.TestCase):
    """MM-BUG-KILN-00152: --only must fail for families prepare.py cannot produce."""

    def test_brass_section_selector_is_supported(self):
        _local_only, only = prepare._family_selection(["--only=brasssection"])
        self.assertEqual(only, {"brasssection"})

    def test_banjo_selector_points_at_the_real_recipe(self):
        with self.assertRaisesRegex(SystemExit, r"banjo.*banjo_extract\.py"):
            prepare._family_selection(["--only=banjo"])

    def test_unknown_selector_is_rejected(self):
        with self.assertRaisesRegex(
            SystemExit, r"unsupported prepare\.py --only family.*notafamily"
        ):
            prepare._family_selection(["--only=notafamily"])


class SoundfontOnsetZoneContractTest(unittest.TestCase):
    """A pinned preset must keep its reviewed root and channel inventory."""

    ROOTS = (41, 48, 54, 58, 60, 65, 69, 72, 77, 84)

    @staticmethod
    def zones(roots, sample_type=17):
        return [
            (root, index * 100, index * 100 + 80, 0, 0, 32000, sample_type)
            for index, root in enumerate(roots)
        ]

    def test_exact_unique_mono_inventory_is_accepted(self):
        prepare._validate_sf_onset_zones(self.zones(self.ROOTS), self.ROOTS)

    def test_duplicate_root_is_rejected(self):
        roots = self.ROOTS[:-1] + (77,)
        with self.assertRaisesRegex(ValueError, "roots"):
            prepare._validate_sf_onset_zones(self.zones(roots), self.ROOTS)

    def test_wrong_root_is_rejected(self):
        roots = self.ROOTS[:-1] + (85,)
        with self.assertRaisesRegex(ValueError, "roots"):
            prepare._validate_sf_onset_zones(self.zones(roots), self.ROOTS)

    def test_linked_or_stereo_zone_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "mono"):
            prepare._validate_sf_onset_zones(self.zones(self.ROOTS, sample_type=18), self.ROOTS)


class Orchestral2RegenerationRecipeTest(unittest.TestCase):
    """MM-BUG-KILN-00152: packaged docs must publish the banjo extractor command."""

    def test_packaged_provenance_names_the_banjo_extractor_command(self):
        path = os.path.join(
            prepare.REPO_ROOT,
            "crates",
            "ferrosintesis-samples-orchestral2",
            "PROVENANCE.md",
        )
        with open(path, encoding="utf-8") as f:
            provenance = f.read()
        # Interpreter-agnostic on purpose: `python` and `python3` are both correct
        # depending on the host, so pinning one name made a docs portability sweep
        # register here as a regression. What this oracle protects is that the
        # packaged provenance publishes the extractor command at all.
        self.assertRegex(
            provenance,
            r"python[0-9.]*\s+tools/ferrosintesis-samples/banjo_extract\.py",
        )
        self.assertNotIn("prepare.py --only=<family>", provenance)


class GrandRegenerationRecipeTest(unittest.TestCase):
    """MM-BUG-KILN-00135/00142: the copyable recipe selects only the grand family."""

    # The interpreter name is stripped before comparison. `python` and `python3` are
    # both correct depending on the host, and pinning one turned a docs portability
    # sweep into a false regression. What this oracle protects is unchanged: the
    # crate's only fenced prepare.py recipe must be the SCOPED one, so nobody copies
    # a command that regenerates every family.
    INTERPRETER = re.compile(r"^python[0-9.]*\s+")
    COMMAND = "tools/ferrosintesis-samples/prepare.py --only=grand"

    @classmethod
    def fenced_prepare_commands(cls, text):
        commands = []
        block = None
        for line in text.splitlines():
            if line.startswith("```"):
                if block is None:
                    block = []
                else:
                    commands.extend(
                        cls.INTERPRETER.sub("", candidate.strip())
                        for candidate in block
                        if "prepare.py" in candidate
                    )
                    block = None
            elif block is not None:
                block.append(line)
        return commands

    def test_packaged_grand_docs_use_the_scoped_command(self):
        crate = os.path.join(
            prepare.REPO_ROOT, "crates", "ferrosintesis-samples-grand")
        for name in ("README.md", "PROVENANCE.md"):
            with self.subTest(name=name):
                with open(os.path.join(crate, name), encoding="utf-8") as f:
                    commands = self.fenced_prepare_commands(f.read())
                self.assertEqual(commands, [self.COMMAND])

    def test_wrong_fenced_command_is_not_redeemed_by_correct_prose(self):
        adversarial = f"""
```powershell
python tools/ferrosintesis-samples/prepare.py
```

For comparison, the text mentions {self.COMMAND}.
"""
        self.assertNotEqual(
            self.fenced_prepare_commands(adversarial), [self.COMMAND])

    def test_stripping_the_interpreter_does_not_excuse_an_unscoped_command(self):
        """The loosened match must still turn on scoping, not on the interpreter.

        Normalising `python`/`python3` away is what lets a portability sweep pass,
        but it must not let an UNSCOPED recipe through — that is the whole defect
        MM-BUG-KILN-00135/00142 filed. Each of these should be rejected.
        """
        for wrong in (
            "python3 tools/ferrosintesis-samples/prepare.py",
            "python tools/ferrosintesis-samples/prepare.py",
            "python3.11 tools/ferrosintesis-samples/prepare.py",
            "python3 tools/ferrosintesis-samples/prepare.py --only=orchestral",
        ):
            with self.subTest(wrong=wrong):
                self.assertNotEqual(
                    self.fenced_prepare_commands(f"```sh\n{wrong}\n```"),
                    [self.COMMAND],
                )

    def test_the_scoped_command_is_accepted_under_either_interpreter(self):
        for right in (
            "python tools/ferrosintesis-samples/prepare.py --only=grand",
            "python3 tools/ferrosintesis-samples/prepare.py --only=grand",
        ):
            with self.subTest(right=right):
                self.assertEqual(
                    self.fenced_prepare_commands(f"```sh\n{right}\n```"),
                    [self.COMMAND],
                )

    def test_grand_selector_excludes_unrelated_local_banks(self):
        local_only, only = prepare._family_selection(["--only=grand"])
        self.assertFalse(local_only)
        self.assertEqual(only, {"grand"})
        self.assertTrue(prepare._wants_family(only, "grand"))
        self.assertFalse(prepare._wants_family(only, "gong"))
        self.assertFalse(prepare._wants_family(only, "bottle"))
        with mock.patch.object(
            prepare, "_bake_gong_bank"
        ) as gong, mock.patch.object(
            prepare, "bake_bottle_loop"
        ) as bottle:
            self.assertEqual(prepare._bake_selected_local_banks(only), [])
        gong.assert_not_called()
        bottle.assert_not_called()


class DarkenedGrandInventoryTest(unittest.TestCase):
    """MM-BUG-KILN-00123: a rebake must reject obsolete owned outputs."""

    def test_rebake_rejects_unexpected_owned_output_before_writing(self):
        with tempfile.TemporaryDirectory() as repo_root:
            grand_dir = os.path.join(
                repo_root, "crates", "ferrosintesis-samples-grand", "samples"
            )
            out_dir = os.path.join(
                repo_root,
                "crates",
                "ferrosintesis-samples-dark-salamander",
                "samples",
            )
            os.makedirs(grand_dir)
            os.makedirs(out_dir)
            open(os.path.join(grand_dir, "grand_C4_mf.wav"), "wb").close()
            open(os.path.join(out_dir, "darkgrand_C4_mf.wav"), "wb").close()
            open(os.path.join(out_dir, "darkgrand_old.wav"), "wb").close()

            with mock.patch.object(prepare, "REPO_ROOT", repo_root), mock.patch.object(
                prepare,
                "read_wav",
                side_effect=AssertionError("inventory must be checked before reading"),
            ):
                with self.assertRaisesRegex(ValueError, r"darkgrand_old\.wav"):
                    prepare._bake_darkened_grand(None)


class BottleLoopTest(unittest.TestCase):
    """MM-BUG-KILN-00065: the GM 76 whole-voice loop must have exactly one owner.

    Before this, nothing emitted the active `bottleloop_G3.wav`; the generic onset
    discovery would have trimmed its source to an attack and routed the result to
    `ferrosintesis-samples-orchestral`, and `--only=bottle` never staged the source.
    """

    def test_the_bottle_source_is_not_a_generic_onset_source(self):
        """Discovery must not sweep the whole-voice source into the onset loop."""
        self.assertNotIn(prepare.BOTTLE_LOOP_SOURCE, prepare.FREESOUND_SOURCES)

    def test_bottle_output_never_routes_to_the_orchestral_crate(self):
        with tempfile.TemporaryDirectory() as root:
            for name in (prepare.BOTTLE_LOOP_OUT, prepare.BOTTLE_LOOP_SOURCE):
                path = prepare.sample_output_path(name, root)
                crate = os.path.relpath(path, root).split(os.sep)[1]
                self.assertEqual(
                    crate, "ferrosintesis-samples-bottle",
                    f"{name} routes to {crate} - the bottle owns its own crate")

    def test_bottle_loop_reproduces_the_committed_asset(self):
        """The recovered recipe is pinned against the shipped bytes.

        It reproduces the committed asset to within a few LSB but NOT byte-for-byte
        (the original bake is not checked in, so its exact float path is unknown).
        The bound is what makes the recipe a real pin rather than a plausible story:
        a wrong trim, fade or gain moves it by thousands of LSB, not a handful.
        """
        with tempfile.TemporaryDirectory() as root:
            got = prepare.bake_bottle_loop(repo_root=root)
            written = os.path.join(root, "crates", "ferrosintesis-samples-bottle",
                                   "samples", prepare.BOTTLE_LOOP_OUT)
            self.assertTrue(os.path.exists(written), "the bake wrote no file")
        committed = os.path.join(prepare.REPO_ROOT, "crates",
                                 "ferrosintesis-samples-bottle", "samples",
                                 prepare.BOTTLE_LOOP_OUT)
        with wave.open(committed, "rb") as w:
            n = w.getnframes()
            want = list(struct.unpack(f"<{n}h", w.readframes(n)))
        self.assertEqual(len(got), len(want), "the bake produced a different length")
        worst = max(abs(a - b) for a, b in zip(got, want))
        peak = max(abs(v) for v in want)
        self.assertLessEqual(
            worst, 24,
            f"the bake drifted {worst} LSB from the committed asset (peak {peak}) - "
            f"the recipe no longer describes what is shipped")

    def test_a_tampered_source_is_refused(self):
        """The pin is the point: a changed source must not be baked silently."""
        with tempfile.TemporaryDirectory() as src_dir:
            path = os.path.join(src_dir, prepare.BOTTLE_LOOP_SOURCE)
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(prepare.OUT_SR)
                w.writeframes(struct.pack("<8h", *([1000] * 8)))
            with self.assertRaises(ValueError):
                prepare.bake_bottle_loop(src_dir=src_dir)


if __name__ == "__main__":
    unittest.main()
