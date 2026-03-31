import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("database").setLevel(logging.DEBUG)
logging.getLogger("monitor").setLevel(logging.DEBUG)

import database as db
from monitor import COMPANIES, run_monitor_cycle
from scheduler import create_scheduler

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    logging.getLogger(__name__).info("Scheduler started")
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="Competitor Monitor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/summaries")
def get_summaries():
    """ดึง Cumulative Summary ล่าสุดของทุกบริษัท"""
    return db.get_all_summaries()


@app.get("/api/snapshots")
def get_snapshots(date: str, slot: str):
    """ดึง Snapshot ตามวันที่และ time slot"""
    return db.get_snapshots(date, slot)


@app.get("/api/dates")
def get_dates():
    """ดึงรายการวันที่ที่มี snapshot"""
    return db.get_available_dates()


@app.get("/api/slots")
def get_slots(date: str):
    """ดึง time slots ที่มีข้อมูลของวันที่นั้น"""
    return db.get_available_slots(date)


@app.post("/api/run")
def run_now(slot: str | None = None):
    """Trigger monitor cycle manually"""
    api_key = os.getenv("PERPLEXITY_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not configured")
    import asyncio
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(run_monitor_cycle, api_key, slot)
        result = future.result(timeout=600)
    return result


@app.get("/api/companies")
def get_companies():
    return [{"id": c["id"], "name": c["name"]} for c in COMPANIES]


@app.get("/health")
def health():
    jobs = [{"id": j.id, "next_run": str(j.next_run_time)} for j in scheduler.get_jobs()]
    return {"status": "ok", "scheduled_jobs": jobs}
