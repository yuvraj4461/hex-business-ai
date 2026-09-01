"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";

import {
  Loader2,
  MessagesSquare,
  Plus,
  Send,
  Table as TableIcon,
  Trash2,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num, timeAgo } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import StatTile from "@/app/components/StatTile";
import { EmptyCard } from "@/app/components/StateCard";
import BarBreakdown from "@/app/components/charts/BarBreakdown";
import TrendLine from "@/app/components/charts/TrendLine";

interface Column {
  key: string;
  label: string;
  type: string;
}

interface QueryResult {
  columns: Column[];
  rows: { label: string; value: number }[];
  chart:
    | { type: "line" | "bar" | "stat"; x: string; y: string; unit: string }
    | null;
  row_count: number;
}

interface Message {
  id: number;
  role: "user" | "hex";
  question?: string | null;
  answer?: string | null;
  spec?: Record<string, unknown> | null;
  spec_label?: string | null;
  result?: QueryResult | null;
  degraded?: boolean;
  created_at?: string | null;
}

interface ThreadSummary {
  id: number;
  title: string;
  message_count: number;
  updated_at?: string | null;
}

interface ThreadDetail {
  id: number;
  title: string;
  messages: Message[];
}

const STARTERS = [
  "Revenue by month",
  "Top 5 products by revenue",
  "Expenses by category",
  "Which suppliers have the longest lead times?",
  "Units sold by product category",
  "Profit over time",
];

export default function AskPage() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);

  const loadThreads = useCallback(async () => {
    try {
      const list = await apiRequest<ThreadSummary[]>("/copilot/data/threads");
      setThreads(list);
      return list;
    } catch {
      return [];
    }
  }, []);

  const openThread = useCallback(async (id: number) => {
    setActiveId(id);
    setLoadingDetail(true);
    setError("");
    try {
      setDetail(await apiRequest<ThreadDetail>(`/copilot/data/threads/${id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load that thread.");
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    loadThreads().then((list) => {
      if (list.length) openThread(list[0].id);
    });
  }, [loadThreads, openThread]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [detail?.messages.length, sending]);

  function startNewThread() {
    setActiveId(null);
    setDetail(null);
    setInput("");
    setError("");
  }

  async function ask(question: string) {
    const q = question.trim();
    if (!q || sending) return;
    setSending(true);
    setError("");
    setInput("");

    try {
      if (activeId == null) {
        const created = await apiRequest<ThreadDetail>("/copilot/data/threads", {
          method: "POST",
          body: JSON.stringify({ question: q }),
        });
        setDetail(created);
        setActiveId(created.id);
        await loadThreads();
      } else {
        // optimistic user bubble
        setDetail((d) =>
          d
            ? {
                ...d,
                messages: [
                  ...d.messages,
                  { id: -Date.now(), role: "user", question: q },
                ],
              }
            : d,
        );
        await apiRequest<Message>(
          `/copilot/data/threads/${activeId}/messages`,
          { method: "POST", body: JSON.stringify({ question: q }) },
        );
        await openThread(activeId);
        await loadThreads();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "That question failed.");
    } finally {
      setSending(false);
    }
  }

  async function remove(id: number) {
    try {
      await apiRequest(`/copilot/data/threads/${id}`, { method: "DELETE" });
    } catch {
      /* ignore */
    }
    const list = await loadThreads();
    if (activeId === id) {
      if (list.length) openThread(list[0].id);
      else startNewThread();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    ask(input);
  }

  const messages = detail?.messages ?? [];

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={MessagesSquare}
        eyebrow="Decision Intelligence"
        title="Ask Your Data"
        description="Ask your business data in plain language. HEX answers with a number, a chart and the rows behind it — then you can drill in."
      />

      <div className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
        {/* history rail */}
        <aside className="flex flex-col gap-2">
          <button
            type="button"
            onClick={startNewThread}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-bg transition hover:bg-accent/90"
          >
            <Plus size={15} /> New thread
          </button>

          <div className="mt-1 space-y-1">
            {threads.length === 0 && (
              <p className="px-2 py-3 text-xs text-mute">
                No threads yet. Ask something to start one.
              </p>
            )}
            {threads.map((t) => (
              <div
                key={t.id}
                className={`group flex items-center gap-1 rounded-lg border px-2.5 py-2 text-sm transition ${
                  t.id === activeId
                    ? "border-accent/40 bg-accent/10 text-white"
                    : "border-hairline bg-panel text-dim hover:border-hairline hover:text-white"
                }`}
              >
                <button
                  type="button"
                  onClick={() => openThread(t.id)}
                  className="min-w-0 flex-1 text-left"
                >
                  <p className="truncate">{t.title}</p>
                  <p className="num mt-0.5 text-[0.65rem] text-mute">
                    {t.message_count} msgs · {timeAgo(t.updated_at)}
                  </p>
                </button>
                <button
                  type="button"
                  aria-label="Delete thread"
                  onClick={() => remove(t.id)}
                  className="shrink-0 rounded p-1 text-mute opacity-0 transition hover:text-critical group-hover:opacity-100"
                >
                  <Trash2 size={13} />
                </button>
              </div>
            ))}
          </div>
        </aside>

        {/* conversation */}
        <section className="flex min-h-0 flex-col">
          <div
            ref={scrollRef}
            className="max-h-[calc(100vh-16rem)] flex-1 space-y-4 overflow-y-auto pr-1"
          >
            {messages.length === 0 && !loadingDetail && (
              <div className="space-y-4">
                <EmptyCard message="Ask a question to begin — or pick one of these:" />
                <div className="flex flex-wrap gap-2">
                  {STARTERS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => ask(s)}
                      className="rounded-full border border-hairline bg-panel px-3.5 py-1.5 text-sm text-dim transition hover:border-accent/40 hover:text-white"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {loadingDetail && (
              <p className="flex items-center gap-2 text-sm text-dim">
                <Loader2 size={15} className="animate-spin" /> Loading thread…
              </p>
            )}

            {messages.map((m) =>
              m.role === "user" ? (
                <div key={m.id} className="flex justify-end">
                  <p className="max-w-[80%] rounded-2xl rounded-br-sm bg-accent/15 px-4 py-2 text-sm text-white">
                    {m.question}
                  </p>
                </div>
              ) : (
                <HexAnswer key={m.id} message={m} />
              ),
            )}

            {sending && (
              <p className="flex items-center gap-2 text-sm text-dim">
                <Loader2 size={15} className="animate-spin" /> HEX is working…
              </p>
            )}
          </div>

          {error && (
            <div className="mt-3 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={
                activeId == null
                  ? "Ask about revenue, orders, products, suppliers…"
                  : "Ask a follow-up — “break it down by category”, “only 2026”…"
              }
              className="flex-1 rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {sending ? (
                <Loader2 size={15} className="animate-spin" />
              ) : (
                <Send size={15} />
              )}
              Ask
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

function HexAnswer({ message }: { message: Message }) {
  const result = message.result;
  const chart = result?.chart ?? null;
  const rows = result?.rows ?? [];
  const isCurrency = chart?.unit === "INR";
  const fmt = (v: number) => (isCurrency ? inr(v) : num(v));
  const chartData = rows.map((r) => ({ name: r.label, value: r.value }));

  return (
    <Panel
      tone="live"
      label={message.spec_label || "HEX"}
      title={undefined}
    >
      <p className="whitespace-pre-wrap text-sm leading-6 text-dim">
        {message.answer}
      </p>

      {chart?.type === "stat" && rows[0] && (
        <div className="mt-4 max-w-xs">
          <StatTile label={rows[0].label} value={fmt(rows[0].value)} tone="live" />
        </div>
      )}

      {chart?.type === "bar" && chartData.length > 0 && (
        <div className="mt-4">
          <BarBreakdown data={chartData} currency={isCurrency} />
        </div>
      )}

      {chart?.type === "line" && chartData.length > 0 && (
        <div className="mt-4">
          <TrendLine data={chartData} currency={isCurrency} />
        </div>
      )}

      {rows.length > 0 && (
        <details className="mt-4 rounded-lg border border-hairline bg-panel-raised/40">
          <summary className="flex cursor-pointer items-center gap-2 px-3 py-2 text-xs text-dim">
            <TableIcon size={13} /> Show the {result?.row_count ?? rows.length} rows
          </summary>
          <div className="max-h-64 overflow-auto border-t border-hairline">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-mute">
                  {(result?.columns ?? []).map((c) => (
                    <th key={c.key} className="px-3 py-1.5 font-medium">
                      {c.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} className="border-t border-hairline/60">
                    <td className="px-3 py-1.5 text-dim">{r.label}</td>
                    <td className="num px-3 py-1.5 text-white">{fmt(r.value)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}

      {message.degraded && (
        <p className="mt-3 text-[0.7rem] text-elevated">
          Interpreted by keyword matching — HEX's language model was busy. If
          this isn&apos;t what you meant, try naming the metric and grouping
          explicitly.
        </p>
      )}
    </Panel>
  );
}
