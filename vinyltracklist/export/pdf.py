# -*- coding: utf-8 -*-
"""Exportació a PDF sense dependències externes.

Fa servir les fonts estàndard Helvetica (no cal incrustar-les) amb
codificació WinAnsi, que cobreix català, castellà i anglès.
"""
import datetime
import zlib

from .common import subtitle, has_custom_marks
from .pdf_metrics import HELVETICA, HELVETICA_BOLD

PAGE_W, PAGE_H = 595.28, 841.89
MARGIN = 50.0
CONTENT_W = PAGE_W - 2 * MARGIN

NAVY = (0.122, 0.227, 0.373)
TEXT = (0.114, 0.153, 0.2)
MUTED = (0.365, 0.42, 0.478)
WHITE = (1, 1, 1)
ROW_ALT = (0.949, 0.961, 0.976)
GRID = (0.835, 0.863, 0.898)
SEV = {"error": (0.753, 0.224, 0.169), "warning": (0.604, 0.42, 0.0), "info": MUTED, None: MUTED}
STATUS = {"green": (0.18, 0.545, 0.341), "yellow": (0.604, 0.42, 0.0), "red": (0.753, 0.224, 0.169),
          "empty": MUTED}

_SUBST = {u"⅓": " 1/3", u"⚠": "(!)", u"✓": "OK", u"✖": "x", u"ℹ": "i", u"↧": "", u"≤": "<=",
          u"≥": ">=", u"♪": "", u"→": "->", u"←": "<-"}


def _enc(s):
    for k, v in _SUBST.items():
        s = s.replace(k, v)
    return s.encode("cp1252", "replace")


def text_width(s, size, bold=False):
    table = HELVETICA_BOLD if bold else HELVETICA
    total = 0
    for b in bytearray(_enc(s)):
        total += table[b - 32] if 32 <= b <= 255 else 556
    return total * size / 1000.0


def fit(s, size, bold, width):
    if text_width(s, size, bold) <= width:
        return s
    ell = u"…"
    lo, hi = 0, len(s)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if text_width(s[:mid] + ell, size, bold) <= width:
            lo = mid
        else:
            hi = mid - 1
    return s[:lo].rstrip() + ell


def wrap(s, size, bold, width):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if text_width(cand, size, bold) <= width or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _esc(b):
    return b.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class _Canvas(object):
    def __init__(self):
        self.pages = []
        self.ops = None

    def new_page(self):
        self.ops = []
        self.pages.append(self.ops)

    def text(self, x, y, s, size=10, bold=False, color=TEXT, align="left"):
        if align == "right":
            x -= text_width(s, size, bold)
        elif align == "center":
            x -= text_width(s, size, bold) / 2.0
        self.ops.append(b"BT /%s %.2f Tf %.3f %.3f %.3f rg %.2f %.2f Td (%s) Tj ET" % (
            b"F2" if bold else b"F1", size, color[0], color[1], color[2], x, y, _esc(_enc(s))))

    def rect(self, x, y, w, h, fill):
        self.ops.append(b"%.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f" % (fill[0], fill[1], fill[2], x, y, w, h))

    def line(self, x1, y1, x2, y2, color=GRID, width=0.6):
        self.ops.append(b"%.3f %.3f %.3f RG %.2f w %.2f %.2f m %.2f %.2f l S" % (
            color[0], color[1], color[2], width, x1, y1, x2, y2))

    def save(self, path, title):
        objs = []

        def add(body):
            objs.append(body)
            return len(objs)

        cat_id = add(None)
        pages_id = add(None)
        f1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        f2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        kids = []
        for ops in self.pages:
            raw = b"\n".join(ops)
            data = zlib.compress(raw)
            cid = add(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(data) + data + b"\nendstream")
            pid = add(("<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] "
                       "/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>"
                       % (pages_id, PAGE_W, PAGE_H, f1, f2, cid)).encode("ascii"))
            kids.append(pid)
        objs[cat_id - 1] = ("<< /Type /Catalog /Pages %d 0 R >>" % pages_id).encode("ascii")
        objs[pages_id - 1] = ("<< /Type /Pages /Kids [%s] /Count %d >>"
                              % (" ".join("%d 0 R" % k for k in kids), len(kids))).encode("ascii")
        now = datetime.datetime.now().strftime("D:%Y%m%d%H%M%S")
        title_hex = (u"﻿" + title).encode("utf-16-be").hex().upper().encode("ascii")
        info = add(b"<< /Title <" + title_hex + b"> /Producer (VinylTracklist) /Creator (VinylTracklist) /CreationDate ("
                   + now.encode("ascii") + b") >>")

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
        for off in offsets:
            out += b"%010d 00000 n \n" % off
        out += (b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (len(objs) + 1, cat_id, info, xref))
        with open(path, "wb") as f:
            f.write(bytes(out))


def layout(rep, c):
    """Dibuixa l'informe a 'c' (PDF o pantalla): new_page(), text(), rect(), line()."""
    lab = rep["labels"]
    state = {"y": 0.0, "page": 0}
    footer_left = " — ".join(x for x in (rep["title"], subtitle(rep)) if x)

    def footer():
        c.line(MARGIN, 38, PAGE_W - MARGIN, 38, GRID, 0.5)
        c.text(MARGIN, 26, fit(footer_left, 7.5, False, CONTENT_W - 60), 7.5, False, MUTED)
        c.text(PAGE_W - MARGIN, 26, lab["page"] % state["page"], 7.5, False, MUTED, "right")

    def new_page():
        if state["page"]:
            footer()
        c.new_page()
        state["page"] += 1
        c.rect(0, PAGE_H - 14, PAGE_W, 14, NAVY)
        state["y"] = PAGE_H - MARGIN

    def need(h):
        if state["y"] - h < 56:
            new_page()
            return True
        return False

    new_page()
    y = state["y"] - 6
    c.text(PAGE_W / 2, y, rep["title"], 22, True, NAVY, "center")
    y -= 22
    sub = subtitle(rep)
    if sub:
        c.text(PAGE_W / 2, y, fit(sub, 12, False, CONTENT_W), 12, False, TEXT, "center")
        y -= 17
    c.text(PAGE_W / 2, y, fit("%s · %s" % (rep["format_line"], rep["pause_line"]), 9.5, False, CONTENT_W),
           9.5, False, MUTED, "center")
    y -= 12
    c.line(MARGIN, y, PAGE_W - MARGIN, y, NAVY, 1.2)
    state["y"] = y - 22

    show_pause = rep["pause_enabled"]
    w_pos, w_pause, w_dur = 38.0, 52.0, 52.0
    x_pos = MARGIN
    x_title = MARGIN + w_pos
    x_dur_r = PAGE_W - MARGIN - 6
    x_pause_r = x_dur_r - w_dur
    w_title = CONTENT_W - w_pos - w_dur - (w_pause if show_pause else 0) - 10
    row_h = 30.0
    head_h = 18.0

    def table_header():
        y = state["y"]
        c.rect(MARGIN, y - head_h, CONTENT_W, head_h, NAVY)
        ty = y - head_h + 5.5
        c.text(x_pos + 6, ty, lab["pos"], 8.5, True, WHITE)
        c.text(x_title, ty, lab["title"], 8.5, True, WHITE)
        if show_pause:
            c.text(x_pause_r, ty, lab["pause"], 8.5, True, WHITE, "right")
        c.text(x_dur_r, ty, lab["duration"], 8.5, True, WHITE, "right")
        state["y"] = y - head_h

    for side in rep["sides"]:
        need(26 + head_h + row_h * 2)
        c.text(MARGIN, state["y"] - 12, side["heading"], 13.5, True, NAVY)
        state["y"] -= 20
        table_header()
        for i, r in enumerate(side["rows"]):
            if need(row_h + 2):
                table_header()
            y = state["y"]
            if i % 2:
                c.rect(MARGIN, y - row_h, CONTENT_W, row_h, ROW_ALT)
            c.line(MARGIN, y - row_h, PAGE_W - MARGIN, y - row_h, GRID, 0.5)
            ty = y - 12.5
            c.text(x_pos + 6, ty, r["pos"], 10, True, NAVY)
            c.text(x_title, ty, fit(r["title"], 10, True, w_title), 10, True, TEXT)
            tech = ("(!) " if r["severity"] else "") + r["tech"]
            c.text(x_title, ty - 11.5, fit(tech, 7.8, False, w_title), 7.8, False, SEV.get(r["severity"], MUTED))
            if show_pause and r["pause"]:
                c.text(x_pause_r, ty, r["pause"] + (" *" if r["pause_custom"] else ""), 8.5, False, MUTED, "right")
            c.text(x_dur_r, ty, r["dur"], 10, True, TEXT, "right")
            state["y"] = y - row_h
        need(36)
        y = state["y"] - 15
        c.text(MARGIN + 6, y, side["total_line"], 11, True, NAVY)
        if side["detail"]:
            c.text(MARGIN + 6 + text_width(side["total_line"], 11, True) + 10, y,
                   "(%s)" % side["detail"], 8.5, False, MUTED)
        if side["rec_line"]:
            y -= 13
            c.text(MARGIN + 6, y, fit(side["rec_line"], 8.5, False, CONTENT_W - 12), 8.5, True,
                   STATUS.get(side["status"], MUTED))
        state["y"] = y - 22

    if has_custom_marks(rep):
        c.text(MARGIN, state["y"] + 6, "* " + rep["custom_note"], 7.5, False, MUTED)
        state["y"] -= 6

    if rep["show_warnings"]:
        need(40)
        c.text(MARGIN, state["y"] - 12, lab["warnings"], 12.5, True, NAVY)
        state["y"] -= 26
        items = rep["warnings"] or [("info", "", lab["no_warnings"])]
        for level, label, text in items:
            prefix = ("[%s] " % label) if label else ""
            pw = text_width(prefix, 8.5, True)
            lines = wrap(text, 8.5, False, CONTENT_W - pw - 4)
            need(len(lines) * 11 + 4)
            y = state["y"]
            if prefix:
                c.text(MARGIN, y, prefix, 8.5, True, SEV.get(level, MUTED))
            for ln in lines:
                c.text(MARGIN + pw, y, ln, 8.5, False, TEXT)
                y -= 11
            state["y"] = y - 3

    c.text(MARGIN, 44, rep["footer"], 7.5, False, MUTED)
    footer()
    return state["page"]


def write_pdf(rep, path):
    c = _Canvas()
    layout(rep, c)
    title = " - ".join(x for x in (rep["title"], rep["artist"], rep["album"]) if x)
    c.save(path, title)
