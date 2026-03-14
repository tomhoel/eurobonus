/**
 * Application configuration.
 * All polling behavior is controlled here — change schedules,
 * routes, and trigger logic without touching code elsewhere.
 */

export const config = {
  /** Default market for SAS API */
  market: "no-no",
  pos: "no",

  /** Cron schedules (Vercel cron expression) */
  cron: {
    pollAvailability: "*/30 * * * *",  // Every 30 minutes
    verifyBonus: "0 */2 * * *",        // Every 2 hours
    refreshSession: "0 */6 * * *",     // Every 6 hours
  },

  /** Rate limiting between SAS API calls (ms) */
  rateLimitMs: 3000,

  /**
   * Base routes to always poll for the deals page,
   * regardless of subscriptions. Add or remove freely.
   */
  baseRoutes: [
    { origin: "OSL", destination: "BKK" },
    { origin: "OSL", destination: "NRT" },
    { origin: "CPH", destination: "BKK" },
    { origin: "CPH", destination: "NRT" },
    { origin: "ARN", destination: "BKK" },
  ] as { origin: string; destination: string }[],

  /**
   * How many months ahead to scan from today.
   */
  scanMonthsAhead: 6,

  /** Notification types that trigger alerts */
  alertTriggers: ["new_seats", "seats_vanishing"] as string[],
} as const;
