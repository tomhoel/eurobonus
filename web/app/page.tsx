import Image from "next/image";
import { SearchForm } from "@/components/search-form";

export default function Home() {
  return (
    <div className="-mx-4 -mt-8">
      {/* Hero */}
      <section className="relative overflow-hidden bg-[#08090e] px-6 pb-24 pt-24">
        {/* Aurora background effect */}
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -left-40 -top-40 h-[600px] w-[600px] rounded-full bg-indigo-600/15 blur-[120px]" />
          <div className="absolute -right-20 top-20 h-[500px] w-[500px] rounded-full bg-violet-600/10 blur-[100px]" />
          <div className="absolute bottom-0 left-1/3 h-[400px] w-[600px] rounded-full bg-blue-600/8 blur-[120px]" />
          {/* Grid overlay */}
          <div
            className="absolute inset-0 opacity-[0.03]"
            style={{
              backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
              backgroundSize: "60px 60px",
            }}
          />
        </div>

        <div className="relative mx-auto max-w-5xl">
          <div className="flex flex-col items-center text-center">
            {/* Badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 backdrop-blur-sm">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
              </span>
              <span className="text-xs font-medium tracking-wide text-white/60">Live tracking SAS &middot; SkyTeam &middot; 150+ routes</span>
            </div>

            {/* Headline */}
            <h1 className="max-w-4xl text-5xl font-extrabold leading-[1.05] tracking-tight text-white sm:text-7xl">
              Stop overpaying for
              <span className="relative mx-2 inline-block">
                <span className="relative z-10 bg-gradient-to-r from-indigo-400 via-violet-400 to-purple-400 bg-clip-text text-transparent"> award flights</span>
              </span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-white/40">
              We verify every bonus seat in real-time against the SAS booking engine. The calendar lies — we don&apos;t.
            </p>

            {/* CTA Row */}
            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
              <a
                href="/search"
                className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-indigo-600 px-8 py-4 font-semibold text-white shadow-2xl shadow-indigo-600/20 transition-all hover:shadow-indigo-600/40"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-violet-600 opacity-0 transition-opacity group-hover:opacity-100" />
                <svg className="relative h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                </svg>
                <span className="relative">Search availability</span>
              </a>
              <a href="/deals" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-4 font-medium text-white/60 backdrop-blur-sm transition-all hover:border-white/20 hover:text-white/80">
                Browse deals
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </a>
            </div>
          </div>

          {/* Search Card — floating glass */}
          <div className="mx-auto mt-16 max-w-3xl rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/20 backdrop-blur-xl">
            <SearchForm />
          </div>

          {/* Stats Row */}
          <div className="mx-auto mt-16 grid max-w-3xl grid-cols-2 gap-4 sm:grid-cols-4">
            {[
              { value: "150+", label: "Routes tracked" },
              { value: "30min", label: "Scan interval" },
              { value: "Real-time", label: "Bonus verification" },
              { value: "Free", label: "Always" },
            ].map((stat) => (
              <div key={stat.label} className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-5 text-center">
                <div className="text-2xl font-bold tracking-tight text-white">{stat.value}</div>
                <div className="mt-1 text-xs text-white/30">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Problem → Solution */}
      <section className="relative bg-[#08090e] px-6 py-24">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-0 h-px w-2/3 -translate-x-1/2 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-indigo-400">The problem</p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              SAS calendars are lying to you
            </h2>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            {/* Before */}
            <div className="rounded-2xl border border-red-500/20 bg-red-500/[0.03] p-8">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1">
                <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
                <span className="text-xs font-semibold text-red-400">Without hellasus.no</span>
              </div>
              <ul className="space-y-4">
                {[
                  "Calendar shows 5 Business seats — they're all revenue tickets at 414,000 pts",
                  "Data updates once per day — real seats vanish within hours",
                  "No way to know if seats are bonus or cash-converted",
                  "Manually checking routes every day hoping to get lucky",
                ].map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-relaxed text-white/50">
                    <svg className="mt-0.5 h-4 w-4 shrink-0 text-red-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            {/* After */}
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.03] p-8">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                <span className="text-xs font-semibold text-emerald-400">With hellasus.no</span>
              </div>
              <ul className="space-y-4">
                {[
                  "We verify against the booking engine — only real bonus seats shown",
                  "Scans every 30 minutes, alerts you instantly via email",
                  "Clear bonus vs revenue labels with exact points cost",
                  "Set it and forget it — we watch, you book",
                ].map((item) => (
                  <li key={item} className="flex gap-3 text-sm leading-relaxed text-white/50">
                    <svg className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path d="M5 12l5 5L20 7" />
                    </svg>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="relative bg-[#08090e] px-6 py-24">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-0 h-px w-2/3 -translate-x-1/2 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-5xl">
          <div className="mb-16 text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.25em] text-indigo-400">How it works</p>
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Three steps to the best seats
            </h2>
          </div>

          <div className="grid gap-1 sm:grid-cols-3">
            {[
              {
                step: "01",
                title: "Search",
                desc: "Pick your route and month. We query the SAS booking engine in real-time — not the stale daily cache.",
                icon: (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                  </svg>
                ),
              },
              {
                step: "02",
                title: "Watch",
                desc: "Set alerts on routes you care about. We scan every 30 minutes and email you the instant bonus seats appear.",
                icon: (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                ),
              },
              {
                step: "03",
                title: "Book",
                desc: "Click straight through to SAS with your flight pre-selected. Grab those 30,000-point business seats.",
                icon: (
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 0 0-2 2v3a2 2 0 1 1 0 4v3a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3a2 2 0 1 1 0-4V7a2 2 0 0 0-2-2H5z" />
                  </svg>
                ),
              },
            ].map((item) => (
              <div key={item.step} className="group rounded-2xl border border-white/5 bg-white/[0.02] p-8 transition-all hover:border-white/10 hover:bg-white/[0.04]">
                <div className="mb-6 flex items-center justify-between">
                  <span className="text-3xl font-black tracking-tighter text-white/10">{item.step}</span>
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-indigo-400 transition-colors group-hover:border-indigo-500/30 group-hover:bg-indigo-500/10">
                    {item.icon}
                  </div>
                </div>
                <h3 className="mb-2 text-xl font-bold text-white">{item.title}</h3>
                <p className="text-sm leading-relaxed text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value comparison — the knockout section */}
      <section className="relative bg-[#08090e] px-6 py-24">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-0 h-px w-2/3 -translate-x-1/2 bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        </div>

        <div className="relative mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-indigo-400">Real example</p>
          <h2 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">
            Copenhagen &rarr; Bangkok
          </h2>
          <p className="mt-3 text-white/40">Same flight. Wildly different prices.</p>

          <div className="mt-12 grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8">
              <div className="text-xs font-semibold uppercase tracking-widest text-white/30">Revenue ticket</div>
              <div className="mt-4 text-5xl font-black tracking-tight text-white/20">414,340</div>
              <div className="mt-1 text-sm text-white/30">points</div>
              <div className="mt-4 text-xs text-white/20">= 19,067 NOK cash value</div>
              <div className="mt-2 text-xs text-red-400/60">0.046 NOK per point</div>
            </div>
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/[0.04] p-8 ring-1 ring-emerald-500/10">
              <div className="text-xs font-semibold uppercase tracking-widest text-emerald-400">Bonus ticket</div>
              <div className="mt-4 text-5xl font-black tracking-tight text-white">108,000</div>
              <div className="mt-1 text-sm text-emerald-400/60">points</div>
              <div className="mt-4 text-xs text-white/40">Business class one-way</div>
              <div className="mt-2 text-xs text-emerald-400">We find these for you</div>
            </div>
          </div>

          <p className="mt-8 text-sm text-white/30">
            The calendar showed both as &ldquo;available.&rdquo; Only one is worth booking.
          </p>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative overflow-hidden bg-[#08090e] px-6 py-32">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute left-1/2 top-1/2 h-[500px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-600/10 blur-[120px]" />
        </div>

        <div className="relative mx-auto max-w-xl text-center">
          <h2 className="text-4xl font-extrabold tracking-tight text-white sm:text-5xl">
            Your next trip is<br />
            <span className="bg-gradient-to-r from-indigo-400 to-violet-400 bg-clip-text text-transparent">waiting</span>
          </h2>
          <p className="mt-6 text-lg text-white/40">
            Sign in, set an alert, go live your life. We&apos;ll ping you when the seats open.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="/api/auth/signin"
              className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl bg-white px-8 py-4 font-semibold text-gray-900 transition-all hover:shadow-xl hover:shadow-white/10"
            >
              Sign in with Google
            </a>
            <a href="/search" className="text-sm text-white/40 underline decoration-white/10 underline-offset-4 transition hover:text-white/60 hover:decoration-white/30">
              or search without an account
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-[#08090e] px-6 py-12">
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-col justify-between gap-10 sm:flex-row">
            <div className="space-y-3">
              <Image src="/sus.png" alt="SUS" width={80} height={32} className="h-8 w-auto rounded bg-white/90 px-1" />
              <p className="text-sm text-white/20">Award search & alerts for SAS EuroBonus</p>
            </div>
            <div className="flex gap-12 text-sm">
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-widest text-white/20">Product</h4>
                <div className="space-y-2 text-white/30">
                  <p><a href="/search" className="transition hover:text-white/60">Search</a></p>
                  <p><a href="/deals" className="transition hover:text-white/60">Deals</a></p>
                  <p><a href="/alerts" className="transition hover:text-white/60">Alerts</a></p>
                </div>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-widest text-white/20">Info</h4>
                <div className="space-y-2 text-white/30">
                  <p>SAS EuroBonus</p>
                  <p>SkyTeam Partners</p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-12 border-t border-white/5 pt-6">
            <p className="text-xs text-white/15">&copy; 2026 hellasus.no &mdash; Not affiliated with SAS or SkyTeam.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
