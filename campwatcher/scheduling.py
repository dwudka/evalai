"""Job scheduling utilities."""

from __future__ import annotations

import datetime
import logging
from typing import List

from apscheduler.schedulers.background import BackgroundScheduler

from .api import check_availability
from .models import SessionLocal, Watcher

scheduler = BackgroundScheduler()
logger = logging.getLogger(__name__)


def schedule_watcher(watcher_id: int, time_str: str) -> None:
    """Schedule a watcher by ID at HH:MM."""
    hour, minute = map(int, time_str.split(":"))
    scheduler.add_job(
        func=run_watcher,
        trigger="cron",
        args=[watcher_id],
        id=str(watcher_id),
        hour=hour,
        minute=minute,
    )


def run_watcher(watcher_id: int) -> None:
    """Check availability for a stored watcher and log results."""
    session = SessionLocal()
    watcher = session.query(Watcher).filter(Watcher.id == watcher_id).first()
    if not watcher:
        session.close()
        return
    today = datetime.date.today()
    month_str = today.strftime("%Y-%m")
    try:
        avail = check_availability(watcher.campground_id, month_str, watcher.site_type)
        if avail:
            logger.info("Availability found for watcher %s: %s", watcher.id, avail)
        else:
            logger.info("No availability for watcher %s", watcher.id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error checking watcher %s: %s", watcher.id, exc)
    finally:
        session.close()
