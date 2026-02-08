async function getJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed ${path}: ${res.status}`);
  return await res.json();
}

function fmtSeconds(s) {
  const n = Math.round(s);
  const m = Math.floor(n / 60);
  const r = n % 60;
  return m > 0 ? `${m}:${String(r).padStart(2,'0')}` : `${r}s`;
}

function renderWeekly(el, rows) {
  rows.sort((a,b) => a.rank_overall - b.rank_overall);
  const html = `
    <table>
      <thead><tr><th>#</th><th>Player</th><th>Div</th><th>Week</th></tr></thead>
      <tbody>
        ${rows.map(r => `
          <tr>
            <td>${r.rank_overall}</td>
            <td>${r.display_name}</td>
            <td><span class="badge">D${r.division}</span></td>
            <td>${fmtSeconds(r.weekly_seconds)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
  el.innerHTML = html;
}

function renderDaily(el, rows) {
  // overall winner per day
  const byDay = new Map();
  for (const r of rows) {
    if (r.rank_overall_day !== 1) continue;
    byDay.set(r.puzzle_date, r);
  }
  const days = [...byDay.keys()].sort();
  const html = `
    <table>
      <thead><tr><th>Date</th><th>Winner</th><th>Time</th></tr></thead>
      <tbody>
        ${days.map(d => {
          const r = byDay.get(d);
          return `<tr><td>${d}</td><td>${r.display_name}</td><td>${fmtSeconds(r.total_seconds)}</td></tr>`;
        }).join("")}
      </tbody>
    </table>
  `;
  el.innerHTML = html;
}

(async function main() {
  const index = await getJSON("./data/computed/index.json");
  const meta = document.getElementById("meta");
  if (!index.latest_week) {
    meta.textContent = "No data yet — once the ingest job runs, this will populate.";
    return;
  }
  meta.textContent = `Latest week: ${index.latest_week} • Generated: ${index.generated_at}`;

  const week = index.latest_week;
  const weekly = await getJSON(`./data/computed/weeks/${week}/weekly.json`);
  const daily = await getJSON(`./data/computed/weeks/${week}/daily.json`);

  renderWeekly(document.getElementById("weekly"), weekly);
  renderDaily(document.getElementById("daily"), daily);
})().catch(err => {
  console.error(err);
  document.getElementById("meta").textContent = "Error loading data. Check console.";
});
