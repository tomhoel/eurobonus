"use client";

import { useMemo } from "react";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { AvailabilityDate } from "@/lib/sas/types";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface ResultCalendarProps {
  dates: AvailabilityDate[];
  onSelectDate: (date: string) => void;
  selectedDate?: string;
}

export function ResultCalendar({ dates, onSelectDate, selectedDate }: ResultCalendarProps) {
  const availMap = useMemo(() => {
    const map = new Map<string, AvailabilityDate>();
    for (const d of dates) map.set(d.date, d);
    return map;
  }, [dates]);

  // Get all months that have data
  const months = useMemo(() => {
    if (dates.length === 0) return [];
    const set = new Set<string>();
    for (const d of dates) set.add(d.date.slice(0, 7));
    return [...set].sort();
  }, [dates]);

  const withAvail = dates.filter(
    (d) => d.economySeats + d.premiumSeats + d.businessSeats > 0,
  ).length;

  if (dates.length === 0) {
    return (
      <div className="py-16 text-center">
        <p className="text-[14px] text-[hsla(0,0%,100%,.22)]">
          Select origin and destination to see availability.
        </p>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="space-y-4">
        {/* Legend */}
        <div className="flex items-center justify-between">
          <div className={`text-[11px] text-[hsla(0,0%,100%,.2)] ${mono}`}>
            {withAvail} of {dates.length} dates have availability
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="flex gap-[2px]">
                {[0.08, 0.15, 0.25, 0.40].map((o, i) => (
                  <div key={i} className="size-[7px] rounded-sm" style={{ background: `hsla(160,84%,39%,${o})` }} />
                ))}
              </div>
              <span className={`text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>seats</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="size-[5px] rounded-full bg-emerald-400/60" />
              <span className={`text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>economy</span>
              <div className="ml-1 size-[5px] rounded-full bg-blue-400/60" />
              <span className={`text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>premium</span>
              <div className="ml-1 size-[5px] rounded-full bg-amber-400/60" />
              <span className={`text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>business</span>
            </div>
          </div>
        </div>

        {/* Two-column month grid */}
        <div className="grid gap-5 sm:grid-cols-2">
          {months.map((month) => (
            <MonthGrid
              key={month}
              month={month}
              availMap={availMap}
              onSelect={onSelectDate}
              selectedDate={selectedDate}
            />
          ))}
        </div>
      </div>
    </TooltipProvider>
  );
}

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function MonthGrid({
  month,
  availMap,
  onSelect,
  selectedDate,
}: {
  month: string;
  availMap: Map<string, AvailabilityDate>;
  onSelect: (date: string) => void;
  selectedDate?: string;
}) {
  const [yearStr, monthStr] = month.split("-");
  const year = parseInt(yearStr, 10);
  const monthIdx = parseInt(monthStr, 10) - 1;
  const firstDay = new Date(year, monthIdx, 1);
  const lastDay = new Date(year, monthIdx + 1, 0);
  const startPad = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const cells: { day: number; dateStr: string; isPast: boolean }[] = [];
  for (let d = 1; d <= lastDay.getDate(); d++) {
    const dateStr = `${month}-${String(d).padStart(2, "0")}`;
    const cellDate = new Date(year, monthIdx, d);
    cells.push({ day: d, dateStr, isPast: cellDate < today });
  }

  return (
    <div className="rounded-lg border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.015)] px-4 pb-3 pt-3">
      {/* Month header */}
      <div className="mb-3 flex items-baseline gap-1.5">
        <span className="text-[14px] font-semibold text-[hsla(0,0%,100%,.65)]">
          {MONTH_NAMES[monthIdx]}
        </span>
        <span className={`text-[12px] text-[hsla(0,0%,100%,.2)] ${mono}`}>{year}</span>
      </div>

      {/* Weekday headers */}
      <div className="mb-1 grid grid-cols-7 gap-1">
        {WEEKDAYS.map((d) => (
          <div key={d} className={`text-center text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-1">
        {/* Padding cells */}
        {Array.from({ length: startPad }, (_, i) => (
          <div key={`pad-${i}`} />
        ))}

        {/* Actual days */}
        {cells.map(({ day, dateStr, isPast }) => {
          const avail = availMap.get(dateStr);
          const isSelected = dateStr === selectedDate;

          if (isPast) {
            return (
              <div key={dateStr} className={`flex aspect-square items-center justify-center rounded text-[12px] text-[hsla(0,0%,100%,.06)] ${mono}`}>
                {day}
              </div>
            );
          }

          if (!avail) {
            return (
              <div key={dateStr} className={`flex aspect-square items-center justify-center rounded text-[12px] text-[hsla(0,0%,100%,.12)] ${mono}`}>
                {day}
              </div>
            );
          }

          const eco = avail.economySeats;
          const prem = avail.premiumSeats;
          const biz = avail.businessSeats;
          const total = eco + prem + biz;

          return (
            <Tooltip key={dateStr}>
              <TooltipTrigger
                onClick={() => onSelect(dateStr)}
                className={`relative flex aspect-square cursor-pointer flex-col items-center justify-center rounded transition-all ${
                  isSelected
                    ? "bg-emerald-500 shadow-[0_0_8px_hsla(160,84%,39%,0.25)]"
                    : total === 0
                    ? "hover:bg-[hsla(0,0%,100%,.04)]"
                    : "hover:ring-1 hover:ring-[hsla(0,0%,100%,.2)]"
                }`}
                style={!isSelected && total > 0 ? { background: heatBg(total) } : undefined}
              >
                <span className={`text-[12px] leading-none ${mono} ${
                  isSelected ? "font-bold text-white"
                  : total >= 5 ? "font-medium text-emerald-300/90"
                  : total > 0 ? "font-medium text-[hsla(0,0%,100%,.55)]"
                  : "text-[hsla(0,0%,100%,.12)]"
                }`}>
                  {day}
                </span>

                {total > 0 && !isSelected && (
                  <div className="mt-[2px] flex gap-[2px]">
                    {eco > 0 && <div className="size-[3px] rounded-full bg-emerald-400/60" />}
                    {prem > 0 && <div className="size-[3px] rounded-full bg-blue-400/60" />}
                    {biz > 0 && <div className="size-[3px] rounded-full bg-amber-400/60" />}
                  </div>
                )}
              </TooltipTrigger>
              <TooltipContent
                side="bottom"
                sideOffset={4}
                className="rounded-lg border border-[hsla(0,0%,100%,.08)] bg-[#111] px-3 py-2.5 text-white shadow-xl"
              >
                <DateTooltip avail={avail} />
              </TooltipContent>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );
}

function DateTooltip({ avail }: { avail: AvailabilityDate }) {
  const formatted = new Date(avail.date).toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
  });
  const total = avail.economySeats + avail.premiumSeats + avail.businessSeats;

  return (
    <div className={`min-w-[140px] ${mono}`}>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[11px] font-semibold text-white">{formatted}</span>
        <span className={`text-[10px] ${total > 0 ? "text-emerald-400" : "text-[#555]"}`}>
          {total} seat{total !== 1 ? "s" : ""}
        </span>
      </div>
      <div className="space-y-1">
        <TipRow label="Economy" seats={avail.economySeats} dot="bg-emerald-400" />
        <TipRow label="Premium" seats={avail.premiumSeats} dot="bg-blue-400" />
        <TipRow label="Business" seats={avail.businessSeats} dot="bg-amber-400" />
      </div>
    </div>
  );
}

function TipRow({ label, seats, dot }: { label: string; seats: number; dot: string }) {
  return (
    <div className="flex items-center justify-between gap-4 text-[10px]">
      <div className="flex items-center gap-1.5">
        <div className={`size-[5px] rounded-full ${seats > 0 ? dot : "bg-[#333]"}`} />
        <span className={seats > 0 ? "text-[#bbb]" : "text-[#444]"}>{label}</span>
      </div>
      <span className={`${mono} ${seats > 0 ? "font-medium text-white" : "text-[#333]"}`}>{seats}</span>
    </div>
  );
}

function heatBg(total: number): string {
  if (total >= 8) return "hsla(160, 84%, 39%, 0.16)";
  if (total >= 5) return "hsla(160, 84%, 39%, 0.10)";
  if (total >= 3) return "hsla(160, 84%, 39%, 0.06)";
  if (total >= 2) return "hsla(38, 92%, 50%, 0.07)";
  return "hsla(0, 72%, 51%, 0.07)";
}
