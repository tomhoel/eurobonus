import { db } from "@/lib/db";
import { availabilityCache } from "@/lib/db/schema";
import { desc, gt, sql, and, eq } from "drizzle-orm";

export async function getBestDeals(
  options: { cabinFilter?: string; limit?: number } = {},
) {
  const { cabinFilter, limit = 20 } = options;

  // Build WHERE conditions
  const conditions = [];
  if (cabinFilter === "economy")
    conditions.push(gt(availabilityCache.economySeats, 0));
  else if (cabinFilter === "premium")
    conditions.push(gt(availabilityCache.premiumSeats, 0));
  else if (cabinFilter === "business")
    conditions.push(gt(availabilityCache.businessSeats, 0));
  else {
    // Any cabin with seats
    conditions.push(
      sql`(${availabilityCache.economySeats} > 0 OR ${availabilityCache.premiumSeats} > 0 OR ${availabilityCache.businessSeats} > 0)`,
    );
  }

  conditions.push(eq(availabilityCache.direction, "outbound"));

  const rows = await db
    .select()
    .from(availabilityCache)
    .where(and(...conditions))
    .orderBy(
      desc(availabilityCache.businessSeats),
      desc(availabilityCache.fetchedAt),
    )
    .limit(limit);

  return rows;
}
