"""Regression tests for the fret-noise bake's reproducibility contract."""

from __future__ import annotations

import contextlib
import functools
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
# `fretnoise_bake` imports numpy, an optional dev dependency of the bake tools. Skip
# the module rather than letting the import raise, so the gate step stays green on a
# box without numpy and the lost coverage shows up as a skip.
try:
    SPEC.loader.exec_module(BAKE)
except ImportError as exc:  # pragma: no cover - only on a box without numpy
    raise unittest.SkipTest(f"numpy is required by fretnoise_bake: {exc}") from None


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
