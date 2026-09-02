"use client";

import { useEffect, useState } from "react";

import {
  BarChart3,
  Boxes,
  DollarSign,
  ShoppingCart,
  Users,
  Wallet,
  type LucideIcon,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import StatTile from "@/app/components/StatTile";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import BarBreakdown from "@/app/components/charts/BarBreakdown";
import TrendLine from "@/app/components/charts/TrendLine";
import { chartTheme } from "@/app/components/charts/theme";
import type { Tone } from "@/app/components/tone";

interface Kpi {
  label: string;
  value: number | string;
  unit: string;
  delta?: string | null;
  delta_tone?: string | null;
}

interface Row {
  label: string;
  value: number;
}

interface PnlRow {
  label: string;
  revenue: number;
  expenses: number;
  profit: number;
}

interface Overview {
  financial: { kpis: Kpi[]; pnl_trend: PnlRow[]; expense_breakdown: Row[] };
  sales: {
    kpis: Kpi[];
    sales_trend: Row[];
    by_category: Row[];
    top_products: Row[];
    order_status: Row[];
  };
  customers: { kpis: Kpi[]; new_vs_returning: Row[]; top_customers: Row[] };
  products: { kpis: Kpi[]; revenue_by_product: Row[]; units_by_category: Row[] };
  operations: {
    kpis: Kpi[];
    inventory_by_category: Row[];
    lead_time_by_supplier: Row[];
  };
}

const SECTIONS: { id: string; label: string; icon: LucideIcon }[] = [
  { id: "financial", label: "Financial", icon: Wallet },
  { id: "sales", label: "Sales", icon: ShoppingCart },
  { id: "customers", label: "Customers", icon: Users },
  { id: "products", label: "Products", icon: BarChart3 },
  { id: "operations", label: "Operations", icon: Boxes },
];

function fmtKpi(k: Kpi): string {
  if (k.unit === "INR") return inr(k.value);
  if (k.unit === "percent") return `${Number(k.value).toFixed(1)}%`;
  if (k.unit === "days") return `${num(k.value)} days`;
  if (k.unit === "text") return String(k.value);
  return num(k.value);
}

function toChart(rows: Row[]) {
  return rows.map((r) => ({ name: r.label, value: r.value }));
}

export default function AnalyticsPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError("");
        setData(await apiRequest<Overview>("/analytics/overview"));
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load analytics.",
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Crunching your numbers…" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard title="Analytics unavailable" message={error} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={BarChart3}
        eyebrow="Business Performance"
        title="Analytics"
        description="Financial, sales, customer, product and supply-chain performance — computed from your own data."
      />

      {/* section nav */}
      <div className="sticky top-0 z-10 -mx-6 mb-6 flex flex-wrap gap-2 border-b border-hairline bg-bg/90 px-6 py-3 backdrop-blur lg:-mx-8 lg:px-8">
        {SECTIONS.map((s) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className="inline-flex items-center gap-1.5 rounded-full border border-hairline bg-panel px-3 py-1.5 text-xs font-medium text-dim transition hover:border-accent/40 hover:text-white"
          >
            <s.icon size={13} /> {s.label}
          </a>
        ))}
      </div>

      {/* Financial */}
      <Section id="financial" title="Financial" icon={Wallet}>
        <KpiRow kpis={data.financial.kpis} />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel label="Trend" title="Profit by month" tone="live">
            <TrendLine
              data={data.financial.pnl_trend.map((r) => ({
                name: r.label,
                value: r.profit,
              }))}
            />
          </Panel>
          <Panel label="Composition" title="Expenses by category" tone="elevated">
            <BarBreakdown data={toChart(data.financial.expense_breakdown)} />
          </Panel>
        </div>
        <div className="mt-5">
          <Panel label="Trend" title="Revenue vs expenses by month" tone="live">
            <RevExpTrend rows={data.financial.pnl_trend} />
          </Panel>
        </div>
      </Section>

      {/* Sales */}
      <Section id="sales" title="Sales" icon={ShoppingCart}>
        <KpiRow kpis={data.sales.kpis} />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel label="Trend" title="Revenue by month" tone="live">
            <TrendLine data={toChart(data.sales.sales_trend)} />
          </Panel>
          <Panel label="Mix" title="Revenue by category" tone="live">
            <BarBreakdown data={toChart(data.sales.by_category)} />
          </Panel>
          <Panel label="Ranking" title="Top products by revenue" tone="stable">
            <BarBreakdown data={toChart(data.sales.top_products)} />
          </Panel>
          <Panel label="Fulfilment" title="Orders by status" tone="elevated">
            <BarBreakdown data={toChart(data.sales.order_status)} currency={false} />
          </Panel>
        </div>
      </Section>

      {/* Customers */}
      <Section id="customers" title="Customers" icon={Users}>
        <KpiRow kpis={data.customers.kpis} />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel label="Loyalty" title="New vs returning" tone="live">
            <BarBreakdown
              data={toChart(data.customers.new_vs_returning)}
              currency={false}
            />
          </Panel>
          <Panel label="Ranking" title="Top customers by revenue" tone="stable">
            <BarBreakdown data={toChart(data.customers.top_customers)} />
          </Panel>
        </div>
      </Section>

      {/* Products */}
      <Section id="products" title="Products" icon={BarChart3}>
        <KpiRow kpis={data.products.kpis} />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel label="Ranking" title="Revenue by product" tone="stable">
            <BarBreakdown data={toChart(data.products.revenue_by_product)} />
          </Panel>
          <Panel label="Volume" title="Units sold by category" tone="live">
            <BarBreakdown
              data={toChart(data.products.units_by_category)}
              currency={false}
            />
          </Panel>
        </div>
      </Section>

      {/* Operations */}
      <Section id="operations" title="Operations & Supply Chain" icon={Boxes}>
        <KpiRow kpis={data.operations.kpis} />
        <div className="mt-5 grid gap-5 lg:grid-cols-2">
          <Panel label="Stock" title="Inventory by category" tone="live">
            <BarBreakdown
              data={toChart(data.operations.inventory_by_category)}
              currency={false}
            />
          </Panel>
          <Panel label="Suppliers" title="Lead time by supplier" tone="elevated">
            <BarBreakdown
              data={toChart(data.operations.lead_time_by_supplier)}
              currency={false}
            />
          </Panel>
        </div>
      </Section>
    </div>
  );
}

function Section({
  id,
  title,
  icon: Icon,
  children,
}: {
  id: string;
  title: string;
  icon: LucideIcon;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="mt-10 scroll-mt-24 first:mt-0">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-accent/90">
        <Icon size={15} /> {title}
      </h2>
      {children}
    </section>
  );
}

function KpiRow({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {kpis.map((k) => (
        <StatTile
          key={k.label}
          label={k.label}
          value={fmtKpi(k)}
          delta={k.delta ?? undefined}
          deltaTone={(k.delta_tone as Tone | undefined) ?? undefined}
          tone={(k.delta_tone as Tone | undefined) ?? "live"}
        />
      ))}
    </div>
  );
}

/** Two thin lines — revenue and expenses — over the same month axis. */
function RevExpTrend({ rows }: { rows: PnlRow[] }) {
  const max = Math.max(1, ...rows.map((r) => Math.max(r.revenue, r.expenses)));
  return (
    <div className="space-y-3">
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-3">
          <span className="num w-16 shrink-0 text-xs text-mute">{r.label}</span>
          <div className="flex-1 space-y-1">
            <Bar value={r.revenue} max={max} color={chartTheme.stable} />
            <Bar value={r.expenses} max={max} color={chartTheme.elevated} />
          </div>
          <span
            className={`num w-24 shrink-0 text-right text-xs ${
              r.profit >= 0 ? "text-stable" : "text-critical"
            }`}
          >
            {inr(r.profit)}
          </span>
        </div>
      ))}
      <div className="flex gap-4 pt-1 text-[0.7rem] text-mute">
        <span className="flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: chartTheme.stable }}
          />
          Revenue
        </span>
        <span className="flex items-center gap-1.5">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: chartTheme.elevated }}
          />
          Expenses
        </span>
      </div>
    </div>
  );
}

function Bar({
  value,
  max,
  color,
}: {
  value: number;
  max: number;
  color: string;
}) {
  return (
    <div className="h-2 overflow-hidden rounded-full bg-panel-raised">
      <div
        className="h-full rounded-full"
        style={{
          width: `${Math.max(2, (value / max) * 100)}%`,
          background: color,
        }}
      />
    </div>
  );
}
