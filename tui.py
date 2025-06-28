import curses
import requests
from datetime import date, datetime
from typing import List, Tuple

# Simple mapping of ZIP codes to coordinates for demo purposes
ZIP_COORDS = {
    "94102": (37.7793, -122.4193),  # San Francisco
    "10001": (40.7506, -73.9971),  # New York
    "30301": (33.7525, -84.3915),  # Atlanta
}

SEARCH_API = "https://www.recreation.gov/api/facilities"
AVAILABILITY_API = (
    "https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"
)


def fetch_campgrounds(lat: float, lon: float) -> List[dict]:
    """Fetch campgrounds near a coordinate."""
    params = {"latitude": lat, "longitude": lon}
    resp = requests.get(SEARCH_API, params=params)
    resp.raise_for_status()
    return resp.json().get("RECDATA", [])


def _fetch_availability(campground_id: str, month: str) -> dict:
    start_date = f"{month}-01T00:00:00.000Z"
    url = AVAILABILITY_API.format(campground_id=campground_id)
    resp = requests.get(url, params={"start_date": start_date})
    resp.raise_for_status()
    return resp.json()


def weekend_available(campground_id: str, month: str) -> List[Tuple[str, str]]:
    """Return list of (site_id, date) tuples available on Fri or Sat."""
    data = _fetch_availability(campground_id, month)
    results = []
    for site_id, info in data.get("campsites", {}).items():
        for day, status in info.get("availabilities", {}).items():
            if status != "Available":
                continue
            dt = datetime.fromisoformat(day)
            if dt.weekday() in (4, 5):  # Fri=4, Sat=5
                results.append((site_id, dt.date().isoformat()))
    return results


def difficulty_score(campground_id: str, month: str) -> float:
    """Estimate booking difficulty for a campground."""
    data = _fetch_availability(campground_id, month)
    total = 0
    available = 0
    for site in data.get("campsites", {}).values():
        avail = site.get("availabilities", {})
        total += len(avail)
        available += sum(1 for v in avail.values() if v == "Available")
    if total == 0:
        return 1.0
    return 1.0 - (available / total)


def draw_center(stdscr, y: int, text: str, attr=0):
    h, w = stdscr.getmaxyx()
    x = max((w - len(text)) // 2, 0)
    stdscr.addstr(y, x, text, attr)


def tui_main(stdscr):
    curses.curs_set(1)
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    stdscr.clear()
    draw_center(stdscr, 1, "Campground Finder", curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(3, 2, "ZIP code: ")
    curses.echo()
    zip_code = stdscr.getstr(3, 12, 10).decode().strip()
    stdscr.addstr(5, 2, "Weekend only search? (y/n): ")
    choice = stdscr.getstr(5, 31, 1).decode().strip().lower()
    weekend_only = choice == "y"
    stdscr.addstr(7, 2, "Searching...", curses.color_pair(2))
    stdscr.refresh()

    if zip_code not in ZIP_COORDS:
        stdscr.addstr(9, 2, "Unknown ZIP code", curses.color_pair(3))
        stdscr.getch()
        return

    lat, lon = ZIP_COORDS[zip_code]
    month = date.today().strftime("%Y-%m")
    try:
        camps = fetch_campgrounds(lat, lon)
    except Exception as e:
        stdscr.addstr(9, 2, f"Error: {e}")
        stdscr.getch()
        return

    stdscr.clear()
    draw_center(stdscr, 1, "Results", curses.color_pair(1) | curses.A_BOLD)
    row = 3
    for camp in camps[:10]:
        name = camp.get("FacilityName", "Unknown")
        cid = str(camp.get("FacilityID"))
        try:
            score = difficulty_score(cid, month)
        except Exception:
            score = 0.0
        highlight = curses.A_BOLD
        if score > 0.8:
            highlight |= curses.color_pair(3)
        stdscr.addstr(row, 2, f"{name} (difficulty {score:.2f})", highlight)
        row += 1
        if weekend_only:
            try:
                avail = weekend_available(cid, month)
            except Exception:
                avail = []
        else:
            avail = []
        for site_id, day in avail[:3]:
            stdscr.addstr(row, 4, f"Site {site_id} available {day}")
            row += 1
        row += 1
        if row > curses.LINES - 2:
            break
    stdscr.addstr(row, 2, "Press any key to exit...", curses.color_pair(2))
    stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(tui_main)
