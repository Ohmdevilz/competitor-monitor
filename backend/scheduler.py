"""
scheduler.py — APScheduler cron job
Runs monitor cycle once daily at 09:00 Bangkok time.
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

from monitor import run_monitor_cycle

logger = logging.getLogger(__name__)
TZ_BANGKOK = pytz.timezone("Asia/Bangkok")


def _daily_job():
    perplexity_key = os.getenv("PERPLEXITY_API_KEY", "")
    gemini_key = os.getenv("GOOGLE_API_KEY", "")
    if not perplexity_key:
        logger.error("PERPLEXITY_API_KEY not set — skipping cycle")
        return
    if not gemini_key:
        logger.error("GOOGLE_API_KEY not set — skipping cycle")
        return
    run_monitor_cycle(perplexity_key, gemini_key)


def create_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone=TZ_BANGKOK)

    scheduler.add_job(
        _daily_job,
        CronTrigger(hour=9, minute=0, timezone=TZ_BANGKOK),
        id="daily_monitor",
        name="Daily Competitor Monitor 09:00",
        max_instances=1,
        coalesce=True,
    )

    return scheduler
