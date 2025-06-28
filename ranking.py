# coding: utf-8
"""Utility functions for ranking campsite demand and booking difficulty."""

from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple

import requests
from campwatcher.config import config


def _fetch_availability(campground_id: str, month_str: str) -> Dict:
    url = config.availability_api.format(campground_id=campground_id)
    """Return raw availability JSON for a campground and month."""
    start_date = f"{month_str}-01T00:00:00.000Z"
    resp = requests.get(url, params={"start_date": start_date})
    resp.raise_for_status()
    return resp.json()


def difficulty_score(campground_id: str, month: str | None = None) -> float:
    """Estimate how hard it is to book a campsite at a campground.

    The score is 1.0 when no sites are available at all and decreases as
    availability increases. 0.0 means every site is available every day.
    """
    if not month:
        month = date.today().strftime("%Y-%m")
    data = _fetch_availability(campground_id, month)
    total_days = 0
    available_days = 0
    for site in data.get("campsites", {}).values():
        availabilities = site.get("availabilities", {})
        total_days += len(availabilities)
        available_days += sum(
            1 for val in availabilities.values() if val == "Available"
        )
    if total_days == 0:
        return 1.0
    ratio = available_days / total_days
    return 1.0 - ratio


def rank_sites_for_campground(
    campground_id: str, month: str | None = None
) -> List[Tuple[str, float]]:
    """Return site IDs ranked by scarcity (lower availability first)."""
    if not month:
        month = date.today().strftime("%Y-%m")
    data = _fetch_availability(campground_id, month)
    site_scores: List[Tuple[str, float]] = []
    for site_id, site in data.get("campsites", {}).items():
        availabilities = site.get("availabilities", {})
        total = len(availabilities)
        available = sum(1 for val in availabilities.values() if val == "Available")
        rate = available / total if total else 0.0
        site_scores.append((site_id, rate))
    site_scores.sort(key=lambda t: t[1])  # least available first
    return site_scores


def rank_campgrounds(
    campground_ids: List[str], month: str | None = None
) -> List[Tuple[str, float]]:
    """Rank campgrounds by difficulty score in descending order."""
    scores = []
    for cid in campground_ids:
        scores.append((cid, difficulty_score(cid, month)))
    scores.sort(key=lambda t: t[1], reverse=True)
    return scores
