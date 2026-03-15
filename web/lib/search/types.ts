import type { FlightOffer, PartnerFlight, CabinName, AvailabilityDate } from "@/lib/sas/types";

export type SortOption = "best-value" | "lowest-points" | "shortest" | "fewest-stops";
export type TimeRange = "any" | "morning" | "afternoon" | "evening" | "night";
export type ViewMode = "list" | "calendar" | "map";
export type AvailabilityTrend = "any" | "increasing" | "decreasing" | "stable";

export interface SearchFilters {
  origin: string;
  destination: string;
  dateFrom: string;
  dateTo: string;
  flexDays: number;
  cabin: CabinName | "ANY";
  month: string;
  // Points & value
  maxPoints: number;
  bonusOnly: boolean;
  minValueScore: number;
  // Route & schedule
  maxStops: number | null; // null = any
  airlines: string[];
  departureTime: TimeRange;
  maxDuration: number; // minutes, 0 = any
  // Power-user
  includePartners: boolean;
  availabilityTrend: AvailabilityTrend;
  minSeats: number;
  // Sort
  sortBy: SortOption;
}

export const DEFAULT_FILTERS: SearchFilters = {
  origin: "",
  destination: "",
  dateFrom: "",
  dateTo: "",
  flexDays: 0,
  cabin: "ANY",
  month: "",
  maxPoints: 0,
  bonusOnly: false,
  minValueScore: 0,
  maxStops: null,
  airlines: [],
  departureTime: "any",
  maxDuration: 0,
  includePartners: true,
  availabilityTrend: "any",
  minSeats: 1,
  sortBy: "best-value",
};

export interface SearchResult {
  id: string;
  type: "sas" | "partner";
  origin: string;
  destination: string;
  date: string;
  cabinClass: CabinName;
  points: number;
  taxes: number;
  currency: string;
  availableSeats: number;
  stops: number;
  totalDurationMinutes: number;
  departureTime: string;
  arrivalTime: string;
  carriers: string[];
  carrierNames: string[];
  route: string;
  isBonusTicket: boolean;
  segments: FlightOffer["segments"];
  flightId: string;
  bookingClass: string;
  productName: string;
  // Computed
  valueScore: number;
  isTopPick: boolean;
  percentBelowAvg: number;
  seatUrgency: "high" | "medium" | "low";
}

export interface CabinOption {
  cabinClass: CabinName;
  points: number;
  taxes: number;
  currency: string;
  availableSeats: number;
  isBonusTicket: boolean;
  productName: string;
  bookingClass: string;
  valueScore: number;
  percentBelowAvg: number;
  seatUrgency: "high" | "medium" | "low";
}

export interface GroupedFlight {
  id: string;
  type: "sas" | "partner";
  origin: string;
  destination: string;
  date: string;
  departureTime: string;
  arrivalTime: string;
  stops: number;
  totalDurationMinutes: number;
  carriers: string[];
  carrierNames: string[];
  route: string;
  segments: FlightOffer["segments"];
  flightId: string;
  cabins: CabinOption[];
  lowestPoints: number;
  hasBonusFare: boolean;
  isTopPick: boolean;
}

export interface AIInsight {
  bestDeal: SearchResult | null;
  pricePrediction: { date: string; seats: number }[];
  suggestions: AISuggestion[];
  proTip: string;
}

export interface AISuggestion {
  origin: string;
  destination: string;
  cabin: CabinName;
  points: number;
  seats: number;
  label: string;
}

export type { FlightOffer, PartnerFlight, CabinName, AvailabilityDate };
