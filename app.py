"""Flask application entry point."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from flask.typing import ResponseReturnValue
from flask import Flask, jsonify, request

from campwatcher import api
from campwatcher.models import SessionLocal, Watcher
from campwatcher.schemas import WatcherCreate
from campwatcher.scheduling import schedule_watcher, scheduler
from campwatcher.config import config
from reserve_ca import (
    fetch_availability as fetch_ca_availability,
    fetch_update_time as fetch_ca_update_time,
)


def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)

    dictConfig(
        {
            "version": 1,
            "formatters": {
                "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "default"}
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )

    @app.route("/search")
    def search_campgrounds() -> ResponseReturnValue:
        query = request.args.get("query")
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        results = api.fetch_campgrounds(query, lat, lon)
        return jsonify(results)

    @app.route("/ca_availability")
    def ca_availability() -> ResponseReturnValue:
        park_id = request.args.get("park_id")
        facility_id = request.args.get("facility_id")
        start_date = request.args.get("start_date")
        if not park_id or not facility_id or not start_date:
            return (
                jsonify({"error": "park_id, facility_id and start_date required"}),
                400,
            )
        data = fetch_ca_availability(park_id, facility_id, start_date)
        return jsonify(data)

    @app.route("/ca_update_time")
    def ca_update_time() -> ResponseReturnValue:
        park_id = request.args.get("park_id")
        facility_id = request.args.get("facility_id")
        if not park_id or not facility_id:
            return jsonify({"error": "park_id and facility_id required"}), 400
        update_dt = fetch_ca_update_time(park_id, facility_id)
        return jsonify(
            {"next_update_time": update_dt.isoformat() if update_dt else None}
        )

    @app.route("/watchers", methods=["POST"])
    def add_watcher() -> ResponseReturnValue:
        model = WatcherCreate.model_validate(request.json)
        session = SessionLocal()
        watcher = Watcher(
            campground_id=model.campground_id,
            site_type=model.site_type,
            check_time=model.check_time,
            email=model.email,
        )
        session.add(watcher)
        session.commit()
        schedule_watcher(watcher.id, model.check_time)
        session.close()
        return jsonify({"id": watcher.id})

    @app.before_first_request
    def start_scheduler() -> None:
        session = SessionLocal()
        watchers = session.query(Watcher).all()
        for w in watchers:
            schedule_watcher(w.id, w.check_time)
        scheduler.start()
        session.close()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
