interface Props {
  mode: "latest" | "snapshot";
  selectedDate: string;
  selectedSlot: string;
  availableDates: string[];
  availableSlots: string[];
  onLatest: () => void;
  onDateChange: (date: string) => void;
  onSlotChange: (slot: string) => void;
}

export default function FilterBar({
  mode, selectedDate, selectedSlot,
  availableDates, availableSlots,
  onLatest, onDateChange, onSlotChange,
}: Props) {
  return (
    <div className="filter-bar">
      <button
        className={`btn-filter${mode === "latest" ? " active" : ""}`}
        onClick={onLatest}
      >
        ล่าสุด
      </button>

      <select
        className="filter-select"
        value={selectedDate}
        onChange={(e) => onDateChange(e.target.value)}
      >
        <option value="">— เลือกวันที่ —</option>
        {availableDates.map((d) => (
          <option key={d} value={d}>{d}</option>
        ))}
      </select>

      <select
        className="filter-select"
        value={selectedSlot}
        onChange={(e) => onSlotChange(e.target.value)}
        disabled={!selectedDate || availableSlots.length === 0}
      >
        <option value="">— เลือกเวลา —</option>
        {availableSlots.map((s) => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
    </div>
  );
}
