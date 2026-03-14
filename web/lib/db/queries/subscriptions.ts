import { db } from "@/lib/db";
import { routeSubscriptions } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";

export async function getUserSubscriptions(userId: string) {
  return db
    .select()
    .from(routeSubscriptions)
    .where(eq(routeSubscriptions.userId, userId));
}

export async function createSubscription(data: {
  userId: string;
  origin: string;
  destination: string;
  cabinClass: string;
  dateFrom?: string;
  dateTo?: string;
}) {
  const [row] = await db
    .insert(routeSubscriptions)
    .values({
      userId: data.userId,
      origin: data.origin.toUpperCase(),
      destination: data.destination.toUpperCase(),
      cabinClass: data.cabinClass,
      dateFrom: data.dateFrom ?? null,
      dateTo: data.dateTo ?? null,
    })
    .returning();
  return row;
}

export async function deleteSubscription(id: string, userId: string) {
  const result = await db
    .delete(routeSubscriptions)
    .where(
      and(eq(routeSubscriptions.id, id), eq(routeSubscriptions.userId, userId)),
    );
  return result;
}

export async function getActiveSubscriptions() {
  return db
    .select()
    .from(routeSubscriptions)
    .where(eq(routeSubscriptions.active, true));
}

export async function getUniqueSubscribedRoutes(): Promise<
  { origin: string; destination: string }[]
> {
  const rows = await db
    .selectDistinct({
      origin: routeSubscriptions.origin,
      destination: routeSubscriptions.destination,
    })
    .from(routeSubscriptions)
    .where(eq(routeSubscriptions.active, true));
  return rows;
}
