import { useEffect, useState, useCallback } from "react";
import type { CompanyData } from "./api";
import { fetchSummaries, fetchSnapshots, fetchDates, fetchSlots, triggerRun } from "./api";
import CompanyCard from "./components/CompanyCard";
import FilterBar from "./components/FilterBar";

type Mode = "latest" | "snapshot";
type Status = "idle" | "loading" | "error";

export default function App() {
  const [mode, setMode] = useState<Mode>("latest");
  const [data, setData] = useState<CompanyData[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedSlot, setSelectedSlot] = useState("");
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [availableSlots, setAvailableSlots] = useState<string[]>([]);
  const [runStatus, setRunStatus] = useState("");
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    const stored = localStorage.getItem("darkMode");
    return stored !== null ? stored === "true" : true;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", darkMode ? "dark" : "light");
    localStorage.setItem("darkMode", String(darkMode));
  }, [darkMode]);

  // Load available dates on mount
  useEffect(() => {
    fetchDates().then(setAvailableDates).catch(console.error);
  }, []);

  const loadLatest = useCallback(async () => {
    setStatus("loading");
    try {
      const result = await fetchSummaries();
      setData(result);
      setMode("latest");
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }, []);

  // Load latest on mount
  useEffect(() => { loadLatest(); }, [loadLatest]);

  async function handleDateChange(date: string) {
    setSelectedDate(date);
    setSelectedSlot("");
    setData([]);
    if (!date) { loadLatest(); return; }
    const slots = await fetchSlots(date);
    setAvailableSlots(slots);
  }

  async function handleSlotChange(slot: string) {
    setSelectedSlot(slot);
    if (!slot || !selectedDate) return;
    setStatus("loading");
    try {
      const result = await fetchSnapshots(selectedDate, slot);
      setData(result);
      setMode("snapshot");
      setStatus("idle");
    } catch {
      setStatus("error");
    }
  }

  function handleLatest() {
    setSelectedDate("");
    setSelectedSlot("");
    setAvailableSlots([]);
    loadLatest();
  }

  async function handleRunNow() {
    setRunStatus("กำลังรัน...");
    try {
      await triggerRun();
      setRunStatus("รันเสร็จแล้ว! กำลังโหลดข้อมูลใหม่...");
      await loadLatest();
      const dates = await fetchDates();
      setAvailableDates(dates);
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
          <span className="app-subtitle">ติดตามคู่แข่งตลาดโลจิสติกส์ไทย</span>
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

      <div className="filter-section">
        <FilterBar
          mode={mode}
          selectedDate={selectedDate}
          selectedSlot={selectedSlot}
          availableDates={availableDates}
          availableSlots={availableSlots}
          onLatest={handleLatest}
          onDateChange={handleDateChange}
          onSlotChange={handleSlotChange}
        />
        {mode === "snapshot" && selectedDate && selectedSlot && (
          <span className="viewing-label">
            ดู Snapshot: {selectedDate} เวลา {selectedSlot}
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
          <div className="empty-state">ยังไม่มีข้อมูล — กด "รันตอนนี้" เพื่อเริ่มต้น</div>
        )}
        {status === "idle" && data.map((company) => (
          <CompanyCard key={company.company_id} data={company} mode={mode} />
        ))}
      </main>
    </div>
  );
}
