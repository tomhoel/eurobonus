export interface Airport {
  code: string;
  name: string;
  country: string;
}

/** SAS hubs and Star Alliance/SkyTeam hubs used as origins */
export const ORIGINS: Airport[] = [
  // Scandinavia
  { code: "OSL", name: "Oslo", country: "Norway" },
  { code: "CPH", name: "Copenhagen", country: "Denmark" },
  { code: "ARN", name: "Stockholm Arlanda", country: "Sweden" },
  { code: "GOT", name: "Gothenburg", country: "Sweden" },
  { code: "BMA", name: "Stockholm Bromma", country: "Sweden" },
  { code: "BGO", name: "Bergen", country: "Norway" },
  { code: "TRD", name: "Trondheim", country: "Norway" },
  { code: "SVG", name: "Stavanger", country: "Norway" },
  { code: "AAL", name: "Aalborg", country: "Denmark" },
  { code: "BLL", name: "Billund", country: "Denmark" },
  { code: "HEL", name: "Helsinki", country: "Finland" },
  // Major European hubs
  { code: "LHR", name: "London Heathrow", country: "United Kingdom" },
  { code: "CDG", name: "Paris CDG", country: "France" },
  { code: "AMS", name: "Amsterdam", country: "Netherlands" },
  { code: "FRA", name: "Frankfurt", country: "Germany" },
  { code: "MUC", name: "Munich", country: "Germany" },
  { code: "ZRH", name: "Zurich", country: "Switzerland" },
  { code: "BRU", name: "Brussels", country: "Belgium" },
];

/** SAS award destinations — Europe, Asia, Americas */
export const DESTINATIONS: Airport[] = [
  // Southern Europe
  { code: "AGP", name: "Malaga", country: "Spain" },
  { code: "ALC", name: "Alicante", country: "Spain" },
  { code: "BCN", name: "Barcelona", country: "Spain" },
  { code: "MAD", name: "Madrid", country: "Spain" },
  { code: "PMI", name: "Palma de Mallorca", country: "Spain" },
  { code: "TFS", name: "Tenerife", country: "Spain" },
  { code: "LPA", name: "Gran Canaria", country: "Spain" },
  { code: "FCO", name: "Rome", country: "Italy" },
  { code: "MXP", name: "Milan", country: "Italy" },
  { code: "NAP", name: "Naples", country: "Italy" },
  { code: "VCE", name: "Venice", country: "Italy" },
  { code: "ATH", name: "Athens", country: "Greece" },
  { code: "CHQ", name: "Chania", country: "Greece" },
  { code: "RHO", name: "Rhodes", country: "Greece" },
  { code: "LIS", name: "Lisbon", country: "Portugal" },
  { code: "FAO", name: "Faro", country: "Portugal" },
  { code: "SPU", name: "Split", country: "Croatia" },
  { code: "DBV", name: "Dubrovnik", country: "Croatia" },
  { code: "NIC", name: "Nice", country: "France" },
  // Central & Eastern Europe
  { code: "VIE", name: "Vienna", country: "Austria" },
  { code: "PRG", name: "Prague", country: "Czech Republic" },
  { code: "WAW", name: "Warsaw", country: "Poland" },
  { code: "GDN", name: "Gdansk", country: "Poland" },
  { code: "BUD", name: "Budapest", country: "Hungary" },
  // UK & Ireland
  { code: "MAN", name: "Manchester", country: "United Kingdom" },
  { code: "EDI", name: "Edinburgh", country: "United Kingdom" },
  { code: "DUB", name: "Dublin", country: "Ireland" },
  // Nordics & Baltics
  { code: "KEF", name: "Reykjavik", country: "Iceland" },
  { code: "TLL", name: "Tallinn", country: "Estonia" },
  { code: "RIX", name: "Riga", country: "Latvia" },
  // Middle East & Turkey
  { code: "IST", name: "Istanbul", country: "Turkey" },
  { code: "AYT", name: "Antalya", country: "Turkey" },
  // Asia
  { code: "BKK", name: "Bangkok", country: "Thailand" },
  { code: "NRT", name: "Tokyo Narita", country: "Japan" },
  { code: "HND", name: "Tokyo Haneda", country: "Japan" },
  { code: "KIX", name: "Osaka", country: "Japan" },
  { code: "SIN", name: "Singapore", country: "Singapore" },
  { code: "PVG", name: "Shanghai", country: "China" },
  { code: "PEK", name: "Beijing", country: "China" },
  { code: "HKG", name: "Hong Kong", country: "Hong Kong" },
  { code: "SGN", name: "Ho Chi Minh City", country: "Vietnam" },
  { code: "HAN", name: "Hanoi", country: "Vietnam" },
  { code: "ICN", name: "Seoul", country: "South Korea" },
  { code: "DEL", name: "Delhi", country: "India" },
  { code: "BOM", name: "Mumbai", country: "India" },
  // Americas
  { code: "JFK", name: "New York", country: "USA" },
  { code: "EWR", name: "Newark", country: "USA" },
  { code: "LAX", name: "Los Angeles", country: "USA" },
  { code: "SFO", name: "San Francisco", country: "USA" },
  { code: "ORD", name: "Chicago", country: "USA" },
  { code: "MIA", name: "Miami", country: "USA" },
  { code: "IAD", name: "Washington DC", country: "USA" },
  { code: "BOS", name: "Boston", country: "USA" },
  { code: "YYZ", name: "Toronto", country: "Canada" },
  // Africa
  { code: "CPT", name: "Cape Town", country: "South Africa" },
  { code: "NBO", name: "Nairobi", country: "Kenya" },
];

/** All known airports for autocomplete */
export const ALL_AIRPORTS: Airport[] = [...ORIGINS, ...DESTINATIONS];

export function findAirport(code: string): Airport | undefined {
  return ALL_AIRPORTS.find((a) => a.code === code.toUpperCase());
}
