"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ORIGINS, DESTINATIONS } from "@/lib/route-map";

export function SearchForm() {
  const router = useRouter();
  const [origin, setOrigin] = useState<string>("");
  const [destination, setDestination] = useState<string>("");
  const [month, setMonth] = useState<string>("");

  const months = Array.from({ length: 12 }, (_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() + i);
    return {
      value: `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`,
      label: d.toLocaleDateString("en-US", { year: "numeric", month: "long" }),
    };
  });

  function handleSearch() {
    if (!origin || !destination) return;
    const params = new URLSearchParams({ origin, destination });
    if (month) params.set("month", month);
    router.push(`/search?${params.toString()}`);
  }

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">
          From
        </label>
        <Select onValueChange={(v: string | null) => setOrigin(v ?? "")}>
          <SelectTrigger>
            <SelectValue placeholder="Origin" />
          </SelectTrigger>
          <SelectContent>
            {ORIGINS.map((a) => (
              <SelectItem key={a.code} value={a.code}>
                {a.code} — {a.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">
          To
        </label>
        <Select onValueChange={(v: string | null) => setDestination(v ?? "")}>
          <SelectTrigger>
            <SelectValue placeholder="Destination" />
          </SelectTrigger>
          <SelectContent>
            {DESTINATIONS.map((a) => (
              <SelectItem key={a.code} value={a.code}>
                {a.code} — {a.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex-1">
        <label className="mb-1 block text-xs font-medium text-muted-foreground">
          Month (optional)
        </label>
        <Select onValueChange={(v: string | null) => setMonth(v ?? "")}>
          <SelectTrigger>
            <SelectValue placeholder="Any month" />
          </SelectTrigger>
          <SelectContent>
            {months.map((m) => (
              <SelectItem key={m.value} value={m.value}>
                {m.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <Button
        onClick={handleSearch}
        className="bg-indigo-600 hover:bg-indigo-700"
      >
        Search
      </Button>
    </div>
  );
}
