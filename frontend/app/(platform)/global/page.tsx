"use client";

import { useEffect, useState } from "react";

import { DollarSign, Globe2, Wheat } from "lucide-react";

import { apiRequest } from "@/lib/api";
import { signedPercent } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import SeverityBadge from "@/app/components/SeverityBadge";
import { EmptyCard, LoadingCard } from "@/app/components/StateCard";
import { toneForStatus } from "@/app/components/tone";

interface GlobalEvent {
  id: number;
  title: string;
  event_type: string;
  severity: string;
  region?: string;
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

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [marketError, setMarketError] = useState("");
  const [agricultureError, setAgricultureError] = useState("");

  useEffect(() => {
    async function loadGlobalData() {
      setLoading(true);
      setError("");

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

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Globe2}
        eyebrow="External Intelligence"
        title="Global Intelligence"
        description="Global events, commodities, agriculture and currency signals that may affect your business."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
          {error}
        </div>
      )}

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
