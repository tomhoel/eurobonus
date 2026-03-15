"use client";

import { useState, useMemo } from "react";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Calendar, ChevronLeft, ChevronRight } from "lucide-react";

const mono = "font-[family-name:var(--font-geist-mono)]";

interface DateRangePickerProps {
  dateFrom: string;
  dateTo: string;
  month: string;
  onDateChange: (from: string, to: string) => void;
  onMonthChange: (month: string) => void;
}

const MONTH_NAMES = ["January","February","March","April","May","June","July","August","September","October","November","December"];

export function DateRangePicker({ dateFrom, month, onDateChange, onMonthChange }: DateRangePickerProps) {
  const [open, setOpen] = useState(false);
  const today = new Date();
  const currentYM = month || `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, "0")}`;
  const viewYear = parseInt(currentYM.slice(0, 4), 10);
  const viewMonth = parseInt(currentYM.slice(4, 6), 10) - 1;

  const months = useMemo(() => {
    const r: { value: string; label: string; short: string }[] = [];
    const now = new Date();
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() + i, 1);
      r.push({ value: `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`, label: `${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}`, short: MONTH_NAMES[d.getMonth()].slice(0, 3) });
    }
    return r;
  }, []);

  const days = useMemo(() => {
    const first = new Date(viewYear, viewMonth, 1);
    const last = new Date(viewYear, viewMonth + 1, 0);
    const pad = first.getDay() === 0 ? 6 : first.getDay() - 1;
    const r: (Date | null)[] = [];
    for (let i = 0; i < pad; i++) r.push(null);
    for (let d = 1; d <= last.getDate(); d++) r.push(new Date(viewYear, viewMonth, d));
    return r;
  }, [viewYear, viewMonth]);

  const nav = (delta: number) => {
    const d = new Date(viewYear, viewMonth + delta, 1);
    onMonthChange(`${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  const fmt = (s: string) => { if (!s) return ""; const d = new Date(s); return d.toLocaleDateString("en-US", { month: "short", day: "numeric" }); };
  const isPast = (d: Date) => { const t = new Date(); t.setHours(0,0,0,0); return d < t; };
  const isTd = (d: Date) => { const t = new Date(); return d.getDate()===t.getDate()&&d.getMonth()===t.getMonth()&&d.getFullYear()===t.getFullYear(); };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[hsla(0,0%,100%,.03)]">
        <Calendar className="size-4 shrink-0 text-[hsla(0,0%,100%,.2)]" />
        <div>
          <div className={`text-[10px] font-medium uppercase tracking-[0.06em] text-[hsla(0,0%,100%,.3)] ${mono}`}>
            Date
          </div>
          {dateFrom ? (
            <div className={`mt-0.5 text-[15px] font-semibold text-white ${mono}`}>{fmt(dateFrom)}</div>
          ) : (
            <div className="mt-0.5 text-[14px] text-[hsla(0,0%,100%,.2)]">Select date</div>
          )}
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-[300px] border-[hsla(0,0%,100%,.08)] bg-[#0a0a0a] p-4" align="start">
        {/* Quick months */}
        <div className="mb-3 flex gap-1">
          {months.slice(0, 6).map((m) => (
            <button key={m.value} onClick={() => onMonthChange(m.value)}
              className={`flex-1 rounded py-1 text-[10px] transition-colors ${mono} ${currentYM === m.value ? "bg-emerald-500/15 text-emerald-400" : "text-[hsla(0,0%,100%,.22)] hover:text-[hsla(0,0%,100%,.4)]"}`}>
              {m.short}
            </button>
          ))}
        </div>
        {/* Nav */}
        <div className="mb-2 flex items-center justify-between">
          <button onClick={() => nav(-1)} className="rounded p-1 text-[hsla(0,0%,100%,.22)] hover:text-[hsla(0,0%,100%,.5)]"><ChevronLeft className="size-3.5" /></button>
          <span className={`text-[12px] text-[hsla(0,0%,100%,.45)] ${mono}`}>{MONTH_NAMES[viewMonth]} {viewYear}</span>
          <button onClick={() => nav(1)} className="rounded p-1 text-[hsla(0,0%,100%,.22)] hover:text-[hsla(0,0%,100%,.5)]"><ChevronRight className="size-3.5" /></button>
        </div>
        {/* Headers */}
        <div className="mb-0.5 grid grid-cols-7 text-center">
          {["M","T","W","T","F","S","S"].map((d,i)=>(
            <div key={i} className={`py-1 text-[9px] text-[hsla(0,0%,100%,.15)] ${mono}`}>{d}</div>
          ))}
        </div>
        {/* Days */}
        <div className="grid grid-cols-7 gap-px">
          {days.map((day,i) => {
            if (!day) return <div key={`p${i}`} />;
            const ds = `${day.getFullYear()}-${String(day.getMonth()+1).padStart(2,"0")}-${String(day.getDate()).padStart(2,"0")}`;
            const sel = ds === dateFrom;
            return (
              <button key={ds} disabled={isPast(day)} onClick={() => { onDateChange(ds,ds); setOpen(false); }}
                className={`rounded py-1.5 text-[11px] transition-colors ${mono} ${
                  sel ? "bg-emerald-500 font-bold text-white"
                  : isPast(day) ? "cursor-not-allowed text-[hsla(0,0%,100%,.06)]"
                  : isTd(day) ? "text-emerald-400"
                  : "text-[hsla(0,0%,100%,.3)] hover:bg-[hsla(0,0%,100%,.05)]"
                }`}>
                {day.getDate()}
              </button>
            );
          })}
        </div>
        <div className="mt-3 border-t border-[hsla(0,0%,100%,.06)] pt-2">
          <select value={currentYM} onChange={(e) => onMonthChange(e.target.value)}
            className={`w-full rounded border border-[hsla(0,0%,100%,.06)] bg-transparent px-2 py-1 text-[10px] text-[hsla(0,0%,100%,.35)] outline-none ${mono}`}>
            {months.map((m)=>(<option key={m.value} value={m.value}>{m.label}</option>))}
          </select>
        </div>
      </PopoverContent>
    </Popover>
  );
}
