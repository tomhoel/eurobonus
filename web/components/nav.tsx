import Link from "next/link";
import { UserMenu } from "./user-menu";

export function Nav() {
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <Link href="/" className="text-sm font-semibold tracking-tight text-indigo-600">
            Award Finder
          </Link>
          <nav className="hidden gap-4 sm:flex">
            <Link href="/search" className="text-sm text-muted-foreground hover:text-foreground">
              Search
            </Link>
            <Link href="/deals" className="text-sm text-muted-foreground hover:text-foreground">
              Deals
            </Link>
          </nav>
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
