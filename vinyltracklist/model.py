# -*- coding: utf-8 -*-
"""Model de dades: cares, temes, pauses, temps i avisos."""
import itertools
import json
import os
import re
import unicodedata

from . import i18n
from .wavinfo import read_wav_info

_ids = itertools.count(1)

STD_RATES = (44100, 48000, 88200, 96000, 176400, 192000)
PAUSE_MIN = 0.0
PAUSE_MAX = 30.0
WAV_EXTS = (".wav", ".wave", ".bwf")


def natural_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def filename_key(path):
    """Ordre alfabètic natural pel nom del fitxer (sense accents: «À» va amb «A»; «2» abans de «10»)."""
    name = unicodedata.normalize("NFKD", os.path.basename(path))
    name = "".join(c for c in name if not unicodedata.combining(c))
    return natural_key(name)


_PREFIX_RE = re.compile(r"^\s*(?:[A-Da-d]\s?\d{1,2}|\d{1,3})(?:\s*[-.)]\s*|\s+)+")


def title_from_filename(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    s = stem.replace("_", " ")
    s2 = _PREFIX_RE.sub("", s, count=1)
    s2 = re.sub(r"\s+", " ", s2).strip(" -")
    return s2 or stem.strip() or stem


def clamp_pause(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return max(PAUSE_MIN, min(PAUSE_MAX, round(v * 10) / 10.0))


def parse_number(text):
    try:
        return float(str(text).strip().replace(",", "."))
    except ValueError:
        return None


def fmt_dur(seconds):
    s = int(round(seconds))
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return "%d:%02d:%02d" % (h, m, sec)
    return "%d:%02d" % (m, sec)


def fmt_minutes(lang, v):
    if abs(v - round(v)) < 1e-9:
        return "%d" % int(round(v))
    return i18n.decimal(lang, v, 1)


class Track(object):
    def __init__(self, path, info=None, title=None, pause_after=None):
        self.id = next(_ids)
        self.path = path
        self.info = info if info is not None else read_wav_info(path)
        self.title = title if title else title_from_filename(path)
        self.pause_after = pause_after   # None = pausa global

    @property
    def duration(self):
        return self.info.duration if self.info.ok else 0.0

    def tech_text(self, lang="ca"):
        inf = self.info
        if not inf.ok:
            return i18n.tr(lang, "unreadable") + " — " + i18n.tr(lang, inf.error or "err_corrupt")
        parts = [i18n.fmt_rate(lang, inf.sample_rate)]
        parts.append(i18n.tr(lang, "bits") % inf.effective_bits)
        if inf.is_float:
            parts.append(i18n.tr(lang, "float"))
        elif inf.is_pcm:
            parts.append(i18n.tr(lang, "int"))
        else:
            parts.append(inf.compressed_name)
        if inf.channels == 1:
            parts.append(i18n.tr(lang, "mono"))
        elif inf.channels == 2:
            parts.append(i18n.tr(lang, "stereo"))
        else:
            parts.append(i18n.tr(lang, "ch") % inf.channels)
        return " · ".join(parts)

    def severity(self, cfg):
        """'error', 'warning' o None segons el format del fitxer."""
        inf = self.info
        if not inf.ok or inf.truncated:
            return "error"
        if not inf.is_pcm and not inf.is_float:
            return "error"
        if inf.is_float:
            return "error" if cfg.get("float_not_ok", True) else "warning"
        if inf.channels > 2:
            return "error"
        if inf.effective_bits < 16 or inf.sample_rate not in STD_RATES:
            return "warning"
        return None


class Side(object):
    def __init__(self, name):
        self.name = name
        self.tracks = []


class Warn(object):
    def __init__(self, level, code, params, track_ids=()):
        self.level = level      # 'error' | 'warning' | 'info'
        self.code = code
        self.params = params
        self.track_ids = list(track_ids)

    def text(self, lang="ca"):
        return i18n.tr(lang, self.code) % self.params


class Project(object):
    def __init__(self, cfg):
        self.cfg = cfg
        self.sides = [Side("A"), Side("B")]
        self.disc = cfg.get("disc", "12")
        self.rpm = cfg.get("rpm", "33")
        self.pause_enabled = bool(cfg.get("pause_enabled", True))
        self.pause_global = clamp_pause(cfg.get("default_pause", 2.0)) or 0.0
        self.artist = ""
        self.album = ""
        self.catalog = ""
        self.file_path = None

    # --- accés -----------------------------------------------------------
    def side(self, name):
        for s in self.sides:
            if s.name == name:
                return s
        raise KeyError(name)

    def all_tracks(self):
        for s in self.sides:
            for t in s.tracks:
                yield s, t

    def locate(self, track_id):
        for s in self.sides:
            for i, t in enumerate(s.tracks):
                if t.id == track_id:
                    return s, i
        return None, -1

    def track(self, track_id):
        s, i = self.locate(track_id)
        return s.tracks[i] if s else None

    def position(self, track_id):
        s, i = self.locate(track_id)
        return "%s%d" % (s.name, i + 1) if s else "?"

    def is_empty(self):
        return not any(s.tracks for s in self.sides)

    # --- edició ----------------------------------------------------------
    def add_files(self, side_name, paths):
        """Afegeix WAV al final de la cara, ordenats alfabèticament entre ells.

        Els temes que ja hi eren no canvien d'ordre (ni perden les pauses pròpies).
        Si la cara és buida, queda tota en ordre alfabètic."""
        side = self.side(side_name)
        new = [Track(p) for p in sorted(paths, key=filename_key)]
        side.tracks.extend(new)
        return new

    def sort_side(self, side_name):
        self.side(side_name).tracks.sort(key=lambda t: filename_key(t.path))

    def move(self, track_id, side_name, index):
        src, i = self.locate(track_id)
        if src is None:
            return
        t = src.tracks.pop(i)
        dst = self.side(side_name)
        if dst is src and index > i:
            index -= 1
        index = max(0, min(index, len(dst.tracks)))
        dst.tracks.insert(index, t)

    def shift(self, track_id, delta):
        s, i = self.locate(track_id)
        if s is None:
            return
        j = i + delta
        if 0 <= j < len(s.tracks):
            s.tracks[i], s.tracks[j] = s.tracks[j], s.tracks[i]

    def to_other_side(self, track_id):
        s, _ = self.locate(track_id)
        if s is None:
            return
        names = [x.name for x in self.sides]
        other = names[(names.index(s.name) + 1) % len(names)]
        self.move(track_id, other, len(self.side(other).tracks))

    def remove(self, track_id):
        s, i = self.locate(track_id)
        if s is not None:
            del s.tracks[i]

    def reset_pauses(self):
        for _, t in self.all_tracks():
            t.pause_after = None

    # --- temps -----------------------------------------------------------
    def pause_value(self, track):
        return self.pause_global if track.pause_after is None else track.pause_after

    def gaps(self, side):
        """[(tema, segons, personalitzada)] per a cada separació dins la cara."""
        out = []
        for t in side.tracks[:-1]:
            out.append((t, self.pause_value(t), t.pause_after is not None))
        return out

    def side_music(self, side):
        return sum(t.duration for t in side.tracks)

    def side_pauses(self, side):
        if not self.pause_enabled:
            return 0.0
        return sum(v for _, v, _ in self.gaps(side))

    def side_total(self, side):
        return self.side_music(side) + self.side_pauses(side)

    def has_custom_pauses(self):
        return any(c for s in self.sides for _, _, c in self.gaps(s))

    def range_minutes(self):
        r = self.cfg["ranges"][self.disc][self.rpm]
        return float(r[0]), float(r[1])

    def side_status(self, side):
        total = self.side_total(side)
        if not side.tracks:
            return "empty"
        lo, hi = self.range_minutes()
        if total <= lo * 60 + 0.5:
            return "green"
        if total <= hi * 60 + 0.5:
            return "yellow"
        return "red"

    # --- avisos ----------------------------------------------------------
    def _groups_text(self, lang, groups):
        parts = []
        for label, ids in groups:
            if len(ids) > 4:
                parts.append("%s (%s)" % (label, i18n.tr(lang, "n_tracks") % len(ids)))
            else:
                parts.append("%s (%s)" % (label, ", ".join(self.position(i) for i in ids)))
        return "; ".join(parts)

    def warnings(self, lang="ca"):
        cfg = self.cfg
        out = []
        seen = {}
        rates = {}
        depths = {}
        for side, t in self.all_tracks():
            pos = self.position(t.id)
            base = {"pos": pos, "title": t.title}
            inf = t.info
            key = os.path.normcase(os.path.abspath(t.path))
            seen.setdefault(key, []).append(t.id)
            if not inf.ok:
                if inf.error == "err_io" and not os.path.exists(t.path):
                    p = dict(base, path=t.path)
                    out.append(Warn("error", "w_missing", p, [t.id]))
                else:
                    p = dict(base, reason=i18n.tr(lang, inf.error or "err_corrupt"))
                    out.append(Warn("error", "w_unreadable", p, [t.id]))
                continue
            if inf.truncated:
                out.append(Warn("error", "w_truncated", base, [t.id]))
            if not inf.is_pcm and not inf.is_float:
                out.append(Warn("error", "w_compressed", dict(base, codec=inf.compressed_name), [t.id]))
                continue
            if inf.is_float:
                lvl = "error" if cfg.get("float_not_ok", True) else "warning"
                out.append(Warn(lvl, "w_float", dict(base, bits=inf.effective_bits), [t.id]))
            elif inf.effective_bits < 16:
                out.append(Warn("warning", "w_low_bits", dict(base, bits=inf.effective_bits), [t.id]))
            if inf.channels > 2:
                out.append(Warn("error", "w_multich", dict(base, ch=inf.channels), [t.id]))
            elif inf.channels == 1:
                out.append(Warn("info", "w_mono", base, [t.id]))
            if inf.sample_rate not in STD_RATES:
                out.append(Warn("warning", "w_odd_rate",
                                dict(base, rate=i18n.fmt_rate(lang, inf.sample_rate)), [t.id]))
            rates.setdefault(inf.sample_rate, []).append(t.id)
            dkey = (inf.effective_bits, inf.is_float)
            depths.setdefault(dkey, []).append(t.id)

        for key, ids in seen.items():
            if len(ids) > 1:
                t = self.track(ids[0])
                out.append(Warn("warning", "w_duplicate",
                                {"title": os.path.basename(t.path),
                                 "pos": ", ".join(self.position(i) for i in ids)}, ids))

        if len(rates) > 1:
            groups = sorted(rates.items(), key=lambda kv: -len(kv[1]))
            g = [(i18n.fmt_rate(lang, r), ids) for r, ids in groups]
            all_ids = [i for _, ids in groups for i in ids]
            out.append(Warn("warning", "w_mixed_rates", {"groups": self._groups_text(lang, g)}, all_ids))
        if len(depths) > 1:
            groups = sorted(depths.items(), key=lambda kv: -len(kv[1]))
            g = []
            for (bits, is_float), ids in groups:
                label = i18n.tr(lang, "bits") % bits
                if is_float:
                    label += " " + i18n.tr(lang, "float")
                g.append((label, ids))
            all_ids = [i for _, ids in groups for i in ids]
            out.append(Warn("info", "w_mixed_bits", {"groups": self._groups_text(lang, g)}, all_ids))

        lo, hi = self.range_minutes()
        for side in self.sides:
            if self.side_status(side) == "red":
                out.append(Warn("error", "w_side_over", {
                    "side": side.name,
                    "total": fmt_dur(self.side_total(side)),
                    "max": fmt_minutes(lang, hi),
                    "disc": i18n.fmt_disc(self.disc),
                    "rpm": i18n.fmt_rpm(self.rpm),
                }, [t.id for t in side.tracks]))
        return out

    # --- desar / obrir -----------------------------------------------------
    def to_dict(self, project_path=None):
        base = os.path.dirname(os.path.abspath(project_path)) if project_path else None
        sides = []
        for s in self.sides:
            items = []
            for t in s.tracks:
                item = {"path": os.path.abspath(t.path), "title": t.title, "pause_after": t.pause_after}
                if base:
                    try:
                        item["relpath"] = os.path.relpath(os.path.abspath(t.path), base)
                    except ValueError:  # unitats diferents a Windows
                        pass
                items.append(item)
            sides.append({"name": s.name, "tracks": items})
        return {
            "app": "VinylTracklist", "version": 1,
            "artist": self.artist, "album": self.album, "catalog": self.catalog,
            "disc": self.disc, "rpm": self.rpm,
            "pause_enabled": self.pause_enabled, "pause_global": self.pause_global,
            "sides": sides,
        }

    def save(self, path):
        data = self.to_dict(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.file_path = path

    @classmethod
    def load(cls, path, cfg):
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("app") != "VinylTracklist":
            raise ValueError("not a VinylTracklist project")
        p = cls(cfg)
        p.artist = d.get("artist", "")
        p.album = d.get("album", "")
        p.catalog = d.get("catalog", "")
        if d.get("disc") in cfg["ranges"]:
            p.disc = d["disc"]
        if d.get("rpm") in ("33", "45"):
            p.rpm = d["rpm"]
        p.pause_enabled = bool(d.get("pause_enabled", True))
        pg = clamp_pause(d.get("pause_global", 2.0))
        p.pause_global = 2.0 if pg is None else pg
        base = os.path.dirname(os.path.abspath(path))
        p.sides = []
        for sd in d.get("sides", []):
            side = Side(sd.get("name", "?"))
            for item in sd.get("tracks", []):
                fp = item.get("path", "")
                rel = item.get("relpath")
                if not os.path.exists(fp) and rel:
                    cand = os.path.normpath(os.path.join(base, rel))
                    if os.path.exists(cand):
                        fp = cand
                pa = item.get("pause_after")
                side.tracks.append(Track(fp, title=item.get("title"),
                                         pause_after=None if pa is None else clamp_pause(pa)))
            p.sides.append(side)
        for name in ("A", "B"):
            if name not in [s.name for s in p.sides]:
                p.sides.append(Side(name))
        p.sides.sort(key=lambda s: s.name)
        p.file_path = path
        return p
