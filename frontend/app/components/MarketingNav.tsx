"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { ArrowRight, ChevronDown } from "lucide-react";

import { isAuthenticated } from "@/lib/auth";
import { Wordmark } from "@/app/components/Logo";
import { NAV_ITEMS } from "@/app/components/nav";
import { SOLUTIONS } from "@/app/components/solutions";

const PLATFORM_LINKS = NAV_ITEMS.filter((i) =>
  ["/dashboard", "/global", "/risk", "/scenarios", "/routes", "/agents", "/copilot", "/integrations"].includes(
    i.href,
  ),
);

export default function MarketingNav() {
  const [open, setOpen] = useState<"platform" | "solutions" | null>(null);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client-only auth read
    setAuthed(isAuthenticated());
  }, []);

  return (
    <header
      className="relative z-30"
      onMouseLeave={() => setOpen(null)}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
        <Link href="/">
          <Wordmark size={26} subtitle={null} />
        </Link>

        <nav className="hidden items-center gap-1 text-sm md:flex">
          <button
            type="button"
            onMouseEnter={() => setOpen("platform")}
            onClick={() => setOpen(open === "platform" ? null : "platform")}
            className="inline-flex items-center gap-1 rounded-lg px-3 py-2 font-medium text-dim transition hover:text-white"
          >
            Platform
            <ChevronDown size={13} />
          </button>
          <button
            type="button"
            onMouseEnter={() => setOpen("solutions")}
            onClick={() => setOpen(open === "solutions" ? null : "solutions")}
            className="inline-flex items-center gap-1 rounded-lg px-3 py-2 font-medium text-dim transition hover:text-white"
          >
            Solutions
            <ChevronDown size={13} />
          </button>
          <Link
            href="/enterprise"
            className="rounded-lg px-3 py-2 font-medium text-dim transition hover:text-white"
          >
            Enterprise
          </Link>
          <Link
            href="/pricing"
            className="rounded-lg px-3 py-2 font-medium text-dim transition hover:text-white"
          >
            Pricing
          </Link>
        </nav>

        <div className="flex items-center gap-2 text-sm">
          {authed ? (
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3.5 py-2 font-semibold text-bg transition hover:bg-accent/90"
            >
              Open HEX
              <ArrowRight size={15} />
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3.5 py-2 font-medium text-dim transition hover:text-white"
              >
                Log in
              </Link>
              <Link
                href="/signup"
                className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3.5 py-2 font-semibold text-bg transition hover:bg-accent/90"
              >
                Get started
                <ArrowRight size={15} />
              </Link>
            </>
          )}
        </div>
      </div>

      {/* dropdown panels */}
      {open && (
        <div
          className="absolute inset-x-0 top-full hidden justify-center px-6 md:flex"
          onMouseEnter={() => setOpen(open)}
        >
          <div className="elevated w-full max-w-3xl rounded-2xl border border-hairline bg-panel p-5 ring-1 ring-inset ring-white/[0.03]">
            {open === "platform" ? (
              <div className="grid gap-1 sm:grid-cols-2">
                {PLATFORM_LINKS.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(null)}
                      className="flex gap-3 rounded-lg p-2.5 transition hover:bg-panel-raised/70"
                    >
                      <Icon size={16} className="mt-0.5 shrink-0 text-dim" />
                      <span>
                        <span className="block text-sm font-medium text-white">
                          {item.name}
                        </span>
                        <span className="block text-xs text-mute">
                          {item.description}
                        </span>
                      </span>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="grid gap-1 sm:grid-cols-2">
                {SOLUTIONS.map((s) => {
                  const Icon = s.icon;
                  return (
                    <Link
                      key={s.slug}
                      href={`/solutions#${s.slug}`}
                      onClick={() => setOpen(null)}
                      className="flex gap-3 rounded-lg p-2.5 transition hover:bg-panel-raised/70"
                    >
                      <Icon size={16} className="mt-0.5 shrink-0 text-dim" />
                      <span>
                        <span className="block text-sm font-medium text-white">
                          {s.role}
                        </span>
                        <span className="block text-xs text-mute">
                          {s.tagline}
                        </span>
                      </span>
                    </Link>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
