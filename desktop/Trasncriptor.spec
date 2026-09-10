# -*- mode: python ; coding: utf-8 -*-
"""Empaqueta Trasncriptor PC como UN SOLO .exe para Windows.

- Un único archivo Trasncriptor.exe (sin carpetas ni consola negra).
- Al ejecutarlo abre el navegador solo; el modelo Whisper se descarga
  en el primer uso (después funciona offline).
- Se construye en GitHub Actions (workflows desktop.yml y release.yml).
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
    a.binaries,
    a.zipfiles,
    a.datas,
    name="Trasncriptor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # sin ventana negra: es un programa "normal"
    disable_windowed_traceback=False,
)
