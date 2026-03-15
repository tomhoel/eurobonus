"use client";

import { Suspense } from "react";
import { SearchPage } from "./search-page";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl px-4 py-6">
          <div className="text-sm text-zinc-500">Loading search...</div>
        </div>
      }
    >
      <SearchPage />
    </Suspense>
  );
}
