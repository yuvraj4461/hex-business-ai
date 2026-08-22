"use client";

import {
  useEffect,
  useState,
} from "react";

import {
  Bot,
  CheckCircle2,
  Loader2,
  ShieldAlert,
} from "lucide-react";

import {
  apiRequest,
} from "@/lib/api";


interface AgentStatus {
  name: string;
  status: string;
  description?: string;
}


interface AgentStatusResponse {
  agents: AgentStatus[];
}


export default function AgentsPage() {

  const [
    data,
    setData,
  ] = useState<AgentStatusResponse | null>(
    null
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    async function loadAgents() {

      try {

        setLoading(true);
        setError("");

        const response =
          await apiRequest<AgentStatusResponse>(
            "/agents/status"
          );

        setData(
          response
        );

      } catch (err) {

        console.error(
          "Failed to load agent status:",
          err
        );

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load agent status."
        );

      } finally {

        setLoading(false);

      }
    }

    loadAgents();

  }, []);


  if (loading) {

    return (
      <div className="p-8">

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">

          <Loader2
            className="mx-auto animate-spin text-slate-500"
            size={28}
          />

          <p className="mt-4 text-slate-500">
            Loading agent status...
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
            Unable to load agents
          </p>

          <p className="mt-2 text-sm">
            {error}
          </p>

        </div>

      </div>
    );
  }


  const agents =
    data?.agents || [];


  return (
    <div className="p-6 lg:p-8">

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-violet-100 p-3">

            <Bot
              size={22}
              className="text-violet-600"
            />

          </div>

          <div>

            <p className="text-sm text-slate-500">
              Multi-Agent Intelligence
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              Agent Monitor
            </h1>

          </div>

        </div>

        <p className="mt-3 text-slate-500">
          Monitor the specialized HEX agents used
          for business analysis and decision support.
        </p>

      </div>


      {agents.length === 0 ? (

        <div className="rounded-2xl border bg-white p-8 text-center shadow-sm">
          <p className="text-slate-500">
            No agent status data is currently available.
          </p>
        </div>

      ) : (

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

          {agents.map(
            (agent) => {

              const isHealthy =
                agent.status
                .toUpperCase()
                === "ACTIVE"
                ||
                agent.status
                .toUpperCase()
                === "ONLINE"
                ||
                agent.status
                .toUpperCase()
                === "READY";


              return (
                <div
                  key={agent.name}
                  className="rounded-2xl border bg-white p-6 shadow-sm"
                >

                  <div className="flex items-start justify-between">

                    <div className="rounded-xl bg-slate-100 p-3">
                      <Bot
                        size={20}
                      />
                    </div>


                    <span
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        isHealthy
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-amber-50 text-amber-700"
                      }`}
                    >
                      {agent.status}
                    </span>

                  </div>


                  <h2 className="mt-6 text-lg font-semibold">
                    {agent.name}
                  </h2>


                  <p className="mt-2 text-sm text-slate-500">
                    {agent.description ||
                      "HEX specialized intelligence agent."}
                  </p>


                  <div className="mt-6 flex items-center gap-2 text-sm">

                    {isHealthy ? (
                      <>
                        <CheckCircle2
                          size={17}
                          className="text-emerald-600"
                        />

                        <span className="text-emerald-700">
                          Operational
                        </span>
                      </>
                    ) : (
                      <>
                        <ShieldAlert
                          size={17}
                          className="text-amber-600"
                        />

                        <span className="text-amber-700">
                          Attention required
                        </span>
                      </>
                    )}

                  </div>

                </div>
              );

            }
          )}

        </div>

      )}

    </div>
  );
}