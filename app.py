from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import create_engine, Column, Integer, String, Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import datetime
from reserve_ca import fetch_availability as fetch_ca_availability, fetch_update_time as fetch_ca_update_time

# Database setup
engine = create_engine('sqlite:///watchers.db')
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Watcher(Base):
    __tablename__ = 'watchers'
    id = Column(Integer, primary_key=True)
    campground_id = Column(String, nullable=False)
    site_type = Column(String, nullable=True)
    check_time = Column(String, nullable=False)  # HH:MM
    email = Column(String, nullable=True)

Base.metadata.create_all(engine)

app = Flask(__name__)
scheduler = BackgroundScheduler()

SEARCH_API = "https://www.recreation.gov/api/facilities"
AVAILABILITY_API = "https://www.recreation.gov/api/camps/availability/campground/{campground_id}/month"  # need start_date


def fetch_campgrounds(query, lat=None, lon=None):
    params = {"query": query}
    if lat and lon:
        params.update({"latitude": lat, "longitude": lon})
    resp = requests.get(SEARCH_API, params=params)
    resp.raise_for_status()
    data = resp.json()
    return data.get("RECDATA", [])


def check_availability(campground_id, month_str, site_type=None):
    start_date = f"{month_str}-01T00:00:00.000Z"
    url = AVAILABILITY_API.format(campground_id=campground_id)
    resp = requests.get(url, params={"start_date": start_date})
    resp.raise_for_status()
    data = resp.json()
    available = []
    for site_id, months in data.get("campsites", {}).items():
        for day, info in months.get("availabilities", {}).items():
            if info == "Available":
                if not site_type or months.get("campsite_type") == site_type:
                    available.append({"site_id": site_id, "date": day})
    return available


def schedule_watcher(watcher_id, time_str):
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(func=run_watcher, trigger='cron', args=[watcher_id], id=str(watcher_id), hour=hour, minute=minute)


def run_watcher(watcher_id):
    session = SessionLocal()
    watcher = session.query(Watcher).filter(Watcher.id == watcher_id).first()
    if not watcher:
        return
    today = datetime.date.today()
    month_str = today.strftime("%Y-%m")
    try:
        avail = check_availability(watcher.campground_id, month_str, watcher.site_type)
        if avail:
            print(f"Availability found for watcher {watcher.id}: {avail}")
        else:
            print(f"No availability for watcher {watcher.id}")
    except Exception as e:
        print(f"Error checking watcher {watcher.id}: {e}")
    finally:
        session.close()


@app.route('/search')
def search_campgrounds():
    query = request.args.get('query')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    results = fetch_campgrounds(query, lat, lon)
    return jsonify(results)


@app.route('/ca_availability')
def ca_availability():
    park_id = request.args.get('park_id')
    facility_id = request.args.get('facility_id')
    start_date = request.args.get('start_date')
    if not park_id or not facility_id or not start_date:
        return jsonify({'error': 'park_id, facility_id and start_date required'}), 400
    data = fetch_ca_availability(park_id, facility_id, start_date)
    return jsonify(data)


@app.route('/ca_update_time')
def ca_update_time():
    park_id = request.args.get('park_id')
    facility_id = request.args.get('facility_id')
    if not park_id or not facility_id:
        return jsonify({'error': 'park_id and facility_id required'}), 400
    update_dt = fetch_ca_update_time(park_id, facility_id)
    return jsonify({'next_update_time': update_dt.isoformat() if update_dt else None})


@app.route('/watchers', methods=['POST'])
def add_watcher():
    data = request.json
    campground_id = data.get('campground_id')
    site_type = data.get('site_type')
    check_time = data.get('check_time')  # HH:MM
    email = data.get('email')
    if not campground_id or not check_time:
        return jsonify({'error': 'campground_id and check_time required'}), 400
    session = SessionLocal()
    watcher = Watcher(campground_id=campground_id, site_type=site_type, check_time=check_time, email=email)
    session.add(watcher)
    session.commit()
    schedule_watcher(watcher.id, check_time)
    session.close()
    return jsonify({'id': watcher.id})


@app.before_first_request
def start_scheduler():
    session = SessionLocal()
    watchers = session.query(Watcher).all()
    for w in watchers:
        schedule_watcher(w.id, w.check_time)
    scheduler.start()
    session.close()


if __name__ == '__main__':
    app.run(debug=True)
