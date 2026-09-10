"""Motor de transcripción 100 % local con faster-whisper.

- Gratis, sin cuentas ni claves, funciona sin internet (tras descargar el modelo).
- Solo CPU: usa ctranslate2 en int8, sin necesidad de GPU ni de torch.
"""
from __future__ import annotations

import os
import threading

DEFAULT_MODEL = os.environ.get("TRASNC_MODEL", "base")
LANGUAGE = os.environ.get("TRASNC_LANG", "es")

_models: dict[str, object] = {}
_lock = threading.Lock()


def available() -> bool:
    """True si faster-whisper está instalado."""
    try:
        import faster_whisper  # noqa: F401
        return True
    except Exception:
        return False


def get_model(name: str | None = None):
    """Carga (una sola vez) y devuelve el modelo Whisper indicado."""
    from faster_whisper import WhisperModel

    name = name or DEFAULT_MODEL
    with _lock:
        if name not in _models:
            print(f"[whisper] cargando modelo '{name}' (solo la primera vez tarda)...", flush=True)
            _models[name] = WhisperModel(name, device="cpu", compute_type="int8")
            print("[whisper] modelo listo.", flush=True)
        return _models[name]


def transcribe_file(
    path: str,
    model: str | None = None,
    language: str | None = None,
    beam_size: int = 5,
) -> dict:
    """Transcribe un archivo de audio y devuelve texto + segmentos."""
    language = language or LANGUAGE
    whisper = get_model(model)
    try:
        segments, info = whisper.transcribe(
            path,
            language=language,
            beam_size=beam_size,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
    except Exception:
        # Si el filtro VAD falla (p. ej. falta onnxruntime), reintentar sin él.
        segments, info = whisper.transcribe(path, language=language, beam_size=beam_size)

    segs = [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segments]
    text = " ".join(s["text"] for s in segs).strip()
    return {
        "text": text,
        "language": getattr(info, "language", language),
        "duration": getattr(info, "duration", None),
        "segments": segs,
    }
