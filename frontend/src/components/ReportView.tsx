import { useState } from "react";
import Markdown from "react-markdown";
import { generateReport } from "../api";
import type { ReportResult } from "../api";

export default function ReportView() {
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [report, setReport] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate() {
    if (!dateFrom || !dateTo) return;
    setLoading(true);
    setError("");
    setReport(null);
    try {
      const result = await generateReport(dateFrom, dateTo);
      setReport(result);
    } catch {
      setError("เกิดข้อผิดพลาดในการสร้างรายงาน");
    } finally {
      setLoading(false);
    }
  }

  function handleExportPDF() {
    window.print();
  }

  return (
    <div className="report-view">
      <div className="report-controls">
        <label className="date-label">
          จาก
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="date-input" />
        </label>
        <label className="date-label">
          ถึง
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="date-input" />
        </label>
        <button className="btn-generate" onClick={handleGenerate} disabled={loading || !dateFrom || !dateTo}>
          {loading ? "กำลังสร้างรายงาน..." : "สร้างรายงาน"}
        </button>
        {report && (
          <button className="btn-export" onClick={handleExportPDF}>
            Export PDF
          </button>
        )}
      </div>

      {error && <div className="error-state">{error}</div>}

      {loading && (
        <div className="loading-state">กำลังให้ Gemini วิเคราะห์ข้อมูล... อาจใช้เวลาสักครู่</div>
      )}

      {report && (
        <div className="report-content" id="report-print-area">
          <Markdown>{report.report_md}</Markdown>
        </div>
      )}
    </div>
  );
}
