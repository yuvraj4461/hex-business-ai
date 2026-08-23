"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  DollarSign,
  MapPinned,
  Route as RouteIcon,
  Truck,
  Loader2,
} from "lucide-react";

import { apiRequest } from "@/lib/api";


interface RouteSupplier {
  id: number;
  name: string;
}


interface RouteProduct {
  id: number;
  name: string;
}


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

  supplier?: RouteSupplier | null;
  product?: RouteProduct | null;
}


interface RoutesResponse {
  organization_id: number;
  routes: RouteItem[];
  count: number;
}


function getRiskStyles(risk: string) {
  const value = risk?.toUpperCase();

  if (value === "HIGH") {
    return {
      badge: "bg-red-50 text-red-700",
      border: "border-red-200",
      icon: "text-red-600",
    };
  }

  if (value === "MEDIUM") {
    return {
      badge: "bg-amber-50 text-amber-700",
      border: "border-amber-200",
      icon: "text-amber-600",
    };
  }

  return {
    badge: "bg-emerald-50 text-emerald-700",
    border: "border-emerald-200",
    icon: "text-emerald-600",
  };
}


export default function RoutesPage() {
  const [data, setData] =
    useState<RoutesResponse | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    async function loadRoutes() {
      try {
        setLoading(true);
        setError("");

        const result =
          await apiRequest<RoutesResponse>(
            "/routes"
          );

        setData(result);

      } catch (err) {
        console.error(
          "Failed to load routes:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load routes."
        );

      } finally {
        setLoading(false);
      }
    }

    loadRoutes();
  }, []);


  const summary = useMemo(() => {
    const routes = data?.routes || [];

    return {
      total: routes.length,

      highRisk: routes.filter(
        (route) =>
          route.risk_level?.toUpperCase()
          === "HIGH"
      ).length,

      mediumRisk: routes.filter(
        (route) =>
          route.risk_level?.toUpperCase()
          === "MEDIUM"
      ).length,

      active: routes.filter(
        (route) =>
          route.status?.toUpperCase()
          === "ACTIVE"
      ).length,
    };
  }, [data]);


  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <div className="rounded-2xl border bg-white p-10 text-center shadow-sm">

          <Loader2
            size={30}
            className="mx-auto animate-spin text-slate-500"
          />

          <p className="mt-4 text-slate-500">
            Loading supply routes...
          </p>

        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div className="p-6 lg:p-8">

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6">

          <p className="font-semibold text-red-800">
            Routes unavailable
          </p>

          <p className="mt-2 text-sm text-red-700">
            {error}
          </p>

        </div>

      </div>
    );
  }


  const routes = data?.routes || [];


  return (
    <div className="p-6 lg:p-8">

      {/* HEADER */}

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-slate-900 p-3 text-white">

            <RouteIcon size={22} />

          </div>

          <div>

            <p className="text-sm text-slate-500">
              Supply Chain Intelligence
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              Supply Routes
            </h1>

          </div>

        </div>

        <p className="mt-3 text-slate-500">
          Monitor active routes, transit times,
          freight costs and supply-chain risk.
        </p>

      </div>


      {/* SUMMARY */}

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-slate-100 p-3">
            <RouteIcon size={20} />
          </div>

          <p className="mt-5 text-sm text-slate-500">
            Total Routes
          </p>

          <p className="mt-1 text-3xl font-bold text-slate-900">
            {summary.total}
          </p>

        </div>


        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-emerald-50 p-3">

            <CheckCircle2
              size={20}
              className="text-emerald-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            Active Routes
          </p>

          <p className="mt-1 text-3xl font-bold text-slate-900">
            {summary.active}
          </p>

        </div>


        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-amber-50 p-3">

            <AlertTriangle
              size={20}
              className="text-amber-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            Medium Risk
          </p>

          <p className="mt-1 text-3xl font-bold text-slate-900">
            {summary.mediumRisk}
          </p>

        </div>


        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-red-50 p-3">

            <AlertTriangle
              size={20}
              className="text-red-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            High Risk
          </p>

          <p className="mt-1 text-3xl font-bold text-slate-900">
            {summary.highRisk}
          </p>

        </div>

      </div>


      {/* ROUTES */}

      <section className="mt-10">

        <div className="mb-5">

          <h2 className="text-2xl font-bold text-slate-900">
            Route Network
          </h2>

          <p className="mt-1 text-slate-500">
            Current supply routes connected to
            your organization.
          </p>

        </div>


        {routes.length === 0 ? (

          <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

            <RouteIcon
              size={32}
              className="mx-auto text-slate-300"
            />

            <p className="mt-4 font-semibold text-slate-700">
              No routes found
            </p>

            <p className="mt-1 text-sm text-slate-500">
              No supply routes are currently
              associated with this organization.
            </p>

          </div>

        ) : (

          <div className="space-y-5">

            {routes.map((route) => {

              const risk =
                getRiskStyles(
                  route.risk_level
                );


              return (
                <div
                  key={route.id}
                  className={`rounded-2xl border bg-white p-6 shadow-sm ${risk.border}`}
                >

                  {/* ROUTE HEADER */}

                  <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">

                    <div className="flex min-w-0 items-start gap-4">

                      <div className="rounded-xl bg-slate-100 p-3">

                        <Truck
                          size={21}
                          className={risk.icon}
                        />

                      </div>


                      <div className="min-w-0">

                        <h3 className="text-lg font-bold text-slate-900">
                          {route.route_name}
                        </h3>

                        <p className="mt-1 text-sm text-slate-500">
                          {route.corridor}
                        </p>

                        <p className="mt-2 text-sm text-slate-600">

                          {route.origin_port},{" "}
                          {route.origin_country}

                          <span className="mx-2 text-slate-400">
                            →
                          </span>

                          {route.destination_port},{" "}
                          {route.destination_country}

                        </p>

                      </div>

                    </div>


                    <div className="flex items-center gap-2">

                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                        {route.transport_mode}
                      </span>

                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${risk.badge}`}
                      >
                        {route.risk_level}
                      </span>

                    </div>

                  </div>


                  {/* METRICS */}

                  <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">

                    <div className="rounded-xl bg-slate-50 p-4">

                      <div className="flex items-center gap-2">

                        <MapPinned size={17} />

                        <span className="text-xs text-slate-500">
                          Distance
                        </span>

                      </div>

                      <p className="mt-2 font-semibold text-slate-900">

                        {Number(
                          route.distance_km
                        ).toLocaleString(
                          "en-IN"
                        )}{" "}
                        km

                      </p>

                    </div>


                    <div className="rounded-xl bg-slate-50 p-4">

                      <div className="flex items-center gap-2">

                        <Clock3 size={17} />

                        <span className="text-xs text-slate-500">
                          Transit
                        </span>

                      </div>

                      <p className="mt-2 font-semibold text-slate-900">
                        {route.transit_days} days
                      </p>

                    </div>


                    <div className="rounded-xl bg-slate-50 p-4">

                      <div className="flex items-center gap-2">

                        <DollarSign size={17} />

                        <span className="text-xs text-slate-500">
                          Freight
                        </span>

                      </div>

                      <p className="mt-2 font-semibold text-slate-900">

                        ₹
                        {Number(
                          route.freight_cost
                        ).toLocaleString(
                          "en-IN"
                        )}

                      </p>

                    </div>


                    <div className="rounded-xl bg-slate-50 p-4">

                      <div className="flex items-center gap-2">

                        <CheckCircle2 size={17} />

                        <span className="text-xs text-slate-500">
                          Status
                        </span>

                      </div>

                      <p className="mt-2 font-semibold text-slate-900">
                        {route.status}
                      </p>

                    </div>

                  </div>


                  {/* SUPPLIER / PRODUCT */}

                  <div className="mt-5 grid gap-4 md:grid-cols-2">

                    <div className="rounded-xl border p-4">

                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Supplier
                      </p>

                      <p className="mt-2 font-semibold text-slate-900">

                        {route.supplier?.name ||
                          "Unknown supplier"}

                      </p>

                    </div>


                    <div className="rounded-xl border p-4">

                      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Product
                      </p>

                      <p className="mt-2 font-semibold text-slate-900">

                        {route.product?.name ||
                          "All products"}

                      </p>

                    </div>

                  </div>

                </div>
              );
            })}

          </div>

        )}

      </section>

    </div>
  );
}