"use client";

import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

import { chartTheme, tooltipStyle } from "./theme";

const SEVERITY_COLOR: Record<string, string> = {
  HIGH: chartTheme.critical,
  CRITICAL: chartTheme.critical,
  MEDIUM: chartTheme.elevated,
  ELEVATED: chartTheme.elevated,
  LOW: chartTheme.stable,
  INFO: chartTheme.live,
};

/**
 * SeverityDonut — distribution of items by severity string.
 */
export default function SeverityDonut({
  items,
  height = 220,
}: {
  items: { severity?: string }[];
  height?: number;
}) {
  const counts = new Map<string, number>();

  for (const item of items) {
    const key = (item.severity ?? "UNKNOWN").toUpperCase();
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }

  const data = [...counts.entries()].map(([name, value]) => ({
    name,
    value,
  }));

  if (data.length === 0) {
    return (
      <div className="grid h-[220px] place-items-center text-sm text-mute">
        No events to chart.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          innerRadius={52}
          outerRadius={78}
          paddingAngle={2}
          stroke={chartTheme.panel}
        >
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={SEVERITY_COLOR[d.name] ?? chartTheme.mute}
            />
          ))}
        </Pie>

        <Tooltip contentStyle={tooltipStyle} />

        <Legend
          verticalAlign="middle"
          align="right"
          layout="vertical"
          iconType="circle"
          formatter={(value) => (
            <span style={{ color: chartTheme.dim, fontSize: 12 }}>
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
