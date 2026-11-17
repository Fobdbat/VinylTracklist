# -*- coding: utf-8 -*-
"""Panell d'una cara del vinil: llista de temes, pauses i temps total."""
import tkinter as tk
from tkinter import ttk

from .. import i18n
from ..model import fmt_dur, fmt_minutes, parse_number, clamp_pause
from . import dnd
from . import theme as th
from .scrollframe import ScrollFrame

PAUSE_VALUES = tuple(i18n.decimal("ca", i * 0.5, 1) for i in range(0, 61))

STATUS_TEXT = {
    "empty": "Cara buida",
    "green": "Marge còmode",
    "yellow": "Dins del rang recomanat",
    "red": "SUPERA el màxim recomanat",
}


class GapRow(object):
    """Fila de pausa entre dos temes, editable."""

    def __init__(self, panel, parent, track):
        self.panel = panel
        self.track = track
        tab = panel.tab
        self.frame = tk.Frame(parent, bg=th.PANEL)
        box = tk.Frame(self.frame, bg=th.PANEL)
        box.pack(anchor="center", pady=1)
        self.lbl = tk.Label(box, text="pausa", bg=th.PANEL, fg=th.MUTED, font=th.FONTS["small"])
        self.lbl.pack(side="left")
        self.var = tk.StringVar()
        self.spin = tk.Spinbox(box, values=PAUSE_VALUES, width=5, justify="right",
                               textvariable=self.var, font=th.FONTS["small"],
                               command=self.commit, relief="solid", borderwidth=1)
        self.spin.pack(side="left", padx=(4, 2))
        self.var.set(i18n.decimal("ca", tab.project.pause_value(track), 1))
        tk.Label(box, text="s", bg=th.PANEL, fg=th.MUTED, font=th.FONTS["small"]).pack(side="left")
        self.reset_btn = tk.Button(box, text="restablir", relief="flat", bg=th.PANEL, fg=th.ACCENT,
                                   activebackground=th.GAP_BG, borderwidth=0, cursor="hand2",
                                   font=th.FONTS["small"], command=self.reset)
        self.spin.bind("<Return>", lambda e: self.commit())
        self.spin.bind("<KP_Enter>", lambda e: self.commit())
        self.spin.bind("<FocusOut>", lambda e: self.commit())
        self.style()

    def style(self):
        custom = self.track.pause_after is not None
        self.spin.configure(fg=th.ACCENT if custom else th.TEXT,
                            font=th.FONTS["bold"] if custom else th.FONTS["small"])
        if custom:
            self.reset_btn.pack(side="left", padx=(4, 0))
            self.lbl.configure(text="pausa pròpia")
        else:
            self.reset_btn.pack_forget()
            self.lbl.configure(text="pausa")

    def commit(self):
        tab = self.panel.tab
        v = parse_number(self.var.get())
        current = tab.project.pause_value(self.track)
        if v is None:
            self.var.set(i18n.decimal("ca", current, 1))
            return
        v = clamp_pause(v)
        self.var.set(i18n.decimal("ca", v, 1))
        if abs(v - current) < 1e-9 and self.track.pause_after is None:
            return
        if self.track.pause_after is not None and abs(v - self.track.pause_after) < 1e-9:
            return
        self.track.pause_after = v
        self.style()
        tab.on_pause_changed()

    def reset(self):
        self.track.pause_after = None
        self.var.set(i18n.decimal("ca", self.panel.tab.project.pause_global, 1))
        self.style()
        self.panel.tab.on_pause_changed()


class SidePanel(tk.Frame):
    def __init__(self, master, tab, side_name):
        tk.Frame.__init__(self, master, bg=th.PANEL, highlightthickness=1,
                          highlightbackground=th.BORDER)
        self.tab = tab
        self.side_name = side_name
        self.cards = []          # [(track_id, frame)]
        self.title_labels = []   # [(label, full_text)]
        self.gap_rows = []
        self._styles = {}
        self._last_width = 0

        # Capçalera
        head = tk.Frame(self, bg=th.NAVY)
        head.pack(fill="x")
        tk.Label(head, text="CARA %s" % side_name, bg=th.NAVY, fg=th.WHITE,
                 font=th.FONTS["side"], padx=10, pady=6).pack(side="left")
        self.status_dot = tk.Label(head, text="●", bg=th.NAVY, fg=th.STATUS_COLORS["empty"],
                                   font=th.FONTS["side"])
        self.status_dot.pack(side="right", padx=(0, 10))
        self.total_lbl = tk.Label(head, text="0:00", bg=th.NAVY, fg=th.WHITE,
                                  font=th.FONTS["big"], padx=4)
        self.total_lbl.pack(side="right")

        # Barra d'eines
        bar = tk.Frame(self, bg=th.PANEL)
        bar.pack(fill="x", padx=6, pady=(6, 2))
        ttk.Button(bar, text="+ Afegir WAV…", command=lambda: tab.add_files_dialog(side_name)).pack(side="left")
        self.btn_up = ttk.Button(bar, text="▲", width=3, command=lambda: tab.shift_selected(-1))
        self.btn_down = ttk.Button(bar, text="▼", width=3, command=lambda: tab.shift_selected(1))
        other = "B" if side_name == "A" else "A"
        arrow = "→" if side_name == "A" else "←"
        self.btn_move = ttk.Button(bar, text="%s Cara %s" % (arrow, other),
                                   command=tab.move_selected_other)
        self.btn_del = ttk.Button(bar, text="Treure", command=tab.remove_selected)
        self.btn_del.pack(side="right")
        self.btn_move.pack(side="right", padx=(0, 4))
        self.btn_down.pack(side="right", padx=(0, 4))
        self.btn_up.pack(side="right", padx=(0, 2))

        # Llista
        self.list = ScrollFrame(self, bg=th.PANEL)
        self.list.pack(fill="both", expand=True, padx=(6, 2), pady=2)
        self.list.inner.bind("<Configure>", self._on_resize, add="+")
        self.indicator = tk.Frame(self.list.inner, bg=th.ACCENT, height=3)

        # Peu: barra de temps i resum
        foot = tk.Frame(self, bg=th.PANEL)
        foot.pack(fill="x", padx=8, pady=(4, 8))
        self.bar = tk.Canvas(foot, height=20, bg=th.PANEL, highlightthickness=0)
        self.bar.pack(fill="x")
        self.bar.bind("<Configure>", lambda e: self.draw_bar())
        self.sum_lbl = tk.Label(foot, text="", bg=th.PANEL, fg=th.TEXT, font=th.FONTS["normal"], anchor="w")
        self.sum_lbl.pack(fill="x", pady=(3, 0))
        self.status_lbl = tk.Label(foot, text="", bg=th.PANEL, fg=th.MUTED, font=th.FONTS["bold"], anchor="w")
        self.status_lbl.pack(fill="x")

        for w in (self.list.canvas, self.list.inner):
            dnd.register_files_drop(w, self._on_files_dropped)

    # ------------------------------------------------------------------
    @property
    def side(self):
        return self.tab.project.side(self.side_name)

    def _on_files_dropped(self, paths, _y_root=None):
        self.tab.add_paths(self.side_name, paths)

    def rebuild(self):
        for child in self.list.inner.winfo_children():
            if child is not self.indicator:
                child.destroy()
        self.cards = []
        self.title_labels = []
        self.gap_rows = []
        self._styles = {}
        project = self.tab.project
        side = self.side
        if not side.tracks:
            msg = "Arrossega aquí els WAV de la cara %s\no fes clic a «Afegir WAV…»" % self.side_name
            if not dnd.AVAILABLE:
                msg = "Fes clic a «Afegir WAV…» per carregar\nels WAV de la cara %s" % self.side_name
            ph = tk.Label(self.list.inner, text=msg, bg=th.PANEL, fg=th.MUTED,
                          font=th.FONTS["normal"], pady=40, justify="center")
            ph.pack(fill="x")
            dnd.register_files_drop(ph, self._on_files_dropped)
        for i, t in enumerate(side.tracks):
            self._make_card(t, i)
            if i < len(side.tracks) - 1 and project.pause_enabled:
                g = GapRow(self, self.list.inner, t)
                g.frame.pack(fill="x")
                self.gap_rows.append(g)
            elif i < len(side.tracks) - 1:
                tk.Frame(self.list.inner, bg=th.PANEL, height=4).pack(fill="x")
        self.indicator.lift()
        self.update_summary()
        self.update_toolbar()
        self.after_idle(self._fit_titles)

    def _make_card(self, t, idx):
        tab = self.tab
        sev = t.severity(tab.cfg)
        selected = tab.selected_id == t.id
        bg = th.CARD_SEL if selected else th.CARD
        card = tk.Frame(self.list.inner, bg=bg, highlightthickness=1,
                        highlightbackground=th.ACCENT if selected else th.BORDER)
        card.pack(fill="x", pady=0)
        strip_color = th.SEVERITY_COLORS.get(sev) if sev else bg
        strip = tk.Frame(card, bg=strip_color, width=4)
        strip.grid(row=0, column=0, rowspan=2, sticky="ns")
        pos = tk.Label(card, text="%s%d" % (self.side_name, idx + 1), bg=bg, fg=th.NAVY,
                       font=th.FONTS["bold"], width=4, anchor="w")
        pos.grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(4, 0))
        title = tk.Label(card, text=t.title, bg=bg, fg=th.TEXT, font=th.FONTS["bold"], anchor="w", width=1)
        title.grid(row=0, column=2, sticky="ew", pady=(4, 0))
        dur = tk.Label(card, text=fmt_dur(t.duration) if t.info.ok else "--:--", bg=bg, fg=th.TEXT,
                       font=th.FONTS["bold"], anchor="e")
        dur.grid(row=0, column=3, sticky="e", padx=(6, 8), pady=(4, 0))
        tech_txt = t.tech_text("ca")
        if sev:
            tech_txt = "(!) " + tech_txt
        tech = tk.Label(card, text=tech_txt, bg=bg, fg=th.SEVERITY_COLORS.get(sev, th.MUTED),
                        font=th.FONTS["small"], anchor="w", width=1)
        tech.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(6, 8), pady=(0, 4))
        card.grid_columnconfigure(2, weight=1)
        self.title_labels.append((title, t.title, pos, dur))
        self.title_labels.append((tech, tech_txt, None, None))
        for w in (card, strip, pos, title, dur, tech):
            w.bind("<ButtonPress-1>", lambda e, tid=t.id: tab.drag.press(e, tid))
            w.bind("<B1-Motion>", tab.drag.motion)
            w.bind("<ButtonRelease-1>", tab.drag.release)
            w.bind("<Double-Button-1>", lambda e, tid=t.id: tab.rename(tid))
            w.bind("<Button-3>", lambda e, tid=t.id: tab.context_menu(e, tid))
            w.configure(cursor="hand2")
        self.cards.append((t.id, card))
        self._styles[t.id] = (card, (pos, title, dur, tech), strip, bool(sev))

    def restyle_selection(self):
        """Actualitza el ressaltat de selecció sense reconstruir la llista."""
        sel = self.tab.selected_id
        for tid, (card, labels, strip, has_sev) in self._styles.items():
            selected = tid == sel
            bg = th.CARD_SEL if selected else th.CARD
            try:
                card.configure(bg=bg, highlightbackground=th.ACCENT if selected else th.BORDER)
                for w in labels:
                    w.configure(bg=bg)
                if not has_sev:
                    strip.configure(bg=bg)
            except tk.TclError:
                pass
        self.update_toolbar()

    def _on_resize(self, e):
        if abs(e.width - self._last_width) > 2:
            self._last_width = e.width
            self.after_idle(self._fit_titles)

    def _fit_titles(self):
        try:
            width = self.list.inner.winfo_width()
        except tk.TclError:
            return
        for label, full, pos, dur in self.title_labels:
            try:
                if pos is not None:
                    avail = width - pos.winfo_reqwidth() - dur.winfo_reqwidth() - 30
                    font = th.FONTS["bold"]
                else:
                    avail = width - 30
                    font = th.FONTS["small"]
                label.configure(text=th.fit_text(font, full, avail))
            except tk.TclError:
                pass

    # ------------------------------------------------------------------
    def update_summary(self):
        project = self.tab.project
        side = self.side
        music = project.side_music(side)
        pauses = project.side_pauses(side)
        total = music + pauses
        status = project.side_status(side)
        lo, hi = project.range_minutes()
        self.total_lbl.configure(text=fmt_dur(total))
        self.status_dot.configure(fg=th.STATUS_COLORS[status])
        n = len(side.tracks)
        if project.pause_enabled and n > 1:
            txt = "Música %s  +  pauses %s  =  %s  ·  %d temes" % (fmt_dur(music), fmt_dur(pauses), fmt_dur(total), n)
        else:
            txt = "Música %s  ·  %d temes" % (fmt_dur(music), n)
        self.sum_lbl.configure(text=txt)
        rec = "Recomanat %s–%s min (%s · %s rpm)" % (
            fmt_minutes("ca", lo), fmt_minutes("ca", hi),
            i18n.fmt_disc(project.disc), i18n.fmt_rpm(project.rpm))
        color = {"red": th.RED, "yellow": th.YELLOW_TEXT, "green": th.GREEN}.get(status, th.MUTED)
        self.status_lbl.configure(text="%s  ·  %s" % (STATUS_TEXT[status], rec), fg=color)
        self.draw_bar()

    def draw_bar(self):
        c = self.bar
        c.delete("all")
        w = c.winfo_width()
        h = int(c.cget("height"))
        if w < 20:
            return
        project = self.tab.project
        side = self.side
        total = project.side_total(side)
        lo, hi = project.range_minutes()
        scale = max(hi * 60 * 1.2, total * 1.05, 1)
        x = lambda sec: 1 + (w - 2) * min(sec, scale) / scale  # noqa: E731
        c.create_rectangle(1, 4, w - 1, h - 4, fill="#e2e7ee", outline="")
        # Rang recomanat
        c.create_rectangle(x(lo * 60), 4, x(hi * 60), h - 4, fill="#f6ecc8", outline="")
        status = project.side_status(side)
        if total > 0:
            c.create_rectangle(1, 6, x(total), h - 6, fill=th.STATUS_COLORS[status], outline="")
        for m in (lo, hi):
            xm = x(m * 60)
            c.create_line(xm, 1, xm, h - 1, fill=th.TEXT, width=1)
        c.create_text(x(lo * 60) - 3, h / 2, text="%s'" % fmt_minutes("ca", lo), anchor="e",
                      font=th.FONTS["small"], fill=th.TEXT)
        c.create_text(x(hi * 60) + 3, h / 2, text="%s'" % fmt_minutes("ca", hi), anchor="w",
                      font=th.FONTS["small"], fill=th.TEXT)

    def update_toolbar(self):
        tab = self.tab
        s, i = tab.project.locate(tab.selected_id) if tab.selected_id else (None, -1)
        mine = s is not None and s.name == self.side_name
        n = len(self.side.tracks)
        self.btn_up.state(["!disabled"] if mine and i > 0 else ["disabled"])
        self.btn_down.state(["!disabled"] if mine and i < n - 1 else ["disabled"])
        self.btn_move.state(["!disabled"] if mine else ["disabled"])
        self.btn_del.state(["!disabled"] if mine else ["disabled"])

    # --- arrossegar dins del programa -------------------------------------
    def insertion_index(self, y_root):
        for i, (_tid, card) in enumerate(self.cards):
            mid = card.winfo_rooty() + card.winfo_height() / 2.0
            if y_root < mid:
                return i
        return len(self.cards)

    def show_indicator(self, index):
        if not self.cards:
            y = 6
        elif index < len(self.cards):
            y = max(0, self.cards[index][1].winfo_y() - 3)
        else:
            last = self.cards[-1][1]
            y = last.winfo_y() + last.winfo_height() + 1
        self.indicator.place(x=0, y=y, relwidth=1.0, height=3)
        self.indicator.lift()

    def hide_indicator(self):
        self.indicator.place_forget()

    def card_widget(self, track_id):
        for tid, card in self.cards:
            if tid == track_id:
                return card
        return None
