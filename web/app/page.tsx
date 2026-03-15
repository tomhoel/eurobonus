import Image from "next/image";
import Link from "next/link";
import { HoverCard, HoverRow } from "@/components/hover-card";

const mono = "font-[family-name:var(--font-geist-mono)]";

export default function Home() {
  return (
    <>
      {/* ═══ SECTION 1: HERO — centered headline + sub + 2 CTAs ═══ */}
      <section className="relative overflow-hidden pb-16 pt-[min(18vh,160px)]">
        {/* Gradient orb behind headline */}
        <div className="pointer-events-none absolute left-1/2 top-0 h-[600px] w-[1000px] -translate-x-1/2">
          <div className="h-full w-full rounded-full opacity-30 blur-[100px]" style={{ background: "conic-gradient(from 180deg at 50% 50%, #1e3a8a 0deg, #7c3aed 120deg, #2563eb 240deg, #1e3a8a 360deg)" }} />
        </div>

        <div className="relative mx-auto max-w-[1200px] px-6 text-center">
          <h1
            className="mx-auto max-w-[900px] font-bold"
            style={{
              fontSize: "clamp(44px, 7.5vw, 80px)",
              lineHeight: 1.05,
              letterSpacing: "-0.04em",
              background: "linear-gradient(180deg, #fff 30%, hsla(0,0%,100%,.38) 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            Find and book on the EuroBonus network.
          </h1>

          <p className="mx-auto mt-6 max-w-[600px] text-[18px] leading-[1.65] text-[hsla(0,0%,100%,.48)]">
            hellasus.no scans the SAS booking engine every 30 minutes, verifies genuine bonus seats, and alerts you before they vanish.
          </p>

          <div className="mt-10 flex items-center justify-center gap-3">
            <Link href="/search" className="inline-flex h-[44px] items-center gap-2 rounded-[8px] bg-white px-5 text-[14px] font-medium text-black transition hover:bg-white/90">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg>
              Start Searching
            </Link>
            <Link href="/deals" className="inline-flex h-[44px] items-center rounded-[8px] border border-[hsla(0,0%,100%,.14)] px-5 text-[14px] font-medium text-[hsla(0,0%,100%,.63)] transition hover:border-[hsla(0,0%,100%,.25)] hover:text-[hsla(0,0%,100%,.85)]">
              View Deals
            </Link>
          </div>
        </div>

        {/* Hero visual — terminal window */}
        <div className="relative mx-auto mt-16 max-w-[960px] px-6">
          <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] shadow-[0_20px_60px_-15px_rgba(0,0,0,.6)]">
            {/* Window chrome */}
            <div className="flex items-center gap-2 border-b border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.025)] px-4 py-[10px]">
              <div className="flex gap-[6px]">
                {[0, 1, 2].map((d) => <div key={d} className="h-[12px] w-[12px] rounded-full bg-[hsla(0,0%,100%,.07)]" />)}
              </div>
              <div className="ml-3 flex items-center gap-2">
                <span className={`text-[12px] text-[hsla(0,0%,100%,.22)] ${mono}`}>live — bonus seat availability</span>
              </div>
              <div className="ml-auto flex items-center gap-[6px]">
                <span className="h-[6px] w-[6px] rounded-full bg-emerald-500" />
                <span className="text-[11px] text-[hsla(0,0%,100%,.18)]">updated 2 min ago</span>
              </div>
            </div>
            {/* Table head */}
            <div className={`flex items-center border-b border-[hsla(0,0%,100%,.06)] px-5 py-[10px] text-[11px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.22)] ${mono}`}>
              <span className="w-[160px]">Route</span>
              <span className="w-[180px]">City pair</span>
              <span className="flex-1">Date</span>
              <span className="w-[90px] text-right">Economy</span>
              <span className="w-[90px] text-right">Business</span>
              <span className="w-[80px] text-right">Status</span>
            </div>
            {/* Rows */}
            {[
              { r: "OSL → BKK", c: "Oslo → Bangkok", d: "Mar 15", e: "30,000", b: "60,000", ok: true, s: 4 },
              { r: "CPH → NRT", c: "Copenhagen → Tokyo", d: "Apr 03", e: "30,000", b: "60,000", ok: true, s: 2 },
              { r: "ARN → SIN", c: "Stockholm → Singapore", d: "Mar 22", e: "30,000", b: "—", ok: false, s: 6 },
              { r: "CDG → HND", c: "Paris → Haneda", d: "Apr 10", e: "—", b: "60,000", ok: true, s: 1 },
              { r: "AMS → PEK", c: "Amsterdam → Beijing", d: "May 01", e: "30,000", b: "—", ok: false, s: 3 },
              { r: "LHR → KIX", c: "London → Osaka", d: "Jun 14", e: "30,000", b: "60,000", ok: true, s: 3 },
            ].map((r, i) => (
              <HoverRow key={i}>
                <span className={`w-[160px] font-medium text-[hsla(0,0%,100%,.75)] ${mono}`}>{r.r}</span>
                <span className="w-[180px] text-[13px] text-[hsla(0,0%,100%,.25)]">{r.c}</span>
                <span className="flex-1 text-[13px] text-[hsla(0,0%,100%,.25)]">{r.d}, 2026</span>
                <span className={`w-[90px] text-right text-[13px] ${r.e !== "—" ? "text-[hsla(0,0%,100%,.45)]" : "text-[hsla(0,0%,100%,.12)]"} ${mono}`}>{r.e}</span>
                <span className={`w-[90px] text-right text-[13px] ${r.ok ? "font-medium text-emerald-500" : "text-[hsla(0,0%,100%,.12)]"} ${mono}`}>{r.b}</span>
                <span className="flex w-[80px] items-center justify-end gap-[5px] text-[11px]">
                  {r.ok ? (
                    <><span className="h-[5px] w-[5px] rounded-full bg-emerald-500" /><span className="text-emerald-500/70">{r.s}</span></>
                  ) : (
                    <span className="text-[hsla(0,0%,100%,.15)]">—</span>
                  )}
                </span>
              </HoverRow>
            ))}
            <div className={`flex items-center justify-between border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.025)] px-5 py-[10px] text-[11px] text-[hsla(0,0%,100%,.15)] ${mono}`}>
              <span>EuroBonus bonus fares · points only</span>
              <span>hellasus.no</span>
            </div>
          </div>
          {/* Bottom fade */}
          <div className="pointer-events-none absolute -bottom-16 left-0 right-0 h-16 bg-gradient-to-b from-transparent to-black" />
        </div>
      </section>

      {/* ═══ SECTION 2: SOCIAL PROOF — 3 metrics in a row ═══ */}
      <section className="border-y border-[hsla(0,0%,100%,.06)]">
        <div className="mx-auto grid max-w-[1200px] grid-cols-3 px-6">
          {[
            { metric: "5.8×", desc: "better point value vs revenue tickets" },
            { metric: "30 min", desc: "scan interval across all routes" },
            { metric: "150+", desc: "SkyTeam routes monitored live" },
          ].map((item, i) => (
            <div key={i} className={`py-10 text-center ${i > 0 ? "border-l border-[hsla(0,0%,100%,.06)]" : ""}`}>
              <div className={`text-[28px] font-bold tracking-[-0.02em] ${mono}`}>{item.metric}</div>
              <div className="mt-1 text-[13px] text-[hsla(0,0%,100%,.32)]">{item.desc}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ SECTION 3: "YOUR AWARD, VERIFIED" — 3 feature cards (dark bg) ═══ */}
      <section className="px-6 py-[100px]">
        <div className="mx-auto max-w-[1200px]">
          <div className="mb-14 max-w-[500px]">
            <p className="mb-3 text-[14px] font-medium text-blue-400">Your award, verified.</p>
            <h2 className="text-[clamp(28px,3.5vw,44px)] font-bold leading-[1.1] tracking-[-0.035em]">
              Real-time data, bonus detection, and alerts included.
            </h2>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            {/* Card 1 — tall with code block */}
            <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.025)]">
              <div className="p-7">
                <h3 className="mb-2 text-[18px] font-semibold">Real-time engine</h3>
                <p className="text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.4)]">
                  We query the SAS offers API — the same endpoint used by the booking page. Cached calendars miss seats and show phantoms.
                </p>
              </div>
              <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] p-5">
                <pre className={`text-[12px] leading-[1.8] text-[hsla(0,0%,100%,.38)] ${mono}`}>
{`GET /api/offers/flights
  ?from=CPH&to=BKK
  &outDate=20260315
  &bookingFlow=points`}
                </pre>
              </div>
            </div>

            {/* Card 2 */}
            <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.025)]">
              <div className="p-7">
                <h3 className="mb-2 text-[18px] font-semibold">Bonus detection</h3>
                <p className="text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.4)]">
                  The calendar says &ldquo;5 Business seats.&rdquo; We tell you 3 are revenue at 414k pts and 2 are bonus at 60k pts. Only the bonus ones matter.
                </p>
              </div>
              <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] p-5">
                <div className="flex items-center justify-between py-2 text-[13px]">
                  <span className="text-[hsla(0,0%,100%,.3)]">Revenue</span>
                  <span className={`text-[hsla(0,0%,100%,.2)] ${mono}`}>414,340 pts</span>
                </div>
                <div className="flex items-center justify-between border-t border-[hsla(0,0%,100%,.05)] py-2 text-[13px]">
                  <span className="flex items-center gap-2 text-emerald-400">
                    <span className="h-[5px] w-[5px] rounded-full bg-emerald-400" />
                    Bonus
                  </span>
                  <span className={`font-medium text-emerald-400 ${mono}`}>60,000 pts</span>
                </div>
              </div>
            </div>

            {/* Card 3 */}
            <div className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.025)]">
              <div className="p-7">
                <h3 className="mb-2 text-[18px] font-semibold">Instant alerts</h3>
                <p className="text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.4)]">
                  Subscribe to any route and cabin class. The second a bonus seat appears, you get an email with the exact point cost and a direct SAS booking link.
                </p>
              </div>
              <div className="border-t border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] p-5">
                <div className="rounded-lg border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)] p-4">
                  <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.2)]">New alert</div>
                  <div className="text-[14px] font-medium">Business seats: OSL → BKK</div>
                  <div className="mt-1 text-[12px] text-[hsla(0,0%,100%,.3)]">4 bonus seats · 60,000 pts · Mar 15</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ SECTION 4: ADDITIONAL FEATURES — 2×2 grid ═══ */}
      <section className="border-t border-[hsla(0,0%,100%,.06)] px-6 py-[100px]">
        <div className="mx-auto max-w-[1200px]">
          <div className="grid gap-4 sm:grid-cols-2">
            <HoverCard>
              <h3 className="mb-2 text-[18px] font-semibold">SkyTeam network</h3>
              <p className="mb-6 text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.4)]">
                Search partner awards on Air France, KLM, Delta, Korean Air — connections SAS doesn&apos;t surface in their own calendar.
              </p>
              <div className="flex flex-wrap gap-[6px]">
                {["SK", "AF", "KL", "DL", "KE", "MU", "VN", "GA", "CI", "SU"].map((c) => (
                  <span key={c} className={`rounded border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] px-[10px] py-[4px] text-[12px] text-[hsla(0,0%,100%,.3)] ${mono}`}>{c}</span>
                ))}
              </div>
            </HoverCard>
            <HoverCard>
              <h3 className="mb-2 text-[18px] font-semibold">150+ destinations</h3>
              <p className="mb-6 text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.4)]">
                The full SAS award route network mapped. Oslo, Copenhagen, Stockholm, Paris, Amsterdam — to Bangkok, Tokyo, Singapore, New York.
              </p>
              <div className="flex flex-wrap gap-[6px]">
                {["OSL", "CPH", "ARN", "CDG", "AMS", "→", "BKK", "NRT", "SIN", "JFK", "HND", "KIX"].map((c, i) => (
                  <span key={i} className={`${c === "→" ? "text-[hsla(0,0%,100%,.15)]" : `rounded border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.03)] px-[10px] py-[4px] text-[hsla(0,0%,100%,.3)]`} text-[12px] ${mono}`}>{c}</span>
                ))}
              </div>
            </HoverCard>
          </div>
        </div>
      </section>

      {/* ═══ SECTION 5: HOW IT WORKS — full-width dark band ═══ */}
      <section className="border-y border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] px-6 py-[100px]">
        <div className="mx-auto max-w-[1200px]">
          <div className="mb-14 text-center">
            <p className="mb-3 text-[14px] font-medium text-blue-400">How it works</p>
            <h2 className="text-[clamp(28px,3.5vw,44px)] font-bold leading-[1.1] tracking-[-0.035em]">
              Search. Watch. Book.
            </h2>
          </div>

          <div className="mx-auto grid max-w-[900px] gap-0 overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.08)] sm:grid-cols-3">
            {[
              { n: "01", t: "Search", d: "Pick a route. We query the booking engine — real-time availability, not the stale daily calendar cache." },
              { n: "02", t: "Watch", d: "Subscribe to routes. We scan every 30 min and email you the instant genuine bonus seats appear." },
              { n: "03", t: "Book", d: "Click through to SAS with your flight pre-selected. Economy from 5k, business from 20k–60k points depending on route." },
            ].map((s, i) => (
              <div key={s.n} className={`bg-[hsla(0,0%,100%,.02)] p-8 ${i > 0 ? "border-l border-[hsla(0,0%,100%,.06)]" : ""}`}>
                <span className={`text-[11px] font-medium text-[hsla(0,0%,100%,.2)] ${mono}`}>{s.n}</span>
                <h3 className="mt-3 text-[18px] font-semibold">{s.t}</h3>
                <p className="mt-3 text-[14px] leading-[1.7] text-[hsla(0,0%,100%,.38)]">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ SECTION 6: PRICING COMPARISON — side by side ═══ */}
      <section className="px-6 py-[100px]">
        <div className="mx-auto max-w-[1200px]">
          <div className="mb-14 text-center">
            <h2 className="text-[clamp(28px,3.5vw,44px)] font-bold leading-[1.1] tracking-[-0.035em]">
              Same flight. <span className="text-[hsla(0,0%,100%,.3)]">Different price.</span>
            </h2>
            <p className="mt-4 text-[16px] text-[hsla(0,0%,100%,.4)]">
              CPH → Bangkok, Business class. The calendar shows both as &ldquo;available.&rdquo;
            </p>
          </div>

          <div className="mx-auto grid max-w-[640px] gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)] p-8">
              <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.08em] text-[hsla(0,0%,100%,.22)]">Revenue ticket</div>
              <div className={`mt-3 text-[40px] font-bold tracking-[-0.03em] text-[hsla(0,0%,100%,.18)] ${mono}`}>414,340</div>
              <div className="text-[13px] text-[hsla(0,0%,100%,.18)]">pts</div>
              <div className="mt-6 space-y-[10px] border-t border-[hsla(0,0%,100%,.05)] pt-5 text-[13px]">
                <div className="flex justify-between"><span className="text-[hsla(0,0%,100%,.22)]">Cash price</span><span className="text-[hsla(0,0%,100%,.3)]">19,067 NOK</span></div>
                <div className="flex justify-between"><span className="text-[hsla(0,0%,100%,.22)]">Per point</span><span className={`text-[hsla(0,0%,100%,.22)] ${mono}`}>0.046 NOK</span></div>
              </div>
            </div>
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.03] p-8">
              <div className="mb-1 text-[11px] font-medium uppercase tracking-[0.08em] text-emerald-400">Bonus ticket ✓</div>
              <div className={`mt-3 text-[40px] font-bold tracking-[-0.03em] text-white ${mono}`}>60,000</div>
              <div className="text-[13px] text-emerald-400/50">pts</div>
              <div className="mt-6 space-y-[10px] border-t border-emerald-500/10 pt-5 text-[13px]">
                <div className="flex justify-between"><span className="text-[hsla(0,0%,100%,.22)]">Cabin</span><span className="text-[hsla(0,0%,100%,.5)]">Business</span></div>
                <div className="flex justify-between"><span className="text-[hsla(0,0%,100%,.22)]">Per point</span><span className={`text-emerald-400 ${mono}`}>0.32 NOK</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ SECTION 7: "DEPLOY" CTA — centered like Vercel ═══ */}
      <section className="relative overflow-hidden border-t border-[hsla(0,0%,100%,.06)] px-6 py-[120px]">
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-[400px] w-[700px] -translate-x-1/2 -translate-y-1/2 rounded-full blur-[120px]" style={{ background: "radial-gradient(circle, hsla(217,91%,60%,.1) 0%, transparent 70%)" }} />
        <div className="relative mx-auto max-w-[560px] text-center">
          <h2 className="text-[clamp(32px,4.5vw,52px)] font-bold leading-[1.08] tracking-[-0.04em]">
            Start searching in seconds.
          </h2>
          <p className="mt-5 text-[16px] leading-[1.6] text-[hsla(0,0%,100%,.4)]">
            Set an alert, close the tab. We&apos;ll email you when seats open.
          </p>
          <div className="mt-10 flex items-center justify-center gap-3">
            <a href="/search" className="inline-flex h-[44px] items-center rounded-[8px] bg-white px-6 text-[14px] font-medium text-black transition hover:bg-white/90">
              Start Searching
            </a>
          </div>
          <p className="mt-5 text-[13px] text-[hsla(0,0%,100%,.18)]">Free forever · No credit card</p>
        </div>
      </section>

      {/* ═══ SECTION 8: SECONDARY CTAs — 2 wide buttons like Vercel ═══ */}
      <section className="border-t border-[hsla(0,0%,100%,.06)] px-6 py-10">
        <div className="mx-auto grid max-w-[900px] gap-4 sm:grid-cols-2">
          <Link href="/deals" className="group flex items-center justify-between rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.02)] p-6 transition-colors hover:border-[hsla(0,0%,100%,.16)]">
            <div>
              <div className="text-[16px] font-semibold">Browse live deals</div>
              <div className="mt-1 text-[13px] text-[hsla(0,0%,100%,.35)]">See the best bonus availability right now</div>
            </div>
            <svg className="h-5 w-5 text-[hsla(0,0%,100%,.25)] transition group-hover:translate-x-1 group-hover:text-[hsla(0,0%,100%,.5)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M5 12h14M12 5l7 7-7 7" /></svg>
          </Link>
          <Link href="/alerts" className="group flex items-center justify-between rounded-xl border border-[hsla(0,0%,100%,.08)] bg-[hsla(0,0%,100%,.02)] p-6 transition-colors hover:border-[hsla(0,0%,100%,.16)]">
            <div>
              <div className="text-[16px] font-semibold">Set up alerts</div>
              <div className="mt-1 text-[13px] text-[hsla(0,0%,100%,.35)]">Get emailed when bonus seats appear</div>
            </div>
            <svg className="h-5 w-5 text-[hsla(0,0%,100%,.25)] transition group-hover:translate-x-1 group-hover:text-[hsla(0,0%,100%,.5)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path d="M5 12h14M12 5l7 7-7 7" /></svg>
          </Link>
        </div>
      </section>

      {/* ═══ FOOTER — multi-column like Vercel ═══ */}
      <footer className="border-t border-[hsla(0,0%,100%,.06)] px-6 pb-10 pt-14">
        <div className="mx-auto max-w-[1200px]">
          <div className="grid grid-cols-2 gap-8 sm:grid-cols-4 lg:grid-cols-5">
            {/* Brand col */}
            <div className="col-span-2 sm:col-span-1">
              <Image src="/sus-white.png" alt="SUS" width={94} height={36} className="mb-4 h-[31px] w-auto opacity-70" />
              <p className="text-[13px] text-[hsla(0,0%,100%,.2)]">Award search &amp; alerts<br />for SAS EuroBonus</p>
            </div>
            {/* Link columns */}
            {[
              { title: "Product", links: ["Search Flights", "Browse Deals", "Set Alerts", "Notifications"] },
              { title: "Resources", links: ["API Documentation", "SAS EuroBonus", "SkyTeam Partners", "Route Map"] },
              { title: "Routes", links: ["OSL → BKK", "CPH → NRT", "ARN → SIN", "CDG → HND"] },
              { title: "Company", links: ["hellasus.no", "GitHub", "Contact"] },
            ].map((col) => (
              <div key={col.title}>
                <h4 className="mb-4 text-[13px] font-medium text-[hsla(0,0%,100%,.4)]">{col.title}</h4>
                <ul className="space-y-[10px]">
                  {col.links.map((link) => (
                    <li key={link}><span className="cursor-pointer text-[13px] text-[hsla(0,0%,100%,.22)] transition hover:text-[hsla(0,0%,100%,.5)]">{link}</span></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          {/* Bottom bar */}
          <div className="mt-14 flex items-center justify-between border-t border-[hsla(0,0%,100%,.06)] pt-6">
            <span className="text-[12px] text-[hsla(0,0%,100%,.15)]">&copy; 2026 hellasus.no</span>
            <div className="flex items-center gap-[6px] text-[12px] text-[hsla(0,0%,100%,.15)]">
              <span className="h-[6px] w-[6px] rounded-full bg-emerald-500" />
              All systems operational
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
