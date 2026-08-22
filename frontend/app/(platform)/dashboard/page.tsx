"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  DollarSign,
  Globe2,
  ShoppingCart,
  Truck,
} from "lucide-react";

import {
  apiRequest,
} from "@/lib/api";


interface Overview {
  revenue?: number;
  expenses?: number;
  profit?: number;
  orders?: number;
}


interface GlobalEvent {
  id: number;
  title: string;
  event_type: string;
  severity: string;
  region?: string;
}


export default function DashboardPage() {

  const [
    overview,
    setOverview,
  ] = useState<Overview | null>(
    null,
  );


  const [
    events,
    setEvents,
  ] = useState<GlobalEvent[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    async function loadDashboard() {

      try {

        setLoading(true);
        setError("");


        const [
          businessData,
          globalEvents,
        ] = await Promise.all([

          apiRequest<Overview>(
            "/business/overview",
          ),

          apiRequest<GlobalEvent[]>(
            "/global-events/?limit=5",
          ),

        ]);


        setOverview(
          businessData,
        );

        setEvents(
          globalEvents,
        );

      } catch (err) {

        console.error(
          "Dashboard error:",
          err,
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard.",
        );

      } finally {

        setLoading(false);

      }

    }


    loadDashboard();

  }, []);


  if (loading) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

          <p className="text-slate-500">
            Loading HEX dashboard...
          </p>

        </div>

      </div>
    );
  }


  if (error) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-700">

          <p className="font-semibold">
            Dashboard unavailable
          </p>

          <p className="mt-2">
            {error}
          </p>

        </div>

      </div>
    );
  }


  const cards = [

    {
      title: "Revenue",
      value:
        overview?.revenue ?? 0,
      icon: DollarSign,
    },

    {
      title: "Expenses",
      value:
        overview?.expenses ?? 0,
      icon: ArrowDownRight,
    },

    {
      title: "Profit",
      value:
        overview?.profit ?? 0,
      icon: ArrowUpRight,
    },

    {
      title: "Orders",
      value:
        overview?.orders ?? 0,
      icon: ShoppingCart,
    },

  ];


  return (
    <div className="p-6 lg:p-8">

      <div className="mb-8">

        <p className="text-sm font-medium text-slate-500">
          Executive Overview
        </p>

        <h1 className="mt-1 text-3xl font-bold text-slate-900">
          Business Dashboard
        </h1>

        <p className="mt-2 text-slate-500">
          Your business, internal operations,
          and global intelligence in one place.
        </p>

      </div>


      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">

        {cards.map(
          (card) => {

            const Icon =
              card.icon;

            return (

              <div
                key={card.title}
                className="rounded-2xl border bg-white p-6 shadow-sm"
              >

                <div className="rounded-xl bg-slate-100 p-3 w-fit">

                  <Icon size={20} />

                </div>

                <p className="mt-6 text-sm text-slate-500">
                  {card.title}
                </p>

                <p className="mt-1 text-2xl font-bold text-slate-900">

                  {typeof card.value === "number"
                    ? card.value.toLocaleString(
                        "en-IN",
                      )
                    : card.value}

                </p>

              </div>

            );
          },
        )}

      </div>


      <div className="mt-8 grid gap-6 xl:grid-cols-3">

        <div className="xl:col-span-2 rounded-2xl border bg-white p-6 shadow-sm">

          <div className="flex items-center justify-between">

            <div>

              <h2 className="font-semibold text-slate-900">
                Global Intelligence
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                External events that may affect your business.
              </p>

            </div>

            <Globe2 size={22} />

          </div>


          <div className="mt-6 space-y-3">

            {events.length === 0 ? (

              <div className="rounded-xl bg-slate-50 p-6 text-sm text-slate-500">
                No recent global events.
              </div>

            ) : (

              events.map(
                (event) => (

                  <div
                    key={event.id}
                    className="flex items-center gap-4 rounded-xl border p-4"
                  >

                    <div className="rounded-lg bg-amber-50 p-2">

                      <AlertTriangle
                        size={18}
                        className="text-amber-600"
                      />

                    </div>


                    <div className="min-w-0 flex-1">

                      <p className="font-medium text-slate-900">
                        {event.title}
                      </p>

                      <p className="mt-1 text-xs text-slate-500">

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

                ),
              )

            )}

          </div>

        </div>


        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-slate-100 p-3">
              <Truck size={20} />
            </div>

            <div>

              <h2 className="font-semibold">
                Supply Chain
              </h2>

              <p className="text-sm text-slate-500">
                Operational intelligence
              </p>

            </div>

          </div>


          <div className="mt-6 space-y-4">

            {[
              ["Route Monitoring", "Active"],
              ["Supplier Risk", "Monitoring"],
              ["Inventory", "Tracking"],
            ].map(
              ([label, value]) => (

                <div
                  key={label}
                  className="rounded-xl bg-slate-50 p-4"
                >

                  <p className="text-sm text-slate-500">
                    {label}
                  </p>

                  <p className="mt-1 font-semibold">
                    {value}
                  </p>

                </div>

              ),
            )}

          </div>

        </div>

      </div>

    </div>
  );
}