"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";

import {
  apiRequest,
} from "@/lib/api";

import {
  setToken,
} from "@/lib/auth";


interface LoginResponse {
  access_token: string;
  token_type: string;
}


export default function LoginPage() {

  const router =
    useRouter();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {

    event.preventDefault();

    setLoading(true);
    setError("");

    try {

      const data =
        await apiRequest<LoginResponse>(
          "/auth/login",
          {
            method: "POST",

            body: JSON.stringify({
              email,
              password,
            }),
          }
        );


      if (!data.access_token) {

        throw new Error(
          "Login succeeded but no access token was returned."
        );

      }


      setToken(
        data.access_token
      );

      router.push(
        "/dashboard"
      );

    } catch (err) {

      console.error(
        "Login failed:",
        err
      );

      setError(
        err instanceof Error
          ? err.message
          : "Login failed."
      );

    } finally {

      setLoading(false);

    }
  }


  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">

      <div className="w-full max-w-md rounded-2xl border bg-white p-8 shadow-sm">

        <div className="mb-8">

          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-lg font-bold text-white">
            H
          </div>

          <h1 className="mt-5 text-2xl font-bold text-slate-900">
            Welcome to HEX
          </h1>

          <p className="mt-2 text-sm text-slate-500">
            Business intelligence and decision support.
          </p>

        </div>


        {error && (
          <div className="mb-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}


        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >

          <div>

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              required
              className="w-full rounded-xl border px-4 py-3 outline-none transition focus:border-slate-500"
              placeholder="you@example.com"
            />

          </div>


          <div>

            <label className="mb-2 block text-sm font-medium text-slate-700">
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              required
              className="w-full rounded-xl border px-4 py-3 outline-none transition focus:border-slate-500"
              placeholder="••••••••"
            />

          </div>


          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-slate-900 px-4 py-3 font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading
              ? "Signing in..."
              : "Sign in"}
          </button>

        </form>

      </div>

    </main>
  );
}