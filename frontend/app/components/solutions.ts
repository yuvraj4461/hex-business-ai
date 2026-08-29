import {
  Boxes,
  Building2,
  LineChart,
  ShieldAlert,
  Truck,
  type LucideIcon,
} from "lucide-react";

export interface Solution {
  slug: string;
  role: string;
  href: string;
  icon: LucideIcon;
  tagline: string;
  body: string;
  points: string[];
}

/** By-team solutions — what HEX does for each kind of user. */
export const SOLUTIONS: Solution[] = [
  {
    slug: "procurement",
    role: "Procurement & supply chain",
    href: "/risk",
    icon: Boxes,
    tagline: "Know which orders are exposed before the delay lands.",
    body: "HEX matches every live disruption to your suppliers, lanes and open purchase orders, so you see the shipments at risk — not just the headlines.",
    points: [
      "Per-event exposure across suppliers, routes and open POs",
      "Corridor matching (Red Sea, Suez, Hormuz, Panama, Taiwan…)",
      "Shipments projected from POs and kept in sync",
    ],
  },
  {
    slug: "finance",
    role: "Finance",
    href: "/analytics",
    icon: LineChart,
    tagline: "Put a rupee figure on every disruption.",
    body: "The Finance agent establishes your money baseline; the Risk agent converts exposure into cost impact and revenue at risk so you can protect margin.",
    points: [
      "Revenue, expense and profit trends kept current",
      "Cost impact and revenue-at-risk per scenario",
      "Financial trade-off on every reroute decision",
    ],
  },
  {
    slug: "operations",
    role: "Operations & logistics",
    href: "/scenarios",
    icon: Truck,
    tagline: "Compare reroute options with the numbers attached.",
    body: "Simulate a disruption and HEX lays out the alternatives — transit days, freight cost and risk level — with an AI recommendation and a human approval step.",
    points: [
      "Alternative-route engine with transit and freight",
      "Scenario simulation for any detected event",
      "Approvals: high-impact decisions need a human sign-off",
    ],
  },
  {
    slug: "risk",
    role: "Risk & resilience",
    href: "/global",
    icon: ShieldAlert,
    tagline: "A standing watch on the events that move supply chains.",
    body: "World Watch continuously collects disasters, conflict, tariffs, freight and FX signals, scores them, and recomputes your exposure automatically.",
    points: [
      "Always-on collection: GDELT, web search, FX, commodities",
      "Severity scoring and noise filtering",
      "Auto-recompute of exposure on new high-severity events",
    ],
  },
  {
    slug: "leadership",
    role: "Leadership",
    href: "/dashboard",
    icon: Building2,
    tagline: "One command center for business health and world risk.",
    body: "The Command Center puts your finances, operations and the global picture on one panel, with a live headline ticker and an AI copilot a click away.",
    points: [
      "Executive KPIs with live global-event feed",
      "Copilot grounded in web research + your data",
      "Five specialist agents reasoning together",
    ],
  },
];
