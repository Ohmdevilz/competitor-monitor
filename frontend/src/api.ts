const BASE = import.meta.env.VITE_API_URL || "/api";

// ─── Types ──────────────────────────────────────────────────────────────────

export interface DailySnapshot {
  id: string;
  company_id: string;
  company_name: string;
  snapshot_date: string;
  snapshot_time: string;
  raw_news: string;
  sentiment_score: number | null;
  sentiment_label: string | null;
  summary: string | null;
  top_themes: string[];
  action_items: string | null;
  risk_flag: boolean;
  trigger_source: string;
  created_at: string;
}

export interface RunInfo {
  date: string;
  time: string;
  trigger_source: string;  // "scheduled" | "manual"
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
  trigger_filter?: string;
  created_at: string;
}

// ─── Daily Snapshots ────────────────────────────────────────────────────────

export async function fetchDaily(date: string, time: string): Promise<DailySnapshot[]> {
  const res = await fetch(`${BASE}/daily?date=${date}&time=${encodeURIComponent(time)}`);
  if (!res.ok) throw new Error("Failed to fetch daily snapshots");
  return res.json();
}

export async function fetchRuns(): Promise<RunInfo[]> {
  const res = await fetch(`${BASE}/runs`);
  if (!res.ok) return [];
  return res.json();
}

// ─── On-Demand Report ───────────────────────────────────────────────────────

export async function generateReport(
  dateFrom: string,
  dateTo: string,
  triggerSource: string = "all",
): Promise<ReportResult> {
  const res = await fetch(
    `${BASE}/report?date_from=${dateFrom}&date_to=${dateTo}&trigger_source=${triggerSource}`,
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
  const timeout = setTimeout(() => controller.abort(), 30 * 60 * 1000); // 30 min (retries may take long)
  try {
    const res = await fetch(`${BASE}/run`, { method: "POST", signal: controller.signal });
    if (!res.ok) throw new Error("Failed to trigger run");
  } finally {
    clearTimeout(timeout);
  }
}
