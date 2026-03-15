"use client";

import { useState, useRef, useCallback } from "react";
import { Search, Sparkles, Loader2 } from "lucide-react";
import type { SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface SearchBarProps {
  onApplyFilters: (partial: Partial<SearchFilters>) => void;
}

export function SearchBar({ onApplyFilters }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [isAI, setIsAI] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const detectAI = (text: string) =>
    text.length > 3 && /[a-z\s]{4,}/i.test(text) && !/^[A-Z]{3}$/.test(text.trim());

  const handleChange = useCallback((value: string) => {
    setQuery(value);
    const ai = detectAI(value);
    setIsAI(ai);

    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (ai && value.length > 5) {
      debounceRef.current = setTimeout(async () => {
        setParsing(true);
        try {
          const res = await fetch("/api/search/ai", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ mode: "parse", query: value }),
          });
          const data = await res.json();
          if (data.filters) {
            const parts: string[] = [];
            if (data.filters.cabin) parts.push(data.filters.cabin);
            if (data.filters.destination) parts.push(`→ ${data.filters.destination}`);
            if (data.filters.origin) parts.push(`${data.filters.origin} →`);
            if (data.filters.maxPoints)
              parts.push(`≤${(data.filters.maxPoints / 1000).toFixed(0)}k`);
            if (data.filters.maxStops === 0) parts.push("direct");
            if (data.filters.bonusOnly) parts.push("bonus");
            setPreview(parts.length > 0 ? parts.join(" · ") : null);
          }
        } catch {
          setPreview(null);
        } finally {
          setParsing(false);
        }
      }, 400);
    } else {
      setPreview(null);
    }
  }, []);

  const handleSubmit = async () => {
    if (!query.trim()) return;
    if (isAI) {
      setParsing(true);
      try {
        const res = await fetch("/api/search/ai", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode: "parse", query }),
        });
        const data = await res.json();
        if (data.filters) {
          onApplyFilters(data.filters);
          setQuery("");
          setPreview(null);
        }
      } catch {
        // Silent
      } finally {
        setParsing(false);
      }
    }
  };

  return (
    <div className="relative">
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
          placeholder='Try "business to Tokyo under 80k points" or type an airport code'
          className={`flex-1 bg-transparent text-[14px] text-[hsla(0,0%,100%,.75)] outline-none placeholder:text-[hsla(0,0%,100%,.18)] ${mono}`}
        />
        {parsing && (
          <Loader2 className="size-[14px] animate-spin text-emerald-400" />
        )}
      </div>
      {preview && (
        <div className="absolute top-full z-10 mt-2 w-full rounded-lg border border-emerald-500/15 bg-[#0a0a0a] px-4 py-2.5 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="size-3 text-emerald-400" />
              <span className={`text-[12px] text-emerald-400/80 ${mono}`}>
                {preview}
              </span>
            </div>
            <button
              onClick={handleSubmit}
              className={`rounded-md bg-emerald-500/10 px-3 py-1 text-[11px] font-medium text-emerald-400 transition hover:bg-emerald-500/20 ${mono}`}
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
