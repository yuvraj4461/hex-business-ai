"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { axisStyle, chartTheme, tooltipStyle } from "./theme";

export interface TrendDay {
  date: string;
  CRITICAL?: number;
  HIGH?: number;
  MEDIUM?: number;
  LOW?: number;
  INFO?: number;
  total?: number;
}

const SERIES: { key: keyof TrendDay; label: string; color: string }[] = [
  { key: "CRITICAL", label: "Critical", color: chartTheme.critical },
  { key: "HIGH", label: "High", color: "#f97362" },
  { key: "MEDIUM", label: "Medium", color: chartTheme.elevated },
  { key: "LOW", label: "Low", color: chartTheme.live },
  { key: "INFO", label: "Info", color: chartTheme.mute },
];

function shortDate(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/**
 * IncidentTrend — stacked bars of detected incidents per day,
 * coloured by severity. The headline visual for World Watch.
 */
export default function IncidentTrend({
  data,
  height = 300,
}: {
  data: TrendDay[];
  height?: number;
}) {
  const empty =
    data.length === 0 || data.every((d) => (d.total ?? 0) === 0);

  if (empty) {
    return (
      <div
        className="grid place-items-center rounded-lg bg-panel-raised/40 text-sm text-mute"
        style={{ height }}
      >
        No incidents detected in this window yet.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        margin={{ top: 8, right: 8, bottom: 0, left: 0 }}
        barCategoryGap="18%"
      >
        <CartesianGrid
          stroke={chartTheme.hairline}
          strokeDasharray="3 3"
          vertical={false}
        />

        <XAxis
          dataKey="date"
          tickFormatter={shortDate}
          tick={axisStyle}
          axisLine={{ stroke: chartTheme.hairline }}
          tickLine={false}
          interval="preserveStartEnd"
          minTickGap={16}
        />

        <YAxis
          allowDecimals={false}
          tick={axisStyle}
          axisLine={false}
          tickLine={false}
          width={36}
        />

        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ fill: chartTheme.hairline, opacity: 0.25 }}
          labelFormatter={(v) => shortDate(String(v))}
        />

        <Legend
          iconType="circle"
          formatter={(value) => (
            <span style={{ color: chartTheme.dim, fontSize: 12 }}>{value}</span>
          )}
        />

        {SERIES.map((s) => (
          <Bar
            key={s.key as string}
            dataKey={s.key as string}
            name={s.label}
            stackId="sev"
            fill={s.color}
            radius={s.key === "CRITICAL" ? [3, 3, 0, 0] : undefined}
            maxBarSize={40}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
