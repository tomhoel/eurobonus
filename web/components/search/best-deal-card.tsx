"use client";

import { Sparkles, Star } from "lucide-react";
import type { SearchResult } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface BestDealCardProps {
  deal: SearchResult | null;
}

export function BestDealCard({ deal }: BestDealCardProps) {
  if (!deal) return null;

  return (
    <div className="rounded-xl border border-emerald-500/15 bg-emerald-500/[0.03] p-4">
      <div className={`mb-3 flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-[0.08em] text-emerald-400 ${mono}`}>
        <Sparkles className="size-3" />
        Best Deal
      </div>
      <div className="flex items-center justify-between">
        <div>
          <div className={`text-[14px] font-bold text-[hsla(0,0%,100%,.75)] ${mono}`}>
            {deal.origin} → {deal.destination}
          </div>
          <div className="mt-0.5 text-[12px] text-[hsla(0,0%,100%,.3)]">
            {deal.cabinClass} · {deal.carrierNames[0] || deal.carriers[0]}
          </div>
        </div>
        <div className="text-right">
          <div className={`text-[20px] font-bold text-emerald-400 ${mono}`}>
            {deal.points.toLocaleString()}
          </div>
          <div className={`text-[10px] text-[hsla(0,0%,100%,.22)] ${mono}`}>
            points
          </div>
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3 border-t border-emerald-500/10 pt-3">
        {deal.percentBelowAvg > 0 && (
          <span className={`text-[11px] text-amber-400/70 ${mono}`}>
            {deal.percentBelowAvg}% below avg
          </span>
        )}
        <div className="flex items-center gap-[2px]">
          {Array.from({ length: 5 }, (_, i) => (
            <Star
              key={i}
              className={`size-[9px] ${
                i < Math.round(deal.valueScore / 2)
                  ? "fill-emerald-400 text-emerald-400"
                  : "text-[hsla(0,0%,100%,.08)]"
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
