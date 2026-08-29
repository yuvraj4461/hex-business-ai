import {
  BarChart3,
  Bot,
  Globe,
  LayoutDashboard,
  Plug,
  Route,
  ShieldAlert,
  Sparkles,
  Stamp,
  Target,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  description: string;
  group: NavGroup;
}

export type NavGroup = "Command" | "Intelligence" | "Operations" | "Decisions";

export const NAV_GROUPS: NavGroup[] = [
  "Command",
  "Intelligence",
  "Operations",
  "Decisions",
];

/** Single source of truth for navigation — sidebar + Platform mega-menu. */
export const NAV_ITEMS: NavItem[] = [
  {
    name: "Command Center",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Business, operations and global intelligence on one panel",
    group: "Command",
  },
  {
    name: "Global Intelligence",
    href: "/global",
    icon: Globe,
    description: "Live disruption feed, markets, agriculture and FX signals",
    group: "Intelligence",
  },
  {
    name: "Risk Center",
    href: "/risk",
    icon: ShieldAlert,
    description: "Turn an event into supplier, route and financial exposure",
    group: "Intelligence",
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
    description: "Revenue, cost and performance trends for your business",
    group: "Intelligence",
  },
  {
    name: "Supply Routes",
    href: "/routes",
    icon: Route,
    description: "Lanes, corridors and shipments across your supply chain",
    group: "Operations",
  },
  {
    name: "Integrations",
    href: "/integrations",
    icon: Plug,
    description: "Connect an ERP or accounting system, or upload files",
    group: "Operations",
  },
  {
    name: "Scenarios",
    href: "/scenarios",
    icon: Target,
    description: "Simulate a disruption and compare route decisions",
    group: "Decisions",
  },
  {
    name: "Agents",
    href: "/agents",
    icon: Bot,
    description: "The five-agent graph: finance, sales, ops, watch, risk",
    group: "Decisions",
  },
  {
    name: "AI Copilot",
    href: "/copilot",
    icon: Sparkles,
    description: "Ask HEX — grounded in live web research and your data",
    group: "Decisions",
  },
  {
    name: "Approvals",
    href: "/approvals",
    icon: Stamp,
    description: "Record human decisions on HEX recommendations",
    group: "Decisions",
  },
];

export function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}
