import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI, SchemaType } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_GENERATIVE_AI_API_KEY || "");

// All SAS EuroBonus network airports the system knows about
const NETWORK_AIRPORTS = `
SCANDINAVIA: OSL (Oslo), CPH (Copenhagen), ARN (Stockholm), GOT (Gothenburg), BGO (Bergen), TRD (Trondheim), SVG (Stavanger), HEL (Helsinki), KEF (Reykjavik)
BALTICS: TLL (Tallinn), RIX (Riga)
UK & IRELAND: LHR (London), MAN (Manchester), EDI (Edinburgh), DUB (Dublin)
SOUTHERN EUROPE: CDG (Paris), BCN (Barcelona), MAD (Madrid), AGP (Malaga), ALC (Alicante), PMI (Mallorca), TFS (Tenerife), LPA (Gran Canaria), FCO (Rome), MXP (Milan), NAP (Naples), VCE (Venice), ATH (Athens), CHQ (Crete), RHO (Rhodes), LIS (Lisbon), FAO (Faro), IST (Istanbul), AYT (Antalya), SPU (Split), DBV (Dubrovnik), NIC (Nice)
CENTRAL EUROPE: FRA (Frankfurt), MUC (Munich), AMS (Amsterdam), BRU (Brussels), ZRH (Zurich), VIE (Vienna), PRG (Prague), WAW (Warsaw), GDN (Gdansk), BUD (Budapest)
ASIA: BKK (Bangkok), NRT (Tokyo Narita), HND (Tokyo Haneda), KIX (Osaka), SIN (Singapore), HKG (Hong Kong), ICN (Seoul), PEK (Beijing), PVG (Shanghai), DEL (Delhi), BOM (Mumbai), SGN (Ho Chi Minh), HAN (Hanoi)
AMERICAS: JFK (New York), EWR (Newark), LAX (Los Angeles), SFO (San Francisco), ORD (Chicago), MIA (Miami), BOS (Boston), IAD (Washington), YYZ (Toronto)
AFRICA: CPT (Cape Town), NBO (Nairobi)
`.trim();

const AWARD_CHART = `
SAS EuroBonus award pricing (one-way, from 1 Dec 2025):
- Domestic (within NO/SE/DK): Economy 5,000 · Premium 10,000 · Business —
- Between Nordic+ (NO/SE/DK/FI/IS/EE/LV/LT): Economy 10,000 · Business 20,000
- Nordic+ ↔ Europe: Economy 15,000 · Business 35,000
- Intra-Europe: Economy 25,000 · Business 40,000
- To/from Asia & North America: Economy 30,000 · Premium 45,000 · Business 60,000
`.trim();

// Approximate flight times from Scandinavia (hours)
const FLIGHT_TIMES = `
Approximate flight times from Scandinavian hubs:
- Domestic Scandinavia: 1-2h
- UK/Ireland: 2-3h
- Central Europe: 2-3h
- Southern Europe (Mediterranean): 3-5h
- Turkey/Greece: 4-5h
- Canary Islands: 5-6h
- Middle East: 5-6h
- US East Coast: 8-9h
- US West Coast: 11-12h
- Thailand/Vietnam: 10-11h
- Japan/South Korea: 11-12h
- Singapore: 12-13h
- India: 8-9h
- South Africa: 12-13h
`.trim();

// Climate knowledge for "somewhere warm/hot/cold" queries
const CLIMATE_HINTS = `
Warm/hot destinations by month:
- Dec-Feb (winter): BKK, SIN, SGN, HAN, BOM, DEL, NBO, CPT, TFS, LPA, MIA, AYT (shoulder)
- Mar-May (spring): BKK, SIN, ATH, BCN, LIS, FCO, IST, AGP, FAO, PMI, NIC
- Jun-Aug (summer): ATH, BCN, MAD, AGP, FCO, NAP, SPU, DBV, CHQ, RHO, PMI, AYT, IST, FAO, NIC, LPA
- Sep-Nov (autumn): BKK, SIN, ATH, BCN, IST, AYT, LIS, FCO, TFS, NBO, CPT

Cold/northern destinations: KEF (Iceland), TRD/BGO/SVG (Norway fjords)
City breaks year-round: LHR, CDG, AMS, PRG, VIE, BUD, BCN, FCO, IST
Beach destinations: AGP, ALC, PMI, TFS, LPA, CHQ, RHO, FAO, AYT, DBV, SPU, NIC, MIA
`.trim();

const SYSTEM_PROMPT = `You are the AI search assistant for hellasus.no — a SAS EuroBonus award flight search engine. Your job is to interpret natural language travel queries and extract structured search filters.

## Network
${NETWORK_AIRPORTS}

## Award Chart
${AWARD_CHART}

## Flight Times
${FLIGHT_TIMES}

## Climate & Destinations
${CLIMATE_HINTS}

## Rules
1. Always return valid IATA 3-letter airport codes from the network above.
2. If the user says "somewhere hot/warm" or similar, pick the best 1-2 matching destinations for the current season (today is ${new Date().toISOString().slice(0, 10)}) and set "destination" to the top pick. List alternatives in "suggestions".
3. If the user mentions flight duration (e.g. "under 5 hours"), convert to minutes for maxDuration. Base estimates on flights FROM Scandinavian hubs.
4. If the user says "bonus tickets" or "bonus seats", set bonusOnly to true.
5. If the user is OK with stops or says "multiple stops", set maxStops to 2. If they want direct, set maxStops to 0. If not mentioned, leave null.
6. Default origin to "OSL" if not specified and the user seems Scandinavian/Norwegian.
7. For "cabin" — only set if the user explicitly mentions a class. Use "ANY" if not mentioned.
8. "reasoning" should be a short, helpful sentence explaining your interpretation. Be friendly and specific.
9. "suggestions" should list 2-4 alternative airport codes that also match the query well (e.g. other warm destinations).
10. For date-related queries like "next month", "this summer", "christmas", convert to approximate YYYY-MM-DD ranges.
11. maxPoints: only set if the user mentions a budget. Use the award chart to suggest realistic values.
`;

const responseSchema = {
  type: SchemaType.OBJECT as const,
  properties: {
    origin: { type: SchemaType.STRING as const, description: "IATA origin airport code", nullable: true },
    destination: { type: SchemaType.STRING as const, description: "IATA destination airport code", nullable: true },
    cabin: { type: SchemaType.STRING as const, description: "ECONOMY, PREMIUM, BUSINESS, or ANY", nullable: true },
    maxPoints: { type: SchemaType.INTEGER as const, description: "Maximum points budget", nullable: true },
    maxStops: { type: SchemaType.INTEGER as const, description: "Maximum number of stops (0=direct, null=any)", nullable: true },
    bonusOnly: { type: SchemaType.BOOLEAN as const, description: "Only show bonus/saver tickets", nullable: true },
    maxDuration: { type: SchemaType.INTEGER as const, description: "Max flight duration in minutes", nullable: true },
    dateFrom: { type: SchemaType.STRING as const, description: "Start date YYYY-MM-DD", nullable: true },
    dateTo: { type: SchemaType.STRING as const, description: "End date YYYY-MM-DD", nullable: true },
    reasoning: { type: SchemaType.STRING as const, description: "Friendly explanation of how the query was interpreted" },
    suggestions: {
      type: SchemaType.ARRAY as const,
      items: { type: SchemaType.STRING as const },
      description: "Alternative destination codes that also match the query",
    },
  },
  required: ["reasoning", "suggestions"],
};

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { mode, query } = body as { mode: string; query: string };

    if (mode === "parse") {
      // Check if API key is configured
      if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY) {
        // Fallback to basic pattern matching when no API key
        return NextResponse.json({ filters: fallbackParse(query), reasoning: null, suggestions: [] });
      }

      const model = genAI.getGenerativeModel({
        model: "gemini-3.1-flash-lite-preview",
        systemInstruction: SYSTEM_PROMPT,
        generationConfig: {
          responseMimeType: "application/json",
          responseSchema,
          temperature: 0.3,
          maxOutputTokens: 512,
        },
      });

      const result = await model.generateContent(query);
      const text = result.response.text();
      const parsed = JSON.parse(text);

      // Clean up: remove null/undefined/empty values from filters
      const filters: Record<string, unknown> = {};
      if (parsed.origin) filters.origin = parsed.origin;
      if (parsed.destination) filters.destination = parsed.destination;
      if (parsed.cabin && parsed.cabin !== "ANY") filters.cabin = parsed.cabin;
      if (parsed.maxPoints) filters.maxPoints = parsed.maxPoints;
      if (parsed.maxStops !== null && parsed.maxStops !== undefined) filters.maxStops = parsed.maxStops;
      if (parsed.bonusOnly) filters.bonusOnly = true;
      if (parsed.maxDuration) filters.maxDuration = parsed.maxDuration;
      if (parsed.dateFrom) filters.dateFrom = parsed.dateFrom;
      if (parsed.dateTo) filters.dateTo = parsed.dateTo;

      return NextResponse.json({
        filters,
        reasoning: parsed.reasoning || null,
        suggestions: parsed.suggestions || [],
      });
    }

    return NextResponse.json({ error: "Unknown mode" }, { status: 400 });
  } catch (e) {
    console.error("[AI] Gemini error:", e);
    // Fallback to basic parsing on any error
    try {
      const body = await req.clone().json().catch(() => ({ query: "" }));
      return NextResponse.json({ filters: fallbackParse(body.query || ""), reasoning: null, suggestions: [] });
    } catch {
      return NextResponse.json({ error: "AI unavailable" }, { status: 500 });
    }
  }
}

// Basic keyword fallback when Gemini is unavailable
function fallbackParse(query: string): Record<string, unknown> {
  const q = query.toLowerCase();
  const filters: Record<string, unknown> = {};

  if (q.includes("business")) filters.cabin = "BUSINESS";
  else if (q.includes("premium")) filters.cabin = "PREMIUM";
  else if (q.includes("economy")) filters.cabin = "ECONOMY";

  const destMap: Record<string, string> = {
    tokyo: "NRT", bangkok: "BKK", singapore: "SIN", osaka: "KIX",
    seoul: "ICN", shanghai: "PVG", beijing: "PEK", hanoi: "HAN",
    "ho chi minh": "SGN", "new york": "JFK", "los angeles": "LAX",
    miami: "MIA", london: "LHR", paris: "CDG", barcelona: "BCN",
    rome: "FCO", amsterdam: "AMS", istanbul: "IST", athens: "ATH",
    lisbon: "LIS", dubrovnik: "DBV", crete: "CHQ", malaga: "AGP",
  };
  for (const [keyword, code] of Object.entries(destMap)) {
    if (q.includes(keyword)) { filters.destination = code; break; }
  }

  const originMap: Record<string, string> = {
    oslo: "OSL", copenhagen: "CPH", stockholm: "ARN",
    paris: "CDG", amsterdam: "AMS", london: "LHR", frankfurt: "FRA",
    helsinki: "HEL", gothenburg: "GOT", bergen: "BGO",
  };
  for (const [keyword, code] of Object.entries(originMap)) {
    if (q.includes(keyword)) { filters.origin = code; break; }
  }

  const ptsMatch = q.match(/(\d+)\s*k?\s*(?:points|pts)/);
  if (ptsMatch) {
    let pts = parseInt(ptsMatch[1], 10);
    if (pts < 1000) pts *= 1000;
    filters.maxPoints = pts;
  }

  if (q.includes("direct") || q.includes("nonstop") || q.includes("non-stop")) filters.maxStops = 0;
  if (q.includes("bonus") || q.includes("saver")) filters.bonusOnly = true;

  return filters;
}
