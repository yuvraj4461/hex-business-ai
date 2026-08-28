"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import {
  CheckCircle2,
  Clock3,
  DollarSign,
  Info,
  Loader2,
  Route as RouteIcon,
  ShieldAlert,
  Sparkles,
  Truck,
  XCircle,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import Panel from "@/app/components/Panel";
import SeverityBadge from "@/app/components/SeverityBadge";
import StatTile from "@/app/components/StatTile";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import { toneForStatus } from "@/app/components/tone";

interface RouteOption {
  route_id?: number;
  route_name?: string;
  corridor?: string;
  transit_days?: number;
  freight_cost?: number;
  risk_level?: string;
}

interface ScenarioData {
  status: string;
  message?: string;
  event?: {
    id?: number;
    title?: string;
    type?: string;
    severity?: string;
    region?: string;
  };
  exposure?: {
    exposures?: unknown[];
    financial?: {
      total_cost_impact?: number;
      total_revenue_at_risk?: number;
    };
  };
  route_alternatives?: RouteOption[];
  ai_recommendation?: string;
}

function ScenariosView() {
  const searchParams = useSearchParams();
  const eventId = searchParams.get("event");

  const [data, setData] = useState<ScenarioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState("");

  const loadScenario = useCallback(async () => {
    try {
      setLoading(true);
      setError("");
      setApproved(false);
      const path = eventId
        ? `/scenarios/${encodeURIComponent(eventId)}`
        : "/demo/red-sea";
      setData(await apiRequest<ScenarioData>(path));
    } catch (err) {
      console.error("[HEX] Scenario error:", err);
      setError(
        err instanceof Error ? err.message : "Unable to load scenario.",
      );
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- fetch on mount / param change
    loadScenario();
  }, [loadScenario]);

  async function approveRecommendation() {
    if (!data?.ai_recommendation) return;

    try {
      setApproving(true);
      setError("");

      await apiRequest("/approvals", {
        method: "POST",
        body: JSON.stringify({
          recommendation: data.ai_recommendation,
          scenario: data.event?.title ?? "Scenario analysis",
          event_id: data.event?.id ?? null,
          comment: "Approved from HEX scenario dashboard.",
        }),
      });

      setApproved(true);
    } catch (err) {
      console.error("[HEX] Approval failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to approve recommendation.",
      );
    } finally {
      setApproving(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Running HEX scenario analysis…" />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard
          title="Scenario analysis failed"
          message={error}
          onRetry={loadScenario}
        />
      </div>
    );
  }

  if (!data) return null;

  const event = data.event;
  const financial = data.exposure?.financial;
  const routeOptions = data.route_alternatives ?? [];
  const affectedCount = data.exposure?.exposures?.length ?? 0;
  const hasExposure = affectedCount > 0;

  const eventTitle =
    event?.title ??
    (eventId ? "Scenario Simulation" : "Simulated Red Sea shipping disruption");
  const eventRegion = event?.region ?? (eventId ? "—" : "Red Sea");
  const eventSeverity = event?.severity ?? "HIGH";

  return (
    <div className="p-6 lg:p-8">
      {error && (
        <div className="mb-6 flex items-center justify-between gap-4 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
          <p>{error}</p>
          <button
            type="button"
            onClick={() => setError("")}
            className="font-semibold underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Hero */}
      <div className="relative overflow-hidden rounded-xl border border-hairline bg-panel p-7">
        <span
          aria-hidden
          className={`absolute inset-y-0 left-0 w-[3px] ${
            hasExposure ? "bg-critical" : "bg-stable"
          }`}
        />
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <p className="eyebrow">Scenario Simulation</p>
            <h1 className="mt-2 text-3xl font-bold text-white">{eventTitle}</h1>
            <p className="mt-3 max-w-2xl text-sm text-dim">
              HEX evaluates the event, business exposure, route
              alternatives, financial impact and an AI recommendation.
            </p>
          </div>

          <div
            className={`rounded-lg border px-4 py-3 ${
              hasExposure
                ? "border-critical/30 bg-critical/10"
                : "border-stable/30 bg-stable/10"
            }`}
          >
            <SeverityBadge value={`${eventSeverity} RISK`} />
            <p className="mt-2 text-sm text-dim">{eventRegion}</p>
          </div>
        </div>
      </div>

      <div className="mt-5">
        <Panel
          tone={toneForStatus(event?.severity)}
          label="Detected Event"
          title={eventTitle}
        >
          <p className="num text-sm text-mute">
            {(event?.type ?? "LOGISTICS")} · {eventRegion}
          </p>
        </Panel>
      </div>

      {!hasExposure && (
        <div className="mt-5">
          <Panel
            tone="stable"
            label="Exposure"
            title="No supply-chain exposure detected"
            action={<Info size={18} className="text-stable" />}
          >
            <p className="text-sm leading-6 text-dim">
              This event does not intersect any of your active supply
              routes or open shipments, so HEX projects no direct
              operational or financial impact. It stays on the watch list
              and will be re-evaluated if your routes or its severity
              change.
            </p>
          </Panel>
        </div>
      )}

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <StatTile
          label="Revenue at Risk"
          value={inr(financial?.total_revenue_at_risk)}
          icon={DollarSign}
          tone={hasExposure ? "critical" : "stable"}
        />
        <StatTile
          label="Affected Routes"
          value={num(affectedCount)}
          icon={Truck}
          tone={hasExposure ? "elevated" : "stable"}
        />
        <StatTile
          label="Scenario Status"
          value={approved ? "APPROVED" : hasExposure ? "AWAITING REVIEW" : "NO ACTION NEEDED"}
          icon={ShieldAlert}
          tone={approved || !hasExposure ? "stable" : "elevated"}
        />
      </div>

      {hasExposure && (
        <section className="mt-8">
          <h2 className="eyebrow mb-4">Route Decision</h2>

          <div className="grid gap-5 lg:grid-cols-2">
            <Panel
              tone="critical"
              label="Current Route"
              title="Affected Corridor"
            >
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-panel-raised p-3">
                  <div className="flex items-center gap-1.5 text-mute">
                    <Clock3 size={14} />
                    <span className="eyebrow">Routes hit</span>
                  </div>
                  <p className="num mt-1.5 text-lg font-semibold text-white">
                    {num(affectedCount)}
                  </p>
                </div>
                <div className="rounded-lg bg-panel-raised p-3">
                  <div className="flex items-center gap-1.5 text-mute">
                    <DollarSign size={14} />
                    <span className="eyebrow">Impact</span>
                  </div>
                  <p className="num mt-1.5 text-lg font-semibold text-white">
                    {inr(financial?.total_cost_impact)}
                  </p>
                </div>
              </div>
            </Panel>

            <Panel
              tone="live"
              label="HEX Route Engine"
              title="Alternatives"
              action={<RouteIcon size={18} className="text-dim" />}
            >
              {routeOptions.length === 0 ? (
                <p className="rounded-lg bg-panel-raised p-4 text-sm text-dim">
                  No alternative route data was returned by the backend.
                </p>
              ) : (
                <div className="space-y-2.5">
                  {routeOptions.map((route, index) => (
                    <div
                      key={route.route_id ?? index}
                      className="rounded-lg border border-hairline bg-panel-raised/40 p-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-semibold text-white">
                            {route.route_name ??
                              `Alternative Route #${index + 1}`}
                          </p>
                          <p className="text-xs text-mute">
                            {route.corridor ?? "Alternative corridor"}
                          </p>
                        </div>
                        <SeverityBadge value={route.risk_level ?? "UNKNOWN"} />
                      </div>

                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div>
                          <p className="eyebrow">Transit</p>
                          <p className="num font-semibold text-white">
                            {num(route.transit_days)} days
                          </p>
                        </div>
                        <div>
                          <p className="eyebrow">Freight</p>
                          <p className="num font-semibold text-white">
                            {route.freight_cost != null
                              ? inr(route.freight_cost)
                              : "—"}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Panel>
          </div>
        </section>
      )}

      <section className="mt-8">
        <Panel
          tone="live"
          label="Decision Intelligence"
          title="HEX Recommendation"
          action={<Sparkles size={18} className="text-live" />}
        >
          <div className="rounded-lg bg-panel-raised p-4">
            <p className="whitespace-pre-wrap text-sm leading-6 text-dim">
              {data.ai_recommendation ??
                "HEX has not generated a recommendation yet."}
            </p>
          </div>
        </Panel>
      </section>

      {hasExposure && (
        <section className="mt-5">
          <Panel tone="elevated" title="Human approval required">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <p className="max-w-2xl text-sm text-dim">
                HEX provides decision support. High-impact operational
                decisions require authorized human review.
              </p>

              {!approved ? (
                <div className="flex gap-3">
                  <button
                    type="button"
                    disabled={approving || !data.ai_recommendation}
                    onClick={approveRecommendation}
                    className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {approving ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Approving…
                      </>
                    ) : (
                      <>
                        <CheckCircle2 size={16} />
                        Approve
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-lg border border-hairline px-4 py-2.5 text-sm font-semibold text-dim transition hover:text-white"
                  >
                    <XCircle size={16} />
                    Reject
                  </button>
                </div>
              ) : (
                <div className="inline-flex items-center gap-2 rounded-lg bg-stable/15 px-4 py-2.5 text-sm font-semibold text-stable">
                  <CheckCircle2 size={16} />
                  Recommendation approved
                </div>
              )}
            </div>
          </Panel>
        </section>
      )}
    </div>
  );
}

export default function ScenariosPage() {
  return (
    <Suspense
      fallback={
        <div className="p-6 lg:p-8">
          <LoadingCard message="Running HEX scenario analysis…" />
        </div>
      }
    >
      <ScenariosView />
    </Suspense>
  );
}
