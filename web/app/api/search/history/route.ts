import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const origin = searchParams.get("origin")?.toUpperCase();
  const destination = searchParams.get("destination")?.toUpperCase();
  const days = parseInt(searchParams.get("days") ?? "30", 10);

  if (!origin || !destination) {
    return NextResponse.json(
      { error: "origin and destination required" },
      { status: 400 },
    );
  }

  // Generate mock historical data for the sparkline
  // In production, this would query the availabilityCache table
  const history: { date: string; seats: number }[] = [];
  const now = new Date();
  for (let i = days; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    history.push({
      date: d.toISOString().slice(0, 10),
      seats: Math.floor(Math.random() * 8) + 1,
    });
  }

  return NextResponse.json({ history });
}
