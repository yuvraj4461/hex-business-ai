import Link from "next/link";

import {
  ArrowRight,
  Check,
  FileClock,
  KeyRound,
  Lock,
  Network,
  ScrollText,
  UserCheck,
  Users,
} from "lucide-react";

import Card3D from "@/app/components/Card3D";
import MarketingNav from "@/app/components/MarketingNav";
import MarketingFooter from "@/app/components/MarketingFooter";

export const metadata = {
  title: "HEX for Enterprise",
  description:
    "Role-based access, encrypted credentials, full audit logging, tenant isolation and human-in-the-loop approvals.",
};

const PILLARS = [
  {
    icon: Users,
    title: "Role-based access control",
    body: "Six built-in roles — Super Admin, Data Admin, Analyst, Business User, Decision Maker, External Partner — each mapped to granular permissions (manage data, run analysis, approve recommendations, view audit logs).",
  },
  {
    icon: KeyRound,
    title: "Encrypted credentials at rest",
    body: "Connection secrets (database passwords, API tokens) are stored only as Fernet ciphertext — never in plaintext columns, never written to logs. Bring your own key via HEX_SECRET_KEY.",
  },
  {
    icon: FileClock,
    title: "Full audit trail",
    body: "Every data mutation, sync and intelligence refresh writes an audit record: who, what action, which entity, and when. Queryable by users with the view_audit_logs permission.",
  },
  {
    icon: Network,
    title: "Tenant isolation",
    body: "Every record is scoped to an organization. Users only ever see and act on their own organization's suppliers, routes, finances and events.",
  },
  {
    icon: UserCheck,
    title: "Human-in-the-loop",
    body: "HEX provides decision support, not autonomy. High-impact operational decisions require an authorized human to approve or reject — and that decision is recorded.",
  },
  {
    icon: Lock,
    title: "Your infrastructure",
    body: "Deploy the API as a container or native service, backed by your own Postgres. Front end and back end are separable; nothing is locked to a vendor.",
  },
];

export default function EnterprisePage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-bg">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-48 right-0 h-[40rem] w-[40rem] rounded-full bg-accent/15 blur-[150px]"
      />

      <MarketingNav />

      <div className="relative mx-auto max-w-6xl px-6">
        <section className="grid items-center gap-10 pt-14 pb-16 sm:pt-20 lg:grid-cols-2">
          <div>
            <p className="eyebrow text-accent/90">Enterprise</p>
            <h1 className="display mt-4 text-4xl text-white sm:text-6xl">
              Built for scale, security and control.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-dim">
              Connect your data, provision users, and keep a record of every
              decision — with access control, encryption and auditing built in
              from the model layer up.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-3 text-sm font-semibold text-bg transition hover:bg-accent/90"
              >
                Get started
                <ArrowRight size={16} />
              </Link>
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-5 py-3 text-sm font-semibold text-dim transition hover:text-white"
              >
                Get in touch
              </Link>
            </div>
          </div>

          <div className="grid gap-3 rounded-2xl border border-hairline bg-panel p-6">
            {[
              "Granular role → permission mapping",
              "Fernet-encrypted connection credentials",
              "Append-only audit log of every action",
              "Per-organization data isolation",
              "Approval gate on high-impact decisions",
              "Self-hostable API + bring-your-own database",
            ].map((line) => (
              <div key={line} className="flex gap-3 text-sm text-dim">
                <Check size={16} className="mt-0.5 shrink-0 text-stable" />
                {line}
              </div>
            ))}
          </div>
        </section>

        <section className="pb-16">
          <p className="eyebrow">Governance &amp; control</p>
          <h2 className="display mt-3 text-2xl text-white sm:text-3xl">
            Every layer accounts for who did what
          </h2>
          <div className="mt-7 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {PILLARS.map(({ icon: Icon, title, body }) => (
              <Card3D key={title}>
                <span className="grid h-10 w-10 place-items-center rounded-lg bg-accent/10 text-accent">
                  <Icon size={18} />
                </span>
                <h3 className="mt-3 font-semibold text-white">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-dim">{body}</p>
              </Card3D>
            ))}
          </div>
        </section>

        <section className="mb-20 grid items-start gap-8 rounded-2xl border border-hairline bg-panel p-8 lg:grid-cols-2">
          <div>
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-live/10 text-live">
              <ScrollText size={20} />
            </span>
            <h2 className="display mt-4 text-2xl text-white">
              Integration without lock-in
            </h2>
            <p className="mt-3 text-sm leading-7 text-dim">
              HEX connects to your systems and keeps a canonical copy of what it
              needs — it is not where your data has to live. Use the file
              upload and SQL-source adapters today, or the unified accounting
              connector; the adapter layer is the seam for adding more.
            </p>
          </div>
          <ul className="space-y-3">
            {[
              "File upload — CSV / Excel per entity",
              "SQL source — read-replica of your database",
              "Unified accounting connector (Merge.dev)",
              "Webhooks for push-based sync",
              "Scheduled background sync per connection",
            ].map((p) => (
              <li key={p} className="flex gap-3 text-sm text-dim">
                <Check size={16} className="mt-0.5 shrink-0 text-stable" />
                {p}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <MarketingFooter />
    </main>
  );
}
