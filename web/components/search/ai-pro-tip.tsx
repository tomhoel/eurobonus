"use client";

import { Info } from "lucide-react";
import type { SearchResult, SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface AIProTipProps {
  results: SearchResult[];
  filters: SearchFilters;
}

const TIPS: string[] = [
  "Book bonus tickets 60-90 days out for best availability on popular routes.",
  "SAS releases more award seats on off-peak days — try Tue or Wed departures.",
  "Partner awards via SkyTeam often have different availability than SAS metal.",
  "Business bonus tickets to Asia are most available from Scandinavian hubs.",
  "Set alerts for your route — availability changes daily.",
  "Try positioning flights from nearby airports if your hub has no availability.",
  "One-stop via CPH or ARN often has better award availability than direct.",
];

export function AIProTip({ results, filters }: AIProTipProps) {
  let tip = TIPS[0];
  if (filters.cabin === "BUSINESS") tip = TIPS[3];
  else if (results.length === 0 && filters.origin) tip = TIPS[5];
  else if (results.some((r) => r.stops > 0)) tip = TIPS[6];
  else if (results.length > 0) tip = TIPS[1];

  return (
    <div className="rounded-xl border border-blue-400/10 bg-blue-400/[0.03] p-4">
      <div className={`mb-2 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.08em] text-blue-400/60 ${mono}`}>
        <Info className="size-3" />
        Pro Tip
      </div>
      <p className="text-[12px] leading-[1.7] text-[hsla(0,0%,100%,.35)]">
        {tip}
      </p>
    </div>
  );
}
