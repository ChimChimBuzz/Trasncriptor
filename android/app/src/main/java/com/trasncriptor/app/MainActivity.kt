package com.trasncriptor.app

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.SystemClock
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.trasncriptor.app.data.Dictation
import com.trasncriptor.app.data.HistoryStore
import com.trasncriptor.app.speech.DictationManager
import com.trasncriptor.app.text.CommandProcessor
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { TrasncriptorApp() }
    }
}

@Composable
fun TrasncriptorApp() {
    val context = LocalContext.current
    val store = remember { HistoryStore(context.applicationContext) }
    var tab by remember { mutableStateOf(0) }
    var resultText by remember { mutableStateOf("") }
    var editingId by remember { mutableStateOf<String?>(null) }

    MaterialTheme(colorScheme = darkColorScheme()) {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            Column(modifier = Modifier.fillMaxSize()) {
                Box(modifier = Modifier.weight(1f)) {
                    when (tab) {
                        0 -> DictateScreen(
                            store = store,
                            text = resultText,
                            onTextChange = { resultText = it },
                            editingId = editingId,
                            onEditingIdChange = { editingId = it }
                        )
                        else -> HistoryScreen(
                            store = store,
                            onOpen = { item ->
                                editingId = item.id
                                resultText = item.text
                                tab = 0
                            }
                        )
                    }
                }
                NavigationBar {
                    NavigationBarItem(
                        selected = tab == 0,
                        onClick = { tab = 0 },
                        icon = { Icon(Icons.Filled.Mic, contentDescription = "Dictar") },
                        label = { Text("Dictar") }
                    )
                    NavigationBarItem(
                        selected = tab == 1,
                        onClick = { tab = 1 },
                        icon = { Icon(Icons.Filled.List, contentDescription = "Historial") },
                        label = { Text("Historial") }
                    )
                }
            }
        }
    }
}

@Composable
fun DictateScreen(
    store: HistoryStore,
    text: String,
    onTextChange: (String) -> Unit,
    editingId: String?,
    onEditingIdChange: (String?) -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val clipboard = LocalClipboardManager.current

    val recording = remember { mutableStateOf(false) }
    val live = remember { mutableStateOf("") }
    val error = remember { mutableStateOf<String?>(null) }
    val rawChunks = remember { mutableStateListOf<String>() }
    var applyCommands by remember { mutableStateOf(true) }
    var elapsed by remember { mutableStateOf(0L) }

    // Referencias frescas para usar dentro del listener (evita closures obsoletos).
    val applyCommandsRef = rememberUpdatedState(applyCommands)
    val onTextRef = rememberUpdatedState(onTextChange)
    val onEditIdRef = rememberUpdatedState(onEditingIdChange)

    fun consolidate() {
        val raw = rawChunks.joinToString(" ").trim()
        rawChunks.clear()
        live.value = ""
        if (raw.isNotEmpty()) {
            val done = CommandProcessor.process(raw, applyCommandsRef.value)
            onTextRef.value(done)
            onEditIdRef.value(null)
            scope.launch { store.add(done) }
        }
    }

    val manager = remember {
        DictationManager(
            context.applicationContext,
            object : DictationManager.Listener {
                override fun onPartial(t: String) {
                    live.value = t
                }

                override fun onFinal(chunk: String) {
                    rawChunks.add(chunk)
                    live.value = ""
                }

                override fun onError(message: String) {
                    error.value = message
                    if (recording.value) {
                        recording.value = false
                        consolidate()
                    }
                }

                override fun onListening(listening: Boolean) {
                    if (!listening && recording.value) {
                        // Se detuvo tras entregar el último trozo: consolidar.
                        recording.value = false
                        consolidate()
                    }
                }
            }
        )
    }
    DisposableEffect(Unit) { onDispose { manager.destroy() } }

    // Cronómetro mientras se graba.
    LaunchedEffect(recording.value) {
        if (!recording.value) return@LaunchedEffect
        val t0 = SystemClock.elapsedRealtime()
        while (true) {
            elapsed = SystemClock.elapsedRealtime() - t0
            delay(250)
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            startDictation(manager, recording, live, error, rawChunks) { elapsed = 0 }
        } else {
            error.value = "Sin permiso de micrófono no se puede dictar."
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("🎙️ Trasncriptor", style = MaterialTheme.typography.headlineSmall)
        Text(
            "Dicta y di: coma, punto, punto y aparte…",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Spacer(Modifier.height(16.dp))

        Button(
            onClick = {
                if (recording.value) {
                    manager.stop() // la consolidación llega vía onListening(false)
                    scope.launch {
                        // Red de seguridad: si el reconocedor no responde, consolidar igual.
                        delay(3000)
                        if (recording.value) {
                            recording.value = false
                            consolidate()
                        }
                    }
                } else {
                    val ok = ContextCompat.checkSelfPermission(
                        context, Manifest.permission.RECORD_AUDIO
                    ) == PackageManager.PERMISSION_GRANTED
                    if (ok) {
                        startDictation(manager, recording, live, error, rawChunks) { elapsed = 0 }
                    } else {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                }
            },
            modifier = Modifier.size(120.dp),
            shape = CircleShape,
            colors = ButtonDefaults.buttonColors(
                containerColor = if (recording.value) MaterialTheme.colorScheme.error
                else MaterialTheme.colorScheme.primary
            )
        ) {
            Icon(
                if (recording.value) Icons.Filled.Stop else Icons.Filled.Mic,
                contentDescription = if (recording.value) "Detener" else "Dictar",
                modifier = Modifier.size(52.dp)
            )
        }
        Spacer(Modifier.height(8.dp))
        Text(fmtTime(elapsed), style = MaterialTheme.typography.headlineMedium)
        Text(
            if (recording.value) "Escuchando… pulsa para detener y transcribir"
            else "Pulsa el micrófono para empezar",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        if (recording.value && live.value.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text(
                live.value,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary
            )
        }
        error.value?.let {
            Spacer(Modifier.height(8.dp))
            Text(it, color = MaterialTheme.colorScheme.error)
        }

        Spacer(Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Checkbox(checked = applyCommands, onCheckedChange = { applyCommands = it })
            Text("Interpretar coma, punto, punto y aparte…")
        }

        Spacer(Modifier.height(8.dp))
        Text(
            "Transcripción",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(Modifier.height(4.dp))
        OutlinedTextField(
            value = text,
            onValueChange = onTextChange,
            modifier = Modifier
                .fillMaxWidth()
                .heightIn(min = 140.dp),
            placeholder = { Text("Aquí aparecerá lo que dictes…") }
        )
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                onClick = {
                    if (text.isNotEmpty()) {
                        clipboard.setText(AnnotatedString(text))
                        Toast.makeText(context, "Copiado", Toast.LENGTH_SHORT).show()
                    }
                }
            ) { Text("Copiar") }
            OutlinedButton(onClick = { if (text.isNotEmpty()) shareText(context, text) }) {
                Text("Compartir")
            }
        }
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                onClick = {
                    if (text.isBlank()) return@OutlinedButton
                    scope.launch {
                        if (editingId != null) store.update(editingId!!, text)
                        else {
                            store.add(text)
                            onEditingIdChange(null)
                        }
                        Toast.makeText(context, "Guardado", Toast.LENGTH_SHORT).show()
                    }
                }
            ) { Text("Guardar") }
            OutlinedButton(
                onClick = {
                    onEditingIdChange(null)
                    onTextChange("")
                }
            ) { Text("Nuevo") }
        }
        Spacer(Modifier.height(16.dp))
    }
}

private fun startDictation(
    manager: DictationManager,
    recording: androidx.compose.runtime.MutableState<Boolean>,
    live: androidx.compose.runtime.MutableState<String>,
    error: androidx.compose.runtime.MutableState<String?>,
    rawChunks: MutableList<String>,
    onResetTimer: () -> Unit
) {
    rawChunks.clear()
    live.value = ""
    error.value = null
    onResetTimer()
    recording.value = true
    manager.start()
}

@Composable
fun HistoryScreen(store: HistoryStore, onOpen: (Dictation) -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val clipboard = LocalClipboardManager.current
    val items by store.items.collectAsState(initial = emptyList())

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(
            "Historial ${if (items.isNotEmpty()) "(${items.size})" else ""}",
            style = MaterialTheme.typography.titleLarge
        )
        Spacer(Modifier.height(8.dp))
        if (items.isEmpty()) {
            Text(
                "Aún no hay dictados. Todo se guarda solo en este móvil.",
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(items, key = { it.id }) { item ->
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text(
                                item.ts,
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(Modifier.height(4.dp))
                            Text(
                                item.text,
                                maxLines = 4,
                                overflow = TextOverflow.Ellipsis
                            )
                            Spacer(Modifier.height(8.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                OutlinedButton(onClick = { onOpen(item) }) { Text("Abrir") }
                                OutlinedButton(
                                    onClick = {
                                        clipboard.setText(AnnotatedString(item.text))
                                        Toast.makeText(context, "Copiado", Toast.LENGTH_SHORT).show()
                                    }
                                ) { Text("Copiar") }
                                OutlinedButton(
                                    onClick = { scope.launch { store.remove(item.id) } }
                                ) { Text("Borrar") }
                            }
                        }
                    }
                }
            }
        }
    }
}

private fun shareText(context: Context, text: String) {
    context.startActivity(
        Intent.createChooser(
            Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_TEXT, text)
            },
            "Compartir transcripción"
        )
    )
}

private fun fmtTime(ms: Long): String {
    val s = ms / 1000
    return "%02d:%02d".format(s / 60, s % 60)
}
