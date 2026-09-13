"""Always-on integrity checks for the committed fret-noise bank."""

from __future__ import annotations

import hashlib
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = ROOT / "crates" / "ferrosintesis-samples-fretnoise" / "samples"
MANIFEST = ROOT / "crates" / "ferrosintesis-samples-fretnoise" / "BAKE-SHA256"
PIN_RE = re.compile(r"^([0-9a-f]{64})  (fretnoise_rr\d{2}\.flac)$")


def load_file_pins(path: Path) -> dict[str, str]:
    """Parse the exact packaged-file manifest without third-party dependencies."""
    pins: dict[str, str] = {}
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN_RE.fullmatch(line)
        if match is None:
            raise ValueError(f"{path}:{line_no}: malformed SHA-256 pin {raw!r}")
        digest, name = match.groups()
        if name in pins:
            raise ValueError(f"{path}:{line_no}: duplicate SHA-256 pin for {name}")
        pins[name] = digest
    if not pins:
        raise ValueError(f"{path}: no packaged-file SHA-256 pins")
    return pins


def file_pin_errors(
    manifest: Path,
    samples_dir: Path,
    read_file=Path.read_bytes,
) -> list[str]:
    """Return exact inventory and byte-hash failures for one packaged bank."""
    pins = load_file_pins(manifest)
    actual = {entry.name for entry in samples_dir.iterdir()}
    expected = set(pins)
    errors = [
        f"{name}: committed output has no SHA-256 pin"
        for name in sorted(actual - expected)
    ]
    errors.extend(
        f"{name}: committed output is missing" for name in sorted(expected - actual)
    )
    for name in sorted(expected & actual):
        path = samples_dir / name
        if not path.is_file():
            errors.append(f"{name}: committed output is not a file")
            continue
        digest = hashlib.sha256(read_file(path)).hexdigest()
        if digest != pins[name]:
            errors.append(f"{name}: sha256 {digest} != pinned {pins[name]}")
    return errors


class FretNoiseManifestTests(unittest.TestCase):
    def test_manifest_parser_rejects_duplicates_and_malformed_lines(self) -> None:
        digest = hashlib.sha256(b"payload").hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "BAKE-SHA256"
            manifest.write_text(
                f"{digest}  fretnoise_rr01.flac\n"
                f"{digest}  fretnoise_rr01.flac\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_file_pins(manifest)
            manifest.write_text("not a pin\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "malformed"):
                load_file_pins(manifest)

    def test_committed_bank_matches_exact_file_manifest(self) -> None:
        self.assertEqual(file_pin_errors(MANIFEST, SAMPLES_DIR), [])

    def test_manifest_requires_exact_filename_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            samples = root / "samples"
            samples.mkdir()
            payload = b"committed payload"
            (samples / "fretnoise_rr01.flac").write_bytes(payload)
            manifest = root / "BAKE-SHA256"
            manifest.write_text(
                f"{hashlib.sha256(payload).hexdigest()}  fretnoise_rr01.flac\n",
                encoding="utf-8",
            )

            (samples / "fretnoise_rr99.flac").write_bytes(payload)
            self.assertEqual(
                file_pin_errors(manifest, samples),
                ["fretnoise_rr99.flac: committed output has no SHA-256 pin"],
            )
            (samples / "fretnoise_rr99.flac").unlink()
            (samples / "fretnoise_rr01.flac").unlink()
            self.assertEqual(
                file_pin_errors(manifest, samples),
                ["fretnoise_rr01.flac: committed output is missing"],
            )

    def test_same_length_mutation_fails_the_exact_hash_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            samples = root / "samples"
            samples.mkdir()
            path = samples / "fretnoise_rr01.flac"
            original = b"same length payload"
            path.write_bytes(original)
            manifest = root / "BAKE-SHA256"
            manifest.write_text(
                f"{hashlib.sha256(original).hexdigest()}  {path.name}\n",
                encoding="utf-8",
            )
            self.assertEqual(file_pin_errors(manifest, samples), [])

            mutated = bytearray(original)
            mutated[-1] ^= 1
            self.assertEqual(len(mutated), len(original))
            path.write_bytes(mutated)
            errors = file_pin_errors(manifest, samples)
            self.assertEqual(len(errors), 1)
            self.assertIn("sha256", errors[0])


if __name__ == "__main__":
    unittest.main()
