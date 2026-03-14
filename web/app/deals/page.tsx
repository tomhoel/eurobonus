"use client";
import { useEffect, useState } from "react";
import { DealCard } from "@/components/deal-card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DealsPage() {
  const [deals, setDeals] = useState<any[]>([]);
  const [cabin, setCabin] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = cabin !== "all" ? `?cabin=${cabin}` : "";
    fetch(`/api/deals${params}`)
      .then((r) => r.json())
      .then((data) => setDeals(data.deals ?? []))
      .finally(() => setLoading(false));
  }, [cabin]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Best Deals</h1>
        <p className="text-sm text-muted-foreground">
          Current award availability across all monitored routes.
        </p>
      </div>

      <Tabs value={cabin} onValueChange={setCabin}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="economy">Economy</TabsTrigger>
          <TabsTrigger value="premium">Premium</TabsTrigger>
          <TabsTrigger value="business">Business</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading deals...</p>
      ) : deals.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No deals found. Check back after the next scan.
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {deals.map((d, i) => (
            <DealCard key={i} deal={d} />
          ))}
        </div>
      )}
    </div>
  );
}
