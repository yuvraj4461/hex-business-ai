"use client";

import { useEffect, useState } from "react";

import {
  CheckCircle2,
  Clock3,
  DollarSign,
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

export default function ScenariosPage() {
  const [data, setData] = useState<ScenarioData | null>(null);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  const [approved, setApproved] = useState(false);
  const [error, setError] = useState("");

  async function loadScenario() {
    try {
      setLoading(true);
      setError("");
      setData(await apiRequest<ScenarioData>("/demo/red-sea"));
    } catch (err) {
      console.error("[HEX] Scenario error:", err);
      setError(
        err instanceof Error ? err.message : "Unable to load scenario.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch
    loadScenario();
  }, []);

  async function approveRecommendation() {
    if (!data?.ai_recommendation) return;

    try {
      setApproving(true);
      setError("");

      await apiRequest("/approvals", {
        method: "POST",
        body: JSON.stringify({
          recommendation: data.ai_recommendation,
          scenario: "Red Sea shipping disruption",
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
          className="absolute inset-y-0 left-0 w-[3px] bg-critical"
        />
        <div className="flex flex-wrap items-start justify-between gap-6">
          <div>
            <p className="eyebrow">Scenario Simulation</p>
            <h1 className="mt-2 text-3xl font-bold text-white">
              Red Sea Disruption
            </h1>
            <p className="mt-3 max-w-2xl text-sm text-dim">
              HEX evaluates the disruption, business exposure, route
              alternatives, financial impact and an AI recommendation.
            </p>
          </div>

          <div className="rounded-lg border border-critical/30 bg-critical/10 px-4 py-3">
            <SeverityBadge value={`${event?.severity ?? "HIGH"} RISK`} />
            <p className="mt-2 text-sm text-dim">
              {event?.region ?? "Red Sea"}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-5">
        <Panel
          tone={toneForStatus(event?.severity)}
          label="Detected Event"
          title={
            event?.title ?? "Simulated Red Sea shipping disruption"
          }
        >
          <p className="num text-sm text-mute">
            {event?.type ?? "LOGISTICS"} · {event?.region ?? "Red Sea"}
          </p>
        </Panel>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <StatTile
          label="Revenue at Risk"
          value={inr(financial?.total_revenue_at_risk)}
          icon={DollarSign}
          tone="critical"
        />
        <StatTile
          label="Affected Routes"
          value={num(data.exposure?.exposures?.length ?? 0)}
          icon={Truck}
          tone="elevated"
        />
        <StatTile
          label="Scenario Status"
          value={approved ? "APPROVED" : "AWAITING REVIEW"}
          icon={ShieldAlert}
          tone={approved ? "stable" : "elevated"}
        />
      </div>

      <section className="mt-8">
        <h2 className="eyebrow mb-4">Route Decision</h2>

        <div className="grid gap-5 lg:grid-cols-2">
          <Panel tone="critical" label="Current Route" title="Red Sea Corridor">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-panel-raised p-3">
                <div className="flex items-center gap-1.5 text-mute">
                  <Clock3 size={14} />
                  <span className="eyebrow">Delay</span>
                </div>
                <p className="num mt-1.5 text-lg font-semibold text-white">
                  +14 days
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
    </div>
  );
}
