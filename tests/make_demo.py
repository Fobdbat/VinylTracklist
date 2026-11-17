# -*- coding: utf-8 -*-
"""Crea un disc de prova a tests/demo/ (fitxers sparse: no ocupen disc)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wavgen import write_wav  # noqa: E402

DEMO = os.path.join(HERE, "demo")

A = [("A01_La_nit_de_Sant_Joan.wav", 252), ("A02 - Carrer de la Pau.wav", 263),
     ("A03_Ones_del_Mediterrani.wav", 236), ("A04_Cami_de_Ronda.wav", 230),
     ("A05_Llum_de_tardor.wav", 223), ("A06_Final_de_festa.wav", 321)]
B = [("B01_Vent_de_Mestral.wav", 191, {}), ("B02_Ball_de_mitjanit.wav", 191, {}),
     ("B03_Sota_la_pluja.wav", 266, {"bits": 32, "tag": 3}),            # coma flotant
     ("B04_Cancons_de_bressol.wav", 214, {"rate": 48000, "bits": 24}),  # 48 kHz
     ("B05_Lluna_plena.wav", 340, {}), ("B06_Tornada.wav", 66, {})]


def main():
    if not os.path.isdir(DEMO):
        os.makedirs(DEMO)
    for name, sec in A:
        write_wav(os.path.join(DEMO, name), 44100, 2, 24, 1, seconds=sec, extensible=True)
    for name, sec, kw in B:
        write_wav(os.path.join(DEMO, name), kw.get("rate", 44100), 2, kw.get("bits", 24),
                  kw.get("tag", 1), seconds=sec, extensible=kw.get("tag", 1) == 1)
    sys.path.insert(0, os.path.dirname(HERE))
    from vinyltracklist import config
    from vinyltracklist.model import Project
    p = Project(config.load_config())
    p.artist, p.album, p.catalog = "Marina Soler", "Cançons de la Mediterrània", "IND-2026-014"
    p.add_files("A", [os.path.join(DEMO, n) for n, _ in A])
    p.add_files("B", [os.path.join(DEMO, n) for n, _, _ in B])
    p.side("A").tracks[2].pause_after = 3.5
    p.save(os.path.join(DEMO, "Demo.vtracklist"))
    print("Demo a", DEMO)


if __name__ == "__main__":
    main()
