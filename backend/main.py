import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logging.getLogger("database").setLevel(logging.DEBUG)
logging.getLogger("monitor").setLevel(logging.DEBUG)

import database as db
from monitor import COMPANIES, run_monitor_cycle, generate_report
from scheduler import create_scheduler


def _get_gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")


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


# ─── V2 Endpoints ───────────────────────────────────────────────────────────


@app.get("/api/daily")
def get_daily(date: str, time: str):
    """ดึง Daily Snapshots ของวันที่+เวลาที่ระบุ"""
    return db.get_daily_snapshots(date, time)


@app.get("/api/runs")
def get_runs():
    """ดึงรายการ runs ที่มี (date + time + trigger_source)"""
    return db.get_available_runs()


@app.post("/api/report")
def create_report(
    date_from: str = Query(..., description="Start date YYYY-MM-DD"),
    date_to: str = Query(..., description="End date YYYY-MM-DD"),
    trigger_source: str = Query("all", description="Filter: all | scheduled | manual"),
):
    """Generate on-demand report for a date range via Gemini"""
    gemini_key = _get_gemini_key()
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY / GOOGLE_API_KEY not configured")

    report_md = generate_report(date_from, date_to, gemini_key, trigger_source)
    saved = db.save_report(date_from, date_to, report_md, trigger_filter=trigger_source)
    return {"report_md": report_md, "date_from": date_from, "date_to": date_to, "id": saved.get("id")}


@app.get("/api/reports")
def get_reports():
    """ดึงรายการ reports ที่เคย generate"""
    return db.get_reports()


@app.post("/api/run")
def run_now():
    """Trigger daily monitor cycle manually"""
    perplexity_key = os.getenv("PERPLEXITY_API_KEY", "")
    gemini_key = _get_gemini_key()
    if not perplexity_key:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not configured")
    if not gemini_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY / GOOGLE_API_KEY not configured")

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        future = pool.submit(run_monitor_cycle, perplexity_key, gemini_key)
        result = future.result(timeout=1800)  # 30 min (retries may take long)
    return result


@app.get("/api/companies")
def get_companies():
    return [{"id": c["id"], "name": c["name"]} for c in COMPANIES]


# ─── Legacy Endpoints ───────────────────────────────────────────────────────


@app.get("/api/summaries")
def get_summaries():
    """ดึง Cumulative Summary ล่าสุดของทุกบริษัท (legacy)"""
    return db.get_all_summaries()


@app.get("/health")
def health():
    jobs = [{"id": j.id, "next_run": str(j.next_run_time)} for j in scheduler.get_jobs()]
    return {"status": "ok", "scheduled_jobs": jobs}
