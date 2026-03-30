const BASE = "/api";

export interface CompanyData {
  company_id: string;
  company_name: string;
  summary?: string;   // from competitor_summary
  content?: string;   // from competitor_snapshots
  has_alert: boolean;
  updated_at?: string;
  snapshot_date?: string;
  snapshot_time_slot?: string;
}

export async function fetchSummaries(): Promise<CompanyData[]> {
  const res = await fetch(`${BASE}/summaries`);
  if (!res.ok) throw new Error("Failed to fetch summaries");
  return res.json();
}

export async function fetchSnapshots(date: string, slot: string): Promise<CompanyData[]> {
  const res = await fetch(`${BASE}/snapshots?date=${date}&slot=${encodeURIComponent(slot)}`);
  if (!res.ok) throw new Error("Failed to fetch snapshots");
  return res.json();
}

export async function fetchDates(): Promise<string[]> {
  const res = await fetch(`${BASE}/dates`);
  if (!res.ok) return [];
  return res.json();
}

export async function fetchSlots(date: string): Promise<string[]> {
  const res = await fetch(`${BASE}/slots?date=${date}`);
  if (!res.ok) return [];
  return res.json();
}

export async function triggerRun(): Promise<void> {
  const res = await fetch(`${BASE}/run`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger run");
}
