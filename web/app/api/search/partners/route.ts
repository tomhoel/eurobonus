import { NextRequest, NextResponse } from "next/server";
import { getPartnerAwards } from "@/lib/sas/partners";

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
    const partners = await getPartnerAwards(origin, destination, date);
    return NextResponse.json({ partners });
  } catch {
    return NextResponse.json({ partners: [], error: "Failed to fetch partners" });
  }
}
