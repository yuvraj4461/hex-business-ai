"use client";

import { FormEvent, Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";

import { ArrowRight, Loader2 } from "lucide-react";

import { apiRequest } from "@/lib/api";
import { isAuthenticated, setToken } from "@/lib/auth";
import { Wordmark } from "@/app/components/Logo";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

function safeNext(raw: string | null): string {
  // only allow internal paths
  if (raw && raw.startsWith("/") && !raw.startsWith("//")) return raw;
  return "/dashboard";
}

function LoginView() {
  const router = useRouter();
  const params = useSearchParams();
  const next = safeNext(params.get("next"));

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Already signed in? Go straight to the intended page.
  useEffect(() => {
    if (isAuthenticated()) router.replace(next);
  }, [router, next]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError("");

    try {
      const data = await apiRequest<LoginResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (!data.access_token) {
        throw new Error("Login succeeded but no access token was returned.");
      }

      setToken(data.access_token);
      router.push(next);
    } catch (err) {
      console.error("Login failed:", err);
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

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
            Sign in
          </h1>
          <p className="mt-1 text-sm text-dim">
            Supply-chain risk intelligence and decision support.
          </p>

          {error && (
            <div className="mt-5 rounded-lg border border-critical/30 bg-critical/5 p-3 text-sm text-critical">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <div>
              <label className="eyebrow mb-1.5 block">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
            </div>

            <div>
              <label className="eyebrow mb-1.5 block">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="w-full rounded-lg border border-hairline bg-panel-raised px-3.5 py-2.5 text-sm outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-semibold text-bg transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Signing in…
                </>
              ) : (
                <>
                  Sign in
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          <p className="mt-5 text-sm text-dim">
            New to HEX?{" "}
            <Link
              href={`/signup${next !== "/dashboard" ? `?next=${encodeURIComponent(next)}` : ""}`}
              className="font-semibold text-accent hover:underline"
            >
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-bg" />}>
      <LoginView />
    </Suspense>
  );
}
