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

export interface SavedReport {
  id: string;
  date_from: string;
  date_to: string;
  report_md: string;
  created_at: string;
}

// ─── Daily Snapshots ────────────────────────────────────────────────────────

export async function fetchDaily(date: string): Promise<DailySnapshot[]> {
  const res = await fetch(`${BASE}/daily?date=${date}`);
  if (!res.ok) throw new Error("Failed to fetch daily snapshots");
  return res.json();
}

export interface DateInfo {
  date: string;
  trigger_source: string;  // "scheduled" | "manual"
}

export async function fetchDates(): Promise<DateInfo[]> {
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

export async function fetchReports(): Promise<SavedReport[]> {
  const res = await fetch(`${BASE}/reports`);
  if (!res.ok) return [];
  return res.json();
}

// ─── Manual Run ─────────────────────────────────────────────────────────────

export async function triggerRun(): Promise<void> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10 min
  try {
    const res = await fetch(`${BASE}/run`, { method: "POST", signal: controller.signal });
    if (!res.ok) throw new Error("Failed to trigger run");
  } finally {
    clearTimeout(timeout);
  }
}
