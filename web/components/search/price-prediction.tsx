"use client";

import { useEffect, useState } from "react";
import { TrendingUp } from "lucide-react";

interface PricePredictionProps {
  origin: string;
  destination: string;
}

interface HistoryPoint {
  date: string;
  seats: number;
}

export function PricePrediction({ origin, destination }: PricePredictionProps) {
  const [history, setHistory] = useState<HistoryPoint[]>([]);

  useEffect(() => {
    if (!origin || !destination) return;
    fetch(`/api/search/history?origin=${origin}&destination=${destination}&days=30`)
      .then((r) => r.json())
      .then((data) => setHistory(data.history ?? []))
      .catch(() => {});
  }, [origin, destination]);

  if (history.length === 0) return null;

  const maxSeats = Math.max(...history.map((h) => h.seats), 1);
  const width = 280;
  const height = 60;
  const padding = 4;

  const points = history.map((h, i) => {
    const x = padding + (i / (history.length - 1)) * (width - padding * 2);
    const y = height - padding - (h.seats / maxSeats) * (height - padding * 2);
    return `${x},${y}`;
  });

  const linePath = `M ${points.join(" L ")}`;
  const areaPath = `${linePath} L ${width - padding},${height - padding} L ${padding},${height - padding} Z`;

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium text-zinc-400">
        <TrendingUp className="size-3 text-emerald-400" />
        Availability Trend (30d)
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full">
        <defs>
          <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgb(16, 185, 129)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="rgb(16, 185, 129)" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#sparkGrad)" />
        <path d={linePath} fill="none" stroke="rgb(16, 185, 129)" strokeWidth="1.5" />
        {/* Now indicator */}
        <circle
          cx={width - padding}
          cy={parseFloat(points[points.length - 1]?.split(",")[1] ?? "30")}
          r="3"
          fill="rgb(16, 185, 129)"
        />
      </svg>
      <div className="mt-1 flex items-center justify-between text-[10px] text-zinc-600">
        <span>{history[0]?.date.slice(5)}</span>
        <span className="font-medium text-emerald-400">Now</span>
      </div>
    </div>
  );
}
