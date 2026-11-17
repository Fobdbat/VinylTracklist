# -*- coding: utf-8 -*-
import sys
import tkinter as tk
from tkinter import ttk


class ScrollFrame(tk.Frame):
    """Frame amb barra de desplaçament vertical i roda del ratolí."""

    def __init__(self, master, bg, **kw):
        tk.Frame.__init__(self, master, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, borderwidth=0)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", self._bind_wheel)
        self.canvas.bind("<Leave>", self._unbind_wheel)

    def _on_inner(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def _bind_wheel(self, _e=None):
        if sys.platform.startswith("linux"):
            self.canvas.bind_all("<Button-4>", lambda e: self.scroll(-1))
            self.canvas.bind_all("<Button-5>", lambda e: self.scroll(1))
        else:
            self.canvas.bind_all("<MouseWheel>", self._on_wheel)

    def _unbind_wheel(self, _e=None):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.canvas.unbind_all(seq)

    def _on_wheel(self, e):
        step = -1 if e.delta > 0 else 1
        self.scroll(step * max(1, abs(e.delta) // 120))

    def scroll(self, units):
        top, bottom = self.canvas.yview()
        if top <= 0 and bottom >= 1:
            return
        self.canvas.yview_scroll(units, "units")

    def see(self, widget):
        """Desplaça la vista perquè 'widget' sigui visible."""
        self.update_idletasks()
        total = max(1, self.inner.winfo_height())
        y = widget.winfo_y()
        h = widget.winfo_height()
        top, bottom = self.canvas.yview()
        view_top = top * total
        view_bottom = bottom * total
        if y < view_top:
            self.canvas.yview_moveto(y / float(total))
        elif y + h > view_bottom:
            self.canvas.yview_moveto((y + h - (view_bottom - view_top)) / float(total))
