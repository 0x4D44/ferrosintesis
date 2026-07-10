from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import render_opus


class LyricsSidecarTests(unittest.TestCase):
    def make_midi(self, root: Path, stem: str = "01 - Test") -> Path:
        midi = root / "album" / "midi" / f"{stem}.mid"
        midi.parent.mkdir(parents=True)
        midi.touch()
        return midi

    def test_missing_sidecar_is_optional(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            midi = self.make_midi(Path(td))
            self.assertIsNone(render_opus.lyrics_for(midi))

    def test_multiline_unicode_is_preserved_and_crlf_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            midi = self.make_midi(Path(td))
            sidecar = render_opus.lyrics_path_for(midi)
            sidecar.parent.mkdir()
            sidecar.write_bytes("Why\r\n\r\n0:12 — flute → choir\r\n".encode())
            self.assertEqual(
                render_opus.lyrics_for(midi),
                "Why\n\n0:12 — flute → choir",
            )

    def test_blank_nul_and_invalid_utf8_are_rejected(self) -> None:
        payloads = (b" \r\n", b"valid\x00invalid", b"\xff")
        for payload in payloads:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as td:
                midi = self.make_midi(Path(td))
                sidecar = render_opus.lyrics_path_for(midi)
                sidecar.parent.mkdir()
                sidecar.write_bytes(payload)
                with self.assertRaises(ValueError):
                    render_opus.lyrics_for(midi)

    def test_orphan_sidecar_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            midi = self.make_midi(Path(td))
            sidecar = midi.parent.parent / "lyrics" / "02 - Missing.txt"
            sidecar.parent.mkdir()
            sidecar.write_text("orphan", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "02 - Missing.txt"):
                render_opus.validate_lyrics_sidecars([midi])

    def test_encoder_comments_add_exactly_one_lyrics_value(self) -> None:
        lyrics = "Why\n\nListening guide"
        comments = render_opus.encoder_comments("Artist", 14, lyrics)
        self.assertEqual(
            [item for item in comments if item.startswith("LYRICS=")],
            [f"LYRICS={lyrics}"],
        )

    def test_every_committed_opus_has_one_well_shaped_sidecar(self) -> None:
        midis = [
            midi for midi in render_opus.all_midis()
            if render_opus.opus_path_for(midi).exists()
        ]
        render_opus.validate_lyrics_sidecars(midis)
        missing = [
            str(midi.relative_to(render_opus.REPO))
            for midi in midis if render_opus.lyrics_for(midi) is None
        ]
        self.assertFalse(missing, f"committed Opus files without lyrics: {missing}")
        for midi in midis:
            note = render_opus.lyrics_for(midi)
            assert note is not None
            self.assertTrue(note.startswith("Why this piece\n"))
            self.assertIn("\n\nListening guide\n", note)
            self.assertIn("\n\nMIDI techniques\n", note)
            self.assertLess(len(note), 8_000, midi.name)


if __name__ == "__main__":
    unittest.main()
