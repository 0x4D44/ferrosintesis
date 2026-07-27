import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np


SCRIPT = Path(__file__).with_name("banjo_extract.py")
SPEC = importlib.util.spec_from_file_location("banjo_extract", SCRIPT)
banjo_extract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(banjo_extract)


class BanjoPublicationTest(unittest.TestCase):
    """MM-BUG-KILN-00153: a failed regeneration preserves the old bank."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.out = root / "samples"
        self.staging = root / "staging"
        self.out.mkdir()
        self.staging.mkdir()
        self.expected = banjo_extract.expected_banjo_files()
        self.old_bytes = {}
        for name in self.expected:
            old = f"old bank: {name}".encode()
            (self.out / name).write_bytes(old)
            self.old_bytes[name] = old
            banjo_extract.write_wav16(
                self.staging / name, np.array([0.0, 0.25, -0.25, 0.0]))

    def assert_old_bank_unchanged(self):
        self.assertEqual(
            {path.name for path in self.out.glob(banjo_extract.BANJO_GLOB)},
            set(self.expected),
        )
        for name, old in self.old_bytes.items():
            self.assertEqual((self.out / name).read_bytes(), old)

    def test_missing_zone_is_rejected_before_publication(self):
        (self.staging / sorted(self.expected)[0]).unlink()

        with self.assertRaisesRegex(RuntimeError, "missing: banjo_"):
            banjo_extract.publish_banjo_bank(self.staging, self.out)

        self.assert_old_bank_unchanged()

    def test_mid_publish_write_failure_rolls_back_every_file(self):
        replacements = 0

        def fail_on_fifth_replace(source, destination):
            nonlocal replacements
            replacements += 1
            if replacements == 5:
                raise OSError("injected replacement failure")
            os.replace(source, destination)

        with self.assertRaisesRegex(OSError, "injected replacement failure"):
            banjo_extract.publish_banjo_bank(
                self.staging, self.out, replace_file=fail_on_fifth_replace)

        self.assertEqual(replacements, 5)
        self.assert_old_bank_unchanged()

    def test_complete_bank_replaces_every_file_and_removes_obsolete_ones(self):
        (self.out / "banjo_obsolete.wav").write_bytes(b"obsolete")

        banjo_extract.publish_banjo_bank(self.staging, self.out)

        self.assertEqual(
            banjo_extract.validate_banjo_output_plan(self.out), self.expected)
        self.assertFalse((self.out / "banjo_obsolete.wav").exists())
        for name, old in self.old_bytes.items():
            self.assertNotEqual((self.out / name).read_bytes(), old)


if __name__ == "__main__":
    unittest.main()
