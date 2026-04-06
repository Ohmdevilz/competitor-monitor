import { useEffect, useState } from "react";
import Markdown from "react-markdown";
import { generateReport, fetchReports } from "../api";
import type { ReportResult, SavedReport } from "../api";

export default function ReportView() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [report, setReport] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [history, setHistory] = useState<SavedReport[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [viewingHistory, setViewingHistory] = useState<SavedReport | null>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    setHistoryLoading(true);
    const reports = await fetchReports();
    setHistory(reports);
    setHistoryLoading(false);
  }

  async function handleGenerate() {
    if (!dateFrom || !dateTo) return;
    if (!window.confirm(`ยืนยันสร้างรายงาน?\nช่วง ${dateFrom} ถึง ${dateTo}\nอาจใช้เวลาสักครู่`)) return;
    setLoading(true);
    setError("");
    setReport(null);
    setViewingHistory(null);
    try {
      const result = await generateReport(dateFrom, dateTo, sourceFilter);
      setReport(result);
      await loadHistory();
    } catch {
      setError("เกิดข้อผิดพลาดในการสร้างรายงาน");
    } finally {
      setLoading(false);
    }
  }

  function handleExportPDF() {
    window.print();
  }

  function handleViewHistory(item: SavedReport) {
    setViewingHistory(item);
    setReport(null);
  }

  function handleBackToNew() {
    setViewingHistory(null);
  }

  const displayReport = viewingHistory
    ? { report_md: viewingHistory.report_md, date_from: viewingHistory.date_from, date_to: viewingHistory.date_to }
    : report;

  return (
    <div className="report-view">
      {/* Generate controls */}
      <div className="report-controls">
        <label className="date-label">
          จาก
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="date-input" />
        </label>
        <label className="date-label">
          ถึง
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="date-input" />
        </label>
        <label className="date-label">
          ข้อมูลจาก
          <select className="filter-select" value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
            <option value="all">All</option>
            <option value="scheduled">Scheduled เท่านั้น</option>
            <option value="manual">Manual เท่านั้น</option>
          </select>
        </label>
        <button className="btn-generate" onClick={handleGenerate} disabled={loading || !dateFrom || !dateTo}>
          {loading ? "กำลังสร้างรายงาน..." : "สร้างรายงาน"}
        </button>
        {displayReport && (
          <button className="btn-export" onClick={handleExportPDF}>
            Export PDF
          </button>
        )}
      </div>

      {error && <div className="error-state">{error}</div>}

      {loading && (
        <div className="loading-state">กำลังให้ Gemini วิเคราะห์ข้อมูล... อาจใช้เวลาสักครู่</div>
      )}

      {/* Active report display */}
      {displayReport && (
        <>
          {viewingHistory && (
            <div className="history-viewing-bar">
              <span>กำลังดูรายงานเก่า: {viewingHistory.date_from} ถึง {viewingHistory.date_to}</span>
              <button className="btn-back" onClick={handleBackToNew}>กลับ</button>
            </div>
          )}
          <div className="report-content" id="report-print-area">
            <Markdown>{displayReport.report_md}</Markdown>
          </div>
        </>
      )}

      {/* History section */}
      {!loading && !displayReport && (
        <div className="report-history">
          <h3 className="history-title">รายงานที่เคยสร้าง</h3>
          {historyLoading && <div className="loading-state">กำลังโหลด...</div>}
          {!historyLoading && history.length === 0 && (
            <div className="empty-state">ยังไม่มีรายงาน — เลือกช่วงวันที่แล้วกด "สร้างรายงาน"</div>
          )}
          {!historyLoading && history.map((item) => (
            <button key={item.id} className="history-item" onClick={() => handleViewHistory(item)}>
              <div className="history-item-dates">
                {item.date_from} ถึง {item.date_to}
              </div>
              <div className="history-item-meta">
                สร้างเมื่อ {new Date(item.created_at).toLocaleString("th-TH", { timeZone: "Asia/Bangkok" })}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
