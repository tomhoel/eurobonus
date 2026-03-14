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
