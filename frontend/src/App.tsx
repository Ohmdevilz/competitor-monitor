import { useEffect, useState, useCallback } from "react";
import type { DailySnapshot } from "./api";
import { fetchDaily, fetchDates, triggerRun } from "./api";
import CompanyCard from "./components/CompanyCard";
import ReportView from "./components/ReportView";

type Tab = "daily" | "report";
type Status = "idle" | "loading" | "error";

export default function App() {
  const [tab, setTab] = useState<Tab>("daily");
  const [data, setData] = useState<DailySnapshot[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [selectedDate, setSelectedDate] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [runStatus, setRunStatus] = useState("");
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const stored = localStorage.getItem("darkMode");
    return stored !== null ? stored === "true" : false;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("darkMode", String(darkMode));
  }, [darkMode]);

  // Load available dates on mount
  useEffect(() => {
    fetchDates().then((dates) => {
      setAvailableDates(dates);
      if (dates.length > 0 && !selectedDate) {
        setSelectedDate(dates[0]);
      }
    }).catch(console.error);
  }, []);

  // Load daily snapshots when date changes
  const loadDaily = useCallback(async (date: string) => {
    if (!date) return;
    setStatus("loading");
    try {
      const result = await fetchDaily(date);
      setData(result);
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }, []);

  useEffect(() => {
    if (selectedDate) loadDaily(selectedDate);
  }, [selectedDate, loadDaily]);

  async function handleRunNow() {
    setRunStatus("กำลังรัน...");
    try {
      await triggerRun();
      setRunStatus("รันเสร็จแล้ว! กำลังโหลดข้อมูลใหม่...");
      const dates = await fetchDates();
      setAvailableDates(dates);
      if (dates.length > 0) {
        setSelectedDate(dates[0]);
        await loadDaily(dates[0]);
      }
      setRunStatus("");
    } catch {
      setRunStatus("เกิดข้อผิดพลาด");
      setTimeout(() => setRunStatus(""), 3000);
    }
  }

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
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
            >
              <option value="">— เลือกวันที่ —</option>
              {availableDates.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
            {selectedDate && (
              <span className="viewing-label">
                แสดงข้อมูลวันที่ {selectedDate}
              </span>
            )}
          </div>

          <main className="card-grid">
            {status === "loading" && (
              <div className="loading-state">กำลังโหลดข้อมูล...</div>
            )}
            {status === "error" && (
              <div className="error-state">เกิดข้อผิดพลาดในการโหลดข้อมูล</div>
            )}
            {status === "idle" && data.length === 0 && (
              <div className="empty-state">ยังไม่มีข้อมูลสำหรับวันนี้ — กด "รันตอนนี้" เพื่อเริ่มต้น</div>
            )}
            {status === "idle" && data.map((snapshot) => (
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
