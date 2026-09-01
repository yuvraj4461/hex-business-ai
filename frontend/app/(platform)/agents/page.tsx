"use client";

import { useEffect, useState } from "react";

import {
  Bot,
  ChevronRight,
  DollarSign,
  Loader2,
  Play,
  Radar,
  ShieldAlert,
  ShoppingCart,
  Truck,
  type LucideIcon,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import SeverityBadge from "@/app/components/SeverityBadge";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import { TONE_BADGE, toneForStatus, type Tone } from "@/app/components/tone";

const AGENT_ICON: Record<string, LucideIcon> = {
  finance: DollarSign,
  sales: ShoppingCart,
  operations: Truck,
  watch: Radar,
  risk: ShieldAlert,
};

interface AgentStatus {
  key: string;
  name: string;
  description: string;
  status: string;
  detail: string;
  position: number;
  data_sources: Record<string, number | null>;
}

interface StatusResponse {
  pipeline: string[];
  agents_total: number;
  agents_ready: number;
  system_status: string;
  agents: AgentStatus[];
}

interface AgentRun {
  agent?: string;
  key?: string;
  status?: string;
  duration_ms?: number;
  findings_added?: number;
  recommendations_added?: number;
  error?: string;
}

interface AgentItem {
  agent?: string;
  type?: string;
  severity?: string;
  data?: Record<string, unknown>;
}

interface RunResponse {
  question: string;
  duration_ms: number;
  agents_run: number;
  agents_succeeded: number;
  agents_failed: number;
  status: string;
  agent_runs: AgentRun[];
  findings: (AgentItem | string)[];
  recommendations: (AgentItem | string)[];
  errors: string[];
}

function humanize(value?: string): string {
  return (value ?? "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function describeItem(item: AgentItem | string): {
  title: string;
  body?: string;
} {
  if (typeof item === "string") {
    return { title: item };
  }

  const data = item.data ?? {};
  const note =
    (data.note as string | undefined) ??
    (data.message as string | undefined) ??
    (data.summary as string | undefined);

  const fmt = (v: unknown): string => {
    if (v == null) return "—";
    if (typeof v === "number") return v.toLocaleString("en-IN");
    if (typeof v === "string") return v;
    return JSON.stringify(v);
  };

  const body =
    note ??
    Object.entries(data)
      // Skip nested structures — they don't read well on one line.
      .filter(([, v]) => typeof v !== "object" || v === null)
      .slice(0, 5)
      .map(([k, v]) => `${humanize(k)}: ${fmt(v)}`)
      .join("  ·  ");

  return {
    title:
      [item.agent, humanize(item.type)].filter(Boolean).join(" — ") ||
      "Item",
    body: body || undefined,
  };
}

export default function AgentsPage() {
  const [data, setData] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [question, setQuestion] = useState(
    "Provide a full business health assessment.",
  );
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");
  const [run, setRun] = useState<RunResponse | null>(null);

  async function loadStatus() {
    try {
      setLoading(true);
      setError("");
      const response = await apiRequest<StatusResponse>("/agents/status");
      setData(response);
    } catch (err) {
      console.error("Failed to load agent status:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load agent status.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch
    loadStatus();
  }, []);

  async function runAgents() {
    try {
      setRunning(true);
      setRunError("");
      setRun(null);

      const response = await apiRequest<RunResponse>("/agents/run", {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      });

      setRun(response);
    } catch (err) {
      console.error("Agent run failed:", err);
      setRunError(
        err instanceof Error ? err.message : "Agent run failed.",
      );
    } finally {
      setRunning(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Checking agent readiness…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard
          title="Unable to load agents"
          message={error}
          onRetry={loadStatus}
        />
      </div>
    );
  }

  const systemTone = toneForStatus(data?.system_status);

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Bot}
        tone="live"
        eyebrow="Multi-Agent Intelligence"
        title="Agent Monitor"
        description="Each agent is checked against the data it needs. The graph runs finance → sales → operations → world watch → risk."
        actions={
          <SeverityBadge
            value={data?.system_status}
            tone={systemTone}
          />
        }
      />

      {/* Pipeline strip */}
      <Panel label="Pipeline" title="Execution Order" tone="live">
        <div className="flex flex-wrap items-center gap-2">
          {(data?.pipeline ?? []).map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <span className="rounded-lg border border-hairline bg-panel-raised px-3 py-1.5 text-sm text-white">
                <span className="num text-mute">{i + 1}</span> {step}
              </span>
              {i < (data?.pipeline.length ?? 0) - 1 && (
                <ChevronRight size={14} className="text-mute" />
              )}
            </div>
          ))}
        </div>

        <p className="num mt-4 text-xs text-mute">
          {num(data?.agents_ready)} / {num(data?.agents_total)} agents ready
        </p>
      </Panel>

      {/* Agent grid */}
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {(data?.agents ?? []).map((agent) => {
          const tone: Tone =
            agent.status === "READY"
              ? "stable"
              : agent.status === "DEGRADED"
                ? "elevated"
                : "critical";
          const Icon = AGENT_ICON[agent.key] ?? Bot;
          const sources = Object.entries(agent.data_sources);

          return (
            <div
              key={agent.key}
              className="elevated group relative overflow-hidden rounded-xl border border-hairline bg-panel p-4 ring-1 ring-inset ring-white/[0.02] transition hover:-translate-y-0.5 hover:ring-accent/30"
              title={agent.detail}
            >
              <span
                aria-hidden
                className={`absolute inset-x-0 top-0 h-0.5 ${
                  tone === "critical"
                    ? "bg-critical"
                    : tone === "elevated"
                      ? "bg-elevated"
                      : "bg-stable"
                }`}
              />

              <div className="flex items-start justify-between">
                <span className="grid h-9 w-9 place-items-center rounded-lg bg-panel-raised text-dim group-hover:text-accent">
                  <Icon size={17} />
                </span>
                <span className="num text-xs text-mute">
                  0{agent.position}
                </span>
              </div>

              <p className="mt-3 font-semibold leading-tight text-white">
                {agent.name}
              </p>

              <span
                className={`mt-2 inline-block rounded-md px-2 py-0.5 text-[0.7rem] font-semibold ${TONE_BADGE[tone]}`}
              >
                {agent.status}
              </span>

              <div className="mt-3 flex items-center gap-1.5">
                {sources.map(([table, count]) => (
                  <span
                    key={table}
                    title={`${table}: ${count === null ? "unavailable" : count}`}
                    className={`h-1.5 w-1.5 rounded-full ${
                      count === null
                        ? "bg-critical"
                        : count === 0
                          ? "bg-elevated"
                          : "bg-stable"
                    }`}
                  />
                ))}
                <span className="num ml-1 text-[0.65rem] text-mute">
                  {sources.length} src
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Run analysis */}
      <div className="mt-5">
        <Panel
          label="Decision Intelligence"
          title="Run Analysis"
          tone="live"
        >
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask the agent graph a question…"
              className="flex-1 rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
            />

            <button
              type="button"
              onClick={runAgents}
              disabled={running || !question.trim()}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {running ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Running…
                </>
              ) : (
                <>
                  <Play size={15} />
                  Run
                </>
              )}
            </button>
          </div>

          {runError && (
            <div className="mt-4 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
              {runError}
            </div>
          )}

          {run && (
            <div className="mt-5 space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <SeverityBadge value={run.status} />
                <span className="num text-xs text-mute">
                  {num(run.agents_succeeded)}/{num(run.agents_run)} ok ·{" "}
                  {num(run.agents_failed)} failed · {num(run.duration_ms)}ms
                </span>
              </div>

              <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
                {run.agent_runs.map((r, i) => (
                  <div
                    key={i}
                    className="flex items-start justify-between gap-3 rounded-lg border border-hairline bg-panel-raised/40 p-3"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white">
                        {r.agent ?? r.key ?? `Agent ${i + 1}`}
                      </p>
                      <p className="num mt-1 text-xs text-dim">
                        {r.error
                          ? r.error
                          : `+${num(r.findings_added)} findings · +${num(
                              r.recommendations_added,
                            )} recs · ${num(r.duration_ms)}ms`}
                      </p>
                    </div>
                    <SeverityBadge value={r.status} />
                  </div>
                ))}
              </div>

              {run.findings.length > 0 && (
                <div>
                  <p className="eyebrow">
                    Findings{" "}
                    <span className="num text-mute">{run.findings.length}</span>
                  </p>
                  <ul className="mt-2 max-h-[22rem] space-y-1.5 overflow-y-auto pr-1">
                    {run.findings.map((f, i) => {
                      const { title, body } = describeItem(f);
                      return (
                        <li
                          key={i}
                          className="rounded-lg bg-panel-raised px-3 py-2 text-sm"
                        >
                          <p className="font-medium text-white">{title}</p>
                          {body && (
                            <p className="num mt-0.5 text-xs text-dim">
                              {body}
                            </p>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              {run.recommendations.length > 0 && (
                <div>
                  <p className="eyebrow">
                    Recommendations{" "}
                    <span className="num text-mute">
                      {run.recommendations.length}
                    </span>
                  </p>
                  <ul className="mt-2 max-h-[22rem] space-y-1.5 overflow-y-auto pr-1">
                    {run.recommendations.map((r, i) => {
                      const { title, body } = describeItem(r);
                      return (
                        <li
                          key={i}
                          className="rounded-lg border border-live/25 bg-live/5 px-3 py-2 text-sm"
                        >
                          <p className="font-medium text-white">{title}</p>
                          {body && (
                            <p className="num mt-0.5 text-xs text-dim">
                              {body}
                            </p>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              {run.errors.length > 0 && (
                <div>
                  <p className="eyebrow !text-critical">Errors</p>
                  <ul className="mt-2 max-h-52 space-y-1.5 overflow-y-auto pr-1">
                    {run.errors.map((e, i) => (
                      <li
                        key={i}
                        className="rounded-lg border border-critical/25 bg-critical/5 px-3 py-2 text-sm text-critical"
                      >
                        {e}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Panel>
      </div>
    </div>
  );
}
