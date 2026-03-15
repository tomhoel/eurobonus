"use client";
import { SessionProvider } from "next-auth/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionProvider
      // Prevent ClientFetchError from crashing React tree when DB is not configured
      refetchOnWindowFocus={false}
      refetchInterval={0}
    >
      {children}
    </SessionProvider>
  );
}
