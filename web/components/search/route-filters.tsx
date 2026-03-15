"use client";

import { Slider } from "@/components/ui/slider";
import type { SearchFilters, TimeRange } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface RouteFiltersProps {
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
}

const STOP_OPTIONS: { value: number | null; label: string }[] = [
  { value: null, label: "Any" },
  { value: 0, label: "Direct" },
  { value: 1, label: "1" },
  { value: 2, label: "2" },
];

const TIME_OPTIONS: { value: TimeRange; label: string }[] = [
  { value: "any", label: "Any" },
  { value: "morning", label: "AM" },
  { value: "afternoon", label: "PM" },
  { value: "evening", label: "Eve" },
  { value: "night", label: "Night" },
];

const AIRLINES = [
  { code: "SK", name: "SAS" },
  { code: "AF", name: "Air France" },
  { code: "KL", name: "KLM" },
  { code: "DL", name: "Delta" },
  { code: "TG", name: "Thai" },
  { code: "KE", name: "Korean" },
  { code: "CZ", name: "China S." },
  { code: "GA", name: "Garuda" },
];

export function RouteFilters({ filters, updateFilter }: RouteFiltersProps) {
  const toggleAirline = (code: string) => {
    const next = filters.airlines.includes(code)
      ? filters.airlines.filter((c) => c !== code)
      : [...filters.airlines, code];
    updateFilter("airlines", next);
  };

  return (
    <div className="space-y-5">
      <h4 className={`text-[10px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.22)] ${mono}`}>
        Route & Schedule
      </h4>

      <div className="space-y-2">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Max stops</span>
        <div className="flex gap-1">
          {STOP_OPTIONS.map((opt) => (
            <button
              key={String(opt.value)}
              onClick={() => updateFilter("maxStops", opt.value)}
              className={`rounded-md px-3 py-1.5 text-[11px] font-medium transition-colors ${mono} ${
                filters.maxStops === opt.value
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "bg-[hsla(0,0%,100%,.03)] text-[hsla(0,0%,100%,.25)] hover:bg-[hsla(0,0%,100%,.06)]"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Airlines</span>
        <div className="flex flex-wrap gap-1">
          {AIRLINES.map((a) => (
            <button
              key={a.code}
              onClick={() => toggleAirline(a.code)}
              className={`rounded border px-2 py-1 text-[11px] transition-colors ${mono} ${
                filters.airlines.includes(a.code)
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-400"
                  : "border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] text-[hsla(0,0%,100%,.25)] hover:border-[hsla(0,0%,100%,.12)]"
              }`}
            >
              {a.code}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Departure</span>
        <div className="flex flex-wrap gap-1">
          {TIME_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => updateFilter("departureTime", opt.value)}
              className={`rounded-md px-2.5 py-1.5 text-[11px] font-medium transition-colors ${mono} ${
                filters.departureTime === opt.value
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "bg-[hsla(0,0%,100%,.03)] text-[hsla(0,0%,100%,.25)] hover:bg-[hsla(0,0%,100%,.06)]"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Max duration</span>
          <span className={`text-[12px] text-emerald-400/80 ${mono}`}>
            {filters.maxDuration > 0 ? `${Math.floor(filters.maxDuration / 60)}h` : "Any"}
          </span>
        </div>
        <Slider
          min={0}
          max={2400}
          value={[filters.maxDuration]}
          onValueChange={(val) => updateFilter("maxDuration", Array.isArray(val) ? val[0] : val)}
          step={60}
          className="[&_[data-slot=slider-range]]:bg-emerald-500 [&_[data-slot=slider-thumb]]:border-emerald-500"
        />
      </div>
    </div>
  );
}
