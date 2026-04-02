import os
import json
import logging
from datetime import datetime, timezone
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


# ─── Daily Snapshots (V2) ───────────────────────────────────────────────────


def save_daily_snapshot(
    company_id: str,
    company_name: str,
    snapshot_date: str,
    raw_news: str,
    sentiment_score: float | None = None,
    sentiment_label: str | None = None,
    summary: str | None = None,
    top_themes: list[str] | None = None,
    action_items: str | None = None,
    risk_flag: bool = False,
) -> None:
    row = {
        "company_id": company_id,
        "company_name": company_name,
        "snapshot_date": snapshot_date,
        "raw_news": raw_news,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "summary": summary,
        "top_themes": json.dumps(top_themes or []),
        "action_items": action_items,
        "risk_flag": risk_flag,
    }
    resp = (
        get_client()
        .table("daily_snapshots")
        .upsert(row, on_conflict="company_id,snapshot_date")
        .execute()
    )
    if resp is None:
        logger.error("[save_daily_snapshot] got None response for %s/%s", company_id, snapshot_date)


def get_daily_snapshots(snapshot_date: str) -> list[dict]:
    resp = (
        get_client()
        .table("daily_snapshots")
        .select("*")
        .eq("snapshot_date", snapshot_date)
        .order("company_name")
        .execute()
    )
    return resp.data or []


def get_snapshots_by_date_range(date_from: str, date_to: str) -> list[dict]:
    resp = (
        get_client()
        .table("daily_snapshots")
        .select("*")
        .gte("snapshot_date", date_from)
        .lte("snapshot_date", date_to)
        .order("snapshot_date", desc=True)
        .order("company_name")
        .execute()
    )
    return resp.data or []


def get_available_snapshot_dates() -> list[str]:
    resp = (
        get_client()
        .table("daily_snapshots")
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


# ─── Generated Reports ──────────────────────────────────────────────────────


def save_report(date_from: str, date_to: str, report_md: str) -> dict:
    row = {
        "date_from": date_from,
        "date_to": date_to,
        "report_md": report_md,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    resp = get_client().table("generated_reports").insert(row).execute()
    if resp and resp.data:
        return resp.data[0]
    return row


def get_reports() -> list[dict]:
    resp = (
        get_client()
        .table("generated_reports")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return resp.data or []


# ─── Legacy functions (backward compat) ─────────────────────────────────────


def get_all_summaries() -> list[dict]:
    resp = get_client().table("competitor_summary").select("*").order("company_name").execute()
    return resp.data or []


def get_summary(company_id: str) -> dict | None:
    resp = (
        get_client()
        .table("competitor_summary")
        .select("*")
        .eq("company_id", company_id)
        .maybe_single()
        .execute()
    )
    if resp is None:
        return None
    return resp.data if isinstance(resp.data, dict) else None
