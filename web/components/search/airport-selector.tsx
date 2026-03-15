"use client";

import { useState, useMemo } from "react";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { ALL_AIRPORTS, findAirport, type Airport } from "@/lib/route-map";
import { getDestinationsFrom } from "@/lib/sas/route-network";
import { MapPin, Search, Check, Plane } from "lucide-react";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface AirportSelectorProps {
  value: string;
  onChange: (code: string) => void;
  label: string;
  /** When set, only show destinations reachable from this origin */
  fromOrigin?: string;
}

interface Region {
  name: string;
  airports: Airport[];
}

function groupIntoRegions(airports: Airport[]): Region[] {
  const regionDef: [string, string[]][] = [
    ["Scandinavia", ["Norway", "Denmark", "Sweden", "Finland", "Iceland"]],
    ["UK & Ireland", ["United Kingdom", "Ireland"]],
    ["Southern Europe", ["Spain", "Italy", "Greece", "Portugal", "Croatia", "France"]],
    ["Central Europe", ["Germany", "Netherlands", "Belgium", "Switzerland", "Austria", "Czech Republic", "Poland", "Hungary"]],
    ["Baltics & Turkey", ["Estonia", "Latvia", "Turkey"]],
    ["Asia", ["Thailand", "Japan", "Singapore", "China", "Hong Kong", "Vietnam", "South Korea", "India"]],
    ["Americas", ["USA", "Canada"]],
    ["Africa", ["South Africa", "Kenya"]],
  ];

  const matched = new Set<string>();
  const regions: Region[] = [];
  for (const [name, countries] of regionDef) {
    const list = airports.filter((a) => countries.includes(a.country));
    if (list.length > 0) {
      regions.push({ name, airports: list });
      list.forEach((a) => matched.add(a.code));
    }
  }
  const other = airports.filter((a) => !matched.has(a.code));
  if (other.length > 0) regions.push({ name: "Other", airports: other });
  return regions;
}

export function AirportSelector({ value, onChange, label, fromOrigin }: AirportSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const selected = ALL_AIRPORTS.find((a) => a.code === value);

  // If fromOrigin is set, filter airports to only reachable destinations
  const availableAirports = useMemo(() => {
    if (!fromOrigin) return ALL_AIRPORTS;
    const destCodes = getDestinationsFrom(fromOrigin);
    if (destCodes.length === 0) return ALL_AIRPORTS;
    return ALL_AIRPORTS.filter((a) => destCodes.includes(a.code));
  }, [fromOrigin]);

  const regions = useMemo(() => groupIntoRegions(availableAirports), [availableAirports]);

  const query = search.toLowerCase().trim();
  const filteredRegions = useMemo(() => {
    if (!query) return regions;
    return regions
      .map((r) => ({
        ...r,
        airports: r.airports.filter(
          (a) =>
            a.code.toLowerCase().includes(query) ||
            a.name.toLowerCase().includes(query) ||
            a.country.toLowerCase().includes(query),
        ),
      }))
      .filter((r) => r.airports.length > 0);
  }, [regions, query]);

  const handleSelect = (code: string) => {
    onChange(code);
    setSearch("");
    setOpen(false);
  };

  const originAirport = fromOrigin ? findAirport(fromOrigin) : null;

  return (
    <Popover open={open} onOpenChange={(v) => { setOpen(v); if (!v) setSearch(""); }}>
      <PopoverTrigger className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[hsla(0,0%,100%,.03)]">
        <MapPin className="size-4 shrink-0 text-[hsla(0,0%,100%,.2)]" />
        <div className="min-w-0 flex-1">
          <div className={`text-[10px] font-medium uppercase tracking-[0.06em] text-[hsla(0,0%,100%,.3)] ${mono}`}>{label}</div>
          {selected ? (
            <div className="mt-0.5 flex items-baseline gap-1.5 truncate">
              <span className={`text-[15px] font-semibold text-white ${mono}`}>{selected.code}</span>
              <span className="truncate text-[13px] text-[hsla(0,0%,100%,.4)]">{selected.name}</span>
            </div>
          ) : (
            <div className="mt-0.5 text-[14px] text-[hsla(0,0%,100%,.2)]">Select airport</div>
          )}
        </div>
      </PopoverTrigger>

      <PopoverContent className="w-[580px] border-[hsla(0,0%,100%,.08)] bg-[#0c0c0c] p-0 shadow-2xl" align="start" sideOffset={6}>
        {/* Header with origin context */}
        {originAirport && (
          <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] px-3 py-2">
            <Plane className="size-3 text-emerald-400/60" />
            <span className={`text-[11px] text-[hsla(0,0%,100%,.3)] ${mono}`}>
              Destinations from
            </span>
            <span className={`text-[11px] font-bold text-emerald-400 ${mono}`}>
              {originAirport.code}
            </span>
            <span className="text-[11px] text-[hsla(0,0%,100%,.25)]">
              {originAirport.name}
            </span>
            <span className={`ml-auto text-[10px] text-[hsla(0,0%,100%,.15)] ${mono}`}>
              {availableAirports.length} routes
            </span>
          </div>
        )}

        {/* Search */}
        <div className="border-b border-[hsla(0,0%,100%,.06)] px-3 py-2">
          <div className="flex items-center gap-2 rounded-md bg-[hsla(0,0%,100%,.04)] px-2.5 py-1.5">
            <Search className="size-3.5 text-[hsla(0,0%,100%,.2)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search city or airport code..."
              className={`flex-1 bg-transparent text-[13px] text-white outline-none placeholder:text-[hsla(0,0%,100%,.18)] ${mono}`}
              autoFocus
            />
            {search && (
              <button onClick={() => setSearch("")} className="text-[10px] text-[hsla(0,0%,100%,.25)] hover:text-white">Clear</button>
            )}
          </div>
        </div>

        {/* Region grid */}
        <div className="max-h-[400px] overflow-y-auto px-3 py-2">
          {filteredRegions.length === 0 ? (
            <div className="py-8 text-center text-[13px] text-[hsla(0,0%,100%,.22)]">
              No airports match &ldquo;{search}&rdquo;
            </div>
          ) : (
            <div className="columns-3 gap-0">
              {filteredRegions.map((region) => (
                <div key={region.name} className="mb-1 break-inside-avoid">
                  <div className={`px-1.5 pb-[3px] pt-1.5 text-[8px] font-semibold uppercase tracking-[0.1em] text-[hsla(0,0%,100%,.18)] ${mono}`}>
                    {region.name}
                  </div>
                  {region.airports.map((a) => {
                    const isSel = value === a.code;
                    return (
                      <button
                        key={a.code}
                        onClick={() => handleSelect(a.code)}
                        className={`flex w-full items-center gap-1.5 rounded px-1.5 py-[3px] text-left transition-colors ${
                          isSel ? "bg-emerald-500/10" : "hover:bg-[hsla(0,0%,100%,.04)]"
                        }`}
                      >
                        <span className={`w-[28px] text-[10px] font-bold ${mono} ${isSel ? "text-emerald-400" : "text-[hsla(0,0%,100%,.4)]"}`}>
                          {a.code}
                        </span>
                        <span className={`flex-1 truncate text-[11px] ${isSel ? "text-emerald-300/80" : "text-[hsla(0,0%,100%,.45)]"}`}>
                          {a.name}
                        </span>
                        {isSel && <Check className="size-2.5 shrink-0 text-emerald-400" />}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
