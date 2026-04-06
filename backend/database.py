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
    snapshot_time: str,
    raw_news: str,
    sentiment_score: float | None = None,
    sentiment_label: str | None = None,
    summary: str | None = None,
    top_themes: list[str] | None = None,
    action_items: str | None = None,
    risk_flag: bool = False,
    trigger_source: str = "manual",
) -> None:
    row = {
        "company_id": company_id,
        "company_name": company_name,
        "snapshot_date": snapshot_date,
        "snapshot_time": snapshot_time,
        "raw_news": raw_news,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "summary": summary,
        "top_themes": json.dumps(top_themes or []),
        "action_items": action_items,
        "risk_flag": risk_flag,
        "trigger_source": trigger_source,
    }
    resp = (
        get_client()
        .table("daily_snapshots")
        .upsert(row, on_conflict="company_id,snapshot_date,snapshot_time")
        .execute()
    )
    if resp is None:
        logger.error("[save_daily_snapshot] got None response for %s/%s %s", company_id, snapshot_date, snapshot_time)


def get_daily_snapshots(snapshot_date: str, snapshot_time: str) -> list[dict]:
    resp = (
        get_client()
        .table("daily_snapshots")
        .select("*")
        .eq("snapshot_date", snapshot_date)
        .eq("snapshot_time", snapshot_time)
        .order("company_name")
        .execute()
    )
    return resp.data or []


def get_snapshots_by_date_range(
    date_from: str,
    date_to: str,
    trigger_source: str | None = None,
) -> list[dict]:
    q = (
        get_client()
        .table("daily_snapshots")
        .select("*")
        .gte("snapshot_date", date_from)
        .lte("snapshot_date", date_to)
    )
    if trigger_source and trigger_source != "all":
        q = q.eq("trigger_source", trigger_source)
    resp = (
        q.order("snapshot_date", desc=True)
        .order("snapshot_time", desc=True)
        .order("company_name")
        .execute()
    )
    return resp.data or []


def get_available_runs() -> list[dict]:
    """Return unique (date, time, trigger_source) combos, newest first."""
    resp = (
        get_client()
        .table("daily_snapshots")
        .select("snapshot_date,snapshot_time,trigger_source")
        .order("snapshot_date", desc=True)
        .order("snapshot_time", desc=True)
        .execute()
    )
    seen: set[str] = set()
    runs: list[dict] = []
    for row in (resp.data or []):
        key = f"{row['snapshot_date']}_{row['snapshot_time']}"
        if key not in seen:
            seen.add(key)
            runs.append({
                "date": row["snapshot_date"],
                "time": row["snapshot_time"],
                "trigger_source": row.get("trigger_source", "manual"),
            })
    return runs


# ─── Generated Reports ──────────────────────────────────────────────────────


def save_report(date_from: str, date_to: str, report_md: str, trigger_filter: str = "all") -> dict:
    row = {
        "date_from": date_from,
        "date_to": date_to,
        "report_md": report_md,
        "trigger_filter": trigger_filter,
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
