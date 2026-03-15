"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Globe, Loader2, X } from "lucide-react";
import { findAirport } from "@/lib/route-map";

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
  onHoverDest?: (code: string | null) => void;
  onDestsLoaded?: (dests: { code: string; city: string; lat: number; lng: number; totalSeats: number; hasBusiness: boolean }[]) => void;
}

// ── Destination images (Unsplash CDN — permanent URLs) ──
const DEST_IMAGES: Record<string, string> = {
  // Asia & Oceania
  BKK: "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=400&h=300&fit=crop&auto=format&q=75",
  NRT: "https://images.unsplash.com/photo-1540959733332-eab84b3681b5?w=400&h=300&fit=crop&auto=format&q=75",
  HND: "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=400&h=300&fit=crop&auto=format&q=75",
  KIX: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?w=400&h=300&fit=crop&auto=format&q=75",
  SIN: "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=400&h=300&fit=crop&auto=format&q=75",
  HKG: "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=400&h=300&fit=crop&auto=format&q=75",
  ICN: "https://images.unsplash.com/photo-1517154421773-0529f29ea451?w=400&h=300&fit=crop&auto=format&q=75",
  PEK: "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400&h=300&fit=crop&auto=format&q=75",
  PVG: "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=400&h=300&fit=crop&auto=format&q=75",
  DEL: "https://images.unsplash.com/photo-1524492412937-b28074a5d7da?w=400&h=300&fit=crop&auto=format&q=75",
  BOM: "https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?w=400&h=300&fit=crop&auto=format&q=75",
  SGN: "https://images.unsplash.com/photo-1583417319070-4a69db38a482?w=400&h=300&fit=crop&auto=format&q=75",
  HAN: "https://images.unsplash.com/photo-1509030450996-dd1a26dda07a?w=400&h=300&fit=crop&auto=format&q=75",
  // Southern Europe
  CDG: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=400&h=300&fit=crop&auto=format&q=75",
  BCN: "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=400&h=300&fit=crop&auto=format&q=75",
  MAD: "https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=400&h=300&fit=crop&auto=format&q=75",
  AGP: "https://images.unsplash.com/photo-1509840841025-9088ba78a826?w=400&h=300&fit=crop&auto=format&q=75",
  ALC: "https://images.unsplash.com/photo-1504019347908-b45f9b0b8dd5?w=400&h=300&fit=crop&auto=format&q=75",
  PMI: "https://images.unsplash.com/photo-1558642452-9d2a7deb7f62?w=400&h=300&fit=crop&auto=format&q=75",
  FCO: "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=400&h=300&fit=crop&auto=format&q=75",
  MXP: "https://images.unsplash.com/photo-1513581166391-887a96ddeafd?w=400&h=300&fit=crop&auto=format&q=75",
  NAP: "https://images.unsplash.com/photo-1516483638261-f4dbaf036963?w=400&h=300&fit=crop&auto=format&q=75",
  VCE: "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=400&h=300&fit=crop&auto=format&q=75",
  ATH: "https://images.unsplash.com/photo-1555993539-1732b0258235?w=400&h=300&fit=crop&auto=format&q=75",
  CHQ: "https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?w=400&h=300&fit=crop&auto=format&q=75",
  RHO: "https://images.unsplash.com/photo-1586861635167-e5223aadc9fe?w=400&h=300&fit=crop&auto=format&q=75",
  LIS: "https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400&h=300&fit=crop&auto=format&q=75",
  FAO: "https://images.unsplash.com/photo-1555881400-74d7acaacd8b?w=400&h=300&fit=crop&auto=format&q=75",
  IST: "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=400&h=300&fit=crop&auto=format&q=75",
  AYT: "https://images.unsplash.com/photo-1589561454226-796a8aa89b05?w=400&h=300&fit=crop&auto=format&q=75",
  SPU: "https://images.unsplash.com/photo-1555990538-18a37b3c65b5?w=400&h=300&fit=crop&auto=format&q=75",
  DBV: "https://images.unsplash.com/photo-1555990538-18a37b3c65b5?w=400&h=300&fit=crop&auto=format&q=75",
  NIC: "https://images.unsplash.com/photo-1491147334573-44cbb4602074?w=400&h=300&fit=crop&auto=format&q=75",
  TFS: "https://images.unsplash.com/photo-1540541338287-41700207dee6?w=400&h=300&fit=crop&auto=format&q=75",
  LPA: "https://images.unsplash.com/photo-1540541338287-41700207dee6?w=400&h=300&fit=crop&auto=format&q=75",
  // Central Europe
  FRA: "https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=400&h=300&fit=crop&auto=format&q=75",
  MUC: "https://images.unsplash.com/photo-1595867818082-083862f3d630?w=400&h=300&fit=crop&auto=format&q=75",
  AMS: "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=400&h=300&fit=crop&auto=format&q=75",
  BRU: "https://images.unsplash.com/photo-1559113202-c916b8e44373?w=400&h=300&fit=crop&auto=format&q=75",
  ZRH: "https://images.unsplash.com/photo-1515488764276-beab7607c1e6?w=400&h=300&fit=crop&auto=format&q=75",
  VIE: "https://images.unsplash.com/photo-1516550893923-42d28e5677af?w=400&h=300&fit=crop&auto=format&q=75",
  PRG: "https://images.unsplash.com/photo-1519677100203-a0e668c92439?w=400&h=300&fit=crop&auto=format&q=75",
  WAW: "https://images.unsplash.com/photo-1519197924294-4ba991a11128?w=400&h=300&fit=crop&auto=format&q=75",
  GDN: "https://images.unsplash.com/photo-1587825140708-dfaf18c4c5bd?w=400&h=300&fit=crop&auto=format&q=75",
  BUD: "https://images.unsplash.com/photo-1551867633-194f125bddfa?w=400&h=300&fit=crop&auto=format&q=75",
  // UK & Ireland
  LHR: "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=400&h=300&fit=crop&auto=format&q=75",
  MAN: "https://images.unsplash.com/photo-1515586838455-8f8f940d6853?w=400&h=300&fit=crop&auto=format&q=75",
  EDI: "https://images.unsplash.com/photo-1506377585622-bedcbb027afc?w=400&h=300&fit=crop&auto=format&q=75",
  DUB: "https://images.unsplash.com/photo-1549918864-48ac978761a4?w=400&h=300&fit=crop&auto=format&q=75",
  // Scandinavia
  OSL: "https://images.unsplash.com/photo-1433757741270-94a3bcadc2f0?w=400&h=300&fit=crop&auto=format&q=75",
  CPH: "https://images.unsplash.com/photo-1513622304351-e8f8b1d04da7?w=400&h=300&fit=crop&auto=format&q=75",
  ARN: "https://images.unsplash.com/photo-1509356843971-0ef9b9df16a8?w=400&h=300&fit=crop&auto=format&q=75",
  GOT: "https://images.unsplash.com/photo-1572883454540-3094e1d1dcbe?w=400&h=300&fit=crop&auto=format&q=75",
  BGO: "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=400&h=300&fit=crop&auto=format&q=75",
  TRD: "https://images.unsplash.com/photo-1520769669658-f07657f5a307?w=400&h=300&fit=crop&auto=format&q=75",
  SVG: "https://images.unsplash.com/photo-1507272931001-fc06c17e4f43?w=400&h=300&fit=crop&auto=format&q=75",
  HEL: "https://images.unsplash.com/photo-1538332576228-eb5b4c4de6f5?w=400&h=300&fit=crop&auto=format&q=75",
  KEF: "https://images.unsplash.com/photo-1504893524553-b855bce32c67?w=400&h=300&fit=crop&auto=format&q=75",
  // Baltics
  TLL: "https://images.unsplash.com/photo-1565008576549-57569a49371d?w=400&h=300&fit=crop&auto=format&q=75",
  RIX: "https://images.unsplash.com/photo-1587974928442-77dc3e0748b1?w=400&h=300&fit=crop&auto=format&q=75",
  // Americas
  JFK: "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400&h=300&fit=crop&auto=format&q=75",
  EWR: "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400&h=300&fit=crop&auto=format&q=75",
  LAX: "https://images.unsplash.com/photo-1534190760961-74e8c1c5c3da?w=400&h=300&fit=crop&auto=format&q=75",
  SFO: "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=400&h=300&fit=crop&auto=format&q=75",
  ORD: "https://images.unsplash.com/photo-1494522855154-9297ac14b55f?w=400&h=300&fit=crop&auto=format&q=75",
  MIA: "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=400&h=300&fit=crop&auto=format&q=75",
  BOS: "https://images.unsplash.com/photo-1501979376754-2ff867a4f659?w=400&h=300&fit=crop&auto=format&q=75",
  IAD: "https://images.unsplash.com/photo-1501466044931-62695aada8e9?w=400&h=300&fit=crop&auto=format&q=75",
  YYZ: "https://images.unsplash.com/photo-1517090504332-af41c6c55d87?w=400&h=300&fit=crop&auto=format&q=75",
  // Africa
  CPT: "https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=400&h=300&fit=crop&auto=format&q=75",
  NBO: "https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?w=400&h=300&fit=crop&auto=format&q=75",
};

// Generate a unique gradient for destinations without curated photos
function getDestGradient(code: string, region: string): string {
  const hash = code.split("").reduce((h, c) => Math.imul(31, h) + c.charCodeAt(0), 0);
  const hue = Math.abs(hash) % 360;
  const regionHueShift: Record<string, number> = {
    Scandinavia: 200, "UK & Ireland": 220, "Southern Europe": 30,
    "Central Europe": 250, Baltics: 210, Asia: 15, Americas: 230, Africa: 35, Other: 270,
  };
  const baseHue = (hue + (regionHueShift[region] ?? 0)) % 360;
  return `linear-gradient(135deg, hsl(${baseHue}, 45%, 14%) 0%, hsl(${(baseHue + 25) % 360}, 50%, 18%) 50%, hsl(${(baseHue + 50) % 360}, 40%, 12%) 100%)`;
}

// Group destinations into regions
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

// ── Region section with grid ──
function RegionSection({ children, label, count }: { children: React.ReactNode; label: string; count: number }) {
  return (
    <div>
      <div className="mb-2.5 flex items-center gap-2 px-5">
        <span className={`text-[10px] font-semibold uppercase tracking-[0.12em] text-[hsla(0,0%,100%,.28)] ${mono}`}>
          {label}
        </span>
        <div className="h-px flex-1 bg-[hsla(0,0%,100%,.04)]" />
        <span className={`text-[10px] text-[hsla(0,0%,100%,.15)] ${mono}`}>{count}</span>
      </div>
      <div className="grid grid-cols-3 gap-2.5 px-5 sm:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
        {children}
      </div>
    </div>
  );
}

// ── Photo destination card ──
function DestCard({
  dest,
  origin,
  region,
  onSelect,
  onHover,
  onLeave,
  index,
}: {
  dest: DestSummary;
  origin: string;
  region: string;
  onSelect: () => void;
  onHover: () => void;
  onLeave: () => void;
  index: number;
}) {
  const [imgError, setImgError] = useState(false);
  const imgUrl = DEST_IMAGES[dest.code];
  const showImage = imgUrl && !imgError;

  return (
    <motion.button
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      onClick={onSelect}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      className="group relative overflow-hidden rounded-xl text-left transition-all duration-300 hover:scale-[1.03] hover:shadow-[0_8px_30px_-6px_rgba(0,0,0,.6)] focus:outline-none focus-visible:ring-1 focus-visible:ring-emerald-400/50"
    >
      <div className="relative aspect-[3/4] w-full">
        {/* Background — photo or gradient */}
        {showImage ? (
          <img
            src={imgUrl}
            alt={dest.city}
            loading="lazy"
            onError={() => setImgError(true)}
            className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
        ) : (
          <div className="absolute inset-0" style={{ background: getDestGradient(dest.code, region) }}>
            {/* Decorative light blobs on gradient cards */}
            <div className="absolute inset-0 opacity-30" style={{
              backgroundImage: "radial-gradient(circle at 25% 20%, hsla(0,0%,100%,.12) 0%, transparent 50%), radial-gradient(circle at 75% 75%, hsla(0,0%,100%,.06) 0%, transparent 50%)"
            }} />
            {/* Large city initial watermark */}
            <div className={`absolute right-3 top-2 text-[48px] font-bold leading-none text-white/[0.04] ${mono}`}>
              {dest.city.charAt(0)}
            </div>
          </div>
        )}

        {/* Dark overlay for readability */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-black/10 transition-opacity group-hover:from-black/80 group-hover:via-black/20" />

        {/* Top: cabin availability pills */}
        <div className="absolute left-2.5 top-2.5 flex gap-[4px]">
          {dest.economySeats > 0 && (
            <div className="flex items-center gap-[3px] rounded-full bg-black/40 px-[6px] py-[2px] backdrop-blur-sm">
              <div className="size-[5px] rounded-full bg-emerald-400" />
              <span className={`text-[8px] font-medium text-emerald-300 ${mono}`}>{dest.economySeats}</span>
            </div>
          )}
          {dest.premiumSeats > 0 && (
            <div className="flex items-center gap-[3px] rounded-full bg-black/40 px-[6px] py-[2px] backdrop-blur-sm">
              <div className="size-[5px] rounded-full bg-blue-400" />
              <span className={`text-[8px] font-medium text-blue-300 ${mono}`}>{dest.premiumSeats}</span>
            </div>
          )}
          {dest.businessSeats > 0 && (
            <div className="flex items-center gap-[3px] rounded-full bg-black/40 px-[6px] py-[2px] backdrop-blur-sm">
              <div className="size-[5px] rounded-full bg-amber-400" />
              <span className={`text-[8px] font-medium text-amber-300 ${mono}`}>{dest.businessSeats}</span>
            </div>
          )}
        </div>

        {/* Top-right: route badge */}
        <div className="absolute right-2.5 top-2.5">
          <div className={`rounded-[4px] bg-black/40 px-[6px] py-[2px] text-[8px] text-[hsla(0,0%,100%,.5)] backdrop-blur-sm ${mono}`}>
            {origin} → {dest.code}
          </div>
        </div>

        {/* Bottom: destination info */}
        <div className="absolute inset-x-0 bottom-0 p-3">
          <div className={`text-[22px] font-bold leading-none tracking-[-0.03em] text-white transition-colors group-hover:text-emerald-300 ${mono}`}>
            {dest.code}
          </div>
          <div className="mt-1">
            <div className="text-[12px] font-medium leading-tight text-[hsla(0,0%,100%,.85)]">
              {dest.city}
            </div>
            {dest.country && (
              <div className="text-[10px] text-[hsla(0,0%,100%,.35)]">{dest.country}</div>
            )}
          </div>

          {/* Availability bar */}
          <div className="mt-2">
            <div className="mb-[3px] flex items-center justify-between">
              <span className={`text-[8px] text-[hsla(0,0%,100%,.3)] ${mono}`}>
                {dest.datesWithSeats} of {dest.totalDates} dates
              </span>
            </div>
            <div className="h-[2px] overflow-hidden rounded-full bg-[hsla(0,0%,100%,.1)]">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${dest.totalDates > 0 ? Math.round((dest.datesWithSeats / dest.totalDates) * 100) : 0}%`,
                  background: "linear-gradient(90deg, #10b981, #34d399)",
                }}
              />
            </div>
          </div>
        </div>

        {/* Hover border */}
        <div className="pointer-events-none absolute inset-0 rounded-xl border border-transparent transition-colors group-hover:border-emerald-400/20" />
      </div>
    </motion.button>
  );
}

export function RouteDiscovery({ origin, onSelectDestination, onClose, onHoverDest, onDestsLoaded }: RouteDiscoveryProps) {
  const [destinations, setDestinations] = useState<DestSummary[]>([]);
  const [loading, setLoading] = useState(true);

  const originAirport = findAirport(origin);

  useEffect(() => {
    if (!origin) return;
    setLoading(true);
    fetch(`/api/search/destinations?origin=${origin}`)
      .then((r) => r.json())
      .then((data) => {
        const dests = (data.destinations ?? []).map((d: DestSummary) => ({
          ...d,
          country: d.country || findAirport(d.code)?.country || "",
        }));
        setDestinations(dests);
        // Expose destinations to parent for the Globe
        onDestsLoaded?.(dests.map((d: DestSummary) => ({
          code: d.code,
          city: d.city,
          lat: d.lat,
          lng: d.lng,
          totalSeats: d.totalSeats,
          hasBusiness: d.businessSeats > 0,
        })));
      })
      .catch(() => setDestinations([]))
      .finally(() => setLoading(false));
  }, [origin]);

  // Group by region — all regions shown as carousels
  const grouped = useMemo(() => {
    const map = new Map<string, DestSummary[]>();
    for (const d of destinations) {
      const region = getRegion(d.country || d.city);
      const list = map.get(region) ?? [];
      list.push(d);
      map.set(region, list);
    }
    const order = ["Scandinavia", "UK & Ireland", "Southern Europe", "Central Europe", "Baltics", "Asia", "Americas", "Africa", "Other"];
    return order
      .filter((r) => map.has(r))
      .map((r) => ({ region: r, destinations: map.get(r)! }));
  }, [destinations]);

  const totalDests = destinations.length;
  const withBusiness = destinations.filter((d) => d.businessSeats > 0).length;
  const totalSeats = destinations.reduce((s, d) => s + d.totalSeats, 0);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
        className="overflow-hidden"
      >
        <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] shadow-[0_20px_60px_-15px_rgba(0,0,0,.6)]">
          {/* Terminal chrome */}
          <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.025)] px-5 py-[10px]">
            <div className="flex gap-[6px]">
              {[0, 1, 2].map((d) => (
                <div key={d} className="h-[12px] w-[12px] rounded-full bg-[hsla(0,0%,100%,.07)]" />
              ))}
            </div>
            <div className="ml-3 flex items-center gap-2">
              <Globe className="size-3 text-emerald-400/50" />
              <span className={`text-[12px] text-[hsla(0,0%,100%,.22)] ${mono}`}>
                route discovery — {origin}
              </span>
              {originAirport?.name && (
                <span className="text-[11px] text-[hsla(0,0%,100%,.12)]">{originAirport.name}</span>
              )}
            </div>
            {!loading && (
              <div className="ml-auto flex items-center gap-[6px]">
                <span className="h-[6px] w-[6px] rounded-full bg-emerald-500" />
                <span className={`text-[11px] text-[hsla(0,0%,100%,.18)] ${mono}`}>{totalDests} live</span>
              </div>
            )}
            <button onClick={onClose} className="ml-3 rounded-md p-1 text-[hsla(0,0%,100%,.15)] transition-colors hover:bg-[hsla(0,0%,100%,.05)] hover:text-[hsla(0,0%,100%,.4)]">
              <X className="size-3.5" />
            </button>
          </div>

          {/* Stats strip */}
          {!loading && (
            <div className="grid grid-cols-3 border-b border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)]">
              {[
                { value: totalDests.toString(), label: "destinations" },
                { value: withBusiness.toString(), label: "with business" },
                { value: totalSeats.toLocaleString(), label: "total seats" },
              ].map((stat, i) => (
                <div
                  key={stat.label}
                  className={`flex items-center justify-center gap-2 py-2.5 ${i > 0 ? "border-l border-[hsla(0,0%,100%,.06)]" : ""}`}
                >
                  <span className={`text-[14px] font-bold tracking-[-0.02em] text-[hsla(0,0%,100%,.6)] ${mono}`}>{stat.value}</span>
                  <span className="text-[10px] text-[hsla(0,0%,100%,.2)]">{stat.label}</span>
                </div>
              ))}
            </div>
          )}

          {/* Carousels */}
          {loading ? (
            <div className="flex flex-col items-center justify-center gap-3 bg-[#040a18] py-16">
              <div className="relative">
                <div className="absolute inset-0 animate-ping rounded-full bg-emerald-400/10" />
                <Loader2 className="relative size-5 animate-spin text-emerald-400/60" />
              </div>
              <span className={`text-[12px] text-[hsla(0,0%,100%,.22)] ${mono}`}>Scanning SAS award routes...</span>
            </div>
          ) : (
            <div className="max-h-[560px] space-y-5 overflow-y-auto bg-[#040a18] py-4 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-[hsla(0,0%,100%,.06)]">
              {grouped.map(({ region, destinations: dests }, rIdx) => (
                <motion.div
                  key={region}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: rIdx * 0.06, duration: 0.3 }}
                >
                  <RegionSection label={region} count={dests.length}>
                    {dests.map((dest, dIdx) => (
                      <DestCard
                        key={dest.code}
                        dest={dest}
                        origin={origin}
                        region={region}
                        onSelect={() => onSelectDestination(dest.code)}
                        onHover={() => onHoverDest?.(dest.code)}
                        onLeave={() => onHoverDest?.(null)}
                        index={dIdx}
                      />
                    ))}
                  </RegionSection>
                </motion.div>
              ))}
            </div>
          )}

          {/* Footer */}
          {!loading && (
            <div className={`flex items-center justify-between border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)] px-5 py-[8px] text-[10px] text-[hsla(0,0%,100%,.12)] ${mono}`}>
              <span>EuroBonus award routes · click to search</span>
              <span>hellasus.no</span>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
