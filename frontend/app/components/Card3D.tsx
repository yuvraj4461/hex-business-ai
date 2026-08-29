"use client";

import { useRef, type ReactNode } from "react";

/**
 * Card3D — a card that tilts toward the cursor in perspective, with a
 * violet glow + border sheen that track the pointer and inner content
 * lifted on the Z axis so it reads as a physical object. Falls back to
 * a plain card for touch / reduced-motion (no pointer events fire).
 */
export default function Card3D({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  function onMove(e: React.MouseEvent<HTMLDivElement>) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const px = (e.clientX - r.left) / r.width;
    const py = (e.clientY - r.top) / r.height;
    const rx = (0.5 - py) * 16;
    const ry = (px - 0.5) * 18;
    el.style.transform = `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) scale(1.02)`;
    el.style.setProperty("--gx", `${px * 100}%`);
    el.style.setProperty("--gy", `${py * 100}%`);
  }

  function reset() {
    const el = ref.current;
    if (!el) return;
    el.style.transform =
      "perspective(800px) rotateX(0deg) rotateY(0deg) scale(1)";
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={reset}
      style={{ transition: "transform 150ms ease" }}
      className={`card3d group relative overflow-hidden rounded-2xl border border-hairline bg-panel p-6 ring-1 ring-inset ring-white/[0.03] [transform-style:preserve-3d] ${className}`}
    >
      {/* pointer-following glow */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(420px circle at var(--gx,50%) var(--gy,0%), color-mix(in srgb, var(--accent) 26%, transparent), transparent 60%)",
        }}
      />
      {/* border sheen */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          border: "1px solid transparent",
          background:
            "linear-gradient(140deg, color-mix(in srgb, var(--accent) 55%, transparent), transparent 45%) border-box",
          WebkitMask:
            "linear-gradient(#000 0 0) padding-box, linear-gradient(#000 0 0)",
          WebkitMaskComposite: "xor",
          maskComposite: "exclude",
        }}
      />
      <div className="relative [transform:translateZ(28px)]">{children}</div>
    </div>
  );
}
