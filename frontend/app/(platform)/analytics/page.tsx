"use client";

import { useEffect, useState } from "react";

import {
  BarChart3,
  DollarSign,
  Package,
  ShoppingCart,
  TrendingDown,
  TrendingUp,
  Users,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import StatTile from "@/app/components/StatTile";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import BarBreakdown from "@/app/components/charts/BarBreakdown";
import { chartTheme } from "@/app/components/charts/theme";

interface DashboardData {
  organization_id: number;
  metrics: {
    revenue: number;
    expenses: number;
    profit: number;
    orders: number;
    customers: number;
    low_stock_products: number;
  };
}

export default function AnalyticsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError("");

        const result = await apiRequest<DashboardData>(
          "/business/dashboard",
        );

        setData(result);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unable to load analytics.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading analytics…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard title="Analytics unavailable" message={error} />
      </div>
    );
  }

  const m = data?.metrics;

  const margin =
    m && m.revenue ? (m.profit / m.revenue) * 100 : 0;

  const breakdown = [
    { name: "Revenue", value: m?.revenue ?? 0, color: chartTheme.stable },
    { name: "Expenses", value: m?.expenses ?? 0, color: chartTheme.elevated },
    { name: "Profit", value: m?.profit ?? 0, color: chartTheme.live },
  ];

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={BarChart3}
        eyebrow="Business Performance"
        title="Analytics"
        description="Financial, sales, customer and inventory performance for your organization."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile
          label="Revenue"
          value={inr(m?.revenue)}
          icon={DollarSign}
          tone="stable"
        />
        <StatTile
          label="Expenses"
          value={inr(m?.expenses)}
          icon={TrendingDown}
          tone="elevated"
        />
        <StatTile
          label="Profit"
          value={inr(m?.profit)}
          delta={`${margin.toFixed(1)}% margin`}
          deltaTone={margin >= 0 ? "stable" : "critical"}
          icon={TrendingUp}
          tone="live"
        />
        <StatTile
          label="Orders"
          value={num(m?.orders)}
          icon={ShoppingCart}
          tone="live"
        />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Panel label="Composition" title="Revenue · Expenses · Profit" tone="live">
            <BarBreakdown data={breakdown} />
          </Panel>
        </div>

        <div className="space-y-5">
          <StatTile
            label="Customers"
            value={num(m?.customers)}
            icon={Users}
            tone="stable"
          />
          <StatTile
            label="Low Stock Products"
            value={num(m?.low_stock_products)}
            delta="require attention"
            deltaTone={
              (m?.low_stock_products ?? 0) > 0 ? "elevated" : "stable"
            }
            icon={Package}
            tone={(m?.low_stock_products ?? 0) > 0 ? "elevated" : "stable"}
          />
        </div>
      </div>
    </div>
  );
}
