# -*- coding: utf-8 -*-
"""Panell informatiu de temps recomanats per cara."""
import tkinter as tk

from ..config import DISCS, RPMS
from ..model import fmt_minutes
from . import theme as th

DISC_CM = {"7": "17,8 cm", "10": "25,4 cm", "12": "30,5 cm"}


class InfoPanel(tk.Frame):
    def __init__(self, master, tab):
        tk.Frame.__init__(self, master, bg=th.PANEL, highlightthickness=1, highlightbackground=th.BORDER)
        self.tab = tab
        head = tk.Frame(self, bg=th.NAVY)
        head.pack(fill="x")
        tk.Label(head, text="TEMPS RECOMANAT PER CARA", bg=th.NAVY, fg=th.WHITE,
                 font=th.FONTS["bold"], padx=10, pady=8).pack(side="left")

        self.grid_frame = tk.Frame(self, bg=th.PANEL)
        self.grid_frame.pack(fill="x", padx=10, pady=(10, 4))
        self.cells = {}
        hdrs = ["Mida", "33 1/3 rpm", "45 rpm"]
        for c, txt in enumerate(hdrs):
            tk.Label(self.grid_frame, text=txt, bg=th.PANEL, fg=th.MUTED,
                     font=th.FONTS["bold"]).grid(row=0, column=c, padx=2, pady=(0, 4), sticky="ew")
        for r, disc in enumerate(DISCS, start=1):
            tk.Label(self.grid_frame, text='%s"\n%s' % (disc, DISC_CM[disc]), bg=th.PANEL, fg=th.TEXT,
                     font=th.FONTS["small"], justify="center").grid(row=r, column=0, padx=2, pady=2, sticky="nsew")
            for c, rpm in enumerate(RPMS, start=1):
                lbl = tk.Label(self.grid_frame, text="", bg=th.CARD, fg=th.TEXT, font=th.FONTS["bold"],
                               relief="solid", borderwidth=1, padx=6, pady=6, cursor="hand2")
                lbl.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                lbl.bind("<Button-1>", lambda e, d=disc, rp=rpm: tab.set_format(d, rp))
                self.cells[(disc, rpm)] = lbl
        for c in range(3):
            self.grid_frame.grid_columnconfigure(c, weight=1)
        tk.Label(self, text="Clica una casella per triar el format.", bg=th.PANEL, fg=th.MUTED,
                 font=th.FONTS["small"]).pack(anchor="w", padx=10)

        leg = tk.Frame(self, bg=th.PANEL)
        leg.pack(fill="x", padx=10, pady=(10, 4))
        for color, txt in ((th.GREEN, "Fins al mínim: marge còmode"),
                           (th.YELLOW, "Dins del rang recomanat"),
                           (th.RED, "Supera el màxim recomanat")):
            row = tk.Frame(leg, bg=th.PANEL)
            row.pack(anchor="w", pady=1)
            tk.Frame(row, bg=color, width=12, height=12).pack(side="left", padx=(2, 0))
            tk.Label(row, text=txt, fg=th.TEXT, bg=th.PANEL, font=th.FONTS["small"]).pack(side="left", padx=4)

        notes = (
            "• Com més minuts per cara, més junts han d'anar els solcs.",
            "• Molt greu i molt volum necessiten més espai i redueixen el temps disponible.",
            "• El final de cada cara (diàmetre interior) és la zona més delicada.",
            "• Valors típics de la indústria. Els màxims teòrics poden ser una mica superiors, "
            "amb compromís de qualitat. Es poden editar a Eines › Configuració.",
        )
        self.notes = tk.Label(self, text="\n".join(notes), bg=th.PANEL, fg=th.TEXT,
                              font=th.FONTS["small"], justify="left", anchor="nw", wraplength=240)
        self.notes.pack(fill="x", padx=10, pady=(8, 10))
        self.bind("<Configure>", lambda e: self.notes.configure(wraplength=max(120, e.width - 24)))

    def refresh(self):
        project = self.tab.project
        ranges = self.tab.cfg["ranges"]
        for (disc, rpm), lbl in self.cells.items():
            lo, hi = ranges[disc][rpm]
            lbl.configure(text="%s–%s min" % (fmt_minutes("ca", lo), fmt_minutes("ca", hi)))
            sel = disc == project.disc and rpm == project.rpm
            lbl.configure(bg=th.NAVY if sel else th.CARD, fg=th.WHITE if sel else th.TEXT)
