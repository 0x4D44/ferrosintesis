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

    def test_atlas_has_one_well_shaped_sidecar_per_midi(self) -> None:
        album = (Path(__file__).resolve().parents[1] / "albums" / "gpt5-6" /
                 "Atlas of Becoming")
        midis = sorted((album / "midi").glob("*.mid"))
        self.assertEqual(len(midis), 14)
        render_opus.validate_lyrics_sidecars(midis)
        notes = [render_opus.lyrics_for(midi) for midi in midis]
        self.assertTrue(all(note is not None for note in notes))
        for note in notes:
            assert note is not None
            self.assertTrue(note.startswith("Why this piece\n"))
            self.assertIn("\n\nListening guide\n", note)
            self.assertIn("\n\nMIDI techniques\n", note)


if __name__ == "__main__":
    unittest.main()
