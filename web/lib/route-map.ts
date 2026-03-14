export interface Airport {
  code: string;
  name: string;
  country: string;
}

/** Common origin airports for award searches */
export const ORIGINS: Airport[] = [
  { code: "OSL", name: "Oslo", country: "Norway" },
  { code: "CPH", name: "Copenhagen", country: "Denmark" },
  { code: "ARN", name: "Stockholm", country: "Sweden" },
  { code: "CDG", name: "Paris", country: "France" },
  { code: "AMS", name: "Amsterdam", country: "Netherlands" },
  { code: "LHR", name: "London Heathrow", country: "United Kingdom" },
  { code: "FRA", name: "Frankfurt", country: "Germany" },
];

/** Popular long-haul destinations */
export const DESTINATIONS: Airport[] = [
  { code: "BKK", name: "Bangkok", country: "Thailand" },
  { code: "NRT", name: "Tokyo Narita", country: "Japan" },
  { code: "HND", name: "Tokyo Haneda", country: "Japan" },
  { code: "KIX", name: "Osaka", country: "Japan" },
  { code: "SIN", name: "Singapore", country: "Singapore" },
  { code: "PVG", name: "Shanghai", country: "China" },
  { code: "PEK", name: "Beijing", country: "China" },
  { code: "SGN", name: "Ho Chi Minh City", country: "Vietnam" },
  { code: "HAN", name: "Hanoi", country: "Vietnam" },
  { code: "ICN", name: "Seoul", country: "South Korea" },
  { code: "JFK", name: "New York", country: "USA" },
  { code: "LAX", name: "Los Angeles", country: "USA" },
  { code: "MIA", name: "Miami", country: "USA" },
];

/** All known airports for autocomplete */
export const ALL_AIRPORTS: Airport[] = [...ORIGINS, ...DESTINATIONS];

export function findAirport(code: string): Airport | undefined {
  return ALL_AIRPORTS.find((a) => a.code === code.toUpperCase());
}
