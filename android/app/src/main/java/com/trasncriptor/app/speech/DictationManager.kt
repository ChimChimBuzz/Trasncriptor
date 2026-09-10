package com.trasncriptor.app.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer

/**
 * Dictado continuo con el reconocedor del dispositivo.
 * Pide modo offline (EXTRA_PREFER_OFFLINE): gratis y sin red si el móvil
 * tiene descargado el paquete de voz español (Ajustes → Idioma → Voz).
 * Como el reconocedor se detiene en cada pausa, se reinicia solo hasta
 * que el usuario pulsa detener.
 */
class DictationManager(
    private val context: Context,
    private val listener: Listener
) {

    interface Listener {
        fun onPartial(text: String)
        fun onFinal(chunk: String)
        fun onError(message: String)
        fun onListening(listening: Boolean)
    }

    private var recognizer: SpeechRecognizer? = null
    private var wantListening = false

    fun start() {
        if (!SpeechRecognizer.isRecognitionAvailable(context)) {
            listener.onError("Reconocimiento de voz no disponible en este dispositivo.")
            return
        }
        wantListening = true
        listen()
    }

    fun stop() {
        wantListening = false
        try {
            recognizer?.stopListening()
        } catch (_: Exception) {
        }
        listener.onListening(false)
    }

    fun destroy() {
        stop()
        try {
            recognizer?.destroy()
        } catch (_: Exception) {
        }
        recognizer = null
    }

    private fun listen() {
        if (!wantListening) return
        if (recognizer == null) {
            recognizer = SpeechRecognizer.createSpeechRecognizer(context).apply {
                setRecognitionListener(recognitionListener)
            }
        }
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, "es-ES")
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_PREFER_OFFLINE, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }
        try {
            recognizer?.startListening(intent)
            listener.onListening(true)
        } catch (e: Exception) {
            listener.onError("No se pudo iniciar: ${e.message}")
        }
    }

    private val recognitionListener = object : RecognitionListener {
        override fun onResults(results: Bundle) {
            val text = results
                .getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()?.trim().orEmpty()
            if (text.isNotEmpty()) listener.onFinal(text)
            if (wantListening) listen() else listener.onListening(false)
        }

        override fun onPartialResults(partial: Bundle) {
            val text = partial
                .getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                ?.firstOrNull()?.trim().orEmpty()
            listener.onPartial(text)
        }

        override fun onError(error: Int) {
            if (!wantListening) {
                listener.onListening(false)
                return
            }
            // Errores recuperables (silencio, sin coincidencia): seguir escuchando.
            if (error == SpeechRecognizer.ERROR_NO_MATCH ||
                error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT
            ) {
                listen()
                return
            }
            wantListening = false
            listener.onListening(false)
            listener.onError(
                when (error) {
                    SpeechRecognizer.ERROR_AUDIO -> "Error de audio del micrófono."
                    SpeechRecognizer.ERROR_CLIENT -> "Error interno del cliente."
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS ->
                        "Falta el permiso de micrófono."
                    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT ->
                        "Sin conexión y sin paquete de voz offline. Descarga el español en Ajustes → Idioma → Voz."
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Reconocedor ocupado, reintenta."
                    SpeechRecognizer.ERROR_SERVER -> "Error del servidor de voz."
                    else -> "Error $error al reconocer voz."
                }
            )
        }

        override fun onReadyForSpeech(params: Bundle) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray) {}
        override fun onEndOfSpeech() {}
        override fun onEvent(eventType: Int, params: Bundle) {}
    }
}
