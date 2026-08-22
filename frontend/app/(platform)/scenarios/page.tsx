"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DollarSign,
  Route as RouteIcon,
  ShieldAlert,
  Sparkles,
  Truck,
  XCircle,
  Loader2,
} from "lucide-react";

import { apiRequest } from "@/lib/api";


interface RouteOption {
  route_id?: number;
  route_name?: string;
  corridor?: string;
  transit_days?: number;
  freight_cost?: number;
  risk_level?: string;
  cost_difference?: number;
  delay_difference?: number;
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
    exposures?: any[];
    suppliers?: any[];
    products?: any[];

    financial?: {
      total_cost_impact?: number;
      total_revenue_at_risk?: number;
    };
  };

  route_alternatives?: RouteOption[];

  ai_recommendation?: string;
}


export default function ScenariosPage() {

  const [
    data,
    setData,
  ] = useState<ScenarioData | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    approving,
    setApproving,
  ] = useState(false);


  const [
    approved,
    setApproved,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  // -------------------------------------------------
  // Load scenario
  // -------------------------------------------------

  async function loadScenario() {

    try {

      setLoading(true);
      setError("");

      console.log(
        "[HEX] Loading Red Sea scenario..."
      );

      const result =
        await apiRequest<ScenarioData>(
          "/demo/red-sea"
        );

      console.log(
        "[HEX] Scenario response:",
        result
      );

      setData(result);

    } catch (err) {

      console.error(
        "[HEX] Scenario error:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load scenario."
      );

    } finally {

      setLoading(false);

    }
  }


  // -------------------------------------------------
  // Load scenario once
  // -------------------------------------------------

  useEffect(() => {

    loadScenario();

  }, []);


  // -------------------------------------------------
  // Approve recommendation
  // -------------------------------------------------

  async function approveRecommendation() {

    if (!data?.ai_recommendation) {
      return;
    }


    try {

      setApproving(true);
      setError("");


      await apiRequest(
        "/approvals",
        {
          method: "POST",

          body: JSON.stringify({
            recommendation:
              data.ai_recommendation,

            scenario:
              "Red Sea shipping disruption",

            event_id:
              data.event?.id ??
              null,

            comment:
              "Approved from HEX scenario dashboard.",
          }),
        }
      );


      setApproved(true);

    } catch (err) {

      console.error(
        "[HEX] Approval failed:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to approve recommendation."
      );

    } finally {

      setApproving(false);

    }
  }


  // -------------------------------------------------
  // Loading
  // -------------------------------------------------

  if (loading) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

          <div className="flex justify-center">

            <div className="rounded-full bg-slate-100 p-4">

              <Loader2
                size={28}
                className="animate-spin text-slate-600"
              />

            </div>

          </div>


          <p className="mt-4 text-slate-500">

            Running HEX scenario analysis...

          </p>

        </div>

      </div>
    );
  }


  // -------------------------------------------------
  // Error
  // -------------------------------------------------

  if (error && !data) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">

          <p className="font-semibold">
            Scenario analysis failed
          </p>

          <p className="mt-2 text-sm">
            {error}
          </p>

          <button
            type="button"
            onClick={loadScenario}
            className="mt-5 rounded-xl bg-red-700 px-4 py-2 text-sm font-semibold text-white hover:bg-red-800"
          >
            Try Again
          </button>

        </div>

      </div>
    );
  }


  if (!data) {
    return null;
  }


  const event =
    data.event;


  const financial =
    data.exposure?.financial;


  const routeOptions =
    data.route_alternatives || [];


  return (
    <div className="p-6 lg:p-8">


      {/* ERROR */}

      {error && (

        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">

          <div className="flex items-center justify-between gap-4">

            <p>
              {error}
            </p>

            <button
              type="button"
              onClick={() =>
                setError("")
              }
              className="text-sm font-semibold underline"
            >
              Dismiss
            </button>

          </div>

        </div>

      )}


      {/* HERO */}

      <div className="rounded-3xl bg-slate-900 p-8 text-white">

        <div className="flex flex-wrap items-start justify-between gap-6">

          <div>

            <p className="text-sm font-medium text-slate-400">
              Scenario Simulation
            </p>

            <h1 className="mt-2 text-4xl font-bold">
              Red Sea Disruption
            </h1>

            <p className="mt-3 max-w-2xl text-slate-300">

              HEX evaluates the disruption,
              business exposure, route alternatives,
              financial impact and AI recommendation.

            </p>

          </div>


          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-5 py-4">

            <div className="flex items-center gap-2">

              <AlertTriangle
                size={18}
                className="text-red-300"
              />

              <span className="text-sm font-semibold text-red-300">

                {event?.severity || "HIGH"} RISK

              </span>

            </div>


            <p className="mt-2 text-sm text-slate-300">

              {event?.region || "Red Sea"}

            </p>

          </div>

        </div>

      </div>


      {/* EVENT */}

      <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 p-5">

        <div className="flex items-center gap-3">

          <ShieldAlert
            size={20}
            className="text-red-600"
          />

          <div>

            <p className="text-sm text-red-600">
              Detected Event
            </p>

            <h2 className="mt-1 font-semibold text-slate-900">

              {event?.title ||
                "Simulated Red Sea shipping disruption"}

            </h2>

            <p className="mt-1 text-sm text-slate-500">

              {event?.type || "LOGISTICS"}

              {" · "}

              {event?.region || "Red Sea"}

            </p>

          </div>

        </div>

      </div>


      {/* BUSINESS IMPACT */}

      <div className="mt-8 grid gap-5 md:grid-cols-3">


        {/* REVENUE */}

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-red-50 p-3">

            <DollarSign
              size={21}
              className="text-red-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            Revenue at Risk
          </p>

          <p className="mt-1 text-3xl font-bold">

            ₹
            {Number(
              financial?.total_revenue_at_risk
              || 0
            ).toLocaleString(
              "en-IN"
            )}

          </p>

        </div>


        {/* ROUTES */}

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-orange-50 p-3">

            <Truck
              size={21}
              className="text-orange-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            Affected Routes
          </p>

          <p className="mt-1 text-3xl font-bold">

            {
              data.exposure
                ?.exposures
                ?.length
              || 0
            }

          </p>

        </div>


        {/* STATUS */}

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="w-fit rounded-xl bg-purple-50 p-3">

            <ShieldAlert
              size={21}
              className="text-purple-600"
            />

          </div>

          <p className="mt-5 text-sm text-slate-500">
            Scenario Status
          </p>

          <p className="mt-1 text-2xl font-bold">

            {approved
              ? "APPROVED"
              : "AWAITING REVIEW"}

          </p>

        </div>

      </div>


      {/* ROUTE DECISION */}

      <section className="mt-10">

        <div className="mb-5">

          <h2 className="text-2xl font-bold">
            Route Decision
          </h2>

          <p className="mt-1 text-slate-500">

            Compare the current route with
            available alternatives.

          </p>

        </div>


        <div className="grid gap-6 lg:grid-cols-2">


          {/* CURRENT ROUTE */}

          <div className="rounded-2xl border border-red-200 bg-white p-6 shadow-sm">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-sm font-semibold text-red-600">
                  CURRENT ROUTE
                </p>

                <h3 className="mt-1 text-xl font-bold">
                  Red Sea Corridor
                </h3>

              </div>


              <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                HIGH RISK
              </span>

            </div>


            <div className="mt-6 grid grid-cols-2 gap-4">


              <div className="rounded-xl bg-slate-50 p-4">

                <div className="flex items-center gap-2">

                  <Clock3
                    size={16}
                  />

                  <span className="text-sm text-slate-500">
                    Delay
                  </span>

                </div>

                <p className="mt-2 text-xl font-bold">
                  +14 days
                </p>

              </div>


              <div className="rounded-xl bg-slate-50 p-4">

                <div className="flex items-center gap-2">

                  <DollarSign
                    size={16}
                  />

                  <span className="text-sm text-slate-500">
                    Impact
                  </span>

                </div>

                <p className="mt-2 text-xl font-bold">

                  ₹
                  {Number(
                    financial?.total_cost_impact
                    || 0
                  ).toLocaleString(
                    "en-IN"
                  )}

                </p>

              </div>

            </div>

          </div>


          {/* ALTERNATIVES */}

          <div className="rounded-2xl border bg-white p-6 shadow-sm">

            <div className="flex items-center gap-3">

              <RouteIcon size={21} />

              <div>

                <p className="text-sm text-slate-500">
                  HEX ROUTE ENGINE
                </p>

                <h3 className="text-xl font-bold">
                  Alternatives
                </h3>

              </div>

            </div>


            <div className="mt-5 space-y-3">

              {routeOptions.length === 0 ? (

                <div className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">

                  No alternative route data was
                  returned by the backend.

                </div>

              ) : (

                routeOptions.map(
                  (
                    route,
                    index
                  ) => {

                    const isLowRisk =
                      route.risk_level
                      === "LOW";


                    return (

                      <div
                        key={
                          route.route_id
                          ?? index
                        }
                        className={`rounded-xl border p-4 ${
                          isLowRisk
                            ? "border-emerald-200 bg-emerald-50"
                            : "bg-slate-50"
                        }`}
                      >

                        <div className="flex items-center gap-3">

                          <RouteIcon
                            size={18}
                          />

                          <div className="flex-1">

                            <p className="font-semibold">

                              {route.route_name
                                ||
                                `Alternative Route #${
                                  index + 1
                                }`}

                            </p>

                            <p className="mt-1 text-xs text-slate-500">

                              {route.corridor
                                ||
                                "Alternative corridor"}

                            </p>

                          </div>


                          <span
                            className={`rounded-full px-3 py-1 text-xs font-semibold ${
                              isLowRisk
                                ? "bg-emerald-100 text-emerald-700"
                                : "bg-amber-100 text-amber-700"
                            }`}
                          >

                            {route.risk_level
                              || "UNKNOWN"}

                          </span>

                        </div>


                        <div className="mt-4 grid grid-cols-2 gap-3">

                          <div>

                            <p className="text-xs text-slate-500">
                              Transit
                            </p>

                            <p className="font-semibold">

                              {route.transit_days
                                ?? "—"}

                              {" "}days

                            </p>

                          </div>


                          <div>

                            <p className="text-xs text-slate-500">
                              Freight
                            </p>

                            <p className="font-semibold">

                              ₹
                              {route.freight_cost
                                != null
                                ? Number(
                                    route.freight_cost
                                  ).toLocaleString(
                                    "en-IN"
                                  )
                                : "—"}

                            </p>

                          </div>

                        </div>

                      </div>

                    );

                  }
                )

              )}

            </div>

          </div>

        </div>

      </section>


      {/* AI RECOMMENDATION */}

      <section className="mt-10">

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-violet-100 p-3">

              <Sparkles
                size={21}
                className="text-violet-600"
              />

            </div>

            <div>

              <p className="text-sm text-slate-500">
                DECISION INTELLIGENCE
              </p>

              <h2 className="text-2xl font-bold">
                HEX Recommendation
              </h2>

            </div>

          </div>


          <div className="mt-6 rounded-2xl bg-slate-50 p-6">

            <p className="whitespace-pre-wrap leading-7 text-slate-700">

              {data.ai_recommendation
                ||
                "HEX has not generated a recommendation yet."}

            </p>

          </div>

        </div>

      </section>


      {/* APPROVAL */}

      <section className="mt-8">

        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6">

          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

            <div>

              <div className="flex items-center gap-2">

                <ShieldAlert
                  size={20}
                  className="text-amber-600"
                />

                <h2 className="font-bold">
                  Human approval required
                </h2>

              </div>


              <p className="mt-2 max-w-2xl text-sm text-slate-600">

                HEX provides decision support.
                High-impact operational decisions
                require authorized human review.

              </p>

            </div>


            {!approved ? (

              <div className="flex gap-3">

                <button
                  type="button"
                  disabled={
                    approving
                    ||
                    !data.ai_recommendation
                  }
                  onClick={
                    approveRecommendation
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                >

                  {approving ? (
                    <>
                      <Loader2
                        size={18}
                        className="animate-spin"
                      />

                      Approving...

                    </>
                  ) : (
                    <>
                      <CheckCircle2
                        size={18}
                      />

                      Approve Recommendation

                    </>
                  )}

                </button>


                <button
                  type="button"
                  className="inline-flex items-center gap-2 rounded-xl border bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >

                  <XCircle
                    size={18}
                  />

                  Reject

                </button>

              </div>

            ) : (

              <div className="flex items-center gap-2 rounded-xl bg-emerald-100 px-5 py-3 text-sm font-semibold text-emerald-700">

                <CheckCircle2
                  size={18}
                />

                Recommendation Approved

              </div>

            )}

          </div>

        </div>

      </section>


      {/* FOOTER */}

      <div className="mt-8 flex items-center gap-2 text-xs text-slate-400">

        <ArrowRight
          size={14}
        />

        <span>

          Approval is recorded through the
          HEX decision workflow.

        </span>

      </div>

    </div>
  );
}