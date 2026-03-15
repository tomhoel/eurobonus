import type { FlightOffer, PartnerFlight, RouteInfo, CabinName } from "@/lib/sas/types";
import { CABIN_CODE_TO_NAME } from "@/lib/sas/types";
import type { SearchResult, GroupedFlight, CabinOption } from "./types";

export function normalizeResults(
  offers: FlightOffer[],
  partners: PartnerFlight[],
): SearchResult[] {
  const results: SearchResult[] = [];

  for (const offer of offers) {
    const firstSeg = offer.segments[0];
    const lastSeg = offer.segments[offer.segments.length - 1];
    results.push({
      id: `sas-${offer.flightId}-${offer.cabinClass}-${offer.bookingClass}`,
      type: "sas",
      origin: offer.origin,
      destination: offer.destination,
      date: offer.date,
      cabinClass: offer.cabinClass,
      points: offer.points,
      taxes: offer.taxes,
      currency: offer.currency,
      availableSeats: offer.availableSeats,
      stops: offer.stops,
      totalDurationMinutes: offer.totalDurationMinutes,
      departureTime: firstSeg?.departureTime ?? "",
      arrivalTime: lastSeg?.arrivalTime ?? "",
      carriers: [...new Set(offer.segments.map((s) => s.carrier))],
      carrierNames: [...new Set(offer.segments.map((s) => s.carrierName).filter(Boolean))],
      route: [offer.origin, ...offer.segments.slice(0, -1).map((s) => s.arrivalAirport), offer.destination].join(" → "),
      isBonusTicket: offer.isBonusTicket,
      segments: offer.segments,
      flightId: offer.flightId,
      bookingClass: offer.bookingClass,
      productName: offer.productName,
      valueScore: 0,
      isTopPick: false,
      percentBelowAvg: 0,
      seatUrgency: getSeatUrgency(offer.availableSeats),
    });
  }

  for (const pf of partners) {
    for (const cabin of pf.cabins) {
      results.push({
        id: `partner-${pf.date}-${pf.route}-${cabin.cabin}`,
        type: "partner",
        origin: pf.origin,
        destination: pf.destination,
        date: pf.date,
        cabinClass: cabin.cabin,
        points: cabin.points,
        taxes: cabin.cash,
        currency: "NOK",
        availableSeats: cabin.seats,
        stops: pf.stops,
        totalDurationMinutes: pf.totalDurationMinutes,
        departureTime: pf.departureTime,
        arrivalTime: pf.arrivalTime,
        carriers: pf.carriers,
        carrierNames: pf.carrierNames,
        route: pf.route,
        isBonusTicket: false,
        segments: [],
        flightId: "",
        bookingClass: "",
        productName: "Partner Award",
        valueScore: 0,
        isTopPick: false,
        percentBelowAvg: 0,
        seatUrgency: getSeatUrgency(cabin.seats),
      });
    }
  }

  return computeValueScores(results);
}

/**
 * Convert RouteInfo[] (from the BFF routes API) into SearchResults.
 * Used as fallback when the offers API returns empty.
 */
export function normalizeRoutes(
  routes: RouteInfo[],
  origin: string,
  destination: string,
): SearchResult[] {
  const results: SearchResult[] = [];

  for (const route of routes) {
    // Each route has availability per cabin code (AG, AP, AB)
    const cabinEntries = Object.entries(route.availability);
    for (const [code, seats] of cabinEntries) {
      if (seats <= 0) continue;
      const cabinName = CABIN_CODE_TO_NAME[code as keyof typeof CABIN_CODE_TO_NAME];
      if (!cabinName) continue;

      results.push({
        id: `route-${route.flightId}-${code}`,
        type: "sas",
        origin,
        destination,
        date: route.departureDate,
        cabinClass: cabinName,
        points: 0, // Not available from route API
        taxes: 0,
        currency: "NOK",
        availableSeats: seats,
        stops: Math.max(0, route.numFlights - 1),
        totalDurationMinutes: route.totalTimeMinutes || route.flyTimeMinutes,
        departureTime: route.departureTime,
        arrivalTime: route.arrivalTime,
        carriers: ["SK"],
        carrierNames: ["SAS"],
        route: `${origin} → ${destination}`,
        isBonusTicket: false,
        segments: [],
        flightId: route.flightId,
        bookingClass: "",
        productName: cabinName,
        valueScore: 5,
        isTopPick: false,
        percentBelowAvg: 0,
        seatUrgency: getSeatUrgency(seats),
      });
    }
  }

  return results;
}

function getSeatUrgency(seats: number): "high" | "medium" | "low" {
  if (seats <= 1) return "high";
  if (seats <= 3) return "medium";
  return "low";
}

function computeValueScores(results: SearchResult[]): SearchResult[] {
  if (results.length === 0) return results;

  // Group by cabin for relative scoring
  const byCabin = new Map<string, SearchResult[]>();
  for (const r of results) {
    const group = byCabin.get(r.cabinClass) ?? [];
    group.push(r);
    byCabin.set(r.cabinClass, group);
  }

  // Cabin multipliers (business is worth more per point)
  const cabinWeight: Record<string, number> = {
    BUSINESS: 1.5,
    PREMIUM: 1.2,
    ECONOMY: 1.0,
  };

  for (const [cabin, group] of byCabin) {
    const points = group.map((r) => r.points);
    const avg = points.reduce((a, b) => a + b, 0) / points.length;
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;

    for (const r of group) {
      // Base score: how much below average (0-1)
      const belowAvg = avg > 0 ? (avg - r.points) / avg : 0;
      r.percentBelowAvg = Math.round(belowAvg * 100);

      // Normalized position (1 = cheapest, 0 = most expensive)
      const normalized = 1 - (r.points - min) / range;

      // Factor in cabin weight and bonus ticket boost
      const weight = cabinWeight[cabin] ?? 1;
      const bonusBoost = r.isBonusTicket ? 0.1 : 0;

      // Score 1-10
      r.valueScore = Math.max(1, Math.min(10, Math.round((normalized * weight + bonusBoost) * 10)));
    }
  }

  // Mark top pick (highest value score overall)
  let topPick: SearchResult | null = null;
  for (const r of results) {
    if (!topPick || r.valueScore > topPick.valueScore || (r.valueScore === topPick.valueScore && r.points < topPick.points)) {
      topPick = r;
    }
  }
  if (topPick) topPick.isTopPick = true;

  return results;
}

/**
 * Group SearchResults by flight (same departure time + route),
 * merging cabin options into a single card per flight.
 */
export function groupByFlight(results: SearchResult[]): GroupedFlight[] {
  const groups = new Map<string, GroupedFlight>();
  const CABIN_ORDER: Record<string, number> = { ECONOMY: 0, PREMIUM: 1, BUSINESS: 2 };

  for (const r of results) {
    // Key by departure time + stops + route to group same physical flight
    const key = `${r.departureTime}-${r.arrivalTime}-${r.stops}-${r.route}`;

    if (!groups.has(key)) {
      groups.set(key, {
        id: key,
        type: r.type,
        origin: r.origin,
        destination: r.destination,
        date: r.date,
        departureTime: r.departureTime,
        arrivalTime: r.arrivalTime,
        stops: r.stops,
        totalDurationMinutes: r.totalDurationMinutes,
        carriers: r.carriers,
        carrierNames: r.carrierNames,
        route: r.route,
        segments: r.segments,
        flightId: r.flightId,
        cabins: [],
        lowestPoints: Infinity,
        hasBonusFare: false,
        isTopPick: false,
      });
    }

    const group = groups.get(key)!;

    // Find best offer per cabin (lowest points for each cabin class)
    const existing = group.cabins.find((c) => c.cabinClass === r.cabinClass);
    if (!existing || r.points < existing.points) {
      const cabin: CabinOption = {
        cabinClass: r.cabinClass,
        points: r.points,
        taxes: r.taxes,
        currency: r.currency,
        availableSeats: r.availableSeats,
        isBonusTicket: r.isBonusTicket,
        productName: r.productName,
        bookingClass: r.bookingClass,
        valueScore: r.valueScore,
        percentBelowAvg: r.percentBelowAvg,
        seatUrgency: r.seatUrgency,
      };
      if (existing) {
        const idx = group.cabins.indexOf(existing);
        group.cabins[idx] = cabin;
      } else {
        group.cabins.push(cabin);
      }
    }

    if (r.points > 0 && r.points < group.lowestPoints) {
      group.lowestPoints = r.points;
    }
    if (r.isBonusTicket) group.hasBonusFare = true;
    if (r.isTopPick) group.isTopPick = true;
  }

  // Sort cabins within each group by cabin order
  for (const group of groups.values()) {
    group.cabins.sort((a, b) => (CABIN_ORDER[a.cabinClass] ?? 9) - (CABIN_ORDER[b.cabinClass] ?? 9));
    if (group.lowestPoints === Infinity) group.lowestPoints = 0;
  }

  // Sort groups by lowest points
  return [...groups.values()].sort((a, b) => {
    if (a.hasBonusFare !== b.hasBonusFare) return a.hasBonusFare ? -1 : 1;
    return a.lowestPoints - b.lowestPoints;
  });
}
