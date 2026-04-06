import { useEffect, useState, useCallback } from "react";
import type { DailySnapshot, RunInfo } from "./api";
import { fetchDaily, fetchRuns, triggerRun } from "./api";
import CompanyCard from "./components/CompanyCard";
import ReportView from "./components/ReportView";

type Tab = "daily" | "report";
type Status = "idle" | "loading" | "error";

const COMPANY_ORDER = [
  "thailand_post", "nim_express", "best_express",
  "kex_express", "flash_express", "jnt_express", "tp_logistics",
];

function sortByCompanyOrder(items: DailySnapshot[]): DailySnapshot[] {
  return [...items].sort((a, b) => {
    const ia = COMPANY_ORDER.indexOf(a.company_id);
    const ib = COMPANY_ORDER.indexOf(b.company_id);
    return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
  });
}

function runKey(r: RunInfo): string {
  return `${r.date}_${r.time}`;
}

export default function App() {
  const [tab, setTab] = useState<Tab>("daily");
  const [data, setData] = useState<DailySnapshot[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [selectedRun, setSelectedRun] = useState("");     // "date_time"
  const [availableRuns, setAvailableRuns] = useState<RunInfo[]>([]);
  const [runStatus, setRunStatus] = useState("");
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const stored = localStorage.getItem("darkMode");
    return stored !== null ? stored === "true" : false;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("darkMode", String(darkMode));
  }, [darkMode]);

  // Load available runs on mount
  useEffect(() => {
    fetchRuns().then((runs) => {
      setAvailableRuns(runs);
      if (runs.length > 0 && !selectedRun) {
        setSelectedRun(runKey(runs[0]));
      }
    }).catch(console.error);
  }, []);

  // Load snapshots when selected run changes
  const loadDaily = useCallback(async (key: string) => {
    if (!key) return;
    const [date, time] = key.split("_");
    setStatus("loading");
    try {
      const result = await fetchDaily(date, time);
      setData(result);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (selectedRun) loadDaily(selectedRun);
  }, [selectedRun, loadDaily]);

  async function handleRunNow() {
    if (!window.confirm("ยืนยันการรัน Monitor Cycle?\nจะใช้เวลาประมาณ 2-5 นาที")) return;
    setRunStatus("กำลังรัน...");
    try {
      await triggerRun();
      setRunStatus("รันเสร็จแล้ว! กำลังโหลดข้อมูลใหม่...");
      const runs = await fetchRuns();
      setAvailableRuns(runs);
      if (runs.length > 0) {
        const key = runKey(runs[0]);
        setSelectedRun(key);
        await loadDaily(key);
      }
      setRunStatus("");
    } catch {
      setRunStatus("เกิดข้อผิดพลาด");
      setTimeout(() => setRunStatus(""), 3000);
    }
  }

  const currentRun = availableRuns.find((r) => runKey(r) === selectedRun);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-left">
          <h1 className="app-title">Competitor Monitor</h1>
          <span className="app-subtitle">ติดตามคู่แข่งตลาดโลจิสติกส์ไทย — TP Logistics</span>
        </div>
        <div className="header-right">
          <button className="btn-theme-toggle" onClick={() => setDarkMode(d => !d)} title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
            {darkMode ? "☀ Light" : "☾ Dark"}
          </button>
          <button className="btn-run" onClick={handleRunNow} disabled={!!runStatus}>
            {runStatus || "▶ รันตอนนี้"}
          </button>
        </div>
      </header>

      {/* Tabs */}
      <nav className="tab-bar">
        <button className={`tab-btn${tab === "daily" ? " active" : ""}`} onClick={() => setTab("daily")}>
          Daily Monitor
        </button>
        <button className={`tab-btn${tab === "report" ? " active" : ""}`} onClick={() => setTab("report")}>
          On-Demand Report
        </button>
      </nav>

      {/* Daily Monitor Tab */}
      {tab === "daily" && (
        <>
          <div className="filter-section">
            <select
              className="filter-select"
              value={selectedRun}
              onChange={(e) => setSelectedRun(e.target.value)}
            >
              <option value="">— เลือก Run —</option>
              {availableRuns.map((r) => (
                <option key={runKey(r)} value={runKey(r)}>
                  {r.date} {r.time} [{r.trigger_source === "scheduled" ? "Scheduled" : "Manual"}]
                </option>
              ))}
            </select>
            {currentRun && (
              <span className={`viewing-label ${currentRun.trigger_source === "scheduled" ? "label--scheduled" : "label--manual"}`}>
                {currentRun.date} {currentRun.time} — {currentRun.trigger_source === "scheduled" ? "Scheduled" : "Manual"}
              </span>
            )}
          </div>

          <div className="legend">
            <span className="legend-item">
              <span className="alert-badge">⚠ Risk</span> = Gemini ตรวจพบการเปลี่ยนแปลงที่กระทบ TP Logistics เช่น คู่แข่งขึ้นราคา, Fuel Surcharge, เปลี่ยน Policy
            </span>
            <span className="legend-item">
              Sentiment (ต่อแบรนด์นั้นๆ):
              <span className="sentiment-badge sentiment--positive">+5</span> ข่าวดีต่อแบรนด์
              <span className="sentiment-badge sentiment--neutral">0</span> เป็นกลาง/ไม่มีข้อมูล
              <span className="sentiment-badge sentiment--negative">-5</span> ข่าวลบต่อแบรนด์
            </span>
          </div>

          <main className="card-grid">
            {status === "loading" && (
              <div className="loading-state">กำลังโหลดข้อมูล...</div>
            )}
            {status === "error" && (
              <div className="error-state">เกิดข้อผิดพลาดในการโหลดข้อมูล</div>
            )}
            {status === "idle" && data.length === 0 && (
              <div className="empty-state">ยังไม่มีข้อมูลสำหรับ run นี้ — กด "รันตอนนี้" เพื่อเริ่มต้น</div>
            )}
            {status === "idle" && sortByCompanyOrder(data)
              .filter((s) => s.company_id !== "tp_logistics")
              .map((snapshot) => (
              <CompanyCard key={snapshot.id} data={snapshot} />
            ))}
          </main>
        </>
      )}

      {/* Report Tab */}
      {tab === "report" && <ReportView />}
    </div>
  );
}
