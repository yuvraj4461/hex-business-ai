"use client";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import Link from "next/link";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Globe2,
  RefreshCw,
  ShoppingCart,
  Truck,
} from "lucide-react";

import {
  apiRequest,
} from "@/lib/api";


interface Overview {
  revenue?: number;
  expenses?: number;
  profit?: number;
  orders?: number;
}


interface GlobalEvent {
  id: number;
  title: string;
  event_type: string;
  severity: string;
  region?: string;
  detected_at?: string;
}


export default function DashboardPage() {

  const [
    overview,
    setOverview,
  ] = useState<Overview | null>(null);


  const [
    events,
    setEvents,
  ] = useState<GlobalEvent[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    refreshing,
    setRefreshing,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  const [
    lastUpdated,
    setLastUpdated,
  ] = useState<Date | null>(null);


  const loadDashboard = useCallback(
    async (
      showFullLoading = false,
    ) => {

      try {

        if (showFullLoading) {
          setLoading(true);
        } else {
          setRefreshing(true);
        }

        setError("");

        const [
          businessData,
          globalEvents,
        ] = await Promise.all([

          apiRequest<Overview>(
            "/business/overview",
          ),

          apiRequest<GlobalEvent[]>(
            "/global-events/?limit=5",
          ),

        ]);

        setOverview(
          businessData,
        );

        setEvents(
          globalEvents,
        );

        setLastUpdated(
          new Date(),
        );

      } catch (err) {

        console.error(
          "Dashboard error:",
          err,
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard.",
        );

      } finally {

        setLoading(false);
        setRefreshing(false);

      }

    },
    [],
  );


  useEffect(() => {

    loadDashboard(true);

    const interval =
      window.setInterval(
        () => {
          loadDashboard(false);
        },
        30_000,
      );

    return () => {
      window.clearInterval(interval);
    };

  }, [loadDashboard]);


  if (loading) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

          <p className="text-slate-500">
            Loading HEX dashboard...
          </p>

        </div>

      </div>
    );
  }


  if (error && !overview) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">

          <p className="font-semibold">
            Dashboard unavailable
          </p>

          <p className="mt-2">
            {error}
          </p>

          <button
            type="button"
            onClick={() => loadDashboard(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800"
          >
            <RefreshCw size={16} />
            Retry
          </button>

        </div>

      </div>
    );
  }


  const cards = [

    {
      title: "Revenue",
      value:
        overview?.revenue ?? 0,
      icon: DollarSign,
    },

    {
      title: "Expenses",
      value:
        overview?.expenses ?? 0,
      icon: ArrowDownRight,
    },

    {
      title: "Profit",
      value:
        overview?.profit ?? 0,
      icon: ArrowUpRight,
    },

    {
      title: "Orders",
      value:
        overview?.orders ?? 0,
      icon: ShoppingCart,
    },

  ];


  return (
    <div className="p-6 lg:p-8">

      {/* Header */}

      <div className="mb-8">

        <div className="flex flex-wrap items-start justify-between gap-4">

          <div>

            <p className="text-sm font-medium text-slate-500">
              Executive Overview
            </p>

            <h1 className="mt-1 text-3xl font-bold text-slate-900">
              Business Dashboard
            </h1>

            <p className="mt-2 text-slate-500">
              Your business, internal operations,
              and global intelligence in one place.
            </p>

          </div>


          {/* Live status */}

          <div className="flex flex-wrap items-center gap-3">

            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">

              <span className="relative flex h-2.5 w-2.5">

                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />

                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />

              </span>

              LIVE MONITORING

            </div>


            <button
              type="button"
              onClick={() =>
                loadDashboard(false)
              }
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
            >

              <RefreshCw
                size={16}
                className={
                  refreshing
                    ? "animate-spin"
                    : ""
                }
              />

              Refresh

            </button>

          </div>

        </div>


        {lastUpdated && (
          <p className="mt-3 text-xs text-slate-400">
            Last synchronized:{" "}
            {lastUpdated.toLocaleTimeString()}
            {" · "}
            Automatic refresh every 30 seconds
          </p>
        )}

      </div>


      {/* Non-blocking refresh warning */}

      {error && overview && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">

          Live refresh temporarily failed.

          The dashboard is still showing the
          last successfully loaded data.

        </div>
      )}


      {/* KPI Cards */}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">

        {cards.map(
          (card) => {

            const Icon =
              card.icon;

            return (

              <div
                key={card.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              >

                <div className="w-fit rounded-xl bg-slate-100 p-3">

                  <Icon size={20} />

                </div>

                <p className="mt-6 text-sm text-slate-500">
                  {card.title}
                </p>

                <p className="mt-1 text-2xl font-bold text-slate-900">

                  {typeof card.value === "number"
                    ? card.value.toLocaleString(
                        "en-IN",
                      )
                    : card.value}

                </p>

              </div>

            );
          },
        )}

      </div>


      {/* Main Intelligence Area */}

      <div className="mt-8 grid gap-6 xl:grid-cols-3">

        {/* Global Intelligence */}

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm xl:col-span-2">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="font-semibold text-slate-900">
                Global Intelligence
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                External events that may affect your business.
              </p>

            </div>


            <Link
              href="/global"
              className="rounded-xl bg-slate-100 p-3 text-slate-700 transition hover:bg-slate-200"
              aria-label="Open Global Intelligence"
            >
              <Globe2 size={22} />
            </Link>

          </div>


          <div className="mt-6 space-y-3">

            {events.length === 0 ? (

              <div className="rounded-xl bg-slate-50 p-6 text-sm text-slate-500">
                No recent global events.
              </div>

            ) : (

              events.map(
                (event) => {

                  const isHigh =
                    event.severity === "HIGH";

                  const detectedAt =
                    event.detected_at
                      ? new Date(
                          event.detected_at,
                        )
                      : null;

                  return (

                    <Link
                      key={event.id}
                      href="/global"
                      className="block rounded-xl border border-slate-200 p-4 transition hover:border-slate-400 hover:bg-slate-50"
                    >

                      <div className="flex items-center gap-4">

                        <div
                          className={
                            isHigh
                              ? "rounded-lg bg-red-50 p-2"
                              : "rounded-lg bg-amber-50 p-2"
                          }
                        >

                          <AlertTriangle
                            size={18}
                            className={
                              isHigh
                                ? "text-red-600"
                                : "text-amber-600"
                            }
                          />

                        </div>


                        <div className="min-w-0 flex-1">

                          <p className="font-medium text-slate-900">
                            {event.title}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">

                            {event.event_type}

                            {event.region
                              ? ` · ${event.region}`
                              : ""}

                          </p>

                          {detectedAt && (
                            <p className="mt-1 text-xs text-slate-400">
                              Detected{" "}
                              {detectedAt.toLocaleString()}
                            </p>
                          )}

                        </div>


                        <span
                          className={
                            isHigh
                              ? "rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700"
                              : "rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700"
                          }
                        >
                          {event.severity}
                        </span>

                      </div>

                    </Link>

                  );

                },
              )

            )}

          </div>

        </div>


        {/* Supply Chain */}

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-slate-100 p-3">
              <Truck size={20} />
            </div>

            <div>

              <h2 className="font-semibold text-slate-900">
                Supply Chain
              </h2>

              <p className="text-sm text-slate-500">
                Operational intelligence
              </p>

            </div>

          </div>


          <div className="mt-6 space-y-4">

            {[
              [
                "Route Monitoring",
                "Active",
              ],

              [
                "Supplier Risk",
                "Monitoring",
              ],

              [
                "Inventory",
                "Tracking",
              ],

            ].map(
              ([label, value]) => (

                <div
                  key={label}
                  className="rounded-xl bg-slate-50 p-4"
                >

                  <p className="text-sm text-slate-500">
                    {label}
                  </p>

                  <p className="mt-1 font-semibold text-slate-900">
                    {value}
                  </p>

                </div>

              ),
            )}

          </div>


          <Link
            href="/routes"
            className="mt-5 block rounded-xl bg-slate-900 px-4 py-3 text-center text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Open Supply Routes
          </Link>

        </div>

      </div>


      {/* Command Center */}

      <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="flex flex-wrap items-center justify-between gap-4">

          <div>

            <p className="text-sm font-medium text-slate-500">
              Decision Intelligence
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              HEX Command Center
            </h2>

            <p className="mt-2 max-w-3xl text-sm text-slate-500">
              Move from business monitoring to risk analysis,
              scenario simulation and AI-assisted decisions.
            </p>

          </div>

          <Link
            href="/copilot"
            className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-700"
          >
            Ask HEX
          </Link>

        </div>


        <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

          <Link
            href="/risk"
            className="rounded-xl border border-slate-200 p-4 transition hover:bg-slate-50"
          >

            <p className="font-semibold text-slate-900">
              Risk Center
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Analyze business exposure.
            </p>

          </Link>


          <Link
            href="/scenarios"
            className="rounded-xl border border-slate-200 p-4 transition hover:bg-slate-50"
          >

            <p className="font-semibold text-slate-900">
              Scenarios
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Simulate route decisions.
            </p>

          </Link>


          <Link
            href="/analytics"
            className="rounded-xl border border-slate-200 p-4 transition hover:bg-slate-50"
          >

            <p className="font-semibold text-slate-900">
              Analytics
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Review business performance.
            </p>

          </Link>


          <Link
            href="/approvals"
            className="rounded-xl border border-slate-200 p-4 transition hover:bg-slate-50"
          >

            <p className="font-semibold text-slate-900">
              Approvals
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Record human decisions.
            </p>

          </Link>

        </div>

      </div>

    </div>
  );
}