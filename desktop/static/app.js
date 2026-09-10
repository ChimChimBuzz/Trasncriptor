/* Trasncriptor PC — grabación con micrófono + envío al motor local. */
const $ = (id) => document.getElementById(id);
const micBtn = $("micBtn"), timerEl = $("timer"), meterFill = $("meterFill");
const hintEl = $("hint"), busyEl = $("busy"), resultText = $("resultText");
const msgEl = $("msg"), histList = $("histList"), histCount = $("histCount");
const statusEl = $("status"), fileInput = $("fileInput");

let recorder = null, chunks = [], stream = null, timerId = null, startedAt = 0;
let analyser = null, audioCtx = null, currentId = null;

function msg(t) { msgEl.textContent = t; setTimeout(() => { msgEl.textContent = ""; }, 3500); }
function fmtTime(ms) {
  const s = Math.floor(ms / 1000);
  return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
}

async function loadStatus() {
  try {
    const r = await fetch("/api/status");
    const s = await r.json();
    if (s.whisper) {
      statusEl.textContent = "● motor local listo";
      statusEl.className = "status ok";
    } else {
      statusEl.textContent = "● falta faster-whisper (ver README)";
      statusEl.className = "status warn";
    }
    $("footModel").textContent = "modelo: " + (s.model || "?");
    const polish = $("optPolish");
    if (!s.polish) {
      polish.disabled = true;
      $("polishNote").textContent = "(sin modelo GGUF)";
    } else {
      $("polishNote").textContent = "(disponible)";
    }
  } catch {
    statusEl.textContent = "● sin conexión con el servidor";
    statusEl.className = "status warn";
  }
}

async function loadHistory() {
  try {
    const r = await fetch("/api/history");
    const { items } = await r.json();
    histCount.textContent = items.length ? `(${items.length})` : "";
    if (!items.length) {
      histList.innerHTML = '<p class="empty">Aún no hay dictados.</p>';
      return;
    }
    histList.innerHTML = "";
    for (const it of items) {
      const div = document.createElement("div");
      div.className = "hist-item";
      const date = (it.ts || "").replace("T", " ").slice(0, 16);
      div.innerHTML = `<time>${date}${it.polished ? " · ✨ pulido" : ""}</time><p></p>
        <div class="mini">
          <button data-a="open">Abrir</button>
          <button data-a="copy">Copiar</button>
          <button data-a="dl">Descargar</button>
          <button data-a="del">Borrar</button>
        </div>`;
      div.querySelector("p").textContent = it.text;
      div.querySelectorAll("button").forEach((b) => {
        b.onclick = () => histAction(b.dataset.a, it);
      });
      histList.appendChild(div);
    }
  } catch { /* sin servidor */ }
}

async function histAction(a, it) {
  if (a === "open") { currentId = it.id; resultText.value = it.text; msg("Dictado cargado."); }
  if (a === "copy") { await navigator.clipboard.writeText(it.text); msg("Copiado."); }
  if (a === "dl") { window.location = "/api/export?id=" + it.id; }
  if (a === "del" && confirm("¿Borrar este dictado?")) {
    await fetch("/api/history?id=" + it.id, { method: "DELETE" });
    loadHistory();
  }
}

function pickMime() {
  const cands = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
  for (const c of cands) {
    if (window.MediaRecorder && MediaRecorder.isTypeSupported(c)) return c;
  }
  return "";
}

async function startRec() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    alert("No se pudo acceder al micrófono. Revisa los permisos del navegador.");
    return;
  }
  chunks = [];
  const mime = pickMime();
  recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
  recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
  recorder.onstop = onStopped;
  // Medidor de volumen
  try {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    src.connect(analyser);
    drawMeter();
  } catch { /* opcional */ }
  recorder.start();
  startedAt = Date.now();
  timerId = setInterval(() => { timerEl.textContent = fmtTime(Date.now() - startedAt); }, 250);
  micBtn.classList.add("rec");
  hintEl.innerHTML = "Grabando… pulsa de nuevo para <strong>detener y transcribir</strong>.";
}

function drawMeter() {
  if (!analyser) return;
  const data = new Uint8Array(analyser.frequencyBinCount);
  const loop = () => {
    if (!analyser) { meterFill.style.width = "0%"; return; }
    analyser.getByteFrequencyData(data);
    const avg = data.reduce((a, b) => a + b, 0) / data.length;
    meterFill.style.width = Math.min(100, avg * 1.4) + "%";
    requestAnimationFrame(loop);
  };
  loop();
}

function stopRec() {
  clearInterval(timerId);
  if (recorder && recorder.state !== "inactive") recorder.stop();
  if (stream) stream.getTracks().forEach((t) => t.stop());
  if (audioCtx) audioCtx.close().catch(() => {});
  analyser = null; audioCtx = null;
  micBtn.classList.remove("rec");
  hintEl.innerHTML = "Procesando…";
}

async function onStopped() {
  const type = (recorder && recorder.mimeType) || "audio/webm";
  const blob = new Blob(chunks, { type });
  chunks = [];
  await sendAudio(blob, "mic");
  timerEl.textContent = "00:00";
  hintEl.innerHTML = "Pulsa el micrófono y dicta. Di <em>coma</em>, <em>punto</em>, <em>punto y aparte</em>…";
}

async function sendAudio(blob, source) {
  if (!blob.size) { msg("Grabación vacía."); return; }
  busyEl.hidden = false;
  const qs = new URLSearchParams({
    commands: $("optCommands").checked ? "1" : "0",
    polish: $("optPolish").checked ? "1" : "0",
    source,
    model: $("optModel").value,
  });
  try {
    const r = await fetch("/api/transcribe?" + qs, {
      method: "POST",
      headers: { "Content-Type": blob.type || "audio/webm" },
      body: blob,
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "error del servidor");
    currentId = data.record.id;
    resultText.value = data.record.text;
    msg(data.record.polished ? "Transcrito y pulido con IA ✨" : "Transcripción lista ✓");
    loadHistory();
  } catch (e) {
    alert("No se pudo transcribir: " + e.message);
  } finally {
    busyEl.hidden = true;
  }
}

micBtn.onclick = () => {
  if (recorder && recorder.state === "recording") stopRec();
  else startRec();
};

fileInput.onchange = () => {
  if (fileInput.files.length) sendAudio(fileInput.files[0], "archivo");
  fileInput.value = "";
};

$("btnCopy").onclick = async () => {
  if (!resultText.value) return;
  await navigator.clipboard.writeText(resultText.value);
  msg("Copiado al portapapeles.");
};
$("btnDownload").onclick = () => {
  if (currentId) { window.location = "/api/export?id=" + currentId; return; }
  if (!resultText.value) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([resultText.value], { type: "text/plain" }));
  a.download = "trasncriptor.txt";
  a.click();
};
$("btnSaveEdit").onclick = async () => {
  if (!resultText.value.trim()) return;
  if (currentId) {
    await fetch("/api/history", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: currentId, text: resultText.value }),
    });
  } else {
    const r = await fetch("/api/history", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: resultText.value }),
    });
    currentId = (await r.json()).record.id;
  }
  msg("Guardado.");
  loadHistory();
};
$("btnNew").onclick = () => { currentId = null; resultText.value = ""; resultText.focus(); };

loadStatus();
loadHistory();
