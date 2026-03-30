# Competitor Monitor

ระบบติดตามความเคลื่อนไหวคู่แข่งตลาดโลจิสติกส์ไทย 6 ราย

## Companies Monitored
- ไปรษณีย์ไทย (Thailand Post)
- Flash Express
- KEX Express (Kerry เดิม)
- J&T Express
- Best Express
- Nim Express

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python / FastAPI / APScheduler |
| AI Search | Perplexity sonar-pro |
| Database | Supabase (PostgreSQL) |
| Frontend | React / Vite / TypeScript |

## Setup

### 1. Supabase
Run `supabase/migrations.sql` in Supabase SQL Editor.

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Cron Schedule (Bangkok Time GMT+7)
- 09:00, 12:00, 15:00, 18:00 ทุกวัน

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /api/summaries | Cumulative summary ล่าสุดทุกบริษัท |
| GET | /api/snapshots?date=&slot= | Snapshot ตามวัน+เวลา |
| GET | /api/dates | วันที่ที่มี snapshot |
| GET | /api/slots?date= | Time slots ของวันที่นั้น |
| POST | /api/run | Trigger manual run |
| GET | /health | Health check + scheduler status |

## How It Works

1. Scheduler triggers at 09:00, 12:00, 15:00, 18:00
2. For each company: get last cumulative summary from DB
3. Send single Perplexity sonar-pro query with old summary as context
4. Perplexity returns "ข่าวใหม่" + "ภาพรวมปัจจุบัน"
5. Save raw findings as snapshot → Upsert cumulative summary
6. Frontend shows latest summaries or historical snapshots via dropdowns
