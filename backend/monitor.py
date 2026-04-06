"""
monitor.py — Core monitoring logic (V2)
Daily flow: Perplexity (news 24h) → Gemini (sentiment + analysis) → Supabase
On-demand: date range → Supabase snapshots → Gemini report
"""
import json
import logging
import re
import time
from datetime import datetime

from google import genai
import pytz
import requests

import database as db

logger = logging.getLogger(__name__)

TZ_BANGKOK = pytz.timezone("Asia/Bangkok")

PERPLEXITY_API_BASE = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"

COMPANIES = [
    {
        "id": "thailand_post", "name": "ไปรษณีย์ไทย", "name_en": "Thailand Post",
        "keywords": ["ไปรษณีย์ไทย", "ปณท", "Thailand Post", "ไปรษณีย์"],
        "website": "https://www.thailandpost.co.th/",
        "facebook": "https://www.facebook.com/thailandpost.co.th/",
    },
    {
        "id": "flash_express", "name": "Flash Express", "name_en": "Flash Express Thailand",
        "keywords": ["Flash Express", "แฟลช เอ็กซ์เพรส", "Flash", "แฟลช"],
        "website": "https://www.flashexpress.co.th/",
        "facebook": "https://www.facebook.com/FlashExpressThailand/",
    },
    {
        "id": "kex_express", "name": "KEX Express", "name_en": "KEX Express Kerry Express Thailand",
        "keywords": ["KEX Express", "เคอีเอ็กซ์", "KEX", "Kerry Express", "เคอรี่", "Kerry"],
        "website": "https://th.kex-express.com/",
        "facebook": "https://www.facebook.com/kexthailand/",
    },
    {
        "id": "jnt_express", "name": "J&T Express", "name_en": "J&T Express Thailand",
        "keywords": ["J&T Express", "เจแอนด์ที", "J&T", "เจแอนด์ที เอ็กซ์เพรส"],
        "website": "https://jtexpress.co.th/",
        "facebook": "https://www.facebook.com/jntexpressthailandHQ/",
    },
    {
        "id": "best_express", "name": "Best Express", "name_en": "Best Express Thailand",
        "keywords": ["Best Express", "เบสท์เอ็กซ์เพรส", "Best", "BEST"],
        "website": "https://www.best-inc.co.th/",
        "facebook": "https://www.facebook.com/BESTExpressThailand/",
    },
    {
        "id": "nim_express", "name": "Nim Express", "name_en": "Nim Express Thailand",
        "keywords": ["Nim Express", "นิ่มเอ็กซ์เพรส", "นิ่ม", "Nim"],
        "website": "https://www.nimexpress.com/",
        "facebook": "https://www.facebook.com/nimexp/",
    },
    {
        "id": "tp_logistics", "name": "TP Logistics", "name_en": "TP Logistics Thailand",
        "keywords": ["TP Logistics", "ไทยพาร์เซิล", "Thai Parcels", "TP", "ทีพี โลจิสติกส์"],
        "website": "https://thaiparcels.com/",
        "facebook": None,
    },
]


# ─── Perplexity: Search news last 24h ───────────────────────────────────────


def _perplexity_search(company: dict, api_key: str) -> str:
    """Search recent 24h news for a company via Perplexity."""
    now_bkk = datetime.now(TZ_BANGKOK).strftime("%Y-%m-%d %H:%M")

    system = (
        "You are a Thai logistics market intelligence analyst. "
        "Search for verified, factual news only from the last 24 hours. "
        "If no recent news is found, say so clearly. Do not hallucinate."
    )

    # Build brand-specific source list and keywords
    sources = [f"- เว็บไซต์หลัก: {company['website']}"]
    if company.get("facebook"):
        sources.append(f"- Facebook: {company['facebook']}")
    sources_text = "\n".join(sources)
    keywords_text = ", ".join(company.get("keywords", [company["name"]]))

    prompt = f"""วันที่และเวลาปัจจุบัน: {now_bkk} (เวลาไทย)

ค้นหาข่าวและข้อมูลใหม่เกี่ยวกับ {company['name']} ({company['name_en']}) ในช่วง 24 ชั่วโมงที่ผ่านมาเท่านั้น

**ชื่อ/คำค้นหาทั้งหมดของแบรนด์นี้:** {keywords_text}
ใช้ชื่อเหล่านี้ทุกชื่อในการค้นหา เพราะแต่ละแหล่งอาจใช้ชื่อต่างกัน

## แหล่งข้อมูลที่ต้องตรวจสอบ (เรียงตามลำดับความสำคัญ)

### 1. แหล่งหลักของแบรนด์ — ตรวจสอบก่อน
{sources_text}

### 2. เว็บข่าวธุรกิจและโลจิสติกส์ไทย
- ข่าวจาก Prachachat, Thansettakij, Marketeer, Logistics Manager, Bangkokbiznews, Posttoday
- ข่าวจาก Google News ที่เกี่ยวข้องกับ {company['name']}

### 3. Pantip
- กระทู้ใน Pantip ที่พูดถึง {keywords_text} ในช่วง 24 ชั่วโมงที่ผ่านมา
- เช่น รีวิว ร้องเรียน ประสบการณ์ใช้บริการ

## หัวข้อที่ต้องค้นหา
1. การปรับราคาค่าขนส่ง หรือค่าบริการใหม่
2. ค่าธรรมเนียมเพิ่มเติม (Fuel Surcharge, Remote Area Surcharge)
3. การงดรับพัสดุ หรือจำกัดพื้นที่บริการ
4. โปรโมชั่นหรือแคมเปญใหม่
5. ข่าวสำคัญ (นโยบายใหม่, ปัญหาบริการ, การขยายธุรกิจ, ความร่วมมือ)
6. ข่าวเชิงลบ (ร้องเรียน, ปัญหาคุณภาพ, ข้อพิพาท)

## รูปแบบการตอบ
ตอบเป็นภาษาไทย พร้อมระบุแหล่งที่มาและวันที่ของข่าวแต่ละชิ้น
ถ้าไม่พบข่าวใหม่ใน 24 ชั่วโมง ให้ระบุว่า "ไม่พบข่าวใหม่ในช่วง 24 ชั่วโมงที่ผ่านมา"
"""

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    resp = requests.post(
        PERPLEXITY_API_BASE,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": PERPLEXITY_MODEL, "messages": messages, "temperature": 0.1},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ─── Gemini: Analyze single brand ───────────────────────────────────────────


def _gemini_analyze_competitor(company: dict, raw_news: str, gemini_client) -> dict:
    """Use Gemini to analyze sentiment of a competitor brand's news."""

    prompt = f"""คุณเป็นนักวิเคราะห์ตลาดขนส่งไทย ให้คำปรึกษาแก่ TP Logistics
วิเคราะห์ข่าวต่อไปนี้ของคู่แข่ง "{company['name']}":

--- ข่าวดิบ ---
{raw_news}
--- จบข่าวดิบ ---

สำคัญ:
- sentiment_score/sentiment_label = ประเมินว่าข่าวนี้เป็นบวกหรือลบ "ต่อแบรนด์ {company['name']}" (ไม่ใช่ต่อ TP Logistics)
- action_items = สิ่งที่ "TP Logistics ควรทำ" เพื่อตอบสนองต่อข่าวของ {company['name']} (ต้องขึ้นต้นด้วย "TP Logistics ควร...")
- risk_flag = ข่าวนี้กระทบ TP Logistics ในเชิงการแข่งขันหรือไม่

ตอบในรูปแบบ JSON เท่านั้น (ไม่ต้องมี markdown code block):
{{
  "sentiment_score": <ตัวเลข -10.0 ถึง 10.0, บวก=ข่าวดีต่อ {company['name']}, ลบ=ข่าวลบต่อ {company['name']}, 0=เป็นกลาง>,
  "sentiment_label": "<positive|neutral|negative>",
  "summary": "<สรุปข่าวสำคัญของ {company['name']} เป็นภาษาไทย 2-3 ประโยค>",
  "top_themes": [<รายการหัวข้อสำคัญ เช่น "pricing", "expansion", "service_issue", "promotion", "partnership">],
  "action_items": "<สิ่งที่ TP Logistics ควรทำตอบสนองต่อข่าวของ {company['name']} — ต้องตอบเสมอ ห้ามเป็น null ขึ้นต้นด้วย 'TP Logistics ควร...'>",
  "risk_flag": <true ถ้ามีการเปลี่ยนแปลงสำคัญที่กระทบ TP Logistics, false ถ้าไม่มี>
}}
"""

    return _parse_gemini_json(gemini_client, prompt, company["id"], raw_news)


def _gemini_analyze_tp(raw_news: str, competitor_actions: list[dict], gemini_client) -> dict:
    """Use Gemini to analyze TP Logistics own news + summarize competitor actions."""

    actions_text = "\n".join(
        f"- {a['name']}: {a['action']}" for a in competitor_actions if a.get("action")
    )

    prompt = f"""คุณเป็นนักวิเคราะห์ตลาดขนส่งไทย วิเคราะห์ข่าวต่อไปนี้ของ TP Logistics (แบรนด์ของเรา):

--- ข่าวดิบของ TP Logistics ---
{raw_news}
--- จบข่าวดิบ ---

--- Action Items จากการวิเคราะห์คู่แข่งทั้ง 6 ราย ---
{actions_text}
--- จบ Action Items ---

สำคัญ:
- sentiment_score/sentiment_label = ประเมินว่าข่าวนี้เป็นบวกหรือลบ "ต่อ TP Logistics"
- action_items = สรุปคำแนะนำภาพรวมสำหรับ TP Logistics จากทั้งข่าวตัวเองและจากสถานการณ์คู่แข่งทั้ง 6 ราย
  ขึ้นต้นด้วย "จากสถานการณ์คู่แข่ง TP Logistics ควร..." แล้วสรุปเป็นข้อๆ

ตอบในรูปแบบ JSON เท่านั้น (ไม่ต้องมี markdown code block):
{{
  "sentiment_score": <ตัวเลข -10.0 ถึง 10.0, บวก=ข่าวดีต่อ TP Logistics, ลบ=ข่าวลบ, 0=เป็นกลาง>,
  "sentiment_label": "<positive|neutral|negative>",
  "summary": "<สรุปข่าวสำคัญของ TP Logistics เป็นภาษาไทย 2-3 ประโยค>",
  "top_themes": [<รายการหัวข้อสำคัญ>],
  "action_items": "<สรุปคำแนะนำภาพรวมจากสถานการณ์คู่แข่ง + ข่าวตัวเอง — ต้องตอบเสมอ ห้ามเป็น null>",
  "risk_flag": <true ถ้ามีความเสี่ยงสำคัญต่อ TP Logistics, false ถ้าไม่มี>
}}
"""

    return _parse_gemini_json(gemini_client, prompt, "tp_logistics", raw_news)


GEMINI_MAX_RETRIES = 3
GEMINI_RETRY_DELAY = 60  # seconds


def _gemini_call_with_retry(gemini_client, prompt: str) -> str:
    """Call Gemini with retry on 429 RESOURCE_EXHAUSTED."""
    for attempt in range(1, GEMINI_MAX_RETRIES + 1):
        try:
            resp = gemini_client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return resp.text.strip() if resp.text else ""
        except Exception as exc:
            if "429" in str(exc) and attempt < GEMINI_MAX_RETRIES:
                logger.warning("  [gemini] 429 rate limit — retry %d/%d in %ds",
                               attempt, GEMINI_MAX_RETRIES, GEMINI_RETRY_DELAY)
                time.sleep(GEMINI_RETRY_DELAY)
            else:
                raise
    return ""


def _parse_gemini_json(gemini_client, prompt: str, company_id: str, raw_news: str) -> dict:
    """Call Gemini and parse JSON response with fallback."""
    text = _gemini_call_with_retry(gemini_client, prompt)

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Gemini returned non-JSON for %s, using defaults", company_id)
        data = {
            "sentiment_score": 0,
            "sentiment_label": "neutral",
            "summary": raw_news[:500],
            "top_themes": [],
            "action_items": None,
            "risk_flag": False,
        }

    return data


# ─── Gemini: Generate on-demand report ──────────────────────────────────────


def generate_report(date_from: str, date_to: str, gemini_api_key: str, trigger_source: str = "all") -> str:
    """Generate a comprehensive report from daily snapshots in a date range."""
    snapshots = db.get_snapshots_by_date_range(date_from, date_to, trigger_source)

    if not snapshots:
        return f"# ไม่พบข้อมูล\n\nไม่พบ snapshot ในช่วง {date_from} ถึง {date_to}"

    # Group by company, separate competitors from TP
    competitors_data: dict[str, list[dict]] = {}
    tp_data: list[dict] = []
    for s in snapshots:
        if s["company_id"] == "tp_logistics":
            tp_data.append(s)
        else:
            competitors_data.setdefault(s["company_id"], []).append(s)

    # Sort competitors by COMPANY_ORDER
    company_order = [c["id"] for c in COMPANIES if c["id"] != "tp_logistics"]
    sorted_cids = sorted(competitors_data.keys(), key=lambda cid: company_order.index(cid) if cid in company_order else 999)

    # Build competitor context
    competitor_parts = []
    for cid in sorted_cids:
        items = competitors_data[cid]
        name = items[0]["company_name"]
        competitor_parts.append(f"\n### {name}")
        for item in items:
            date = item["snapshot_date"]
            score = item.get("sentiment_score", "N/A")
            label = item.get("sentiment_label", "N/A")
            summary = item.get("summary") or item.get("raw_news", "")[:300]
            themes = item.get("top_themes", [])
            risk = "⚠️ YES" if item.get("risk_flag") else "No"
            competitor_parts.append(
                f"- **{date}** | Sentiment: {score} ({label}) | Risk: {risk}\n"
                f"  สรุป: {summary}\n"
                f"  Themes: {', '.join(themes) if isinstance(themes, list) else themes or '-'}"
            )

    # Build TP context
    tp_parts = []
    for item in tp_data:
        date = item["snapshot_date"]
        score = item.get("sentiment_score", "N/A")
        label = item.get("sentiment_label", "N/A")
        summary = item.get("summary") or item.get("raw_news", "")[:300]
        themes = item.get("top_themes", [])
        action = item.get("action_items") or "-"
        risk = "⚠️ YES" if item.get("risk_flag") else "No"
        tp_parts.append(
            f"- **{date}** | Sentiment: {score} ({label}) | Risk: {risk}\n"
            f"  สรุป: {summary}\n"
            f"  Themes: {', '.join(themes) if isinstance(themes, list) else themes or '-'}\n"
            f"  Action: {action}"
        )

    competitor_context = "\n".join(competitor_parts)
    tp_context = "\n".join(tp_parts) if tp_parts else "ไม่มีข้อมูล"

    client = genai.Client(api_key=gemini_api_key)

    prompt = f"""คุณเป็นที่ปรึกษาด้านกลยุทธ์ตลาดขนส่งไทยระดับ Senior ให้กับ TP Logistics
สร้างรายงานวิเคราะห์คู่แข่งจากข้อมูลช่วง {date_from} ถึง {date_to}

--- ข้อมูลคู่แข่ง 6 ราย ---
{competitor_context}
--- จบข้อมูลคู่แข่ง ---

--- ข้อมูล TP Logistics (แบรนด์ของเรา) ---
{tp_context}
--- จบข้อมูล TP Logistics ---

เขียนรายงานเป็น Markdown ภาษาไทย ตามโครงสร้างนี้อย่างเคร่งครัด:

# รายงานวิเคราะห์คู่แข่ง
**ช่วงเวลา:** {date_from} ถึง {date_to}

## Executive Summary
สรุปภาพรวมตลาดขนส่งในช่วงนี้ 3-5 ประโยค

## วิเคราะห์รายแบรนด์
(เรียงลำดับตามนี้: ไปรษณีย์ไทย, Nim Express, Best Express, KEX Express, Flash Express, J&T Express)
(ไม่ต้องรวม TP Logistics ในส่วนนี้)

สำหรับแต่ละแบรนด์คู่แข่ง ให้แสดงเฉพาะ:
### [ชื่อแบรนด์]
- **Sentiment Score:** [คะแนน] ([label])
- **Top Themes:** [หัวข้อสำคัญ]
- **สรุป:** [วิเคราะห์สถานการณ์]

(ห้ามใส่ Action ในส่วนนี้)

## Cross-brand Insights
วิเคราะห์เปรียบเทียบข้ามแบรนด์คู่แข่ง แนวโน้มร่วม ความแตกต่าง

## Strategic Implications สำหรับ TP Logistics
ส่วนนี้ให้สรุปข้อมูลของ TP Logistics รวมกับคำแนะนำเชิงกลยุทธ์:
- **Sentiment Score ของ TP:** [คะแนน] ([label])
- **Top Themes ของ TP:** [หัวข้อสำคัญ]
- **สรุปสถานการณ์ TP:** [สรุปข่าวของ TP Logistics]
- **Action:** [คำแนะนำเชิงกลยุทธ์สำหรับ TP Logistics โดยอิงจากสถานการณ์คู่แข่งทั้ง 6 ราย + ข่าวของ TP เอง]

## Risk Flags
รายการความเสี่ยงที่ต้องจับตา (ถ้ามี) หรือระบุว่าไม่พบความเสี่ยงสำคัญ
"""

    return _gemini_call_with_retry(client, prompt)


# ─── Daily Monitor Cycle ────────────────────────────────────────────────────


def run_monitor_cycle(perplexity_key: str, gemini_key: str, trigger_source: str = "manual") -> dict:
    """
    Main daily cycle — runs for all 7 companies.
    Perplexity search → Gemini analysis → save to Supabase.
    """
    now_bkk = datetime.now(TZ_BANGKOK)
    snapshot_date = now_bkk.strftime("%Y-%m-%d")
    snapshot_time = now_bkk.strftime("%H:%M")

    logger.info("Starting daily monitor cycle: %s %s", snapshot_date, snapshot_time)

    # Init Gemini
    gemini_client = genai.Client(api_key=gemini_key)

    results = {"date": snapshot_date, "time": snapshot_time, "success": [], "failed": []}

    # Separate TP Logistics from competitors
    competitors = [c for c in COMPANIES if c["id"] != "tp_logistics"]
    tp_company = next(c for c in COMPANIES if c["id"] == "tp_logistics")

    # Step A: Process all 6 competitors first
    competitor_actions: list[dict] = []

    for company in competitors:
        try:
            raw_news = _perplexity_search(company, perplexity_key)
            logger.info("  [perplexity] %s — got %d chars", company["name"], len(raw_news))

            analysis = _gemini_analyze_competitor(company, raw_news, gemini_client)
            logger.info("  [gemini] %s — sentiment=%.1f (%s), risk=%s",
                        company["name"],
                        analysis.get("sentiment_score", 0),
                        analysis.get("sentiment_label", "?"),
                        analysis.get("risk_flag", False))

            competitor_actions.append({
                "name": company["name"],
                "action": analysis.get("action_items"),
            })

            _save_snapshot(company, snapshot_date, snapshot_time, raw_news, analysis, trigger_source)
            results["success"].append(company["id"])
            logger.info("  ✓ %s — saved", company["name"])
            time.sleep(2)

        except Exception as exc:
            logger.error("  ✗ %s — %s", company["name"], exc)
            results["failed"].append(company["id"])

    # Step B: Process TP Logistics last — with competitor actions as context
    try:
        raw_news = _perplexity_search(tp_company, perplexity_key)
        logger.info("  [perplexity] %s — got %d chars", tp_company["name"], len(raw_news))

        analysis = _gemini_analyze_tp(raw_news, competitor_actions, gemini_client)
        logger.info("  [gemini] %s — sentiment=%.1f (%s), risk=%s",
                    tp_company["name"],
                    analysis.get("sentiment_score", 0),
                    analysis.get("sentiment_label", "?"),
                    analysis.get("risk_flag", False))

        _save_snapshot(tp_company, snapshot_date, snapshot_time, raw_news, analysis, trigger_source)
        results["success"].append(tp_company["id"])
        logger.info("  ✓ %s — saved", tp_company["name"])

    except Exception as exc:
        logger.error("  ✗ %s — %s", tp_company["name"], exc)
        results["failed"].append(tp_company["id"])

    logger.info("Cycle done: %s/%s success", len(results["success"]), len(COMPANIES))
    return results


def _save_snapshot(company: dict, snapshot_date: str, snapshot_time: str, raw_news: str, analysis: dict, trigger_source: str) -> None:
    db.save_daily_snapshot(
        company_id=company["id"],
        company_name=company["name"],
        snapshot_date=snapshot_date,
        snapshot_time=snapshot_time,
        raw_news=raw_news,
        sentiment_score=analysis.get("sentiment_score"),
        sentiment_label=analysis.get("sentiment_label"),
        summary=analysis.get("summary"),
        top_themes=analysis.get("top_themes", []),
        action_items=analysis.get("action_items"),
        risk_flag=analysis.get("risk_flag", False),
        trigger_source=trigger_source,
    )
