import json
from datetime import datetime
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import os

app = Flask(__name__)

WATCHERS_FILE = os.path.join(os.path.dirname(__file__), '../watchers.json')

scheduler = BackgroundScheduler()
watchers = []


def load_watchers():
    global watchers
    if os.path.exists(WATCHERS_FILE):
        with open(WATCHERS_FILE, 'r') as f:
            watchers.extend(json.load(f))
    for watcher in watchers:
        schedule_watcher(watcher)

def save_watchers():
    with open(WATCHERS_FILE, 'w') as f:
        json.dump(watchers, f, indent=2)

def schedule_watcher(watcher):
    hour, minute = map(int, watcher['check_time'].split(':'))
    trigger = CronTrigger(hour=hour, minute=minute)
    scheduler.add_job(
        check_campsite,
        trigger=trigger,
        args=[watcher],
        id=str(len(watchers))
    )


def check_campsite(watcher):
    campsite = watcher['campsite']
    campsite_type = watcher['campsite_type']
    # Placeholder: replace with real API call to check availability
    available = fake_api_check(campsite, campsite_type)
    if available:
        now = datetime.utcnow().isoformat()
        watcher['last_notified'] = now
        print(
            f"Campsite {campsite} ({campsite_type}) available! Notifying {watcher['email']}"
        )
        save_watchers()


def fake_api_check(campsite, campsite_type):
    # This stub randomly returns True occasionally.
    import random
    return random.choice([True, False, False])

@app.route('/watch', methods=['POST'])
def watch():
    data = request.get_json()
    required = {'campsite', 'check_time', 'campsite_type', 'email'}
    if not data or not required.issubset(data):
        return jsonify({'error': 'missing fields'}), 400
    watchers.append(data)
    schedule_watcher(data)
    save_watchers()
    return jsonify({'message': 'watch added'}), 201

@app.route('/watches', methods=['GET'])
def list_watches():
    return jsonify(watchers)

if __name__ == '__main__':
    load_watchers()
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)
