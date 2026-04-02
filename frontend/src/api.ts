const BASE = import.meta.env.VITE_API_URL || "/api";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface DailySnapshot {
  id: string;
  company_id: string;
  company_name: string;
  snapshot_date: string;
  raw_news: string;
  sentiment_score: number | null;
  sentiment_label: string | null;
  summary: string | null;
  top_themes: string[];
  action_items: string | null;
  risk_flag: boolean;
  created_at: string;
}

export interface ReportResult {
  report_md: string;
  date_from: string;
  date_to: string;
  id?: string;
}

// ─── Daily Snapshots ────────────────────────────────────────────────────────

export async function fetchDaily(date: string): Promise<DailySnapshot[]> {
  const res = await fetch(`${BASE}/daily?date=${date}`);
  if (!res.ok) throw new Error("Failed to fetch daily snapshots");
  return res.json();
}

export async function fetchDates(): Promise<string[]> {
  const res = await fetch(`${BASE}/dates`);
  if (!res.ok) return [];
  return res.json();
}

// ─── On-Demand Report ───────────────────────────────────────────────────────

export async function generateReport(dateFrom: string, dateTo: string): Promise<ReportResult> {
  const res = await fetch(
    `${BASE}/report?date_from=${dateFrom}&date_to=${dateTo}`,
    { method: "POST" },
  );
  if (!res.ok) throw new Error("Failed to generate report");
  return res.json();
}

// ─── Manual Run ─────────────────────────────────────────────────────────────

export async function triggerRun(): Promise<void> {
  const res = await fetch(`${BASE}/run`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger run");
}
