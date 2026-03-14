import { sasRequest, type SASClientOptions } from "./client";
import type { AvailabilityDate, AvailabilityDestination } from "./types";

const DESTINATIONS_URL = "https://www.sas.no/bff/award-finder/destinations/v1";

export async function getAvailabilityCalendar(
  origin: string,
  destination: string = "",
  options: {
    month?: string;
    passengers?: number;
    direct?: boolean;
    cabinClass?: string;
  } & SASClientOptions = {},
): Promise<AvailabilityDestination[]> {
  const { month = "", passengers = 1, direct = false, cabinClass = "", ...clientOpts } = options;

  const raw = await sasRequest<unknown[]>(DESTINATIONS_URL, {
    market: clientOpts.market ?? "no-no",
    origin,
    destinations: destination,
    selectedMonth: month,
    passengers,
    direct: String(direct),
    availability: "true",
    selectedFlightClass: cabinClass,
  }, clientOpts);

  if (!raw || !Array.isArray(raw)) return [];

  return raw.map((dest) => {
    const d = dest as Record<string, unknown>;
    const avail = (d.availability ?? {}) as Record<string, unknown>;
    const parseDay = (day: unknown): AvailabilityDate => {
      const dayObj = (day ?? {}) as Record<string, unknown>;
      return {
        date: String(dayObj.date ?? ""),
        economySeats: Number(dayObj.AG ?? 0),
        premiumSeats: Number(dayObj.AP ?? 0),
        businessSeats: Number(dayObj.AB ?? 0),
      };
    };

    return {
      iataCode: String(d.airportCode ?? d.iataCode ?? ""),
      cityName: String(d.cityName ?? ""),
      outbound: ((avail.outbound ?? []) as unknown[]).map(parseDay),
      inbound: ((avail.inbound ?? []) as unknown[]).map(parseDay),
    };
  });
}

export async function getAvailableDates(
  origin: string,
  destination: string,
  options: { month?: string; cabinClass?: string } & SASClientOptions = {},
): Promise<AvailabilityDate[]> {
  const results = await getAvailabilityCalendar(origin, destination, options);
  const match = results.find((d) => d.iataCode === destination);
  return match?.outbound ?? [];
}
