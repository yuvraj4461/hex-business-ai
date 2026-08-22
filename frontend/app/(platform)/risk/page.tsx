"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AlertOctagon,
  DollarSign,
  Package,
  ShieldAlert,
  Truck,
  Users,
  Loader2,
  X,
  ArrowRight,
} from "lucide-react";

import { apiRequest } from "@/lib/api";


interface Event {
  id: number;
  title: string;
  severity: string;
  event_type: string;
  region?: string;
}


interface Exposure {
  event?: {
    id?: number;
    type?: string;
    title?: string;
    severity?: string;
    region?: string;
  };

  exposures?: any[];

  suppliers?: any[];

  products?: any[];

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


  const [events, setEvents] =
    useState<Event[]>([]);

  const [selectedEvent, setSelectedEvent] =
    useState<Exposure | null>(null);

  const [loading, setLoading] =
    useState(true);

  const [loadingExposureId, setLoadingExposureId] =
    useState<number | null>(null);

  const [error, setError] =
    useState("");

  const [exposureError, setExposureError] =
    useState("");


  // -------------------------------------------------
  // Load global events
  // -------------------------------------------------

  useEffect(() => {

    async function loadEvents() {

      try {

        setLoading(true);
        setError("");

        const data =
          await apiRequest<Event[]>(
            "/global-events/?limit=10"
          );

        setEvents(data);

      } catch (err) {

        console.error(
          "Failed to load global events:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load risk center."
        );

      } finally {

        setLoading(false);

      }
    }

    loadEvents();

  }, []);


  // -------------------------------------------------
  // Load exposure for selected event
  // -------------------------------------------------

  async function handleEventClick(
    eventId: number
  ) {

    try {

      setLoadingExposureId(
        eventId
      );

      setExposureError("");

      const data =
        await apiRequest<Exposure>(
          `/global-exposure/${eventId}`
        );

      console.log(
        "Global exposure response:",
        data
      );

      setSelectedEvent(
        data
      );

    } catch (err) {

      console.error(
        "Failed to load event exposure:",
        err
      );

      setExposureError(
        err instanceof Error
          ? err.message
          : "Unable to load exposure data."
      );

      setSelectedEvent(
        null
      );

    } finally {

      setLoadingExposureId(
        null
      );

    }
  }


  // -------------------------------------------------
  // Open full scenario
  // -------------------------------------------------

  function openFullScenario() {

    const eventId =
      selectedEvent?.event?.id;

    if (!eventId) {
      return;
    }

    router.push(
      `/scenarios?event=${eventId}`
    );
  }


  // -------------------------------------------------
  // Loading page
  // -------------------------------------------------

  if (loading) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

          <Loader2
            className="mx-auto animate-spin text-slate-500"
            size={28}
          />

          <p className="mt-4 text-slate-500">
            Loading risk center...
          </p>

        </div>

      </div>
    );
  }


  // -------------------------------------------------
  // Main page
  // -------------------------------------------------

  return (
    <div className="p-6 lg:p-8">

      {/* PAGE HEADER */}

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-red-600 p-3 text-white">

            <ShieldAlert
              size={22}
            />

          </div>

          <div>

            <p className="text-sm text-slate-500">
              Decision Intelligence
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              Risk Center
            </h1>

          </div>

        </div>

        <p className="mt-3 text-slate-500">
          Understand how external events translate
          into operational and financial exposure.
        </p>

      </div>


      {/* GENERAL ERROR */}

      {error && (

        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
          {error}
        </div>

      )}


      {/* EXPOSURE ERROR */}

      {exposureError && (

        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5">

          <div className="flex items-start justify-between gap-4">

            <div>

              <p className="font-semibold text-red-800">
                Unable to load exposure analysis
              </p>

              <p className="mt-1 text-sm text-red-700">
                {exposureError}
              </p>

            </div>

            <button
              type="button"
              onClick={() =>
                setExposureError("")
              }
              className="rounded-lg p-1 text-red-600 hover:bg-red-100"
            >
              <X size={18} />
            </button>

          </div>

        </div>

      )}


      {/* EVENTS */}

      <section>

        <div className="mb-4">

          <h2 className="text-xl font-semibold text-slate-900">
            Global Events
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Select an event to analyze its impact
            on your business.
          </p>

        </div>


        {events.length === 0 ? (

          <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

            <p className="text-slate-500">
              No global events available.
            </p>

          </div>

        ) : (

          <div className="grid gap-4 lg:grid-cols-2">

            {events.map(
              (event) => {

                const isLoading =
                  loadingExposureId
                  === event.id;

                const isSelected =
                  selectedEvent?.event?.id
                  === event.id;


                return (

                  <div
                    key={event.id}
                    className={`rounded-2xl border bg-white p-5 shadow-sm transition ${
                      isSelected
                        ? "border-red-400 ring-2 ring-red-100"
                        : "border-slate-200"
                    }`}
                  >

                    <div className="flex items-center gap-4">

                      <div className="rounded-xl bg-red-50 p-3">

                        <AlertOctagon
                          size={21}
                          className="text-red-600"
                        />

                      </div>


                      <div className="min-w-0 flex-1">

                        <p className="font-semibold text-slate-900">
                          {event.title}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">

                          {event.event_type}

                          {event.region
                            ? ` · ${event.region}`
                            : ""}

                        </p>

                      </div>


                      <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">
                        {event.severity}
                      </span>

                    </div>


                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() =>
                        handleEventClick(
                          event.id
                        )
                      }
                      className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                    >

                      {isLoading ? (
                        <>
                          <Loader2
                            size={17}
                            className="animate-spin"
                          />

                          Analyzing exposure...
                        </>
                      ) : isSelected ? (
                        <>
                          <ShieldAlert
                            size={17}
                          />

                          Exposure Loaded
                        </>
                      ) : (
                        <>
                          <ShieldAlert
                            size={17}
                          />

                          Analyze Business Impact
                        </>
                      )}

                    </button>

                  </div>

                );

              }
            )}

          </div>

        )}

      </section>


      {/* SELECTED EVENT DETAILS */}

      {selectedEvent && (

        <section className="mt-10">

          {/* SELECTED EVENT */}

          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-6">

            <p className="text-sm font-medium text-red-600">
              Selected Event
            </p>

            <h2 className="mt-1 text-2xl font-bold text-slate-900">
              {selectedEvent.event?.title ||
                "Global Event"}
            </h2>

            <p className="mt-2 text-sm text-slate-500">

              {selectedEvent.event?.type ||
                "UNKNOWN"}

              {" · "}

              {selectedEvent.event?.severity ||
                "UNKNOWN"}

              {selectedEvent.event?.region
                ? ` · ${selectedEvent.event.region}`
                : ""}

            </p>

          </div>


          {/* KPI CARDS */}

          <div className="grid gap-5 md:grid-cols-3">


            {/* REVENUE AT RISK */}

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

              <p className="mt-1 text-3xl font-bold text-slate-900">

                ₹
                {Number(
                  selectedEvent.financial
                    ?.total_revenue_at_risk
                  || 0
                ).toLocaleString(
                  "en-IN"
                )}

              </p>

            </div>


            {/* AFFECTED ROUTES */}

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

              <p className="mt-1 text-3xl font-bold text-slate-900">
                {
                  selectedEvent.exposures
                    ?.length
                  || 0
                }
              </p>

            </div>


            {/* BUSINESS RISK */}

            <div className="rounded-2xl border bg-white p-6 shadow-sm">

              <div className="w-fit rounded-xl bg-red-50 p-3">

                <ShieldAlert
                  size={21}
                  className="text-red-600"
                />

              </div>

              <p className="mt-5 text-sm text-slate-500">
                Business Risk
              </p>

              <p className="mt-1 text-3xl font-bold text-slate-900">
                {
                  selectedEvent.business_risk
                    ?.level
                  || "LOW"
                }
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Score:{" "}
                {
                  selectedEvent.business_risk
                    ?.score
                  ?? 0
                }
                /100
              </p>

            </div>

          </div>


          {/* SUPPLIERS + PRODUCTS */}

          <div className="mt-8 grid gap-6 lg:grid-cols-2">


            {/* SUPPLIERS */}

            <div className="rounded-2xl border bg-white p-6 shadow-sm">

              <div className="flex items-center gap-3">

                <div className="rounded-xl bg-blue-50 p-3">

                  <Users
                    size={20}
                    className="text-blue-600"
                  />

                </div>

                <div>

                  <h2 className="font-semibold text-slate-900">
                    Affected Suppliers
                  </h2>

                  <p className="text-sm text-slate-500">
                    Suppliers exposed to this event
                  </p>

                </div>

              </div>


              <div className="mt-5 space-y-3">

                {(selectedEvent.suppliers || [])
                  .length === 0 ? (

                  <div className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">
                    No affected suppliers found.
                  </div>

                ) : (

                  selectedEvent.suppliers?.map(
                    (supplier: any) => (

                      <div
                        key={
                          supplier.supplier_id
                        }
                        className="rounded-xl bg-slate-50 p-4"
                      >

                        <p className="font-medium text-slate-900">
                          Supplier #
                          {supplier.supplier_id}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">

                          {supplier.route_count}
                          {" "}routes
                          {" · "}
                          {supplier.product_count}
                          {" "}products

                        </p>

                      </div>

                    )
                  )

                )}

              </div>

            </div>


            {/* PRODUCTS */}

            <div className="rounded-2xl border bg-white p-6 shadow-sm">

              <div className="flex items-center gap-3">

                <div className="rounded-xl bg-purple-50 p-3">

                  <Package
                    size={20}
                    className="text-purple-600"
                  />

                </div>

                <div>

                  <h2 className="font-semibold text-slate-900">
                    Affected Products
                  </h2>

                  <p className="text-sm text-slate-500">
                    Products exposed to the disruption
                  </p>

                </div>

              </div>


              <div className="mt-5 space-y-3">

                {(selectedEvent.products || [])
                  .length === 0 ? (

                  <div className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">
                    No affected products found.
                  </div>

                ) : (

                  selectedEvent.products?.map(
                    (product: any) => (

                      <div
                        key={
                          product.product_id
                        }
                        className="rounded-xl bg-slate-50 p-4"
                      >

                        <p className="font-medium text-slate-900">
                          Product #
                          {product.product_id}
                        </p>

                        <p className="mt-1 text-sm text-slate-500">
                          Delay:{" "}
                          {product.delay_days}
                          {" "}days
                        </p>

                      </div>

                    )
                  )

                )}

              </div>

            </div>

          </div>


          {/* EXPOSURE TABLE */}

          <div className="mt-8 rounded-2xl border bg-white p-6 shadow-sm">

            <h2 className="font-semibold text-slate-900">
              Exposure Details
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Route-level impact detected by HEX.
            </p>


            <div className="mt-5 overflow-x-auto">

              {(selectedEvent.exposures || [])
                .length === 0 ? (

                <div className="rounded-xl bg-slate-50 p-5 text-sm text-slate-500">
                  No individual route exposures returned
                  by the backend.
                </div>

              ) : (

                <table className="w-full text-left text-sm">

                  <thead>

                    <tr className="border-b text-slate-500">

                      <th className="px-3 py-3">
                        Route
                      </th>

                      <th className="px-3 py-3">
                        Supplier
                      </th>

                      <th className="px-3 py-3">
                        Product
                      </th>

                      <th className="px-3 py-3">
                        Delay
                      </th>

                      <th className="px-3 py-3">
                        Cost Impact
                      </th>

                      <th className="px-3 py-3">
                        Revenue Risk
                      </th>

                      <th className="px-3 py-3">
                        Severity
                      </th>

                    </tr>

                  </thead>


                  <tbody>

                    {selectedEvent.exposures?.map(
                      (
                        exposure: any,
                        index: number
                      ) => (

                        <tr
                          key={
                            exposure.route_id
                            ?? index
                          }
                          className="border-b last:border-0"
                        >

                          <td className="px-3 py-4">

                            {exposure.route_name ||
                              `Route #${exposure.route_id}`}

                          </td>

                          <td className="px-3 py-4">
                            #{exposure.supplier_id}
                          </td>

                          <td className="px-3 py-4">
                            #{exposure.product_id}
                          </td>

                          <td className="px-3 py-4">
                            {exposure.delay_days}
                            {" "}days
                          </td>

                          <td className="px-3 py-4">

                            ₹
                            {Number(
                              exposure.cost_impact
                              || 0
                            ).toLocaleString(
                              "en-IN"
                            )}

                          </td>

                          <td className="px-3 py-4">

                            ₹
                            {Number(
                              exposure.revenue_at_risk
                              || 0
                            ).toLocaleString(
                              "en-IN"
                            )}

                          </td>

                          <td className="px-3 py-4">

                            <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-semibold text-red-700">

                              {exposure.severity ||
                                "UNKNOWN"}

                            </span>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              )}

            </div>

          </div>


          {/* FULL SCENARIO BUTTON */}

          <div className="mt-8 flex justify-end">

            <button
              type="button"
              disabled={
                !selectedEvent.event?.id
              }
              onClick={
                openFullScenario
              }
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
            >

              View Full Scenario

              <ArrowRight
                size={18}
              />

            </button>

          </div>

        </section>

      )}

    </div>
  );
}