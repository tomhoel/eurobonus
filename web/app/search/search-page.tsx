"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { Loader2, Plane, Clock, Radio, Zap, ArrowRight } from "lucide-react";
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
import { RouteDiscovery } from "@/components/search/route-discovery";
import type { SearchFilters } from "@/lib/search/types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const GlobeView = dynamic<any>(
  () => import("@/components/search/globe-view").then((m) => m.GlobeView),
  { ssr: false, loading: () => <div className="flex h-full items-center justify-center"><Loader2 className="size-5 animate-spin text-emerald-400/20" /></div> },
);

const mono = "font-[family-name:var(--font-geist-mono)]";

interface DiscoveryDest {
  code: string;
  city: string;
  lat: number;
  lng: number;
  totalSeats: number;
  hasBusiness: boolean;
}

// Flagship SAS routes shown on the globe before the user picks an origin
const DEFAULT_GLOBE_DESTS: DiscoveryDest[] = [
  { code: "BKK", city: "Bangkok", lat: 13.68, lng: 100.75, totalSeats: 30, hasBusiness: true },
  { code: "NRT", city: "Tokyo", lat: 35.76, lng: 140.39, totalSeats: 20, hasBusiness: true },
  { code: "SIN", city: "Singapore", lat: 1.35, lng: 103.99, totalSeats: 15, hasBusiness: true },
  { code: "JFK", city: "New York", lat: 40.64, lng: -73.78, totalSeats: 25, hasBusiness: true },
  { code: "LHR", city: "London", lat: 51.47, lng: -0.46, totalSeats: 40, hasBusiness: true },
  { code: "CDG", city: "Paris", lat: 49.01, lng: 2.55, totalSeats: 35, hasBusiness: false },
  { code: "BCN", city: "Barcelona", lat: 41.30, lng: 2.08, totalSeats: 20, hasBusiness: false },
  { code: "FCO", city: "Rome", lat: 41.80, lng: 12.25, totalSeats: 18, hasBusiness: false },
  { code: "ATH", city: "Athens", lat: 37.94, lng: 23.94, totalSeats: 14, hasBusiness: false },
  { code: "IST", city: "Istanbul", lat: 41.28, lng: 28.75, totalSeats: 22, hasBusiness: true },
  { code: "CPH", city: "Copenhagen", lat: 55.62, lng: 12.66, totalSeats: 50, hasBusiness: true },
  { code: "ARN", city: "Stockholm", lat: 59.65, lng: 17.94, totalSeats: 45, hasBusiness: true },
  { code: "HEL", city: "Helsinki", lat: 60.32, lng: 24.96, totalSeats: 30, hasBusiness: false },
  { code: "AMS", city: "Amsterdam", lat: 52.31, lng: 4.76, totalSeats: 35, hasBusiness: false },
  { code: "MIA", city: "Miami", lat: 25.79, lng: -80.29, totalSeats: 12, hasBusiness: true },
];

// ── SAS EuroBonus award chart (from 1 Dec 2025) ──
// Points per one-way, excluding taxes/fees.
// Regions: domestic (within NO/SE/DK), nordic+ (between Nordic+),
//          nordic-europe (Nordic+ ↔ Europe), europe (intra-Europe),
//          long-haul (to/from Asia & North America)
interface AwardPricing { economy: string; premium: string; business: string }

const AWARD_CHART: Record<string, AwardPricing> = {
  domestic:        { economy: "5,000",  premium: "10,000", business: "—" },
  "nordic+":       { economy: "10,000", premium: "—",      business: "20,000" },
  "nordic-europe": { economy: "15,000", premium: "—",      business: "35,000" },
  europe:          { economy: "25,000", premium: "—",      business: "40,000" },
  "long-haul":     { economy: "30,000", premium: "45,000", business: "60,000" },
};

const AIRPORT_COUNTRY: Record<string, string> = {
  OSL: "NO", BGO: "NO", TRD: "NO", SVG: "NO",
  CPH: "DK",
  ARN: "SE", GOT: "SE",
  HEL: "FI", KEF: "IS",
  TLL: "EE", RIX: "LV",
};
const DOMESTIC_COUNTRIES = new Set(["NO", "SE", "DK"]);
const NORDIC_COUNTRIES = new Set(["NO", "SE", "DK", "FI", "IS", "EE", "LV", "LT"]);
const LONG_HAUL_CODES = new Set([
  "BKK", "NRT", "HND", "SIN", "HKG", "ICN", "PEK", "PVG", "DEL", "BOM",
  "SGN", "HAN", "KIX", "JFK", "LAX", "SFO", "ORD", "MIA", "EWR", "IAD",
  "BOS", "YYZ", "CPT", "NBO",
]);

function getRoutePricing(origin: string, dest: string): { tier: string; pricing: AwardPricing } {
  if (LONG_HAUL_CODES.has(origin) || LONG_HAUL_CODES.has(dest)) {
    return { tier: "To/from Asia & North America", pricing: AWARD_CHART["long-haul"] };
  }
  const oC = AIRPORT_COUNTRY[origin];
  const dC = AIRPORT_COUNTRY[dest];
  const oNordic = oC ? NORDIC_COUNTRIES.has(oC) : false;
  const dNordic = dC ? NORDIC_COUNTRIES.has(dC) : false;
  // Same domestic country
  if (oC && dC && oC === dC && DOMESTIC_COUNTRIES.has(oC)) {
    return { tier: "Domestic", pricing: AWARD_CHART.domestic };
  }
  // Both Nordic+
  if (oNordic && dNordic) {
    return { tier: "Between Nordic+", pricing: AWARD_CHART["nordic+"] };
  }
  // One Nordic+, one Europe
  if (oNordic || dNordic) {
    return { tier: "Nordic+ ↔ Europe", pricing: AWARD_CHART["nordic-europe"] };
  }
  // Both Europe
  return { tier: "Intra-Europe", pricing: AWARD_CHART.europe };
}

// Popular route quick-picks (correct Dec 2025 pricing)
const POPULAR_ROUTES = [
  { from: "OSL", to: "BKK", label: "Oslo → Bangkok", cabin: "Business", pts: "60,000" },
  { from: "CPH", to: "NRT", label: "Copenhagen → Tokyo", cabin: "Economy", pts: "30,000" },
  { from: "ARN", to: "JFK", label: "Stockholm → New York", cabin: "Business", pts: "60,000" },
  { from: "OSL", to: "SIN", label: "Oslo → Singapore", cabin: "Economy", pts: "30,000" },
];

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
  const [discoveryDismissed, setDiscoveryDismissed] = useState(false);
  const [hoveredDest, setHoveredDest] = useState<string | null>(null);
  const [discoveryDests, setDiscoveryDests] = useState<DiscoveryDest[]>([]);

  const showDiscovery = !!filters.origin && !filters.destination && !discoveryDismissed;

  const handleApplyPartialFilters = (partial: Partial<SearchFilters>) => {
    setFilters({ ...filters, ...partial });
  };

  const handleSelectDiscoveryDest = (code: string) => {
    updateFilter("destination", code);
    setDiscoveryDismissed(true);
  };

  const handleQuickRoute = (from: string, to: string) => {
    setFilters({ ...filters, origin: from, destination: to });
    setDiscoveryDismissed(true);
  };

  const hasRoute = filters.origin && filters.destination;
  const hasDate = !!filters.dateFrom;
  const showResults = hasRoute && hasDate;

  // Globe data: use discovery destinations when available, otherwise default flagship routes
  const globeOrigin = filters.origin || "OSL";
  const globeDests = discoveryDests.length > 0 ? discoveryDests : DEFAULT_GLOBE_DESTS;

  return (
    <div className="relative min-h-[calc(100vh-64px)]">
      {/* Gradient orb */}
      <div className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[900px] -translate-x-1/2">
        <div
          className="h-full w-full rounded-full opacity-20 blur-[120px]"
          style={{ background: "conic-gradient(from 220deg at 50% 50%, #064e3b 0deg, #1e3a8a 120deg, #7c3aed 240deg, #064e3b 360deg)" }}
        />
      </div>

      <div className="relative mx-auto max-w-[1200px] px-6 pb-20 pt-10">
        {/* ═══ TOP SECTION: Search panel + Globe (always visible) ═══ */}
        <div className="flex items-stretch gap-4">
          {/* ── Left: Search panel ── */}
          <div className="min-w-0 flex-1">
            <div className="flex h-full flex-col overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] shadow-[0_20px_60px_-15px_rgba(0,0,0,.5)]">
              {/* Window chrome */}
              <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.025)] px-5 py-[10px]">
                <div className="flex gap-[6px]">
                  {[0, 1, 2].map((d) => (
                    <div key={d} className="h-[12px] w-[12px] rounded-full bg-[hsla(0,0%,100%,.07)]" />
                  ))}
                </div>
                <span className={`ml-3 text-[12px] text-[hsla(0,0%,100%,.22)] ${mono}`}>
                  award search
                </span>
                <div className="ml-auto flex items-center gap-[6px]">
                  <span className="h-[6px] w-[6px] animate-pulse rounded-full bg-emerald-500" />
                  <span className={`text-[11px] text-[hsla(0,0%,100%,.18)] ${mono}`}>
                    {hasRoute ? "searching" : "ready"}
                  </span>
                </div>
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

              {/* Network status strip */}
              <div className="grid grid-cols-3 border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)]">
                {[
                  { icon: Radio, value: "150+", label: "routes live", color: "text-emerald-400" },
                  { icon: Clock, value: "30 min", label: "scan cycle", color: "text-blue-400" },
                  { icon: Zap, value: "2 min", label: "last update", color: "text-amber-400" },
                ].map((stat, i) => (
                  <div
                    key={stat.label}
                    className={`flex items-center gap-2 px-4 py-2.5 ${i > 0 ? "border-l border-[hsla(0,0%,100%,.06)]" : ""}`}
                  >
                    <stat.icon className={`size-3 ${stat.color} opacity-50`} />
                    <span className={`text-[12px] font-semibold text-[hsla(0,0%,100%,.5)] ${mono}`}>{stat.value}</span>
                    <span className="text-[10px] text-[hsla(0,0%,100%,.18)]">{stat.label}</span>
                  </div>
                ))}
              </div>

              {/* ── State-dependent content ── */}
              {hasRoute ? (
                <>
                  {/* Route summary */}
                  <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] px-5 py-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Plane className="size-3 text-emerald-400/50" />
                      <span className="text-[11px] font-medium text-[hsla(0,0%,100%,.3)]">Selected route</span>
                    </div>
                    <div className="flex items-center gap-3 rounded-lg border border-emerald-500/15 bg-emerald-500/[0.03] px-4 py-3">
                      <div className="flex items-center gap-2">
                        <span className={`text-[18px] font-bold text-emerald-400 ${mono}`}>{filters.origin}</span>
                        <div className="flex items-center gap-1">
                          <div className="h-px w-6 bg-gradient-to-r from-emerald-400/40 to-emerald-400/10" />
                          <Plane className="size-3 text-emerald-400/40" />
                          <div className="h-px w-6 bg-gradient-to-l from-emerald-400/40 to-emerald-400/10" />
                        </div>
                        <span className={`text-[18px] font-bold text-emerald-400 ${mono}`}>{filters.destination}</span>
                      </div>
                    </div>
                  </div>

                  {/* Points reference — dynamic based on route */}
                  {filters.origin && filters.destination && (() => {
                    const { tier, pricing } = getRoutePricing(filters.origin, filters.destination);
                    const cabins = [
                      { cabin: "Economy", pts: pricing.economy, dotClass: "bg-emerald-400/50", ptsClass: "text-emerald-400/70" },
                      { cabin: "Premium", pts: pricing.premium, dotClass: "bg-blue-400/50", ptsClass: "text-blue-400/70" },
                      { cabin: "Business", pts: pricing.business, dotClass: "bg-amber-400/50", ptsClass: "text-amber-400/70" },
                    ];
                    return (
                      <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.01)] px-5 py-3">
                        <div className="mb-0.5 text-[9px] font-semibold uppercase tracking-[0.1em] text-[hsla(0,0%,100%,.18)]">
                          Award price per one-way
                        </div>
                        <div className={`mb-2 text-[9px] text-[hsla(0,0%,100%,.12)] ${mono}`}>
                          {tier} · from 1 Dec 2025
                        </div>
                        <div className="grid grid-cols-3 gap-2">
                          {cabins.map((c) => (
                            <div key={c.cabin} className="rounded-md border border-[hsla(0,0%,100%,.05)] bg-[hsla(0,0%,100%,.02)] px-2.5 py-2 text-center">
                              <div className="flex items-center justify-center gap-1">
                                <div className={`size-[5px] rounded-full ${c.dotClass}`} />
                                <span className="text-[9px] text-[hsla(0,0%,100%,.3)]">{c.cabin}</span>
                              </div>
                              <div className={`mt-1 text-[13px] font-bold ${c.ptsClass} ${mono}`}>{c.pts}</div>
                              <div className="text-[8px] text-[hsla(0,0%,100%,.15)]">{c.pts !== "—" ? "pts" : ""}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Spacer to fill remaining height */}
                  <div className="flex-1 border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.01)]">
                    <div className="flex h-full items-end px-5 py-3">
                      <div className={`text-[10px] leading-[1.6] text-[hsla(0,0%,100%,.15)]`}>
                        <span className="font-medium text-blue-400/50">Tip:</span>{" "}
                        {!hasDate
                          ? "Select a date above to search for available bonus seats on this route."
                          : "Results are loading from the SAS booking engine in real-time."}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Popular routes — quick picks */}
                  <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] px-5 py-4">
                    <div className="mb-2.5 flex items-center gap-2">
                      <Plane className="size-3 text-emerald-400/40" />
                      <span className="text-[11px] font-medium text-[hsla(0,0%,100%,.3)]">Popular routes</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {POPULAR_ROUTES.map((r) => (
                        <button
                          key={r.from + r.to}
                          onClick={() => handleQuickRoute(r.from, r.to)}
                          className="group flex items-center gap-2.5 rounded-lg border border-[hsla(0,0%,100%,.05)] bg-[hsla(0,0%,100%,.02)] px-3 py-2 text-left transition-all hover:border-emerald-500/20 hover:bg-emerald-500/[0.03]"
                        >
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span className={`text-[11px] font-bold text-[hsla(0,0%,100%,.5)] group-hover:text-emerald-400 ${mono}`}>
                                {r.from}
                              </span>
                              <ArrowRight className="size-2.5 text-[hsla(0,0%,100%,.15)]" />
                              <span className={`text-[11px] font-bold text-[hsla(0,0%,100%,.5)] group-hover:text-emerald-400 ${mono}`}>
                                {r.to}
                              </span>
                            </div>
                            <div className="mt-[2px] flex items-center gap-2">
                              <span className="text-[9px] text-[hsla(0,0%,100%,.2)]">{r.cabin}</span>
                              <span className={`text-[9px] text-emerald-400/40 ${mono}`}>from {r.pts}</span>
                            </div>
                          </div>
                          <ArrowRight className="size-3 shrink-0 text-[hsla(0,0%,100%,.06)] transition-all group-hover:translate-x-0.5 group-hover:text-emerald-400/40" />
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* EuroBonus tip + spacer */}
                  <div className="flex flex-1 flex-col border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.01)]">
                    <div className="mt-auto px-5 py-3">
                      <div className={`text-[10px] leading-[1.6] text-[hsla(0,0%,100%,.2)]`}>
                        <span className="font-medium text-blue-400/60">Pro tip:</span>{" "}
                        Business class to Asia or North America costs 60,000 pts one-way — while revenue tickets on the same routes often exceed 15,000 NOK. That&apos;s where EuroBonus points deliver the most value.
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>

          {/* ── Right: Globe (always visible) ── */}
          <div className="hidden w-[380px] shrink-0 overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] shadow-[0_20px_60px_-15px_rgba(0,0,0,.5)] lg:block">
            <GlobeView
              origin={globeOrigin}
              destinations={globeDests}
              onSelectDestination={handleSelectDiscoveryDest}
              compact
              highlightedDest={hoveredDest}
            />
          </div>
        </div>

        {/* ═══ ROUTE DISCOVERY — full width below ═══ */}
        {showDiscovery && (
          <div className="mt-4">
            <RouteDiscovery
              origin={filters.origin}
              onSelectDestination={handleSelectDiscoveryDest}
              onClose={() => setDiscoveryDismissed(true)}
              onHoverDest={setHoveredDest}
              onDestsLoaded={setDiscoveryDests}
            />
          </div>
        )}

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

        {/* ═══ RESULTS ═══ */}
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
      </div>
    </div>
  );
}
