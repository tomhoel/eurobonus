"use client";

import { useState, useRef, useCallback } from "react";
import { Search, Sparkles, Loader2, ArrowRight, MapPin } from "lucide-react";
import type { SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface SearchBarProps {
  onApplyFilters: (partial: Partial<SearchFilters>) => void;
}

interface ParseResult {
  filters: Record<string, unknown>;
  reasoning: string | null;
  suggestions: string[];
}

const EXAMPLE_QUERIES = [
  "Somewhere warm this winter, direct flights only, bonus seats",
  "Business class to Tokyo, flexible on dates",
  "Beach holiday under 5h flight, budget 30k points",
  "Weekend city break in Europe, economy",
];

export function SearchBar({ onApplyFilters }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [isAI, setIsAI] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<ParseResult | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const detectAI = (text: string) =>
    text.length > 3 && /[a-z\s]{4,}/i.test(text) && !/^[A-Z]{3}$/.test(text.trim());

  const parseQuery = useCallback(async (text: string): Promise<ParseResult | null> => {
    try {
      const res = await fetch("/api/search/ai", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: "parse", query: text }),
      });
      const data = await res.json();
      return {
        filters: data.filters ?? {},
        reasoning: data.reasoning ?? null,
        suggestions: data.suggestions ?? [],
      };
    } catch {
      return null;
    }
  }, []);

  const handleChange = useCallback((value: string) => {
    setQuery(value);
    const ai = detectAI(value);
    setIsAI(ai);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (ai && value.length > 8) {
      debounceRef.current = setTimeout(async () => {
        setParsing(true);
        const parsed = await parseQuery(value);
        setResult(parsed);
        setParsing(false);
      }, 600);
    } else {
      setResult(null);
    }
  }, [parseQuery]);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    if (isAI) {
      setParsing(true);
      const parsed = await parseQuery(query);
      if (parsed?.filters && Object.keys(parsed.filters).length > 0) {
        onApplyFilters(parsed.filters as Partial<SearchFilters>);
        setQuery("");
        setResult(null);
      }
      setParsing(false);
    }
  };

  const handleExample = (example: string) => {
    setQuery(example);
    handleChange(example);
  };

  // Build filter chips from parsed result
  const filterChips: { label: string; color: string }[] = [];
  if (result?.filters) {
    const f = result.filters;
    if (f.origin) filterChips.push({ label: `${f.origin} →`, color: "emerald" });
    if (f.destination) filterChips.push({ label: `→ ${f.destination}`, color: "emerald" });
    if (f.cabin && f.cabin !== "ANY") filterChips.push({ label: f.cabin as string, color: "blue" });
    if (f.maxPoints) filterChips.push({ label: `≤${((f.maxPoints as number) / 1000).toFixed(0)}k pts`, color: "amber" });
    if (f.maxStops === 0) filterChips.push({ label: "direct", color: "blue" });
    else if (f.maxStops) filterChips.push({ label: `≤${f.maxStops} stops`, color: "blue" });
    if (f.bonusOnly) filterChips.push({ label: "bonus only", color: "emerald" });
    if (f.maxDuration) filterChips.push({ label: `≤${Math.round((f.maxDuration as number) / 60)}h flight`, color: "blue" });
    if (f.dateFrom) filterChips.push({ label: `from ${f.dateFrom}`, color: "amber" });
  }

  return (
    <div className="relative">
      {/* Input */}
      <div className="flex items-center gap-3 rounded-lg border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] px-4 py-3 transition-all focus-within:border-emerald-500/30 focus-within:bg-[hsla(0,0%,100%,.04)]">
        {isAI ? (
          <Sparkles className="size-[14px] shrink-0 text-emerald-400" />
        ) : (
          <Search className="size-[14px] shrink-0 text-[hsla(0,0%,100%,.22)]" />
        )}
        <input
          type="text"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="Describe your ideal trip — AI will find the best award flights"
          className={`flex-1 bg-transparent text-[14px] text-[hsla(0,0%,100%,.75)] outline-none placeholder:text-[hsla(0,0%,100%,.18)] ${mono}`}
        />
        {parsing && (
          <div className="flex items-center gap-1.5">
            <Loader2 className="size-[14px] animate-spin text-emerald-400" />
            <span className={`text-[10px] text-emerald-400/50 ${mono}`}>thinking</span>
          </div>
        )}
        {isAI && !parsing && query.length > 3 && (
          <span className={`shrink-0 rounded-[4px] bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-medium text-emerald-400/70 ${mono}`}>
            Gemini
          </span>
        )}
      </div>

      {/* Example queries — shown when input is empty */}
      {!query && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {EXAMPLE_QUERIES.map((ex) => (
            <button
              key={ex}
              onClick={() => handleExample(ex)}
              className={`rounded-md border border-[hsla(0,0%,100%,.04)] bg-[hsla(0,0%,100%,.02)] px-2 py-1 text-[10px] text-[hsla(0,0%,100%,.2)] transition-all hover:border-emerald-500/15 hover:text-emerald-400/60 ${mono}`}
            >
              {ex}
            </button>
          ))}
        </div>
      )}

      {/* AI result panel */}
      {result && !parsing && (filterChips.length > 0 || result.reasoning) && (
        <div className="absolute top-full z-20 mt-2 w-full overflow-hidden rounded-xl border border-emerald-500/15 bg-[#0a0f18] shadow-[0_12px_40px_-8px_rgba(0,0,0,.7)]">
          {/* Reasoning */}
          {result.reasoning && (
            <div className="flex items-start gap-2 border-b border-[hsla(0,0%,100%,.06)] px-4 py-3">
              <Sparkles className="mt-0.5 size-3 shrink-0 text-emerald-400" />
              <p className="text-[12px] leading-[1.5] text-[hsla(0,0%,100%,.5)]">
                {result.reasoning}
              </p>
            </div>
          )}

          {/* Filter chips */}
          {filterChips.length > 0 && (
            <div className="flex flex-wrap items-center gap-1.5 border-b border-[hsla(0,0%,100%,.06)] px-4 py-2.5">
              <span className="text-[9px] text-[hsla(0,0%,100%,.2)]">Filters:</span>
              {filterChips.map((chip, i) => (
                <span
                  key={i}
                  className={`rounded-[4px] px-1.5 py-0.5 text-[10px] font-medium ${mono} ${
                    chip.color === "emerald" ? "bg-emerald-500/10 text-emerald-400/80" :
                    chip.color === "amber" ? "bg-amber-500/10 text-amber-400/80" :
                    "bg-blue-500/10 text-blue-400/80"
                  }`}
                >
                  {chip.label}
                </span>
              ))}
            </div>
          )}

          {/* Alternative suggestions */}
          {result.suggestions.length > 0 && (
            <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] px-4 py-2">
              <MapPin className="size-3 text-[hsla(0,0%,100%,.15)]" />
              <span className="text-[9px] text-[hsla(0,0%,100%,.2)]">Also try:</span>
              {result.suggestions.map((code) => (
                <button
                  key={code}
                  onClick={() => {
                    onApplyFilters({ ...result.filters, destination: code } as Partial<SearchFilters>);
                    setQuery("");
                    setResult(null);
                  }}
                  className={`rounded-[4px] border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] px-1.5 py-0.5 text-[10px] font-medium text-[hsla(0,0%,100%,.35)] transition-all hover:border-emerald-500/20 hover:text-emerald-400 ${mono}`}
                >
                  {code}
                </button>
              ))}
            </div>
          )}

          {/* Apply button */}
          <div className="flex items-center justify-between px-4 py-2.5">
            <span className={`text-[9px] text-[hsla(0,0%,100%,.12)] ${mono}`}>
              powered by Gemini
            </span>
            <button
              onClick={handleSubmit}
              className={`flex items-center gap-1.5 rounded-md bg-emerald-500/15 px-3 py-1.5 text-[11px] font-medium text-emerald-400 transition-all hover:bg-emerald-500/25 ${mono}`}
            >
              Apply filters
              <ArrowRight className="size-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
