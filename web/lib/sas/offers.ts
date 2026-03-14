import { sasRequest, type SASClientOptions } from "./client";
import type { FlightOffer, FlightSegment, CabinName } from "./types";

const OFFERS_URL = "https://www.sas.no/api/offers/flights";

export async function getOffersWithPoints(
  origin: string,
  destination: string,
  date: string,
  options: {
    adults?: number;
    bookingFlow?: string;
  } & SASClientOptions = {},
): Promise<FlightOffer[]> {
  const { adults = 1, bookingFlow = "points", ...clientOpts } = options;

  // Normalize date to YYYYMMDD
  const outDate = date.replace(/-/g, "");

  const raw = await sasRequest<unknown>(OFFERS_URL, {
    from: origin,
    to: destination,
    outDate,
    adt: adults,
    bookingFlow,
    pos: clientOpts.pos ?? "no",
    channel: "web",
    displayType: "upsell",
  }, clientOpts);

  if (!raw) return [];
  return parseOffers(raw, origin, destination, date);
}

function parseOffers(data: unknown, origin: string, destination: string, date: string): FlightOffer[] {
  const offers: FlightOffer[] = [];
  const dataObj = (data ?? {}) as Record<string, unknown>;
  // Normalize date
  const normalDate = date.includes("-") ? date : `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`;

  const outboundFlights = dataObj.outboundFlights ?? {};
  const flights = typeof outboundFlights === "object" && !Array.isArray(outboundFlights)
    ? Object.entries(outboundFlights as Record<string, unknown>)
    : [];

  for (const [flightKey, flightData] of flights) {
    if (typeof flightData !== "object" || !flightData) continue;
    const fd = flightData as Record<string, unknown>;

    // Parse segments
    const rawSegments = Array.isArray(fd.segments) ? fd.segments : [];
    const segments: FlightSegment[] = rawSegments.map((seg: unknown) => {
      const s = (seg ?? {}) as Record<string, unknown>;
      const depAir = typeof s.departureAirport === "object"
        ? (s.departureAirport as Record<string, unknown>)?.code
        : s.departureAirport;
      const arrAir = typeof s.arrivalAirport === "object"
        ? (s.arrivalAirport as Record<string, unknown>)?.code
        : s.arrivalAirport;
      const carrier = typeof s.carrier === "object"
        ? (s.carrier as Record<string, unknown>)?.code
        : s.carrier;
      const mc = typeof s.marketingCarrier === "object"
        ? (s.marketingCarrier as Record<string, unknown>)
        : {};
      const ac = typeof s.airCraft === "object"
        ? (s.airCraft as Record<string, unknown>)?.name
        : String(s.airCraft ?? "");
      const durRaw = s.duration;
      let durMins = 0;
      if (typeof durRaw === "string" && durRaw.includes(":")) {
        const [h, m] = durRaw.split(":");
        durMins = Number(h) * 60 + Number(m);
      } else {
        durMins = Number(durRaw ?? 0);
      }

      return {
        flightNumber: String(s.flightNumber ?? ""),
        carrier: String(carrier ?? ""),
        carrierName: String(mc.name ?? ""),
        departureAirport: String(depAir ?? ""),
        arrivalAirport: String(arrAir ?? ""),
        departureTime: String(s.departureTime ?? ""),
        arrivalTime: String(s.arrivalTime ?? ""),
        departureDate: String(s.departureDate ?? normalDate),
        arrivalDate: String(s.arrivalDate ?? normalDate),
        aircraft: String(ac ?? ""),
        durationMinutes: durMins,
      };
    });

    const totalDuration = segments.reduce((sum, s) => sum + s.durationMinutes, 0);
    const stops = Math.max(0, segments.length - 1);

    // Parse cabins -> products
    const cabins = fd.cabins ?? {};
    const cabinEntries = typeof cabins === "object" && !Array.isArray(cabins)
      ? Object.entries(cabins as Record<string, unknown>)
      : [];

    for (const [cabinKey, cabinVal] of cabinEntries) {
      if (typeof cabinVal !== "object" || !cabinVal) continue;
      const cv = cabinVal as Record<string, unknown>;
      const cabinClass = String(cv.cabinClass ?? cabinKey);

      // Collect products from various nesting patterns
      const products: unknown[] = [];
      if (cv.products) {
        if (Array.isArray(cv.products)) products.push(...cv.products);
        else if (typeof cv.products === "object") products.push(...Object.values(cv.products as Record<string, unknown>));
      } else {
        // Check nested sub-objects
        for (const sub of Object.values(cv)) {
          if (typeof sub === "object" && sub && (sub as Record<string, unknown>).products) {
            const p = (sub as Record<string, unknown>).products;
            if (Array.isArray(p)) products.push(...p);
            else if (typeof p === "object") products.push(...Object.values(p as Record<string, unknown>));
          }
        }
      }

      for (const product of products) {
        if (typeof product !== "object" || !product) continue;
        const prod = product as Record<string, unknown>;
        const price = (prod.price ?? {}) as Record<string, unknown>;
        const fares = Array.isArray(prod.fares) ? prod.fares : [];
        const firstFare = (fares[0] ?? {}) as Record<string, unknown>;
        const seats = Number(firstFare.avlSeats ?? 0);
        const bookingClass = String(firstFare.bookingClass ?? "");
        const isBonusTicket = prod.isStandardAward === true || (price.basePrice === 0 && Number(price.points) > 0);

        if (price.points) {
          offers.push({
            origin,
            destination,
            date: normalDate,
            cabinClass: cabinClass.toUpperCase() as CabinName,
            productName: String(prod.productName ?? ""),
            points: Number(price.points ?? 0),
            taxes: Number(price.totalTax ?? 0),
            currency: String(price.currency ?? "NOK"),
            availableSeats: seats,
            bookingClass,
            segments,
            totalDurationMinutes: totalDuration,
            stops,
            flightId: flightKey,
            isBonusTicket,
            basePrice: Number(price.basePrice ?? 0),
          });
        }
      }
    }
  }

  return offers.sort((a, b) => a.points - b.points);
}
