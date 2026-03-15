"use client";

import { useState } from "react";
import { Plane, Clock, Calendar, ChevronDown, ExternalLink, ArrowRight } from "lucide-react";
import type { GroupedFlight, CabinOption } from "@/lib/search/types";
import { ResultCardExpanded } from "./result-card-expanded";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface FlightCardProps {
  flight: GroupedFlight;
}

export function FlightCard({ flight }: FlightCardProps) {
  const [expanded, setExpanded] = useState(false);

  const fmtDur = (mins: number) => {
    if (!mins) return "—";
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  const routeParts = flight.route.split(" → ");
  const connections = routeParts.length > 2 ? routeParts.slice(1, -1) : [];

  const isNextDay =
    flight.segments.length > 0 &&
    flight.segments[flight.segments.length - 1].arrivalDate !==
      flight.segments[0].departureDate;

  const bookUrl = `https://www.sas.no/book/flights/?search=OW_${flight.origin}-${flight.destination}-${flight.date.replace(/-/g, "")}_a1c0i0y0&view=upsell&bookingFlow=points`;

  // Carriers display
  const carrierText = flight.carrierNames.join(", ") || flight.carriers.join(", ") || "SAS";
  const flightNums = flight.segments.map((s) => s.flightNumber).filter(Boolean);
  const aircraft = flight.segments[0]?.aircraft || "";

  return (
    <div
      className={`group overflow-hidden rounded-xl border transition-colors ${
        flight.isTopPick
          ? "border-emerald-500/20 bg-emerald-500/[0.02]"
          : "border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.02)]"
      } hover:border-[hsla(0,0%,100%,.14)]`}
    >
      {/* Flight info row */}
      <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-center">
        {/* LEFT: Times + route */}
        <div className="flex min-w-0 items-center gap-3 lg:w-[320px] lg:shrink-0">
          {/* Departure */}
          <div className="flex flex-col items-center">
            <span className={`text-[20px] font-bold text-white ${mono}`}>
              {flight.departureTime || "—"}
            </span>
            <span className={`text-[11px] text-[hsla(0,0%,100%,.3)] ${mono}`}>
              {flight.origin}
            </span>
          </div>

          {/* Route line */}
          <div className="flex flex-1 flex-col items-center gap-0.5 px-1">
            <div className="flex w-full items-center">
              <div className="h-px flex-1 bg-[hsla(0,0%,100%,.08)]" />
              {flight.stops > 0 ? (
                connections.length > 0 ? (
                  connections.map((city) => (
                    <div key={city} className="flex items-center">
                      <div className="size-[5px] rounded-full border border-[hsla(0,0%,100%,.15)] bg-[hsla(0,0%,100%,.05)]" />
                      <div className="h-px flex-1 bg-[hsla(0,0%,100%,.08)]" />
                    </div>
                  ))
                ) : (
                  Array.from({ length: flight.stops }, (_, i) => (
                    <div key={i} className="flex items-center">
                      <div className="size-[5px] rounded-full border border-[hsla(0,0%,100%,.15)] bg-[hsla(0,0%,100%,.05)]" />
                      <div className="h-px flex-1 bg-[hsla(0,0%,100%,.08)]" />
                    </div>
                  ))
                )
              ) : (
                <>
                  <Plane className="mx-1 size-3 text-[hsla(0,0%,100%,.12)]" />
                  <div className="h-px flex-1 bg-[hsla(0,0%,100%,.08)]" />
                </>
              )}
            </div>
            <div className={`flex items-center gap-1 text-[10px] text-[hsla(0,0%,100%,.22)] ${mono}`}>
              <Clock className="size-[10px]" />
              {fmtDur(flight.totalDurationMinutes)}
              {flight.stops > 0 ? (
                <span className="text-amber-400/60">
                  · {flight.stops} stop{flight.stops > 1 ? "s" : ""}
                  {connections.length > 0 && ` ${connections.join(", ")}`}
                </span>
              ) : (
                <span className="text-emerald-400/60">· direct</span>
              )}
            </div>
          </div>

          {/* Arrival */}
          <div className="flex flex-col items-center">
            <div className="flex items-baseline gap-0.5">
              <span className={`text-[20px] font-bold text-white ${mono}`}>
                {flight.arrivalTime || "—"}
              </span>
              {isNextDay && (
                <span className="text-[10px] font-medium text-amber-400/70">+1</span>
              )}
            </div>
            <span className={`text-[11px] text-[hsla(0,0%,100%,.3)] ${mono}`}>
              {flight.destination}
            </span>
          </div>
        </div>

        {/* RIGHT: Cabin options */}
        <div className="flex flex-1 items-stretch gap-2 overflow-x-auto lg:justify-end">
          {flight.cabins.map((cabin) => (
            <CabinCard key={cabin.cabinClass} cabin={cabin} bookUrl={bookUrl} hasBonusFare={flight.hasBonusFare} />
          ))}
        </div>
      </div>

      {/* Info bar */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={`flex w-full items-center gap-x-2 border-t border-[hsla(0,0%,100%,.04)] px-5 py-2 text-left text-[10px] text-[hsla(0,0%,100%,.2)] transition-colors hover:bg-[hsla(0,0%,100%,.02)] ${mono}`}
      >
        <span>{carrierText}</span>
        {flightNums.length > 0 && (
          <>
            <span className="text-[hsla(0,0%,100%,.07)]">·</span>
            <span>{flightNums.join(", ")}</span>
          </>
        )}
        {aircraft && (
          <>
            <span className="text-[hsla(0,0%,100%,.07)]">·</span>
            <span>{aircraft}</span>
          </>
        )}
        {flight.date && (
          <>
            <span className="text-[hsla(0,0%,100%,.07)]">·</span>
            <span className="flex items-center gap-0.5">
              <Calendar className="size-[10px]" />
              {new Date(flight.date).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
              })}
            </span>
          </>
        )}
        {flight.type === "partner" && (
          <>
            <span className="text-[hsla(0,0%,100%,.07)]">·</span>
            <span className="rounded border border-[hsla(0,0%,100%,.06)] px-1 py-[1px] text-[9px]">
              PARTNER
            </span>
          </>
        )}
        <ChevronDown
          className={`ml-auto size-3 text-[hsla(0,0%,100%,.12)] transition-transform ${
            expanded ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Expanded segment details */}
      {expanded && flight.segments.length > 0 && (
        <ResultCardExpanded
          result={{
            origin: flight.origin,
            destination: flight.destination,
            date: flight.date,
            segments: flight.segments,
            route: flight.route,
            totalDurationMinutes: flight.totalDurationMinutes,
            points: flight.lowestPoints,
            taxes: 0,
            currency: "NOK",
          } as Parameters<typeof ResultCardExpanded>[0]["result"]}
        />
      )}
    </div>
  );
}

// ── Cabin option card ──

const CABIN_COLORS: Record<string, { bg: string; border: string; label: string }> = {
  ECONOMY: {
    bg: "bg-[hsla(0,0%,100%,.02)]",
    border: "border-[hsla(0,0%,100%,.06)]",
    label: "text-[hsla(0,0%,100%,.5)]",
  },
  PREMIUM: {
    bg: "bg-blue-500/[0.03]",
    border: "border-blue-500/10",
    label: "text-blue-400/80",
  },
  BUSINESS: {
    bg: "bg-amber-500/[0.03]",
    border: "border-amber-500/10",
    label: "text-amber-400/80",
  },
};

function CabinCard({
  cabin,
  bookUrl,
  hasBonusFare,
}: {
  cabin: CabinOption;
  bookUrl: string;
  hasBonusFare: boolean;
}) {
  const colors = CABIN_COLORS[cabin.cabinClass] ?? CABIN_COLORS.ECONOMY;
  const seatColor =
    cabin.seatUrgency === "high"
      ? "text-red-400"
      : cabin.seatUrgency === "medium"
      ? "text-amber-400"
      : "text-emerald-400";

  // Revenue fares are muted when bonus fares exist on the same flight
  const isRevenueFaded = !cabin.isBonusTicket && hasBonusFare;

  if (cabin.points === 0) {
    return (
      <a
        href={bookUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={`flex min-w-[130px] flex-col items-center justify-center rounded-lg border ${colors.border} ${colors.bg} px-4 py-3 transition-colors hover:bg-[hsla(0,0%,100%,.04)]`}
      >
        <span className={`text-[10px] font-medium uppercase tracking-wider ${colors.label} ${mono}`}>
          {cabin.cabinClass}
        </span>
        <span className={`mt-1 text-[11px] text-emerald-400 ${mono}`}>
          View price <ArrowRight className="ml-0.5 inline size-[10px]" />
        </span>
      </a>
    );
  }

  return (
    <div
      className={`flex min-w-[140px] flex-col items-center rounded-lg border px-4 py-3 transition-colors ${
        cabin.isBonusTicket
          ? "border-emerald-500/15 bg-emerald-500/[0.04]"
          : `${colors.border} ${colors.bg}`
      } ${isRevenueFaded ? "opacity-40" : ""}`}
    >
      {/* Cabin label */}
      <div className="flex items-center gap-1.5">
        {cabin.isBonusTicket && (
          <span className="size-[5px] rounded-full bg-emerald-400" />
        )}
        <span
          className={`text-[10px] font-medium uppercase tracking-wider ${
            cabin.isBonusTicket ? "text-emerald-400" : colors.label
          } ${mono}`}
        >
          {cabin.cabinClass}
        </span>
      </div>

      {/* Points — the hero */}
      <div className="mt-1 flex items-baseline gap-1">
        <span
          className={`text-[20px] font-bold leading-none tracking-tight ${
            cabin.isBonusTicket ? "text-white" : "text-[hsla(0,0%,100%,.45)]"
          } ${mono}`}
        >
          {cabin.points.toLocaleString()}
        </span>
        <span className={`text-[10px] ${cabin.isBonusTicket ? "text-emerald-400/60" : "text-[hsla(0,0%,100%,.15)]"} ${mono}`}>
          p
        </span>
      </div>

      {/* Product + seats */}
      <div className={`mt-1.5 flex items-center gap-1.5 text-[9px] ${mono}`}>
        {cabin.isBonusTicket && (
          <span className="rounded bg-emerald-500/10 px-1.5 py-[1px] text-emerald-400">
            BONUS
          </span>
        )}
        <span className={seatColor}>
          {cabin.availableSeats > 0
            ? `${cabin.availableSeats} left`
            : ""}
        </span>
      </div>
    </div>
  );
}
