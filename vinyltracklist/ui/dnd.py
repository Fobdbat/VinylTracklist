# -*- coding: utf-8 -*-
"""Arrossegar fitxers des de l'Explorador de Windows (opcional).

Fa servir tkdnd (paquet tkinterdnd2). Si no es pot carregar, el programa
funciona igual amb el botó «Afegir WAV…».

Nota: tkinterdnd2 tria la DLL segons l'arquitectura del Windows, i en un
programa de 32 bits sobre Windows de 64 bits triaria la incorrecta. Aquí
es tria segons l'arquitectura del procés.
"""
import os
import struct
import sys

AVAILABLE = False


def load(root):
    global AVAILABLE
    try:
        import tkinterdnd2  # noqa: F401  (afegeix els mètodes dnd als widgets)
        base = os.path.join(os.path.dirname(tkinterdnd2.__file__), "tkdnd")
        bits64 = struct.calcsize("P") == 8
        if sys.platform == "win32":
            rep = "win-x64" if bits64 else "win-x86"
        elif sys.platform.startswith("linux"):
            rep = "linux-x64"
        elif sys.platform == "darwin":
            import platform
            rep = "osx-arm64" if platform.machine() == "arm64" else "osx-x64"
        else:
            return False
        path = os.path.join(base, rep)
        if not os.path.isdir(path):
            return False
        root.tk.call("lappend", "auto_path", path)
        root.tk.call("package", "require", "tkdnd")
        AVAILABLE = True
    except Exception:
        AVAILABLE = False
    return AVAILABLE


def register_files_drop(widget, callback):
    """callback(llista_de_camins, y_root). Retorna True si s'ha registrat."""
    if not AVAILABLE:
        return False
    try:
        from tkinterdnd2 import DND_FILES, COPY

        def _on_drop(event):
            try:
                paths = list(widget.tk.splitlist(event.data))
            except Exception:
                paths = []
            y_root = getattr(event, "y_root", None)
            widget.after_idle(lambda: callback(paths, y_root))
            return COPY

        widget.drop_target_register(DND_FILES)
        widget.dnd_bind("<<Drop>>", _on_drop)
        return True
    except Exception:
        return False
