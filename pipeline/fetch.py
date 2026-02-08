from __future__ import annotations

import os
import requests
from datetime import date
from typing import Dict, Any, List, Tuple

from utils import Config, now_tz, to_iso, current_puzzle_week_dates, read_jsonl, write_jsonl

NYT_API_ROOT = "https://www.nytimes.com/svc/crosswords/v6/leaderboard/mini"


def fetch_leaderboard_for_day(puzzle_date: date, nyt_cookie: str) -> List[Dict[str, Any]]:
    url = f"{NYT_API_ROOT}/{puzzle_date.strftime('%Y-%m-%d')}.json"
    r = requests.get(url, cookies={"NYT-S": nyt_cookie}, timeout=30)
    r.raise_for_status()
    payload = r.json()
    # payload: { "data": [ { userID, name, score: { secondsSpentSolving } } ... ] }
    return payload.get("data", [])


def main() -> None:
    cfg = Config.load("pipeline/config.yaml")
    tz = cfg.tz()

    nyt_cookie = os.environ.get("NYT_S_COOKIE")
    if not nyt_cookie:
        raise RuntimeError("Missing NYT_S_COOKIE env var (set it in GitHub Secrets).")

    solves_path = cfg.storage()["solves_path"]
    existing = read_jsonl(solves_path)

    # key for dedupe: (puzzle_date, nyt_user_id)
    seen = {(r["puzzle_date"], int(r["nyt_user_id"])) for r in existing}

    week_start_weekday = cfg.cfg["week"]["week_start_weekday"]
    length_days = cfg.cfg["week"]["length_days"]
    week_start, puzzle_days = current_puzzle_week_dates(tz, week_start_weekday, length_days)

    pulled_at = now_tz(tz)

    new_rows: List[Dict[str, Any]] = []
    for d in puzzle_days:
        data = fetch_leaderboard_for_day(d, nyt_cookie)
        for row in data:
            nyt_user_id = row.get("userID")
            name = row.get("name")
            seconds = (row.get("score") or {}).get("secondsSpentSolving")

            if nyt_user_id is None:
                continue

            # only persist when time exists (mirrors your SQL filter SolveTime IS NOT NULL)
            if seconds is None:
                continue

            key = (d.isoformat(), int(nyt_user_id))
            if key in seen:
                continue

            new_rows.append({
                "puzzle_date": d.isoformat(),
                "puzzle_week": week_start.isoformat(),
                "nyt_user_id": int(nyt_user_id),
                "name": name,
                "seconds": int(seconds),
                "first_seen_at": to_iso(pulled_at),
            })
            seen.add(key)

    if new_rows:
        # append and keep stable ordering
        all_rows = existing + new_rows
        all_rows.sort(key=lambda r: (r["puzzle_date"], r["nyt_user_id"], r["first_seen_at"]))
        write_jsonl(solves_path, all_rows)
        print(f"Added {len(new_rows)} new solves.")
    else:
        print("No new solves found.")


if __name__ == "__main__":
    main()
