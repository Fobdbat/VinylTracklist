# -*- coding: utf-8 -*-
"""Exportació a text pla (UTF-8 amb BOM i salts de línia de Windows)."""
from .common import has_custom_marks


def _cut(s, width):
    return s if len(s) <= width else s[: max(1, width - 1)] + "…"


def write_txt(rep, path):
    lab = rep["labels"]
    L = []
    title = rep["title"].upper()
    L.append(title)
    L.append("=" * len(title))
    for key, val in (("artist", rep["artist"]), ("album", rep["album"]), ("catalog", rep["catalog"])):
        if val:
            L.append("%s: %s" % (lab[key], val))
    L.append("%s: %s" % (lab["disc"], rep["format_line"]))
    L.append(rep["pause_line"])
    L.append("")

    all_titles = [r["title"] for s in rep["sides"] for r in s["rows"]]
    tw = min(48, max([len(lab["title"])] + [len(t) for t in all_titles]))
    show_pause = rep["pause_enabled"]
    for side in rep["sides"]:
        L.append(side["heading"])
        L.append("-" * len(side["heading"]))
        head = "%-5s %-*s %8s" % (lab["pos"], tw, lab["title"], lab["duration"])
        if show_pause:
            head += "  %-7s" % lab["pause"]
        head += "   " + lab["audio"]
        L.append(head.rstrip())
        for r in side["rows"]:
            line = "%-5s %-*s %8s" % (r["pos"], tw, _cut(r["title"], tw), r["dur"])
            if show_pause:
                line += "  %-7s" % ((r["pause"] + ("*" if r["pause_custom"] else "")) if r["pause"] else "")
            line += "   " + ("(!) " if r["severity"] else "") + r["tech"]
            L.append(line.rstrip())
        L.append("")
        tl = side["total_line"]
        if side["detail"]:
            tl += "  (%s)" % side["detail"]
        L.append(tl)
        if side["rec_line"]:
            L.append(side["rec_line"])
        L.append("")
    if has_custom_marks(rep):
        L.append("* " + rep["custom_note"])
        L.append("")

    if rep["show_warnings"]:
        L.append(lab["warnings"].upper())
        L.append("-" * len(lab["warnings"]))
        if rep["warnings"]:
            for _level, label, text in rep["warnings"]:
                L.append("[%s] %s" % (label, text))
        else:
            L.append(lab["no_warnings"])
        L.append("")
    L.append(rep["footer"])
    text = ("\r\n".join(L) + "\r\n").replace(u"⅓", " 1/3")
    with open(path, "wb") as f:
        f.write(b"\xef\xbb\xbf" + text.encode("utf-8"))
