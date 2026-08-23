"use client";

import { useEffect, useState } from "react";
import {
  BarChart3,
  DollarSign,
  ShoppingCart,
  TrendingUp,
  Loader2,
} from "lucide-react";

import { apiRequest } from "@/lib/api";

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
  const [data, setData] =
    useState<DashboardData | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiRequest<DashboardData>(
            "/business/dashboard"
          );

        setData(result);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load analytics."
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
        <div className="rounded-2xl border bg-white p-10 text-center shadow-sm">
          <Loader2
            size={30}
            className="mx-auto animate-spin text-slate-500"
          />

          <p className="mt-4 text-slate-500">
            Loading analytics...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 lg:p-8">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">
            Analytics unavailable
          </p>

          <p className="mt-2">
            {error}
          </p>
        </div>
      </div>
    );
  }

  const metrics = data?.metrics;

  return (
    <div className="p-6 lg:p-8">

      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-slate-900 p-3 text-white">
            <BarChart3 size={22} />
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Business Performance
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              Analytics
            </h1>
          </div>
        </div>

        <p className="mt-3 text-slate-500">
          Financial, sales, customer and inventory
          performance for your organization.
        </p>
      </div>

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="w-fit rounded-xl bg-slate-100 p-3">
            <DollarSign size={20} />
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Revenue
          </p>

          <p className="mt-1 text-3xl font-bold">
            ₹
            {Number(
              metrics?.revenue || 0
            ).toLocaleString("en-IN")}
          </p>
        </div>

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="w-fit rounded-xl bg-red-50 p-3">
            <TrendingUp
              size={20}
              className="text-red-600"
            />
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Expenses
          </p>

          <p className="mt-1 text-3xl font-bold">
            ₹
            {Number(
              metrics?.expenses || 0
            ).toLocaleString("en-IN")}
          </p>
        </div>

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="w-fit rounded-xl bg-emerald-50 p-3">
            <TrendingUp
              size={20}
              className="text-emerald-600"
            />
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Profit
          </p>

          <p className="mt-1 text-3xl font-bold">
            ₹
            {Number(
              metrics?.profit || 0
            ).toLocaleString("en-IN")}
          </p>
        </div>

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <div className="w-fit rounded-xl bg-blue-50 p-3">
            <ShoppingCart
              size={20}
              className="text-blue-600"
            />
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Orders
          </p>

          <p className="mt-1 text-3xl font-bold">
            {metrics?.orders || 0}
          </p>
        </div>

      </div>

      <div className="mt-8 grid gap-6 md:grid-cols-2">

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="font-semibold">
            Customers
          </h2>

          <p className="mt-3 text-4xl font-bold">
            {metrics?.customers || 0}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Total customers
          </p>
        </div>

        <div className="rounded-2xl border bg-white p-6 shadow-sm">
          <h2 className="font-semibold">
            Low Stock Products
          </h2>

          <p className="mt-3 text-4xl font-bold">
            {metrics?.low_stock_products || 0}
          </p>

          <p className="mt-1 text-sm text-slate-500">
            Products requiring attention
          </p>
        </div>

      </div>

    </div>
  );
}