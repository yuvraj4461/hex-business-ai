"""Web-search collector — verified price / tariff / inflation / disruption news.

Uses Tavily (https://tavily.com) — a search API that returns an
AI-synthesised answer plus cited sources. Each standing query becomes one
`global_events` row (`source="WEB_SEARCH"`) with the answer + sources in
`raw_data`. No key -> the collector is a graceful no-op.
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.gemini import generate_text, is_configured as gemini_ready
from app.intelligence.queries import CATEGORY_EVENT_TYPE, STANDING_QUERIES
from app.models.global_event import GlobalEvent
from app.services.event_scoring import calculate_severity

logger = logging.getLogger(__name__)

TAVILY_URL = "https://api.tavily.com/search"


def _api_key() -> str | None:
    return os.getenv("TAVILY_API_KEY")


def _search(query: str) -> dict | None:
    try:
        resp = requests.post(
            TAVILY_URL,
            headers={"Authorization": f"Bearer {_api_key()}"},
            json={
                "query": query,
                "topic": "news",
                "days": 7,
                "max_results": 5,
                "search_depth": "basic",
                "include_answer": "advanced",
            },
            timeout=30,
        )
        if resp.status_code >= 400:
            logger.warning(
                "Tavily %s for %r: %s",
                resp.status_code,
                query,
                resp.text[:200],
            )
            return None
        return resp.json()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Tavily search failed for %r: %s", query, exc)
        return None


def _headline(query: str, answer: str) -> str:
    if not gemini_ready():
        return answer.split(". ")[0][:180] if answer else query
    try:
        text = generate_text(
            "In one factual news-headline sentence (max 16 words), summarise:\n"
            f"{answer}"
        )
        return text.strip().strip('"')[:200] or answer[:180]
    except Exception:  # noqa: BLE001
        return answer.split(". ")[0][:180] if answer else query


def collect_web_search(db: Session) -> dict:
    if not _api_key():
        return {"skipped": "TAVILY_API_KEY not set"}

    stored = 0
    failed = 0
    empty = 0
    seen_hashes = {
        h
        for (h,) in db.execute(
            select(GlobalEvent.external_id).where(
                GlobalEvent.source == "WEB_SEARCH"
            )
        ).all()
        if h
    }

    for spec in STANDING_QUERIES:
        result = _search(spec["query"])
        if not result:
            failed += 1
            continue

        answer = (result.get("answer") or "").strip()
        if not answer:
            empty += 1
            continue

        digest = hashlib.sha256(
            f"{spec['query']}|{answer}".encode()
        ).hexdigest()[:32]
        if digest in seen_hashes:
            continue

        sources = [
            {"title": r.get("title"), "url": r.get("url")}
            for r in (result.get("results") or [])[:5]
        ]
        event_type = CATEGORY_EVENT_TYPE.get(
            spec["category"], "GENERAL"
        )
        title = _headline(spec["query"], answer)
        severity = spec.get("severity_hint") or calculate_severity(
            f"{title} {answer}", event_type
        )

        db.add(
            GlobalEvent(
                source="WEB_SEARCH",
                external_id=digest,
                event_type=event_type,
                title=title[:500],
                description=answer[:2000],
                url=sources[0]["url"] if sources else None,
                country=None,
                region=None,
                severity=severity,
                detected_at=datetime.utcnow(),
                raw_data={
                    "query": spec["query"],
                    "category": spec["category"],
                    "answer": answer,
                    "sources": sources,
                },
            )
        )
        seen_hashes.add(digest)
        stored += 1

    db.commit()
    return {
        "queries": len(STANDING_QUERIES),
        "stored": stored,
        "failed": failed,
        "empty_or_duplicate": empty + (len(STANDING_QUERIES) - stored - failed - empty),
    }
