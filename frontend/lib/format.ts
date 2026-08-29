/**
 * Number + currency formatting for HEX.
 *
 * The app is India-facing: currency is INR, grouping is the
 * Indian system (`en-IN`). These helpers replace the
 * `₹ + toLocaleString("en-IN")` pattern that was copy-pasted
 * across ~15 components.
 */

function toNumber(value: unknown): number {
  const n = typeof value === "number" ? value : Number(value ?? 0);
  return Number.isFinite(n) ? n : 0;
}

/** Plain integer-ish number with Indian grouping. */
export function num(value: unknown): string {
  return toNumber(value).toLocaleString("en-IN");
}

/** Currency in INR, e.g. "₹12,34,567". */
export function inr(value: unknown): string {
  return `₹${num(value)}`;
}

/** Compact currency for tight spaces, e.g. "₹1.2Cr", "₹45.0L". */
export function inrCompact(value: unknown): string {
  const n = Math.abs(toNumber(value));
  const sign = toNumber(value) < 0 ? "-" : "";

  if (n >= 1_00_00_000) {
    return `${sign}₹${(n / 1_00_00_000).toFixed(1)}Cr`;
  }

  if (n >= 1_00_000) {
    return `${sign}₹${(n / 1_00_000).toFixed(1)}L`;
  }

  if (n >= 1_000) {
    return `${sign}₹${(n / 1_000).toFixed(1)}K`;
  }

  return `${sign}₹${num(n)}`;
}

/** Signed percentage, e.g. "+2.35%" / "-1.04%". */
export function signedPercent(value: unknown, digits = 2): string {
  const n = toNumber(value);
  return `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`;
}

/** Compact relative time, e.g. "just now", "6m ago", "3h ago", "2d ago". */
export function timeAgo(iso?: string | null): string {
  if (!iso) return "never";
  const secs = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (!Number.isFinite(secs)) return "never";
  if (secs < 60) return "just now";
  if (secs < 3600) return `${Math.round(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.round(secs / 3600)}h ago`;
  return `${Math.round(secs / 86400)}d ago`;
}
