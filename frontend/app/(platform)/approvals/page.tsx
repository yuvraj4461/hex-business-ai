"use client";

import { useEffect, useState } from "react";

import { apiRequest } from "@/lib/api";


interface Approval {
  id: number;
  organization_id: number;
  user_id: number;
  recommendation: string;
  scenario: string;
  event_id: number | null;
  comment: string | null;
  status: string;
  approved_at: string | null;
}


interface CreateApprovalResponse {
  status: string;
  approval: Approval;
}


export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const [recommendation, setRecommendation] = useState(
    "Activate alternative supply routes for the Red Sea disruption."
  );

  const [scenario, setScenario] = useState(
    "Red Sea shipping disruption"
  );

  const [eventId, setEventId] = useState("");

  const [comment, setComment] = useState(
    "Approved for executive review and operational planning."
  );


  async function loadApprovals() {
    try {
      setLoading(true);
      setError("");

      const data = await apiRequest<Approval[]>(
        "/approvals",
        {
          method: "GET",
        }
      );

      setApprovals(data);
    } catch (err) {
      console.error("Failed to load approvals:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Failed to load approvals."
      );
    } finally {
      setLoading(false);
    }
  }


  async function handleCreateApproval() {
    try {
      setCreating(true);
      setError("");

      const payload = {
        recommendation,
        scenario,
        event_id: eventId
          ? Number(eventId)
          : null,
        comment: comment || null,
      };

      const response =
        await apiRequest<CreateApprovalResponse>(
          "/approvals",
          {
            method: "POST",
            body: JSON.stringify(payload),
          }
        );

      setApprovals((current) => [
        response.approval,
        ...current,
      ]);

    } catch (err) {
      console.error(
        "Failed to create approval:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Failed to create approval."
      );
    } finally {
      setCreating(false);
    }
  }


  useEffect(() => {
    loadApprovals();
  }, []);


  return (
    <main className="min-h-screen bg-slate-50 px-6 py-10">
      <div className="mx-auto max-w-6xl">

        {/* Header */}
        <div className="mb-10">
          <div className="text-sm font-medium text-slate-500">
            Governance & Decision Control
          </div>

          <h1 className="mt-2 text-4xl font-bold text-slate-900">
            Approvals
          </h1>

          <p className="mt-3 max-w-3xl text-base text-slate-600">
            Review and record business recommendations generated
            by HEX before operational decisions are implemented.
          </p>
        </div>


        {/* Error */}
        {error && (
          <div className="mb-6 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-700">
            <div className="font-semibold">
              Approval operation failed
            </div>

            <div className="mt-1 text-sm">
              {error}
            </div>
          </div>
        )}


        <div className="grid gap-8 lg:grid-cols-[420px_1fr]">

          {/* Create Approval */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

            <div className="mb-6">
              <h2 className="text-xl font-semibold text-slate-900">
                Record Decision
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                Create an approval record for a HEX recommendation.
              </p>
            </div>


            <div className="space-y-5">

              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Recommendation
                </label>

                <textarea
                  value={recommendation}
                  onChange={(event) =>
                    setRecommendation(
                      event.target.value
                    )
                  }
                  rows={5}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />
              </div>


              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Scenario
                </label>

                <input
                  value={scenario}
                  onChange={(event) =>
                    setScenario(
                      event.target.value
                    )
                  }
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />
              </div>


              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Event ID
                </label>

                <input
                  type="number"
                  value={eventId}
                  onChange={(event) =>
                    setEventId(
                      event.target.value
                    )
                  }
                  placeholder="Optional"
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />
              </div>


              <div>
                <label className="mb-2 block text-sm font-medium text-slate-700">
                  Comment
                </label>

                <textarea
                  value={comment}
                  onChange={(event) =>
                    setComment(
                      event.target.value
                    )
                  }
                  rows={4}
                  className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                />
              </div>


              <button
                type="button"
                onClick={handleCreateApproval}
                disabled={creating}
                className="w-full rounded-xl bg-slate-900 px-5 py-3 font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {creating
                  ? "Recording decision..."
                  : "Record Approval"}
              </button>

            </div>

          </section>


          {/* Approval History */}
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-slate-900">
                  Approval History
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  Decisions recorded by the current organization.
                </p>
              </div>

              <button
                type="button"
                onClick={loadApprovals}
                disabled={loading}
                className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:opacity-60"
              >
                Refresh
              </button>
            </div>


            {loading ? (
              <div className="rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500">
                Loading approval history...
              </div>
            ) : approvals.length === 0 ? (
              <div className="rounded-xl bg-slate-50 p-8 text-center">
                <div className="text-base font-medium text-slate-700">
                  No approvals recorded
                </div>

                <div className="mt-2 text-sm text-slate-500">
                  Create the first decision record using the form.
                </div>
              </div>
            ) : (
              <div className="space-y-5">

                {approvals.map((approval) => (
                  <article
                    key={approval.id}
                    className="rounded-2xl border border-slate-200 p-5"
                  >

                    <div className="flex flex-wrap items-start justify-between gap-4">

                      <div>
                        <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Approval #{approval.id}
                        </div>

                        <h3 className="mt-1 text-lg font-semibold text-slate-900">
                          {approval.scenario}
                        </h3>
                      </div>


                      <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                        {approval.status}
                      </span>

                    </div>


                    <div className="mt-5 rounded-xl bg-slate-50 p-4">

                      <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
                        Recommendation
                      </div>

                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">
                        {approval.recommendation}
                      </p>

                    </div>


                    {approval.comment && (
                      <div className="mt-4">

                        <div className="text-xs font-medium uppercase tracking-wide text-slate-400">
                          Comment
                        </div>

                        <p className="mt-1 text-sm text-slate-600">
                          {approval.comment}
                        </p>

                      </div>
                    )}


                    <div className="mt-5 grid gap-3 text-sm text-slate-500 sm:grid-cols-3">

                      <div>
                        <span className="font-medium text-slate-700">
                          User ID:
                        </span>{" "}
                        {approval.user_id}
                      </div>

                      <div>
                        <span className="font-medium text-slate-700">
                          Event ID:
                        </span>{" "}
                        {approval.event_id ?? "—"}
                      </div>

                      <div>
                        <span className="font-medium text-slate-700">
                          Approved:
                        </span>{" "}
                        {approval.approved_at
                          ? new Date(
                              approval.approved_at
                            ).toLocaleString()
                          : "—"}
                      </div>

                    </div>

                  </article>
                ))}

              </div>
            )}

          </section>

        </div>


        {/* Governance note */}
        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">

          <h2 className="text-lg font-semibold text-slate-900">
            Governance Note
          </h2>

          <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-600">
            HEX records recommendations and business decisions so
            high-impact actions can remain traceable. The current
            backend implementation automatically marks newly created
            approval records as APPROVED.
          </p>

        </section>

      </div>
    </main>
  );
}