import hashlib
import os
import re
import struct
import tempfile
import unittest
import wave
from unittest import mock

import prepare
import prepare_drumkit


class DrumkitOutputPlanTests(unittest.TestCase):
    """MM-BUG-KILN-00124: the generator must preserve the package split."""

    def test_core_documented_source_stems_match_the_generator_manifest(self):
        """MM-BUG-KILN-00126/00131: both packaged docs derive from the manifest."""
        expected = {}
        for bank in prepare_drumkit.BANKS:
            package, family, url_format = bank[0], bank[1], bank[-1]
            if package == prepare_drumkit.CORE_PACKAGE:
                basename = os.path.splitext(os.path.basename(url_format))[0]
                expected[family] = basename.split("_vl{vl}", 1)[0].split(
                    "_rr{rr}", 1
                )[0]
        for bank in prepare_drumkit.PSEUDO_RR_BANKS:
            package, family, url_format = bank[0], bank[1], bank[-1]
            if package == prepare_drumkit.CORE_PACKAGE:
                basename = os.path.splitext(os.path.basename(url_format))[0]
                expected[family] = basename.split("_vl{vl}", 1)[0]

        provenance_path = os.path.join(
            prepare_drumkit.REPO_ROOT,
            "crates",
            prepare_drumkit.CORE_PACKAGE,
            "PROVENANCE.md",
        )
        with open(provenance_path, encoding="utf-8") as provenance_file:
            provenance = provenance_file.read()
        provenance_documented = {}
        for line in provenance.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3 or not cells[0].startswith("`"):
                continue
            family = cells[0].split("`", 2)[1]
            source_stem = cells[2]
            if source_stem.startswith("`") and source_stem.endswith("`"):
                provenance_documented[family] = source_stem.strip("`")

        self.assertEqual(provenance_documented, expected)

        rustdoc_path = os.path.join(
            prepare_drumkit.REPO_ROOT,
            "crates",
            prepare_drumkit.CORE_PACKAGE,
            "src",
            "lib.rs",
        )
        with open(rustdoc_path, encoding="utf-8") as rustdoc_file:
            rustdoc = rustdoc_file.read()
        rustdoc_documented = {}
        bank_pattern = re.compile(
            r"((?:\s*///[^\n]*\n)+)\s*pub static \w+: Bank = Bank \{\s*"
            r'name: "([^"]+)"',
            re.MULTILINE,
        )
        for doc, family in bank_pattern.findall(rustdoc):
            source_stems = re.findall(r"`([^`]+)`", doc)
            if source_stems:
                rustdoc_documented[family] = source_stems[0]

        self.assertEqual(rustdoc_documented, expected)

    def test_output_plan_matches_both_committed_package_inventories(self):
        planned = prepare_drumkit.output_plan()
        committed = {}
        for package in prepare_drumkit.OUTPUT_PACKAGES:
            sample_dir = os.path.join(
                prepare_drumkit.REPO_ROOT, "crates", package, "samples"
            )
            committed[package] = {
                name for name in os.listdir(sample_dir) if name.endswith(".wav")
            }

        self.assertEqual(planned, committed)
        self.assertEqual(
            {package: len(names) for package, names in planned.items()},
            {
                "ferrosintesis-samples-drumkit": 140,
                "ferrosintesis-samples-drumkit2": 48,
            },
        )

    def test_a_failed_generation_never_publishes_staged_outputs(self):
        with tempfile.TemporaryDirectory() as repo_root:
            with mock.patch.object(
                prepare_drumkit,
                "generate_staged",
                side_effect=OSError("injected generation failure"),
            ), mock.patch.object(prepare_drumkit, "publish_staged") as publish:
                with self.assertRaisesRegex(OSError, "injected generation failure"):
                    prepare_drumkit.regenerate("ffmpeg", "cache", repo_root)

            publish.assert_not_called()

    def test_output_plan_rejects_duplicate_or_unowned_banks(self):
        bank = (
            prepare_drumkit.CORE_PACKAGE,
            "only",
            1,
            1,
            0.1,
            0.1,
            (127,),
            "https://example.invalid/{vl}/{rr}",
        )
        with mock.patch.object(prepare_drumkit, "BANKS", [bank, bank]), \
                mock.patch.object(prepare_drumkit, "PSEUDO_RR_BANKS", []):
            with self.assertRaisesRegex(ValueError, "duplicate drum bank stem"):
                prepare_drumkit.output_plan()

        unowned = ("not-a-package", *bank[1:])
        with mock.patch.object(prepare_drumkit, "BANKS", [unowned]), \
                mock.patch.object(prepare_drumkit, "PSEUDO_RR_BANKS", []):
            with self.assertRaisesRegex(ValueError, "unknown output package"):
                prepare_drumkit.output_plan()

    def test_publish_copy_failure_preserves_both_packages(self):
        plans = {
            prepare_drumkit.CORE_PACKAGE: {"core.wav"},
            prepare_drumkit.ACCENT_PACKAGE: {"accent.wav"},
        }
        with tempfile.TemporaryDirectory() as root, \
                tempfile.TemporaryDirectory() as staging:
            for package, names in plans.items():
                staged_dir = os.path.join(staging, package)
                output_dir = os.path.join(root, "crates", package, "samples")
                os.makedirs(staged_dir)
                os.makedirs(output_dir)
                for name in names:
                    with open(os.path.join(staged_dir, name), "wb") as f:
                        f.write(b"new")
                    with open(os.path.join(output_dir, name), "wb") as f:
                        f.write(b"old")

            real_copyfile = prepare_drumkit.shutil.copyfile
            copies = 0

            def fail_second_copy(source, destination):
                nonlocal copies
                copies += 1
                if copies == 2:
                    raise OSError("injected copy failure")
                return real_copyfile(source, destination)

            with mock.patch.object(
                prepare_drumkit.shutil, "copyfile", side_effect=fail_second_copy
            ):
                with self.assertRaisesRegex(OSError, "injected copy failure"):
                    prepare_drumkit.publish_staged(staging, root, plans)

            for package, names in plans.items():
                output_dir = os.path.join(root, "crates", package, "samples")
                for name in names:
                    with open(os.path.join(output_dir, name), "rb") as f:
                        self.assertEqual(f.read(), b"old")
                    self.assertFalse(os.path.exists(
                        os.path.join(output_dir, name + ".part")
                    ))


class DrumkitSourceCacheTests(unittest.TestCase):
    """MM-BUG-KILN-00172: warm inputs must prove their source and recipe."""

    URL = "https://example.invalid/rev-a/source.flac"

    def setUp(self):
        self.cache_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.cache_dir.cleanup)
        self.served = b"PINNED-FLAC-A"
        self.decoded_sample = 1000
        self.fetches = 0
        self.decodes = 0

    @property
    def flac(self):
        return os.path.join(self.cache_dir.name, "source.flac")

    @property
    def wav(self):
        return os.path.join(self.cache_dir.name, "source_dec.wav")

    def fake_fetch(self, _url, path):
        self.fetches += 1
        with open(path, "wb") as output:
            output.write(self.served)

    def fake_run(self, args, **_kwargs):
        self.decodes += 1
        with wave.open(args[-1], "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(44100)
            output.writeframes(struct.pack(
                "<32h", *([self.decoded_sample] * 32)
            ))

    def ensure(self, url=URL, recipe="ffmpeg-pcm-s24le-native-v1"):
        with mock.patch.object(prepare, "fetch", side_effect=self.fake_fetch), \
                mock.patch.object(
                    prepare_drumkit.subprocess, "run", side_effect=self.fake_run
                ):
            return prepare_drumkit.ensure_decoded_source(
                "ffmpeg", self.cache_dir.name, url, recipe
            )

    def test_authenticated_warm_entry_is_reused(self):
        self.ensure()
        self.ensure()

        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.decodes, 1)

    def test_substituted_cached_flac_is_refetched(self):
        self.ensure()
        with open(self.flac, "wb") as output:
            output.write(b"SUBSTITUTED-VALID-FLAC")

        self.ensure()

        self.assertEqual(self.fetches, 2)
        self.assertEqual(
            prepare.sha256_file(self.flac),
            hashlib.sha256(self.served).hexdigest(),
        )

    def test_substituted_valid_decoded_wav_is_rebuilt(self):
        self.ensure()
        with wave.open(self.wav, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(44100)
            output.writeframes(struct.pack("<32h", *([2000] * 32)))

        self.ensure()

        self.assertEqual(self.decodes, 2)
        samples, _sample_rate = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 1000 / 32768.0)

    def test_changed_url_with_stable_basename_refetches_and_redecodes(self):
        self.ensure()
        self.served = b"PINNED-FLAC-B"
        self.decoded_sample = 2000

        self.ensure("https://example.invalid/rev-b/source.flac")

        self.assertEqual(self.fetches, 2)
        self.assertEqual(self.decodes, 2)
        samples, _sample_rate = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 2000 / 32768.0)

    def test_changed_decode_recipe_rebuilds_cached_wav(self):
        self.ensure(recipe="recipe-a")
        self.decoded_sample = 2000

        self.ensure(recipe="recipe-b")

        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.decodes, 2)
        samples, _sample_rate = prepare.read_wav(self.wav)
        self.assertAlmostEqual(samples[0], 2000 / 32768.0)

    def test_legacy_unmanifested_warm_entries_are_rebuilt(self):
        with open(self.flac, "wb") as output:
            output.write(b"LEGACY-FLAC")
        with wave.open(self.wav, "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(44100)
            output.writeframes(struct.pack("<32h", *([2000] * 32)))

        self.ensure()

        self.assertEqual(self.fetches, 1)
        self.assertEqual(self.decodes, 1)

    def test_malformed_manifests_are_rejected(self):
        self.ensure()
        with open(self.flac + ".source.json", "w", encoding="utf-8") as manifest:
            manifest.write("[]")
        with open(self.wav + ".source.json", "w", encoding="utf-8") as manifest:
            manifest.write("[]")

        self.ensure()

        self.assertEqual(self.fetches, 2)
        self.assertEqual(self.decodes, 2)


if __name__ == "__main__":
    unittest.main()
