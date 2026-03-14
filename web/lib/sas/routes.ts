import { sasRequest, type SASClientOptions } from "./client";
import type { RouteInfo } from "./types";

const ROUTES_URL = "https://www.sas.no/bff/award-finder/routes/v1";

export async function getRouteDetails(
  origin: string,
  destination: string,
  departureDate: string,
  options: { direct?: boolean } & SASClientOptions = {},
): Promise<RouteInfo[]> {
  const { direct = false, ...clientOpts } = options;

  const raw = await sasRequest<unknown[]>(ROUTES_URL, {
    market: clientOpts.market ?? "no-no",
    origin,
    destination,
    departureDate,
    direct: String(direct),
  }, clientOpts);

  if (!raw || !Array.isArray(raw)) return [];

  return raw.map((item) => {
    const it = (item ?? {}) as Record<string, unknown>;
    return {
      flightId: String(it.flightId ?? ""),
      departureDate: String(it.departureDate ?? ""),
      departureTime: String(it.departureTime ?? ""),
      arrivalDate: String(it.arrivalDate ?? ""),
      arrivalTime: String(it.arrivalTime ?? ""),
      flyTimeMinutes: Number(it.flyTime ?? 0),
      totalTimeMinutes: Number(it.totalTime ?? 0),
      numFlights: Number(it.noOfFlights ?? 1),
      haulType: String(it.haulType ?? ""),
      availability: (it.availability ?? {}) as Record<string, number>,
    };
  });
}
