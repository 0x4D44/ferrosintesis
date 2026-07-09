import os
import struct
import tempfile
import unittest
import urllib.error
import wave

import prepare


def write_wav(path, sample_width, channels):
    frames = 128
    raw = bytearray()
    for i in range(frames):
        for ch in range(channels):
            v = ((i + ch) % 17) / 16.0 - 0.5
            if sample_width == 2:
                raw.extend(struct.pack("<h", int(v * 32767)))
            else:
                raw.extend(int(v * 8388607).to_bytes(3, "little", signed=True))
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(sample_width)
        w.setframerate(44100)
        w.writeframes(bytes(raw))


class PrepareSampleBankTests(unittest.TestCase):
    def test_fetch_is_atomic_on_short_transfer(self):
        with tempfile.TemporaryDirectory() as td:
            final = os.path.join(td, "sample.wav")
            real_urlretrieve = prepare.urllib.request.urlretrieve

            def short_transfer(_url, filename):
                with open(filename, "wb") as f:
                    f.write(b"partial")
                raise urllib.error.ContentTooShortError("short", b"partial")

            prepare.urllib.request.urlretrieve = short_transfer
            try:
                with self.assertRaises(urllib.error.ContentTooShortError):
                    prepare.fetch("https://example.invalid/sample.wav", final)
            finally:
                prepare.urllib.request.urlretrieve = real_urlretrieve

            self.assertFalse(os.path.exists(final))
            self.assertFalse(os.path.exists(final + ".part"))

    def test_ensure_source_refetches_poisoned_cache_once(self):
        with tempfile.TemporaryDirectory() as td:
            final = os.path.join(td, "sample.wav")
            write_wav(final, 2, 2)
            os.truncate(final, os.path.getsize(final) - 17)
            calls = []
            real_urlretrieve = prepare.urllib.request.urlretrieve

            def good_transfer(_url, filename):
                calls.append(filename)
                write_wav(filename, 2, 2)

            prepare.urllib.request.urlretrieve = good_transfer
            try:
                prepare.ensure_source("sample.wav", "https://example.invalid/sample.wav", td)
            finally:
                prepare.urllib.request.urlretrieve = real_urlretrieve

            self.assertEqual(len(calls), 1)
            self.assertTrue(os.path.exists(final))
            self.assertFalse(os.path.exists(final + ".part"))
            samples, sr = prepare.read_wav(final)
            self.assertEqual(sr, 44100)
            self.assertEqual(len(samples), 128)

    def test_read_wav_rejects_truncated_16_and_24_bit_inputs(self):
        for sample_width in (2, 3):
            for channels in (1, 2):
                with self.subTest(sample_width=sample_width, channels=channels):
                    with tempfile.TemporaryDirectory() as td:
                        path = os.path.join(td, "sample.wav")
                        write_wav(path, sample_width, channels)
                        samples, sr = prepare.read_wav(path)
                        self.assertEqual(sr, 44100)
                        self.assertEqual(len(samples), 128)
                        os.truncate(path, os.path.getsize(path) - 17)
                        with self.assertRaises(ValueError):
                            prepare.read_wav(path)


if __name__ == "__main__":
    unittest.main()
