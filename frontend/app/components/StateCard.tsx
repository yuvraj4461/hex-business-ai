import type { ReactNode } from "react";

import { Loader2, TriangleAlert, Inbox } from "lucide-react";

/**
 * StateCard — the loading / error / empty placeholders that
 * every data page needs. Keeps those three states consistent
 * instead of re-implementing them per page.
 */
export function LoadingCard({ message = "Loading…" }: { message?: string }) {
  return (
    <div className="rounded-xl border border-hairline bg-panel p-10 text-center">
      <Loader2
        size={26}
        className="mx-auto animate-spin text-live"
      />
      <p className="mt-4 text-sm text-dim">{message}</p>
    </div>
  );
}

export function ErrorCard({
  title = "Something went wrong",
  message,
  onRetry,
}: {
  title?: string;
  message?: ReactNode;
  onRetry?: () => void;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-critical/30 bg-critical/5 p-6">
      <span
        aria-hidden
        className="absolute inset-y-0 left-0 w-[3px] bg-critical"
      />

      <div className="flex items-start gap-3">
        <TriangleAlert size={18} className="mt-0.5 shrink-0 text-critical" />

        <div className="min-w-0 flex-1">
          <p className="font-semibold text-critical">{title}</p>

          {message && (
            <p className="mt-1 text-sm text-dim">{message}</p>
          )}

          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-critical/15 px-3 py-1.5 text-sm font-semibold text-critical transition hover:bg-critical/25"
            >
              Retry
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyCard({
  message = "No data available.",
}: {
  message?: ReactNode;
}) {
  return (
    <div className="rounded-xl border border-hairline bg-panel p-10 text-center">
      <Inbox size={26} className="mx-auto text-mute" />
      <p className="mt-3 text-sm text-dim">{message}</p>
    </div>
  );
}
