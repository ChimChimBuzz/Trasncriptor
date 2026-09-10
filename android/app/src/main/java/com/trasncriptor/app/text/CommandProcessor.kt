package com.trasncriptor.app.text

import java.text.Normalizer

/**
 * Interpreta los comandos de voz de puntuación (español).
 * Implementa la especificación compartida de COMANDOS.md, igual que el PC (postprocess.py).
 * Kotlin puro: sin dependencias de Android, para poder probarlo en la JVM.
 */
object CommandProcessor {

    // (frase SIN tildes en minúsculas, símbolo). Orden: frase más larga primero.
    private val COMMANDS: List<Pair<String, String>> = listOf(
        "puntos suspensivos" to "…",
        "punto y a parte" to ".\n\n",
        "punto y aparte" to ".\n\n",
        "punto y seguido" to ". ",
        "signo de interrogacion" to "?",
        "signo de exclamacion" to "!",
        "abrir interrogacion" to "¿",
        "cerrar interrogacion" to "?",
        "abrir exclamacion" to "¡",
        "cerrar exclamacion" to "!",
        "abrir admiracion" to "¡",
        "cerrar admiracion" to "!",
        "abrir parentesis" to "(",
        "cerrar parentesis" to ")",
        "abrir comillas" to "\"",
        "cerrar comillas" to "\"",
        "punto seguido" to ". ",
        "punto aparte" to ".\n\n",
        "punto a parte" to ".\n\n",
        "punto final" to ".",
        "punto y coma" to ";",
        "dos puntos" to ":",
        "salto de linea" to "\n",
        "nueva linea" to "\n",
        "nuevo parrafo" to "\n\n",
        "coma" to ",",
        "punto" to ".",
        "guion" to "-"
    )
    private val BY_PHRASE: Map<String, String> = COMMANDS.toMap()
    private const val MAX_WORDS = 3
    private val MARK = Regex("\\p{Mn}+")
    private const val OPENERS = "¿¡«(\""
    private const val LOWER = "a-záéíóúñüàèìòùâêîôûäëïöüç"

    private fun norm(word: String): String =
        MARK.replace(Normalizer.normalize(word.lowercase(), Normalizer.Form.NFD), "")

    fun process(text: String, applyCommands: Boolean = true): String {
        var t = text.replace(Regex("\\s+"), " ").trim()
        if (t.isEmpty()) return ""
        if (!applyCommands) return capitalize(t)

        val tokens = t.split(" ")
        val out = mutableListOf<String>()
        var i = 0
        while (i < tokens.size) {
            var matched = false
            var n = minOf(MAX_WORDS, tokens.size - i)
            while (n >= 1) {
                val phrase = tokens.subList(i, i + n).joinToString(" ") { norm(it) }
                val symbol = BY_PHRASE[phrase]
                if (symbol != null) {
                    out.add(symbol)
                    i += n
                    matched = true
                    break
                }
                n--
            }
            if (!matched) {
                out.add(tokens[i])
                i++
            }
        }
        return capitalize(fixSpacing(out.joinToString(" ")))
    }

    /** Las comillas rectas son iguales al abrir y cerrar: se alternan. */
    private fun fixQuotes(text: String): String {
        val parts = text.split("\"")
        if (parts.size < 2) return text
        val out = mutableListOf(parts[0])
        for (i in 1 until parts.size) {
            if (i % 2 == 1) { // apertura
                var prev = out.last().trimEnd()
                if (prev.isNotEmpty() && !prev.endsWith("\n") && !prev.endsWith("(") &&
                    !prev.endsWith("¿") && !prev.endsWith("¡") && !prev.endsWith("«")
                ) {
                    prev += " "
                }
                out[out.lastIndex] = prev
                out.add(parts[i].trimStart())
            } else { // cierre
                out[out.lastIndex] = out.last().trimEnd()
                out.add(parts[i])
            }
        }
        return out.joinToString("\"")
    }

    private fun fixSpacing(text: String): String {
        var t = fixQuotes(text)
        t = t.replace(Regex("\\s+([,.;:?!…»”\\)\\]])"), "$1")
        t = t.replace(Regex("([¿¡«“\\[(])\\s+"), "$1")
        t = t.replace(Regex("([,;:])([^\\s\\d])"), "$1 $2")
        t = t.replace(Regex("[ \\t\\u00a0]+"), " ")
        t = t.replace(Regex(" *\\n *"), "\n")
        t = t.replace(Regex("\\n{3,}"), "\n\n")
        return t.trim()
    }

    private fun capitalize(text: String): String {
        var t = text
        // Primera letra (tolerando aperturas: ¿ " ( «).
        t = Regex("^[\\s$OPENERS\\-]*([$LOWER])").replaceFirst(t) { m ->
            m.value.dropLast(1) + m.groupValues[1].uppercase()
        }
        // Después de . ? ! (los suspensivos … continúan la frase).
        t = Regex("([.?!]\\s*[$OPENERS\\-]*)([$LOWER])").replace(t) { m ->
            m.groupValues[1] + m.groupValues[2].uppercase()
        }
        // Después de salto de línea.
        t = Regex("(\\n\\s*[$OPENERS\\-]*)([$LOWER])").replace(t) { m ->
            m.groupValues[1] + m.groupValues[2].uppercase()
        }
        return t
    }
}
