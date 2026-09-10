"""Verifica el pegamento de transcribe.py con un WhisperModel simulado.

No necesita modelo ni internet: inyecta un módulo faster_whisper falso.
Uso: python3 tests/test_transcribe_glue.py
"""
import os
import sys
import types
import unittest

DESKTOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, DESKTOP)


class _Seg:
    def __init__(self, start, end, text):
        self.start, self.end, self.text = start, end, text


class _Info:
    language = "es"
    duration = 4.2


class _FakeModel:
    last_kwargs = None

    def __init__(self, name, device=None, compute_type=None):
        self.name, self.device, self.compute_type = name, device, compute_type

    def transcribe(self, path, **kwargs):
        _FakeModel.last_kwargs = {"path": path, **kwargs}
        if kwargs.get("vad_filter"):
            raise RuntimeError("sin onnxruntime (simulado)")
        segs = [_Seg(0.0, 2.0, " hola coma mundo"), _Seg(2.0, 4.0, " punto final")]
        return segs, _Info()


_fake = types.ModuleType("faster_whisper")
_fake.WhisperModel = _FakeModel
sys.modules["faster_whisper"] = _fake

import transcribe  # noqa: E402


class TestGlue(unittest.TestCase):
    def setUp(self):
        transcribe._models.clear()

    def test_join_y_parametros(self):
        res = transcribe.transcribe_file("/tmp/falso.wav", model="base", language="es")
        self.assertEqual(res["text"], "hola coma mundo punto final")
        self.assertEqual(res["language"], "es")
        self.assertEqual(len(res["segments"]), 2)
        # Reintentó sin VAD tras el fallo simulado:
        self.assertFalse(_FakeModel.last_kwargs.get("vad_filter", False))
        self.assertEqual(_FakeModel.last_kwargs["language"], "es")
        self.assertEqual(_FakeModel.last_kwargs["beam_size"], 5)

    def test_modelo_cacheado_y_en_cpu(self):
        m1 = transcribe.get_model("tiny")
        m2 = transcribe.get_model("tiny")
        self.assertIs(m1, m2)
        self.assertEqual(m1.device, "cpu")
        self.assertEqual(m1.compute_type, "int8")

    def test_available(self):
        self.assertTrue(transcribe.available())


if __name__ == "__main__":
    unittest.main(verbosity=2)
