# EuroBonus Award Finder — Website Design Spec

> **Date:** 2026-03-14
> **Status:** Draft
> **Author:** Claude + Tom

---

## 1. Purpose

Replace the old Telegram bot + background monitor with a polished website for searching SAS EuroBonus award flight availability, browsing deals, and receiving alerts when bonus seats open up.

**Target audience:** Small group of friends/family (invite-style, not public-scale).

---

## 2. Architecture

Single Next.js application deployed to Vercel. All TypeScript.

```
┌─────────────────────────────────────────────────────┐
│                      Vercel                          │
│                                                      │
│  ┌───────────────┐    ┌──────────────────────────┐  │
│  │  Next.js App   │    │  Vercel Cron Jobs         │  │
│  │                │    │                           │  │
│  │  - Pages/UI    │    │  - poll-availability      │  │
│  │  - API routes  │    │    (every 30 min)         │  │
│  │  - Auth        │    │  - verify-bonus           │  │
│  │                │    │    (every 2 hours)        │  │
│  └──────┬────────┘    │  - refresh-session         │  │
│         │             │    (every 6 hours)         │  │
│         │             └────────────┬───────────────┘  │
│         └──────────┬───────────────┘                  │
│                    │                                  │
│         ┌──────────▼──────────┐                       │
│         │   Neon PostgreSQL    │                       │
│         └─────────────────────┘                       │
└─────────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
   ┌─────────────┐    ┌──────────────┐
   │  Browserbase │    │    Resend     │
   │  (sessions)  │    │   (email)     │
   └─────────────┘    └──────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | Next.js 15 (App Router) | Full-stack React, server components, API routes, cron |
| Language | TypeScript | One language everywhere |
| Styling | Tailwind CSS + shadcn/ui | Polished UI with consistent component library |
| Auth | NextAuth.js (Auth.js) | Google OAuth |
| Database | PostgreSQL on Neon | Free tier, serverless |
| ORM | Drizzle | Lightweight, type-safe |
| Email | Resend | Transactional email alerts |
| Session capture | Browserbase | Headless Chrome for Cloudflare bypass |
| Hosting | Vercel | Free tier, auto-deploy, built-in cron |

---

## 4. Pages

### Public (no login required)

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Hero with search bar, live deals ticker, "Sign in to get alerts" CTA |
| `/search` | Search results | Pick origin, destination, month. Calendar grid of availability + flight detail cards with points pricing |
| `/deals` | Deals overview | Best current bonus availability across all routes. Filterable by cabin class, sorted by value |

### Authenticated (Google sign-in)

| Route | Page | Description |
|-------|------|-------------|
| `/alerts` | Alert subscriptions | Add/remove routes to watch, set cabin class and date preferences |
| `/notifications` | Notification history | What opened up, when, link to book on SAS |
| `/settings` | Settings | Email preferences, notification toggles |

### Core user flow

1. Visit the site, search a route or browse deals — no login needed
2. See something interesting → sign in with Google to set up alerts
3. Pick routes to watch (e.g. "OSL → BKK, Business, any date in March")
4. Get an email + in-site notification when bonus seats appear
5. Click through to SAS booking page

---

## 5. SAS API Client (TypeScript)

Rewrite of the existing Python extraction scripts as a TypeScript library within the codebase.

### Module structure: `lib/sas/`

| File | Responsibility |
|------|---------------|
| `client.ts` | Base HTTP client — headers, rate limiting, retry with backoff, session cookie injection |
| `availability.ts` | `/bff/award-finder/destinations/v1` — calendar availability (cached daily by SAS) |
| `routes.ts` | `/bff/award-finder/routes/v1` — flight details, times, connections for a specific date |
| `offers.ts` | `/api/offers/flights` — real-time points pricing, bonus vs revenue detection (needs auth) |
| `partners.ts` | `/award-api/flights` — SkyTeam partner inventory |
| `session.ts` | Browserbase integration — headless browser, Cloudflare bypass, token harvest, DB storage |
| `types.ts` | Shared types — `FlightOffer`, `Availability`, `Segment`, `CabinClass`, etc. |

### Key behaviors

- **Two-tier data strategy:** fast cached endpoints for calendar overview, real-time offers endpoint for actual bonus seat verification
- **Bonus vs revenue detection:** filter on `isStandardAward: true` — only show real bonus tickets
- **Rate limiting:** 2-5s between requests, exponential backoff on HTTP 429
- **Session lifecycle:** Browserbase refreshes auth token when expired, stored in DB

### API endpoints consumed

| Endpoint | Auth needed | Data freshness | Use |
|----------|-----------|---------------|-----|
| `/bff/award-finder/destinations/v1` | No | Daily cache | Calendar overview |
| `/bff/award-finder/routes/v1` | No | Daily cache | Flight times, connections |
| `/api/offers/flights` | Yes (session) | Real-time | Exact points pricing, bonus verification |
| `/award-api/flights` | No | Real-time | SkyTeam partner inventory |

Full API details in `SAS_API_DOCUMENTATION.md`.

---

## 6. Data Model

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| email | text | unique |
| name | text | |
| image | text | Google avatar URL |
| email_verified | timestamp | |
| created_at | timestamp | |

### `accounts` (NextAuth managed)
Standard NextAuth schema for OAuth provider tokens.

### `sessions` (NextAuth managed)
Standard NextAuth session management.

### `route_subscriptions`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| user_id | uuid | FK → users.id |
| origin | text | IATA code (e.g. "OSL") |
| destination | text | IATA code (e.g. "BKK") |
| cabin_class | text | "economy" \| "premium" \| "business" \| "any" |
| date_from | date | nullable — null means any date |
| date_to | date | nullable |
| active | boolean | |
| created_at | timestamp | |

### `availability_cache`
| Column | Type | Notes |
|--------|------|-------|
| id | serial | PK |
| origin | text | IATA code |
| destination | text | IATA code |
| date | date | |
| direction | text | "outbound" \| "inbound" |
| economy_seats | int | |
| premium_seats | int | |
| business_seats | int | |
| is_bonus | boolean | verified via offers API |
| points_economy | int | nullable |
| points_premium | int | nullable |
| points_business | int | nullable |
| fetched_at | timestamp | |
| | | UNIQUE(origin, destination, date, direction) |

### `notifications`
| Column | Type | Notes |
|--------|------|-------|
| id | uuid | PK |
| user_id | uuid | FK → users.id |
| subscription_id | uuid | FK → route_subscriptions.id |
| type | text | "new_seats" \| "price_drop" \| "seats_vanishing" |
| title | text | |
| body | text | |
| route_data | jsonb | snapshot of what triggered it |
| read | boolean | |
| emailed | boolean | |
| created_at | timestamp | |

### `sas_sessions`
| Column | Type | Notes |
|--------|------|-------|
| id | serial | PK |
| cookies | jsonb | |
| bearer_token | text | |
| expires_at | timestamp | |
| refreshed_at | timestamp | |
| status | text | "active" \| "expired" \| "refreshing" |

---

## 7. Cron Jobs

All schedules, route lists, and trigger logic are **configurable** — stored in a config module that can be changed without code modifications.

### Jobs

| Job | Default schedule | What it does |
|-----|-----------------|-------------|
| `poll-availability` | Every 30 min | Hits cached calendar endpoint for tracked routes. Updates `availability_cache`. |
| `verify-bonus` | Every 2 hours | For routes where calendar shows seats, hits `/api/offers/flights` to verify bonus tickets. Needs auth session. |
| `refresh-session` | Every 6 hours | Checks SAS session validity. If expired, triggers Browserbase to harvest a fresh token. |

### Alert flow

```
poll-availability runs
    │
    ├─ Compare new data with availability_cache
    │
    ├─ New seats found? (e.g. OSL→BKK, Mar 15, Business)
    │
    ├─ Query route_subscriptions for matching watchers
    │
    ├─ Create notification record per matched user
    │
    ├─ Send email via Resend (with direct SAS booking link)
    │
    └─ Done
```

### Polling strategy (configurable)

By default: poll routes that have at least one active subscription + a configurable base set of popular routes for the deals page. This keeps API call volume low while ensuring the deals page always has fresh data.

Easily changeable to: poll all known routes, poll only subscribed routes, custom route lists, different schedules per route tier, etc.

---

## 8. Visual Design

**Direction:** Nordic Clean

- Light background (`#f8f9fb` / white)
- Indigo accent color (`#6366f1`)
- Clean typography (system font stack)
- Crisp borders, subtle shadows
- Generous white space
- Feels like a modern SaaS product (Vercel/Linear aesthetic)

### Component library

shadcn/ui provides the base components (buttons, cards, inputs, dialogs, tables, badges). Customized with the Nordic Clean color palette via Tailwind theme config.

---

## 9. External Services

| Service | Tier | Purpose | Limits |
|---------|------|---------|--------|
| Vercel | Free (Hobby) | Hosting, cron | 100GB bandwidth, cron jobs |
| Neon | Free | PostgreSQL | 0.5 GB storage, 190 compute hours |
| Browserbase | Free | Headless Chrome | 60 min/month browser time |
| Resend | Free | Email | 100 emails/day |
| Google OAuth | Free | Sign-in | Unlimited |

All free tiers are sufficient for a small friend/family user group.

---

## 10. What's NOT in scope

- Mobile app (responsive website is enough)
- Multi-language support
- Payment/monetization
- Public registration (small group only, though no hard gate — just not marketed)
- Push notifications (email + in-site notifications cover it)
- Flight booking (we link to SAS, don't handle booking)
