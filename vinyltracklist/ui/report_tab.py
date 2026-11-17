# -*- coding: utf-8 -*-
"""Pestanya Informe: vista prèvia a pantalla, amb el mateix disseny que el PDF."""
import sys
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

from ..export import build_report, layout
from ..export.pdf import PAGE_W, PAGE_H
from . import theme as th

CANVAS_BG = "#d9dee5"


def _hex(c):
    return "#%02x%02x%02x" % tuple(int(round(v * 255)) for v in c)


class TkPainter(object):
    """Mateixa interfície que el llenç PDF, però dibuixant en un tk.Canvas."""

    def __init__(self, canvas, scale, x0, gap):
        self.cv = canvas
        self.s = scale
        self.x0 = x0
        self.gap = gap
        self.index = -1
        self.oy = 0
        self.fonts = {}
        if sys.platform == "win32":
            self.family = "Arial"
        else:
            fams = set(tkfont.families(canvas))
            self.family = next((f for f in ("Liberation Sans", "Arimo", "DejaVu Sans", "Helvetica") if f in fams),
                               "Helvetica")

    def _x(self, x):
        return self.x0 + x * self.s

    def _y(self, y):
        return self.oy + (PAGE_H - y) * self.s

    def _font(self, size, bold):
        px = max(6, int(round(size * self.s)))
        key = (px, bold)
        if key not in self.fonts:
            self.fonts[key] = tkfont.Font(self.cv, family=self.family, size=-px,
                                          weight="bold" if bold else "normal")
        return self.fonts[key]

    def new_page(self):
        self.index += 1
        self.oy = self.gap + self.index * (PAGE_H * self.s + self.gap)
        w, h = PAGE_W * self.s, PAGE_H * self.s
        self.cv.create_rectangle(self.x0 + 4, self.oy + 4, self.x0 + w + 4, self.oy + h + 4,
                                 fill="#b8c0ca", width=0)
        self.cv.create_rectangle(self.x0, self.oy, self.x0 + w, self.oy + h, fill="white", outline="#aab3be")

    def text(self, x, y, s, size=10, bold=False, color=(0, 0, 0), align="left"):
        f = self._font(size, bold)
        anchor = {"left": "nw", "right": "ne", "center": "n"}[align]
        self.cv.create_text(self._x(x), self._y(y) - f.metrics("ascent"), text=s, font=f,
                            fill=_hex(color), anchor=anchor)

    def rect(self, x, y, w, h, fill):
        self.cv.create_rectangle(self._x(x), self._y(y + h), self._x(x + w), self._y(y),
                                 fill=_hex(fill), width=0)

    def line(self, x1, y1, x2, y2, color=(0.8, 0.8, 0.8), width=0.6):
        self.cv.create_line(self._x(x1), self._y(y1), self._x(x2), self._y(y2),
                            fill=_hex(color), width=max(1, int(round(width * self.s))))


class ReportTab(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=th.BG)
        self.app = app
        self._job = None
        self._last_w = 0

        from .tracklist_tab import build_report_selector, build_export_buttons
        top = tk.Frame(self, bg=th.BG)
        top.pack(fill="x", padx=10, pady=8)
        build_report_selector(top, app)
        build_export_buttons(top, app)

        body = tk.Frame(self, bg=CANVAS_BG)
        body.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.cv = tk.Canvas(body, bg=CANVAS_BG, highlightthickness=0)
        self.vbar = ttk.Scrollbar(body, orient="vertical", command=self.cv.yview)
        self.cv.configure(yscrollcommand=self.vbar.set)
        self.cv.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="left", fill="y")
        self.cv.bind("<Configure>", self._on_resize)
        self.cv.bind("<Enter>", self._bind_wheel)
        self.cv.bind("<Leave>", self._unbind_wheel)

    def _on_resize(self, e):
        if abs(e.width - self._last_w) > 4:
            self._last_w = e.width
            self.refresh(keep_scroll=True)

    def _bind_wheel(self, _e=None):
        if sys.platform.startswith("linux"):
            self.cv.bind_all("<Button-4>", lambda e: self.cv.yview_scroll(-2, "units"))
            self.cv.bind_all("<Button-5>", lambda e: self.cv.yview_scroll(2, "units"))
        else:
            self.cv.bind_all("<MouseWheel>", lambda e: self.cv.yview_scroll(-2 if e.delta > 0 else 2, "units"))

    def _unbind_wheel(self, _e=None):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.cv.unbind_all(seq)

    def refresh(self, keep_scroll=False):
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(60, lambda: self.render(keep_scroll))

    def render(self, keep_scroll=False):
        self._job = None
        cv = self.cv
        top = cv.yview()[0] if keep_scroll else 0.0
        cv.delete("all")
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w < 50:
            return
        project = self.app.project
        if project.is_empty():
            cv.create_text(w / 2, h / 3, text="Carrega els WAV a la pestanya Tracklist per veure l'informe.",
                           font=th.FONTS["title"], fill=th.MUTED)
            cv.configure(scrollregion=(0, 0, w, h))
            return
        page_w = min(860, max(460, w - 60))
        scale = page_w / PAGE_W
        gap = 20
        painter = TkPainter(cv, scale, (w - page_w) / 2.0, gap)
        pages = layout(build_report(project, self.app.var_report_kind.get()), painter)
        total_h = gap + pages * (PAGE_H * scale + gap)
        cv.configure(scrollregion=(0, 0, w, total_h))
        cv.yview_moveto(top)
