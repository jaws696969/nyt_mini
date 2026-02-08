from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Set
from datetime import date, timedelta

import pandas as pd


@dataclass
class DivisionConfig:
    target_size: int
    base_divisions: int
    max_divisions: int
    promote_relegate_default: int
    promote_relegate_if_oversize: int
    oversize_threshold: int
    inactive_weeks_to_drop: int


def compute_active_users(
    solves: pd.DataFrame,
    week_start: date,
    inactive_weeks_to_drop: int
) -> Set[int]:
    """
    Active = has at least 1 solve in last N weeks (including current).
    """
    cutoff = week_start - timedelta(weeks=inactive_weeks_to_drop)
    recent = solves[solves["puzzle_week"] >= pd.Timestamp(cutoff)]
    return set(recent["nyt_user_id"].unique().tolist())


def choose_num_divisions(n_players: int, cfg: DivisionConfig) -> int:
    if n_players <= 0:
        return 1
    est = (n_players + cfg.target_size - 1) // cfg.target_size
    est = max(cfg.base_divisions, est)
    return min(cfg.max_divisions, est)


def seed_divisions_for_week(
    week_start: date,
    active_users: List[int],
    prior_week_final_ranks: pd.DataFrame | None,
    cfg: DivisionConfig
) -> Dict[int, int]:
    """
    Returns mapping nyt_user_id -> division (1 = top).
    If prior week ranks exist: keep order; apply promote/relegate later.
    If no prior ranks: simple sort by user_id into divisions.
    """
    n_div = choose_num_divisions(len(active_users), cfg)

    if prior_week_final_ranks is not None and not prior_week_final_ranks.empty:
        # Keep only active users, order by prior rank_in_division then division
        pr = prior_week_final_ranks[prior_week_final_ranks["nyt_user_id"].isin(active_users)].copy()
        pr = pr.sort_values(["division", "rank_in_division"], ascending=[True, True])
        ordered = pr["nyt_user_id"].tolist()
        # include brand new users at the bottom
        new_users = [u for u in active_users if u not in set(ordered)]
        ordered += sorted(new_users)
    else:
        ordered = sorted(active_users)

    mapping: Dict[int, int] = {}
    for i, u in enumerate(ordered):
        div = 1 + (i * n_div) // max(1, len(ordered))
        mapping[int(u)] = int(div)
    return mapping


def promote_relegate(
    prior_week_final_ranks: pd.DataFrame,
    current_mapping: Dict[int, int],
    cfg: DivisionConfig
) -> Dict[int, int]:
    """
    Applies promotion/relegation based on prior week finishing positions.
    Conservative: moves 1 normally, sometimes 2 if division oversize.
    """
    if prior_week_final_ranks.empty:
        return current_mapping

    pr = prior_week_final_ranks.copy()
    pr = pr.sort_values(["division", "rank_in_division"], ascending=[True, True])

    # compute division sizes
    sizes = pr.groupby("division")["nyt_user_id"].count().to_dict()
    max_div = int(pr["division"].max())

    new_mapping = dict(current_mapping)

    for div in range(1, max_div + 1):
        size = int(sizes.get(div, 0))
        move = cfg.promote_relegate_if_oversize if size >= (cfg.target_size + cfg.oversize_threshold) else cfg.promote_relegate_default

        # relegations from this division
        if div < max_div:
            bottom = pr[pr["division"] == div].tail(move)["nyt_user_id"].tolist()
            for u in bottom:
                new_mapping[int(u)] = min(max_div, div + 1)

        # promotions into this division from below
        if div > 1:
            top_below = pr[pr["division"] == (div)].head(0)  # placeholder, handled when iterating below

    # promotions: top from lower division move up
    for div in range(2, max_div + 1):
        size = int(sizes.get(div, 0))
        move = cfg.promote_relegate_if_oversize if size >= (cfg.target_size + cfg.oversize_threshold) else cfg.promote_relegate_default
        top = pr[pr["division"] == div].head(move)["nyt_user_id"].tolist()
        for u in top:
            new_mapping[int(u)] = max(1, div - 1)

    return new_mapping
