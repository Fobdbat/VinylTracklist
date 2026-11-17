# -*- coding: utf-8 -*-
import sys
import tkinter.font as tkfont

NAVY = "#1f3a5f"
NAVY_LIGHT = "#2c5282"
BG = "#eef1f5"
PANEL = "#f7f9fb"
CARD = "#ffffff"
CARD_SEL = "#d8e6f6"
BORDER = "#c9d1dc"
TEXT = "#1d2733"
MUTED = "#5d6b7a"
GAP_BG = "#e7ebf0"
ACCENT = "#1f6fd1"
RED = "#c0392b"
RED_BG = "#fbe9e7"
YELLOW = "#d9a400"
YELLOW_TEXT = "#9a6b00"
GREEN = "#2e8b57"
WHITE = "#ffffff"

STATUS_COLORS = {"green": GREEN, "yellow": YELLOW, "red": RED, "empty": "#b8c2cc"}
SEVERITY_COLORS = {"error": RED, "warning": YELLOW_TEXT, "info": MUTED, None: MUTED}

FONTS = {}


def init_fonts(root):
    family = "Segoe UI" if sys.platform == "win32" else "DejaVu Sans"
    if family not in tkfont.families(root):
        family = tkfont.nametofont("TkDefaultFont").actual("family")
    base = 9
    for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
        try:
            tkfont.nametofont(name).configure(family=family, size=base)
        except Exception:
            pass
    FONTS["normal"] = tkfont.Font(root, family=family, size=base)
    FONTS["bold"] = tkfont.Font(root, family=family, size=base, weight="bold")
    FONTS["small"] = tkfont.Font(root, family=family, size=base - 1)
    FONTS["title"] = tkfont.Font(root, family=family, size=base + 2, weight="bold")
    FONTS["big"] = tkfont.Font(root, family=family, size=base + 7, weight="bold")
    FONTS["side"] = tkfont.Font(root, family=family, size=base + 3, weight="bold")


def fit_text(font, text, width):
    """Retalla el text amb '…' perquè càpiga en 'width' píxels."""
    if width <= 0 or font.measure(text) <= width:
        return text
    ell = "…"
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if font.measure(text[:mid] + ell) <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + ell
