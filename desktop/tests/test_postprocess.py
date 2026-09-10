"""Tests del procesador de comandos de voz. Sin dependencias: `python3 test_postprocess.py`."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from postprocess import process


class TestProcess(unittest.TestCase):
    def test_coma_y_punto(self):
        self.assertEqual(
            process("hola coma esto es una prueba punto"),
            "Hola, esto es una prueba.",
        )

    def test_punto_y_seguido(self):
        self.assertEqual(
            process("esto es una prueba punto y seguido seguimos coma sin parar punto final"),
            "Esto es una prueba. Seguimos, sin parar.",
        )

    def test_punto_y_aparte(self):
        self.assertEqual(
            process("primer parrafo punto y aparte segundo parrafo punto"),
            "Primer parrafo.\n\nSegundo parrafo.",
        )

    def test_comillas_y_parentesis(self):
        self.assertEqual(
            process("dijo abrir comillas hola cerrar comillas punto"),
            'Dijo "hola".',
        )
        self.assertEqual(
            process("esto abrir parentesis importante cerrar parentesis sigue punto"),
            "Esto (importante) sigue.",
        )

    def test_interrogacion_exclamacion(self):
        self.assertEqual(
            process("abrir interrogacion vienes o no cerrar interrogacion"),
            "¿Vienes o no?",
        )
        self.assertEqual(
            process("abrir exclamacion que alegria cerrar exclamacion"),
            "¡Que alegria!",
        )

    def test_sin_tildes_y_mayusculas(self):
        # El reconocedor a veces quita tildes o cambia mayúsculas.
        self.assertEqual(
            process("primera salto de linea segunda linea punto"),
            "Primera\nSegunda linea.",
        )
        self.assertEqual(
            process("trae dos PUNTOS pan punto y coma queso punto"),
            "Trae: pan; queso.",
        )

    def test_suspensivos_y_nuevo_parrafo(self):
        self.assertEqual(
            process("y entonces puntos suspensivos silencio punto"),
            "Y entonces… silencio.",
        )
        self.assertEqual(
            process("uno punto nuevo parrafo dos punto"),
            "Uno.\n\nDos.",
        )

    def test_modo_literal(self):
        self.assertEqual(
            process("hola coma mundo", apply_commands=False),
            "Hola coma mundo",
        )

    def test_vacio(self):
        self.assertEqual(process(""), "")
        self.assertEqual(process("   "), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
