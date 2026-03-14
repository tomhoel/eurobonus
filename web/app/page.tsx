import { SearchForm } from "@/components/search-form";

export default function Home() {
  return (
    <div className="space-y-12">
      <section className="space-y-4 pt-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Find SAS EuroBonus award seats
        </h1>
        <p className="mx-auto max-w-lg text-muted-foreground">
          Search real-time bonus ticket availability across SAS and SkyTeam
          partners. Set up alerts to get notified when seats open up.
        </p>
      </section>

      <section className="mx-auto max-w-3xl rounded-lg border bg-white p-6 shadow-sm">
        <SearchForm />
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border bg-white p-5">
          <h3 className="mb-1 font-semibold">Real-time data</h3>
          <p className="text-sm text-muted-foreground">
            Verified bonus seats from the SAS booking engine, not just cached
            calendars.
          </p>
        </div>
        <div className="rounded-lg border bg-white p-5">
          <h3 className="mb-1 font-semibold">Smart alerts</h3>
          <p className="text-sm text-muted-foreground">
            Sign in to watch routes and get emailed the moment bonus seats
            appear.
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
