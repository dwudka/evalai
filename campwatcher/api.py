"""Helper functions for Recreation.gov endpoints."""

from typing import Any, Dict, List, Optional

import requests

from .config import config


def fetch_campgrounds(
    query: str, lat: str | None = None, lon: str | None = None
) -> List[Dict[str, Any]]:
    """Search for campgrounds using the Recreation.gov API."""
    params = {"query": query}
    if lat and lon:
        params.update({"latitude": lat, "longitude": lon})
    resp = requests.get(config.search_api, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("RECDATA", [])


def check_availability(
    campground_id: str, month_str: str, site_type: str | None = None
) -> List[Dict[str, Any]]:
    """Return available site IDs for a campground/month with attributes."""
    start_date = f"{month_str}-01T00:00:00.000Z"
    url = config.availability_api.format(campground_id=campground_id)
    resp = requests.get(url, params={"start_date": start_date})
    resp.raise_for_status()
    data = resp.json()
    available: List[Dict[str, Any]] = []
    for site_id, months in data.get("campsites", {}).items():
        attrs: Dict[str, Any] = {}
        if months.get("campsite_type"):
            ctype = months.get("campsite_type", "")
            if "TENT" in ctype.upper() and "RV" not in ctype.upper():
                attrs["tent_only"] = True
            if "RV" not in ctype.upper():
                attrs["no_rv"] = True
        for day, info in months.get("availabilities", {}).items():
            if info == "Available":
                if not site_type or months.get("campsite_type") == site_type:
                    entry = {"site_id": site_id, "date": day}
                    entry.update(attrs)
                    available.append(entry)
    return available
