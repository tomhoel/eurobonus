"use client";

import { Lightbulb, ArrowRight } from "lucide-react";
import type { SearchResult, SearchFilters } from "@/lib/search/types";
import { findAirport } from "@/lib/route-map";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface AISuggestionsProps {
  results: SearchResult[];
  filters: SearchFilters;
  onApplyFilters: (partial: Partial<SearchFilters>) => void;
}

export function AISuggestions({ results, filters, onApplyFilters }: AISuggestionsProps) {
  const suggestions = generateSuggestions(results, filters);
  if (suggestions.length === 0) return null;

  return (
    <div className="rounded-xl border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)] p-4">
      <div className={`mb-3 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.25)] ${mono}`}>
        <Lightbulb className="size-3 text-amber-400/60" />
        Suggestions
      </div>
      <div className="space-y-1">
        {suggestions.map((sug, i) => (
          <button
            key={i}
            onClick={() => onApplyFilters(sug.filters)}
            className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left transition-colors hover:bg-[hsla(0,0%,100%,.04)]"
          >
            <ArrowRight className="size-3 shrink-0 text-emerald-400/50" />
            <span className="flex-1 text-[12px] text-[hsla(0,0%,100%,.4)]">
              {sug.label}
            </span>
            {sug.points && (
              <span className={`text-[11px] text-emerald-400/70 ${mono}`}>
                {(sug.points / 1000).toFixed(0)}k
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}

interface Suggestion {
  label: string;
  filters: Partial<SearchFilters>;
  points?: number;
}

function generateSuggestions(results: SearchResult[], filters: SearchFilters): Suggestion[] {
  const suggestions: Suggestion[] = [];

  if (filters.cabin === "BUSINESS" && results.length > 0) {
    suggestions.push({
      label: "Check Premium for lower points",
      filters: { cabin: "PREMIUM" },
    });
  }

  const directFlights = results.filter((r) => r.stops === 0);
  if (directFlights.length === 0 && results.length > 0 && filters.maxStops === null) {
    const lowestStops = Math.min(...results.map((r) => r.stops));
    suggestions.push({
      label: `No direct — best is ${lowestStops} stop${lowestStops > 1 ? "s" : ""}`,
      filters: { maxStops: lowestStops },
    });
  }

  const bonusFares = results.filter((r) => r.isBonusTicket);
  if (bonusFares.length > 0 && !filters.bonusOnly) {
    const lowest = Math.min(...bonusFares.map((r) => r.points));
    suggestions.push({
      label: `${bonusFares.length} bonus fare${bonusFares.length > 1 ? "s" : ""} available`,
      filters: { bonusOnly: true },
      points: lowest,
    });
  }

  if (filters.origin) {
    const nearby: Record<string, string[]> = {
      OSL: ["CPH", "ARN"], CPH: ["OSL", "ARN"], ARN: ["CPH", "OSL"],
    };
    const alt = nearby[filters.origin]?.[0];
    if (alt) {
      const altName = findAirport(alt)?.name ?? alt;
      suggestions.push({ label: `Try from ${altName} (${alt})`, filters: { origin: alt } });
    }
  }

  return suggestions.slice(0, 3);
}
