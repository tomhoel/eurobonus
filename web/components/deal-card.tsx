import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { findAirport } from "@/lib/route-map";

interface Props {
  deal: {
    origin: string;
    destination: string;
    date: string;
    economySeats: number | null;
    premiumSeats: number | null;
    businessSeats: number | null;
    isBonus: boolean | null;
    pointsBusiness: number | null;
  };
}

export function DealCard({ deal }: Props) {
  const orig = findAirport(deal.origin);
  const dest = findAirport(deal.destination);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">
            {orig?.name ?? deal.origin} → {dest?.name ?? deal.destination}
          </h3>
          <span className="text-sm text-muted-foreground">
            {new Date(deal.date + "T00:00").toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            })}
          </span>
        </div>
        <div className="flex gap-2">
          {(deal.economySeats ?? 0) > 0 && (
            <Badge variant="secondary">Economy: {deal.economySeats}</Badge>
          )}
          {(deal.premiumSeats ?? 0) > 0 && (
            <Badge className="bg-amber-50 text-amber-700">
              Premium: {deal.premiumSeats}
            </Badge>
          )}
          {(deal.businessSeats ?? 0) > 0 && (
            <Badge className="bg-indigo-50 text-indigo-700">
              Business: {deal.businessSeats}
            </Badge>
          )}
        </div>
        {deal.isBonus && (
          <p className="mt-2 text-xs text-green-600">Verified bonus seats</p>
        )}
      </CardContent>
    </Card>
  );
}
