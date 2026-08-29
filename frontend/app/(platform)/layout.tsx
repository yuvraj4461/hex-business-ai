"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import AppShell from "@/app/components/AppShell";

import { isAuthenticated } from "@/lib/auth";

export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (isAuthenticated()) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-shot auth gate
      setReady(true);
    } else {
      const next = encodeURIComponent(pathname || "/dashboard");
      router.replace(`/login?next=${next}`);
    }
  }, [router, pathname]);

  // Don't flash the app shell before the auth check resolves.
  if (!ready) {
    return <div className="min-h-screen bg-bg" />;
  }

  return <AppShell>{children}</AppShell>;
}
