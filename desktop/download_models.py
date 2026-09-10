#!/usr/bin/env python3
"""Descarga los modelos locales de Trasncriptor (solo se hace una vez).

Uso:
    python3 download_models.py                 # Whisper 'base' (~150 MB, recomendado)
    python3 download_models.py --whisper small # mejor calidad (~500 MB)
    python3 download_models.py --whisper tiny  # rápido, menor calidad (~75 MB)
    python3 download_models.py --gguf          # + modelo GGUF para "pulir con IA" (~400 MB)
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request

try:  # la consola de Windows (cp1252) no acepta todos los caracteres
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GGUF_DIR = os.path.join(BASE_DIR, "models")
GGUF_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
    "qwen2.5-0.5b-instruct-q4_k_m.gguf"
)


def download_whisper(size: str) -> None:
    from faster_whisper import WhisperModel

    print(f"[1/2] Descargando Whisper '{size}'...")
    WhisperModel(size, device="cpu", compute_type="int8")
    print("Whisper listo.")


def _progress(block: int, size: int, total: int) -> None:
    done = block * size
    pct = 100 * done / total if total > 0 else 0
    print(f"\r  {done / 1e6:.0f}/{total / 1e6:.0f} MB ({pct:.0f}%)", end="", flush=True)


def download_gguf() -> None:
    os.makedirs(GGUF_DIR, exist_ok=True)
    dest = os.path.join(GGUF_DIR, os.path.basename(GGUF_URL))
    if os.path.exists(dest) and os.path.getsize(dest) > 100_000_000:
        print(f"GGUF ya descargado: {dest}")
        return
    print("[2/2] Descargando modelo GGUF (~400 MB, puede tardar)...")
    urllib.request.urlretrieve(GGUF_URL, dest, reporthook=_progress)
    print(f"\nGGUF listo: {dest}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--whisper", default="base", help="tiny|base|small|medium")
    parser.add_argument("--gguf", action="store_true", help="descargar también el GGUF de pulido")
    args = parser.parse_args()
    try:
        download_whisper(args.whisper)
    except Exception as exc:
        print(f"ERROR descargando Whisper: {exc}", file=sys.stderr)
        print("¿Instalaste las dependencias? pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    if args.gguf:
        download_gguf()


if __name__ == "__main__":
    main()
