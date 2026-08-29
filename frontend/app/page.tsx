import Link from "next/link";

import {
  ArrowRight,
  Boxes,
  Globe2,
  LineChart,
  Radar,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import { Wordmark } from "@/app/components/Logo";

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

const AGENTS = [
  ["Finance", "Establishes the money baseline"],
  ["Sales", "Adds demand reality"],
  ["Operations", "Reads supply against demand"],
  ["World Watch", "Live disruption, tariff & price monitoring"],
  ["Risk", "Weighs everything the others found"],
];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-bg">
      {/* ambient brand glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-48 left-1/2 h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-accent/20 blur-[150px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-16rem] right-[-10rem] h-[30rem] w-[30rem] rounded-full bg-live/10 blur-[130px]"
      />

      <div className="relative mx-auto max-w-6xl px-6">
        {/* nav */}
        <header className="flex items-center justify-between py-6">
          <Wordmark size={28} subtitle={null} />
          <nav className="flex items-center gap-3 text-sm">
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
          </nav>
        </header>

        {/* hero */}
        <section className="pt-16 pb-20 sm:pt-24">
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
              href="/login"
              className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-5 py-3 text-sm font-semibold text-dim transition hover:text-white"
            >
              Log in
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

        {/* agent pipeline */}
        <section className="pb-16">
          <p className="eyebrow">The agent graph</p>
          <h2 className="display mt-3 text-2xl text-white sm:text-3xl">
            Five specialists, one answer
          </h2>
          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {AGENTS.map(([name, desc], i) => (
              <div
                key={name}
                className="rounded-xl border border-hairline bg-panel p-4"
              >
                <p className="num text-xs text-mute">0{i + 1}</p>
                <p className="mt-1 font-semibold text-white">{name}</p>
                <p className="mt-1 text-xs leading-5 text-dim">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* what you plug in */}
        <section className="grid gap-4 pb-20 md:grid-cols-3">
          {(
            [
              [Globe2, "Live intelligence", "GDELT, web search, FX and commodity feeds — always on."],
              [Boxes, "Your systems", "Connect an ERP or accounting system, or upload CSV / Excel."],
              [LineChart, "Your numbers", "Revenue, expenses, orders and exposure, kept in sync."],
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
        <section className="mb-24 rounded-2xl border border-hairline bg-panel p-10 text-center">
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

        <footer className="border-t border-hairline py-8 text-xs text-mute">
          HEX — supply-chain risk intelligence. Not affiliated with hex.tech.
        </footer>
      </div>
    </main>
  );
}
