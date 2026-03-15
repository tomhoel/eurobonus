"use client";

import { useState } from "react";
import { useSearch } from "@/hooks/use-search";
import { SearchBar } from "@/components/search/search-bar";
import { SearchInputs } from "@/components/search/search-inputs";
import { FilterChips } from "@/components/search/filter-chips";
import { AdvancedFilters } from "@/components/search/advanced-filters";
import { SortControls } from "@/components/search/sort-controls";
import { ResultList } from "@/components/search/result-list";
import { ResultCalendar } from "@/components/search/result-calendar";
import { ResultMap } from "@/components/search/result-map";
import { AIPanel } from "@/components/search/ai-panel";
import { SearchSkeleton } from "@/components/search/search-skeleton";
import type { SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

export function SearchPage() {
  const {
    filters,
    updateFilter,
    setFilters,
    resetFilters,
    activeFilterCount,
    results,
    filteredResults,
    availableDates,
    isLoading,
    error,
    viewMode,
    setViewMode,
    selectDate,
  } = useSearch();

  const [advancedOpen, setAdvancedOpen] = useState(false);

  const handleApplyPartialFilters = (partial: Partial<SearchFilters>) => {
    setFilters({ ...filters, ...partial });
  };

  const hasRoute = filters.origin && filters.destination;
  const hasDate = !!filters.dateFrom;
  const showResults = hasRoute && hasDate;

  return (
    <div className="relative min-h-[calc(100vh-64px)]">
      {/* Gradient orb — matches landing page */}
      <div className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[900px] -translate-x-1/2">
        <div
          className="h-full w-full rounded-full opacity-20 blur-[120px]"
          style={{
            background:
              "conic-gradient(from 220deg at 50% 50%, #064e3b 0deg, #1e3a8a 120deg, #7c3aed 240deg, #064e3b 360deg)",
          }}
        />
      </div>

      <div className="relative mx-auto max-w-[1200px] px-6 pb-20 pt-10">
        {/* Header */}
        <div className="mb-8">
          <h1
            className="text-[clamp(28px,4vw,40px)] font-bold leading-[1.1] tracking-[-0.035em]"
            style={{
              background:
                "linear-gradient(180deg, #fff 30%, hsla(0,0%,100%,.38) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Search flights
          </h1>
          <p className="mt-2 text-[15px] text-[hsla(0,0%,100%,.35)]">
            Find SAS EuroBonus bonus seats across the SkyTeam network.
          </p>
        </div>

        {/* Search controls card */}
        <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)]">
          {/* Window chrome */}
          <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.025)] px-5 py-[10px]">
            <div className="flex gap-[6px]">
              {[0, 1, 2].map((d) => (
                <div
                  key={d}
                  className="h-[12px] w-[12px] rounded-full bg-[hsla(0,0%,100%,.07)]"
                />
              ))}
            </div>
            <span
              className={`ml-3 text-[12px] text-[hsla(0,0%,100%,.22)] ${mono}`}
            >
              award search
            </span>
            {hasRoute && (
              <div className="ml-auto flex items-center gap-[6px]">
                <span className="h-[6px] w-[6px] rounded-full bg-emerald-500" />
                <span className="text-[11px] text-[hsla(0,0%,100%,.18)]">
                  live
                </span>
              </div>
            )}
          </div>

          {/* Search inputs */}
          <div className="space-y-4 bg-[hsla(0,0%,100%,.015)] p-5">
            <SearchBar onApplyFilters={handleApplyPartialFilters} />
            <SearchInputs
              filters={filters}
              updateFilter={updateFilter}
              setFilters={setFilters}
            />
          </div>
        </div>

        {/* Filter chips */}
        <div className="mt-4">
          <FilterChips
            filters={filters}
            updateFilter={updateFilter}
            activeCount={activeFilterCount}
            onToggleAdvanced={() => setAdvancedOpen(!advancedOpen)}
            advancedOpen={advancedOpen}
          />
        </div>

        {/* Advanced filters */}
        <div className="mt-3">
          <AdvancedFilters
            open={advancedOpen}
            filters={filters}
            updateFilter={updateFilter}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-[13px] text-red-400">
            {error}
          </div>
        )}

        {/* Main content */}
        {hasRoute && (
          <div className="mt-8">
            {showResults && (
              <div className="mb-5">
                <SortControls
                  resultCount={filteredResults.length}
                  sortBy={filters.sortBy}
                  viewMode={viewMode}
                  onSortChange={(sort) => updateFilter("sortBy", sort)}
                  onViewChange={setViewMode}
                />
              </div>
            )}

            <div className="flex gap-8">
              {/* Results area */}
              <div className="min-w-0 flex-1">
                {isLoading ? (
                  <SearchSkeleton />
                ) : viewMode === "calendar" || !hasDate ? (
                  <ResultCalendar
                    dates={availableDates}
                    onSelectDate={selectDate}
                    selectedDate={filters.dateFrom}
                  />
                ) : viewMode === "map" ? (
                  <ResultMap />
                ) : (
                  <ResultList
                    results={filteredResults}
                    isLoading={isLoading}
                  />
                )}
              </div>

              {/* AI panel (desktop) */}
              {showResults && (
                <AIPanel
                  results={results}
                  filteredResults={filteredResults}
                  filters={filters}
                  onApplyFilters={handleApplyPartialFilters}
                />
              )}
            </div>
          </div>
        )}

        {/* Empty state */}
        {!hasRoute && (
          <div className="mt-20 text-center">
            <div
              className="mx-auto text-[clamp(24px,3vw,32px)] font-bold tracking-[-0.03em]"
              style={{
                background:
                  "linear-gradient(180deg, hsla(0,0%,100%,.5) 0%, hsla(0,0%,100%,.15) 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              Select origin and destination to begin
            </div>
            <p className="mt-3 text-[14px] text-[hsla(0,0%,100%,.22)]">
              Search real-time bonus ticket availability across the SAS
              EuroBonus network.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
