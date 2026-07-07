// Seymour Wins capture — popup logic. Talks to the local daily_daemon.py.
const DAEMON = "http://127.0.0.1:8770";

function setStatus(msg, ok) {
  const s = document.getElementById("status");
  s.textContent = msg;
  s.style.color = ok ? "#2a7" : "#a33";
}

document.getElementById("send").addEventListener("click", async () => {
  const payload = {
    year: parseInt(document.getElementById("year").value, 10),
    month: parseInt(document.getElementById("month").value, 10),
    day: parseInt(document.getElementById("day").value, 10),
    theme: document.getElementById("theme").value,
    fact: document.getElementById("fact").value.trim(),
    overlap: document.getElementById("overlap").value.trim(),
  };
  if (!payload.fact) { setStatus("fact required", false); return; }
  try {
    const r = await fetch(DAEMON + "/capture", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const j = await r.json();
    if (j.ok) setStatus("Filed: " + j.path, true);
    else setStatus("Error: " + (j.error || "unknown"), false);
  } catch (e) {
    setStatus("Daemon down? start daily_daemon.py", false);
  }
});

// Pre-fill today's date by default
(function () {
  const t = new Date();
  document.getElementById("year").value = t.getFullYear();
  document.getElementById("month").value = t.getMonth() + 1;
  document.getElementById("day").value = t.getDate();
})();
