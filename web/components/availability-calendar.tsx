"use client";
import type { AvailabilityDate } from "@/lib/sas/types";
import { Badge } from "@/components/ui/badge";

interface Props {
  dates: AvailabilityDate[];
  onSelectDate?: (date: string) => void;
}

export function AvailabilityCalendar({ dates, onSelectDate }: Props) {
  if (!dates.length) {
    return (
      <p className="text-sm text-muted-foreground">
        No availability found for this route and period.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {dates.map((d) => {
        const hasEconomy = d.economySeats > 0;
        const hasPremium = d.premiumSeats > 0;
        const hasBusiness = d.businessSeats > 0;

        return (
          <button
            key={d.date}
            onClick={() => onSelectDate?.(d.date)}
            className="flex items-center justify-between rounded-lg border bg-white p-3 text-left transition hover:border-indigo-300 hover:shadow-sm"
          >
            <span className="text-sm font-medium">
              {new Date(d.date + "T00:00").toLocaleDateString("en-US", {
                weekday: "short",
                month: "short",
                day: "numeric",
              })}
            </span>
            <div className="flex gap-1.5">
              {hasEconomy && (
                <Badge variant="secondary" className="text-xs">
                  E: {d.economySeats}
                </Badge>
              )}
              {hasPremium && (
                <Badge
                  variant="secondary"
                  className="bg-amber-50 text-amber-700 text-xs"
                >
                  P: {d.premiumSeats}
                </Badge>
              )}
              {hasBusiness && (
                <Badge
                  variant="secondary"
                  className="bg-indigo-50 text-indigo-700 text-xs"
                >
                  B: {d.businessSeats}
                </Badge>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
