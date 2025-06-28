"""Flask application entry point."""

from __future__ import annotations

import logging
from logging.config import dictConfig

from flask import Flask, jsonify, request, render_template
from flask.typing import ResponseReturnValue

from campwatcher import api
from campwatcher.models import SessionLocal, Watcher
from campwatcher.schemas import WatcherCreate
from campwatcher.scheduling import schedule_watcher, scheduler
from campwatcher.config import config
from campground_data import CAMPGROUND_ATTRIBUTES
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
            "formatters": {"default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
            "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "default"}},
            "root": {"level": "INFO", "handlers": ["console"]},
        }
    )

    @app.route("/search")
    def search_campgrounds() -> ResponseReturnValue:
        query = request.args.get("query")
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        tent_only = request.args.get("tent_only") == "true"
        no_rv = request.args.get("no_rv") == "true"
        results = api.fetch_campgrounds(query, lat, lon)
        filtered = []
        for camp in results:
            cid = str(camp.get("FacilityID"))
            attrs = CAMPGROUND_ATTRIBUTES.get(cid, {})
            if tent_only and not attrs.get("tent_only"):
                continue
            if no_rv and not attrs.get("no_rv"):
                continue
            filtered.append(camp)
        return jsonify(filtered)

    @app.route("/ca_availability")
    def ca_availability() -> ResponseReturnValue:
        park_id = request.args.get("park_id")
        facility_id = request.args.get("facility_id")
        start_date = request.args.get("start_date")
        if not park_id or not facility_id or not start_date:
            return jsonify({"error": "park_id, facility_id and start_date required"}), 400
        data = fetch_ca_availability(park_id, facility_id, start_date)
        return jsonify(data)

    @app.route("/ca_update_time")
    def ca_update_time() -> ResponseReturnValue:
        park_id = request.args.get("park_id")
        facility_id = request.args.get("facility_id")
        if not park_id or not facility_id:
            return jsonify({"error": "park_id and facility_id required"}), 400
        update_dt = fetch_ca_update_time(park_id, facility_id)
        return jsonify({"next_update_time": update_dt.isoformat() if update_dt else None})

    @app.route("/difficulty_score")
    def difficulty_score_endpoint() -> ResponseReturnValue:
        campground_id = request.args.get("campground_id")
        if not campground_id:
            return jsonify({"error": "campground_id required"}), 400
        from ranking import difficulty_score

        score = difficulty_score(campground_id)
        return jsonify({"campground_id": campground_id, "difficulty_score": score})

    @app.route("/watchers", methods=["POST"])
    def add_watcher() -> ResponseReturnValue:
        model = WatcherCreate.model_validate(request.json)
        session = SessionLocal()
        watcher = Watcher(
            campground_id=model.campground_id,
            site_type=model.site_type,
            tent_only=bool(model.tent_only),
            no_rv=bool(model.no_rv),
            loop=model.loop,
            check_time=model.check_time,
            email=model.email,
        )
        session.add(watcher)
        session.commit()
        schedule_watcher(watcher.id, model.check_time)
        session.close()
        return jsonify({"id": watcher.id})

    @app.route("/")
    def index() -> ResponseReturnValue:
        return render_template("index.html")

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
