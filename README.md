# NYT Mini League (GitHub-only)

This repo runs a NYT Mini weekly competition using:
- GitHub Actions for scraping + computing standings
- GitHub Pages for hosting a static dashboard
- JSON files committed to the repo as the data store

## Setup

1) Add repo secret:
- `NYT_S_COOKIE` = your NYT-S cookie value

2) Enable GitHub Pages:
- Settings → Pages → Source: GitHub Actions

3) Trigger workflow once:
- Actions → "Ingest NYT Mini + Compute" → Run workflow

## Local dev

```bash
pip install -r pipeline/requirements.txt
export NYT_S_COOKIE="..."
python pipeline/fetch.py
python pipeline/compute.py
python -m http.server --directory site 8000

Then open http://localhost:8000
 and ensure site/ can access data/ by running from repo root or adjusting paths.


---

# What you’ll get immediately

- A working static dashboard at `https://<you>.github.io/<repo>/`
- Hourly scrape + nightly compute
- Penalties controlled via `pipeline/config.yaml`
- “First seen solve” capture like your existing approach

---

## Two quick notes (so it doesn’t surprise you)

1) **Cookie expiry**: when NYT expires your session, the hourly job will fail. Easy fix: update the secret. (If you want, we can add “open an issue on failure” for visibility.)

2) **Division logic**: I kept it conservative so it won’t do something weird on week 1. Once you have ~10–20 players, we can:
   - seed divisions using median/avg like you did (`NTILE` logic)
   - lock divisions per week
   - implement variable relegations (1 or 2) based on target size more exactly

---

If you want, paste your repo name and whether you want **1** or **3** divisions as the initial default, and I’ll tweak the `config.yaml` + seeding logic accordingly.
