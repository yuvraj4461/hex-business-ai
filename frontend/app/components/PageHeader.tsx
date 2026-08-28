import type { ComponentType, ReactNode } from "react";

import { TONE_ICON_BG, type Tone } from "./tone";

/**
 * PageHeader — the standard heading block: an icon chip, a
 * wide-tracked eyebrow, the page title and a short description,
 * with an optional actions slot on the right.
 */
export default function PageHeader({
  icon: Icon,
  tone = "live",
  eyebrow,
  title,
  description,
  actions,
}: {
  icon?: ComponentType<{ size?: number; className?: string }>;
  tone?: Tone;
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          {Icon && (
            <span
              className={`grid h-12 w-12 shrink-0 place-items-center rounded-xl ${TONE_ICON_BG[tone]}`}
            >
              <Icon size={22} />
            </span>
          )}

          <div>
            {eyebrow && <p className="eyebrow text-accent/90">{eyebrow}</p>}

            <h1 className="mt-1.5 text-[1.7rem] font-semibold tracking-tight text-white sm:text-[2rem]">
              {title}
            </h1>
          </div>
        </div>

        {actions && (
          <div className="flex flex-wrap items-center gap-3">
            {actions}
          </div>
        )}
      </div>

      {description && (
        <p className="mt-3 max-w-3xl text-sm text-dim">{description}</p>
      )}
    </div>
  );
}
