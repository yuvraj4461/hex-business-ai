import Link from "next/link";

import { ArrowRight, Check } from "lucide-react";

import Card3D from "@/app/components/Card3D";
import MarketingNav from "@/app/components/MarketingNav";
import MarketingFooter from "@/app/components/MarketingFooter";
import { SOLUTIONS } from "@/app/components/solutions";

export const metadata = {
  title: "HEX Solutions — by team",
  description:
    "What HEX does for procurement, finance, operations, risk and leadership.",
};

export default function SolutionsPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-bg">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-48 left-1/2 h-[40rem] w-[40rem] -translate-x-1/2 rounded-full bg-accent/15 blur-[150px]"
      />

      <MarketingNav />

      <div className="relative mx-auto max-w-6xl px-6">
        <section className="pt-14 pb-14 sm:pt-20">
          <p className="eyebrow text-accent/90">Solutions</p>
          <h1 className="display mt-4 max-w-3xl text-4xl text-white sm:text-5xl">
            One connected system. An answer for every team.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-dim">
            HEX combines outside-in intelligence with your own supply-chain and
            financial data. Each team gets the view — and the decisions — that
            matter to them.
          </p>
        </section>

        {/* quick grid */}
        <section className="grid gap-4 pb-16 md:grid-cols-2 lg:grid-cols-3">
          {SOLUTIONS.map((s) => {
            const Icon = s.icon;
            return (
              <Card3D key={s.slug}>
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent">
                  <Icon size={18} />
                </span>
                <h3 className="mt-3 font-semibold text-white">{s.role}</h3>
                <p className="mt-2 text-sm leading-6 text-dim">{s.tagline}</p>
                <a
                  href={`#${s.slug}`}
                  className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-accent hover:underline"
                >
                  Jump to details
                  <ArrowRight size={12} />
                </a>
              </Card3D>
            );
          })}
        </section>

        {/* per-role detail */}
        <div className="space-y-16 pb-20">
          {SOLUTIONS.map((s, idx) => {
            const Icon = s.icon;
            return (
              <section
                key={s.slug}
                id={s.slug}
                className="scroll-mt-24 grid items-start gap-8 lg:grid-cols-2"
              >
                <div className={idx % 2 ? "lg:order-2" : ""}>
                  <span className="grid h-12 w-12 place-items-center rounded-xl bg-accent/10 text-accent">
                    <Icon size={22} />
                  </span>
                  <p className="eyebrow mt-4">{s.role}</p>
                  <h2 className="display mt-2 text-2xl text-white sm:text-3xl">
                    {s.tagline}
                  </h2>
                  <p className="mt-4 text-sm leading-7 text-dim">{s.body}</p>
                  <Link
                    href={s.href}
                    className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90"
                  >
                    Open in HEX
                    <ArrowRight size={15} />
                  </Link>
                </div>

                <ul className="space-y-3 rounded-2xl border border-hairline bg-panel p-6">
                  {s.points.map((p) => (
                    <li key={p} className="flex gap-3 text-sm text-dim">
                      <Check size={16} className="mt-0.5 shrink-0 text-stable" />
                      {p}
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>

        <section className="mb-20 rounded-2xl border border-hairline bg-panel p-10 text-center">
          <h2 className="display text-2xl text-white sm:text-3xl">
            Bring your team onto one system.
          </h2>
          <Link
            href="/signup"
            className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-bg transition hover:bg-accent/90"
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
