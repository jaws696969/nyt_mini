from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from typing import Iterable, Dict, Any, List, Optional, Tuple

import pytz
import yaml


@dataclass(frozen=True)
class Config:
    cfg: Dict[str, Any]

    @staticmethod
    def load(path: str) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            return Config(yaml.safe_load(f))

    def tz(self):
        return pytz.timezone(self.cfg["league"]["timezone"])

    def storage(self) -> Dict[str, Any]:
        return self.cfg["storage"]


def now_tz(tz) -> datetime:
    return datetime.now(tz)


def to_iso(dt: datetime) -> str:
    return dt.isoformat()


def parse_iso(s: str) -> datetime:
    # Handles tz-aware strings we generated.
    return datetime.fromisoformat(s)


def daterange(start: date, end: date) -> Iterable[date]:
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def week_start_for(d: date, week_start_weekday: int) -> date:
    """
    Python weekday: Monday=0..Sunday=6
    If week_start_weekday=1 => Tuesday start.
    """
    offset = (d.weekday() - week_start_weekday) % 7
    return d - timedelta(days=offset)


def current_puzzle_week_dates(tz, week_start_weekday: int, length_days: int = 7) -> Tuple[date, List[date]]:
    today = now_tz(tz).date()
    ws = week_start_for(today, week_start_weekday)
    days = [ws + timedelta(days=i) for i in range(length_days)]
    return ws, days


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
