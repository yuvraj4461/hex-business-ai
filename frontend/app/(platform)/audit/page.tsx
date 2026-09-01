"use client";

import { useEffect, useState } from "react";

import { ScrollText } from "lucide-react";

import { apiRequest } from "@/lib/api";
import { timeAgo } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import { EmptyCard, ErrorCard, LoadingCard } from "@/app/components/StateCard";

interface AuditRow {
  id: number;
  action: string;
  entity_type: string;
  entity_id?: number | null;
  description?: string | null;
  user: string;
  created_at?: string | null;
}

export default function AuditPage() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    try {
      setLoading(true);
      setError("");
      setRows(await apiRequest<AuditRow[]>("/audit-logs?limit=100"));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load the audit log.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch
    load();
  }, []);

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading audit log…" />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={ScrollText}
        tone="live"
        eyebrow="Governance"
        title="Audit Log"
        description="An append-only record of every action taken in your organization — who, what, and when."
      />

      {error ? (
        <ErrorCard
          title="Audit log unavailable"
          message={
            error.includes("permission") || error.includes("403")
              ? "Your role does not include the view_audit_logs permission."
              : error
          }
          onRetry={load}
        />
      ) : rows.length === 0 ? (
        <EmptyCard message="No audit records yet." />
      ) : (
        <Panel label="Recent activity" title={`${rows.length} events`}>
          <div className="max-h-[65vh] overflow-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 z-10 bg-panel">
                <tr className="border-b border-hairline">
                  {["When", "Actor", "Action", "Entity", "Detail"].map((h) => (
                    <th key={h} className="eyebrow bg-panel px-3 py-2.5 font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-hairline last:border-0"
                  >
                    <td className="num px-3 py-3 text-mute">
                      {timeAgo(r.created_at)}
                    </td>
                    <td className="px-3 py-3 text-white">{r.user}</td>
                    <td className="num px-3 py-3">{r.action}</td>
                    <td className="num px-3 py-3 text-dim">
                      {r.entity_type}
                      {r.entity_id ? ` #${r.entity_id}` : ""}
                    </td>
                    <td className="px-3 py-3 text-dim">
                      {r.description ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
