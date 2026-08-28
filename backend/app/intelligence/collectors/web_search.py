"""Web-search collector — verified price / tariff / inflation / disruption news.

Supports two providers, auto-detected from the key:
  - Tavily  (key starts with ``tvly-``)  — returns an AI answer + sources
  - SerpApi (anything else)              — Google News results

Set the key as ``TAVILY_API_KEY`` **or** ``SERPAPI_KEY``. Each standing
query (see ``queries.py``) yields one or more ``global_events`` rows
(``source="WEB_SEARCH"``). No key -> graceful no-op.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime

import requests
from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.intelligence.queries import CATEGORY_EVENT_TYPE, STANDING_QUERIES
from app.models.global_event import GlobalEvent
from app.services.event_scoring import calculate_severity

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"
SERPAPI_URL = "https://serpapi.com/search.json"


def _key() -> str | None:
    return os.getenv("SERPAPI_KEY") or os.getenv("TAVILY_API_KEY")


def _provider() -> str:
    key = _key() or ""
    return "tavily" if key.startswith("tvly-") else "serpapi"


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.utcnow()
    try:
        return date_parser.parse(value, fuzzy=True)
    except (ValueError, OverflowError):
        return datetime.utcnow()


# --- provider fetchers: return a list of {title, url, source, snippet, when}

def _fetch_tavily(query: str) -> list[dict]:
    resp = requests.post(
        TAVILY_URL,
        headers={"Authorization": f"Bearer {_key()}"},
        json={
            "query": query,
            "topic": "news",
            "days": 7,
            "max_results": 5,
            "include_answer": "advanced",
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Tavily {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    items = [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "source": None,
            "snippet": r.get("content"),
            "when": r.get("published_date"),
        }
        for r in (data.get("results") or [])
    ]
    answer = (data.get("answer") or "").strip()
    if answer and items:
        items[0]["snippet"] = answer  # richest summary on the lead item
    return items


def _fetch_serpapi(query: str) -> list[dict]:
    resp = requests.get(
        SERPAPI_URL,
        params={
            "engine": "google_news",
            "q": query,
            "api_key": _key(),
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"SerpApi {resp.status_code}: {resp.text[:200]}")
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"SerpApi: {data['error']}")
    return [
        {
            "title": r.get("title"),
            "url": r.get("link"),
            "source": (r.get("source") or {}).get("name"),
            "snippet": r.get("snippet"),
            "when": r.get("date"),
        }
        for r in (data.get("news_results") or [])
    ]


def collect_web_search(db: Session) -> dict:
    if not _key():
        return {"skipped": "no SERPAPI_KEY / TAVILY_API_KEY set"}

    fetch = _fetch_tavily if _provider() == "tavily" else _fetch_serpapi
    per_query = 1 if _provider() == "tavily" else 3

    seen = {
        h
        for (h,) in db.execute(
            select(GlobalEvent.external_id).where(
                GlobalEvent.source == "WEB_SEARCH"
            )
        ).all()
        if h
    }

    stored = failed = 0

    for spec in STANDING_QUERIES:
        try:
            items = fetch(spec["query"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("web search failed for %r: %s", spec["query"], exc)
            failed += 1
            continue

        event_type = CATEGORY_EVENT_TYPE.get(spec["category"], "GENERAL")

        for item in items[:per_query]:
            title = (item.get("title") or "").strip()
            url = item.get("url")
            if not title or not url:
                continue

            digest = hashlib.sha256(url.encode()).hexdigest()[:32]
            if digest in seen:
                continue

            severity = spec.get("severity_hint") or calculate_severity(
                f"{title} {item.get('snippet') or ''}", event_type
            )
            db.add(
                GlobalEvent(
                    source="WEB_SEARCH",
                    external_id=digest,
                    event_type=event_type,
                    title=title[:500],
                    description=(item.get("snippet") or "")[:2000] or None,
                    url=url,
                    country=None,
                    region=None,
                    severity=severity,
                    detected_at=_parse_date(item.get("when")),
                    raw_data={
                        "query": spec["query"],
                        "category": spec["category"],
                        "provider": _provider(),
                        "answer": item.get("snippet"),
                        "sources": [
                            {
                                "title": item.get("source") or title[:40],
                                "url": url,
                            }
                        ],
                    },
                )
            )
            seen.add(digest)
            stored += 1

    db.commit()
    return {
        "provider": _provider(),
        "queries": len(STANDING_QUERIES),
        "stored": stored,
        "failed": failed,
    }
