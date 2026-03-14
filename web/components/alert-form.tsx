"use client";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ORIGINS, DESTINATIONS } from "@/lib/route-map";

interface Props {
  onCreated: () => void;
}

export function AlertForm({ onCreated }: Props) {
  const [origin, setOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [cabin, setCabin] = useState("any");
  const [saving, setSaving] = useState(false);

  async function handleSubmit() {
    if (!origin || !destination) return;
    setSaving(true);
    await fetch("/api/alerts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ origin, destination, cabinClass: cabin }),
    });
    setSaving(false);
    onCreated();
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
          Cabin
        </label>
        <Select onValueChange={(v: string | null) => setCabin(v ?? "any")} defaultValue="any">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="any">Any class</SelectItem>
            <SelectItem value="economy">Economy</SelectItem>
            <SelectItem value="premium">Premium</SelectItem>
            <SelectItem value="business">Business</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Button
        onClick={handleSubmit}
        disabled={saving}
        className="bg-indigo-600 hover:bg-indigo-700"
      >
        {saving ? "Adding..." : "Add Alert"}
      </Button>
    </div>
  );
}
