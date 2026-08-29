"use client";

import { FormEvent, Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { ArrowRight, Loader2 } from "lucide-react";

import { apiRequest } from "@/lib/api";
import { setToken } from "@/lib/auth";
import { Wordmark } from "@/app/components/Logo";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

const INDUSTRIES = [
  "Food",
  "Clothing",
  "Hardware",
  "Software",
  "Manufacturing",
  "Retail",
  "Logistics",
  "Pharma",
  "Automotive",
  "Other",
];

function safeNext(raw: string | null): string {
  if (raw && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/integrations";
}

function SignupView() {
  const router = useRouter();
  const next = safeNext(useSearchParams().get("next"));

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [company, setCompany] = useState("");
  const [industry, setIndustry] = useState(INDUSTRIES[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await apiRequest<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
          organization_name: company.trim(),
          industry,
          seed_demo: true,
        }),
      });

      if (!data.access_token) {
        throw new Error("Account created but no token was returned.");
      }

      setToken(data.access_token);
      router.push(next);
    } catch (err) {
      console.error("Signup failed:", err);
      setError(err instanceof Error ? err.message : "Signup failed.");
    } finally {
      setLoading(false);
    }
  }

  const field =
    "w-full rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20";

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-bg p-6">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 left-1/2 h-[38rem] w-[38rem] -translate-x-1/2 rounded-full bg-accent/20 blur-[140px]"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute bottom-[-12rem] right-[-8rem] h-[26rem] w-[26rem] rounded-full bg-live/10 blur-[120px]"
      />

      <div className="relative w-full max-w-md">
        <Link href="/" className="mb-8 inline-block">
          <Wordmark size={30} />
        </Link>

        <div className="elevated relative overflow-hidden rounded-xl border border-hairline bg-panel p-7 ring-1 ring-inset ring-white/[0.03]">
          <span
            aria-hidden
            className="absolute inset-y-0 left-0 w-[3px] bg-accent"
          />

          <h1 className="text-xl font-semibold tracking-tight text-white">
            Create your workspace
          </h1>
          <p className="mt-1 text-sm text-dim">
            Free, and pre-loaded with a sample business so you can explore right
            away.
          </p>

          {error && (
            <div className="mt-5 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="eyebrow mb-1.5 block">Full name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Jordan Rivera"
                className={field}
              />
            </div>

            <div>
              <label className="eyebrow mb-1.5 block">Work email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@company.com"
                className={field}
              />
            </div>

            <div>
              <label className="eyebrow mb-1.5 block">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="At least 8 characters"
                className={field}
              />
            </div>

            <div>
              <label className="eyebrow mb-1.5 block">Company name</label>
              <input
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                required
                placeholder="Acme Industries"
                className={field}
              />
            </div>

            <div>
              <label className="eyebrow mb-1.5 block">Industry</label>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className={field}
              >
                {INDUSTRIES.map((i) => (
                  <option key={i} value={i}>
                    {i}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Creating workspace…
                </>
              ) : (
                <>
                  Create workspace
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="mt-5 text-sm text-dim">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-accent hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg" />}>
      <SignupView />
    </Suspense>
  );
}
