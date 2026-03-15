"use client";

import { Map } from "lucide-react";

export function ResultMap() {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-white/10 bg-white/[0.02] py-16 text-center">
      <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-white/5">
        <Map className="size-8 text-zinc-600" />
      </div>
      <h3 className="text-lg font-medium text-zinc-300">Map view coming soon</h3>
      <p className="mt-1 text-sm text-zinc-500">
        Visualize routes and availability on an interactive map.
      </p>
    </div>
  );
}
