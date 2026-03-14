import { db } from "@/lib/db";
import { sasSessions } from "@/lib/db/schema";
import { desc, eq } from "drizzle-orm";

export interface SASSession {
  cookies: string;
  bearerToken: string;
  sessionId: string;
}

/**
 * Get the current active SAS session from DB.
 * Returns null if no active session exists.
 */
export async function getActiveSession(): Promise<SASSession | null> {
  const [row] = await db
    .select()
    .from(sasSessions)
    .where(eq(sasSessions.status, "active"))
    .orderBy(desc(sasSessions.refreshedAt))
    .limit(1);

  if (!row || !row.bearerToken) return null;

  // Check expiry
  if (row.expiresAt && new Date(row.expiresAt) < new Date()) {
    await db.update(sasSessions).set({ status: "expired" }).where(eq(sasSessions.id, row.id));
    return null;
  }

  const cookieObj = (row.cookies ?? {}) as Record<string, string>;
  const cookieStr = Object.entries(cookieObj).map(([k, v]) => `${k}=${v}`).join("; ");

  return {
    cookies: cookieStr,
    bearerToken: row.bearerToken,
    sessionId: cookieObj.session_id ?? "",
  };
}

/**
 * Refresh the SAS session using Browserbase.
 * This launches a remote browser, navigates to sas.no, bypasses Cloudflare,
 * and harvests auth tokens.
 *
 * TODO: Implement Browserbase integration. For now, sessions must be
 * inserted manually into the sas_sessions table.
 */
export async function refreshSession(): Promise<boolean> {
  // Browserbase integration placeholder
  // When implemented:
  // 1. Connect to Browserbase API
  // 2. Launch Chrome session
  // 3. Navigate to sas.no/award-finder
  // 4. Wait for Cloudflare to pass
  // 5. Intercept auth tokens via CDP
  // 6. Store in DB
  console.warn("[SAS Session] Browserbase integration not yet configured. Insert sessions manually.");
  return false;
}
