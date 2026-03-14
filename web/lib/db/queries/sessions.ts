import { db } from "@/lib/db";
import { sasSessions } from "@/lib/db/schema";
import { desc, eq } from "drizzle-orm";

export async function getActiveSASSession() {
  const [row] = await db
    .select()
    .from(sasSessions)
    .where(eq(sasSessions.status, "active"))
    .orderBy(desc(sasSessions.refreshedAt))
    .limit(1);
  return row ?? null;
}

export async function markSessionExpired(id: number) {
  await db.update(sasSessions).set({ status: "expired" }).where(eq(sasSessions.id, id));
}
