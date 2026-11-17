# -*- coding: utf-8 -*-
"""Prepara les dades dels dos informes per als exportadors (TXT, Word, PDF) i la vista prèvia.

- Informe propi ('own'): en castellà, amb temps recomanat i avisos.
- Informe per a fàbrica ('factory'): en anglès, sense temps recomanat ni avisos.
"""
import datetime

from .. import i18n
from ..model import fmt_dur, fmt_minutes

KINDS = {
    "own": {"lang": "es", "show_rec": True, "show_warnings": True, "mark_custom": True},
    "factory": {"lang": "en", "show_rec": False, "show_warnings": False, "mark_custom": False},
}

FILE_SUFFIX = {"own": "Tracklist", "factory": "Tracklist (factory)"}


def build_report(project, kind="own"):
    opts = KINDS[kind]
    lang = opts["lang"]
    p = project
    tr = lambda k: i18n.tr(lang, k)  # noqa: E731
    lo, hi = p.range_minutes()

    if not p.pause_enabled:
        pause_line = tr("pauses_off")
    elif kind == "factory":
        if p.has_custom_pauses():
            pause_line = tr("gaps_listed")
        else:
            pause_line = tr("gaps_uniform") % i18n.fmt_seconds(lang, p.pause_global)
    else:
        pause_line = tr("pauses_on") % i18n.fmt_seconds(lang, p.pause_global)
        if p.has_custom_pauses():
            pause_line += tr("pauses_custom")

    sides = []
    for side in p.sides:
        if not side.tracks:
            continue
        rows = []
        n = len(side.tracks)
        for i, t in enumerate(side.tracks):
            pause = ""
            if p.pause_enabled and i < n - 1:
                pause = i18n.fmt_seconds(lang, p.pause_value(t))
            rows.append({
                "pos": "%s%d" % (side.name, i + 1),
                "title": t.title,
                "dur": fmt_dur(t.duration) if t.info.ok else "--:--",
                "pause": pause,
                "pause_custom": opts["mark_custom"] and t.pause_after is not None and bool(pause),
                "tech": t.tech_text(lang),
                "severity": t.severity(p.cfg) if opts["show_warnings"] else None,
            })
        music = p.side_music(side)
        pauses = p.side_pauses(side)
        total = music + pauses
        status = p.side_status(side)
        detail = ""
        if p.pause_enabled and n > 1:
            detail = "%s %s + %s %s" % (tr("music"), fmt_dur(music), tr("pauses"), fmt_dur(pauses))
        rec_line = "%s: %s–%s min — %s" % (tr("recommended"), fmt_minutes(lang, lo), fmt_minutes(lang, hi),
                                           tr("st_" + status))
        sides.append({
            "name": side.name,
            "heading": "%s %s" % (tr("side").upper(), side.name),
            "rows": rows,
            "total": fmt_dur(total),
            "total_line": (tr("total_side") % side.name) + ": " + fmt_dur(total),
            "detail": detail,
            "status": status,
            "rec_line": rec_line if opts["show_rec"] else "",
        })

    warnings = []
    if opts["show_warnings"]:
        for w in p.warnings(lang):
            warnings.append((w.level, tr("lvl_" + w.level), w.text(lang)))

    now = datetime.datetime.now()
    if kind == "factory":
        footer = tr("date") % now.strftime("%d/%m/%Y")
    else:
        footer = tr("generated") % now.strftime("%d/%m/%Y %H:%M")
    return {
        "kind": kind,
        "lang": lang,
        "show_rec": opts["show_rec"],
        "show_warnings": opts["show_warnings"],
        "mark_custom": opts["mark_custom"],
        "title": tr("tracklist"),
        "artist": p.artist.strip(),
        "album": p.album.strip(),
        "catalog": p.catalog.strip(),
        "format_line": "%s · %s rpm" % (i18n.fmt_disc(p.disc), i18n.fmt_rpm(p.rpm)),
        "pause_enabled": p.pause_enabled,
        "pause_line": pause_line,
        "sides": sides,
        "warnings": warnings,
        "footer": footer,
        "custom_note": {"ca": "pausa personalitzada", "es": "pausa personalizada",
                        "en": "custom gap"}[lang],
        "labels": {k: tr(k) for k in ("artist", "album", "catalog", "disc", "pos", "title", "duration",
                                      "pause", "audio", "warnings", "no_warnings", "page")},
    }


def subtitle(rep):
    parts = [x for x in (rep["artist"], rep["album"]) if x]
    s = " — ".join(parts)
    if rep["catalog"]:
        s = (s + " · " if s else "") + rep["catalog"]
    return s


def has_custom_marks(rep):
    return rep["mark_custom"] and any(r["pause_custom"] for s in rep["sides"] for r in s["rows"])
