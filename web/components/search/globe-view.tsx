"use client";

import { useEffect, useRef, useMemo, useCallback } from "react";
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
}

interface GlobePoint {
  lat: number;
  lng: number;
  size: number;
  color: string;
  label: string;
  code: string;
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
}

// Lat/lng for airports (supplement for airports not in API response)
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

function GlobeObject({ arcs, points }: { arcs: GlobeArc[]; points: GlobePoint[] }) {
  const globeRef = useRef<ThreeGlobe | null>(null);
  const groupRef = useRef<THREE.Group>(null);
  const { scene } = useThree();

  useEffect(() => {
    const globe = new ThreeGlobe({ animateIn: true })
      .hexPolygonsData([]) // We'll load geo data
      .hexPolygonResolution(3)
      .hexPolygonMargin(0.7)
      .hexPolygonColor(() => "rgba(255, 255, 255, 0.06)")
      .showAtmosphere(true)
      .atmosphereColor("#10b981")
      .atmosphereAltitude(0.2)
      .arcsData(arcs)
      .arcColor("color" as unknown as string)
      .arcAltitude(0.15)
      .arcStroke(0.5)
      .arcDashLength(0.9)
      .arcDashGap(4)
      .arcDashAnimateTime(1500)
      .pointsData(points)
      .pointColor("color" as unknown as string)
      .pointsMerge(true)
      .pointAltitude(0.01)
      .pointRadius("size" as unknown as string);

    // Style the globe material
    const globeMaterial = globe.globeMaterial() as THREE.MeshPhongMaterial;
    globeMaterial.color = new THREE.Color("#050d21");
    globeMaterial.emissive = new THREE.Color("#062056");
    globeMaterial.emissiveIntensity = 0.1;
    globeMaterial.shininess = 0.9;

    // Load geo data for country polygons
    fetch("/globe-data.json")
      .then((r) => r.json())
      .then((geoData) => {
        globe
          .hexPolygonsData(geoData.features)
          .hexPolygonResolution(3)
          .hexPolygonMargin(0.7)
          .hexPolygonColor(() => "rgba(255, 255, 255, 0.06)");
      })
      .catch(() => {});

    globeRef.current = globe;
    if (groupRef.current) {
      groupRef.current.add(globe);
    }

    return () => {
      if (groupRef.current) {
        groupRef.current.remove(globe);
      }
    };
  }, []);

  // Update arcs and points when data changes
  useEffect(() => {
    if (globeRef.current) {
      globeRef.current.arcsData(arcs);
      globeRef.current.pointsData(points);
    }
  }, [arcs, points]);

  // Slow rotation
  useFrame(() => {
    if (groupRef.current) {
      groupRef.current.rotation.y += 0.001;
    }
  });

  return <group ref={groupRef} />;
}

function GlobeScene({ arcs, points, originCoords }: { arcs: GlobeArc[]; points: GlobePoint[]; originCoords: [number, number] }) {
  // Convert lat/lng to camera position (looking at the origin)
  const cameraPos = useMemo(() => {
    const lat = originCoords[0] * (Math.PI / 180);
    const lng = originCoords[1] * (Math.PI / 180);
    const dist = 250;
    return new THREE.Vector3(
      dist * Math.cos(lat) * Math.sin(lng),
      dist * Math.sin(lat),
      dist * Math.cos(lat) * Math.cos(lng),
    );
  }, [originCoords]);

  return (
    <>
      <ambientLight intensity={0.6} color="#e0e7ff" />
      <directionalLight position={[-400, 100, 400]} intensity={1} color="#ffffff" />
      <pointLight position={[-200, 500, 200]} intensity={0.8} color="#3b82f6" />
      <GlobeObject arcs={arcs} points={points} />
      <OrbitControls
        enablePan={false}
        enableZoom={false}
        minDistance={200}
        maxDistance={350}
        autoRotate={false}
        target={[0, 0, 0]}
      />
    </>
  );
}

export function GlobeView({ origin, destinations, onSelectDestination }: GlobeViewProps) {
  const originCoords = AIRPORT_COORDS[origin] ?? [60, 11];

  const { arcs, points } = useMemo(() => {
    const originPt = originCoords;
    const arcs: GlobeArc[] = [];
    const points: GlobePoint[] = [];

    // Origin point (larger, emerald)
    points.push({
      lat: originPt[0],
      lng: originPt[1],
      size: 1.2,
      color: "#10b981",
      label: origin,
      code: origin,
    });

    for (const dest of destinations) {
      const coords = AIRPORT_COORDS[dest.code] ?? (dest.lat && dest.lng ? [dest.lat, dest.lng] : null);
      if (!coords) continue;

      // Arc color based on cabin availability
      const color = dest.hasBusiness
        ? "#f59e0b" // amber for business
        : "#10b981"; // emerald for economy

      arcs.push({
        startLat: originPt[0],
        startLng: originPt[1],
        endLat: coords[0],
        endLng: coords[1],
        color,
      });

      points.push({
        lat: coords[0],
        lng: coords[1],
        size: Math.min(1, 0.3 + dest.totalSeats / 100),
        color: dest.hasBusiness ? "#f59e0b" : "#10b981",
        label: dest.city,
        code: dest.code,
      });
    }

    return { arcs, points };
  }, [origin, originCoords, destinations]);

  return (
    <div className="relative overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[#020617]">
      {/* Globe canvas */}
      <div className="h-[500px] w-full">
        <Canvas
          camera={{ position: [0, 0, 300], fov: 50, near: 1, far: 1000 }}
          style={{ background: "transparent" }}
        >
          <GlobeScene arcs={arcs} points={points} originCoords={originCoords} />
        </Canvas>
      </div>

      {/* Overlay info */}
      <div className="absolute left-5 top-5">
        <div className="flex items-center gap-2 rounded-lg bg-black/60 px-3 py-2 backdrop-blur">
          <span className={`text-[10px] text-[hsla(0,0%,100%,.3)] ${mono}`}>Routes from</span>
          <span className={`text-[13px] font-bold text-emerald-400 ${mono}`}>{origin}</span>
          <span className="text-[12px] text-[hsla(0,0%,100%,.4)]">{findAirport(origin)?.name}</span>
        </div>
      </div>

      {/* Legend */}
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

      {/* Bottom gradient */}
      <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#020617] to-transparent" />
    </div>
  );
}
