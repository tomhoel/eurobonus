import type { FlightOffer, FlightSegment, CabinName } from "./types";

const AWARD_API_URL = "https://www.sas.no/award-api/flights";

/**
 * Fetch award flight offers from the SAS award API.
 * Requires a valid SAS user session (EuroBonus login).
 * Returns flights with EuroBonus point pricing.
 */
export async function getAwardFlights(
  origin: string,
  destination: string,
  date: string,
  options: {
    adults?: number;
    pos?: string;
    sessionId?: string;
    cookies?: string;
    bearerToken?: string;
  } = {},
): Promise<FlightOffer[]> {
  const { adults = 1, pos = "NO", sessionId, cookies, bearerToken } = options;

  // This API requires a real SAS session — bail early if none provided
  if (!sessionId && !bearerToken) {
    return [];
  }

  // Ensure YYYY-MM-DD
  const outDate = date.includes("-")
    ? date
    : `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`;

  const qs = new URLSearchParams({
    origin: origin.toUpperCase(),
    destination: destination.toUpperCase(),
    outboundDate: outDate,
    tripType: "one-way",
    adults: String(adults),
    children: "0",
    infants: "0",
    youths: "0",
  });

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    channel: "WEB",
    pos: pos.toUpperCase(),
  };

  if (sessionId) headers["sas-user-session-id"] = sessionId;
  if (bearerToken) headers["Authorization"] = `Bearer ${bearerToken}`;
  if (cookies) headers["Cookie"] = cookies;

  try {
    const res = await fetch(`${AWARD_API_URL}?${qs}`, {
      headers,
      signal: AbortSignal.timeout(30_000),
    });

    if (!res.ok) {
      console.error(`[award-flights] ${res.status} ${res.statusText}`);
      return [];
    }

    const data = await res.json();
    return parseAwardFlights(data, origin.toUpperCase(), destination.toUpperCase(), outDate);
  } catch (err) {
    console.error("[award-flights] Request failed:", err);
    return [];
  }
}

function parseAwardFlights(
  data: unknown,
  origin: string,
  destination: string,
  date: string,
): FlightOffer[] {
  const offers: FlightOffer[] = [];
  if (!data || typeof data !== "object") return offers;
  const obj = data as Record<string, unknown>;

  const flights = Array.isArray(obj.outboundFlights)
    ? obj.outboundFlights
    : [];

  for (const flight of flights) {
    if (!flight || typeof flight !== "object") continue;
    const fl = flight as Record<string, unknown>;

    const rawSegments = Array.isArray(fl.segments) ? fl.segments : [];
    const segments: FlightSegment[] = rawSegments.map((seg: unknown) => {
      const s = (seg ?? {}) as Record<string, unknown>;
      const dep = typeof s.departureAirport === "object"
        ? (s.departureAirport as Record<string, unknown>)?.code
        : s.departureAirport;
      const arr = typeof s.arrivalAirport === "object"
        ? (s.arrivalAirport as Record<string, unknown>)?.code
        : s.arrivalAirport;
      const opCarrier = typeof s.operatingCarrier === "object"
        ? (s.operatingCarrier as Record<string, unknown>)
        : {};
      const mkCarrier = typeof s.marketingCarrier === "object"
        ? (s.marketingCarrier as Record<string, unknown>)
        : {};
      const ac = typeof s.airCraft === "object"
        ? (s.airCraft as Record<string, unknown>)?.name
        : s.airCraft;

      let durMins = 0;
      const durRaw = s.duration ?? s.flyTime;
      if (typeof durRaw === "string" && durRaw.includes(":")) {
        const [h, m] = durRaw.split(":");
        durMins = Number(h) * 60 + Number(m);
      } else if (typeof durRaw === "number") {
        durMins = durRaw;
      }

      return {
        flightNumber: String(s.flightNumber ?? mkCarrier.code ?? ""),
        carrier: String(opCarrier.code ?? mkCarrier.code ?? ""),
        carrierName: String(opCarrier.name ?? mkCarrier.name ?? ""),
        departureAirport: String(dep ?? ""),
        arrivalAirport: String(arr ?? ""),
        departureTime: String(s.departureTime ?? (s.departureDateTime as string)?.slice(11, 16) ?? ""),
        arrivalTime: String(s.arrivalTime ?? (s.arrivalDateTime as string)?.slice(11, 16) ?? ""),
        departureDate: String(s.departureDate ?? (s.departureDateTime as string)?.slice(0, 10) ?? date),
        arrivalDate: String(s.arrivalDate ?? (s.arrivalDateTime as string)?.slice(0, 10) ?? date),
        aircraft: String(ac ?? ""),
        durationMinutes: durMins,
      };
    });

    const totalDuration = segments.reduce((sum, s) => sum + s.durationMinutes, 0);
    const stops = Math.max(0, segments.length - 1);
    const depTime = String(fl.startTimeInLocal ?? fl.departureTime ?? segments[0]?.departureTime ?? "");
    const arrTime = String(fl.endTimeInLocal ?? fl.arrivalTime ?? segments[segments.length - 1]?.arrivalTime ?? "");

    let flightDuration = totalDuration;
    if (fl.totalDuration) {
      const td = fl.totalDuration;
      if (typeof td === "number") flightDuration = td;
      else if (typeof td === "string") {
        const hMatch = (td as string).match(/(\d+)h/);
        const mMatch = (td as string).match(/(\d+)m/);
        flightDuration = (hMatch ? Number(hMatch[1]) * 60 : 0) + (mMatch ? Number(mMatch[1]) : 0);
      }
    }

    const cabins = Array.isArray(fl.cabins) ? fl.cabins : [];
    for (const cabin of cabins) {
      if (!cabin || typeof cabin !== "object") continue;
      const cab = cabin as Record<string, unknown>;
      const price = (cab.price ?? {}) as Record<string, unknown>;
      const cabinClass = String(cab.cabin ?? cab.cabinClass ?? "ECONOMY").toUpperCase() as CabinName;

      const points = Number(price.points ?? price.totalPrice ?? 0);
      const tax = Number(price.totalTax ?? price.cash ?? price.tax ?? 0);
      const seats = Number(cab.availableSeats ?? cab.seatsAvailable ?? 0);
      const isBonus = cab.isStandardAward === true ||
        cab.isBonusFare === true ||
        Number(price.basePrice ?? 1) === 0;

      if (points > 0) {
        offers.push({
          origin,
          destination,
          date,
          cabinClass,
          productName: String(cab.productName ?? cab.fareFamily ?? cabinClass),
          points,
          taxes: tax,
          currency: String(price.currency ?? "NOK"),
          availableSeats: seats,
          bookingClass: String(cab.bookingClass ?? ""),
          segments,
          totalDurationMinutes: flightDuration || totalDuration,
          stops,
          flightId: String(fl.id ?? fl.flightId ?? `${segments[0]?.flightNumber}-${date}`),
          isBonusTicket: isBonus,
          basePrice: Number(price.basePrice ?? 0),
        });
      }
    }
  }

  return offers.sort((a, b) => a.points - b.points);
}
