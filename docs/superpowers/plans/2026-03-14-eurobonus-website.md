# EuroBonus Award Finder Website — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished Next.js website for searching SAS EuroBonus award flights, browsing deals, and receiving email alerts when bonus seats open up.

**Architecture:** Single Next.js 15 app (App Router) with TypeScript throughout. SAS API client rewritten from Python. PostgreSQL on Neon for data. NextAuth for Google sign-in. Vercel cron jobs for background polling. Resend for email. Browserbase for Cloudflare session capture.

**Tech Stack:** Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, Drizzle ORM, Neon PostgreSQL, NextAuth.js, Resend, Browserbase

**Spec:** `docs/superpowers/specs/2026-03-14-eurobonus-award-finder-website-design.md`

**Existing reference code:** `sas_search_api.py` (Python API client to port), `SAS_API_DOCUMENTATION.md` (full API reference)

---

## File Structure

```
app/
├── layout.tsx                    # Root layout, font, theme provider
├── page.tsx                      # Landing page (/)
├── globals.css                   # Tailwind base + custom vars
├── search/
│   └── page.tsx                  # Search results page
├── deals/
│   └── page.tsx                  # Deals overview page
├── alerts/
│   └── page.tsx                  # Alert subscriptions (protected)
├── notifications/
│   └── page.tsx                  # Notification history (protected)
├── settings/
│   └── page.tsx                  # User settings (protected)
├── api/
│   ├── auth/[...nextauth]/
│   │   └── route.ts              # NextAuth route handler
│   ├── search/
│   │   └── route.ts              # Search API endpoint
│   ├── deals/
│   │   └── route.ts              # Deals API endpoint
│   ├── alerts/
│   │   └── route.ts              # CRUD for subscriptions
│   ├── notifications/
│   │   └── route.ts              # Notification list + mark read
│   └── cron/
│       ├── poll-availability/
│       │   └── route.ts          # Cron: poll SAS calendar
│       ├── verify-bonus/
│       │   └── route.ts          # Cron: verify bonus seats
│       └── refresh-session/
│           └── route.ts          # Cron: refresh SAS session
lib/
├── sas/
│   ├── types.ts                  # Shared SAS types
│   ├── client.ts                 # Base HTTP client (rate limit, retry, headers)
│   ├── availability.ts           # /bff/award-finder/destinations/v1
│   ├── routes.ts                 # /bff/award-finder/routes/v1
│   ├── offers.ts                 # /api/offers/flights (needs auth)
│   ├── partners.ts               # /award-api/flights
│   └── session.ts                # Browserbase session capture
├── db/
│   ├── schema.ts                 # Drizzle schema (all tables)
│   ├── index.ts                  # DB connection singleton
│   ├── queries/
│   │   ├── availability.ts       # Availability cache queries
│   │   ├── subscriptions.ts      # Route subscription queries
│   │   ├── notifications.ts      # Notification queries
│   │   └── sessions.ts           # SAS session queries
├── auth.ts                       # NextAuth config
├── email.ts                      # Resend email helper
├── config.ts                     # App config (polling schedules, routes, etc.)
└── route-map.ts                  # Airport data (from sas_route_map.json)
components/
├── ui/                           # shadcn/ui components (auto-generated)
├── search-form.tsx               # Origin/dest/month search form
├── availability-calendar.tsx     # Calendar grid showing seat counts
├── flight-card.tsx               # Single flight result card
├── deal-card.tsx                 # Deal summary card
├── alert-form.tsx                # Add/edit alert subscription form
├── notification-item.tsx         # Single notification row
├── nav.tsx                       # Top navigation bar
├── user-menu.tsx                 # Auth state + user avatar dropdown
└── providers.tsx                 # Session provider wrapper
types/
└── next-auth.d.ts                # Extend NextAuth Session type with user.id
```

---

## Chunk 1: Project Scaffolding & Infrastructure

### Task 1: Initialize Next.js project

**Files:**
- Create: `package.json`, `tsconfig.json`, `next.config.ts`, `tailwind.config.ts`, `app/layout.tsx`, `app/page.tsx`, `app/globals.css`

- [ ] **Step 1: Create Next.js app**

```bash
cd C:\Users\tomho\eurobonus
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir=false --import-alias="@/*" --use-npm
```

This creates a `web/` subdirectory. We build the website there, keeping the existing Python files at root for reference during porting.

- [ ] **Step 2: Install core dependencies**

```bash
cd web
npm install drizzle-orm @neondatabase/serverless next-auth@beta @auth/drizzle-adapter
npm install resend
npm install -D drizzle-kit
```

- [ ] **Step 3: Install shadcn/ui**

```bash
npx shadcn@latest init
```

Select: New York style, Zinc base color, CSS variables = yes.

- [ ] **Step 4: Add essential shadcn components**

```bash
npx shadcn@latest add button card input select badge table dialog dropdown-menu avatar separator tabs toast
```

- [ ] **Step 5: Configure Tailwind theme with Nordic Clean palette**

Update `tailwind.config.ts` to extend the default theme:

```ts
// In the theme.extend section, add:
colors: {
  brand: {
    50: '#eef2ff',
    100: '#e0e7ff',
    500: '#6366f1',
    600: '#4f46e5',
    700: '#4338ca',
  },
},
```

- [ ] **Step 6: Create environment variables file**

Create `web/.env.local`:

```env
# Database
DATABASE_URL=

# Auth
AUTH_SECRET=
AUTH_GOOGLE_ID=
AUTH_GOOGLE_SECRET=

# Email
RESEND_API_KEY=

# Browserbase
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=

# Cron security
CRON_SECRET=
```

Create `web/.env.example` with the same keys but empty values.

- [ ] **Step 7: Commit**

```bash
git add web/
git commit -m "feat: scaffold Next.js project with Tailwind, shadcn/ui, and dependencies"
```

---

### Task 2: Database schema with Drizzle

**Files:**
- Create: `web/lib/db/schema.ts`, `web/lib/db/index.ts`, `web/drizzle.config.ts`

- [ ] **Step 1: Write Drizzle schema**

Create `web/lib/db/schema.ts`:

```ts
import { pgTable, uuid, text, timestamp, boolean, integer, serial, jsonb, date, uniqueIndex } from "drizzle-orm/pg-core";

// NextAuth required tables
export const users = pgTable("users", {
  id: uuid("id").defaultRandom().primaryKey(),
  name: text("name"),
  email: text("email").unique().notNull(),
  emailVerified: timestamp("email_verified", { mode: "date" }),
  image: text("image"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const accounts = pgTable("accounts", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  type: text("type").notNull(),
  provider: text("provider").notNull(),
  providerAccountId: text("provider_account_id").notNull(),
  refreshToken: text("refresh_token"),
  accessToken: text("access_token"),
  expiresAt: integer("expires_at"),
  tokenType: text("token_type"),
  scope: text("scope"),
  idToken: text("id_token"),
  sessionState: text("session_state"),
});

export const sessions = pgTable("sessions", {
  sessionToken: text("session_token").primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  expires: timestamp("expires", { mode: "date" }).notNull(),
});

export const verificationTokens = pgTable("verification_tokens", {
  identifier: text("identifier").notNull(),
  token: text("token").notNull(),
  expires: timestamp("expires", { mode: "date" }).notNull(),
});

// App tables
export const routeSubscriptions = pgTable("route_subscriptions", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  origin: text("origin").notNull(),
  destination: text("destination").notNull(),
  cabinClass: text("cabin_class").notNull().default("any"),
  dateFrom: date("date_from"),
  dateTo: date("date_to"),
  active: boolean("active").notNull().default(true),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const availabilityCache = pgTable("availability_cache", {
  id: serial("id").primaryKey(),
  origin: text("origin").notNull(),
  destination: text("destination").notNull(),
  date: date("date").notNull(),
  direction: text("direction").notNull().default("outbound"),
  economySeats: integer("economy_seats").notNull().default(0),
  premiumSeats: integer("premium_seats").notNull().default(0),
  businessSeats: integer("business_seats").notNull().default(0),
  isBonus: boolean("is_bonus").default(false),
  pointsEconomy: integer("points_economy"),
  pointsPremium: integer("points_premium"),
  pointsBusiness: integer("points_business"),
  fetchedAt: timestamp("fetched_at").defaultNow().notNull(),
}, (table) => [
  uniqueIndex("avail_unique").on(table.origin, table.destination, table.date, table.direction),
]);

export const notifications = pgTable("notifications", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  subscriptionId: uuid("subscription_id").references(() => routeSubscriptions.id, { onDelete: "set null" }),
  type: text("type").notNull(),
  title: text("title").notNull(),
  body: text("body").notNull(),
  routeData: jsonb("route_data"),
  read: boolean("read").notNull().default(false),
  emailed: boolean("emailed").notNull().default(false),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export const sasSessions = pgTable("sas_sessions", {
  id: serial("id").primaryKey(),
  cookies: jsonb("cookies"),
  bearerToken: text("bearer_token"),
  expiresAt: timestamp("expires_at"),
  refreshedAt: timestamp("refreshed_at").defaultNow(),
  status: text("status").notNull().default("expired"),
});
```

- [ ] **Step 2: Write DB connection**

Create `web/lib/db/index.ts`:

```ts
import { neon } from "@neondatabase/serverless";
import { drizzle } from "drizzle-orm/neon-http";
import * as schema from "./schema";

const sql = neon(process.env.DATABASE_URL!);
export const db = drizzle(sql, { schema });
```

- [ ] **Step 3: Write Drizzle config**

Create `web/drizzle.config.ts`:

```ts
import { defineConfig } from "drizzle-kit";

export default defineConfig({
  schema: "./lib/db/schema.ts",
  out: "./drizzle",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
```

- [ ] **Step 4: Commit**

```bash
git add web/lib/db/ web/drizzle.config.ts
git commit -m "feat: add Drizzle schema for users, subscriptions, availability, notifications"
```

---

### Task 3: Auth with NextAuth + Google

**Files:**
- Create: `web/lib/auth.ts`, `web/app/api/auth/[...nextauth]/route.ts`, `web/components/providers.tsx`, `web/components/user-menu.tsx`

- [ ] **Step 1: Write NextAuth config**

Create `web/lib/auth.ts`:

```ts
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import { DrizzleAdapter } from "@auth/drizzle-adapter";
import { db } from "./db";

export const { handlers, auth, signIn, signOut } = NextAuth({
  adapter: DrizzleAdapter(db),
  providers: [
    Google({
      clientId: process.env.AUTH_GOOGLE_ID!,
      clientSecret: process.env.AUTH_GOOGLE_SECRET!,
    }),
  ],
  pages: {
    signIn: "/",
  },
});
```

- [ ] **Step 2: Write route handler**

Create `web/app/api/auth/[...nextauth]/route.ts`:

```ts
import { handlers } from "@/lib/auth";
export const { GET, POST } = handlers;
```

- [ ] **Step 3: Write session provider**

Create `web/components/providers.tsx`:

```tsx
"use client";
import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
```

- [ ] **Step 4: Write user menu component**

Create `web/components/user-menu.tsx`:

```tsx
"use client";
import { useSession, signIn, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function UserMenu() {
  const { data: session } = useSession();

  if (!session) {
    return (
      <Button variant="outline" onClick={() => signIn("google")}>
        Sign in
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Avatar className="h-8 w-8 cursor-pointer">
          <AvatarImage src={session.user?.image ?? undefined} />
          <AvatarFallback>{session.user?.name?.[0] ?? "U"}</AvatarFallback>
        </Avatar>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild><a href="/alerts">My Alerts</a></DropdownMenuItem>
        <DropdownMenuItem asChild><a href="/notifications">Notifications</a></DropdownMenuItem>
        <DropdownMenuItem asChild><a href="/settings">Settings</a></DropdownMenuItem>
        <DropdownMenuItem onClick={() => signOut()}>Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

- [ ] **Step 5: Write nav component**

Create `web/components/nav.tsx`:

```tsx
import Link from "next/link";
import { UserMenu } from "./user-menu";

export function Nav() {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-sm font-semibold tracking-tight text-indigo-600">
            Award Finder
          </Link>
          <nav className="hidden gap-4 sm:flex">
            <Link href="/search" className="text-sm text-muted-foreground hover:text-foreground">Search</Link>
            <Link href="/deals" className="text-sm text-muted-foreground hover:text-foreground">Deals</Link>
          </nav>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
```

- [ ] **Step 6: Update root layout**

Update `web/app/layout.tsx` to wrap with providers and include nav:

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Nav } from "@/components/nav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "EuroBonus Award Finder",
  description: "Find SAS EuroBonus bonus ticket availability",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 antialiased`}>
        <Providers>
          <Nav />
          <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add web/lib/auth.ts web/app/api/auth/ web/components/ web/app/layout.tsx
git commit -m "feat: add NextAuth with Google provider, nav, and user menu"
```

---

## Chunk 2: SAS API Client (TypeScript Port)

### Task 4: Types and base HTTP client

**Files:**
- Create: `web/lib/sas/types.ts`, `web/lib/sas/client.ts`

- [ ] **Step 1: Write shared types**

Create `web/lib/sas/types.ts` — port from Python dataclasses in `sas_search_api.py`:

```ts
export type CabinCode = "AG" | "AP" | "AB";
export type CabinName = "ECONOMY" | "PREMIUM" | "BUSINESS";

export const CABIN_CODE_TO_NAME: Record<CabinCode, CabinName> = {
  AG: "ECONOMY", AP: "PREMIUM", AB: "BUSINESS",
};
export const CABIN_NAME_TO_CODE: Record<CabinName, CabinCode> = {
  ECONOMY: "AG", PREMIUM: "AP", BUSINESS: "AB",
};

export interface FlightSegment {
  flightNumber: string;
  carrier: string;
  carrierName: string;
  departureAirport: string;
  arrivalAirport: string;
  departureTime: string;
  arrivalTime: string;
  departureDate: string;
  arrivalDate: string;
  aircraft: string;
  durationMinutes: number;
}

export interface FlightOffer {
  origin: string;
  destination: string;
  date: string;
  cabinClass: CabinName;
  productName: string;
  points: number;
  taxes: number;
  currency: string;
  availableSeats: number;
  bookingClass: string;
  segments: FlightSegment[];
  totalDurationMinutes: number;
  stops: number;
  flightId: string;
  isBonusTicket: boolean;
  basePrice: number;
}

export interface AvailabilityDate {
  date: string;
  economySeats: number;
  premiumSeats: number;
  businessSeats: number;
}

export interface AvailabilityDestination {
  iataCode: string;
  cityName: string;
  outbound: AvailabilityDate[];
  inbound: AvailabilityDate[];
}

export interface RouteInfo {
  flightId: string;
  departureDate: string;
  departureTime: string;
  arrivalDate: string;
  arrivalTime: string;
  flyTimeMinutes: number;
  totalTimeMinutes: number;
  numFlights: number;
  haulType: string;
  availability: Record<string, number>;
}

export interface PartnerCabin {
  cabin: CabinName;
  points: number;
  cash: number;
  seats: number;
}

export interface PartnerFlight {
  date: string;
  departureTime: string;
  arrivalTime: string;
  origin: string;
  destination: string;
  route: string;
  carriers: string[];
  carrierNames: string[];
  stops: number;
  totalDurationMinutes: number;
  cabins: PartnerCabin[];
}
```

- [ ] **Step 2: Write base HTTP client**

Create `web/lib/sas/client.ts` — port rate limiting, retry, UA rotation from `sas_search_api.py`:

```ts
const USER_AGENTS = [
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
];

function randomUA(): string {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface SASClientOptions {
  market?: string;
  pos?: string;
  cookies?: string;
  sessionId?: string;
  bearerToken?: string;
}

export async function sasRequest<T = unknown>(
  url: string,
  params: Record<string, string | number | boolean>,
  options: SASClientOptions = {},
): Promise<T | null> {
  const { market = "no-no", cookies, sessionId, bearerToken } = options;
  const maxRetries = 3;

  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  }
  const fullUrl = `${url}?${qs.toString()}`;

  const headers: Record<string, string> = {
    Accept: "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": randomUA(),
  };
  if (cookies) headers["Cookie"] = cookies;
  if (sessionId) headers["sas-user-session-id"] = sessionId;
  if (bearerToken) headers["Authorization"] = `Bearer ${bearerToken}`;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await fetch(fullUrl, { headers, signal: AbortSignal.timeout(30_000) });

      if (res.status === 429) {
        const wait = Math.pow(2, attempt + 1) * 1000;
        console.warn(`[SAS] Rate limited, waiting ${wait}ms`);
        await sleep(wait);
        continue;
      }

      if (!res.ok) {
        console.error(`[SAS] ${url} returned ${res.status}`);
        return null;
      }

      return (await res.json()) as T;
    } catch (err) {
      if (attempt < maxRetries - 1) {
        const wait = Math.pow(2, attempt) * 1000;
        console.warn(`[SAS] Request failed, retrying in ${wait}ms`, err);
        await sleep(wait);
      } else {
        console.error(`[SAS] Request failed after ${maxRetries} retries`, err);
        return null;
      }
    }
  }
  return null;
}
```

- [ ] **Step 3: Commit**

```bash
git add web/lib/sas/types.ts web/lib/sas/client.ts
git commit -m "feat: add SAS API types and base HTTP client with retry/rate-limiting"
```

---

### Task 5: Availability and routes endpoints

**Files:**
- Create: `web/lib/sas/availability.ts`, `web/lib/sas/routes.ts`

- [ ] **Step 1: Write availability module**

Create `web/lib/sas/availability.ts` — port `get_availability_calendar` and `get_available_dates` from `sas_search_api.py`:

```ts
import { sasRequest, type SASClientOptions } from "./client";
import type { AvailabilityDate, AvailabilityDestination } from "./types";

const DESTINATIONS_URL = "https://www.sas.no/bff/award-finder/destinations/v1";

export async function getAvailabilityCalendar(
  origin: string,
  destination: string = "",
  options: {
    month?: string;
    passengers?: number;
    direct?: boolean;
    cabinClass?: string;
  } & SASClientOptions = {},
): Promise<AvailabilityDestination[]> {
  const { month = "", passengers = 1, direct = false, cabinClass = "", ...clientOpts } = options;

  const raw = await sasRequest<any[]>(DESTINATIONS_URL, {
    market: clientOpts.market ?? "no-no",
    origin,
    destinations: destination,
    selectedMonth: month,
    passengers,
    direct: String(direct),
    availability: "true",
    selectedFlightClass: cabinClass,
  }, clientOpts);

  if (!raw || !Array.isArray(raw)) return [];

  return raw.map((dest) => {
    const avail = dest.availability ?? {};
    const parseDay = (day: any): AvailabilityDate => ({
      date: day.date ?? "",
      economySeats: Number(day.AG ?? 0),
      premiumSeats: Number(day.AP ?? 0),
      businessSeats: Number(day.AB ?? 0),
    });

    return {
      iataCode: dest.airportCode ?? dest.iataCode ?? "",
      cityName: dest.cityName ?? "",
      outbound: (avail.outbound ?? []).map(parseDay),
      inbound: (avail.inbound ?? []).map(parseDay),
    };
  });
}

export async function getAvailableDates(
  origin: string,
  destination: string,
  options: { month?: string; cabinClass?: string } & SASClientOptions = {},
): Promise<AvailabilityDate[]> {
  const results = await getAvailabilityCalendar(origin, destination, options);
  const match = results.find((d) => d.iataCode === destination);
  return match?.outbound ?? [];
}
```

- [ ] **Step 2: Write routes module**

Create `web/lib/sas/routes.ts` — port `get_route_details` from `sas_search_api.py`:

```ts
import { sasRequest, type SASClientOptions } from "./client";
import type { RouteInfo } from "./types";

const ROUTES_URL = "https://www.sas.no/bff/award-finder/routes/v1";

export async function getRouteDetails(
  origin: string,
  destination: string,
  departureDate: string,
  options: { direct?: boolean } & SASClientOptions = {},
): Promise<RouteInfo[]> {
  const { direct = false, ...clientOpts } = options;

  const raw = await sasRequest<any[]>(ROUTES_URL, {
    market: clientOpts.market ?? "no-no",
    origin,
    destination,
    departureDate,
    direct: String(direct),
  }, clientOpts);

  if (!raw || !Array.isArray(raw)) return [];

  return raw.map((item) => ({
    flightId: item.flightId ?? "",
    departureDate: item.departureDate ?? "",
    departureTime: item.departureTime ?? "",
    arrivalDate: item.arrivalDate ?? "",
    arrivalTime: item.arrivalTime ?? "",
    flyTimeMinutes: item.flyTime ?? 0,
    totalTimeMinutes: item.totalTime ?? 0,
    numFlights: item.noOfFlights ?? 1,
    haulType: item.haulType ?? "",
    availability: item.availability ?? {},
  }));
}
```

- [ ] **Step 3: Commit**

```bash
git add web/lib/sas/availability.ts web/lib/sas/routes.ts
git commit -m "feat: add availability calendar and routes endpoints"
```

---

### Task 6: Offers and partners endpoints

**Files:**
- Create: `web/lib/sas/offers.ts`, `web/lib/sas/partners.ts`

- [ ] **Step 1: Write offers module**

Create `web/lib/sas/offers.ts` — port `get_offers_with_points`, `_parse_offers`, and bonus detection from `sas_search_api.py`:

```ts
import { sasRequest, type SASClientOptions } from "./client";
import type { FlightOffer, FlightSegment } from "./types";

const OFFERS_URL = "https://www.sas.no/api/offers/flights";

export async function getOffersWithPoints(
  origin: string,
  destination: string,
  date: string,
  options: {
    adults?: number;
    bookingFlow?: string;
  } & SASClientOptions = {},
): Promise<FlightOffer[]> {
  const { adults = 1, bookingFlow = "points", ...clientOpts } = options;

  // Normalize date to YYYYMMDD
  const outDate = date.replace(/-/g, "");

  const raw = await sasRequest<any>(OFFERS_URL, {
    from: origin,
    to: destination,
    outDate,
    adt: adults,
    bookingFlow,
    pos: clientOpts.pos ?? "no",
    channel: "web",
    displayType: "upsell",
  }, clientOpts);

  if (!raw) return [];
  return parseOffers(raw, origin, destination, date);
}

function parseOffers(data: any, origin: string, destination: string, date: string): FlightOffer[] {
  const offers: FlightOffer[] = [];
  // Normalize date
  const normalDate = date.includes("-") ? date : `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`;

  const outboundFlights = data.outboundFlights ?? {};
  const flights = typeof outboundFlights === "object" && !Array.isArray(outboundFlights)
    ? Object.entries(outboundFlights)
    : [];

  for (const [flightKey, flightData] of flights) {
    if (typeof flightData !== "object" || !flightData) continue;
    const fd = flightData as any;

    // Parse segments
    const segments: FlightSegment[] = (fd.segments ?? []).map((seg: any) => {
      const depAir = typeof seg.departureAirport === "object" ? seg.departureAirport?.code : seg.departureAirport;
      const arrAir = typeof seg.arrivalAirport === "object" ? seg.arrivalAirport?.code : seg.arrivalAirport;
      const carrier = typeof seg.carrier === "object" ? seg.carrier?.code : seg.carrier;
      const mc = typeof seg.marketingCarrier === "object" ? seg.marketingCarrier : {};
      const ac = typeof seg.airCraft === "object" ? seg.airCraft?.name : String(seg.airCraft ?? "");
      const durRaw = seg.duration;
      let durMins = 0;
      if (typeof durRaw === "string" && durRaw.includes(":")) {
        const [h, m] = durRaw.split(":");
        durMins = Number(h) * 60 + Number(m);
      } else {
        durMins = Number(durRaw ?? 0);
      }

      return {
        flightNumber: seg.flightNumber ?? "",
        carrier: carrier ?? "",
        carrierName: mc.name ?? "",
        departureAirport: depAir ?? "",
        arrivalAirport: arrAir ?? "",
        departureTime: seg.departureTime ?? "",
        arrivalTime: seg.arrivalTime ?? "",
        departureDate: seg.departureDate ?? normalDate,
        arrivalDate: seg.arrivalDate ?? normalDate,
        aircraft: ac,
        durationMinutes: durMins,
      };
    });

    const totalDuration = segments.reduce((sum, s) => sum + s.durationMinutes, 0);
    const stops = Math.max(0, segments.length - 1);

    // Parse cabins -> products
    const cabins = fd.cabins ?? {};
    const cabinEntries = typeof cabins === "object" && !Array.isArray(cabins)
      ? Object.entries(cabins)
      : [];

    for (const [cabinKey, cabinVal] of cabinEntries) {
      if (typeof cabinVal !== "object" || !cabinVal) continue;
      const cv = cabinVal as any;
      const cabinClass = cv.cabinClass ?? cabinKey;

      // Collect products from various nesting patterns
      const products: any[] = [];
      if (cv.products) {
        if (Array.isArray(cv.products)) products.push(...cv.products);
        else if (typeof cv.products === "object") products.push(...Object.values(cv.products));
      } else {
        // Check nested sub-objects
        for (const sub of Object.values(cv)) {
          if (typeof sub === "object" && sub && (sub as any).products) {
            const p = (sub as any).products;
            if (Array.isArray(p)) products.push(...p);
            else if (typeof p === "object") products.push(...Object.values(p));
          }
        }
      }

      for (const product of products) {
        if (typeof product !== "object" || !product) continue;
        const price = product.price ?? {};
        const fares = Array.isArray(product.fares) ? product.fares : [];
        const seats = fares[0]?.avlSeats ?? 0;
        const bookingClass = fares[0]?.bookingClass ?? "";
        const isBonusTicket = product.isStandardAward === true || (price.basePrice === 0 && price.points > 0);

        if (price.points) {
          offers.push({
            origin,
            destination,
            date: normalDate,
            cabinClass: cabinClass.toUpperCase(),
            productName: product.productName ?? "",
            points: price.points ?? 0,
            taxes: price.totalTax ?? 0,
            currency: price.currency ?? "NOK",
            availableSeats: seats,
            bookingClass,
            segments,
            totalDurationMinutes: totalDuration,
            stops,
            flightId: flightKey,
            isBonusTicket,
            basePrice: price.basePrice ?? 0,
          });
        }
      }
    }
  }

  return offers.sort((a, b) => a.points - b.points);
}
```

- [ ] **Step 2: Write partners module**

Create `web/lib/sas/partners.ts` — port `get_partner_awards` and `parse_partner_flights` from `sas_search_api.py`:

```ts
import { sasRequest, type SASClientOptions } from "./client";
import type { PartnerFlight, PartnerCabin } from "./types";

const PARTNER_URL = "https://www.sas.no/award-api/flights";

export async function getPartnerAwards(
  origin: string,
  destination: string,
  date: string,
  options: { adults?: number } & SASClientOptions = {},
): Promise<PartnerFlight[]> {
  const { adults = 1, ...clientOpts } = options;

  // Ensure YYYY-MM-DD
  const outDate = date.length === 8
    ? `${date.slice(0, 4)}-${date.slice(4, 6)}-${date.slice(6, 8)}`
    : date;

  const raw = await sasRequest<any>(PARTNER_URL, {
    origin,
    destination,
    outboundDate: outDate,
    tripType: "one-way",
    adults,
    children: 0,
    infants: 0,
    youths: 0,
    selectedCouponCodes: "",
  }, clientOpts);

  if (!raw) return [];
  return parsePartnerFlights(raw, origin, destination, outDate);
}

function parseDuration(raw: any): number {
  if (typeof raw === "number") return raw;
  if (typeof raw !== "string") return 0;
  if (raw.includes(":")) {
    const [h, m] = raw.split(":");
    return Number(h) * 60 + Number(m);
  }
  const hMatch = raw.match(/(\d+)h/);
  const mMatch = raw.match(/(\d+)m/);
  return (hMatch ? Number(hMatch[1]) * 60 : 0) + (mMatch ? Number(mMatch[1]) : 0);
}

function parsePartnerFlights(data: any, origin: string, destination: string, date: string): PartnerFlight[] {
  const flights: PartnerFlight[] = [];

  for (const flight of data.outboundFlights ?? []) {
    if (typeof flight !== "object" || !flight) continue;
    const segments = flight.segments ?? [];
    if (!segments.length) continue;

    const airports: string[] = [];
    const carriers: string[] = [];
    const carrierNames: string[] = [];

    for (let i = 0; i < segments.length; i++) {
      const seg = segments[i];
      const dep = typeof seg.departureAirport === "object" ? seg.departureAirport?.code : seg.departureAirport;
      airports.push(dep);
      if (i === segments.length - 1) {
        const arr = typeof seg.arrivalAirport === "object" ? seg.arrivalAirport?.code : seg.arrivalAirport;
        airports.push(arr);
      }
      const op = seg.operatingCarrier ?? {};
      const mk = seg.marketingCarrier ?? {};
      const code = (typeof op === "object" ? op.code : null) ?? (typeof mk === "object" ? mk.code : null);
      const name = (typeof op === "object" ? op.name : null) ?? (typeof mk === "object" ? mk.name : null);
      if (code && !carriers.includes(code)) carriers.push(code);
      if (name && !carrierNames.includes(name)) carrierNames.push(name);
    }

    const stopsRaw = flight.stops;
    const numStops = Array.isArray(stopsRaw) ? stopsRaw.length : (Number(stopsRaw) || Math.max(0, segments.length - 1));

    const depTime = flight.startTimeInLocal ?? (flight.startDateTimeInLocal?.slice(11, 16) ?? "");
    const arrTime = flight.endTimeInLocal ?? (flight.endDateTimeInLocal?.slice(11, 16) ?? "");

    const cabins: PartnerCabin[] = [];
    for (const c of flight.cabins ?? []) {
      if (typeof c !== "object" || !c) continue;
      const price = c.price ?? {};
      const pts = price.points ?? price.totalPrice ?? 0;
      if (pts) {
        cabins.push({
          cabin: (c.cabin ?? c.cabinClass ?? "UNKNOWN").toUpperCase(),
          points: pts,
          cash: price.totalTax ?? price.cash ?? 0,
          seats: c.availableSeats ?? 0,
        });
      }
    }

    if (cabins.length) {
      flights.push({
        date,
        departureTime: depTime,
        arrivalTime: arrTime,
        origin,
        destination,
        route: airports.join(" → "),
        carriers,
        carrierNames,
        stops: numStops,
        totalDurationMinutes: parseDuration(flight.totalDuration ?? flight.connectionDuration ?? 0),
        cabins,
      });
    }
  }

  return flights;
}
```

- [ ] **Step 3: Commit**

```bash
git add web/lib/sas/offers.ts web/lib/sas/partners.ts
git commit -m "feat: add offers (points pricing) and partner awards endpoints"
```

---

### Task 7: Session capture and config

**Files:**
- Create: `web/lib/sas/session.ts`, `web/lib/config.ts`, `web/lib/route-map.ts`

- [ ] **Step 1: Write session module (Browserbase stub)**

Create `web/lib/sas/session.ts`:

```ts
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
```

- [ ] **Step 2: Write app config**

Create `web/lib/config.ts`:

```ts
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
```

- [ ] **Step 3: Write airport/route data**

Create `web/lib/route-map.ts` — extract key airports from `sas_route_map.json`:

```ts
export interface Airport {
  code: string;
  name: string;
  country: string;
}

/** Common origin airports for award searches */
export const ORIGINS: Airport[] = [
  { code: "OSL", name: "Oslo", country: "Norway" },
  { code: "CPH", name: "Copenhagen", country: "Denmark" },
  { code: "ARN", name: "Stockholm", country: "Sweden" },
  { code: "CDG", name: "Paris", country: "France" },
  { code: "AMS", name: "Amsterdam", country: "Netherlands" },
  { code: "LHR", name: "London Heathrow", country: "United Kingdom" },
  { code: "FRA", name: "Frankfurt", country: "Germany" },
];

/** Popular long-haul destinations */
export const DESTINATIONS: Airport[] = [
  { code: "BKK", name: "Bangkok", country: "Thailand" },
  { code: "NRT", name: "Tokyo Narita", country: "Japan" },
  { code: "HND", name: "Tokyo Haneda", country: "Japan" },
  { code: "KIX", name: "Osaka", country: "Japan" },
  { code: "SIN", name: "Singapore", country: "Singapore" },
  { code: "PVG", name: "Shanghai", country: "China" },
  { code: "PEK", name: "Beijing", country: "China" },
  { code: "SGN", name: "Ho Chi Minh City", country: "Vietnam" },
  { code: "HAN", name: "Hanoi", country: "Vietnam" },
  { code: "ICN", name: "Seoul", country: "South Korea" },
  { code: "JFK", name: "New York", country: "USA" },
  { code: "LAX", name: "Los Angeles", country: "USA" },
  { code: "MIA", name: "Miami", country: "USA" },
];

/** All known airports for autocomplete */
export const ALL_AIRPORTS: Airport[] = [...ORIGINS, ...DESTINATIONS];

export function findAirport(code: string): Airport | undefined {
  return ALL_AIRPORTS.find((a) => a.code === code.toUpperCase());
}
```

- [ ] **Step 4: Commit**

```bash
git add web/lib/sas/session.ts web/lib/config.ts web/lib/route-map.ts
git commit -m "feat: add session management, app config, and airport data"
```

---

## Chunk 3: Pages & API Routes

### Task 8: Landing page

**Files:**
- Create: `web/app/page.tsx`, `web/components/search-form.tsx`

- [ ] **Step 1: Write search form component**

Create `web/components/search-form.tsx`:

```tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ORIGINS, DESTINATIONS } from "@/lib/route-map";

export function SearchForm() {
  const router = useRouter();
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [month, setMonth] = useState("");

  const months = Array.from({ length: 12 }, (_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() + i);
    return {
      value: `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`,
      label: d.toLocaleDateString("en-US", { year: "numeric", month: "long" }),
    };
  });

  function handleSearch() {
    if (!origin || !destination) return;
    const params = new URLSearchParams({ origin, destination });
    if (month) params.set("month", month);
    router.push(`/search?${params.toString()}`);
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">From</label>
        <Select onValueChange={setOrigin}>
          <SelectTrigger><SelectValue placeholder="Origin" /></SelectTrigger>
          <SelectContent>
            {ORIGINS.map((a) => (
              <SelectItem key={a.code} value={a.code}>{a.code} — {a.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">To</label>
        <Select onValueChange={setDestination}>
          <SelectTrigger><SelectValue placeholder="Destination" /></SelectTrigger>
          <SelectContent>
            {DESTINATIONS.map((a) => (
              <SelectItem key={a.code} value={a.code}>{a.code} — {a.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Month (optional)</label>
        <Select onValueChange={setMonth}>
          <SelectTrigger><SelectValue placeholder="Any month" /></SelectTrigger>
          <SelectContent>
            {months.map((m) => (
              <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button onClick={handleSearch} className="bg-indigo-600 hover:bg-indigo-700">
        Search
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Write landing page**

Create `web/app/page.tsx`:

```tsx
import { SearchForm } from "@/components/search-form";

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="space-y-4 pt-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Find SAS EuroBonus award seats
        </h1>
        <p className="mx-auto max-w-lg text-muted-foreground">
          Search real-time bonus ticket availability across SAS and SkyTeam partners.
          Set up alerts to get notified when seats open up.
        </p>
      </section>

      <section className="mx-auto max-w-3xl rounded-lg border bg-white p-6 shadow-sm">
        <SearchForm />
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border bg-white p-5">
          <h3 className="mb-1 font-semibold">Real-time data</h3>
          <p className="text-sm text-muted-foreground">
            Verified bonus seats from the SAS booking engine, not just cached calendars.
          </p>
        </div>
        <div className="rounded-lg border bg-white p-5">
          <h3 className="mb-1 font-semibold">Smart alerts</h3>
          <p className="text-sm text-muted-foreground">
            Sign in to watch routes and get emailed the moment bonus seats appear.
          </p>
        </div>
        <div className="rounded-lg border bg-white p-5">
          <h3 className="mb-1 font-semibold">Best deals</h3>
          <p className="text-sm text-muted-foreground">
            Browse the hottest award availability across all routes at a glance.
          </p>
        </div>
      </section>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add web/app/page.tsx web/components/search-form.tsx
git commit -m "feat: add landing page with search form"
```

---

### Task 9: Search page + API route

**Files:**
- Create: `web/app/search/page.tsx`, `web/app/api/search/route.ts`, `web/components/availability-calendar.tsx`, `web/components/flight-card.tsx`

- [ ] **Step 1: Write search API route**

Create `web/app/api/search/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { getAvailableDates } from "@/lib/sas/availability";
import { getRouteDetails } from "@/lib/sas/routes";

export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl;
  const origin = searchParams.get("origin")?.toUpperCase();
  const destination = searchParams.get("destination")?.toUpperCase();
  const month = searchParams.get("month") ?? "";
  const date = searchParams.get("date");

  if (!origin || !destination) {
    return NextResponse.json({ error: "origin and destination required" }, { status: 400 });
  }

  // If a specific date is requested, return route details
  if (date) {
    const routes = await getRouteDetails(origin, destination, date);
    return NextResponse.json({ routes });
  }

  // Otherwise return calendar availability
  const dates = await getAvailableDates(origin, destination, { month });
  return NextResponse.json({ dates });
}
```

- [ ] **Step 2: Write availability calendar component**

Create `web/components/availability-calendar.tsx`:

```tsx
"use client";
import type { AvailabilityDate } from "@/lib/sas/types";
import { Badge } from "@/components/ui/badge";

interface Props {
  dates: AvailabilityDate[];
  onSelectDate?: (date: string) => void;
}

export function AvailabilityCalendar({ dates, onSelectDate }: Props) {
  if (!dates.length) {
    return <p className="text-sm text-muted-foreground">No availability found for this route and period.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {dates.map((d) => {
        const hasEconomy = d.economySeats > 0;
        const hasPremium = d.premiumSeats > 0;
        const hasBusiness = d.businessSeats > 0;

        return (
          <button
            key={d.date}
            onClick={() => onSelectDate?.(d.date)}
            className="flex items-center justify-between rounded-lg border bg-white p-3 text-left transition hover:border-indigo-300 hover:shadow-sm"
          >
            <span className="text-sm font-medium">
              {new Date(d.date + "T00:00").toLocaleDateString("en-US", {
                weekday: "short", month: "short", day: "numeric",
              })}
            </span>
            <div className="flex gap-1.5">
              {hasEconomy && <Badge variant="secondary" className="text-xs">E: {d.economySeats}</Badge>}
              {hasPremium && <Badge variant="secondary" className="bg-amber-50 text-amber-700 text-xs">P: {d.premiumSeats}</Badge>}
              {hasBusiness && <Badge variant="secondary" className="bg-indigo-50 text-indigo-700 text-xs">B: {d.businessSeats}</Badge>}
            </div>
          </button>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 3: Write flight card component**

Create `web/components/flight-card.tsx`:

```tsx
import type { FlightOffer } from "@/lib/sas/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

interface Props {
  offer: FlightOffer;
}

export function FlightCard({ offer }: Props) {
  const segments = offer.segments;
  const dep = segments[0];
  const arr = segments[segments.length - 1];

  const bookingUrl = `https://www.sas.no/book/flights/?search=OW_${offer.origin}-${offer.destination}-${offer.date.replace(/-/g, "")}_a1c0i0y0&bookingFlow=points`;

  return (
    <Card>
      <CardContent className="flex items-center justify-between gap-4 p-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm">{dep?.departureTime ?? ""}</span>
            <span className="text-xs text-muted-foreground">→</span>
            <span className="font-mono text-sm">{arr?.arrivalTime ?? ""}</span>
            {offer.stops > 0 && (
              <span className="text-xs text-muted-foreground">({offer.stops} stop{offer.stops > 1 ? "s" : ""})</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">
              {dep?.carrier} {dep?.flightNumber}
            </span>
            <Badge variant={offer.isBonusTicket ? "default" : "outline"} className={offer.isBonusTicket ? "bg-green-600 text-xs" : "text-xs"}>
              {offer.productName}
            </Badge>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-semibold">{offer.points.toLocaleString()} pts</div>
          <div className="text-xs text-muted-foreground">+ {offer.taxes.toFixed(0)} {offer.currency} tax</div>
          <a href={bookingUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-600 hover:underline">
            Book on SAS
          </a>
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Write search page**

Create `web/app/search/page.tsx`:

```tsx
"use client";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import { SearchForm } from "@/components/search-form";
import { AvailabilityCalendar } from "@/components/availability-calendar";
import { findAirport } from "@/lib/route-map";
import type { AvailabilityDate } from "@/lib/sas/types";

function SearchResults() {
  const searchParams = useSearchParams();
  const origin = searchParams.get("origin") ?? "";
  const destination = searchParams.get("destination") ?? "";
  const month = searchParams.get("month") ?? "";
  const [dates, setDates] = useState<AvailabilityDate[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!origin || !destination) return;
    setLoading(true);
    const params = new URLSearchParams({ origin, destination });
    if (month) params.set("month", month);
    fetch(`/api/search?${params}`)
      .then((r) => r.json())
      .then((data) => setDates(data.dates ?? []))
      .finally(() => setLoading(false));
  }, [origin, destination, month]);

  const originAirport = findAirport(origin);
  const destAirport = findAirport(destination);

  return (
    <div className="space-y-6">
      <div className="rounded-lg border bg-white p-4">
        <SearchForm />
      </div>

      {origin && destination && (
        <div>
          <h2 className="mb-4 text-xl font-semibold">
            {originAirport?.name ?? origin} → {destAirport?.name ?? destination}
            {month && <span className="text-muted-foreground font-normal text-base ml-2">
              {new Date(Number(month.slice(0, 4)), Number(month.slice(4)) - 1).toLocaleDateString("en-US", { month: "long", year: "numeric" })}
            </span>}
          </h2>

          {loading ? (
            <p className="text-sm text-muted-foreground">Searching SAS...</p>
          ) : (
            <AvailabilityCalendar dates={dates} />
          )}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading...</p>}>
      <SearchResults />
    </Suspense>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add web/app/search/ web/app/api/search/ web/components/availability-calendar.tsx web/components/flight-card.tsx
git commit -m "feat: add search page with availability calendar and flight cards"
```

---

### Task 10: Deals page + API route

**Files:**
- Create: `web/app/deals/page.tsx`, `web/app/api/deals/route.ts`, `web/components/deal-card.tsx`, `web/lib/db/queries/availability.ts`

- [ ] **Step 1: Write availability queries**

Create `web/lib/db/queries/availability.ts`:

```ts
import { db } from "@/lib/db";
import { availabilityCache } from "@/lib/db/schema";
import { desc, gt, sql, and, eq } from "drizzle-orm";

export async function getBestDeals(options: { cabinFilter?: string; limit?: number } = {}) {
  const { cabinFilter, limit = 20 } = options;

  // Build WHERE conditions
  const conditions = [];
  if (cabinFilter === "economy") conditions.push(gt(availabilityCache.economySeats, 0));
  else if (cabinFilter === "premium") conditions.push(gt(availabilityCache.premiumSeats, 0));
  else if (cabinFilter === "business") conditions.push(gt(availabilityCache.businessSeats, 0));
  else {
    // Any cabin with seats
    conditions.push(
      sql`(${availabilityCache.economySeats} > 0 OR ${availabilityCache.premiumSeats} > 0 OR ${availabilityCache.businessSeats} > 0)`
    );
  }

  conditions.push(eq(availabilityCache.direction, "outbound"));

  const rows = await db
    .select()
    .from(availabilityCache)
    .where(and(...conditions))
    .orderBy(desc(availabilityCache.businessSeats), desc(availabilityCache.fetchedAt))
    .limit(limit);

  return rows;
}
```

- [ ] **Step 2: Write deals API route**

Create `web/app/api/deals/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { getBestDeals } from "@/lib/db/queries/availability";

export async function GET(req: NextRequest) {
  const cabin = req.nextUrl.searchParams.get("cabin") ?? undefined;
  const deals = await getBestDeals({ cabinFilter: cabin });
  return NextResponse.json({ deals });
}
```

- [ ] **Step 3: Write deal card component**

Create `web/components/deal-card.tsx`:

```tsx
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { findAirport } from "@/lib/route-map";

interface Props {
  deal: {
    origin: string;
    destination: string;
    date: string;
    economySeats: number;
    premiumSeats: number;
    businessSeats: number;
    isBonus: boolean | null;
    pointsBusiness: number | null;
  };
}

export function DealCard({ deal }: Props) {
  const orig = findAirport(deal.origin);
  const dest = findAirport(deal.destination);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold">
            {orig?.name ?? deal.origin} → {dest?.name ?? deal.destination}
          </h3>
          <span className="text-sm text-muted-foreground">
            {new Date(deal.date + "T00:00").toLocaleDateString("en-US", {
              month: "short", day: "numeric",
            })}
          </span>
        </div>
        <div className="flex gap-2">
          {deal.economySeats > 0 && <Badge variant="secondary">Economy: {deal.economySeats}</Badge>}
          {deal.premiumSeats > 0 && <Badge className="bg-amber-50 text-amber-700">Premium: {deal.premiumSeats}</Badge>}
          {deal.businessSeats > 0 && <Badge className="bg-indigo-50 text-indigo-700">Business: {deal.businessSeats}</Badge>}
        </div>
        {deal.isBonus && <p className="mt-2 text-xs text-green-600">Verified bonus seats</p>}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Write deals page**

Create `web/app/deals/page.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { DealCard } from "@/components/deal-card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function DealsPage() {
  const [deals, setDeals] = useState<any[]>([]);
  const [cabin, setCabin] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const params = cabin !== "all" ? `?cabin=${cabin}` : "";
    fetch(`/api/deals${params}`)
      .then((r) => r.json())
      .then((data) => setDeals(data.deals ?? []))
      .finally(() => setLoading(false));
  }, [cabin]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Best Deals</h1>
        <p className="text-sm text-muted-foreground">Current award availability across all monitored routes.</p>
      </div>

      <Tabs value={cabin} onValueChange={setCabin}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="economy">Economy</TabsTrigger>
          <TabsTrigger value="premium">Premium</TabsTrigger>
          <TabsTrigger value="business">Business</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading deals...</p>
      ) : deals.length === 0 ? (
        <p className="text-sm text-muted-foreground">No deals found. Check back after the next scan.</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {deals.map((d, i) => <DealCard key={i} deal={d} />)}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add web/app/deals/ web/app/api/deals/ web/components/deal-card.tsx web/lib/db/queries/availability.ts
git commit -m "feat: add deals page with cabin filter tabs"
```

---

### Task 11: Alerts page (protected) + API route

**Files:**
- Create: `web/app/alerts/page.tsx`, `web/app/api/alerts/route.ts`, `web/components/alert-form.tsx`, `web/lib/db/queries/subscriptions.ts`

- [ ] **Step 1: Write subscription queries**

Create `web/lib/db/queries/subscriptions.ts`:

```ts
import { db } from "@/lib/db";
import { routeSubscriptions } from "@/lib/db/schema";
import { eq, and } from "drizzle-orm";

export async function getUserSubscriptions(userId: string) {
  return db.select().from(routeSubscriptions).where(eq(routeSubscriptions.userId, userId));
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
    .where(and(eq(routeSubscriptions.id, id), eq(routeSubscriptions.userId, userId)));
  return result;
}

export async function getActiveSubscriptions() {
  return db.select().from(routeSubscriptions).where(eq(routeSubscriptions.active, true));
}

export async function getUniqueSubscribedRoutes(): Promise<{ origin: string; destination: string }[]> {
  const rows = await db
    .selectDistinct({ origin: routeSubscriptions.origin, destination: routeSubscriptions.destination })
    .from(routeSubscriptions)
    .where(eq(routeSubscriptions.active, true));
  return rows;
}
```

- [ ] **Step 2: Write alerts API route**

Create `web/app/api/alerts/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { getUserSubscriptions, createSubscription, deleteSubscription } from "@/lib/db/queries/subscriptions";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const subs = await getUserSubscriptions(session.user.id);
  return NextResponse.json({ subscriptions: subs });
}

export async function POST(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  const { origin, destination, cabinClass, dateFrom, dateTo } = body;

  if (!origin || !destination) {
    return NextResponse.json({ error: "origin and destination required" }, { status: 400 });
  }

  const sub = await createSubscription({
    userId: session.user.id,
    origin,
    destination,
    cabinClass: cabinClass ?? "any",
    dateFrom,
    dateTo,
  });

  return NextResponse.json({ subscription: sub }, { status: 201 });
}

export async function DELETE(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });

  await deleteSubscription(id, session.user.id);
  return NextResponse.json({ ok: true });
}
```

- [ ] **Step 3: Write alert form component**

Create `web/components/alert-form.tsx`:

```tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ORIGINS, DESTINATIONS } from "@/lib/route-map";

interface Props {
  onCreated: () => void;
}

export function AlertForm({ onCreated }: Props) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [cabin, setCabin] = useState("any");
  const [saving, setSaving] = useState(false);

  async function handleSubmit() {
    if (!origin || !destination) return;
    setSaving(true);
    await fetch("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination, cabinClass: cabin }),
    });
    setSaving(false);
    onCreated();
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">From</label>
        <Select onValueChange={setOrigin}>
          <SelectTrigger><SelectValue placeholder="Origin" /></SelectTrigger>
          <SelectContent>
            {ORIGINS.map((a) => <SelectItem key={a.code} value={a.code}>{a.code} — {a.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">To</label>
        <Select onValueChange={setDestination}>
          <SelectTrigger><SelectValue placeholder="Destination" /></SelectTrigger>
          <SelectContent>
            {DESTINATIONS.map((a) => <SelectItem key={a.code} value={a.code}>{a.code} — {a.name}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">Cabin</label>
        <Select onValueChange={setCabin} defaultValue="any">
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any class</SelectItem>
            <SelectItem value="economy">Economy</SelectItem>
            <SelectItem value="premium">Premium</SelectItem>
            <SelectItem value="business">Business</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button onClick={handleSubmit} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700">
        {saving ? "Adding..." : "Add Alert"}
      </Button>
    </div>
  );
}
```

- [ ] **Step 4: Write alerts page**

Create `web/app/alerts/page.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { AlertForm } from "@/components/alert-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { findAirport } from "@/lib/route-map";

export default function AlertsPage() {
  const { data: session, status } = useSession();
  const [subs, setSubs] = useState<any[]>([]);

  function load() {
    fetch("/api/alerts").then((r) => r.json()).then((d) => setSubs(d.subscriptions ?? []));
  }

  useEffect(() => { if (session) load(); }, [session]);

  async function handleDelete(id: string) {
    await fetch("/api/alerts", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    load();
  }

  if (status === "loading") return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (!session) return <p className="text-sm text-muted-foreground">Sign in with Google to set up alerts.</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Alerts</h1>
        <p className="text-sm text-muted-foreground">Get notified when bonus seats open up on your watched routes.</p>
      </div>

      <Card>
        <CardContent className="p-4">
          <AlertForm onCreated={load} />
        </CardContent>
      </Card>

      {subs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No alerts yet. Add a route above to start watching.</p>
      ) : (
        <div className="space-y-2">
          {subs.map((s) => (
            <Card key={s.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <span className="font-medium">
                    {findAirport(s.origin)?.name ?? s.origin} → {findAirport(s.destination)?.name ?? s.destination}
                  </span>
                  <Badge variant="outline" className="ml-2 text-xs">{s.cabinClass}</Badge>
                </div>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(s.id)}>Remove</Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add web/app/alerts/ web/app/api/alerts/ web/components/alert-form.tsx web/lib/db/queries/subscriptions.ts
git commit -m "feat: add alerts page with subscription CRUD"
```

---

### Task 12: Notifications page + API route

**Files:**
- Create: `web/app/notifications/page.tsx`, `web/app/api/notifications/route.ts`, `web/components/notification-item.tsx`, `web/lib/db/queries/notifications.ts`

- [ ] **Step 1: Write notification queries**

Create `web/lib/db/queries/notifications.ts`:

```ts
import { db } from "@/lib/db";
import { notifications } from "@/lib/db/schema";
import { eq, desc, and } from "drizzle-orm";

export async function getUserNotifications(userId: string, limit = 50) {
  return db
    .select()
    .from(notifications)
    .where(eq(notifications.userId, userId))
    .orderBy(desc(notifications.createdAt))
    .limit(limit);
}

export async function markNotificationRead(id: string, userId: string) {
  await db
    .update(notifications)
    .set({ read: true })
    .where(and(eq(notifications.id, id), eq(notifications.userId, userId)));
}

export async function getUnreadCount(userId: string): Promise<number> {
  const rows = await db
    .select()
    .from(notifications)
    .where(and(eq(notifications.userId, userId), eq(notifications.read, false)));
  return rows.length;
}
```

- [ ] **Step 2: Write notifications API route**

Create `web/app/api/notifications/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { auth } from "@/lib/auth";
import { getUserNotifications, markNotificationRead } from "@/lib/db/queries/notifications";

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const items = await getUserNotifications(session.user.id);
  return NextResponse.json({ notifications: items });
}

export async function PATCH(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const { id } = await req.json();
  if (!id) return NextResponse.json({ error: "id required" }, { status: 400 });
  await markNotificationRead(id, session.user.id);
  return NextResponse.json({ ok: true });
}
```

- [ ] **Step 3: Write notification item component**

Create `web/components/notification-item.tsx`:

```tsx
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Props {
  notification: {
    id: string;
    type: string;
    title: string;
    body: string;
    read: boolean;
    createdAt: string;
  };
  onMarkRead: (id: string) => void;
}

export function NotificationItem({ notification, onMarkRead }: Props) {
  return (
    <Card className={notification.read ? "opacity-60" : ""}>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold">{notification.title}</h3>
              {!notification.read && <Badge className="bg-indigo-600 text-xs">New</Badge>}
            </div>
            <p className="text-sm text-muted-foreground">{notification.body}</p>
            <p className="text-xs text-muted-foreground">
              {new Date(notification.createdAt).toLocaleString()}
            </p>
          </div>
          {!notification.read && (
            <button onClick={() => onMarkRead(notification.id)} className="text-xs text-indigo-600 hover:underline">
              Mark read
            </button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Write notifications page**

Create `web/app/notifications/page.tsx`:

```tsx
"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { NotificationItem } from "@/components/notification-item";

export default function NotificationsPage() {
  const { data: session, status } = useSession();
  const [items, setItems] = useState<any[]>([]);

  function load() {
    fetch("/api/notifications").then((r) => r.json()).then((d) => setItems(d.notifications ?? []));
  }

  useEffect(() => { if (session) load(); }, [session]);

  async function handleMarkRead(id: string) {
    await fetch("/api/notifications", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    load();
  }

  if (status === "loading") return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (!session) return <p className="text-sm text-muted-foreground">Sign in to view notifications.</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-sm text-muted-foreground">Alerts when bonus seats appear on your watched routes.</p>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No notifications yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((n) => <NotificationItem key={n.id} notification={n} onMarkRead={handleMarkRead} />)}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 5: Commit**

```bash
git add web/app/notifications/ web/app/api/notifications/ web/components/notification-item.tsx web/lib/db/queries/notifications.ts
git commit -m "feat: add notifications page with read/unread state"
```

---

## Chunk 4: Cron Jobs & Email Alerts

### Task 13: Poll availability cron job

**Files:**
- Create: `web/app/api/cron/poll-availability/route.ts`

- [ ] **Step 1: Write poll-availability cron handler**

Create `web/app/api/cron/poll-availability/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { config } from "@/lib/config";
import { getAvailableDates } from "@/lib/sas/availability";
import { db } from "@/lib/db";
import { availabilityCache } from "@/lib/db/schema";
import { getUniqueSubscribedRoutes } from "@/lib/db/queries/subscriptions";
import { sql } from "drizzle-orm";

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

  // TODO: After updating cache, check for new availability vs previous state
  // and create notifications for matching subscriptions. This will be
  // implemented in Task 15 (alert matching logic).

  return NextResponse.json({ ok: true, routes: allRoutes.length, updated });
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/api/cron/poll-availability/
git commit -m "feat: add poll-availability cron job"
```

---

### Task 14: Verify-bonus and refresh-session cron jobs

**Files:**
- Create: `web/app/api/cron/verify-bonus/route.ts`, `web/app/api/cron/refresh-session/route.ts`, `web/lib/db/queries/sessions.ts`

- [ ] **Step 1: Write session queries**

Create `web/lib/db/queries/sessions.ts`:

```ts
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
```

- [ ] **Step 2: Write verify-bonus cron**

Create `web/app/api/cron/verify-bonus/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { availabilityCache } from "@/lib/db/schema";
import { getActiveSession } from "@/lib/sas/session";
import { getOffersWithPoints } from "@/lib/sas/offers";
import { and, gt, eq, or, sql } from "drizzle-orm";
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
```

- [ ] **Step 3: Write refresh-session cron**

Create `web/app/api/cron/refresh-session/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { getActiveSession, refreshSession } from "@/lib/sas/session";

export async function GET(req: NextRequest) {
  const authHeader = req.headers.get("authorization");
  if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const current = await getActiveSession();
  if (current) {
    return NextResponse.json({ ok: true, status: "session still active" });
  }

  const success = await refreshSession();
  return NextResponse.json({ ok: success, status: success ? "refreshed" : "refresh failed" });
}
```

- [ ] **Step 4: Create vercel.json with cron config**

Create `web/vercel.json`:

```json
{
  "crons": [
    { "path": "/api/cron/poll-availability", "schedule": "*/30 * * * *" },
    { "path": "/api/cron/verify-bonus", "schedule": "0 */2 * * *" },
    { "path": "/api/cron/refresh-session", "schedule": "0 */6 * * *" }
  ]
}
```

- [ ] **Step 5: Commit**

```bash
git add web/app/api/cron/ web/lib/db/queries/sessions.ts web/vercel.json
git commit -m "feat: add verify-bonus, refresh-session cron jobs, and vercel cron config"
```

---

### Task 15: Email alerts + notification creation

**Files:**
- Create: `web/lib/email.ts`, update `web/app/api/cron/poll-availability/route.ts`

- [ ] **Step 1: Write email helper**

Create `web/lib/email.ts`:

```ts
import { Resend } from "resend";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function sendAlertEmail(options: {
  to: string;
  origin: string;
  originName: string;
  destination: string;
  destinationName: string;
  date: string;
  cabinClass: string;
  seats: number;
}) {
  const bookingUrl = `https://www.sas.no/book/flights/?search=OW_${options.origin}-${options.destination}-${options.date.replace(/-/g, "")}_a1c0i0y0&bookingFlow=points`;

  await resend.emails.send({
    from: "Award Finder <alerts@yourdomain.com>",
    to: options.to,
    subject: `${options.cabinClass} bonus seats: ${options.originName} → ${options.destinationName}, ${options.date}`,
    html: `
      <h2>${options.originName} → ${options.destinationName}</h2>
      <p><strong>${options.seats}</strong> ${options.cabinClass} bonus seats on <strong>${options.date}</strong></p>
      <p><a href="${bookingUrl}" style="background:#6366f1;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;display:inline-block">Book on SAS</a></p>
      <p style="color:#999;font-size:12px">You're getting this because you have an alert set for this route.</p>
    `,
  });
}
```

- [ ] **Step 2: Add alert matching to poll-availability**

Update the TODO in `web/app/api/cron/poll-availability/route.ts` — after the cache update loop, add alert matching logic that:

1. Compares new availability against previous `availability_cache` state
2. When new seats appear that weren't there before, queries `route_subscriptions` for matching users
3. Creates a `notifications` record for each matched user
4. Calls `sendAlertEmail` for each matched user
5. Marks the notification as `emailed: true`

```ts
// Add these imports at top:
import { getActiveSubscriptions } from "@/lib/db/queries/subscriptions";
import { notifications as notificationsTable } from "@/lib/db/schema";
import { sendAlertEmail } from "@/lib/email";
import { findAirport } from "@/lib/route-map";
import { users } from "@/lib/db/schema";
import { eq, and as drizzleAnd, gte, lte } from "drizzle-orm";

// IMPORTANT: Before updating the cache, snapshot the previous state so we can
// detect genuinely NEW seats (seats that were 0 before and are now > 0).
// Build a Map of "origin-dest-date" -> { economy, premium, business } from
// the existing cache before the upsert loop runs.

const previousCache = new Map<string, { economy: number; premium: number; business: number }>();
const existingRows = await db.select().from(availabilityCache);
for (const r of existingRows) {
  previousCache.set(`${r.origin}-${r.destination}-${r.date}`, {
    economy: r.economySeats, premium: r.premiumSeats, business: r.businessSeats,
  });
}

// ... (existing cache update loop runs here) ...

// After the cache update loop, check for NEW availability:
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
      sub.cabinClass === "economy" ? row.economySeats :
      sub.cabinClass === "premium" ? row.premiumSeats :
      sub.cabinClass === "business" ? row.businessSeats :
      row.economySeats + row.premiumSeats + row.businessSeats;

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
```

- [ ] **Step 3: Commit**

```bash
git add web/lib/email.ts web/app/api/cron/poll-availability/
git commit -m "feat: add email alerts and notification creation on new availability"
```

---

### Task 16: Settings page

**Files:**
- Create: `web/app/settings/page.tsx`

- [ ] **Step 1: Write settings page**

Create `web/app/settings/page.tsx` — simple page showing user info and email preference:

```tsx
"use client";
import { useSession } from "next-auth/react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function SettingsPage() {
  const { data: session, status } = useSession();

  if (status === "loading") return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (!session) return <p className="text-sm text-muted-foreground">Sign in to view settings.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <CardContent className="flex items-center gap-4 p-4">
          <Avatar className="h-12 w-12">
            <AvatarImage src={session.user?.image ?? undefined} />
            <AvatarFallback>{session.user?.name?.[0] ?? "U"}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-medium">{session.user?.name}</p>
            <p className="text-sm text-muted-foreground">{session.user?.email}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <h2 className="mb-2 font-semibold">Email Notifications</h2>
          <p className="text-sm text-muted-foreground">
            Alert emails are sent to {session.user?.email} when bonus seats appear on your watched routes.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add web/app/settings/
git commit -m "feat: add settings page"
```

---

### Task 17: Final wiring and database migration

- [ ] **Step 1: Generate Drizzle migration**

```bash
cd web
npx drizzle-kit generate
```

- [ ] **Step 2: Verify the app builds**

```bash
npm run build
```

Fix any TypeScript or build errors.

- [ ] **Step 3: Add NextAuth user ID to session types**

NextAuth with Drizzle adapter does not include `user.id` in the session by default. Add a callback in `web/lib/auth.ts`:

```ts
callbacks: {
  session({ session, user }) {
    if (session.user) session.user.id = user.id;
    return session;
  },
},
```

Create `web/types/next-auth.d.ts` to extend the session type:

```ts
import { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface Session {
    user: { id: string } & DefaultSession["user"];
  }
}
```

This is required — the alerts, notifications, and settings API routes all access `session.user.id`.

- [ ] **Step 4: Run database migration against Neon**

```bash
npx drizzle-kit push
```

- [ ] **Step 5: Test locally**

```bash
npm run dev
```

Verify:
- Landing page loads with search form
- Search redirects and shows results (live SAS API call)
- Google sign-in works
- Alerts CRUD works
- Deals page loads (empty until cron runs)

- [ ] **Step 6: Commit everything**

```bash
git add -A
git commit -m "feat: complete EuroBonus Award Finder website"
```
