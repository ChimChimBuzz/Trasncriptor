# COMANDOS DE VOZ — Especificación compartida (v1)

Tanto la app de PC (`desktop/postprocess.py`) como la de Android
(`android/.../CommandProcessor.kt`) implementan **exactamente** esta tabla.

## Reglas generales

1. La comparación ignora mayúsculas/minúsculas y tildes
   (`línea` = `linea`, `Punto` = `punto`).
2. Se reconoce la coincidencia **más larga primero**
   (`punto y aparte` gana a `punto`).
3. Tras sustituir, se arreglan los espacios (sin espacio antes de `, . ; : ? !`,
   con espacio después) y se ponen mayúsculas al inicio y después de
   `.` `?` `!` y saltos de línea.
4. Si el usuario desactiva "interpretar comandos", el texto se devuelve
   tal cual (solo se recortan espacios sobrantes).

## Tabla de comandos (español)

| Lo que dices | Símbolo | Notas |
|---|---|---|
| `coma` | `,` | |
| `punto` | `.` | |
| `punto y seguido` / `punto seguido` | `. ` | Mayúscula automática en lo siguiente |
| `punto y aparte` / `punto aparte` / `punto y a parte` | `.\n\n` | Nuevo párrafo |
| `punto final` | `.` | |
| `puntos suspensivos` | `…` | |
| `dos puntos` | `:` | |
| `punto y coma` | `;` | |
| `nueva línea` / `salto de línea` | `\n` | |
| `nuevo párrafo` | `\n\n` | |
| `abrir paréntesis` / `cerrar paréntesis` | `(` `)` | |
| `abrir comillas` / `cerrar comillas` | `"` `"` | Comillas rectas (compatibles) |
| `abrir interrogación` | `¿` | |
| `cerrar interrogación` / `signo de interrogación` | `?` | |
| `abrir exclamación` / `abrir admiración` | `¡` | |
| `cerrar exclamación` / `cerrar admiración` / `signo de exclamación` | `!` | |
| `guion` | `-` | Para listas o diálogos |

## Ejemplos

- Dices: `hola coma esto es una prueba punto y seguido seguimos punto final`
  Obtienes: `Hola, esto es una prueba. Seguimos.`
- Dices: `primer párrafo punto y aparte segundo párrafo punto`
  Obtienes:
  ```
  Primer párrafo.

  Segundo párrafo.
  ```
- Dices: `dijo abrir comillas hola cerrar comillas punto`
  Obtienes: `Dijo "hola".`
