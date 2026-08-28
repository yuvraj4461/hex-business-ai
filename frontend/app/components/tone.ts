/**
 * Tone is how HEX encodes state as colour. It is deliberately
 * small: in a risk system colour has to mean something.
 *
 *   critical  red    — needs action now
 *   elevated  amber  — watch closely
 *   stable    teal   — healthy / nominal
 *   live      cyan   — live data / informational
 *   neutral   —      — no state
 */
export type Tone =
  | "critical"
  | "elevated"
  | "stable"
  | "live"
  | "neutral";

export const TONE_RAIL: Record<Tone, string> = {
  critical: "bg-critical",
  elevated: "bg-elevated",
  stable: "bg-stable",
  live: "bg-live",
  neutral: "bg-hairline",
};

export const TONE_TEXT: Record<Tone, string> = {
  critical: "text-critical",
  elevated: "text-elevated",
  stable: "text-stable",
  live: "text-live",
  neutral: "text-dim",
};

export const TONE_ICON_BG: Record<Tone, string> = {
  critical: "bg-critical/10 text-critical",
  elevated: "bg-elevated/10 text-elevated",
  stable: "bg-stable/10 text-stable",
  live: "bg-live/10 text-live",
  neutral: "bg-panel-raised text-dim",
};

export const TONE_BADGE: Record<Tone, string> = {
  critical: "bg-critical/12 text-critical ring-1 ring-critical/25",
  elevated: "bg-elevated/12 text-elevated ring-1 ring-elevated/25",
  stable: "bg-stable/12 text-stable ring-1 ring-stable/25",
  live: "bg-live/12 text-live ring-1 ring-live/25",
  neutral: "bg-panel-raised text-dim ring-1 ring-hairline",
};

/**
 * Map any raw status/severity string coming from the backend
 * to a tone. Covers global-event severities, route risk levels,
 * agent status and approval status.
 */
export function toneForStatus(raw: string | null | undefined): Tone {
  const value = (raw ?? "").toUpperCase();

  if (
    [
      "HIGH",
      "CRITICAL",
      "SEVERE",
      "UNAVAILABLE",
      "FAILED",
      "REJECTED",
      "OFFLINE",
    ].includes(value)
  ) {
    return "critical";
  }

  if (
    [
      "MEDIUM",
      "MODERATE",
      "ELEVATED",
      "DEGRADED",
      "WARNING",
      "PARTIAL",
      "AWAITING REVIEW",
      "PENDING",
    ].includes(value)
  ) {
    return "elevated";
  }

  if (
    [
      "LOW",
      "STABLE",
      "READY",
      "OK",
      "ACTIVE",
      "ONLINE",
      "APPROVED",
      "OPERATIONAL",
      "HEALTHY",
    ].includes(value)
  ) {
    return "stable";
  }

  if (["INFO", "LIVE", "NEW"].includes(value)) {
    return "live";
  }

  return "neutral";
}
