if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js");
fetch("/api/health").then(r => r.json()).then(d => document.querySelector("#status").textContent = `Servicio ${d.status} · V${d.version}`).catch(() => document.querySelector("#status").textContent = "Servicio no disponible");
