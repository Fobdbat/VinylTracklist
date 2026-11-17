# -*- coding: utf-8 -*-
"""Prova de la interfície amb esdeveniments reals (s'executa amb xvfb-run)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import tkinter as tk  # noqa: E402
from vinyltracklist.ui import dnd  # noqa: E402
from vinyltracklist.ui.app import App  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/out"
results = []


def shot(name):
    subprocess.call(["import", "-window", "root", os.path.join(OUT, name)])


def check(cond, msg):
    results.append((bool(cond), msg))


root = tk.Tk()
root.geometry("+0+0")
dnd_ok = dnd.load(root)
app = App(root)
root.geometry("1320x860+0+0")
tab = app.tracklist


def step1():
    app.open_project(os.path.join(HERE, "demo", "Demo.vtracklist"))
    # Afegir de nou un fitxer: la cara s'ha de reordenar sencera
    app.project.shift(app.project.side("A").tracks[0].id, 2)
    tab.add_paths("A", [os.path.join(HERE, "demo", "A01_La_nit_de_Sant_Joan.wav")])
    root.update()
    names = [os.path.basename(t.path)[:3] for t in app.project.side("A").tracks]
    check(names == ["A01", "A01", "A02", "A03", "A04", "A05", "A06"], "afegir reordena la cara: %s" % names)
    app.project.remove(app.project.side("A").tracks[0].id)
    tab.refresh_all()
    root.update()
    check(len(tab.panels["A"].cards) == 6 and len(tab.panels["B"].cards) == 6, "12 temes carregats a les cares")
    tid = app.project.side("B").tracks[1].id
    tab.select(tid)
    root.after(400, step2)


def step2():
    shot("gui_1_loaded.png")
    # Arrossegar A6 (Final de festa) a la cara B, entre B1 i B2
    src_id = app.project.side("A").tracks[5].id
    card = tab.panels["A"].card_widget(src_id)
    target = tab.panels["B"].cards[1][1]
    x0, y0 = card.winfo_rootx() + 60, card.winfo_rooty() + 10
    x1, y1 = target.winfo_rootx() + 60, target.winfo_rooty() + 4
    card.event_generate("<ButtonPress-1>", x=60, y=10, rootx=x0, rooty=y0)
    for k in range(1, 11):
        xi = x0 + (x1 - x0) * k // 10
        yi = y0 + (y1 - y0) * k // 10
        card.event_generate("<B1-Motion>", x=60, y=10, rootx=xi, rooty=yi)
    root.update()
    shot("gui_2_dragging.png")
    card.event_generate("<ButtonRelease-1>", x=60, y=10, rootx=x1, rooty=y1)
    root.after(300, step3)


def step3():
    a = [t.title for t in app.project.side("A").tracks]
    b = [t.title for t in app.project.side("B").tracks]
    check(len(a) == 5 and b[1] == "Final de festa", "arrossegar A6 entre B1 i B2 -> %s" % b[:3])
    # Pausa personalitzada a la cara A (gap 1) via el Spinbox
    g = tab.panels["A"].gap_rows[0]
    g.var.set("4,5")
    g.commit()
    check(app.project.side("A").tracks[0].pause_after == 4.5, "pausa pròpia 4,5 s a A1")
    # Pausa global 3 s
    tab.var_pause.set("3,0")
    tab._on_global_pause()
    root.update()
    p = app.project
    check(p.pause_value(p.side("A").tracks[1]) == 3.0 and p.side("A").tracks[0].pause_after == 4.5,
          "global 3 s respecta la pròpia")
    # Canviar format clicant la taula d'informació
    tab.info.cells[("12", "45")].event_generate("<Button-1>")
    root.update()
    check((p.disc, p.rpm) == ("12", "45"), "format 12\" 45 rpm des de la taula")
    tab.info.cells[("12", "33")].event_generate("<Button-1>")
    root.update()
    root.after(400, step4)


def step4():
    shot("gui_3_after.png")
    # Desmarcar pauses
    tab.var_pause_on.set(False)
    tab._on_pause_toggle()
    root.update()
    check(len(tab.panels["A"].gap_rows) == 0, "sense pauses: no hi ha files de pausa")
    tab.var_pause_on.set(True)
    tab._on_pause_toggle()
    root.update()
    # Botons ▲ ▼ i treure
    first = app.project.side("B").tracks[0].id
    tab.select(first)
    tab.shift_selected(1)
    root.update()
    check(app.project.side("B").tracks[1].id == first, "botó ▼")
    tab.remove_selected()
    root.update()
    check(len(app.project.side("B").tracks) == 6, "treure tema")
    app.notebook.select(1)
    root.update()
    root.after(400, step5)


def step5():
    shot("gui_4_report_own.png")
    check(len(app.report.cv.find_all()) > 50, "vista prèvia de l'informe dibuixada")
    app.var_report_kind.set("factory")
    app.on_report_kind()
    root.after(400, step6)


def step6():
    shot("gui_5_report_factory.png")
    app.notebook.select(0)
    app.dirty = False
    check(True, "tkdnd carregat: %s" % dnd_ok)
    root.after(100, root.destroy)


root.after(300, step1)
root.mainloop()
for ok, msg in results:
    print(("OK   " if ok else "FAIL ") + msg)
sys.exit(0 if all(ok for ok, _ in results) else 1)
