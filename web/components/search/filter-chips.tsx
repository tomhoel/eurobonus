"use client";

import { X, SlidersHorizontal } from "lucide-react";
import type { SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface FilterChipsProps {
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
  activeCount: number;
  onToggleAdvanced: () => void;
  advancedOpen: boolean;
}

interface Chip {
  key: keyof SearchFilters;
  label: string;
  accent: string;
  resetValue: unknown;
}

export function FilterChips({
  filters,
  updateFilter,
  activeCount,
  onToggleAdvanced,
  advancedOpen,
}: FilterChipsProps) {
  const chips: Chip[] = [];

  if (filters.cabin !== "ANY")
    chips.push({ key: "cabin", label: filters.cabin, accent: "emerald", resetValue: "ANY" });
  if (filters.maxPoints > 0)
    chips.push({ key: "maxPoints", label: `≤${(filters.maxPoints / 1000).toFixed(0)}k pts`, accent: "purple", resetValue: 0 });
  if (filters.bonusOnly)
    chips.push({ key: "bonusOnly", label: "Bonus only", accent: "emerald", resetValue: false });
  if (filters.maxStops !== null)
    chips.push({
      key: "maxStops",
      label: filters.maxStops === 0 ? "Direct" : `≤${filters.maxStops} stop${filters.maxStops > 1 ? "s" : ""}`,
      accent: "blue",
      resetValue: null,
    });
  if (filters.airlines.length > 0)
    chips.push({ key: "airlines", label: filters.airlines.join(" "), accent: "blue", resetValue: [] });
  if (filters.departureTime !== "any")
    chips.push({ key: "departureTime", label: filters.departureTime, accent: "blue", resetValue: "any" });
  if (filters.maxDuration > 0)
    chips.push({ key: "maxDuration", label: `≤${Math.floor(filters.maxDuration / 60)}h`, accent: "blue", resetValue: 0 });
  if (!filters.includePartners)
    chips.push({ key: "includePartners", label: "SAS only", accent: "purple", resetValue: true });
  if (filters.minSeats > 1)
    chips.push({ key: "minSeats", label: `${filters.minSeats}+ seats`, accent: "purple", resetValue: 1 });

  const accentStyles: Record<string, string> = {
    emerald: "border-emerald-500/15 text-emerald-400/80",
    purple: "border-purple-400/15 text-purple-400/80",
    blue: "border-blue-400/15 text-blue-400/80",
  };

  if (chips.length === 0 && activeCount === 0) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {chips.map((chip) => (
        <span
          key={chip.key}
          className={`inline-flex items-center gap-1.5 rounded-full border bg-[hsla(0,0%,100%,.02)] px-2.5 py-[3px] text-[11px] ${mono} ${accentStyles[chip.accent]}`}
        >
          {chip.label}
          <button
            onClick={() =>
              updateFilter(chip.key, chip.resetValue as SearchFilters[typeof chip.key])
            }
            className="rounded-full p-[1px] transition-colors hover:bg-[hsla(0,0%,100%,.08)]"
          >
            <X className="size-[10px]" />
          </button>
        </span>
      ))}
      <button
        onClick={onToggleAdvanced}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-[3px] text-[11px] transition-colors ${mono} ${
          advancedOpen
            ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
            : "border-[hsla(0,0%,100%,.06)] text-[hsla(0,0%,100%,.25)] hover:border-[hsla(0,0%,100%,.12)] hover:text-[hsla(0,0%,100%,.4)]"
        }`}
      >
        <SlidersHorizontal className="size-[10px]" />
        {advancedOpen ? "Hide" : "+ Filters"}
      </button>
    </div>
  );
}
