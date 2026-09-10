"""Test integral del servidor HTTP con motor de transcripción simulado.

Verifica de punta a punta: subir audio → transcribir → comandos de voz →
historial → exportar → borrar. Solo usa la librería estándar.
Uso: python3 tests/test_server.py
"""
import json
import math
import os
import struct
import sys
import threading
import urllib.request
import wave

DESKTOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DESKTOP)

FAKE_TEXT = "hola coma esto es una prueba punto y seguido seguimos punto final"
EXPECTED = "Hola, esto es una prueba. Seguimos."
PORT = 18765
BASE = f"http://127.0.0.1:{PORT}"

import app as server_app  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402


def _fake_transcribe(path, model=None, language=None, beam_size=5):
    assert os.path.exists(path), "el servidor debe guardar el audio subido"
    assert os.path.getsize(path) > 1000, "el audio debe llegar completo"
    return {"text": FAKE_TEXT, "language": "es", "duration": 2.0, "segments": []}


class _FakeEngine:
    DEFAULT_MODEL = "tiny-test"

    @staticmethod
    def transcribe_file(*args, **kwargs):
        return _fake_transcribe(*args, **kwargs)


def _beep_wav(path: str) -> None:
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * 440 * i / 16000)))
            for i in range(16000 * 2)
        )
        wf.writeframes(frames)


def _req(method: str, path: str, body: bytes | None = None, ctype: str | None = None):
    req = urllib.request.Request(BASE + path, data=body, method=method)
    if ctype:
        req.add_header("Content-Type", ctype)
    with urllib.request.urlopen(req) as res:
        raw = res.read()
    try:
        return res.status, json.loads(raw)
    except json.JSONDecodeError:
        return res.status, raw


def main() -> None:
    server_app.engine = _FakeEngine()
    server_app.WHISPER_OK = True
    server_app.HISTORY_PATH = "/tmp/trasnc_test_history.json"
    if os.path.exists(server_app.HISTORY_PATH):
        os.unlink(server_app.HISTORY_PATH)

    server = ThreadingHTTPServer(("127.0.0.1", PORT), server_app.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 1. estado
    status, data = _req("GET", "/api/status")
    assert status == 200 and data["whisper"] is True, data
    print("✓ /api/status")

    # 2. transcribir un wav real (pitido) → comandos aplicados
    _beep_wav("/tmp/trasnc_beep.wav")
    with open("/tmp/trasnc_beep.wav", "rb") as fh:
        audio = fh.read()
    status, data = _req("POST", "/api/transcribe?commands=1&source=mic", audio, "audio/wav")
    assert status == 200, data
    assert data["record"]["text"] == EXPECTED, data["record"]["text"]
    assert data["record"]["raw"] == FAKE_TEXT
    rid = data["record"]["id"]
    print(f"✓ /api/transcribe → {data['record']['text']!r}")

    # 3. modo literal (sin comandos)
    status, data = _req("POST", "/api/transcribe?commands=0", audio, "audio/wav")
    assert data["record"]["text"] == "Hola coma esto es una prueba punto y seguido seguimos punto final", data
    print("✓ modo literal")

    # 4. historial + exportar + editar + borrar
    status, data = _req("GET", "/api/history")
    assert len(data["items"]) == 2, data
    status, txt = _req("GET", f"/api/export?id={rid}")
    assert txt.decode() == EXPECTED
    status, data = _req("PUT", "/api/history",
                         json.dumps({"id": rid, "text": "Editado."}).encode(), "application/json")
    assert data["record"]["text"] == "Editado."
    status, data = _req("DELETE", f"/api/history?id={rid}")
    assert len(data["items"]) == 1
    print("✓ historial / exportar / editar / borrar")

    # 5. portada e interfaz
    status, html = _req("GET", "/")
    assert b"Trasncriptor" in html and b"micBtn" in html
    print("✓ interfaz web")

    server.shutdown()
    os.unlink("/tmp/trasnc_beep.wav")
    os.unlink(server_app.HISTORY_PATH)
    print("\nTODO OK — servidor verificado de punta a punta.")


if __name__ == "__main__":
    main()
