import Link from "next/link";

import { Wordmark } from "@/app/components/Logo";

export default function MarketingFooter() {
  return (
    <footer className="border-t border-hairline">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Wordmark size={24} subtitle={null} />
          <p className="mt-2 text-xs text-mute">
            Supply-chain risk intelligence. Not affiliated with hex.tech.
          </p>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-dim">
          <Link href="/solutions" className="hover:text-white">
            Solutions
          </Link>
          <Link href="/enterprise" className="hover:text-white">
            Enterprise
          </Link>
          <Link href="/pricing" className="hover:text-white">
            Pricing
          </Link>
          <Link href="/login" className="hover:text-white">
            Log in
          </Link>
          <Link href="/signup" className="hover:text-white">
            Get started
          </Link>
        </nav>
      </div>
    </footer>
  );
}
