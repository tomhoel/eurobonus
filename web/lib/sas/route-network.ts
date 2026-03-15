/**
 * SAS EuroBonus award route network.
 * Maps each origin to its available destinations.
 * Based on SAS route map and award-finder data.
 */
export const SAS_ROUTES: Record<string, string[]> = {
  // ── Scandinavia ──
  OSL: [
    // Domestic & Nordic
    "BGO", "TRD", "SVG", "CPH", "ARN", "GOT", "HEL", "KEF", "AAL", "BLL",
    // Europe
    "LHR", "MAN", "EDI", "DUB", "CDG", "NIC", "AMS", "FRA", "MUC", "ZRH", "BRU",
    "BCN", "MAD", "AGP", "ALC", "PMI", "TFS", "LPA",
    "FCO", "MXP", "NAP", "VCE",
    "ATH", "CHQ", "RHO",
    "LIS", "FAO",
    "SPU", "DBV",
    "VIE", "PRG", "WAW", "GDN", "BUD",
    "TLL", "RIX",
    "IST", "AYT",
    // Long-haul
    "BKK", "NRT", "HND", "SIN", "PVG", "PEK", "HKG", "SGN", "ICN",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD",
  ],
  CPH: [
    "OSL", "BGO", "TRD", "SVG", "ARN", "GOT", "HEL", "KEF", "AAL", "BLL", "BMA",
    "LHR", "MAN", "EDI", "DUB", "CDG", "NIC", "AMS", "FRA", "MUC", "ZRH", "BRU",
    "BCN", "MAD", "AGP", "ALC", "PMI", "TFS", "LPA",
    "FCO", "MXP", "NAP", "VCE",
    "ATH", "CHQ", "RHO",
    "LIS", "FAO",
    "SPU", "DBV",
    "VIE", "PRG", "WAW", "GDN", "BUD",
    "TLL", "RIX",
    "IST", "AYT",
    "BKK", "NRT", "HND", "SIN", "PVG", "PEK", "HKG", "SGN", "ICN",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD", "BOS",
    "YYZ",
    "CPT", "NBO",
  ],
  ARN: [
    "OSL", "BGO", "TRD", "CPH", "GOT", "HEL", "KEF", "AAL", "BLL", "BMA",
    "LHR", "MAN", "EDI", "DUB", "CDG", "NIC", "AMS", "FRA", "MUC", "ZRH", "BRU",
    "BCN", "MAD", "AGP", "ALC", "PMI", "TFS", "LPA",
    "FCO", "MXP", "NAP",
    "ATH", "CHQ", "RHO",
    "LIS",
    "SPU", "DBV",
    "VIE", "PRG", "WAW", "BUD",
    "TLL", "RIX",
    "IST", "AYT",
    "BKK", "NRT", "HND", "SIN", "PVG", "PEK", "HKG", "ICN",
    "JFK", "LAX", "MIA",
  ],
  GOT: [
    "OSL", "CPH", "ARN", "HEL",
    "LHR", "AMS", "FRA", "MUC",
    "BCN", "AGP", "PMI", "TFS",
    "FCO",
    "ATH", "CHQ",
    "SPU",
    "IST", "AYT",
  ],
  BGO: [
    "OSL", "CPH", "ARN",
    "LHR", "AMS", "FRA",
    "BCN", "AGP", "PMI", "TFS", "LPA",
    "ATH", "CHQ",
    "SPU",
    "IST", "AYT",
  ],
  TRD: [
    "OSL", "CPH", "ARN",
    "LHR", "AMS",
    "AGP", "PMI", "TFS", "LPA",
    "ATH", "CHQ",
    "AYT",
  ],
  SVG: [
    "OSL", "CPH", "ARN",
    "LHR", "AMS",
    "AGP", "PMI", "TFS",
    "ATH",
    "AYT",
  ],
  AAL: ["OSL", "CPH"],
  BLL: ["OSL", "CPH", "ARN", "FRA", "MUC"],
  BMA: ["CPH", "ARN"],
  HEL: [
    "OSL", "CPH", "ARN", "GOT",
    "LHR", "CDG", "AMS", "FRA", "MUC", "ZRH", "BRU",
    "BCN", "MAD", "AGP",
    "FCO", "MXP",
    "ATH",
    "LIS",
    "VIE", "PRG", "WAW", "BUD",
    "TLL", "RIX",
    "IST",
    "BKK", "NRT", "SIN", "HKG", "PEK",
    "JFK",
  ],
  // ── Major European hubs (connecting via SAS or SkyTeam) ──
  LHR: [
    "OSL", "CPH", "ARN", "GOT", "BGO", "SVG", "HEL",
    "BKK", "NRT", "HND", "SIN", "HKG", "PEK", "PVG", "ICN", "DEL", "BOM",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD", "BOS", "YYZ",
    "CPT", "NBO",
  ],
  CDG: [
    "OSL", "CPH", "ARN", "HEL",
    "BKK", "NRT", "HND", "SIN", "HKG", "PEK", "PVG", "SGN", "HAN", "ICN", "DEL", "BOM",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD", "BOS", "YYZ",
    "CPT", "NBO",
  ],
  AMS: [
    "OSL", "CPH", "ARN", "GOT", "BGO", "TRD", "SVG", "HEL",
    "BKK", "NRT", "HND", "KIX", "SIN", "HKG", "PEK", "PVG", "SGN", "HAN", "ICN", "DEL", "BOM",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD", "BOS", "YYZ",
    "CPT", "NBO",
  ],
  FRA: [
    "OSL", "CPH", "ARN", "GOT", "BGO", "BLL", "HEL",
    "BKK", "NRT", "HND", "KIX", "SIN", "HKG", "PEK", "PVG", "SGN", "ICN", "DEL", "BOM",
    "JFK", "EWR", "LAX", "SFO", "ORD", "MIA", "IAD", "YYZ",
    "CPT", "NBO",
  ],
  MUC: [
    "OSL", "CPH", "ARN", "GOT", "BLL", "HEL",
    "BKK", "NRT", "SIN", "HKG", "PEK", "PVG", "ICN", "DEL",
    "JFK", "LAX", "SFO", "ORD",
    "CPT",
  ],
  ZRH: [
    "OSL", "CPH", "ARN", "HEL",
    "BKK", "NRT", "SIN", "HKG", "PEK",
    "JFK", "LAX", "SFO",
  ],
  BRU: [
    "OSL", "CPH", "ARN", "HEL",
    "BKK", "NRT", "SIN", "HKG",
    "JFK", "IAD",
    "NBO",
  ],
};

/**
 * Get available destinations from a given origin.
 * Returns the destination codes that SAS operates from this origin.
 */
export function getDestinationsFrom(origin: string): string[] {
  return SAS_ROUTES[origin.toUpperCase()] ?? [];
}

/**
 * Check if a route exists in the SAS network.
 */
export function isValidRoute(origin: string, destination: string): boolean {
  const dests = SAS_ROUTES[origin.toUpperCase()];
  return dests?.includes(destination.toUpperCase()) ?? false;
}
