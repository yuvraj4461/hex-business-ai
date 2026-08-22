"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  CloudRain,
  DollarSign,
  Globe2,
  Wheat,
} from "lucide-react";

import {
  apiRequest,
} from "@/lib/api";


interface GlobalEvent {
  id: number;
  title: string;
  event_type: string;
  severity: string;
  region?: string;
}


interface MarketOverview {
  commodities?: Record<
    string,
    any
  >;

  fx?: Record<
    string,
    any
  >;
}


interface AgricultureOverview {
  risks?: any[];
  commodity_impact?: any[];
}


export default function GlobalPage() {

  const [
    events,
    setEvents,
  ] = useState<GlobalEvent[]>([]);


  const [
    market,
    setMarket,
  ] = useState<MarketOverview | null>(
    null,
  );


  const [
    agriculture,
    setAgriculture,
  ] = useState<AgricultureOverview | null>(
    null,
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  const [
    marketError,
    setMarketError,
  ] = useState("");


  const [
    agricultureError,
    setAgricultureError,
  ] = useState("");


  useEffect(() => {

    async function loadGlobalData() {

      setLoading(true);
      setError("");


      try {

        const eventData =
          await apiRequest<GlobalEvent[]>(
            "/global-events/?limit=10",
          );

        setEvents(
          eventData,
        );

      } catch (err) {

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load global events.",
        );

      }


      try {

        const marketData =
          await apiRequest<MarketOverview>(
            "/market/overview",
          );

        setMarket(
          marketData,
        );

      } catch (err) {

        console.error(
          "Market intelligence error:",
          err,
        );

        setMarketError(
          err instanceof Error
            ? err.message
            : "Market data unavailable.",
        );

      }


      try {

        const agricultureData =
          await apiRequest<AgricultureOverview>(
            "/agriculture/overview",
          );

        setAgriculture(
          agricultureData,
        );

      } catch (err) {

        console.error(
          "Agriculture intelligence error:",
          err,
        );

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
      <div className="p-8">
        Loading global intelligence...
      </div>
    );
  }


  return (
    <div className="p-6 lg:p-8">

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-slate-900 p-3 text-white">

            <Globe2 size={22} />

          </div>

          <div>

            <p className="text-sm text-slate-500">
              External Intelligence
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              Global Intelligence
            </h1>

          </div>

        </div>


        <p className="mt-3 text-slate-500">

          Monitor global events, commodities,
          agriculture and currency signals that
          may affect your business.

        </p>

      </div>


      {error && (

        <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">

          {error}

        </div>

      )}


      {/* GLOBAL EVENTS */}

      <section>

        <div className="mb-4 flex items-center gap-2">

          <Globe2 size={18} />

          <h2 className="text-xl font-semibold">
            Global Events
          </h2>

        </div>


        <div className="grid gap-4 lg:grid-cols-2">

          {events.length === 0 ? (

            <div className="rounded-2xl border bg-white p-6 text-sm text-slate-500">
              No global events available.
            </div>

          ) : (

            events.map(
              (event) => (

                <div
                  key={event.id}
                  className="rounded-2xl border bg-white p-5 shadow-sm"
                >

                  <div className="flex items-start gap-4">

                    <div className="rounded-xl bg-amber-50 p-3">

                      <AlertTriangle
                        size={20}
                        className="text-amber-600"
                      />

                    </div>


                    <div className="min-w-0 flex-1">

                      <h3 className="font-semibold text-slate-900">

                        {event.title}

                      </h3>


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

                </div>

              ),
            )

          )}

        </div>

      </section>


      {/* MARKET */}

      <section className="mt-10">

        <div className="mb-4 flex items-center gap-2">

          <DollarSign size={18} />

          <h2 className="text-xl font-semibold">
            Market Intelligence
          </h2>

        </div>


        {marketError ? (

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-700">

            Market intelligence is temporarily unavailable.

          </div>

        ) : (

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

            {Object.entries(
              market?.commodities || {},
            ).map(
              ([name, rawData]) => {

                const data =
                  rawData as any;

                const change =
                  Number(
                    data?.percentage_change
                    ?? 0,
                  );

                const positive =
                  change >= 0;


                return (

                  <div
                    key={name}
                    className="rounded-2xl border bg-white p-5 shadow-sm"
                  >

                    <p className="text-sm text-slate-500">
                      {name}
                    </p>


                    <p className="mt-2 text-2xl font-bold">

                      {data?.latest_value
                        ?? "-"}

                    </p>


                    <p className="mt-1 text-xs text-slate-500">

                      {data?.unit
                        ?? ""}

                    </p>


                    <p
                      className={`mt-3 text-sm font-semibold ${
                        positive
                          ? "text-emerald-600"
                          : "text-red-600"
                      }`}
                    >

                      {positive
                        ? "+"
                        : ""}

                      {change.toFixed(2)}%

                    </p>

                  </div>

                );

              },
            )}

          </div>

        )}

      </section>


      {/* AGRICULTURE */}

      <section className="mt-10">

        <div className="mb-4 flex items-center gap-2">

          <Wheat size={18} />

          <h2 className="text-xl font-semibold">
            Agriculture Intelligence
          </h2>

        </div>


        {agricultureError ? (

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-700">

            Agriculture intelligence is temporarily unavailable.

          </div>

        ) : (

          <div className="grid gap-4 lg:grid-cols-2">

            {(agriculture?.risks || [])
              .slice(0, 6)
              .map(
                (
                  risk: any,
                  index: number,
                ) => (

                  <div
                    key={
                      risk.id
                      ?? index
                    }
                    className="rounded-2xl border bg-white p-5 shadow-sm"
                  >

                    <div className="flex justify-between gap-4">

                      <div>

                        <p className="font-semibold">
                          {risk.crop
                            ?? "Crop"}
                        </p>

                        <p className="text-sm text-slate-500">
                          {risk.region
                            ?? ""}
                        </p>

                      </div>


                      <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">

                        {risk.severity
                          ?? "INFO"}

                      </span>

                    </div>


                    <div className="mt-4">

                      <p className="text-sm text-slate-500">
                        {risk.signal_type
                          ?? "Signal"}
                      </p>


                      <p className="mt-1 text-xl font-bold">

                        {risk.value
                          ?? "-"}

                        {risk.unit
                          ? ` ${risk.unit}`
                          : ""}

                      </p>

                    </div>

                  </div>

                ),
              )}

          </div>

        )}

      </section>


      {/* SUMMARY */}

      <section className="mt-10">

        <div className="mb-4 flex items-center gap-2">

          <CloudRain size={18} />

          <h2 className="text-xl font-semibold">
            Intelligence Summary
          </h2>

        </div>


        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <p className="text-slate-600">

            HEX continuously combines external
            signals with internal business data to
            determine how global events could
            affect suppliers, products, routes and
            financial performance.

          </p>

        </div>

      </section>

    </div>
  );
}