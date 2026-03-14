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
    fetch("/api/alerts")
      .then((r) => r.json())
      .then((d) => setSubs(d.subscriptions ?? []));
  }

  useEffect(() => {
    if (session) load();
  }, [session]);

  async function handleDelete(id: string) {
    await fetch("/api/alerts", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    load();
  }

  if (status === "loading")
    return <p className="text-sm text-muted-foreground">Loading...</p>;
  if (!session)
    return (
      <p className="text-sm text-muted-foreground">
        Sign in with Google to set up alerts.
      </p>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">My Alerts</h1>
        <p className="text-sm text-muted-foreground">
          Get notified when bonus seats open up on your watched routes.
        </p>
      </div>

      <Card>
        <CardContent className="p-4">
          <AlertForm onCreated={load} />
        </CardContent>
      </Card>

      {subs.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No alerts yet. Add a route above to start watching.
        </p>
      ) : (
        <div className="space-y-2">
          {subs.map((s) => (
            <Card key={s.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <span className="font-medium">
                    {findAirport(s.origin)?.name ?? s.origin} →{" "}
                    {findAirport(s.destination)?.name ?? s.destination}
                  </span>
                  <Badge variant="outline" className="ml-2 text-xs">
                    {s.cabinClass}
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDelete(s.id)}
                >
                  Remove
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
