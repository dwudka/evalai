# EvalAI Campsite Watcher

This sample web app demonstrates how to watch California recreation campsites and notify when new availability appears. It uses Flask for the web server and APScheduler to check campsites at a user-specified time each day. The app stores watches in `watchers.json`.

## Running

Create a virtual environment and install requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Start the server:

```bash
python app/server.py
```

POST a watch to `/watch` with JSON:

```json
{
  "campsite": "Crystal Cove",
  "campsite_type": "cottage",
  "check_time": "08:00",
  "email": "user@example.com"
}
```

List watches via `GET /watches`.

The `fake_api_check` function is a stub. Replace it with code that queries the real reservation system.
