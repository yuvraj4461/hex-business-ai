"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  Bot,
  Loader2,
  Send,
  Sparkles,
} from "lucide-react";

import {
  apiRequest,
} from "@/lib/api";


interface CopilotData {
  organization_id?: number;

  business?: any;

  market?: any;

  agriculture?: any;

  global_event?: any;

  exposure?: any;
}


interface CopilotResponse {
  question: string;
  answer: string;
  data?: CopilotData;
}


export default function CopilotPage() {

  const [
    question,
    setQuestion,
  ] = useState("");


  const [
    response,
    setResponse,
  ] = useState<CopilotResponse | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {

    event.preventDefault();

    if (!question.trim()) {
      return;
    }


    try {

      setLoading(true);
      setError("");


      const result =
        await apiRequest<CopilotResponse>(
          "/copilot/ask",
          {
            method: "POST",

            body: JSON.stringify({
              question:
                question.trim(),
            }),
          }
        );


      setResponse(
        result
      );

    } catch (err) {

      console.error(
        "Copilot request failed:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to get a Copilot response."
      );

    } finally {

      setLoading(false);

    }
  }


  return (
    <div className="p-6 lg:p-8">

      <div className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-xl bg-violet-100 p-3">

            <Sparkles
              size={22}
              className="text-violet-600"
            />

          </div>

          <div>

            <p className="text-sm text-slate-500">
              Decision Intelligence
            </p>

            <h1 className="text-3xl font-bold text-slate-900">
              AI Copilot
            </h1>

          </div>

        </div>

        <p className="mt-3 text-slate-500">
          Ask HEX about your business,
          operations, market conditions and risk.
        </p>

      </div>


      <div className="grid gap-6 lg:grid-cols-3">


        {/* ASK PANEL */}

        <div className="rounded-2xl border bg-white p-6 shadow-sm lg:col-span-2">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-slate-100 p-3">

              <Bot size={20} />

            </div>

            <div>

              <h2 className="font-semibold">
                Ask HEX
              </h2>

              <p className="text-sm text-slate-500">
                Use natural language.
              </p>

            </div>

          </div>


          <form
            onSubmit={handleSubmit}
            className="mt-6"
          >

            <textarea
              value={question}
              onChange={(event) =>
                setQuestion(
                  event.target.value
                )
              }
              rows={6}
              placeholder="Example: What is the biggest risk to my business right now?"
              className="w-full resize-none rounded-2xl border p-4 outline-none transition focus:border-slate-500"
            />


            {error && (

              <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>

            )}


            <div className="mt-4 flex justify-end">

              <button
                type="submit"
                disabled={
                  loading
                  ||
                  !question.trim()
                }
                className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
              >

                {loading ? (
                  <>
                    <Loader2
                      size={17}
                      className="animate-spin"
                    />

                    Analyzing...

                  </>
                ) : (
                  <>
                    <Send
                      size={17}
                    />

                    Ask HEX

                  </>
                )}

              </button>

            </div>

          </form>

        </div>


        {/* CONTEXT PANEL */}

        <div className="rounded-2xl border bg-white p-6 shadow-sm">

          <h2 className="font-semibold">
            Available Context
          </h2>

          <div className="mt-5 space-y-3">

            {[
              "Business performance",
              "Historical analytics",
              "Global events",
              "Commodity intelligence",
              "Agriculture signals",
              "Demand forecasts",
              "Business exposure",
              "Route disruption",
            ].map(
              (item) => (

                <div
                  key={item}
                  className="rounded-xl bg-slate-50 px-4 py-3 text-sm text-slate-600"
                >
                  {item}
                </div>

              )
            )}

          </div>

        </div>

      </div>


      {/* RESPONSE */}

      {response && (

        <div className="mt-8 rounded-2xl border bg-white p-6 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-emerald-50 p-3">

              <Sparkles
                size={20}
                className="text-emerald-600"
              />

            </div>

            <div>

              <p className="text-sm text-slate-500">
                HEX Response
              </p>

              <h2 className="font-semibold">
                {response.question}
              </h2>

            </div>

          </div>


          <div className="mt-6 rounded-2xl bg-slate-50 p-6">

            <p className="whitespace-pre-wrap leading-7 text-slate-700">
              {response.answer}
            </p>

          </div>

        </div>

      )}

    </div>
  );
}