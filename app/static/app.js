// Countdowns, the board clock, the note counter, and live refresh while a report is processing.

function pad(n) {
  return String(n).padStart(2, "0");
}

function tick() {
  for (const el of document.querySelectorAll("[data-deadline]")) {
    const s = Math.round((Date.parse(el.dataset.deadline) - Date.now()) / 1000);
    const a = Math.abs(s);
    const text = `${Math.floor(a / 60)}:${pad(a % 60)}`;
    el.textContent = s >= 0 ? text : `+${text} OVER`;
    el.dataset.state = s < 0 ? "over" : s < 120 ? "soon" : "";
  }
  const now = new Date();
  for (const el of document.querySelectorAll("[data-clock]")) {
    el.textContent = `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}`;
  }
}

async function refresh() {
  const main = document.getElementById("console");
  // Never swap the page out from under someone typing a name or ticking a box.
  if (!main || main.dataset.live !== "true" || main.contains(document.activeElement)) return;
  try {
    const res = await fetch(location.href, { headers: { Accept: "text/html" } });
    if (!res.ok) return;
    const doc = new DOMParser().parseFromString(await res.text(), "text/html");
    for (const sel of ["#console", ".counts"]) {
      const fresh = doc.querySelector(sel);
      const old = document.querySelector(sel);
      if (fresh && old) old.replaceWith(fresh);
    }
    tick();
  } catch {
    // offline for a moment; try again on the next interval
  }
}

document.addEventListener("input", (e) => {
  const counter = document.querySelector(`[data-count-for="${e.target.name}"]`);
  if (counter) counter.textContent = e.target.value.length;
});

tick();
setInterval(tick, 1000);
setInterval(refresh, 2000);
