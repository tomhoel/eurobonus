"use client";

import { useEffect, useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import ThreeGlobe from "three-globe";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { findAirport } from "@/lib/route-map";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface GlobeArc {
  startLat: number;
  startLng: number;
  endLat: number;
  endLng: number;
  color: string;
  destCode: string;
  highlighted: boolean;
  dimmed: boolean;
  glow: boolean;
}

interface GlobePoint {
  lat: number;
  lng: number;
  size: number;
  color: string;
  label: string;
  code: string;
  highlighted: boolean;
  dimmed: boolean;
}

interface GlobeRing {
  lat: number;
  lng: number;
  maxR: number;
  propagationSpeed: number;
  repeatPeriod: number;
  color: string;
}

interface GlobeLabel {
  lat: number;
  lng: number;
  text: string;
  size: number;
  color: string;
}

interface DestInfo {
  code: string;
  city: string;
  lat: number;
  lng: number;
  totalSeats: number;
  hasBusiness: boolean;
}

interface GlobeViewProps {
  origin: string;
  destinations: DestInfo[];
  onSelectDestination?: (code: string) => void;
  compact?: boolean;
  highlightedDest?: string | null;
}

const AIRPORT_COORDS: Record<string, [number, number]> = {
  OSL: [60.19, 11.10], CPH: [55.62, 12.66], ARN: [59.65, 17.94],
  GOT: [57.67, 12.29], BGO: [60.29, 5.22], TRD: [63.46, 10.92],
  SVG: [58.88, 5.64], HEL: [60.32, 24.96], KEF: [63.99, -22.61],
  LHR: [51.47, -0.46], CDG: [49.01, 2.55], AMS: [52.31, 4.76],
  FRA: [50.03, 8.57], MUC: [48.35, 11.79], ZRH: [47.46, 8.55],
  BRU: [50.90, 4.48], BCN: [41.30, 2.08], MAD: [40.47, -3.57],
  AGP: [36.67, -4.50], FCO: [41.80, 12.25], ATH: [37.94, 23.94],
  LIS: [38.77, -9.13], IST: [41.28, 28.75], BKK: [13.68, 100.75],
  NRT: [35.76, 140.39], HND: [35.55, 139.78], SIN: [1.35, 103.99],
  PEK: [40.08, 116.58], HKG: [22.31, 113.91], ICN: [37.46, 126.44],
  JFK: [40.64, -73.78], LAX: [33.94, -118.41], SFO: [37.62, -122.38],
  ORD: [41.97, -87.91], MIA: [25.79, -80.29], EWR: [40.69, -74.17],
  IAD: [38.94, -77.46], BOS: [42.36, -71.01], YYZ: [43.68, -79.63],
  CPT: [-33.97, 18.60], NBO: [-1.32, 36.93], DEL: [28.56, 77.10],
  BOM: [19.09, 72.87], SGN: [10.82, 106.65], HAN: [21.22, 105.81],
  PMI: [39.55, 2.74], TFS: [28.04, -16.57], LPA: [27.93, -15.39],
  ALC: [38.28, -0.56], MXP: [45.63, 8.72], NAP: [40.89, 14.29],
  VCE: [45.51, 12.35], CHQ: [35.53, 24.15], RHO: [36.41, 28.09],
  FAO: [37.01, -7.97], SPU: [43.54, 16.30], DBV: [42.56, 18.27],
  NIC: [43.66, 7.22], VIE: [48.11, 16.57], PRG: [50.10, 14.26],
  WAW: [52.17, 20.97], GDN: [54.38, 18.47], BUD: [47.44, 19.26],
  TLL: [59.42, 24.83], RIX: [56.92, 23.97], AYT: [36.90, 30.80],
  DUB: [53.43, -6.27], EDI: [55.95, -3.37], MAN: [53.35, -2.28],
  KIX: [34.43, 135.24], PVG: [31.14, 121.81],
};

// Haversine distance in km (for flight distance display)
function haversineKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6371;
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLng = (lng2 - lng1) * (Math.PI / 180);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function GlobeObject({
  arcs, points, rings, labels, focusLng, originLng, hasHighlight,
}: {
  arcs: GlobeArc[]; points: GlobePoint[]; rings: GlobeRing[]; labels: GlobeLabel[];
  focusLng: number | null; originLng: number; hasHighlight: boolean;
}) {
  const globeRef = useRef<ThreeGlobe | null>(null);
  const groupRef = useRef<THREE.Group>(null);

  useEffect(() => {
    const globe = new ThreeGlobe({ animateIn: true })
      .showAtmosphere(true)
      .atmosphereColor("#10b981")
      .atmosphereAltitude(0.2)
      // ── Arcs ──
      .arcsData(arcs)
      .arcColor((d: unknown) => {
        const a = d as GlobeArc;
        if (a.glow) return a.highlighted ? `rgba(16, 185, 129, 0.12)` : "transparent";
        if (a.highlighted) return a.color;
        if (a.dimmed) return "rgba(255,255,255,0.03)";
        return a.color;
      })
      .arcAltitude((d: unknown) => {
        const a = d as GlobeArc;
        if (a.glow) return a.highlighted ? 0.24 : 0.15;
        return a.highlighted ? 0.24 : 0.12;
      })
      .arcStroke((d: unknown) => {
        const a = d as GlobeArc;
        if (a.glow) return a.highlighted ? 5 : 0;
        if (a.highlighted) return 1.8;
        if (a.dimmed) return 0.1;
        return 0.4;
      })
      .arcDashLength((d: unknown) => {
        const a = d as GlobeArc;
        return a.highlighted ? 1.2 : 0.8;
      })
      .arcDashGap((d: unknown) => {
        const a = d as GlobeArc;
        return a.highlighted ? 1 : 4;
      })
      .arcDashAnimateTime((d: unknown) => {
        const a = d as GlobeArc;
        return a.highlighted ? 600 : 2000;
      })
      // ── Points ──
      .pointsData(points)
      .pointColor((d: unknown) => {
        const p = d as GlobePoint;
        if (p.highlighted) return "#ffffff";
        if (p.dimmed) return "rgba(255,255,255,0.05)";
        return p.color;
      })
      .pointsMerge(false)
      .pointAltitude((d: unknown) => {
        const p = d as GlobePoint;
        return p.highlighted ? 0.04 : 0.008;
      })
      .pointRadius((d: unknown) => {
        const p = d as GlobePoint;
        if (p.highlighted) return p.size * 2;
        if (p.dimmed) return p.size * 0.4;
        return p.size;
      })
      // ── Rings (pulsing at origin + highlighted dest) ──
      .ringsData(rings)
      .ringColor((d: unknown) => {
        const r = d as GlobeRing;
        const c = r.color;
        return (t: number) => {
          const opacity = Math.max(0, 1 - t);
          // Parse hex to rgb
          const hex = c.replace("#", "");
          const rv = parseInt(hex.substring(0, 2), 16);
          const gv = parseInt(hex.substring(2, 4), 16);
          const bv = parseInt(hex.substring(4, 6), 16);
          return `rgba(${rv},${gv},${bv},${opacity * 0.6})`;
        };
      })
      .ringMaxRadius("maxR" as unknown as string)
      .ringPropagationSpeed("propagationSpeed" as unknown as string)
      .ringRepeatPeriod("repeatPeriod" as unknown as string)
      // ── Labels (destination name on hover) ──
      .labelsData(labels)
      .labelText("text" as unknown as string)
      .labelSize("size" as unknown as string)
      .labelColor("color" as unknown as string)
      .labelDotRadius(0.3)
      .labelAltitude(0.025)
      .labelResolution(2);

    // Globe material
    const mat = globe.globeMaterial() as THREE.MeshPhongMaterial;
    mat.color = new THREE.Color("#030d1f");
    mat.emissive = new THREE.Color("#071a4a");
    mat.emissiveIntensity = 0.1;
    mat.shininess = 0.7;

    // Country polygons
    fetch("/globe-data.json")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((geo) => {
        globe
          .polygonsData(geo.features)
          .polygonCapColor(() => "rgba(20, 50, 100, 0.35)")
          .polygonSideColor(() => "rgba(15, 35, 70, 0.2)")
          .polygonStrokeColor(() => "rgba(80, 140, 255, 0.12)")
          .polygonAltitude(0.004);
      })
      .catch(() => {
        fetch("/globe-data.json").then((r) => r.json()).then((geo) => {
          globe.hexPolygonsData(geo.features).hexPolygonResolution(3).hexPolygonMargin(0.62).hexPolygonColor(() => "rgba(40, 80, 180, 0.2)");
        }).catch(() => {});
      });

    globeRef.current = globe;
    if (groupRef.current) groupRef.current.add(globe);
    return () => { if (groupRef.current) groupRef.current.remove(globe); };
  }, []);

  // Update all data layers reactively
  useEffect(() => {
    const g = globeRef.current;
    if (!g) return;
    g.arcsData(arcs);
    g.pointsData(points);
    g.ringsData(rings);
    g.labelsData(labels);
  }, [arcs, points, rings, labels]);

  // Animation: rotation + zoom
  useFrame((_, delta) => {
    if (!groupRef.current) return;

    // Smooth zoom: scale up 10% when highlighting a route
    const targetScale = hasHighlight ? 1.1 : 1;
    const s = groupRef.current.scale.x;
    groupRef.current.scale.setScalar(s + (targetScale - s) * Math.min(1, 4 * delta));

    // Rotation
    if (focusLng !== null) {
      const targetY = (originLng - focusLng) * (Math.PI / 180);
      let diff = targetY - groupRef.current.rotation.y;
      while (diff > Math.PI) diff -= 2 * Math.PI;
      while (diff < -Math.PI) diff += 2 * Math.PI;
      groupRef.current.rotation.y += diff * Math.min(1, 4.5 * delta);
    } else {
      groupRef.current.rotation.y += 0.0008;
    }
  });

  return <group ref={groupRef} />;
}

function GlobeScene({
  arcs, points, rings, labels, originCoords, focusLng, hasHighlight,
}: {
  arcs: GlobeArc[]; points: GlobePoint[]; rings: GlobeRing[]; labels: GlobeLabel[];
  originCoords: [number, number]; focusLng: number | null; hasHighlight: boolean;
}) {
  return (
    <>
      <ambientLight intensity={0.5} color="#c7d2fe" />
      <directionalLight position={[-400, 100, 400]} intensity={0.9} color="#ffffff" />
      <pointLight position={[-200, 500, 200]} intensity={0.7} color="#3b82f6" />
      <pointLight position={[300, -100, -200]} intensity={0.3} color="#10b981" />
      <GlobeObject
        arcs={arcs} points={points} rings={rings} labels={labels}
        focusLng={focusLng} originLng={originCoords[1]} hasHighlight={hasHighlight}
      />
      <OrbitControls enablePan={false} enableZoom={false} minDistance={200} maxDistance={350} autoRotate={false} target={[0, 0, 0]} />
    </>
  );
}

export function GlobeView({ origin, destinations, onSelectDestination, compact, highlightedDest }: GlobeViewProps) {
  const originCoords = AIRPORT_COORDS[origin] ?? [60, 11];

  // Focus longitude: midpoint biased toward destination
  const focusLng = useMemo(() => {
    if (!highlightedDest) return null;
    const dest = destinations.find((d) => d.code === highlightedDest);
    if (!dest) return null;
    const dc = AIRPORT_COORDS[dest.code] ?? (dest.lat && dest.lng ? [dest.lat, dest.lng] : null);
    if (!dc) return null;
    let diff = dc[1] - originCoords[1];
    if (diff > 180) diff -= 360;
    if (diff < -180) diff += 360;
    return originCoords[1] + diff * 0.6;
  }, [highlightedDest, destinations, originCoords]);

  // Highlighted destination info (for overlay)
  const highlightedInfo = useMemo(() => {
    if (!highlightedDest) return null;
    const dest = destinations.find((d) => d.code === highlightedDest);
    if (!dest) return null;
    const dc = AIRPORT_COORDS[dest.code] ?? (dest.lat && dest.lng ? [dest.lat, dest.lng] : null);
    if (!dc) return null;
    const km = haversineKm(originCoords[0], originCoords[1], dc[0], dc[1]);
    const hours = Math.round(km / 800); // rough flight time
    return { code: dest.code, city: dest.city, hasBusiness: dest.hasBusiness, km: Math.round(km), hours };
  }, [highlightedDest, destinations, originCoords]);

  const { arcs, points, rings, labels } = useMemo(() => {
    const oP = originCoords;
    const hasHL = !!highlightedDest;
    const arcs: GlobeArc[] = [];
    const points: GlobePoint[] = [];
    const rings: GlobeRing[] = [];
    const labels: GlobeLabel[] = [];

    // Origin — always visible, always pulsing
    points.push({ lat: oP[0], lng: oP[1], size: 1.0, color: "#10b981", label: origin, code: origin, highlighted: false, dimmed: false });
    rings.push({ lat: oP[0], lng: oP[1], maxR: 3, propagationSpeed: 1.5, repeatPeriod: 2000, color: "#10b981" });

    for (const dest of destinations) {
      const coords = AIRPORT_COORDS[dest.code] ?? (dest.lat && dest.lng ? [dest.lat, dest.lng] : null);
      if (!coords) continue;

      const isHL = highlightedDest === dest.code;
      const isDim = hasHL && !isHL;
      const color = dest.hasBusiness ? "#f59e0b" : "#10b981";

      // Normal arc
      arcs.push({
        startLat: oP[0], startLng: oP[1], endLat: coords[0], endLng: coords[1],
        color, destCode: dest.code, highlighted: isHL, dimmed: isDim, glow: false,
      });

      // Glow arc (wider, semi-transparent) — only for highlighted
      if (isHL) {
        arcs.push({
          startLat: oP[0], startLng: oP[1], endLat: coords[0], endLng: coords[1],
          color, destCode: dest.code, highlighted: true, dimmed: false, glow: true,
        });
      }

      points.push({
        lat: coords[0], lng: coords[1],
        size: Math.min(1, 0.3 + dest.totalSeats / 100),
        color, label: dest.city, code: dest.code,
        highlighted: isHL, dimmed: isDim,
      });

      // Pulsing ring at highlighted destination
      if (isHL) {
        rings.push({ lat: coords[0], lng: coords[1], maxR: 4, propagationSpeed: 3, repeatPeriod: 800, color: "#ffffff" });
        labels.push({ lat: coords[0], lng: coords[1], text: dest.city, size: 1.0, color: "rgba(255,255,255,0.9)" });
      }
    }

    return { arcs, points, rings, labels };
  }, [origin, originCoords, destinations, highlightedDest]);

  const hasHighlight = !!highlightedDest;

  if (compact) {
    return (
      <div className="relative h-full min-h-[340px] bg-[#020617]">
        {/* Vignette edges */}
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 h-16 bg-gradient-to-b from-[#020617]/70 to-transparent" />
        <div className="pointer-events-none absolute inset-x-0 bottom-0 z-10 h-24 bg-gradient-to-t from-[#020617] to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 left-0 z-10 w-6 bg-gradient-to-r from-[#020617]/40 to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 z-10 w-6 bg-gradient-to-l from-[#020617]/40 to-transparent" />

        <div className="h-full w-full">
          <Canvas
            camera={{ position: [0, 0, 280], fov: 50, near: 1, far: 1000 }}
            style={{ background: "transparent", height: "100%" }}
          >
            <GlobeScene
              arcs={arcs} points={points} rings={rings} labels={labels}
              originCoords={originCoords} focusLng={focusLng} hasHighlight={hasHighlight}
            />
          </Canvas>
        </div>

        {/* Origin badge */}
        <div className="absolute left-3 top-3 z-20">
          <div className="flex items-center gap-1.5 rounded-md bg-black/50 px-2.5 py-1 backdrop-blur-sm">
            <span className="h-[5px] w-[5px] animate-pulse rounded-full bg-emerald-400" />
            <span className={`text-[10px] font-bold text-emerald-400 ${mono}`}>{origin}</span>
            <span className="text-[9px] text-[hsla(0,0%,100%,.3)]">{findAirport(origin)?.name}</span>
          </div>
        </div>

        {/* Highlighted route info panel — rich overlay */}
        {highlightedInfo && (
          <div className="absolute right-3 top-3 z-20 animate-in fade-in slide-in-from-right-2 duration-200">
            <div className="rounded-lg bg-black/60 px-3 py-2 backdrop-blur-sm">
              <div className="flex items-center gap-1.5">
                <span className="h-[5px] w-[5px] rounded-full bg-white shadow-[0_0_6px_rgba(255,255,255,.5)]" />
                <span className={`text-[12px] font-bold text-white ${mono}`}>{highlightedInfo.code}</span>
              </div>
              <div className="mt-0.5 text-[10px] text-[hsla(0,0%,100%,.6)]">{highlightedInfo.city}</div>
              <div className="mt-1.5 flex items-center gap-3 border-t border-[hsla(0,0%,100%,.08)] pt-1.5">
                <span className={`text-[9px] text-[hsla(0,0%,100%,.3)] ${mono}`}>{highlightedInfo.km.toLocaleString()} km</span>
                <span className={`text-[9px] text-[hsla(0,0%,100%,.3)] ${mono}`}>~{highlightedInfo.hours}h</span>
                {highlightedInfo.hasBusiness && (
                  <span className="flex items-center gap-1">
                    <span className="h-[4px] w-[4px] rounded-full bg-amber-400" />
                    <span className={`text-[8px] text-amber-400/70 ${mono}`}>biz</span>
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-3 left-3 z-20 flex items-center gap-3 rounded-md bg-black/50 px-2.5 py-1.5 backdrop-blur-sm">
          <div className="flex items-center gap-1">
            <div className="h-[2px] w-2.5 rounded-full bg-emerald-400" />
            <span className={`text-[8px] text-[hsla(0,0%,100%,.35)] ${mono}`}>eco</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="h-[2px] w-2.5 rounded-full bg-amber-400" />
            <span className={`text-[8px] text-[hsla(0,0%,100%,.35)] ${mono}`}>biz</span>
          </div>
          <span className={`text-[8px] text-[hsla(0,0%,100%,.18)] ${mono}`}>{destinations.length}</span>
        </div>
      </div>
    );
  }

  // Full-size globe (non-compact)
  return (
    <div className="relative overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[#020617]">
      <div className="h-[500px] w-full">
        <Canvas camera={{ position: [0, 0, 300], fov: 50, near: 1, far: 1000 }} style={{ background: "transparent" }}>
          <GlobeScene
            arcs={arcs} points={points} rings={rings} labels={labels}
            originCoords={originCoords} focusLng={focusLng} hasHighlight={hasHighlight}
          />
        </Canvas>
      </div>

      <div className="absolute left-5 top-5">
        <div className="flex items-center gap-2 rounded-lg bg-black/60 px-3 py-2 backdrop-blur">
          <span className={`text-[10px] text-[hsla(0,0%,100%,.3)] ${mono}`}>Routes from</span>
          <span className={`text-[13px] font-bold text-emerald-400 ${mono}`}>{origin}</span>
          <span className="text-[12px] text-[hsla(0,0%,100%,.4)]">{findAirport(origin)?.name}</span>
        </div>
      </div>

      <div className="absolute bottom-5 left-5 flex items-center gap-4 rounded-lg bg-black/60 px-3 py-2 backdrop-blur">
        <div className="flex items-center gap-1.5">
          <div className="h-[2px] w-4 rounded-full bg-emerald-400" />
          <span className={`text-[9px] text-[hsla(0,0%,100%,.3)] ${mono}`}>economy</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="h-[2px] w-4 rounded-full bg-amber-400" />
          <span className={`text-[9px] text-[hsla(0,0%,100%,.3)] ${mono}`}>business</span>
        </div>
        <span className={`text-[10px] text-[hsla(0,0%,100%,.2)] ${mono}`}>{destinations.length} destinations</span>
      </div>

      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#020617] to-transparent" />
    </div>
  );
}
