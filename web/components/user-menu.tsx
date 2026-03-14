"use client";
import { useSession, signIn, signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar";

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
      <DropdownMenuTrigger
        render={
          <Avatar className="h-8 w-8 cursor-pointer">
            <AvatarImage src={session.user?.image ?? undefined} />
            <AvatarFallback>{session.user?.name?.[0] ?? "U"}</AvatarFallback>
          </Avatar>
        }
        nativeButton={false}
      />
      <DropdownMenuContent align="end">
        <DropdownMenuItem render={<a href="/alerts" />}>
          My Alerts
        </DropdownMenuItem>
        <DropdownMenuItem render={<a href="/notifications" />}>
          Notifications
        </DropdownMenuItem>
        <DropdownMenuItem render={<a href="/settings" />}>
          Settings
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => signOut()}>Sign out</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
