"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { NotificationItem } from "@/components/notification-item";

export default function NotificationsPage() {
  const { data: session, status } = useSession();
  const [items, setItems] = useState<any[]>([]);

  function load() {
    fetch("/api/notifications")
      .then((r) => r.json())
      .then((d) => setItems(d.notifications ?? []));
  }

  useEffect(() => {
    if (session) load();
  }, [session]);

  async function handleMarkRead(id: string) {
    await fetch("/api/notifications", {
      method: "PATCH",
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
        Sign in to view notifications.
      </p>
    );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-sm text-muted-foreground">
          Alerts when bonus seats appear on your watched routes.
        </p>
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No notifications yet.</p>
      ) : (
        <div className="space-y-2">
          {items.map((n) => (
            <NotificationItem
              key={n.id}
              notification={n}
              onMarkRead={handleMarkRead}
            />
          ))}
        </div>
      )}
    </div>
  );
}
