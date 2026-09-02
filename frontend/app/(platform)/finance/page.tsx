"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  Calculator,
  Gauge,
  Loader2,
  Sigma,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { inr, num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import StatTile from "@/app/components/StatTile";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";

interface Metric {
  label: string;
  value: number | null;
  unit: string;
  formula: string;
  inputs: Record<string, unknown>;
  note?: string | null;
}

interface Battery {
  headline: {
    revenue: number;
    expenses: number;
    profit: number;
    operating_margin_pct: number;
    months_of_data: number;
    active_customers: number;
  };
  sections: Record<string, Metric[]>;
}

interface FormulaParam {
  name: string;
  label: string;
  kind: string;
}

interface FormulaDef {
  key: string;
  label: string;
  category: string;
  unit: string;
  description: string;
  params: FormulaParam[];
}

const SECTION_LABELS: Record<string, string> = {
  profitability: "Profitability",
  growth: "Growth & Trend",
  cash: "Cash",
  risk: "Risk & Volatility",
  unit_economics: "Unit Economics",
  break_even: "Break-even",
};

function fmtUnit(value: number | null, unit: string): string {
  if (value === null || value === undefined) return "—";
  if (unit === "currency") return inr(value);
  if (unit === "percent") return `${value.toFixed(1)}%`;
  if (unit === "ratio") return value.toFixed(2);
  if (unit === "months") return `${value.toFixed(1)} months`;
  if (unit === "years") return `${value.toFixed(2)} yrs`;
  return num(Number(value.toFixed(2)));
}

export default function FinancePage() {
  const [tab, setTab] = useState<"metrics" | "calc">("metrics");

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Sigma}
        eyebrow="Deterministic Finance Engine"
        title="Finance"
        description="Every figure is computed by a tested formula, not a language model — with the formula and its inputs shown."
      />

      <div className="mb-6 flex gap-2">
        {(
          [
            { id: "metrics", label: "Company metrics", icon: Gauge },
            { id: "calc", label: "Calculator", icon: Calculator },
          ] as const
        ).map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-semibold transition ${
              tab === t.id
                ? "border-accent bg-accent text-bg"
                : "border-hairline bg-panel text-dim hover:border-accent/40 hover:text-white"
            }`}
          >
            <t.icon size={13} /> {t.label}
          </button>
        ))}
      </div>

      <div key={tab} className="animate-section">
        {tab === "metrics" ? <CompanyMetrics /> : <FormulaCalculator />}
      </div>
    </div>
  );
}

function CompanyMetrics() {
  const [data, setData] = useState<Battery | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<Battery>("/finance/metrics")
      .then(setData)
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Unable to load metrics."),
      )
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingCard message="Running the finance engine…" />;
  if (error || !data)
    return <ErrorCard title="Finance metrics unavailable" message={error} />;

  const h = data.headline;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile label="Revenue" value={inr(h.revenue)} tone="stable" />
        <StatTile label="Expenses" value={inr(h.expenses)} tone="elevated" />
        <StatTile
          label="Profit"
          value={inr(h.profit)}
          delta={`${h.operating_margin_pct.toFixed(1)}% operating margin`}
          deltaTone={h.operating_margin_pct >= 0 ? "stable" : "critical"}
          tone="live"
        />
        <StatTile
          label="Months of data"
          value={num(h.months_of_data)}
          delta={`${num(h.active_customers)} active customers`}
          tone="live"
        />
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        {Object.entries(data.sections).map(([key, rows]) => (
          <Panel key={key} label="Computed" title={SECTION_LABELS[key] ?? key} tone="live">
            <div className="space-y-2">
              {rows.map((m) => (
                <div
                  key={m.label}
                  className="rounded-lg border border-hairline bg-panel-raised/40 p-3"
                >
                  <div className="flex items-baseline justify-between gap-3">
                    <p className="text-sm font-medium text-white">{m.label}</p>
                    <p
                      className={`num shrink-0 text-sm font-semibold ${
                        m.value === null ? "text-mute" : "text-white"
                      }`}
                    >
                      {fmtUnit(m.value, m.unit)}
                    </p>
                  </div>
                  <p className="num mt-1 text-[0.7rem] text-mute">{m.formula}</p>
                  {m.note && (
                    <p className="mt-1 text-[0.7rem] text-elevated">{m.note}</p>
                  )}
                </div>
              ))}
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function FormulaCalculator() {
  const [defs, setDefs] = useState<FormulaDef[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [result, setResult] = useState<{
    label: string;
    value: number | number[] | null;
    unit: string;
    description: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    apiRequest<{ formulas: FormulaDef[] }>("/finance/formulas")
      .then((d) => {
        setDefs(d.formulas);
        setSelected(d.formulas[0]?.key ?? "");
      })
      .catch((e) =>
        setError(e instanceof Error ? e.message : "Unable to load formulas."),
      );
  }, []);

  const current = useMemo(
    () => defs.find((d) => d.key === selected),
    [defs, selected],
  );

  const grouped = useMemo(() => {
    const g: Record<string, FormulaDef[]> = {};
    for (const d of defs) (g[d.category] ??= []).push(d);
    return g;
  }, [defs]);

  useEffect(() => {
    setInputs({});
    setResult(null);
    setError("");
  }, [selected]);

  async function calculate(e: FormEvent) {
    e.preventDefault();
    if (!current) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const payload: Record<string, unknown> = {};
      for (const p of current.params) {
        const raw = inputs[p.name];
        if (raw === undefined || raw === "") continue;
        payload[p.name] = raw;
      }
      const res = await apiRequest<{
        label: string;
        value: number | number[] | null;
        unit: string;
        description: string;
      }>("/finance/calc", {
        method: "POST",
        body: JSON.stringify({ formula: current.key, inputs: payload }),
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Calculation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_320px]">
      <Panel label="Formula" title={current?.label ?? "Calculator"} tone="live">
        <select
          value={selected}
          onChange={(e) => setSelected(e.target.value)}
          className="w-full rounded-lg border border-hairline bg-panel-raised px-3 py-2.5 text-sm outline-none focus:border-accent"
        >
          {Object.entries(grouped).map(([cat, list]) => (
            <optgroup key={cat} label={cat}>
              {list.map((d) => (
                <option key={d.key} value={d.key}>
                  {d.label}
                </option>
              ))}
            </optgroup>
          ))}
        </select>

        {current && (
          <p className="mt-3 text-xs leading-5 text-dim">{current.description}</p>
        )}

        <form onSubmit={calculate} className="mt-4 space-y-3">
          {current?.params.map((p) => (
            <div key={p.name}>
              <label className="eyebrow mb-1 block">
                {p.label}
                {p.kind === "series" && (
                  <span className="ml-1 text-mute">(space or comma separated)</span>
                )}
                {p.kind === "percent" && (
                  <span className="ml-1 text-mute">(as a ratio, e.g. 0.1 = 10%)</span>
                )}
              </label>
              <input
                value={inputs[p.name] ?? ""}
                onChange={(e) =>
                  setInputs((s) => ({ ...s, [p.name]: e.target.value }))
                }
                inputMode={p.kind === "series" ? "text" : "decimal"}
                placeholder={p.kind === "series" ? "e.g. 100 120 90 140" : "0"}
                className="w-full rounded-lg border border-hairline bg-panel-raised px-3 py-2 text-sm outline-none focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
            </div>
          ))}

          <button
            type="submit"
            disabled={busy || !current}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:opacity-60"
          >
            {busy ? <Loader2 size={15} className="animate-spin" /> : <Calculator size={15} />}
            Calculate
          </button>
        </form>

        {error && (
          <div className="mt-4 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
            {error}
          </div>
        )}
      </Panel>

      <Panel label="Result" title="Output" tone={result ? "stable" : "neutral"}>
        {result ? (
          <div>
            <p className="eyebrow">{result.label}</p>
            <p className="num mt-2 text-3xl font-semibold text-white">
              {Array.isArray(result.value)
                ? result.value.map((v) => v.toFixed(2)).join(", ")
                : fmtUnit(result.value as number | null, result.unit)}
            </p>
            <p className="mt-3 text-xs leading-5 text-dim">{result.description}</p>
          </div>
        ) : (
          <p className="text-sm text-mute">
            Pick a formula, fill the inputs, and the deterministic engine returns
            the exact result.
          </p>
        )}
      </Panel>
    </div>
  );
}
