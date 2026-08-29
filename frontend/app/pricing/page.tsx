import Link from "next/link";

import { ArrowRight, Check } from "lucide-react";

import MarketingNav from "@/app/components/MarketingNav";
import MarketingFooter from "@/app/components/MarketingFooter";

export const metadata = {
  title: "HEX Pricing",
  description: "Start free. Scale when your team does.",
};

const TIERS = [
  {
    name: "Free",
    price: "₹0",
    note: "For exploring and small teams",
    cta: "Get started",
    href: "/signup",
    highlight: false,
    features: [
      "One workspace, pre-loaded with sample data",
      "All five agents + AI Copilot",
      "Live World Watch feed",
      "File upload + one SQL source",
    ],
  },
  {
    name: "Team",
    price: "Talk to us",
    note: "For supply-chain and finance teams",
    cta: "Get started",
    href: "/signup",
    highlight: true,
    features: [
      "Everything in Free",
      "Multiple connections + scheduled sync",
      "Unified accounting connector",
      "Role-based access for the whole team",
      "Priority intelligence refresh",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    note: "For security-conscious organizations",
    cta: "Get in touch",
    href: "/enterprise",
    highlight: false,
    features: [
      "Everything in Team",
      "Self-hosted API + bring-your-own database",
      "Bring-your-own encryption key",
      "Full audit-log export",
      "SSO / directory onboarding assistance",
    ],
  },
];

export default function PricingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-bg">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-48 left-1/2 h-[38rem] w-[38rem] -translate-x-1/2 rounded-full bg-accent/15 blur-[150px]"
      />

      <MarketingNav />

      <div className="relative mx-auto max-w-6xl px-6">
        <section className="pt-14 pb-12 text-center sm:pt-20">
          <p className="eyebrow text-accent/90">Pricing</p>
          <h1 className="display mt-4 text-4xl text-white sm:text-5xl">
            Start free. Scale when your team does.
          </h1>
        </section>

        <section className="grid gap-5 pb-20 lg:grid-cols-3">
          {TIERS.map((t) => (
            <div
              key={t.name}
              className={`relative rounded-2xl border bg-panel p-7 ${
                t.highlight
                  ? "border-accent/40 ring-1 ring-accent/20"
                  : "border-hairline"
              }`}
            >
              {t.highlight && (
                <span className="absolute -top-2.5 left-7 rounded-md bg-accent px-2 py-0.5 text-[0.7rem] font-semibold text-bg">
                  Most popular
                </span>
              )}
              <h2 className="font-semibold text-white">{t.name}</h2>
              <p className="mt-1 text-xs text-mute">{t.note}</p>
              <p className="display mt-4 text-3xl text-white">{t.price}</p>

              <Link
                href={t.href}
                className={`mt-5 inline-flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${
                  t.highlight
                    ? "bg-accent text-bg hover:bg-accent/90"
                    : "border border-hairline text-dim hover:text-white"
                }`}
              >
                {t.cta}
                <ArrowRight size={15} />
              </Link>

              <ul className="mt-6 space-y-2.5">
                {t.features.map((f) => (
                  <li key={f} className="flex gap-2.5 text-sm text-dim">
                    <Check size={15} className="mt-0.5 shrink-0 text-stable" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </section>
      </div>

      <MarketingFooter />
    </main>
  );
}
