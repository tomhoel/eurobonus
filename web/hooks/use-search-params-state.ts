"use client";

import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback, useMemo } from "react";
import type { SearchFilters } from "@/lib/search/types";
import { DEFAULT_FILTERS } from "@/lib/search/types";

const PARAM_MAP: Record<string, keyof SearchFilters> = {
  origin: "origin",
  dest: "destination",
  from: "dateFrom",
  to: "dateTo",
  flex: "flexDays",
  cabin: "cabin",
  month: "month",
  maxPts: "maxPoints",
  bonus: "bonusOnly",
  minVal: "minValueScore",
  stops: "maxStops",
  airlines: "airlines",
  time: "departureTime",
  maxDur: "maxDuration",
  partners: "includePartners",
  trend: "availabilityTrend",
  minSeats: "minSeats",
  sort: "sortBy",
};

const REVERSE_MAP = Object.fromEntries(
  Object.entries(PARAM_MAP).map(([k, v]) => [v, k]),
);

export function useSearchParamsState() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const filters = useMemo<SearchFilters>(() => {
    const f = { ...DEFAULT_FILTERS };
    for (const [param, key] of Object.entries(PARAM_MAP)) {
      const val = searchParams.get(param);
      if (val === null) continue;

      switch (key) {
        case "flexDays":
        case "maxPoints":
        case "minValueScore":
        case "maxDuration":
        case "minSeats":
          (f as Record<string, unknown>)[key] = parseInt(val, 10) || 0;
          break;
        case "maxStops":
          (f as Record<string, unknown>)[key] = val === "any" ? null : parseInt(val, 10);
          break;
        case "bonusOnly":
        case "includePartners":
          (f as Record<string, unknown>)[key] = val === "1";
          break;
        case "airlines":
          f.airlines = val.split(",").filter(Boolean);
          break;
        default:
          (f as Record<string, unknown>)[key] = val;
      }
    }
    return f;
  }, [searchParams]);

  const setFilters = useCallback(
    (newFilters: SearchFilters) => {
      const params = new URLSearchParams();
      for (const [key, paramName] of Object.entries(REVERSE_MAP)) {
        const val = newFilters[key as keyof SearchFilters];
        const def = DEFAULT_FILTERS[key as keyof SearchFilters];

        // Skip defaults
        if (JSON.stringify(val) === JSON.stringify(def)) continue;

        if (key === "airlines" && Array.isArray(val) && val.length > 0) {
          params.set(paramName, val.join(","));
        } else if (key === "maxStops") {
          params.set(paramName, val === null ? "any" : String(val));
        } else if (typeof val === "boolean") {
          params.set(paramName, val ? "1" : "0");
        } else if (val !== "" && val !== 0 && val !== null) {
          params.set(paramName, String(val));
        }
      }

      const qs = params.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, pathname],
  );

  const updateFilter = useCallback(
    <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => {
      setFilters({ ...filters, [key]: value });
    },
    [filters, setFilters],
  );

  const resetFilters = useCallback(() => {
    setFilters({
      ...DEFAULT_FILTERS,
      origin: filters.origin,
      destination: filters.destination,
    });
  }, [filters.origin, filters.destination, setFilters]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.cabin !== "ANY") count++;
    if (filters.maxPoints > 0) count++;
    if (filters.bonusOnly) count++;
    if (filters.minValueScore > 0) count++;
    if (filters.maxStops !== null) count++;
    if (filters.airlines.length > 0) count++;
    if (filters.departureTime !== "any") count++;
    if (filters.maxDuration > 0) count++;
    if (!filters.includePartners) count++;
    if (filters.minSeats > 1) count++;
    return count;
  }, [filters]);

  return { filters, setFilters, updateFilter, resetFilters, activeFilterCount };
}
