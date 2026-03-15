"use client";

import { AirportSelector } from "./airport-selector";
import { DateRangePicker } from "./date-range-picker";
import { CabinSelector } from "./cabin-selector";
import { SwapButton } from "./swap-button";
import type { SearchFilters } from "@/lib/search/types";

interface SearchInputsProps {
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
  setFilters: (filters: SearchFilters) => void;
}

export function SearchInputs({ filters, updateFilter, setFilters }: SearchInputsProps) {
  const handleSwap = () => {
    setFilters({ ...filters, origin: filters.destination, destination: filters.origin });
  };

  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:gap-0">
      {/* Route pair — joined with swap */}
      <div className="relative flex flex-1 rounded-lg border border-[hsla(0,0%,100%,.1)] sm:rounded-r-none sm:border-r-0">
        <div className="flex-1">
          <AirportSelector
            value={filters.origin}
            onChange={(code) => updateFilter("origin", code)}
            label="From"
          />
        </div>
        <div className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2">
          <SwapButton onSwap={handleSwap} />
        </div>
        <div className="flex-1 border-l border-[hsla(0,0%,100%,.06)] pl-5">
          <AirportSelector
            value={filters.destination}
            onChange={(code) => updateFilter("destination", code)}
            label="To"
            fromOrigin={filters.origin}
          />
        </div>
      </div>

      {/* Date */}
      <div className="rounded-lg border border-[hsla(0,0%,100%,.1)] sm:rounded-none sm:border-l-0 sm:border-r-0">
        <DateRangePicker
          dateFrom={filters.dateFrom}
          dateTo={filters.dateTo}
          month={filters.month}
          onDateChange={(from, to) => setFilters({ ...filters, dateFrom: from, dateTo: to })}
          onMonthChange={(m) => updateFilter("month", m)}
        />
      </div>

      {/* Cabin */}
      <div className="rounded-lg border border-[hsla(0,0%,100%,.1)] sm:rounded-l-none sm:border-l-0">
        <CabinSelector
          value={filters.cabin}
          onChange={(cabin) => updateFilter("cabin", cabin)}
        />
      </div>
    </div>
  );
}
