import type { ReactNode } from "react";

import { TONE_RAIL, type Tone } from "./tone";

/**
 * Panel — the signature HEX surface. A panel on the dark navy
 * ground with a thin colour rail on its leading edge that
 * encodes its state at a glance.
 */
export default function Panel({
  tone = "neutral",
  label,
  title,
  action,
  className = "",
  bodyClassName = "",
  children,
}: {
  tone?: Tone;
  label?: ReactNode;
  title?: ReactNode;
  action?: ReactNode;
  className?: string;
  bodyClassName?: string;
  children: ReactNode;
}) {
  const hasHeader = Boolean(label || title || action);

  return (
    <div
      className={`elevated relative overflow-hidden rounded-xl border border-hairline bg-panel ring-1 ring-inset ring-white/[0.02] ${className}`}
    >
      <span
        aria-hidden
        className={`absolute inset-y-0 left-0 w-[3px] ${TONE_RAIL[tone]}`}
      />

      <div className={`px-5 py-5 sm:px-6 ${bodyClassName}`}>
        {hasHeader && (
          <div className="mb-4 flex items-start justify-between gap-4">
            <div className="min-w-0">
              {label && <p className="eyebrow">{label}</p>}

              {title && (
                <h2 className="mt-1 text-base font-semibold tracking-tight text-white">
                  {title}
                </h2>
              )}
            </div>

            {action && <div className="shrink-0">{action}</div>}
          </div>
        )}

        {children}
      </div>
    </div>
  );
}
