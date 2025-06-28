import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

PARK_PAGE_URL = "https://www.reservecalifornia.com/Web/#!park/{park_id}/{facility_id}"
AVAILABILITY_API = "https://calirdr.usedirect.com/RDR/rdr/availability/park"


def fetch_availability(park_id: str, facility_id: str, start_date: str):
    """Fetch availability data for a specific park and facility.

    Parameters
    ----------
    park_id: str
        Numeric ID of the park.
    facility_id: str
        Numeric ID of the facility/loop within the park.
    start_date: str
        Date string in YYYY-MM-DD format.

    Returns
    -------
    dict
        Parsed JSON availability response.
    """
    params = {
        "parkId": park_id,
        "facilityId": facility_id,
        "startDate": start_date,
    }
    resp = requests.get(AVAILABILITY_API, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_update_time(park_id: str, facility_id: str):
    """Parse the park page to determine the next availability update time.

    The ReserveCalifornia park page embeds a JSON blob containing the next time
    new availability will be released. This function extracts that timestamp and
    returns it as a ``datetime``.
    """
    url = PARK_PAGE_URL.format(park_id=park_id, facility_id=facility_id)
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    script_tags = soup.find_all("script")
    for tag in script_tags:
        if not tag.string:
            continue
        m = re.search(r'"nextAvailabilityUpdate"\s*:\s*"([^"]+)"', tag.string)
        if m:
            try:
                return datetime.fromisoformat(m.group(1))
            except ValueError:
                pass
    return None
