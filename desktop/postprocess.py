"""Interpreta los comandos de voz de puntuación (español).

Implementa la especificación compartida de COMANDOS.md, igual que la app
Android (CommandProcessor.kt). Sin dependencias externas.
"""
from __future__ import annotations

import re
import unicodedata

# (frase de comando SIN tildes y en minúsculas, símbolo que produce)
# Ordenados de frase más larga a más corta para coincidencia greedy.
COMMANDS: list[tuple[str, str]] = [
    ("puntos suspensivos", "…"),
    ("punto y a parte", ".\n\n"),
    ("punto y aparte", ".\n\n"),
    ("punto y seguido", ". "),
    ("signo de interrogacion", "?"),
    ("signo de exclamacion", "!"),
    ("abrir interrogacion", "¿"),
    ("cerrar interrogacion", "?"),
    ("abrir exclamacion", "¡"),
    ("cerrar exclamacion", "!"),
    ("abrir admiracion", "¡"),
    ("cerrar admiracion", "!"),
    ("abrir parentesis", "("),
    ("cerrar parentesis", ")"),
    ("abrir comillas", '"'),
    ("cerrar comillas", '"'),
    ("punto seguido", ". "),
    ("punto aparte", ".\n\n"),
    ("punto a parte", ".\n\n"),
    ("punto final", "."),
    ("punto y coma", ";"),
    ("dos puntos", ":"),
    ("salto de linea", "\n"),
    ("nueva linea", "\n"),
    ("nuevo parrafo", "\n\n"),
    ("coma", ","),
    ("punto", "."),
    ("guion", "-"),
]

_MAX_WORDS = max(len(cmd.split()) for cmd, _ in COMMANDS)
_BY_PHRASE = {cmd: sym for cmd, sym in COMMANDS}

_OPENERS = "¿¡«(\""
_CLOSERS = ",.;:?!…»)"


def _norm(word: str) -> str:
    """Minúsculas sin tildes para comparar comandos."""
    word = unicodedata.normalize("NFD", word.lower())
    return "".join(c for c in word if unicodedata.category(c) != "Mn")


def _fix_quotes(text: str) -> str:
    """Las comillas rectas son iguales al abrir y cerrar: se alternan."""
    parts = text.split('"')
    if len(parts) < 2:
        return text
    out = [parts[0]]
    for i in range(1, len(parts)):
        if i % 2 == 1:  # comilla de apertura
            out[-1] = out[-1].rstrip()
            if out[-1] and not out[-1].endswith(("\n", "(", "¿", "¡", "«")):
                out[-1] += " "
            out.append(parts[i].lstrip())
        else:  # comilla de cierre
            out[-1] = out[-1].rstrip()
            out.append(parts[i])
    result = out[0]
    for chunk in out[1:]:
        result += '"' + chunk
    return result


def _fix_spacing(text: str) -> str:
    text = _fix_quotes(text)
    # Sin espacio antes de signos de cierre.
    text = re.sub(r"\s+([,.;:?!…»”\)\]])", r"\1", text)
    # Sin espacio después de signos de apertura.
    text = re.sub(r"([¿¡«“\(\[])\s+", r"\1", text)
    # Un espacio después de , ; : cuando sigue una letra/número.
    text = re.sub(r"([,;:])([^\s\d])", r"\1 \2", text)
    # Colapsar espacios horizontales.
    text = re.sub(r"[ \t\u00a0]+", " ", text)
    # Limpiar espacios alrededor de saltos de línea y limitar a 2 seguidos.
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _capitalize(text: str) -> str:
    lower = "a-záéíóúñüàèìòùâêîôûäëïöüç"
    # Primera letra del texto (tolerando aperturas: ¿ " ( «).
    text = re.sub(
        rf"^([\s{_OPENERS}\-]*)([{lower}])",
        lambda m: m.group(1) + m.group(2).upper(),
        text,
        count=1,
    )
    # Después de . ? ! (los suspensivos … continúan la frase: sin mayúscula)
    # y después de salto de línea.
    text = re.sub(
        rf"([.?!]\s*[{_OPENERS}\-]*)([{lower}])",
        lambda m: m.group(1) + m.group(2).upper(),
        text,
    )
    text = re.sub(
        rf"(\n\s*[{_OPENERS}\-]*)([{lower}])",
        lambda m: m.group(1) + m.group(2).upper(),
        text,
    )
    return text


def process(text: str, apply_commands: bool = True) -> str:
    """Aplica comandos de voz, espaciado y mayúsculas al texto dictado."""
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return ""
    if not apply_commands:
        return _capitalize(text)

    tokens = text.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        matched = False
        for n in range(min(_MAX_WORDS, len(tokens) - i), 0, -1):
            phrase = " ".join(_norm(t) for t in tokens[i : i + n])
            symbol = _BY_PHRASE.get(phrase)
            if symbol is not None:
                out.append(symbol)
                i += n
                matched = True
                break
        if not matched:
            out.append(tokens[i])
            i += 1

    return _capitalize(_fix_spacing(" ".join(out)))
