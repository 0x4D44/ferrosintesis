"""Regression tests for the fret-noise bake's reproducibility contract."""

from __future__ import annotations

import contextlib
import functools
import hashlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("fretnoise_bake.py")
SPEC = importlib.util.spec_from_file_location("fretnoise_bake", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BAKE = importlib.util.module_from_spec(SPEC)
# `fretnoise_bake` imports numpy, an optional dev dependency of the bake tools. Skip
# the module rather than letting the import raise, so the gate step stays green on a
# box without numpy and the lost coverage shows up as a skip.
try:
    SPEC.loader.exec_module(BAKE)
except ImportError as exc:  # pragma: no cover - only on a box without numpy
    raise unittest.SkipTest(f"numpy is required by fretnoise_bake: {exc}") from None


class FretNoiseBakeTests(unittest.TestCase):
    @staticmethod
    def _synthetic_payloads():
        return [
            (
                f"fretnoise_rr{i:02d}.flac",
                f"new payload {i}".encode(),
                0.0,
                0.0,
                0.0,
                0.0,
            )
            for i in range(1, 4)
        ]

    def test_staged_bank_validates_inventory_and_pinned_pcm(self) -> None:
        payloads = self._synthetic_payloads()
        pins = {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload, *_ in payloads
        }
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp)
            for name, payload, *_ in payloads:
                (staging / name).write_bytes(payload)

            self.assertEqual(
                BAKE.validate_staged_bank(
                    payloads, pins, staging, read_staged=Path.read_bytes
                ),
                [],
            )
            (staging / "fretnoise_rr99.flac").write_bytes(b"unexpected")
            errors = BAKE.validate_staged_bank(
                payloads, pins, staging, read_staged=Path.read_bytes
            )
            self.assertEqual(
                errors,
                ["fretnoise_rr99.flac: staged output was not generated"],
            )

    def test_late_staged_write_failure_leaves_published_bank_unchanged(self) -> None:
        payloads = self._synthetic_payloads()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "published"
            staging = root / "staging"
            out_dir.mkdir()
            staging.mkdir()
            old = {}
            for name, *_ in payloads:
                old[name] = f"old bank: {name}".encode()
                (out_dir / name).write_bytes(old[name])

            writes = 0

            def fail_on_third_write(payload, destination):
                nonlocal writes
                writes += 1
                destination.write_bytes(payload[:4])
                if writes == 3:
                    raise OSError("injected staged write failure")
                destination.write_bytes(payload)

            with self.assertRaisesRegex(OSError, "injected staged write failure"):
                BAKE.stage_fretnoise_bank(
                    payloads,
                    {},
                    staging,
                    encode=fail_on_third_write,
                    read_staged=Path.read_bytes,
                )

            self.assertEqual(writes, 3)
            self.assertEqual(
                {path.name: path.read_bytes() for path in out_dir.iterdir()}, old
            )

    def test_late_publish_replacement_failure_rolls_back_every_file(self) -> None:
        payloads = self._synthetic_payloads()
        expected = {name for name, *_ in payloads}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out_dir = root / "published"
            staging = root / "staging"
            out_dir.mkdir()
            staging.mkdir()
            old = {}
            for name, payload, *_ in payloads:
                old[name] = f"old bank: {name}".encode()
                (out_dir / name).write_bytes(old[name])
                (staging / name).write_bytes(payload)

            replacements = 0

            def fail_on_second_replace(source, destination):
                nonlocal replacements
                replacements += 1
                if replacements == 2:
                    raise OSError("injected replacement failure")
                os.replace(source, destination)

            with self.assertRaisesRegex(OSError, "injected replacement failure"):
                BAKE.publish_fretnoise_bank(
                    staging,
                    out_dir,
                    expected,
                    replace_file=fail_on_second_replace,
                )

            self.assertEqual(replacements, 2)
            self.assertEqual(
                {path.name: path.read_bytes() for path in out_dir.iterdir()}, old
            )

    def test_environment_contract_names_every_byte_identity_input(self) -> None:
        self.assertEqual(
            BAKE.canonical_environment_errors(
                BAKE.CANONICAL_PYTHON,
                "cpython",
                BAKE.CANONICAL_NUMPY,
                BAKE.CANONICAL_PLATFORM,
                BAKE.CANONICAL_MACHINE,
            ),
            [],
        )
        errors = BAKE.canonical_environment_errors(
            (3, 14, 4), "pypy", "2.4.5", "linux", "aarch64"
        )
        self.assertEqual(len(errors), 5)
        self.assertTrue(any("Python" in error for error in errors))
        self.assertTrue(any("NumPy" in error for error in errors))
        self.assertTrue(any("platform" in error for error in errors))
        self.assertTrue(any("machine" in error for error in errors))

    def test_pin_manifest_is_strict_and_rejects_duplicates(self) -> None:
        digest = hashlib.sha256(b"take").hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "BAKE-SHA256"
            manifest.write_text(
                f"# pins\n{digest}  fretnoise_rr01.flac\n", encoding="utf-8"
            )
            self.assertEqual(
                BAKE.load_output_pins(manifest),
                {"fretnoise_rr01.flac": digest},
            )
            manifest.write_text(
                f"{digest}  fretnoise_rr01.flac\n"
                f"{digest}  fretnoise_rr01.flac\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "duplicate"):
                BAKE.load_output_pins(manifest)
            manifest.write_text("not a pin\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "malformed"):
                BAKE.load_output_pins(manifest)

    def test_output_verifier_checks_generated_and_committed_bytes(self) -> None:
        """The committed side is read through the injected PCM reader.

        `read_committed=Path.read_bytes` keeps this a test of the VERIFIER — the
        pin bookkeeping and the three error paths — without needing ffmpeg or a
        real FLAC stream. The default reader decodes FLAC, and that route is
        exercised end-to-end by the canonical `--verify` test below.
        """
        name = "fretnoise_rr01.flac"
        payload = b"canonical payload"
        digest = hashlib.sha256(payload).hexdigest()
        generated = [(name, payload, 0.0, 0.0, 0.0, 0.0)]
        verify = functools.partial(
            BAKE.output_pin_errors, read_committed=Path.read_bytes
        )
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / name).write_bytes(payload)
            self.assertEqual(verify(generated, {name: digest}, out_dir), [])
            (out_dir / name).write_bytes(b"canonical payloae")
            errors = verify(generated, {name: digest}, out_dir)
            self.assertEqual(len(errors), 1)
            self.assertIn("committed sha256", errors[0])
            (out_dir / name).write_bytes(payload)
            (out_dir / "fretnoise_rr99.flac").write_bytes(payload)
            errors = verify(generated, {name: digest}, out_dir)
            self.assertEqual(
                errors,
                ["fretnoise_rr99.flac: committed output has no SHA-256 pin"],
            )

    def test_canonical_verify_rebakes_without_touching_assets(self) -> None:
        errors = BAKE.canonical_environment_errors()
        if errors:
            self.skipTest("canonical bake environment is unavailable: " + "; ".join(errors))

        root = BAKE.find_repo_root(SCRIPT.resolve())
        out_dir = root / "crates" / "ferrosintesis-samples-fretnoise" / "samples"
        before = {
            path.name: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(out_dir.glob("fretnoise_rr*.flac"))
        }
        self.assertEqual(len(before), 12, "the committed bank was not found")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            self.assertEqual(BAKE.main(["--verify"]), 0)
        after = {
            path.name: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(out_dir.glob("fretnoise_rr*.flac"))
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
