"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { NAV_GROUPS, NAV_ITEMS, isActive } from "./nav";

/**
 * PlatformMenu — a full-width mega-menu of every HEX module, grouped.
 * Opened from the "Platform" control in the sidebar / header.
 */
export default function PlatformMenu({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const pathname = usePathname();
  const ref = useRef<HTMLDivElement>(null);

  // Close on route change.
  useEffect(() => {
    if (open) onClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  // Close on Esc + outside click.
  useEffect(() => {
    if (!open) return;

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }

    document.addEventListener("keydown", onKey);
    // defer so the opening click doesn't immediately close it
    const t = window.setTimeout(
      () => document.addEventListener("mousedown", onClick),
      0,
    );
    return () => {
      document.removeEventListener("keydown", onKey);
      window.clearTimeout(t);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[1px]" />

      <div
        ref={ref}
        className="elevated absolute left-2 right-2 top-16 mx-auto max-w-5xl overflow-hidden rounded-2xl border border-hairline bg-panel ring-1 ring-inset ring-white/[0.03] lg:left-64"
      >
        <div className="border-b border-hairline px-6 py-3">
          <p className="eyebrow">Platform</p>
          <p className="mt-0.5 text-sm text-dim">
            One connected system — sensing, exposure and decisions.
          </p>
        </div>

        <div className="grid gap-x-8 gap-y-6 p-6 sm:grid-cols-2 lg:grid-cols-4">
          {NAV_GROUPS.map((group) => (
            <div key={group}>
              <p className="eyebrow mb-2.5">{group}</p>
              <div className="space-y-1">
                {NAV_ITEMS.filter((i) => i.group === group).map((item) => {
                  const Icon = item.icon;
                  const active = isActive(pathname, item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={onClose}
                      className={`flex gap-3 rounded-lg p-2.5 transition ${
                        active
                          ? "bg-accent/12"
                          : "hover:bg-panel-raised/70"
                      }`}
                    >
                      <Icon
                        size={16}
                        className={`mt-0.5 shrink-0 ${
                          active ? "text-accent" : "text-dim"
                        }`}
                      />
                      <span className="min-w-0">
                        <span className="block text-sm font-medium text-white">
                          {item.name}
                        </span>
                        <span className="block text-xs leading-4 text-mute">
                          {item.description}
                        </span>
                      </span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
