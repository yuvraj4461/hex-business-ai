"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import {
  Bot,
  ExternalLink,
  Loader2,
  Plus,
  Send,
  Sparkles,
} from "lucide-react";

import { apiRequest } from "@/lib/api";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";

interface Source {
  title: string;
  url: string;
}

interface CopilotResponse {
  question: string;
  answer: string;
  sources?: Source[];
}

interface ChatMessage {
  id: number;
  role: "user" | "hex";
  text: string;
  sources?: Source[];
  error?: boolean;
}

const CONTEXT = [
  "Live web search (Google)",
  "Wikipedia",
  "Business performance",
  "Historical analytics",
  "Global events",
  "Commodity intelligence",
  "Agriculture signals",
  "Demand forecasts",
  "Business exposure",
  "Route disruption",
];

const EXAMPLES = [
  "What is the biggest risk to my business right now?",
  "How would a Red Sea disruption affect my costs?",
  "Summarise my current supplier exposure.",
  "What's driving my expenses this quarter?",
];

export default function CopilotPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, loading]);

  async function send(question: string) {
    const q = question.trim();
    if (!q || loading) return;

    setInput("");
    const history = messages.slice(-8).map((m) => ({
      role: m.role,
      content: m.text.slice(0, 2000),
    }));
    setMessages((m) => [
      ...m,
      { id: Date.now(), role: "user", text: q },
    ]);
    setLoading(true);

    try {
      const result = await apiRequest<CopilotResponse>("/copilot/ask", {
        method: "POST",
        body: JSON.stringify({ question: q, history }),
      });
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "hex",
          text: result.answer,
          sources: result.sources,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: Date.now() + 1,
          role: "hex",
          text:
            err instanceof Error
              ? err.message
              : "Unable to get a Copilot response.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    send(input);
  }

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Sparkles}
        eyebrow="Decision Intelligence"
        title="AI Copilot"
        description="Ask HEX about your business, operations, market conditions and risk."
        actions={
          messages.length > 0 ? (
            <button
              type="button"
              onClick={() => setMessages([])}
              className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-3.5 py-2 text-sm font-medium text-dim transition hover:text-white"
            >
              <Plus size={15} /> New chat
            </button>
          ) : undefined
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* chat */}
        <div className="lg:col-span-2">
          <Panel
            label="Natural Language"
            title="Ask HEX"
            tone="live"
            action={<Bot size={18} className="text-dim" />}
            bodyClassName="flex h-[calc(100vh-16rem)] flex-col"
          >
            <div
              ref={scrollRef}
              className="-mx-1 flex-1 space-y-4 overflow-y-auto px-1"
            >
              {messages.length === 0 && !loading && (
                <div className="flex h-full flex-col justify-center gap-4">
                  <p className="text-sm text-dim">
                    Ask a question to start. HEX answers using live web
                    research and your own business data.
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {EXAMPLES.map((e) => (
                      <button
                        key={e}
                        type="button"
                        onClick={() => send(e)}
                        className="rounded-full border border-hairline bg-panel-raised px-3.5 py-1.5 text-left text-sm text-dim transition hover:border-accent/40 hover:text-white"
                      >
                        {e}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="flex justify-end">
                    <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-accent/15 px-4 py-2.5 text-sm text-white">
                      {m.text}
                    </p>
                  </div>
                ) : (
                  <div key={m.id} className="flex gap-3">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-live/10 text-live">
                      <Sparkles size={15} />
                    </span>
                    <div
                      className={`min-w-0 flex-1 rounded-2xl rounded-tl-sm border p-4 ${
                        m.error
                          ? "border-critical/30 bg-critical/5"
                          : "border-hairline bg-panel-raised/50"
                      }`}
                    >
                      <p
                        className={`whitespace-pre-wrap text-sm leading-6 ${
                          m.error ? "text-critical" : "text-dim"
                        }`}
                      >
                        {m.text}
                      </p>

                      {m.sources && m.sources.length > 0 && (
                        <div className="mt-3 border-t border-hairline pt-3">
                          <p className="eyebrow mb-2">Sources</p>
                          <div className="flex flex-wrap gap-2">
                            {m.sources.map((s) => (
                              <a
                                key={s.url}
                                href={s.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-1.5 rounded-md border border-hairline bg-panel-raised px-2.5 py-1 text-xs text-live transition hover:brightness-125"
                              >
                                <ExternalLink size={11} />
                                {s.title.length > 48
                                  ? `${s.title.slice(0, 48)}…`
                                  : s.title}
                              </a>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ),
              )}

              {loading && (
                <div className="flex gap-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-live/10 text-live">
                    <Sparkles size={15} />
                  </span>
                  <p className="flex items-center gap-2 rounded-2xl rounded-tl-sm border border-hairline bg-panel-raised/50 px-4 py-3 text-sm text-dim">
                    <Loader2 size={15} className="animate-spin" /> HEX is
                    thinking…
                  </p>
                </div>
              )}
            </div>

            <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask HEX anything about your business or the market…"
                className="flex-1 rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Send size={15} />
                )}
                Ask
              </button>
            </form>
          </Panel>
        </div>

        <Panel label="Grounding" title="Available Context">
          <div className="space-y-2">
            {CONTEXT.map((item) => (
              <div
                key={item}
                className="rounded-lg bg-panel-raised px-3.5 py-2.5 text-sm text-dim"
              >
                {item}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}
