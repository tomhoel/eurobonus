"use client";

import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import type { SearchFilters } from "@/lib/search/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface PointsFiltersProps {
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
}

export function PointsFilters({ filters, updateFilter }: PointsFiltersProps) {
  return (
    <div className="space-y-5">
      <h4 className={`text-[10px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.22)] ${mono}`}>
        Points & Value
      </h4>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Max points</span>
          <span className={`text-[12px] text-emerald-400/80 ${mono}`}>
            {filters.maxPoints > 0 ? `${(filters.maxPoints / 1000).toFixed(0)}k` : "Any"}
          </span>
        </div>
        <Slider
          min={0}
          max={200000}
          value={[filters.maxPoints]}
          onValueChange={(val) => updateFilter("maxPoints", Array.isArray(val) ? val[0] : val)}
          step={5000}
          className="[&_[data-slot=slider-range]]:bg-emerald-500 [&_[data-slot=slider-thumb]]:border-emerald-500"
        />
        <div className={`flex justify-between text-[10px] text-[hsla(0,0%,100%,.15)] ${mono}`}>
          <span>Any</span><span>50k</span><span>100k</span><span>150k</span><span>200k</span>
        </div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Bonus fares only</span>
        <Switch
          checked={filters.bonusOnly}
          onCheckedChange={(checked) => updateFilter("bonusOnly", !!checked)}
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[13px] text-[hsla(0,0%,100%,.35)]">Min value score</span>
          <span className={`text-[12px] text-emerald-400/80 ${mono}`}>
            {filters.minValueScore > 0 ? `${filters.minValueScore}/10` : "Any"}
          </span>
        </div>
        <Slider
          min={0}
          max={10}
          value={[filters.minValueScore]}
          onValueChange={(val) => updateFilter("minValueScore", Array.isArray(val) ? val[0] : val)}
          step={1}
          className="[&_[data-slot=slider-range]]:bg-emerald-500 [&_[data-slot=slider-thumb]]:border-emerald-500"
        />
      </div>
    </div>
  );
}
