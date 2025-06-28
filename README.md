# Campsite Availability Watcher

This is a simple Flask web application that allows users to search for campsites on Recreation.gov and watch specific campgrounds for new availability. Watchers run at a specified time each day and log when new campsites become available.

## Setup

1. Install dependencies (use a virtual environment recommended):
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```
   The server will start on `http://localhost:5000`.

## API Usage

### Search for Campgrounds

```
GET /search?query=crystal+cove
```

Optional parameters:
- `lat` and `lon` – search near a coordinate.

### Add a Watcher

```
POST /watchers
Content-Type: application/json
{
  "campground_id": "232450",
  "site_type": "STANDARD NONELECTRIC",
  "check_time": "08:00",
  "email": "user@example.com"
}
```

The `campground_id` corresponds to the ID from Recreation.gov. The `check_time` is the time of day (24h format) the watcher should run.

When availability is found, a message is printed to the console. This can be extended to send an email or other notification.

### ReserveCalifornia Endpoints

Two additional endpoints allow checking campsite information for California
State Parks using ReserveCalifornia.

```bash
GET /ca_availability?park_id=<park>&facility_id=<facility>&start_date=YYYY-MM-DD
GET /ca_update_time?park_id=<park>&facility_id=<facility>
```

`/ca_availability` returns the raw availability JSON from the ReserveCalifornia
API. `/ca_update_time` scrapes the park page to find the timestamp of the next
scheduled availability update, if available.
