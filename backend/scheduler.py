"""
scheduler.py — APScheduler cron jobs
Runs monitor cycle at 09:00, 12:00, 15:00, 18:00 Bangkok time daily.
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from monitor import run_monitor_cycle

logger = logging.getLogger(__name__)
TZ_BANGKOK = pytz.timezone("Asia/Bangkok")


def _make_job(slot: str):
    def job():
        api_key = os.getenv("PERPLEXITY_API_KEY", "")
        if not api_key:
            logger.error("PERPLEXITY_API_KEY not set — skipping cycle")
            return
        run_monitor_cycle(api_key, time_slot=slot)
    job.__name__ = f"monitor_{slot.replace(':', '')}"
    return job


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=TZ_BANGKOK)

    for hour, slot in [(9, "09:00"), (12, "12:00"), (15, "15:00"), (18, "18:00")]:
        scheduler.add_job(
            _make_job(slot),
            CronTrigger(hour=hour, minute=0, timezone=TZ_BANGKOK),
            id=f"monitor_{slot.replace(':', '')}",
            name=f"Competitor Monitor {slot}",
            max_instances=1,
            coalesce=True,
        )

    return scheduler
