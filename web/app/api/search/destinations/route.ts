import { NextRequest, NextResponse } from "next/server";
import { getAvailabilityCalendar } from "@/lib/sas/availability";

export interface DestinationSummary {
  code: string;
  city: string;
  country: string;
  lat: number;
  lng: number;
  economySeats: number;
  premiumSeats: number;
  businessSeats: number;
  totalSeats: number;
  datesWithSeats: number;
  totalDates: number;
  nextAvailableDate: string | null;
}

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const origin = searchParams.get("origin")?.toUpperCase();

  if (!origin) {
    return NextResponse.json({ error: "origin required" }, { status: 400 });
  }

  try {
    const results = await getAvailabilityCalendar(origin, "", {
      direct: false,
    });

    // Today's date string for filtering out past dates
    const today = new Date().toISOString().slice(0, 10);

    const destinations: DestinationSummary[] = results
      .map((dest) => {
        // Only count future dates
        const futureDates = (dest.outbound ?? []).filter((d) => d.date >= today);

        const eco = futureDates.reduce((s, d) => s + d.economySeats, 0);
        const prem = futureDates.reduce((s, d) => s + d.premiumSeats, 0);
        const biz = futureDates.reduce((s, d) => s + d.businessSeats, 0);
        const datesWithSeats = futureDates.filter(
          (d) => d.economySeats + d.premiumSeats + d.businessSeats > 0,
        ).length;
        const nextDate = futureDates.find(
          (d) => d.economySeats + d.premiumSeats + d.businessSeats > 0,
        );

        const raw = dest as unknown as Record<string, unknown>;
        return {
          code: dest.iataCode,
          city: dest.cityName,
          country: String(raw.countryName ?? ""),
          lat: Number(raw.lat ?? 0),
          lng: Number(raw.long ?? raw.lng ?? 0),
          economySeats: eco,
          premiumSeats: prem,
          businessSeats: biz,
          totalSeats: eco + prem + biz,
          datesWithSeats,
          totalDates: futureDates.length,
          nextAvailableDate: nextDate?.date ?? null,
        };
      })
      .filter((d) => d.totalSeats > 0)
      .sort((a, b) => b.totalSeats - a.totalSeats);

    return NextResponse.json({ destinations, origin });
  } catch (e) {
    console.error("[destinations] Error:", e);
    return NextResponse.json({ destinations: [], origin });
  }
}
