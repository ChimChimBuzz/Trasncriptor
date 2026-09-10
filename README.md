# 🎙️ Trasncriptor

Dicta con un botón y recibe la transcripción con la puntuación puesta.
**Gratis, sin cuentas, sin claves y sin que tu voz salga de tus dispositivos.**

Di literalmente `coma`, `punto`, `punto y seguido`, `punto y aparte`…
y la app escribe `,` `.` `.` `¶`. Tabla completa en [COMANDOS.md](COMANDOS.md).

## Las dos apps

| | PC (Windows / Mac / Linux) | Móvil (Android) |
|---|---|---|
| Motor | Whisper en local (offline tras descargar el modelo) | Reconocimiento de voz del dispositivo (offline con paquete español) |
| Extra | Pulido opcional con modelo GGUF local | — |
| Historial | Guardado local, copiar / descargar / borrar | Guardado local, copiar / compartir / borrar |
| Instrucciones | [desktop/README.md](desktop/README.md) | [android/README.md](android/README.md) |

## Conseguirlas sin instalar nada técnico

Cada vez que se sube código, GitHub **compila automáticamente**:

- El **APK de Android**: pestaña *Actions* → *Android (tests + APK)* →
  última ejecución en verde → *Artifacts* → `Trasncriptor-debug-apk`.
  Pásalo al móvil e instálalo (permite "instalar de origen desconocido").
- El **programa de Windows**: *Actions* → *PC (tests + programa Windows)* →
  *Artifacts* → `Trasncriptor-windows`. Descomprime y ejecuta `Trasncriptor.exe`.

En el PC también puedes usarla directamente con Python (más ligero):
ver [desktop/README.md](desktop/README.md).

## Privacidad

- PC: el audio se transcribe dentro de tu equipo con Whisper local.
- Android: usa el reconocedor del sistema en modo offline preferente.
- El historial vive en archivos locales (`desktop/data/`, memoria de la app).
  Nada se envía a ningún servidor.

## Desarrollo

```text
Trasncriptor/
├── COMANDOS.md          # especificación compartida de comandos de voz
├── desktop/             # app PC: Python + Whisper local + interfaz web offline
│   ├── app.py           # servidor local (solo librería estándar)
│   ├── transcribe.py    # motor faster-whisper (CPU)
│   ├── postprocess.py   # comandos de voz → puntuación
│   ├── polish.py        # pulido opcional con GGUF (llama-cpp-python)
│   ├── static/          # interfaz (sin CDNs: funciona offline)
│   └── tests/           # 3 suites de tests
└── android/             # app Android nativa (Kotlin + Compose)
    └── app/src/main/java/com/trasncriptor/app/
        ├── MainActivity.kt        # UI: dictar + historial
        ├── speech/DictationManager.kt  # reconocedor offline continuo
        ├── text/CommandProcessor.kt    # mismos comandos que el PC
        └── data/HistoryStore.kt        # historial local
```

Licencia MIT — úsala y modifícala a tu gusto.
