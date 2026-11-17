"""Lectura de capçaleres WAV sense descodificar l'àudio.

Suporta RIFF/WAVE, RF64 i BW64; formats PCM enter, coma flotant i
WAVE_FORMAT_EXTENSIBLE. Compatible amb Python 3.8.
"""
import os
import struct

WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

# Cua comuna dels GUID KSDATAFORMAT_SUBTYPE_* (els 2 primers bytes indiquen el format)
_GUID_TAIL = bytes.fromhex("000000001000800000aa00389b71")

COMPRESSED_NAMES = {
    0x0002: "MS ADPCM",
    0x0006: "A-law",
    0x0007: "mu-law",
    0x0011: "IMA ADPCM",
    0x0050: "MPEG",
    0x0055: "MP3",
}


class WavInfo(object):
    """Resultat de llegir un WAV. Si ok és False, error conté un codi."""

    def __init__(self, path):
        self.path = path
        self.ok = False
        self.error = None          # codi d'error (vegeu i18n: 'err_*')
        self.error_detail = ""
        self.container = ""        # RIFF / RF64 / BW64
        self.format_tag = None
        self.sample_rate = 0
        self.channels = 0
        self.bits = 0              # bits del contenidor
        self.valid_bits = 0        # bits útils (EXTENSIBLE)
        self.block_align = 0
        self.is_float = False
        self.is_pcm = False
        self.frames = 0
        self.duration = 0.0        # segons
        self.data_size = 0
        self.truncated = False
        self.file_size = 0

    @property
    def effective_bits(self):
        return self.valid_bits or self.bits

    @property
    def compressed_name(self):
        if self.format_tag in COMPRESSED_NAMES:
            return COMPRESSED_NAMES[self.format_tag]
        return "0x%04X" % (self.format_tag or 0)

    def __repr__(self):
        if not self.ok:
            return "<WavInfo %s ERROR %s>" % (os.path.basename(self.path), self.error)
        return "<WavInfo %s %d Hz %d bit %s %dch %.3fs>" % (
            os.path.basename(self.path), self.sample_rate, self.effective_bits,
            "float" if self.is_float else "int", self.channels, self.duration)


def read_wav_info(path):
    info = WavInfo(path)
    try:
        info.file_size = os.path.getsize(path)
        with open(path, "rb") as f:
            _parse(f, info)
    except (IOError, OSError) as exc:
        info.ok = False
        info.error = "err_io"
        info.error_detail = str(exc)
    except struct.error:
        info.ok = False
        info.error = "err_corrupt"
    return info


def _parse(f, info):
    head = f.read(12)
    if len(head) < 12 or head[8:12] != b"WAVE" or head[0:4] not in (b"RIFF", b"RF64", b"BW64"):
        info.error = "err_not_wav"
        return
    info.container = head[0:4].decode("ascii")
    is_64 = info.container in ("RF64", "BW64")
    ds64_data_size = None
    fmt_found = False
    data_offset = None
    data_size = None
    file_size = info.file_size

    while True:
        hdr = f.read(8)
        if len(hdr) < 8:
            break
        cid = hdr[0:4]
        csize = struct.unpack("<I", hdr[4:8])[0]
        start = f.tell()

        if cid == b"ds64" and is_64:
            body = f.read(min(csize, 28))
            if len(body) >= 16:
                ds64_data_size = struct.unpack("<Q", body[8:16])[0]
        elif cid == b"fmt ":
            body = f.read(min(csize, 40))
            if len(body) < 16:
                info.error = "err_corrupt"
                return
            (tag, ch, rate, _avg, align, bits) = struct.unpack("<HHIIHH", body[0:16])
            info.format_tag = tag
            info.channels = ch
            info.sample_rate = rate
            info.block_align = align
            info.bits = bits
            if tag == WAVE_FORMAT_EXTENSIBLE and len(body) >= 40:
                valid_bits = struct.unpack("<H", body[18:20])[0]
                sub = body[24:40]
                info.valid_bits = valid_bits if 0 < valid_bits <= bits else 0
                if sub[2:16] == _GUID_TAIL:
                    sub_tag = struct.unpack("<H", sub[0:2])[0]
                    info.format_tag = sub_tag
                else:
                    info.format_tag = None
            info.is_pcm = info.format_tag == WAVE_FORMAT_PCM
            info.is_float = info.format_tag == WAVE_FORMAT_IEEE_FLOAT
            fmt_found = True
        elif cid == b"data":
            data_offset = start
            data_size = csize
            if is_64 and csize == 0xFFFFFFFF and ds64_data_size is not None:
                data_size = ds64_data_size
            # No cal llegir les dades: saltem fins al final del bloc
            skip = data_size
            if data_offset + skip > file_size:
                info.truncated = True
                data_size = max(0, file_size - data_offset)
                break
            f.seek(data_offset + skip + (skip & 1))
            continue

        # Saltar a la següent capçalera (amb byte de farciment si la mida és senar)
        nxt = start + csize + (csize & 1)
        if nxt > file_size:
            break
        f.seek(nxt)

    if not fmt_found:
        info.error = "err_no_fmt"
        return
    if data_offset is None:
        info.error = "err_no_data"
        return
    if info.sample_rate <= 0 or info.channels <= 0:
        info.error = "err_corrupt"
        return

    align = info.block_align or (info.channels * ((info.bits + 7) // 8))
    if align <= 0:
        info.error = "err_corrupt"
        return
    info.data_size = data_size
    info.frames = data_size // align
    info.duration = info.frames / float(info.sample_rate)
    info.ok = True
