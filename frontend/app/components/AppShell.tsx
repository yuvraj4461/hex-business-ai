"use client";

import { useState } from "react";

import {
  ChevronDown,
  LayoutGrid,
  LogOut,
  Menu,
  ShieldCheck,
  X,
} from "lucide-react";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { clearToken } from "@/lib/auth";

import { Wordmark } from "@/app/components/Logo";
import PlatformMenu from "@/app/components/PlatformMenu";
import { NAV_ITEMS, isActive } from "@/app/components/nav";

export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [platformOpen, setPlatformOpen] = useState(false);

  const current = NAV_ITEMS.find((item) => isActive(pathname, item.href));

  function logout() {
    clearToken();
    router.push("/login");
  }

  const navList = (
    <nav className="flex-1 space-y-0.5 overflow-y-auto p-3">
      <button
        type="button"
        onClick={() => {
          setPlatformOpen((v) => !v);
          setMobileOpen(false);
        }}
        className={`relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
          platformOpen
            ? "bg-accent/12 text-white"
            : "text-dim hover:bg-panel-raised/70 hover:text-white"
        }`}
      >
        <LayoutGrid
          size={17}
          className={`shrink-0 ${platformOpen ? "text-accent" : ""}`}
        />
        Platform
        <ChevronDown
          size={14}
          className={`ml-auto transition ${platformOpen ? "rotate-180" : ""}`}
        />
      </button>

      <div className="my-1.5 border-t border-hairline" />

      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const active = isActive(pathname, item.href);

        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={() => setMobileOpen(false)}
            className={`relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
              active
                ? "bg-accent/12 text-white"
                : "text-dim hover:bg-panel-raised/70 hover:text-white"
            }`}
          >
            {active && (
              <span className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-accent" />
            )}
            <Icon
              size={17}
              className={`shrink-0 ${active ? "text-accent" : ""}`}
            />
            {item.name}
          </Link>
        );
      })}
    </nav>
  );

  const brand = (
    <div className="border-b border-hairline px-5 py-4">
      <Link href="/dashboard">
        <Wordmark size={26} />
      </Link>
    </div>
  );

  const logoutButton = (
    <div className="border-t border-hairline p-3">
      <button
        onClick={logout}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-dim transition hover:bg-panel-raised hover:text-white"
      >
        <LogOut size={17} />
        Logout
      </button>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-bg">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-hairline bg-panel lg:flex">
        {brand}
        {navList}
        {logoutButton}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/60"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col border-r border-hairline bg-panel">
            <div className="flex items-center justify-between border-b border-hairline pr-2">
              <div className="flex-1">{brand}</div>
              <button
                onClick={() => setMobileOpen(false)}
                className="rounded-lg p-2 text-dim hover:text-white"
              >
                <X size={18} />
              </button>
            </div>
            {navList}
            {logoutButton}
          </aside>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-hairline bg-bg/90 px-4 backdrop-blur lg:px-6">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-lg p-2 text-dim hover:text-white lg:hidden"
            >
              <Menu size={18} />
            </button>

            <button
              type="button"
              onClick={() => setPlatformOpen((v) => !v)}
              className={`hidden items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium transition lg:inline-flex ${
                platformOpen
                  ? "bg-accent/12 text-white"
                  : "text-dim hover:text-white"
              }`}
            >
              <LayoutGrid size={15} />
              Platform
              <ChevronDown
                size={13}
                className={`transition ${platformOpen ? "rotate-180" : ""}`}
              />
            </button>

            <span className="text-hairline hidden lg:inline">/</span>

            <p className="text-sm font-medium text-dim">
              {current?.name ?? "HEX"}
            </p>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full border border-stable/25 bg-stable/10 px-3 py-1">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-stable opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-stable" />
            </span>
            <span className="eyebrow !text-stable">System Online</span>
            <ShieldCheck size={13} className="text-stable" />
          </div>
        </header>

        <PlatformMenu
          open={platformOpen}
          onClose={() => setPlatformOpen(false)}
        />

        <main className="min-w-0 flex-1">{children}</main>
      </div>
    </div>
  );
}
