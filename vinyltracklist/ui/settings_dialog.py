# -*- coding: utf-8 -*-
"""Diàleg de configuració: temps recomanats i regles d'avís."""
import copy
import tkinter as tk
from tkinter import ttk, messagebox

from .. import i18n
from ..config import DISCS, RPMS, DEFAULT_RANGES
from ..model import parse_number
from . import theme as th


class SettingsDialog(tk.Toplevel):
    def __init__(self, app):
        tk.Toplevel.__init__(self, app.root)
        self.app = app
        self.title("Configuració")
        self.configure(bg=th.BG)
        self.resizable(False, False)
        self.transient(app.root)
        self.result = False

        frm = tk.Frame(self, bg=th.BG)
        frm.pack(padx=16, pady=14, fill="both")

        tk.Label(frm, text="Temps recomanat per cara (minuts)", bg=th.BG, fg=th.NAVY,
                 font=th.FONTS["bold"]).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 6))
        tk.Label(frm, text="", bg=th.BG).grid(row=1, column=0)
        for c, rpm in enumerate(RPMS):
            tk.Label(frm, text="%s rpm (mín – màx)" % i18n.fmt_rpm(rpm), bg=th.BG, fg=th.TEXT,
                     font=th.FONTS["bold"]).grid(row=1, column=1 + c * 2, columnspan=2, padx=8)
        self.vars = {}
        for r, disc in enumerate(DISCS, start=2):
            tk.Label(frm, text='%s"' % disc, bg=th.BG, fg=th.TEXT, font=th.FONTS["bold"]).grid(
                row=r, column=0, sticky="e", padx=(0, 6), pady=3)
            for c, rpm in enumerate(RPMS):
                lo, hi = app.cfg["ranges"][disc][rpm]
                for k, val in enumerate((lo, hi)):
                    var = tk.StringVar(value=i18n.decimal("ca", val, 1).replace(",0", ""))
                    ttk.Entry(frm, textvariable=var, width=6, justify="right").grid(
                        row=r, column=1 + c * 2 + k, padx=4, pady=3)
                    self.vars[(disc, rpm, k)] = var

        ttk.Separator(frm).grid(row=6, column=0, columnspan=5, sticky="ew", pady=12)
        self.var_float = tk.BooleanVar(value=app.cfg.get("float_not_ok", True))
        ttk.Checkbutton(frm, text="Considerar el WAV en coma flotant com a error (no apte per a fàbrica)",
                        variable=self.var_float).grid(row=7, column=0, columnspan=5, sticky="w")
        tk.Label(frm, text="Els valors per defecte són els de la taula de referència.\n"
                           "Es desen en aquest ordinador i s'apliquen a tots els projectes.",
                 bg=th.BG, fg=th.MUTED, font=th.FONTS["small"], justify="left").grid(
            row=8, column=0, columnspan=5, sticky="w", pady=(10, 0))

        btns = tk.Frame(self, bg=th.BG)
        btns.pack(fill="x", padx=16, pady=(0, 14))
        ttk.Button(btns, text="Restablir valors per defecte", command=self.defaults).pack(side="left")
        ttk.Button(btns, text="Cancel·lar", command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Desar", command=self.save).pack(side="right", padx=6)
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()
        self.focus_set()

    def defaults(self):
        for disc in DISCS:
            for rpm in RPMS:
                lo, hi = DEFAULT_RANGES[disc][rpm]
                self.vars[(disc, rpm, 0)].set(str(lo))
                self.vars[(disc, rpm, 1)].set(str(hi))
        self.var_float.set(True)

    def save(self):
        ranges = copy.deepcopy(self.app.cfg["ranges"])
        for disc in DISCS:
            for rpm in RPMS:
                lo = parse_number(self.vars[(disc, rpm, 0)].get())
                hi = parse_number(self.vars[(disc, rpm, 1)].get())
                if lo is None or hi is None or lo <= 0 or hi < lo or hi > 60:
                    messagebox.showerror("Configuració", 'Valors no vàlids per a %s" a %s rpm.\n'
                                         "El mínim ha de ser més gran que 0 i no superar el màxim."
                                         % (disc, i18n.fmt_rpm(rpm)), parent=self)
                    return
                ranges[disc][rpm] = [lo, hi]
        self.app.cfg["ranges"] = ranges
        self.app.cfg["float_not_ok"] = bool(self.var_float.get())
        self.app.save_cfg()
        self.result = True
        self.destroy()
