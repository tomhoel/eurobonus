import type { SearchFilters, SearchResult, SortOption, TimeRange } from "./types";

export function applyClientFilters(
  results: SearchResult[],
  filters: SearchFilters,
): SearchResult[] {
  return results.filter((r) => {
    // Cabin filter
    if (filters.cabin !== "ANY" && r.cabinClass !== filters.cabin) return false;

    // Points budget
    if (filters.maxPoints > 0 && r.points > filters.maxPoints) return false;

    // Bonus only
    if (filters.bonusOnly && !r.isBonusTicket) return false;

    // Value score
    if (filters.minValueScore > 0 && r.valueScore < filters.minValueScore) return false;

    // Stops
    if (filters.maxStops !== null && r.stops > filters.maxStops) return false;

    // Airlines
    if (filters.airlines.length > 0) {
      const hasMatch = r.carriers.some((c) => filters.airlines.includes(c));
      if (!hasMatch) return false;
    }

    // Departure time
    if (filters.departureTime !== "any") {
      const hour = parseHour(r.departureTime);
      if (!isInTimeRange(hour, filters.departureTime)) return false;
    }

    // Max duration
    if (filters.maxDuration > 0 && r.totalDurationMinutes > filters.maxDuration) return false;

    // Partner toggle
    if (!filters.includePartners && r.type === "partner") return false;

    // Min seats
    if (r.availableSeats < filters.minSeats) return false;

    return true;
  });
}

export function applySorting(
  results: SearchResult[],
  sortBy: SortOption,
): SearchResult[] {
  const sorted = [...results];
  switch (sortBy) {
    case "best-value":
      sorted.sort((a, b) => b.valueScore - a.valueScore || a.points - b.points);
      break;
    case "lowest-points":
      sorted.sort((a, b) => a.points - b.points);
      break;
    case "shortest":
      sorted.sort((a, b) => a.totalDurationMinutes - b.totalDurationMinutes);
      break;
    case "fewest-stops":
      sorted.sort((a, b) => a.stops - b.stops || a.points - b.points);
      break;
  }
  return sorted;
}

function parseHour(time: string): number {
  if (!time) return 0;
  const parts = time.split(":");
  return parseInt(parts[0], 10) || 0;
}

function isInTimeRange(hour: number, range: TimeRange): boolean {
  switch (range) {
    case "morning": return hour >= 5 && hour < 12;
    case "afternoon": return hour >= 12 && hour < 17;
    case "evening": return hour >= 17 && hour < 21;
    case "night": return hour >= 21 || hour < 5;
    default: return true;
  }
}
