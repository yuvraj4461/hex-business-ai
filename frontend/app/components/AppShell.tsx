"use client";

import {
  BarChart3,
  Bot,
  Globe,
  LayoutDashboard,
  LogOut,
  Route,
  ShieldAlert,
  Sparkles,
  Target,
} from "lucide-react";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";

import {
  clearToken,
} from "@/lib/auth";


const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Global Intelligence",
    href: "/global",
    icon: Globe,
  },
  {
    name: "Risk Center",
    href: "/risk",
    icon: ShieldAlert,
  },
  {
    name: "Scenarios",
    href: "/scenarios",
    icon: Target,
  },
  {
    name: "Routes",
    href: "/routes",
    icon: Route,
  },
  {
    name: "AI Copilot",
    href: "/copilot",
    icon: Sparkles,
  },
  {
    name: "Agents",
    href: "/agents",
    icon: Bot,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
];


export default function AppShell({
  children,
}: {
  children: React.ReactNode;
}) {

  const pathname =
    usePathname();

  const router =
    useRouter();


  function logout() {

    clearToken();

    router.push("/login");
  }


  return (
    <div className="flex min-h-screen bg-slate-50">

      <aside className="hidden w-64 border-r bg-white lg:flex lg:flex-col">

        <div className="border-b px-6 py-5">

          <div className="flex items-center gap-3">

            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
              H
            </div>

            <div>
              <h1 className="font-bold text-slate-900">
                HEX
              </h1>

              <p className="text-xs text-slate-500">
                Business AI
              </p>
            </div>

          </div>

        </div>


        <nav className="flex-1 space-y-1 p-4">

          {navigation.map(
            (item) => {

              const Icon =
                item.icon;

              const active =
                pathname ===
                item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition ${
                    active
                      ? "bg-slate-900 text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <Icon
                    size={18}
                  />

                  {item.name}
                </Link>
              );
            }
          )}

        </nav>


        <div className="border-t p-4">

          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-100"
          >
            <LogOut size={18} />

            Logout
          </button>

        </div>

      </aside>


      <main className="min-w-0 flex-1">

        <header className="sticky top-0 z-10 border-b bg-white/90 backdrop-blur">

          <div className="flex h-16 items-center justify-between px-6">

            <div>
              <p className="text-sm font-medium text-slate-500">
                HEX Business Intelligence
              </p>
            </div>

            <div className="flex items-center gap-2">

              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                System Online
              </span>

            </div>

          </div>

        </header>


        {children}

      </main>

    </div>
  );
}