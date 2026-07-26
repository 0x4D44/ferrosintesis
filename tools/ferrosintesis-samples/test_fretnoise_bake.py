"""Regression tests for the fret-noise bake's reproducibility contract."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("fretnoise_bake.py")
SPEC = importlib.util.spec_from_file_location("fretnoise_bake", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BAKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BAKE)


class FretNoiseBakeTests(unittest.TestCase):
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
                f"# pins\n{digest}  fretnoise_rr01.wav\n", encoding="utf-8"
            )
            self.assertEqual(
                BAKE.load_output_pins(manifest),
                {"fretnoise_rr01.wav": digest},
            )
            manifest.write_text(
                f"{digest}  fretnoise_rr01.wav\n"
                f"{digest}  fretnoise_rr01.wav\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SystemExit, "duplicate"):
                BAKE.load_output_pins(manifest)
            manifest.write_text("not a pin\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "malformed"):
                BAKE.load_output_pins(manifest)

    def test_output_verifier_checks_generated_and_committed_bytes(self) -> None:
        name = "fretnoise_rr01.wav"
        payload = b"canonical payload"
        digest = hashlib.sha256(payload).hexdigest()
        generated = [(name, payload, 0.0, 0.0, 0.0, 0.0)]
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            (out_dir / name).write_bytes(payload)
            self.assertEqual(
                BAKE.output_pin_errors(generated, {name: digest}, out_dir), []
            )
            (out_dir / name).write_bytes(b"canonical payloae")
            errors = BAKE.output_pin_errors(generated, {name: digest}, out_dir)
            self.assertEqual(len(errors), 1)
            self.assertIn("committed sha256", errors[0])
            (out_dir / name).write_bytes(payload)
            (out_dir / "fretnoise_rr99.wav").write_bytes(payload)
            errors = BAKE.output_pin_errors(generated, {name: digest}, out_dir)
            self.assertEqual(
                errors,
                ["fretnoise_rr99.wav: committed output has no SHA-256 pin"],
            )

    def test_canonical_verify_rebakes_without_touching_assets(self) -> None:
        errors = BAKE.canonical_environment_errors()
        if errors:
            self.skipTest("canonical bake environment is unavailable: " + "; ".join(errors))

        root = BAKE.find_repo_root(SCRIPT.resolve())
        out_dir = root / "crates" / "ferrosintesis-samples-fretnoise" / "samples"
        before = {
            path.name: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(out_dir.glob("fretnoise_rr*.wav"))
        }
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            self.assertEqual(BAKE.main(["--verify"]), 0)
        after = {
            path.name: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in sorted(out_dir.glob("fretnoise_rr*.wav"))
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
