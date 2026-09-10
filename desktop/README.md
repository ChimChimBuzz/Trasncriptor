# Trasncriptor PC 🎙️

Dictado offline para Windows, Mac y Linux. El navegador solo pone el
micrófono y los botones: la transcripción la hace **Whisper dentro de tu PC**.

## Puesta en marcha (5 minutos)

1. Instala **Python 3.10 o superior** (marca "Add python to PATH" en Windows).
2. En una terminal, dentro de esta carpeta:
   ```bash
   pip install -r requirements.txt
   python download_models.py        # descarga Whisper 'base' (~150 MB, una vez)
   python app.py
   ```
3. Abre **http://localhost:8765**, pulsa el micrófono y dicta.

> ¿No quieres instalar Python? Descarga `Trasncriptor.exe` (un solo archivo,
> sin instalación) desde la página de [Releases](../../releases): ejecútalo
> y se abrirá solo en tu navegador.

## Modelos Whisper

| Tamaño | Descarga con | Calidad ES | Velocidad (CPU) |
|---|---|---|---|
| `tiny` | `--whisper tiny` | Aceptable | Muy rápido |
| `base` | (por defecto) | Buena | Rápido |
| `small` | `--whisper small` | Muy buena | Medio (~1× tiempo real) |

Cámbialo en la descarga o al vuelo en la propia interfaz.

## Pulido con IA local (opcional)

Corrige gramática y puntuación con un modelo GGUF en tu equipo:

```bash
pip install llama-cpp-python
python download_models.py --gguf   # Qwen 0.5B Q4 (~400 MB, una vez)
```

Luego marca **"Pulir con IA local"** en la interfaz. Sin modelo, la opción
aparece desactivada y todo lo demás funciona igual.

## Uso

- Pulsa el micrófono para empezar y otra vez para detener y transcribir.
- Di los comandos de [COMANDOS.md](../COMANDOS.md): *coma, punto,
  punto y seguido, punto y aparte…*
- Desmarca "Interpretar comandos" si quieres el texto literal.
- **Transcribir archivo**: convierte cualquier audio/vídeo que tengas.
- Historial con copiar, descargar, editar y borrar (se guarda en `data/`).

## Tests

```bash
python tests/test_postprocess.py     # comandos de voz (9 casos)
python tests/test_transcribe_glue.py # pegamento Whisper (simulado)
python tests/test_server.py          # servidor de punta a punta (simulado)
```

## Problemas habituales

- **El navegador no pide micrófono**: usa `localhost`, no la IP.
- **Primera transcripción lenta**: el modelo se carga en memoria una vez.
- **`faster-whisper` falla al instalar**: actualiza pip (`pip install -U pip`).
- **Sin internet el primer día**: descarga los modelos con conexión una vez;
  después todo funciona offline.
