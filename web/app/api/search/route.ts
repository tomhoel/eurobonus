import { NextRequest, NextResponse } from "next/server";
import { getAvailableDates } from "@/lib/sas/availability";
import { getRouteDetails } from "@/lib/sas/routes";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const origin = searchParams.get("origin")?.toUpperCase();
  const destination = searchParams.get("destination")?.toUpperCase();
  const month = searchParams.get("month") ?? "";
  const date = searchParams.get("date");

  if (!origin || !destination) {
    return NextResponse.json(
      { error: "origin and destination required" },
      { status: 400 },
    );
  }

  // If a specific date is requested, return route details
  if (date) {
    const routes = await getRouteDetails(origin, destination, date);
    return NextResponse.json({ routes });
  }

  // Otherwise return calendar availability
  const dates = await getAvailableDates(origin, destination, { month });
  return NextResponse.json({ dates });
}
