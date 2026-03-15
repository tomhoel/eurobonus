"use client";

export function HoverCard({
  children,
  className = "",
  wide = false,
  full = false,
}: {
  children: React.ReactNode;
  className?: string;
  wide?: boolean;
  full?: boolean;
}) {
  return (
    <div
      className={`transition-colors ${wide ? "sm:col-span-2" : ""} ${full ? "sm:col-span-2 lg:col-span-3" : ""} ${className}`}
      style={{
        borderRadius: 12,
        border: "1px solid hsla(0,0%,100%,.08)",
        padding: 32,
        background: "hsla(0,0%,100%,.02)",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = "hsla(0,0%,100%,.16)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "hsla(0,0%,100%,.08)"; }}
    >
      {children}
    </div>
  );
}

export function HoverRow({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      className="flex items-center transition-colors"
      style={{
        padding: "14px 20px",
        borderBottom: "1px solid hsla(0,0%,100%,.04)",
        cursor: "pointer",
        fontSize: 14,
      }}
      onMouseEnter={(e) => { e.currentTarget.style.background = "hsla(0,0%,100%,.02)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
    >
      {children}
    </div>
  );
}
