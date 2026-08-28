"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  Database,
  FileSpreadsheet,
  Loader2,
  Plug,
  RefreshCw,
  Ship,
  Trash2,
  Upload,
  Zap,
} from "lucide-react";

import { apiRequest } from "@/lib/api";
import { num } from "@/lib/format";

import PageHeader from "@/app/components/PageHeader";
import Panel from "@/app/components/Panel";
import SeverityBadge from "@/app/components/SeverityBadge";
import { ErrorCard, LoadingCard } from "@/app/components/StateCard";
import { toneForStatus, type Tone } from "@/app/components/tone";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface Connection {
  id: number;
  source_type: string;
  display_name: string;
  status: string;
  config: {
    uploads?: Record<string, { filename?: string }>;
    webhook_secret?: string;
    auto_sync?: boolean;
  };
  cursor: Record<string, string>;
  has_credentials: boolean;
  last_sync_at: string | null;
  last_error: string | null;
}

interface ReadinessDomain {
  domain: string;
  status: string;
  detail: string;
  row_count: number;
  synced_row_count: number;
  last_synced_at: string | null;
  sources: string[];
}

interface Readiness {
  overall: string;
  domains: ReadinessDomain[];
}

interface SyncResult {
  rows_written: number;
  errors: string[];
  entities: Record<
    string,
    { fetched: number; inserted: number; updated: number; skipped: number; failed: number }
  >;
}

const ENTITY_TYPES = [
  "supplier",
  "product",
  "purchase_order",
  "purchase_order_line",
  "shipment",
  "inventory",
  "transaction",
  "expense",
];

const readinessTone = (status: string): Tone =>
  status === "READY" ? "stable" : status === "PARTIAL" ? "elevated" : "critical";

export default function IntegrationsPage() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [readiness, setReadiness] = useState<Readiness | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [notice, setNotice] = useState("");
  const [projecting, setProjecting] = useState(false);

  const load = useCallback(async () => {
    try {
      setError("");
      const [conns, ready] = await Promise.all([
        apiRequest<Connection[]>("/connections"),
        apiRequest<Readiness>("/data/readiness"),
      ]);
      setConnections(conns);
      setReadiness(ready);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load integrations.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial fetch
    load();
  }, [load]);

  async function projectShipments() {
    setProjecting(true);
    setNotice("");
    try {
      const r = await apiRequest<{
        created: number;
        updated: number;
        skipped: number;
      }>("/shipments/project", { method: "POST" });
      setNotice(
        `Projected shipments: ${num(r.created)} new, ${num(r.updated)} updated.`,
      );
    } catch (err) {
      setNotice(
        err instanceof Error ? err.message : "Projection failed.",
      );
    } finally {
      setProjecting(false);
    }
  }

  async function toggleAutoSync(conn: Connection) {
    try {
      await apiRequest(`/connections/${conn.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          config: {
            ...conn.config,
            auto_sync: conn.config.auto_sync === false,
          },
        }),
      });
      await load();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Update failed.");
    }
  }

  async function act(
    id: number,
    path: string,
    label: string,
  ) {
    setBusyId(id);
    setNotice("");
    try {
      if (path === "delete") {
        await apiRequest(`/connections/${id}`, { method: "DELETE" });
        setNotice(`${label} done.`);
      } else if (path === "sync") {
        const r = await apiRequest<SyncResult>(
          `/connections/${id}/sync`,
          { method: "POST" },
        );
        setNotice(
          `Sync: ${num(r.rows_written)} rows written` +
            (r.errors.length ? `, ${r.errors.length} errors` : ""),
        );
      } else {
        const r = await apiRequest<{ ok: boolean; message: string }>(
          `/connections/${id}/test`,
          { method: "POST" },
        );
        setNotice(`Test: ${r.message}`);
      }
      await load();
    } catch (err) {
      setNotice(
        err instanceof Error ? err.message : `${label} failed.`,
      );
    } finally {
      setBusyId(null);
    }
  }

  if (loading) {
    return (
      <div className="p-6 lg:p-8">
        <LoadingCard message="Loading integrations…" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 lg:p-8">
        <ErrorCard title="Integrations unavailable" message={error} onRetry={load} />
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8">
      <PageHeader
        icon={Plug}
        eyebrow="Data Integration"
        title="Integrations"
        description="Connect your ERP, accounting or commerce system — or upload spreadsheets — so HEX runs on your real operational data."
        actions={
          <button
            type="button"
            onClick={projectShipments}
            disabled={projecting}
            className="inline-flex items-center gap-2 rounded-lg border border-hairline bg-panel px-3.5 py-2 text-sm font-medium text-dim transition hover:text-white disabled:opacity-60"
          >
            {projecting ? (
              <Loader2 size={15} className="animate-spin" />
            ) : (
              <Ship size={15} />
            )}
            Project shipments from POs
          </button>
        }
      />

      {notice && (
        <div className="mb-6 rounded-lg border border-live/25 bg-live/5 p-3 text-sm text-white">
          {notice}
        </div>
      )}

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          {connections.length === 0 ? (
            <Panel label="Connections" title="No sources connected yet" tone="elevated">
              <p className="text-sm text-dim">
                Add a connection below. Until then, HEX runs on seeded demo
                data only.
              </p>
            </Panel>
          ) : (
            connections.map((c) => (
              <ConnectionCard
                key={c.id}
                conn={c}
                busy={busyId === c.id}
                onAct={act}
                onChanged={load}
                onToggleAutoSync={() => toggleAutoSync(c)}
              />
            ))
          )}

          <AddConnection onCreated={load} />
        </div>

        <Panel
          label="Coverage"
          title="Data Readiness"
          tone={readiness ? readinessTone(readiness.overall) : "neutral"}
        >
          <div className="space-y-2.5">
            {readiness?.domains.map((d) => (
              <div
                key={d.domain}
                className="rounded-lg border border-hairline bg-panel-raised/40 p-3"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium capitalize text-white">
                    {d.domain}
                  </span>
                  <SeverityBadge value={d.status} tone={readinessTone(d.status)} />
                </div>
                <p className="num mt-1 text-xs text-mute">{d.detail}</p>
                {d.sources.length > 0 && (
                  <p className="mt-1 text-xs text-dim">
                    via {d.sources.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function ConnectionCard({
  conn,
  busy,
  onAct,
  onChanged,
  onToggleAutoSync,
}: {
  conn: Connection;
  busy: boolean;
  onAct: (id: number, path: string, label: string) => void;
  onChanged: () => void;
  onToggleAutoSync: () => void;
}) {
  const tone = toneForStatus(conn.status);
  const Icon =
    conn.source_type === "sql"
      ? Database
      : conn.source_type === "merge"
        ? Zap
        : FileSpreadsheet;
  const autoSync = conn.config.auto_sync !== false;
  const webhookUrl = conn.config.webhook_secret
    ? `${API_BASE}/webhooks/connections/${conn.id}`
    : null;

  return (
    <Panel
      tone={tone}
      label={conn.source_type.replace("_", " ")}
      title={
        <span className="flex items-center gap-2">
          <Icon size={16} className="text-dim" />
          {conn.display_name}
        </span>
      }
      action={<SeverityBadge value={conn.status} tone={tone} />}
    >
      <p className="num text-xs text-mute">
        {conn.last_sync_at
          ? `Last sync ${new Date(conn.last_sync_at).toLocaleString()}`
          : "Never synced"}
      </p>

      {conn.last_error && (
        <p className="mt-2 rounded-lg bg-critical/10 p-2 text-xs text-critical">
          {conn.last_error}
        </p>
      )}

      {conn.source_type === "file_upload" && (
        <FileUploadRow connectionId={conn.id} config={conn.config} onDone={onChanged} />
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-hairline pt-3 text-xs">
        <button
          type="button"
          onClick={onToggleAutoSync}
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-semibold transition ${
            autoSync
              ? "bg-stable/12 text-stable ring-1 ring-stable/25"
              : "bg-panel-raised text-mute ring-1 ring-hairline"
          }`}
        >
          <RefreshCw size={12} />
          Auto-sync {autoSync ? "on" : "off"}
        </button>

        {webhookUrl && (
          <button
            type="button"
            onClick={() => {
              navigator.clipboard
                ?.writeText(
                  `${webhookUrl}  (X-HEX-Token: ${conn.config.webhook_secret})`,
                )
                .catch(() => {});
            }}
            className="text-mute underline decoration-dotted hover:text-dim"
            title="Copy webhook URL + token"
          >
            Copy webhook URL
          </button>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => onAct(conn.id, "test", "Test")}
          className="rounded-lg border border-hairline px-3 py-1.5 text-sm text-dim transition hover:text-white disabled:opacity-60"
        >
          Test
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => onAct(conn.id, "sync", "Sync")}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:opacity-60"
        >
          {busy ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <RefreshCw size={14} />
          )}
          Sync now
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => onAct(conn.id, "delete", "Delete")}
          className="inline-flex items-center gap-1.5 rounded-lg border border-critical/30 px-3 py-1.5 text-sm text-critical transition hover:bg-critical/10 disabled:opacity-60"
        >
          <Trash2 size={14} />
          Delete
        </button>
      </div>
    </Panel>
  );
}

function FileUploadRow({
  connectionId,
  config,
  onDone,
}: {
  connectionId: number;
  config: Connection["config"];
  onDone: () => void;
}) {
  const [entity, setEntity] = useState("supplier");
  const [idColumn, setIdColumn] = useState("");
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const uploaded = config.uploads ?? {};

  async function upload() {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setErr("Choose a file first.");
      return;
    }
    setUploading(true);
    setErr("");
    try {
      const form = new FormData();
      form.append("entity_type", entity);
      if (idColumn) form.append("id_column", idColumn);
      form.append("file", file);

      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("hex_token")
          : null;

      const res = await fetch(
        `${API_BASE}/connections/${connectionId}/upload`,
        {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: form,
        },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Upload failed (${res.status})`);
      }
      if (fileRef.current) fileRef.current.value = "";
      setIdColumn("");
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="mt-4 rounded-lg border border-hairline bg-panel-raised/40 p-3">
      <p className="eyebrow mb-2">Upload data file</p>

      {Object.keys(uploaded).length > 0 && (
        <p className="mb-2 text-xs text-dim">
          Loaded:{" "}
          {Object.entries(uploaded)
            .map(([e, u]) => `${e} (${u.filename ?? "file"})`)
            .join(", ")}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <select
          value={entity}
          onChange={(e) => setEntity(e.target.value)}
          className="rounded-lg border border-hairline bg-panel-raised px-2.5 py-1.5 text-sm outline-none focus:border-accent"
        >
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <input
          value={idColumn}
          onChange={(e) => setIdColumn(e.target.value)}
          placeholder="id column (optional)"
          className="w-36 rounded-lg border border-hairline bg-panel-raised px-2.5 py-1.5 text-sm outline-none focus:border-accent"
        />

        <input
          ref={fileRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="text-xs text-dim file:mr-2 file:rounded-md file:border-0 file:bg-panel-raised file:px-2 file:py-1 file:text-dim"
        />

        <button
          type="button"
          disabled={uploading}
          onClick={upload}
          className="inline-flex items-center gap-1.5 rounded-lg border border-hairline px-3 py-1.5 text-sm text-dim transition hover:text-white disabled:opacity-60"
        >
          {uploading ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Upload size={14} />
          )}
          Upload
        </button>
      </div>

      {err && <p className="mt-2 text-xs text-critical">{err}</p>}
    </div>
  );
}

const inputClass =
  "w-full rounded-lg border border-hairline bg-panel-raised px-3 py-2 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20";

function AddConnection({ onCreated }: { onCreated: () => void }) {
  const [sourceType, setSourceType] = useState<"file_upload" | "sql">(
    "file_upload",
  );
  const [name, setName] = useState("");
  const [sql, setSql] = useState({
    host: "",
    port: "5432",
    database: "",
    user: "",
    password: "",
    driver: "postgresql",
  });
  const [queries, setQueries] = useState(
    '{\n  "supplier": "SELECT id AS external_id, name, country FROM vendors WHERE updated_at > :since"\n}',
  );
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  async function create() {
    setSaving(true);
    setErr("");
    try {
      const body: Record<string, unknown> = {
        source_type: sourceType,
        display_name: name || `${sourceType} source`,
        config: {},
        credentials: {},
      };

      if (sourceType === "sql") {
        let parsedQueries: unknown = {};
        try {
          parsedQueries = JSON.parse(queries);
        } catch {
          throw new Error("Queries must be valid JSON.");
        }
        body.config = { driver: sql.driver, queries: parsedQueries };
        body.credentials = {
          host: sql.host,
          port: Number(sql.port) || 5432,
          database: sql.database,
          user: sql.user,
          password: sql.password,
        };
      }

      await apiRequest("/connections", {
        method: "POST",
        body: JSON.stringify(body),
      });
      setName("");
      onCreated();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not create connection.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel label="New" title="Add a connection" tone="live">
      <div className="space-y-3">
        <div className="flex gap-2">
          {(["file_upload", "sql"] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => setSourceType(t)}
              className={`rounded-lg border px-3 py-1.5 text-sm transition ${
                sourceType === t
                  ? "border-accent bg-accent/10 text-white"
                  : "border-hairline text-dim hover:text-white"
              }`}
            >
              {t === "file_upload" ? "File upload" : "SQL database"}
            </button>
          ))}
        </div>

        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Display name (e.g. NetSuite replica)"
          className={inputClass}
        />

        {sourceType === "sql" && (
          <>
            <div className="grid grid-cols-2 gap-2">
              <input
                value={sql.host}
                onChange={(e) => setSql({ ...sql, host: e.target.value })}
                placeholder="host"
                className={inputClass}
              />
              <input
                value={sql.port}
                onChange={(e) => setSql({ ...sql, port: e.target.value })}
                placeholder="port"
                className={inputClass}
              />
              <input
                value={sql.database}
                onChange={(e) =>
                  setSql({ ...sql, database: e.target.value })
                }
                placeholder="database"
                className={inputClass}
              />
              <select
                value={sql.driver}
                onChange={(e) => setSql({ ...sql, driver: e.target.value })}
                className={inputClass}
              >
                <option value="postgresql">postgresql</option>
                <option value="mysql">mysql</option>
                <option value="mssql">mssql</option>
              </select>
              <input
                value={sql.user}
                onChange={(e) => setSql({ ...sql, user: e.target.value })}
                placeholder="user (read-only)"
                className={inputClass}
              />
              <input
                type="password"
                value={sql.password}
                onChange={(e) =>
                  setSql({ ...sql, password: e.target.value })
                }
                placeholder="password"
                className={inputClass}
              />
            </div>

            <div>
              <label className="eyebrow mb-1 block">
                Entity queries (JSON) — use{" "}
                <span className="num">:since</span> for incremental sync
              </label>
              <textarea
                value={queries}
                onChange={(e) => setQueries(e.target.value)}
                rows={5}
                className={`${inputClass} num`}
              />
            </div>
          </>
        )}

        {err && <p className="text-xs text-critical">{err}</p>}

        <button
          type="button"
          disabled={saving}
          onClick={create}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:opacity-60"
        >
          {saving && <Loader2 size={14} className="animate-spin" />}
          Create connection
        </button>

        {sourceType === "file_upload" && (
          <p className="text-xs text-mute">
            After creating, upload one CSV/Excel file per entity from the
            card above.
          </p>
        )}

        <div className="border-t border-hairline pt-3">
          <MergeConnect onCreated={onCreated} />
        </div>
      </div>
    </Panel>
  );
}

function MergeConnect({ onCreated }: { onCreated: () => void }) {
  const [state, setState] = useState<"idle" | "checking" | "ready" | "off">(
    "idle",
  );
  const [msg, setMsg] = useState("");

  async function connect() {
    setState("checking");
    setMsg("");
    try {
      // Obtaining a link token also tells us whether Merge is configured.
      await apiRequest<{ link_token: string }>(
        "/connections/merge/link-token",
        { method: "POST" },
      );
      setState("ready");
      setMsg(
        "Merge is configured. Finish wiring the Merge Link popup (npm i @mergeapi/react-merge-link) to complete the OAuth flow.",
      );
    } catch (e) {
      setState("off");
      setMsg(
        e instanceof Error
          ? e.message
          : "Merge is not configured (set MERGE_API_KEY on the backend).",
      );
    }
    onCreated();
  }

  return (
    <div>
      <p className="eyebrow mb-1.5">Unified accounting API</p>
      <button
        type="button"
        onClick={connect}
        disabled={state === "checking"}
        className="inline-flex items-center gap-2 rounded-lg border border-hairline px-3 py-1.5 text-sm text-dim transition hover:text-white disabled:opacity-60"
      >
        {state === "checking" ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          <Zap size={14} />
        )}
        Connect via Merge (QuickBooks / Xero / NetSuite…)
      </button>
      {msg && (
        <p
          className={`mt-2 text-xs ${
            state === "off" ? "text-elevated" : "text-dim"
          }`}
        >
          {msg}
        </p>
      )}
    </div>
  );
}
