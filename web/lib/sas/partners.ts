import { sasRequest, type SASClientOptions } from "./client";
import type { PartnerFlight, PartnerCabin, CabinName } from "./types";

const PARTNER_URL = "https://www.sas.no/award-api/flights";

export async function getPartnerAwards(
  origin: string,
  destination: string,
  date: string,
  options: { adults?: number } & SASClientOptions = {},
): Promise<PartnerFlight[]> {
  const { adults = 1, ...clientOpts } = options;

  // Ensure YYYY-MM-DD
  const outDate = date.length === 8
    ? `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`
    : date;

  const raw = await sasRequest<unknown>(PARTNER_URL, {
    origin,
    destination,
    outboundDate: outDate,
    tripType: "one-way",
    adults,
    children: 0,
    infants: 0,
    youths: 0,
    selectedCouponCodes: "",
  }, clientOpts);

  if (!raw) return [];
  return parsePartnerFlights(raw, origin, destination, outDate);
}

function parseDuration(raw: unknown): number {
  if (typeof raw === "number") return raw;
  if (typeof raw !== "string") return 0;
  if (raw.includes(":")) {
    const [h, m] = raw.split(":");
    return Number(h) * 60 + Number(m);
  }
  const hMatch = raw.match(/(\d+)h/);
  const mMatch = raw.match(/(\d+)m/);
  return (hMatch ? Number(hMatch[1]) * 60 : 0) + (mMatch ? Number(mMatch[1]) : 0);
}

function parsePartnerFlights(data: unknown, origin: string, destination: string, date: string): PartnerFlight[] {
  const flights: PartnerFlight[] = [];
  const dataObj = (data ?? {}) as Record<string, unknown>;

  for (const flight of (dataObj.outboundFlights ?? []) as unknown[]) {
    if (typeof flight !== "object" || !flight) continue;
    const fl = flight as Record<string, unknown>;
    const segments = Array.isArray(fl.segments) ? fl.segments : [];
    if (!segments.length) continue;

    const airports: string[] = [];
    const carriers: string[] = [];
    const carrierNames: string[] = [];

    for (let i = 0; i < segments.length; i++) {
      const seg = (segments[i] ?? {}) as Record<string, unknown>;
      const dep = typeof seg.departureAirport === "object"
        ? (seg.departureAirport as Record<string, unknown>)?.code
        : seg.departureAirport;
      airports.push(String(dep ?? ""));
      if (i === segments.length - 1) {
        const arr = typeof seg.arrivalAirport === "object"
          ? (seg.arrivalAirport as Record<string, unknown>)?.code
          : seg.arrivalAirport;
        airports.push(String(arr ?? ""));
      }
      const op = typeof seg.operatingCarrier === "object" ? (seg.operatingCarrier as Record<string, unknown>) : {};
      const mk = typeof seg.marketingCarrier === "object" ? (seg.marketingCarrier as Record<string, unknown>) : {};
      const code = String(op.code ?? mk.code ?? "");
      const name = String(op.name ?? mk.name ?? "");
      if (code && !carriers.includes(code)) carriers.push(code);
      if (name && !carrierNames.includes(name)) carrierNames.push(name);
    }

    const stopsRaw = fl.stops;
    const numStops = Array.isArray(stopsRaw) ? stopsRaw.length : (Number(stopsRaw) || Math.max(0, segments.length - 1));

    const depTime = String(fl.startTimeInLocal ?? ((fl.startDateTimeInLocal as string | undefined)?.slice(11, 16) ?? ""));
    const arrTime = String(fl.endTimeInLocal ?? ((fl.endDateTimeInLocal as string | undefined)?.slice(11, 16) ?? ""));

    const cabins: PartnerCabin[] = [];
    for (const c of (fl.cabins ?? []) as unknown[]) {
      if (typeof c !== "object" || !c) continue;
      const cab = c as Record<string, unknown>;
      const price = (cab.price ?? {}) as Record<string, unknown>;
      const pts = Number(price.points ?? price.totalPrice ?? 0);
      if (pts) {
        cabins.push({
          cabin: String(cab.cabin ?? cab.cabinClass ?? "UNKNOWN").toUpperCase() as CabinName,
          points: pts,
          cash: Number(price.totalTax ?? price.cash ?? 0),
          seats: Number(cab.availableSeats ?? 0),
        });
      }
    }

    if (cabins.length) {
      flights.push({
        date,
        departureTime: depTime,
        arrivalTime: arrTime,
        origin,
        destination,
        route: airports.join(" → "),
        carriers,
        carrierNames,
        stops: numStops,
        totalDurationMinutes: parseDuration(fl.totalDuration ?? fl.connectionDuration ?? 0),
        cabins,
      });
    }
  }

  return flights;
}
