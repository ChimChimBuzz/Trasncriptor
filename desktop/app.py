#!/usr/bin/env python3
"""Trasncriptor PC — servidor local con transcripción offline (Whisper).

Uso:
    pip install -r requirements.txt
    python3 download_models.py
    python3 app.py
    # abre http://localhost:8765 en tu navegador

Sin dependencias web externas: el servidor usa solo la librería estándar.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import tempfile
import traceback
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_PATH = os.path.join(DATA_DIR, "history.json")
MAX_UPLOAD = 32 * 1024 * 1024  # 32 MB

from postprocess import process as apply_commands  # noqa: E402

try:
    import transcribe as engine

    WHISPER_OK = engine.available()
except Exception as exc:  # pragma: no cover
    print(f"[aviso] faster-whisper no disponible: {exc}", flush=True)
    engine = None  # type: ignore
    WHISPER_OK = False

try:
    import polish as polisher

    POLISH_OK = polisher.available()
except Exception:  # pragma: no cover
    polisher = None  # type: ignore
    POLISH_OK = False

EXT_BY_TYPE = {
    "audio/webm": ".webm",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
}


# ----------------------------- historial -----------------------------

def _load_history() -> list[dict]:
    try:
        with open(HISTORY_PATH, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_history(items: list[dict]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as fh:
        json.dump(items[:500], fh, ensure_ascii=False, indent=2)


def _add_record(text: str, raw: str, **extra) -> dict:
    items = _load_history()
    record = {
        "id": uuid.uuid4().hex[:8],
        "ts": datetime.now().isoformat(timespec="seconds"),
        "text": text,
        "raw": raw,
        **extra,
    }
    items.insert(0, record)
    _save_history(items)
    return record


# ----------------------------- servidor -----------------------------

class Handler(BaseHTTPRequestHandler):
    server_version = "Trasncriptor/1.0"

    def log_message(self, fmt, *args):  # log compacto
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}", flush=True)

    def _send_json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, name: str) -> None:
        name = os.path.basename(name) or "index.html"
        path = os.path.join(STATIC_DIR, name)
        if not os.path.isfile(path):
            self.send_error(404, "No encontrado")
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if path.endswith(".html"):
            ctype = "text/html; charset=utf-8"
        with open(path, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path in ("/", "/index.html"):
            return self._serve_static("index.html")
        if parsed.path in ("/app.js", "/styles.css", "/favicon.ico"):
            return self._serve_static(parsed.path.lstrip("/"))
        if parsed.path == "/api/status":
            return self._send_json(
                {
                    "whisper": WHISPER_OK,
                    "model": getattr(engine, "DEFAULT_MODEL", None),
                    "polish": POLISH_OK,
                    "history_count": len(_load_history()),
                }
            )
        if parsed.path == "/api/history":
            return self._send_json({"items": _load_history()})
        if parsed.path == "/api/export":
            rid = (qs.get("id") or [""])[0]
            for item in _load_history():
                if item.get("id") == rid:
                    body = item.get("text", "").encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header(
                        "Content-Disposition",
                        f'attachment; filename="trasncriptor-{rid}.txt"',
                    )
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
            return self._send_json({"error": "no existe ese dictado"}, 404)
        return self.send_error(404, "No encontrado")

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/transcribe":
            return self._handle_transcribe(parse_qs(parsed.query))
        if parsed.path == "/api/history":
            return self._handle_save()
        return self.send_error(404, "No encontrado")

    def do_PUT(self):  # noqa: N802
        if urlparse(self.path).path == "/api/history":
            return self._handle_update()
        return self.send_error(404, "No encontrado")

    def do_DELETE(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/history":
            rid = (parse_qs(parsed.query).get("id") or [""])[0]
            items = [i for i in _load_history() if i.get("id") != rid]
            _save_history(items)
            return self._send_json({"ok": True, "items": items})
        return self.send_error(404, "No encontrado")

    # -- acciones --

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_UPLOAD:
            raise ValueError("audio vacío o demasiado grande (máx. 32 MB)")
        return self.rfile.read(length)

    def _handle_transcribe(self, qs: dict) -> None:
        if not WHISPER_OK or engine is None:
            return self._send_json(
                {"error": "faster-whisper no está instalado. Ejecuta: pip install -r requirements.txt"},
                500,
            )
        try:
            body = self._read_body()
        except ValueError as exc:
            return self._send_json({"error": str(exc)}, 400)

        ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
        ext = EXT_BY_TYPE.get(ctype, ".webm")
        use_commands = (qs.get("commands") or ["1"])[0] != "0"
        use_polish = (qs.get("polish") or ["0"])[0] == "1"
        model = (qs.get("model") or [None])[0] or None
        source = (qs.get("source") or ["mic"])[0]

        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        try:
            tmp.write(body)
            tmp.close()
            result = engine.transcribe_file(tmp.name, model=model)
        except Exception as exc:
            traceback.print_exc()
            return self._send_json({"error": f"no se pudo transcribir: {exc}"}, 500)
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

        raw = result.get("text", "")
        text = apply_commands(raw, apply_commands=use_commands)
        polished = False
        if use_polish and polisher is not None and POLISH_OK and text:
            text = polisher.polish(text)
            polished = True
        record = _add_record(
            text, raw, duration=result.get("duration"), source=source, polished=polished
        )
        self._send_json({"ok": True, "record": record, "segments": result.get("segments", [])})

    def _handle_save(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send_json({"error": "petición inválida"}, 400)
        text = (payload.get("text") or "").strip()
        if not text:
            return self._send_json({"error": "texto vacío"}, 400)
        return self._send_json({"ok": True, "record": _add_record(text, "", source="text")})

    def _handle_update(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            return self._send_json({"error": "petición inválida"}, 400)
        rid, text = payload.get("id"), (payload.get("text") or "").strip()
        items = _load_history()
        for item in items:
            if item.get("id") == rid:
                item["text"] = text
                _save_history(items)
                return self._send_json({"ok": True, "record": item})
        return self._send_json({"error": "no existe ese dictado"}, 404)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trasncriptor PC — dictado offline")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"\n🎙️  Trasncriptor listo → http://{args.host}:{args.port}")
    print("   Pulsa Ctrl+C para detener.\n", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n¡Hasta luego!")


if __name__ == "__main__":
    main()
