package com.trasncriptor.app.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

private val Context.dataStore by preferencesDataStore("trasncriptor")

/** Un dictado guardado en el dispositivo. */
data class Dictation(val id: String, val ts: String, val text: String)

/** Historial local (DataStore). Nada sale del móvil. */
class HistoryStore(private val context: Context) {

    private val key = stringPreferencesKey("history_json")

    val items: Flow<List<Dictation>> = context.dataStore.data.map { prefs ->
        parse(prefs[key] ?: "[]")
    }

    suspend fun add(text: String) {
        val item = Dictation(
            id = UUID.randomUUID().toString().take(8),
            ts = SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault()).format(Date()),
            text = text
        )
        save((listOf(item) + items.first()).take(300))
    }

    suspend fun update(id: String, text: String) {
        save(items.first().map { if (it.id == id) it.copy(text = text) else it })
    }

    suspend fun remove(id: String) {
        save(items.first().filter { it.id != id })
    }

    private suspend fun save(list: List<Dictation>) {
        val arr = JSONArray()
        list.forEach { d ->
            arr.put(JSONObject().put("id", d.id).put("ts", d.ts).put("text", d.text))
        }
        context.dataStore.edit { prefs -> prefs[key] = arr.toString() }
    }

    private fun parse(json: String): List<Dictation> {
        return try {
            val arr = JSONArray(json)
            List(arr.length()) { i ->
                val o = arr.getJSONObject(i)
                Dictation(o.getString("id"), o.getString("ts"), o.getString("text"))
            }
        } catch (_: Exception) {
            emptyList()
        }
    }
}
