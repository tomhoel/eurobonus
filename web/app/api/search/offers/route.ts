import { NextRequest, NextResponse } from "next/server";
import { getOffersWithPoints } from "@/lib/sas/offers";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const origin = searchParams.get("origin")?.toUpperCase();
  const destination = searchParams.get("destination")?.toUpperCase();
  const date = searchParams.get("date");

  if (!origin || !destination || !date) {
    return NextResponse.json(
      { error: "origin, destination, and date required" },
      { status: 400 },
    );
  }

  try {
    const offers = await getOffersWithPoints(origin, destination, date);
    return NextResponse.json({ offers });
  } catch (e) {
    console.error("[offers] Error:", e);
    return NextResponse.json({ offers: [], error: "Failed to fetch offers" });
  }
}
