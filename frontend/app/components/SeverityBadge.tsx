import { TONE_BADGE, toneForStatus, type Tone } from "./tone";

/**
 * SeverityBadge — a small pill that names a state and colours
 * it by tone. Pass the raw backend string; tone is derived.
 */
export default function SeverityBadge({
  value,
  tone,
  className = "",
}: {
  value: string | null | undefined;
  tone?: Tone;
  className?: string;
}) {
  const resolved = tone ?? toneForStatus(value);
  const label = (value ?? "UNKNOWN").toString().toUpperCase();

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[0.6875rem] font-semibold tracking-wide ${TONE_BADGE[resolved]} ${className}`}
    >
      {label}
    </span>
  );
}
