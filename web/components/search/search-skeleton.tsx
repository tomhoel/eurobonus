const mono = "font-[family-name:var(--font-geist-mono)]";

export function SearchSkeleton() {
  return (
    <div className="space-y-2">
      {Array.from({ length: 4 }, (_, i) => (
        <div
          key={i}
          className="overflow-hidden rounded-xl border border-[hsla(0,0%,100%,.06)] bg-[hsla(0,0%,100%,.02)]"
        >
          <div className="flex items-center gap-4 p-5">
            {/* Time left */}
            <div className="flex flex-col items-center gap-1">
              <div className="h-[18px] w-12 animate-pulse rounded bg-[hsla(0,0%,100%,.06)]" />
              <div className={`h-3 w-8 animate-pulse rounded bg-[hsla(0,0%,100%,.03)] ${mono}`} />
            </div>
            {/* Route line */}
            <div className="flex flex-1 flex-col items-center gap-1">
              <div className="h-px w-full bg-[hsla(0,0%,100%,.04)]" />
              <div className="h-3 w-20 animate-pulse rounded bg-[hsla(0,0%,100%,.03)]" />
            </div>
            {/* Time right */}
            <div className="flex flex-col items-center gap-1">
              <div className="h-[18px] w-12 animate-pulse rounded bg-[hsla(0,0%,100%,.06)]" />
              <div className="h-3 w-8 animate-pulse rounded bg-[hsla(0,0%,100%,.03)]" />
            </div>
            {/* Points */}
            <div className="flex flex-col items-end gap-1">
              <div className="h-[22px] w-24 animate-pulse rounded bg-[hsla(0,0%,100%,.06)]" />
              <div className="h-3 w-16 animate-pulse rounded bg-[hsla(0,0%,100%,.03)]" />
            </div>
          </div>
          <div className="border-t border-[hsla(0,0%,100%,.04)] px-5 py-2">
            <div className="h-3 w-28 animate-pulse rounded bg-[hsla(0,0%,100%,.03)]" />
          </div>
        </div>
      ))}
    </div>
  );
}
