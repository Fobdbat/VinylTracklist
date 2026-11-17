import os
import sys
import struct
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from vinyltracklist.wavinfo import read_wav_info  # noqa: E402
from wavgen import write_wav  # noqa: E402


class WavInfoTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()

    def p(self, name):
        return os.path.join(self.d, name)

    def test_pcm16(self):
        write_wav(self.p("a.wav"), 44100, 2, 16, 1, seconds=25.2,
                  extra_chunks_before=[(b"LIST", b"INFOtest")])
        i = read_wav_info(self.p("a.wav"))
        self.assertTrue(i.ok, i.error)
        self.assertEqual((i.sample_rate, i.channels, i.effective_bits, i.is_float, i.is_pcm),
                         (44100, 2, 16, False, True))
        self.assertAlmostEqual(i.duration, 25.2, places=3)

    def test_pcm24_extensible(self):
        write_wav(self.p("b.wav"), 48000, 2, 24, 1, seconds=10, extensible=True)
        i = read_wav_info(self.p("b.wav"))
        self.assertTrue(i.ok)
        self.assertEqual((i.sample_rate, i.effective_bits, i.is_float, i.is_pcm), (48000, 24, False, True))

    def test_24_in_32_container(self):
        write_wav(self.p("c.wav"), 96000, 2, 32, 1, seconds=3, extensible=True, valid_bits=24)
        i = read_wav_info(self.p("c.wav"))
        self.assertTrue(i.ok)
        self.assertEqual((i.bits, i.effective_bits, i.is_float), (32, 24, False))
        self.assertAlmostEqual(i.duration, 3.0, places=4)

    def test_float(self):
        write_wav(self.p("d.wav"), 44100, 2, 32, 3, seconds=5)
        i = read_wav_info(self.p("d.wav"))
        self.assertTrue(i.ok)
        self.assertTrue(i.is_float)
        self.assertFalse(i.is_pcm)

    def test_float_extensible(self):
        write_wav(self.p("e.wav"), 88200, 2, 32, 3, seconds=2, extensible=True)
        i = read_wav_info(self.p("e.wav"))
        self.assertTrue(i.ok)
        self.assertTrue(i.is_float)
        self.assertEqual(i.sample_rate, 88200)

    def test_mono(self):
        write_wav(self.p("f.wav"), 44100, 1, 16, 1, seconds=1)
        i = read_wav_info(self.p("f.wav"))
        self.assertEqual(i.channels, 1)

    def test_rf64(self):
        write_wav(self.p("g.wav"), 48000, 2, 24, 1, seconds=6, container=b"RF64")
        i = read_wav_info(self.p("g.wav"))
        self.assertTrue(i.ok, i.error)
        self.assertEqual(i.container, "RF64")
        self.assertAlmostEqual(i.duration, 6.0, places=3)

    def test_odd_chunk_and_bext(self):
        write_wav(self.p("h.wav"), 44100, 2, 16, 1, seconds=7, odd_junk=True,
                  extra_chunks_before=[(b"bext", b"\x00" * 602)])
        i = read_wav_info(self.p("h.wav"))
        self.assertTrue(i.ok, i.error)
        self.assertAlmostEqual(i.duration, 7.0, places=3)

    def test_truncated(self):
        write_wav(self.p("i.wav"), 44100, 2, 16, 1, seconds=10, truncate_to=44100 * 4 * 4)
        i = read_wav_info(self.p("i.wav"))
        self.assertTrue(i.ok)
        self.assertTrue(i.truncated)
        self.assertAlmostEqual(i.duration, 4.0, places=3)

    def test_not_wav(self):
        with open(self.p("j.wav"), "wb") as f:
            f.write(b"ID3\x03\x00 this is an mp3 renamed" * 10)
        i = read_wav_info(self.p("j.wav"))
        self.assertFalse(i.ok)
        self.assertEqual(i.error, "err_not_wav")

    def test_compressed(self):
        write_wav(self.p("k.wav"), 44100, 2, 16, 0x55, seconds=1)
        i = read_wav_info(self.p("k.wav"))
        self.assertTrue(i.ok)
        self.assertFalse(i.is_pcm)
        self.assertFalse(i.is_float)
        self.assertEqual(i.format_tag, 0x55)

    def test_missing(self):
        i = read_wav_info(self.p("nope.wav"))
        self.assertFalse(i.ok)
        self.assertEqual(i.error, "err_io")

    def test_empty_file(self):
        open(self.p("l.wav"), "wb").close()
        i = read_wav_info(self.p("l.wav"))
        self.assertFalse(i.ok)

    def test_python_stdlib_agrees(self):
        # Contrast amb el mòdul wave de Python per a PCM 16 bits real
        import wave
        path = self.p("m.wav")
        w = wave.open(path, "wb")
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x01\x00\x02\x00" * 12345)
        w.close()
        i = read_wav_info(path)
        self.assertEqual(i.frames, 12345)


if __name__ == "__main__":
    unittest.main()
