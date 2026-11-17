# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: genera dist\VinylTracklist.exe (un sol fitxer, sense consola).
# Feu servir Python 3.8 de 32 bits perquè funcioni de Windows 7 a Windows 11.
import os
from PyInstaller.utils.hooks import collect_data_files

datas = [
    (os.path.join("assets", "vinyltracklist.ico"), "assets"),
    (os.path.join("assets", "vinyltracklist.png"), "assets"),
]
# Arrossegar des de l'Explorador (tkdnd): només els binaris de Windows
for src, dst in collect_data_files("tkinterdnd2"):
    low = src.replace("\\", "/").lower()
    if "/osx-" in low or "/linux-" in low or "/win-arm64" in low:
        continue
    datas.append((src, dst))

a = Analysis(
    ["VinylTracklist.pyw"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=["tkinterdnd2", "tkinterdnd2.TkinterDnD"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["numpy", "PIL", "matplotlib", "unittest", "pydoc", "test"],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="VinylTracklist",
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join("assets", "vinyltracklist.ico"),
    version="version_info.txt",
)
