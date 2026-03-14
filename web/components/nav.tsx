import Link from "next/link";
import Image from "next/image";
import { UserMenu } from "./user-menu";

export function Nav() {
  return (
    <header className="border-b border-white/5 bg-[#08090e]/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-8">
          <Link href="/">
            <Image src="/sus.png" alt="SUS" width={72} height={28} className="h-7 w-auto rounded bg-white/90 px-1 transition hover:opacity-90" />
          </Link>
          <nav className="hidden gap-6 sm:flex">
            <Link href="/search" className="text-sm text-white/40 transition hover:text-white/80">
              Search
            </Link>
            <Link href="/deals" className="text-sm text-white/40 transition hover:text-white/80">
              Deals
            </Link>
            <Link href="/alerts" className="text-sm text-white/40 transition hover:text-white/80">
              Alerts
            </Link>
          </nav>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
