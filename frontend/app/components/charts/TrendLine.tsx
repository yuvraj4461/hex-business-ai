"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { inrCompact } from "@/lib/format";

import { axisStyle, chartTheme, tooltipStyle } from "./theme";

export interface TrendDatum {
  name: string;
  value: number;
}

/**
 * TrendLine — a value over an ordered (usually time) axis. Companion to
 * BarBreakdown for categorical data.
 */
export default function TrendLine({
  data,
  currency = true,
  height = 260,
}: {
  data: TrendDatum[];
  currency?: boolean;
  height?: number;
}) {
  const format = (v: unknown) =>
    currency ? inrCompact(v) : Number(v ?? 0).toLocaleString("en-IN");

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <defs>
          <linearGradient id="hex-trend-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={chartTheme.accent} stopOpacity={0.35} />
            <stop offset="100%" stopColor={chartTheme.accent} stopOpacity={0} />
          </linearGradient>
        </defs>

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
          cursor={{ stroke: chartTheme.hairline }}
          formatter={(v) => [format(v), ""] as [string, string]}
        />

        <Area
          type="monotone"
          dataKey="value"
          stroke={chartTheme.accent}
          strokeWidth={2}
          fill="url(#hex-trend-fill)"
          dot={{ r: 2, fill: chartTheme.accent }}
          activeDot={{ r: 4 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
