# Trasncriptor Android 🎙️

App nativa (Kotlin + Compose) con dictado continuo y puntuación por voz.
Usa el **reconocedor del dispositivo en modo offline preferente**: gratis,
sin cuentas y sin nube.

## Instalar (sin programar)

1. En GitHub: página de [Releases](../../releases) → descarga `Trasncriptor.apk`.
2. Pasa el APK al móvil, ábrelo y permite "instalar de origen desconocido".

## Dictado 100 % offline (recomendado)

1. En el móvil: **Ajustes → Sistema → Idioma → Voz** (o *Reconocimiento de voz*).
2. Descarga el paquete **Español (España)**.
3. Listo: la app pide `EXTRA_PREFER_OFFLINE` y no tira de red.

Sin el paquete, el sistema usará red como alternativa (igual que el dictado
del teclado de Google).

## Uso

- Pestaña **Dictar**: pulsa el micrófono, habla (di *coma, punto,
  punto y aparte…* — ver [COMANDOS.md](../COMANDOS.md)) y pulsa para detener.
- El texto se procesa y **se guarda solo** en el historial.
- **Copiar / Compartir / Guardar / Nuevo** bajo la transcripción.
- Pestaña **Historial**: abrir, copiar y borrar dictados.

## Compilar desde código

Con [Android Studio](https://developer.android.com/studio) (Hedgehog o superior):

1. *Open* → carpeta `android/`.
2. Deja que sincronice Gradle (descarga dependencias una vez).
3. *Run* para probarla o *Build → Build APK(s)* para el APK.

Por terminal (con JDK 17 + Android SDK):

```bash
gradle :app:testDebugUnitTest :app:assembleDebug
# APK en app/build/outputs/apk/debug/app-debug.apk
```

## Clave de firma

El APK de Releases va firmado con `android/trasncriptor.keystore`, una clave
de **ejemplo incluida en el repo** (alias y contraseñas: `trasncriptor`).
Vale para uso personal y permite actualizar sin desinstalar.

Si vas a publicar la app en serio, genera tu propia clave privada y no la
subas al repositorio:

```bash
keytool -genkeypair -keystore mi-clave.keystore -alias mi-alias \
  -keyalg RSA -keysize 2048 -validity 9125
```

y apunta `storeFile`/`storePassword`/`keyAlias`/`keyPassword` en
`app/build.gradle.kts` a tu clave (mejor con secretos de GitHub Actions).

## Notas técnicas

- `minSdk 26` (Android 8.0+), Compose + Material 3, único permiso: micrófono.
- El reconocedor se detiene en cada pausa: `DictationManager` lo reinicia
  solo y concatena los trozos hasta que pulsas detener.
- `CommandProcessor` implementa la misma [especificación](../COMANDOS.md)
  que el PC y tiene los mismos tests (`CommandProcessorTest`).
- Historial en DataStore local (máx. 300 dictados).

## ¿Por qué no lleva Whisper/GGUF dentro?

Un modelo de voz en el APK pesaría GB y transcribiría muy lento en el móvil.
El reconocedor offline del sistema da el mismo resultado (gratis, privado)
usando el paquete de voz de Android. El PC sí usa Whisper local, donde hay
CPU y disco de sobra.
