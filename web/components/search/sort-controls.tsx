"use client";

import { List, CalendarDays, Map } from "lucide-react";
import type { SortOption, ViewMode } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface SortControlsProps {
  resultCount: number;
  sortBy: SortOption;
  viewMode: ViewMode;
  onSortChange: (sort: SortOption) => void;
  onViewChange: (view: ViewMode) => void;
}

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "best-value", label: "Best value" },
  { value: "lowest-points", label: "Lowest points" },
  { value: "shortest", label: "Shortest" },
  { value: "fewest-stops", label: "Fewest stops" },
];

const VIEW_OPTIONS: { value: ViewMode; icon: typeof List; label: string }[] = [
  { value: "list", icon: List, label: "List" },
  { value: "calendar", icon: CalendarDays, label: "Calendar" },
  { value: "map", icon: Map, label: "Map" },
];

export function SortControls({
  resultCount,
  sortBy,
  viewMode,
  onSortChange,
  onViewChange,
}: SortControlsProps) {
  return (
    <div className="flex items-center justify-between border-b border-[hsla(0,0%,100%,.06)] pb-4">
      <div className="text-[13px] text-[hsla(0,0%,100%,.35)]">
        <span className={`font-bold text-[hsla(0,0%,100%,.75)] ${mono}`}>
          {resultCount}
        </span>{" "}
        flight{resultCount !== 1 ? "s" : ""} found
      </div>

      <div className="flex items-center gap-3">
        <select
          value={sortBy}
          onChange={(e) => onSortChange(e.target.value as SortOption)}
          className={`rounded-md border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] px-2.5 py-1.5 text-[11px] text-[hsla(0,0%,100%,.4)] outline-none ${mono}`}
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <div className="flex rounded-md border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)]">
          {VIEW_OPTIONS.map(({ value, icon: Icon, label }) => (
            <button
              key={value}
              onClick={() => onViewChange(value)}
              title={label}
              className={`p-2 transition-colors first:rounded-l-md last:rounded-r-md ${
                viewMode === value
                  ? "bg-emerald-500/15 text-emerald-400"
                  : "text-[hsla(0,0%,100%,.18)] hover:text-[hsla(0,0%,100%,.4)]"
              }`}
            >
              <Icon className="size-3.5" />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
