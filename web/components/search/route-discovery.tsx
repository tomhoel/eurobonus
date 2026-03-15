"use client";

import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import { motion, AnimatePresence } from "framer-motion";
import { Plane, Globe, TrendingUp, Loader2, X, ChevronRight, Map as MapIcon } from "lucide-react";
import { findAirport } from "@/lib/route-map";

// Dynamic import for the 3D globe (needs WebGL, no SSR)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const GlobeView = dynamic<any>(
  () => import("./globe-view").then((m) => m.GlobeView),
  { ssr: false, loading: () => <div className="flex h-[400px] items-center justify-center"><Loader2 className="size-5 animate-spin text-emerald-400/30" /></div> },
);

const mono = "font-[family-name:var(--font-geist-mono)]";

interface DestSummary {
  code: string;
  city: string;
  country: string;
  lat: number;
  lng: number;
  economySeats: number;
  premiumSeats: number;
  businessSeats: number;
  totalSeats: number;
  datesWithSeats: number;
  totalDates: number;
  nextAvailableDate: string | null;
}

interface RouteDiscoveryProps {
  origin: string;
  onSelectDestination: (code: string) => void;
  onClose: () => void;
}

// Group destinations into regions by country
const COUNTRY_TO_REGION: Record<string, string> = {
  Norway: "Scandinavia", Danmark: "Scandinavia", Denmark: "Scandinavia", Sweden: "Scandinavia", Sverige: "Scandinavia",
  Finland: "Scandinavia", Iceland: "Scandinavia", Island: "Scandinavia",
  "United Kingdom": "UK & Ireland", Storbritannia: "UK & Ireland", Ireland: "UK & Ireland", Irland: "UK & Ireland",
  Spain: "Southern Europe", Spania: "Southern Europe", Italy: "Southern Europe", Italia: "Southern Europe",
  Greece: "Southern Europe", Hellas: "Southern Europe", Portugal: "Southern Europe",
  Croatia: "Southern Europe", Kroatia: "Southern Europe", France: "Southern Europe", Frankrike: "Southern Europe",
  Turkey: "Southern Europe", Tyrkia: "Southern Europe", Cyprus: "Southern Europe", Kypros: "Southern Europe",
  Morocco: "Southern Europe", Marokko: "Southern Europe",
  Germany: "Central Europe", Tyskland: "Central Europe", Netherlands: "Central Europe", Nederland: "Central Europe",
  Belgium: "Central Europe", Belgia: "Central Europe", Switzerland: "Central Europe", Sveits: "Central Europe",
  Austria: "Central Europe", Østerrike: "Central Europe", Poland: "Central Europe", Polen: "Central Europe",
  "Czech Republic": "Central Europe", Tsjekkia: "Central Europe", Hungary: "Central Europe", Ungarn: "Central Europe",
  Estonia: "Baltics", Estland: "Baltics", Latvia: "Baltics", Litauen: "Baltics", Lithuania: "Baltics",
  Thailand: "Asia", Japan: "Asia", Singapore: "Asia", China: "Asia", Kina: "Asia",
  "Hong Kong": "Asia", Vietnam: "Asia", "South Korea": "Asia", "Sør-Korea": "Asia", India: "Asia",
  USA: "Americas", Canada: "Americas", Kanada: "Americas",
  "South Africa": "Africa", "Sør-Afrika": "Africa", Kenya: "Africa",
};

function getRegion(country: string): string {
  return COUNTRY_TO_REGION[country] ?? "Other";
}

export function RouteDiscovery({ origin, onSelectDestination, onClose }: RouteDiscoveryProps) {
  const [destinations, setDestinations] = useState<DestSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"list" | "globe">("list");

  const originAirport = findAirport(origin);

  useEffect(() => {
    if (!origin) return;
    setLoading(true);
    fetch(`/api/search/destinations?origin=${origin}`)
      .then((r) => r.json())
      .then((data) => {
        const dests = (data.destinations ?? []).map((d: DestSummary) => ({
          ...d,
          // Enrich country from local route-map if API returns Norwegian names
          country: d.country || findAirport(d.code)?.country || "",
        }));
        setDestinations(dests);
      })
      .catch(() => setDestinations([]))
      .finally(() => setLoading(false));
  }, [origin]);

  // Group by region
  const grouped = useMemo(() => {
    const map = new Map<string, DestSummary[]>();
    for (const d of destinations) {
      const region = getRegion(d.country || d.city);
      const list = map.get(region) ?? [];
      list.push(d);
      map.set(region, list);
    }
    // Sort regions
    const order = ["Scandinavia", "UK & Ireland", "Southern Europe", "Central Europe", "Baltics", "Asia", "Americas", "Africa", "Other"];
    return order
      .filter((r) => map.has(r))
      .map((r) => ({ region: r, destinations: map.get(r)! }));
  }, [destinations]);

  // Filter by region
  const displayed = filter
    ? grouped.filter((g) => g.region === filter)
    : grouped;

  // Stats
  const totalDests = destinations.length;
  const withBusiness = destinations.filter((d) => d.businessSeats > 0).length;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
        className="overflow-hidden"
      >
        <div className="rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.015)]">
          {/* Header */}
          <div className="flex items-center gap-3 border-b border-[hsla(0,0%,100%,.06)] px-5 py-3">
            <div className="flex size-7 items-center justify-center rounded-full bg-emerald-500/10">
              <Globe className="size-3.5 text-emerald-400" />
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span className="text-[13px] font-semibold text-[hsla(0,0%,100%,.7)]">
                  Award routes from
                </span>
                <span className={`text-[14px] font-bold text-emerald-400 ${mono}`}>
                  {origin}
                </span>
                <span className="text-[13px] text-[hsla(0,0%,100%,.3)]">
                  {originAirport?.name}
                </span>
              </div>
              {!loading && (
                <div className={`mt-0.5 text-[10px] text-[hsla(0,0%,100%,.2)] ${mono}`}>
                  {totalDests} destinations with availability · {withBusiness} with business class
                </div>
              )}
            </div>
            {/* View toggle */}
            {!loading && (
              <div className="flex rounded-md border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)]">
                <button
                  onClick={() => setViewMode("list")}
                  className={`rounded-l-md px-2.5 py-1.5 text-[10px] font-medium transition-colors ${mono} ${
                    viewMode === "list" ? "bg-emerald-500/15 text-emerald-400" : "text-[hsla(0,0%,100%,.2)] hover:text-[hsla(0,0%,100%,.4)]"
                  }`}
                >
                  List
                </button>
                <button
                  onClick={() => setViewMode("globe")}
                  className={`flex items-center gap-1 rounded-r-md px-2.5 py-1.5 text-[10px] font-medium transition-colors ${mono} ${
                    viewMode === "globe" ? "bg-emerald-500/15 text-emerald-400" : "text-[hsla(0,0%,100%,.2)] hover:text-[hsla(0,0%,100%,.4)]"
                  }`}
                >
                  <MapIcon className="size-3" />
                  Globe
                </button>
              </div>
            )}
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-[hsla(0,0%,100%,.2)] transition-colors hover:bg-[hsla(0,0%,100%,.05)] hover:text-[hsla(0,0%,100%,.5)]"
            >
              <X className="size-4" />
            </button>
          </div>

          {/* Globe view */}
          {viewMode === "globe" && !loading && (
            <GlobeView
              origin={origin}
              destinations={destinations.map((d) => ({
                code: d.code,
                city: d.city,
                lat: d.lat,
                lng: d.lng,
                totalSeats: d.totalSeats,
                hasBusiness: d.businessSeats > 0,
              }))}
              onSelectDestination={onSelectDestination}
            />
          )}

          {/* Region filter tabs (list view only) */}
          {viewMode === "list" && !loading && (
            <div className="flex gap-1 overflow-x-auto border-b border-[hsla(0,0%,100%,.04)] px-5 py-2">
              <button
                onClick={() => setFilter(null)}
                className={`shrink-0 rounded-md px-2.5 py-1 text-[10px] font-medium transition-colors ${mono} ${
                  filter === null
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "text-[hsla(0,0%,100%,.25)] hover:text-[hsla(0,0%,100%,.45)]"
                }`}
              >
                All ({totalDests})
              </button>
              {grouped.map(({ region, destinations: dests }) => (
                <button
                  key={region}
                  onClick={() => setFilter(filter === region ? null : region)}
                  className={`shrink-0 rounded-md px-2.5 py-1 text-[10px] font-medium transition-colors ${mono} ${
                    filter === region
                      ? "bg-emerald-500/15 text-emerald-400"
                      : "text-[hsla(0,0%,100%,.25)] hover:text-[hsla(0,0%,100%,.45)]"
                  }`}
                >
                  {region} ({dests.length})
                </button>
              ))}
            </div>
          )}

          {/* Content (list view) */}
          <div className={`max-h-[420px] overflow-y-auto px-5 py-3 ${viewMode === "globe" && !loading ? "hidden" : ""}`}>
            {loading ? (
              <div className="flex items-center justify-center gap-2 py-12">
                <Loader2 className="size-4 animate-spin text-emerald-400/50" />
                <span className={`text-[12px] text-[hsla(0,0%,100%,.25)] ${mono}`}>
                  Scanning SAS routes...
                </span>
              </div>
            ) : (
              <div className="space-y-4">
                {displayed.map(({ region, destinations: dests }, rIdx) => (
                  <motion.div
                    key={region}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: rIdx * 0.03, duration: 0.2 }}
                  >
                    <div className={`mb-2 text-[9px] font-semibold uppercase tracking-[0.1em] text-[hsla(0,0%,100%,.18)] ${mono}`}>
                      {region}
                    </div>
                    <div className="grid gap-1 sm:grid-cols-2 lg:grid-cols-3">
                      {dests.map((dest, dIdx) => (
                        <motion.button
                          key={dest.code}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: rIdx * 0.03 + dIdx * 0.01 }}
                          onClick={() => onSelectDestination(dest.code)}
                          className="group flex items-center gap-3 rounded-lg px-3 py-2 text-left transition-all hover:bg-[hsla(0,0%,100%,.04)]"
                        >
                          {/* Route indicator */}
                          <div className="flex shrink-0 flex-col items-center gap-[2px]">
                            <div className="flex gap-[2px]">
                              {dest.economySeats > 0 && <div className="size-[5px] rounded-full bg-emerald-400/60" />}
                              {dest.premiumSeats > 0 && <div className="size-[5px] rounded-full bg-blue-400/60" />}
                              {dest.businessSeats > 0 && <div className="size-[5px] rounded-full bg-amber-400/60" />}
                            </div>
                          </div>

                          {/* Destination info */}
                          <div className="min-w-0 flex-1">
                            <div className="flex items-baseline gap-1.5">
                              <span className={`text-[11px] font-bold text-[hsla(0,0%,100%,.5)] group-hover:text-emerald-400 ${mono}`}>
                                {dest.code}
                              </span>
                              <span className="truncate text-[11px] text-[hsla(0,0%,100%,.4)]">
                                {dest.city}
                              </span>
                            </div>
                            <div className={`mt-[1px] text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>
                              {dest.datesWithSeats} date{dest.datesWithSeats !== 1 ? "s" : ""}
                              {dest.businessSeats > 0 && (
                                <span className="text-amber-400/40"> · {dest.businessSeats} business</span>
                              )}
                            </div>
                          </div>

                          {/* Arrow */}
                          <ChevronRight className="size-3 shrink-0 text-[hsla(0,0%,100%,.08)] transition-all group-hover:translate-x-0.5 group-hover:text-emerald-400/50" />
                        </motion.button>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
