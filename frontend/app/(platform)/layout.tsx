"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import AppShell from "@/app/components/AppShell";

import { isAuthenticated } from "@/lib/auth";

export default function PlatformLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
    }
  }, [router]);

  return <AppShell>{children}</AppShell>;
}
