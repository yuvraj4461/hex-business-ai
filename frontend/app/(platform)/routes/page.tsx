"use client";

import { useEffect, useMemo, useState } from "react";

import {
  CheckCircle2,
  Clock3,
  DollarSign,
  MapPinned,
  Route as RouteIcon,
  Ship,
  Truck,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import IntelCard from "@/app/components/IntelCard";
import SeverityBadge from "@/app/components/SeverityBadge";
import StatTile from "@/app/components/StatTile";
import { EmptyCard, ErrorCard, LoadingCard } from "@/app/components/StateCard";
import { TONE_RAIL, toneForStatus } from "@/app/components/tone";

interface RouteItem {
  id: number;
  route_name: string;
  origin_country: string;
  origin_port: string;
  destination_country: string;
  destination_port: string;
  transport_mode: string;
  corridor: string;
  distance_km: number;
  transit_days: number;
  freight_cost: number;
  risk_level: string;
  status: string;
  supplier?: { id: number; name: string } | null;
  product?: { id: number; name: string } | null;
}

interface RoutesResponse {
  organization_id: number;
  routes: RouteItem[];
  count: number;
}

interface ShipmentItem {
  id: number;
  reference: string;
  status: string;
  transport_mode: string;
  carrier: string | null;
  route_name: string | null;
  corridor: string | null;
  origin: string | null;
  destination: string | null;
  eta: string | null;
  value_amount: number;
  currency: string;
  is_derived: boolean;
}

export default function RoutesPage() {
  const [data, setData] = useState<RoutesResponse | null>(null);
  const [shipments, setShipments] = useState<ShipmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadRoutes() {
      try {
        setLoading(true);
        setError("");
        const [routesResp, shipmentsResp] = await Promise.all([
          apiRequest<RoutesResponse>("/routes"),
          apiRequest<ShipmentItem[]>("/shipments").catch(() => []),
        ]);
        setData(routesResp);
        setShipments(shipmentsResp);
      } catch (err) {
        console.error("Failed to load routes:", err);
        setError(
          err instanceof Error ? err.message : "Unable to load routes.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadRoutes();
  }, []);

  const summary = useMemo(() => {
    const routes = data?.routes ?? [];
    const by = (level: string) =>
      routes.filter((r) => r.risk_level?.toUpperCase() === level).length;

    return {
      total: routes.length,
      high: by("HIGH"),
      medium: by("MEDIUM"),
      active: routes.filter((r) => r.status?.toUpperCase() === "ACTIVE")
        .length,
    };
  }, [data]);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading supply routes…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard title="Routes unavailable" message={error} />
      </div>
    );
  }

  const routes = data?.routes ?? [];

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={RouteIcon}
        eyebrow="Supply Chain Intelligence"
        title="Supply Routes"
        description="Monitor active routes, transit times, freight costs and supply-chain risk."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile
          label="Total Routes"
          value={num(summary.total)}
          icon={RouteIcon}
          tone="live"
        />
        <StatTile
          label="Active Routes"
          value={num(summary.active)}
          icon={CheckCircle2}
          tone="stable"
        />
        <StatTile
          label="Medium Risk"
          value={num(summary.medium)}
          icon={Truck}
          tone="elevated"
        />
        <StatTile
          label="High Risk"
          value={num(summary.high)}
          icon={Truck}
          tone="critical"
        />
      </div>

      {shipments.length > 0 && (
        <section className="mt-6">
          <Panel
            label="In Transit"
            title="Shipments"
            tone="live"
            action={<Ship size={18} className="text-dim" />}
          >
            <div className="max-h-[45vh] overflow-auto">
              <table className="w-full text-left text-sm">
                <thead className="sticky top-0 z-10 bg-panel">
                  <tr className="border-b border-hairline">
                    {["Reference", "Lane", "Status", "ETA", "Value", ""].map(
                      (h) => (
                        <th
                          key={h}
                          className="eyebrow bg-panel px-3 py-2.5 font-semibold"
                        >
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {shipments.map((s) => (
                    <tr
                      key={s.id}
                      className="border-b border-hairline last:border-0"
                    >
                      <td className="num px-3 py-3 text-white">
                        {s.reference}
                      </td>
                      <td className="px-3 py-3 text-dim">
                        {s.origin ?? "—"}
                        <span className="mx-1.5 text-mute">→</span>
                        {s.destination ?? "—"}
                        {s.corridor && (
                          <span className="num ml-2 text-xs text-mute">
                            {s.corridor}
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-3">
                        <SeverityBadge value={s.status} />
                      </td>
                      <td className="num px-3 py-3 text-dim">
                        {s.eta
                          ? new Date(s.eta).toLocaleDateString()
                          : "—"}
                      </td>
                      <td className="num px-3 py-3 text-dim">
                        {inr(s.value_amount)}
                      </td>
                      <td className="px-3 py-3">
                        {s.is_derived && (
                          <span className="rounded-full bg-panel-raised px-2 py-0.5 text-[0.625rem] font-semibold text-mute">
                            projected
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        </section>
      )}

      <section className="mt-8">
        {routes.length === 0 ? (
          <>
            <h2 className="eyebrow mb-4">Route Network</h2>
            <EmptyCard message="No supply routes are associated with this organization." />
          </>
        ) : (
          <IntelCard
            label="Network"
            title="Route Network"
            tone={
              routes.some((r) => /high/i.test(r.risk_level))
                ? "critical"
                : routes.some((r) => /medium/i.test(r.risk_level))
                  ? "elevated"
                  : "live"
            }
            maxHeight="66vh"
            action={
              <span className="num text-xs text-mute">
                {routes.length} lanes
              </span>
            }
          >
            <div className="grid gap-3 lg:grid-cols-2">
              {routes.map((route) => (
                <div
                  key={route.id}
                  className="relative overflow-hidden rounded-lg border border-hairline bg-panel-raised/40 p-4"
                >
                  <span
                    aria-hidden
                    className={`absolute inset-y-0 left-0 w-[3px] ${TONE_RAIL[toneForStatus(route.risk_level)]}`}
                  />
                  <div className="flex items-start justify-between gap-3 pl-2">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-white">
                        {route.route_name}
                      </h3>
                      <p className="mt-0.5 text-xs text-dim">
                        {route.origin_port}, {route.origin_country}
                        <span className="mx-1.5 text-mute">→</span>
                        {route.destination_port}, {route.destination_country}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-1.5">
                      <span className="rounded-full bg-panel-raised px-2 py-0.5 text-[0.65rem] font-semibold text-dim">
                        {route.transport_mode}
                      </span>
                      <SeverityBadge value={route.risk_level} />
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-2 gap-2 pl-2 text-xs sm:grid-cols-4">
                    {[
                      { icon: MapPinned, label: "Distance", value: `${num(route.distance_km)} km` },
                      { icon: Clock3, label: "Transit", value: `${num(route.transit_days)} d` },
                      { icon: DollarSign, label: "Freight", value: inr(route.freight_cost) },
                      { icon: CheckCircle2, label: "Status", value: route.status },
                    ].map((cell) => {
                      const Icon = cell.icon;
                      return (
                        <div key={cell.label}>
                          <div className="flex items-center gap-1 text-mute">
                            <Icon size={11} />
                            <span className="eyebrow">{cell.label}</span>
                          </div>
                          <p className="num mt-0.5 font-semibold text-white">
                            {cell.value}
                          </p>
                        </div>
                      );
                    })}
                  </div>

                  <p className="num mt-3 pl-2 text-[0.7rem] text-mute">
                    {route.supplier?.name ?? "Unknown supplier"}
                    {" · "}
                    {route.product?.name ?? "All products"}
                    {route.corridor ? ` · ${route.corridor}` : ""}
                  </p>
                </div>
              ))}
            </div>
          </IntelCard>
        )}
      </section>
    </div>
  );
}
