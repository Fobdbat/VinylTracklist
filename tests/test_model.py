# -*- coding: utf-8 -*-
import os
import shutil
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from vinyltracklist import config  # noqa: E402
from vinyltracklist.model import Project, title_from_filename, fmt_dur  # noqa: E402
from vinyltracklist.export import build_report, write_txt, write_docx, write_pdf  # noqa: E402
from wavgen import write_wav  # noqa: E402


def make(d, name, sec, **kw):
    """Per defecte 8 kHz mono 8 bits: fitxers petits encara que durin molts minuts."""
    p = os.path.join(d, name)
    write_wav(p, kw.get("rate", 8000), kw.get("ch", 1), kw.get("bits", 8), kw.get("tag", 1), seconds=sec)
    return p


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cfg = config.load_config()
        self.cfg["ranges"] = config.DEFAULT_RANGES
        self.cfg["float_not_ok"] = True

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_titles(self):
        cases = {
            "A04_TENDRAS_QUE_CONFORMARTE.wav": "TENDRAS QUE CONFORMARTE",
            "04_-_TENDRAS_QUE_CONFORMARTE.wav": "TENDRAS QUE CONFORMARTE",
            "01 - Intro.wav": "Intro",
            "B1 Tornada.wav": "Tornada",
            "1. Hola.wav": "Hola",
            "Sense numero.wav": "Sense numero",
            "1999 Party.wav": "1999 Party",
            "12.wav": "12",
        }
        for fn, exp in cases.items():
            self.assertEqual(title_from_filename(fn), exp, fn)

    def test_pauses_and_totals(self):
        p = Project(self.cfg)
        files = [make(self.d, "A%02d.wav" % i, 60) for i in range(1, 5)]
        p.add_files("A", files)
        side = p.side("A")
        self.assertEqual(len(p.gaps(side)), 3)
        self.assertAlmostEqual(p.side_total(side), 240 + 3 * 2.0)
        side.tracks[1].pause_after = 5.0
        self.assertAlmostEqual(p.side_total(side), 240 + 2 + 5 + 2)
        side.tracks[3].pause_after = 9.0   # l'últim no compta
        self.assertAlmostEqual(p.side_total(side), 240 + 2 + 5 + 2)
        p.pause_global = 3.0
        self.assertAlmostEqual(p.side_total(side), 240 + 3 + 5 + 3)
        p.pause_enabled = False
        self.assertAlmostEqual(p.side_total(side), 240)
        p.pause_enabled = True
        p.reset_pauses()
        self.assertAlmostEqual(p.side_total(side), 240 + 9)

    def test_status_and_over(self):
        p = Project(self.cfg)  # 12" 33: 18-22 min
        p.add_files("A", [make(self.d, "a.wav", 17 * 60)])
        self.assertEqual(p.side_status(p.side("A")), "green")
        p.add_files("A", [make(self.d, "b.wav", 3 * 60)])
        self.assertEqual(p.side_status(p.side("A")), "yellow")
        p.add_files("A", [make(self.d, "c.wav", 3 * 60)])
        self.assertEqual(p.side_status(p.side("A")), "red")
        codes = [w.code for w in p.warnings()]
        self.assertIn("w_side_over", codes)
        p.disc, p.rpm = "7", "45"
        self.assertEqual(p.side_status(p.side("B")), "empty")

    def test_warnings(self):
        p = Project(self.cfg)
        st = dict(rate=44100, ch=2, bits=16)
        a = make(self.d, "A1.wav", 1, **st)
        p.add_files("A", [a, make(self.d, "A2.wav", 1, rate=44100, ch=2, bits=32, tag=3),
                          make(self.d, "A3.wav", 1, rate=48000, ch=2, bits=16),
                          make(self.d, "A4.wav", 1, rate=44100, ch=1, bits=16),
                          make(self.d, "A5.wav", 1, rate=22050, ch=2, bits=16)])
        p.add_files("B", [a])
        bad = os.path.join(self.d, "B2.wav")
        with open(bad, "wb") as f:
            f.write(b"not a wav at all")
        p.add_files("B", [bad])
        codes = sorted(set(w.code for w in p.warnings()))
        for c in ("w_float", "w_mixed_rates", "w_mono", "w_odd_rate", "w_duplicate", "w_unreadable",
                  "w_mixed_bits"):
            self.assertIn(c, codes)
        for lang in ("ca", "es", "en"):
            for w in p.warnings(lang):
                self.assertTrue(w.text(lang))

    def test_move(self):
        p = Project(self.cfg)
        p.add_files("A", [make(self.d, "A%d.wav" % i, 5) for i in range(1, 4)])
        ids = [t.id for t in p.side("A").tracks]
        p.move(ids[0], "A", 3)
        self.assertEqual([t.id for t in p.side("A").tracks], [ids[1], ids[2], ids[0]])
        p.move(ids[2], "B", 0)
        self.assertEqual([t.id for t in p.side("B").tracks], [ids[2]])
        p.to_other_side(ids[2])
        self.assertEqual(p.side("A").tracks[-1].id, ids[2])
        p.shift(ids[2], -1)
        self.assertEqual(p.side("A").tracks[-2].id, ids[2])

    def test_save_load_and_relocate(self):
        p = Project(self.cfg)
        p.artist, p.album = "Artista", "Disc"
        p.add_files("A", [make(self.d, "A1.wav", 100), make(self.d, "A2.wav", 50)])
        p.side("A").tracks[0].pause_after = 4.5
        p.side("A").tracks[0].title = "Títol editat"
        proj = os.path.join(self.d, "disc.vtracklist")
        p.save(proj)
        # Simular un altre ordinador: moure tota la carpeta
        d2 = self.d + "_moved"
        shutil.move(self.d, d2)
        try:
            q = Project.load(os.path.join(d2, "disc.vtracklist"), self.cfg)
            self.assertEqual(q.artist, "Artista")
            t = q.side("A").tracks[0]
            self.assertEqual(t.title, "Títol editat")
            self.assertEqual(t.pause_after, 4.5)
            self.assertTrue(t.info.ok, "relpath no resolt")
        finally:
            shutil.move(d2, self.d)

    def test_exports(self):
        p = Project(self.cfg)
        p.artist, p.album, p.catalog = "Artista «prova»", "Disc & <coses>", "IND-001"
        p.add_files("A", [make(self.d, "A1 - Cançó amb l·l i ñ.wav", 20, rate=44100, ch=2, bits=24),
                          make(self.d, "A2.wav", 10, rate=44100, ch=2, bits=24)])
        p.add_files("B", [make(self.d, "B1.wav", 10, rate=44100, ch=2, bits=32, tag=3)])
        p.side("A").tracks[0].pause_after = 3.0
        for kind in ("own", "factory"):
            if True:
                rep = build_report(p, kind)
                base = os.path.join(self.d, "out_%s" % kind)
                write_txt(rep, base + ".txt")
                write_docx(rep, base + ".docx")
                write_pdf(rep, base + ".pdf")
                with open(base + ".txt", "rb") as f:
                    raw = f.read()
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
                self.assertIn(b"\r\n", raw)
                self.assertNotIn(b"\n\n", raw.replace(b"\r\n", b"X"))
                with zipfile.ZipFile(base + ".docx") as z:
                    self.assertIn("word/document.xml", z.namelist())
                with open(base + ".pdf", "rb") as f:
                    pdf = f.read()
                self.assertTrue(pdf.startswith(b"%PDF-1.4"))
                self.assertTrue(pdf.rstrip().endswith(b"%%EOF"))

    def test_factory_vs_own(self):
        p = Project(self.cfg)
        p.artist = "Artista"
        p.add_files("A", [make(self.d, "A1.wav", 22 * 60, rate=44100, ch=2, bits=32, tag=3)])  # float i massa llarg
        p.add_files("B", [make(self.d, "B1.wav", 60), make(self.d, "B2.wav", 60)])
        p.side("B").tracks[0].pause_after = 4.0
        own = os.path.join(self.d, "own.txt")
        fac = os.path.join(self.d, "fac.txt")
        write_txt(build_report(p, "own"), own)
        write_txt(build_report(p, "factory"), fac)
        with open(own, encoding="utf-8-sig") as fh:
            o = fh.read()
        with open(fac, encoding="utf-8-sig") as fh:
            f = fh.read()
        for s in ("CARA A", "Recomendado", "AVISOS", "Duración", "coma flotante", "* pausa personalizada"):
            self.assertIn(s, o)
        for s in ("SIDE A", "Duration", "Gap", "Side B total", "Date:", "floating point", "Gaps between tracks: as listed"):
            self.assertIn(s, f)
        for s in ("Recommended", "WARNING", "(!)", "EXCEEDS", "*"):
            self.assertNotIn(s, f)

    def test_sort_whole_side(self):
        p = Project(self.cfg)
        p.add_files("A", [make(self.d, n, 5) for n in ("B10.wav", "b2.wav", "Àlex.wav", "a1.wav")])
        names = lambda: [os.path.basename(t.path) for t in p.side("A").tracks]  # noqa: E731
        self.assertEqual(names(), ["a1.wav", "Àlex.wav", "b2.wav", "B10.wav"])
        p.shift(p.side("A").tracks[0].id, 1)          # ordre manual...
        p.add_files("A", [make(self.d, "a0.wav", 5)])  # ...afegir reordena la cara sencera
        self.assertEqual(names(), ["a0.wav", "a1.wav", "Àlex.wav", "b2.wav", "B10.wav"])

    def test_fmt_dur(self):
        self.assertEqual(fmt_dur(59.4), "0:59")
        self.assertEqual(fmt_dur(59.6), "1:00")
        self.assertEqual(fmt_dur(3725), "1:02:05")


if __name__ == "__main__":
    unittest.main()
