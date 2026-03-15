"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { useSearchParamsState } from "./use-search-params-state";
import { normalizeResults, normalizeRoutes } from "@/lib/search/normalize";
import { applyClientFilters, applySorting } from "@/lib/search/filters";
import type { SearchResult, ViewMode, AvailabilityDate, FlightOffer, PartnerFlight } from "@/lib/search/types";
import type { RouteInfo } from "@/lib/sas/types";

export function useSearch() {
  const { filters, setFilters, updateFilter, resetFilters, activeFilterCount } =
    useSearchParamsState();

  const [results, setResults] = useState<SearchResult[]>([]);
  const [availableDates, setAvailableDates] = useState<AvailabilityDate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const abortRef = useRef<AbortController | null>(null);

  // Fetch calendar availability when origin/destination/month changes
  useEffect(() => {
    if (!filters.origin || !filters.destination) return;

    const controller = new AbortController();
    const params = new URLSearchParams({
      origin: filters.origin,
      destination: filters.destination,
    });
    if (filters.month) params.set("month", filters.month);
    if (filters.cabin !== "ANY") params.set("cabin", filters.cabin.toLowerCase());

    setIsLoading(true);
    setError(null);

    fetch(`/api/search?${params}`, { signal: controller.signal })
      .then((r) => r.json())
      .then((data) => {
        setAvailableDates(data.dates ?? []);
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError("Failed to load availability");
      })
      .finally(() => setIsLoading(false));

    return () => controller.abort();
  }, [filters.origin, filters.destination, filters.month, filters.cabin]);

  // Fetch detailed results when a date is selected
  useEffect(() => {
    if (!filters.origin || !filters.destination || !filters.dateFrom) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setIsLoading(true);
    setError(null);

    const fetchResults = async () => {
      try {
        const baseParams = {
          origin: filters.origin,
          destination: filters.destination,
          date: filters.dateFrom,
        };

        // Fetch offers, partners, and route details in parallel
        const [offersRes, partnersRes, routesRes] = await Promise.allSettled([
          fetch(
            `/api/search/offers?${new URLSearchParams({
              ...baseParams,
              ...(filters.cabin !== "ANY" ? { cabin: filters.cabin.toLowerCase() } : {}),
            })}`,
            { signal: controller.signal },
          ).then((r) => r.json()),
          filters.includePartners
            ? fetch(
                `/api/search/partners?${new URLSearchParams(baseParams)}`,
                { signal: controller.signal },
              ).then((r) => r.json())
            : Promise.resolve({ partners: [] }),
          fetch(
            `/api/search?${new URLSearchParams(baseParams)}`,
            { signal: controller.signal },
          ).then((r) => r.json()),
        ]);

        const offers: FlightOffer[] =
          offersRes.status === "fulfilled" ? offersRes.value.offers ?? [] : [];
        const partners: PartnerFlight[] =
          partnersRes.status === "fulfilled" ? partnersRes.value.partners ?? [] : [];
        const routes: RouteInfo[] =
          routesRes.status === "fulfilled" ? routesRes.value.routes ?? [] : [];

        // Use offers + partners as primary data
        let normalized = normalizeResults(offers, partners);

        // If offers are empty but routes have data, use routes as fallback
        if (normalized.length === 0 && routes.length > 0) {
          normalized = normalizeRoutes(routes, filters.origin, filters.destination);
        }

        setResults(normalized);
      } catch (e) {
        if ((e as Error).name !== "AbortError") {
          setError("Failed to load flight results");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
    return () => controller.abort();
  }, [filters.origin, filters.destination, filters.dateFrom, filters.cabin, filters.includePartners]);

  const filteredResults = useMemo(() => {
    const filtered = applyClientFilters(results, filters);
    return applySorting(filtered, filters.sortBy);
  }, [results, filters]);

  const selectDate = useCallback(
    (date: string) => {
      setFilters({ ...filters, dateFrom: date, dateTo: date });
      setViewMode("list");
    },
    [filters, setFilters],
  );

  return {
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
  };
}
