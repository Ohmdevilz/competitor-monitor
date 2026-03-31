import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client: Client | None = None

def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
        _client = create_client(url, key)
    return _client


def get_all_summaries() -> list[dict]:
    resp = get_client().table("competitor_summary").select("*").order("company_name").execute()
    return resp.data or []


def upsert_summary(company_id: str, company_name: str, summary: str, has_alert: bool) -> None:
    from datetime import datetime, timezone
    get_client().table("competitor_summary").upsert({
        "company_id": company_id,
        "company_name": company_name,
        "summary": summary,
        "has_alert": has_alert,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, on_conflict="company_id").execute()


def get_summary(company_id: str) -> dict | None:
    resp = (
        get_client()
        .table("competitor_summary")
        .select("*")
        .eq("company_id", company_id)
        .maybe_single()
        .execute()
    )
    logger.info("[get_summary] company_id=%s | resp type=%s | repr=%s",
                company_id, type(resp).__name__, repr(resp)[:300])
    if not hasattr(resp, "data"):
        logger.error("[get_summary] resp has NO .data attribute — returning None")
        return None
    logger.info("[get_summary] resp.data type=%s | repr=%s",
                type(resp.data).__name__, repr(resp.data)[:300])
    return resp.data


def save_snapshot(
    company_id: str,
    company_name: str,
    content: str,
    has_alert: bool,
    snapshot_date: str,
    snapshot_time_slot: str,
) -> None:
    get_client().table("competitor_snapshots").insert({
        "company_id": company_id,
        "company_name": company_name,
        "content": content,
        "has_alert": has_alert,
        "snapshot_date": snapshot_date,
        "snapshot_time_slot": snapshot_time_slot,
    }).execute()


def get_snapshots(snapshot_date: str, snapshot_time_slot: str) -> list[dict]:
    resp = (
        get_client()
        .table("competitor_snapshots")
        .select("*")
        .eq("snapshot_date", snapshot_date)
        .eq("snapshot_time_slot", snapshot_time_slot)
        .order("company_name")
        .execute()
    )
    return resp.data or []


def get_available_dates() -> list[str]:
    resp = (
        get_client()
        .table("competitor_snapshots")
        .select("snapshot_date")
        .order("snapshot_date", desc=True)
        .execute()
    )
    seen = []
    for row in (resp.data or []):
        d = row["snapshot_date"]
        if d not in seen:
            seen.append(d)
    return seen


def get_available_slots(snapshot_date: str) -> list[str]:
    resp = (
        get_client()
        .table("competitor_snapshots")
        .select("snapshot_time_slot")
        .eq("snapshot_date", snapshot_date)
        .execute()
    )
    ORDER = ["09:00", "12:00", "15:00", "18:00"]
    seen = set(row["snapshot_time_slot"] for row in (resp.data or []))
    return [s for s in ORDER if s in seen]
