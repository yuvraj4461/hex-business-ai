"use client";

import { useCallback, useEffect, useState } from "react";

import Link from "next/link";

import {
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Globe2,
  RefreshCw,
  ShoppingCart,
  Truck,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import NewsTicker from "@/app/components/NewsTicker";
import SeverityBadge from "@/app/components/SeverityBadge";
import StatTile from "@/app/components/StatTile";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import { toneForStatus } from "@/app/components/tone";
import SeverityDonut from "@/app/components/charts/SeverityDonut";

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
  const [overview, setOverview] = useState<Overview | null>(null);
  const [events, setEvents] = useState<GlobalEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadDashboard = useCallback(async (showFullLoading = false) => {
    try {
      if (showFullLoading) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }
      setError("");

      const [businessData, globalEvents] = await Promise.all([
        apiRequest<Overview>("/business/overview"),
        apiRequest<GlobalEvent[]>("/global-events/?limit=5"),
      ]);

      setOverview(businessData);
      setEvents(globalEvents);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Dashboard error:", err);
      setError(
        err instanceof Error ? err.message : "Unable to load dashboard.",
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch
    loadDashboard(true);

    const interval = window.setInterval(() => {
      loadDashboard(false);
    }, 30_000);

    return () => window.clearInterval(interval);
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading command center…" />
      </div>
    );
  }

  if (error && !overview) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard
          title="Dashboard unavailable"
          message={error}
          onRetry={() => loadDashboard(true)}
        />
      </div>
    );
  }

  const worstTone = events.reduce(
    (acc, e) => {
      const t = toneForStatus(e.severity);
      const rank = { critical: 3, elevated: 2, live: 1, stable: 1, neutral: 0 };
      return rank[t] > rank[acc] ? t : acc;
    },
    "neutral" as ReturnType<typeof toneForStatus>,
  );

  const cards = [
    { title: "Revenue", value: inr(overview?.revenue), icon: DollarSign, tone: "stable" as const },
    { title: "Expenses", value: inr(overview?.expenses), icon: ArrowDownRight, tone: "elevated" as const },
    { title: "Profit", value: inr(overview?.profit), icon: ArrowUpRight, tone: "stable" as const },
    { title: "Orders", value: num(overview?.orders), icon: ShoppingCart, tone: "live" as const },
  ];

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Globe2}
        eyebrow="Executive Overview"
        title="Command Center"
        description="Your business, internal operations and global intelligence on one panel."
        actions={
          <>
            <div className="inline-flex items-center gap-2 rounded-full border border-live/25 bg-live/10 px-3 py-1.5">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-live opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-live" />
              </span>
              <span className="eyebrow !text-live">Live Monitoring</span>
            </div>

            <button
              type="button"
              onClick={() => loadDashboard(false)}
              disabled={refreshing}
              className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-3.5 py-2 text-sm font-medium text-dim transition hover:text-white disabled:opacity-60"
            >
              <RefreshCw
                size={15}
                className={refreshing ? "animate-spin" : ""}
              />
              Refresh
            </button>
          </>
        }
      />

      {lastUpdated && (
        <p className="num -mt-4 mb-4 text-xs text-mute">
          Synced {lastUpdated.toLocaleTimeString()} · auto every 30s
        </p>
      )}

      <NewsTicker />

      {error && overview && (
        <div className="mb-6 rounded-lg border border-elevated/30 bg-elevated/5 p-3 text-sm text-elevated">
          Live refresh failed — showing the last good data.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <StatTile
            key={card.title}
            label={card.title}
            value={card.value}
            icon={card.icon}
            tone={card.tone}
          />
        ))}
      </div>

      <div className="mt-6 grid gap-5 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <Panel
            tone={worstTone}
            label="External Intelligence"
            title="Global Events"
            action={
              <Link
                href="/global"
                className="text-sm font-medium text-live hover:underline"
              >
                View all
              </Link>
            }
          >
            {events.length === 0 ? (
              <p className="rounded-lg bg-panel-raised p-5 text-sm text-dim">
                No recent global events.
              </p>
            ) : (
              <div className="space-y-2.5">
                {events.map((event) => {
                  const detectedAt = event.detected_at
                    ? new Date(event.detected_at)
                    : null;

                  return (
                    <Link
                      key={event.id}
                      href="/global"
                      className="block rounded-lg border border-hairline bg-panel-raised/40 p-4 transition hover:border-live/40"
                    >
                      <div className="flex items-start gap-4">
                        <div className="min-w-0 flex-1">
                          <p className="font-medium text-white">
                            {event.title}
                          </p>
                          <p className="num mt-1 text-xs text-mute">
                            {event.event_type}
                            {event.region ? ` · ${event.region}` : ""}
                            {detectedAt
                              ? ` · ${detectedAt.toLocaleDateString()}`
                              : ""}
                          </p>
                        </div>
                        <SeverityBadge value={event.severity} />
                      </div>
                    </Link>
                  );
                })}
              </div>
            )}
          </Panel>
        </div>

        <Panel label="Distribution" title="Events by Severity" tone="live">
          <SeverityDonut items={events} />
        </Panel>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <Panel
          label="Operational Intelligence"
          title="Supply Chain"
          tone="stable"
          action={<Truck size={18} className="text-dim" />}
        >
          <div className="space-y-2.5">
            {[
              ["Route Monitoring", "Active"],
              ["Supplier Risk", "Monitoring"],
              ["Inventory", "Tracking"],
            ].map(([label, value]) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-lg bg-panel-raised px-4 py-3"
              >
                <p className="text-sm text-dim">{label}</p>
                <p className="text-sm font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>

          <Link
            href="/routes"
            className="mt-4 block rounded-lg bg-accent px-4 py-2.5 text-center text-sm font-semibold text-bg transition hover:bg-accent/90"
          >
            Open Supply Routes
          </Link>
        </Panel>

        <div className="lg:col-span-2">
          <Panel
            label="Decision Intelligence"
            title="Next Actions"
            tone="live"
            action={
              <Link
                href="/copilot"
                className="rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg transition hover:bg-accent/90"
              >
                Ask HEX
              </Link>
            }
          >
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ["/risk", "Risk Center", "Analyze business exposure."],
                ["/scenarios", "Scenarios", "Simulate route decisions."],
                ["/analytics", "Analytics", "Review business performance."],
                ["/approvals", "Approvals", "Record human decisions."],
              ].map(([href, title, desc]) => (
                <Link
                  key={href}
                  href={href}
                  className="rounded-lg border border-hairline bg-panel-raised/40 p-4 transition hover:border-live/40"
                >
                  <p className="font-semibold text-white">{title}</p>
                  <p className="mt-1 text-xs text-mute">{desc}</p>
                </Link>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
