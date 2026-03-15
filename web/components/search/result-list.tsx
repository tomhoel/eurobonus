"use client";

import { useMemo } from "react";
import { Search } from "lucide-react";
import type { SearchResult } from "@/lib/search/types";
import { groupByFlight } from "@/lib/search/normalize";
import { FlightCard } from "./result-card";

interface ResultListProps {
  results: SearchResult[];
  isLoading: boolean;
}

export function ResultList({ results, isLoading }: ResultListProps) {
  const grouped = useMemo(() => groupByFlight(results), [results]);

  if (isLoading) return null;

  if (grouped.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-[hsla(0,0%,100%,.03)]">
          <Search className="size-8 text-[hsla(0,0%,100%,.12)]" />
        </div>
        <h3 className="text-lg font-medium text-[hsla(0,0%,100%,.5)]">No flights found</h3>
        <p className="mt-1 max-w-sm text-sm text-[hsla(0,0%,100%,.22)]">
          Try adjusting your filters, selecting a different date, or expanding your search criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {grouped.map((flight) => (
        <FlightCard key={flight.id} flight={flight} />
      ))}
    </div>
  );
}
