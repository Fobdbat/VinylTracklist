# -*- coding: utf-8 -*-
"""Configuració persistent (temps recomanats, regles, preferències)."""
import copy
import json
import os

# Minuts per cara (mínim, màxim) segons la taula de referència
DEFAULT_RANGES = {
    "7": {"33": [5, 7], "45": [4, 5]},
    "10": {"33": [10, 13], "45": [8, 10]},
    "12": {"33": [18, 22], "45": [10, 15]},
}

DEFAULTS = {
    "ranges": DEFAULT_RANGES,
    "float_not_ok": True,
    "pause_enabled": True,
    "default_pause": 2.0,
    "disc": "12",
    "rpm": "33",
    "report_kind": "own",
    "last_dir": "",
}

DISCS = ("7", "10", "12")
RPMS = ("33", "45")


def config_dir():
    base = os.environ.get("APPDATA")
    if base:
        return os.path.join(base, "VinylTracklist")
    return os.path.join(os.path.expanduser("~"), ".config", "vinyltracklist")


def config_path():
    return os.path.join(config_dir(), "config.json")


def _merge(defaults, loaded):
    out = copy.deepcopy(defaults)
    if not isinstance(loaded, dict):
        return out
    for key, val in loaded.items():
        if key not in out:
            continue
        if key == "ranges":
            for disc in DISCS:
                for rpm in RPMS:
                    try:
                        lo, hi = loaded["ranges"][disc][rpm]
                        lo, hi = float(lo), float(hi)
                        if 0 < lo <= hi:
                            out["ranges"][disc][rpm] = [lo, hi]
                    except (KeyError, TypeError, ValueError):
                        pass
        elif type(val) == type(out[key]) or (isinstance(out[key], float) and isinstance(val, int)):
            out[key] = val
    return out


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            return _merge(DEFAULTS, json.load(f))
    except (IOError, OSError, ValueError):
        return copy.deepcopy(DEFAULTS)


def save_config(cfg):
    try:
        d = config_dir()
        if not os.path.isdir(d):
            os.makedirs(d)
        tmp = config_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        if os.path.exists(config_path()):
            os.remove(config_path())
        os.rename(tmp, config_path())
        return True
    except (IOError, OSError):
        return False
