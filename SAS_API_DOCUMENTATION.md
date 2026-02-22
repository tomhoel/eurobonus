# SAS Award Finder API Documentation

> **Last Updated:** January 2026  
> **API Version:** v1  
> **Base URL:** `https://www.sas.no/bff/award-finder/destinations/v1`

## Overview

The SAS Award Finder API is an internal SAS API providing information about SkyTeam award ticket availability. Multiple endpoints exist with **different data freshness levels**—the calendar/routes endpoints are cached daily, while the offers endpoint provides real-time booking data. These APIs power the award search functionality on sas.no and can be used to monitor bonus ticket releases.

> [!NOTE]
> SAS joined **SkyTeam** in September 2024, leaving Star Alliance. Award availability now reflects SkyTeam partner airlines.

> [!IMPORTANT]
> This is an unofficial, undocumented API. SAS may change or restrict access at any time.

---

## Authentication

### Headers Required

All requests should include standard browser emulation headers to avoid immediate rejection.

```http
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
Accept: application/json
Accept-Language: en-US,en;q=0.9
Cookie: <session_cookies>  # Optional for basic queries, required for full pricing/offers
```

### Session Cookies

While some endpoints work without cookies, authenticated sessions (valid `auth0` and `session_id` cookies) are required for:
1. **Cloudflare Bypass**: Without a valid session or proper browser emulation, Cloudflare often blocks requests.
2. **Detailed Pricing**: The `/api/offers/flights` endpoint strictly requires a valid authenticated session.
3. **Higher Rate Limits**: Authenticated sessions generally tolerate higher request volumes.

---

## Endpoints

### 1. Get Award Availability (Calendar View)

Retrieves a calendar view of availability for a given route. Useful for finding dates with seats.

```http
GET /bff/award-finder/destinations/v1
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `market` | string | Yes | - | Market identifier (e.g., `no-no`, `se-sv`, `gb-en`) |
| `origin` | string | Yes | - | Origin airport IATA code (e.g., `OSL`, `CPH`) |
| `destinations` | string | No | `""` | Destination IATA code. Empty returns all available destinations. |
| `selectedMonth` | string | No | `""` | Filter by month in `YYYYMM` format (e.g., `202603`). |
| `passengers` | integer | No | `1` | Number of passengers (1-9). |
| `direct` | string | No | `"false"` | Filter direct flights only (`"true"`/`"false"`). |
| `availability` | string | No | `"true"` | `"true"` for seat counts, `"false"` for just a list of destinations. |
| `selectedFlightClass` | string | No | `""` | Filter by cabin class (see below). |

#### Cabin Codes

| Code | Class |
|------|-------|
| `AG` | Economy (SAS Go) |
| `AP` | Premium Economy (SAS Plus) |
| `AB` | Business Class |

#### Example CUrl

```bash
curl "https://www.sas.no/bff/award-finder/destinations/v1?market=no-no&origin=OSL&destinations=BKK&passengers=1&availability=true"
```

#### Response Structure

```json
[
  {
    "iataCode": "BKK",
    "cityName": "Bangkok",
    "availability": {
      "outbound": [
        { "date": "2026-03-15", "AG": 4, "AP": 2, "AB": 0 }
      ]
    }
  }
]
```

---

### 2. Get Flight Routes (Detailed Schedule)

Returns flight details for a specific date, inclusive of flight numbers, times, and connection info.

```http
GET /bff/award-finder/routes/v1
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `market` | string | Yes | Market identifier (e.g., `no-no`). |
| `origin` | string | Yes | Origin airport IATA code. |
| `destination` | string | Yes | Destination airport IATA code. |
| `departureDate` | string | Yes | Departure date in `YYYY-MM-DD` format. |
| `direct` | string | No | Filter direct flights only. |

#### Example CUrl

```bash
curl "https://www.sas.no/bff/award-finder/routes/v1?market=no-no&origin=OSL&destination=BKK&departureDate=2026-02-03"
```

---

### 3. Get Flight Offers (Exact Points Pricing)

Returns precise flight offers including **exact EuroBonus points cost**, taxes, and detailed fare rules. This is the booking engine backend.

> [!WARNING]
> This endpoint requires a valid, authenticated browser session (cookies) to work.

```http
GET /api/offers/flights
```

#### Query Parameters

| Parameter | Type | Required | Value / Description |
|-----------|------|----------|---------------------|
| `from` | string | Yes | Origin IATA code |
| `to` | string | Yes | Destination IATA code |
| `outDate` | string | Yes | Date in `YYYYMMDD` format |
| `adt` | integer | No | Adults (default: 1) |
| `bookingFlow` | string | Yes | `"points"` |
| `pos` | string | Yes | Point of sale (e.g., `"no"`) |
| `channel` | string | Yes | `"web"` |
| `displayType` | string | Yes | `"upsell"` |

#### Response Structure

The response is complex. The key data resides in `outboundFlights` -> `cabins` -> `products` -> `price`.

```json
{
  "outboundFlights": {
    "F0": {
      "segments": [...],
      "cabins": {
        "BUSINESS": {
           "products": {
              "O_1": {
                 "price": {
                    "points": 108000,
                    "totalTax": 1234.00,
                    "currency": "NOK"
                 }
              }
           }
        }
      }
    }
  }
}
```

---

### 4. Partner Award Search (SkyTeam)

Used specifically for searching flights on SkyTeam partners (Air France, KLM, etc.).

> [!NOTE]
> This endpoint is highly reliable for finding partner inventory that occasionally misses the cached calendars.

```http
GET /award-api/flights
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `origin` | string | Yes | Origin airport IATA code |
| `destination` | string | Yes | Destination airport IATA code |
| `outboundDate` | string | Yes | Date in `YYYY-MM-DD` format |
| `tripType` | string | Yes | `"one-way"` or `"round-trip"` |
| `adults` | integer | Yes | Number of adults |

---

### 5. Profile Points & Status

Returns current EuroBonus points balance, status tier, and member ID.

```http
GET /bff/profile/profiles/profile-button/v2
```

#### Response Example

```json
{
  "pointsBalance": 125000,
  "level": "GOLD",
  "memberId": "123456789",
  "expiryDate": "2026-12-31"
}
```

---

### 6. Saved Passengers

Retrieves names and details of travelers saved in the EuroBonus account.

```http
GET /bff/passengers/saved/v1
```

---

### 7. Route Network & Discovery

To avoid "guessing" valid routes, the API supports a discovery mode that maps every possible origin and destination combination in the SAS award network.

#### Mapping Logic
- **Discovery Tool**: `sas_route_discovery.py` performs a recursive crawl of the flight network.
- **Data Source**: `sas_route_map.json` contains the latest mapped routes.
- **Stats**: Currently 149+ unique destinations and 100+ proven origin cities are mapped.

#### Using the Map
Instead of brute-forcing all possible IATA codes, tools should iterate through the `sas_route_map.json` to find valid pairs.

```json
{
  "routes": {
    "CPH": [
      { "code": "BKK", "name": "Bangkok", "country": "Thailand" },
      { "code": "JFK", "name": "New York", "country": "USA" }
    ],
    "BKK": [
      { "code": "CPH", "name": "Copenhagen", "country": "Denmark" },
      { "code": "ARN", "name": "Stockholm", "country": "Sweden" }
    ]
  }
}
```

---

### 8. Frontend Deep-Link "APIs" & Scraping Targets

SAS provides structured frontend URLs that function similarly to an API by allowing you to deep-link directly into specific booking flows, pre-select flights, and enforce points-based searches. These URLs are ideal launch parameters for automated browsers (like `nodriver` or `playwright`) when simulating user flows.

#### A. The Booking Deep-Link API (`/book/flights/`)

This URL pattern allows you to bypass the search page and jump directly to flight selection or passenger details. 

**Base URL:** 
`https://www.sas.no/book/flights/`

**Query Parameters:**

| Parameter | Example Value | Description |
|-----------|---------------|-------------|
| `search` | `OW_OSL-BKK-20260225_a1c0i0y0` | **The Core Search String.** Format: `<TripType>_<Origin>-<Destination>-<Date>_<Passengers>`<br>- **TripType**: `OW` (One Way) or `RT` (Round Trip).<br>- **Date**: `YYYYMMDD` (For RT, use `YYYYMMDD-YYYYMMDD`).<br>- **Passengers**: `a` (Adult), `c` (Child), `i` (Infant), `y` (Youth). E.g., `a1c0i0y0` = 1 Adult. |
| `bookingFlow` | `points` | Forces the search to yield EuroBonus award availability rather than cash (`revenue`). |
| `out_class` | `ECONOMY` | Pre-selects the cabin class for the outbound journey (`ECONOMY`, `PREMIUM`, `BUSINESS`). |
| `out_sub_class` | `ECONOMY BONUS` | Pre-selects the specific fare product (e.g., `ECONOMY BONUS`, `PLUS BONUS`, `BUSINESS BONUS`). |
| `out_flight_number`| `SK459,SK973` | Comma-separated list of flight numbers to automatically select for the outbound journey. |
| `view` | `upsell` | Forces the expanded cabin upsell view. |
| `sortBy` | `rec` | Sorting order (`rec` = Recommended). |
| `filterBy` | `all` | Filter applied to the results. |

**Example Usage:** Jump directly to a pre-selected Business Bonus flight:
```text
https://www.sas.no/book/flights/?search=OW_OSL-BKK-20260225_a1c0i0y0&view=upsell&bookingFlow=points&sortBy=rec&filterBy=all&out_class=BUSINESS&out_sub_class=BUSINESS%20BONUS&out_flight_number=SK459,SK973
```

#### B. Discovery & Calendar Scraping Targets

These pages are React/Next.js applications that load availability data dynamically via internal XHR requests. When scraping these via browser automation, monitoring the Network tab allows you to intercept the underlying `/bff/` and `/api/` calls.

*   `https://www.sas.no/award-finder`: **The Award Calendar.** A dedicated interface for finding pure EuroBonus seats. Use this to visually scrape month-long cached award data.
*   `https://www.sas.no/lavpriskalender`: **The Low Fare Calendar.** Useful for scraping the lowest available cash fares across broad swaths of dates. Driven by SAS's internal low-fare offers API.
*   `https://www.sas.no/reisemal`: **Destinations Map.** Can be scraped to extract all active nodes in the SAS network, powering automated routing graphs.

---

## Critical: Data Freshness & Ticket Types

### Endpoint Data Freshness

> [!CAUTION]
> **The Ghost Availability Problem**: The award-finder endpoints are **cached and update only once per day**. 
> This means seats may appear on the calendar that are already gone, or (more likely) **real-time seats on specific dates may be MISSING from the calendar entirely**.
>
> *Example*: Searching CPH -> BKK for Feb 2026 may show no seats for Feb 11th in the calendar overview, but a specific direct probe for Feb 11th reveals 5+ seats.

| Endpoint | Update Frequency | Use Case |
|----------|------------------|----------|
| `/bff/award-finder/destinations/v1` | **Daily** (cached) | Quick calendar overview, finding dates with potential availability |
| `/bff/award-finder/routes/v1` | **Daily** (cached) | Flight times and connections |
| `/api/offers/flights` | **Real-time** | Actual bookable inventory, exact points pricing |
| `/award-api/flights` | **Real-time** | Actual partner/SkyTeam inventory |

**Example discrepancy observed:**
```
Award-finder (cached):  AG=10, AB=5
Offers API (real-time): ECONOMY=9 BONUS seats, BUSINESS=9 revenue seats (NO bonus)
```

The award-finder showed 5 Business seats, but **zero** were actual bonus tickets.

### Bonus Tickets vs Revenue Tickets

The `/api/offers/flights` endpoint distinguishes between two fundamentally different ticket types:

#### 1. Bonus/Award Tickets (`isStandardAward: true`)
- **Fixed EuroBonus point rates** (e.g., 30,000 pts for Economy long-haul)
- `basePrice: 0` (no cash equivalent)
- Best redemption value (~0.25+ NOK per point)
- Limited inventory released by SAS

#### 2. Revenue Tickets (paid with points)
- **Cash price converted to points** at ~20 pts = 1 NOK
- `basePrice` shows the cash equivalent
- Poor redemption value (~0.05 NOK per point)
- Always available if cash seats exist

#### Identifying Ticket Type in API Response

```json
// BONUS ticket (good value)
{
  "productName": "ECONOMY BONUS",
  "productCode": "SNEUES",
  "isStandardAward": true,
  "price": {
    "points": 30000,
    "basePrice": 0.0
  }
}

// REVENUE ticket (poor value)
{
  "productName": "BUSINESS",
  "productCode": "NEUBS",
  // Note: isStandardAward is missing or false
  "price": {
    "points": 414340,
    "basePrice": 19067.0   // Cash price in NOK
  }
}
```

#### Value Comparison Example (CPH→BKK)

| Ticket Type | Points | Cash Equiv | NOK/Point | Value |
|-------------|--------|------------|-----------|-------|
| Economy BONUS | 30,000 | N/A | ~0.27 | Excellent |
| Premium (revenue) | 159,714 | 7,286 NOK | 0.046 | Poor |
| Business (revenue) | 414,340 | 19,067 NOK | 0.046 | Poor |

> [!TIP]
> **Only book BONUS tickets** (`isStandardAward: true`) for good value. Revenue tickets cost ~5× more points for the same seat.

### Why Award-Finder Can Be Misleading

The award-finder calendar showing "AB: 5" (Business) does **not** guarantee Business bonus tickets exist. It may indicate:
1. Revenue Business seats (payable with points at poor rates)
2. Stale data from the daily cache
3. Seats that were booked since the last refresh

**Always verify with `/api/offers/flights`** before assuming bonus availability.

---

## Integration Guide for Tools

### JSON Schema for Pricing Extraction

When building tools to extract pricing, traverse the JSON object as follows:

1. Iterate over `outboundFlights` (keys like "F0", "F1"...).
2. Inside each flight, access `cabins`.
3. Iterate keys (e.g., "ECONOMY", "BUSINESS").
4. Iterate `products` to find the fare.
5. Extract `price.points` (integer) and `price.totalTax` (float).

### Rate Limiting & Handling 429s

The API is sensitive to high-frequency requests.

*   **Sequential Requests**: Add a delay of **2-5 seconds** between requests.
*   **Batching**: If scanning a year, break it into small chunks.
*   **Backoff**: If you receive HTTP 429 (Too Many Requests), pause for **>60 seconds** before retrying.

### Cloudflare & Bot Detection Evasion

SAS protects its endpoints—especially `/api/offers/flights`—with strict Cloudflare Turnstile and bot-detection heuristics. Standard scraping tools (e.g., `requests`, basic Puppeteer/Playwright) will almost always be met with a `403 Forbidden` or infinite CAPTCHA loops.

To consistently bypass this, our architecture leverages **undetected browser automation** specifically tuned to mimic human behavior and harvest necessary authentication tokens.

#### 1. Under-the-Hood: How `nodriver` Bypasses Cloudflare
The primary tool used for session capture is `nodriver` (an evolution of `undetected-chromedriver`). Key evasion strategies implemented in `capture_session.py`:

*   **CDP Protocol Instead of WebDriver**: `nodriver` interacts directly with the Chrome DevTools Protocol (CDP), avoiding the `window.navigator.webdriver = true` flag that explicitly announces automation frameworks.
*   **Headless Modes**: Running headless often triggers Cloudflare. If run headlessly (e.g., in Docker), specific arguments like `--disable-blink-features=AutomationControlled` must be injected.
*   **Network Interception (CDP)**: Instead of scraping the DOM, the script uses CDP network monitoring (`cdp.network.RequestWillBeSent`) to passively intercept the `Authorization` bearer token as the React app makes underlying API calls to `/award-api/flights`.
*   **Event Emulation**: Instead of instantly injecting text via DOM manipulation, the script falls back to slow, simulated keystrokes (`element_slow_type`) and CDP `insertText` tools.
*   **Third-Party Cookie Flags**: Cloudflare often demands third-party cookie access. The script launches Chrome with `--disable-features=ThirdPartyCookieDeprecation,SameSiteByDefaultCookies` to ensure Cloudflare's invisible frames evaluate successfully.

#### 2. The Multi-Layer Token Harvesting Strategy
Because Auth0 tokens are hidden across different browser layers, `capture_session.py` attempts a waterfall approach to extract the necessary `Bearer` token to use for headless API calls later:

1.  **CDP Inspection**: Listens to outbound network requests for the `Authorization` header.
2.  **Storage Scanning**: Injecting JavaScript to parse `localStorage` and `sessionStorage` for keys matching `@@auth0`.
3.  **IndexedDB Extraction**: Iterating through the browser's local databases for cached Auth0 session bodies.
4.  **Fetch Interception**: Mutating the `window.fetch` prototype in the browser context to catch tokens bound to XHR requests.

Once the `sas_session.json` (containing the cookies, token, and storage state) is generated, lightweight scripts (like `sas_search_api.py`) can inject these cookies into standard Python HTTP clients and achieve high-speed, headless API querying without triggering further Cloudflare blocks.

---

## Implementation Notes

This documentation is designed to be **language-agnostic** and usable by any tool, AI, or developer regardless of programming language.

### Translating Examples

- **curl examples** can be directly translated to any HTTP client library. The key elements are the URL, query parameters, headers, and HTTP method.
- **JSON response parsing** follows standard JSON conventions—use your language's native JSON parser.
- **Any HTTP library** that supports custom headers and cookie handling will work (e.g., `requests` in Python, `fetch` in JavaScript, `net/http` in Go, `HttpClient` in C#/.NET, etc.).

### Key Requirements for Any Implementation

1. **HTTP GET requests** with proper query string encoding
2. **Custom headers** (User-Agent, Accept, Accept-Language)
3. **Cookie storage and transmission** for authenticated endpoints
4. **JSON parsing** for response handling
5. **Error handling** for HTTP 429 (rate limiting) and 403 (bot detection)
