/**
 * HEX mark — an original layered-hexagon glyph. Deliberately not the
 * pixel-block wordmark of the unrelated hex.tech; this is a geometric
 * hexagon with an inner cut, in the violet brand accent.
 */
export default function Logo({
  size = 28,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  const id = "hexgrad";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      aria-hidden
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="32" y2="32">
          <stop offset="0" stopColor="#8b7cf6" />
          <stop offset="1" stopColor="#6d5ae8" />
        </linearGradient>
      </defs>

      {/* outer hexagon */}
      <path
        d="M16 2.5 27.7 9.25 27.7 22.75 16 29.5 4.3 22.75 4.3 9.25Z"
        stroke={`url(#${id})`}
        strokeWidth="2.2"
        strokeLinejoin="round"
      />

      {/* inner hexagon, solid */}
      <path
        d="M16 10 21.2 13 21.2 19 16 22 10.8 19 10.8 13Z"
        fill={`url(#${id})`}
      />
    </svg>
  );
}

/** Mark + wordmark lockup. */
export function Wordmark({
  size = 28,
  subtitle = "Command Center",
}: {
  size?: number;
  subtitle?: string | null;
}) {
  return (
    <div className="flex items-center gap-2.5">
      <Logo size={size} />
      <div className="leading-none">
        <p className="text-[0.95rem] font-bold tracking-[0.14em] text-white">
          HEX
        </p>
        {subtitle && (
          <p className="mt-1 text-[0.6rem] font-semibold uppercase tracking-[0.16em] text-dim">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}
