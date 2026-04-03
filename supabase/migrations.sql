-- ============================================================
-- V2: Daily Snapshot + Sentiment Architecture
-- ============================================================

-- daily_snapshots: one row per brand per day
-- contains raw news from Perplexity + Gemini analysis
create table if not exists daily_snapshots (
  id              uuid primary key default gen_random_uuid(),
  company_id      text not null,
  company_name    text not null,
  snapshot_date   text not null,                -- 'YYYY-MM-DD' Bangkok time
  raw_news        text not null,                -- raw Perplexity response
  sentiment_score numeric(3,1),                 -- -10.0 to 10.0
  sentiment_label text,                         -- 'positive' | 'neutral' | 'negative'
  summary         text,                         -- Gemini brand summary (Thai markdown)
  top_themes      jsonb default '[]'::jsonb,    -- ["pricing","expansion",...]
  action_items    text,                         -- recommended actions
  risk_flag       boolean not null default false,
  trigger_source  text not null default 'manual',   -- 'scheduled' | 'manual'
  created_at      timestamptz not null default now(),
  unique(company_id, snapshot_date)
);

create index if not exists idx_daily_company_date
  on daily_snapshots (company_id, snapshot_date desc);
create index if not exists idx_daily_date
  on daily_snapshots (snapshot_date desc);

-- generated_reports: on-demand reports for date ranges
create table if not exists generated_reports (
  id          uuid primary key default gen_random_uuid(),
  date_from   text not null,
  date_to     text not null,
  report_md   text not null,                    -- full markdown report
  created_at  timestamptz not null default now()
);

create index if not exists idx_reports_dates
  on generated_reports (date_from, date_to);

-- ============================================================
-- Legacy tables (kept for backward compatibility, can be dropped later)
-- ============================================================

-- competitor_snapshots: each monitoring cycle's raw findings per company
create table if not exists competitor_snapshots (
  id                 uuid primary key default gen_random_uuid(),
  company_id         text not null,
  company_name       text not null,
  content            text not null,
  has_alert          boolean not null default false,
  snapshot_date      text not null,
  snapshot_time_slot text not null,
  created_at         timestamptz not null default now()
);

create index if not exists idx_snapshots_date_slot
  on competitor_snapshots (snapshot_date desc, snapshot_time_slot);
create index if not exists idx_snapshots_company_date
  on competitor_snapshots (company_id, snapshot_date desc);

-- competitor_summary: latest cumulative profile per company (upserted each cycle)
create table if not exists competitor_summary (
  company_id   text primary key,
  company_name text not null,
  summary      text not null,
  has_alert    boolean not null default false,
  updated_at   timestamptz not null default now()
);
