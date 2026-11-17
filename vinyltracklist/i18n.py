# -*- coding: utf-8 -*-
"""Textos per a la interfície (català) i les exportacions (ca / es / en)."""

LANGS = [("ca", "Català"), ("es", "Castellano"), ("en", "English")]

T = {
    "ca": {
        "tracklist": "Tracklist",
        "artist": "Artista",
        "album": "Títol",
        "catalog": "Referència",
        "disc": "Format",
        "speed": "Velocitat",
        "side": "Cara",
        "pos": "Pos.",
        "title": "Títol",
        "duration": "Durada",
        "pause": "Pausa",
        "audio": "Format d'àudio",
        "pauses_on": "Pausa entre temes: %s per defecte",
        "pauses_custom": " (personalitzada en alguns temes)",
        "pauses_off": "Sense pauses entre temes",
        "gaps_uniform": "Pausa entre temes: %s",
        "gaps_listed": "Pauses entre temes: segons la taula",
        "date": "Data: %s",
        "total_side": "Total cara %s",
        "music": "música",
        "pauses": "pauses",
        "recommended": "Recomanat",
        "st_empty": "buida",
        "st_green": "marge còmode",
        "st_yellow": "dins del rang recomanat",
        "st_red": "SUPERA el màxim recomanat",
        "warnings": "Avisos",
        "no_warnings": "Sense avisos.",
        "generated": "Generat amb VinylTracklist el %s",
        "page": "Pàg. %d",
        "min": "min",
        "int": "enter (PCM)",
        "float": "coma flotant",
        "mono": "mono",
        "stereo": "estèreo",
        "ch": "%d canals",
        "bits": "%d bits",
        "unreadable": "il·legible",
        "n_tracks": "%d temes",
        "lvl_error": "ERROR",
        "lvl_warning": "AVÍS",
        "lvl_info": "INFO",
        # Errors de lectura
        "err_io": "no s'ha pogut obrir el fitxer",
        "err_not_wav": "no és un fitxer WAV",
        "err_no_fmt": "falta el bloc de format (fmt)",
        "err_no_data": "falta el bloc d'àudio (data)",
        "err_corrupt": "capçalera corrupta",
        # Avisos
        "w_unreadable": "%(pos)s «%(title)s»: %(reason)s.",
        "w_compressed": "%(pos)s «%(title)s»: format comprimit (%(codec)s), no és PCM. No apte per a fàbrica.",
        "w_float": "%(pos)s «%(title)s»: WAV en coma flotant (%(bits)d bits float). No apte per a mastering/fàbrica: cal exportar-lo en enter (PCM) de 24 o 16 bits.",
        "w_low_bits": "%(pos)s «%(title)s»: només %(bits)d bits.",
        "w_multich": "%(pos)s «%(title)s»: %(ch)d canals; un vinil és estèreo o mono.",
        "w_mono": "%(pos)s «%(title)s»: fitxer mono.",
        "w_truncated": "%(pos)s «%(title)s»: fitxer incomplet (la capçalera indica més àudio del que conté). Durada calculada sobre el que hi ha.",
        "w_odd_rate": "%(pos)s «%(title)s»: freqüència poc habitual (%(rate)s).",
        "w_mixed_rates": "Freqüències de mostreig diferents al disc: %(groups)s.",
        "w_mixed_bits": "Resolucions diferents al disc: %(groups)s.",
        "w_side_over": "Cara %(side)s: %(total)s supera el màxim recomanat (%(max)s min) per a %(disc)s a %(rpm)s rpm.",
        "w_duplicate": "El fitxer «%(title)s» està carregat més d'una vegada (%(pos)s).",
        "w_missing": "%(pos)s «%(title)s»: no es troba el fitxer (%(path)s).",
    },
    "es": {
        "tracklist": "Tracklist",
        "artist": "Artista",
        "album": "Título",
        "catalog": "Referencia",
        "disc": "Formato",
        "speed": "Velocidad",
        "side": "Cara",
        "pos": "Pos.",
        "title": "Título",
        "duration": "Duración",
        "pause": "Pausa",
        "audio": "Formato de audio",
        "pauses_on": "Pausa entre temas: %s por defecto",
        "pauses_custom": " (personalizada en algunos temas)",
        "pauses_off": "Sin pausas entre temas",
        "gaps_uniform": "Pausa entre temas: %s",
        "gaps_listed": "Pausas entre temas: según la tabla",
        "date": "Fecha: %s",
        "total_side": "Total cara %s",
        "music": "música",
        "pauses": "pausas",
        "recommended": "Recomendado",
        "st_empty": "vacía",
        "st_green": "margen holgado",
        "st_yellow": "dentro del rango recomendado",
        "st_red": "SUPERA el máximo recomendado",
        "warnings": "Avisos",
        "no_warnings": "Sin avisos.",
        "generated": "Generado con VinylTracklist el %s",
        "page": "Pág. %d",
        "min": "min",
        "int": "entero (PCM)",
        "float": "coma flotante",
        "mono": "mono",
        "stereo": "estéreo",
        "ch": "%d canales",
        "bits": "%d bits",
        "unreadable": "ilegible",
        "n_tracks": "%d temas",
        "lvl_error": "ERROR",
        "lvl_warning": "AVISO",
        "lvl_info": "INFO",
        "err_io": "no se ha podido abrir el archivo",
        "err_not_wav": "no es un archivo WAV",
        "err_no_fmt": "falta el bloque de formato (fmt)",
        "err_no_data": "falta el bloque de audio (data)",
        "err_corrupt": "cabecera corrupta",
        "w_unreadable": "%(pos)s «%(title)s»: %(reason)s.",
        "w_compressed": "%(pos)s «%(title)s»: formato comprimido (%(codec)s), no es PCM. No apto para fábrica.",
        "w_float": "%(pos)s «%(title)s»: WAV en coma flotante (%(bits)d bits float). No apto para mastering/fábrica: hay que exportarlo en entero (PCM) de 24 o 16 bits.",
        "w_low_bits": "%(pos)s «%(title)s»: solo %(bits)d bits.",
        "w_multich": "%(pos)s «%(title)s»: %(ch)d canales; un vinilo es estéreo o mono.",
        "w_mono": "%(pos)s «%(title)s»: archivo mono.",
        "w_truncated": "%(pos)s «%(title)s»: archivo incompleto (la cabecera indica más audio del que contiene). Duración calculada sobre lo que hay.",
        "w_odd_rate": "%(pos)s «%(title)s»: frecuencia poco habitual (%(rate)s).",
        "w_mixed_rates": "Frecuencias de muestreo distintas en el disco: %(groups)s.",
        "w_mixed_bits": "Resoluciones distintas en el disco: %(groups)s.",
        "w_side_over": "Cara %(side)s: %(total)s supera el máximo recomendado (%(max)s min) para %(disc)s a %(rpm)s rpm.",
        "w_duplicate": "El archivo «%(title)s» está cargado más de una vez (%(pos)s).",
        "w_missing": "%(pos)s «%(title)s»: no se encuentra el archivo (%(path)s).",
    },
    "en": {
        "tracklist": "Tracklist",
        "artist": "Artist",
        "album": "Title",
        "catalog": "Catalogue no.",
        "disc": "Format",
        "speed": "Speed",
        "side": "Side",
        "pos": "Pos.",
        "title": "Title",
        "duration": "Duration",
        "pause": "Gap",
        "audio": "Audio format",
        "pauses_on": "Gap between tracks: %s by default",
        "pauses_custom": " (custom on some tracks)",
        "pauses_off": "No gaps between tracks",
        "gaps_uniform": "Gaps between tracks: %s",
        "gaps_listed": "Gaps between tracks: as listed per track",
        "date": "Date: %s",
        "total_side": "Side %s total",
        "music": "music",
        "pauses": "gaps",
        "recommended": "Recommended",
        "st_empty": "empty",
        "st_green": "comfortable margin",
        "st_yellow": "within recommended range",
        "st_red": "EXCEEDS recommended maximum",
        "warnings": "Warnings",
        "no_warnings": "No warnings.",
        "generated": "Generated with VinylTracklist on %s",
        "page": "Page %d",
        "min": "min",
        "int": "integer (PCM)",
        "float": "floating point",
        "mono": "mono",
        "stereo": "stereo",
        "ch": "%d channels",
        "bits": "%d-bit",
        "unreadable": "unreadable",
        "n_tracks": "%d tracks",
        "lvl_error": "ERROR",
        "lvl_warning": "WARNING",
        "lvl_info": "INFO",
        "err_io": "file could not be opened",
        "err_not_wav": "not a WAV file",
        "err_no_fmt": "format chunk (fmt) missing",
        "err_no_data": "audio chunk (data) missing",
        "err_corrupt": "corrupt header",
        "w_unreadable": "%(pos)s “%(title)s”: %(reason)s.",
        "w_compressed": "%(pos)s “%(title)s”: compressed format (%(codec)s), not PCM. Not suitable for the plant.",
        "w_float": "%(pos)s “%(title)s”: floating-point WAV (%(bits)d-bit float). Not suitable for mastering/plant: export as integer PCM, 24 or 16-bit.",
        "w_low_bits": "%(pos)s “%(title)s”: only %(bits)d-bit.",
        "w_multich": "%(pos)s “%(title)s”: %(ch)d channels; vinyl is stereo or mono.",
        "w_mono": "%(pos)s “%(title)s”: mono file.",
        "w_truncated": "%(pos)s “%(title)s”: incomplete file (header declares more audio than present). Duration based on available audio.",
        "w_odd_rate": "%(pos)s “%(title)s”: unusual sample rate (%(rate)s).",
        "w_mixed_rates": "Mixed sample rates on the record: %(groups)s.",
        "w_mixed_bits": "Mixed bit depths on the record: %(groups)s.",
        "w_side_over": "Side %(side)s: %(total)s exceeds the recommended maximum (%(max)s min) for %(disc)s at %(rpm)s rpm.",
        "w_duplicate": "File “%(title)s” is loaded more than once (%(pos)s).",
        "w_missing": "%(pos)s “%(title)s”: file not found (%(path)s).",
    },
}


def tr(lang, key):
    table = T.get(lang) or T["ca"]
    return table.get(key, T["ca"].get(key, key))


def decimal(lang, value, digits=1):
    s = ("%." + str(digits) + "f") % value
    if lang in ("ca", "es"):
        s = s.replace(".", ",")
    return s


def fmt_rate(lang, rate):
    khz = rate / 1000.0
    if abs(khz - round(khz)) < 1e-9:
        s = "%d" % int(round(khz))
    else:
        s = ("%.3f" % khz).rstrip("0").rstrip(".")
        if lang in ("ca", "es"):
            s = s.replace(".", ",")
    return s + " kHz"


def fmt_seconds(lang, sec):
    return decimal(lang, sec, 1) + " s"


def fmt_rpm(rpm, unicode_ok=False):
    if rpm == "33":
        return "33⅓" if unicode_ok else "33 1/3"
    return rpm


def fmt_disc(disc):
    return '%s"' % disc
