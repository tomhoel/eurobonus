import Link from "next/link";
import Image from "next/image";
import { UserMenu } from "./user-menu";

export function Nav() {
  return (
    <header
      className="sticky top-0 z-50"
      style={{
        borderBottom: "1px solid hsla(0,0%,100%,.08)",
        backgroundColor: "hsla(0,0%,0%,.5)",
        backdropFilter: "saturate(180%) blur(20px)",
        WebkitBackdropFilter: "saturate(180%) blur(20px)",
      }}
    >
      <div className="mx-auto flex items-center justify-between px-6" style={{ maxWidth: 1200, height: 64 }}>
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center">
            <Image
              src="/sus-white.png"
              alt="SUS"
              width={104}
              height={42}
              className="h-[36px] w-auto"
            />
          </Link>
          <span className="text-[hsla(0,0%,100%,.16)]">/</span>
          <span className="text-[14px] text-[hsla(0,0%,100%,.5)]">Award Search</span>
        </div>
        <nav className="hidden items-center gap-1 sm:flex">
          {[
            { label: "Search", href: "/search" },
            { label: "Deals", href: "/deals" },
            { label: "Alerts", href: "/alerts" },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="rounded-md px-3 py-1.5 text-[14px] text-[hsla(0,0%,100%,.5)] transition-colors hover:bg-[hsla(0,0%,100%,.06)] hover:text-[hsla(0,0%,100%,.8)]"
            >
              {item.label}
            </Link>
          ))}
          <div className="ml-2 h-4 w-px bg-[hsla(0,0%,100%,.08)]" />
          <div className="ml-2 flex items-center gap-2">
            <UserMenu />
            <Link
              href="/search"
              className="rounded-md bg-white px-3 py-1.5 text-[14px] font-medium text-black transition-colors hover:bg-[hsla(0,0%,100%,.85)]"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </div>
    </header>
  );
}
