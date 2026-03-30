-- competitor_snapshots: each monitoring cycle's raw findings per company
create table if not exists competitor_snapshots (
  id                 uuid primary key default gen_random_uuid(),
  company_id         text not null,
  company_name       text not null,
  content            text not null,
  has_alert          boolean not null default false,
  snapshot_date      text not null,       -- 'YYYY-MM-DD' Bangkok time
  snapshot_time_slot text not null,       -- '09:00' | '12:00' | '15:00' | '18:00'
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
