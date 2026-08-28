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
