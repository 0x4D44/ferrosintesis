import os
import tempfile
import unittest
from unittest import mock

import prepare_drumkit


class DrumkitOutputPlanTests(unittest.TestCase):
    """MM-BUG-KILN-00124: the generator must preserve the package split."""

    def test_core_provenance_source_stems_match_the_generator_manifest(self):
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
        documented = {}
        for line in provenance.splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if len(cells) < 3 or not cells[0].startswith("`"):
                continue
            family = cells[0].split("`", 2)[1]
            source_stem = cells[2]
            if source_stem.startswith("`") and source_stem.endswith("`"):
                documented[family] = source_stem.strip("`")

        self.assertEqual(documented, expected)

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


if __name__ == "__main__":
    unittest.main()
