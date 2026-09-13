import importlib.util
import tempfile
import unittest
import wave
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("to_flac.py")
SPEC = importlib.util.spec_from_file_location("to_flac", SCRIPT)
to_flac = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(to_flac)


class ToFlacBankPublicationTest(unittest.TestCase):
    NAMES = ("bank_C4.wav", "bank_E4.wav", "bank_G4.wav")

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.samples = root / "samples"
        self.samples.mkdir()
        for index, name in enumerate(self.NAMES, 1):
            with wave.open(str(self.samples / name), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(44100)
                output.writeframes((index.to_bytes(2, "little", signed=True)) * 4)
            (self.samples / name.replace(".wav", ".flac")).write_bytes(
                f"old bank: {name}".encode("ascii")
            )

    def snapshot(self):
        return {
            path.name: path.read_bytes()
            for path in self.samples.iterdir()
            if path.is_file()
        }

    def stage(self, staging, encode=None):
        def fake_encode(wav_path, flac_path):
            Path(flac_path).write_bytes(to_flac.riff_data_chunk(wav_path))

        with (
            mock.patch.object(to_flac, "encode", side_effect=encode or fake_encode),
            mock.patch.object(
                to_flac, "decoded_pcm", side_effect=lambda path, _scratch: Path(path).read_bytes()
            ),
        ):
            return to_flac._stage_bank(
                "fixture",
                str(self.samples),
                self.NAMES,
                str(staging),
                str(Path(staging).parent / "verify"),
            )

    def test_late_encode_failure_leaves_the_previous_bank_and_no_staging_files(self):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as staging:
            calls = 0

            def fail_on_third(wav_path, flac_path):
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("injected late encoder failure")
                Path(flac_path).write_bytes(to_flac.riff_data_chunk(wav_path))

            with self.assertRaisesRegex(OSError, "late encoder failure"):
                self.stage(staging, encode=fail_on_third)

            self.assertEqual(calls, 3)
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(list(Path(staging).iterdir()), [])

    def test_first_conversion_publishes_only_the_verified_flac_bank(self):
        expected = {
            name.replace(".wav", ".flac"): to_flac.riff_data_chunk(
                str(self.samples / name)
            )
            for name in self.NAMES
        }
        for name in self.NAMES:
            (self.samples / name.replace(".wav", ".flac")).unlink()

        with tempfile.TemporaryDirectory() as staging:
            plan = self.stage(staging)
            to_flac._publish_bank(plan)
            to_flac._cleanup_backup(plan)

            self.assertEqual(
                {path.name for path in self.samples.iterdir()},
                {name.replace(".wav", ".flac") for name in self.NAMES},
            )
            for name in self.NAMES:
                self.assertEqual(
                    (self.samples / name.replace(".wav", ".flac")).read_bytes(),
                    expected[name.replace(".wav", ".flac")],
                )

    def test_extra_staged_output_is_rejected_before_publication(self):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as staging:
            plan = self.stage(staging)
            (Path(staging) / "unexpected.flac").write_bytes(b"not part of the bank")

            with self.assertRaisesRegex(ValueError, "inventory mismatch"):
                to_flac._publish_bank(plan)

            self.assertEqual(self.snapshot(), before)

    def test_late_publish_failure_restores_every_file(self):
        before = self.snapshot()
        with tempfile.TemporaryDirectory() as staging:
            plan = self.stage(staging)
            real_replace = to_flac.os.replace
            publishes = 0

            def fail_on_second_publish(source, destination):
                nonlocal publishes
                destination_path = Path(destination)
                if destination_path.parent == self.samples and destination_path.suffix == ".flac":
                    publishes += 1
                    if publishes == 2:
                        raise OSError("injected late publication failure")
                return real_replace(source, destination)

            with mock.patch.object(to_flac.os, "replace", side_effect=fail_on_second_publish):
                with self.assertRaisesRegex(OSError, "late publication failure"):
                    to_flac._publish_bank(plan)

            self.assertGreaterEqual(publishes, 2)
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(
                [path.name for path in self.samples.iterdir() if path.name.startswith(".fixture-")],
                [],
            )


if __name__ == "__main__":
    unittest.main()
