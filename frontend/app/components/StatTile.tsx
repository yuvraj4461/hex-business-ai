import type { ComponentType, ReactNode } from "react";

import { TONE_ICON_BG, TONE_RAIL, TONE_TEXT, type Tone } from "./tone";

/**
 * StatTile — a single reading on the instrument panel. The
 * value renders in Geist Mono with tabular figures.
 */
export default function StatTile({
  label,
  value,
  unit,
  delta,
  deltaTone,
  icon: Icon,
  tone = "neutral",
}: {
  label: ReactNode;
  value: ReactNode;
  unit?: ReactNode;
  delta?: ReactNode;
  deltaTone?: Tone;
  icon?: ComponentType<{ size?: number; className?: string }>;
  tone?: Tone;
}) {
  return (
    <div className="elevated relative overflow-hidden rounded-xl border border-hairline bg-panel p-5 ring-1 ring-inset ring-white/[0.02]">
      <span
        aria-hidden
        className={`absolute inset-y-0 left-0 w-[3px] ${TONE_RAIL[tone]}`}
      />

      <div className="flex items-start justify-between">
        <p className="eyebrow">{label}</p>

        {Icon && (
          <span
            className={`grid h-8 w-8 place-items-center rounded-lg ${TONE_ICON_BG[tone]}`}
          >
            <Icon size={16} />
          </span>
        )}
      </div>

      <div className="mt-4 flex items-baseline gap-1.5">
        <span className="num text-2xl font-semibold tracking-tight text-white">
          {value}
        </span>

        {unit && (
          <span className="text-xs text-mute">{unit}</span>
        )}
      </div>

      {delta != null && (
        <p
          className={`num mt-1 text-xs ${
            deltaTone ? TONE_TEXT[deltaTone] : "text-dim"
          }`}
        >
          {delta}
        </p>
      )}
    </div>
  );
}
