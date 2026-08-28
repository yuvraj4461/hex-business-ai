/**
 * Concrete colour values for recharts (it needs real colours,
 * not CSS custom properties). Mirrors the tokens in globals.css.
 */
export const chartTheme = {
  bg: "#0a1120",
  panel: "#0f1a2e",
  hairline: "#223252",
  text: "#e9edf6",
  dim: "#97a6c2",
  mute: "#5f6f8d",

  critical: "#fb5c74",
  elevated: "#f5a524",
  stable: "#2dd4bf",
  live: "#8b7cf6",
  accent: "#7c6df5",
};

/** Categorical series — violet-forward, matches the brand accent. */
export const chartSeries = [
  "#7c6df5",
  "#a78bfa",
  "#5b8def",
  "#38bdf8",
  "#c4b5fd",
  "#2dd4bf",
];

export const tooltipStyle = {
  backgroundColor: chartTheme.panel,
  border: `1px solid ${chartTheme.hairline}`,
  borderRadius: 10,
  color: chartTheme.text,
  fontSize: 12,
} as const;

export const axisStyle = {
  fill: chartTheme.mute,
  fontSize: 11,
} as const;
