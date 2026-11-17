# -*- coding: utf-8 -*-
"""Finestra principal de VinylTracklist."""
import datetime
import os
import re
import subprocess
import sys
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .. import config as cfgmod
from .. import __version__
from ..model import Project
from ..export import build_report, write_txt, write_docx, write_pdf, FILE_SUFFIX
from . import dnd
from . import theme as th
from .report_tab import ReportTab
from .settings_dialog import SettingsDialog
from .tracklist_tab import TracklistTab

APP_NAME = "VinylTracklist"
PROJECT_EXT = ".vtracklist"


def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    return os.path.join(base, rel)


def enable_dpi_awareness():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)   # Windows 8.1+
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()        # Windows 7
    except Exception:
        pass


def open_with_system(path):
    try:
        if sys.platform == "win32":
            os.startfile(path)  # noqa: B606
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def safe_filename(s):
    s = re.sub(r'[\\/:*?"<>|]+', " ", s)
    return re.sub(r"\s+", " ", s).strip(" .")


class App(object):
    def __init__(self, root):
        self.root = root
        self.cfg = cfgmod.load_config()
        self.project = Project(self.cfg)
        self.dirty = False

        th.init_fonts(root)
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        else:
            style.theme_use("clam")
        style.configure("TNotebook.Tab", padding=(14, 5))
        root.configure(bg=th.BG)
        scale = max(1.0, root.winfo_fpixels("1i") / 96.0)
        root.geometry("%dx%d" % (int(1320 * scale), int(860 * scale)))
        root.minsize(int(1040 * scale), int(640 * scale))
        try:
            if sys.platform == "win32":
                root.iconbitmap(default=resource_path(os.path.join("assets", "vinyltracklist.ico")))
            else:
                img = tk.PhotoImage(file=resource_path(os.path.join("assets", "vinyltracklist.png")))
                root.iconphoto(True, img)
        except Exception:
            pass

        kind = self.cfg.get("report_kind", "own")
        self.var_report_kind = tk.StringVar(value=kind if kind in FILE_SUFFIX else "own")
        self._build_menu()
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True)
        self.tracklist = TracklistTab(nb, self)
        self.report = ReportTab(nb, self)
        nb.add(self.tracklist, text="  Tracklist  ")
        nb.add(self.report, text="  Informe  ")
        self.notebook = nb
        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.tracklist.load_project_into_ui()
        self.update_title()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.bind("<Delete>", self.tracklist.delete_key)
        root.bind("<Control-s>", lambda e: self.save_project())
        root.bind("<Control-o>", lambda e: self.open_project())
        root.bind("<Control-n>", lambda e: self.new_project())
        root.report_callback_exception = self.report_exception

    # ------------------------------------------------------------------
    def _build_menu(self):
        m = tk.Menu(self.root)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="Projecte nou", accelerator="Ctrl+N", command=self.new_project)
        f.add_command(label="Obrir projecte…", accelerator="Ctrl+O", command=self.open_project)
        f.add_command(label="Desar projecte", accelerator="Ctrl+S", command=self.save_project)
        f.add_command(label="Desar projecte com a…", command=lambda: self.save_project(save_as=True))
        f.add_separator()
        for kind, label in (("own", "Exportar informe propi (castellano)"),
                            ("factory", "Exportar informe per a fàbrica (English)")):
            sub = tk.Menu(f, tearoff=0)
            sub.add_command(label="PDF…", command=lambda k=kind: self.export("pdf", k))
            sub.add_command(label="Word (.docx)…", command=lambda k=kind: self.export("docx", k))
            sub.add_command(label="Text (.txt)…", command=lambda k=kind: self.export("txt", k))
            f.add_cascade(label=label, menu=sub)
        f.add_separator()
        f.add_command(label="Sortir", command=self.on_close)
        m.add_cascade(label="Fitxer", menu=f)
        t = tk.Menu(m, tearoff=0)
        t.add_command(label="Configuració…", command=self.open_settings)
        m.add_cascade(label="Eines", menu=t)
        h = tk.Menu(m, tearoff=0)
        h.add_command(label="Quant a VinylTracklist", command=self.about)
        m.add_cascade(label="Ajuda", menu=h)
        self.root.configure(menu=m)

    def set_dirty(self, value=True):
        if self.dirty != value:
            self.dirty = value
            self.update_title()

    def update_title(self):
        name = os.path.basename(self.project.file_path) if self.project.file_path else "Projecte nou"
        self.root.title("%s%s — %s %s" % ("*" if self.dirty else "", name, APP_NAME, __version__))

    def save_cfg(self):
        cfgmod.save_config(self.cfg)

    # --- projectes -------------------------------------------------------
    def confirm_discard(self):
        if not self.dirty or self.project.is_empty():
            return True
        ans = messagebox.askyesnocancel(APP_NAME, "Hi ha canvis sense desar.\nVols desar el projecte?",
                                        parent=self.root)
        if ans is None:
            return False
        if ans:
            return self.save_project()
        return True

    def new_project(self):
        if not self.confirm_discard():
            return
        self.project = Project(self.cfg)
        self.dirty = False
        self.tracklist.load_project_into_ui()
        self.update_title()

    def open_project(self, path=None):
        if path is None:
            if not self.confirm_discard():
                return
            path = filedialog.askopenfilename(
                parent=self.root, title="Obrir projecte",
                initialdir=self.cfg.get("last_dir") or None,
                filetypes=[("Projectes VinylTracklist", "*" + PROJECT_EXT), ("Tots els fitxers", "*.*")])
            if not path:
                return
        try:
            self.project = Project.load(path, self.cfg)
        except Exception as exc:
            messagebox.showerror(APP_NAME, "No s'ha pogut obrir el projecte:\n%s" % exc, parent=self.root)
            return
        self.dirty = False
        self.tracklist.load_project_into_ui()
        self.update_title()

    def save_project(self, save_as=False):
        path = self.project.file_path
        if save_as or not path:
            initial = safe_filename(" - ".join(x for x in (self.project.artist, self.project.album) if x)) or "Vinil"
            path = filedialog.asksaveasfilename(
                parent=self.root, title="Desar projecte", defaultextension=PROJECT_EXT,
                initialfile=initial + PROJECT_EXT, initialdir=self.cfg.get("last_dir") or None,
                filetypes=[("Projectes VinylTracklist", "*" + PROJECT_EXT)])
            if not path:
                return False
        try:
            self.project.save(path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, "No s'ha pogut desar el projecte:\n%s" % exc, parent=self.root)
            return False
        self.dirty = False
        self.update_title()
        return True

    # --- informes i exportació -------------------------------------------------
    def _on_tab_changed(self, _e=None):
        if self.notebook.select() == str(self.report):
            self.report.refresh()

    def on_report_kind(self):
        self.cfg["report_kind"] = self.var_report_kind.get()
        if self.notebook.select() == str(self.report):
            self.report.refresh()

    def export(self, kind, report_kind=None):
        report_kind = report_kind or self.var_report_kind.get()
        p = self.project
        if p.is_empty():
            messagebox.showinfo(APP_NAME, "Encara no hi ha cap tema carregat.", parent=self.root)
            return
        errors = [w for w in p.warnings("ca") if w.level == "error"]
        if errors and not messagebox.askyesno(
                APP_NAME, "Hi ha %d error%s a la llista d'avisos.\nVols exportar el tracklist igualment?"
                % (len(errors), "" if len(errors) == 1 else "s"), parent=self.root):
            return
        ext = {"txt": ".txt", "docx": ".docx", "pdf": ".pdf"}[kind]
        desc = {"txt": "Text", "docx": "Document de Word", "pdf": "PDF"}[kind]
        base = safe_filename(" - ".join(x for x in (p.artist, p.album) if x)) or "Vinil"
        initial = "%s - %s%s" % (base, FILE_SUFFIX[report_kind], ext)
        initialdir = (os.path.dirname(p.file_path) if p.file_path else None) or self.cfg.get("last_dir") or None
        path = filedialog.asksaveasfilename(parent=self.root, title="Exportar tracklist",
                                            defaultextension=ext, initialfile=initial,
                                            initialdir=initialdir, filetypes=[(desc, "*" + ext)])
        if not path:
            return
        try:
            report = build_report(p, report_kind)
            {"txt": write_txt, "docx": write_docx, "pdf": write_pdf}[kind](report, path)
        except Exception as exc:
            messagebox.showerror(APP_NAME, "No s'ha pogut exportar:\n%s" % exc, parent=self.root)
            return
        if messagebox.askyesno(APP_NAME, "Tracklist desat a:\n%s\n\nVols obrir-lo ara?" % path, parent=self.root):
            open_with_system(path)

    # --- altres ------------------------------------------------------------
    def open_settings(self):
        dlg = SettingsDialog(self)
        self.root.wait_window(dlg)
        if dlg.result:
            self.tracklist.refresh_all()

    def about(self):
        dnd_txt = "actiu" if dnd.AVAILABLE else "no disponible (fes servir «Afegir WAV…»)"
        messagebox.showinfo(
            "Quant a %s" % APP_NAME,
            "%s %s\nTracklist de les cares d'un vinil a partir dels WAV.\n\n"
            "Arrossegar des de l'Explorador: %s\nConfiguració: %s\n\n"
            "Europe Multimedia Service · INDESINENTER Records"
            % (APP_NAME, __version__, dnd_txt, cfgmod.config_path()), parent=self.root)

    def report_exception(self, exc, val, tb):
        text = "".join(traceback.format_exception(exc, val, tb))
        try:
            d = cfgmod.config_dir()
            if not os.path.isdir(d):
                os.makedirs(d)
            with open(os.path.join(d, "errors.log"), "a", encoding="utf-8") as f:
                f.write("\n[%s]\n%s" % (datetime.datetime.now().isoformat(), text))
        except Exception:
            pass
        messagebox.showerror(APP_NAME, "S'ha produït un error inesperat:\n%s\n\nS'ha desat el detall a errors.log "
                                       "a la carpeta de configuració." % val, parent=self.root)

    def on_close(self):
        if not self.confirm_discard():
            return
        self.save_cfg()
        self.root.destroy()


def run(argv=None):
    argv = argv or []
    enable_dpi_awareness()
    root = tk.Tk()
    dnd.load(root)
    app = App(root)
    for a in argv:
        if a.lower().endswith(PROJECT_EXT) and os.path.isfile(a):
            app.open_project(a)
            break
    root.mainloop()
