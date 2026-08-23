"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import AppShell from "@/app/components/AppShell";

import { isAuthenticated } from "@/lib/auth";


const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
  },
  {
    name: "Global Intelligence",
    href: "/global",
  },
  {
    name: "Risk Center",
    href: "/risk",
  },
  {
    name: "Supply Routes",
    href: "/routes",
  },
  {
    name: "Scenarios",
    href: "/scenarios",
  },
  {
    name: "Analytics",
    href: "/analytics",
  },
  {
    name: "Agents",
    href: "/agents",
  },
  {
    name: "AI Copilot",
    href: "/copilot",
  },
  {
    name: "Approvals",
    href: "/approvals",
  },
];


export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode;
}) {

  const router = useRouter();
  const pathname = usePathname();


  useEffect(() => {

    if (!isAuthenticated()) {
      router.push("/login");
    }

  }, [router]);


  return (
    <AppShell>

      <div className="min-h-screen bg-slate-50">

        {/* Navigation */}
        <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">

          <div className="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto px-6 py-3">

            <Link
              href="/dashboard"
              className="mr-4 shrink-0 text-lg font-bold text-slate-900"
            >
              HEX
            </Link>


            {navigation.map((item) => {

              const active =
                pathname === item.href ||
                pathname.startsWith(
                  `${item.href}/`
                );

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "shrink-0 rounded-lg px-3 py-2 text-sm font-medium transition",
                    active
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  ].join(" ")}
                >
                  {item.name}
                </Link>
              );
            })}

          </div>

        </nav>


        {/* Page Content */}
        <main>
          {children}
        </main>

      </div>

    </AppShell>
  );
}