export type CabinCode = "AG" | "AP" | "AB";
export type CabinName = "ECONOMY" | "PREMIUM" | "BUSINESS";

export const CABIN_CODE_TO_NAME: Record<CabinCode, CabinName> = {
  AG: "ECONOMY", AP: "PREMIUM", AB: "BUSINESS",
};
export const CABIN_NAME_TO_CODE: Record<CabinName, CabinCode> = {
  ECONOMY: "AG", PREMIUM: "AP", BUSINESS: "AB",
};

export interface FlightSegment {
  flightNumber: string;
  carrier: string;
  carrierName: string;
  departureAirport: string;
  arrivalAirport: string;
  departureTime: string;
  arrivalTime: string;
  departureDate: string;
  arrivalDate: string;
  aircraft: string;
  durationMinutes: number;
}

export interface FlightOffer {
  origin: string;
  destination: string;
  date: string;
  cabinClass: CabinName;
  productName: string;
  points: number;
  taxes: number;
  currency: string;
  availableSeats: number;
  bookingClass: string;
  segments: FlightSegment[];
  totalDurationMinutes: number;
  stops: number;
  flightId: string;
  isBonusTicket: boolean;
  basePrice: number;
}

export interface AvailabilityDate {
  date: string;
  economySeats: number;
  premiumSeats: number;
  businessSeats: number;
}

export interface AvailabilityDestination {
  iataCode: string;
  cityName: string;
  outbound: AvailabilityDate[];
  inbound: AvailabilityDate[];
}

export interface RouteInfo {
  flightId: string;
  departureDate: string;
  departureTime: string;
  arrivalDate: string;
  arrivalTime: string;
  flyTimeMinutes: number;
  totalTimeMinutes: number;
  numFlights: number;
  haulType: string;
  availability: Record<string, number>;
}

export interface PartnerCabin {
  cabin: CabinName;
  points: number;
  cash: number;
  seats: number;
}

export interface PartnerFlight {
  date: string;
  departureTime: string;
  arrivalTime: string;
  origin: string;
  destination: string;
  route: string;
  carriers: string[];
  carrierNames: string[];
  stops: number;
  totalDurationMinutes: number;
  cabins: PartnerCabin[];
}
