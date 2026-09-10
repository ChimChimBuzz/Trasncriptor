package com.trasncriptor.app

import com.trasncriptor.app.text.CommandProcessor
import org.junit.Assert.assertEquals
import org.junit.Test

/** Mismos casos que desktop/tests/test_postprocess.py (COMANDOS.md). */
class CommandProcessorTest {

    @Test
    fun comaYPunto() {
        assertEquals(
            "Hola, esto es una prueba.",
            CommandProcessor.process("hola coma esto es una prueba punto")
        )
    }

    @Test
    fun puntoYSeguido() {
        assertEquals(
            "Esto es una prueba. Seguimos, sin parar.",
            CommandProcessor.process(
                "esto es una prueba punto y seguido seguimos coma sin parar punto final"
            )
        )
    }

    @Test
    fun puntoYAparte() {
        assertEquals(
            "Primer parrafo.\n\nSegundo parrafo.",
            CommandProcessor.process("primer parrafo punto y aparte segundo parrafo punto")
        )
    }

    @Test
    fun comillasYParentesis() {
        assertEquals(
            "Dijo \"hola\".",
            CommandProcessor.process("dijo abrir comillas hola cerrar comillas punto")
        )
        assertEquals(
            "Esto (importante) sigue.",
            CommandProcessor.process("esto abrir parentesis importante cerrar parentesis sigue punto")
        )
    }

    @Test
    fun interrogacionExclamacion() {
        assertEquals(
            "¿Vienes o no?",
            CommandProcessor.process("abrir interrogacion vienes o no cerrar interrogacion")
        )
        assertEquals(
            "¡Que alegria!",
            CommandProcessor.process("abrir exclamacion que alegria cerrar exclamacion")
        )
    }

    @Test
    fun ignoraTildesYMayusculas() {
        assertEquals(
            "Primera\nSegunda linea.",
            CommandProcessor.process("primera salto de linea segunda linea punto")
        )
        assertEquals(
            "Trae: pan; queso.",
            CommandProcessor.process("trae dos PUNTOS pan punto y coma queso punto")
        )
    }

    @Test
    fun suspensivosYNuevoParrafo() {
        assertEquals(
            "Y entonces… silencio.",
            CommandProcessor.process("y entonces puntos suspensivos silencio punto")
        )
        assertEquals(
            "Uno.\n\nDos.",
            CommandProcessor.process("uno punto nuevo parrafo dos punto")
        )
    }

    @Test
    fun modoLiteral() {
        assertEquals(
            "Hola coma mundo",
            CommandProcessor.process("hola coma mundo", applyCommands = false)
        )
    }
}
