"use client";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { SearchForm } from "@/components/search-form";
import { AvailabilityCalendar } from "@/components/availability-calendar";
import { findAirport } from "@/lib/route-map";
import type { AvailabilityDate } from "@/lib/sas/types";

function SearchResults() {
  const searchParams = useSearchParams();
  const origin = searchParams.get("origin") ?? "";
  const destination = searchParams.get("destination") ?? "";
  const month = searchParams.get("month") ?? "";
  const [dates, setDates] = useState<AvailabilityDate[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!origin || !destination) return;
    setLoading(true);
    const params = new URLSearchParams({ origin, destination });
    if (month) params.set("month", month);
    fetch(`/api/search?${params}`)
      .then((r) => r.json())
      .then((data) => setDates(data.dates ?? []))
      .finally(() => setLoading(false));
  }, [origin, destination, month]);

  const originAirport = findAirport(origin);
  const destAirport = findAirport(destination);

  return (
    <div className="space-y-6">
      <div className="rounded-lg border bg-white p-4">
        <SearchForm />
      </div>

      {origin && destination && (
        <div>
          <h2 className="mb-4 text-xl font-semibold">
            {originAirport?.name ?? origin} →{" "}
            {destAirport?.name ?? destination}
            {month && (
              <span className="text-muted-foreground font-normal text-base ml-2">
                {new Date(
                  Number(month.slice(0, 4)),
                  Number(month.slice(4)) - 1,
                ).toLocaleDateString("en-US", {
                  month: "long",
                  year: "numeric",
                })}
              </span>
            )}
          </h2>

          {loading ? (
            <p className="text-sm text-muted-foreground">Searching SAS...</p>
          ) : (
            <AvailabilityCalendar dates={dates} />
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense
      fallback={<p className="text-sm text-muted-foreground">Loading...</p>}
    >
      <SearchResults />
    </Suspense>
  );
}
