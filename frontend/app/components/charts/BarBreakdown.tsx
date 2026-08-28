"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { inrCompact } from "@/lib/format";

import { axisStyle, chartTheme, tooltipStyle } from "./theme";

export interface BreakdownDatum {
  name: string;
  value: number;
  color?: string;
}

/**
 * BarBreakdown — a categorical composition, e.g. revenue vs
 * expenses vs profit. Not a time series.
 */
export default function BarBreakdown({
  data,
  currency = true,
  height = 260,
}: {
  data: BreakdownDatum[];
  currency?: boolean;
  height?: number;
}) {
  const format = (v: unknown) =>
    currency ? inrCompact(v) : Number(v ?? 0).toLocaleString("en-IN");

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <CartesianGrid
          stroke={chartTheme.hairline}
          strokeDasharray="3 3"
          vertical={false}
        />

        <XAxis
          dataKey="name"
          tick={axisStyle}
          axisLine={{ stroke: chartTheme.hairline }}
          tickLine={false}
        />

        <YAxis
          tick={axisStyle}
          axisLine={false}
          tickLine={false}
          tickFormatter={format}
          width={64}
        />

        <Tooltip
          contentStyle={tooltipStyle}
          cursor={{ fill: chartTheme.hairline, opacity: 0.3 }}
          formatter={(v) => [format(v), ""] as [string, string]}
        />

        <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={72}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.color ?? chartTheme.accent} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
