"use client";

import { FormEvent, useState } from "react";

import { Bot, ExternalLink, Loader2, Send, Sparkles } from "lucide-react";

import { apiRequest } from "@/lib/api";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";

interface CopilotResponse {
  question: string;
  answer: string;
  sources?: { title: string; url: string }[];
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

export default function CopilotPage() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<CopilotResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!question.trim()) return;

    try {
      setLoading(true);
      setError("");

      const result = await apiRequest<CopilotResponse>("/copilot/ask", {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      });

      setResponse(result);
    } catch (err) {
      console.error("Copilot request failed:", err);
      setError(
        err instanceof Error
          ? err.message
          : "Unable to get a Copilot response.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Sparkles}
        eyebrow="Decision Intelligence"
        title="AI Copilot"
        description="Ask HEX about your business, operations, market conditions and risk."
      />

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Panel
            label="Natural Language"
            title="Ask HEX"
            tone="live"
            action={<Bot size={18} className="text-dim" />}
          >
            <form onSubmit={handleSubmit}>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={6}
                placeholder="Example: What is the biggest risk to my business right now?"
                className="w-full resize-none rounded-lg border border-hairline bg-panel-raised p-3.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              />

              {error && (
                <div className="mt-4 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
                  {error}
                </div>
              )}

              <div className="mt-4 flex justify-end">
                <button
                  type="submit"
                  disabled={loading || !question.trim()}
                  className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Analyzing…
                    </>
                  ) : (
                    <>
                      <Send size={15} />
                      Ask HEX
                    </>
                  )}
                </button>
              </div>
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

      {response && (
        <div className="mt-5">
          <Panel
            label="HEX Response"
            title={response.question}
            tone="stable"
            action={<Sparkles size={18} className="text-stable" />}
          >
            <div className="rounded-lg bg-panel-raised p-4">
              <p className="whitespace-pre-wrap text-sm leading-6 text-dim">
                {response.answer}
              </p>
            </div>

            {response.sources && response.sources.length > 0 && (
              <div className="mt-4">
                <p className="eyebrow mb-2">Sources</p>
                <div className="flex flex-wrap gap-2">
                  {response.sources.map((s) => (
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
          </Panel>
        </div>
      )}
    </div>
  );
}
