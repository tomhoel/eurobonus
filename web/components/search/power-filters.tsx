"use client";

import { Switch } from "@/components/ui/switch";
import type { SearchFilters, AvailabilityTrend } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface PowerFiltersProps {
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
}

const TREND_OPTIONS: { value: AvailabilityTrend; label: string }[] = [
  { value: "any", label: "Any" },
  { value: "increasing", label: "↑" },
  { value: "decreasing", label: "↓" },
  { value: "stable", label: "—" },
];

export function PowerFilters({ filters, updateFilter }: PowerFiltersProps) {
  return (
    <div className="space-y-5">
      <h4 className={`text-[10px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.22)] ${mono}`}>
        Power User
      </h4>

      <div className="space-y-2">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">
          Availability trend
        </span>
        <div className="flex gap-1">
          {TREND_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => updateFilter("availabilityTrend", opt.value)}
              className={`rounded-md px-3 py-1.5 text-[11px] font-medium transition-colors ${mono} ${
                filters.availabilityTrend === opt.value
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "bg-[hsla(0,0%,100%,.03)] text-[hsla(0,0%,100%,.25)] hover:bg-[hsla(0,0%,100%,.06)]"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">
          Include partners
        </span>
        <Switch
          checked={filters.includePartners}
          onCheckedChange={(checked) => updateFilter("includePartners", !!checked)}
        />
      </div>

      <div className="space-y-2">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Min seats</span>
        <div className="flex gap-1">
          {[1, 2, 3, 4].map((n) => (
            <button
              key={n}
              onClick={() => updateFilter("minSeats", n)}
              className={`rounded-md px-3 py-1.5 text-[11px] font-medium transition-colors ${mono} ${
                filters.minSeats === n
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "bg-[hsla(0,0%,100%,.03)] text-[hsla(0,0%,100%,.25)] hover:bg-[hsla(0,0%,100%,.06)]"
              }`}
            >
              {n}+
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
