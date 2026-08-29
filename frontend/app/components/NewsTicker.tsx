"use client";

import { useEffect, useState } from "react";

import { ExternalLink } from "lucide-react";

import { apiRequest } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { TONE_TEXT, toneForStatus } from "@/app/components/tone";

interface FeedItem {
  id: number;
  source: string;
  event_type: string;
  title: string;
  severity: string;
  region?: string | null;
  url?: string | null;
  detected_at?: string | null;
}

function TickerItem({ item }: { item: FeedItem }) {
  const tone = toneForStatus(item.severity);
  const meta = [
    item.event_type?.replace(/_/g, " "),
    item.region,
    timeAgo(item.detected_at),
  ]
    .filter(Boolean)
    .join(" · ");

  const inner = (
    <span className="mx-6 inline-flex items-center gap-2 whitespace-nowrap text-sm">
      <span
        className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${TONE_TEXT[tone]} bg-current`}
      />
      <span className="font-medium text-white">{item.title}</span>
      <span className="num text-xs text-mute">{meta}</span>
      {item.url && <ExternalLink size={11} className="text-mute" />}
    </span>
  );

  return item.url ? (
    <a
      href={item.url}
      target="_blank"
      rel="noreferrer"
      className="transition hover:brightness-125"
    >
      {inner}
    </a>
  ) : (
    inner
  );
}

/**
 * NewsTicker — one seamless right-to-left scroll of the live event feed.
 * Renders nothing until it has items, so it never leaves an empty bar.
 */
export default function NewsTicker() {
  const [items, setItems] = useState<FeedItem[]>([]);

  useEffect(() => {
    let alive = true;

    async function load() {
      try {
        const feed = await apiRequest<FeedItem[]>(
          "/intelligence/feed?limit=20",
        );
        if (alive) setItems(feed.filter((f) => f.title));
      } catch {
        /* ticker is optional */
      }
    }

    load();
    const t = window.setInterval(load, 60_000);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, []);

  if (items.length === 0) return null;

  return (
    <div className="ticker-mask relative mb-6 overflow-hidden rounded-lg border border-hairline bg-panel">
      <span className="absolute left-0 top-0 z-10 flex h-full items-center gap-1.5 border-r border-hairline bg-panel px-3">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-live opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-live" />
        </span>
        <span className="eyebrow !text-live">Live</span>
      </span>

      <div className="ticker-track py-2.5 pl-24">
        {[...items, ...items].map((item, i) => (
          <TickerItem key={`${item.id}-${i}`} item={item} />
        ))}
      </div>

      <div className="pointer-events-none absolute right-0 top-0 h-full w-12 bg-gradient-to-l from-panel to-transparent" />
    </div>
  );
}
