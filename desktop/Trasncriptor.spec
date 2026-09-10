# -*- mode: python ; coding: utf-8 -*-
"""Empaqueta Trasncriptor PC como carpeta portable para Windows.

Se construye solo en GitHub Actions (ver .github/workflows/desktop.yml):
el modelo Whisper se descarga en el primer arranque, no va incluido.
"""
from PyInstaller.utils.hooks import collect_all

datas = [("static", "static")]
binaries = []
hiddenimports = []
for _pkg in ["faster_whisper", "ctranslate2", "tokenizers", "av", "onnxruntime", "huggingface_hub"]:
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["torch", "tensorflow", "scipy"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Trasncriptor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="Trasncriptor",
)
