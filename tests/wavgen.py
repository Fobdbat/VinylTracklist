"""Generador de WAV de prova (capçaleres de tots els formats).

Els fitxers llargs es creen com a fitxers 'sparse': la mida és real però
no ocupen disc, perquè el programa només llegeix la capçalera.
"""
import struct

PCM_GUID = bytes.fromhex("0100000000001000800000aa00389b71")
FLOAT_GUID = bytes.fromhex("0300000000001000800000aa00389b71")


def _chunk(cid, body):
    pad = b"\x00" if len(body) & 1 else b""
    return cid + struct.pack("<I", len(body)) + body + pad


def fmt_body(tag, ch, rate, bits, extensible=False, valid_bits=None, sub=None, cb=None):
    align = ch * ((bits + 7) // 8)
    base = struct.pack("<HHIIHH", 0xFFFE if extensible else tag, ch, rate, rate * align, align, bits)
    if extensible:
        vb = valid_bits if valid_bits is not None else bits
        mask = 0x3 if ch == 2 else 0x4
        return base + struct.pack("<HHI", 22, vb, mask) + (sub or (PCM_GUID if tag == 1 else FLOAT_GUID))
    if cb is not None:
        return base + struct.pack("<H", cb)
    return base


def write_wav(path, rate=44100, ch=2, bits=16, tag=1, seconds=1.0, extensible=False,
              valid_bits=None, extra_chunks_before=(), sparse=True, container=b"RIFF",
              truncate_to=None, odd_junk=False):
    align = ch * ((bits + 7) // 8)
    frames = int(round(seconds * rate))
    data_size = frames * align
    body_chunks = b""
    if odd_junk:
        body_chunks += _chunk(b"JUNK", b"abc")  # mida senar + farciment
    for cid, payload in extra_chunks_before:
        body_chunks += _chunk(cid, payload)
    fmt = fmt_body(tag, ch, rate, bits, extensible, valid_bits, cb=0 if tag == 3 and not extensible else None)
    body_chunks += _chunk(b"fmt ", fmt)
    if tag == 3:
        body_chunks += _chunk(b"fact", struct.pack("<I", frames))

    if container == b"RIFF":
        riff_size = 4 + len(body_chunks) + 8 + data_size + (data_size & 1)
        header = b"RIFF" + struct.pack("<I", riff_size & 0xFFFFFFFF) + b"WAVE"
        data_hdr = b"data" + struct.pack("<I", data_size)
    else:
        riff_total = 4 + 36 + len(body_chunks) + 8 + data_size
        ds64 = struct.pack("<QQQI", riff_total, data_size, frames, 0)
        header = container + struct.pack("<I", 0xFFFFFFFF) + b"WAVE" + _chunk(b"ds64", ds64)
        data_hdr = b"data" + struct.pack("<I", 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(header + body_chunks + data_hdr)
        start = f.tell()
        total = data_size if truncate_to is None else truncate_to
        if total > 0:
            if sparse:
                f.seek(start + total - 1)
                f.write(b"\x00")
            else:
                f.write(b"\x00" * total)
    return frames
