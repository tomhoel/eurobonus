"use client";

import { useState } from "react";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Users, ChevronDown, Check } from "lucide-react";
import type { CabinName } from "@/lib/sas/types";

const mono = "font-[family-name:var(--font-geist-mono)]";
type CabinOption = CabinName | "ANY";

interface CabinSelectorProps {
  value: CabinOption;
  onChange: (cabin: CabinOption) => void;
}

const OPTIONS: { value: CabinOption; label: string; desc: string }[] = [
  { value: "ANY", label: "Any class", desc: "All cabin classes" },
  { value: "ECONOMY", label: "Economy", desc: "SAS Go" },
  { value: "PREMIUM", label: "Premium", desc: "SAS Plus" },
  { value: "BUSINESS", label: "Business", desc: "SAS Business" },
];

export function CabinSelector({ value, onChange }: CabinSelectorProps) {
  const [open, setOpen] = useState(false);
  const selected = OPTIONS.find((o) => o.value === value) ?? OPTIONS[0];

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger className="flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-[hsla(0,0%,100%,.03)]">
        <Users className="size-4 shrink-0 text-[hsla(0,0%,100%,.2)]" />
        <div className="flex-1">
          <div className={`text-[10px] font-medium uppercase tracking-[0.06em] text-[hsla(0,0%,100%,.3)] ${mono}`}>
            Cabin
          </div>
          <div className={`mt-0.5 text-[15px] font-semibold text-white ${mono}`}>
            {selected.label}
          </div>
        </div>
        <ChevronDown className="size-3.5 text-[hsla(0,0%,100%,.2)]" />
      </PopoverTrigger>
      <PopoverContent className="w-[220px] border-[hsla(0,0%,100%,.08)] bg-[#0a0a0a] p-1" align="start">
        {OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => { onChange(opt.value); setOpen(false); }}
            className={`flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-left transition-colors ${
              value === opt.value ? "bg-emerald-500/10" : "hover:bg-[hsla(0,0%,100%,.04)]"
            }`}
          >
            <div className="flex-1">
              <div className={`text-[13px] font-medium ${value === opt.value ? "text-emerald-400" : "text-[hsla(0,0%,100%,.7)]"}`}>
                {opt.label}
              </div>
              <div className={`text-[11px] text-[hsla(0,0%,100%,.25)] ${mono}`}>
                {opt.desc}
              </div>
            </div>
            {value === opt.value && <Check className="size-3.5 text-emerald-400" />}
          </button>
        ))}
      </PopoverContent>
    </Popover>
  );
}
