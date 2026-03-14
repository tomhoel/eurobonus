import type { FlightOffer } from "@/lib/sas/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  offer: FlightOffer;
}

export function FlightCard({ offer }: Props) {
  const segments = offer.segments;
  const dep = segments[0];
  const arr = segments[segments.length - 1];

  const bookingUrl = `https://www.sas.no/book/flights/?search=OW_${offer.origin}-${offer.destination}-${offer.date.replace(/-/g, "")}_a1c0i0y0&bookingFlow=points`;

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 p-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm">
              {dep?.departureTime ?? ""}
            </span>
            <span className="text-xs text-muted-foreground">→</span>
            <span className="font-mono text-sm">{arr?.arrivalTime ?? ""}</span>
            {offer.stops > 0 && (
              <span className="text-xs text-muted-foreground">
                ({offer.stops} stop{offer.stops > 1 ? "s" : ""})
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {dep?.carrier} {dep?.flightNumber}
            </span>
            <Badge
              variant={offer.isBonusTicket ? "default" : "outline"}
              className={
                offer.isBonusTicket ? "bg-green-600 text-xs" : "text-xs"
              }
            >
              {offer.productName}
            </Badge>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold">
            {offer.points.toLocaleString()} pts
          </div>
          <div className="text-xs text-muted-foreground">
            + {offer.taxes.toFixed(0)} {offer.currency} tax
          </div>
          <a
            href={bookingUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-indigo-600 hover:underline"
          >
            Book on SAS
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
