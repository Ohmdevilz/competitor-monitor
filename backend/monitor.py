"""
monitor.py — Core monitoring logic
Each cycle: for each company, get last summary → search new news via Perplexity
→ build cumulative profile → save snapshot + upsert summary
"""
import logging
import time
from datetime import datetime

import pytz
import requests

import database as db

logger = logging.getLogger(__name__)

TZ_BANGKOK = pytz.timezone("Asia/Bangkok")

PERPLEXITY_API_BASE = "https://api.perplexity.ai/chat/completions"
MODEL = "sonar-pro"

COMPANIES = [
    {"id": "thailand_post",  "name": "ไปรษณีย์ไทย",  "name_en": "Thailand Post"},
    {"id": "flash_express",  "name": "Flash Express",  "name_en": "Flash Express Thailand"},
    {"id": "kex_express",    "name": "KEX Express",    "name_en": "KEX Express Kerry Express Thailand"},
    {"id": "jnt_express",    "name": "J&T Express",    "name_en": "J&T Express Thailand"},
    {"id": "best_express",   "name": "Best Express",   "name_en": "Best Express Thailand"},
    {"id": "nim_express",    "name": "Nim Express",    "name_en": "Nim Express Thailand"},
]

ALERT_KEYWORDS = [
    "ปรับราคา", "ขึ้นราคา", "เพิ่มราคา", "ลดราคา", "งดรับ", "ยกเลิกบริการ",
    "fuel surcharge", "ค่าน้ำมัน", "ประกาศด่วน", "price increase",
    "rate adjustment", "suspension", "หยุดให้บริการ", "ปรับขึ้น", "ค่าธรรมเนียมใหม่",
]


def _detect_alert(content: str) -> bool:
    cl = content.lower()
    return any(kw.lower() in cl for kw in ALERT_KEYWORDS)


def _perplexity_query(prompt: str, api_key: str, system: str = "") -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = requests.post(
        PERPLEXITY_API_BASE,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "temperature": 0.1},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _search_and_update(company: dict, old_summary: str | None, old_updated: str | None, api_key: str) -> dict:
    """Single Perplexity call: search new news + produce updated cumulative profile."""
    now_bkk = datetime.now(TZ_BANGKOK).strftime("%Y-%m-%d %H:%M")

    if old_summary and old_updated:
        context_block = (
            f"ข้อมูลที่มีอยู่แล้ว (อัปเดตล่าสุดเมื่อ {old_updated}):\n{old_summary}\n\n"
        )
        since_clause = f"ตั้งแต่ {old_updated} จนถึงตอนนี้"
    else:
        context_block = ""
        since_clause = "ในช่วง 3 เดือนที่ผ่านมา"

    system = (
        "You are a Thai logistics market intelligence analyst. "
        "Search verified, factual news only. Do not hallucinate. "
        "If you cannot find specific information, say so clearly."
    )

    prompt = f"""วันนี้คือ {now_bkk} (เวลาไทย)

บริษัท: {company['name']} ({company['name_en']})
{context_block}
ค้นหาข้อมูลและข่าวใหม่เกี่ยวกับ {company['name']} ({company['name_en']}) {since_clause}

หัวข้อที่ต้องค้นหา:
1. การปรับราคาค่าขนส่ง หรือค่าบริการใหม่
2. ค่าธรรมเนียมเพิ่มเติม เช่น Fuel Surcharge, Remote Area Surcharge
3. การงดรับพัสดุ หรือจำกัดพื้นที่บริการ
4. โปรโมชั่นหรือแคมเปญใหม่
5. ข่าวสำคัญของบริษัท (เช่น นโยบายใหม่, ปัญหาบริการ, การขยายธุรกิจ)

ตอบในรูปแบบนี้เท่านั้น:

## ข่าวใหม่
[สิ่งที่ค้นพบใหม่ พร้อมวันที่ ถ้าไม่พบข่าวใหม่ให้เขียน "ไม่พบข่าวใหม่ในช่วงนี้"]

## ภาพรวมปัจจุบัน
[สรุปภาพรวมของบริษัทที่รวมข้อมูลเก่าและใหม่เข้าด้วยกัน ครอบคลุม:
- ราคามาตรฐาน/โครงสร้างราคา (ถ้าทราบ)
- ค่าธรรมเนียมที่ใช้อยู่ปัจจุบัน
- โปรโมชั่นที่ใช้งานอยู่
- ข้อจำกัดหรือพื้นที่งดบริการ
- ข่าวสำคัญล่าสุด
- อัปเดตล่าสุด: {now_bkk}]
"""

    response = _perplexity_query(prompt, api_key, system=system)

    # Parse sections
    new_findings = response
    updated_profile = response

    if "## ข่าวใหม่" in response and "## ภาพรวมปัจจุบัน" in response:
        parts = response.split("## ภาพรวมปัจจุบัน", 1)
        new_findings = parts[0].replace("## ข่าวใหม่", "").strip()
        updated_profile = parts[1].strip()

    has_alert = _detect_alert(new_findings)

    return {
        "new_findings": new_findings,
        "updated_profile": updated_profile,
        "has_alert": has_alert,
    }


def run_monitor_cycle(api_key: str, time_slot: str | None = None) -> dict:
    """
    Main cycle — runs for all 6 companies sequentially.
    Returns summary of what was processed.
    """
    now_bkk = datetime.now(TZ_BANGKOK)
    snapshot_date = now_bkk.strftime("%Y-%m-%d")

    if time_slot is None:
        # Round to nearest scheduled slot
        hour = now_bkk.hour
        slots = {9: "09:00", 12: "12:00", 15: "15:00", 18: "18:00"}
        time_slot = slots.get(hour) or f"{hour:02d}:00"

    logger.info("Starting monitor cycle: %s %s", snapshot_date, time_slot)
    results = {"success": [], "failed": []}

    for company in COMPANIES:
        try:
            # Get last cumulative summary
            last = db.get_summary(company["id"])
            logger.info("  [monitor] get_summary(%s) → type=%s | repr=%s",
                        company["id"], type(last).__name__, repr(last)[:300])
            old_summary = last["summary"] if last else None
            old_updated = last["updated_at"] if last else None
            logger.info("  [monitor] old_summary exists=%s | old_updated=%s",
                        bool(old_summary), old_updated)

            # Search + build updated profile (single Perplexity call)
            result = _search_and_update(company, old_summary, old_updated, api_key)

            # Save raw findings as snapshot
            db.save_snapshot(
                company_id=company["id"],
                company_name=company["name"],
                content=result["new_findings"],
                has_alert=result["has_alert"],
                snapshot_date=snapshot_date,
                snapshot_time_slot=time_slot,
            )

            # Upsert cumulative summary
            db.upsert_summary(
                company_id=company["id"],
                company_name=company["name"],
                summary=result["updated_profile"],
                has_alert=result["has_alert"],
            )

            results["success"].append(company["id"])
            logger.info("  ✓ %s — alert=%s", company["name"], result["has_alert"])

            # Small delay between Perplexity calls to avoid rate limiting
            time.sleep(2)

        except Exception as exc:
            logger.error("  ✗ %s — %s", company["name"], exc)
            results["failed"].append(company["id"])

    logger.info("Cycle done: %s/%s success", len(results["success"]), len(COMPANIES))
    return results
