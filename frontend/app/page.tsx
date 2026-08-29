import Link from "next/link";

import {
  ArrowRight,
  Boxes,
  DollarSign,
  Globe2,
  Radar,
  ShieldAlert,
  ShoppingCart,
  Sparkles,
  Truck,
} from "lucide-react";

import Card3D from "@/app/components/Card3D";
import CardArt, { type ArtKind } from "@/app/components/CardArt";
import MarketingNav from "@/app/components/MarketingNav";
import MarketingFooter from "@/app/components/MarketingFooter";
import { SOLUTIONS } from "@/app/components/solutions";

export const metadata = {
  title: "HEX — Supply-Chain Risk Intelligence",
  description:
    "HEX senses global disruption, maps it onto your supply chain, and turns it into decisions.",
};

const CAPABILITIES = [
  {
    icon: Radar,
    title: "Outside-in sensing",
    body: "A standing watch on disasters, conflict, tariffs, freight and FX — scored, deduped and streamed as a live feed.",
  },
  {
    icon: ShieldAlert,
    title: "Exposure, in rupees",
    body: "Every event is matched to your routes, suppliers and open shipments. You see cost and revenue at risk, not headlines.",
  },
  {
    icon: Sparkles,
    title: "Decisions, not dashboards",
    body: "Five specialist agents — finance, sales, operations, world-watch, risk — reason together and hand you a recommendation.",
  },
];

const AGENTS: {
  icon: typeof DollarSign;
  art: ArtKind;
  name: string;
  desc: string;
}[] = [
  { icon: DollarSign, art: "sparkline", name: "Finance", desc: "Establishes the money baseline" },
  { icon: ShoppingCart, art: "bars", name: "Sales", desc: "Adds demand reality" },
  { icon: Truck, art: "route", name: "Operations", desc: "Reads supply against demand" },
  { icon: Radar, art: "radar", name: "World Watch", desc: "Live disruption, tariff & FX monitoring" },
  { icon: ShieldAlert, art: "shield", name: "Risk", desc: "Weighs everything the others found" },
];

const SOLUTION_ART: ArtKind[] = ["flow", "sparkline", "route", "radar", "donut"];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-bg">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-48 left-1/2 h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-accent/20 blur-[150px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-16rem] right-[-10rem] h-[30rem] w-[30rem] rounded-full bg-live/10 blur-[130px]"
      />

      <MarketingNav />

      <div className="relative mx-auto max-w-6xl px-6">
        {/* hero */}
        <section className="pt-14 pb-20 sm:pt-20">
          <p className="eyebrow text-accent/90">Supply-Chain Risk Intelligence</p>
          <h1 className="display mt-4 max-w-3xl text-4xl text-white sm:text-6xl">
            Global disruption, translated into your next decision.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-dim sm:text-lg">
            HEX watches the world for the events that move supply chains — wars,
            weather, strikes, tariffs, freight and currency shocks — maps them
            onto your suppliers and routes, and lets a team of AI agents reason
            about what to do.
          </p>

          <div className="mt-9 flex flex-wrap gap-3">
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accent/90"
            >
              Get started for free
              <ArrowRight size={16} />
            </Link>
            <Link
              href="/enterprise"
              className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-5 py-3 text-sm font-semibold text-dim transition hover:text-white"
            >
              HEX for enterprise
            </Link>
          </div>
        </section>

        {/* capabilities */}
        <section className="grid gap-4 pb-16 md:grid-cols-3">
          {CAPABILITIES.map(({ icon: Icon, title, body }) => (
            <div
              key={title}
              className="elevated rounded-xl border border-hairline bg-panel p-6 ring-1 ring-inset ring-white/[0.02]"
            >
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-accent/10 text-accent">
                <Icon size={20} />
              </span>
              <h3 className="mt-4 font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-dim">{body}</p>
            </div>
          ))}
        </section>

        {/* agent pipeline — 3D cards */}
        <section className="pb-16">
          <p className="eyebrow">The agent graph</p>
          <h2 className="display mt-3 text-2xl text-white sm:text-3xl">
            Five specialists, one answer
          </h2>
          <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {AGENTS.map(({ icon: Icon, art, name, desc }, i) => (
              <Card3D key={name} className="p-5">
                <div className="flex items-start justify-between">
                  <span className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent">
                    <Icon size={18} />
                  </span>
                  <p className="num text-xs text-mute">0{i + 1}</p>
                </div>
                <span className="mt-3 block text-accent/70">
                  <CardArt kind={art} />
                </span>
                <p className="mt-2 font-semibold text-white">{name}</p>
                <p className="mt-1 text-xs leading-5 text-dim">{desc}</p>
              </Card3D>
            ))}
          </div>
        </section>

        {/* solutions — 3D cards */}
        <section className="pb-16">
          <p className="eyebrow">Solutions</p>
          <h2 className="display mt-3 text-2xl text-white sm:text-3xl">
            Built for every seat at the table
          </h2>
          <div className="mt-7 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {SOLUTIONS.map((s, i) => {
              const Icon = s.icon;
              return (
                <Card3D key={s.slug}>
                  <div className="flex items-center justify-between">
                    <span className="grid h-10 w-10 place-items-center rounded-lg bg-live/10 text-live">
                      <Icon size={18} />
                    </span>
                    <span className="w-20 text-live/70">
                      <CardArt kind={SOLUTION_ART[i % SOLUTION_ART.length]} />
                    </span>
                  </div>
                  <h3 className="mt-3 font-semibold text-white">{s.role}</h3>
                  <p className="mt-2 text-sm leading-6 text-dim">{s.tagline}</p>
                  <Link
                    href={`/solutions#${s.slug}`}
                    className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline"
                  >
                    Learn more
                    <ArrowRight size={12} />
                  </Link>
                </Card3D>
              );
            })}
          </div>
        </section>

        {/* what you plug in */}
        <section className="grid gap-4 pb-20 md:grid-cols-3">
          {(
            [
              [Globe2, "Live intelligence", "GDELT, web search, FX and commodity feeds — always on."],
              [Boxes, "Your systems", "Connect an ERP or accounting system, or upload CSV / Excel."],
              [ShieldAlert, "Your exposure", "Revenue, cost and route risk, recomputed as the world changes."],
            ] as const
          ).map(([Icon, title, body]) => (
            <div
              key={title}
              className="rounded-xl border border-hairline bg-panel/60 p-6"
            >
              <Icon size={18} className="text-live" />
              <h3 className="mt-3 font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-6 text-dim">{body}</p>
            </div>
          ))}
        </section>

        {/* closing CTA */}
        <section className="mb-20 rounded-2xl border border-hairline bg-panel p-10 text-center">
          <h2 className="display text-2xl text-white sm:text-3xl">
            See your supply chain the way HEX does.
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-dim">
            Create a free workspace — it comes pre-loaded with a sample business
            so you can explore in seconds, then connect your own data.
          </p>
          <Link
            href="/signup"
            className="mt-7 inline-flex items-center gap-2 rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-bg transition hover:bg-accent/90"
          >
            Get started for free
            <ArrowRight size={16} />
          </Link>
        </section>
      </div>

      <MarketingFooter />
    </main>
  );
}
