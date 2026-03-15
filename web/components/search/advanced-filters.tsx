"use client";

import { AnimatePresence, motion } from "framer-motion";
import { PointsFilters } from "./points-filters";
import { RouteFilters } from "./route-filters";
import { PowerFilters } from "./power-filters";
import type { SearchFilters } from "@/lib/search/types";

interface AdvancedFiltersProps {
  open: boolean;
  filters: SearchFilters;
  updateFilter: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void;
}

export function AdvancedFilters({ open, filters, updateFilter }: AdvancedFiltersProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.25, ease: "easeInOut" }}
          className="overflow-hidden"
        >
          <div className="grid gap-6 rounded-xl border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] p-6 md:grid-cols-3">
            <PointsFilters filters={filters} updateFilter={updateFilter} />
            <RouteFilters filters={filters} updateFilter={updateFilter} />
            <PowerFilters filters={filters} updateFilter={updateFilter} />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
