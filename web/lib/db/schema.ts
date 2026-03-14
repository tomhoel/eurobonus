import {
  pgTable,
  uuid,
  text,
  timestamp,
  boolean,
  integer,
  serial,
  jsonb,
  date,
  uniqueIndex,
} from "drizzle-orm/pg-core";

// ── Users ────────────────────────────────────────────────────────────────────

export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: text("name"),
  email: text("email").unique().notNull(),
  emailVerified: timestamp("emailVerified", { mode: "date" }),
  image: text("image"),
  createdAt: timestamp("createdAt", { mode: "date" }).defaultNow().notNull(),
});

// ── NextAuth: Accounts ────────────────────────────────────────────────────────

export const accounts = pgTable("accounts", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  type: text("type").notNull(),
  provider: text("provider").notNull(),
  providerAccountId: text("providerAccountId").notNull(),
  refresh_token: text("refresh_token"),
  access_token: text("access_token"),
  expires_at: integer("expires_at"),
  token_type: text("token_type"),
  scope: text("scope"),
  id_token: text("id_token"),
  session_state: text("session_state"),
});

// ── NextAuth: Sessions ────────────────────────────────────────────────────────

export const sessions = pgTable("sessions", {
  sessionToken: text("sessionToken").primaryKey(),
  userId: uuid("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  expires: timestamp("expires", { mode: "date" }).notNull(),
});

// ── NextAuth: Verification Tokens ─────────────────────────────────────────────

export const verificationTokens = pgTable("verificationTokens", {
  identifier: text("identifier").notNull(),
  token: text("token").notNull(),
  expires: timestamp("expires", { mode: "date" }).notNull(),
});

// ── Route Subscriptions ───────────────────────────────────────────────────────

export const routeSubscriptions = pgTable("routeSubscriptions", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  origin: text("origin").notNull(),
  destination: text("destination").notNull(),
  cabinClass: text("cabinClass").default("any").notNull(),
  dateFrom: date("dateFrom"),
  dateTo: date("dateTo"),
  active: boolean("active").default(true).notNull(),
  createdAt: timestamp("createdAt", { mode: "date" }).defaultNow().notNull(),
});

// ── Availability Cache ────────────────────────────────────────────────────────

export const availabilityCache = pgTable(
  "availabilityCache",
  {
    id: serial("id").primaryKey(),
    origin: text("origin").notNull(),
    destination: text("destination").notNull(),
    date: date("date").notNull(),
    direction: text("direction").default("outbound").notNull(),
    economySeats: integer("economySeats"),
    premiumSeats: integer("premiumSeats"),
    businessSeats: integer("businessSeats"),
    isBonus: boolean("isBonus").default(false).notNull(),
    pointsEconomy: integer("pointsEconomy"),
    pointsPremium: integer("pointsPremium"),
    pointsBusiness: integer("pointsBusiness"),
    fetchedAt: timestamp("fetchedAt", { mode: "date" }).defaultNow().notNull(),
  },
  (table) => [
    uniqueIndex("availabilityCache_unique_idx").on(
      table.origin,
      table.destination,
      table.date,
      table.direction,
    ),
  ],
);

// ── Notifications ─────────────────────────────────────────────────────────────

export const notifications = pgTable("notifications", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("userId")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  subscriptionId: uuid("subscriptionId").references(
    () => routeSubscriptions.id,
    { onDelete: "set null" },
  ),
  type: text("type").notNull(),
  title: text("title").notNull(),
  body: text("body").notNull(),
  routeData: jsonb("routeData"),
  read: boolean("read").default(false).notNull(),
  emailed: boolean("emailed").default(false).notNull(),
  createdAt: timestamp("createdAt", { mode: "date" }).defaultNow().notNull(),
});

// ── SAS Sessions ──────────────────────────────────────────────────────────────

export const sasSessions = pgTable("sasSessions", {
  id: serial("id").primaryKey(),
  cookies: jsonb("cookies"),
  bearerToken: text("bearerToken"),
  expiresAt: timestamp("expiresAt", { mode: "date" }),
  refreshedAt: timestamp("refreshedAt", { mode: "date" }),
  status: text("status").default("expired").notNull(),
});
