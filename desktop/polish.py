"""Pulido opcional del texto con un modelo GGUF en local (llama-cpp-python).

Si no hay modelo GGUF descargado o la librería no está instalada, la app
funciona igual pero sin esta mejora. Ver download_models.py --gguf.
"""
from __future__ import annotations

import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.environ.get("TRASNC_GGUF_DIR", os.path.join(BASE_DIR, "models"))

_llm = None


def find_gguf() -> str | None:
    """Ruta del primer .gguf encontrado, o None."""
    matches = sorted(glob.glob(os.path.join(MODEL_DIR, "*.gguf")))
    return matches[0] if matches else None


def available() -> bool:
    """True si se puede pulir con IA local (librería + modelo)."""
    try:
        import llama_cpp  # noqa: F401
    except Exception:
        return False
    return find_gguf() is not None


def _get_llm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama

        path = find_gguf()
        if path is None:
            raise RuntimeError("No hay modelo .gguf en " + MODEL_DIR)
        print(f"[gguf] cargando {os.path.basename(path)}...", flush=True)
        _llm = Llama(model_path=path, n_ctx=2048, n_threads=os.cpu_count() or 4, verbose=False)
        print("[gguf] modelo listo.", flush=True)
    return _llm


PROMPT = (
    "Corrige la gramática, la ortografía y la puntuación del siguiente texto en español, "
    "sin cambiar su significado, sin añadir información y sin explicaciones. "
    "Devuelve SOLO el texto corregido.\n\nTexto: {text}\n\nCorregido:"
)


def polish(text: str, max_tokens: int = 512) -> str:
    """Devuelve el texto pulido, o el original si algo falla."""
    text = (text or "").strip()
    if not text:
        return text
    try:
        llm = _get_llm()
        out = llm(PROMPT.format(text=text), max_tokens=max_tokens, temperature=0.2, stop=["\n\nTexto:"])
        fixed = out["choices"][0]["text"].strip().strip('"').strip()
        return fixed or text
    except Exception as exc:  # nunca romper la app por el pulido
        print(f"[gguf] aviso: no se pudo pulir ({exc})", flush=True)
        return text
