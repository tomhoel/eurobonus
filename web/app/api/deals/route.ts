import { NextRequest, NextResponse } from "next/server";
import { getBestDeals } from "@/lib/db/queries/availability";

export async function GET(req: NextRequest) {
  const cabin = req.nextUrl.searchParams.get("cabin") ?? undefined;
  const deals = await getBestDeals({ cabinFilter: cabin });
  return NextResponse.json({ deals });
}
