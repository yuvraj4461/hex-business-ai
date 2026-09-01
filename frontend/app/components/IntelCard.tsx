"use client";

import { useRef, type ReactNode } from "react";

import { TONE_RAIL, type Tone } from "./tone";

/**
 * IntelCard — a bounded, internally-scrolling dashboard panel with a
 * subtle 3D hover tilt and a pointer-following violet glow (same family
 * as Card3D, but tuned down so reading a scrolling list is not disturbed).
 *
 * The card never grows past `maxHeight` (default 70vh); its header stays
 * pinned and the body scrolls. Several IntelCards sit side by side in a
 * grid so the whole intelligence picture fits one screen.
 */
export default function IntelCard({
  tone = "neutral",
  label,
  title,
  action,
  children,
  className = "",
  bodyClassName = "",
  maxHeight = "70vh",
}: {
  tone?: Tone;
  label?: ReactNode;
  title?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
  maxHeight?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    const rx = (0.5 - py) * 4;
    const ry = (px - 0.5) * 5;
    el.style.transform = `perspective(1200px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`;
    el.style.setProperty("--gx", `${px * 100}%`);
    el.style.setProperty("--gy", `${py * 100}%`);
  }

  function reset() {
    const el = ref.current;
    if (!el) return;
    el.style.transform =
      "perspective(1200px) rotateX(0deg) rotateY(0deg) translateY(0)";
  }

  const hasHeader = Boolean(label || title || action);

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      style={{ transition: "transform 200ms ease", maxHeight }}
      className={`group elevated relative flex min-h-0 flex-col overflow-hidden rounded-xl border border-hairline bg-panel ring-1 ring-inset ring-white/[0.02] ${className}`}
    >
      <span
        aria-hidden
        className={`absolute inset-y-0 left-0 z-20 w-[3px] ${TONE_RAIL[tone]}`}
      />

      {/* pointer-following glow — sits behind the content */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 z-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(520px circle at var(--gx,50%) var(--gy,0%), color-mix(in srgb, var(--accent) 18%, transparent), transparent 60%)",
        }}
      />

      {hasHeader && (
        <div className="relative z-10 flex shrink-0 items-start justify-between gap-4 border-b border-hairline px-5 py-4 sm:px-6">
          <div className="min-w-0">
            {label && <p className="eyebrow">{label}</p>}
            {title && (
              <h2 className="mt-1 text-base font-semibold tracking-tight text-white">
                {title}
              </h2>
            )}
          </div>
          {action && <div className="shrink-0 text-right">{action}</div>}
        </div>
      )}

      <div
        className={`relative z-10 min-h-0 flex-1 overflow-y-auto px-5 py-4 sm:px-6 ${bodyClassName}`}
      >
        {children}
      </div>
    </div>
  );
}
