import Link from "next/link";
import Image from "next/image";
import { UserMenu } from "./user-menu";

export function Nav() {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/">
            <Image src="/sus.png" alt="SUS" width={80} height={32} className="h-8 w-auto" />
          </Link>
          <nav className="hidden gap-4 sm:flex">
            <Link href="/search" className="text-sm text-muted-foreground hover:text-foreground">
              Search
            </Link>
            <Link href="/deals" className="text-sm text-muted-foreground hover:text-foreground">
              Deals
            </Link>
            <Link href="/alerts" className="text-sm text-muted-foreground hover:text-foreground">
              Alerts
            </Link>
          </nav>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
