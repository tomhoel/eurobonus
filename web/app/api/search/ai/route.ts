import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { mode, query } = body as { mode: string; query: string };

    if (mode === "parse") {
      // Parse natural language query into filter suggestions
      const filters = parseNaturalLanguage(query);
      return NextResponse.json({ filters });
    }

    return NextResponse.json({ error: "Unknown mode" }, { status: 400 });
  } catch {
    return NextResponse.json({ error: "AI unavailable" }, { status: 500 });
  }
}

function parseNaturalLanguage(query: string): Record<string, unknown> {
  const q = query.toLowerCase();
  const filters: Record<string, unknown> = {};

  // Cabin detection
  if (q.includes("business")) filters.cabin = "BUSINESS";
  else if (q.includes("premium")) filters.cabin = "PREMIUM";
  else if (q.includes("economy")) filters.cabin = "ECONOMY";

  // Destination detection
  const destMap: Record<string, string> = {
    tokyo: "NRT", bangkok: "BKK", singapore: "SIN",
    osaka: "KIX", seoul: "ICN", shanghai: "PVG",
    beijing: "PEK", hanoi: "HAN", "ho chi minh": "SGN",
    "new york": "JFK", "los angeles": "LAX", miami: "MIA",
    japan: "NRT", thailand: "BKK", asia: "BKK",
  };
  for (const [keyword, code] of Object.entries(destMap)) {
    if (q.includes(keyword)) {
      filters.destination = code;
      break;
    }
  }

  // Origin detection
  const originMap: Record<string, string> = {
    oslo: "OSL", copenhagen: "CPH", stockholm: "ARN",
    paris: "CDG", amsterdam: "AMS", london: "LHR", frankfurt: "FRA",
  };
  for (const [keyword, code] of Object.entries(originMap)) {
    if (q.includes(keyword)) {
      filters.origin = code;
      break;
    }
  }

  // Points budget
  const ptsMatch = q.match(/(\d+)\s*k?\s*(?:points|pts)/);
  if (ptsMatch) {
    let pts = parseInt(ptsMatch[1], 10);
    if (pts < 1000) pts *= 1000; // e.g., "80k" or "80"
    filters.maxPoints = pts;
  }

  // Stops
  if (q.includes("direct") || q.includes("nonstop") || q.includes("non-stop")) {
    filters.maxStops = 0;
  }

  // Bonus
  if (q.includes("bonus") || q.includes("saver")) {
    filters.bonusOnly = true;
  }

  return filters;
}
