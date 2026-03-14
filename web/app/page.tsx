import Image from "next/image";
import { SearchForm } from "@/components/search-form";

export default function Home() {
  return (
    <div className="-mx-4 -mt-8">
      {/* Hero */}
      <section className="bg-gradient-to-b from-white via-indigo-50/60 to-indigo-100/40 px-6 pb-16 pt-20 text-center">
        <div className="mx-auto max-w-3xl space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-1.5">
            <svg className="h-3.5 w-3.5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
            <span className="text-xs font-semibold text-indigo-600">SAS EuroBonus Award Search</span>
          </div>

          <h1 className="text-5xl font-bold leading-[1.1] tracking-tight text-gray-900 sm:text-6xl">
            Find bonus seats<br />before they vanish
          </h1>

          <p className="mx-auto max-w-xl text-lg text-gray-500">
            Search real-time SAS and SkyTeam award availability.
            Get alerted the moment business class bonus seats open up.
          </p>

          <div className="mx-auto max-w-3xl rounded-2xl border bg-white p-4 shadow-lg shadow-gray-900/5">
            <SearchForm />
          </div>

          <div className="flex items-center justify-center gap-6 text-sm text-gray-400">
            <span>Tracking availability on</span>
            <span className="font-bold text-gray-500 tracking-wide">SAS</span>
            <span className="h-1 w-1 rounded-full bg-gray-300" />
            <span className="font-bold text-gray-500">Air France</span>
            <span className="h-1 w-1 rounded-full bg-gray-300" />
            <span className="font-bold text-gray-500 tracking-wide">KLM</span>
            <span className="h-1 w-1 rounded-full bg-gray-300" />
            <span className="font-bold text-gray-500">SkyTeam</span>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white px-6 py-20">
        <div className="mx-auto max-w-5xl space-y-12">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-600">How it works</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
              Award seats in three steps
            </h2>
            <p className="mt-3 text-gray-500">No guesswork. No stale data. Just real bonus availability.</p>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {[
              {
                num: "1",
                icon: (
                  <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                  </svg>
                ),
                title: "Search routes",
                desc: "Pick your origin, destination, and travel month. We check real-time SAS and SkyTeam partner availability instantly.",
              },
              {
                num: "2",
                icon: (
                  <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                ),
                title: "Set alerts",
                desc: "Watch the routes you care about. We'll email you the moment new bonus seats appear — before anyone else books them.",
              },
              {
                num: "3",
                icon: (
                  <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 0 0-2 2v3a2 2 0 1 1 0 4v3a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3a2 2 0 1 1 0-4V7a2 2 0 0 0-2-2H5z" />
                  </svg>
                ),
                title: "Book on SAS",
                desc: "Click through directly to the SAS booking page with your flight pre-selected. Grab those bonus seats before they vanish.",
              },
            ].map((step) => (
              <div key={step.num} className="rounded-2xl bg-gray-50 p-8 text-center">
                <div className="mx-auto mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-50">
                  <span className="text-lg font-bold text-indigo-600">{step.num}</span>
                </div>
                <div className="mb-4">{step.icon}</div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">{step.title}</h3>
                <p className="text-sm leading-relaxed text-gray-500">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features — Dark */}
      <section className="bg-slate-900 px-6 py-20">
        <div className="mx-auto max-w-5xl space-y-12">
          <div className="text-center">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-indigo-400">Why hellasus.no</p>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">
              The data SAS doesn&apos;t show you
            </h2>
            <p className="mx-auto mt-3 max-w-lg text-slate-400">
              SAS calendars are cached and misleading. We verify every seat in real-time.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-3">
            {[
              {
                icon: (
                  <svg className="h-5 w-5 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z" />
                  </svg>
                ),
                title: "Real-time verification",
                desc: "We hit the actual booking engine to confirm bonus seats exist — not just the stale daily cache.",
              },
              {
                icon: (
                  <svg className="h-5 w-5 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0M2 8c0-3.5 2.5-6.5 6-7M22 8c0-3.5-2.5-6.5-6-7" />
                  </svg>
                ),
                title: "Instant email alerts",
                desc: "The moment new bonus seats appear on your watched routes, you get an email. Book before they're gone.",
              },
              {
                icon: (
                  <svg className="h-5 w-5 text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path d="M3.85 8.62a4 4 0 0 1 4.78-2.65 6 6 0 0 1 6.74 0 4 4 0 0 1 4.78 2.65 4 4 0 0 1-1.46 4.34L12 18.5l-6.69-5.54a4 4 0 0 1-1.46-4.34z" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                ),
                title: "Bonus vs revenue filter",
                desc: "SAS shows 'available' seats that cost 5x more in points. We filter to real bonus tickets only — the ones worth booking.",
              },
            ].map((feat) => (
              <div key={feat.title} className="rounded-2xl border border-slate-700 bg-slate-800 p-7">
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-950">
                  {feat.icon}
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{feat.title}</h3>
                <p className="text-sm leading-relaxed text-slate-400">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-b from-indigo-50 to-gray-50 px-6 py-20 text-center">
        <div className="mx-auto max-w-xl space-y-8">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
            Stop missing bonus seats
          </h2>
          <p className="text-lg text-gray-500">
            Sign in with Google and set up your first alert in 30 seconds.
            We&apos;ll watch the routes — you just pack your bags.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a href="/api/auth/signin" className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-8 py-4 font-semibold text-white shadow-lg shadow-indigo-600/25 transition hover:bg-indigo-700">
              Sign in with Google
            </a>
            <a href="/search" className="inline-flex items-center gap-2 rounded-xl border border-gray-300 px-8 py-4 font-medium text-gray-500 transition hover:border-gray-400 hover:text-gray-700">
              Search without signing in
            </a>
          </div>
          <p className="text-sm text-gray-400">Free forever. No credit card. Just better award travel.</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 px-6 py-12">
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-col justify-between gap-8 sm:flex-row">
            <div className="space-y-2">
              <Image src="/sus.png" alt="SUS" width={100} height={40} className="h-10 w-auto brightness-0 invert" />
              <p className="text-sm text-slate-500">SAS EuroBonus award search & alerts</p>
            </div>
            <div className="flex gap-16">
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Product</h4>
                <div className="space-y-2 text-sm text-slate-500">
                  <p><a href="/search" className="hover:text-slate-300">Search Flights</a></p>
                  <p><a href="/deals" className="hover:text-slate-300">Browse Deals</a></p>
                  <p><a href="/alerts" className="hover:text-slate-300">Set Alerts</a></p>
                </div>
              </div>
              <div className="space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Resources</h4>
                <div className="space-y-2 text-sm text-slate-500">
                  <p>API Documentation</p>
                  <p>SAS EuroBonus</p>
                  <p>SkyTeam Partners</p>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-10 border-t border-slate-800 pt-6">
            <p className="text-xs text-slate-600">&copy; 2026 hellasus.no — Not affiliated with SAS or SkyTeam.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
