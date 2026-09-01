"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ArrowRight,
  DollarSign,
  Loader2,
  Package,
  Info,
  ShieldAlert,
  Truck,
  Users,
  X,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import IntelCard from "@/app/components/IntelCard";
import SeverityBadge from "@/app/components/SeverityBadge";
import StatTile from "@/app/components/StatTile";
import { EmptyCard, LoadingCard } from "@/app/components/StateCard";
import { TONE_RAIL, toneForStatus } from "@/app/components/tone";

interface Event {
  id: number;
  title: string;
  severity: string;
  event_type: string;
  region?: string;
}

interface ExposureRow {
  route_id?: number;
  route_name?: string;
  supplier_id?: number;
  product_id?: number;
  delay_days?: number;
  cost_impact?: number;
  revenue_at_risk?: number;
  severity?: string;
}

interface SupplierRow {
  supplier_id?: number;
  route_count?: number;
  product_count?: number;
}

interface ProductRow {
  product_id?: number;
  delay_days?: number;
}

interface Exposure {
  event?: {
    id?: number;
    type?: string;
    title?: string;
    severity?: string;
    region?: string;
  };
  exposures?: ExposureRow[];
  suppliers?: SupplierRow[];
  products?: ProductRow[];
  financial?: {
    total_cost_impact?: number;
    total_revenue_at_risk?: number;
  };
  business_risk?: {
    score?: number;
    level?: string;
  };
}

export default function RiskPage() {
  const router = useRouter();

  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<Exposure | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingExposureId, setLoadingExposureId] = useState<number | null>(
    null,
  );
  const [error, setError] = useState("");
  const [exposureError, setExposureError] = useState("");

  useEffect(() => {
    async function loadEvents() {
      try {
        setLoading(true);
        setError("");
        setEvents(
          await apiRequest<Event[]>("/global-events/?limit=40"),
        );
      } catch (err) {
        console.error("Failed to load global events:", err);
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load risk center.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadEvents();
  }, []);

  async function handleEventClick(eventId: number) {
    try {
      setLoadingExposureId(eventId);
      setExposureError("");
      const data = await apiRequest<Exposure>(
        `/global-exposure/${eventId}`,
      );
      setSelectedEvent(data);
    } catch (err) {
      console.error("Failed to load event exposure:", err);
      setExposureError(
        err instanceof Error
          ? err.message
          : "Unable to load exposure data.",
      );
      setSelectedEvent(null);
    } finally {
      setLoadingExposureId(null);
    }
  }

  function openFullScenario() {
    const eventId = selectedEvent?.event?.id;
    if (!eventId) return;
    router.push(`/scenarios?event=${eventId}`);
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading risk center…" />
      </div>
    );
  }

  const riskLevel = selectedEvent?.business_risk?.level ?? "LOW";
  const affectedCount = selectedEvent?.exposures?.length ?? 0;
  const hasExposure = affectedCount > 0;

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={ShieldAlert}
        tone="critical"
        eyebrow="Decision Intelligence"
        title="Risk Center"
        description="Understand how external events translate into operational and financial exposure."
      />

      {error && (
        <div className="mb-6 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
          {error}
        </div>
      )}

      {exposureError && (
        <div className="mb-6 flex items-start justify-between gap-4 rounded-lg border border-critical/30 bg-critical/5 p-3">
          <div>
            <p className="font-semibold text-critical">
              Unable to load exposure analysis
            </p>
            <p className="mt-1 text-sm text-dim">{exposureError}</p>
          </div>
          <button
            type="button"
            onClick={() => setExposureError("")}
            className="rounded-lg p-1 text-critical hover:bg-critical/10"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <section>
        {events.length === 0 ? (
          <>
            <h2 className="eyebrow mb-1">Global Events</h2>
            <EmptyCard message="No global events available." />
          </>
        ) : (
          <IntelCard
            label="Signals"
            title="Global Events"
            tone={
              events.some((e) => /crit|high/i.test(e.severity))
                ? "critical"
                : "live"
            }
            maxHeight="62vh"
            action={
              <span className="num text-xs text-mute">
                {events.length} tracked
              </span>
            }
          >
            <p className="mb-4 text-sm text-dim">
              Select an event to analyze its impact on your business.
            </p>
            <div className="grid gap-3 lg:grid-cols-2">
              {events.map((event) => {
                const isLoading = loadingExposureId === event.id;
                const isSelected = selectedEvent?.event?.id === event.id;

                return (
                  <div
                    key={event.id}
                    className={`relative overflow-hidden rounded-lg border bg-panel-raised/40 p-3 ${
                      isSelected
                        ? "border-critical/40 ring-1 ring-critical/30"
                        : "border-hairline"
                    }`}
                  >
                    <span
                      aria-hidden
                      className={`absolute inset-y-0 left-0 w-[3px] ${TONE_RAIL[toneForStatus(event.severity)]}`}
                    />
                    <div className="flex items-start justify-between gap-3 pl-2">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-white">
                          {event.title}
                        </p>
                        <p className="num mt-1 text-[0.7rem] text-mute">
                          {event.event_type}
                          {event.region ? ` · ${event.region}` : ""}
                        </p>
                      </div>
                      <SeverityBadge value={event.severity} />
                    </div>

                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() => handleEventClick(event.id)}
                      className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isLoading ? (
                        <>
                          <Loader2 size={15} className="animate-spin" />
                          Analyzing…
                        </>
                      ) : isSelected ? (
                        "Exposure loaded"
                      ) : (
                        "Analyze business impact"
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          </IntelCard>
        )}
      </section>

      {selectedEvent && (
        <section className="mt-10">
          <Panel
            tone={toneForStatus(selectedEvent.event?.severity)}
            label="Selected Event"
            title={selectedEvent.event?.title ?? "Global Event"}
          >
            <p className="num text-sm text-mute">
              {selectedEvent.event?.type ?? "UNKNOWN"}
              {" · "}
              {selectedEvent.event?.severity ?? "UNKNOWN"}
              {selectedEvent.event?.region
                ? ` · ${selectedEvent.event.region}`
                : ""}
            </p>
          </Panel>

          {!hasExposure && (
            <div className="mt-5">
              <Panel
                tone="stable"
                label="Exposure"
                title="No exposure to your supply chain"
                action={<Info size={18} className="text-stable" />}
              >
                <p className="text-sm leading-6 text-dim">
                  HEX matched this event against your active supply routes
                  and open shipments and found no overlap — none of your
                  lanes pass through the affected region or corridor, so
                  there is no projected cost or revenue impact. If you
                  expected exposure here, check that your routes and
                  shipments are synced under Integrations.
                </p>
              </Panel>
            </div>
          )}

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            <StatTile
              label="Revenue at Risk"
              value={inr(
                selectedEvent.financial?.total_revenue_at_risk,
              )}
              icon={DollarSign}
              tone="critical"
            />
            <StatTile
              label="Affected Routes"
              value={num(selectedEvent.exposures?.length ?? 0)}
              icon={Truck}
              tone="elevated"
            />
            <StatTile
              label="Business Risk"
              value={riskLevel}
              delta={`score ${num(
                selectedEvent.business_risk?.score ?? 0,
              )}/100`}
              deltaTone={toneForStatus(riskLevel)}
              icon={ShieldAlert}
              tone={toneForStatus(riskLevel)}
            />
          </div>

          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <Panel
              label="Exposed"
              title="Affected Suppliers"
              tone="live"
              action={<Users size={18} className="text-dim" />}
            >
              {(selectedEvent.suppliers ?? []).length === 0 ? (
                <p className="rounded-lg bg-panel-raised p-4 text-sm text-dim">
                  No affected suppliers found.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {selectedEvent.suppliers?.map((supplier) => (
                    <div
                      key={supplier.supplier_id}
                      className="rounded-lg bg-panel-raised p-3"
                    >
                      <p className="font-medium text-white">
                        Supplier #{supplier.supplier_id}
                      </p>
                      <p className="num mt-1 text-xs text-mute">
                        {num(supplier.route_count)} routes ·{" "}
                        {num(supplier.product_count)} products
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>

            <Panel
              label="Exposed"
              title="Affected Products"
              tone="live"
              action={<Package size={18} className="text-dim" />}
            >
              {(selectedEvent.products ?? []).length === 0 ? (
                <p className="rounded-lg bg-panel-raised p-4 text-sm text-dim">
                  No affected products found.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {selectedEvent.products?.map((product) => (
                    <div
                      key={product.product_id}
                      className="rounded-lg bg-panel-raised p-3"
                    >
                      <p className="font-medium text-white">
                        Product #{product.product_id}
                      </p>
                      <p className="num mt-1 text-xs text-mute">
                        Delay: {num(product.delay_days)} days
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>

          <div className="mt-5">
            <Panel label="Route-level" title="Exposure Details" tone="critical">
              {(selectedEvent.exposures ?? []).length === 0 ? (
                <p className="rounded-lg bg-panel-raised p-4 text-sm text-dim">
                  No individual route exposures returned by the backend.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-hairline">
                        {[
                          "Route",
                          "Supplier",
                          "Product",
                          "Delay",
                          "Cost Impact",
                          "Revenue Risk",
                          "Severity",
                        ].map((h) => (
                          <th
                            key={h}
                            className="eyebrow px-3 py-2.5 font-semibold"
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {selectedEvent.exposures?.map((exposure, index) => (
                        <tr
                          key={exposure.route_id ?? index}
                          className="border-b border-hairline last:border-0"
                        >
                          <td className="px-3 py-3">
                            {exposure.route_name ??
                              `Route #${exposure.route_id}`}
                          </td>
                          <td className="num px-3 py-3">
                            #{exposure.supplier_id}
                          </td>
                          <td className="num px-3 py-3">
                            #{exposure.product_id}
                          </td>
                          <td className="num px-3 py-3">
                            {num(exposure.delay_days)} days
                          </td>
                          <td className="num px-3 py-3">
                            {inr(exposure.cost_impact)}
                          </td>
                          <td className="num px-3 py-3">
                            {inr(exposure.revenue_at_risk)}
                          </td>
                          <td className="px-3 py-3">
                            <SeverityBadge value={exposure.severity} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="button"
              disabled={!selectedEvent.event?.id}
              onClick={openFullScenario}
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-50"
            >
              View full scenario
              <ArrowRight size={16} />
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
