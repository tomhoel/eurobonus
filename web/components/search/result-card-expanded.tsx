"use client";

import { Plane, Clock, ExternalLink } from "lucide-react";
import type { SearchResult } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface ResultCardExpandedProps {
  result: SearchResult;
}

export function ResultCardExpanded({ result }: ResultCardExpandedProps) {
  const formatDuration = (mins: number) => {
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return `${h}h ${m}m`;
  };

  const bookUrl = `https://www.sas.no/book/flights?origin=${result.origin}&destination=${result.destination}&outDate=${result.date.replace(/-/g, "")}&adt=1&bookingFlow=points`;

  if (result.segments.length === 0) {
    return (
      <div className="border-t border-[hsla(0,0%,100%,.04)] bg-[hsla(0,0%,100%,.01)] p-5">
        <div className="flex items-center justify-between">
          <div className="text-[13px] text-[hsla(0,0%,100%,.35)]">
            <span className={`font-medium text-[hsla(0,0%,100%,.5)] ${mono}`}>
              {result.route}
            </span>
            <span className="ml-2">{formatDuration(result.totalDurationMinutes)}</span>
          </div>
          <BookLink url={bookUrl} />
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-[hsla(0,0%,100%,.04)] bg-[hsla(0,0%,100%,.01)] p-5">
      <div className="space-y-3">
        {result.segments.map((seg, i) => (
          <div key={i}>
            {i > 0 && (
              <div className={`mb-3 flex items-center gap-2 rounded-md bg-amber-500/5 px-3 py-1.5 text-[11px] text-amber-400/70 ${mono}`}>
                <Clock className="size-3" />
                Layover at {result.segments[i - 1].arrivalAirport} ·{" "}
                {formatLayover(result.segments[i - 1], seg)}
              </div>
            )}

            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex size-6 items-center justify-center rounded-full bg-[hsla(0,0%,100%,.04)]">
                <Plane className="size-3 text-emerald-400/60" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 text-[13px]">
                  <span className={`font-bold text-[hsla(0,0%,100%,.6)] ${mono}`}>
                    {seg.flightNumber}
                  </span>
                  <span className="text-[hsla(0,0%,100%,.15)]">·</span>
                  <span className="text-[hsla(0,0%,100%,.3)]">
                    {seg.carrierName || seg.carrier}
                  </span>
                  {seg.aircraft && (
                    <>
                      <span className="text-[hsla(0,0%,100%,.15)]">·</span>
                      <span className="text-[hsla(0,0%,100%,.18)]">{seg.aircraft}</span>
                    </>
                  )}
                </div>
                <div className={`mt-1.5 flex items-center gap-3 text-[12px] ${mono}`}>
                  <div>
                    <span className="text-emerald-400/70">{seg.departureAirport}</span>
                    <span className="ml-1 text-[hsla(0,0%,100%,.35)]">{seg.departureTime}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[hsla(0,0%,100%,.12)]">
                    <div className="h-px w-5 bg-[hsla(0,0%,100%,.06)]" />
                    <span className="text-[10px]">{formatDuration(seg.durationMinutes)}</span>
                    <div className="h-px w-5 bg-[hsla(0,0%,100%,.06)]" />
                  </div>
                  <div>
                    <span className="text-emerald-400/70">{seg.arrivalAirport}</span>
                    <span className="ml-1 text-[hsla(0,0%,100%,.35)]">{seg.arrivalTime}</span>
                    {seg.arrivalDate !== seg.departureDate && (
                      <span className="ml-1 text-amber-400/60">+1</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 flex justify-end border-t border-[hsla(0,0%,100%,.04)] pt-4">
        <BookLink url={bookUrl} />
      </div>
    </div>
  );
}

function BookLink({ url }: { url: string }) {
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={`inline-flex items-center gap-1.5 rounded-md border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.03)] px-3 py-1.5 text-[11px] font-medium text-[hsla(0,0%,100%,.45)] transition-colors hover:border-[hsla(0,0%,100%,.15)] hover:text-[hsla(0,0%,100%,.7)] ${mono}`}
    >
      Book on SAS
      <ExternalLink className="size-3" />
    </a>
  );
}

function formatLayover(
  prev: { arrivalTime: string; arrivalDate: string },
  next: { departureTime: string; departureDate: string },
): string {
  try {
    const [ph, pm] = prev.arrivalTime.split(":").map(Number);
    const [nh, nm] = next.departureTime.split(":").map(Number);
    let diffMins = nh * 60 + nm - (ph * 60 + pm);
    if (prev.arrivalDate !== next.departureDate) diffMins += 24 * 60;
    if (diffMins < 0) diffMins += 24 * 60;
    const h = Math.floor(diffMins / 60);
    const m = diffMins % 60;
    return `${h}h ${m}m`;
  } catch {
    return "—";
  }
}
