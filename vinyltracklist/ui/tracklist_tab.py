# -*- coding: utf-8 -*-
"""Pestanya Tracklist: cares A/B, pauses, temps recomanats i avisos."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from .. import i18n
from ..config import DISCS, RPMS
from ..model import WAV_EXTS, parse_number, clamp_pause, natural_key
from . import theme as th
from .info_panel import InfoPanel
from .side_panel import SidePanel, PAUSE_VALUES

REPORT_LABELS = (("own", "Informe propi (castellano)"), ("factory", "Informe per a fàbrica (English)"))


def build_report_selector(parent, app, bg=None):
    bg = bg or th.BG
    tk.Label(parent, text="Informe", bg=bg, fg=th.NAVY, font=th.FONTS["bold"]).pack(side="left", padx=(0, 8))
    for value, label in REPORT_LABELS:
        ttk.Radiobutton(parent, text=label, value=value, variable=app.var_report_kind,
                        command=app.on_report_kind).pack(side="left", padx=(0, 12))


def build_export_buttons(parent, app):
    ttk.Button(parent, text="PDF", command=lambda: app.export("pdf")).pack(side="right")
    ttk.Button(parent, text="Word (.docx)", command=lambda: app.export("docx")).pack(side="right", padx=6)
    ttk.Button(parent, text="Text (.txt)", command=lambda: app.export("txt")).pack(side="right")
    tk.Label(parent, text="Exportar:", bg=parent.cget("bg"), fg=th.TEXT).pack(side="right", padx=(0, 8))

DISC_LABELS = ['7"', '10"', '12"']
RPM_LABELS = ["33 1/3", "45"]
LEVEL_ICON = {"error": "●", "warning": "●", "info": "●"}


class DragManager(object):
    """Arrossegar temes dins d'una cara i entre cares."""

    def __init__(self, tab):
        self.tab = tab
        self.track_id = None
        self.start = None
        self.dragging = False
        self.ghost = None
        self.target = None   # (panel, index)

    def press(self, e, track_id):
        self.track_id = track_id
        self.start = (e.x_root, e.y_root)
        self.dragging = False
        self.target = None
        self.tab.select(track_id)

    def motion(self, e):
        if self.track_id is None:
            return
        if not self.dragging:
            dx = abs(e.x_root - self.start[0])
            dy = abs(e.y_root - self.start[1])
            if dx + dy < 6:
                return
            self.dragging = True
            self._make_ghost()
        if self.ghost is not None:
            self.ghost.geometry("+%d+%d" % (e.x_root + 14, e.y_root + 8))
        panel = self._panel_at(e.x_root, e.y_root)
        for p in self.tab.panels.values():
            if p is not panel:
                p.hide_indicator()
        if panel is None:
            self.target = None
            return
        canvas = panel.list.canvas
        top = canvas.winfo_rooty()
        bottom = top + canvas.winfo_height()
        if e.y_root < top + 24:
            panel.list.scroll(-1)
        elif e.y_root > bottom - 24:
            panel.list.scroll(1)
        idx = panel.insertion_index(e.y_root)
        panel.show_indicator(idx)
        self.target = (panel, idx)

    def release(self, e):
        tid = self.track_id
        target = self.target if self.dragging else None
        self._cleanup()
        if tid is not None and target is not None:
            panel, idx = target
            self.tab.project.move(tid, panel.side_name, idx)
            self.tab.changed()

    def _panel_at(self, x, y):
        w = self.tab.winfo_containing(x, y)
        if w is None:
            return None
        path = str(w)
        for p in self.tab.panels.values():
            pp = str(p)
            if path == pp or path.startswith(pp + "."):
                return p
        return None

    def _make_ghost(self):
        t = self.tab.project.track(self.track_id)
        if t is None:
            return
        try:
            g = tk.Toplevel(self.tab)
            g.overrideredirect(True)
            try:
                g.attributes("-topmost", True)
                g.attributes("-alpha", 0.9)
            except tk.TclError:
                pass
            tk.Label(g, text="♪  %s  %s" % (self.tab.project.position(t.id), t.title),
                     bg=th.NAVY, fg=th.WHITE, font=th.FONTS["bold"], padx=10, pady=4).pack()
            self.ghost = g
        except tk.TclError:
            self.ghost = None

    def _cleanup(self):
        if self.ghost is not None:
            try:
                self.ghost.destroy()
            except tk.TclError:
                pass
        self.ghost = None
        for p in self.tab.panels.values():
            p.hide_indicator()
        self.track_id = None
        self.dragging = False
        self.target = None


class TracklistTab(tk.Frame):
    def __init__(self, master, app):
        tk.Frame.__init__(self, master, bg=th.BG)
        self.app = app
        self.selected_id = None
        self.drag = DragManager(self)
        self._building = False

        self._build_data_bar()
        self._build_options_bar()

        main = tk.Frame(self, bg=th.BG)
        main.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 4))
        self.panels = {}
        for c, name in enumerate(("A", "B")):
            p = SidePanel(main, self, name)
            p.grid(row=0, column=c, sticky="nsew", padx=(0, 8))
            main.grid_columnconfigure(c, weight=1, uniform="sides")
            self.panels[name] = p
        self.info = InfoPanel(main, self)
        self.info.grid(row=0, column=2, sticky="nsew")
        main.grid_columnconfigure(2, weight=0, minsize=260)
        main.grid_rowconfigure(0, weight=1)

        self._build_warnings()
        self._build_export_bar()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    @property
    def project(self):
        return self.app.project

    @property
    def cfg(self):
        return self.app.cfg

    def _build_data_bar(self):
        bar = tk.Frame(self, bg=th.BG)
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 2))
        self.var_artist = tk.StringVar()
        self.var_album = tk.StringVar()
        self.var_catalog = tk.StringVar()
        specs = (("Artista", self.var_artist, 30, "artist"),
                 ("Títol del disc", self.var_album, 30, "album"),
                 ("Referència", self.var_catalog, 14, "catalog"))
        for label, var, width, attr in specs:
            tk.Label(bar, text=label, bg=th.BG, fg=th.TEXT, font=th.FONTS["normal"]).pack(side="left", padx=(0, 4))
            ttk.Entry(bar, textvariable=var, width=width).pack(side="left", padx=(0, 14))
            var.trace_add("write", lambda *_a, v=var, a=attr: self._on_meta(a, v))

    def _on_meta(self, attr, var):
        if self._building:
            return
        setattr(self.project, attr, var.get())
        self.app.set_dirty()

    def _build_options_bar(self):
        bar = tk.Frame(self, bg=th.BG)
        bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 6))
        tk.Label(bar, text="Format", bg=th.BG, fg=th.TEXT).pack(side="left", padx=(0, 4))
        self.cb_disc = ttk.Combobox(bar, values=DISC_LABELS, width=5, state="readonly")
        self.cb_disc.pack(side="left", padx=(0, 12))
        tk.Label(bar, text="Velocitat", bg=th.BG, fg=th.TEXT).pack(side="left", padx=(0, 4))
        self.cb_rpm = ttk.Combobox(bar, values=RPM_LABELS, width=7, state="readonly")
        self.cb_rpm.pack(side="left")
        tk.Label(bar, text="rpm", bg=th.BG, fg=th.TEXT).pack(side="left", padx=(4, 18))
        self.cb_disc.bind("<<ComboboxSelected>>", self._on_format_combo)
        self.cb_rpm.bind("<<ComboboxSelected>>", self._on_format_combo)

        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=(0, 16))
        self.var_pause_on = tk.BooleanVar()
        ttk.Checkbutton(bar, text="Pausa entre temes", variable=self.var_pause_on,
                        command=self._on_pause_toggle).pack(side="left")
        tk.Label(bar, text="per defecte", bg=th.BG, fg=th.TEXT).pack(side="left", padx=(10, 4))
        self.var_pause = tk.StringVar()
        self.spin_pause = tk.Spinbox(bar, values=PAUSE_VALUES, width=5, justify="right",
                                     textvariable=self.var_pause, command=self._on_global_pause,
                                     relief="solid", borderwidth=1)
        self.spin_pause.pack(side="left")
        self.spin_pause.bind("<Return>", lambda e: self._on_global_pause())
        self.spin_pause.bind("<KP_Enter>", lambda e: self._on_global_pause())
        self.spin_pause.bind("<FocusOut>", lambda e: self._on_global_pause())
        tk.Label(bar, text="s", bg=th.BG, fg=th.TEXT).pack(side="left", padx=(3, 10))
        self.btn_reset_pauses = ttk.Button(bar, text="Aplicar a tots els temes", command=self._reset_pauses)
        self.btn_reset_pauses.pack(side="left")
        self.lbl_custom = tk.Label(bar, text="", bg=th.BG, fg=th.ACCENT, font=th.FONTS["small"])
        self.lbl_custom.pack(side="left", padx=8)

    def _build_warnings(self):
        box = tk.Frame(self, bg=th.PANEL, highlightthickness=1, highlightbackground=th.BORDER)
        box.grid(row=3, column=0, sticky="ew", padx=10, pady=(4, 4))
        head = tk.Frame(box, bg=th.PANEL)
        head.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(head, text="AVISOS", bg=th.PANEL, fg=th.NAVY, font=th.FONTS["bold"]).pack(side="left")
        self.lbl_warn_count = tk.Label(head, text="", bg=th.PANEL, fg=th.MUTED, font=th.FONTS["small"])
        self.lbl_warn_count.pack(side="left", padx=10)
        body = tk.Frame(box, bg=th.PANEL)
        body.pack(fill="x", padx=8, pady=(0, 8))
        self.txt_warn = tk.Text(body, height=5, wrap="word", bg=th.CARD, fg=th.TEXT,
                                relief="flat", font=th.FONTS["normal"], cursor="arrow",
                                highlightthickness=1, highlightbackground=th.BORDER, padx=6, pady=4)
        sb = ttk.Scrollbar(body, orient="vertical", command=self.txt_warn.yview)
        self.txt_warn.configure(yscrollcommand=sb.set)
        self.txt_warn.pack(side="left", fill="x", expand=True)
        sb.pack(side="left", fill="y")
        self.txt_warn.tag_configure("error", foreground=th.RED)
        self.txt_warn.tag_configure("warning", foreground=th.YELLOW_TEXT)
        self.txt_warn.tag_configure("info", foreground=th.MUTED)
        self.txt_warn.tag_configure("ok", foreground=th.GREEN)
        self.txt_warn.configure(state="disabled")

    def _build_export_bar(self):
        bar = tk.Frame(self, bg=th.BG)
        bar.grid(row=4, column=0, sticky="ew", padx=10, pady=(2, 10))
        build_report_selector(bar, self.app)
        build_export_buttons(bar, self.app)

    # --- refresc -------------------------------------------------------
    def load_project_into_ui(self):
        self._building = True
        try:
            p = self.project
            self.var_artist.set(p.artist)
            self.var_album.set(p.album)
            self.var_catalog.set(p.catalog)
            self.selected_id = None
        finally:
            self._building = False
        self.refresh_all()

    def refresh_all(self):
        p = self.project
        self.cb_disc.current(DISCS.index(p.disc))
        self.cb_rpm.current(RPMS.index(p.rpm))
        self.var_pause_on.set(p.pause_enabled)
        self.var_pause.set(i18n.decimal("ca", p.pause_global, 1))
        self.spin_pause.configure(state="normal" if p.pause_enabled else "disabled")
        self.btn_reset_pauses.state(["!disabled"] if p.pause_enabled else ["disabled"])
        for panel in self.panels.values():
            panel.rebuild()
        self.info.refresh()
        self.refresh_custom_label()
        self.refresh_warnings()

    def refresh_summaries(self):
        for panel in self.panels.values():
            panel.update_summary()
        self.info.refresh()
        self.refresh_custom_label()
        self.refresh_warnings()

    def refresh_custom_label(self):
        p = self.project
        n = sum(1 for s in p.sides for _, _, c in p.gaps(s) if c)
        if p.pause_enabled and n:
            self.lbl_custom.configure(text="1 pausa personalitzada" if n == 1 else "%d pauses personalitzades" % n)
        else:
            self.lbl_custom.configure(text="")

    def refresh_warnings(self):
        ws = self.project.warnings("ca")
        t = self.txt_warn
        t.configure(state="normal")
        t.delete("1.0", "end")
        for tag in t.tag_names():
            if tag.startswith("w_"):
                t.tag_delete(tag)
        if self.project.is_empty():
            t.insert("end", "Carrega els WAV de cada cara per veure'n l'anàlisi.", ("info",))
        elif not ws:
            t.insert("end", "Cap avís: formats correctes i cares dins del temps recomanat.", ("ok",))
        for i, w in enumerate(ws):
            tag = "w_%d" % i
            t.insert("end", "%s  %s\n" % (LEVEL_ICON[w.level], w.text("ca")), (w.level, tag))
            if w.track_ids:
                t.tag_bind(tag, "<Button-1>", lambda e, tid=w.track_ids[0]: self.select(tid, scroll=True))
                t.tag_bind(tag, "<Enter>", lambda e: self.txt_warn.configure(cursor="hand2"))
                t.tag_bind(tag, "<Leave>", lambda e: self.txt_warn.configure(cursor="arrow"))
        t.configure(state="disabled")
        n_err = sum(1 for w in ws if w.level == "error")
        n_warn = sum(1 for w in ws if w.level == "warning")
        n_info = sum(1 for w in ws if w.level == "info")
        parts = []
        if n_err:
            parts.append("%d error%s" % (n_err, "" if n_err == 1 else "s"))
        if n_warn:
            parts.append("1 avís" if n_warn == 1 else "%d avisos" % n_warn)
        if n_info:
            parts.append("%d informatiu%s" % (n_info, "" if n_info == 1 else "s"))
        self.lbl_warn_count.configure(text="  ·  ".join(parts) + ("  —  clica un avís per anar al tema" if ws else ""),
                                      fg=th.RED if n_err else th.MUTED)

    def changed(self, rebuild=True):
        self.app.set_dirty()
        if rebuild:
            self.after_idle(self.refresh_all)
        else:
            self.refresh_summaries()

    def on_pause_changed(self):
        self.app.set_dirty()
        self.refresh_summaries()

    # --- selecció --------------------------------------------------------
    def select(self, track_id, scroll=False):
        self.selected_id = track_id
        for panel in self.panels.values():
            panel.restyle_selection()
        if scroll and track_id:
            s, _ = self.project.locate(track_id)
            if s is not None:
                panel = self.panels.get(s.name)
                card = panel.card_widget(track_id) if panel else None
                if card is not None:
                    panel.list.see(card)

    # --- accions -----------------------------------------------------------
    def add_files_dialog(self, side_name):
        paths = filedialog.askopenfilenames(
            parent=self, title="Afegir WAV a la cara %s" % side_name,
            initialdir=self.cfg.get("last_dir") or None,
            filetypes=[("Fitxers WAV", "*.wav *.WAV *.wave *.bwf"), ("Tots els fitxers", "*.*")])
        if paths:
            self.add_paths(side_name, list(self.tk.splitlist(paths)) if isinstance(paths, str) else list(paths))

    def add_paths(self, side_name, paths):
        files = []
        skipped = []
        for p in paths:
            if os.path.isdir(p):
                inner = [os.path.join(p, f) for f in os.listdir(p)
                         if f.lower().endswith(WAV_EXTS) and os.path.isfile(os.path.join(p, f))]
                files.extend(sorted(inner, key=lambda x: natural_key(os.path.basename(x))))
            elif p.lower().endswith(WAV_EXTS):
                files.append(p)
            else:
                skipped.append(os.path.basename(p))
        if not files:
            if skipped:
                messagebox.showwarning("VinylTracklist", "Només es poden carregar fitxers WAV.\n\nIgnorats: %s"
                                       % ", ".join(skipped[:8]), parent=self)
            return
        self.cfg["last_dir"] = os.path.dirname(files[0])
        self.winfo_toplevel().configure(cursor="watch")
        self.update_idletasks()
        try:
            self.project.add_files(side_name, files)
        finally:
            self.winfo_toplevel().configure(cursor="")
        self.changed()
        if skipped:
            messagebox.showinfo("VinylTracklist", "S'han ignorat %d fitxers que no són WAV:\n%s"
                                % (len(skipped), ", ".join(skipped[:8])), parent=self)

    def shift_selected(self, delta):
        if self.selected_id:
            self.project.shift(self.selected_id, delta)
            self.changed()

    def move_selected_other(self):
        if self.selected_id:
            self.project.to_other_side(self.selected_id)
            self.changed()

    def remove_selected(self):
        if self.selected_id:
            self.project.remove(self.selected_id)
            self.selected_id = None
            self.changed()

    def rename(self, track_id):
        t = self.project.track(track_id)
        if t is None:
            return
        self.drag._cleanup()
        new = simpledialog.askstring("Títol del tema", "Títol de %s:" % self.project.position(track_id),
                                     initialvalue=t.title, parent=self)
        if new is not None and new.strip():
            t.title = new.strip()
            self.changed()

    def show_in_folder(self, track_id):
        t = self.project.track(track_id)
        if t is None:
            return
        path = os.path.normpath(t.path)
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception:
            pass

    def context_menu(self, e, track_id):
        self.select(track_id)
        s, i = self.project.locate(track_id)
        if s is None:
            return
        other = "B" if s.name == "A" else "A"
        m = tk.Menu(self, tearoff=0)
        m.add_command(label="Canviar el títol…", command=lambda: self.rename(track_id))
        m.add_command(label="Moure a la cara %s" % other, command=self.move_selected_other)
        m.add_command(label="Pujar", command=lambda: self.shift_selected(-1),
                      state="normal" if i > 0 else "disabled")
        m.add_command(label="Baixar", command=lambda: self.shift_selected(1),
                      state="normal" if i < len(s.tracks) - 1 else "disabled")
        m.add_separator()
        m.add_command(label="Mostrar el fitxer a la carpeta", command=lambda: self.show_in_folder(track_id))
        m.add_command(label="Treure de la llista", command=self.remove_selected)
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def delete_key(self, _e=None):
        focus = self.focus_get()
        if isinstance(focus, (tk.Entry, ttk.Entry, tk.Spinbox, tk.Text)):
            return
        self.remove_selected()

    # --- format i pauses ------------------------------------------------------
    def _on_format_combo(self, _e=None):
        self.set_format(DISCS[self.cb_disc.current()], RPMS[self.cb_rpm.current()])

    def set_format(self, disc, rpm):
        p = self.project
        if (p.disc, p.rpm) == (disc, rpm):
            return
        p.disc, p.rpm = disc, rpm
        self.cfg["disc"], self.cfg["rpm"] = disc, rpm
        self.cb_disc.current(DISCS.index(disc))
        self.cb_rpm.current(RPMS.index(rpm))
        self.app.set_dirty()
        self.refresh_summaries()

    def _on_pause_toggle(self):
        self.project.pause_enabled = bool(self.var_pause_on.get())
        self.cfg["pause_enabled"] = self.project.pause_enabled
        self.changed()

    def _on_global_pause(self):
        v = parse_number(self.var_pause.get())
        p = self.project
        if v is None:
            self.var_pause.set(i18n.decimal("ca", p.pause_global, 1))
            return
        v = clamp_pause(v)
        self.var_pause.set(i18n.decimal("ca", v, 1))
        if abs(v - p.pause_global) < 1e-9:
            return
        p.pause_global = v
        self.cfg["default_pause"] = v
        self.changed()

    def _reset_pauses(self):
        self._on_global_pause()
        p = self.project
        n = sum(1 for s in p.sides for _, _, c in p.gaps(s) if c)
        if n and not messagebox.askyesno(
                "Pauses", "Hi ha %d pauses personalitzades.\nVols posar %s s a totes les separacions?"
                % (n, i18n.decimal("ca", p.pause_global, 1)), parent=self):
            return
        p.reset_pauses()
        self.changed()
