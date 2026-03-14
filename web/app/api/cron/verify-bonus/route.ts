import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { availabilityCache } from "@/lib/db/schema";
import { getActiveSession } from "@/lib/sas/session";
import { getOffersWithPoints } from "@/lib/sas/offers";
import { and, gt, eq, or } from "drizzle-orm";
import { config } from "@/lib/config";

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const session = await getActiveSession();
  if (!session) {
    return NextResponse.json({ ok: false, reason: "No active SAS session" });
  }

  // Find cached entries that have seats but haven't been verified
  const candidates = await db
    .select()
    .from(availabilityCache)
    .where(
      and(
        eq(availabilityCache.isBonus, false),
        or(
          gt(availabilityCache.economySeats, 0),
          gt(availabilityCache.premiumSeats, 0),
          gt(availabilityCache.businessSeats, 0),
        ),
      ),
    )
    .limit(10);

  let verified = 0;

  for (const row of candidates) {
    try {
      const offers = await getOffersWithPoints(row.origin, row.destination, row.date, {
        cookies: session.cookies,
        sessionId: session.sessionId,
        bearerToken: session.bearerToken,
      });

      const bonusOffers = offers.filter((o) => o.isBonusTicket);
      const hasBonusEconomy = bonusOffers.some((o) => o.cabinClass === "ECONOMY");
      const hasBonusPremium = bonusOffers.some((o) => o.cabinClass === "PREMIUM");
      const hasBonusBusiness = bonusOffers.some((o) => o.cabinClass === "BUSINESS");

      const economyPts = bonusOffers.find((o) => o.cabinClass === "ECONOMY")?.points ?? null;
      const premiumPts = bonusOffers.find((o) => o.cabinClass === "PREMIUM")?.points ?? null;
      const businessPts = bonusOffers.find((o) => o.cabinClass === "BUSINESS")?.points ?? null;

      await db
        .update(availabilityCache)
        .set({
          isBonus: hasBonusEconomy || hasBonusPremium || hasBonusBusiness,
          pointsEconomy: economyPts,
          pointsPremium: premiumPts,
          pointsBusiness: businessPts,
        })
        .where(eq(availabilityCache.id, row.id));

      verified++;
      await new Promise((r) => setTimeout(r, config.rateLimitMs));
    } catch (err) {
      console.error(`[Cron] Failed to verify ${row.origin}-${row.destination} ${row.date}:`, err);
    }
  }

  return NextResponse.json({ ok: true, verified });
}
