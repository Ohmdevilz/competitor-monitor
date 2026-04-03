import type { DailySnapshot } from "../api";

interface Props {
  data: DailySnapshot;
}

function sentimentColor(label: string | null): string {
  if (label === "positive") return "sentiment--positive";
  if (label === "negative") return "sentiment--negative";
  return "sentiment--neutral";
}

function formatScore(score: number | null): string {
  if (score === null) return "N/A";
  const sign = score > 0 ? "+" : "";
  return `${sign}${score.toFixed(1)}`;
}

function parseThemes(raw: unknown): string[] {
  if (Array.isArray(raw)) return raw;
  if (typeof raw === "string") {
    try { const parsed = JSON.parse(raw); if (Array.isArray(parsed)) return parsed; } catch {}
    return raw ? raw.split(",").map((s) => s.trim()).filter(Boolean) : [];
  }
  return [];
}

export default function CompanyCard({ data }: Props) {
  const themes = parseThemes(data.top_themes);
  return (
    <div className={`company-card${data.risk_flag ? " company-card--alert" : ""}`}>
      <div className="card-header">
        <span className="company-name">{data.company_name}</span>
        <div className="card-badges">
          {data.risk_flag && <span className="alert-badge">⚠ Risk</span>}
          <span className={`sentiment-badge ${sentimentColor(data.sentiment_label)}`}>
            {formatScore(data.sentiment_score)}
          </span>
        </div>
      </div>

      <div className="card-meta">
        {data.snapshot_date}
        {data.sentiment_label && (
          <span className={`label-tag ${sentimentColor(data.sentiment_label)}`}>
            {data.sentiment_label}
          </span>
        )}
      </div>

      {themes.length > 0 && (
        <div className="card-themes">
          {themes.map((t) => (
            <span key={t} className="theme-tag">{t}</span>
          ))}
        </div>
      )}

      <div className="card-content">
        {data.summary || data.raw_news || <span className="no-data">ยังไม่มีข้อมูล</span>}
      </div>

      {data.action_items && data.company_id !== "tp_logistics" && (
        <div className="card-action">
          <strong>Action:</strong> {data.action_items}
        </div>
      )}
    </div>
  );
}
