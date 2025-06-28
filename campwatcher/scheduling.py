"""Job scheduling utilities."""

from __future__ import annotations

import datetime
import logging
from typing import Any, List


from apscheduler.schedulers.background import BackgroundScheduler

from .api import check_availability
from .models import SessionLocal, Watcher
from campground_data import CAMPGROUND_ATTRIBUTES
import smtplib
from email.message import EmailMessage

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


def send_email(to_addr: str | None, subject: str, body: str) -> None:
    """Send a notification email if an address is provided."""
    if not to_addr:
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = "noreply@example.com"
    msg["To"] = to_addr
    msg.set_content(body)
    try:
        with smtplib.SMTP("localhost") as smtp:
            smtp.send_message(msg)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send email: %s", exc)



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
        avail = check_availability(
            watcher.campground_id, month_str, watcher.site_type
        )
        filtered: List[dict[str, Any]] = []
        for item in avail:
            attrs = CAMPGROUND_ATTRIBUTES.get(watcher.campground_id, {})
            if watcher.tent_only and not attrs.get("tent_only"):
                continue
            if watcher.no_rv and not attrs.get("no_rv"):
                continue
            if watcher.loop and watcher.loop != item.get("loop"):
                continue
            filtered.append(item)
        if filtered:
            logger.info("Availability found for watcher %s: %s", watcher.id, filtered)
            send_email(
                watcher.email,
                "Campsite available",
                f"Matching sites found: {filtered}",
            )

        else:
            logger.info("No availability for watcher %s", watcher.id)
    except Exception as exc:  # noqa: BLE001
        logger.error("Error checking watcher %s: %s", watcher.id, exc)
    finally:
        session.close()
