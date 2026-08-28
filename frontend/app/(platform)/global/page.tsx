"use client";

import { useEffect, useState } from "react";

import {
  Activity,
  DollarSign,
  ExternalLink,
  Globe2,
  Loader2,
  RefreshCw,
  Radar,
  Wheat,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { num, signedPercent } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import SeverityBadge from "@/app/components/SeverityBadge";
import { EmptyCard, LoadingCard } from "@/app/components/StateCard";
import { toneForStatus } from "@/app/components/tone";
import IncidentTrend, {
  type TrendDay,
} from "@/app/components/charts/IncidentTrend";
import BarBreakdown from "@/app/components/charts/BarBreakdown";

interface GlobalEvent {
  id: number;
  title: string;
  event_type: string;
  severity: string;
  region?: string;
}

interface FeedItem {
  id: number;
  source: string;
  event_type: string;
  title: string;
  summary?: string | null;
  severity: string;
  region?: string | null;
  url?: string | null;
  sources: { title?: string; url?: string }[];
  detected_at?: string | null;
}

interface FeedStatus {
  last_run_at: string | null;
  high_events_24h: number;
}

interface TrendData {
  days: number;
  total: number;
  high_critical: number;
  daily: TrendDay[];
  by_type: { type: string; count: number }[];
  by_severity: { severity: string; count: number }[];
}

function timeAgo(iso?: string | null): string {
  if (!iso) return "never";
  const secs = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
  return `${Math.round(secs / 86400)}d ago`;
}

interface CommodityDatum {
  latest_value?: number | string;
  unit?: string;
  percentage_change?: number;
}

interface MarketOverview {
  commodities?: Record<string, CommodityDatum>;
  fx?: Record<string, unknown>;
}

interface AgricultureRisk {
  id?: number;
  crop?: string;
  region?: string;
  severity?: string;
  signal_type?: string;
  value?: number | string;
  unit?: string;
}

interface AgricultureOverview {
  risks?: AgricultureRisk[];
  commodity_impact?: unknown[];
}

export default function GlobalPage() {
  const [events, setEvents] = useState<GlobalEvent[]>([]);
  const [market, setMarket] = useState<MarketOverview | null>(null);
  const [agriculture, setAgriculture] =
    useState<AgricultureOverview | null>(null);
  const [feed, setFeed] = useState<FeedItem[]>([]);
  const [feedStatus, setFeedStatus] = useState<FeedStatus | null>(null);
  const [trend, setTrend] = useState<TrendData | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [marketError, setMarketError] = useState("");
  const [agricultureError, setAgricultureError] = useState("");

  async function loadFeed() {
    try {
      const [items, status] = await Promise.all([
        apiRequest<FeedItem[]>("/intelligence/feed?limit=20"),
        apiRequest<FeedStatus>("/intelligence/status"),
      ]);
      setFeed(items);
      setFeedStatus(status);
    } catch {
      /* feed is optional */
    }

    try {
      setTrend(
        await apiRequest<TrendData>("/intelligence/trend?days=14"),
      );
    } catch {
      /* trend is optional */
    }
  }

  async function refreshFeed() {
    setRefreshing(true);
    try {
      await apiRequest("/intelligence/refresh-now", { method: "POST" });
      await loadFeed();
    } catch {
      /* ignore */
    } finally {
      setRefreshing(false);
    }
  }

  useEffect(() => {
    async function loadGlobalData() {
      setLoading(true);
      setError("");

      void loadFeed();

      try {
        setEvents(
          await apiRequest<GlobalEvent[]>("/global-events/?limit=10"),
        );
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load global events.",
        );
      }

      try {
        setMarket(await apiRequest<MarketOverview>("/market/overview"));
      } catch (err) {
        console.error("Market intelligence error:", err);
        setMarketError(
          err instanceof Error ? err.message : "Market data unavailable.",
        );
      }

      try {
        setAgriculture(
          await apiRequest<AgricultureOverview>("/agriculture/overview"),
        );
      } catch (err) {
        console.error("Agriculture intelligence error:", err);
        setAgricultureError(
          err instanceof Error
            ? err.message
            : "Agriculture data unavailable.",
        );
      }

      setLoading(false);
    }

    loadGlobalData();
  }, []);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading global intelligence…" />
      </div>
    );
  }

  const commodities = Object.entries(market?.commodities ?? {});
  const risks = (agriculture?.risks ?? []).slice(0, 6);

  const topCategory = trend?.by_type?.[0];
  const typeBreakdown = (trend?.by_type ?? []).slice(0, 6).map((t) => ({
    name: t.type.replace(/_/g, " "),
    value: t.count,
  }));

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Globe2}
        eyebrow="External Intelligence"
        title="Global Intelligence"
        description="Global events, commodities, agriculture and currency signals that may affect your business."
        actions={
          <button
            type="button"
            onClick={refreshFeed}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-3.5 py-2 text-sm font-medium text-dim transition hover:text-white disabled:opacity-60"
          >
            {refreshing ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <RefreshCw size={15} />
            )}
            Refresh intelligence
          </button>
        }
      />

      {error && (
        <div className="mb-6 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
          {error}
        </div>
      )}

      {/* Incident Activity — the headline graph */}
      <section className="mb-8">
        <Panel
          label={
            <span className="flex items-center gap-1.5">
              <Activity size={12} /> World Watch
            </span>
          }
          title={`Incident Activity — last ${trend?.days ?? 14} days`}
          tone={(trend?.high_critical ?? 0) > 0 ? "critical" : "live"}
          action={
            <div className="flex gap-5 text-right">
              <div>
                <p className="num text-lg font-semibold text-white">
                  {num(trend?.total ?? 0)}
                </p>
                <p className="eyebrow">incidents</p>
              </div>
              <div>
                <p className="num text-lg font-semibold text-critical">
                  {num(trend?.high_critical ?? 0)}
                </p>
                <p className="eyebrow">high / critical</p>
              </div>
              {topCategory && (
                <div>
                  <p className="text-lg font-semibold text-white">
                    {topCategory.type.replace(/_/g, " ")}
                  </p>
                  <p className="eyebrow">most active</p>
                </div>
              )}
            </div>
          }
        >
          <IncidentTrend data={trend?.daily ?? []} height={300} />

          {typeBreakdown.length > 0 && (
            <div className="mt-6 border-t border-hairline pt-5">
              <p className="eyebrow mb-3">Incidents by category</p>
              <BarBreakdown
                data={typeBreakdown}
                currency={false}
                height={200}
              />
            </div>
          )}
        </Panel>
      </section>

      {/* Live Feed — World Watch */}
      <section className="mb-8">
        <Panel
          label={
            <span className="flex items-center gap-1.5">
              <Radar size={12} /> World Watch
            </span>
          }
          title="Live Feed"
          tone={
            (feedStatus?.high_events_24h ?? 0) > 0 ? "critical" : "live"
          }
          action={
            <span className="num text-xs text-mute">
              {feedStatus?.high_events_24h ?? 0} HIGH / 24h · updated{" "}
              {timeAgo(feedStatus?.last_run_at)}
            </span>
          }
        >
          {feed.length === 0 ? (
            <p className="rounded-lg bg-panel-raised p-4 text-sm text-dim">
              No feed items yet. Hit “Refresh intelligence”, or the scheduled
              collector will populate this shortly.
            </p>
          ) : (
            <div className="space-y-2">
              {feed.map((item) => (
                <div
                  key={`${item.source}-${item.id}`}
                  className="rounded-lg border border-hairline bg-panel-raised/40 p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white">
                        {item.title}
                      </p>
                      {item.summary && (
                        <p className="mt-1 line-clamp-2 text-xs text-dim">
                          {item.summary}
                        </p>
                      )}
                      <p className="num mt-1 text-[0.7rem] text-mute">
                        {item.source} · {item.event_type}
                        {item.region ? ` · ${item.region}` : ""} ·{" "}
                        {timeAgo(item.detected_at)}
                      </p>
                    </div>
                    <SeverityBadge value={item.severity} />
                  </div>

                  {(item.sources.length > 0 || item.url) && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(item.sources.length
                        ? item.sources
                        : [{ title: "source", url: item.url ?? undefined }]
                      )
                        .slice(0, 3)
                        .map(
                          (s, i) =>
                            s.url && (
                              <a
                                key={i}
                                href={s.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1 rounded-md bg-panel-raised px-2 py-0.5 text-[0.7rem] text-live hover:underline"
                              >
                                <ExternalLink size={10} />
                                {(s.title ?? new URL(s.url).hostname).slice(
                                  0,
                                  32,
                                )}
                              </a>
                            ),
                        )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Panel>
      </section>

      {/* Events */}
      <section>
        <h2 className="eyebrow mb-3">Global Events</h2>

        {events.length === 0 ? (
          <EmptyCard message="No global events available." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {events.map((event) => (
              <Panel key={event.id} tone={toneForStatus(event.severity)}>
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-white">
                      {event.title}
                    </h3>
                    <p className="num mt-1 text-xs text-mute">
                      {event.event_type}
                      {event.region ? ` · ${event.region}` : ""}
                    </p>
                  </div>
                  <SeverityBadge value={event.severity} />
                </div>
              </Panel>
            ))}
          </div>
        )}
      </section>

      {/* Market */}
      <section className="mt-10">
        <h2 className="eyebrow mb-3 flex items-center gap-2">
          <DollarSign size={13} /> Market Intelligence
        </h2>

        {marketError ? (
          <div className="rounded-lg border border-elevated/30 bg-elevated/5 p-4 text-sm text-elevated">
            Market intelligence is temporarily unavailable.
          </div>
        ) : commodities.length === 0 ? (
          <EmptyCard message="No commodity data available." />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {commodities.map(([name, data]) => {
              const change = Number(data?.percentage_change ?? 0);
              const tone = change >= 0 ? "stable" : "critical";

              return (
                <Panel key={name} tone={tone}>
                  <p className="eyebrow">{name}</p>
                  <p className="num mt-2 text-2xl font-semibold text-white">
                    {data?.latest_value ?? "—"}
                  </p>
                  <p className="mt-0.5 text-xs text-mute">
                    {data?.unit ?? ""}
                  </p>
                  <p
                    className={`num mt-3 text-sm font-semibold ${
                      change >= 0 ? "text-stable" : "text-critical"
                    }`}
                  >
                    {signedPercent(change)}
                  </p>
                </Panel>
              );
            })}
          </div>
        )}
      </section>

      {/* Agriculture */}
      <section className="mt-10">
        <h2 className="eyebrow mb-3 flex items-center gap-2">
          <Wheat size={13} /> Agriculture Intelligence
        </h2>

        {agricultureError ? (
          <div className="rounded-lg border border-elevated/30 bg-elevated/5 p-4 text-sm text-elevated">
            Agriculture intelligence is temporarily unavailable.
          </div>
        ) : risks.length === 0 ? (
          <EmptyCard message="No agriculture signals available." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {risks.map((risk, index) => (
              <Panel
                key={risk.id ?? index}
                tone={toneForStatus(risk.severity)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white">
                      {risk.crop ?? "Crop"}
                    </p>
                    <p className="text-sm text-dim">{risk.region ?? ""}</p>
                  </div>
                  <SeverityBadge value={risk.severity ?? "INFO"} />
                </div>

                <div className="mt-4">
                  <p className="eyebrow">{risk.signal_type ?? "Signal"}</p>
                  <p className="num mt-1 text-xl font-semibold text-white">
                    {risk.value ?? "—"}
                    {risk.unit ? ` ${risk.unit}` : ""}
                  </p>
                </div>
              </Panel>
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <Panel label="Intelligence Summary" title="How HEX uses these signals" tone="live">
          <p className="text-sm leading-6 text-dim">
            HEX continuously combines external signals with internal business
            data to determine how global events could affect suppliers,
            products, routes and financial performance.
          </p>
        </Panel>
      </section>
    </div>
  );
}
