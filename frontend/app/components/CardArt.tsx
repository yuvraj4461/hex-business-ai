/**
 * CardArt — tiny inline-SVG schematics that sit inside Card3D so the
 * cards read as little instruments, not plain boxes. Uses currentColor
 * so the parent controls the hue.
 */
export type ArtKind =
  | "sparkline"
  | "bars"
  | "flow"
  | "radar"
  | "shield"
  | "ledger"
  | "donut"
  | "route"
  | "lock"
  | "users";

export default function CardArt({
  kind,
  className = "",
}: {
  kind: ArtKind;
  className?: string;
}) {
  const common = {
    viewBox: "0 0 120 48",
    fill: "none",
    className: `h-12 w-full ${className}`,
    "aria-hidden": true as const,
  };
  const stroke = {
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (kind) {
    case "sparkline":
      return (
        <svg {...common}>
          <path d="M2 40 L18 30 L34 34 L50 16 L66 22 L82 8 L98 18 L118 6" {...stroke} />
          <circle cx="118" cy="6" r="2.5" fill="currentColor" />
        </svg>
      );
    case "bars":
      return (
        <svg {...common}>
          {[8, 22, 14, 30, 20, 38, 26].map((h, i) => (
            <rect
              key={i}
              x={4 + i * 17}
              y={46 - h}
              width="10"
              height={h}
              rx="2"
              fill="currentColor"
              opacity={0.35 + i * 0.09}
            />
          ))}
        </svg>
      );
    case "flow":
      return (
        <svg {...common}>
          <path d="M14 24 H54 M66 24 H106" {...stroke} />
          {[14, 60, 106].map((cx) => (
            <circle key={cx} cx={cx} cy="24" r="6" {...stroke} />
          ))}
          <circle cx="60" cy="24" r="3" fill="currentColor" />
        </svg>
      );
    case "radar":
      return (
        <svg {...common}>
          {[6, 12, 18].map((r) => (
            <circle key={r} cx="60" cy="24" r={r} {...stroke} opacity={0.5} />
          ))}
          <path d="M60 24 L60 4" {...stroke} />
          <circle cx="60" cy="24" r="2.5" fill="currentColor" />
          <circle cx="76" cy="14" r="2.5" fill="currentColor" />
        </svg>
      );
    case "shield":
      return (
        <svg {...common}>
          <path d="M60 4 L82 12 V26 C82 38 72 44 60 46 C48 44 38 38 38 26 V12 Z" {...stroke} />
          <path d="M52 24 L58 30 L70 18" {...stroke} />
        </svg>
      );
    case "ledger":
      return (
        <svg {...common}>
          {[10, 20, 30, 40].map((y, i) => (
            <path
              key={y}
              d={`M8 ${y} H${112 - i * 14}`}
              {...stroke}
              opacity={0.8 - i * 0.15}
            />
          ))}
        </svg>
      );
    case "donut":
      return (
        <svg {...common}>
          <circle cx="60" cy="24" r="16" {...stroke} opacity={0.35} />
          <path d="M60 8 A16 16 0 0 1 74 32" {...stroke} />
        </svg>
      );
    case "route":
      return (
        <svg {...common}>
          <path d="M6 38 C30 38 30 10 54 10 S86 38 114 12" {...stroke} strokeDasharray="1 6" />
          {[
            [6, 38],
            [54, 10],
            [114, 12],
          ].map(([cx, cy]) => (
            <circle key={cx} cx={cx} cy={cy} r="3.5" fill="currentColor" />
          ))}
        </svg>
      );
    case "lock":
      return (
        <svg {...common}>
          <rect x="44" y="20" width="32" height="22" rx="3" {...stroke} />
          <path d="M50 20 V14 A10 10 0 0 1 70 14 V20" {...stroke} />
          <circle cx="60" cy="30" r="2.5" fill="currentColor" />
        </svg>
      );
    case "users":
      return (
        <svg {...common}>
          <circle cx="44" cy="18" r="7" {...stroke} />
          <path d="M30 42 C30 30 58 30 58 42" {...stroke} />
          <circle cx="74" cy="20" r="6" {...stroke} opacity={0.6} />
          <path d="M64 42 C64 32 88 32 88 42" {...stroke} opacity={0.6} />
        </svg>
      );
  }
}
