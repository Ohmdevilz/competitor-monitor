import type { CompanyData } from "../api";

interface Props {
  data: CompanyData;
  mode: "latest" | "snapshot";
}

function formatDate(iso: string | undefined): string {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString("th-TH", {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
    timeZone: "Asia/Bangkok",
  });
}

export default function CompanyCard({ data, mode }: Props) {
  const content = mode === "latest" ? (data.summary ?? "") : (data.content ?? "");
  const updatedAt = mode === "latest" ? data.updated_at : data.snapshot_date
    ? `${data.snapshot_date} ${data.snapshot_time_slot}`
    : undefined;

  return (
    <div className={`company-card${data.has_alert ? " company-card--alert" : ""}`}>
      <div className="card-header">
        <span className="company-name">{data.company_name}</span>
        {data.has_alert && <span className="alert-badge">⚠ ประกาศใหม่</span>}
      </div>

      <div className="card-meta">
        อัปเดต: {mode === "latest" ? formatDate(data.updated_at) : updatedAt ?? "-"}
      </div>

      <div className="card-content">
        {content || <span className="no-data">ยังไม่มีข้อมูล</span>}
      </div>
    </div>
  );
}
