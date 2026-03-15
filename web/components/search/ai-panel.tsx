"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, ChevronRight, ChevronLeft } from "lucide-react";
import type { SearchResult, SearchFilters } from "@/lib/search/types";
import { BestDealCard } from "./best-deal-card";
import { PricePrediction } from "./price-prediction";
import { AISuggestions } from "./ai-suggestions";
import { AIProTip } from "./ai-pro-tip";

interface AIPanelProps {
  results: SearchResult[];
  filteredResults: SearchResult[];
  filters: SearchFilters;
  onApplyFilters: (partial: Partial<SearchFilters>) => void;
}

const mono = "font-[family-name:var(--font-geist-mono)]";

export function AIPanel({
  results,
  filteredResults,
  filters,
  onApplyFilters,
}: AIPanelProps) {
  const [collapsed, setCollapsed] = useState(false);
  const bestDeal = filteredResults.find((r) => r.isTopPick) ?? null;

  return (
    <>
      {/* Desktop panel */}
      <AnimatePresence mode="wait">
        {!collapsed && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 300, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="hidden shrink-0 lg:block"
          >
            <div className="sticky top-20 space-y-3">
              <div className="flex items-center justify-between">
                <div className={`flex items-center gap-1.5 text-[12px] font-medium text-[hsla(0,0%,100%,.35)] ${mono}`}>
                  <Sparkles className="size-3.5 text-emerald-400" />
                  AI INSIGHTS
                </div>
                <button
                  onClick={() => setCollapsed(true)}
                  className="rounded-md p-1 text-[hsla(0,0%,100%,.18)] transition hover:bg-[hsla(0,0%,100%,.05)] hover:text-[hsla(0,0%,100%,.4)]"
                >
                  <ChevronRight className="size-3.5" />
                </button>
              </div>

              <BestDealCard deal={bestDeal} />
              <PricePrediction
                origin={filters.origin}
                destination={filters.destination}
              />
              <AISuggestions
                results={results}
                filters={filters}
                onApplyFilters={onApplyFilters}
              />
              <AIProTip results={filteredResults} filters={filters} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Collapsed strip */}
      {collapsed && (
        <button
          onClick={() => setCollapsed(false)}
          className="hidden shrink-0 lg:flex lg:w-8 lg:flex-col lg:items-center lg:gap-1.5 lg:rounded-lg lg:border lg:border-[hsla(0,0%,100%,.06)] lg:bg-[hsla(0,0%,100%,.02)] lg:py-4 lg:text-emerald-400/60 lg:transition-colors lg:hover:border-[hsla(0,0%,100%,.12)] lg:hover:text-emerald-400"
        >
          <ChevronLeft className="size-3" />
          <Sparkles className="size-3" />
          <span className={`mt-1 text-[10px] [writing-mode:vertical-lr] ${mono}`}>
            AI
          </span>
        </button>
      )}

      {/* Mobile section */}
      {!collapsed && filteredResults.length > 0 && (
        <div className="mt-8 space-y-3 lg:hidden">
          <div className={`flex items-center gap-1.5 text-[12px] font-medium text-[hsla(0,0%,100%,.35)] ${mono}`}>
            <Sparkles className="size-3.5 text-emerald-400" />
            AI INSIGHTS
          </div>
          <BestDealCard deal={bestDeal} />
          <div className="grid gap-3 sm:grid-cols-2">
            <PricePrediction
              origin={filters.origin}
              destination={filters.destination}
            />
            <AIProTip results={filteredResults} filters={filters} />
          </div>
          <AISuggestions
            results={results}
            filters={filters}
            onApplyFilters={onApplyFilters}
          />
        </div>
      )}
    </>
  );
}
