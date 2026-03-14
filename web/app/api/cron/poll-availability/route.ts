import { NextRequest, NextResponse } from "next/server";
import { config } from "@/lib/config";
import { getAvailableDates } from "@/lib/sas/availability";
import { db } from "@/lib/db";
import { availabilityCache, notifications as notificationsTable, users } from "@/lib/db/schema";
import { getUniqueSubscribedRoutes, getActiveSubscriptions } from "@/lib/db/queries/subscriptions";
import { sql, eq, and as drizzleAnd, gte, lte } from "drizzle-orm";
import { sendAlertEmail } from "@/lib/email";
import { findAirport } from "@/lib/route-map";

export async function GET(req: NextRequest) {
  // Verify cron secret
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Merge base routes + subscribed routes
  const subscribedRoutes = await getUniqueSubscribedRoutes();
  const allRoutes = [...config.baseRoutes];
  for (const sr of subscribedRoutes) {
    if (!allRoutes.some((r) => r.origin === sr.origin && r.destination === sr.destination)) {
      allRoutes.push(sr);
    }
  }

  // Snapshot previous cache state before updating
  const previousCache = new Map<string, { economy: number; premium: number; business: number }>();
  const existingRows = await db.select().from(availabilityCache);
  for (const r of existingRows) {
    previousCache.set(`${r.origin}-${r.destination}-${r.date}`, {
      economy: r.economySeats ?? 0, premium: r.premiumSeats ?? 0, business: r.businessSeats ?? 0,
    });
  }

  let updated = 0;

  for (const route of allRoutes) {
    try {
      const dates = await getAvailableDates(route.origin, route.destination);

      for (const d of dates) {
        await db
          .insert(availabilityCache)
          .values({
            origin: route.origin,
            destination: route.destination,
            date: d.date,
            direction: "outbound",
            economySeats: d.economySeats,
            premiumSeats: d.premiumSeats,
            businessSeats: d.businessSeats,
            fetchedAt: new Date(),
          })
          .onConflictDoUpdate({
            target: [availabilityCache.origin, availabilityCache.destination, availabilityCache.date, availabilityCache.direction],
            set: {
              economySeats: sql`excluded.economy_seats`,
              premiumSeats: sql`excluded.premium_seats`,
              businessSeats: sql`excluded.business_seats`,
              fetchedAt: sql`excluded.fetched_at`,
            },
          });
        updated++;
      }

      // Rate limit between routes
      await new Promise((r) => setTimeout(r, config.rateLimitMs));
    } catch (err) {
      console.error(`[Cron] Failed to poll ${route.origin}-${route.destination}:`, err);
    }
  }

  // After the cache update loop, check for NEW availability and send alerts
  const subs = await getActiveSubscriptions();
  for (const sub of subs) {
    // Build conditions including date range filter
    const conditions = [
      eq(availabilityCache.origin, sub.origin),
      eq(availabilityCache.destination, sub.destination),
      sql`(${availabilityCache.economySeats} > 0 OR ${availabilityCache.premiumSeats} > 0 OR ${availabilityCache.businessSeats} > 0)`,
    ];
    // Filter by subscription date range if specified
    if (sub.dateFrom) conditions.push(gte(availabilityCache.date, sub.dateFrom));
    if (sub.dateTo) conditions.push(lte(availabilityCache.date, sub.dateTo));

    const matchingRows = await db
      .select()
      .from(availabilityCache)
      .where(drizzleAnd(...conditions));

    for (const row of matchingRows) {
      const seats =
        sub.cabinClass === "economy" ? (row.economySeats ?? 0) :
        sub.cabinClass === "premium" ? (row.premiumSeats ?? 0) :
        sub.cabinClass === "business" ? (row.businessSeats ?? 0) :
        (row.economySeats ?? 0) + (row.premiumSeats ?? 0) + (row.businessSeats ?? 0);

      if (seats <= 0) continue;

      // Check if this is genuinely NEW availability (was 0 before, now > 0)
      const prev = previousCache.get(`${row.origin}-${row.destination}-${row.date}`);
      const prevSeats = prev
        ? (sub.cabinClass === "economy" ? prev.economy :
           sub.cabinClass === "premium" ? prev.premium :
           sub.cabinClass === "business" ? prev.business :
           prev.economy + prev.premium + prev.business)
        : 0;

      // Only alert if seats are genuinely new (were 0 or didn't exist before)
      if (prevSeats > 0) continue;

      // Also check we haven't already notified for this exact route+date
      const existing = await db
        .select()
        .from(notificationsTable)
        .where(
          drizzleAnd(
            eq(notificationsTable.userId, sub.userId),
            eq(notificationsTable.subscriptionId, sub.id),
            sql`route_data->>'date' = ${row.date}`,
          ),
        )
        .limit(1);

      if (existing.length > 0) continue;

      const orig = findAirport(row.origin);
      const dest = findAirport(row.destination);
      const cabin = sub.cabinClass === "any" ? "Award" : sub.cabinClass;

      // Create notification
      await db.insert(notificationsTable).values({
        userId: sub.userId,
        subscriptionId: sub.id,
        type: "new_seats",
        title: `${cabin} seats: ${orig?.name ?? row.origin} → ${dest?.name ?? row.destination}`,
        body: `${seats} ${cabin} bonus seats on ${row.date}`,
        routeData: { origin: row.origin, destination: row.destination, date: row.date, seats },
        emailed: false,
      });

      // Send email
      try {
        const [user] = await db.select().from(users).where(eq(users.id, sub.userId)).limit(1);
        if (user?.email) {
          await sendAlertEmail({
            to: user.email,
            origin: row.origin,
            originName: orig?.name ?? row.origin,
            destination: row.destination,
            destinationName: dest?.name ?? row.destination,
            date: row.date,
            cabinClass: cabin,
            seats,
          });
        }
      } catch (err) {
        console.error(`[Cron] Failed to send email for sub ${sub.id}:`, err);
      }
    }
  }

  return NextResponse.json({ ok: true, routes: allRoutes.length, updated });
}
