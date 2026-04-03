Always respond in Thai language, regardless of what language I use to write my prompts.

Every time you finish editing or creating files, immediately commit and push to GitHub without asking for confirmation.

Every time there is a significant change to the project (new feature, major bug fix, architecture change), update the "Project Status & Change Log" section at the bottom of this file. This serves as the single source of truth for both developers and Claude across all sessions.

---

# Project Status & Change Log

## Overview
**Competitor Monitor** — ระบบติดตามคู่แข่งตลาดโลจิสติกส์ไทยสำหรับ TP Logistics
- **Backend**: FastAPI + Supabase + Perplexity API + Gemini API (google-genai SDK, model: gemini-2.5-flash)
- **Frontend**: React + Vite + TypeScript + react-markdown
- **Deploy**: Backend → Railway / Frontend → Vercel
- **Scheduler**: APScheduler 1 รอบ/วัน 09:00 Bangkok time
- **Brands (7)**: ไปรษณีย์ไทย, Flash Express, KEX Express, J&T Express, Best Express, Nim Express, TP Logistics

## Architecture (V2)
```
DAILY FLOW:
Perplexity API (ข่าว 24 ชม. × 7 แบรนด์)
  → Gemini API (sentiment + analysis per brand)
  → Supabase daily_snapshots
  → Frontend Card UI

ON-DEMAND REPORT:
User เลือก Date Range + trigger_source filter
  → ดึง daily_snapshots จาก Supabase
  → Gemini Generate Report (Markdown)
  → แสดงบน Dashboard + Export PDF
```

## Key Tables (Supabase)
- **daily_snapshots**: per brand per run — unique(company_id, snapshot_date, snapshot_time), มี sentiment_score, sentiment_label, top_themes, action_items, risk_flag, trigger_source
- **generated_reports**: on-demand reports — date_from, date_to, report_md

## Change Log

### 2026-04-03 — Multi-run support + Action scope fix
- เพิ่ม `snapshot_time` (HH:MM) รองรับหลาย run ต่อวันไม่ทับกัน
- เพิ่ม `trigger_source` field (scheduled/manual) ทั้ง backend + frontend
- Dropdown แสดง date + time + [Scheduled/Manual] label
- On-Demand Report เพิ่ม filter: All / Scheduled / Manual
- แก้ Action Box scope: คู่แข่ง = "TP ควรตอบสนอง", TP = "สรุปคำแนะนำ" (สรุปจากคู่แข่ง 6 ราย)
- Legend + Tooltip อธิบาย Risk Badge และ Sentiment Score ชัดเจน (sentiment = ต่อแบรนด์นั้นๆ)
- แก้ fetch timeout เป็น 10 นาที ป้องกัน false error ตอนกดรัน
- แก้ Gemini prompt ให้ action_items ไม่เป็น null
- แก้ top_themes handle ทั้ง string/array/null ไม่ crash

### 2026-04-03 — V2 Architecture Refactor
- เปลี่ยนจาก 4 รอบ/วัน cumulative summary → Perplexity 24h + Gemini sentiment pipeline
- เพิ่ม TP Logistics เป็นแบรนด์ที่ 7
- ย้ายจาก google-generativeai (deprecated) → google-genai SDK + gemini-2.5-flash
- Frontend: Tab UI (Daily Monitor / On-Demand Report), Sentiment Card, Markdown Report, Export PDF, Report History
- เรียงลำดับ Card: ไปรษณีย์ไทย → Nim → Best → KEX → Flash → J&T → TP Logistics
- Env variable รองรับทั้ง GEMINI_API_KEY และ GOOGLE_API_KEY

### 2026-04-02 — Bug fix + Deploy setup
- แก้ NoneType bug ใน get_summary() (maybe_single + null check)
- เพิ่ม Procfile + railway.toml สำหรับ Railway deploy
- เพิ่ม vercel.json + vite-env.d.ts สำหรับ Vercel deploy
- Frontend ชี้ Railway URL ผ่าน VITE_API_URL
- เพิ่ม Favicon, Default Light Mode
