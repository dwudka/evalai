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

Two additional endpoints allow checking campsite information for California State Parks using ReserveCalifornia.

```bash
GET /ca_availability?park_id=<park>&facility_id=<facility>&start_date=YYYY-MM-DD
GET /ca_update_time?park_id=<park>&facility_id=<facility>
```

`/ca_availability` returns the raw availability JSON from the ReserveCalifornia API. `/ca_update_time` scrapes the park page to find the timestamp of the next scheduled availability update, if available.

### Ranking Booking Difficulty

The `ranking.py` module provides helper functions to estimate how difficult it is to book a campground and to order individual sites by scarcity. Example usage:

```python
from ranking import difficulty_score, rank_sites_for_campground

score = difficulty_score("232450")
print("Difficulty score:", score)

sites = rank_sites_for_campground("232450")
print("Least available sites:", sites[:3])
```

Higher difficulty scores indicate fewer available dates across all sites.

## Running Locally

Follow these steps to start the application on your machine.

1. **Clone the repository** (if you have not already):

   ```bash
   git clone <repo-url>
   cd evalai
   ```

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask server**:

   ```bash
   python app.py
   ```

   The service will be available at `http://localhost:5000`.

You can now make requests to the API endpoints described above. Watcher jobs
will run at the configured times and log any newly available sites to the
console.
