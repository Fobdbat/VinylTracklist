# -*- coding: utf-8 -*-
"""Exportació a Word (.docx) sense dependències externes.

Genera un document Office Open XML mínim i vàlid (Word 2007 o posterior,
LibreOffice, Google Docs).
"""
import datetime
import re
import zipfile
from xml.sax.saxutils import escape

from .common import subtitle, has_custom_marks

NAVY = "1F3A5F"
MUTED = "5D6B7A"
TEXT = "1D2733"
ROW_ALT = "F2F5F9"
GRID = "D5DCE5"
SEV = {"error": "C0392B", "warning": "9A6B00", "info": MUTED, None: MUTED}
STATUS = {"green": "2E8B57", "yellow": "9A6B00", "red": "C0392B", "empty": MUTED}

PAGE_W, PAGE_H, MARGIN = 11906, 16838, 1134
CONTENT_W = PAGE_W - 2 * MARGIN

_BAD = re.compile(u"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def _x(s):
    return escape(_BAD.sub("", s or ""))


def _run(text, bold=False, size=None, color=None, italic=False):
    rpr = ""
    if bold:
        rpr += "<w:b/><w:bCs/>"
    if italic:
        rpr += "<w:i/><w:iCs/>"
    if color:
        rpr += '<w:color w:val="%s"/>' % color
    if size:
        hp = int(round(size * 2))
        rpr += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (hp, hp)
    if rpr:
        rpr = "<w:rPr>%s</w:rPr>" % rpr
    return '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr, _x(text))


def _para(runs, align=None, before=0, after=0, keep_next=False, border_bottom=None):
    ppr = ""
    if keep_next:
        ppr += "<w:keepNext/>"
    if border_bottom:
        ppr += ('<w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" w:color="%s"/></w:pBdr>'
                % border_bottom)
    ppr += '<w:spacing w:before="%d" w:after="%d"/>' % (before, after)
    if align:
        ppr += '<w:jc w:val="%s"/>' % align
    if isinstance(runs, str):
        runs = [runs]
    return "<w:p><w:pPr>%s</w:pPr>%s</w:p>" % (ppr, "".join(runs))


def _cell(width, paras, fill=None, valign="center"):
    tcpr = '<w:tcW w:w="%d" w:type="dxa"/>' % width
    if fill:
        tcpr += '<w:shd w:val="clear" w:color="auto" w:fill="%s"/>' % fill
    tcpr += '<w:vAlign w:val="%s"/>' % valign
    return "<w:tc><w:tcPr>%s</w:tcPr>%s</w:tc>" % (tcpr, "".join(paras))


def _row(cells, header=False):
    trpr = "<w:trPr><w:cantSplit/>%s</w:trPr>" % ("<w:tblHeader/>" if header else "")
    return "<w:tr>%s%s</w:tr>" % (trpr, "".join(cells))


def _table(widths, rows):
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    borders = ('<w:tblBorders>'
               '<w:top w:val="single" w:sz="4" w:space="0" w:color="%s"/>'
               '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="%s"/>'
               '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="%s"/>'
               '</w:tblBorders>') % (GRID, GRID, GRID)
    tblpr = ('<w:tblPr><w:tblW w:w="%d" w:type="dxa"/>%s<w:tblLayout w:type="fixed"/>'
             '<w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
             '<w:bottom w:w="40" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>'
             '<w:tblLook w:val="0000"/></w:tblPr>') % (sum(widths), borders)
    return "<w:tbl>%s<w:tblGrid>%s</w:tblGrid>%s</w:tbl>" % (tblpr, grid, "".join(rows))


def _body(rep):
    lab = rep["labels"]
    out = []
    out.append(_para(_run(rep["title"], bold=True, size=22, color=NAVY), align="center", after=60))
    sub = subtitle(rep)
    if sub:
        out.append(_para(_run(sub, size=12, color=TEXT), align="center", after=40))
    out.append(_para(_run("%s · %s" % (rep["format_line"], rep["pause_line"]), size=10, color=MUTED),
                     align="center", after=120, border_bottom=NAVY))

    show_pause = rep["pause_enabled"]
    w_pos, w_pause, w_dur = 820, 1050, 1050
    w_title = CONTENT_W - w_pos - w_dur - (w_pause if show_pause else 0)
    widths = [w_pos, w_title] + ([w_pause] if show_pause else []) + [w_dur]

    for side in rep["sides"]:
        out.append(_para(_run(side["heading"], bold=True, size=14, color=NAVY), before=280, after=100,
                         keep_next=True))
        hdr_runs = [lab["pos"], lab["title"]] + ([lab["pause"]] if show_pause else []) + [lab["duration"]]
        aligns = ["left", "left"] + (["right"] if show_pause else []) + ["right"]
        rows = [_row([_cell(w, [_para(_run(t, bold=True, size=9, color="FFFFFF"), align=a)], fill=NAVY)
                      for w, t, a in zip(widths, hdr_runs, aligns)], header=True)]
        for i, r in enumerate(side["rows"]):
            fill = ROW_ALT if i % 2 else None
            title_paras = [_para(_run(r["title"], bold=True, size=10, color=TEXT))]
            tech = ("(!) " if r["severity"] else "") + r["tech"]
            title_paras.append(_para(_run(tech, size=8, color=SEV.get(r["severity"], MUTED))))
            cells = [_cell(w_pos, [_para(_run(r["pos"], bold=True, size=10, color=NAVY))], fill),
                     _cell(w_title, title_paras, fill)]
            if show_pause:
                pause_txt = r["pause"] + (" *" if r["pause_custom"] else "")
                cells.append(_cell(w_pause, [_para(_run(pause_txt, size=9, color=MUTED), align="right")], fill))
            cells.append(_cell(w_dur, [_para(_run(r["dur"], bold=True, size=10, color=TEXT), align="right")], fill))
            rows.append(_row(cells))
        out.append(_table(widths, rows))
        runs = [_run(side["total_line"], bold=True, size=11, color=NAVY)]
        if side["detail"]:
            runs.append(_run("   (%s)" % side["detail"], size=9, color=MUTED))
        if side["rec_line"]:
            out.append(_para(runs, before=100, after=20, keep_next=True))
            out.append(_para(_run(side["rec_line"], size=9, color=STATUS.get(side["status"], MUTED)), after=60))
        else:
            out.append(_para(runs, before=100, after=60))

    if has_custom_marks(rep):
        out.append(_para(_run("* " + rep["custom_note"], size=8, color=MUTED), before=60))

    if rep["show_warnings"]:
        out.append(_para(_run(lab["warnings"], bold=True, size=13, color=NAVY), before=300, after=80,
                         keep_next=True))
        if rep["warnings"]:
            for level, label, text in rep["warnings"]:
                out.append(_para([_run("[%s] " % label, bold=True, size=9, color=SEV.get(level)),
                                  _run(text, size=9, color=TEXT)], after=50))
        else:
            out.append(_para(_run(lab["no_warnings"], size=9, color=MUTED)))
    out.append(_para(_run(rep["footer"], italic=True, size=8, color=MUTED), before=360))
    sect = ('<w:sectPr><w:pgSz w:w="%d" w:h="%d"/>'
            '<w:pgMar w:top="%d" w:right="%d" w:bottom="%d" w:left="%d" w:header="567" w:footer="567" w:gutter="0"/>'
            '</w:sectPr>') % (PAGE_W, PAGE_H, MARGIN, MARGIN, MARGIN, MARGIN)
    return "".join(out) + sect


def write_docx(rep, path):
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    document = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<w:document xmlns:w="%s" xmlns:r="%s"><w:body>%s</w:body></w:document>'
                % (W, R, _body(rep)))
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<w:styles xmlns:w="%s"><w:docDefaults><w:rPrDefault><w:rPr>'
              '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'
              '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="%s"/></w:rPr></w:rPrDefault>'
              '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr>'
              '</w:pPrDefault></w:docDefaults>'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>'
              '</w:styles>' % (W, {"es": "es-ES", "en": "en-GB"}.get(rep["lang"], "ca-ES")))
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        '<Override PartName="/docProps/core.xml" '
        'ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        '</Types>')
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/'
        'core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>')
    doc_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
        'styles" Target="styles.xml"/></Relationships>')
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    title = " - ".join(x for x in (rep["title"], rep["artist"], rep["album"]) if x)
    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>%s</dc:title><dc:creator>VinylTracklist</dc:creator>'
        '<dcterms:created xsi:type="dcterms:W3CDTF">%s</dcterms:created>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">%s</dcterms:modified>'
        '</cp:coreProperties>') % (_x(title), now, now)
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>VinylTracklist</Application></Properties>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", doc_rels)
        z.writestr("word/styles.xml", styles)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
